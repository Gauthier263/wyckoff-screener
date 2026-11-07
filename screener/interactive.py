"""
interactive.py — Graphe interactif HTML (texte de l'analyse ↔ graphe, sur une seule page).

But : supprimer l'aller-retour analyse ↔ TradingView. La page embarque :
  * un graphe **Lightweight Charts** (librairie open-source de TradingView, même rendu,
    zoom/pan à la souris) en 3 panneaux synchronisés : cours / volume (+ vol MA) / OI ;
    bougies **dans la même TF que l'analyse**, horodatage CEST ;
  * un **panneau latéral** : texte de l'analyse + table des niveaux + table des événements.
    Chaque référence du texte (`{BH}`, `{SC}`, `{N1}`, `{M1}`…) devient une **référence
    cliquable** (étiquette neutre, sans pastille de couleur) : clic → le graphe se recentre et met l'élément en surbrillance ; survol →
    surbrillance seule. Inversement, survoler une bougie d'événement surligne sa ligne.

La librairie est **inlinée** (screener/vendor, Apache-2.0) : le fichier marche hors-ligne,
sans CDN, et se partage tel quel.

Deux sources de contenu, combinables :
  1. `struct` (`WindowStructure` détectée) → bornes de plage + événements auto ;
  2. `notes` (dict / JSON écrit pour une analyse discrétionnaire) :
       {
         "title": "BTC H1 — redistribution ?",
         "levels": [{"id": "N1", "price": 75736, "label": "plancher",
                     "reason": "low de l'AR, borne basse", "kind": "range"}],
         "zones":  [{"id": "M1", "from": "03/11 14:00", "to": "03/11 20:00",
                     "label": "rebond sur la borne", "kind": "range"}],
         "events": [{"id": "UT1", "name": "UT?", "time": "03/11 18:00",
                     "kind": "trap", "where": "high", "why": "…"}],
         "text":   "### Lecture\\n{BC} fixe le plafond {BH}… **{N1}** tient."
       }
     Heures des notes en **CEST** (heure affichée sur le graphe), formats acceptés :
     « JJ/MM HH:MM », « AAAA-MM-JJ HH:MM ». `kind` = sens/couleur (palette CLAUDE.md) :
     demand (vert) · supply (rouge) · trap (orange) · range (bleu) · pivot (violet).

CLI :
    python -m screener.interactive --symbol BTC/USDT --timeframe 1h [--notes notes.json]
"""
from __future__ import annotations

import argparse
import html
import json
import math
import re
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from .window import WindowStructure

_VENDOR = Path(__file__).with_name("vendor") / "lightweight-charts-5.0.8.js"

# Palette fixe CLAUDE.md : couleur = sens.
KIND_COLOR = {
    "demand": "#22a861",   # vert  : demande / force (SC, SOS, OI coin↑)
    "supply": "#e0473e",   # rouge : offre / résistance (BC, SOW)
    "trap": "#f08c1a",     # orange: piège / faux signal (UTAD, upthrust, faux SOS)
    "range": "#3b82f6",    # bleu  : bornes de plage / support / repli (LPS)
    "pivot": "#9b5de5",    # violet: spring / pivot / Phase C
    "neutral": "#8a8f98",
}
EVENT_KIND = {
    "SC": "demand", "SOS": "demand", "BC": "supply", "SOW": "supply",
    "UTAD": "trap", "SPRING": "pivot", "AR": "range", "ST": "range",
    "LPS": "range", "LPSY": "supply",
}
# Extrême de la barre sur lequel poser le marqueur (cohérent avec plot._wanted_extreme).
_HIGH_EVENTS_ACC = {"AR", "SOS", "UTAD", "LPSY", "BC"}
_HIGH_EVENTS_DIS = {"BC", "ST", "SOS", "UTAD", "LPSY"}


def _fmt_price(v: float) -> str:
    a = abs(v)
    if a >= 1000:
        return f"{v:,.0f}".replace(",", " ")
    if a >= 1:
        return f"{v:.2f}"
    if a >= 0.01:
        return f"{v:.4f}"
    return f"{v:.6f}"


def _plain(s: str) -> str:
    """Retire l'emphase markdown (*x*, **x**) des textes affichés tels quels en table."""
    return re.sub(r"\*{1,2}([^*]+)\*{1,2}", r"\1", s or "")


def _precision(v: float) -> int:
    a = abs(v)
    return 0 if a >= 10000 else 1 if a >= 1000 else 2 if a >= 1 else 4 if a >= 0.01 else 6


def _parse_local(s: str, year: int, tz_hours: int) -> pd.Timestamp:
    """Heure CEST (texte) → Timestamp UTC réel."""
    s = s.strip()
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M", "%d/%m/%Y %H:%M", "%d/%m %H:%M",
                "%d/%m %Hh", "%Y-%m-%d %Hh"):
        try:
            d = datetime.strptime(s, fmt)
            if "%Y" not in fmt:
                d = d.replace(year=year)
            return pd.Timestamp(d, tz="UTC") - pd.Timedelta(hours=tz_hours)
        except ValueError:
            continue
    raise ValueError(f"heure non reconnue : {s!r} (attendu « JJ/MM HH:MM »)")


def _sec(ts: pd.Timestamp, tz_hours: int) -> int:
    """Secondes epoch décalées de +tz_hours : Lightweight Charts affiche en UTC, on lui
    donne donc l'heure CEST « étiquetée UTC » (même convention que plot.py)."""
    return int(ts.timestamp()) + tz_hours * 3600


# --------------------------------------------------------------------------- #
# Texte : mini-markdown + références cliquables
# --------------------------------------------------------------------------- #
_REF = re.compile(r"\{([A-Za-z][A-Za-z0-9_+\-?]*)\}")


