"""
test_regime.py — Tests synthétiques du classificateur de régime (`regime.tag_regime`).

Un scénario OHLCV fabriqué par état attendu, pour vérifier le gate ON/OFF et que
chaque signature (volume → OI) déclenche le bon tag.
"""
import numpy as np
import pandas as pd

from screener.features import add_features, detect_trading_range
from screener.regime import RegimeThresholds, tag_regime


def make_df(close, volume, spread):
    """Construit un OHLCV synthétique + features. `spread` = (high-low) par barre."""
    close = np.asarray(close, dtype=float)
    n = len(close)
    volume = np.asarray(volume, dtype=float) if np.ndim(volume) else np.full(n, float(volume))
    spread = np.asarray(spread, dtype=float) if np.ndim(spread) else np.full(n, float(spread))
    open_ = np.concatenate([[close[0]], close[:-1]])
    high = np.maximum(open_, close) + spread / 2
    low = np.minimum(open_, close) - spread / 2
    idx = pd.date_range("2024-01-01", periods=n, freq="1h", tz="UTC")
    df = pd.DataFrame({"open": open_, "high": high, "low": low,
                       "close": close, "volume": volume}, index=idx)
    return add_features(df, vol_ma=20, atr_period=14)


def _tr(df):
    return detect_trading_range(df, lookback=80, buffer=5)


def test_range_on_is_tradable():
    # Sinusoïde de période 12 : oscille proprement entre ~100 et ~110, net ~0.
    i = np.arange(120)
    close = 105 + 5 * np.sin(2 * np.pi * i / 12)
    df = make_df(close, volume=1000, spread=1.0)
    reg = tag_regime(df, _tr(df))
    assert reg.state == "RANGE_ON"
    assert reg.tradable is True


def test_trend_markup_is_off():
    close = np.linspace(100, 200, 120)  # markup régulier
    df = make_df(close, volume=1000, spread=1.0)
    reg = tag_regime(df, _tr(df))
    assert reg.state == "TREND"
    assert reg.tradable is False


def test_climax_is_off():
    i = np.arange(120)
    close = 101 + np.sin(2 * np.pi * i / 12)        # calme
    close[-1] = 90                                   # barre de capitulation
    vol = np.full(120, 1000.0)
    vol[-1] = 7000.0                                 # volume climactique
    spread = np.full(120, 0.5)
    spread[-1] = 9.0                                 # spread très large
    df = make_df(close, vol, spread)
    reg = tag_regime(df, _tr(df))
    assert reg.state == "CLIMAX"
    assert reg.tradable is False


def test_vol_expansion_is_off():
    i = np.arange(120)
    close = 100 + 0.5 * np.sin(2 * np.pi * i / 4)    # net ~0 (pas de tendance)
    spread = np.full(120, 0.5)
    spread[-15:] = 3.0                                # explosion de volatilité
    vol = np.full(120, 1000.0)
    vol[-15:] = 1100.0                                # volume normal (pas un climax)
    df = make_df(close, vol, spread)
    reg = tag_regime(df, _tr(df))
    assert reg.state == "VOL_EXPANSION"
    assert reg.tradable is False


def test_low_liquidity_is_off():
    i = np.arange(120)
    close = 101 + np.sin(2 * np.pi * i / 12)
    vol = np.full(120, 1500.0)
    vol[-12:] = 200.0                                 # volume famélique soutenu
    df = make_df(close, vol, spread=0.5)
    reg = tag_regime(df, _tr(df))
    assert reg.state == "LOW_LIQ"
    assert reg.tradable is False


def test_chop_is_off():
    i = np.arange(120)
    close = 102 + 2 * np.sin(2 * np.pi * i / 7)       # oscillation sans structure nette
    spread = np.full(120, 1.0)
    spread[60] = 56.0                                 # spike unique DANS la fenêtre de plage
    df = make_df(close, volume=1000, spread=spread)
    tr = _tr(df)
    assert not tr.is_valid                            # le spike casse la validité de la plage
    reg = tag_regime(df, tr)
    assert reg.state == "CHOP"
    assert reg.tradable is False


def test_liquidation_is_off():
    close = np.linspace(320, 100, 120)               # cascade baissière directionnelle
    spread = np.full(120, 1.0)
    spread[-3:] = 10.0                               # barres larges de purge
    oi = np.full(120, 1000.0)
    oi[-12:] = np.linspace(990, 900, 12)            # OI coin qui s'effondre (~-10%)
    oi_series = pd.Series(oi, index=pd.date_range("2024-01-01", periods=120, freq="1h", tz="UTC"))
    df = make_df(close, volume=1000, spread=spread)
    reg = tag_regime(df, _tr(df), oi=oi_series)
    assert reg.state == "LIQUIDATION"
    assert reg.tradable is False


def test_thresholds_are_adjustable():
    # Drift haussier modéré : non directionnel avec le seuil par défaut (trend_move_atr=4),
    # mais TREND une fois le seuil abaissé → preuve que les seuils sont ajustables.
    close = np.linspace(100, 130, 120)
    df = make_df(close, volume=1000, spread=1.0)
    assert tag_regime(df, _tr(df)).state != "TREND"
    loose = RegimeThresholds(trend_move_atr=2.0, trend_consistency=0.5)
    assert tag_regime(df, _tr(df), th=loose).state == "TREND"
