"""
backtest.py — Backtest walk-forward des événements Wyckoff.

Méthode (sans lookahead) :
  1. On parcourt l'historique barre par barre. À la barre t, on détecte les
     événements sur la fenêtre df[:t+1] uniquement (features causales).
  2. Si un événement *déclencheur* survient sur la barre courante (bars_ago == 0)
     et qu'aucune position n'est ouverte, on entre à la clôture de t.
        long  : SPRING, SOS, LPS
        short : UTAD, SOW, LPSY
  3. Stop = entrée ∓ stop_atr × ATR(t) ; objectif = entrée ± rr × (distance stop).
     On simule les barres t+1 … t+max_hold ; si stop et objectif sont touchés dans
     la même barre, on suppose le stop d'abord (pessimiste). Sinon sortie au marché
     à max_hold. Résultat exprimé en R (multiples du risque).
  4. Une seule position par symbole à la fois (pas de chevauchement).

Sortie : statistiques par type d'événement (n, win%, R moyen, espérance, profit factor).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .divergence import DivergenceParams, detect_forming_entry
from .events import Thresholds, detect_events
from .features import add_features, detect_trading_range

LONG_EVENTS = {"SPRING", "SOS", "LPS"}
SHORT_EVENTS = {"UTAD", "SOW", "LPSY"}


@dataclass
class BTParams:
    stop_atr: float = 1.0     # distance du stop, en ATR
    rr: float = 2.0           # ratio objectif / risque
    max_hold: int = 30        # barres max en position
    cooldown: int = 0         # barres à ignorer après une sortie
    cost: float = 0.0         # coût par côté (frais+slippage), fraction du notionnel


@dataclass
class Trade:
    symbol: str
    event: str
    direction: str       # "long" | "short"
    entry_i: int
    entry: float
    stop: float
    target: float
    exit_i: int
    exit: float
    r: float             # résultat en multiples de risque
    outcome: str         # "win" | "loss" | "timeout"


def _simulate_exit(feat: pd.DataFrame, t: int, direction: str,
                   entry: float, stop: float, target: float, p: BTParams) -> tuple[int, float, str]:
    risk = abs(entry - stop)
    end = min(t + p.max_hold, len(feat) - 1)
    for j in range(t + 1, end + 1):
        hi, lo = float(feat["high"].iloc[j]), float(feat["low"].iloc[j])
        if direction == "long":
            if lo <= stop:                       # stop d'abord (pessimiste)
                return j, stop, "loss"
            if hi >= target:
                return j, target, "win"
        else:
            if hi >= stop:
                return j, stop, "loss"
            if lo <= target:
                return j, target, "win"
    exit_px = float(feat["close"].iloc[end])
    return end, exit_px, "timeout"


def backtest_features(symbol: str, feat: pd.DataFrame, cfg: dict, p: BTParams,
                      th: Thresholds, entry_start: int | None = None,
                      entry_end: int | None = None) -> list[Trade]:
    """
    Coeur du backtest sur features déjà calculées (réutilisable par l'optimiseur).
    Les entrées sont prises sur les barres [entry_start, entry_end). La détection à
    la barre t n'utilise que df[:t+1] ; les features sont causales (pas de lookahead).
    Un trade est rattaché à la fenêtre de sa *barre d'entrée* (séparation IS/OOS nette).
    """
    warmup = cfg["lookback"] + cfg["buffer"] + cfg["vol_ma"]
    n = len(feat)
    lo = max(warmup, entry_start if entry_start is not None else warmup)
    hi = entry_end if entry_end is not None else n
    trades: list[Trade] = []

    t = lo
    while t < hi:
        sl = feat.iloc[: t + 1]
        tr = detect_trading_range(sl, lookback=cfg["lookback"], buffer=cfg["buffer"])
        atr_t = float(feat["atr"].iloc[t])
        if not tr.is_valid or not atr_t or np.isnan(atr_t):
            t += 1
            continue

        events = detect_events(sl, tr, buffer=cfg["buffer"], th=th)
        fresh = [e for e in events if e.bars_ago == 0 and (e.name in LONG_EVENTS or e.name in SHORT_EVENTS)]
        if not fresh:
            t += 1
            continue

        e = max(fresh, key=lambda x: x.strength)   # déclencheur le plus fort
        direction = "long" if e.name in LONG_EVENTS else "short"
        entry = float(feat["close"].iloc[t])
        risk = p.stop_atr * atr_t
        if direction == "long":
            stop, target = entry - risk, entry + p.rr * risk
        else:
            stop, target = entry + risk, entry - p.rr * risk

        exit_i, exit_px, outcome = _simulate_exit(feat, t, direction, entry, stop, target, p)
        gross = (exit_px - entry) if direction == "long" else (entry - exit_px)
        r = (gross - p.cost * (entry + exit_px)) / risk
        trades.append(Trade(symbol, e.name, direction, t, entry, stop, target,
                            exit_i, exit_px, float(r), outcome))
        t = exit_i + 1 + p.cooldown   # pas de chevauchement
    return trades


def backtest_symbol(symbol: str, df: pd.DataFrame, cfg: dict, p: BTParams) -> list[Trade]:
    feat = add_features(df, vol_ma=cfg["vol_ma"], atr_period=cfg["atr_period"])
    th = Thresholds(**cfg.get("thresholds", {}))
    return backtest_features(symbol, feat, cfg, p, th)


def backtest_entry_features(symbol: str, feat: pd.DataFrame, cfg: dict, p: BTParams,
                            th: Thresholds, params: DivergenceParams,
                            target: str = "t1", long_only: bool = False,
                            entry_start: int | None = None,
                            entry_end: int | None = None) -> list[Trade]:
    """Backtest du mode « entrée au 2ᵉ creux » (detect_forming_entry), sans lookahead.

    À la barre t, on détecte sur df[:t+1] ; si la barre courante est une entrée
    CONFIRMÉE (rejet + divergence dans la zone), on entre à la clôture de t. Stop = juste
    au-delà du 2ᵉ creux. Cible : `target` = "t1" (ligne de cou) ou "t2" (objectif mesuré).
    `long_only` ignore les double tops. Frais `p.cost` par côté. Résultat en R."""
    warmup = cfg["lookback"] + cfg["buffer"] + cfg["vol_ma"]
    n = len(feat)
    lo = max(warmup, entry_start if entry_start is not None else warmup)
    hi = entry_end if entry_end is not None else n
    look = cfg["lookback"] + cfg["buffer"]
    trades: list[Trade] = []

    t = lo
    while t < hi:
        sl = feat.iloc[: t + 1]
        tr = detect_trading_range(sl, lookback=cfg["lookback"], buffer=cfg["buffer"])
        atr_t = float(feat["atr"].iloc[t])
        if not tr.is_valid or not atr_t or np.isnan(atr_t):
            t += 1
            continue

        res = detect_forming_entry(symbol, sl, tr, th=th, params=params, lookback=look)
        if res is None or not res.confirmed:
            t += 1
            continue
        if long_only and res.bias != "accumulation":
            t += 1
            continue

        direction = "long" if res.bias == "accumulation" else "short"
        entry = float(feat["close"].iloc[t])
        stop = res.stop
        tgt = res.target if target == "t1" else res.measured
        risk = abs(entry - stop)
        # garde-fou : géométrie cohérente (stop du bon côté, objectif au-delà de l'entrée)
        ok = (direction == "long" and stop < entry < tgt) or \
             (direction == "short" and tgt < entry < stop)
        if not risk or not ok:
            t += 1
            continue

        exit_i, exit_px, outcome = _simulate_exit(feat, t, direction, entry, stop, tgt, p)
        gross = (exit_px - entry) if direction == "long" else (entry - exit_px)
        r = (gross - p.cost * (entry + exit_px)) / risk
        trades.append(Trade(symbol, res.pattern, direction, t, entry, stop, tgt,
                            exit_i, exit_px, float(r), outcome))
        t = exit_i + 1 + p.cooldown
    return trades


def backtest_entry_symbol(symbol: str, df: pd.DataFrame, cfg: dict, p: BTParams) -> list[Trade]:
    feat = add_features(df, vol_ma=cfg["vol_ma"], atr_period=cfg["atr_period"],
                        rsi_period=cfg.get("divergence", {}).get("rsi_period", 14))
    th = Thresholds(**cfg.get("thresholds", {}))
    params = DivergenceParams(**cfg.get("divergence", {}))
    return backtest_entry_features(symbol, feat, cfg, p, th, params)


def aggregate(trades: list[Trade]) -> pd.DataFrame:
    if not trades:
        return pd.DataFrame()
    rows = []
    df = pd.DataFrame([t.__dict__ for t in trades])
    for event, grp in list(df.groupby("event")) + [("TOUS", df)]:
        wins = grp[grp["r"] > 0]["r"]
        losses = grp[grp["r"] <= 0]["r"]
        pf = wins.sum() / abs(losses.sum()) if losses.sum() != 0 else np.inf
        rows.append({
            "event": event,
            "n": len(grp),
            "win%": round(100 * (grp["r"] > 0).mean(), 1),
            "R_moy": round(grp["r"].mean(), 3),       # espérance par trade
            "R_total": round(grp["r"].sum(), 2),
            "profit_factor": round(pf, 2) if np.isfinite(pf) else "∞",
            "R_max": round(grp["r"].max(), 2),
            "R_min": round(grp["r"].min(), 2),
        })
    out = pd.DataFrame(rows).sort_values("n", ascending=False)
    return out


def run_backtest(cfg: dict, p: BTParams, entry: bool = False) -> tuple[pd.DataFrame, list[Trade]]:
    from . import data as data_mod
    ex = data_mod.get_exchange(cfg["exchange"], mirror=cfg.get("mirror") or None)
    universe = cfg["symbols"] or data_mod.build_universe(ex, quote=cfg["quote"], top_n=cfg["top"])
    fn = backtest_entry_symbol if entry else backtest_symbol
    all_trades: list[Trade] = []
    for sym in universe:
        try:
            df = data_mod.fetch_ohlcv(ex, sym, cfg["timeframe"], cfg["limit"], cfg["use_cache"])
            all_trades += fn(sym, df, cfg, p)
        except Exception as e:
            import sys
            print(f"  [skip] {sym}: {e}", file=sys.stderr)
    return aggregate(all_trades), all_trades


def main() -> None:
    import argparse
    from .cli import load_config

    cfg = {
        "exchange": "binance", "mirror": "", "quote": "USDT", "timeframe": "1h", "top": 60,
        "limit": 1000, "lookback": 80, "buffer": 5, "vol_ma": 20, "atr_period": 14,
        "use_cache": True, "symbols": [], "thresholds": {}, "divergence": {},
    }
    cfg.update(load_config())

    ap = argparse.ArgumentParser(description="Backtest Wyckoff (événements ou entrée 2ᵉ creux)")
    ap.add_argument("--timeframe", default=cfg["timeframe"])
    ap.add_argument("--symbols", nargs="*", default=cfg["symbols"])
    ap.add_argument("--top", type=int, default=cfg["top"])
    ap.add_argument("--limit", type=int, default=cfg["limit"])
    ap.add_argument("--mirror", default=cfg.get("mirror", ""))
    ap.add_argument("--entry", action="store_true",
                    help="backteste le mode « entrée au 2ᵉ creux » (double bottom/top + divergence)")
    ap.add_argument("--stop-atr", type=float, default=1.0)
    ap.add_argument("--rr", type=float, default=2.0)
    ap.add_argument("--max-hold", type=int, default=30)
    ap.add_argument("--csv", default="backtest_trades.csv")
    ap.add_argument("--no-cache", action="store_true")
    args = ap.parse_args()

    cfg.update(timeframe=args.timeframe, symbols=args.symbols, top=args.top,
               limit=args.limit, mirror=args.mirror, use_cache=not args.no_cache)
    p = BTParams(stop_atr=args.stop_atr, rr=args.rr, max_hold=args.max_hold)

    stats, trades = run_backtest(cfg, p, entry=args.entry)
    if stats.empty:
        print("Aucun trade généré sur la période.")
        return
    mode = "entrée 2ᵉ creux (stop sous le creux, cible ligne de cou)" if args.entry \
        else f"stop {p.stop_atr} ATR, objectif {p.rr}R"
    print(f"\nBacktest {cfg['timeframe']} — {mode}, hold max {p.max_hold} barres — "
          f"{len(trades)} trades")
    print(stats.to_string(index=False))
    pd.DataFrame([t.__dict__ for t in trades]).to_csv(args.csv, index=False)


if __name__ == "__main__":
    main()
