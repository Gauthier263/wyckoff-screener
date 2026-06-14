"""
Tests synthétiques du détecteur double creux / double sommet + divergence RSI
(divergence.py). On fabrique :
  - une accumulation : plage ouverte par un Selling Climax, deux creux proches près
    du plancher, le 2e sur RSI plus haut (divergence haussière) → double bottom détecté ;
  - son miroir distribution (double top + divergence baissière) ;
  - un cas négatif : 2e creux sur momentum DÉCROISSANT (pas de divergence) → None.
Hors-ligne, aucune dépendance réseau.
"""
import numpy as np
import pandas as pd

from screener.divergence import (
    DivergenceParams, detect_double_divergence, detect_forming_entry,
)
from screener.features import TradingRange, add_features, detect_trading_range


def _df(rows):
    idx = pd.date_range("2024-01-01", periods=len(rows), freq="h", tz="UTC")
    df = pd.DataFrame(rows, columns=["open", "high", "low", "close", "volume"], index=idx)
    return add_features(df, vol_ma=20, atr_period=14, rsi_period=14)


def _drift(n, base, vol=1000.0, seed=0):
    rng = np.random.default_rng(seed)
    rows, c = [], base
    for _ in range(n):
        c = c + rng.normal(0, 0.4)
        o = c + rng.normal(0, 0.3)
        h = max(o, c) + abs(rng.normal(0, 0.3))
        l = min(o, c) - abs(rng.normal(0, 0.3))
        rows.append([o, h, l, c, vol * rng.uniform(0.85, 1.1)])
    return rows


def _acc_rows(dip2=93.2, path2=(100.0, 97.8, 96.2)):
    """Accumulation : SC (1er creux + climax) → plage → 2e creux récent.

    Deux seuls creux près du plancher : le Selling Climax (descente brève et raide →
    RSI très bas) et un 2e test récent atteint par une contraction plus douce
    (`path2`/`dip2`) → RSI plus haut = divergence haussière. En durcissant `path2`
    (descente longue et raide) on supprime la divergence (cas négatif)."""
    rows = _drift(30, 100.0, seed=1)
    # descente brève vers le climax → RSI au plus bas
    rows += [[100.0, 100.3, 98.8, 99.0, 1100.0],
             [99.0, 99.2, 97.5, 97.8, 1200.0],
             [97.8, 98.0, 96.0, 96.2, 1300.0]]
    # SC : grosse barre, plus-bas 93.5, clôture haute, volume climactique (= 1er creux)
    rows += [[96.2, 96.5, 93.5, 95.8, 3600.0]]
    # 2e touche basse (≈ support) mais pas un pivot (le SC est plus bas à gauche)
    rows += [[95.8, 96.0, 94.3, 95.0, 1500.0]]
    # AR + 1ère poussée au plafond (~103)
    rows += [[95.0, 98.0, 94.9, 97.9, 1200.0],
             [97.9, 100.0, 97.7, 99.8, 1100.0],
             [99.8, 103.0, 99.6, 102.8, 1300.0]]
    # repli peu profond (reste au-dessus de la zone support)
    rows += [[102.8, 103.0, 100.0, 100.2, 900.0],
             [100.2, 101.0, 98.5, 99.0, 800.0]]
    # 2e poussée au plafond (2e touche du haut)
    rows += [[99.0, 101.0, 98.8, 100.8, 1000.0],
             [100.8, 103.1, 100.6, 102.9, 1200.0]]
    # contraction vers le 2e creux (chemin paramétré)
    for c in path2:
        rows += [[c + 0.2, c + 0.3, c - 1.6, c, 850.0]]
    # P2 : 2e creux récent, volume sec
    rows += [[dip2 + 2.2, dip2 + 2.4, dip2, dip2 + 1.4, 600.0]]
    # 2 barres de « formation » sous la ligne de cou
    rows += [[dip2 + 1.4, dip2 + 2.8, dip2 + 1.2, dip2 + 2.6, 650.0],
             [dip2 + 2.6, dip2 + 3.3, dip2 + 2.4, dip2 + 3.0, 650.0]]
    return rows


def _acc_rows_nodiv():
    """Même ouverture (SC + plage) mais le 2e creux est un nouveau plus-bas atteint
    sur une accélération baissière (clôtures faibles) → RSI plus BAS qu'au climax :
    pas de divergence haussière, donc aucun signal attendu."""
    rows = _drift(30, 100.0, seed=1)
    rows += [[100.0, 100.3, 98.8, 99.0, 1100.0],
             [99.0, 99.2, 97.5, 97.8, 1200.0],
             [97.8, 98.0, 96.0, 96.2, 1300.0]]
    rows += [[96.2, 96.5, 93.5, 95.8, 3600.0]]          # SC (1er creux)
    rows += [[95.8, 96.0, 94.3, 95.0, 1500.0]]          # 2e touche basse (pas pivot)
    rows += [[95.0, 98.0, 94.9, 97.9, 1200.0],
             [97.9, 100.0, 97.7, 99.8, 1100.0],
             [99.8, 103.0, 99.6, 102.8, 1300.0]]        # poussée plafond #1
    rows += [[102.8, 103.0, 100.0, 100.2, 900.0],
             [100.2, 101.0, 98.5, 99.0, 800.0]]
    rows += [[99.0, 101.0, 98.8, 100.8, 1000.0],
             [100.8, 103.1, 100.6, 102.9, 1200.0]]      # poussée plafond #2
    # plongeon accéléré, clôtures sur les bas → momentum baissier fort
    rows += [[102.9, 103.0, 99.0, 99.2, 900.0],
             [99.2, 99.3, 95.0, 95.2, 950.0],
             [95.2, 95.3, 91.5, 91.8, 1000.0]]
    rows += [[91.8, 91.9, 90.0, 90.2, 1100.0]]          # 2e creux : nouveau plus-bas faible
    rows += [[90.2, 91.0, 90.1, 90.8, 650.0],
             [90.8, 91.5, 90.6, 91.2, 650.0]]
    return rows


