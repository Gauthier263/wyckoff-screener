"""
mtf.py — Confluence multi-timeframe.

Principe Wyckoff : un déclencheur (spring/UTAD sur le timeframe bas, LTF) vaut bien
plus quand le contexte du timeframe haut (HTF) va dans le même sens. Le HTF dit
*dans quelle campagne on est* (accumulation vs distribution), le LTF donne le
*point d'entrée*.

Multiplicateur de confluence appliqué au score LTF :
    HTF aligné + déclencheur LTF        → 1.5
    HTF aligné (même biais, sans trig.) → 1.25
    HTF sans contexte net               → 1.0
    conflit HTF / LTF                    → 0.5
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .score import SymbolResult

TRIGGER_EVENTS = {"SPRING", "UTAD", "SOS", "SOW", "LPS", "LPSY"}


@dataclass
class MTFResult:
    symbol: str
    htf: str
    ltf: str
    bias: str
    htf_bias: str
    htf_phase: str
    ltf_event: str
    ltf_bars_ago: int
    confluence: float
    score: float
    price: float
    note: str

    def as_row(self) -> dict:
        return {
            "symbol": self.symbol,
            "bias": self.bias,
            f"htf({self.htf})": self.htf_bias,
            "htf_phase": self.htf_phase,
            f"ltf({self.ltf})": self.ltf_event,
            "bars_ago": self.ltf_bars_ago,
            "confl.": self.confluence,
            "score": round(self.score, 3),
            "price": self.price,
            "note": self.note,
        }


def combine_mtf(symbol: str, htf_tf: str, ltf_tf: str,
                res_htf: SymbolResult | None, res_ltf: SymbolResult | None) -> MTFResult | None:
    """Combine le résultat HTF (contexte) et LTF (déclencheur)."""
    if res_ltf is None or res_ltf.score <= 0:
        return None

    has_trigger = any(e.name in TRIGGER_EVENTS for e in res_ltf.events)
    htf_ok = res_htf is not None and res_htf.tr.is_valid and res_htf.bias != "neutral"

    if htf_ok and res_htf.bias == res_ltf.bias:
        mult = 1.5 if has_trigger else 1.25
        note = f"HTF {res_htf.bias} confirme"
    elif htf_ok and res_htf.bias != res_ltf.bias:
        mult = 0.5
        note = f"conflit {res_htf.bias}/{res_ltf.bias}"
    else:
        mult = 1.0
        note = "HTF sans contexte net"

    return MTFResult(
        symbol=symbol, htf=htf_tf, ltf=ltf_tf,
        bias=res_ltf.bias,
        htf_bias=(res_htf.bias if res_htf else "—"),
        htf_phase=(res_htf.phase if res_htf else "—"),
        ltf_event=res_ltf.top_event, ltf_bars_ago=res_ltf.top_bars_ago,
        confluence=mult, score=res_ltf.score * mult,
        price=res_ltf.price, note=note,
    )
