"""calibrate.py — distribution des leviers **mesurée**, au lieu d'être devinée.

Dans `liqmap`, la répartition des positions entre paliers de levier est le seul paramètre
qui ne vienne d'aucune mesure — et c'est lui qui décide de l'emplacement des amas de
liquidation. Ce module la déduit des **liquidations réellement exécutées**.

Principe
--------
Pour chaque palier de levier `L`, on simule un carnet où *tout* le flux irait à ce palier,
et on relève la série temporelle du carburant brûlé, barre par barre : `pred[L][t]`. On
cherche ensuite les poids `w_L ≥ 0` qui reconstituent au mieux les liquidations observées :

    obs[t] ≈ Σ_L  w_L · pred[L][t]

résolu par moindres carrés non négatifs, séparément pour les longs et les shorts. Un palier
dont le profil temporel ne ressemble pas à l'observé reçoit un poids nul : seul un levier
dont les liquidations tombent **aux mêmes moments** que les vraies est retenu.

La somme des poids obtenus vaut rarement 1 : le complément est la part des positions sans
liquidation atteignable (cross largement collatéralisé, couverture, teneur de marché), que
`liqmap` appelle `unlevered_frac`. On ne la postule donc plus non plus.

Limites
-------
- Les liquidations publiées par les bourses sont **sous-déclarées** (Binance en diffuse un
  échantillon). Les poids relatifs entre paliers restent lisibles, le niveau absolu non :
  d'où le calage de l'échelle globale sur le total observé.
- La calibration dépend de la fenêtre : un mois calme et un mois de krach ne donnent pas la
  même distribution. On recalibre sur fenêtre glissante plutôt qu'une fois pour toutes.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .. import data as D
from . import liqmap as L

CANDIDATE_LEVERAGES = (5, 10, 20, 25, 50, 100)


def observed_liquidations(symbol: str, timeframe: str, start, end,
                          index: pd.Index) -> "pd.DataFrame | None":
    """Liquidations exécutées, en **coin**, réalignées sur `index`.

    `fetch_liquidations` renvoie déjà des BTC (et non des dollars, contrairement à ce que
    disait sa docstring) : aucune conversion par le prix ne doit être faite ici.
    """
    df = D.fetch_liquidations(symbol, timeframe, start=start, end=end)
    if df is None or df.empty:
        return None
    df = df.reindex(index).fillna(0.0)
    return pd.DataFrame({"long": df["long_liq"], "short": df["short_liq"]})


def predicted_burn(df: pd.DataFrame, oi: pd.Series, delta: "pd.Series | None",
                   leverages=CANDIDATE_LEVERAGES, **kw) -> dict:
    """Pour chaque levier, la série du carburant brûlé si *tout* le flux y était placé."""
    out = {}
    for lev in leverages:
        m = L.build_map(df, oi, delta, unlevered_frac=0.0,
                        leverage_tiers={lev: 1.0}, **kw)
        out[lev] = {"long": m["burn_long_ts"], "short": m["burn_short_ts"]}
    return out


def nnls(A: np.ndarray, b: np.ndarray, iters: int = 500) -> np.ndarray:
    """Moindres carrés non négatifs (descente de gradient projetée) — pur, testable.

    Évite une dépendance à scipy pour un problème à six inconnues.
    """
    A = np.asarray(A, dtype=float)
    b = np.asarray(b, dtype=float)
    if A.size == 0 or A.shape[0] == 0:
        return np.zeros(A.shape[1] if A.ndim == 2 else 0)
    x = np.zeros(A.shape[1])
    lip = float(np.linalg.norm(A, 2) ** 2) or 1.0
    for _ in range(iters):
        x = np.maximum(0.0, x - (A.T @ (A @ x - b)) / lip)
    return x


def fit_leverage_tiers(df: pd.DataFrame, oi: pd.Series, delta: "pd.Series | None",
                       observed: pd.DataFrame, leverages=CANDIDATE_LEVERAGES,
                       min_fit: float = 0.2, **kw) -> dict:
    """Ajuste les poids de levier sur les liquidations observées.

    Les deux côtés sont ajustés **séparément** : les longs et les shorts n'ont pas le même
    profil de levier, et les confondre déplace les amas (vérifié sur le 22/11).

    Renvoie `{"tiers": {"long": {...}, "short": {...}}, "unlevered_frac": {...},
    "fit": {...}, "status": ...}`, directement utilisable par `liqmap.build_map`. `fit` est
    la corrélation entre prédit et observé, côté par côté : sous `min_fit`, la calibration
    n'a rien appris et ce côté garde les valeurs par défaut — le dire plutôt que de livrer
    un ajustement illusoire.
    """
    pred = predicted_burn(df, oi, delta, leverages, **kw)
    levs = list(leverages)
    tiers, fit = {}, {}
    for side in ("long", "short"):
        A = np.column_stack([pred[l][side].reindex(observed.index).fillna(0.0).to_numpy()
                             for l in levs])
        b = observed[side].to_numpy()
        w = nnls(A, b)
        yhat = A @ w
        fit[side] = (float(np.corrcoef(yhat, b)[0, 1])
                     if yhat.std() > 0 and b.std() > 0 else 0.0)
        total = float(w.sum())
        if total <= 0 or fit[side] < min_fit:
            tiers[side] = dict(L.DEFAULT_LEVERAGE_TIERS)
            continue
        # Les poids sont normalisés à 1 : le NNLS donne la **forme** de la distribution des
        # leviers, jamais son niveau absolu. Les bourses sous-déclarent leurs liquidations
        # (Binance n'en diffuse qu'un échantillon), donc la somme brute ne mesure rien.
        tiers[side] = {lev: float(wi / total) for lev, wi in zip(levs, w) if wi > 0}
    unlev = fit_unlevered_frac(df, oi, delta, tiers, **kw)
    weak = [s for s in ("long", "short") if fit[s] < min_fit]
    status = ("ajusté sur les liquidations observées" if not weak else
              "ajustement trop faible, valeurs par défaut conservées pour : "
              + ", ".join(weak))
    return {"tiers": tiers, "unlevered_frac": unlev, "fit": fit, "status": status}


def fit_unlevered_frac(df: pd.DataFrame, oi: pd.Series, delta: "pd.Series | None",
                       tiers: dict, lo: float = 0.0, hi: float = 0.95,
                       iters: int = 12, **kw) -> float:
    """Part non liquidable déduite d'une **contrainte dure** : la masse du profil reconstruit
    doit valoir l'OI courant.

    Sans elle, tout le carnet porte un levier, un mouvement de 26 % le liquide en entier et
    il ne reste qu'un résidu (2 BTC sur 93 611 au 15/11) : les amas lus ne sont alors que du
    bruit. Recherche par bissection, la masse restante croissant avec la part non liquidable.
    """
    if oi is None or len(oi.dropna()) == 0:
        return 0.45
    target = float(oi.dropna().iloc[-1])
    kw.pop("leverage_tiers", None)
    kw.pop("unlevered_frac", None)

    def mass(u):
        try:
            return float(L.build_map(df, oi, delta, leverage_tiers=tiers,
                                     unlevered_frac=u, **kw)["positions"].sum())
        except Exception:
            return 0.0

    if mass(hi) < target:          # même tout non liquidable ne suffit pas
        return hi
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        if mass(mid) < target:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)
