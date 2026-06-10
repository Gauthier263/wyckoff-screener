"""
optimize.py — Grid-search des seuils avec validation out-of-sample.

Principe :
  1. On balaye une grille de combinaisons de seuils (climax_vol, rr, stop_atr, ...).
  2. Pour chaque combinaison, on backteste sur la partie IN-SAMPLE (début de l'historique)
     et on calcule la métrique d'optimisation.
  3. On retient la meilleure combinaison IN-SAMPLE, puis on mesure sa performance
     OUT-OF-SAMPLE (fin de l'historique, jamais vue pendant l'optimisation).
  4. Si l'edge tient en OOS → robuste. S'il s'effondre → surajustement, on s'abstient.

Anti-surajustement intégré :
  - métrique "robust" = espérance pénalisée par l'erreur d'échantillonnage
  - plancher `min_trades` (les combos trop peu fréquents sont disqualifiés)
  - rapport IS vs OOS + drapeau d'overfit
  - option walk-forward (plusieurs plis glissants) pour une validation plus stricte

Les features sont calculées une seule fois par symbole (causales), puis réutilisées
pour toutes les combinaisons — l'optimiseur reste rapide.
"""
from __future__ import annotations

import itertools
import sys
from dataclasses import dataclass

import numpy as np
import pandas as pd

from .backtest import BTParams, Trade, backtest_features
from .events import Thresholds

# Clés routées vers Thresholds vs BTParams
TH_KEYS = {"climax_vol", "sos_vol", "wide_spread_atr", "narrow_spread_atr",
           "test_vol", "pen_atr", "reclaim_clv"}
BT_KEYS = {"stop_atr", "rr", "max_hold", "cooldown"}

# Grille par défaut : 6 leviers à fort impact (3^6 = 729 combinaisons).
DEFAULT_GRID = {
    "climax_vol": [1.8, 2.0, 2.5],
    "sos_vol": [1.2, 1.3, 1.5],
    "wide_spread_atr": [1.1, 1.3, 1.5],
    "pen_atr": [0.05, 0.10, 0.20],
    "rr": [1.5, 2.0, 3.0],
    "stop_atr": [0.75, 1.0, 1.5],
}


# --------------------------------------------------------------------------- #
# Métriques
# --------------------------------------------------------------------------- #
def trade_stats(trades: list[Trade]) -> dict:
    rs = np.array([t.r for t in trades], dtype=float)
    n = len(rs)
    if n == 0:
        return {"n": 0, "r_moy": 0.0, "win": 0.0, "pf": 0.0, "std": 0.0, "r_total": 0.0}
    wins, losses = rs[rs > 0], rs[rs <= 0]
    pf = wins.sum() / abs(losses.sum()) if losses.sum() != 0 else np.inf
    return {
        "n": n,
        "r_moy": float(rs.mean()),
        "win": float(100 * (rs > 0).mean()),
        "pf": float(pf),
        "std": float(rs.std(ddof=1)) if n > 1 else 0.0,
        "r_total": float(rs.sum()),
    }


def metric_value(trades: list[Trade], kind: str, min_trades: int, z: float = 1.0) -> float:
    """Valeur à maximiser. Disqualifie les combos sous le plancher de trades."""
    s = trade_stats(trades)
    if s["n"] < min_trades:
        return float("-inf")
    if kind == "expectancy":
        return s["r_moy"]
    if kind == "profit_factor":
        return s["pf"] if np.isfinite(s["pf"]) else 99.0
    # "robust" (défaut) : borne basse de l'espérance ~ moyenne - z·erreur-type
    se = s["std"] / np.sqrt(s["n"]) if s["n"] > 0 else 0.0
    return s["r_moy"] - z * se


# --------------------------------------------------------------------------- #
# Grid-search avec split IS / OOS
# --------------------------------------------------------------------------- #
def _split_combo(combo: dict) -> tuple[dict, dict]:
    th_kw = {k: v for k, v in combo.items() if k in TH_KEYS}
    bt_kw = {k: v for k, v in combo.items() if k in BT_KEYS}
    return th_kw, bt_kw