def render_text(text: str, refs: dict[str, dict], thumbs_on: bool = False) -> str:
    """Mini-markdown (### titres, - listes, **gras**, paragraphes) ; une ligne seule
    `[[events]]` / `[[levels]]` / `[[zones]]` place la table correspondante à cet endroit du
    texte (format canonique : tableau événement en section 2, niveaux en section 5) ; `{ID}` → référence
    cliquable si l'ID est connu (niveau, zone ou événement), sinon laissé tel quel.
    Sous le **premier** bloc (paragraphe / puce) qui cite une zone `{M…}`, insère une
    **vignette zoomée** (`<div class="thumb">`) dessinée côté page : le mouvement évoqué
    est visible juste sous la phrase, sans aller le chercher sur le graphe."""
    thumbed: set[str] = set()
    found: list[str] = []

    def thumbs() -> str:
        if not thumbs_on:                                  # défaut : graphe principal seul
            found.clear()
            return ""
        new = [z for z in found if z not in thumbed]
        thumbed.update(new)
        found.clear()
        return "".join(f'<div class="thumb" data-zone="{html.escape(z)}"></div>' for z in new)

    def inline(s: str) -> str:
        s = html.escape(s, quote=False)
        s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
        s = re.sub(r"\*([^*\s][^*]*?)\*", r"<em>\1</em>", s)

        def chip(m):
            rid = m.group(1)
            r = refs.get(rid)
            if r is None:
                return m.group(0)
            if r["type"] == "zone":
                found.append(rid)
            # référence neutre : aucune pastille de couleur (la couleur vit sur le graphe)
            return (f'<button class="ref" data-ref="{html.escape(rid)}">'
                    f'{html.escape(r["chip"])}</button>')
        return _REF.sub(chip, s)

    out, para, items = [], [], []

    def flush():
        if para:
            out.append(f"<p>{inline(' '.join(para))}</p>{thumbs()}")
            para.clear()
        if items:
            out.append("<ul>" + "".join(f"<li>{inline(i)}{thumbs()}</li>" for i in items) + "</ul>")
            items.clear()

    for raw in (text or "").splitlines():
        line = raw.strip()
        if not line:
            flush()
        elif re.fullmatch(r"\[\[(events|levels|zones)\]\]", line):
            flush()
            out.append(f'<div class="slot" data-slot="{line[2:-2]}"></div>')
        elif line.startswith("#"):
            flush()
            out.append(f"<h3>{inline(line.lstrip('#').strip())}</h3>")
            found.clear()                                  # pas de vignette sous un titre
        elif line[:2] in ("- ", "* ", "• "):
            if para:
                out.append(f"<p>{inline(' '.join(para))}</p>{thumbs()}")
                para.clear()
            items.append(line[2:])
        else:
            if items:
                flush()
            para.append(line)
    flush()
    return "\n".join(out)


# --------------------------------------------------------------------------- #
# Modèle : niveaux, zones, événements
# --------------------------------------------------------------------------- #
def _struct_items(struct: WindowStructure | None) -> tuple[list[dict], list[dict]]:
    """Bornes (BH/BB) + événements issus de la détection automatique."""
    if struct is None or not struct.events:
        return [], []
    acc = struct.bias == "accumulation"
    ev = {e.name: e for e in struct.events}
    levels: list[dict] = []
    if acc and "SC" in ev:
        levels.append(dict(id="BB", price=ev["SC"].bar_low, label="borne basse",
                           reason="plancher = low du SC (climax vendeur absorbé)", kind="range"))
        if "AR" in ev:
            levels.append(dict(id="BH", price=ev["AR"].bar_high, label="borne haute",
                               reason="plafond = high de l'AR (rebond réflexe post-SC)", kind="range"))
    elif not acc and "BC" in ev:
        levels.append(dict(id="BH", price=ev["BC"].bar_high, label="borne haute",
                           reason="plafond = high du BC (climax acheteur distribué)", kind="range"))
        if "AR" in ev:
            levels.append(dict(id="BB", price=ev["AR"].bar_low, label="borne basse",
                               reason="plancher = low de l'AR (repli réflexe post-BC)", kind="range"))
    highs = _HIGH_EVENTS_ACC if acc else _HIGH_EVENTS_DIS
    events, seen = [], {}
    for e in struct.events:
        n = seen.get(e.name, 0) + 1
        seen[e.name] = n
        where = "high" if e.name in highs else "low"
        events.append(dict(
            id=e.name if n == 1 else f"{e.name}{n}", name=e.name, ts=e.ts,
            kind=EVENT_KIND.get(e.name, "neutral"), where=where,
            price=e.bar_high if where == "high" else e.bar_low,
            vol_ratio=e.vol_ratio, spread_atr=e.spread_atr, clv=e.clv,
            oi_chg=None if pd.isna(e.oi_chg) else float(e.oi_chg),
            why=e.why, theory=e.theory, auto=True))
    return levels, events


def _bar_at(df: pd.DataFrame, ts: pd.Timestamp) -> int:
    """Index de la barre contenant `ts` (dernière barre ouverte ≤ ts)."""
    i = int(df.index.searchsorted(ts, side="right")) - 1
    return min(max(i, 0), len(df) - 1)


