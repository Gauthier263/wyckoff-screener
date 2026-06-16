"""
Tests sur données synthétiques pour les Order Blocks ICT. Aucune connexion réseau.

On fabrique une base plate (ATR ≈ 1), puis on injecte :
  - un OB haussier dont le retest **rebondit** (respecté),
  - un OB haussier dont le retest **clôture au travers** (cassé),
  - un OB haussier que le prix **ne revient jamais** tester (non testé).

    pytest -q
"""
import numpy as np
import pandas as pd

from screener.features import add_features
from screener.ob_screen import screen_symbol
from screener.orderblocks import OBThresholds, analyze_order_blocks, detect_order_blocks

COLS = ["open", "high", "low", "close", "volume"]


def _flat(n=40, px=100.0):
    """Bougies dojis serrées : range 1.0 → ATR ≈ 1, et c==o → aucun OB."""
    rows = [[px, px + 0.5, px - 0.5, px, 1000.0] for _ in range(n)]
    idx = pd.date_range("2024-01-01", periods=n, freq="h", tz="UTC")
    return pd.DataFrame(rows, columns=COLS, index=idx)


def _with(rows):
    base = _flat()
    extra = pd.DataFrame(rows, columns=COLS,
                         index=pd.date_range("2024-02-01", periods=len(rows), freq="h", tz="UTC"))
    df = pd.concat([base, extra])
    return add_features(df, vol_ma=20, atr_period=14)


# Bougie OB haussière commune : down candle, corps top=100 / bottom=99, puis impulsion ↑.
_OB_AND_IMPULSE = [
    [100.0, 100.1, 98.9, 99.0, 1000.0],    # OB : bougie baissière
    [99.1, 102.6, 99.0, 102.5, 3000.0],    # impulsion 1 (up)
    [102.5, 103.5, 102.0, 103.3, 3000.0],  # impulsion 2 (up) → sommet 103.5
    [103.0, 103.1, 100.5, 100.8, 1000.0],  # repli (reste au-dessus de la zone)
]


def _ob_at(obs, idx):
    """L'OB formé sur une barre donnée (les scénarios créent aussi des OB annexes)."""
    return next(o for o in obs if o.idx == idx)


def test_flat_base_has_no_ob():
    feat = add_features(_flat(60), vol_ma=20, atr_period=14)
    assert detect_order_blocks(feat) == []


def test_bullish_ob_detected_with_displacement():
    feat = _with(_OB_AND_IMPULSE)
    obs = detect_order_blocks(feat)
    assert len(obs) == 1, obs
    ob = obs[0]
    assert ob.bias == "bullish"
    assert abs(ob.top - 100.0) < 1e-6 and abs(ob.bottom - 99.0) < 1e-6
    assert ob.displacement >= 2.0


def test_bullish_ob_respected():
    feat = _with(_OB_AND_IMPULSE + [
        [100.6, 101.0, 99.5, 100.5, 1000.0],  # retest : low ≤ top, tient
        [100.7, 102.0, 100.5, 101.8, 1000.0],  # rebond ≥ 1.5 ATR au-dessus de la zone
    ])
    ob = _ob_at(analyze_order_blocks(feat), 40)
    assert ob.outcome == "respecté", (ob.outcome, ob.mfe_R)
    assert ob.mfe_R >= 1.5


def test_bullish_ob_broken():
    feat = _with(_OB_AND_IMPULSE + [
        [100.6, 100.8, 99.5, 99.8, 1000.0],   # retest faible (mfe < seuil)
        [99.7, 99.9, 98.5, 98.7, 2000.0],     # clôture du corps sous la zone → cassé
    ])
    ob = _ob_at(analyze_order_blocks(feat), 40)
    assert ob.outcome == "cassé", (ob.outcome, ob.mfe_R)


def test_bullish_ob_not_tested():
    feat = _with(_OB_AND_IMPULSE + [
        [103.5, 104.5, 103.0, 104.2, 1000.0],  # le prix s'éloigne et ne revient jamais
        [104.2, 105.0, 103.8, 104.8, 1000.0],
    ])
    ob = _ob_at(analyze_order_blocks(feat), 40)
    assert ob.outcome == "non_testé", ob.outcome


def test_bearish_ob_respected():
    # Miroir : bougie haussière (OB) → impulsion ↓, retest par le bas, rebond baissier.
    feat = _with([
        [100.0, 101.1, 99.9, 101.0, 1000.0],   # OB : bougie haussière (top=101, bottom=100)
        [100.9, 101.0, 97.5, 97.6, 3000.0],    # impulsion 1 (down)
        [97.6, 98.0, 96.5, 96.7, 3000.0],      # impulsion 2 (down) → creux 96.5
        [96.9, 99.5, 96.8, 99.2, 1000.0],      # repli (reste sous la zone)
        [99.4, 100.5, 99.3, 99.5, 1000.0],     # retest : high ≥ bottom, tient
        [99.4, 99.6, 98.0, 98.2, 1000.0],      # rebond ≥ 1.5 ATR sous la zone
    ])
    ob = _ob_at(analyze_order_blocks(feat), 40)
    assert ob.bias == "bearish"
    assert abs(ob.top - 101.0) < 1e-6 and abs(ob.bottom - 100.0) < 1e-6
    assert ob.outcome == "respecté", (ob.outcome, ob.mfe_R)


def test_screen_symbol_aggregates():
    feat = _with(_OB_AND_IMPULSE + [
        [100.6, 101.0, 99.5, 100.5, 1000.0],
        [100.7, 102.0, 100.5, 101.8, 1000.0],
    ])
    stats = screen_symbol("TEST/USDT", feat, OBThresholds(), min_tests=1)
    assert stats is not None
    assert stats.n_ob >= 1 and stats.n_test >= 1
    assert stats.respect_rate == 100.0
    assert stats.score > 0
