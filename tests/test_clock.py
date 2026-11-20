import pandas as pd

from screener import clock
from screener.interactive import build_model


def test_paris_winter_and_summer_offsets():
    w = pd.Timestamp("2026-11-20 10:50", tz="UTC")
    s = pd.Timestamp("2026-07-01 10:50", tz="UTC")
    assert clock.fmt(w) == "20/11 11:50" and clock.label(w) == "CET"
    assert clock.fmt(s) == "01/07 12:50" and clock.label(s) == "CEST"
    assert clock.parse("20/11 11:50", 2026) == w
    assert clock.parse("01/07 12:50", 2026) == s
    assert clock.wall_sec(w) == int(w.timestamp()) + 3600


def test_model_uses_paris_time_and_survives_dst_change():
    """Données à cheval sur le passage à l'heure d'hiver (25/10/2026 03:00 CEST → 02:00
    CET) : temps d'affichage strictement croissants, libellé CET en fin de série."""
    idx = pd.date_range("2026-10-24 20:00", "2026-10-25 06:00", freq="1h", tz="UTC")
    df = pd.DataFrame({"open": 100.0, "high": 101.0, "low": 99.0, "close": 100.5,
                       "volume": 10.0}, index=idx)
    m = build_model("TEST/USDT", "1h", df, min_bars=5)
    times = [c["time"] for c in m["candles"]]
    assert all(b > a for a, b in zip(times, times[1:]))
    assert m["tz"] == "CET" and m["last_time"] == "25/10 07:00"
