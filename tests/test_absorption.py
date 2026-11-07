"""Test synthétique : effort (CVD) vs résultat (prix) — absorption & no-demand.

Bougies fabriquées pour isoler chaque cas du 2×2 effort/résultat :
  - effort fort + clôture rejetée            → absorption (signe = côté absorbant)
  - effort fort + clôture alignée             → mouvement honnête (pas d'absorption)
  - résultat fort (prix voyage) + effort nul → no_demand / no_supply
"""
import numpy as np
import pandas as pd

from screener.features import add_features, add_absorption


def _base(n=30):
    """n bougies « neutres » : range 10, clôture au milieu, delta ±3 alterné."""
    idx = pd.date_range("2026-06-01", periods=n, freq="8h", tz="UTC")
    o = np.full(n, 100.0)
    hi = np.full(n, 105.0)
    lo = np.full(n, 95.0)
    c = np.full(n, 100.0)
    vol = np.full(n, 1000.0)
    delta = np.where(np.arange(n) % 2 == 0, 3.0, -3.0)
    df = pd.DataFrame({"open": o, "high": hi, "low": lo, "close": c, "volume": vol}, index=idx)
    return df, pd.Series(delta, index=idx)


def _build():
    df, delta = _base(30)
    # bar 25 — ABSORPTION haussière : vente agressive (delta très négatif) MAIS clôture haute
    df.iloc[25, df.columns.get_loc("close")] = 104.0     # clv = 0.9
    delta.iloc[25] = -30.0
    # bar 26 — mouvement HONNÊTE baissier : vente agressive ET clôture basse
    df.iloc[26, df.columns.get_loc("close")] = 96.0      # clv = 0.1
    delta.iloc[26] = -30.0
    # bar 27 — NO-DEMAND : large bougie haussière, mais delta nul
    df.iloc[27, df.columns.get_loc("open")] = 100.0
    df.iloc[27, df.columns.get_loc("high")] = 112.0
    df.iloc[27, df.columns.get_loc("low")] = 100.0
    df.iloc[27, df.columns.get_loc("close")] = 112.0     # ret = +12 ≈ 1.2 ATR
    delta.iloc[27] = 0.0
    # bar 28 — NO-SUPPLY : large bougie baissière, mais delta nul
    df.iloc[28, df.columns.get_loc("open")] = 100.0
    df.iloc[28, df.columns.get_loc("high")] = 100.0
    df.iloc[28, df.columns.get_loc("low")] = 88.0
    df.iloc[28, df.columns.get_loc("close")] = 88.0      # ret = −12 ≈ −1.2 ATR
    delta.iloc[28] = 0.0
    feat = add_features(df)
    return add_absorption(feat, delta)


def test_absorption_sign_and_side():
    out = _build()
    # bar 25 : flux vendeur rejeté (clôture haute) → absorption > 0, côté vente (delta_z < 0)
    assert out["absorption"].iloc[25] > 0
    assert out["delta_z"].iloc[25] < 0          # la DEMANDE absorbe (haussier)
    # bar 26 : vente + clôture basse = honnête → pas d'absorption
    assert out["absorption"].iloc[26] < 0


def test_absorption_zero_on_honest_neutral_bar():
    out = _build()
    # une bougie neutre (clôture au milieu, clv 0.5) → clv_s = 0 → absorption ≈ 0
    assert abs(out["absorption"].iloc[20]) < 1e-9


def test_no_demand_and_no_supply_flags():
    out = _build()
    # bar 27 : prix monte fort sans flux → no_demand, pas no_supply
    assert bool(out["no_demand"].iloc[27]) is True
    assert bool(out["no_supply"].iloc[27]) is False
    # bar 28 : prix baisse fort sans flux → no_supply, pas no_demand
    assert bool(out["no_supply"].iloc[28]) is True
    assert bool(out["no_demand"].iloc[28]) is False
    # une bougie à fort flux n'est jamais un no-demand/no-supply
    assert bool(out["no_demand"].iloc[25]) is False
    assert bool(out["no_supply"].iloc[25]) is False


def test_columns_present():
    out = _build()
    for col in ("delta", "delta_z", "ret_atr", "absorption", "absorption_w",
                "no_demand", "no_supply"):
        assert col in out.columns


def test_windowed_absorption_catches_multibar():
    """Vente sur la barre N puis rejet sur la barre N+1 : le per-barre RATE l'absorption,
    la version fenêtrée (absorption_w) la CAPTE."""
    df, delta = _base(30)
    # bar 25 : vente agressive, clôture sur le bas (per-barre = honnête, abs < 0)
    df.iloc[25, df.columns.get_loc("open")] = 100.0
    df.iloc[25, df.columns.get_loc("high")] = 105.0
    df.iloc[25, df.columns.get_loc("low")] = 90.0
    df.iloc[25, df.columns.get_loc("close")] = 90.0      # clv = 0
    delta.iloc[25] = -30.0
    # bar 26 : reprise franche (reclaim), peu de flux
    df.iloc[26, df.columns.get_loc("open")] = 90.0
    df.iloc[26, df.columns.get_loc("high")] = 102.0
    df.iloc[26, df.columns.get_loc("low")] = 90.0
    df.iloc[26, df.columns.get_loc("close")] = 101.0     # ravale la vente
    delta.iloc[26] = 0.0
    out = add_absorption(add_features(df), delta, win=3)
    # per-barre sur la barre de vente = honnête (négatif), rate l'absorption
    assert out["absorption"].iloc[25] < 0
    # fenêtré sur la barre de reprise = absorption captée (vente nette rejetée sur 3 barres)
    assert out["absorption_w"].iloc[26] > 0
