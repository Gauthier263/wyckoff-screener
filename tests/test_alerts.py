"""Test du moteur de déclenchement d'alertes (check_trigger, check_weakness), hors-ligne."""
import numpy as np
import pandas as pd

from screener.alerts import check_trigger, check_weakness

LEVELS = {"tp1": 64800, "tp2": 65500, "stop": 63184, "resist": 64500, "profit_floor": 63800}


def _bar(high, close, vr=1.0, clv=0.5):
    return {"high": high, "close": close, "vol_ratio": vr, "clv": clv}


def test_tp2_priority_over_tp1():
    t, msg = check_trigger(_bar(65600, 65550), np.nan, LEVELS)
    assert t == "TP2" and "65,500" in msg


def test_tp1_hit():
    t, _ = check_trigger(_bar(64850, 64820), 1.2, LEVELS)
    assert t == "TP1"


def test_exhaustion_high_vol_poor_close_above_resist():
    # close au-dessus de resist, volume fort, clôture faible -> Buying Climax/UTAD
    t, msg = check_trigger(_bar(64790, 64600, vr=2.8, clv=0.3), 1.0, LEVELS)
    assert t == "EXH" and "vol×2.8" in msg


def test_no_exhaustion_if_volume_normal():
    assert check_trigger(_bar(64790, 64600, vr=1.5, clv=0.3), 1.0, LEVELS) is None


def test_stop_break():
    t, _ = check_trigger(_bar(63200, 63100, clv=0.4), -0.5, LEVELS)
    assert t == "STOP"


def test_no_trigger_midrange():
    assert check_trigger(_bar(64000, 63950), 0.1, LEVELS) is None


def test_oi_shown_when_available():
    _, msg = check_trigger(_bar(64850, 64820), 2.3, LEVELS)
    assert "+2.3%" in msg


# ── Signaux de faiblesse précoce (check_weakness) ──────────────────────────────
def _df(rows):
    """rows: list de (open, high, low, close, vol_ratio, clv)."""
    idx = pd.date_range("2026-06-20", periods=len(rows), freq="15min", tz="UTC")
    return pd.DataFrame(rows, columns=["open", "high", "low", "close", "vol_ratio", "clv"], index=idx)


def _flat(n, price=64000):
    return [(price, price + 20, price - 20, price, 0.8, 0.5) for _ in range(n)]


def test_weakness_supply_bar():
    # avant-dernière barre = barre de vente volumique à clôture basse, en profit
    rows = _flat(13) + [(64200, 64250, 63900, 63950, 2.4, 0.15), (63950, 64000, 63900, 63960, 0.5, 0.5)]
    t, msg = check_weakness(_df(rows), None, LEVELS)
    assert t == "SUPPLY" and "vol×2.4" in msg


def test_no_supply_when_below_profit_floor():
    rows = _flat(13, price=63000) + [(63000, 63050, 62700, 62750, 2.5, 0.1), (62750, 62800, 62700, 62760, 0.5, 0.5)]
    assert check_weakness(_df(rows), None, LEVELS) is None     # sous profit_floor → ignoré


def test_weakness_oi_divergence_near_high():
    # prix proche du plus-haut récent, mais OI en baisse sur ~1h30 → DIVERG
    rows = _flat(13, price=64200) + [(64200, 64300, 64150, 64290, 0.9, 0.8), (64290, 64300, 64250, 64295, 0.7, 0.7)]
    df = _df(rows)
    oi = pd.Series(np.linspace(6.40e9, 6.10e9, len(df)), index=df.index)   # OI qui décline nettement
    t, msg = check_weakness(df, oi, LEVELS)
    assert t == "DIVERG" and "OI en baisse" in msg


def test_no_divergence_when_oi_rising():
    rows = _flat(13, price=64200) + [(64200, 64300, 64150, 64290, 0.9, 0.8), (64290, 64300, 64250, 64295, 0.7, 0.7)]
    df = _df(rows)
    oi = pd.Series(np.linspace(6.18e9, 6.30e9, len(df)), index=df.index)   # OI qui monte
    assert check_weakness(df, oi, LEVELS) is None


