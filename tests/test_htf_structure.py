"""Tests synthétiques de la structure de prix HTF (hors-ligne, aucun appel réseau)."""
import numpy as np
import pandas as pd

from screener.htf import structure as S


def _ohlc(closes, highs=None, lows=None, freq="4h"):
    c = np.asarray(closes, dtype=float)
    idx = pd.date_range("2026-01-01", periods=len(c), freq=freq, tz="UTC")
    h = np.asarray(highs, dtype=float) if highs is not None else c * 1.002
    l = np.asarray(lows, dtype=float) if lows is not None else c * 0.998
    return pd.DataFrame({"open": c, "high": h, "low": l, "close": c,
                         "volume": np.ones(len(c))}, index=idx)


def _zigzag(low, high, cycles, per=20):
    """Oscillation régulière entre deux bornes : un range de manuel."""
    out = []
    for _ in range(cycles):
        out += list(np.linspace(low, high, per)) + list(np.linspace(high, low, per))
    return out


# ----------------------------------------------------------------- niveaux et ranges

def test_cluster_levels_regroupe_et_compte_les_touches():
    lv = S.cluster_levels([100.0, 100.2, 100.1, 120.0, 119.8], tol_pct=0.01)
    assert lv[0]["touches"] == 3 and abs(lv[0]["price"] - 100.1) < 0.2
    assert lv[1]["touches"] == 2
    assert S.cluster_levels([]) == []


def test_find_range_retrouve_les_bornes():
    df = _ohlc(_zigzag(60_000, 80_000, cycles=4))
    r = S.find_range(df)
    assert r is not None
    assert abs(r.low / 60_000 - 1) < 0.02
    assert abs(r.high / 80_000 - 1) < 0.02
    assert abs(r.mid - 70_000) < 2_000
    assert r.touches_low >= 2 and r.touches_high >= 2


def test_range_zone_et_position():
    r = S.Range(low=60_000, high=80_000)
    assert r.zone(61_000) == "bas"
    assert r.zone(70_000) == "milieu"       # « nothing to do at mid-range »
    assert r.zone(79_000) == "haut"
    assert abs(r.position(70_000) - 0.5) < 1e-9


def test_nested_ranges_du_plus_large_au_plus_serre():
    large = _zigzag(60_000, 80_000, cycles=3)
    serre = _zigzag(72_000, 78_000, cycles=3)
    df = _ohlc(large + serre)
    rs = S.nested_ranges(df, windows=(None, 120))
    assert len(rs) == 2
    assert rs[0].high - rs[0].low > rs[1].high - rs[1].low


# ----------------------------------------------------------------- acceptance

def test_acceptance_exige_des_clotures_pas_une_meche():
    # le prix pique au-dessus de 100 mais clôture toujours dessous
    df = _ohlc([98, 99, 98.5, 99.2, 98.8], highs=[99, 101.5, 99.5, 102.0, 99.2],
               lows=[97, 98, 98, 98, 98])
    a = S.acceptance(df, 100.0, "above", min_closes=2)
    assert a["accepted"] is False
    assert a["wicked_only"] is True
    assert a["closes_beyond"] == 0

    # puis deux clôtures franches au-dessus
    df2 = _ohlc([98, 101, 102], highs=[99, 102, 103], lows=[97, 100, 101])
    a2 = S.acceptance(df2, 100.0, "above", min_closes=2)
    assert a2["accepted"] is True and a2["consecutive"] == 2
    assert a2["wicked_only"] is False


def test_acceptance_en_dessous():
    df = _ohlc([102, 99, 98], highs=[103, 100, 99], lows=[101, 98, 97])
    a = S.acceptance(df, 100.0, "below", min_closes=2)
    assert a["accepted"] is True and a["consecutive"] == 2


# ----------------------------------------------------------------- déviation

def test_deviation_sous_le_plancher_puis_reintegration():
    """Le cas du 22/11 : une mèche sort sous le plancher du range puis le prix revient."""
    base = _zigzag(60_000, 80_000, cycles=3)
    sortie = [59_000, 56_000, 55_130, 58_000, 61_000, 62_000]
    df = _ohlc(base + sortie)
    r = S.Range(low=60_000, high=80_000)
    d = S.detect_deviation(df, r)
    assert d is not None
    assert d.side == "sous le plancher"
    assert abs(d.extreme - 55_130 * 0.998) < 200      # l'extrême est le low de la barre
    assert d.reclaimed is True
    assert d.depth_pct > 0.07


def test_pas_de_deviation_si_le_prix_reste_dehors():
    base = _zigzag(60_000, 80_000, cycles=3)
    df = _ohlc(base + [59_000] * 20)                  # cassure installée, pas déviation
    d = S.detect_deviation(df, S.Range(low=60_000, high=80_000), max_bars_out=10)
    assert d is None


def test_deviation_au_dessus_du_plafond():
    base = _zigzag(60_000, 80_000, cycles=3)
    df = _ohlc(base + [81_000, 82_500, 79_000, 77_000])
    d = S.detect_deviation(df, S.Range(low=60_000, high=80_000))
    assert d is not None and d.side == "au-dessus du plafond" and d.reclaimed


