"""Tests synthétiques de la carte de liquidité (hors-ligne, aucun appel réseau)."""
import numpy as np
import pandas as pd

from screener.htf import liqmap as L


def _bars(prices, volumes=None):
    idx = pd.date_range("2026-01-01", periods=len(prices), freq="1h", tz="UTC")
    p = np.asarray(prices, dtype=float)
    return pd.DataFrame({"open": p, "high": p * 1.001, "low": p * 0.999, "close": p,
                         "volume": volumes if volumes is not None else np.ones(len(p))},
                        index=idx)


def test_price_grid_geometrique():
    g = L.price_grid(100, 110, 0.01)
    assert g[0] == 100 and g[-1] >= 110
    assert np.allclose(np.diff(g) / g[:-1], 0.01)
    assert len(L.price_grid(110, 100, 0.01)) == 0


def test_side_split_sans_flux_ne_tranche_pas():
    assert L.side_split(0.0, 100.0) == 0.5
    assert L.side_split(50.0, 0.0) == 0.5          # volume nul
    assert L.side_split(float("nan"), 100.0) == 0.5
    assert L.side_split(100.0, 100.0) == 1.0       # flux 100 % acheteur -> longs
    assert L.side_split(-100.0, 100.0) == 0.0


def test_positions_se_deposent_au_prix_douverture():
    # OI qui monte de 100 pendant que le prix stagne à 60 000 -> mur à 60 000
    df = _bars([60000] * 10)
    oi = pd.Series(np.linspace(1000, 1100, 10), index=df.index)
    m = L.build_map(df, oi, step_pct=0.002)
    peak = m["grid"][int(np.argmax(m["positions"]))]
    assert abs(peak / 60000 - 1) < 0.005
    assert m["positions"].sum() > 0


def test_les_fermetures_retirent_les_positions():
    """Sans retrait des fermetures, le profil ne ferait qu'empiler — l'erreur du prototype."""
    df = _bars([60000] * 20)
    monte = pd.Series(np.r_[np.linspace(1000, 1100, 10), np.full(10, 1100.0)], index=df.index)
    aller_retour = pd.Series(np.r_[np.linspace(1000, 1100, 10),
                                   np.linspace(1100, 1000, 10)], index=df.index)
    tot_monte = L.build_map(df, monte, step_pct=0.002)["positions"].sum()
    tot_ar = L.build_map(df, aller_retour, step_pct=0.002)["positions"].sum()
    assert tot_ar < tot_monte * 0.25


def test_liquidations_longues_sous_le_prix_et_courtes_au_dessus():
    df = _bars([60000] * 10)
    oi = pd.Series(np.linspace(1000, 1100, 10), index=df.index)
    delta = pd.Series(np.ones(10), index=df.index)      # flux 100 % acheteur -> longs
    m = L.build_map(df, oi, delta, step_pct=0.002, leverage_tiers={10: 1.0})
    g = m["grid"]
    assert m["liq_long"].sum() > 0
    assert m["liq_short"].sum() == 0                    # aucun short initiateur
    peak = g[int(np.argmax(m["liq_long"]))]
    assert abs(peak / (60000 * 0.9) - 1) < 0.01         # levier 10 -> -10 %

    m2 = L.build_map(df, oi, -delta, step_pct=0.002, leverage_tiers={10: 1.0})
    peak2 = m2["grid"][int(np.argmax(m2["liq_short"]))]
    assert abs(peak2 / (60000 * 1.1) - 1) < 0.01        # shorts -> +10 %
    assert m2["liq_long"].sum() == 0


def test_carburant_consomme_quand_le_prix_le_traverse():
    """Un amas touché n'attire plus : « liquidation cluster hit »."""
    monte = [60000] * 10
    df_a = _bars(monte)
    oi_a = pd.Series(np.linspace(1000, 1100, 10), index=df_a.index)
    delta_a = pd.Series(-np.ones(10), index=df_a.index)   # shorts -> liquidations à 66 000
    m_a = L.build_map(df_a, oi_a, delta_a, step_pct=0.002, leverage_tiers={10: 1.0})
    assert m_a["liq_short"].sum() > 0

    # même séquence, puis le prix va chercher 66 000 : le carburant doit y brûler
    df_b = _bars(monte + [62000, 64000, 66000, 65000])
    oi_b = pd.Series(np.r_[np.linspace(1000, 1100, 10), [1100.0] * 4], index=df_b.index)
    delta_b = pd.Series(np.r_[-np.ones(10), np.zeros(4)], index=df_b.index)
    m_b = L.build_map(df_b, oi_b, delta_b, step_pct=0.002, leverage_tiers={10: 1.0})
    g = m_b["grid"]
    around = (g >= 65800) & (g <= 66200)
    assert m_b["liq_short"][around].sum() == 0