def test_weakness_none_without_profit_floor():
    rows = _flat(13) + [(64200, 64250, 63900, 63950, 2.4, 0.15), (63950, 64000, 63900, 63960, 0.5, 0.5)]
    assert check_weakness(_df(rows), None, {"tp1": 1, "tp2": 2, "stop": 0, "resist": 1}) is None


# ── Scan de fenêtre (catch-up robuste aux trous de cron) ───────────────────────
from screener.alerts import scan_window


def _closed(rows):
    idx = pd.date_range("2026-06-22 00:00", periods=len(rows), freq="15min", tz="UTC")
    return pd.DataFrame(rows, columns=["open", "high", "low", "close", "vol_ratio", "clv"], index=idx)


def test_scan_catches_tp1_in_earlier_bar():
    # TP1 touché à l'avant-dernière barre (pas la dernière) → doit être rattrapé
    rows = _flat(3) + [(64000, 64850, 63990, 64820, 1.2, 0.7), (64820, 64300, 64200, 64250, 0.6, 0.5)]
    closed = _closed(rows)
    res = scan_window(closed, None, LEVELS, since_ts=closed.index[0] - pd.Timedelta(minutes=1))
    assert res is not None and res[0] == "TP1"
    assert res[2] == closed.index[3]                      # la barre qui a touché 64 800


def test_cold_start_only_last_bar_no_retro_spam():
    # démarrage à froid (since=None) : un TP touché plus tôt n'est PAS re-notifié
    rows = _flat(3) + [(64000, 64850, 63990, 64820, 1.2, 0.7), (64820, 64300, 64200, 64250, 0.6, 0.5)]
    assert scan_window(_closed(rows), None, LEVELS, since_ts=None) is None


def test_already_evaluated_bars_skipped():
    rows = _flat(3) + [(64000, 64850, 63990, 64820, 1.2, 0.7), (64820, 64300, 64200, 64250, 0.6, 0.5)]
    closed = _closed(rows)
    # since = la barre du TP → on ne rescanne que la suivante (normale) → rien
    assert scan_window(closed, None, LEVELS, since_ts=closed.index[3]) is None


def test_scan_catches_stop_break():
    rows = _flat(3) + [(63300, 63350, 63100, 63150, 1.0, 0.3), (63150, 63300, 63100, 63200, 0.6, 0.5)]
    closed = _closed(rows)
    res = scan_window(closed, None, LEVELS, since_ts=closed.index[0] - pd.Timedelta(minutes=1))
    assert res is not None and res[0] == "STOP"


def test_scan_empty_window_returns_none():
    assert scan_window(None, None, LEVELS) is None
    closed = _closed(_flat(5))
    # since_ts après la dernière barre → rien de nouveau à évaluer
    assert scan_window(closed, None, LEVELS, since_ts=closed.index[-1]) is None


def test_scan_exhaustion_on_last_bar():
    # dernière barre clôturée : vol fort + clôture faible au-dessus de resist → EXH
    rows = _flat(4) + [(64550, 64790, 64500, 64600, 2.8, 0.2)]
    closed = _closed(rows)
    res = scan_window(closed, None, LEVELS, since_ts=closed.index[0])
    assert res is not None and res[0] == "EXH" and res[2] == closed.index[-1]


def test_scan_weakness_supply_via_window():
    # pas de TP/stop/EXH, mais barre de vente volumique en profit → SUPPLY remonte
    rows = _flat(13) + [(64200, 64250, 63900, 63950, 2.4, 0.15), (63950, 64000, 63900, 63960, 0.5, 0.5)]
    closed = _closed(rows)
    res = scan_window(closed, None, LEVELS, since_ts=closed.index[0])
    assert res is not None and res[0] == "SUPPLY"


# ── ΔOI aligné (_oi_chg_at) ─────────────────────────────────────────────────────
from screener.alerts import _oi_chg_at


def test_oi_chg_at():
    idx = pd.date_range("2026-06-22", periods=6, freq="15min", tz="UTC")
    oi = pd.Series([100.0, 100, 100, 100, 100, 102.0], index=idx)
    assert abs(_oi_chg_at(oi, idx, idx[-1], bars_back=2) - 2.0) < 1e-9
    assert np.isnan(_oi_chg_at(None, idx, idx[-1]))                    # pas d'OI
    assert np.isnan(_oi_chg_at(oi, idx, idx[1], bars_back=2))          # pas assez d'historique
    assert np.isnan(_oi_chg_at(oi, idx, pd.Timestamp("2030-01-01", tz="UTC")))  # ts hors index


