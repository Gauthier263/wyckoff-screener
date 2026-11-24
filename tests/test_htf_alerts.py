"""Tests synthétiques des alertes HTF (hors-ligne)."""
import numpy as np
import pandas as pd

from screener.htf import alerts as A
from screener.htf import bias as B

RANGE = B.Bounds(60000, 80000, (59000, 60600), (79500, 80500))


def _path(extra=()):
    """1h : 40 jours à 70k, chute sous le plancher (creux 55 130), reprise au-dessus de 60,6k.
    `extra` : clôtures 4h ajoutées ensuite (chacune tenue 4 bougies 1h)."""
    seg = [np.full(40 * 24, 70000.0), np.linspace(70000, 57000, 24), np.full(12, 57000.0),
           np.linspace(57000, 59500, 12), np.full(12, 59500.0), np.full(48, 61500.0)]
    seg += [np.full(4, float(x)) for x in extra]
    c = np.concatenate(seg)
    idx = pd.date_range("2026-01-01", periods=len(c), freq="1h", tz="UTC")
    h1 = pd.DataFrame({"open": c, "high": c * 1.002, "low": c * 0.998, "close": c,
                       "volume": 1.0}, index=idx)
    i = 40 * 24 + 30
    h1.iloc[i, h1.columns.get_loc("low")] = 55130.0
    agg = {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}
    return {"1h": h1, "4h": h1.resample("4h").agg(agg), "1d": h1.resample("1D").agg(agg),
            "liq": None}


def test_freeze_ne_garde_que_les_bougies_closes():
    data = _path()
    t = pd.Timestamp("2026-01-10 06:00", tz="UTC")
    d = A.freeze(data, t)
    assert d["4h"].index[-1] == pd.Timestamp("2026-01-10 00:00", tz="UTC")
    assert d["1d"].index[-1] == pd.Timestamp("2026-01-09", tz="UTC")
    assert d["1h"].index[-1] == pd.Timestamp("2026-01-10 05:00", tz="UTC")


def test_sequence_deviation_puis_acceptance_une_alerte_par_changement():
    data = _path()
    t0 = pd.Timestamp("2026-02-09 20:00", tz="UTC")
    closes = list(pd.date_range(t0, data["4h"].index[-1] + A.BAR, freq="4h"))
    ev = A.scan(data, closes, RANGE)
    types = [it["type"] for _, items, _, _ in ev for it in items]
    assert types.count("déviation") == 1
    assert types.count("acceptance") == 1
    assert "biais" in types
    dev = next(it for _, items, _, _ in ev for it in items if it["type"] == "déviation")
    assert "55 130" in dev["texte"] and "(haut de la zone du plancher, range 1D)" in dev["texte"]
    # la déviation apparaît avant (ou avec) l'acceptance, jamais après
    t_dev = next(t for t, items, _, _ in ev if any(i["type"] == "déviation" for i in items))
    t_acc = next(t for t, items, _, _ in ev if any(i["type"] == "acceptance" for i in items))
    assert t_dev <= t_acc
    _, items, r, s = ev[-1]
    msg = A.compose(r, s, items)
    assert "ne pas vendre la cassure" in msg and msg.endswith(A.FOOTER)
    assert "🟢" not in msg and "🔴" not in msg


def _snap(bornes=(1, 2), dev=None, bias="neutre", wicks=None):
    b = B.Bounds(60000, 80000, (59000, 60600), (79500, 80500))
    return {"asof": pd.Timestamp("2026-11-22", tz="UTC"), "price": 61000, "bias": bias,
            "score": 0, "conviction": "aucune", "wicks": wicks or {},
            "frames": {"4h": {"zone": "bas", "bornes": bornes, "b": b, "déviation": dev,
                              "cassure": None, "accomplie": None}}}


