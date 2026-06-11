"""
Tests synthétiques du screener multi-cours (scan.py + sources.py), hors-ligne.

Couvre : validité minimale Climax+AR+ST, vérification du contexte (markdown avant
accumulation), validation événementielle (emojis), verdict/commentaire, le rendu, le
ré-échantillonnage 4h et l'univers.
"""
import numpy as np
import pandas as pd

from screener import scan, sources
from screener.features import add_features
from screener.universe import TF_SET_BY_CLASS, Asset, build_assets
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
    from screener import report
    df = _df(_accumulation_with_markdown())
    monkeypatch.setattr(sources, "fetch", lambda *a, **k: df.copy())
    asset = Asset("TEST", "crypto", "TEST-USD", "TEST/USDT")
    rep = scan.analyze_tf(asset, "1h", dict(_CFG))
    out = report.render_detail(rep)
    assert "Contexte" in out and "Critique" in out and "Séquence" in out


def test_tf_set_per_class():
    assert TF_SET_BY_CLASS["crypto"] == ("1h", "4h")
    assert TF_SET_BY_CLASS["equity"] == ("4h", "1d")
    assert TF_SET_BY_CLASS["commodity"] == ("4h", "1d")


def test_non_us_equities_daily_only():
    # KR/JP : volume intraday Yahoo lacunaire → D1 uniquement.
    samsung = Asset("Samsung", "equity", "005930.KS")
    tokyo = Asset("Tokyo Electron", "equity", "8035.T")
    aapl = Asset("Apple", "equity", "AAPL")
    assert samsung.timeframes() == ("1d",)
    assert tokyo.timeframes() == ("1d",)
    assert aapl.timeframes() == ("4h", "1d")


def test_resample_session_aligns_on_open():
    # Séance type actions US : 7 barres 1h démarrant à 9h30 locale, sur 2 jours.
    import datetime as dt
    idx = []
    for day in (1, 2):
        start = pd.Timestamp(f"2024-07-0{day} 09:30", tz="America/New_York")
        idx += [start + pd.Timedelta(hours=h) for h in range(7)]
    rows = [[100 + i, 101 + i, 99 + i, 100.5 + i, 1000] for i in range(len(idx))]
    df = pd.DataFrame(rows, columns=["open", "high", "low", "close", "volume"],
                      index=pd.DatetimeIndex(idx))
    out = sources.resample_session_ohlcv(df, 4)
    # 2 blocs par séance : 4 barres (9h30→13h30) puis 3 barres (13h30→clôture)
    assert len(out) == 4
    first = out.iloc[0]
    assert first.name.hour == 9 and first.name.minute == 30   # aligné sur l'ouverture
    assert first["volume"] == 4000                            # 4 barres pleines
    assert out.iloc[1]["volume"] == 3000                      # fin de séance : 3 barres
    assert out.iloc[1].name.hour == 13                        # second bloc à 13h30
    # OHLC du bloc : open de la 1re barre, extrêmes du bloc, close de la dernière
    assert first["open"] == 100 and first["close"] == 103.5
    assert first["high"] == 104 and first["low"] == 99


def test_build_assets_count():
    assert len(build_assets(("crypto",))) == 46
    assert len(build_assets()) == 46 + 90 + 8


def _polygon_30m_synthetic(days=2):
    """Agrégats 30 min couvrant pre-market + séance + after-hours (index UTC)."""
    idx, rows = [], []
    i = 0
    for day in range(1, days + 1):
        # 8h00 → 19h30 ET : pre-market (3 barres), séance 9h30-16h (13), after (7)
        start = pd.Timestamp(f"2024-07-0{day} 08:00", tz="America/New_York")
        for k in range(23):
            idx.append(start + pd.Timedelta(minutes=30 * k))
            rows.append([100 + i, 101 + i, 99 + i, 100.5 + i, 500])
            i += 1
    df = pd.DataFrame(rows, columns=["open", "high", "low", "close", "volume"],
                      index=pd.DatetimeIndex(idx).tz_convert("UTC"))
    return df


