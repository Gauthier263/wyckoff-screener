"""
monitor.py — Suivi d'un cours à intervalle régulier et détection de l'émergence
d'une accumulation / distribution, avec alerte au déclencheur.

Cas d'usage : tu *anticipes* un retournement (haussier → accumulation, baissier →
distribution) sur un symbole et une TF. Ce module suit le cours barre après barre,
reconnaît le schéma Wyckoff *en train de se former* et t'alerte quand le déclencheur
d'entrée tombe (force significative côté accumulation, faiblesse côté distribution).

Il ne réinvente rien : il orchestre les briques existantes —
  - `window.detect_window_structure` : progression de la séquence (climax→AR→ST→signe) ;
  - `events.detect_events`            : signaux frais sur les dernières barres ;
  - `score.score_symbol`              : biais dominant + phase (B/C/D).

Trois états par instantané :
  NONE   — rien d'exploitable (ou schéma contraire à ce que tu anticipes) ;
  WATCH  — le schéma attendu se construit (climax / AR / test présents) ;
  ALERT  — un déclencheur frais (bars_ago==0) conforme au biais attendu vient de tomber.

Deux modes de lancement (même cœur `monitor_once`) :
  run_watch — boucle bloquante, poll aligné sur la clôture de barre (écran ouvert) ;
  run_once  — un seul poll, état persisté sur disque pour dédup (cron / terminal fermé).

Aide à la décision discrétionnaire — jamais d'exécution d'ordre automatique.
"""
from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone

import pandas as pd

from . import data as data_mod
from . import notify
from .events import Event, Thresholds, detect_events
from .features import add_features, detect_trading_range
from .window import WindowStructure, detect_window_structure

# Déclencheurs d'entrée par biais (mêmes familles que mtf.TRIGGER_EVENTS, scindées).
# Accumulation : on entre sur une *force* (spring validé, cassure haussière, repli tenu).
# Distribution : on entre sur une *faiblesse* (upthrust rejeté, cassure baissière, rebond mou).
ENTRY_TRIGGERS: dict[str, set[str]] = {
    "accumulation": {"SPRING", "SOS", "LPS"},
    "distribution": {"UTAD", "SOW", "LPSY"},
}

# Séquence canonique servant à jauger l'avancement vers le déclencheur.
SEQUENCE: dict[str, list[str]] = {
    "accumulation": ["SC", "AR", "ST", "SOS"],
    "distribution": ["BC", "AR", "ST", "SOW"],
}

_STAGE_LABEL = {"SC": "climax", "BC": "climax", "AR": "rebond auto",
                "ST": "test", "SOS": "déclencheur", "SOW": "déclencheur"}


@dataclass
class MonitorSnapshot:
    ts: pd.Timestamp           # horodatage de la dernière barre clôturée
    price: float
    expect: str | None         # biais anticipé : accumulation | distribution | None
    schema_bias: str           # biais reconnu par la structure fenêtre
    phase: str                 # phase Wyckoff (B/C/D) si disponible
    stage: str                 # étape la plus avancée du schéma attendu (label FR)
    progress: float            # 0..1 vers le déclencheur du biais attendu
    state: str                 # NONE | WATCH | ALERT
    fresh_signal: Event | None  # déclencheur frais (bars_ago==0), s'il y en a un
    structure: WindowStructure
    events: list[Event] = field(default_factory=list)
    note: str = ""

    # --- progression vers le déclencheur ------------------------------------ #
    def as_row(self) -> dict:
        sig = self.fresh_signal
        return {
            "time": _cest(self.ts).strftime("%d/%m %H:%M"),
            "price": round(self.price, 2),
            "anticipe": self.expect or "—",
            "schema": self.schema_bias,
            "phase": self.phase,
            "etape": self.stage,
            "avancement": f"{round(self.progress * 100)}%",
            "signal": f"{sig.name} (f{sig.strength:.2f})" if sig else "—",
            "etat": self.state,
        }


def _cest(ts: pd.Timestamp) -> pd.Timestamp:
    """Horodatage en heure d'Europe (CEST ≈ UTC+2), cohérent avec le reste du projet."""
    return ts + pd.Timedelta(hours=2)


# --------------------------------------------------------------------------- #
# Cœur : un instantané d'analyse
# --------------------------------------------------------------------------- #
def _progress_and_stage(struct: WindowStructure, bias: str) -> tuple[float, str]:
    """Avancement (0..1) et étape la plus avancée atteinte dans la séquence `bias`."""
    if bias not in SEQUENCE:
        return 0.0, "—"
    seq = SEQUENCE[bias]
    names = {e.name for e in struct.events}
    reached = -1
    for i, name in enumerate(seq):
        if name in names:
            reached = i
    if reached < 0:
        return 0.0, "—"
    return (reached + 1) / len(seq), _STAGE_LABEL.get(seq[reached], "—")


