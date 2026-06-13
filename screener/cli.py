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
from .divergence import DivergenceParams, detect_double_divergence
from .events import Thresholds, detect_events
from .features import add_features, detect_trading_range, swing_points
from .mtf import MTFResult, combine_mtf
from .score import SymbolResult, score_symbol
from .window import detect_window_structure


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
    ex = data_mod.get_exchange(cfg["exchange"], mirror=cfg.get("mirror") or None)
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
    ex = data_mod.get_exchange(cfg["exchange"], mirror=cfg.get("mirror") or None)
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
    ex = data_mod.get_exchange(cfg["exchange"], mirror=cfg.get("mirror") or None)
    universe = cfg["symbols"] or data_mod.build_universe(ex, quote=cfg["quote"], top_n=cfg["top"])
    th = Thresholds(**cfg.get("thresholds", {}))
    lookback = cfg.get("window", 30)

    rows: list[dict] = []
    for sym in universe:
        try:
            df = data_mod.fetch_ohlcv(ex, sym, cfg["timeframe"], cfg["limit"], cfg["use_cache"])
            df = add_features(df, vol_ma=cfg["vol_ma"], atr_period=cfg["atr_period"])
            struct = detect_window_structure(df, lookback=lookback, th=th)
            if not struct.is_valid:
                continue
            for e in struct.events:
                rows.append({
                    "symbol": sym, "schema": struct.bias, "event": e.name,
                    "time": (e.ts + pd.Timedelta(hours=2)).strftime("%d/%m %Hh"),
                    "price": round(e.price, 2), "vol_x": round(e.vol_ratio, 2),
                    "spread_atr": round(e.spread_atr, 2), "clv": round(e.clv, 2),
                    "volume/spread → thèse": e.why, "théorie": e.theory,
                })
            if cfg.get("chart"):
                from .plot import plot_window_structure
                out = f"chart_{sym.replace('/', '').lower()}_{cfg['timeframe']}_window.png"
                plot_window_structure(sym, cfg["timeframe"], struct, out, ex=ex)
                print(f"→ graphique : {out}", file=sys.stderr)
        except Exception as e:
            print(f"  [skip] {sym}: {e}", file=sys.stderr)
    return pd.DataFrame(rows)


def run_divergence(cfg: dict) -> pd.DataFrame:
    """Mode double creux / double sommet + divergence RSI : paires en consolidation
    (plage ouverte par un climax) amorçant un double bottom/top avec divergence RSI."""
    ex = data_mod.get_exchange(cfg["exchange"], mirror=cfg.get("mirror") or None)
    universe = cfg["symbols"] or data_mod.build_universe(ex, quote=cfg["quote"], top_n=cfg["top"])
    th = Thresholds(**cfg.get("thresholds", {}))
    params = DivergenceParams(**cfg.get("divergence", {}))
    look = cfg["lookback"] + cfg["buffer"]

    results = []
    for i, sym in enumerate(universe, 1):
        try:
            df = data_mod.fetch_ohlcv(ex, sym, cfg["timeframe"], cfg["limit"], cfg["use_cache"])
            if df is None or len(df) < cfg["lookback"] + cfg["buffer"] + cfg["vol_ma"]:
                continue
            df = add_features(df, vol_ma=cfg["vol_ma"], atr_period=cfg["atr_period"],
                              rsi_period=params.rsi_period)
            tr = detect_trading_range(df, lookback=cfg["lookback"], buffer=cfg["buffer"])
            res = detect_double_divergence(sym, df, tr, th=th, params=params, lookback=look)
            if res is None:
                continue
            if cfg.get("bias") and cfg["bias"] != "both" and res.bias != cfg["bias"]:
                continue
            results.append(res)
        except Exception as e:
            print(f"  [skip] {sym}: {e}", file=sys.stderr)
        if i % 10 == 0:
            print(f"  ...{i}/{len(universe)}", file=sys.stderr)

    results.sort(key=lambda r: r.strength, reverse=True)
    results = results[: cfg["max_results"]]

    if cfg.get("chart") and results:
        from .plot import plot_double_divergence
        for r in results:
            out = f"chart_{r.symbol.replace('/', '').lower()}_{cfg['timeframe']}_divergence.png"
            try:
                plot_double_divergence(r.symbol, cfg["timeframe"], r, out, ex=ex,
                                       rsi_period=params.rsi_period)
                print(f"→ graphique : {out}", file=sys.stderr)
            except Exception as e:
                print(f"  [chart skip] {r.symbol}: {e}", file=sys.stderr)

    return pd.DataFrame([r.as_row() for r in results])


def main() -> None:
    # Console Windows en cp1252 : on force l'UTF-8 pour les symboles (→, ×, …).
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass

    cfg = {
        "exchange": "binance", "mirror": "", "quote": "USDT", "timeframe": "1h", "top": 60,
        "limit": 300, "lookback": 80, "buffer": 5, "vol_ma": 20, "atr_period": 14,
        "max_results": 25, "use_cache": True, "bias": "both", "symbols": [],
        "thresholds": {}, "divergence": {}, "timeframes": ["4h", "1h"], "window": 30,
    }
    cfg.update(load_config())

    p = argparse.ArgumentParser(description="Wyckoff crypto screener (accumulation/distribution)")
    p.add_argument("--exchange", default=cfg["exchange"])
    p.add_argument("--mirror", default=cfg["mirror"],
                   help="hôte miroir des données publiques Binance (ex. data-api.binance.vision)")
    p.add_argument("--timeframe", default=cfg["timeframe"], help="1h, 4h, ...")
    p.add_argument("--top", type=int, default=cfg["top"])
    p.add_argument("--symbols", nargs="*", default=cfg["symbols"])
    p.add_argument("--bias", choices=["accumulation", "distribution", "both"], default=cfg["bias"])
    p.add_argument("--max-results", type=int, default=cfg["max_results"])
    p.add_argument("--mtf", action="store_true", help="confluence multi-timeframe (HTF→LTF)")
    p.add_argument("--window", nargs="?", type=int, const=30, default=None,
                   help="mode séquence Wyckoff sur fenêtre glissante (défaut 30 barres)")
    p.add_argument("--divergence", action="store_true",
                   help="double creux/sommet + divergence RSI dans une plage ouverte par un climax")
    p.add_argument("--chart", action="store_true", help="génère un graphique (bougies TF inférieure)")
    p.add_argument("--no-cache", action="store_true")
    p.add_argument("--csv", default="watchlist.csv")
    args = p.parse_args()

    cfg.update(exchange=args.exchange, mirror=args.mirror, timeframe=args.timeframe,
               top=args.top, symbols=args.symbols, bias=args.bias,
               max_results=args.max_results, use_cache=not args.no_cache, chart=args.chart)
    if args.window is not None:
        cfg["window"] = args.window

    if args.divergence:
        table = run_divergence(cfg)
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
