"""
Tests synthétiques du détecteur de Fair Value Gaps / liquidity voids (liquidity.py).

On fabrique un déplacement haussier propre laissant un gap 3 bougies (FVG), puis :
  - on vérifie que le vide est détecté avec la bonne direction et des bornes correctes ;
  - qu'un vide non comblé est marqué "unfilled" et scoré positivement ;
  - qu'un retour du prix dans le gap le passe en "partial"/"filled" ;
  - qu'une dérive plate sans déplacement ne produit aucun vide.
Hors-ligne (pas de réseau).
"""
import numpy as np
import pandas as pd

from screener.features import add_features
from screener.liquidity import VoidThresholds, detect_voids


def _df(rows):
    idx = pd.date_range("2024-01-01", periods=len(rows), freq="h", tz="UTC")
    df = pd.DataFrame(rows, columns=["open", "high", "low", "close", "volume"], index=idx)
    return add_features(df, vol_ma=20, atr_period=14)


def _drift(n, base, vol=1000.0, seed=0):
    """Barres calmes proches de `base` (volume normal, spread étroit)."""
    rng = np.random.default_rng(seed)
    rows, c = [], base
    for _ in range(n):
        c = c + rng.normal(0, 0.4)
        o = c + rng.normal(0, 0.3)
        h = max(o, c) + abs(rng.normal(0, 0.3))
        l = min(o, c) - abs(rng.normal(0, 0.3))
        rows.append([o, h, l, c, vol * rng.uniform(0.8, 1.1)])
    return rows


def test_bullish_fvg_unfilled():
    rows = _drift(40, 100.0, seed=1)            # base pour ATR/vol_ma (spread ~1)
    # FVG haussier : bougie 1 normale (high ~100.x), bougie 2 = déplacement large et
    # volumique, bougie 3 ouvre nettement au-dessus (low > high de la bougie 1).
    rows += [[100.0, 100.5, 99.6, 100.2, 1000.0]]   # bougie 1 : high = 100.5
    rows += [[100.3, 106.0, 100.3, 105.8, 4000.0]]  # bougie 2 : déplacement (spread ~5.7)
    rows += [[105.9, 107.0, 102.0, 106.5, 1500.0]]  # bougie 3 : low = 102.0 > 100.5 → gap
    # le prix reste haut : vide (100.5, 102.0) non comblé
    rows += _drift(3, 106.5, vol=900.0, seed=2)

    voids = detect_voids(_df(rows), lookback=60)
    assert voids, "un FVG haussier doit être détecté"
    v = voids[0]
    assert v.direction == "bullish"
    assert abs(v.bottom - 100.5) < 0.6 and abs(v.top - 102.0) < 0.6
    assert v.fill_status == "unfilled"
    assert v.score > 0
    assert "déplacement" in v.why and v.theory


def test_fvg_gets_filled_when_price_returns():
    rows = _drift(40, 100.0, seed=3)
    rows += [[100.0, 100.5, 99.6, 100.2, 1000.0]]
    rows += [[100.3, 106.0, 100.3, 105.8, 4000.0]]
    rows += [[105.9, 107.0, 102.0, 106.5, 1500.0]]   # gap (100.5, 102.0)
    # le prix redescend traverser tout le gap → comblement complet
    rows += [[106.0, 106.2, 100.0, 100.4, 1200.0]]
    rows += _drift(2, 100.5, vol=900.0, seed=4)

    voids = detect_voids(_df(rows), lookback=60)
    bull = [v for v in voids if v.direction == "bullish" and abs(v.bottom - 100.5) < 0.6]
    assert bull, "le FVG doit toujours être repéré, même comblé"
    assert bull[0].fill_status == "filled"
    assert bull[0].score == 0.0          # vide purgé → plus de signal


def test_bearish_fvg():
    rows = _drift(40, 100.0, seed=5)
    rows += [[100.0, 100.4, 99.5, 99.8, 1000.0]]     # bougie 1 : low = 99.5
    rows += [[99.7, 99.7, 94.0, 94.2, 4000.0]]       # bougie 2 : déplacement vendeur
    rows += [[94.1, 98.0, 93.0, 93.5, 1500.0]]       # bougie 3 : high = 98.0 < 99.5 → gap
    rows += _drift(3, 93.5, vol=900.0, seed=6)

    voids = detect_voids(_df(rows), lookback=60)
    bear = [v for v in voids if v.direction == "bearish"]
    assert bear, "un FVG baissier doit être détecté"
    assert abs(bear[0].bottom - 98.0) < 0.6 and abs(bear[0].top - 99.5) < 0.6


def test_no_void_on_flat_drift():
    voids = detect_voids(_df(_drift(80, 100.0, seed=9)), lookback=60)
    assert voids == []
