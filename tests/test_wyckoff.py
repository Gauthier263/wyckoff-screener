"""
Tests synthétiques du détecteur de structure (wyckoff.py).

On fabrique une séquence d'accumulation propre (SC → AR → ST → SOS) et son miroir
de distribution, puis on vérifie que `detect_window_structure` retrouve le bon
schéma, l'ordre des événements, et remplit théorie + justification. Hors-ligne.
"""
import numpy as np
import pandas as pd

from screener.features import add_features
from screener.wyckoff import detect_window_structure


def _df(rows):
    idx = pd.date_range("2024-01-01", periods=len(rows), freq="h", tz="UTC")
    df = pd.DataFrame(rows, columns=["open", "high", "low", "close", "volume"], index=idx)
    return add_features(df, vol_ma=20, atr_period=14)


def _drift(n, base, vol=1000.0, seed=0):
    """Barres calmes proches de `base` (volume normal, spread étroit)."""
    rng = np.random.default_rng(seed)
    rows = []
    c = base
    for _ in range(n):
        c = c + rng.normal(0, 0.4)
        o = c + rng.normal(0, 0.3)
        h = max(o, c) + abs(rng.normal(0, 0.3))
        l = min(o, c) - abs(rng.normal(0, 0.3))
        rows.append([o, h, l, c, vol * rng.uniform(0.8, 1.1)])
    return rows


def test_accumulation_sequence():
    rows = _drift(40, 100.0, seed=1)                       # base pour vol_ma/ATR
    # SC : grosse barre vendeuse qui fait un plus-bas et clôture haut, volume x3
    rows += [[100.0, 100.5, 95.0, 99.5, 3200.0]]
    # AR : rebond auto, volume en repli
    rows += [[99.5, 103.0, 99.4, 102.6, 800.0]]
    rows += _drift(4, 102.0, vol=600.0, seed=2)            # dérive haute, volume sec
    # ST : retour près du plancher (95.x) sur volume sec, barre étroite, creux plus haut
    rows += [[96.6, 97.0, 95.6, 96.4, 500.0]]
    rows += _drift(3, 97.5, vol=600.0, seed=3)
    # SOS : poussée large et volumique, clôture haute
    rows += [[98.0, 104.5, 97.8, 104.2, 2600.0]]
    rows += _drift(2, 104.0, vol=700.0, seed=4)

    struct = detect_window_structure(_df(rows), lookback=20)
    assert struct.bias == "accumulation"
    assert struct.is_valid
    names = [e.name for e in struct.events]
    assert names[0] == "SC"
    assert "SOS" in names
    assert {"SC", "AR"}.issubset(set(names))
    # chaque événement porte théorie + justification volume/spread
    for e in struct.events:
        assert e.theory and "vol" in e.why


def test_distribution_sequence():
    rows = _drift(40, 100.0, seed=5)
    # BC : grosse barre acheteuse qui fait un plus-haut et clôture bas, volume x3
    rows += [[100.0, 105.0, 99.6, 100.4, 3200.0]]
    # AR : repli auto, volume en repli
    rows += [[100.4, 100.6, 97.0, 97.4, 800.0]]
    rows += _drift(4, 98.0, vol=600.0, seed=6)
    # ST : retour près du plafond (104.x) sur volume sec, barre étroite, sommet plus bas
    rows += [[103.6, 104.4, 103.2, 103.8, 500.0]]
    rows += _drift(3, 102.5, vol=600.0, seed=7)
    # SOW : cassure baissière large et volumique, clôture basse
    rows += [[102.0, 102.2, 95.5, 95.8, 2600.0]]
    rows += _drift(2, 96.0, vol=700.0, seed=8)

    struct = detect_window_structure(_df(rows), lookback=20)
    assert struct.bias == "distribution"
    assert struct.is_valid
    names = [e.name for e in struct.events]
    assert names[0] == "BC"
    assert "SOW" in names


def test_no_structure_on_flat_drift():
    struct = detect_window_structure(_df(_drift(80, 100.0, seed=9)), lookback=30)
    assert struct.bias == "neutral"
    assert not struct.is_valid


