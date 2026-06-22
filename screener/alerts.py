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


def _oi_chg_at(oi_aligned, index, ts, bars_back: int = 2) -> float:
    """ΔOI % (coin) sur ~`bars_back` barres jusqu'à `ts`. nan si indispo."""
    if oi_aligned is None:
        return float("nan")
    try:
        i = index.get_loc(ts)
        return (oi_aligned.iloc[i] / oi_aligned.iloc[i - bars_back] - 1) * 100 if i >= bars_back else float("nan")
    except Exception:
        return float("nan")


def scan_window(closed, oi_aligned, levels: dict, since_ts=None) -> "tuple[str, str, object] | None":
    """Scanne les bougies CLÔTURÉES postérieures à `since_ts` (catch-up robuste aux trous de
    cron) et retourne le premier déclencheur (type, message, ts), ou None. Pure/testable.

    Priorité : TP2/TP1 (via le **plus-haut** de la fenêtre — un TP touché plusieurs barres
    plus tôt est rattrapé) > stop (close < stop) > épuisement/faiblesse (sur la dernière barre).
    `since_ts=None` (démarrage à froid) → on n'évalue que la dernière close (pas de spam
    rétroactif). `closed` doit exclure la barre en formation.
    """
    if closed is None or len(closed) == 0:
        return None
    scan = closed.iloc[-1:] if since_ts is None else closed[closed.index > since_ts]
    if len(scan) == 0:
        return None
    # TP : on prend la barre qui a touché (plus-haut de la fenêtre)
    if float(scan["high"].max()) >= levels["tp1"]:
        cand = scan[scan["high"] >= levels["tp1"]].iloc[0]
        res = check_trigger(cand, _oi_chg_at(oi_aligned, closed.index, cand.name), levels)
        if res is not None:                                 # TP2 ou TP1 selon le high
            return (res[0], res[1], cand.name)
    # Stop : première clôture sous le stop
    if (scan["close"] < levels["stop"]).any():
        cand = scan[scan["close"] < levels["stop"]].iloc[0]
        res = check_trigger(cand, _oi_chg_at(oi_aligned, closed.index, cand.name), levels)
        if res is not None:
            return (res[0], res[1], cand.name)
    # Épuisement / faiblesse : sur la dernière barre clôturée
    last = closed.iloc[-1]
    res = check_trigger(last, _oi_chg_at(oi_aligned, closed.index, last.name), levels)
    if res is not None and res[0] == "EXH":
        return (res[0], res[1], last.name)
    w = check_weakness(closed, oi_aligned, levels)
    if w is not None:
        return (w[0], w[1], closed.index[-1])
    return None


def evaluate(symbol: str, timeframe: str, levels: dict, since_ts=None):
    """Récupère les bougies + OI (coin) et applique `scan_window`. Retourne
    (dernière_ts_clôturée, type|None, message|None)."""
    ex = data_mod.get_exchange("binance")
    df = add_features(data_mod.fetch_ohlcv(ex, symbol, timeframe, limit=60, use_cache=False))
    if len(df) < 3:
        return None
    oi = data_mod.fetch_open_interest(symbol, timeframe, limit=60, source="binance")
    oi_aligned = oi["oi"].reindex(df.index, method="nearest") if oi is not None else None
    closed = df.iloc[:-1]                                   # exclut la barre en formation
    last_ts = closed.index[-1]
    res = scan_window(closed, oi_aligned, levels, since_ts)
    if res is None:
        return (last_ts, None, None)
    typ, m, ts = res
    cest = (ts + pd.Timedelta(hours=2)).strftime("%d/%m %Hh%M")
    return (last_ts, typ, f"{symbol} {timeframe} @ {cest} CEST\n{m}\n[aide à la décision, pas un ordre]")


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


def _notify(msg: str) -> None:
    """Envoie sur Telegram si les secrets sont présents, sinon stdout (logs CI / local)."""
    token, chat = os.environ.get("TELEGRAM_BOT_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID")
    if token and chat:
        send_telegram(token, chat, msg)
    else:
        print(msg)


def run_test(symbol: str, timeframe: str) -> None:
    """Envoie un message de **test** Telegram (vérifie le bout-en-bout données+notif par actif)."""
    try:
        ex = data_mod.get_exchange("binance")
        c = float(data_mod.fetch_ohlcv(ex, symbol, timeframe, limit=3, use_cache=False)["close"].iloc[-1])
        price = f" (dernier prix {c:,.2f})"
    except Exception:
        price = ""
    _notify(f"✅ Test alerte {symbol} — système opérationnel{price}. [test, à ignorer]")


def run_once(symbol: str, timeframe: str, levels: dict, state_path: str) -> bool:
    """Un seul cycle (pour cron). Scanne toutes les barres depuis le dernier check (catch-up
    robuste aux trous de cron) et notifie au plus un déclencheur. True si une alerte est envoyée."""
    state = _load_state(state_path)
    since = state.get("evaluated_until")
    since_ts = None
    if since:
        try:
            since_ts = pd.Timestamp(since)
        except Exception:
            since_ts = None
    out = evaluate(symbol, timeframe, levels, since_ts)
    if out is None:
        return False
    last_ts, typ, msg = out
    state["evaluated_until"] = last_ts.isoformat()         # ces barres sont désormais évaluées
    sent = False
    if typ is not None and msg is not None:
        if typ in WEAKNESS_TYPES:                          # faiblesse : cooldown 2h (anti-spam)
            lw = state.get("last_weak")
            cool = False
            if lw:
                try:
                    cool = (last_ts - pd.Timestamp(lw)) < pd.Timedelta(hours=2)
                except Exception:
                    cool = False
            if not cool:
                _notify(msg); state["last_weak"] = last_ts.isoformat(); sent = True
        else:
            _notify(msg); sent = True
    _save_state(state_path, state)
    return sent


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
    p.add_argument("--test", action="store_true", help="envoie un message de test Telegram puis sort")
    a = p.parse_args(argv)
    if a.test:
        run_test(a.symbol, a.timeframe)
        return
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