def build_model(symbol: str, timeframe: str, df: pd.DataFrame,
                struct: WindowStructure | None = None, notes: dict | None = None,
                oi_ohlc: pd.DataFrame | None = None, tz_hours: int = 2,
                tz_label: str = "CEST", min_bars: int = 80) -> dict:
    """Assemble les données sérialisées en JSON pour la page (fonction pure, hors-ligne)."""
    notes = notes or {}
    if "vol_ma" not in df.columns:
        from .features import add_features
        df = add_features(df)
    year = int(df.index[-1].year)

    levels, events = _struct_items(struct)
    by_id = {lv["id"]: lv for lv in levels}
    for lv in notes.get("levels", []):          # les notes priment sur l'auto (même ID)
        by_id[lv["id"]] = {"kind": "range", "label": "", "reason": "", **lv}
    levels = list(by_id.values())

    ev_by_id = {e["id"]: e for e in events}
    oi_pct = None
    if oi_ohlc is not None and len(oi_ohlc):
        oi_pct = oi_ohlc["close"].pct_change() * 100           # ΔOI coin % de la barre
    bias_notes = notes.get("bias")                             # "accumulation" | "distribution"
    for e in notes.get("events", []):
        ts = _parse_local(e["time"], year, tz_hours)
        i = _bar_at(df, ts)
        bar = df.iloc[i]
        where = e.get("where", "high")
        ev_by_id[e["id"]] = dict(
            id=e["id"], name=e.get("name", e["id"]), ts=df.index[i],
            kind=e.get("kind", EVENT_KIND.get(e.get("name", ""), "neutral")), where=where,
            price=float(bar["high"] if where == "high" else bar["low"]),
            vol_ratio=float(bar.get("vol_ratio", np.nan)),
            spread_atr=float(bar.get("spread_atr", np.nan)), clv=float(bar.get("clv", np.nan)),
            oi_chg=_note_oi(e, oi_pct, df.index[i]), why=e.get("why", ""),
            theory=e.get("theory") or _note_theory(e, bias_notes),
            verdict=e.get("verdict", ""), sense=e.get("sense", ""), auto=False)
    events = sorted(ev_by_id.values(), key=lambda e: e["ts"])

    zones = []
    for z in notes.get("zones", []):
        t0 = _parse_local(z["from"], year, tz_hours)
        t1 = _parse_local(z["to"], year, tz_hours)
        i0, i1 = sorted((_bar_at(df, t0), _bar_at(df, t1)))
        seg = df.iloc[i0:i1 + 1]
        zones.append(dict(
            id=z["id"], label=z.get("label", ""), reason=z.get("reason", ""),
            kind=z.get("kind", "range"), i0=i0, i1=i1,
            t0=_sec(df.index[i0], tz_hours), t1=_sec(df.index[i1], tz_hours),
            lo=float(z.get("low", seg["low"].min())), hi=float(z.get("high", seg["high"].max()))))

    # Fenêtre initiale : ≥ min_bars, couvrant les événements/zones + la dernière barre.
    anchors = [_bar_at(df, e["ts"]) for e in events] + [z["i0"] for z in zones]
    first = min(anchors) - 12 if anchors else len(df) - min_bars
    first = max(0, min(first, len(df) - min_bars))
    last_i = len(df) - 1
    view = notes.get("view") or {}
    if view.get("to"):
        last_i = _bar_at(df, _parse_local(view["to"], year, tz_hours))
    if view.get("from"):
        first = _bar_at(df, _parse_local(view["from"], year, tz_hours))
    first = max(0, min(first, last_i - min_bars + 1))

    pr = _precision(float(df["close"].iloc[-1]))
    candles, volume, vol_ma = [], [], []
    ev_bars = {_bar_at(df, e["ts"]): e for e in events}
    for i, (ts, r) in enumerate(df.iterrows()):
        t = _sec(ts, tz_hours)
        candles.append(dict(time=t, open=round(float(r["open"]), pr + 1),
                            high=round(float(r["high"]), pr + 1),
                            low=round(float(r["low"]), pr + 1),
                            close=round(float(r["close"]), pr + 1)))
        e = ev_bars.get(i)
        volume.append(dict(time=t, value=float(r["volume"]),
                           up=bool(r["close"] >= r["open"]),
                           ev=(KIND_COLOR[e["kind"]] if e else None)))
        if not math.isnan(float(r["vol_ma"])):
            vol_ma.append(dict(time=t, value=float(r["vol_ma"])))

    oi, oi_unit = [], ""
    if oi_ohlc is not None and len(oi_ohlc):
        med = float(oi_ohlc["close"].median())
        scale, oi_unit = (1e9, "Md$") if med > 1e6 else (1e3, "k coin")
        lo_ts, hi_ts = df.index[0], df.index[-1]
        for ts, r in oi_ohlc.loc[lo_ts:hi_ts].iterrows():
            oi.append(dict(time=_sec(ts, tz_hours),
                           **{k: float(r[k]) / scale for k in ("open", "high", "low", "close")}))

    def ev_out(e):
        return dict(id=e["id"], name=e["name"], time=_sec(e["ts"], tz_hours),
                    label=(e["ts"] + pd.Timedelta(hours=tz_hours)).strftime("%d/%m %H:%M"),
                    kind=e["kind"], color=KIND_COLOR.get(e["kind"], KIND_COLOR["neutral"]),
                    where=e["where"], price=e["price"], price_txt=_fmt_price(e["price"]),
                    vol_ratio=None if pd.isna(e["vol_ratio"]) else round(float(e["vol_ratio"]), 2),
                    spread_atr=None if pd.isna(e["spread_atr"]) else round(float(e["spread_atr"]), 2),
                    clv=None if pd.isna(e.get("clv", np.nan)) else round(float(e["clv"]), 2),
                    oi_chg=None if e["oi_chg"] is None else round(e["oi_chg"], 2),
                    why=_plain(e["why"]), theory=_plain(e["theory"]),
                    verdict=e.get("verdict", ""), sense=_plain(e.get("sense", "")), auto=e["auto"])

    def lv_anchor(lv):
        """Bougie d'origine du niveau : `from` des notes (CEST), sinon la bougie dont le
        high ou le low vaut le prix (± 0.02 %). None → ligne sur toute la largeur."""
        if lv.get("from"):
            return _sec(df.index[_bar_at(df, _parse_local(lv["from"], year, tz_hours))], tz_hours)
        p = float(lv["price"])
        d = np.minimum((df["high"] - p).abs(), (df["low"] - p).abs())
        if len(d) and float(d.min()) <= p * 2e-4:
            return _sec(d.idxmin(), tz_hours)
        return None

    lv_out = [dict(id=lv["id"], price=float(lv["price"]), price_txt=_fmt_price(float(lv["price"])),
                   t0=lv_anchor(lv),
                   label=lv.get("label", ""), reason=lv.get("reason", ""), kind=lv["kind"],
                   color=KIND_COLOR.get(lv["kind"], KIND_COLOR["neutral"]))
              for lv in sorted(levels, key=lambda x: -float(x["price"]))]
    zn_out = [dict(z, color=KIND_COLOR.get(z["kind"], KIND_COLOR["neutral"]),
                   span=(f"{(df.index[z['i0']] + pd.Timedelta(hours=tz_hours)).strftime('%d/%m %H:%M')}"
                         f" → {(df.index[z['i1']] + pd.Timedelta(hours=tz_hours)).strftime('%d/%m %H:%M')}"))
              for z in zones]
    ev_list = [ev_out(e) for e in events]

    refs = {lv["id"]: dict(type="level", color=lv["color"],
                           chip=f'{lv["id"]} {lv["price_txt"]}') for lv in lv_out}
    refs.update({z["id"]: dict(type="zone", color=z["color"],
                               chip=f'{z["id"]} {z["label"]}'.strip()) for z in zn_out})
    refs.update({e["id"]: dict(type="event", color=e["color"], chip=e["id"]) for e in ev_list})

    bias = struct.bias if struct is not None and struct.events else "—"
    seq = " → ".join(e["name"] for e in ev_list) or "—"
    text = notes.get("text") or _auto_text(bias, lv_out, ev_list)
    last = float(df["close"].iloc[-1])
    return dict(
        symbol=symbol, timeframe=timeframe, tz=tz_label, bias=bias, seq=seq,
        title=notes.get("title") or f"{symbol} {timeframe} — {bias}",
        last=last, last_txt=_fmt_price(last),
        last_time=(df.index[-1] + pd.Timedelta(hours=tz_hours)).strftime("%d/%m %H:%M"),
        precision=pr, candles=candles, volume=volume, vol_ma=vol_ma, oi=oi, oi_unit=oi_unit,
        levels=lv_out, zones=zn_out, events=ev_list, first=first, last_i=last_i,
        subtitle=notes.get("subtitle", ""), footer=notes.get("footer", ""),
        page_title=notes.get("page_title", ""),
        text_html=render_text(text, refs, thumbs_on=bool(notes.get("thumbs", False))),
    )


def _note_oi(e: dict, oi_pct: "pd.Series | None", ts: pd.Timestamp) -> "float | None":
    """ΔOI coin % de la barre de l'événement : valeur des notes si fournie, sinon calculée."""
    if e.get("oi_chg") is not None:
        return float(e["oi_chg"])
    if oi_pct is None or ts not in oi_pct.index or pd.isna(oi_pct.loc[ts]):
        return None
    return float(oi_pct.loc[ts])


_THEORY_ALIASES = {"SPRING?": "SPRING", "SOS?": "SOS", "UTAD?": "UTAD", "UT": "UTAD",
                   "UPTHRUST": "UTAD", "LPS?": "LPS", "LPSY?": "LPSY", "BC?": "BC", "SC?": "SC"}