def test_bornes_recalculees_ne_creent_pas_d_evenement():
    dev = {"côté": "sous le plancher", "extrême": 55130.0, "acceptance": False,
           "seuil_acceptance": 60600.0}
    assert A.transitions(_snap(bornes=(1, 2)), _snap(bornes=(1, 3), dev=dev)) == []
    assert [i["type"] for i in A.transitions(_snap(), _snap(dev=dev))] == ["déviation"]


def test_meche_de_liquidation_signalee_une_fois_si_non_retestee():
    w = {"tf": "4h", "at": pd.Timestamp("2026-11-21 04:00", tz="UTC"), "direction": "basse",
         "tip": 55130.0, "half": 55935.0, "size_atr": 1.8, "liq_rel": 3.1, "âge": 4,
         "retestée": False, "validée": True, "attendu": "retest du 50 % d'abord",
         "taux": 0.62, "témoin": 0.44}
    k = "4h|x|basse"
    items = A.transitions(_snap(), _snap(wicks={k: w}))
    assert [i["type"] for i in items] == ["mèche"]
    assert "55 935 (moitié de la mèche 4h" in items[0]["texte"]
    assert "62 %" in items[0]["texte"] and "1,8 ATR" in items[0]["texte"]
    assert A.transitions(_snap(wicks={k: w}), _snap(wicks={k: w})) == []
    assert A.transitions(_snap(), _snap(wicks={k: {**w, "retestée": True}})) == []
    assert A.transitions(_snap(), _snap(wicks={k: {**w, "âge": 14}})) == []


def test_justify_ajoute_la_raison_du_niveau():
    r = {60600: "haut de la zone du plancher"}
    assert A.justify("au-dessus de 60,600", r) == "au-dessus de 60 600 (haut de la zone du plancher)"
    assert A.justify("sous 12,345", r) == "sous 12 345"


def test_run_once_rattrape_puis_ne_renvoie_rien(tmp_path, monkeypatch):
    from screener import alerts as base
    data = _path()
    sent = []
    monkeypatch.setattr(A, "load_data", lambda symbol="BTC/USDT", end=None: data)
    monkeypatch.setattr(base, "_notify", lambda m: sent.append(m))
    monkeypatch.setattr(A, "MAX_CATCHUP", 40)
    bpath = tmp_path / "b.json"
    bpath.write_text('{"floor": 60000, "ceiling": 80000, "floor_zone": [59000, 60600], '
                     '"ceiling_zone": [79500, 80500]}')
    state = tmp_path / "s.json"
    state.write_text('{"evaluated_until": "2026-02-09T16:00:00+00:00"}')
    now = data["4h"].index[-1] + A.BAR + pd.Timedelta("5min")
    n1 = A.run_once(bounds_path=str(bpath), state_path=str(state), now=now)
    assert n1 >= 1 and len(sent) == n1
    assert A.run_once(bounds_path=str(bpath), state_path=str(state), now=now) == 0


def test_load_bounds_lit_la_config():
    b = A.load_bounds("config/htf_bounds.json")
    assert b.floor == 60000 and b.floor_zone == (59000, 60600) and b.source == "analyste"


def _acc_items(extra):
    data = _path(extra)
    t0 = pd.Timestamp("2026-02-14 12:00", tz="UTC")          # acceptance déjà acquise ici
    closes = list(pd.date_range(t0, data["4h"].index[-1] + A.BAR, freq="4h"))
    return [it for _, items, _, _ in A.scan(data, closes, RANGE) for it in items
            if it["type"] == "acceptance"]


def test_acceptance_perdue_seulement_apres_deux_clotures_dessous():
    """24/11 : une clôture sous 60,6k puis une indécise ne suffisent pas ; la 2e clôture
    consécutive dessous fait perdre l'acceptance, même après une clôture isolée (bug de la
    mémoire non partagée dans `scan`)."""
    assert _acc_items([60300, 61000, 61200]) == []            # clôture isolée : rien
    items = _acc_items([60300, 60300, 60400])
    assert len(items) == 1 and "PERDUE" in items[0]["texte"]
    assert "2 clôtures 4h repassées dessous" in items[0]["texte"]
