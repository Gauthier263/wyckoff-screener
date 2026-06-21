"""Fix #2 — l'archive Binance périmée (J-1) ne doit pas être reportée à plat dans l'OI
*live* : on mesure son retard via `_archive_lag_hours` et on l'exclut au-delà du seuil."""
import numpy as np
import pandas as pd

from screener.data import _ARCHIVE_MAX_LAG_H, _archive_lag_hours


def _series(last, n=5):
    idx = pd.date_range(end=last, periods=n, freq="5min", tz="UTC")
    return pd.Series(np.arange(n, dtype=float), index=idx)


def test_lag_hours_measures_delay():
    now = pd.Timestamp("2026-06-19 12:00", tz="UTC")
    s = _series(pd.Timestamp("2026-06-19 02:00", tz="UTC"))
    assert _archive_lag_hours(s, now) == 10.0


def test_lag_none_when_empty():
    now = pd.Timestamp("2026-06-19 12:00", tz="UTC")
    assert _archive_lag_hours(None, now) is None
    assert _archive_lag_hours(pd.Series(dtype=float), now) is None


def test_threshold_separates_fresh_from_stale():
    now = pd.Timestamp("2026-06-19 12:00", tz="UTC")
    fresh = _series(now - pd.Timedelta(hours=2))
    stale = _series(now - pd.Timedelta(hours=10))
    assert _archive_lag_hours(fresh, now) <= _ARCHIVE_MAX_LAG_H     # gardée dans l'agrégat live
    assert _archive_lag_hours(stale, now) > _ARCHIVE_MAX_LAG_H      # exclue de l'agrégat live
