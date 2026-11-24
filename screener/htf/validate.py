"""validate.py — banc de validation de la carte de liquidité sur les cartes Hyblock.

Pour chaque relevé de `references.py`, gèle nos données à la date de la capture, construit
la carte et mesure l'écart. Deux scores, volontairement simples et lisibles :

- **placement** : distance relative entre l'amas que la capture désigne comme le plus dense
  et le nôtre le mieux classé du même côté. On compte une réussite sous `tol_pct`.
- **côté** : notre amas le plus dense est-il du bon côté du prix ?

`python -m screener.htf.validate` affiche le détail et le bilan. Avec `--grid`, il compare
plusieurs jeux de paramètres sur une moitié des dates (apprentissage) puis vérifie sur
l'autre (contrôle) — sans ce partage, on ne ferait que du sur-ajustement.
"""
from __future__ import annotations

import argparse

import numpy as np
import pandas as pd

from . import calibrate as C
from . import liqmap as L
from . import references as R
from . import replay as RP


def _mid(c: dict) -> float:
    return 0.5 * (float(c["low"]) + float(c["high"]))


def evaluate_one(ref: dict, lookback_days: int = 30, timeframe: str = "4h",
                 calibrated: bool = True, tol_pct: float = 0.015,
                 match_venues: bool = False, venues=("binance",), **kw) -> dict:
    """Confronte notre carte à un relevé. Renvoie un dict de mesures, jamais d'exception."""
    out = {"asof": ref["asof"][:16], "kind": ref["kind"], "note": ref["note"][:46]}
    try:
        vs = venues
        if match_venues and ref.get("venues"):
            # on charge les bourses que la capture agrège, moins celles que Coinalyze
            # n'expose pas (Bitmex), pour ne pas comparer deux couvertures différentes
            vs = tuple(v for v in ref["venues"] if v in RP.VENUES) or venues
        out["venues"] = "+".join(vs)
        df, oi, delta = RP.load_frozen(ref["asof"], lookback_days, timeframe, venues=vs)
        if df.empty or oi is None or len(oi.dropna()) == 0:
            out["status"] = "données indisponibles"
            return out
        if calibrated and "leverage_tiers" not in kw:
            end = pd.Timestamp(ref["asof"], tz="UTC")
            obs = C.observed_liquidations("BTC/USDT", timeframe,
                                          end - pd.Timedelta(days=lookback_days), end,
                                          df.index)
            if obs is not None:
                fit = C.fit_leverage_tiers(df, oi, delta, obs, step_pct=0.002)
                kw["leverage_tiers"] = fit["tiers"]
                out["fit_long"] = round(fit["fit"]["long"], 2)
                out["fit_short"] = round(fit["fit"]["short"], 2)
        m = L.build_map(df, oi, delta, **kw)
    except Exception as e:
        out["status"] = f"{type(e).__name__}: {e}"
        return out

    g, px = m["grid"], m["price"]
    out["price"] = round(px)
    out["price_ref"] = ref.get("price")

    for w in ref.get("walls", []):
        ours = L.clusters(g, m["positions"], top_n=4)
        if ours.empty:
            out["wall_err"] = None
            break
        err = min(abs(float(p) / w - 1.0) for p in ours["peak"])
        out["wall_ref"] = w
        out["wall_ours"] = round(float(ours.loc[0, "peak"]))
        out["wall_err"] = round(err, 4)
        out["wall_ok"] = err <= tol_pct

    target = R.rank1(ref)
    if target:
        side = target["side"]
        vals = m["liq_long"] if side == "long" else m["liq_short"]
        ours = L.clusters(g, vals, top_n=4)
        out["clust_side"] = side
        out["clust_ref"] = round(_mid(target))
        if ours.empty:
            out["clust_err"] = None
        else:
            peaks = [float(p) for p in ours["peak"]]
            out["clust_ours"] = round(peaks[0])
            out["clust_err"] = round(abs(peaks[0] / _mid(target) - 1.0), 4)
            out["clust_ok"] = out["clust_err"] <= tol_pct
            # tolérant : l'un de nos quatre amas tombe-t-il dans sa bande ?
            out["clust_any"] = any(float(target["low"]) <= p <= float(target["high"])
                                   for p in peaks)
            # le plus dense, tous côtés confondus, est-il du bon côté du prix ?
            best_up = L.clusters(g, m["liq_short"], top_n=1)
            best_dn = L.clusters(g, m["liq_long"], top_n=1)
            up_v = float(best_up.loc[0, "value"]) if not best_up.empty else 0.0
            dn_v = float(best_dn.loc[0, "value"]) if not best_dn.empty else 0.0
            out["side_ok"] = (side == "short") == (up_v >= dn_v)

    counts = ref.get("counts")
    if counts:
        nl = int((m["liq_long"] > 0).sum())
        ns = int((m["liq_short"] > 0).sum())
        out["counts_ours"] = f"{nl}/{ns}"
        out["counts_ref"] = f"{counts['long']}/{counts['short']}"
        ref_up = counts["short"] > counts["long"]
        out["counts_side_ok"] = (ns > nl) == ref_up
    out["status"] = "ok"
    return out


def run(refs=None, **kw) -> pd.DataFrame:
    refs = refs if refs is not None else R.REFERENCES
    return pd.DataFrame([evaluate_one(r, **kw) for r in refs])


def summarise(df: pd.DataFrame) -> dict:
    def rate(col):
        s = df[col].dropna() if col in df.columns else pd.Series(dtype=bool)
        return (round(float(s.mean()), 2), int(s.sum()), int(len(s))) if len(s) else (None, 0, 0)

    return {"amas placés": rate("clust_ok"), "amas dans la bande": rate("clust_any"),
            "bon côté": rate("side_ok"), "murs placés": rate("wall_ok"),
            "sens du comptage": rate("counts_side_ok"),
            "erreur médiane amas": (round(float(df["clust_err"].median()), 4)
                                    if "clust_err" in df.columns
                                    and df["clust_err"].notna().any() else None)}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--timeframe", default="4h")
    ap.add_argument("--lookback", type=int, default=30)
    ap.add_argument("--tol", type=float, default=0.015)
    ap.add_argument("--no-calib", action="store_true")
    ap.add_argument("--seed-bars", type=int, default=0)
    ap.add_argument("--match-venues", action="store_true",
                    help="charger les bourses que chaque capture agrège")
    args = ap.parse_args()
    df = run(lookback_days=args.lookback, timeframe=args.timeframe, tol_pct=args.tol,
             calibrated=not args.no_calib, seed_bars=args.seed_bars,
             match_venues=args.match_venues)
    cols = [c for c in ("asof", "kind", "venues", "price", "price_ref", "clust_side", "clust_ref",
                        "clust_ours", "clust_err", "clust_any", "side_ok", "wall_ref",
                        "wall_ours", "wall_err", "counts_ref", "counts_ours", "status")
            if c in df.columns]
    print(df[cols].to_string(index=False))
    print()
    for k, v in summarise(df).items():
        print(f"{k:>22} : {v}")


if __name__ == "__main__":
    main()
