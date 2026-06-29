"""CVD (Cumulative Volume Delta) — tests hors-ligne.

On mocke `requests.get` et les fonctions réseau pour valider :
- Le parsing des klines spot (colonne 9 = taker_buy_base_asset_volume)
- Le parsing des klines futures archive (zip, colonnes 0/5/9)
- La fusion archive + spot dans `fetch_cvd`
- Les features de divergence dans `add_cvd_features`
- L'absorption (vol fort + spread faible)
"""
from __future__ import annotations

import io
import zipfile
import pandas as pd
import pytest
import numpy as np

from screener import data as D
from screener.features import add_cvd_features, add_features


# ── helpers ──────────────────────────────────────────────────────────────────

def _make_kline_row(ts_ms: int, volume: float, buy_vol: float, price: float = 100.0) -> list:
    """Simule une ligne de réponse klines Binance (12 colonnes)."""
    return [ts_ms, price, price + 1, price - 1, price, volume,
            ts_ms + 3_600_000, volume * price, 1000, buy_vol, buy_vol * price, "0"]


def _make_kline_rows(n: int = 5) -> list[list]:
    base_ts = 1_700_000_000_000
    rows = []
    for i in range(n):
        vol = 100.0 + i * 10
        buy = vol * 0.6  # 60 % acheteurs nets → delta positif
        rows.append(_make_kline_row(base_ts + i * 3_600_000, vol, buy, price=50_000.0 + i * 100))
    return rows


class _FakeResp:
    def __init__(self, status: int, payload=None):
        self.status_code = status
        self._payload = payload
        self.headers = {}

    def json(self):
        return self._payload


def _make_futures_zip(n: int = 3) -> bytes:
    """Crée un zip de klines futures (colonnes 0, 5, 9) en mémoire."""
    base_ts = 1_700_000_000_000
    lines = []
    for i in range(n):
        vol = 200.0 + i * 20
        buy = vol * 0.4   # 40 % → delta négatif
        cols = [""] * 12
        cols[0] = str(base_ts + i * 3_600_000)
        cols[5] = str(vol)
        cols[9] = str(buy)
        lines.append(",".join(cols))
    csv_bytes = "\n".join(lines).encode()
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("data.csv", csv_bytes)
    return buf.getvalue()


# ── tests data.fetch_cvd_spot ────────────────────────────────────────────────

def test_fetch_cvd_spot_parsing(monkeypatch, tmp_path):
    monkeypatch.setattr(D, "CACHE_DIR", str(tmp_path))
    rows = _make_kline_rows(5)
    import requests
    monkeypatch.setattr(requests, "get", lambda *a, **k: _FakeResp(200, rows))

    df = D.fetch_cvd_spot("BTC/USDT", "1h", limit=5, use_cache=False)
    assert df is not None
    assert list(df.columns) == ["buy_vol", "sell_vol", "delta", "cvd"]
    assert df.index.tz is not None  # UTC
    # 60 % buy_vol → delta positif
    assert (df["delta"] > 0).all()
    # CVD croissant (delta toujours positif)
    assert (df["cvd"].diff().dropna() > 0).all()


def test_fetch_cvd_spot_http_error(monkeypatch, tmp_path):
    monkeypatch.setattr(D, "CACHE_DIR", str(tmp_path))
    import requests
    monkeypatch.setattr(requests, "get", lambda *a, **k: _FakeResp(451))
    assert D.fetch_cvd_spot("BTC/USDT", "1h", use_cache=False) is None


# ── tests data.fetch_cvd_futures_archive ────────────────────────────────────

def test_fetch_cvd_futures_archive_parsing(monkeypatch, tmp_path):
    monkeypatch.setattr(D, "CACHE_DIR", str(tmp_path))
    monkeypatch.setattr(D, "_archive_days", lambda *a, **k: ["2024-01-15"])
    import requests
    monkeypatch.setattr(requests, "get",
                        lambda *a, **k: _FakeResp(200) if False else
                        type("R", (), {"status_code": 200, "content": _make_futures_zip(3),
                                       "headers": {}})())

    df = D.fetch_cvd_futures_archive("BTC/USDT", "1h", days=1)
    assert df is not None
    assert "delta" in df.columns and "cvd" in df.columns
    # 40 % buy → delta négatif
    assert (df["delta"] < 0).all()


def test_fetch_cvd_futures_archive_no_dates(monkeypatch, tmp_path):
    monkeypatch.setattr(D, "CACHE_DIR", str(tmp_path))
    monkeypatch.setattr(D, "_archive_days", lambda *a, **k: [])
    assert D.fetch_cvd_futures_archive("BTC/USDT", "1h") is None


# ── tests data.fetch_cvd (fusion) ────────────────────────────────────────────

def _make_cvd_df(n: int, base_ts_s: int, delta_sign: float = 1.0) -> pd.DataFrame:
    idx = pd.date_range(pd.Timestamp(base_ts_s, unit="s", tz="UTC"), periods=n, freq="1h")
    vol = 100.0
    buy = vol * (0.6 if delta_sign > 0 else 0.4)
    sell = vol - buy
    delta = (buy - sell) * np.ones(n)
    df = pd.DataFrame({"buy_vol": buy, "sell_vol": sell, "delta": delta,
                        "cvd": delta.cumsum()}, index=idx)
    return df


