"""htf/alerts.py — alertes sur événement du biais HTF (1D / 4h).

À chaque clôture 4h, le moteur (`bias.assess`) est évalué deux fois sur des données figées :
à la clôture qui vient de tomber et à la précédente. Seuls les **changements d'état** sont
signalés, jamais un état qui dure :

| Type | Quand | Pourquoi c'est mesuré |
|---|---|---|
| `déviation` | une sortie de range vient d'être reprise (ou son extrême s'étend) | milieu atteint 55-70 % contre 17-32 % (`structure_rules.md`) |
| `acceptance` | le déclencheur d'une déviation passe acquis / perdu (2 clôtures 4h) | filtre de validité (`structure_rules.md`) |
| `déviation close` | la déviation est accomplie (milieu atteint) ou annulée (prix ressorti) | — |
| `cassure` | une cassure de borne devient acceptée | idem acceptance |
| `mèche` | une mèche de liquidation 1h/4h vient d'être qualifiée et n'est pas retestée | 50 % retesté d'abord ~6 fois sur 10 (`wick_rule.md`) |
| `biais` | le biais passe haussier / neutre / baissier | assemblage des règles ci-dessus |

Seuls les cadres aux bornes **tracées par l'analyste** (le 1D, `config/htf_bounds.json`)
déclenchent des alertes de structure : la détection automatique ne retrouve les bornes de
CrypNuevo que 2 fois sur 7, et le cadre 4h automatique produisait à lui seul 6 alertes en
4 jours sur le rejeu d'octobre-novembre. Il continue de compter dans le biais. Un changement
de biais doit tenir 2 clôtures 4h, sauf s'il vient d'un événement 1D (clôture journalière).
L'acceptance n'est perdue qu'après 2 clôtures 4h repassées de l'autre côté du seuil : même
exigence dans les deux sens (une clôture isolée faisait basculer l'état 4 fois en 2 jours).

    python -m screener.htf.alerts                    # un passage (cron), Telegram si secrets
    python -m screener.htf.alerts --replay "2026-11-15 00:00" "2026-11-24 12:00"

Bornes 1D lues dans `config/htf_bounds.json` (tracées par l'analyste). Aide à la décision :
aucun ordre n'est jamais passé.
"""
from __future__ import annotations

import argparse
import json
import os
import re

import pandas as pd

from ..clock import fmt, label, parse
from . import bias as B
from . import structure as S
from . import wick_study as WS

BOUNDS_PATH = "config/htf_bounds.json"
STATE_PATH = ".cache/htf_alerts_state.json"
FOOTER = "[aide à la décision, pas un ordre]"
BAR = pd.Timedelta("4h")
MAX_CATCHUP = 6                       # au plus 24 h rattrapées si le cron a sauté des passages
WICK_RECENT = {"4h": 13, "1h": 30}    # 1h : la mèche n'est qualifiée qu'à la clôture du jour
# Profondeur chargée : le 1D sert aux bornes automatiques et à l'EMA, les mèches n'ont
# besoin que des 200 dernières bougies (ATR compris). Garde un premier passage léger en CI.
HISTORY = {"1d": "2020-01-01", "4h": "2024-01-01", "1h": "2025-06-01"}


# ===================================================================== bornes et données

def load_bounds(path: str = BOUNDS_PATH) -> "B.Bounds | None":
    try:
        with open(path, encoding="utf-8") as f:
            c = json.load(f)
    except (OSError, ValueError):
        return None
    return B.Bounds(float(c["floor"]), float(c["ceiling"]),
                    tuple(c.get("floor_zone") or ()) or None,
                    tuple(c.get("ceiling_zone") or ()) or None,
                    source="analyste", note=c.get("source", ""))