def monitor_once(
    df: pd.DataFrame,
    expect: str | None = None,
    th: Thresholds | None = None,
    lookback: int = 30,
    tr_lookback: int = 80,
    buffer: int = 5,
) -> MonitorSnapshot:
    """Analyse un DataFrame *déjà clôturé* (features incluses) et renvoie l'instantané.

    `expect` : biais anticipé. S'il est posé, seul un déclencheur de ce biais lève ALERT,
    et l'avancement est mesuré sur sa séquence. À None, on suit le biais dominant détecté.
    """
    th = th or Thresholds()
    price = float(df["close"].iloc[-1])
    ts = df.index[-1]

    struct = detect_window_structure(df, lookback=lookback, th=th)

    # Signaux frais (events.py) : nécessite une plage valide pour se référencer.
    tr = detect_trading_range(df, lookback=tr_lookback, buffer=buffer)
    ev: list[Event] = detect_events(df, tr, buffer=buffer, th=th) if tr.is_valid else []

    # Biais de référence : ce que tu anticipes, sinon ce que la structure reconnaît.
    ref_bias = expect or (struct.bias if struct.bias != "neutral" else None)
    progress, stage = _progress_and_stage(struct, ref_bias) if ref_bias else (0.0, "—")

    # Déclencheurs candidats = events.py + signe directionnel de la structure fenêtre.
    trigger_names = (ENTRY_TRIGGERS.get(expect) if expect
                     else ENTRY_TRIGGERS["accumulation"] | ENTRY_TRIGGERS["distribution"])
    candidates: list[Event] = list(ev)
    for we in struct.events:
        if we.name in trigger_names:
            candidates.append(Event(we.name, we.bias, we.bars_ago, we.strength, we.price, we.why))

    fresh = [e for e in candidates
             if e.bars_ago == 0 and e.name in trigger_names
             and (expect is None or e.bias == expect)]
    fresh_signal = max(fresh, key=lambda e: e.strength) if fresh else None

    # --- état --------------------------------------------------------------- #
    note = ""
    if fresh_signal is not None:
        state = "ALERT"
    elif struct.is_valid and (expect is None or struct.bias == expect):
        state = "WATCH"
    elif expect and struct.is_valid and struct.bias != expect:
        state, note = "NONE", f"schéma contraire ({struct.bias}) à l'anticipation"
    else:
        state = "NONE"

    return MonitorSnapshot(
        ts=ts, price=price, expect=expect,
        schema_bias=struct.bias, phase=_phase_of(struct),
        stage=stage, progress=progress, state=state,
        fresh_signal=fresh_signal, structure=struct, events=ev, note=note,
    )


def _phase_of(struct: WindowStructure) -> str:
    """Phase Wyckoff grossière à partir des événements de la structure fenêtre."""
    names = {e.name for e in struct.events}
    if struct.bias == "accumulation":
        if "SOS" in names:
            return "D (markup imminent)"
        if "ST" in names:
            return "C/B (test)"
        if "SC" in names:
            return "B (construction)"
    elif struct.bias == "distribution":
        if "SOW" in names:
            return "D (markdown imminent)"
        if "ST" in names:
            return "C/B (test)"
        if "BC" in names:
            return "B (construction)"
    return "—"


# --------------------------------------------------------------------------- #
# Mise en forme de l'alerte
# --------------------------------------------------------------------------- #
def alert_text(symbol: str, timeframe: str, snap: MonitorSnapshot) -> str:
    """Message d'alerte (déclencheur frais), partagé console / Telegram."""
    sig = snap.fresh_signal
    sens = "FORCE (accumulation)" if (sig and sig.bias == "accumulation") else "FAIBLESSE (distribution)"
    why = f"\n  → {sig.note}" if sig and sig.note else ""
    return (
        f"⚠️ {symbol} {timeframe} — DÉCLENCHEUR {sig.name if sig else '?'} [{sens}]\n"
        f"  {_cest(snap.ts).strftime('%d/%m %H:%M')} CEST · prix {snap.price:g}\n"
        f"  schéma {snap.schema_bias} · phase {snap.phase} · avancement {round(snap.progress*100)}%"
        f"{why}"
    )


# --------------------------------------------------------------------------- #
# Cadence : alignement sur la clôture de barre
# --------------------------------------------------------------------------- #
def timeframe_seconds(timeframe: str) -> int:
    unit = timeframe[-1]
    qty = int(timeframe[:-1])
    mult = {"m": 60, "h": 3600, "d": 86400}.get(unit)
    if mult is None:
        raise ValueError(f"timeframe non géré : {timeframe}")
    return qty * mult


def seconds_to_next_close(timeframe: str, now: float | None = None, offset: float = 5.0) -> float:
    """Secondes jusqu'à la prochaine clôture de barre (+ `offset` s de marge pour que
    l'exchange ait publié la barre close)."""
    period = timeframe_seconds(timeframe)
    now = time.time() if now is None else now
    return (period - (now % period)) + offset


# --------------------------------------------------------------------------- #
# Persistance d'état (mode --once / cron) : dédup des alertes entre exécutions
# --------------------------------------------------------------------------- #
def _state_path(symbol: str, timeframe: str) -> str:
    os.makedirs(data_mod.CACHE_DIR, exist_ok=True)
    safe = symbol.replace("/", "_")
    return os.path.join(data_mod.CACHE_DIR, f"monitor_{safe}_{timeframe}.json")