def test_fetch_cvd_spot_only(monkeypatch, tmp_path):
    monkeypatch.setattr(D, "CACHE_DIR", str(tmp_path))
    spot = _make_cvd_df(10, 1_700_000_000)
    monkeypatch.setattr(D, "fetch_cvd_spot", lambda *a, **k: spot)
    monkeypatch.setattr(D, "fetch_cvd_futures_archive", lambda *a, **k: None)
    result = D.fetch_cvd("BTC/USDT")
    assert result is not None
    assert len(result) == 10


def test_fetch_cvd_fusion_recumulates(monkeypatch, tmp_path):
    monkeypatch.setattr(D, "CACHE_DIR", str(tmp_path))
    arch = _make_cvd_df(5, 1_700_000_000, delta_sign=1.0)
    spot = _make_cvd_df(5, 1_700_018_000, delta_sign=-1.0)  # 5h après
    monkeypatch.setattr(D, "fetch_cvd_spot", lambda *a, **k: spot)
    monkeypatch.setattr(D, "fetch_cvd_futures_archive", lambda *a, **k: arch)

    result = D.fetch_cvd("BTC/USDT", limit=100)
    assert result is not None
    # CVD re-cumulé sur toute la série fusionnée
    expected_cvd = result["delta"].cumsum()
    pd.testing.assert_series_equal(result["cvd"].reset_index(drop=True),
                                   expected_cvd.reset_index(drop=True), check_names=False)


def test_fetch_cvd_both_none(monkeypatch, tmp_path):
    monkeypatch.setattr(D, "CACHE_DIR", str(tmp_path))
    monkeypatch.setattr(D, "fetch_cvd_spot", lambda *a, **k: None)
    monkeypatch.setattr(D, "fetch_cvd_futures_archive", lambda *a, **k: None)
    assert D.fetch_cvd("BTC/USDT") is None


# ── tests features.add_cvd_features ─────────────────────────────────────────

def _make_ohlcv(n: int = 40) -> pd.DataFrame:
    idx = pd.date_range("2024-01-01", periods=n, freq="1h", tz="UTC")
    np.random.seed(42)
    close = 50_000 + np.cumsum(np.random.randn(n) * 200)
    df = pd.DataFrame({
        "open": close - 50, "high": close + 100, "low": close - 100,
        "close": close, "volume": np.random.uniform(100, 500, n),
    }, index=idx)
    return add_features(df)


def test_add_cvd_features_columns(monkeypatch):
    df = _make_ohlcv(40)
    idx = df.index
    delta = np.random.randn(40) * 50
    cvd_df = pd.DataFrame({
        "buy_vol": 200.0, "sell_vol": 150.0,
        "delta": delta, "cvd": delta.cumsum(),
    }, index=idx)
    out = add_cvd_features(df, cvd_df)
    for col in ("cvd_delta", "cvd", "cvd_div_bull", "cvd_div_bear", "absorption"):
        assert col in out.columns, f"colonne manquante : {col}"


def test_cvd_div_bull_at_low_with_positive_delta():
    """Prix au creux de la fenêtre + delta positif → divergence haussière."""
    n = 30
    idx = pd.date_range("2024-01-01", periods=n, freq="1h", tz="UTC")
    # Prix décroissant (lows toujours plus bas) mais delta positif
    close = np.linspace(51_000, 50_000, n)
    df = pd.DataFrame({
        "open": close - 20, "high": close + 50, "low": close - 80,
        "close": close, "volume": 300.0,
    }, index=idx)
    df = add_features(df)
    delta_vals = np.ones(n) * 50  # toujours positif
    cvd_df = pd.DataFrame({
        "buy_vol": 175.0, "sell_vol": 125.0,
        "delta": delta_vals, "cvd": delta_vals.cumsum(),
    }, index=idx)
    out = add_cvd_features(df, cvd_df, window=20)
    # Les dernières barres sont au bas de la fenêtre + delta positif → div bull
    assert out["cvd_div_bull"].iloc[-5:].any(), "aucune divergence haussière détectée"


def test_absorption_high_vol_low_spread():
    n = 20
    idx = pd.date_range("2024-01-01", periods=n, freq="1h", tz="UTC")
    close = np.ones(n) * 50_000
    # Barres normales (larges) pour faire monter l'ATR, puis barres d'absorption
    # (spread quasi nul = 10 vs ~400 pour les normales) à fort volume.
    high = np.where(np.arange(n) > 15, close + 10, close + 200)
    low = np.where(np.arange(n) > 15, close - 10, close - 200)
    df = pd.DataFrame({
        "open": close, "high": high, "low": low, "close": close,
        "volume": np.where(np.arange(n) > 15, 600.0, 200.0),
    }, index=idx)
    df = add_features(df)
    cvd_df = pd.DataFrame({
        "buy_vol": 100.0, "sell_vol": 100.0,
        "delta": np.zeros(n), "cvd": np.zeros(n),
    }, index=idx)
    out = add_cvd_features(df, cvd_df)
    # spread_atr ≈ 0.05 (10/200) et vol_ratio ≈ 3× → absorption marquée
    assert out["absorption"].iloc[16:].any(), "aucune barre d'absorption détectée"
