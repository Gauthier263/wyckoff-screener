"""report.py — la commande du biais HTF : texte, JSON et page interactive.

    python -m screener.htf.report                          # maintenant, bornes automatiques
    python -m screener.htf.report --floor 60000 --ceiling 81341 \\
        --floor-zone 59000,60600 --ceiling-zone 81000,81500 --html page.html
    python -m screener.htf.report --asof "2026-11-22 22:00"  # rejeu (heure de Paris)

Les bornes tracées par l'analyste priment toujours sur la détection automatique, qui ne
retrouve celles de CrypNuevo que deux fois sur sept (`research/replay_forecasts.md`).

La page reprend le rendu des analyses Wyckoff (`screener/interactive.py`) : bougies 1D,
volume et OI coin en panneaux synchronisés, heure de Paris, niveaux cliquables. Rien n'y est
écrit à la main : tout vient du `Report`.
"""
from __future__ import annotations

import argparse
import json
import re
import sys

import pandas as pd

from ..clock import fmt, label, parse
from . import bias as B

KIND = {"plancher": "demand", "plafond": "supply", "milieu": "range", "déviation": "trap",
        "mèche": "pivot", "mur": "range"}


def _paris(ts: pd.Timestamp) -> str:
    return fmt(ts, "%Y-%m-%d %H:%M")


def _k(v: float) -> str:
    return f"{v:,.0f}".replace(",", " ")


def _fr(s: str) -> str:
    """« 60,600 » → « 60 600 » : séparateur de milliers français partout dans la page."""
    return re.sub(r"(?<=\d),(?=\d{3}\b)", " ", s)


def notes_from_report(r: B.Report, d1: pd.DataFrame, view_days: int = 160) -> dict:
    """Annotations de la page interactive, construites depuis le rapport (pur)."""
    out = _notes(r, d1, view_days)
    out["text"] = _fr(out["text"])
    for lv in out["levels"]:
        lv["reason"], lv["label"] = _fr(lv["reason"]), _fr(lv["label"])
    return out


def _notes(r: B.Report, d1: pd.DataFrame, view_days: int) -> dict:
    levels = []
    for i, z in enumerate(r.zones, start=1):
        raison = z["raison"]
        kind = next((v for k, v in KIND.items() if k in raison), "range")
        lab = raison.split(" (")[0][:40]
        levels.append({"id": f"N{i}", "price": round(float(z["prix"]), 1), "label": lab,
                       "kind": kind, "reason": raison})
    ref = {round(float(z["prix"]), 1): f"N{i}" for i, z in enumerate(r.zones, start=1)}

    def nid(v):
        return "{" + ref.get(round(float(v), 1), "") + "}" if round(float(v), 1) in ref else _k(v)

    zones = []
    f1 = next((f for f in r.frames if f["cadre"] == "1D"), None)
    if f1:
        b = f1["bornes"]
        t0 = d1.index[max(0, len(d1) - view_days)]
        t1 = d1.index[-1]
        if b.floor_zone[1] > b.floor_zone[0]:
            zones.append({"id": "M1", "from": _paris(t0), "to": _paris(t1), "kind": "demand",
                          "low": b.floor_zone[0], "high": b.floor_zone[1],
                          "label": "zone du plancher 1D",
                          "reason": f"du creux extrême au niveau le plus défendu ({b.source})"})
        if b.ceiling_zone[1] > b.ceiling_zone[0]:
            zones.append({"id": "M2", "from": _paris(t0), "to": _paris(t1), "kind": "supply",
                          "low": b.ceiling_zone[0], "high": b.ceiling_zone[1],
                          "label": "zone du plafond 1D",
                          "reason": f"du niveau le plus défendu au sommet extrême ({b.source})"})

    t = [f"### Biais",
         f"- **{r.bias.capitalize()}**, conviction {r.conviction} (score {r.score:+d}), "
         f"prix {_k(r.price)} au {fmt(r.asof)} {label(r.asof)}."]
    if r.bias == "neutre":
        t.append("- Aucun avantage mesuré à cet endroit : au milieu du range, les prévisions "
                 "rejouées valent pile ou face (11 sur 21). Attendre un extrême ou une sortie.")
    t += ["", "### Cadres"]
    for f in r.frames:
        b = f["bornes"]
        t.append(f"- **{f['cadre']}** — range {_k(b.floor)} – {_k(b.ceiling)} ({b.source}), "
                 f"prix en zone « {f['zone']} » ({f['position']:.0%}).")
        for x in f["raisons"]:
            t.append(f"- {x}")
    t += ["", "### Scénarios"]
    for s in r.scenarios:
        cib = " puis ".join(c if isinstance(c, str) else nid(c) for c in s["cibles"]) or "-"
        t.append(f"- **{s['nom'].capitalize()}** : déclencheur {s['déclencheur']} ; "
                 f"cibles {cib} ; invalidation {s['invalidation']}.")
    t += ["", "### Niveaux (justifiés)", "[[levels]]"]
    liq = [w for w in r.wicks if w.get("attendu")]
    if liq:
        t += ["", "### Mèches de liquidation"]
        for w in liq:
            t.append(f"- {w['tf']} {fmt(w['at'])}, mèche {w['direction']}, liquidations "
                     f"{w['liq_rel']:.1f}× : {w['note']}")
    t += ["", "### Hors mesure (contexte)"]
    e = r.context.get("EMA 50 1D") or {}
    if e.get("ema"):
        t.append(f"- EMA 50 1D {_k(e['ema'])}, prix à {e['stretch_atr']:+.1f} ATR "
                 f"({'au-dessus' if e['above'] else 'en dessous'}) : non mesuré, poids nul.")
    if r.alerts:
        t += ["", "### Alertes"] + [f"- {a}" for a in r.alerts]
    return {
        "page_title": "Biais HTF BTC",
        "title": f"BTC 1D — biais {r.bias} ({fmt(r.asof)} {label(r.asof)})",
        "subtitle": ("Moteur de biais HTF : règles mesurées seulement (déviation, acceptance, "
                     "extrêmes de range, mèches de liquidation). Bougies et volume Binance spot, "
                     "OI coin Binance via Coinalyze. Heure de Paris."),
        "view": {"from": _paris(d1.index[max(0, len(d1) - view_days)])},
        "levels": levels, "zones": zones, "events": [], "text": "\n".join(t),
        "footer": ("Chaque règle et sa mesure : research/structure_rules.md, wick_rule.md, "
                   "three_taps.md, replay_forecasts.md."),
    }


