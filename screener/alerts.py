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


WEAKNESS_TYPES = ("SUPPLY", "DIVERG")   # signaux de faiblesse (cooldown anti-spam)


def check_weakness(df, oi_aligned, levels: dict) -> "tuple[str, str] | None":
    """Signaux de **faiblesse précoce** (retournement possible) quand le long est déjà en
    profit (close > `profit_floor`). Évite d'alerter dans la base. Fonction testable.

    SUPPLY : barre de vente volumique à clôture basse (l'offre entre).
    DIVERG : prix proche du plus-haut récent mais OI en repli sur ~1h30 (hausse portée par
    du short-covering, pas de demande neuve). Retourne (type, message) ou None.
    """
    pf = levels.get("profit_floor")
    if pf is None or len(df) < 14:
        return None
    bar = df.iloc[-2]
    c, o = float(bar["close"]), float(bar["open"])
    if c < pf:                                             # encore dans la base : non pertinent
        return None
    vr, clv = float(bar["vol_ratio"]), float(bar["clv"])
    if c < o and vr >= 2.0 and clv < 0.25:
        return "SUPPLY", (f"⚠️ Faiblesse — barre de vente vol×{vr:.1f} clôture basse (clv {clv:.2f}) à "
                          f"{c:,.0f} = l'offre entre. Retournement possible → envisage un TP partiel précoce.")
    recent_high = float(df["high"].iloc[-14:-2].max())
    if oi_aligned is not None and len(oi_aligned) >= 8 and c >= recent_high * 0.996:
        oi6 = (float(oi_aligned.iloc[-2]) / float(oi_aligned.iloc[-8]) - 1) * 100
        if oi6 <= -1.2:
            return "DIVERG", (f"⚠️ Divergence — prix proche du plus-haut ({c:,.0f}) mais OI en baisse "
                              f"({oi6:+.1f}% sur ~1h30) = hausse portée par du short-covering, pas de demande "
                              f"neuve. Retournement possible → TP partiel à considérer.")
    return None


def evaluate(symbol: str, timeframe: str, levels: dict) -> "tuple[str, str, str] | None":
    """Récupère la dernière bougie close + OI, applique `check_trigger` puis `check_weakness`.
    Retourne (clé_dédup, type, message) ou None."""
    ex = data_mod.get_exchange("binance")
    df = add_features(data_mod.fetch_ohlcv(ex, symbol, timeframe, limit=60, use_cache=False))
    oi = data_mod.fetch_open_interest(symbol, timeframe, limit=60, source="binance")
    oi_aligned = oi["oi"].reindex(df.index, method="nearest") if oi is not None else None
    oi_chg = ((oi_aligned.iloc[-2] / oi_aligned.iloc[-4] - 1) * 100
              if (oi_aligned is not None and len(oi_aligned) >= 4) else float("nan"))
    bar, ts = df.iloc[-2], df.index[-2]                    # dernière bougie CLÔTURÉE
    res = check_trigger(bar, oi_chg, levels) or check_weakness(df, oi_aligned, levels)
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
    key, typ, msg = out
    state = _load_state(state_path)
    if typ in WEAKNESS_TYPES:                              # faiblesse : cooldown 2h (anti-spam)
        ts_iso = key.split("|")[0]
        last_weak = state.get("last_weak")
        if last_weak is not None:
            try:
                if (pd.Timestamp(ts_iso) - pd.Timestamp(last_weak)) < pd.Timedelta(hours=2):
                    return False
            except Exception:
                pass
        state["last_weak"] = ts_iso
    else:                                                  # TP/stop/épuisement : 1 par bougie
        if state.get("last") == key:
            return False
        state["last"] = key
    token, chat = os.environ.get("TELEGRAM_BOT_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID")
    if token and chat:
        send_telegram(token, chat, msg)
    else:
        print(msg)                                         # repli : stdout (logs CI)
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
    p.add_argument("--profit-floor", type=float, default=None, dest="profit_floor",
                   help="au-dessus de ce prix, guette aussi les signaux de faiblesse précoce (SUPPLY/DIVERG)")
    p.add_argument("--state", default=".cache/alerts_state.json")
    p.add_argument("--loop", action="store_true", help="boucle locale (sinon: un seul cycle, pour cron)")
    p.add_argument("--interval", type=int, default=300)
    a = p.parse_args(argv)
    levels = {"tp1": a.tp1, "tp2": a.tp2, "stop": a.stop, "resist": a.resist, "profit_floor": a.profit_floor}
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