def grid_search(feats: dict[str, pd.DataFrame], cfg: dict, grid: dict | None = None,
                metric: str = "robust", min_trades: int = 30,
                split: float = 0.6, max_hold: int = 30) -> pd.DataFrame:
    grid = grid or DEFAULT_GRID
    keys = list(grid)
    combos = list(itertools.product(*[grid[k] for k in keys]))
    print(f"Grid-search : {len(combos)} combinaisons × {len(feats)} symboles "
          f"(IS={split:.0%} / OOS={1 - split:.0%})", file=sys.stderr)

    rows = []
    for ci, values in enumerate(combos, 1):
        combo = dict(zip(keys, values))
        combo.setdefault("max_hold", max_hold)
        th_kw, bt_kw = _split_combo(combo)
        th, p = Thresholds(**th_kw), BTParams(**bt_kw)

        is_tr, oos_tr = [], []
        for sym, feat in feats.items():
            n = len(feat)
            cut = int(n * split)
            is_tr += backtest_features(sym, feat, cfg, p, th, entry_end=cut)
            oos_tr += backtest_features(sym, feat, cfg, p, th, entry_start=cut)

        is_m = metric_value(is_tr, metric, min_trades)
        is_s, oos_s = trade_stats(is_tr), trade_stats(oos_tr)
        rows.append({
            **combo,
            "is_metric": round(is_m, 4) if np.isfinite(is_m) else None,
            "is_n": is_s["n"], "is_r_moy": round(is_s["r_moy"], 3), "is_win%": round(is_s["win"], 1),
            "oos_n": oos_s["n"], "oos_r_moy": round(oos_s["r_moy"], 3),
            "oos_win%": round(oos_s["win"], 1),
            "oos_pf": round(oos_s["pf"], 2) if np.isfinite(oos_s["pf"]) else None,
        })
        if ci % 100 == 0:
            print(f"  ...{ci}/{len(combos)}", file=sys.stderr)

    df = pd.DataFrame(rows)
    df = df[df["is_metric"].notna()].sort_values("is_metric", ascending=False)
    return df.reset_index(drop=True)


def overfit_report(results: pd.DataFrame) -> dict:
    """Compare le meilleur combo IS à sa performance OOS et lève un drapeau."""
    if results.empty:
        return {"verdict": "aucun combo valide (relâche min_trades ou élargis la grille)"}
    best = results.iloc[0]
    is_r, oos_r = best["is_r_moy"], best["oos_r_moy"]
    if oos_r <= 0:
        verdict = "❌ SURAJUSTEMENT — edge IS qui disparaît (ou s'inverse) en OOS"
    elif oos_r < 0.5 * is_r:
        verdict = "⚠️ FRAGILE — l'edge OOS est nettement plus faible qu'en IS"
    else:
        verdict = "✅ ROBUSTE — l'edge tient hors échantillon"
    # Stabilité : dispersion des paramètres dans le top 10 (top serré = plus fiable)
    top = results.head(10)
    return {
        "verdict": verdict,
        "is_r_moy": is_r, "oos_r_moy": oos_r,
        "oos_win%": best["oos_win%"], "oos_n": int(best["oos_n"]),
        "top10_oos_r_moy_median": round(top["oos_r_moy"].median(), 3),
    }


