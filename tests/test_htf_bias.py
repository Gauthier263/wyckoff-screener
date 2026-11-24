"""Tests synthétiques du moteur de biais HTF (hors-ligne)."""
import numpy as np
import pandas as pd

from screener.htf import bias as B


def _d(closes, lows=None, highs=None, freq="1D"):
    c = np.asarray(closes, dtype=float)
    idx = pd.date_range("2026-01-01", periods=len(c), freq=freq, tz="UTC")
    lo = np.asarray(lows, dtype=float) if lows is not None else c * 0.995
    hi = np.asarray(highs, dtype=float) if highs is not None else c * 1.005
    return pd.DataFrame({"open": c, "high": hi, "low": lo, "close": c,
                         "volume": np.ones(len(c))}, index=idx)


RANGE = B.Bounds(60000, 80000, (59000, 60600), (79500, 80500))


def test_deviation_sous_le_plancher_reprise_donne_un_biais_haussier():
    """Le cas du 22/11 : sortie sous le plancher puis retour dans le range."""
    c = [70000] * 20 + [62000, 58000, 56000, 59500, 60800, 61000]
    lo = list(np.array(c) * 0.995)
    lo[-4] = 55130
    f = B.read_frame(_d(c, lows=lo), RANGE, "1D")
    assert f["déviation"] and f["déviation"]["côté"] == "sous le plancher"
    assert f["déviation"]["extrême"] == 55130
    assert f["score"] == 2 and f["cassure"] is None


def test_l_episode_le_plus_recent_l_emporte():
    """Un franchissement du plafond ancien ne masque pas la sortie récente sous le plancher
    (bug constaté sur le 22/11)."""
    c = [79000, 81500, 79000] + [70000] * 15 + [58000, 57000, 60800, 61000]
    hi = list(np.array(c) * 1.005)
    hi[1] = 82061
    f = B.read_frame(_d(c, highs=hi), RANGE, "1D", lookback=30)
    assert f["déviation"]["côté"] == "sous le plancher"


def test_cassure_installee_donne_le_sens_de_la_cassure():
    c = [70000] * 20 + [58000, 57500, 57000, 56500]
    f = B.read_frame(_d(c), RANGE, "1D")
    assert f["cassure"] and f["cassure"]["sens"] == "baissière"
    assert f["score"] == -2 and f["zone"] == "sous le range"


def test_milieu_du_range_est_neutre():
    f = B.read_frame(_d([70000] * 30), RANGE, "1D")
    assert f["zone"] == "milieu" and f["score"] == 0


def test_zone_du_plafond_penche_a_la_baisse_sans_signal_fort():
    f = B.read_frame(_d([79000] * 30), RANGE, "4h")
    assert f["zone"] == "haut" and f["score"] == -1


def test_assess_assemble_biais_scenarios_et_alerte():
    c = [70000] * 40 + [62000, 58000, 56000, 59500, 60800, 61000]
    lo = list(np.array(c) * 0.995)
    lo[-4] = 55130
    d1 = _d(c, lows=lo)
    h4 = _d([61000] * 60, freq="4h")
    r = B.assess(d1, h4, bounds_1d=RANGE, bounds_4h=B.Bounds(55000, 66000))
    assert r.bias == "haussier"
    haussier = r.scenarios[0]
    assert haussier["nom"] == "haussier" and "60,600" in haussier["déclencheur"]
    assert "acquise" in haussier["déclencheur"]          # 2 clôtures 4h au-dessus de 60,6k
    assert haussier["invalidation"].endswith("55,130")
    assert any("ne pas vendre la cassure" in a for a in r.alerts)
    assert any(z["prix"] == RANGE.mid for z in r.zones)
    assert "Biais : haussier" in B.to_text(r)


def test_bounds_zones_par_defaut():
    b = B.Bounds(60000, 80000)
    assert b.floor_zone == (60000, 60000) and b.mid == 70000
    assert abs(b.position(70000) - 0.5) < 1e-9