def run(asof=None, bounds: "B.Bounds | None" = None, symbol: str = "BTC/USDT",
        with_liqmap: bool = False):
    """Charge les données figées à `asof` (maintenant par défaut) et produit le rapport."""
    t = pd.Timestamp.now(tz="UTC") if asof is None else pd.Timestamp(asof)
    if t.tzinfo is None:
        t = t.tz_localize("UTC")
    d = B.load_asof(t, symbol)
    lm = None
    if with_liqmap:
        from . import replay as RP
        try:
            lm = RP.replay(t, lookback_days=30, timeframe="1h")
        except Exception:
            lm = None
    r = B.assess(d["1d"], d["4h"], d["1h"], bounds_1d=bounds, liq_daily=d["liq"],
                 liqmap=lm, asof=t)
    return r, d


def write_page(r: B.Report, d1: pd.DataFrame, out: str, symbol: str = "BTC/USDT",
               with_oi: bool = True) -> str:
    from .. import data as D
    from ..interactive import build_interactive_html

    df = d1.tail(400)
    oi = None
    if with_oi:
        try:
            oi = D.fetch_open_interest_ohlc(symbol, "1d", len(df), start=df.index[0],
                                            end=df.index[-1])
        except Exception:
            oi = None
    return build_interactive_html(symbol, "1d", df, out, notes=notes_from_report(r, df),
                                  oi_ohlc=oi)


def _pair(s: "str | None"):
    if not s:
        return None
    a, b = (float(x) for x in s.split(","))
    return (min(a, b), max(a, b))


def main(argv=None):
    p = argparse.ArgumentParser(description="Biais HTF (1D/4h) : texte, JSON, page.")
    p.add_argument("--asof", help="date de rejeu, heure de Paris (« 2026-11-22 22:00 »)")
    p.add_argument("--symbol", default="BTC/USDT")
    p.add_argument("--floor", type=float, help="plancher du range 1D tracé par l'analyste")
    p.add_argument("--ceiling", type=float, help="plafond du range 1D tracé par l'analyste")
    p.add_argument("--floor-zone", help="zone du plancher « bas,haut »")
    p.add_argument("--ceiling-zone", help="zone du plafond « bas,haut »")
    p.add_argument("--liqmap", action="store_true", help="ajouter les murs d'OI (plus lent)")
    p.add_argument("--html", help="écrire la page interactive à ce chemin")
    p.add_argument("--json", help="écrire le rapport en JSON à ce chemin")
    a = p.parse_args(argv)
    asof = parse(a.asof, pd.Timestamp.now().year) if a.asof else None
    bounds = None
    if a.floor and a.ceiling:
        bounds = B.Bounds(a.floor, a.ceiling, _pair(a.floor_zone), _pair(a.ceiling_zone))
    r, d = run(asof, bounds, a.symbol, a.liqmap)
    print(B.to_text(r))
    if a.json:
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump({"asof": str(r.asof), "prix": r.price, "biais": r.bias, "score": r.score,
                       "conviction": r.conviction, "scénarios": r.scenarios,
                       "zones": [{**z, "zone": list(z["zone"]) if z["zone"] else None}
                                 for z in r.zones], "alertes": r.alerts},
                      f, ensure_ascii=False, indent=1, default=str)
    if a.html:
        print(f"→ page : {write_page(r, d['1d'], a.html, a.symbol)}", file=sys.stderr)


if __name__ == "__main__":
    main()
