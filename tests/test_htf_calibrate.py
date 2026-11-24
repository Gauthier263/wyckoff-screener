"""Tests hors-ligne de la calibration des leviers (aucun appel réseau)."""
import numpy as np
import pandas as pd

from screener.htf import calibrate as C


def test_nnls_retrouve_des_poids_connus():
    rng = np.random.default_rng(0)
    A = rng.random((60, 3))
    w = np.array([0.5, 0.0, 0.25])
    x = C.nnls(A, A @ w)
    assert np.allclose(x, w, atol=1e-2)
    assert (x >= 0).all()


def test_nnls_ne_renvoie_jamais_de_poids_negatif():
    A = np.array([[1.0, 0.0], [0.0, 1.0]])
    b = np.array([1.0, -5.0])          # second coefficient « naturellement » négatif
    x = C.nnls(A, b)
    assert (x >= 0).all() and x[0] > 0


def test_fit_retombe_sur_les_defauts_quand_rien_nest_appris(monkeypatch):
    idx = pd.date_range("2026-01-01", periods=30, freq="1h", tz="UTC")
    zero = pd.Series(np.zeros(30), index=idx)
    monkeypatch.setattr(C, "predicted_burn",
                        lambda *a, **k: {l: {"long": zero, "short": zero}
                                         for l in C.CANDIDATE_LEVERAGES})
    obs = pd.DataFrame({"long": np.ones(30), "short": np.ones(30)}, index=idx)
    res = C.fit_leverage_tiers(pd.DataFrame(), None, None, obs)
    assert res["fit"] == {"long": 0.0, "short": 0.0}
    assert res["tiers"]["long"] == res["tiers"]["short"]
    assert "défaut" in res["status"]


def test_fit_separe_les_deux_cotes(monkeypatch):
    """Les longs et les shorts n'ont pas le même profil de levier : les confondre
    déplace les amas (constaté sur le 22/11)."""
    idx = pd.date_range("2026-01-01", periods=40, freq="1h", tz="UTC")
    a = pd.Series(np.where(np.arange(40) % 4 == 0, 1.0, 0.0), index=idx)
    b = pd.Series(np.where(np.arange(40) % 7 == 0, 1.0, 0.0), index=idx)
    monkeypatch.setattr(C, "predicted_burn", lambda *x, **k: {
        5: {"long": a, "short": 0 * a}, 10: {"long": 0 * b, "short": b},
        20: {"long": 0 * a, "short": 0 * a}, 25: {"long": 0 * a, "short": 0 * a},
        50: {"long": 0 * a, "short": 0 * a}, 100: {"long": 0 * a, "short": 0 * a}})
    obs = pd.DataFrame({"long": a * 0.6, "short": b * 0.3})
    res = C.fit_leverage_tiers(pd.DataFrame(), None, None, obs)
    assert max(res["tiers"]["long"], key=res["tiers"]["long"].get) == 5
    assert max(res["tiers"]["short"], key=res["tiers"]["short"].get) == 10