def test_ar_is_first_reaction_not_later_higher_high():
    """L'AR doit être le PREMIER rebond après le SC, pas un plus-haut tardif d'un markup
    (bug corrigé : argmax sur fenêtre → premier pivot)."""
    from screener.wyckoff import _scan, Thresholds
    rows = _drift(20, 110.0, seed=0)
    rows += [[110 - i, 110.3 - i, 109.6 - i, 109.9 - i, 900] for i in range(10)]  # markdown
    rows += [[100.0, 100.5, 95.0, 99.5, 3200.0]]      # SC (low 95)
    rows += [[99.5, 100.6, 99.2, 100.4, 700.0]]       # +1 montée
    rows += [[100.4, 102.2, 100.2, 101.8, 700.0]]     # +2 sommet P1 = AR
    rows += [[101.0, 100.2, 99.0, 99.4, 600.0]]       # +3 repli
    rows += [[99.4, 99.6, 98.5, 99.0, 600.0]]         # +4 repli (confirme pivot)
    rows += [[99.0, 101.5, 98.8, 101.2, 800.0]]       # rallye…
    rows += [[101.2, 104.5, 101.0, 104.2, 1000.0]]
    rows += [[104.2, 108.5, 104.0, 107.8, 1400.0]]    # plus-haut TARDIF (piège)
    rows += _drift(4, 106.0, vol=700.0, seed=2)
    df = _df(rows)
    s = _scan(df, lookback=26, th=Thresholds(), bias="accumulation")
    ar = next(e for e in s.events if e.name == "AR")
    assert ar.bar_high < 104                       # l'AR reste au premier sommet (~102)
    assert df["high"].iloc[-12:].max() > 107       # un plus-haut existe bien plus tard


def test_st_at_trough_not_driest_mid_rise():
    """Le ST doit être au creux (premier pivot bas près du support), pas la barre la
    plus sèche au milieu d'une montée."""
    from screener.wyckoff import _scan, Thresholds
    rows = _drift(20, 110.0, seed=3)
    rows += [[110 - i, 110.3 - i, 109.6 - i, 109.9 - i, 900] for i in range(12)]  # markdown
    rows += [[100.0, 100.5, 95.0, 99.5, 3200.0]]      # SC
    rows += [[99.5, 103.0, 99.4, 102.6, 800.0]]       # AR (sommet)
    rows += [[101.5, 101.8, 98.0, 98.5, 600.0]]       # repli…
    rows += [[97.5, 97.8, 95.6, 96.4, 500.0]]         # ST = creux (low 95.6) près du support
    rows += _drift(6, 99.5, vol=600.0, seed=4)         # remontée
    rows += [[98.0, 98.2, 95.8, 96.2, 60.0]]          # barre ULTRA-sèche près support (piège)
    rows += _drift(3, 99.0, vol=600.0, seed=5)
    df = _df(rows)
    s = _scan(df, lookback=30, th=Thresholds(), bias="accumulation")
    st = next(e for e in s.events if e.name == "ST")
    assert abs(st.bar_low - 95.6) < 0.6            # ST posé au creux, pas sur la barre tardive
    assert st.vol_ratio > 0.2                       # pas la barre vol=60 (≈0.06)


def test_distribution_st_at_resistance_peak():
    """Miroir distribution : le ST est un sommet (lower-high) près de la résistance."""
    struct = detect_window_structure(_df(
        _drift(40, 100.0, seed=5)
        + [[100.0, 105.0, 99.6, 100.4, 3200.0]]      # BC (high 105)
        + [[100.4, 100.6, 97.0, 97.4, 800.0]]        # AR (creux)
        + _drift(4, 98.0, vol=600.0, seed=6)
        + [[103.6, 104.4, 103.2, 103.8, 500.0]]      # ST = sommet près de 105
        + _drift(3, 102.5, vol=600.0, seed=7)
        + [[102.0, 102.2, 95.5, 95.8, 2600.0]]       # SOW
        + _drift(2, 96.0, vol=700.0, seed=8)), lookback=20)
    st = next(e for e in struct.events if e.name == "ST")
    assert st.bar_high > 103                          # ST au sommet (résistance), pas en bas


def test_noise_without_real_reaction_rejected():
    """Un SC volumique suivi de bruit plat (pas de rebond ≥ 1 ATR) ne forme PAS une
    structure (rejette le bruit type CBRS/RKLB)."""
    from screener.wyckoff import _scan, Thresholds
    rows = _drift(20, 110.0, seed=7)
    rows += [[110 - i, 110.3 - i, 109.6 - i, 109.9 - i, 900] for i in range(10)]
    rows += [[100.0, 100.5, 95.0, 99.5, 3200.0]]      # SC
    rows += _drift(18, 96.0, vol=600.0, seed=8)        # bruit plat, aucun rebond franc
    s = _scan(_df(rows), lookback=30, th=Thresholds(), bias="accumulation")
    names = [e.name for e in s.events]
    assert names == ["SC"] or "AR" not in names        # pas d'AR fabriqué → pas de structure
