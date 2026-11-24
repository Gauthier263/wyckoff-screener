"""Tests synthétiques de l'étude Three Taps (hors-ligne)."""
import numpy as np
import pandas as pd

from screener.htf import taps_study as T


def _path(points, per=8):
    """Trajectoire linéaire par morceaux entre des prix-clés, bougies serrées."""
    c = []
    for a, b in zip(points[:-1], points[1:]):
        c += list(np.linspace(a, b, per, endpoint=False))
    c.append(points[-1])
    c = np.asarray(c, dtype=float)
    idx = pd.date_range("2026-01-01", periods=len(c), freq="4h", tz="UTC")
    return pd.DataFrame({"open": c, "high": c + 0.4, "low": c - 0.4, "close": c,
                         "volume": np.ones(len(c))}, index=idx)


# préambule plat (l'ATR n'est défini qu'après 14 bougies), puis plancher à 100, plafond
# vers 120 ; trois touches, la troisième en déviation, puis 120
PRE = [115, 115, 115]
THREE = PRE + [110, 100, 118, 101, 119, 97, 105, 112, 121, 121]


def test_mirror_inverse_haut_et_bas():
    df = _path([100, 110])
    m = T.mirror(df)
    assert (m["high"] == -df["low"]).all() and (m["low"] == -df["high"]).all()
    assert (T.mirror(m)["close"] == df["close"]).all()


def test_tap_trades_numerote_les_touches_et_repere_la_deviation():
    tr = T.tap_trades(_path(THREE), pivot=3, min_height_atr=2.0, horizon=60)
    c = tr[tr["protocole"] == "contact"]
    assert set(c["k"]) >= {1, 2, 3}
    # au contact, la déviation de la 3e touche chasse le stop du trader naïf
    assert c[c["k"] == 3].iloc[0]["issue"] == "stop"
    # en entrant sur la reprise du niveau après la déviation, le trade réussit
    r = tr[(tr["protocole"] == "reprise") & (tr["k"] == 3)].iloc[0]
    assert r["deviation"] and r["issue"] == "cible"
    assert r["stop"] < r["entry"] < r["target"] and r["r"] > 0


def test_tap_trades_arrete_la_sequence_sur_cassure_installee():
    broken = PRE + [110, 100, 118, 101, 119, 90, 85, 84, 83, 82]   # le plancher cède
    tr = T.tap_trades(_path(broken), pivot=3, min_height_atr=2.0, horizon=60)
    assert (tr[tr["k"] >= 3]["issue"] != "cible").all()


def test_early_signale_une_troisieme_touche_trop_rapide():
    # 1re→2e touche : long ; 2e→3e : court (moins de la moitié)
    early = PRE + [110, 100, 118, 118, 118, 118, 100.3, 110, 100.3, 112, 121]
    tr = T.tap_trades(_path(early, per=6), pivot=3, min_height_atr=2.0, horizon=60)
    t3 = tr[(tr["k"] == 3) & (tr["protocole"] == "contact")]
    assert not t3.empty and bool(t3.iloc[0]["early"])


def test_both_sides_traite_le_plafond_par_symetrie():
    up = T.both_sides(_path(THREE), pivot=3, min_height_atr=2.0, horizon=60)
    down = T.both_sides(T.mirror(_path(THREE)), pivot=3, min_height_atr=2.0, horizon=60)
    a = up[up["côté"] == "plancher"][["k", "protocole", "issue"]].reset_index(drop=True)
    b = down[down["côté"] == "plafond"][["k", "protocole", "issue"]].reset_index(drop=True)
    assert a.equals(b)


def test_expectancy():
    g = pd.DataFrame({"issue": ["cible", "stop", "ouvert", "pas de reprise"],
                      "r": [2.0, 1.0, 5.0, None]})
    assert T.expectancy(g) == 0.5                # (+2 − 1) / 2, le trade ouvert exclu


def test_stop_en_acceptance_ne_sort_pas_sur_une_meche():
    """Sa méthode : l'invalidation est l'acceptance sous le niveau, pas une mèche. Une
    mèche isolée sous le stop ne fait pas sortir ; deux clôtures dessous, si."""
    pts = PRE + [110, 100, 118, 100.3, 100.3, 112, 121]
    df = _path(pts, per=6)
    # juste après l'entrée au contact de la 2e touche, une mèche plonge sous le stop
    base = T.tap_trades(df, pivot=3, min_height_atr=2.0, horizon=60)
    t2 = base[(base["protocole"] == "contact") & (base["k"] == 2)].iloc[0]
    i_entry = df.index.get_loc(t2["at"])
    df.iloc[i_entry + 1, df.columns.get_loc("low")] = 95.0
    meche = T.tap_trades(df, pivot=3, min_height_atr=2.0, horizon=60)
    accep = T.tap_trades(df, pivot=3, min_height_atr=2.0, horizon=60, stop_mode="acceptance")
    m2 = meche[(meche["protocole"] == "contact") & (meche["k"] == 2)].iloc[0]
    a2 = accep[(accep["protocole"] == "contact") & (accep["k"] == 2)].iloc[0]
    assert m2["issue"] == "stop" and a2["issue"] == "cible"
