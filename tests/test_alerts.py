"""Test du moteur de déclenchement d'alertes (check_trigger, check_weakness), hors-ligne."""
import numpy as np
import pandas as pd

from screener.alerts import check_trigger, check_weakness

LEVELS = {"tp1": 64800, "tp2": 65500, "stop": 63184, "resist": 64500, "profit_floor": 63800}


def _bar(high, close, vr=1.0, clv=0.5):
    return {"high": high, "close": close, "vol_ratio": vr, "clv": clv}


def test_tp2_priority_over_tp1():
    t, msg = check_trigger(_bar(65600, 65550), np.nan, LEVELS)
    assert t == "TP2" and "65,500" in msg


def test_tp1_hit():
    t, _ = check_trigger(_bar(64850, 64820), 1.2, LEVELS)
    assert t == "TP1"


def test_exhaustion_high_vol_poor_close_above_resist():
    # close au-dessus de resist, volume fort, clôture faible -> Buying Climax/UTAD
    t, msg = check_trigger(_bar(64790, 64600, vr=2.8, clv=0.3), 1.0, LEVELS)
    assert t == "EXH" and "vol×2.8" in msg


def test_no_exhaustion_if_volume_normal():
    assert check_trigger(_bar(64790, 64600, vr=1.5, clv=0.3), 1.0, LEVELS) is None


def test_stop_break():
    t, _ = check_trigger(_bar(63200, 63100, clv=0.4), -0.5, LEVELS)
    assert t == "STOP"


def test_no_trigger_midrange():
    assert check_trigger(_bar(64000, 63950), 0.1, LEVELS) is None


def test_oi_shown_when_available():
    _, msg = check_trigger(_bar(64850, 64820), 2.3, LEVELS)
    assert "+2.3%" in msg


# ── Signaux de faiblesse précoce (check_weakness) ──────────────────────────────
def _df(rows):
    """rows: list de (open, high, low, close, vol_ratio, clv)."""
    idx = pd.date_range("2026-06-20", periods=len(rows), freq="15min", tz="UTC")
    return pd.DataFrame(rows, columns=["open", "high", "low", "close", "vol_ratio", "clv"], index=idx)


def _flat(n, price=64000):
    return [(price, price + 20, price - 20, price, 0.8, 0.5) for _ in range(n)]


def test_weakness_supply_bar():
    # avant-dernière barre = barre de vente volumique à clôture basse, en profit
    rows = _flat(13) + [(64200, 64250, 63900, 63950, 2.4, 0.15), (63950, 64000, 63900, 63960, 0.5, 0.5)]
    t, msg = check_weakness(_df(rows), None, LEVELS)
    assert t == "SUPPLY" and "vol×2.4" in msg


def test_no_supply_when_below_profit_floor():
    rows = _flat(13, price=63000) + [(63000, 63050, 62700, 62750, 2.5, 0.1), (62750, 62800, 62700, 62760, 0.5, 0.5)]
    assert check_weakness(_df(rows), None, LEVELS) is None     # sous profit_floor → ignoré


def test_weakness_oi_divergence_near_high():
    # prix proche du plus-haut récent, mais OI en baisse sur ~1h30 → DIVERG
    rows = _flat(13, price=64200) + [(64200, 64300, 64150, 64290, 0.9, 0.8), (64290, 64300, 64250, 64295, 0.7, 0.7)]
    df = _df(rows)
    oi = pd.Series(np.linspace(6.40e9, 6.10e9, len(df)), index=df.index)   # OI qui décline nettement
    t, msg = check_weakness(df, oi, LEVELS)
    assert t == "DIVERG" and "OI en baisse" in msg


def test_no_divergence_when_oi_rising():
    rows = _flat(13, price=64200) + [(64200, 64300, 64150, 64290, 0.9, 0.8), (64290, 64300, 64250, 64295, 0.7, 0.7)]
    df = _df(rows)
    oi = pd.Series(np.linspace(6.18e9, 6.30e9, len(df)), index=df.index)   # OI qui monte
    assert check_weakness(df, oi, LEVELS) is None


def test_weakness_none_without_profit_floor():
    rows = _flat(13) + [(64200, 64250, 63900, 63950, 2.4, 0.15), (63950, 64000, 63900, 63960, 0.5, 0.5)]
    assert check_weakness(_df(rows), None, {"tp1": 1, "tp2": 2, "stop": 0, "resist": 1}) is None


# ── Scan de fenêtre (catch-up robuste aux trous de cron) ───────────────────────
from screener.alerts import scan_window


def _closed(rows):
    idx = pd.date_range("2026-06-22 00:00", periods=len(rows), freq="15min", tz="UTC")
    return pd.DataFrame(rows, columns=["open", "high", "low", "close", "vol_ratio", "clv"], index=idx)


def test_scan_catches_tp1_in_earlier_bar():
    # TP1 touché à l'avant-dernière barre (pas la dernière) → doit être rattrapé
    rows = _flat(3) + [(64000, 64850, 63990, 64820, 1.2, 0.7), (64820, 64300, 64200, 64250, 0.6, 0.5)]
    closed = _closed(rows)
    res = scan_window(closed, None, LEVELS, since_ts=closed.index[0] - pd.Timedelta(minutes=1))
    assert res is not None and res[0] == "TP1"
    assert res[2] == closed.index[3]                      # la barre qui a touché 64 800


def test_cold_start_only_last_bar_no_retro_spam():
    # démarrage à froid (since=None) : un TP touché plus tôt n'est PAS re-notifié
    rows = _flat(3) + [(64000, 64850, 63990, 64820, 1.2, 0.7), (64820, 64300, 64200, 64250, 0.6, 0.5)]
    assert scan_window(_closed(rows), None, LEVELS, since_ts=None) is None


def test_already_evaluated_bars_skipped():
    rows = _flat(3) + [(64000, 64850, 63990, 64820, 1.2, 0.7), (64820, 64300, 64200, 64250, 0.6, 0.5)]
    closed = _closed(rows)
    # since = la barre du TP → on ne rescanne que la suivante (normale) → rien
    assert scan_window(closed, None, LEVELS, since_ts=closed.index[3]) is None


def test_scan_catches_stop_break():
    rows = _flat(3) + [(63300, 63350, 63100, 63150, 1.0, 0.3), (63150, 63300, 63100, 63200, 0.6, 0.5)]
    closed = _closed(rows)
    res = scan_window(closed, None, LEVELS, since_ts=closed.index[0] - pd.Timedelta(minutes=1))
    assert res is not None and res[0] == "STOP"
