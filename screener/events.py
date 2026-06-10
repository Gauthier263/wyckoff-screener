"""
events.py — Détecteurs d'événements Wyckoff.

Chaque détecteur renvoie 0..n objets Event sur la fenêtre récente (`buffer` dernières
barres) en se référant à la plage de trading `tr`. Les seuils sont des heuristiques
transparentes et ajustables (voir config.yaml) — Wyckoff reste discrétionnaire, ces
signaux sont une aide à la décision, pas un automate d'exécution.

Familles :
  Accumulation : SC (selling climax), AR, ST, SPRING, TEST, SOS, LPS
  Distribution : BC (buying climax), AR, ST, UTAD, SOW, LPSY
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

import numpy as np
import pandas as pd

from .features import TradingRange

Bias = Literal["accumulation", "distribution", "neutral"]


@dataclass
class Event:
    name: str           # ex. "SPRING", "UTAD", "SOS"
    bias: Bias
    bars_ago: int       # 0 = dernière barre clôturée
    strength: float     # 0..1, qualité « manuel Wyckoff » du signal
    price: float
    note: str = ""


@dataclass
class Thresholds:
    climax_vol: float = 2.0       # vol_ratio pour un climax (SC/BC)
    sos_vol: float = 1.3          # vol_ratio pour SOS/SOW
    wide_spread_atr: float = 1.3  # spread_atr d'une barre « large »
    narrow_spread_atr: float = 0.7
    test_vol: float = 0.85        # vol_ratio plafond pour un test/ST (volume sec)
    pen_atr: float = 0.1          # pénétration mini hors borne, en ATR
    reclaim_clv: float = 0.5      # clôture au-dessus/dessous du milieu de barre


def _last(df: pd.DataFrame, bars_ago: int, col: str) -> float:
    return float(df[col].iloc[-1 - bars_ago])


def detect_events(
    df: pd.DataFrame,
    tr: TradingRange,
    buffer: int = 5,
    th: Thresholds | None = None,
) -> list[Event]:
    th = th or Thresholds()
    events: list[Event] = []
    if not tr.is_valid:
        return events
    atr_ref = float(df["atr"].iloc[-1])
    if not atr_ref or np.isnan(atr_ref):
        return events

    n = len(df)
    span = range(min(buffer, n - 1))  # 0..buffer-1 barres en arrière

    for k in span:
        idx = -1 - k
        bar = df.iloc[idx]
        high, low, close = float(bar["high"]), float(bar["low"]), float(bar["close"])
        clv = float(bar["clv"])
        vr = float(bar["vol_ratio"]) if not np.isnan(bar["vol_ratio"]) else 1.0
        sa = float(bar["spread_atr"]) if not np.isnan(bar["spread_atr"]) else 1.0

        below = tr.low - low                     # profondeur sous le support
        above = high - tr.high                   # dépassement au-dessus de la résistance

        # ---------------- SPRING / SHAKEOUT (accumulation) ---------------- #
        if below > th.pen_atr * atr_ref and close > tr.low:
            reclaim = (close - tr.low) / atr_ref
            # volume non climactique = meilleur spring (faible offre) ; fort reclaim = bonus
            vol_bonus = 1.0 if vr <= th.climax_vol else 0.6
            strength = float(np.clip(0.4 + 0.5 * min(reclaim, 1.0), 0, 1)) * vol_bonus
            events.append(Event("SPRING", "accumulation", k, strength, close,
                                 f"pénétration {below/atr_ref:.2f} ATR sous support, reclaim {reclaim:.2f} ATR"))

        # ---------------- UTAD (distribution) ---------------- #
        if above > th.pen_atr * atr_ref and close < tr.high:
            reject = (tr.high - close) / atr_ref
            vol_bonus = 1.0 if vr <= th.climax_vol else 0.6
            strength = float(np.clip(0.4 + 0.5 * min(reject, 1.0), 0, 1)) * vol_bonus
            events.append(Event("UTAD", "distribution", k, strength, close,
                                 f"dépassement {above/atr_ref:.2f} ATR au-dessus résistance, rejet {reject:.2f} ATR"))

        # ---------------- SC : Selling Climax ---------------- #
        if (vr >= th.climax_vol and sa >= th.wide_spread_atr
                and clv >= th.reclaim_clv and low <= tr.low + 0.2 * tr.height):
            strength = float(np.clip(0.3 + 0.2 * (vr - th.climax_vol) + 0.3 * clv, 0, 1))
            events.append(Event("SC", "accumulation", k, strength, close,
                                 f"vol x{vr:.1f}, spread {sa:.1f} ATR, clôture haute"))

        # ---------------- BC : Buying Climax ---------------- #
        if (vr >= th.climax_vol and sa >= th.wide_spread_atr
                and clv <= (1 - th.reclaim_clv) and high >= tr.high - 0.2 * tr.height):
            strength = float(np.clip(0.3 + 0.2 * (vr - th.climax_vol) + 0.3 * (1 - clv), 0, 1))
            events.append(Event("BC", "distribution", k, strength, close,
                                 f"vol x{vr:.1f}, spread {sa:.1f} ATR, clôture basse"))

        # ---------------- SOS : Sign of Strength ---------------- #
        if (close > tr.high and vr >= th.sos_vol and sa >= th.wide_spread_atr and clv >= 0.6):
            strength = float(np.clip(0.4 + 0.3 * clv + 0.1 * (vr - th.sos_vol), 0, 1))
            events.append(Event("SOS", "accumulation", k, strength, close,
                                 f"cassure résistance, vol x{vr:.1f}, spread large"))

        # ---------------- SOW : Sign of Weakness ---------------- #
        if (close < tr.low and vr >= th.sos_vol and sa >= th.wide_spread_atr and clv <= 0.4):
            strength = float(np.clip(0.4 + 0.3 * (1 - clv) + 0.1 * (vr - th.sos_vol), 0, 1))
            events.append(Event("SOW", "distribution", k, strength, close,
                                 f"cassure support, vol x{vr:.1f}, spread large"))

        # ---------------- ST : Secondary Test (volume sec près d'une borne) ---------------- #
        near_low = abs(low - tr.low) <= 0.15 * tr.height
        near_high = abs(high - tr.high) <= 0.15 * tr.height
        if near_low and vr <= th.test_vol and sa <= th.wide_spread_atr and close >= tr.low:
            events.append(Event("ST", "accumulation", k, float(np.clip(0.5 * (1 - vr), 0, 1)),
                                 close, f"retest support, vol x{vr:.1f} (sec)"))
        if near_high and vr <= th.test_vol and sa <= th.wide_spread_atr and close <= tr.high:
            events.append(Event("ST", "distribution", k, float(np.clip(0.5 * (1 - vr), 0, 1)),
                                 close, f"retest résistance, vol x{vr:.1f} (sec)"))

    # ---------------- LPS / LPSY : structure après SOS/SOW ---------------- #
    names = {e.name for e in events}
    if "SOS" in names:
        # repli sur volume décroissant tenant au-dessus de la résistance cassée
        last_clv = _last(df, 0, "clv")
        last_vr = _last(df, 0, "vol_ratio")
        if last_vr <= th.test_vol and last_clv >= 0.4 and _last(df, 0, "close") >= tr.high:
            events.append(Event("LPS", "accumulation", 0, 0.55, _last(df, 0, "close"),
                                 "repli à volume sec au-dessus de la résistance cassée"))
    if "SOW" in names:
        last_clv = _last(df, 0, "clv")
        last_vr = _last(df, 0, "vol_ratio")
        if last_vr <= th.test_vol and last_clv <= 0.6 and _last(df, 0, "close") <= tr.low:
            events.append(Event("LPSY", "distribution", 0, 0.55, _last(df, 0, "close"),
                                 "rebond faible à volume sec sous le support cassé"))

    return events
