import numpy as np
import pandas as pd

from screener.session import is_thin, session_of, session_rvol


def test_session_of_boundaries():
    t = lambda s: pd.Timestamp(s, tz="UTC")
    assert session_of(t("2026-11-13 23:00")) == "Semaine"          # vendredi
    assert session_of(t("2026-11-14 00:00")) == "Sam"
    assert session_of(t("2026-11-15 19:00")) == "Dim"
    assert session_of(t("2026-11-15 20:00")).startswith("Reprise")
    assert session_of(t("2026-11-16 05:00")).startswith("Reprise")
    assert session_of(t("2026-11-16 06:00")) == "Semaine"
    assert is_thin(t("2026-11-14 12:00")) and not is_thin(t("2026-11-15 21:00"))


def test_session_rvol_flags_thin_weekend():
    """Volume semaine = 100, week-end = 50 : le Rvol séance d'un dimanche ≈ 0.5, alors que
    le Rvol(20) habituel remonte vers 1 au fil du week-end."""
    idx = pd.date_range("2026-09-01", "2026-11-16", freq="1h", tz="UTC")
    vol = np.where([is_thin(t) for t in idx], 50.0, 100.0)
    df = pd.DataFrame({"volume": vol}, index=idx)
    sr = session_rvol(df)
    sunday = sr.loc["2026-11-15 10:00"]
    assert abs(sunday - 0.5) < 1e-9
    assert abs(sr.loc["2026-11-12 10:00"] - 1.0) < 1e-9
    classic = (df.volume / df.volume.rolling(20, min_periods=1).mean()).loc["2026-11-15 10:00"]
    assert classic > 0.9                                            # le Rvol(20) masque le creux
