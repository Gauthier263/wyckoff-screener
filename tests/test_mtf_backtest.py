"""
Tests MTF + backtest (données synthétiques, hors-ligne).
    pytest -q
"""
import numpy as np
import pandas as pd

from screener.backtest import BTParams, aggregate, backtest_symbol
from screener.events import Event
from screener.features import TradingRange
from screener.mtf import combine_mtf
from screener.score import SymbolResult


def _tr(valid=True):
    return TradingRange(low=100.0, high=110.0, mid=105.0, height=10.0,
                        height_atr=8.0, is_valid=valid)


def _res(bias, events, score=0.5):
    return SymbolResult("X/USDT", bias, "C", events[0].name if events else "—",
                        0, score, 105.0, _tr(), 5.0, 5.0, events)


def test_mtf_confluence_boost():
    spring = Event("SPRING", "accumulation", 0, 0.8, 100.5)
    res_l = _res("accumulation", [spring], score=0.5)
    res_h = _res("accumulation", [Event("SOS", "accumulation", 1, 0.7, 109)], score=0.6)
    m = combine_mtf("X/USDT", "4h", "1h", res_h, res_l)
    assert m.confluence == 1.5          # HTF aligné + déclencheur LTF
    assert m.score > res_l.score


def test_mtf_conflict_penalty():
    res_l = _res("accumulation", [Event("SPRING", "accumulation", 0, 0.8, 100.5)])
    res_h = _res("distribution", [Event("UTAD", "distribution", 1, 0.7, 110.5)])
    m = combine_mtf("X/USDT", "4h", "1h", res_h, res_l)
    assert m.confluence == 0.5          # conflit HTF/LTF


def _series_with_springs(n=320, low=100.0, high=110.0, period=40, seed=1):
    rng = np.random.default_rng(seed)
    mid = (low + high) / 2
    amp = (high - low) / 2 * 0.7
    rows = []
    for i in range(n):
        c = mid + amp * np.sin(i / 5) + rng.normal(0, 0.2)
        o = c + rng.normal(0, 0.1)
        h = min(max(o, c) + abs(rng.normal(0, 0.3)), high)
        l = max(min(o, c) - abs(rng.normal(0, 0.3)), low)
        v = rng.uniform(900, 1100)
        # tous les `period` bars : un spring (plonge sous le support, clôture dedans)
        if i > 120 and i % period == 0:
            l = low - 3.0
            c = mid
            o = mid - 1
            h = mid + 0.5
            v = 1000
        rows.append([o, h, l, c, v])
    idx = pd.date_range("2024-01-01", periods=n, freq="h", tz="UTC")
    return pd.DataFrame(rows, columns=["open", "high", "low", "close", "volume"], index=idx)


def test_backtest_generates_trades_and_stats():
    df = _series_with_springs()
    cfg = dict(lookback=80, buffer=5, vol_ma=20, atr_period=14, thresholds={})
    trades = backtest_symbol("X/USDT", df, cfg, BTParams(stop_atr=1.0, rr=2.0, max_hold=20))
    assert len(trades) > 0
    assert all(t.outcome in ("win", "loss", "timeout") for t in trades)
    stats = aggregate(trades)
    assert {"event", "n", "win%", "R_moy", "profit_factor"}.issubset(stats.columns)
    assert (stats["event"] == "TOUS").any()


def test_backtest_no_lookahead_exit_after_entry():
    df = _series_with_springs()
    cfg = dict(lookback=80, buffer=5, vol_ma=20, atr_period=14, thresholds={})
    trades = backtest_symbol("X/USDT", df, cfg, BTParams())
    assert all(t.exit_i > t.entry_i for t in trades)   # sortie toujours après l'entrée
