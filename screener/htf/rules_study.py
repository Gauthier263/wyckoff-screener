"""rules_study.py — mesurer les règles de structure sur l'historique, au lieu de les croire.

Chaque règle reprise de CrypNuevo est une affirmation statistique déguisée. Ce module les
teste sur l'historique BTC complet, en 4h et en 1D :

1. **Remplissage des mèches** — « Long wicks tend to fill sooner rather than later, at
   least the 50 % level. » Quelle proportion se remplit vraiment ? En combien de barres ?
   La taille de la mèche change-t-elle quelque chose ? Un remplissage à 50 % annonce-t-il
   le 100 % ?
2. **Déviation de range** — une sortie suivie d'un retour dedans mène-t-elle vraiment au
   milieu du range plus souvent qu'une cassure installée ?
3. **Acceptance** — après deux clôtures au-delà d'un niveau, le prix continue-t-il, ou
   revient-il ? Autrement dit, l'acceptance vaut-elle mieux qu'une mèche comme signal ?

La sortie est un tableau de taux et de délais, avec le nombre de cas. Une règle mesurée
sur moins d'une trentaine de cas n'est pas un résultat : le tableau affiche `n` pour qu'on
s'en souvienne.

`python -m screener.htf.rules_study --timeframe 4h`
"""
from __future__ import annotations

import argparse

import numpy as np
import pandas as pd

from ..features import atr
from . import structure as S


def wilson(k: int, n: int, z: float = 1.96) -> tuple:
    """Intervalle de confiance à 95 % d'une proportion (méthode de Wilson) — pur.

    Un taux sans son intervalle n'est pas un résultat : 1,00 sur 2 cas et 0,88 sur 128
    s'affichent pareil et ne valent pas la même chose.
    """
    if n <= 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    marge = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, centre - marge), min(1.0, centre + marge))


def _rate(mask: pd.Series) -> str:
    """« 0,88 [0,81-0,93] » — le taux et son intervalle, toujours ensemble."""
    k, n = int(mask.sum()), int(len(mask))
    if n == 0:
        return "-"
    lo, hi = wilson(k, n)
    return f"{k / n:.2f} [{lo:.2f}-{hi:.2f}]"


# --------------------------------------------------------------------- mèches

