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

from .events import Thresholds, detect_events
from .features import add_features, detect_trading_range, market_regime

LONG_EVENTS = {"SPRING", "SOS", "LPS"}
SHORT_EVENTS = {"UTAD", "SOW", "LPSY"}


@dataclass
class BTParams:
    stop_atr: float = 1.0     # distance du stop, en ATR
    rr: float = 2.0           # ratio objectif / risque
    max_hold: int = 30        # barres max en position
    cooldown: int = 0         # barres à ignorer après une sortie


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
    score: float = float("nan")   # score du setup (dryup) ; NaN pour les événements


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
        r = ((exit_px - entry) if direction == "long" else (entry - exit_px)) / risk
        trades.append(Trade(symbol, e.name, direction, t, entry, stop, target,
                            exit_i, exit_px, float(r), outcome))
        t = exit_i + 1 + p.cooldown   # pas de chevauchement
    return trades


def backtest_symbol(symbol: str, df: pd.DataFrame, cfg: dict, p: BTParams) -> list[Trade]:
    feat = add_features(df, vol_ma=cfg["vol_ma"], atr_period=cfg["atr_period"])
    th = Thresholds(**cfg.get("thresholds", {}))
    return backtest_features(symbol, feat, cfg, p, th)


def backtest_dryup_features(symbol: str, feat: pd.DataFrame, cfg: dict, p: BTParams,
                            th: Thresholds, entry_start: int | None = None,
                            entry_end: int | None = None, score_min: float = 0.60,
                            bias: str = "accumulation", regime=None) -> list[Trade]:
    """Backtest de l'assèchement de l'offre (long en accumulation / short en distribution).

    À la barre t, on détecte `detect_supply_dryup` sur `feat[:t+1]` (causal, pas de lookahead).
    Setup valide + score ≥ `score_min` → entrée à la clôture de t. Le stop est **structurel** :
    juste sous le support / le low du spring (invalidation du coil), avec un tampon `stop_atr`
    en ATR ; objectif = entrée ± rr × risque. Une position à la fois, sans chevauchement.
    """
    from .window import detect_supply_dryup
    lookback = cfg.get("dryup", 40)
    warmup = lookback + cfg["vol_ma"] + cfg["atr_period"]
    n = len(feat)
    lo = max(warmup, entry_start if entry_start is not None else warmup)
    hi = entry_end if entry_end is not None else n
    acc = bias == "accumulation"
    trades: list[Trade] = []

    t = lo
    while t < hi:
        sl = feat.iloc[: t + 1]
        atr_t = float(feat["atr"].iloc[t])
        if not atr_t or np.isnan(atr_t):
            t += 1
            continue
        # Filtre de régime (CONTRE-TENDANCE) : le dry-up est un signal de RETOURNEMENT —
        # l'accumulation se fait en fin de baisse, pas en tendance haussière établie. On saute
        # donc le long quand le régime est déjà franchement haussier (et le short en baissier).
        # Validé sur Bitget : ce sens redresse l'espérance IS (le sens inverse la dégrade).
        if regime is not None:
            rt = int(regime.iloc[t])
            if (rt > 0) if acc else (rt < 0):
                t += 1
                continue
        d = detect_supply_dryup(sl, th=th, lookback=lookback, bias=bias)
        if not d.is_valid or d.score < score_min:
            t += 1
            continue

        entry = float(feat["close"].iloc[t])
        if acc:
            spring_ext = d.spring.bar_low if d.spring else d.support
            stop = min(d.support, spring_ext) - p.stop_atr * atr_t
            direction = "long"
        else:
            spring_ext = d.spring.bar_high if d.spring else d.resistance
            stop = max(d.resistance, spring_ext) + p.stop_atr * atr_t
            direction = "short"
        risk = abs(entry - stop)
        if risk <= 0:
            t += 1
            continue
        target = entry + p.rr * risk if acc else entry - p.rr * risk

        exit_i, exit_px, outcome = _simulate_exit(feat, t, direction, entry, stop, target, p)
        r = ((exit_px - entry) if acc else (entry - exit_px)) / risk
        trades.append(Trade(symbol, "DRYUP", direction, t, entry, stop, target,
                            exit_i, exit_px, float(r), outcome, float(d.score)))
        t = exit_i + 1 + p.cooldown
    return trades