def load_data(symbol: str = "BTC/USDT", end=None) -> dict:
    """Charge une fois tout l'historique nécessaire ; `freeze` le découpe ensuite."""
    from .. import data as D
    out = {tf: WS.load(symbol, tf, HISTORY[tf]) for tf in ("1d", "4h", "1h")}
    end = pd.Timestamp.now(tz="UTC") if end is None else pd.Timestamp(end)
    try:
        out["liq"] = D.fetch_liquidations(symbol, "1d",
                                          start=pd.Timestamp("2020-01-01", tz="UTC"), end=end)
    except Exception:
        out["liq"] = None
    return out


def freeze(data: dict, asof: pd.Timestamp) -> dict:
    """Bougies clôturées avant `asof`, liquidations des journées closes (pur)."""
    out = {}
    for tf, dur in (("1d", "1D"), ("4h", "4h"), ("1h", "1h")):
        df = data[tf]
        out[tf] = df[df.index + pd.Timedelta(dur) <= asof]
    liq = data.get("liq")
    out["liq"] = None if liq is None else liq[liq.index + pd.Timedelta("1D") <= asof]
    return out


def last_close(now: pd.Timestamp) -> pd.Timestamp:
    """Heure de clôture de la dernière bougie 4h (UTC, multiples de 4 h)."""
    return pd.Timestamp(now).tz_convert("UTC").floor("4h")


# ===================================================================== état et transitions

def _bkey(b: B.Bounds) -> tuple:
    return tuple(round(float(x), 1) for x in (b.floor, b.ceiling, *b.floor_zone, *b.ceiling_zone))


def snapshot(r: B.Report, wicks: "list | None" = None,
             h4: "pd.DataFrame | None" = None) -> dict:
    """État comparable d'un rapport (pur). `wicks` : mèches qualifiées (sinon `r.wicks`).

    `h4` sert à mesurer le **rejet** du seuil d'acceptance : 2 clôtures 4h consécutives
    repassées de l'autre côté. C'est ce rejet, et non une seule clôture, qui fait perdre
    l'acceptance — même exigence dans les deux sens.
    """
    frames = {}
    for f in r.frames:
        dv, rejet = f["déviation"], False
        if dv and h4 is not None and len(h4):
            other = "below" if dv["côté"] == "sous le plancher" else "above"
            rejet = S.acceptance(h4.tail(12), dv["seuil_acceptance"], other,
                                 min_closes=2)["accepted"]
        frames[f["cadre"]] = {"zone": f["zone"], "bornes": _bkey(f["bornes"]),
                              "b": f["bornes"], "déviation": dv, "rejet": rejet,
                              "cassure": f["cassure"],
                              "accomplie": f.get("déviation_accomplie")}
    wk = {}
    for w in (r.wicks if wicks is None else wicks):
        if w.get("attendu") and w.get("validée"):
            wk[f"{w['tf']}|{pd.Timestamp(w['at']).isoformat()}|{w['direction']}"] = w
    return {"asof": r.asof, "price": r.price, "bias": r.bias, "score": r.score,
            "conviction": r.conviction, "frames": frames, "wicks": wk}


def _k(v: float) -> str:
    return f"{v:,.0f}".replace(",", " ")


def _f(v: float) -> str:
    return f"{v:.1f}".replace(".", ",")


def _pct(v: float) -> str:
    return f"{v * 100:.0f} %"


def level_reasons(frames: dict) -> dict:
    """Prix arrondi → raison qui en fait un niveau clé (pour justifier chaque chiffre)."""
    out = {}

    def put(v, why):
        out.setdefault(round(float(v)), why)

    for cadre, f in frames.items():
        b = f["b"]
        rng = "range 1D" if cadre == "1D" else "sous-range 4h"
        dv = f["déviation"]
        if dv:
            put(dv["extrême"], f"extrême de la déviation {cadre}")
        put(b.floor_zone[0], f"bas de la zone du plancher, {rng}")
        put(b.floor_zone[1], f"haut de la zone du plancher, {rng}")
        put(b.floor, f"plancher du {rng}")
        put(b.mid, f"milieu du {rng}")
        put(b.ceiling, f"plafond du {rng}")
        put(b.ceiling_zone[0], f"bas de la zone du plafond, {rng}")
        put(b.ceiling_zone[1], f"haut de la zone du plafond, {rng}")
    return out


