"""
Tests synthétiques du screener multi-cours (scan.py + sources.py), hors-ligne.

Couvre : validité minimale Climax+AR+ST, vérification du contexte (markdown avant
accumulation), validation événementielle (emojis), verdict/commentaire, le rendu,
l'univers et le routage des sources.
"""
import numpy as np
import pandas as pd

from screener import scan, sources
from screener.features import add_features
from screener.universe import Asset, build_assets
from screener.wyckoff import Thresholds, detect_window_structure


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
    "limit": 400, "use_cache": False,
}


def test_has_min_sequence():
    s = detect_window_structure(add_features(_df(_accumulation_with_markdown())), lookback=30)
    assert scan.has_min_sequence(s)
    flat = detect_window_structure(add_features(_df(_drift(80, 100.0, seed=9))), lookback=30)
    assert not scan.has_min_sequence(flat)


def test_context_requires_prior_markdown():
    df = add_features(_df(_accumulation_with_markdown()))
    s = detect_window_structure(df, lookback=30)
    assert s.context_ok and s.context_move < 0       # contexte porté par la structure
    emoji, text, ok = scan._context(s)
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
        _, _, ok = scan._context(s)
        assert not ok


def test_analyze_tf_full_report(monkeypatch):
    df = _df(_accumulation_with_markdown())
    monkeypatch.setattr(sources, "fetch", lambda *a, **k: df.copy())
    asset = Asset("TEST", "crypto", "TEST/USDT", "binance")
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
    asset = Asset("FLAT", "crypto", "FLAT/USDT", "binance")
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
    from screener import report
    df = _df(_accumulation_with_markdown())
    monkeypatch.setattr(sources, "fetch", lambda *a, **k: df.copy())
    asset = Asset("TEST", "crypto", "TEST/USDT", "binance")
    rep = scan.analyze_tf(asset, "1h", dict(_CFG))
    out = report.render_detail(rep)
    assert "Contexte" in out and "Critique" in out and "Séquence" in out




def test_timeframes_uniform_24_7():
    from screener.universe import TIMEFRAMES
    assert TIMEFRAMES == ("1h", "4h")
    assert Asset("NVDA", "equity", "NVDA/USDT:USDT", "bitget").timeframes() == ("1h", "4h")
    assert Asset("BTC", "crypto", "BTC/USDT", "binance").timeframes() == ("1h", "4h")


def test_build_assets_count_and_sources():
    assert len(build_assets(("crypto",))) == 46
    assert len(build_assets(("equity",))) == 35
    assert len(build_assets(("metal",))) == 7
    assert len(build_assets(("commodity",))) == 3
    assert len(build_assets()) == 46 + 35 + 7 + 3
    crypto = build_assets(("crypto",))
    assert all(a.source == "binance" and a.symbol.endswith("/USDT") for a in crypto)
    bitget = build_assets(("equity", "metal", "commodity"))
    assert all(a.source == "bitget" and a.symbol.endswith("/USDT:USDT") for a in bitget)


def test_fetch_routes_to_asset_exchange(monkeypatch):
    calls = {}

    class FakeEx:
        def __init__(self, tag): self.tag = tag

    def fake_fetch_ohlcv(ex, symbol, timeframe, limit, use_cache):
        calls["ex"] = ex.tag
        calls["symbol"] = symbol
        return "df"

    monkeypatch.setattr(sources.data_mod, "fetch_ohlcv", fake_fetch_ohlcv)
    exchanges = {"binance": FakeEx("binance"), "bitget": FakeEx("bitget")}
    nvda = Asset("NVDA", "equity", "NVDA/USDT:USDT", "bitget")
    sources.fetch(nvda, "1h", 300, exchanges=exchanges)
    assert calls == {"ex": "bitget", "symbol": "NVDA/USDT:USDT"}


def test_oi_reading_refines_ar():
    # L'AR : rachat de shorts (OI↓) = rebond réflexe conforme ; OI↑ = vrais acheteurs.
    assert "rachat de shorts" in scan._oi_reading("AR", acc=True, d=-5)
    assert "vrais acheteurs" in scan._oi_reading("AR", acc=True, d=+5)
    # SOS sans OI nouveau = signe moins fiable.
    assert "moins fiable" in scan._oi_reading("SOS", acc=True, d=-4)
    assert "demande réelle" in scan._oi_reading("SOS", acc=True, d=+4)


def test_event_oi_deltas_and_flags():
    df = add_features(_df(_accumulation_with_markdown()))
    s = detect_window_structure(df, lookback=30)
    ordered = sorted(s.events, key=lambda e: e.bars_ago, reverse=True)
    oi = pd.Series(range(100, 100 + len(df)), index=df.index, dtype=float)  # OI croissant
    deltas = scan._event_oi_deltas(ordered, oi, "1h")
    assert deltas and all(v > 0 for v in deltas.values())   # OI croissant → ΔOI>0 partout
    chk = scan._check_event(ordered[0], acc=True, th=Thresholds(), oi_delta=5.0)
    assert chk.oi_delta == 5.0 and chk.oi_note and any("ΔOI" in f for f in chk.flags)
    # sans OI : pas de flag ΔOI ni de note
    chk2 = scan._check_event(ordered[0], acc=True, th=Thresholds(), oi_delta=None)
    assert chk2.oi_delta is None and not chk2.oi_note


def test_render_solid_table(monkeypatch):
    from screener import report
    df = _df(_accumulation_with_markdown())
    monkeypatch.setattr(sources, "fetch", lambda *a, **k: df.copy())
    monkeypatch.setattr(sources, "fetch_open_interest", lambda *a, **k: None)
    asset = Asset("TEST", "crypto", "TEST/USDT", "binance")
    rep = scan.analyze_tf(asset, "1h", dict(_CFG))
    rep.verdict = "✅ solide"   # force pour tester le rendu du tableau
    table = report.render_solid_table([rep])
    assert "Événements" in table and "TEST" in table and "SC(" in table
