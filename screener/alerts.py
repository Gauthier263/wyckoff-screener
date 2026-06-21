"""
alerts.py — Lanceur d'alertes durable (téléphone via Telegram), indépendant de toute
session interactive. Conçu pour tourner en **cron GitHub Actions** (mode `--once`) ou en
boucle locale (`--loop`). Poll OHLCV Binance + OI Binance (Coinalyze) → déclencheurs
take-profit / stop / épuisement → push Telegram.

Secrets (env) : COINALYZE_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID.
Dédup : un petit fichier d'état JSON (caché entre runs en CI) évite de re-notifier la
même bougie. Heuristiques transparentes, niveaux passés en arguments (jamais en dur).
"""
from __future__ import annotations

import argparse
import json
import os
import time

import pandas as pd

from . import data as data_mod
from .features import add_features


def check_trigger(bar, oi_chg: float, levels: dict) -> "tuple[str, str] | None":
    """Évalue les déclencheurs sur une bougie CLÔTURÉE. Fonction pure (testable hors-ligne).

    `levels` : {tp1, tp2, stop, resist}. Retourne (type, message) ou None. Priorité :
    TP2 > TP1 > épuisement (Buying Climax/UTAD) > stop. `oi_chg` = ΔOI % récent (peut être nan).
    """
    h, c = float(bar["high"]), float(bar["close"])
    vr, clv = float(bar["vol_ratio"]), float(bar["clv"])
    oi_txt = "n/d" if pd.isna(oi_chg) else f"{oi_chg:+.1f}%"
    if h >= levels["tp2"]:
        return "TP2", (f"🎯 TP2 {levels['tp2']:,.0f} atteint — high {h:,.0f}, close {c:,.0f}, "
                       f"OI Δ {oi_txt}. Sors le 2e tiers, garde un runner stop suiveur.")
    if h >= levels["tp1"]:
        return "TP1", (f"🎯 TP1 {levels['tp1']:,.0f} atteint — high {h:,.0f}, close {c:,.0f}, "
                       f"OI Δ {oi_txt}. Zone d'offre : sors ⅓ à ½, stop à breakeven.")
    if c > levels["resist"] and vr >= levels.get("exh_vol", 2.5) and clv < levels.get("exh_clv", 0.4):
        return "EXH", (f"⚠️ Épuisement — bougie vol×{vr:.1f} clôture faible (clv {clv:.2f}) à {c:,.0f}, "
                       f"OI Δ {oi_txt}. Possible Buying Climax/UTAD → envisage de solder.")
    if c < levels["stop"]:
        return "STOP", (f"🛑 Stop {levels['stop']:,.0f} cassé — close {c:,.0f}, OI Δ {oi_txt}. "
                        f"Sécurise le gain.")
    return None


def send_telegram(token: str, chat_id: str, text: str) -> bool:
    """Envoie un message Telegram. True si OK. Tolérant : False sans lever."""
    try:
        import requests

        r = requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                          json={"chat_id": chat_id, "text": text}, timeout=20)
        return r.status_code == 200
    except Exception:
        return False


def _oi_chg(symbol: str, timeframe: str, index, bars_back: int = 2) -> float:
    """ΔOI % (Binance/Coinalyze) sur ~`bars_back` bougies, aligné sur les barres de prix."""
    try:
        oi = data_mod.fetch_open_interest(symbol, timeframe, limit=60, source="binance")
        if oi is None:
            return float("nan")
        s = oi["oi"].reindex(index, method="nearest")
        if len(s) <= bars_back:
            return float("nan")
        return (s.iloc[-2] / s.iloc[-2 - bars_back] - 1) * 100
    except Exception:
        return float("nan")


def evaluate(symbol: str, timeframe: str, levels: dict) -> "tuple[str, str, str] | None":
    """Récupère la dernière bougie close + OI, applique `check_trigger`.
    Retourne (clé_dédup, type, message) ou None."""
    ex = data_mod.get_exchange("binance")
    df = add_features(data_mod.fetch_ohlcv(ex, symbol, timeframe, limit=60, use_cache=False))
    bar, ts = df.iloc[-2], df.index[-2]                    # dernière bougie CLÔTURÉE
    res = check_trigger(bar, _oi_chg(symbol, timeframe, df.index), levels)
    if res is None:
        return None
    typ, msg = res
    cest = (ts + pd.Timedelta(hours=2)).strftime("%d/%m %Hh%M")
    return f"{ts.isoformat()}|{typ}", typ, f"{symbol} {timeframe} @ {cest} CEST\n{msg}\n[aide à la décision, pas un ordre]"


def _load_state(path: str) -> dict:
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return {}


def _save_state(path: str, state: dict) -> None:
    try:
        with open(path, "w") as f:
            json.dump(state, f)
    except Exception:
        pass


def run_once(symbol: str, timeframe: str, levels: dict, state_path: str) -> bool:
    """Un seul cycle (pour cron). True si une alerte a été envoyée."""
    out = evaluate(symbol, timeframe, levels)
    if out is None:
        return False
    key, _typ, msg = out
    state = _load_state(state_path)
    if state.get("last") == key:                           # déjà notifié cette bougie
        return False
    token, chat = os.environ.get("TELEGRAM_BOT_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID")
    if token and chat:
        send_telegram(token, chat, msg)
    else:
        print(msg)                                         # repli : stdout (logs CI)
    state["last"] = key
    _save_state(state_path, state)
    return True


def main(argv=None):
    p = argparse.ArgumentParser(description="Lanceur d'alertes BTC (Telegram, cron-friendly)")
    p.add_argument("--symbol", default="BTC/USDT")
    p.add_argument("--timeframe", default="15m")
    p.add_argument("--tp1", type=float, required=True)
    p.add_argument("--tp2", type=float, required=True)
    p.add_argument("--stop", type=float, required=True)
    p.add_argument("--resist", type=float, required=True, help="seuil prix au-dessus duquel guetter l'épuisement")
    p.add_argument("--state", default=".cache/alerts_state.json")
    p.add_argument("--loop", action="store_true", help="boucle locale (sinon: un seul cycle, pour cron)")
    p.add_argument("--interval", type=int, default=300)
    a = p.parse_args(argv)
    levels = {"tp1": a.tp1, "tp2": a.tp2, "stop": a.stop, "resist": a.resist}
    os.makedirs(os.path.dirname(a.state) or ".", exist_ok=True)
    if not a.loop:
        sent = run_once(a.symbol, a.timeframe, levels, a.state)
        print("alerte envoyée" if sent else "pas de déclencheur")
        return
    while True:
        try:
            run_once(a.symbol, a.timeframe, levels, a.state)
        except Exception as e:
            print(f"[transitoire] {e}")
        time.sleep(a.interval)


if __name__ == "__main__":
    main()
