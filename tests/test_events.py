"""
Tests sur données synthétiques : on fabrique des plages avec un spring ou un UTAD
clairs, et on vérifie que les détecteurs les retrouvent. Aucune connexion réseau.

    pytest -q
"""
import numpy as np
import pandas as pd

from screener.events import detect_events
from screener.features import add_features, detect_trading_range, swing_points


def _range_base(n=100, low=100.0, high=110.0, seed=0):
    """Construit n barres oscillant proprement dans [low, high]."""
    rng = np.random.default_rng(seed)
    mid = (low + high) / 2
    amp = (high - low) / 2 * 0.8
    closes = mid + amp * np.sin(np.linspace(0, 6 * np.pi, n)) + rng.normal(0, 0.2, n)
    rows = []
    for c in closes:
        o = c + rng.normal(0, 0.1)
        h = max(o, c) + abs(rng.normal(0, 0.3))
        l = min(o, c) - abs(rng.normal(0, 0.3))
        h = min(h, high)          # contenu dans la plage
        l = max(l, low)
        rows.append([o, h, l, c, rng.uniform(900, 1100)])
    idx = pd.date_range("2024-01-01", periods=n, freq="h", tz="UTC")
    return pd.DataFrame(rows, columns=["open", "high", "low", "close", "volume"], index=idx)


def _append(df, o, h, l, c, v):
    idx = df.index[-1] + (df.index[-1] - df.index[-2])
    return pd.concat([df, pd.DataFrame([[o, h, l, c, v]],
                     columns=["open", "high", "low", "close", "volume"], index=[idx])])


def _analyze(df):
    df = add_features(df, vol_ma=20, atr_period=14)
    df = swing_points(df)
    tr = detect_trading_range(df, lookback=80, buffer=5)
    return tr, detect_events(df, tr, buffer=5)


def test_range_is_valid():
    tr, _ = _analyze(_range_base())
    assert tr.is_valid
    assert tr.low < tr.high


def test_spring_detected():
    df = _range_base()
    # barre de spring : plonge sous 100 puis clôture nettement à l'intérieur
    df = _append(df, 100.5, 101.0, 97.5, 100.6, 1000)
    tr, events = _analyze(df)
    names = [e.name for e in events]
    assert "SPRING" in names, names


def test_utad_detected():
    df = _range_base()
    # upthrust : pique au-dessus de 110 puis clôture sous la résistance
    df = _append(df, 109.5, 112.5, 109.0, 109.4, 1000)
    tr, events = _analyze(df)
    names = [e.name for e in events]
    assert "UTAD" in names, names


def test_sos_detected():
    df = _range_base()
    # cassure haussière franche avec volume et clôture haute
    df = _append(df, 110.0, 113.0, 109.8, 112.8, 2500)
    tr, events = _analyze(df)
    names = [e.name for e in events]
    assert "SOS" in names, names


def test_neutral_range_has_few_events():
    tr, events = _analyze(_range_base(seed=3))
    # une plage calme ne doit pas crouler sous les signaux de cassure
    breakout = [e for e in events if e.name in ("SOS", "SOW", "SPRING", "UTAD")]
    assert len(breakout) == 0, [e.name for e in events]
