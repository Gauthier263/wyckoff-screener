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


def add_features(df: pd.DataFrame, vol_ma: int = 20, atr_period: int = 14) -> pd.DataFrame:
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
    return out


def add_absorption(df: pd.DataFrame, delta, vol_window: int = 20,
                   move_atr: float = 1.0, weak_eff: float = 0.5,
                   win: int = 3) -> pd.DataFrame:
    """Effort (CVD) vs résultat (prix) : **absorption** et **no-demand / no-supply**.

    Deux lectures opposées de la loi effort-vs-résultat, à partir du flux d'ordres agressifs.
    `df` doit déjà porter `clv` et `atr` (via :func:`add_features`) ; `delta` est le flux
    agressif net par barre (taker_buy − taker_sell, en coin), aligné sur l'index de `df`
    (cf. :func:`screener.data.fetch_taker_delta`).

    Colonnes ajoutées :
      - ``delta``      : flux agressif net par barre (coin).
      - ``delta_z``    : delta / écart-type glissant — **EFFORT** en σ (signe = côté agressif).
      - ``ret_atr``    : (close − open) / atr — **RÉSULTAT** directionnel, en ATR.
      - ``absorption`` : ``−delta_z · (2·clv − 1)`` — version **per-barre** (in-barre). Le **signe**
        discrimine : **> 0 = flux rejeté = absorption** (``delta_z < 0`` vente rejetée → demande
        absorbe, haussier ; ``delta_z > 0`` achat rejeté → offre absorbe, baissier) ;
        **< 0 = mouvement honnête confirmé** (effort ET clôture alignés : un SOS/SOW franc sort
        nettement négatif) ; **≈ 0 = flux faible** ou clôture neutre (AR/ST).
      - ``absorption_w`` : **même formule sur une fenêtre de ``win`` barres** (défaut 3) — flux net
        cumulé vs position de la clôture dans le range des ``win`` dernières barres. **Plus
        robuste** : capture l'absorption même quand la vente et le rejet sont sur des barres
        DIFFÉRENTES (ce que le per-barre rate), donc moins sensible au découpage de TF. **C'est la
        lecture de référence ; ``absorption`` per-barre sert pour la barre d'événement précise.**
      - ``no_demand``  : prix MONTE ≥ ``move_atr`` ATR avec ``|delta_z| ≤ weak_eff`` (hausse
        sans demande agressive = faiblesse / distribution).
      - ``no_supply``  : prix BAISSE ≥ ``move_atr`` ATR avec ``|delta_z| ≤ weak_eff`` (baisse
        sans offre agressive = force / accumulation).
    """
    out = df.copy()
    d = delta if isinstance(delta, pd.Series) else pd.Series(delta, index=out.index)
    d = d.reindex(out.index).astype(float)
    out["delta"] = d

    sd = d.rolling(vol_window, min_periods=max(3, vol_window // 4)).std()
    out["delta_z"] = d / sd.replace(0, np.nan)
    out["ret_atr"] = (out["close"] - out["open"]) / out["atr"].replace(0, np.nan)

    clv_s = 2.0 * out["clv"] - 1.0                 # clôture dans le range, [-1, +1]
    out["absorption"] = -out["delta_z"] * clv_s

    # ── version fenêtrée (option A) : même formule sur `win` barres ──────────
    dsum = d.rolling(win, min_periods=1).sum()                       # flux net cumulé
    dsum_z = dsum / dsum.rolling(vol_window, min_periods=max(3, vol_window // 4)).std().replace(0, np.nan)
    hi_w = out["high"].rolling(win, min_periods=1).max()
    lo_w = out["low"].rolling(win, min_periods=1).min()
    clv_w = ((out["close"] - lo_w) / (hi_w - lo_w).replace(0, np.nan)).clip(0, 1)
    out["absorption_w"] = -dsum_z * (2.0 * clv_w - 1.0)

    weak = out["delta_z"].abs() <= weak_eff        # NaN → False (pas de faux flag)
    out["no_demand"] = (out["ret_atr"] >= move_atr) & weak
    out["no_supply"] = (out["ret_atr"] <= -move_atr) & weak
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
