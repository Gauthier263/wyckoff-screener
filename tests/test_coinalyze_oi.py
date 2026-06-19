"""OI Binance live via Coinalyze : parsing de la réponse, mapping symbole, repli sans clé.
Hors-ligne : on mocke `requests.get` et la lecture de clé (aucune vraie clé en test)."""
import pandas as pd
import pytest

from screener import data as D


class _FakeResp:
    def __init__(self, status, payload=None, headers=None):
        self.status_code = status
        self._payload = payload
        self.headers = headers or {}

    def json(self):
        return self._payload

    def raise_for_status(self):
        pass


_HISTORY = [{
    "symbol": "BTCUSDT_PERP.A",
    "history": [
        {"t": 1_781_860_000, "o": 6.0e9, "h": 6.1e9, "l": 5.9e9, "c": 6.05e9},
        {"t": 1_781_860_300, "o": 6.05e9, "h": 6.2e9, "l": 6.0e9, "c": 6.15e9},
        {"t": 1_781_860_600, "o": 6.15e9, "h": 6.3e9, "l": 6.1e9, "c": 6.25e9},
    ],
}]


def test_symbol_mapping_binance_suffix():
    assert D._coinalyze_symbol("BTC/USDT") == "BTCUSDT_PERP.A"
    assert D._coinalyze_symbol("ETH/USDT", exch="A") == "ETHUSDT_PERP.A"


def test_series_and_ohlc_parsing(monkeypatch):
    monkeypatch.setattr(D, "_coinalyze_key", lambda: "FAKEKEY")
    import requests
    monkeypatch.setattr(requests, "get", lambda *a, **k: _FakeResp(200, _HISTORY))

    s = D.fetch_coinalyze_oi("BTC/USDT", "5m", limit=3)
    assert list(s.values) == [6.05e9, 6.15e9, 6.25e9]
    assert s.index.tz is not None                       # ts UTC

    o = D.fetch_coinalyze_oi("BTC/USDT", "5m", limit=3, ohlc=True)
    assert list(o.columns) == ["open", "high", "low", "close"]
    assert o["close"].iloc[-1] == 6.25e9 and o["high"].iloc[-1] == 6.3e9


def test_no_key_returns_none(monkeypatch):
    monkeypatch.setattr(D, "_coinalyze_key", lambda: None)
    assert D.fetch_coinalyze_oi("BTC/USDT", "5m") is None


def test_fetch_open_interest_binance_falls_back_to_okx_without_key(monkeypatch):
    # Pas de clé → la source 'binance' doit se replier sur l'agrégat OKX, pas planter.
    monkeypatch.setattr(D, "_coinalyze_key", lambda: None)
    called = {}

    def _fake_agg(symbol, tf, limit, source, start=None, end=None):
        called["source"] = source
        idx = pd.date_range("2026-06-19", periods=3, freq="5min", tz="UTC")
        return pd.Series([1.0, 2.0, 3.0], index=idx)

    monkeypatch.setattr(D, "_aggregate_oi", _fake_agg)
    out = D.fetch_open_interest("BTC/USDT", "5m", limit=3, source="binance")
    assert out is not None and called["source"] == "okx"   # repli effectif
    assert list(out["oi"].values) == [1.0, 2.0, 3.0]


def test_rate_limit_retry_then_success(monkeypatch):
    monkeypatch.setattr(D, "_coinalyze_key", lambda: "FAKEKEY")
    monkeypatch.setattr(D.time, "sleep", lambda *_: None)   # pas d'attente réelle
    seq = [_FakeResp(429, headers={"Retry-After": "0"}), _FakeResp(200, _HISTORY)]
    import requests
    monkeypatch.setattr(requests, "get", lambda *a, **k: seq.pop(0))
    s = D.fetch_coinalyze_oi("BTC/USDT", "5m", limit=3)
    assert s is not None and len(s) == 3                   # a réessayé après le 429