def _note_theory(e: dict, bias: "str | None") -> str:
    """Mémo théorie (rôle + seuils vol×/ATR/clôture) d'un événement des notes, via
    `window._theory` et les `Thresholds` courants. Clé = `theory_of` (ex. « SOW ») ou le
    nom de l'événement ; cadre = `bias` de l'événement sinon celui des notes. Vide si inconnu."""
    from .events import Thresholds
    from .window import _THEORY_DESC, _theory
    key = (e.get("theory_of") or e.get("name") or "").upper().strip()
    key = _THEORY_ALIASES.get(key, key.rstrip(" ?"))
    b = e.get("bias") or bias
    if not b or (b, key) not in _THEORY_DESC:
        return ""
    return _theory(b, key, Thresholds())


def _auto_text(bias: str, levels: list[dict], events: list[dict]) -> str:
    if not events:
        return "Aucune structure détectée sur la fenêtre — ajoute des `notes` pour annoter."
    lines = [f"### Structure détectée : {bias}"]
    ids = {lv["id"] for lv in levels}
    if {"BH", "BB"} <= ids:
        lines.append("Plage bornée par {BH} et {BB}.")
    lines.append("")
    for e in events:
        lines.append(f"- {{{e['id']}}} {e['label']} — {e['why']}")
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Rendu HTML
# --------------------------------------------------------------------------- #
def build_interactive_html(symbol: str, timeframe: str, df: pd.DataFrame, out_path: str,
                           struct: WindowStructure | None = None, notes: dict | None = None,
                           oi_ohlc: pd.DataFrame | None = None, tz_hours: int = 2,
                           tz_label: str = "CEST") -> str:
    """Écrit la page interactive autonome (librairie inlinée) et renvoie son chemin."""
    model = build_model(symbol, timeframe, df, struct, notes, oi_ohlc, tz_hours, tz_label)
    payload = json.dumps(model, ensure_ascii=False).replace("</", "<\\/")
    lib = _VENDOR.read_text(encoding="utf-8")
    page = (_TEMPLATE.replace("__TITLE__", html.escape(model.get("page_title") or model["title"]))
            .replace("__LIB__", lib).replace("__DATA__", payload))
    Path(out_path).write_text(page, encoding="utf-8")
    return out_path


_TEMPLATE = r"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>
:root{
  --bg:#ffffff; --panel:#f6f7f9; --text:#16181d; --muted:#626a76; --border:#dfe2e7;
  --grid:#eef0f3; --up:#26a69a; --down:#ef5350; --volma:#6b7280; --hl:rgba(59,130,246,.10);
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    --bg:#131722; --panel:#1a1f2b; --text:#d8dbe2; --muted:#8b93a1; --border:#2a3040;
    --grid:#1f2533; --volma:#9aa3b2; --hl:rgba(59,130,246,.18); color-scheme:dark;
  }
}
:root[data-theme="dark"]{
  --bg:#131722; --panel:#1a1f2b; --text:#d8dbe2; --muted:#8b93a1; --border:#2a3040;
  --grid:#1f2533; --volma:#9aa3b2; --hl:rgba(59,130,246,.18); color-scheme:dark;
}
*{box-sizing:border-box}
html,body{margin:0;height:100%;background:var(--bg);color:var(--text);
  font:14px/1.45 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}
.app{display:grid;grid-template-columns:minmax(0,1fr) 500px;height:100vh}
.chartcol{position:relative;display:flex;flex-direction:column;min-width:0}
header{display:flex;gap:12px;align-items:baseline;flex-wrap:wrap;padding:10px 14px;
  border-bottom:1px solid var(--border)}
header h1{font-size:15px;margin:0}
header .meta{color:var(--muted);font-size:12px}
header .tools{margin-left:auto;display:flex;gap:6px}
header button{background:var(--panel);color:var(--text);border:1px solid var(--border);
  border-radius:6px;padding:3px 9px;font-size:12px;cursor:pointer}
header button:focus-visible,#nav button:focus-visible,.ref:focus-visible{outline:2px solid var(--muted);outline-offset:1px}
#chartwrap{position:relative;flex:1;min-height:420px}
#chart{position:absolute;inset:0}
#overlay{position:absolute;inset:0;pointer-events:none;z-index:3}
#legend{position:absolute;left:10px;top:6px;z-index:4;font-size:12px;color:var(--muted);
  pointer-events:none;font-variant-numeric:tabular-nums}
#legend b{color:var(--text);font-weight:600}
aside{border-left:1px solid var(--border);background:var(--panel);overflow-y:auto;padding:4px 16px 24px}
aside h2{font-size:12px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);
  margin:18px 0 6px}
.text h3{font-size:14px;margin:14px 0 4px}
.text p,.text li{margin:4px 0}
.text ul{padding-left:18px;margin:4px 0}
table{width:100%;border-collapse:collapse;font-size:12.5px;font-variant-numeric:tabular-nums}
th{text-align:left;color:var(--muted);font-weight:500;padding:4px 4px;border-bottom:1px solid var(--border)}
td{padding:5px 4px;border-bottom:1px solid var(--border);vertical-align:top}
tr.row{cursor:pointer}
tr.row:hover, tr.row.on{background:var(--hl)}
#events tr.row{scroll-margin-top:52px}
tr.row.flash td{background:var(--hl);box-shadow:inset 0 0 0 1px var(--muted)}
#chart{cursor:crosshair}
td.num{text-align:right;white-space:nowrap}
td.why{color:var(--muted);font-size:12px}
details{font-size:12px;color:var(--muted);margin-top:3px}
summary{cursor:pointer}
.ref{display:inline-flex;align-items:center;border:1px solid var(--border);
  background:var(--panel);color:var(--text);border-radius:5px;text-decoration:underline dotted;
  padding:0 6px;margin:0 1px;font:600 12.5px/1.6 inherit;cursor:pointer;white-space:nowrap}
.ref:hover,.ref.on{background:var(--hl);border-color:var(--muted)}
.hint{color:var(--muted);font-size:12px;margin:8px 0 0}
#nav{position:sticky;top:0;z-index:6;display:flex;flex-wrap:wrap;gap:4px;padding:8px 0;
  background:var(--panel);border-bottom:1px solid var(--border)}
#nav button{background:var(--bg);color:var(--text);border:1px solid var(--border);border-radius:5px;
  padding:2px 8px;font-size:12px;cursor:pointer}
#nav button.on{border-color:var(--muted);background:var(--hl)}
#sub{color:var(--muted);font-size:12.5px;margin:10px 0 0}
.text h3{scroll-margin-top:48px}
.slot{margin:6px 0 10px;overflow-x:auto}
td.vd{font-weight:600}
#events td:nth-child(2){white-space:nowrap}
#foot{margin:14px 0 0;padding:8px 10px;border:1px solid var(--border);border-radius:6px;
  background:var(--bg);font-size:12.5px}
.thumb{position:relative;height:150px;margin:6px 0 10px;border:1px solid var(--border);
  border-radius:6px;background:var(--bg);overflow:hidden;cursor:pointer}