def justify(text: str, reasons: dict) -> str:
    """« au-dessus de 60,600 » → « au-dessus de 60 600 (haut de la zone du plancher, …) »."""
    def rep(m):
        v = float(m.group(0).replace(",", ""))
        why = reasons.get(round(v))
        return _k(v) + (f" ({why})" if why else "")
    return re.sub(r"\d{1,3}(?:,\d{3})+(?:\.\d+)?", rep, text)


def _acc_status(f: dict) -> "str | None":
    """« acquise » (2 clôtures 4h au-delà), « perdue » (2 clôtures repassées), sinon None."""
    dv = f["déviation"]
    if not dv:
        return None
    return "acquise" if dv["acceptance"] else "perdue" if f.get("rejet") else None


def transitions(prev: dict, cur: dict, memory: "dict | None" = None) -> list:
    """Changements d'état entre deux évaluations successives.

    Renvoie une liste de `{"type", "cadre", "clé", "texte"}`. La clé sert à la déduplication.
    `memory` (mis à jour sur place, sérialisable en JSON) garde le dernier état **confirmé**
    de chaque acceptance et du biais : une clôture isolée de l'autre côté ne le change pas.
    """
    mem = {} if memory is None else memory
    accm = mem.setdefault("acc", {})
    out = []
    reasons = level_reasons(cur["frames"])
    for cadre, c in cur["frames"].items():
        p = prev["frames"].get(cadre)
        if p is None or p["bornes"] != c["bornes"]:
            continue                                   # bornes recalculées : pas d'événement
        if c["b"].source == "automatique" and not mem.get("auto_frames"):
            continue                                   # bornes non tracées : pas d'alerte
        b = c["b"]
        cd, pd_ = c["déviation"], p["déviation"]
        if cd and (not pd_ or pd_["côté"] != cd["côté"]):
            edge = b.floor_zone[0] if cd["côté"] == "sous le plancher" else b.ceiling_zone[1]
            sens = "haussier" if cd["côté"] == "sous le plancher" else "baissier"
            acc = "acquise" if cd["acceptance"] else "à obtenir"
            out.append({"type": "déviation", "cadre": cadre,
                        "clé": f"dev|{cadre}|{cd['côté']}|{round(cd['extrême'])}",
                        "texte": (f"{cadre} : déviation {cd['côté']} reprise — extrême "
                                  f"{_k(cd['extrême'])} (extrême de la sortie), prix revenu dans "
                                  f"le range au-delà de {_k(edge)} ({reasons.get(round(edge), '')}). "
                                  f"Scénario {sens} : acceptance (2 clôtures 4h) "
                                  f"{'au-dessus de' if sens == 'haussier' else 'sous'} "
                                  f"{_k(cd['seuil_acceptance'])} "
                                  f"({reasons.get(round(cd['seuil_acceptance']), '')}) — {acc}. "
                                  f"Mesure : {B.DEV_MEASURE}.")})
        elif cd and pd_ and abs(cd["extrême"] / pd_["extrême"] - 1) > 0.002:
            out.append({"type": "déviation", "cadre": cadre,
                        "clé": f"dev|{cadre}|{cd['côté']}|{round(cd['extrême'])}",
                        "texte": (f"{cadre} : la déviation {cd['côté']} s'étend — nouvel extrême "
                                  f"{_k(cd['extrême'])} (était {_k(pd_['extrême'])}) : "
                                  "l'invalidation du scénario de reprise recule d'autant.")})
        st = _acc_status(c)
        if cd and (not pd_ or pd_["côté"] != cd["côté"]):
            accm[f"{cadre}|{cd['côté']}"] = st       # annoncé avec la déviation
        elif cd:
            key = f"{cadre}|{cd['côté']}"
            known = accm.setdefault(key, _acc_status(p))
            changed = st is not None and st != known
            accm[key] = st if st is not None else known
            if changed and (st == "acquise" or known == "acquise"):
                lv = cd["seuil_acceptance"]
                haut = cd["côté"] == "sous le plancher"
                if st == "acquise":
                    txt = (f"{cadre} : acceptance ACQUISE {'au-dessus de' if haut else 'sous'} "
                           f"{_k(lv)} ({reasons.get(round(lv), '')}) — 2 clôtures 4h : le "
                           f"déclencheur du scénario {'haussier' if haut else 'baissier'} est rempli. "
                           f"Mesure : {B.ACC_MEASURE}.")
                else:
                    txt = (f"{cadre} : acceptance PERDUE {'au-dessus de' if haut else 'sous'} "
                           f"{_k(lv)} ({reasons.get(round(lv), '')}) — 2 clôtures 4h repassées "
                           f"{'dessous' if haut else 'au-dessus'} : le déclencheur du scénario "
                           f"{'haussier' if haut else 'baissier'} n'est plus rempli ; la déviation "
                           f"reste valable tant que l'extrême {_k(cd['extrême'])} tient.")
                out.append({"type": "acceptance", "cadre": cadre,
                            "clé": f"acc|{cadre}|{cd['côté']}|{cd['acceptance']}|{cur['asof']}",
                            "texte": txt})
        if pd_ and not cd:
            accm.pop(f"{cadre}|{pd_['côté']}", None)
        if pd_ and not cd and not c["cassure"]:
            if c["accomplie"]:
                txt = (f"{cadre} : déviation {pd_['côté']} ACCOMPLIE — le milieu {_k(b.mid)} "
                       f"(cible d'une déviation reprise) est atteint ; elle ne porte plus le biais.")
                typ = "déviation close"
            else:
                edge = b.floor_zone[0] if pd_["côté"] == "sous le plancher" else b.ceiling_zone[1]
                txt = (f"{cadre} : déviation {pd_['côté']} ANNULÉE — clôture de nouveau hors du "
                       f"range, au-delà de {_k(edge)} ({reasons.get(round(edge), '')}). "
                       "Pas encore une cassure : il faut 2 clôtures pour l'acceptance.")
                typ = "déviation close"
            out.append({"type": typ, "cadre": cadre,
                        "clé": f"devclose|{cadre}|{pd_['côté']}|{cur['asof']}", "texte": txt})
        cc, pc = c["cassure"], p["cassure"]
        if cc and (not pc or pc["sens"] != cc["sens"]):
            out.append({"type": "cassure", "cadre": cadre,
                        "clé": f"brk|{cadre}|{cc['sens']}|{round(cc['niveau'])}",
                        "texte": (f"{cadre} : cassure {cc['sens']} ACCEPTÉE de {_k(cc['niveau'])} "
                                  f"({reasons.get(round(cc['niveau']), '')}), extrême "
                                  f"{_k(cc['extrême'])}. Mesure : {B.ACC_MEASURE}. Une ré-entrée "
                                  "dans le range en ferait une déviation.")})
    fresh = [(k, w) for k, w in cur["wicks"].items()
             if k not in prev["wicks"] and not w["retestée"] and w["âge"] <= 13]
    # Une même mèche vue en 4h et en 1h (même pointe) : une seule ligne, les deux 50 %.
    groups = {}
    for k, w in sorted(fresh, key=lambda kw: kw[1]["tf"] != "4h"):
        groups.setdefault((w["direction"], round(w["tip"])), []).append((k, w))
    for (direction, _), ws in groups.items():
        k, w = ws[0]
        sens = "monter" if direction == "basse" else "baisser"
        halves = " ; ".join(f"50 % {x['tf']} à {_k(x['half'])} (moitié de la mèche {x['tf']}, "
                            f"{_f(x['size_atr'])} ATR, âge {x['âge']} bougies {x['tf']})"
                            for _, x in ws)
        out.append({"type": "mèche", "cadre": "/".join(x["tf"] for _, x in ws),
                    "clé": "wick|" + "+".join(kk for kk, _ in ws),
                    "texte": (f"mèche de liquidation {direction} du "
                              f"{fmt(w['at'], '%d/%m %Hh%M')} {label(w['at'])} — pointe "
                              f"{_k(w['tip'])} ({'plus-bas' if direction == 'basse' else 'plus-haut'}"
                              f" de la mèche), liquidations du jour {_f(w['liq_rel'])}× la médiane. "
                              f"{halves}. Si le prix doit {sens}, il retesterait d'abord le 50 % "
                              f"({_pct(w['taux'])} des cas contre {_pct(w['témoin'])} pour un "
                              f"niveau quelconque, médiane {WS.RULE_STATS['délai médian']} "
                              "bougies) ; l'avance disparaît après 8 à 13 bougies sans retest. "
                              "Le 100 % n'a aucun avantage mesuré.")})
    # Biais : un changement porté par un événement 1D (clôture journalière) est signalé tout
    # de suite ; sinon il doit tenir 2 clôtures 4h (un aller-retour de zone 4h n'en est pas un).
    known = mem.setdefault("bias", prev["bias"])
    structural = any(i["cadre"] == "1D" and i["type"] in ("déviation", "cassure", "déviation close")
                     for i in out)
    if cur["bias"] != known and (structural or cur["bias"] == prev["bias"]):
        why = "événement 1D" if structural else "tenu 2 clôtures 4h"
        out.append({"type": "biais", "cadre": "HTF",
                    "clé": f"bias|{cur['bias']}|{cur['asof']}",
                    "texte": (f"biais {known} → {cur['bias'].upper()} ({why} ; score "
                              f"{cur['score']:+d}, conviction {cur['conviction']}).")})
        mem["bias"] = cur["bias"]
    return out


