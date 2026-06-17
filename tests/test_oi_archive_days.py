"""Test du planificateur de dates d'archive OI Binance (_archive_days), hors-ligne."""
import pandas as pd

from screener.data import _archive_days

NOW = pd.Timestamp("2026-06-16 05:00", tz="UTC")


def test_days_mode_last_n_excludes_today():
    days = _archive_days(NOW, days=3)
    # archive en retard ~1j : on s'arrête à la veille (15/06), pas aujourd'hui
    assert days == ["2026-06-13", "2026-06-14", "2026-06-15"]


def test_range_mode_spans_interval_capped_at_yesterday():
    days = _archive_days(NOW, start="2026-06-10", end="2026-06-20")
    assert days[0] == "2026-06-10" and days[-1] == "2026-06-15"   # borné à la veille
    assert len(days) == 6


def test_range_deep_history_march():
    days = _archive_days(NOW, start="2026-03-01", end="2026-03-05")
    assert days == ["2026-03-01", "2026-03-02", "2026-03-03", "2026-03-04", "2026-03-05"]


def test_cap_limits_download_count():
    days = _archive_days(NOW, start="2020-01-01", end="2026-06-16", cap=30)
    assert len(days) == 30 and days[-1] == "2026-06-15"


def test_empty_when_start_after_available():
    assert _archive_days(NOW, start="2026-06-16", end="2026-06-16") == []