def study_wick_precedence(df: pd.DataFrame, min_atr: float = 1.0, atr_period: int = 14,
                          target_atr: float = 2.0, horizon: int = 120,
                          level: str = "half", control_offset: int = 40) -> pd.DataFrame:
    """La règle réelle de CrypNuevo : le retracement de la mèche **précède** le mouvement.

    Ce n'est pas « la mèche finira par être remplie » — ça, c'est seulement dire que le
    prix revient sur ses pas. C'est une règle d'**ordre des événements**, conditionnelle au
    scénario :

    > Dans une hypothèse d'accumulation, si le prix doit monter, il ne montera pas avant
    > d'avoir retracé 50 % (ou 100 %) de la mèche basse. Inversement en distribution.

    On mesure donc, pour chaque longue mèche, lequel des deux arrive en premier :

    - **A**, le retracement : le prix revient toucher le niveau 50 % (ou 100 %) de la mèche
      — pour une mèche **basse**, en redescendant ; pour une mèche **haute**, en remontant ;
    - **B**, le mouvement directionnel : le prix progresse de `target_atr` ATR dans le sens
      attendu par le scénario — vers le **haut** après une mèche basse (accumulation), vers
      le **bas** après une mèche haute (distribution).

    La règle est vraie si A précède B nettement plus souvent que l'inverse. Encore faut-il
    un **témoin** valable. Un niveau « à la même distance, côté opposé » ne convient pas
    ici : pour une mèche basse, il retombe exactement sur le niveau testé. Le témoin est
    donc une **barre ordinaire antérieure** (sans longue mèche), à laquelle on applique le
    même écart relatif, exprimé en ATR. Si la mèche n'apporte rien, une barre quelconque
    donne le même ordre pour un niveau placé aussi loin.

    `dist_atr` rapporte cet écart : pour une mèche de 1 à 1,5 ATR, le niveau 50 % n'est
    qu'à une fraction d'ATR du cours, donc touché presque immédiatement. La règle n'a de
    portée que si le niveau est **loin**.

    Les barres où A et B surviennent toutes deux sont comptées à part (`indéterminé`) :
    sans données intra-barre, on ne peut pas savoir laquelle est venue en premier, et
    trancher au hasard fausserait le résultat.
    """
    a = atr(df, atr_period)
    body_hi = df[["open", "close"]].max(axis=1)
    body_lo = df[["open", "close"]].min(axis=1)
    rows = []
    n = len(df)
    for direction, ratio_s, base_s, tip_s in (
            ("haute", (df["high"] - body_hi) / a, body_hi, df["high"]),
            ("basse", (body_lo - df["low"]) / a, body_lo, df["low"])):
        for i in range(atr_period, n - horizon):
            r = float(ratio_s.iloc[i])
            if not np.isfinite(r) or r < min_atr:
                continue
            base, tip = float(base_s.iloc[i]), float(tip_s.iloc[i])
            retrace = 0.5 * (base + tip) if level == "half" else tip
            close = float(df["close"].iloc[i])
            span = float(a.iloc[i])
            if not np.isfinite(span) or span <= 0:
                continue
            fut = df.iloc[i + 1:i + 1 + horizon]
            if fut.empty:
                continue

            dist_atr = abs(close - retrace) / span
            if direction == "basse":
                # accumulation : retracer vers le bas, puis monter
                hit_a = fut["low"] <= retrace
                hit_b = fut["high"] >= close + target_atr * span
            else:
                # distribution : retracer vers le haut, puis descendre
                hit_a = fut["high"] >= retrace
                hit_b = fut["low"] <= close - target_atr * span

            ia = int(np.argmax(hit_a.to_numpy())) if hit_a.any() else None
            ib = int(np.argmax(hit_b.to_numpy())) if hit_b.any() else None

            # Témoin : une barre ordinaire antérieure, sans longue mèche, avec le même
            # écart relatif et la même cible. Elle contrôle à la fois la distance et la
            # période de marché.
            isham = ishamb = None
            j = i - control_offset
            if j >= atr_period and float(ratio_s.iloc[j]) < min_atr:
                cj, sj = float(df["close"].iloc[j]), float(a.iloc[j])
                if np.isfinite(sj) and sj > 0:
                    fj = df.iloc[j + 1:j + 1 + horizon]
                    if not fj.empty:
                        if direction == "basse":
                            sa = fj["low"] <= cj - dist_atr * sj
                            sb = fj["high"] >= cj + target_atr * sj
                        else:
                            sa = fj["high"] >= cj + dist_atr * sj
                            sb = fj["low"] <= cj - target_atr * sj
                        isham = int(np.argmax(sa.to_numpy())) if sa.any() else None
                        ishamb = int(np.argmax(sb.to_numpy())) if sb.any() else None

            if ib is None:
                verdict = "pas de mouvement"          # le scénario ne s'est pas réalisé
            elif ia is None:
                verdict = "mouvement sans retracement"
            elif ia < ib:
                verdict = "retracement d'abord"
            elif ia > ib:
                verdict = "mouvement d'abord"
            else:
                verdict = "indéterminé"               # même barre : on ne tranche pas

            if ishamb is None:
                verdict_sham = "pas de mouvement"
            elif isham is None:
                verdict_sham = "mouvement sans retracement"
            elif isham < ishamb:
                verdict_sham = "retracement d'abord"
            elif isham > ishamb:
                verdict_sham = "mouvement d'abord"
            else:
                verdict_sham = "indéterminé"

            rows.append({"direction": direction, "at": df.index[i], "atr_ratio": r,
                         "dist_atr": dist_atr, "verdict": verdict, "témoin": verdict_sham,
                         "barres_retracement": ia, "barres_mouvement": ib})
    return pd.DataFrame(rows)


def summarise_precedence(w: pd.DataFrame) -> pd.DataFrame:
    """Part des cas où le retracement précède le mouvement, mèche contre témoin.

    Seuls les cas où le mouvement a eu lieu **et** où l'ordre est tranchable entrent dans
    le calcul : les « pas de mouvement » ne disent rien de la règle, et les « indéterminé »
    ne sont pas départageables sans données intra-barre.
    """
    if w.empty:
        return pd.DataFrame()
    bins = [1.0, 1.5, 2.0, np.inf]
    labels = ["1-1.5 ATR", "1.5-2 ATR", ">2 ATR"]
    w = w.assign(taille=pd.cut(w["atr_ratio"], bins, labels=labels, right=False))
    tranchable = {"retracement d'abord", "mouvement d'abord", "mouvement sans retracement"}
    out = []
    for (direction, taille), g in w.groupby(["direction", "taille"], observed=True):
        dec = g[g["verdict"].isin(tranchable)]
        dec_s = g[g["témoin"].isin(tranchable)]
        if dec.empty:
            continue
        out.append({
            "mèche": direction, "scénario": ("accumulation" if direction == "basse"
                                             else "distribution"),
            "taille": str(taille), "n": len(dec),
            "écart (ATR)": round(float(g["dist_atr"].median()), 2),
            "retracement d'abord": _rate(dec["verdict"] == "retracement d'abord"),
            "témoin": _rate(dec_s["témoin"] == "retracement d'abord"),
            "barres méd.": (int(dec.loc[dec["verdict"] == "retracement d'abord",
                                        "barres_retracement"].median())
                            if (dec["verdict"] == "retracement d'abord").any() else None),
            "sans mouvement": int((g["verdict"] == "pas de mouvement").sum()),
            "indéterminé": int((g["verdict"] == "indéterminé").sum()),
        })
    return pd.DataFrame(out)