# ===================================================================== message

def _cible(c, reasons) -> str:
    if isinstance(c, str):
        return c
    why = reasons.get(round(float(c)))
    return _k(c) + (f" ({why})" if why else "")


def compose(r: B.Report, cur: dict, items: list, symbol: str = "BTC/USDT") -> str:
    """Un message par passage : en-tête, événements, scénario principal, garde-fous."""
    reasons = level_reasons(cur["frames"])
    head = (f"{symbol.split('/')[0]} HTF — clôture 4h du {fmt(r.asof, '%d/%m %Hh%M')} "
            f"{label(r.asof)} — prix {_k(r.price)}")
    lines = [head, ""]
    if items:
        lines += [f"- {it['texte']}" for it in items] + [""]
    lines += [f"Biais : {r.bias} (score {r.score:+d}, conviction {r.conviction})."]
    # biais tranché : le scénario principal ; neutre : les deux, aucun n'a l'avantage
    for s in (r.scenarios if r.bias == "neutre" else r.scenarios[:1]):
        cib = (" puis ".join(_cible(c, reasons) for c in s["cibles"])
               or "hors du range : pas de cible mesurée")
        lines.append(f"Scénario {s['nom']} : déclencheur {justify(s['déclencheur'], reasons)} ; "
                     f"cibles {cib} ; invalidation {justify(s['invalidation'], reasons)}.")
    for a in r.alerts:
        if "ne pas vendre" in a or "ne pas acheter" in a:
            lines.append("Garde-fou : " + justify(a, reasons) + ".")
    lines += ["", FOOTER]
    return "\n".join(lines)


