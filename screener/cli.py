"""
cli.py — Point d'entrée du screener.

Usage :
    python -m screener.cli                       # config par défaut
    python -m screener.cli --timeframe 4h --top 80 --bias accumulation
    python -m screener.cli --symbols BTC/USDT ETH/USDT --no-cache
"""
from __future__ import annotations

import argparse
import sys

import pandas as pd
import yaml

from . import data as data_mod
from .events import Thresholds, detect_events
from .features import add_features, detect_trading_range, market_regime, swing_points
from .mtf import MTFResult, combine_mtf
from .score import SymbolResult, score_symbol
from .window import detect_supply_dryup, detect_window_structure


def load_config(path: str = "config.yaml") -> dict:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        return {}


def analyze_symbol(symbol: str, df: pd.DataFrame, cfg: dict) -> SymbolResult | None:
    if df is None or len(df) < cfg["lookback"] + cfg["buffer"] + cfg["vol_ma"]:
        return None
    df = add_features(df, vol_ma=cfg["vol_ma"], atr_period=cfg["atr_period"])
    df = swing_points(df, left=3, right=3)
    tr = detect_trading_range(df, lookback=cfg["lookback"], buffer=cfg["buffer"])
    th = Thresholds(**cfg.get("thresholds", {}))
    events = detect_events(df, tr, buffer=cfg["buffer"], th=th)
    return score_symbol(symbol, df, tr, events)


def run(cfg: dict) -> pd.DataFrame:
    ex = data_mod.get_exchange(cfg["exchange"])
    if cfg.get("symbols"):
        universe = cfg["symbols"]
    else:
        universe = data_mod.build_universe(ex, quote=cfg["quote"], top_n=cfg["top"])
        print(f"Univers : {len(universe)} paires {cfg['quote']} sur {cfg['exchange']}", file=sys.stderr)

    results: list[SymbolResult] = []
    for i, sym in enumerate(universe, 1):
        try:
            df = data_mod.fetch_ohlcv(ex, sym, timeframe=cfg["timeframe"],
                                      limit=cfg["limit"], use_cache=cfg["use_cache"])
            r = analyze_symbol(sym, df, cfg)
            if r and r.score > 0:
                results.append(r)
        except Exception as e:  # un symbole qui échoue ne casse pas le screen
            print(f"  [skip] {sym}: {e}", file=sys.stderr)
        if i % 10 == 0:
            print(f"  ...{i}/{len(universe)}", file=sys.stderr)

    if cfg.get("bias") and cfg["bias"] != "both":
        results = [r for r in results if r.bias == cfg["bias"]]

    results.sort(key=lambda r: r.score, reverse=True)
    results = results[: cfg["max_results"]]
    return pd.DataFrame([r.as_row() for r in results])


def run_mtf(cfg: dict) -> pd.DataFrame:
    """Scan en confluence : contexte HTF + déclencheur LTF (cfg['timeframes'])."""
    htf_tf, ltf_tf = cfg["timeframes"]
    ex = data_mod.get_exchange(cfg["exchange"])
    if cfg.get("symbols"):
        universe = cfg["symbols"]
    else:
        universe = data_mod.build_universe(ex, quote=cfg["quote"], top_n=cfg["top"])
        print(f"Univers : {len(universe)} paires — confluence {htf_tf}→{ltf_tf}", file=sys.stderr)

    results: list[MTFResult] = []
    for i, sym in enumerate(universe, 1):
        try:
            df_h = data_mod.fetch_ohlcv(ex, sym, htf_tf, cfg["limit"], cfg["use_cache"])
            df_l = data_mod.fetch_ohlcv(ex, sym, ltf_tf, cfg["limit"], cfg["use_cache"])
            res_h = analyze_symbol(sym, df_h, cfg)
            res_l = analyze_symbol(sym, df_l, cfg)
            m = combine_mtf(sym, htf_tf, ltf_tf, res_h, res_l)
            if m and m.score > 0:
                results.append(m)
        except Exception as e:
            print(f"  [skip] {sym}: {e}", file=sys.stderr)
        if i % 10 == 0:
            print(f"  ...{i}/{len(universe)}", file=sys.stderr)

    if cfg.get("bias") and cfg["bias"] != "both":
        results = [r for r in results if r.bias == cfg["bias"]]
    results.sort(key=lambda r: r.score, reverse=True)
    results = results[: cfg["max_results"]]
    return pd.DataFrame([r.as_row() for r in results])


