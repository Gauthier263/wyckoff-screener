"""Test du filtre de régime : hausse → +1, baisse → −1, plat → 0 (causal)."""
import numpy as np
import pandas as pd

from screener.features import market_regime


def _df(closes):
    idx = pd.date_range("2024-01-01", periods=len(closes), freq="h", tz="UTC")
    c = np.asarray(closes, float)
    return pd.DataFrame({"open": c, "high": c + 1, "low": c - 1, "close": c, "volume": 1.0}, index=idx)


def test_regime_uptrend_bull():
    reg = market_regime(_df(np.linspace(100, 200, 120)), ma=50, slope=10)
    assert reg.iloc[-1] == 1


def test_regime_downtrend_bear():
    reg = market_regime(_df(np.linspace(200, 100, 120)), ma=50, slope=10)
    assert reg.iloc[-1] == -1


def test_regime_flat_neutral():
    rng = np.random.default_rng(0)
    reg = market_regime(_df(100 + rng.normal(0, 0.3, 120)), ma=50, slope=10)
    assert reg.iloc[-1] == 0


def test_regime_causal_no_lookahead():
    # la valeur à t ne doit dépendre que du passé : tronquer après t ne la change pas
    c = np.concatenate([np.linspace(100, 150, 80), np.linspace(150, 90, 40)])
    full = market_regime(_df(c), ma=50, slope=10)
    trunc = market_regime(_df(c[:80]), ma=50, slope=10)
    assert full.iloc[79] == trunc.iloc[79]
