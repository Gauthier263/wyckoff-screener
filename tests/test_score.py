"""
Tests de score.py (agrégation par symbole) sur données synthétiques, hors-ligne.

On vérifie l'arbitrage du biais dominant, la décroissance de récence, la déduction
de phase et le formatage `as_row`. `score_symbol` n'était jusqu'ici jamais appelé
par la suite de tests.

    pytest -q
"""
import pandas as pd

from screener.events import Event
from screener.features import TradingRange
from screener.score import SymbolResult, _phase_guess, _recency, score_symbol


def _df(price=105.0, n=5):
    idx = pd.date_range("2024-01-01", periods=n, freq="h", tz="UTC")
    return pd.DataFrame(
        {"open": price, "high": price, "low": price, "close": price, "volume": 1000.0},
        index=idx,
    )


def _tr(valid=True, low=100.0, high=110.0):
    return TradingRange(low=low, high=high, mid=(low + high) / 2,
                        height=high - low, height_atr=8.0, is_valid=valid)


# ── Récence ────────────────────────────────────────────────────────────────────
def test_recency_half_life():
    assert _recency(0) == 1.0
    assert _recency(4) == 0.5              # demi-vie 4 barres
    assert _recency(8) == 0.25


def test_recency_monotone_decreasing():
    vals = [_recency(k) for k in range(0, 12)]
    assert all(a > b for a, b in zip(vals, vals[1:]))


# ── Garde-fous ─────────────────────────────────────────────────────────────────
def test_invalid_range_returns_none():
    ev = [Event("SPRING", "accumulation", 0, 0.8, 100.5)]
    assert score_symbol("X/USDT", _df(), _tr(valid=False), ev) is None


def test_no_events_returns_neutral():
    res = score_symbol("X/USDT", _df(price=105.0), _tr(), [])
    assert res is not None
    assert res.bias == "neutral"
    assert res.phase == "—"
    assert res.top_event == "—"
    assert res.top_bars_ago == -1
    assert res.score == 0.0
    # les distances aux bornes restent renseignées même sans événement
    assert round(res.dist_support_pct, 2) == 4.76      # (105-100)/105*100
    assert round(res.dist_resist_pct, 2) == 4.76       # (110-105)/105*100


# ── Arbitrage du biais dominant ────────────────────────────────────────────────
def test_accumulation_bias_wins():
    ev = [
        Event("SPRING", "accumulation", 0, 0.9, 100.5),
        Event("ST", "distribution", 3, 0.3, 109.0),
    ]
    res = score_symbol("X/USDT", _df(), _tr(), ev)
    assert res.bias == "accumulation"
    assert res.score > 0
    assert res.top_event == "SPRING"


def test_distribution_bias_wins():
    ev = [
        Event("UTAD", "distribution", 0, 0.9, 110.5),
        Event("ST", "accumulation", 4, 0.3, 100.5),
    ]
    res = score_symbol("X/USDT", _df(), _tr(), ev)
    assert res.bias == "distribution"
    assert res.top_event == "UTAD"


def test_tie_prefers_accumulation():
    # contributions strictement égales des deux côtés → acc >= dist ⇒ accumulation
    ev = [
        Event("SOS", "accumulation", 0, 0.5, 110.0),
        Event("SOW", "distribution", 0, 0.5, 100.0),
    ]
    res = score_symbol("X/USDT", _df(), _tr(), ev)
    assert res.bias == "accumulation"


def test_recency_favours_recent_event_as_top():
    # même type/force ; le plus récent doit ressortir comme top_event via la récence
    ev = [
        Event("SOS", "accumulation", 0, 0.6, 110.0),
        Event("SOS", "accumulation", 8, 0.6, 110.0),
    ]
    res = score_symbol("X/USDT", _df(), _tr(), ev)
    assert res.top_bars_ago == 0


# ── Déduction de phase ─────────────────────────────────────────────────────────
def test_phase_guess_accumulation():
    assert _phase_guess([Event("LPS", "accumulation", 0, 0.5, 1)], "accumulation").startswith("D")
    assert _phase_guess([Event("SOS", "accumulation", 0, 0.5, 1)], "accumulation").startswith("D")
    assert _phase_guess([Event("SPRING", "accumulation", 0, 0.5, 1)], "accumulation").startswith("C")
    assert _phase_guess([Event("ST", "accumulation", 0, 0.5, 1)], "accumulation").startswith("B")
    assert _phase_guess([Event("SC", "accumulation", 0, 0.5, 1)], "accumulation").startswith("B")


def test_phase_guess_distribution():
    assert _phase_guess([Event("LPSY", "distribution", 0, 0.5, 1)], "distribution").startswith("D")
    assert _phase_guess([Event("SOW", "distribution", 0, 0.5, 1)], "distribution").startswith("D")
    assert _phase_guess([Event("UTAD", "distribution", 0, 0.5, 1)], "distribution").startswith("C")
    assert _phase_guess([Event("BC", "distribution", 0, 0.5, 1)], "distribution").startswith("B")


def test_phase_guess_unknown():
    assert _phase_guess([], "accumulation") == "—"
    assert _phase_guess([Event("AR", "accumulation", 0, 0.5, 1)], "neutral") == "—"


# ── Formatage as_row ───────────────────────────────────────────────────────────
def test_as_row_keys_and_rounding():
    ev = [
        Event("SPRING", "accumulation", 0, 0.8, 100.5),
        Event("SOS", "accumulation", 1, 0.7, 110.2),
        Event("SOS", "accumulation", 2, 0.6, 110.1),   # doublon de nom → dédupliqué
    ]
    row = score_symbol("X/USDT", _df(price=105.0), _tr(), ev).as_row()
    assert set(row) == {"symbol", "bias", "phase", "top_event", "bars_ago",
                        "score", "price", "dist_supp_%", "dist_res_%", "events"}
    assert row["symbol"] == "X/USDT"
    assert row["events"] == "SOS SPRING"               # unique + trié
    # arrondis : score à 3 décimales, distances à 2
    assert row["score"] == round(row["score"], 3)
    assert row["dist_supp_%"] == round(row["dist_supp_%"], 2)