def run_window(cfg: dict) -> pd.DataFrame:
    """Mode fenêtre : reconnaît une séquence Wyckoff (SC-AR-ST-SOS / BC-AR-ST-SOW)
    sur une fenêtre glissante, avec rappel théorique et justification volume/spread
    par événement. Optionnellement, génère un graphique en TF inférieure par symbole."""
    ex = data_mod.get_exchange(cfg["exchange"])
    universe = cfg["symbols"] or data_mod.build_universe(ex, quote=cfg["quote"], top_n=cfg["top"])
    th = Thresholds(**cfg.get("thresholds", {}))
    lookback = cfg.get("window", 60)

    # Mémo théorie (HTML cliquable) régénéré à chaque analyse, sur les seuils courants.
    from .theory_table import build_theory_html
    memo = build_theory_html(th)
    print(f"→ mémo théorie : {memo}", file=sys.stderr)

    rows: list[dict] = []
    for sym in universe:
        try:
            df = data_mod.fetch_ohlcv(ex, sym, cfg["timeframe"], cfg["limit"], cfg["use_cache"])
            df = add_features(df, vol_ma=cfg["vol_ma"], atr_period=cfg["atr_period"])
            oi = data_mod.fetch_open_interest(sym, cfg["timeframe"], cfg["limit"],
                                              source=cfg.get("oi_source", "binance")) if cfg.get("oi", True) else None
            struct = detect_window_structure(df, lookback=lookback, th=th, oi=oi)
            if not struct.is_valid:
                continue
            for e in struct.events:
                rows.append({
                    "symbol": sym, "schema": struct.bias, "event": e.name,
                    "time": (e.ts + pd.Timedelta(hours=2)).strftime("%d/%m %Hh"),
                    "price": round(e.price, 2), "vol_x": round(e.vol_ratio, 2),
                    "spread_atr": round(e.spread_atr, 2), "clv": round(e.clv, 2),
                    "oi_3h_%": "—" if pd.isna(e.oi_chg) else round(e.oi_chg, 2),
                    "volume/spread → thèse": e.why, "théorie": e.theory,
                })
            if cfg.get("chart"):
                from .plot import plot_window_structure
                out = f"chart_{sym.replace('/', '').lower()}_{cfg['timeframe']}_window.png"
                plot_window_structure(sym, cfg["timeframe"], struct, out, ex=ex,
                                      oi_source=cfg.get("oi_source", "binance"))
                print(f"→ graphique : {out}", file=sys.stderr)
        except Exception as e:
            print(f"  [skip] {sym}: {e}", file=sys.stderr)
    return pd.DataFrame(rows)


