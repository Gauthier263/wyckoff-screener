import numpy as np
import pandas as pd
import pytest

from screener import journal
from screener.guard import check_trade, structure_tf


def _frame(freq: str, n: int, start: str, step: float, wiggle: float) -> pd.DataFrame:
    """Série en dents de scie : `n` barres, tendance `step` par barre, amplitude `wiggle`."""
    idx = pd.date_range(start, periods=n, freq=freq, tz="UTC")
    base = 60000 + step * np.arange(n) + wiggle * np.sin(np.arange(n))
    return pd.DataFrame({"open": base, "high": base + wiggle, "low": base - wiggle,
                         "close": base, "volume": 1.0}, index=idx)


def test_structure_tf_picks_the_band():
    """Plage de 50 h : en 5m (600 barres) et 15m (200) trop longue, en 4h (12) trop courte →
    la 1h (50 barres) commande, avec une hauteur ≥ 5 ATR."""
    start = "2026-11-20 00:00"
    frames = {tf: _frame(f, n + 30, "2026-11-18 18:00", step, w)
              for tf, f, n, step, w in [("5m", "5min", 1200, 3, 60), ("15m", "15min", 400, 9, 120),
                                        ("1h", "1h", 100, 40, 300), ("4h", "4h", 25, 160, 700)]}
    st = structure_tf(frames, start, "2026-11-22 01:00")
    assert st.tf == "1h" and st.eligible
    assert 20 <= st.bars <= 80 and st.height_atr >= 5
    assert st.is_internal(0.8 * st.atr) and not st.is_internal(1.2 * st.atr)
    assert "Unité de structure : 1h" in st.header()


def _struct_2211():
    """Structure 1h du dimanche 22/11 : SC 55 130 → ancien climax 62 006, ATR 1h 639."""
    from screener.guard import StructureTF
    return StructureTF("1h", 639.0, 55130.0, 62006.0, 50, 10.8, True)


def test_check_trade_reproduces_the_sunday_short_as_red():
    """Short 60 985 à 15h40 CET (14h40 UTC), stop 61 100, niveau tiré de la plage 5 min de
    501 points, dimanche : séance creuse, niveau interne (0,8 ATR 1h), stop sous l'UT 61 670."""
    g = check_trade(side="short", entry=60985, stop=61100, target=60464,
                    when="2026-11-22 14:40", struct=_struct_2211(), frame_bias="neutral",
                    invalidation=61670, level_span=501, recent_extreme=61160,
                    attempts_before=0, mirror_plan=None)
    s = {p.key: p.status for p in g.points}
    assert g.verdict == "rouge"
    assert s["niveau"] == "ko" and s["stop"] == "ko" and s["séance"] == "ko" and s["miroir"] == "ko"
    assert s["position"] == "ok"                       # 85 % de la plage : quart haut
    assert g.breakeven == 60870 and g.partial == 60755  # +1 R / +2 R (risque 115)


def test_check_trade_green_when_everything_holds():
    g = check_trade(side="short", entry=61900, stop=62700, target=59500,
                    when="2026-11-24 14:00", struct=_struct_2211(), frame_bias="bear",
                    invalidation=62006, level_span=6876, recent_extreme=62200,
                    attempts_before=1, mirror_plan="si spring sous 60 464 : couper, long sur LPS")
    assert g.verdict == "vert", g.summary()


def test_check_trade_orange_on_unknown_critical_and_third_attempt_red():
    kw = dict(side="long", entry=55600, stop=54700, target=57500, when="2026-11-24 14:00",
              struct=_struct_2211(), frame_bias="bull", invalidation=55130, level_span=6876,
              mirror_plan="si SOW : couper")
    assert check_trade(**kw).verdict == "orange"                   # tentatives inconnues
    assert check_trade(**kw, attempts_before=2).verdict == "rouge"  # 3e tentative
    with pytest.raises(ValueError):
        check_trade(**{**kw, "stop": 56000})                        # stop du mauvais côté


def test_journal_roundtrip_and_weekly_summary(tmp_path):
    p = tmp_path / "trades.csv"
    t1 = journal.add(side="short", entry=60985, stop=61100, at="2026-11-22 15:40",
                     garde_fou="rouge", raison="retour sous le plafond 5 min", path=p)
    journal.close(t1, exit_=61100, at="2026-11-22 17:10", lecon="niveau 5 min = bruit en 1h", path=p)
    journal.add(side="short", entry=60780, stop=60985, at="2026-11-22 18:10",
                exit_=60985, exit_at="2026-11-22 22:00", path=p)
    journal.add(side="long", entry=62000, stop=61500, at="2026-11-23 10:00", path=p)  # ouvert
    df = journal.load(p)
    assert list(df["r"].iloc[:2]) == [-1.0, -1.0] and list(df["pts"].iloc[:2]) == [-115, -205]
    assert journal.attempts_today("short", "2026-11-22", p) == 2
    assert journal.attempts_today("short", "2026-11-23", p) == 0
    wk = journal.weekly_summary("2026-11-22", p)          # semaine du lundi 16/11
    assert wk["trades"] == 2 and wk["perdants"] == 2 and wk["points"] == -320 and wk["r_total"] == -2
    assert wk["garde_fou"] == {"rouge": 1, "non noté": 1}
    assert journal.weekly_summary("2026-11-23", p)["trades"] == 1   # nouvelle semaine
