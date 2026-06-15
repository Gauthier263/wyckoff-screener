"""
Tests synthétiques du détecteur de vides de chute brutale (liquidity.py).

On fabrique une dérive calme puis une **chute violente one-sided** (grosse barre baissière,
volume climactique) et on vérifie que :
  - le vide est détecté avec les bonnes bornes (haut = avant-chute, bas = extrême) ;
  - un vide non récupéré est "open" et scoré positivement ;
  - une remontée du prix dans le vide le passe en "partial"/"filled" (+ snap-back) ;
  - une dérive plate (aucune chute anormale) ne produit aucun vide ;
  - le gate de tendance (`in_uptrend`) reflète la position vs MA longue.
Hors-ligne (pas de réseau).
"""
import numpy as np
import pandas as pd

from screener.features import add_features
from screener.liquidity import VoidThresholds, detect_voids


def _df(rows):
    idx = pd.date_range("2024-01-01", periods=len(rows), freq="h", tz="UTC")
    df = pd.DataFrame(rows, columns=["open", "high", "low", "close", "volume"], index=idx)
    return add_features(df, vol_ma=20, atr_period=14)


def _drift(n, base, vol=1000.0, seed=0, step=0.0):
    """Barres calmes proches de `base` (volume normal, spread étroit), dérive `step`/barre."""
    rng = np.random.default_rng(seed)
    rows, c = [], base
    for _ in range(n):
        c = c + step + rng.normal(0, 0.4)
        o = c + rng.normal(0, 0.3)
        h = max(o, c) + abs(rng.normal(0, 0.3))
        l = min(o, c) - abs(rng.normal(0, 0.3))
        rows.append([o, h, l, c, vol * rng.uniform(0.8, 1.1)])
    return rows


# z_window=20 / trend_ma=30 pour des fixtures courtes
TH = VoidThresholds(z_window=20, trend_ma=30)


def test_drop_void_open():
    rows = _drift(60, 100.0, seed=1)                 # base calme (ATR/MAD/MA)
    # chute violente : ouvre à 100, s'effondre à 92, clôture 92.3, volume ×4 → one-sided
    rows += [[100.0, 100.1, 92.0, 92.3, 4000.0]]
    rows += _drift(3, 91.5, vol=900.0, seed=2)        # reste sous la clôture : non récupéré

    voids = detect_voids(_df(rows), th=TH, lookback=40)
    assert voids, "une chute brutale anormale doit créer un vide"
    v = voids[0]
    assert abs(v.top - 100.1) < 0.5 and abs(v.bottom - 92.0) < 0.5
    assert v.ret_z <= -2.5 and v.vol_ratio >= 3.0 and v.body_frac >= 0.6
    assert v.fill_status == "open" and v.score > 0
    assert "chute" in v.why and v.theory
    assert isinstance(v.ts, pd.Timestamp)


def test_drop_void_recovers():
    rows = _drift(60, 100.0, seed=3)
    rows += [[100.0, 100.1, 92.0, 92.3, 4000.0]]
    # le prix remonte traverser tout le vide (récupération complète) + snap-back
    rows += [[92.5, 100.5, 92.4, 100.2, 1500.0]]
    rows += _drift(2, 100.0, vol=900.0, seed=4)

    voids = detect_voids(_df(rows), th=TH, lookback=40)
    assert voids, "le vide doit rester repéré, même récupéré"
    v = voids[0]
    assert v.fill_status == "filled"
    assert v.reclaimed is True            # clôture repassée au-dessus de l'open de la chute
    assert v.score == 0.0                 # vide purgé → plus de signal


def test_no_void_on_flat_drift():
    voids = detect_voids(_df(_drift(80, 100.0, seed=9)), th=TH, lookback=40)
    assert voids == []


def test_backtest_void_fills_win():
    from screener.backtest import BTParams, backtest_void_features
    rows = _drift(60, 100.0, seed=11)
    rows += [[100.0, 100.1, 92.0, 92.3, 4000.0]]       # chute (haut du vide = 100.1)
    rows += [[92.5, 101.0, 92.4, 100.5, 1500.0]]       # remonte combler le vide → win
    rows += _drift(3, 100.0, vol=900.0, seed=12)
    feat = _df(rows)
    p = BTParams(stop_atr=1.0, fill_target=1.0, max_hold=5)
    trades = backtest_void_features("X/USDT", feat, TH, p)
    assert len(trades) == 1
    t = trades[0]
    assert t.direction == "long" and t.outcome == "win" and t.r > 0
    assert t.event in ("void_up", "void_down")


def _cycles(n_cycles, recover, seed):
    """Série : chutes brutales répétées, suivies (ou non) d'une récupération complète."""
    rng = np.random.default_rng(seed)
    rows, c = [], 100.0
    for _ in range(30):                                   # calme initial (z/MA)
        c += rng.normal(0, 0.3); o = c + rng.normal(0, 0.2)
        h, l = max(o, c) + abs(rng.normal(0, 0.2)), min(o, c) - abs(rng.normal(0, 0.2))
        rows.append([o, h, l, c, 1000 * rng.uniform(0.9, 1.1)])
    for _ in range(n_cycles):
        top = c
        rows.append([c, c + 0.1, c - 9.0, c - 8.5, 6000.0]); c = c - 8.5   # chute
        if recover:
            rows.append([c, top + 1.0, c - 0.2, top + 0.5, 1500.0]); c = top + 0.5   # comble
        for _ in range(14):                               # dérive (volume normal)
            c += rng.normal(0, 0.3); o = c + rng.normal(0, 0.2)
            h, l = max(o, c) + abs(rng.normal(0, 0.2)), min(o, c) - abs(rng.normal(0, 0.2))
            rows.append([o, h, l, c, 1000 * rng.uniform(0.9, 1.1)])
    return _df(rows)


def test_void_efficiency_distinguishes_markets():
    from screener.liquidity import void_efficiency
    eff = void_efficiency(_cycles(6, recover=True, seed=1), th=TH, horizon=8, last_n=20)
    ineff = void_efficiency(_cycles(6, recover=False, seed=2), th=TH, horizon=8, last_n=20)
    assert eff["n_voids"] >= 5 and ineff["n_voids"] >= 5
    assert eff["pct90"] >= 80.0          # marché qui rééquilibre
    assert ineff["pct90"] <= 20.0        # marché qui ne récupère pas
    assert eff["median_bars90"] is not None


def test_trend_gate_flags_downtrend():
    # chute anormale au sein d'un downtrend établi → in_uptrend False (couteau qui tombe)
    rows = _drift(60, 140.0, seed=5, step=-0.8)       # dérive baissière (prix < MA ? non…)
    rows += [[float(rows[-1][3]), float(rows[-1][3]) + 0.1,
              float(rows[-1][3]) - 8.0, float(rows[-1][3]) - 7.7, 4000.0]]
    rows += _drift(3, float(rows[-1][3]), vol=900.0, seed=6, step=-0.5)
    voids = detect_voids(_df(rows), th=TH, lookback=40)
    assert voids
    assert voids[0].in_uptrend is False
