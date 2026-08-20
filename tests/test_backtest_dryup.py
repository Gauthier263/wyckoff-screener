"""Test synthétique du backtest dryup : un coil d'accumulation suivi d'un markup doit
produire au moins un trade long gagnant (cible R atteinte). Hors-ligne."""
import numpy as np
import pandas as pd

from screener.backtest import BTParams, aggregate_by_score, backtest_dryup_symbol
from test_window import _drift, _spring_coil


def _markup_tail(n, start, end, seed=7):
    rng = np.random.default_rng(seed)
    rows = []
    step = (end - start) / n
    c = start
    for _ in range(n):
        o = c
        c = c + step + rng.normal(0, 0.2)
        h = max(o, c) + abs(rng.normal(0, 0.2))
        l = min(o, c) - abs(rng.normal(0, 0.2))
        rows.append([o, h, l, c, 700 * rng.uniform(0.8, 1.1)])
    return rows


def test_backtest_dryup_long_win_after_coil():
    rows = _drift(50, 92.0, seed=5)          # historique (warmup vol_ma/ATR)
    rows += _spring_coil()                    # markup préalable + coil d'accumulation (~98–101)
    rows += _markup_tail(24, 99.3, 113.0)     # markup franc après le coil → cible atteinte
    idx = pd.date_range("2024-01-01", periods=len(rows), freq="h", tz="UTC")
    df = pd.DataFrame(rows, columns=["open", "high", "low", "close", "volume"], index=idx)

    cfg = {"vol_ma": 20, "atr_period": 14, "dryup": 40}
    p = BTParams(stop_atr=0.3, rr=2.0, max_hold=40)
    is_tr, oos_tr = backtest_dryup_symbol("SYN/USDT", df, cfg, p, score_min=0.5)

    assert len(is_tr) >= 1                                  # au moins une entrée
    assert all(t.direction == "long" for t in is_tr)       # accumulation → long
    assert any(t.outcome == "win" for t in is_tr)          # la cible R est atteinte
    assert max(t.r for t in is_tr) > 0
    # l'agrégat par score renvoie un tableau exploitable
    agg = aggregate_by_score(is_tr)
    assert not agg.empty and {"n", "win%", "R_moy"}.issubset(agg.columns)
