"""Test du moteur de déclenchement d'alertes (check_trigger), hors-ligne."""
import numpy as np

from screener.alerts import check_trigger

LEVELS = {"tp1": 64800, "tp2": 65500, "stop": 63184, "resist": 64500}


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