.thumb .tc{position:absolute;inset:18px 0 0 0}
.thumb canvas.ov{position:absolute;inset:18px 0 0 0;pointer-events:none;z-index:3}
.thumb .cap{position:absolute;left:6px;top:2px;right:6px;font-size:11px;color:var(--muted);
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.thumb .cap b{color:var(--text)}
.thumb.on{outline:2px solid var(--muted)}
@media (max-width: 900px){
  .app{grid-template-columns:1fr;grid-template-rows:auto auto;height:auto}
  .chartcol{position:sticky;top:0;z-index:5;background:var(--bg);border-bottom:1px solid var(--border)}
  header{padding:6px 10px;gap:6px}
  header h1{font-size:13px}
  header .meta{display:none}
  #chartwrap{flex:none;min-height:0;height:48vh}
  #legend{font-size:10.5px;right:60px}
  aside{border-left:0;border-top:1px solid var(--border);padding:4px 16px 24px}
  #nav{position:static}
  #events tr.row{scroll-margin-top:calc(48vh + 60px)}
}
</style>
</head>
<body>
<div class="app">
  <div class="chartcol">
    <header>
      <h1 id="ttl"></h1><span class="meta" id="meta"></span>
      <div class="tools">
        <button id="zonesbtn" title="Afficher / masquer les rectangles des mouvements M1, M2…" aria-pressed="true">Zones M</button>
        <button id="fit" title="Revenir à la vue initiale">Vue initiale</button>
        <button id="all" title="Tout l'historique chargé">Tout</button>
        <button id="theme" title="Thème clair / sombre">◐</button>
      </div>
    </header>
    <div id="chartwrap"><div id="chart"></div><canvas id="overlay"></canvas><div id="legend"></div></div>
  </div>
  <aside>
    <nav id="nav"></nav>
    <p id="sub"></p>
    <h2>Analyse</h2>
    <div class="text" id="text"></div>
    <div id="foot" hidden></div>
    <p class="hint">Clic sur une référence → le graphe s'y place. Survol d'une bougie
      d'événement → sa ligne s'allume.</p>
    <h2 id="lh">Niveaux</h2>
    <table id="levels"><thead><tr><th>Niveau</th><th class="num">Prix</th><th>Pourquoi ce niveau</th></tr></thead><tbody></tbody></table>
    <h2 id="zh">Mouvements</h2>
    <table id="zones"><thead><tr><th>Zone</th><th>Période</th><th>Lecture</th></tr></thead><tbody></tbody></table>
    <h2 id="eh">Événements</h2>
    <table id="events"><thead><tr><th>Évt</th><th>Heure</th><th class="num">Prix</th><th class="num">vol×</th><th class="num">spr ATR</th><th class="num">CLV</th><th class="num">ΔOI%</th><th>Verdict</th></tr></thead><tbody></tbody></table>
  </aside>
</div>
<script>__LIB__</script>
<script>
const D = __DATA__;
const LW = LightweightCharts;
const $ = s => document.querySelector(s);
const css = n => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const fmt = (v, p) => v == null ? '—' : Number(v).toLocaleString('fr-FR', {maximumFractionDigits: p ?? D.precision});

$('#ttl').textContent = D.title;
$('#meta').textContent = `${D.seq} · bougies ${D.timeframe} (${D.tz}) · dernier ${D.last_txt} @ ${D.last_time}`;
$('#text').innerHTML = D.text_html;
if (D.subtitle) $('#sub').textContent = D.subtitle; else $('#sub').hidden = true;
if (D.footer) { $('#foot').textContent = D.footer; $('#foot').hidden = false; }

// ---------------- Graphe ----------------
const el = $('#chart');
const chart = LW.createChart(el, {
  autoSize: true,
  layout: {attributionLogo: false, panes: {separatorColor: css('--border')}},
  rightPriceScale: {borderVisible: false},
  timeScale: {timeVisible: true, secondsVisible: false, borderVisible: false, rightOffset: 6},
  crosshair: {mode: LW.CrosshairMode.Normal},
});
const priceFormat = {type: 'price', precision: D.precision, minMove: Math.pow(10, -D.precision)};
const candles = chart.addSeries(LW.CandlestickSeries, {
  upColor: css('--up'), downColor: css('--down'), wickUpColor: css('--up'), wickDownColor: css('--down'),
  borderVisible: false, priceFormat,
}, 0);
candles.setData(D.candles);

const vol = chart.addSeries(LW.HistogramSeries, {priceFormat: {type: 'volume'}, priceLineVisible: false, lastValueVisible: false}, 1);
const volMa = chart.addSeries(LW.LineSeries, {lineWidth: 1, priceLineVisible: false, lastValueVisible: false, crosshairMarkerVisible: false}, 1);
volMa.setData(D.vol_ma);
let oiSeries = null;
if (D.oi.length) {
  oiSeries = chart.addSeries(LW.CandlestickSeries, {borderVisible: false, priceLineVisible: false,
    priceFormat: {type: 'price', precision: 3, minMove: 0.001}, title: 'OI ' + D.oi_unit}, 2);
  oiSeries.setData(D.oi);
}
function paneHeights() {
  // cours / volume / OI ≈ 60 / 18 / 22 %
  const ps = chart.panes(), f = [3.4, 1, 1.25];
  ps.forEach((p, i) => p.setStretchFactor(f[i] ?? 1));
}

// Niveaux = segments pointillés qui partent de la bougie d'origine (sommet / creux qui
// définit le niveau, `t0`) jusqu'à la dernière bougie ; sans origine connue → toute la largeur.
// Hors autoscale (comme une price line) : un niveau lointain n'écrase pas les bougies.
const plines = {};
function levelData(lv, a, b) {
  const t0 = Math.max(lv.t0 ?? a, a);
  return t0 <= b ? (t0 === b ? [{time: b, value: lv.price}] : [{time: t0, value: lv.price}, {time: b, value: lv.price}]) : [];
}
for (const lv of D.levels) {
  const ls = chart.addSeries(LW.LineSeries, {color: lv.color, lineWidth: 1, lineStyle: LW.LineStyle.Dashed,
    priceLineVisible: false, lastValueVisible: true, title: lv.id, crosshairMarkerVisible: false,
    pointMarkersVisible: false, autoscaleInfoProvider: () => null, priceFormat}, 0);
  ls.setData(levelData(lv, D.candles[0].time, D.candles[D.candles.length - 1].time));
  plines[lv.id] = ls;
}
// Événements = marqueurs ronds sur l'extrême réel de la barre.
let focusId = null;
const markersApi = LW.createSeriesMarkers(candles, []);
function drawMarkers() {
  markersApi.setMarkers(D.events.map(e => ({
    time: e.time, position: e.where === 'high' ? 'aboveBar' : 'belowBar', color: e.color,
    shape: 'circle', text: e.id,
    size: focusId === e.id ? 2 : 1,
  })));
}

function applyTheme() {
  const t = css('--text'), g = css('--grid');
  chart.applyOptions({layout: {background: {color: css('--bg')}, textColor: css('--muted'),
    panes: {separatorColor: css('--border')}}, grid: {vertLines: {color: g}, horzLines: {color: g}}});
  candles.applyOptions({upColor: css('--up'), downColor: css('--down'), wickUpColor: css('--up'), wickDownColor: css('--down')});
  if (oiSeries) oiSeries.applyOptions({upColor: css('--up'), downColor: css('--down'), wickUpColor: css('--up'), wickDownColor: css('--down')});
  volMa.applyOptions({color: css('--volma')});
  const up = css('--up') + '99', dn = css('--down') + '99';
  vol.setData(D.volume.map(v => ({time: v.time, value: v.value, color: v.ev || (v.up ? up : dn)})));
  drawOverlay();
}

// ---------------- Overlay : zones + traits d'événements + surbrillance ----------------
const cv = $('#overlay'), ctx = cv.getContext('2d');
let showZones = true;
try { showZones = localStorage.getItem('wy-zones') !== '0'; } catch (e) {}
function drawOverlay() {
  const dpr = window.devicePixelRatio || 1, w = el.clientWidth, h = el.clientHeight;
  cv.width = w * dpr; cv.height = h * dpr; cv.style.width = w + 'px'; cv.style.height = h + 'px';
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0); ctx.clearRect(0, 0, w, h);
  const ts = chart.timeScale(), plotW = w - chart.priceScale('right').width();
  const bottom = h - ts.height();
  ctx.save(); ctx.beginPath(); ctx.rect(0, 0, plotW, bottom); ctx.clip();
  const bw = Math.max(ts.options().barSpacing, 2);
  // zones (mouvements cités dans l'analyse)
  for (const z of D.zones) {
    if (!showZones && focusId !== z.id) continue;          // masquées : seule la zone cliquée reste
    const x0 = ts.timeToCoordinate(z.t0), x1 = ts.timeToCoordinate(z.t1);
    if (x0 == null || x1 == null) continue;
    const y0 = candles.priceToCoordinate(z.hi), y1 = candles.priceToCoordinate(z.lo);
    const on = focusId === z.id;
    ctx.fillStyle = z.color + (on ? '40' : '1c'); ctx.strokeStyle = z.color + (on ? 'ff' : '88');
    ctx.lineWidth = on ? 2 : 1;
    const X = x0 - bw / 2, W = x1 - x0 + bw, Y = y0 - 4, H = y1 - y0 + 8;
    ctx.fillRect(X, Y, W, H); ctx.strokeRect(X, Y, W, H);
    ctx.fillStyle = z.color; ctx.font = '600 11px sans-serif'; ctx.fillText(z.id, X + 3, Y - 4);
  }
  // trait vertical uniquement pour l'événement cliqué / survolé (graphe allégé au repos)
  const fe = D.events.find(e => e.id === focusId);
  if (fe) { const x = ts.timeToCoordinate(fe.time);
    if (x != null) { ctx.strokeStyle = fe.color; ctx.lineWidth = 1.5; ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, bottom); ctx.stroke(); } }
  // niveau focalisé : bandeau
  const lv = D.levels.find(l => l.id === focusId);
  if (lv) { const y = candles.priceToCoordinate(lv.price);
    if (y != null) { ctx.fillStyle = lv.color + '2a'; ctx.fillRect(0, y - 5, plotW, 10); } }
  ctx.restore();
}
chart.timeScale().subscribeVisibleLogicalRangeChange(() => requestAnimationFrame(drawOverlay));
new ResizeObserver(() => requestAnimationFrame(drawOverlay)).observe(el);