# ===================================================================== évaluation

def evaluate_at(data: dict, asof: pd.Timestamp, bounds: "B.Bounds | None") -> tuple:
    """Rapport + état à `asof` (données déjà chargées)."""
    d = freeze(data, asof)
    r = B.assess(d["1d"], d["4h"], d["1h"], bounds_1d=bounds, liq_daily=d["liq"], asof=asof)
    wk = []
    for tf in ("4h", "1h"):
        wk += B.liquidation_wicks(d[tf], tf, d["liq"], recent=WICK_RECENT[tf])
    return r, snapshot(r, wk, d["4h"])


def scan(data: dict, closes: list, bounds: "B.Bounds | None", symbol: str = "BTC/USDT",
         memory: "dict | None" = None) -> list:
    """Événements sur une suite de clôtures 4h consécutives : [(asof, items, rapport, état)]."""
    out = []
    prev = None
    memory = {} if memory is None else memory      # partagée sur toute la suite de clôtures
    for t in [closes[0] - BAR] + list(closes):
        r, s = evaluate_at(data, t, bounds)
        if prev is not None:
            items = transitions(prev, s, memory)
            if items:
                out.append((t, items, r, s))
        prev = s
    return out


def run_once(symbol: str = "BTC/USDT", bounds_path: str = BOUNDS_PATH,
             state_path: str = STATE_PATH, now=None) -> int:
    """Un passage (cron) : rattrape les clôtures 4h non évaluées, notifie, mémorise."""
    from ..alerts import _load_state, _notify, _save_state
    now = pd.Timestamp.now(tz="UTC") if now is None else pd.Timestamp(now)
    t1 = last_close(now)
    state = _load_state(state_path)
    seen = set(state.get("sent", []))
    t0 = pd.Timestamp(state["evaluated_until"]) + BAR if state.get("evaluated_until") else t1
    t0 = max(t0, t1 - BAR * (MAX_CATCHUP - 1))
    if t0 > t1:
        return 0
    closes = list(pd.date_range(t0, t1, freq="4h"))
    data = load_data(symbol, end=now)
    sent = 0
    memory = state.get("memory") or {}
    for t, items, r, s in scan(data, closes, load_bounds(bounds_path), symbol, memory):
        fresh = [it for it in items if it["clé"] not in seen]
        if not fresh:
            continue
        _notify(compose(r, s, fresh, symbol))
        seen |= {it["clé"] for it in fresh}
        sent += 1
    state["evaluated_until"] = t1.isoformat()
    state["sent"] = sorted(seen)[-300:]
    state["memory"] = memory
    _save_state(state_path, state)
    return sent