def _load_state(path: str) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_state(path: str, state: dict) -> None:
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(state, f)
    except Exception:
        pass


# --------------------------------------------------------------------------- #
# Récupération + analyse d'un poll
# --------------------------------------------------------------------------- #
def _fetch_and_analyze(ex, symbol: str, cfg: dict) -> MonitorSnapshot:
    df = data_mod.fetch_ohlcv(ex, symbol, cfg["timeframe"], cfg["limit"], use_cache=False)
    if cfg.get("drop_forming", True) and len(df) > 1:
        df = df.iloc[:-1]  # la dernière bougie ccxt est en cours : on n'analyse que du clôturé
    df = add_features(df, vol_ma=cfg["vol_ma"], atr_period=cfg["atr_period"])
    th = Thresholds(**cfg.get("thresholds", {}))
    return monitor_once(df, expect=cfg.get("expect"), th=th,
                        lookback=cfg.get("window", 30), tr_lookback=cfg["lookback"],
                        buffer=cfg["buffer"])


def _emit(symbol: str, cfg: dict, snap: MonitorSnapshot) -> None:
    """Affiche la ligne d'état ; sur ALERT, bandeau console + Telegram."""
    row = snap.as_row()
    line = " | ".join(f"{k}={v}" for k, v in row.items())
    if snap.state == "ALERT":
        msg = alert_text(symbol, cfg["timeframe"], snap)
        print("\n" + "=" * 60 + f"\n{msg}\n" + "=" * 60, flush=True)
        ok = notify.send_telegram(msg, cfg.get("tg_token"), cfg.get("tg_chat_id"))
        if not ok and notify.telegram_configured(cfg.get("tg_token"), cfg.get("tg_chat_id")):
            print("  [telegram] échec d'envoi", file=sys.stderr)
    else:
        print(f"[{symbol}] {line}", flush=True)


# --------------------------------------------------------------------------- #
# Mode one-shot (cron / terminal fermé)
# --------------------------------------------------------------------------- #
def run_once(cfg: dict) -> None:
    ex = data_mod.get_exchange(cfg["exchange"])
    symbols = cfg["symbols"] or ["BTC/USDT"]
    for sym in symbols:
        path = _state_path(sym, cfg["timeframe"])
        st = _load_state(path)
        try:
            snap = _fetch_and_analyze(ex, sym, cfg)
        except Exception as e:
            print(f"  [skip] {sym}: {e}", file=sys.stderr)
            continue
        bar_id = str(snap.ts)
        # Dédup : on n'alerte qu'une fois par barre clôturée.
        if snap.state == "ALERT" and st.get("last_alert_bar") == bar_id:
            snap.state = "WATCH"  # déjà notifié sur cette barre
            snap.note = "déjà alerté sur cette barre"
        _emit(sym, cfg, snap)
        if snap.state == "ALERT":
            st["last_alert_bar"] = bar_id
        st["last_bar"] = bar_id
        _save_state(path, st)


# --------------------------------------------------------------------------- #
# Mode boucle bloquante (écran ouvert)
# --------------------------------------------------------------------------- #
def run_watch(cfg: dict) -> None:
    ex = data_mod.get_exchange(cfg["exchange"])
    symbols = cfg["symbols"] or ["BTC/USDT"]
    interval = cfg.get("interval")  # secondes ; None = aligné sur la clôture de barre
    last_alert_bar: dict[str, str] = {}

    tg = "Telegram actif" if notify.telegram_configured(cfg.get("tg_token"), cfg.get("tg_chat_id")) else "console seule"
    print(f"Suivi {', '.join(symbols)} en {cfg['timeframe']} "
          f"(anticipation : {cfg.get('expect') or 'auto'}) — {tg}. Ctrl-C pour arrêter.",
          file=sys.stderr)

    try:
        while True:
            for sym in symbols:
                try:
                    snap = _fetch_and_analyze(ex, sym, cfg)
                except Exception as e:
                    print(f"  [skip] {sym}: {e}", file=sys.stderr)
                    continue
                bar_id = str(snap.ts)
                if snap.state == "ALERT" and last_alert_bar.get(sym) == bar_id:
                    snap.state, snap.note = "WATCH", "déjà alerté sur cette barre"
                _emit(sym, cfg, snap)
                if snap.state == "ALERT":
                    last_alert_bar[sym] = bar_id

            wait = interval if interval else seconds_to_next_close(cfg["timeframe"])
            nxt = datetime.fromtimestamp(time.time() + wait, tz=timezone.utc)
            print(f"  …prochain poll dans {wait/60:.1f} min "
                  f"(~{(nxt + pd.Timedelta(hours=2)).strftime('%H:%M')} CEST)", file=sys.stderr)
            time.sleep(max(1.0, wait))
    except KeyboardInterrupt:
        print("\nSuivi arrêté.", file=sys.stderr)
