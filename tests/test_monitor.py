"""
Tests synthétiques du mode suivi (monitor.py). Hors-ligne.

On fabrique une distribution propre (BC → AR → ST → SOW) dont le SOW tombe sur la
dernière barre clôturée, et on vérifie que :
  - en anticipant une distribution, l'état passe à ALERT (déclencheur frais SOW) ;
  - sans déclencheur frais (schéma encore en construction), l'état est WATCH ;
  - une dérive plate ne lève rien (NONE) ;
  - l'alignement sur la clôture de barre et le parsing de timeframe sont corrects.
"""
import numpy as np
import pandas as pd

from screener.features import add_features
from screener.monitor import (
    monitor_once,
    seconds_to_next_close,
    timeframe_seconds,
)


def _df(rows):
    idx = pd.date_range("2024-01-01", periods=len(rows), freq="h", tz="UTC")
    df = pd.DataFrame(rows, columns=["open", "high", "low", "close", "volume"], index=idx)
    return add_features(df, vol_ma=20, atr_period=14)


def _drift(n, base, vol=1000.0, seed=0):
    rng = np.random.default_rng(seed)
    rows, c = [], base
    for _ in range(n):
        c = c + rng.normal(0, 0.4)
        o = c + rng.normal(0, 0.3)
        h = max(o, c) + abs(rng.normal(0, 0.3))
        l = min(o, c) - abs(rng.normal(0, 0.3))
        rows.append([o, h, l, c, vol * rng.uniform(0.8, 1.1)])
    return rows


def _distribution_rows():
    rows = _drift(40, 100.0, seed=5)
    rows += [[100.0, 105.0, 99.6, 100.4, 3200.0]]   # BC
    rows += [[100.4, 100.6, 97.0, 97.4, 800.0]]      # AR
    rows += _drift(4, 98.0, vol=600.0, seed=6)
    rows += [[103.6, 104.4, 103.2, 103.8, 500.0]]    # ST
    rows += _drift(3, 102.5, vol=600.0, seed=7)
    rows += [[102.0, 102.2, 95.5, 95.8, 2600.0]]     # SOW (dernière barre = déclencheur frais)
    return rows


def test_alert_on_fresh_sow():
    snap = monitor_once(_df(_distribution_rows()), expect="distribution", lookback=20)
    assert snap.state == "ALERT"
    assert snap.fresh_signal is not None
    assert snap.fresh_signal.bias == "distribution"
    assert snap.schema_bias == "distribution"
    assert snap.progress >= 0.75            # séquence quasi complète (BC/AR/ST/SOW)


def test_watch_before_trigger():
    # Même schéma mais on coupe avant le SOW : pas de déclencheur frais → WATCH.
    rows = _distribution_rows()[:-1]
    rows += _drift(2, 102.0, vol=600.0, seed=11)     # barres calmes, aucun signe frais
    snap = monitor_once(_df(rows), expect="distribution", lookback=20)
    assert snap.state in {"WATCH", "NONE"}
    assert snap.fresh_signal is None


def test_none_on_flat_drift():
    snap = monitor_once(_df(_drift(80, 100.0, seed=9)), expect="distribution", lookback=30)
    assert snap.state == "NONE"
    assert snap.fresh_signal is None


def test_contrary_schema_is_not_alert():
    # On anticipe une accumulation alors que c'est une distribution : pas d'ALERT.
    snap = monitor_once(_df(_distribution_rows()), expect="accumulation", lookback=20)
    assert snap.state != "ALERT"


def test_timeframe_and_cadence():
    assert timeframe_seconds("5m") == 300
    assert timeframe_seconds("1h") == 3600
    assert timeframe_seconds("4h") == 14400
    # À 12:00:00 pile, la prochaine clôture 5m est dans 300 s (+ marge offset).
    t0 = 1_700_000_000 - (1_700_000_000 % 300)
    assert abs(seconds_to_next_close("5m", now=t0, offset=0) - 300) < 1e-6