# ----------------------------------------------------------------- mèches

def test_find_wicks_mesure_le_remplissage_a_50_et_100():
    # une barre à longue mèche basse, puis le prix remonte au-dessus du 50 %
    closes = [100.0] * 20 + [100.0, 101.0, 102.0]
    highs = [100.2] * 20 + [100.5, 101.5, 102.5]
    lows = [99.8] * 20 + [90.0, 100.5, 101.0]
    df = _ohlc(closes, highs, lows)
    ws = [w for w in S.find_wicks(df, min_atr=1.0) if w.direction == "basse"]
    assert ws, "la longue mèche basse doit être détectée"
    w = ws[0]
    assert abs(w.tip - 90.0) < 1e-6
    assert abs(w.half - 95.0) < 1e-6
    # le prix monte après la mèche : elle n'est donc pas remplie (la remplir, c'est
    # redescendre dans la zone de la mèche)
    assert w.filled_half is False and w.filled_full is False and w.bars_to_half is None

    # même mèche, mais le prix redescend ensuite jusqu'à 94 : le 50 % est rempli, pas le 100 %
    closes2 = [100.0] * 20 + [100.0, 97.0, 94.5]
    highs2 = [100.2] * 20 + [100.5, 100.0, 97.0]
    lows2 = [99.8] * 20 + [90.0, 96.0, 94.0]
    w2 = [x for x in S.find_wicks(_ohlc(closes2, highs2, lows2), min_atr=1.0)
          if x.direction == "basse"][0]
    assert w2.filled_half is True and w2.filled_full is False
    assert w2.bars_to_half == 2


def test_find_wicks_ignore_les_petites_meches():
    df = _ohlc([100.0] * 40)
    assert S.find_wicks(df, min_atr=1.0) == []


# ----------------------------------------------------------------- three taps

def test_detect_taps_compte_les_touches_et_repere_la_deviation():
    seq = ([70_000] * 5 + [60_100] + [70_000] * 10 + [60_050] + [70_000] * 10
           + [59_000] + [70_000] * 5)       # 3e touche en déviation sous le niveau
    df = _ohlc(seq)
    t = S.detect_taps(df, 60_000, "plancher", tol_pct=0.01)
    assert t is not None and t.count == 3
    assert t.deviation_index == 2            # la 3e est la déviation
    assert t.third_too_early is False


def test_detect_taps_signale_un_troisieme_trop_tot():
    """« The third hit should come later, otherwise it won't draw enough liquidity. »"""
    seq = ([70_000] * 5 + [60_100] + [70_000] * 20 + [60_050] + [70_000] * 4
           + [60_020] + [70_000] * 5)
    df = _ohlc(seq)
    t = S.detect_taps(df, 60_000, "plancher", tol_pct=0.01)
    assert t is not None and t.count == 3
    assert t.gaps[1] < t.gaps[0]
    assert t.third_too_early is True


def test_detect_taps_sur_un_plafond():
    seq = [60_000] * 5 + [79_900] + [60_000] * 10 + [82_000] + [60_000] * 5
    df = _ohlc(seq)
    t = S.detect_taps(df, 80_000, "plafond", tol_pct=0.01)
    assert t is not None and t.count == 2
    assert t.deviation_index == 1        # la 2e touche dépasse franchement le niveau


# ----------------------------------------------------------------- EMA

def test_ema_state_detecte_la_surextension():
    monte = list(np.linspace(60_000, 62_000, 60))
    df = _ohlc(monte)
    st = S.ema_state(df, period=50)
    assert st["above"] is True and st["stretch_atr"] > 0 and st["slope_pct"] > 0

    chute = list(np.linspace(62_000, 60_000, 50)) + [50_000]
    st2 = S.ema_state(_ohlc(chute), period=50)
    assert st2["above"] is False and st2["stretch_atr"] < 0

    assert S.ema_state(_ohlc([1.0] * 10), period=50)["ema"] is None


# ----------------------------------------------------------------- étude des règles

def test_wilson_encadre_la_proportion():
    """Un taux sans son intervalle n'est pas un résultat : 1,00 sur 2 cas ne vaut pas
    1,00 sur 200."""
    from screener.htf.rules_study import wilson
    lo, hi = wilson(113, 128)
    assert lo < 113 / 128 < hi and hi - lo < 0.15
    lo2, hi2 = wilson(2, 2)
    assert lo2 < 0.4 and hi2 == 1.0          # deux cas n'excluent presque rien
    assert all(np.isnan(x) for x in wilson(0, 0))


def test_study_deviations_echantillonne_sans_chevauchement():
    """Un pas plus court que l'horizon fait partager leur futur à deux observations et
    gonfle l'effectif : le pas par défaut vaut donc l'horizon."""
    import inspect

    from screener.htf import rules_study as R
    src = inspect.getsource(R.study_deviations)
    assert "step = int(step or horizon)" in src
    assert inspect.signature(R.study_deviations).parameters["step"].default is None