def test_polygon_session_frames_filters_rth_and_aligns():
    raw = _polygon_30m_synthetic(days=2)
    h4 = sources.polygon_session_frames(raw, "4h")
    # 2 blocs par séance (9h30→13h30 : 8×30min, puis 13h30→16h : 5×30min)
    assert len(h4) == 4
    et = h4.index.tz_convert("America/New_York")
    assert {(t.hour, t.minute) for t in et} == {(9, 30), (13, 30)}
    assert h4["volume"].iloc[0] == 8 * 500      # bloc plein, sans pre-market
    assert h4["volume"].iloc[1] == 5 * 500      # fin de séance
    d1 = sources.polygon_session_frames(raw, "1d")
    assert len(d1) == 2 and d1["volume"].iloc[0] == 13 * 500  # séance entière
    h1 = sources.polygon_session_frames(raw, "1h")
    assert len(h1) == 14                        # 7 blocs par séance


def test_rescale_intraday_volume_matches_daily():
    # 2 séances de 7 barres 1h ; Yahoo intraday sous-estime (Σ=7000 vs daily consolidé).
    idx, rows = [], []
    for day in (1, 2):
        start = pd.Timestamp(f"2024-07-0{day} 09:30", tz="America/New_York")
        for h in range(7):
            idx.append(start + pd.Timedelta(hours=h))
            rows.append([100, 101, 99, 100.5, 1000])
    intra = pd.DataFrame(rows, columns=["open", "high", "low", "close", "volume"],
                         index=pd.DatetimeIndex(idx))
    daily = pd.DataFrame(
        {"open": [100, 100], "high": [101, 101], "low": [99, 99],
         "close": [100.5, 100.5], "volume": [14000.0, 7000.0]},  # jour 1 : il manque 50 %
        index=pd.DatetimeIndex([pd.Timestamp(f"2024-07-0{d} 00:00", tz="America/New_York")
                                for d in (1, 2)]))
    out = sources.rescale_intraday_volume(intra, daily)
    sums = out["volume"].groupby(pd.Index(out.index.date)).sum()
    assert float(sums.iloc[0]) == 14000.0   # recalé sur le consolidé
    assert float(sums.iloc[1]) == 7000.0    # facteur 1 → inchangé
    # le profil intra-journalier reste uniforme (facteur appliqué à toutes les barres)
    assert float(out["volume"].iloc[0]) == 2000.0


def test_rescale_guard_against_aberrant_factor():
    # Intraday quasi vide (cas crypto Yahoo troué) : facteur > 5 → pas de correction.
    idx = pd.DatetimeIndex([pd.Timestamp("2024-07-01 09:30", tz="America/New_York")])
    intra = pd.DataFrame([[100, 101, 99, 100.5, 10]],
                         columns=["open", "high", "low", "close", "volume"], index=idx)
    daily = pd.DataFrame({"open": [100], "high": [101], "low": [99],
                          "close": [100.5], "volume": [1_000_000.0]},
                         index=pd.DatetimeIndex([pd.Timestamp("2024-07-01", tz="America/New_York")]))
    out = sources.rescale_intraday_volume(intra, daily)
    assert float(out["volume"].iloc[0]) == 10.0  # inchangé


def test_source_routing_polygon(monkeypatch):
    aapl = Asset("Apple", "equity", "AAPL")
    samsung = Asset("Samsung", "equity", "005930.KS")
    gold = Asset("Gold", "commodity", "GC=F")
    monkeypatch.setattr(sources, "polygon_key", lambda: "fake-key")
    assert sources.source_for(aapl, "ccxt") == "polygon"
    assert sources.source_for(samsung, "ccxt") == "yahoo"   # non-US → Yahoo
    assert sources.source_for(gold, "ccxt") == "yahoo"      # futures → Yahoo
    monkeypatch.setattr(sources, "polygon_key", lambda: "")
    assert sources.source_for(aapl, "ccxt") == "yahoo"      # sans clé → repli
