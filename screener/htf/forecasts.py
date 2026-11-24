"""forecasts.py — les prévisions BTC datées de CrypNuevo, et leur issue mesurée sur les prix.

Transcrites depuis `research/crypnuevo_tweets.md`. Seules les prévisions **directionnelles**
sont retenues (une direction, une cible, et quand il la donne, une invalidation) ; les
lectures neutres (« deux voies, j'attends ») sont écartées. Les bornes de range sont celles
qu'il trace sur le graphe du tweet, pour rejouer le moteur de biais avec ses bornes.

L'issue est mesurée de deux façons, indépendantes l'une de l'autre :
- `issue_cible` : **sa** cible est-elle atteinte avant **son** invalidation, dans l'horizon ?
- `issue_marché` : dans quel sens le prix fait-il d'abord un mouvement de `move_pct` ? C'est
  le juge commun de sa direction et de celle de l'outil.

Horodatages en UTC (ceux de X).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

# direction : +1 haussier, -1 baissier. cible / invalidation : prix. bornes : (plancher,
# plafond, zone_basse, zone_haute) telles qu'il les trace. horizon : jours.
FORECASTS = [
    {"asof": "2026-01-04T16:12Z", "dir": -1, "cible": 80600, "inval": 100000, "h": 40,
     "bornes": (84804, 94312, (80600, 84804), (94312, 96000)),
     "texte": "balayage des plus bas du range (~80,6k), avec ou sans liquidity run vers 96k"},
    {"asof": "2026-01-11T15:36Z", "dir": -1, "cible": 80600, "inval": 100000, "h": 35,
     "bornes": (84804, 94312, (80600, 84804), (94312, 96000)),
     "texte": "retour aux low 80s ; liquidity run possible vers la 1W50EMA d'abord"},
    {"asof": "2026-01-18T18:40Z", "dir": -1, "cible": 84804, "inval": 100000, "h": 28,
     "bornes": (84804, 94312, (80600, 84804), (94312, 96000)),
     "texte": "pression baissière, retour dans le range puis vers les range lows"},
    {"asof": "2026-01-25T16:09Z", "dir": -1, "cible": 80600, "inval": 100000, "h": 28,
     "bornes": (84804, 94312, (80600, 84804), (94312, 96000)),
     "texte": "perte du mid-range : continuation vers les range lows (low 80s)"},
    {"asof": "2026-02-01T16:03Z", "dir": 1, "cible": 90000, "inval": 70000, "h": 45,
     "bornes": (74647, 97000, (70000, 74647), (97000, 100000)),
     "texte": "liquidity grab sous 74,6k puis rallye (acceptance dessous = scénario baissier)"},
    {"asof": "2026-02-08T17:35Z", "dir": -1, "cible": 65115, "inval": 77000, "h": 35,
     "bornes": (53500, 74000, (53500, 60000), (72000, 74000)),
     "texte": "remplissage d'au moins 50 % de la mèche 1W (65,1k), pump 72-77k possible avant"},
    {"asof": "2026-02-22T18:10Z", "dir": -1, "cible": 61000, "inval": 72000, "h": 21,
     "bornes": (53500, 74000, (53500, 60000), (72000, 74000)),
     "texte": "biais short : 61k sous 2-3 semaines (100 % de la mèche)"},
    {"asof": "2026-03-15T21:18Z", "dir": 1, "cible": 75000, "inval": 68000, "h": 14,
     "bornes": (60000, 79000, (59500, 61500), (79000, 81000)),
     "texte": "longs favorisés (wick imbalance), TP 73,9k puis 75k"},
    {"asof": "2026-03-22T15:43Z", "dir": -1, "cible": 65000, "inval": 71000, "h": 14,
     "bornes": (60000, 79000, (59500, 61500), (79000, 81000)),
     "texte": "rotation LTF vers 65k ; acceptance au-dessus de 71k l'invalide"},
    {"asof": "2026-04-05T18:53Z", "dir": -1, "cible": 64000, "inval": 79000, "h": 21,
     "bornes": (60000, 79000, (59500, 62000), (79000, 81000)),
     "texte": "range lows d'abord (liquidations HTF 64-64,5k), longs en bas de range"},
    {"asof": "2026-04-12T21:57Z", "dir": -1, "cible": 64000, "inval": 80000, "h": 21,
     "bornes": (60000, 79000, (59500, 61500), (79000, 81000)),
     "texte": "liquidations HTF à 64k : bas du range d'abord"},
    {"asof": "2026-04-26T22:01Z", "dir": -1, "cible": 70000, "inval": 82500, "h": 35,
     "bornes": (60000, 79200, (59500, 61500), (79200, 81500)),
     "texte": "déviation au-dessus des range highs (80-81k) puis vers 70k (mid-range)"},
    {"asof": "2026-05-03T19:05Z", "dir": -1, "cible": 73300, "inval": 83000, "h": 28,
     "bornes": (60150, 79300, (59500, 61500), (79300, 81500)),
     "texte": "stop hunt au-dessus des range highs puis liquidity pool 71-73k"},
    {"asof": "2026-05-10T19:56Z", "dir": 1, "cible": 84000, "inval": 79000, "h": 14,
     "bornes": (60150, 79300, (59500, 61500), (79300, 81500)),
     "texte": "acceptance au-dessus de 81k : 84-85k ; retour sous 79k invalide"},
    {"asof": "2026-05-21T22:49Z", "dir": -1, "cible": 73300, "inval": 80000, "h": 21,
     "bornes": (60150, 79300, (59500, 61500), (79300, 81500)),
     "texte": "retest des range highs puis liquidity pool 71-73k ; invalidation au-dessus de 80k"},
    {"asof": "2026-05-31T21:12Z", "dir": 1, "cible": 75400, "inval": 71500, "h": 10,
     "bornes": (60150, 79300, (59500, 61500), (79300, 81500)),
     "texte": "long 72,5-73k (mèche), cible le gap CME 75,4k"},
    {"asof": "2026-06-07T16:22Z", "dir": 1, "cible": 69500, "inval": 57000, "h": 60,
     "bornes": (60200, 79300, (59300, 61500), (79300, 81500)),
     "texte": "fort rebond (sur-extension) vers le mid-range 69-70k, puis range highs"},
    {"asof": "2026-06-21T15:35Z", "dir": 1, "cible": 69000, "inval": 62200, "h": 21,
     "bornes": (60200, 79300, (59300, 61500), (79300, 81500)),
     "texte": "acceptance au-dessus de 64,5k : nouveau plus haut local ; perte de 62,2k : 60k"},
    {"asof": "2026-06-28T20:25Z", "dir": 1, "cible": 65000, "inval": 57000, "h": 21,
     "bornes": (60200, 79300, (58000, 61000), (79300, 81500)),
     "texte": "tenir lundi + reclaim de 61k : reprise ; acceptance sous 57k invalide"},
    {"asof": "2026-07-05T17:04Z", "dir": 1, "cible": 69000, "inval": 57000, "h": 45,
     "bornes": (60200, 79300, (58000, 61000), (79300, 81500)),
     "texte": "Three Taps : cible principale le mid-range ~69-70k"},
    {"asof": "2026-07-19T11:12Z", "dir": 1, "cible": 69000, "inval": 60000, "h": 30,
     "bornes": (60200, 79300, (58000, 61000), (79300, 81500)),
     "texte": "acceptance au-dessus de la 1D50EMA, TP au mid-range 69k"},
    {"asof": "2026-08-03T01:22Z", "dir": 1, "cible": 69000, "inval": 59000, "h": 30,
     "bornes": (60200, 79300, (58000, 61000), (79300, 81500)),
     "texte": "reclaim de 65k pour pousser plus haut, sinon retour direct à 59k"},
    {"asof": "2026-08-16T08:53Z", "dir": -1, "cible": 61600, "inval": 66000, "h": 10,
     "bornes": (60200, 79300, (58000, 61000), (79300, 81500)),
     "texte": "début de semaine : prise de la liquidité sous le double creux (~61,6k)"},
    {"asof": "2026-08-30T08:40Z", "dir": 1, "cible": 81000, "inval": 76000, "h": 14,
     "bornes": (60000, 79300, (58000, 61000), (79300, 81500)),
     "texte": "scénario optimiste : remplissage de la mèche 1h haute (~81k)"},
    {"asof": "2026-09-13T15:16Z", "dir": -1, "cible": 74600, "inval": 82000, "h": 14,
     "bornes": (60200, 79500, (58000, 61000), (79500, 82000)),
     "texte": "faux mouvement haussier (78,8k) puis prise des plus bas locaux (Bart Simpson)"},
    {"asof": "2026-09-20T09:44Z", "dir": -1, "cible": 75500, "inval": 82900, "h": 14,
     "bornes": (60500, 80000, (58000, 61000), (80000, 82900)),
     "texte": "retracement probable (long squeeze) ; cassure au-dessus de 82,9k : 89,3k"},
    {"asof": "2026-09-27T10:35Z", "dir": 1, "cible": 89300, "inval": 80000, "h": 21,
     "bornes": (60000, 80000, (58000, 61000), (80000, 82900)),
     "texte": "retracement de la liquidity pool jusqu'à 89,3k après sweep sous 82,85k"},
    {"asof": "2026-10-11T15:59Z", "dir": 1, "cible": 87500, "inval": 80300, "h": 14,
     "bornes": (60000, 82363, (58000, 61000), (82363, 87300)),
     "texte": "long après reclaim de 82,5k, cible au-dessus de 87,5k"},
    {"asof": "2026-10-25T20:25Z", "dir": -1, "cible": 78600, "inval": 82400, "h": 10,
     "bornes": (60000, 82363, (58000, 61000), (82363, 87300)),
     "texte": "liquidations à 78,8k et test de la 1W50EMA (78,6k)"},
    {"asof": "2026-11-01T12:27Z", "dir": -1, "cible": 75545, "inval": 81500, "h": 10,
     "bornes": (75545, 81341, (75300, 75600), (81300, 81500)),
     "texte": "pas de V-recovery : retour aux plus bas 75,5k (W ou Three Taps)"},
    {"asof": "2026-11-08T07:43Z", "dir": -1, "cible": 73000, "inval": 81200, "h": 10,
     "bornes": (75849, 81197, (75300, 75850), (81197, 81500)),
     "texte": "retracement vers 76,6-78,8k puis amas de liquidations 74,7-73k"},
    {"asof": "2026-11-15T23:50Z", "dir": -1, "cible": 60500, "inval": 70000, "h": 7,
     "bornes": (60000, 81341, (59000, 60600), (81000, 81500)),
     "texte": "range lows à 60k lundi-mardi, puis rebond (« give me 60k and I'm in »)"},
    {"asof": "2026-11-22T20:52Z", "dir": 1, "cible": 65400, "inval": 55130, "h": 10,
     "bornes": (60000, 81341, (59000, 60600), (81000, 81500)),
     "texte": "acceptance au-dessus de 60,6k : +8 à 10 % ; mur à 58,6k"},
]


def first_hit(h1: pd.DataFrame, asof, up: float, down: float, horizon_days: float):
    """Lequel des deux niveaux est touché en premier après `asof` (pur).

    Renvoie `("haut"|"bas"|"indéterminé"|"aucun", heures)`. `indéterminé` : les deux dans la
    même bougie horaire.
    """
    t0 = pd.Timestamp(asof)
    fut = h1[(h1.index >= t0) & (h1.index < t0 + pd.Timedelta(days=horizon_days))]
    if fut.empty:
        return "aucun", None
    hu = np.flatnonzero((fut["high"] >= up).to_numpy())
    hd = np.flatnonzero((fut["low"] <= down).to_numpy())
    iu = hu[0] if len(hu) else None
    idn = hd[0] if len(hd) else None
    if iu is None and idn is None:
        return "aucun", None
    if idn is None or (iu is not None and iu < idn):
        return "haut", int(iu)
    if iu is None or idn < iu:
        return "bas", int(idn)
    return "indéterminé", int(iu)


def outcomes(h1: pd.DataFrame, fc: dict, move_pct: float = 0.05) -> dict:
    """Issue de sa prévision (sa cible contre son invalidation) et sens du premier
    mouvement de `move_pct` du marché (pur)."""
    t0 = pd.Timestamp(fc["asof"])
    p0 = float(h1[h1.index < t0]["close"].iloc[-1])
    if fc["dir"] > 0:
        hit, hrs = first_hit(h1, t0, fc["cible"], fc["inval"], fc["h"])
        issue = {"haut": "cible", "bas": "invalidée"}.get(hit, hit)
    else:
        hit, hrs = first_hit(h1, t0, fc["inval"], fc["cible"], fc["h"])
        issue = {"bas": "cible", "haut": "invalidée"}.get(hit, hit)
    m, mh = first_hit(h1, t0, p0 * (1 + move_pct), p0 * (1 - move_pct), 45)
    return {"prix": p0, "issue_cible": issue, "heures": hrs,
            "marché": {"haut": 1, "bas": -1}.get(m, 0), "heures_marché": mh}


def replay_all(symbol: str = "BTC/USDT") -> pd.DataFrame:
    """Rejoue le moteur de biais figé à la date de chaque prévision, avec ses bornes puis
    avec les bornes automatiques, et mesure l'issue. Réseau requis (données, liquidations)."""
    from .. import data as D
    from . import bias as B
    from . import wick_study as WS

    h1 = WS.load(symbol, "1h", "2020-01-01")
    liq_all = D.fetch_liquidations(symbol, "1d", start=pd.Timestamp("2020-01-01", tz="UTC"),
                                   end=pd.Timestamp.now(tz="UTC"))
    sgn = {"haussier": 1, "baissier": -1, "neutre": 0}
    rows = []
    for fc in FORECASTS:
        t = pd.Timestamp(fc["asof"])
        d = B.load_asof(t, symbol, with_liq=False)
        liq = liq_all[liq_all.index + pd.Timedelta("1D") <= t] if liq_all is not None else None
        fl, ce, zb, zh = fc["bornes"]
        r = B.assess(d["1d"], d["4h"], d["1h"], bounds_1d=B.Bounds(fl, ce, zb, zh),
                     liq_daily=liq, asof=t)
        ra = B.assess(d["1d"], d["4h"], d["1h"], liq_daily=liq, asof=t)
        o = outcomes(h1, fc)
        rows.append({"asof": t, "prix": o["prix"], "lui": fc["dir"], "outil": sgn[r.bias],
                     "score": r.score, "outil_auto": sgn[ra.bias], "sa_cible": o["issue_cible"],
                     "marché": o["marché"], "texte": fc["texte"]})
    return pd.DataFrame(rows)


