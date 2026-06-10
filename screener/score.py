"""
score.py — Agrège les événements détectés en un résultat par symbole :
biais dominant, phase probable, meilleur événement, score composite.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .events import Event
from .features import TradingRange

# Poids « importance » par type d'événement (déclencheur d'action vs contexte)
EVENT_WEIGHT = {
    "SPRING": 1.0, "UTAD": 1.0,
    "SOS": 0.9, "SOW": 0.9,
    "LPS": 0.85, "LPSY": 0.85,
    "SC": 0.6, "BC": 0.6,
    "ST": 0.5,
}


def _recency(bars_ago: int, half_life: float = 4.0) -> float:
    """Décroissance exponentielle : un signal récent vaut plus."""
    return float(0.5 ** (bars_ago / half_life))


@dataclass
class SymbolResult:
    symbol: str
    bias: str
    phase: str
    top_event: str
    top_bars_ago: int
    score: float
    price: float
    tr: TradingRange
    dist_support_pct: float
    dist_resist_pct: float
    events: list[Event]

    def as_row(self) -> dict:
        return {
            "symbol": self.symbol,
            "bias": self.bias,
            "phase": self.phase,
            "top_event": self.top_event,
            "bars_ago": self.top_bars_ago,
            "score": round(self.score, 3),
            "price": self.price,
            "dist_supp_%": round(self.dist_support_pct, 2),
            "dist_res_%": round(self.dist_resist_pct, 2),
            "events": " ".join(sorted({e.name for e in self.events})),
        }


def _phase_guess(events: list[Event], bias: str) -> str:
    names = {e.name for e in events}
    if bias == "accumulation":
        if "LPS" in names or "SOS" in names:
            return "D (markup imminent)"
        if "SPRING" in names:
            return "C (spring/test)"
        if "ST" in names or "SC" in names:
            return "B (test/construction)"
    elif bias == "distribution":
        if "LPSY" in names or "SOW" in names:
            return "D (markdown imminent)"
        if "UTAD" in names:
            return "C (upthrust)"
        if "ST" in names or "BC" in names:
            return "B (test/construction)"
    return "—"


def score_symbol(symbol: str, df: pd.DataFrame, tr: TradingRange,
                 events: list[Event]) -> SymbolResult | None:
    price = float(df["close"].iloc[-1])
    if not tr.is_valid:
        return None

    dist_supp = (price - tr.low) / price * 100
    dist_res = (tr.high - price) / price * 100

    if not events:
        return SymbolResult(symbol, "neutral", "—", "—", -1, 0.0, price, tr,
                            dist_supp, dist_res, [])

    # Score = somme pondérée (poids type × force × récence)
    acc = dist = 0.0
    for e in events:
        contrib = EVENT_WEIGHT.get(e.name, 0.4) * e.strength * _recency(e.bars_ago)
        if e.bias == "accumulation":
            acc += contrib
        elif e.bias == "distribution":
            dist += contrib

    if acc >= dist:
        bias, score = "accumulation", acc
    else:
        bias, score = "distribution", dist

    # Meilleur événement = plus fort × récent du biais dominant
    biased = [e for e in events if e.bias == bias] or events
    top = max(biased, key=lambda e: EVENT_WEIGHT.get(e.name, 0.4) * e.strength * _recency(e.bars_ago))

    return SymbolResult(
        symbol=symbol, bias=bias, phase=_phase_guess(events, bias),
        top_event=top.name, top_bars_ago=top.bars_ago, score=score,
        price=price, tr=tr, dist_support_pct=dist_supp, dist_resist_pct=dist_res,
        events=events,
    )