def run_dryup(cfg: dict) -> pd.DataFrame:
    """Mode assèchement de l'offre : cherche une consolidation (coil) où l'offre se tarit
    — tests réussis à volume décroissant, spring + test de Phase C, contraction — mesurée
    en unités ATR/ratio (identique 15m/1h/4h). OI lu en **coin**. Une ligne par événement ;
    graphique 3 panneaux optionnel."""
    ex = data_mod.get_exchange(cfg["exchange"])
    # Univers : futures/swap (Bitget & co) si --futures ou venue ≠ binance, sinon spot.
    if cfg["symbols"]:
        universe = cfg["symbols"]
    elif cfg.get("futures") or cfg["exchange"] != "binance":
        universe = data_mod.build_futures_universe(
            ex, quote=cfg["quote"], top_n=cfg["top"],
            include_rwa=cfg.get("rwa", True), only_rwa=cfg.get("only_rwa", False),
            min_vol_musd=cfg.get("min_vol", 0.0), exclude_etf=cfg.get("exclude_etf", True))
        print(f"Univers futures {cfg['exchange']} : {len(universe)} perp "
              f"(RWA={'oui' if cfg.get('rwa', True) else 'non'}, ETF={'non' if cfg.get('exclude_etf', True) else 'oui'}, "
              f"vol≥{cfg.get('min_vol', 0)}M)", file=sys.stderr)
    else:
        universe = data_mod.build_universe(ex, quote=cfg["quote"], top_n=cfg["top"])
    th = Thresholds(**cfg.get("thresholds", {}))
    lookback = cfg.get("dryup", 40)
    bias = cfg["bias"] if cfg["bias"] in ("accumulation", "distribution") else "accumulation"

    from .theory_table import build_theory_html
    memo = build_theory_html(th)
    print(f"→ mémo théorie : {memo}", file=sys.stderr)

    rows: list[dict] = []
    valid: list[tuple] = []          # (score, sym, dry, df) pour grapher les meilleurs
    for i, sym in enumerate(universe, 1):
        try:
            df = data_mod.fetch_ohlcv(ex, sym, cfg["timeframe"], cfg["limit"], cfg["use_cache"])
            df = add_features(df, vol_ma=cfg["vol_ma"], atr_period=cfg["atr_period"])
            oi = None
            if cfg.get("oi", True):
                try:
                    o = data_mod.fetch_oi_ohlc_coin(sym, cfg["timeframe"], cfg["limit"])
                    oi = o["close"].rename("oi").to_frame() if o is not None and len(o) else None
                except Exception:
                    oi = None
            dry = detect_supply_dryup(df, th=th, oi=oi, lookback=lookback, bias=bias)
            if not dry.is_valid:
                continue
            # Régime courant (contexte). Gate CONTRE-TENDANCE optionnel (--regime) : on écarte
            # le long d'accu en régime haussier établi (et le short de distrib en baissier).
            reg = int(market_regime(df).iloc[-1])
            if cfg.get("regime"):
                acc = dry.bias == "accumulation"
                if (reg > 0) if acc else (reg < 0):
                    continue
            valid.append((dry.score, sym, dry, df))
            for e in dry.events:
                rows.append({
                    "symbol": sym, "bias": dry.bias, "score": round(dry.score, 2), "regime": reg,
                    "support": round(dry.support, 6), "resistance": round(dry.resistance, 6),
                    "event": e.name, "time": (e.ts + pd.Timedelta(hours=2)).strftime("%d/%m %Hh"),
                    "vol_x": round(e.vol_ratio, 2), "spread_atr": round(e.spread_atr, 2),
                    "clv": round(e.clv, 2), "oi_3h_%": "—" if pd.isna(e.oi_chg) else round(e.oi_chg, 2),
                    "volume/spread → thèse": e.why,
                })
        except Exception as e:
            print(f"  [skip] {sym}: {e}", file=sys.stderr)
        if len(universe) > 30 and i % 40 == 0:
            print(f"  ...{i}/{len(universe)} ({len(valid)} setups)", file=sys.stderr)

    # Graphes des N meilleurs setups (par score), pas de tous.
    if cfg.get("chart") and valid:
        from .plot import plot_supply_dryup
        for score, sym, dry, df in sorted(valid, key=lambda v: v[0], reverse=True)[: cfg.get("chart_top", 4)]:
            safe = sym.replace("/", "").replace(":", "").lower()
            out = f"chart_{safe}_{cfg['timeframe']}_dryup.png"
            try:
                plot_supply_dryup(sym, cfg["timeframe"], dry, out, ex=ex, df=df)
                print(f"→ graphique : {out}  (score {score:.2f})", file=sys.stderr)
            except Exception as e:
                print(f"  [chart skip] {sym}: {e}", file=sys.stderr)
    return pd.DataFrame(rows)


