"""
Tests synthétiques du screener multi-cours (scan.py + sources.py).

Hors-ligne : on monkeypatche `sources.fetch` pour injecter des séries fabriquées,
puis on vérifie la validité minimale (Climax+AR+ST), le score de fiabilité, la phase
et la logique de confluence. Test dédié pour le ré-échantillonnage 4h.
"""
import numpy as np
import pandas as pd

from screener import scan, sources
from screener.features import add_features
from screener.universe import Asset, build_assets
from screener.window import detect_window_structure


def _df(rows):
    idx = pd.date_range("2024-01-01", periods=len(rows), freq="h", tz="UTC")
    df = pd.DataFrame(rows, columns=["open", "high", "low", "close", "volume"], index=idx)
    return df


def _drift(n, base, vol=1000.0, seed=0):
    rng = np.random.default_rng(seed)
    rows, c = [], base
    for _ in range(n):
        c = c + rng.normal(0, 0.4)
        o = c + rng.normal(0, 0.3)
        h = max(o, c) + abs(rng.normal(0, 0.3))
        l = min(o, c) - abs(rng.normal(0, 0.3))
        rows.append([o, h, l, c, vol * rng.uniform(0.8, 1.1)])
    return rows


def _accumulation_rows():
    rows = _drift(40, 100.0, seed=1)
    rows += [[100.0, 100.5, 95.0, 99.5, 3200.0]]      # SC
    rows += [[99.5, 103.0, 99.4, 102.6, 800.0]]       # AR
    rows += _drift(4, 102.0, vol=600.0, seed=2)
    rows += [[96.6, 97.0, 95.6, 96.4, 500.0]]         # ST
    rows += _drift(3, 97.5, vol=600.0, seed=3)
    rows += [[98.0, 104.5, 97.8, 104.2, 2600.0]]      # SOS
    rows += _drift(2, 104.0, vol=700.0, seed=4)
    return rows


_CFG = {
    "thresholds": {}, "window": 20, "vol_ma": 20, "atr_period": 14,
    "limit": 300, "source": "yahoo", "use_cache": False,
}


def test_has_min_sequence_true_on_accumulation():
    struct = detect_window_structure(add_features(_df(_accumulation_rows())), lookback=20)
    assert scan.has_min_sequence(struct)


def test_has_min_sequence_false_on_flat():
    struct = detect_window_structure(add_features(_df(_drift(80, 100.0, seed=9))), lookback=30)
    assert not scan.has_min_sequence(struct)


def test_analyze_asset_detects_validated_accumulation(monkeypatch):
    df = _df(_accumulation_rows())
    monkeypatch.setattr(sources, "fetch", lambda *a, **k: df.copy())
    asset = Asset("TEST", "crypto", "TEST-USD", "TEST/USDT")
    res = scan.analyze_asset(asset, dict(_CFG))
    assert res is not None
    assert res.schema == "accumulation"
    assert res.reliability > 0
    assert "SC" in res.events and "ST" in res.events
    # SOS imprimé → phase D, et confluence renforcée (HTF identique au LTF ici).
    assert res.phase.startswith("D")
    assert res.confluence >= scan.CONFL_ALIGNED


def test_analyze_asset_rejects_flat(monkeypatch):
    df = _df(_drift(80, 100.0, seed=11))
    monkeypatch.setattr(sources, "fetch", lambda *a, **k: df.copy())
    asset = Asset("FLAT", "crypto", "FLAT-USD", "FLAT/USDT")
    assert scan.analyze_asset(asset, dict(_CFG)) is None


def test_confluence_from_bias():
    acc = detect_window_structure(add_features(_df(_accumulation_rows())), lookback=20)
    # HTF aligné + SOS présent dans la séquence → multiplicateur déclencheur (1.5)
    mult_aligned, bias = scan._confluence("accumulation", acc)
    assert mult_aligned == scan.CONFL_TRIGGER and bias == "accumulation"
    # HTF en conflit → pénalité
    mult_conflict, _ = scan._confluence("distribution", acc)
    assert mult_conflict == scan.CONFL_CONFLICT
    # HTF neutre → pas de modification
    mult_neutral, shown = scan._confluence("neutral", acc)
    assert mult_neutral == scan.CONFL_NEUTRAL and shown == "—"


def test_htf_context_phase_aware():
    # Tendance haussière + clôture au plus haut → contexte distribution en B→C.
    up = _df(_drift(50, 100.0, seed=1))
    up.iloc[-1, up.columns.get_loc("close")] = float(up["high"].max())
    # force une hausse nette de la moyenne récente vs le début de fenêtre
    up.iloc[-10:, up.columns.get_loc("close")] += 12.0
    up.iloc[-10:, up.columns.get_loc("high")] += 12.0
    assert scan.htf_context_bias(up, "distribution", phase_d=False) == "distribution"
    # En phase D, une tendance baissière confirme la distribution (markdown en cours).
    down = _df(_drift(50, 100.0, seed=2))
    down.iloc[-10:, down.columns.get_loc("close")] -= 12.0
    down.iloc[-10:, down.columns.get_loc("low")] -= 12.0
    assert scan.htf_context_bias(down, "distribution", phase_d=True) == "distribution"
    # Dérive plate → neutre.
    flat = _df(_drift(50, 100.0, seed=3))
    assert scan.htf_context_bias(flat, "distribution", phase_d=False) == "neutral"


def test_resample_4h_aggregates_ohlcv():
    rows = [[10, 12, 9, 11, 100], [11, 15, 10, 14, 200],
            [14, 16, 13, 15, 150], [15, 15, 11, 12, 250],
            [12, 13, 8, 9, 300], [9, 11, 7, 10, 120],
            [10, 14, 10, 13, 130], [13, 18, 12, 17, 170]]
    df = _df(rows)
    out = sources.resample_ohlcv(df, "4h")
    assert len(out) == 2
    first = out.iloc[0]
    assert first["open"] == 10 and first["close"] == 12   # open du 1er, close du 4e
    assert first["high"] == 16 and first["low"] == 9       # extrêmes du bloc
    assert first["volume"] == 700                          # somme 100+200+150+250


def test_volume_guard_rejects_sparse_volume(monkeypatch):
    rows = _accumulation_rows()
    df = _df(rows)
    # force la moitié des barres de la fenêtre à volume nul (cas Yahoo crypto intraday)
    df.iloc[-20::2, df.columns.get_loc("volume")] = 0
    monkeypatch.setattr(sources, "fetch", lambda *a, **k: df.copy())
    asset = Asset("SPARSE", "crypto", "SPARSE-USD", "SPARSE/USDT")
    assert scan.analyze_asset(asset, dict(_CFG)) is None


def test_timeframes_per_class():
    from screener.universe import TF_BY_CLASS
    # Crypto reste en intraday 4h×1h (via ccxt), actions/MP en 1D×4h.
    assert TF_BY_CLASS["crypto"] == ("4h", "1h")
    assert TF_BY_CLASS["equity"] == ("1d", "4h")
    assert TF_BY_CLASS["commodity"] == ("1d", "4h")


def test_build_assets_classes_and_count():
    crypto = build_assets(("crypto",))
    assert all(a.cls == "crypto" and a.ccxt for a in crypto)
    assert len(crypto) == 46
    alla = build_assets()
    assert len(alla) == 46 + 90 + 8
