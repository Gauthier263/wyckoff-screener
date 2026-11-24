"""Tests synthétiques de l'étude des mèches (hors-ligne)."""
import numpy as np
import pandas as pd

from screener.htf import wick_study as W


def _df(o, h, l, c, v=None, freq="4h", start="2026-01-01"):
    idx = pd.date_range(start, periods=len(c), freq=freq, tz="UTC")
    return pd.DataFrame({"open": o, "high": h, "low": l, "close": c,
                         "volume": v if v is not None else np.ones(len(c))}, index=idx)


def _flat_with_wick(n=40, at=20, low=90.0):
    c = np.full(n, 100.0)
    h = c + 0.3
    lo = c - 0.3
    lo[at] = low
    return _df(c, h, lo, c)


def test_detect_wicks_trouve_la_meche_basse_et_ses_niveaux():
    w = W.detect_wicks(_flat_with_wick(), min_atr=1.0)
    w = w[w["direction"] == "basse"]
    assert len(w) == 1
    r = w.iloc[0]
    assert r["tip"] == 90.0 and r["base"] == 100.0 and r["half"] == 95.0
    assert r["size_atr"] > 1.0 and 0.9 < r["wick_share"] <= 1.0


def test_detect_wicks_fusionne_les_grappes():
    """Deux mèches à 3 bougies d'écart sont un même épisode : une seule observation."""
    df = _flat_with_wick()
    # la seconde est bien plus profonde : elle reste la plus grande même mesurée avec un
    # ATR gonflé par la première
    df.iloc[23, df.columns.get_loc("low")] = 70.0
    w = W.detect_wicks(df, min_atr=1.0, min_sep=10)
    w = w[w["direction"] == "basse"]
    assert len(w) == 1 and w.iloc[0]["tip"] == 70.0      # on garde la plus grande (en ATR)


def test_first_touch_compte_les_bougies_jusqua_au_retour():
    df = _flat_with_wick()
    df.iloc[27, df.columns.get_loc("low")] = 94.0        # retour sous le 50 % (95)
    assert W.first_touch(df, 20, 95.0, "down", 50) == 7
    assert W.first_touch(df, 20, 90.0, "down", 50) is None   # 100 % jamais retesté
    assert W.first_touch(df, 20, 95.0, "down", 5) is None    # horizon trop court


def test_survival_cumule():
    s = W.survival(pd.Series([1, 3, None, 8]), checkpoints=(1, 5, 10))
    assert s == {1: 0.25, 5: 0.5, 10: 0.75}


def test_ltf_imbalance_distingue_vide_et_absorption():
    """Même mèche, deux histoires : traversée éclair sans volume (vide) contre volume
    concentré dans la zone (absorption)."""
    t0 = pd.Timestamp("2026-01-01", tz="UTC")
    idx = pd.date_range(t0, periods=4, freq="1h", tz="UTC")
    # bougie mère de 100 à 90 : mèche 90-95, corps au-dessus
    # vide : une seule bougie fine traverse la mèche, avec peu de volume
    vide = pd.DataFrame({"open": [100, 96, 98, 99], "high": [100, 96, 99, 100],
                         "low": [96, 90, 97, 98], "close": [96, 97, 99, 100],
                         "volume": [100, 5, 100, 100]}, index=idx)
    # absorption : la zone est retraitée par plusieurs bougies fines, volume lourd
    absorb = pd.DataFrame({"open": [100, 94, 92, 94], "high": [100, 95, 95, 100],
                           "low": [94, 90, 90, 93], "close": [94, 92, 94, 100],
                           "volume": [50, 300, 300, 50]}, index=idx)
    a = W.ltf_imbalance(vide, t0, t0 + pd.Timedelta(hours=4), 90.0, 95.0)
    b = W.ltf_imbalance(absorb, t0, t0 + pd.Timedelta(hours=4), 90.0, 95.0)
    assert a["vol_density"] < 1.0 < b["vol_density"]
    assert a["bars_in_zone"] < b["bars_in_zone"]


def test_wilson_et_rate():
    lo, hi = W.wilson(50, 100)
    assert lo < 0.5 < hi
    assert W.rate([True, False]).startswith("0.50")


def test_precedence_ordre_retest_puis_mouvement():
    df = _flat_with_wick(n=60)
    # après la mèche (bougie 20, base 100, 50 % à 95) : retour à 94 en bougie 23, puis
    # envolée à 110 en bougie 30
    df.iloc[23, df.columns.get_loc("low")] = 94.0
    for k in range(30, 60):
        for col in ("open", "high", "low", "close"):
            df.iloc[k, df.columns.get_loc(col)] = 110.0
    w = W.detect_wicks(df, min_atr=1.0)
    w = w[w["direction"] == "basse"]
    p = W.precedence(df, w, target_atr=2.0, horizon=35, control_offset=60)
    assert p.iloc[0]["verdict"] == "retest d'abord"


def test_liq_rel_rapporte_le_jour_a_sa_mediane():
    idx = pd.date_range("2026-01-01", periods=40, freq="1D", tz="UTC")
    liq = pd.DataFrame({"long_liq": np.r_[np.full(39, 100.0), 500.0],
                        "short_liq": np.full(40, 50.0)}, index=idx)
    at = idx[-1] + pd.Timedelta(hours=9)
    assert W.liq_rel(liq, at, "basse") == 5.0       # longs liquidés : 500 contre 100
    assert W.liq_rel(liq, at, "haute") == 1.0       # shorts : jour ordinaire
    assert np.isnan(W.liq_rel(liq, idx[3], "basse"))   # pas assez d'historique


def test_classify_wick_suit_la_regle_validee():
    assert W.classify_wick(1.2, 5.0, "basse")["attendu"] is None          # trop petite
    sans = W.classify_wick(2.0, 1.0, "basse")
    assert sans["attendu"] is None and "aucun avantage" in sans["note"]
    liq = W.classify_wick(2.0, 3.0, "basse")
    assert liq["type"] == "mèche de liquidation"
    assert liq["taux"] > liq["témoin"]
    assert "100 %" in liq["note"]
    assert W.classify_wick(2.0, float("nan"), "haute")["attendu"] is None
