"""
Tests synthétiques du détecteur de structure sur fenêtre (window.py).

On fabrique une séquence d'accumulation propre (SC → AR → ST → SOS) et son miroir
de distribution, puis on vérifie que `detect_window_structure` retrouve le bon
schéma, l'ordre des événements, et remplit théorie + justification. Hors-ligne.
"""
import numpy as np
import pandas as pd

from screener.features import add_features
from screener.window import detect_window_structure


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


def test_accumulation_spring_and_lps():
    """Séquence complète Phase A→D : SC → AR → ST → SPRING → SOS → LPS.

    Vérifie le resserrement de l'AR (rebond réflexe immédiat, volume en repli) et la
    reconnaissance du Spring (fausse cassure sous le plancher) puis du LPS (back-up sec)."""
    rows = _drift(40, 100.0, seed=11)                      # warmup vol_ma/ATR (~1000)
    rows += [[100.0, 100.5, 95.0, 99.5, 3200.0]]           # SC : climax, plancher 95.0
    rows += [[99.5, 103.0, 99.4, 102.6, 800.0]]            # AR : rebond réflexe, volume en repli (<1×)
    rows += _drift(2, 101.5, vol=600.0, seed=12)
    rows += [[96.6, 97.0, 95.6, 96.4, 500.0]]              # ST : test sec, creux plus haut
    rows += _drift(8, 99.0, vol=650.0, seed=13)            # Phase B (lows > 95)
    rows += [[96.0, 96.2, 94.2, 95.8, 900.0]]              # SPRING : sous 95.0 puis clôture rentrée
    rows += _drift(1, 97.0, vol=600.0, seed=14)
    rows += [[98.0, 104.5, 97.8, 104.2, 2600.0]]           # SOS : JAC large + volumique
    rows += _drift(1, 102.0, vol=700.0, seed=15)
    rows += [[102.0, 102.5, 100.5, 101.8, 500.0]]          # LPS : back-up sec, creux plus haut
    rows += _drift(2, 102.0, vol=700.0, seed=16)

    struct = detect_window_structure(_df(rows), lookback=20)
    names = [e.name for e in struct.events]
    assert struct.bias == "accumulation" and struct.is_valid
    assert names[0] == "SC"
    for ev in ("AR", "ST", "SPRING", "SOS", "LPS"):
        assert ev in names, f"{ev} manquant : {names}"
    # ordre chronologique respecté
    assert names == sorted(names, key=lambda nm: [e.ts for e in struct.events if e.name == nm][0])
    # l'AR validé porte bien un volume en repli (< 1×)
    ar = next(e for e in struct.events if e.name == "AR")
    assert ar.vol_ratio < 1.0


def test_ar_gated_by_open_interest():
    """L'AR n'est validé que si l'OI est EN REPLI (débouclage), en plus du volume."""
    rows = _drift(40, 100.0, seed=1)
    rows += [[100.0, 100.5, 95.0, 99.5, 3200.0]]          # SC
    rows += [[99.5, 103.0, 99.4, 102.6, 800.0]]           # AR (volume en repli)
    rows += _drift(4, 102.0, vol=600.0, seed=2)
    rows += [[96.6, 97.0, 95.6, 96.4, 500.0]]             # ST
    rows += _drift(3, 97.5, vol=600.0, seed=3)
    rows += [[98.0, 104.5, 97.8, 104.2, 2600.0]]          # SOS
    rows += _drift(2, 104.0, vol=700.0, seed=4)
    df = _df(rows)
    n = len(df)
    rising = pd.DataFrame({"oi": np.linspace(1000, 2000, n)}, index=df.index)
    falling = pd.DataFrame({"oi": np.linspace(2000, 1000, n)}, index=df.index)

    up = detect_window_structure(df, lookback=20, oi=rising)
    dn = detect_window_structure(df, lookback=20, oi=falling)
    assert "AR" not in [e.name for e in up.events]        # OI en hausse → AR refusé
    assert "AR" in [e.name for e in dn.events]            # OI en repli → AR validé
    ar = next(e for e in dn.events if e.name == "AR")
    assert ar.oi_chg < 0                                   # ΔOI annoté (négatif)


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