def backtest_dryup_symbol(symbol: str, df: pd.DataFrame, cfg: dict, p: BTParams,
                          score_min: float = 0.60, oos: float = 0.0,
                          bias: str = "accumulation", use_regime: bool = False,
                          regime_ma: int = 50) -> tuple[list[Trade], list[Trade]]:
    """Renvoie (trades_IS, trades_OOS). `oos`=0 → tout dans IS. Split temporel par symbole :
    IS = barres d'entrée [warmup, split), OOS = [split, n). `use_regime` active le filtre de
    contexte CONTRE-TENDANCE (pas de long d'accu en régime haussier établi), causal, même df."""
    feat = add_features(df, vol_ma=cfg["vol_ma"], atr_period=cfg["atr_period"])
    th = Thresholds(**cfg.get("thresholds", {}))
    reg = market_regime(feat, ma=regime_ma) if use_regime else None
    n = len(feat)
    if oos <= 0:
        return backtest_dryup_features(symbol, feat, cfg, p, th, score_min=score_min,
                                       bias=bias, regime=reg), []
    split = int((1 - oos) * n)
    is_tr = backtest_dryup_features(symbol, feat, cfg, p, th, entry_end=split,
                                    score_min=score_min, bias=bias, regime=reg)
    oos_tr = backtest_dryup_features(symbol, feat, cfg, p, th, entry_start=split,
                                     score_min=score_min, bias=bias, regime=reg)
    return is_tr, oos_tr


def aggregate_by_score(trades: list[Trade],
                       buckets=((0.60, 0.70), (0.70, 0.75), (0.75, 1.01))) -> pd.DataFrame:
    """Ventile les trades par tranche de score (le score est le signal de qualité du dryup)."""
    if not trades:
        return pd.DataFrame()
    df = pd.DataFrame([t.__dict__ for t in trades])
    rows = []
    for blo, bhi in buckets:
        g = df[(df["score"] >= blo) & (df["score"] < bhi)]
        if not len(g):
            continue
        wins, losses = g[g["r"] > 0]["r"], g[g["r"] <= 0]["r"]
        pf = wins.sum() / abs(losses.sum()) if losses.sum() != 0 else np.inf
        rows.append({
            "score": f"[{blo:.2f},{bhi:.2f})", "n": len(g),
            "win%": round(100 * (g["r"] > 0).mean(), 1),
            "R_moy": round(g["r"].mean(), 3), "R_total": round(g["r"].sum(), 2),
            "profit_factor": round(pf, 2) if np.isfinite(pf) else "∞",
        })
    return pd.DataFrame(rows)


def run_backtest_dryup(cfg: dict, p: BTParams, score_min: float = 0.60,
                       oos: float = 0.0, bias: str = "accumulation"
                       ) -> tuple[list[Trade], list[Trade]]:
    """Backtest dryup sur tout l'univers. Renvoie (trades_IS, trades_OOS)."""
    from . import data as data_mod
    ex = data_mod.get_exchange(cfg["exchange"])
    universe = cfg["symbols"] or data_mod.build_universe(ex, quote=cfg["quote"], top_n=cfg["top"])
    is_all: list[Trade] = []
    oos_all: list[Trade] = []
    for sym in universe:
        try:
            df = data_mod.fetch_ohlcv(ex, sym, cfg["timeframe"], cfg["limit"], cfg["use_cache"])
            # exclut stables/pegs (ne markupent pas) : volatilité quasi nulle
            if df["close"].pct_change().abs().median() < 0.003:
                continue
            it, ot = backtest_dryup_symbol(sym, df, cfg, p, score_min=score_min, oos=oos, bias=bias)
            is_all += it
            oos_all += ot
        except Exception as e:
            import sys
            print(f"  [skip] {sym}: {e}", file=sys.stderr)
    return is_all, oos_all


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