# ── État persistant + run_once (dédup, cooldown) ───────────────────────────────
from screener import alerts as alerts_mod
from screener.alerts import _load_state, _save_state, run_once


def test_state_roundtrip(tmp_path):
    p = str(tmp_path / "state.json")
    _save_state(p, {"evaluated_until": "2026-06-22T10:00:00+00:00"})
    assert _load_state(p) == {"evaluated_until": "2026-06-22T10:00:00+00:00"}


def test_state_missing_or_corrupt_returns_empty(tmp_path):
    assert _load_state(str(tmp_path / "absent.json")) == {}
    bad = tmp_path / "bad.json"
    bad.write_text("{pas du json")
    assert _load_state(str(bad)) == {}


def _patch_notify(monkeypatch):
    sent = []
    monkeypatch.setattr(alerts_mod, "_notify", lambda msg: sent.append(msg))
    return sent


def test_run_once_sends_and_records_state(tmp_path, monkeypatch):
    sent = _patch_notify(monkeypatch)
    ts = pd.Timestamp("2026-06-22 10:00", tz="UTC")
    monkeypatch.setattr(alerts_mod, "evaluate",
                        lambda s, tf, lv, since: (ts, "TP1", "msg TP1"))
    p = str(tmp_path / "state.json")
    assert run_once("BTC/USDT", "15m", LEVELS, p) is True
    assert sent == ["msg TP1"]
    assert _load_state(p)["evaluated_until"] == ts.isoformat()


def test_run_once_passes_since_ts_from_state(tmp_path, monkeypatch):
    _patch_notify(monkeypatch)
    seen = {}
    ts = pd.Timestamp("2026-06-22 10:15", tz="UTC")

    def fake_eval(s, tf, lv, since):
        seen["since"] = since
        return (ts, None, None)

    monkeypatch.setattr(alerts_mod, "evaluate", fake_eval)
    p = str(tmp_path / "state.json")
    _save_state(p, {"evaluated_until": "2026-06-22T10:00:00+00:00"})
    assert run_once("BTC/USDT", "15m", LEVELS, p) is False       # rien déclenché
    assert seen["since"] == pd.Timestamp("2026-06-22 10:00", tz="UTC")


def test_run_once_weakness_cooldown_2h(tmp_path, monkeypatch):
    sent = _patch_notify(monkeypatch)
    p = str(tmp_path / "state.json")
    t0 = pd.Timestamp("2026-06-22 10:00", tz="UTC")

    def eval_at(ts):
        return lambda s, tf, lv, since: (ts, "SUPPLY", f"faiblesse @ {ts}")

    monkeypatch.setattr(alerts_mod, "evaluate", eval_at(t0))
    assert run_once("BTC/USDT", "15m", LEVELS, p) is True        # 1re faiblesse : envoyée
    monkeypatch.setattr(alerts_mod, "evaluate", eval_at(t0 + pd.Timedelta(minutes=30)))
    assert run_once("BTC/USDT", "15m", LEVELS, p) is False       # < 2h : silencieux
    monkeypatch.setattr(alerts_mod, "evaluate", eval_at(t0 + pd.Timedelta(hours=3)))
    assert run_once("BTC/USDT", "15m", LEVELS, p) is True        # > 2h : ré-armé
    assert len(sent) == 2


def test_run_once_tp_not_subject_to_cooldown(tmp_path, monkeypatch):
    sent = _patch_notify(monkeypatch)
    p = str(tmp_path / "state.json")
    t0 = pd.Timestamp("2026-06-22 10:00", tz="UTC")
    monkeypatch.setattr(alerts_mod, "evaluate",
                        lambda s, tf, lv, since: (t0, "TP1", "tp"))
    assert run_once("BTC/USDT", "15m", LEVELS, p) is True
    monkeypatch.setattr(alerts_mod, "evaluate",
                        lambda s, tf, lv, since: (t0 + pd.Timedelta(minutes=15), "TP2", "tp2"))
    assert run_once("BTC/USDT", "15m", LEVELS, p) is True        # pas de cooldown sur les TP
    assert sent == ["tp", "tp2"]


