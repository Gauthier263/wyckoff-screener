"""Test synthétique : RSI de Wilder + divergence prix/RSI aux pivots.

Tierce de repli (n'exige que l'OHLCV, contrairement à CVD/OI) : signale un défaut
de confirmation momentum quand le prix fait un nouvel extrême mais le RSI non.
Bougies plates (high=low=close) pour isoler la logique sur la seule série de
clôtures ; `left=right=2` et `period=5` pour un warmup court.
"""
import numpy as np
import pandas as pd

from screener.features import rsi, add_rsi_divergence


def _flat(closes: list[float]) -> pd.DataFrame:
    idx = pd.date_range("2026-06-01", periods=len(closes), freq="4h", tz="UTC")
    return pd.DataFrame(
        {"open": closes, "high": closes, "low": closes, "close": closes,
         "volume": [1000.0] * len(closes)},
        index=idx,
    )


def test_rsi_monotonic_bounds():
    up = _flat([100 + 5 * i for i in range(20)])
    down = _flat([200 - 5 * i for i in range(20)])
    # hausse pure sans aucune perte -> RSI au plafond ; baisse pure -> RSI au plancher
    assert rsi(up, period=5).iloc[-1] == 100.0
    assert rsi(down, period=5).iloc[-1] == 0.0


def test_bearish_divergence_higher_high_weaker_rsi():
    # rallye 1 : monotone propre (RSI au plafond au pivot) ; rallye 2 : plus haut en
    # prix mais entrecoupé de pertes -> RSI plus faible au second pivot = divergence.
    closes = [100, 101, 100, 101, 100, 101, 100, 101,
              111, 121, 131, 141, 151,
              140, 130, 120, 110, 100,
              120, 100, 140, 160, 150, 145]
    out = add_rsi_divergence(_flat(closes), period=5, left=2, right=2)

    assert bool(out["swing_high"].iloc[12]) is True   # premier pivot (close=151)
    assert bool(out["swing_high"].iloc[21]) is True   # second pivot (close=160 > 151)
    assert out["rsi"].iloc[21] < out["rsi"].iloc[12]   # momentum plus faible malgré le plus-haut
    assert bool(out["rsi_bear_div"].iloc[21]) is True
    assert bool(out["rsi_bull_div"].iloc[21]) is False


def test_bullish_divergence_lower_low_stronger_rsi():
    # miroir exact du cas bear (inversion symétrique autour de 100) : creux plus bas
    # en prix mais RSI moins survendu au second pivot = divergence haussière.
    bear_closes = [100, 101, 100, 101, 100, 101, 100, 101,
                   111, 121, 131, 141, 151,
                   140, 130, 120, 110, 100,
                   120, 100, 140, 160, 150, 145]
    closes = [200 - c for c in bear_closes]
    out = add_rsi_divergence(_flat(closes), period=5, left=2, right=2)

    assert bool(out["swing_low"].iloc[12]) is True    # premier pivot (close=49)
    assert bool(out["swing_low"].iloc[21]) is True     # second pivot (close=40 < 49)
    assert out["rsi"].iloc[21] > out["rsi"].iloc[12]   # momentum moins survendu malgré le plus-bas
    assert bool(out["rsi_bull_div"].iloc[21]) is True
    assert bool(out["rsi_bear_div"].iloc[21]) is False


def test_no_divergence_when_momentum_confirms_new_high():
    # second pivot plus haut en prix ET en RSI -> mouvement confirmé, pas de divergence.
    closes = [100, 101, 100, 101, 100, 101, 100, 101,
              108, 100, 115, 130, 145,
              140, 135,
              150, 165, 180, 195, 210,
              205, 200]
    out = add_rsi_divergence(_flat(closes), period=5, left=2, right=2)

    assert bool(out["swing_high"].iloc[12]) is True
    assert bool(out["swing_high"].iloc[19]) is True
    assert out["rsi"].iloc[19] > out["rsi"].iloc[12]
    assert bool(out["rsi_bear_div"].iloc[19]) is False


def test_columns_present():
    closes = [100 + (i % 3) for i in range(20)]
    out = add_rsi_divergence(_flat(closes), period=5, left=2, right=2)
    for col in ("rsi", "swing_high", "swing_low", "rsi_bear_div", "rsi_bull_div"):
        assert col in out.columns