def run_backtest(cfg: dict, p: BTParams) -> tuple[pd.DataFrame, list[Trade]]:
    from . import data as data_mod
    ex = data_mod.get_exchange(cfg["exchange"])
    universe = cfg["symbols"] or data_mod.build_universe(ex, quote=cfg["quote"], top_n=cfg["top"])
    all_trades: list[Trade] = []
    for sym in universe:
        try:
            df = data_mod.fetch_ohlcv(ex, sym, cfg["timeframe"], cfg["limit"], cfg["use_cache"])
            all_trades += backtest_symbol(sym, df, cfg, p)
        except Exception as e:
            import sys
            print(f"  [skip] {sym}: {e}", file=sys.stderr)
    return aggregate(all_trades), all_trades


def main() -> None:
    import argparse
    from .cli import load_config

    cfg = {
        "exchange": "binance", "quote": "USDT", "timeframe": "1h", "top": 60,
        "limit": 1000, "lookback": 80, "buffer": 5, "vol_ma": 20, "atr_period": 14,
        "use_cache": True, "symbols": [], "thresholds": {},
    }
    cfg.update(load_config())

    ap = argparse.ArgumentParser(description="Backtest des événements Wyckoff")
    ap.add_argument("--timeframe", default=cfg["timeframe"])
    ap.add_argument("--symbols", nargs="*", default=cfg["symbols"])
    ap.add_argument("--top", type=int, default=cfg["top"])
    ap.add_argument("--limit", type=int, default=cfg["limit"])
    ap.add_argument("--stop-atr", type=float, default=1.0,
                    help="tampon du stop en ATR (dryup : sous le support/spring)")
    ap.add_argument("--rr", type=float, default=2.0)
    ap.add_argument("--max-hold", type=int, default=30)
    ap.add_argument("--dryup", action="store_true", help="backtest du détecteur d'assèchement de l'offre")
    ap.add_argument("--score-min", type=float, default=0.60, help="score minimum du setup dryup")
    ap.add_argument("--dryup-lookback", type=int, default=40)
    ap.add_argument("--oos", type=float, default=0.0, help="fraction OOS (ex. 0.3) → split IS/OOS temporel")
    ap.add_argument("--bias", choices=["accumulation", "distribution"], default="accumulation")
    ap.add_argument("--csv", default="backtest_trades.csv")
    ap.add_argument("--no-cache", action="store_true")
    args = ap.parse_args()

    cfg.update(timeframe=args.timeframe, symbols=args.symbols, top=args.top,
               limit=args.limit, use_cache=not args.no_cache, dryup=args.dryup_lookback)
    p = BTParams(stop_atr=args.stop_atr, rr=args.rr, max_hold=args.max_hold)

    if args.dryup:
        is_tr, oos_tr = run_backtest_dryup(cfg, p, score_min=args.score_min, oos=args.oos, bias=args.bias)
        hdr = (f"\nBacktest DRYUP {cfg['timeframe']} ({args.bias}) — stop support−{p.stop_atr} ATR, "
               f"objectif {p.rr}R, hold max {p.max_hold}, score≥{args.score_min}")
        print(hdr)
        if args.oos > 0:
            for lbl, tr in (("IN-SAMPLE", is_tr), (f"OUT-OF-SAMPLE ({args.oos:.0%})", oos_tr)):
                print(f"\n=== {lbl} — {len(tr)} trades ===")
                if tr:
                    print(aggregate(tr).to_string(index=False))
                    print("par score :"); print(aggregate_by_score(tr).to_string(index=False))
        else:
            trades = is_tr
            print(f"— {len(trades)} trades")
            if trades:
                print(aggregate(trades).to_string(index=False))
                print("\npar tranche de score :"); print(aggregate_by_score(trades).to_string(index=False))
            pd.DataFrame([t.__dict__ for t in trades]).to_csv(args.csv, index=False)
        return

    stats, trades = run_backtest(cfg, p)
    if stats.empty:
        print("Aucun trade généré sur la période.")
        return
    print(f"\nBacktest {cfg['timeframe']} — stop {p.stop_atr} ATR, objectif {p.rr}R, "
          f"hold max {p.max_hold} barres — {len(trades)} trades")
    print(stats.to_string(index=False))
    pd.DataFrame([t.__dict__ for t in trades]).to_csv(args.csv, index=False)


if __name__ == "__main__":
    main()