def test_run_once_evaluate_none_returns_false(tmp_path, monkeypatch):
    _patch_notify(monkeypatch)
    monkeypatch.setattr(alerts_mod, "evaluate", lambda s, tf, lv, since: None)
    assert run_once("BTC/USDT", "15m", LEVELS, str(tmp_path / "s.json")) is False


# ── evaluate : glue données→scan (fetchers monkeypatchés, hors-ligne) ──────────
def test_evaluate_formats_cest_and_excludes_forming_bar(monkeypatch):
    from screener import data as data_mod
    # 20 barres plates puis TP1 touché à l'avant-dernière ; la DERNIÈRE est en formation
    idx = pd.date_range("2026-06-22 10:00", periods=22, freq="15min", tz="UTC")
    rows = [[64000, 64020, 63980, 64000, 1000]] * 20 \
        + [[64000, 64850, 63990, 64820, 1200]] \
        + [[64820, 64830, 64800, 64810, 100]]          # en formation → doit être exclue
    ohlcv = pd.DataFrame(rows, columns=["open", "high", "low", "close", "volume"], index=idx)

    monkeypatch.setattr(data_mod, "get_exchange", lambda name: object())
    monkeypatch.setattr(data_mod, "fetch_ohlcv",
                        lambda ex, s, tf, limit, use_cache: ohlcv.copy())
    monkeypatch.setattr(data_mod, "fetch_open_interest",
                        lambda s, tf, limit, source: None)

    out = alerts_mod.evaluate("BTC/USDT", "15m", LEVELS, since_ts=idx[0])
    assert out is not None
    last_ts, typ, msg = out
    assert last_ts == idx[-2]                          # dernière barre CLÔTURÉE
    assert typ == "TP1"
    # la barre TP1 (15:00 UTC) doit être horodatée 17h00 CEST dans le message
    assert "17h00 CEST" in msg and "BTC/USDT" in msg


def test_evaluate_no_trigger_returns_ts_only(monkeypatch):
    from screener import data as data_mod
    idx = pd.date_range("2026-06-22 10:00", periods=22, freq="15min", tz="UTC")
    ohlcv = pd.DataFrame([[64000, 64020, 63980, 64000, 1000]] * 22,
                         columns=["open", "high", "low", "close", "volume"], index=idx)
    monkeypatch.setattr(data_mod, "get_exchange", lambda name: object())
    monkeypatch.setattr(data_mod, "fetch_ohlcv",
                        lambda ex, s, tf, limit, use_cache: ohlcv.copy())
    monkeypatch.setattr(data_mod, "fetch_open_interest",
                        lambda s, tf, limit, source: None)
    out = alerts_mod.evaluate("BTC/USDT", "15m", LEVELS, since_ts=idx[0])
    assert out == (idx[-2], None, None)


# ── _notify : repli stdout sans secrets Telegram ───────────────────────────────
def test_notify_stdout_without_secrets(monkeypatch, capsys):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    alerts_mod._notify("hello")
    assert "hello" in capsys.readouterr().out


def test_notify_telegram_with_secrets(monkeypatch):
    calls = []
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "tok")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "42")
    monkeypatch.setattr(alerts_mod, "send_telegram",
                        lambda token, chat, text: calls.append((token, chat, text)) or True)
    alerts_mod._notify("ping")
    assert calls == [("tok", "42", "ping")]


# ── main : parsing CLI (mode cron --once implicite) ────────────────────────────
def test_main_once_passes_levels(tmp_path, monkeypatch, capsys):
    seen = {}

    def fake_run_once(symbol, timeframe, levels, state_path):
        seen.update(symbol=symbol, timeframe=timeframe, levels=levels)
        return True

    monkeypatch.setattr(alerts_mod, "run_once", fake_run_once)
    alerts_mod.main(["--symbol", "BTC/USDT", "--timeframe", "15m",
                     "--tp1", "64800", "--tp2", "65500", "--stop", "63184",
                     "--resist", "64500", "--profit-floor", "63800",
                     "--state", str(tmp_path / "s.json")])
    assert seen["levels"] == LEVELS
    assert "alerte envoyée" in capsys.readouterr().out