def run_test(symbol: str = "BTC/USDT", bounds_path: str = BOUNDS_PATH) -> str:
    """Message de test : l'état actuel, envoyé par le même canal (vérifie le bout-en-bout)."""
    from ..alerts import _notify
    now = pd.Timestamp.now(tz="UTC")
    data = load_data(symbol, end=now)
    r, s = evaluate_at(data, last_close(now), load_bounds(bounds_path))
    msg = "TEST alertes HTF (à ignorer) — état actuel\n" + compose(r, s, [], symbol)
    _notify(msg)
    return msg


def main(argv=None):
    p = argparse.ArgumentParser(description="Alertes sur événement du biais HTF (1D/4h).")
    p.add_argument("--symbol", default="BTC/USDT")
    p.add_argument("--bounds", default=BOUNDS_PATH)
    p.add_argument("--state", default=STATE_PATH)
    p.add_argument("--replay", nargs=2, metavar=("DEBUT", "FIN"),
                   help="rejouer les alertes entre deux dates (heure de Paris), sans notifier")
    p.add_argument("--test", action="store_true",
                   help="envoyer l'état actuel comme message de test, puis sortir")
    a = p.parse_args(argv)
    if a.test:
        run_test(a.symbol, a.bounds)
        return
    if a.replay:
        year = pd.Timestamp.now().year
        t0, t1 = (last_close(parse(x, year)) for x in a.replay)
        data = load_data(a.symbol, end=t1 + BAR)
        closes = list(pd.date_range(t0, t1, freq="4h"))
        ev = scan(data, closes, load_bounds(a.bounds), a.symbol)
        for _, items, r, s in ev:
            print(compose(r, s, items, a.symbol), end="\n\n")
        print(f"{len(ev)} passage(s) avec alerte sur {len(closes)} clôtures 4h")
        return
    os.makedirs(os.path.dirname(a.state) or ".", exist_ok=True)
    n = run_once(a.symbol, a.bounds, a.state)
    print(f"{n} alerte(s) envoyée(s)" if n else "aucun changement d'état")


if __name__ == "__main__":
    main()
