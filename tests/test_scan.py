"""
Tests synthétiques du screener multi-cours (scan.py + sources.py), hors-ligne.

Couvre : validité minimale Climax+AR+ST, vérification du contexte (markdown avant
accumulation), validation événementielle (emojis), verdict/commentaire, le rendu, le
ré-échantillonnage 4h et l'univers.
"""
import numpy as np
import pandas as pd

from screener import scan, sources
from screener.events import Thresholds
from screener.features import add_features
from screener.universe import TF_SET_BY_CLASS, Asset, build_assets
from screener.window import detect_window_structure


def _df(rows):
    idx = pd.date_range("2024-01-01", periods=len(rows), freq="h", tz="UTC")
    return pd.DataFrame(rows, columns=["open", "high", "low", "close", "volume"], index=idx)


def _drift(n, base, vol=800.0, seed=0):
    rng = np.random.default_rng(seed)
    rows, c = [], base
    for _ in range(n):
        c = c + rng.normal(0, 0.4)
        o = c + rng.normal(0, 0.3)
        h = max(o, c) + abs(rng.normal(0, 0.3))
        l = min(o, c) - abs(rng.normal(0, 0.3))
        rows.append([o, h, l, c, vol * rng.uniform(0.8, 1.1)])
    return rows


def _markdown(n, start, end, vol=800.0, seed=0):
    """Segment baissier régulier (markdown) de `start` vers `end`."""
    rng = np.random.default_rng(seed)
    rows = []
    for i in range(n):
        c = start + (end - start) * (i + 1) / n
        o = c + rng.normal(0, 0.3)
        h = max(o, c) + abs(rng.normal(0, 0.3))
        l = min(o, c) - abs(rng.normal(0, 0.3))
        rows.append([o, h, l, c, vol * rng.uniform(0.8, 1.1)])
    return rows


def _accumulation_with_markdown():
    """Markdown → SC → AR → ST : accumulation (phase B→C) avec contexte correct.

    Espacement choisi pour qu'une des fenêtres (30/45/60) place le SC dans la « tête »
    sans que la recherche de l'AR n'attrape un extrême lointain.
    """
    rows = _drift(20, 110.0, seed=0)               # warmup vol_ma/ATR
    rows += _markdown(16, 109.0, 96.0, seed=1)     # markdown préalable (contexte)
    rows += [[100.0, 100.5, 95.0, 99.5, 3200.0]]   # SC
    rows += [[99.5, 103.0, 99.4, 102.6, 800.0]]    # AR
    rows += _drift(11, 101.0, vol=600.0, seed=2)
    rows += [[96.6, 97.0, 95.6, 96.4, 500.0]]      # ST
    rows += _drift(12, 98.0, vol=600.0, seed=3)
    return rows


_CFG = {
    "thresholds": {}, "vol_ma": 20, "atr_period": 14,
    "limit": 400, "source": "yahoo", "use_cache": False,
}


def test_has_min_sequence():
    s = detect_window_structure(add_features(_df(_accumulation_with_markdown())), lookback=30)
    assert scan.has_min_sequence(s)
    flat = detect_window_structure(add_features(_df(_drift(80, 100.0, seed=9))), lookback=30)
    assert not scan.has_min_sequence(flat)


def test_context_requires_prior_markdown():
    df = add_features(_df(_accumulation_with_markdown()))
    s = detect_window_structure(df, lookback=30)
    emoji, text, ok = scan._context(df, s)
    assert ok and emoji == "✅" and "markdown" in text


def test_context_rejects_flat_prelude():
    # SC sans markdown préalable (drift plat avant le climax) → contexte invalide.
    rows = _drift(40, 100.0, seed=5)
    rows += [[100.0, 100.5, 95.0, 99.5, 3200.0]]   # SC sans baisse préalable
    rows += [[99.5, 103.0, 99.4, 102.6, 800.0]]    # AR
    rows += _drift(4, 102.0, vol=600.0, seed=6)
    rows += [[96.6, 97.0, 95.6, 96.4, 500.0]]      # ST
    rows += _drift(3, 97.5, vol=600.0, seed=7)
    df = add_features(_df(rows))
    s = detect_window_structure(df, lookback=30)
    if scan.has_min_sequence(s):  # selon le drift, la séquence peut être détectée
        _, _, ok = scan._context(df, s)
        assert not ok


def test_analyze_tf_full_report(monkeypatch):
    df = _df(_accumulation_with_markdown())
    monkeypatch.setattr(sources, "fetch", lambda *a, **k: df.copy())
    asset = Asset("TEST", "crypto", "TEST-USD", "TEST/USDT")
    r = scan.analyze_tf(asset, "1h", dict(_CFG))
    assert r is not None
    assert r.schema == "accumulation"
    assert "SC" in r.sequence and "ST" in r.sequence
    assert r.context_emoji == "✅"
    assert r.verdict in ("✅ solide", "⚠️ à surveiller", "❌ douteux")
    assert r.events and any("✅" in f for c in r.events for f in c.flags)
    assert r.comment


def test_analyze_tf_rejects_flat(monkeypatch):
    df = _df(_drift(90, 100.0, seed=11))
    monkeypatch.setattr(sources, "fetch", lambda *a, **k: df.copy())
    asset = Asset("FLAT", "crypto", "FLAT-USD", "FLAT/USDT")
    assert scan.analyze_tf(asset, "1h", dict(_CFG)) is None


def test_event_check_emojis():
    th = Thresholds()
    df = add_features(_df(_accumulation_with_markdown()))
    s = detect_window_structure(df, lookback=30)
    climax = next(e for e in s.events if e.name == "SC")
    chk = scan._check_event(climax, acc=True, th=th)
    assert chk.name == "SC"
    assert any("vol ×" in f for f in chk.flags)
    assert any("✅" in f for f in chk.flags)  # climax volumique fort


def test_render_detail_contains_sections(monkeypatch):
    df = _df(_accumulation_with_markdown())
    monkeypatch.setattr(sources, "fetch", lambda *a, **k: df.copy())
    asset = Asset("TEST", "crypto", "TEST-USD", "TEST/USDT")
    rep = scan.analyze_tf(asset, "1h", dict(_CFG))
    out = scan.render_detail(rep)
    assert "Contexte" in out and "Critique" in out and "Séquence" in out


def test_resample_4h_aggregates_ohlcv():
    rows = [[10, 12, 9, 11, 100], [11, 15, 10, 14, 200],
            [14, 16, 13, 15, 150], [15, 15, 11, 12, 250],
            [12, 13, 8, 9, 300], [9, 11, 7, 10, 120],
            [10, 14, 10, 13, 130], [13, 18, 12, 17, 170]]
    out = sources.resample_ohlcv(_df(rows), "4h")
    assert len(out) == 2
    f = out.iloc[0]
    assert f["open"] == 10 and f["close"] == 12 and f["high"] == 16 and f["low"] == 9
    assert f["volume"] == 700


def test_tf_set_per_class():
    assert TF_SET_BY_CLASS["crypto"] == ("1h", "4h")
    assert TF_SET_BY_CLASS["equity"] == ("4h", "1d")
    assert TF_SET_BY_CLASS["commodity"] == ("4h", "1d")


def test_build_assets_count():
    assert len(build_assets(("crypto",))) == 46
    assert len(build_assets()) == 46 + 90 + 8
