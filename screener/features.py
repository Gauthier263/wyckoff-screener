"""
features.py — Calcul des features de Volume Spread Analysis (VSA) et détection
de la plage de trading (trading range) servant de contexte aux événements Wyckoff.

Toutes les fonctions prennent un DataFrame OHLCV avec colonnes:
    ['open', 'high', 'low', 'close', 'volume'] indexé par timestamp (UTC).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


# --------------------------------------------------------------------------- #
# Indicateurs de base
# --------------------------------------------------------------------------- #
def true_range(df: pd.DataFrame) -> pd.Series:
    prev_close = df["close"].shift(1)
    tr = pd.concat(
        [
            df["high"] - df["low"],
            (df["high"] - prev_close).abs(),
            (df["low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return tr


def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    return true_range(df).rolling(period, min_periods=period).mean()


def rsi(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """RSI de Wilder (lissage exponentiel à coefficient 1/period).

    Mesure le momentum : une divergence prix/RSI (prix qui fait un creux ≤ mais
    RSI qui remonte) trahit un essoufflement de la pression vendeuse — confirmation
    classique d'un double creux d'absorption.
    """
    delta = df["close"].diff()
    gain = delta.clip(lower=0.0)
    loss = (-delta).clip(lower=0.0)
    # Lissage de Wilder = EMA de coefficient alpha = 1/period.
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    out = 100 - 100 / (1 + rs)
    # avg_loss == 0 (que des hausses) → RSI = 100 ; avg_gain == 0 → RSI = 0.
    out = out.where(avg_loss != 0, 100.0)
    out = out.where(avg_gain != 0, 0.0)
    return out


def add_features(df: pd.DataFrame, vol_ma: int = 20, atr_period: int = 14,
                 rsi_period: int = 14) -> pd.DataFrame:
    """Enrichit le DataFrame avec les colonnes VSA utilisées par les détecteurs."""
    out = df.copy()
    rng = (out["high"] - out["low"]).replace(0, np.nan)

    out["spread"] = out["high"] - out["low"]
    # Close Location Value: 0 = clôture sur le bas, 1 = clôture sur le haut
    out["clv"] = ((out["close"] - out["low"]) / rng).clip(0, 1).fillna(0.5)
    out["atr"] = atr(out, atr_period)
    out["vol_ma"] = out["volume"].rolling(vol_ma, min_periods=1).mean()
    out["vol_ratio"] = out["volume"] / out["vol_ma"].replace(0, np.nan)
    # Spread relatif à l'ATR : > 1 = barre large, < 1 = barre étroite
    out["spread_atr"] = out["spread"] / out["atr"].replace(0, np.nan)
    out["ret"] = out["close"].pct_change()
    out["rsi"] = rsi(out, rsi_period)
    return out


# --------------------------------------------------------------------------- #
# Pivots / swings
# --------------------------------------------------------------------------- #
def swing_points(df: pd.DataFrame, left: int = 3, right: int = 3) -> pd.DataFrame:
    """Marque les pivots hauts/bas (fractales). right>0 = pivots confirmés à retard."""
    highs, lows = df["high"].values, df["low"].values
    n = len(df)
    is_high = np.zeros(n, dtype=bool)
    is_low = np.zeros(n, dtype=bool)
    for i in range(left, n - right):
        win_h = highs[i - left : i + right + 1]
        win_l = lows[i - left : i + right + 1]
        if highs[i] == win_h.max() and (win_h.argmax() == left):
            is_high[i] = True
        if lows[i] == win_l.min() and (win_l.argmin() == left):
            is_low[i] = True
    out = df.copy()
    out["swing_high"] = is_high
    out["swing_low"] = is_low
    return out


# --------------------------------------------------------------------------- #
# Trading range
# --------------------------------------------------------------------------- #
@dataclass
class TradingRange:
    low: float          # support (bas de range)
    high: float         # résistance (haut de range)
    mid: float
    height: float       # high - low
    height_atr: float   # hauteur rapportée à l'ATR
    is_valid: bool      # True si une vraie plage latérale est détectée


def detect_trading_range(
    df: pd.DataFrame,
    lookback: int = 80,
    buffer: int = 5,
    max_height_atr: float = 18.0,
    min_touches: int = 2,
) -> TradingRange:
    """
    Définit la plage *avant* les `buffer` dernières barres, de sorte qu'un spring ou
    un upthrust survenant récemment soit mesuré contre la plage qui le précède.

    Heuristique de validité: la hauteur de plage rapportée à l'ATR doit rester bornée
    (sinon on est en tendance, pas en range) et les bornes doivent avoir été touchées
    plusieurs fois.
    """
    window = df.iloc[-(lookback + buffer) : -buffer] if buffer > 0 else df.iloc[-lookback:]
    if len(window) < 10:
        return TradingRange(np.nan, np.nan, np.nan, np.nan, np.nan, False)

    hi = float(window["high"].max())
    lo = float(window["low"].min())
    mid = (hi + lo) / 2
    height = hi - lo
    a = float(df["atr"].iloc[-buffer - 1]) if "atr" in df else float(true_range(df).iloc[-buffer - 1])
    height_atr = height / a if a and not np.isnan(a) else np.inf

    # Compte les "touches" des bornes (à 15% de la hauteur)
    tol = 0.15 * height
    touch_hi = (window["high"] >= hi - tol).sum()
    touch_lo = (window["low"] <= lo + tol).sum()

    is_valid = (
        height_atr <= max_height_atr
        and touch_hi >= min_touches
        and touch_lo >= min_touches
    )
    return TradingRange(lo, hi, mid, height, height_atr, bool(is_valid))
