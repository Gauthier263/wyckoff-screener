"""Test de la fusion multi-venues de l'OI (_combine_oi) : somme + comblage des trous."""
import numpy as np
import pandas as pd

from screener.data import _combine_oi


def _series(start, n, val):
    idx = pd.date_range(start, periods=n, freq="1h", tz="UTC")
    return pd.Series(np.full(n, val, dtype=float), index=idx)


def test_combine_sums_aligned_series():
    a = _series("2026-06-15 00:00", 5, 1.0)
    b = _series("2026-06-15 00:00", 5, 2.0)
    out = _combine_oi([a, b])
    assert (out == 3.0).all() and len(out) == 5


def test_combine_no_cliff_when_one_venue_ends_early():
    # OKX/Gate couvrent 8h ; Binance s'arrête à la 5e (retard d'archive).
    live = _series("2026-06-15 00:00", 8, 2.0)            # okx+gate combinés
    binance = _series("2026-06-15 00:00", 5, 6.0)         # s'arrête tôt
    out = _combine_oi([live, binance])
    assert len(out) == 8
    # pas de falaise : la valeur Binance est reportée (carry) après sa fin
    assert out.iloc[4] == 8.0          # 2 + 6 (zone couverte)
    assert out.iloc[-1] == 8.0         # 2 + 6 (Binance carry-forward, pas de chute à 2)
    assert out.min() == 8.0            # aucun point ne retombe au seul niveau live


def test_combine_handles_none_and_empty():
    a = _series("2026-06-15 00:00", 3, 1.0)
    assert _combine_oi([a, None]).equals(a)
    assert _combine_oi([None, None]) is None
    assert _combine_oi([]) is None