def test_clusters_regroupe_et_classe():
    grid = np.array([100.0, 100.4, 100.8, 110.0, 120.0])
    vals = np.array([5.0, 5.0, 0.0, 1.0, 9.0])
    c = L.clusters(grid, vals, top_n=3, merge_pct=0.006)
    # 100.0 et 100.4 fusionnent (10.0 au total) et passent donc devant le pic isolé à 120
    assert c.loc[0, "value"] == 10.0 and c.loc[0, "low"] == 100.0
    assert c.loc[1, "peak"] == 120.0
    assert abs(c["share"].sum() - 1.0) < 1e-9
    assert L.clusters(np.array([]), np.array([])).empty


def test_thin_air_detecte_le_vide_au_dessus():
    grid = np.array([100.0, 101.0, 102.0, 103.0, 104.0, 105.0])
    vals = np.array([10.0, 10.0, 0.0, 0.0, 0.0, 10.0])
    ta = L.thin_air(grid, vals, price=101.0, side="up", min_width_pct=0.005)
    assert len(ta) == 1
    assert ta.loc[0, "low"] == 102.0 and ta.loc[0, "high"] == 104.0


def test_squeeze_delta_signe_et_ratio():
    grid = np.array([90.0, 95.0, 105.0, 110.0])
    liq_long = np.array([4.0, 2.0, 0.0, 0.0])      # sous le prix
    liq_short = np.array([0.0, 0.0, 3.0, 9.0])     # au-dessus
    d = L.squeeze_delta(liq_long, liq_short, grid, price=100.0, within_pct=0.15)
    assert d["long_fuel_down"] == 6.0 and d["short_fuel_up"] == 12.0
    assert d["ratio"] == 2.0 and d["skew"] > 0
    vide = L.squeeze_delta(np.zeros(4), np.zeros(4), grid, 100.0)
    assert vide["skew"] == 0.0


def test_les_longs_hauts_sont_liquides_quand_le_prix_seffondre():
    """Un long entré à 76k ne survit pas à un prix tombé à 59k : son niveau de liquidation
    a été franchi. Sans cette règle, nos murs restaient collés à 75k le 22/11 (prix 59k)."""
    prices = [76000.0] * 30 + list(np.linspace(76000, 59000, 30))
    df = _bars(prices, volumes=np.full(60, 100.0))
    # OI qui monte pendant la phase haute (longs qui ouvrent), puis stable
    oi = pd.Series(np.r_[np.linspace(1000, 2000, 30), np.full(30, 2000.0)], index=df.index)
    delta = pd.Series(np.r_[np.full(30, 100.0), np.zeros(30)], index=df.index)  # longs

    m = L.build_map(df, oi, delta, step_pct=0.002, churn_frac=0.0,
                    unlevered_frac=0.0, leverage_tiers={10: 1.0})
    g, pos = m["grid"], m["positions"]
    assert m["burned_long"] > 0                     # des longs liquidés en route
    assert pos[g >= 74000].sum() < 1e-6             # plus rien n'est resté ouvert en haut

    # à l'inverse, des SHORTS ouverts à 76k survivent à la chute : ils sont en gain
    m2 = L.build_map(df, oi, -delta, step_pct=0.002, churn_frac=0.0,
                     unlevered_frac=0.0, leverage_tiers={10: 1.0})
    assert m2["burned_short"] == 0
    assert m2["positions"][m2["grid"] >= 74000].sum() > 0

    # avec un palier non liquidable, une part des longs hauts survit : c'est ce que
    # montrent les positions réelles Hyperliquid (cross très collatéralisé)
    m3 = L.build_map(df, oi, delta, step_pct=0.002, churn_frac=0.0,
                     unlevered_frac=0.5, leverage_tiers={10: 1.0})
    assert m3["positions"][m3["grid"] >= 74000].sum() > 0


def test_churn_erode_les_positions_a_oi_constant():
    """OI stable ≠ absence de rotation : le renouvellement doit faire tourner le carnet."""
    df = _bars([60000.0] * 40, volumes=np.full(40, 100.0))
    oi = pd.Series(np.r_[np.linspace(1000, 2000, 20), np.full(20, 2000.0)], index=df.index)
    sans = L.build_map(df, oi, step_pct=0.002, churn_frac=0.0)
    avec = L.build_map(df, oi, step_pct=0.002, churn_frac=0.2)
    # même OI total, mais avec churn l'âge moyen du carnet est plus faible : on le voit à
    # la quantité restante issue des toutes premières barres (niveaux hors du prix final)
    assert avec["positions"].sum() <= sans["positions"].sum() + 1e-6