# --------------------------------------------------------------------- déviations

def study_deviations(df: pd.DataFrame, window: int = 180, step: "int | None" = None,
                     horizon: int = 60, max_bars_out: int = 10) -> pd.DataFrame:
    """Après une déviation de range, le prix rejoint-il le milieu du range ?

    Comparaison avec le cas opposé : une sortie qui **s'installe** (cassure). Si la
    déviation ne fait pas mieux, la règle « une sortie suivie d'un retour est un signal de
    réévaluation » ne vaut rien.
    """
    # Le pas doit valoir au moins l'horizon : avec un pas plus court, deux observations
    # partagent presque tout leur futur et ne sont donc pas indépendantes. Un pas de 6 sur
    # un horizon de 60 gonflait l'effectif d'un facteur dix et donnait une fausse
    # confiance.
    step = int(step or horizon)
    rows = []
    for i in range(window, len(df) - horizon, step):
        hist = df.iloc[i - window:i]
        rng = S.find_range(hist)
        if rng is None or rng.height_pct < 0.03:
            continue
        dev = S.detect_deviation(hist.tail(40), rng, max_bars_out=max_bars_out)
        out_mask_low = hist["low"].tail(15) < rng.low
        out_mask_high = hist["high"].tail(15) > rng.high
        installed = (int(out_mask_low.sum()) > max_bars_out
                     or int(out_mask_high.sum()) > max_bars_out)
        if dev is None and not installed:
            continue
        fut = df.iloc[i:i + horizon]
        # « rejoindre le milieu » dépend du côté d'où l'on vient : sous le milieu il faut
        # monter jusqu'à lui, au-dessus il faut y redescendre. (L'écriture condensée
        # précédente dépendait de la précédence de `and`/`or`/`if`, illisible et fragile.)
        if float(df["close"].iloc[i]) < rng.mid:
            reached_mid = bool((fut["high"] >= rng.mid).any())
        else:
            reached_mid = bool((fut["low"] <= rng.mid).any())
        rows.append({
            "at": df.index[i],
            "cas": ("déviation " + dev.side) if dev is not None else "cassure installée",
            "reclaimed": bool(dev.reclaimed) if dev is not None else False,
            "mid atteint": reached_mid,
            "rendement %": float(fut["close"].iloc[-1] / df["close"].iloc[i] - 1.0) * 100,
        })
    return pd.DataFrame(rows)


def summarise_deviations(d: pd.DataFrame) -> pd.DataFrame:
    if d.empty:
        return pd.DataFrame()
    out = []
    for cas, g in d.groupby("cas"):
        out.append({"cas": cas, "n": len(g),
                    "milieu atteint": _rate(g["mid atteint"]),
                    "rendement médian %": round(float(g["rendement %"].median()), 2)})
    return pd.DataFrame(out)


# --------------------------------------------------------------------- acceptance