// ---------------- Navigation ----------------
const N = D.candles.length;
function initialView() { chart.timeScale().setVisibleLogicalRange({from: D.first, to: (D.last_i ?? N - 1) + 6}); }
function idxOf(t) { let lo = 0, hi = N - 1; while (lo < hi) { const m = (lo + hi + 1) >> 1; if (D.candles[m].time <= t) lo = m; else hi = m - 1; } return lo; }
function showPrice(p) {
  // s'assurer que le niveau est dans l'échelle : élargit l'autoscale si besoin
  candles.applyOptions({autoscaleInfoProvider: orig => { const r = orig(); if (!r) return r;
    return {priceRange: {minValue: Math.min(r.priceRange.minValue, p), maxValue: Math.max(r.priceRange.maxValue, p)}, margins: r.margins}; }});
}
function setFocus(id, move) {
  focusId = id;
  document.querySelectorAll('[data-ref]').forEach(n => n.classList.toggle('on', n.dataset.ref === id));
  for (const [k, pl] of Object.entries(plines)) pl.applyOptions({lineWidth: k === id ? 3 : 1,
    lineStyle: k === id ? LW.LineStyle.Solid : LW.LineStyle.Dashed});
  drawMarkers();
  if (move) {
    const e = D.events.find(x => x.id === id), z = D.zones.find(x => x.id === id), lv = D.levels.find(x => x.id === id);
    const r = chart.timeScale().getVisibleLogicalRange(), span = r ? Math.max(40, r.to - r.from) : 80;
    if (e) { const i = idxOf(e.time); chart.timeScale().setVisibleLogicalRange({from: i - span / 2, to: i + span / 2}); }
    if (z) { const pad = Math.max(25, (z.i1 - z.i0)); chart.timeScale().setVisibleLogicalRange({from: z.i0 - pad, to: z.i1 + pad}); }
    if (lv) showPrice(lv.price);
  }
  requestAnimationFrame(drawOverlay);
}
document.addEventListener('click', ev => {
  const n = ev.target.closest('[data-ref]'); if (n) setFocus(n.dataset.ref, true);
});
document.addEventListener('mouseover', ev => {
  const n = ev.target.closest('[data-ref]'); if (n && focusId !== n.dataset.ref) { focusId = n.dataset.ref; drawMarkers(); requestAnimationFrame(drawOverlay); }
});
$('#fit').onclick = () => { candles.applyOptions({autoscaleInfoProvider: undefined}); setFocus(null, false); initialView(); };
$('#all').onclick = () => chart.timeScale().fitContent();
function syncZonesBtn() { const b = $('#zonesbtn'); b.setAttribute('aria-pressed', String(showZones));
  b.textContent = showZones ? 'Masquer zones M' : 'Afficher zones M'; }
$('#zonesbtn').onclick = () => { showZones = !showZones; syncZonesBtn();
  try { localStorage.setItem('wy-zones', showZones ? '1' : '0'); } catch (e) {}
  requestAnimationFrame(drawOverlay); };