def _mirror(rows, pivot=100.0):
    """Reflète une séquence d'accumulation en distribution autour de `pivot`."""
    out = []
    for o, h, l, c, v in rows:
        out.append([2 * pivot - o, 2 * pivot - l, 2 * pivot - h, 2 * pivot - c, v])
    return out


def test_accumulation_double_bottom_divergence():
    df = _df(_acc_rows())
    tr = detect_trading_range(df, lookback=30, buffer=5)
    assert tr.is_valid
    res = detect_double_divergence("TEST/USDT", df, tr,
                                   params=DivergenceParams(recent_bars=8), lookback=45)
    assert res is not None
    assert res.bias == "accumulation"
    assert res.pattern == "double bottom"
    assert res.climax == "SC"
    assert res.rsi_div >= 5.0                 # RSI du 2e creux nettement plus haut
    assert res.p2.price <= res.p1.price       # vraie divergence : 2e creux égal ou PLUS BAS
    assert res.p2.bars_ago <= 8               # 2e creux récent (formation)
    assert res.is_forming                     # ligne de cou pas encore cassée
    assert res.p2.vol_ratio < res.p1.vol_ratio  # 2e test plus sec
    assert "RSI" in res.why and res.theory


def test_distribution_double_top_divergence():
    df = _df(_mirror(_acc_rows()))
    tr = detect_trading_range(df, lookback=30, buffer=5)
    assert tr.is_valid
    res = detect_double_divergence("TEST/USDT", df, tr,
                                   params=DivergenceParams(recent_bars=8), lookback=45)
    assert res is not None
    assert res.bias == "distribution"
    assert res.pattern == "double top"
    assert res.climax == "BC"
    assert res.rsi_div >= 5.0
    assert res.p2.price >= res.p1.price       # vraie divergence : 2e sommet égal ou PLUS HAUT


def test_no_divergence_when_momentum_falls():
    df = _df(_acc_rows_nodiv())
    tr = detect_trading_range(df, lookback=30, buffer=5)
    res = detect_double_divergence("TEST/USDT", df, tr,
                                   params=DivergenceParams(recent_bars=8), lookback=45)
    assert res is None


def test_no_divergence_on_higher_low():
    # 2e creux PLUS HAUT que le 1er, avec RSI lui aussi plus haut : prix et momentum
    # montent ensemble → simple confirmation, PAS une divergence (cas type TRX).
    df = _df(_acc_rows(dip2=95.0, path2=(98.0,)))
    tr = detect_trading_range(df, lookback=30, buffer=5)
    res = detect_double_divergence("TEST/USDT", df, tr,
                                   params=DivergenceParams(recent_bars=8), lookback=45)
    assert res is None


def _entry_rows(last_low=93.6, last=(94.0, 95.3, 95.0)):
    """Double bottom EN FORMATION : SC (1er creux) → rally (ligne de cou) → descente
    douce → la DERNIÈRE barre teste la zone du plancher. `last`=(open,high,close) et
    `last_low` pilotent la barre de test (rejet/zone)."""
    rows = _drift(30, 100.0, seed=1)
    rows += [[100.0, 100.3, 98.8, 99.0, 1100.0],
             [99.0, 99.2, 97.5, 97.8, 1200.0],
             [97.8, 98.0, 96.0, 96.2, 1300.0]]
    rows += [[96.2, 96.5, 93.5, 95.8, 3600.0]]                 # SC = 1er creux (93.5)
    rows += [[95.8, 98.0, 95.6, 97.9, 1200.0],
             [97.9, 100.0, 97.7, 99.8, 1100.0],
             [99.8, 103.0, 99.6, 102.8, 1300.0]]               # rally → ligne de cou ~103
    rows += [[102.8, 103.0, 101.0, 101.2, 900.0],
             [101.2, 101.4, 99.0, 99.2, 800.0],
             [99.2, 99.4, 97.0, 97.2, 800.0],
             [97.2, 97.4, 95.5, 95.7, 750.0]]                  # descente douce (reste > support)
    o, h, c = last
    rows += [[o, h, last_low, c, 600.0]]                       # barre COURANTE = test du plancher
    return rows


def _tr():
    return TradingRange(low=93.5, high=103.0, mid=98.25, height=9.5, height_atr=5.0, is_valid=True)


def test_forming_entry_confirmed():
    df = _df(_entry_rows())                       # test à 93.6, clôture haute (rejet)
    res = detect_forming_entry("T/USDT", df, _tr(),
                               params=DivergenceParams(min_rsi_div=5), lookback=60)
    assert res is not None
    assert res.bias == "accumulation" and res.pattern == "double bottom"
    assert res.climax == "SC"
    assert res.confirmed                          # rejet haussier présent sur la barre
    assert res.rsi_div >= 5
    assert res.stop < res.test_ext                # stop sous le 2e creux
    assert res.target > res.test_close            # cible (ligne de cou) au-dessus de l'entrée
    assert res.rr > 0


def test_forming_entry_none_when_not_testing_support():
    # dernière barre en plein milieu de plage (ne teste pas le plancher) → pas d'entrée
    df = _df(_entry_rows(last_low=98.0, last=(98.5, 99.0, 98.8)))
    res = detect_forming_entry("T/USDT", df, _tr(),
                               params=DivergenceParams(min_rsi_div=5), lookback=60)
    assert res is None
