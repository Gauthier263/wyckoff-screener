"""Fix #1 — une venue qui refuse le TF demandé (ex. OKX en 15m) ne doit plus être
silencieusement exclue : `_oi_series` se rabat sur une base 5 min puis resample."""
import pandas as pd
import pytest

from screener.data import _oi_series


class _FakeOKX:
    """Mime ccxt OKX : n'accepte que 5m/1h/1d en historique d'OI, lève sinon."""

    id = "okx"

    def __init__(self):
        self.markets = {"BTC/USDT:USDT": {}}
        self.calls = []

    def fetch_open_interest_history(self, perp, timeframe, limit=0):
        self.calls.append(timeframe)
        if timeframe not in ("5m", "1h", "1d"):
            raise Exception("okx fetchOpenInterestHistory cannot only use the 5m, 1h, and 1d timeframe")
        # 6 points 5m croissants -> 2 buckets 15m
        idx = pd.date_range("2026-06-19 09:00", periods=6, freq="5min", tz="UTC")
        vals = [100, 101, 102, 103, 104, 105]
        return [{"timestamp": int(t.timestamp() * 1000), "openInterestValue": v}
                for t, v in zip(idx, vals)]


def test_okx_15m_falls_back_to_5m_resample():
    ex = _FakeOKX()
    s = _oi_series(ex, "BTC/USDT", "15m", limit=20)
    assert s is not None and len(s) >= 1          # plus None : la venue est bien incluse
    # le repli passe par 5m (le 15m direct n'est même pas tenté car connu non supporté)
    assert "5m" in ex.calls and "15m" not in ex.calls
    # resample 'last' : le bucket 09:00 prend la dernière obs (09:10 -> 102)
    assert s.iloc[0] == 102


def test_supported_tf_uses_direct_call():
    ex = _FakeOKX()
    s = _oi_series(ex, "BTC/USDT", "5m", limit=20)
    assert s is not None and ex.calls == ["5m"]   # pas de repli inutile
    assert list(s.values) == [100, 101, 102, 103, 104, 105]


def test_missing_perp_returns_none():
    ex = _FakeOKX()
    ex.markets = {}
    assert _oi_series(ex, "BTC/USDT", "15m", limit=20) is None