if (!D.zones.length) $('#zonesbtn').hidden = true;
syncZonesBtn();
$('#theme').onclick = () => {
  const r = document.documentElement, dark = matchMedia('(prefers-color-scheme: dark)').matches;
  const cur = r.dataset.theme || (dark ? 'dark' : 'light');
  r.dataset.theme = cur === 'dark' ? 'light' : 'dark';
  try { localStorage.setItem('wy-theme', r.dataset.theme); } catch (e) {}
  applyTheme();
};
try { const t = localStorage.getItem('wy-theme'); if (t) document.documentElement.dataset.theme = t; } catch (e) {}
matchMedia('(prefers-color-scheme: dark)').addEventListener('change', applyTheme);

// ---------------- Légende (crosshair) + lien bougie → ligne ----------------
const evByTime = Object.fromEntries(D.events.map(e => [e.time, e]));
const volByTime = Object.fromEntries(D.volume.map(v => [v.time, v.value]));
const maByTime = Object.fromEntries(D.vol_ma.map(v => [v.time, v.value]));
const oiByTime = Object.fromEntries(D.oi.map(o => [o.time, o]));
function legend(t) {
  const c = t != null ? D.candles[idxOf(t)] : D.candles[N - 1];
  const v = volByTime[c.time], ma = maByTime[c.time], o = oiByTime[c.time];
  const chg = ((c.close - c.open) / c.open * 100);
  let s = `<b>${D.symbol} ${D.timeframe}</b> O <b>${fmt(c.open)}</b> H <b>${fmt(c.high)}</b> L <b>${fmt(c.low)}</b> C <b>${fmt(c.close)}</b> `
        + `<span style="color:${chg >= 0 ? css('--up') : css('--down')}">${chg >= 0 ? '+' : ''}${chg.toFixed(2)}%</span>`;
  if (v != null) s += ` · vol <b>${fmt(v, 0)}</b>${ma ? ` (×${(v / ma).toFixed(2)})` : ''}`;
  if (o) s += ` · OI Δ <b>${((o.close - o.open) / o.open * 100).toFixed(2)}%</b>`;
  const e = evByTime[c.time];
  if (e) s += ` · événement <b>${esc(e.id)}</b>`;
  $('#legend').innerHTML = s;
  document.querySelectorAll('tr.row[data-ref]').forEach(n => n.classList.toggle('on', !!e && n.dataset.ref === e.id));
}
chart.subscribeCrosshairMove(p => legend(p && p.time != null ? p.time : null));
// Clic sur une bougie d'événement (± 1 bougie) → sa ligne du tableau, dans le texte.
chart.subscribeClick(p => {
  if (!p || p.time == null) return;
  const i = idxOf(p.time);
  let best = null;
  for (const e of D.events) { const d = Math.abs(idxOf(e.time) - i); if (d <= 1 && (!best || d < best.d)) best = {e, d}; }
  if (!best) return;
  setFocus(best.e.id, false);
  const row = document.querySelector(`#events tr.row[data-ref="${CSS.escape(best.e.id)}"]`);
  if (row) { row.scrollIntoView({behavior: 'smooth', block: 'start'});
    row.classList.add('flash'); setTimeout(() => row.classList.remove('flash'), 1600); }
});

// ---------------- Tables ----------------
$('#levels tbody').innerHTML = D.levels.map(l => `<tr class="row" data-ref="${esc(l.id)}">
  <td><button class="ref sq" data-ref="${esc(l.id)}">${esc(l.id)}</button> ${esc(l.label)}</td>
  <td class="num"><b>${esc(l.price_txt)}</b></td><td class="why">${esc(l.reason)}</td></tr>`).join('')
  || '<tr><td colspan="3" class="why">—</td></tr>';
if (D.zones.length) {
  $('#zones tbody').innerHTML = D.zones.map(z => `<tr class="row" data-ref="${esc(z.id)}">
    <td><button class="ref zn" data-ref="${esc(z.id)}">${esc(z.id)}</button></td>
    <td class="why">${esc(z.span)}</td><td>${esc(z.label)}${z.reason ? `<div class="why">${esc(z.reason)}</div>` : ''}</td></tr>`).join('');
} else { $('#zones').style.display = 'none'; $('#zh').style.display = 'none'; }
$('#events tbody').innerHTML = D.events.map(e => `<tr class="row" data-ref="${esc(e.id)}">
  <td><button class="ref dot" data-ref="${esc(e.id)}">${esc(e.id)}</button></td>
  <td>${esc(e.label)}</td><td class="num">${esc(e.price_txt)}</td>
  <td class="num">${e.vol_ratio != null ? e.vol_ratio.toFixed(2) : '—'}</td>
  <td class="num">${e.spread_atr != null ? e.spread_atr.toFixed(2) : '—'}</td>
  <td class="num">${e.clv != null ? e.clv.toFixed(2) : '—'}</td>
  <td class="num">${e.oi_chg != null ? (e.oi_chg > 0 ? '+' : '') + e.oi_chg.toFixed(2) : '—'}</td>
  <td class="vd">${esc(e.verdict || '')}</td></tr>
  ${(e.sense || e.why || e.theory) ? `<tr data-ref="${esc(e.id)}" class="row"><td colspan="8" class="why">${esc(e.sense || e.why)}
    ${e.theory ? `<details><summary>Théorie</summary>${esc(e.theory)}</details>` : ''}</td></tr>` : ''}`).join('')
  || '<tr><td colspan="8" class="why">—</td></tr>';
// Tables placées dans le texte ([[events]] / [[levels]] / [[zones]]) : on les déplace.
for (const [slot, tid, hid] of [['events', '#events', '#eh'], ['levels', '#levels', '#lh'], ['zones', '#zones', '#zh']]) {
  const box = document.querySelector(`.slot[data-slot="${slot}"]`);
  if (box) { box.appendChild($(tid)); $(hid).style.display = 'none'; }
}
// Navigation par section (une entrée par titre ### du texte).
const heads = [...document.querySelectorAll('.text h3')];
heads.forEach((h, i) => { h.id = 'sec' + i; });
$('#nav').innerHTML = heads.map((h, i) => `<button data-sec="${i}">${esc(h.textContent.split('(')[0].trim().slice(0, 30))}</button>`).join('');
if (!heads.length) $('#nav').hidden = true;
$('#nav').addEventListener('click', ev => { const b = ev.target.closest('button[data-sec]'); if (!b) return;
  document.getElementById('sec' + b.dataset.sec).scrollIntoView({behavior: 'smooth', block: 'start'}); });
const aside = document.querySelector('aside');
function navSpy() { let cur = 0; const top = aside.getBoundingClientRect().top + 56;
  heads.forEach((h, i) => { if (h.getBoundingClientRect().top <= top) cur = i; });
  document.querySelectorAll('#nav button').forEach((b, i) => b.classList.toggle('on', i === cur)); }
aside.addEventListener('scroll', () => requestAnimationFrame(navSpy));
window.addEventListener('scroll', () => requestAnimationFrame(navSpy)); navSpy();