def main() -> None:
    # Console Windows en cp1252 : on force l'UTF-8 pour les symboles (→, ×, …).
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass

    cfg = {
        "exchange": "binance", "quote": "USDT", "timeframe": "1h", "top": 60,
        "limit": 300, "lookback": 80, "buffer": 5, "vol_ma": 20, "atr_period": 14,
        "max_results": 25, "use_cache": True, "bias": "both", "symbols": [],
        "thresholds": {}, "timeframes": ["4h", "1h"], "window": 60, "oi": True,
        "oi_source": "binance",
    }
    cfg.update(load_config())

    p = argparse.ArgumentParser(description="Wyckoff crypto screener (accumulation/distribution)")
    p.add_argument("--exchange", default=cfg["exchange"])
    p.add_argument("--timeframe", default=cfg["timeframe"], help="1h, 4h, ...")
    p.add_argument("--top", type=int, default=cfg["top"])
    p.add_argument("--symbols", nargs="*", default=cfg["symbols"])
    p.add_argument("--bias", choices=["accumulation", "distribution", "both"], default=cfg["bias"])
    p.add_argument("--max-results", type=int, default=cfg["max_results"])
    p.add_argument("--mtf", action="store_true", help="confluence multi-timeframe (HTF→LTF)")
    p.add_argument("--window", nargs="?", type=int, const=60, default=None,
                   help="mode séquence Wyckoff sur fenêtre glissante (défaut 60 barres)")
    p.add_argument("--dryup", nargs="?", type=int, const=40, default=None,
                   help="mode assèchement de l'offre (coil + tests + spring/Phase C, défaut 40 barres)")
    p.add_argument("--futures", action="store_true",
                   help="univers perp/swap (auto si --exchange ≠ binance ; inclut les RWA)")
    p.add_argument("--min-vol", type=float, default=0.0,
                   help="filtre de liquidité : volume 24h minimum en M USD (futures)")
    p.add_argument("--no-rwa", action="store_true", help="exclut les RWA (actions/métaux/indices)")
    p.add_argument("--only-rwa", action="store_true", help="uniquement les RWA (actions/métaux/indices)")
    p.add_argument("--include-etf", action="store_true", help="réintègre les ETF & produits à levier (exclus par défaut)")
    p.add_argument("--regime", action="store_true",
                   help="filtre de régime CONTRE-TENDANCE : n'affiche les dry-up longs qu'hors régime haussier établi")
    p.add_argument("--chart-top", type=int, default=4, help="nb de graphiques (meilleurs setups) en mode --chart")
    p.add_argument("--chart", action="store_true", help="génère un graphique (bougies TF inférieure)")
    p.add_argument("--no-cache", action="store_true")
    p.add_argument("--no-oi", action="store_true", help="désactive l'Open Interest (confirmation AR + ΔOI)")
    p.add_argument("--oi-source", choices=["binance", "okx", "agg3"], default=cfg["oi_source"],
                   help="source d'OI : binance (défaut, Coinalyze = TradingView, repli OKX), okx (venue unique), agg3 (archive Binance, profondeur historique)")
    p.add_argument("--csv", default="watchlist.csv")
    args = p.parse_args()

    cfg.update(exchange=args.exchange, timeframe=args.timeframe, top=args.top,
               symbols=args.symbols, bias=args.bias, max_results=args.max_results,
               use_cache=not args.no_cache, chart=args.chart, oi=not args.no_oi,
               oi_source=args.oi_source, futures=args.futures, min_vol=args.min_vol,
               rwa=not args.no_rwa, only_rwa=args.only_rwa, chart_top=args.chart_top,
               exclude_etf=not args.include_etf, regime=args.regime)
    if args.window is not None:
        cfg["window"] = args.window
    if args.dryup is not None:
        cfg["dryup"] = args.dryup

    if args.dryup is not None:
        table = run_dryup(cfg)
    elif args.window is not None:
        table = run_window(cfg)
    elif args.mtf:
        table = run_mtf(cfg)
    else:
        table = run(cfg)
    if table.empty:
        print("Aucun setup détecté avec les seuils actuels.")
        return
    with pd.option_context("display.max_rows", None, "display.width", 200):
        print(table.to_string(index=False))
    table.to_csv(args.csv, index=False)
    print(f"\n→ Watchlist écrite dans {args.csv}", file=sys.stderr)


if __name__ == "__main__":
    main()