# --------------------------------------------------------------------------- #
# Walk-forward (validation plus stricte)
# --------------------------------------------------------------------------- #
def walk_forward(feats: dict[str, pd.DataFrame], cfg: dict, grid: dict | None = None,
                 metric: str = "robust", min_trades: int = 20, folds: int = 4,
                 train_frac: float = 0.5, max_hold: int = 30) -> pd.DataFrame:
    """
    Découpe le temps en `folds` plis. Pour chaque pli : optimise sur une fenêtre
    d'entraînement, valide sur la fenêtre suivante (jamais vue). On agrège les
    résultats OOS de tous les plis = simulation d'une recalibration périodique.
    """
    grid = grid or DEFAULT_GRID
    keys = list(grid)
    combos = [dict(zip(keys, v)) for v in itertools.product(*[grid[k] for k in keys])]

    # Bornes temporelles communes (fraction de l'historique, par symbole)
    bounds = np.linspace(0, 1, folds + 1)
    rows = []
    for f in range(folds):
        # train = [bounds[f], split_frac], validate = [split_frac, bounds[f+1]]
        split_frac = bounds[f] + train_frac * (bounds[f + 1] - bounds[f])

        best_combo, best_m = None, float("-inf")
        for combo in combos:
            c = dict(combo); c.setdefault("max_hold", max_hold)
            th, p = Thresholds(**_split_combo(c)[0]), BTParams(**_split_combo(c)[1])
            tr_trades = []
            for sym, feat in feats.items():
                n = len(feat)
                a, b = int(n * bounds[f]), int(n * split_frac)
                tr_trades += backtest_features(sym, feat, cfg, p, th, entry_start=a, entry_end=b)
            m = metric_value(tr_trades, metric, min_trades)
            if m > best_m:
                best_m, best_combo = m, c

        if best_combo is None:
            continue
        th, p = Thresholds(**_split_combo(best_combo)[0]), BTParams(**_split_combo(best_combo)[1])
        val_trades = []
        for sym, feat in feats.items():
            n = len(feat)
            a, b = int(n * split_frac), int(n * bounds[f + 1])
            val_trades += backtest_features(sym, feat, cfg, p, th, entry_start=a, entry_end=b)
        vs = trade_stats(val_trades)
        rows.append({"fold": f + 1, **{k: best_combo[k] for k in keys},
                     "val_n": vs["n"], "val_r_moy": round(vs["r_moy"], 3),
                     "val_win%": round(vs["win"], 1)})
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def _load_feats(cfg: dict) -> dict[str, pd.DataFrame]:
    from . import data as data_mod
    from .features import add_features
    ex = data_mod.get_exchange(cfg["exchange"])
    universe = cfg["symbols"] or data_mod.build_universe(ex, quote=cfg["quote"], top_n=cfg["top"])
    feats = {}
    for sym in universe:
        try:
            df = data_mod.fetch_ohlcv(ex, sym, cfg["timeframe"], cfg["limit"], cfg["use_cache"])
            feats[sym] = add_features(df, vol_ma=cfg["vol_ma"], atr_period=cfg["atr_period"])
        except Exception as e:
            print(f"  [skip] {sym}: {e}", file=sys.stderr)
    return feats


def main() -> None:
    import argparse
    from .cli import load_config

    cfg = {
        "exchange": "binance", "quote": "USDT", "timeframe": "1h", "top": 40,
        "limit": 1500, "lookback": 80, "buffer": 5, "vol_ma": 20, "atr_period": 14,
        "use_cache": True, "symbols": [], "thresholds": {},
    }
    cfg.update(load_config())

    ap = argparse.ArgumentParser(description="Grid-search des seuils Wyckoff (IS/OOS)")
    ap.add_argument("--timeframe", default=cfg["timeframe"])
    ap.add_argument("--symbols", nargs="*", default=cfg["symbols"])
    ap.add_argument("--top", type=int, default=cfg["top"])
    ap.add_argument("--limit", type=int, default=cfg["limit"])
    ap.add_argument("--metric", choices=["robust", "expectancy", "profit_factor"], default="robust")
    ap.add_argument("--min-trades", type=int, default=30)
    ap.add_argument("--split", type=float, default=0.6, help="fraction in-sample")
    ap.add_argument("--walk", type=int, default=0, help="nb de plis walk-forward (0 = split simple)")
    ap.add_argument("--csv", default="optimize_results.csv")
    ap.add_argument("--no-cache", action="store_true")
    args = ap.parse_args()

    cfg.update(timeframe=args.timeframe, symbols=args.symbols, top=args.top,
               limit=args.limit, use_cache=not args.no_cache)

    feats = _load_feats(cfg)
    if not feats:
        print("Aucune donnée chargée."); return

    if args.walk and args.walk > 1:
        wf = walk_forward(feats, cfg, metric=args.metric, min_trades=args.min_trades, folds=args.walk)
        print("\nWalk-forward (performance OOS par pli) :")
        print(wf.to_string(index=False))
        if not wf.empty:
            print(f"\nR moyen OOS agrégé sur les plis : {wf['val_r_moy'].mean():.3f}")
        return

    results = grid_search(feats, cfg, metric=args.metric,
                          min_trades=args.min_trades, split=args.split)
    if results.empty:
        print("Aucun combo au-dessus du plancher de trades."); return

    print("\nTop 10 combinaisons (classées sur la métrique IN-SAMPLE) :")
    print(results.head(10).to_string(index=False))
    rep = overfit_report(results)
    print("\n--- Verdict out-of-sample ---")
    for k, v in rep.items():
        print(f"  {k}: {v}")
    results.to_csv(args.csv, index=False)
    print(f"\n→ Grille complète dans {args.csv} (inspecte la stabilité du top)", file=sys.stderr)


if __name__ == "__main__":
    main()