// ---------------- Vignettes zoomées (une par mouvement cité) ----------------
const thumbs = [];
document.querySelectorAll('.thumb[data-zone]').forEach(box => {
  const z = D.zones.find(x => x.id === box.dataset.zone); if (!z) return;
  box.dataset.ref = z.id;
  box.innerHTML = `<div class="cap"><b>${esc(z.id)}</b> ${esc(z.label)} · ${esc(z.span)}${z.reason ? ' — ' + esc(z.reason) : ''}</div><div class="tc"></div><canvas class="ov"></canvas>`;
  const pad = Math.max(8, Math.round((z.i1 - z.i0) * 1.2));
  const a = Math.max(0, z.i0 - pad), b = Math.min(N - 1, z.i1 + pad), lack = z.i1 + pad - b;
  const sub = D.candles.slice(a, b + 1);
  const lo = Math.min(...sub.map(c => c.low)), hi = Math.max(...sub.map(c => c.high)), m = (hi - lo) * 0.35;
  const tc = LW.createChart(box.querySelector('.tc'), {autoSize: true, handleScroll: false, handleScale: false,
    layout: {attributionLogo: false}, rightPriceScale: {visible: false}, leftPriceScale: {visible: false},
    timeScale: {visible: false}, crosshair: {mode: LW.CrosshairMode.Hidden}});
  // échelle figée sur le mouvement : sinon les marqueurs (grosse taille relative) écrasent les bougies
  const s = tc.addSeries(LW.CandlestickSeries, {borderVisible: false, priceLineVisible: false, lastValueVisible: false, priceFormat,
    autoscaleInfoProvider: () => ({priceRange: {minValue: lo - (hi - lo) * 0.08, maxValue: hi + (hi - lo) * 0.08}, margins: {above: 4, below: 4}})});
  s.setData(sub);
  // niveaux proches du mouvement (dans la plage visible ± 35 %) : même ligne que le grand graphe
  for (const lv of D.levels) if (lv.price >= lo - m && lv.price <= hi + m) {
    const d = levelData(lv, sub[0].time, sub[sub.length - 1].time); if (!d.length) continue;
    tc.addSeries(LW.LineSeries, {color: lv.color, lineWidth: 1, lineStyle: LW.LineStyle.Dashed, priceLineVisible: false,
      lastValueVisible: false, crosshairMarkerVisible: false, pointMarkersVisible: false, title: lv.id,
      autoscaleInfoProvider: () => null}).setData(d);
  }
  const ev = D.events.filter(e => e.time >= sub[0].time && e.time <= sub[sub.length - 1].time);
  LW.createSeriesMarkers(s, ev.map(e => ({time: e.time, position: e.where === 'high' ? 'aboveBar' : 'belowBar',
    color: e.color, shape: 'circle', text: e.id})));
  // mouvement en bord droit (dernières bougies) : on garde de l'air à droite pour le voir entier
  if (lack > 0) { tc.timeScale().applyOptions({rightOffset: lack}); tc.timeScale().setVisibleLogicalRange({from: -1, to: sub.length - 1 + lack}); }
  else tc.timeScale().fitContent();
  const cvs = box.querySelector('canvas.ov'), g = cvs.getContext('2d');
  const draw = () => {
    const w = cvs.clientWidth, h = cvs.clientHeight, dpr = window.devicePixelRatio || 1;
    cvs.width = w * dpr; cvs.height = h * dpr; g.setTransform(dpr, 0, 0, dpr, 0, 0); g.clearRect(0, 0, w, h);
    const x0 = tc.timeScale().timeToCoordinate(z.t0), x1 = tc.timeScale().timeToCoordinate(z.t1);
    const y0 = s.priceToCoordinate(z.hi), y1 = s.priceToCoordinate(z.lo);
    if (x0 == null || x1 == null || y0 == null || y1 == null) return;
    const bw = Math.max(tc.timeScale().options().barSpacing, 3);
    g.fillStyle = z.color + '26'; g.strokeStyle = z.color; g.lineWidth = 1.5;
    g.fillRect(x0 - bw / 2, y0 - 3, x1 - x0 + bw, y1 - y0 + 6); g.strokeRect(x0 - bw / 2, y0 - 3, x1 - x0 + bw, y1 - y0 + 6);
  };
  new ResizeObserver(() => requestAnimationFrame(draw)).observe(box);
  tc.timeScale().subscribeVisibleLogicalRangeChange(() => requestAnimationFrame(draw));
  tc.timeScale().subscribeSizeChange(() => requestAnimationFrame(draw));
  setTimeout(draw, 150);
  thumbs.push({tc, s});
});
function themeThumbs() {
  for (const {tc, s} of thumbs) {
    tc.applyOptions({layout: {background: {color: css('--bg')}, textColor: css('--muted')},
      grid: {vertLines: {visible: false}, horzLines: {color: css('--grid')}}});
    s.applyOptions({upColor: css('--up'), downColor: css('--down'), wickUpColor: css('--up'), wickDownColor: css('--down')});
  }
}
const _applyTheme = applyTheme;
applyTheme = function () { _applyTheme(); themeThumbs(); };

applyTheme(); drawMarkers(); paneHeights(); initialView(); legend(null);
</script>
</body>
</html>
"""


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def main(argv: list[str] | None = None) -> None:
    from . import data as data_mod
    from .events import Thresholds
    from .features import add_features
    from .window import detect_window_structure

    p = argparse.ArgumentParser(description="Graphe interactif HTML (analyse ↔ graphe)")
    p.add_argument("--symbol", default="BTC/USDT")
    p.add_argument("--timeframe", default="1h")
    p.add_argument("--limit", type=int, default=300)
    p.add_argument("--window", type=int, default=60, help="fenêtre de détection (barres)")
    p.add_argument("--notes", help="JSON d'annotations (niveaux, zones, événements, texte)")
    p.add_argument("--no-detect", action="store_true", help="n'afficher que les notes")
    p.add_argument("--oi-source", default="binance", choices=["binance", "okx", "agg3"])
    p.add_argument("--out", help="chemin du HTML (défaut : chart_<sym>_<tf>.html)")
    a = p.parse_args(argv)

    ex = data_mod.get_exchange("binance")
    df = add_features(data_mod.fetch_ohlcv(ex, a.symbol, a.timeframe, a.limit, use_cache=False))
    oi = data_mod.fetch_open_interest(a.symbol, a.timeframe, a.limit, source=a.oi_source)
    struct = None if a.no_detect else detect_window_structure(df, lookback=a.window, th=Thresholds(), oi=oi)
    oi_ohlc = data_mod.fetch_open_interest_ohlc(a.symbol, a.timeframe, a.limit, source=a.oi_source,
                                                start=df.index[0], end=df.index[-1])
    notes = json.loads(Path(a.notes).read_text(encoding="utf-8")) if a.notes else None
    out = a.out or f"chart_{a.symbol.replace('/', '').lower()}_{a.timeframe}.html"
    build_interactive_html(a.symbol, a.timeframe, df, out, struct=struct, notes=notes, oi_ohlc=oi_ohlc)
    print(f"→ graphe interactif : {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
