"""
Tests de l'optimiseur (hors-ligne, données synthétiques).
    pytest -q
"""
import numpy as np
import pandas as pd

from screener.backtest import Trade
from screener.features import add_features
from screener.optimize import (
    grid_search, metric_value, overfit_report, trade_stats, walk_forward,
)
from tests.test_mtf_backtest import _series_with_springs


def _mk_trades(rs):
    return [Trade("X", "SPRING", "long", i, 1, 0, 2, i + 1, 1 + r, float(r), "x")
            for i, r in enumerate(rs)]


def test_metric_min_trades_floor():
    trades = _mk_trades([2.0, 2.0])           # excellente espérance mais 2 trades
    assert metric_value(trades, "robust", min_trades=30) == float("-inf")
    assert metric_value(trades, "robust", min_trades=1) > 0


def test_metric_robust_penalises_variance():
    stable = _mk_trades([0.5] * 40)
    noisy = _mk_trades([3, -2, 3, -2] * 10)   # même moyenne ~0.5 mais très dispersé
    m_stable = metric_value(stable, "robust", min_trades=10)
    m_noisy = metric_value(noisy, "robust", min_trades=10)
    assert m_stable > m_noisy                 # le robuste préfère la régularité


def _feats(n_symbols=4):
    feats = {}
    for s in range(n_symbols):
        df = _series_with_springs(n=360, period=35, seed=s + 1)
        feats[f"S{s}/USDT"] = add_features(df, vol_ma=20, atr_period=14)
    return feats


def test_grid_search_runs_and_ranks():
    cfg = dict(lookback=80, buffer=5, vol_ma=20, atr_period=14, thresholds={})
    small = {"rr": [1.5, 2.0], "stop_atr": [1.0, 1.5], "pen_atr": [0.1, 0.2]}
    res = grid_search(_feats(), cfg, grid=small, metric="robust",
                      min_trades=5, split=0.6)
    assert not res.empty
    # trié décroissant sur la métrique in-sample
    assert res["is_metric"].is_monotonic_decreasing
    assert {"is_n", "oos_n", "oos_r_moy"}.issubset(res.columns)


def test_overfit_report_verdict_present():
    cfg = dict(lookback=80, buffer=5, vol_ma=20, atr_period=14, thresholds={})
    small = {"rr": [2.0, 3.0], "stop_atr": [1.0]}
    res = grid_search(_feats(), cfg, grid=small, metric="robust", min_trades=5)
    rep = overfit_report(res)
    assert "verdict" in rep
    assert any(tag in rep["verdict"] for tag in ("ROBUSTE", "FRAGILE", "SURAJUSTEMENT"))


def test_walk_forward_runs():
    cfg = dict(lookback=80, buffer=5, vol_ma=20, atr_period=14, thresholds={})
    small = {"rr": [1.5, 2.0], "stop_atr": [1.0]}
    wf = walk_forward(_feats(), cfg, grid=small, metric="robust",
                      min_trades=3, folds=3)
    assert "fold" in wf.columns
    assert "val_r_moy" in wf.columns


def _series_with_drops(n=400, period=30, seed=0):
    """Marche aléatoire calme entrecoupée de chutes violentes périodiques (vol ×6)."""
    rng = np.random.default_rng(seed)
    rows, c = [], 100.0
    for k in range(n):
        if k > 60 and k % period == 0:                 # chute brutale one-sided
            o, lo, cl = c, c - 12.0, c - 11.5
            rows.append([o, o + 0.1, lo, cl, 6000.0])
            c = cl
        else:
            c = c + rng.normal(0, 0.4)
            o = c + rng.normal(0, 0.3)
            h, l = max(o, c) + abs(rng.normal(0, 0.3)), min(o, c) - abs(rng.normal(0, 0.3))
            rows.append([o, h, l, c, 1000 * rng.uniform(0.8, 1.1)])
    idx = pd.date_range("2024-01-01", periods=len(rows), freq="h", tz="UTC")
    df = pd.DataFrame(rows, columns=["open", "high", "low", "close", "volume"], index=idx)
    return add_features(df, vol_ma=20, atr_period=14)


def _void_feats(n_symbols=4):
    return {f"S{s}/USDT": _series_with_drops(seed=s + 1) for s in range(n_symbols)}


def test_grid_search_void_mode():
    cfg = dict(lookback=80, buffer=5, vol_ma=20, atr_period=14, void={})
    # require_uptrend=False pour garantir des trades quelle que soit la tendance synthétique
    grid = {"ret_z": [-2.0, -2.5], "fill_target": [0.5, 0.75],
            "z_window": [20], "require_uptrend": [False]}
    res = grid_search(_void_feats(), cfg, grid=grid, metric="robust",
                      min_trades=3, split=0.6, mode="void")
    assert not res.empty
    assert res["is_metric"].is_monotonic_decreasing
    assert {"ret_z", "fill_target", "is_n", "oos_n", "oos_r_moy"}.issubset(res.columns)