def study_acceptance(df: pd.DataFrame, window: int = 180, step: "int | None" = None,
                     horizon: int = 30, min_closes: int = 2) -> pd.DataFrame:
    """Une acceptance (clôtures au-delà) tient-elle mieux qu'une simple mèche ?

    Pour chaque borne de range, on classe l'état courant en « acceptance » ou « mèche
    seule », puis on regarde ce que fait le prix ensuite. C'est le test de la règle qui
    manquait le 22/11 : « jamais sur une mèche ».

    Les deux états sont comparés sur la **même** question, posée de façon symétrique :
    où se trouve le prix à la fin de l'horizon ? Demander « est-il revenu en deçà ? »
    donnait 100 % aux mèches seules par pure construction, puisque celles-ci se
    définissent précisément par l'absence de clôture au-delà.
    """
    step = int(step or horizon)      # cf. study_deviations : indépendance des observations
    rows = []
    for i in range(window, len(df) - horizon, step):
        hist = df.iloc[i - window:i]
        rng = S.find_range(hist)
        if rng is None or rng.height_pct < 0.03:
            continue
        fut = df.iloc[i:i + horizon]
        ref = float(df["close"].iloc[i])
        for level, side in ((rng.high, "above"), (rng.low, "below")):
            a = S.acceptance(hist, level, side, min_closes=min_closes, lookback=10)
            if not a["accepted"] and not a["wicked_only"]:
                continue
            # « ça continue » = le prix progresse encore de 1 % **à partir d'ici**. Mesurer
            # depuis le niveau donnerait 99 % de réussite par construction, puisque
            # l'acceptance suppose déjà des clôtures au-delà.
            target = ref * (1.01 if side == "above" else 0.99)
            went_on = bool((fut["high"] >= target).any() if side == "above"
                           else (fut["low"] <= target).any())
            # « Est revenu » était biaisé par construction : une mèche seule signifie
            # justement qu'aucune clôture n'a eu lieu au-delà, donc le prix est DÉJÀ en
            # deçà au moment du test et « revient » mécaniquement dès la première barre.
            # D'où un 1,00 systématique qui ne mesurait rien. On compare plutôt, pour les
            # deux états, où se trouve le prix à la FIN de l'horizon.
            end = float(fut["close"].iloc[-1])
            beyond_end = bool(end > level if side == "above" else end < level)
            rows.append({"at": df.index[i], "côté": side,
                         "état": "acceptance" if a["accepted"] else "mèche seule",
                         "a continué": went_on, "au-delà à la fin": beyond_end,
                         "rendement %": float(end / ref - 1.0) * 100})
    return pd.DataFrame(rows)


def summarise_acceptance(a: pd.DataFrame) -> pd.DataFrame:
    if a.empty:
        return pd.DataFrame()
    out = []
    for (etat, cote), g in a.groupby(["état", "côté"]):
        out.append({"état": etat, "côté": cote, "n": len(g),
                    "a continué": _rate(g["a continué"]),
                    "au-delà à la fin": _rate(g["au-delà à la fin"]),
                    "rendement médian %": round(float(g["rendement %"].median()), 2)})
    return pd.DataFrame(out)


# --------------------------------------------------------------------- CLI

def load(symbol: str = "BTC/USDT", timeframe: str = "4h", years: float = 3.0):
    """OHLCV sur `years` années, paginé."""
    from .. import data as D
    from .replay import fetch_ohlcv_range
    end = pd.Timestamp.now(tz="UTC")
    start = end - pd.Timedelta(days=int(365 * years))
    return fetch_ohlcv_range(D.get_exchange("binance"), symbol, timeframe, start, end)


def report(df: pd.DataFrame, horizon: int, label: str = "", level: str = "half",
           only_wicks: bool = False) -> None:
    print(f"--- {label} : {len(df)} bougies, du {df.index[0]:%Y-%m-%d} "
          f"au {df.index[-1]:%Y-%m-%d} ---")
    w = summarise_precedence(study_wick_precedence(df, horizon=max(horizon, 120),
                                                   level=level))
    print(f"\n1. Mèches : le retracement ({'50 %' if level == 'half' else '100 %'}) "
          "précède-t-il le mouvement ?")
    print(w.to_string(index=False) if not w.empty else "  (aucun cas)")
    if only_wicks:
        print()
        return
    d = summarise_deviations(study_deviations(df, horizon=horizon))
    print("\n2. Déviation de range contre cassure installée")
    print(d.to_string(index=False) if not d.empty else "  (aucun cas)")
    a = summarise_acceptance(study_acceptance(df))
    print("\n3. Acceptance contre mèche seule")
    print(a.to_string(index=False) if not a.empty else "  (aucun cas)")
    print()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--symbol", default="BTC/USDT")
    ap.add_argument("--timeframe", default="4h")
    ap.add_argument("--years", type=float, default=3.0)
    ap.add_argument("--horizon", type=int, default=60)
    ap.add_argument("--level", default="half", choices=("half", "full"),
                    help="niveau de retracement testé : 50 %% ou 100 %% de la mèche")
    ap.add_argument("--only-wicks", action="store_true")
    ap.add_argument("--split", type=int, default=0,
                    help="découper l'historique en N sous-périodes et les comparer : "
                         "une règle qui ne tient que sur une moitié n'est pas une règle")
    args = ap.parse_args()
    df = load(args.symbol, args.timeframe, args.years)
    print(f"{args.symbol} {args.timeframe}\n")
    if args.split and args.split > 1:
        bounds = np.linspace(0, len(df), args.split + 1).astype(int)
        for k in range(args.split):
            report(df.iloc[bounds[k]:bounds[k + 1]], args.horizon,
                   f"période {k + 1}/{args.split}", args.level, args.only_wicks)
    else:
        report(df, args.horizon, "ensemble", args.level, args.only_wicks)


if __name__ == "__main__":
    main()