def score(X: pd.DataFrame) -> dict:
    """Taux de bonne direction (contre le premier mouvement de 5 %) — pur."""
    def acc(pred):
        m = (pred != 0) & (X["marché"] != 0)
        return int((pred[m] == X.loc[m, "marché"]).sum()), int(m.sum())
    out = {"lui": acc(X["lui"]), "outil": acc(X["outil"]), "outil_auto": acc(X["outil_auto"])}
    prononce = X["outil"] != 0
    m = prononce & (X["marché"] != 0)
    out["lui_quand_outil_se_prononce"] = (int((X.loc[m, "lui"] == X.loc[m, "marché"]).sum()), int(m.sum()))
    m = ~prononce & (X["marché"] != 0)
    out["lui_quand_outil_neutre"] = (int((X.loc[m, "lui"] == X.loc[m, "marché"]).sum()), int(m.sum()))
    return out


if __name__ == "__main__":
    from .wick_study import wilson

    X = replay_all()
    pd.set_option("display.width", 200)
    print(X.drop(columns=["texte"]).to_string(index=False))
    for k, (a, n) in score(X).items():
        lo, hi = wilson(a, n) if n else (float("nan"), float("nan"))
        print(f"{k:30} {a}/{n} = {a / n if n else float('nan'):.0%}  [{lo:.0%}-{hi:.0%}]")
