"""bias.py — le biais HTF (1D / 4h) : direction, deux scénarios chiffrés, zones cibles.

Assemble uniquement ce qui a été **mesuré**, avec le poids que la mesure lui donne :

| Élément | Statut | Référence |
|---|---|---|
| Déviation de range reprise | mesuré (milieu atteint 55-70 % contre 17-32 % après une cassure installée), **instable sur BTC 2020-2023** | `research/structure_rules.md` |
| Acceptance au-delà d'une borne | mesuré — filtre de validité d'une cassure, pas signal de direction | idem |
| Extrême de range | mesuré — zone de réaction (avantage relatif), pas signal d'entrée | `research/three_taps.md` |
| Mèche de liquidation | mesuré — 50 % retesté avant le mouvement ~6 fois sur 10, fenêtre 8-13 bougies | `research/wick_rule.md` |
| Murs d'OI / carburant de liquidation | mesuré — murs 2/2 à ~1 %, côté du carburant 2 fois sur 3 | `research/liqmap_validation.md` |
| EMA 50, sur-extension, sentiment | **non mesuré** : affiché comme contexte, poids nul | — |

Les **bornes de range** peuvent être fournies (celles que l'analyste trace, comme CrypNuevo
dans chaque tweet) ou détectées automatiquement. La détection automatique est imparfaite —
elle ne retrouve ses bornes que deux fois sur sept — et le rapport le signale toujours.

Pur : des DataFrames entrent, un dict sort. Le chargement est dans `load_asof`.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from ..features import swing_points
from . import structure as S
from . import wick_study as WS

DEV_MEASURE = ("après une déviation reprise, le milieu du range est atteint dans 55 à 70 % "
               "des cas contre 17 à 32 % après une cassure installée ; règle instable sur "
               "BTC 2020-2023")
ACC_MEASURE = ("après une acceptance (2 clôtures), le prix est encore du bon côté 7 à 8,5 "
               "fois sur 10, contre 1,4 à 5 après une simple mèche ; filtre de validité, "
               "pas signal de direction")
EDGE_MEASURE = ("un extrême de range est une zone de réaction mesurée (rebond plus fréquent "
                "qu'ailleurs), pas un signal d'entrée")


# ===================================================================== bornes

@dataclass
class Bounds:
    """Bornes d'un range, en **zones** : un plancher n'est pas un prix mais une bande, du
    creux extrême au niveau le plus défendu (idem pour le plafond)."""
    floor: float
    ceiling: float
    floor_zone: tuple = None
    ceiling_zone: tuple = None
    source: str = "analyste"
    note: str = ""

    def __post_init__(self):
        if self.floor_zone is None:
            self.floor_zone = (self.floor, self.floor)
        if self.ceiling_zone is None:
            self.ceiling_zone = (self.ceiling, self.ceiling)

    @property
    def mid(self) -> float:
        return 0.5 * (self.floor + self.ceiling)

    def position(self, price: float) -> float:
        span = self.ceiling - self.floor
        return (price - self.floor) / span if span > 0 else float("nan")


def auto_bounds(df: pd.DataFrame, exclude: int = 7,
                windows=(60, 90, 120, 150, 180, 240, 300, 365), q: float = 0.25,
                tol: float = 0.025, max_slope: float = 0.35) -> "Bounds | None":
    """Bornes du range **courant**, détectées automatiquement (pur).

    Cherche la plus longue fenêtre récente (hors `exclude` dernières bougies, pour ne pas
    mesurer le range avec l'épisode qu'on veut juger) dont les clôtures restent
    horizontales (pente cumulée ≤ `max_slope` × largeur) et qui compte au moins trois
    touches de chaque côté. Plancher = zone allant du creux extrême au niveau le plus
    retouché du quart bas des clôtures ; plafond, symétrique.
    """
    best = None
    for lb in windows:
        if len(df) < lb + exclude:
            continue
        win = df.iloc[-(lb + exclude):-exclude] if exclude else df.tail(lb)
        sw = swing_points(win, 3, 3)
        c = win["close"]
        lows = sw.loc[sw["swing_low"] & (sw["low"] <= c.quantile(q)), "low"]
        highs = sw.loc[sw["swing_high"] & (sw["high"] >= c.quantile(1 - q)), "high"]
        if len(lows) < 3 or len(highs) < 3:
            continue
        bl = max(S.cluster_levels(lows, tol), key=lambda d: (d["touches"], -d["price"]))
        bh = max(S.cluster_levels(highs, tol), key=lambda d: (d["touches"], d["price"]))
        width = bh["price"] - bl["price"]
        if width <= 0:
            continue
        slope = np.polyfit(np.arange(len(win)), c.to_numpy(), 1)[0] * len(win)
        if abs(slope) > max_slope * width:
            continue
        best = Bounds(floor=bl["price"], ceiling=bh["price"],
                      floor_zone=(float(lows.min()), max(bl["price"], float(lows.min()))),
                      ceiling_zone=(min(bh["price"], float(highs.max())), float(highs.max())),
                      source="automatique", note=f"fenêtre {lb} bougies")
    return best


# ===================================================================== lecture d'un cadre

def read_frame(df: pd.DataFrame, b: Bounds, label: str, lookback: int = 30,
               min_closes: int = 2) -> dict:
    """État du prix par rapport aux bornes d'un cadre (pur).

    Renvoie la zone (`bas`, `milieu`, `haut`, `sous le range`, `au-dessus du range`), une
    éventuelle déviation (sortie puis reprise), une cassure installée (acceptance hors du
    range) et la contribution au score directionnel, avec sa justification.
    """
    tail = df.tail(lookback)
    price = float(df["close"].iloc[-1])
    out = {"cadre": label, "prix": price, "bornes": b, "position": b.position(price),
           "déviation": None, "cassure": None, "score": 0, "raisons": []}
    lo_edge, hi_edge = b.floor_zone[0], b.ceiling_zone[1]

    # On évalue les deux côtés, puis on ne retient que l'épisode le plus RÉCENT : un
    # franchissement du plafond fin octobre ne doit pas masquer la sortie sous le plancher
    # de la semaine (bug constaté sur le 22/11).
    episodes = []
    for side, mask, edge, ext_col in (
            ("bas", tail["low"] < lo_edge * 0.999, lo_edge, "low"),
            ("haut", tail["high"] > hi_edge * 1.001, hi_edge, "high")):
        if not mask.any():
            continue
        idx = np.flatnonzero(mask.to_numpy())
        last = int(idx[-1])
        start = last
        for k in range(len(idx) - 1, 0, -1):         # épisode contigu (trou d'au plus 2)
            if idx[k] - idx[k - 1] <= 3:
                start = int(idx[k - 1])
            else:
                break
        episodes.append((last, side, edge, ext_col, start))
    if episodes:
        last, side, edge, ext_col, start = max(episodes, key=lambda e: e[0])
        seg = tail.iloc[start:]
        # Une déviation dont la cible (le milieu du range) a déjà été atteinte après
        # l'extrême est ACCOMPLIE : ce n'est plus un signal. Sans ce garde-fou, la sortie
        # au-dessus du plafond de fin octobre restait « active » le 15/11, alors que le
        # prix était descendu de 82k à 62k en traversant le milieu.
        after = seg.iloc[int(np.argmin(seg[ext_col].to_numpy()) if side == "bas"
                             else np.argmax(seg[ext_col].to_numpy())):]
        reached_mid = bool((after["high"] >= b.mid).any() if side == "bas"
                           else (after["low"] <= b.mid).any())
        if reached_mid and not (side == "bas" and price < edge) \
                and not (side == "haut" and price > edge):
            out["déviation_accomplie"] = side
            episodes = []
    if episodes:
        ext = float(seg[ext_col].min() if side == "bas" else seg[ext_col].max())
        if side == "bas":
            broke = S.acceptance(seg, edge, "below", min_closes=min_closes, lookback=len(seg))
            if broke["accepted"] and price < edge:
                out["cassure"] = {"sens": "baissière", "niveau": edge, "extrême": ext}
            elif price > edge:
                acc = S.acceptance(df.tail(10), b.floor_zone[1], "above", min_closes=min_closes)
                out["déviation"] = {"côté": "sous le plancher", "extrême": ext,
                                    "profondeur": edge / ext - 1.0, "reprise": True,
                                    "acceptance": acc["accepted"],
                                    "seuil_acceptance": b.floor_zone[1]}
        else:
            broke = S.acceptance(seg, edge, "above", min_closes=min_closes, lookback=len(seg))
            if broke["accepted"] and price > edge:
                out["cassure"] = {"sens": "haussière", "niveau": edge, "extrême": ext}
            elif price < edge:
                acc = S.acceptance(df.tail(10), b.ceiling_zone[0], "below", min_closes=min_closes)
                out["déviation"] = {"côté": "au-dessus du plafond", "extrême": ext,
                                    "profondeur": ext / edge - 1.0, "reprise": True,
                                    "acceptance": acc["accepted"],
                                    "seuil_acceptance": b.ceiling_zone[0]}

    w = 2 if label == "1D" else 1
    pos = out["position"]
    if out["cassure"]:
        sgn = 1 if out["cassure"]["sens"] == "haussière" else -1
        out["zone"] = "au-dessus du range" if sgn > 0 else "sous le range"
        out["score"] += sgn * w
        out["raisons"].append(f"{label} : cassure {out['cassure']['sens']} acceptée "
                              f"({out['cassure']['niveau']:,.0f}) — {ACC_MEASURE}")
    elif out["déviation"]:
        sgn = 1 if out["déviation"]["côté"] == "sous le plancher" else -1
        out["zone"] = "bas" if sgn > 0 else "haut"
        out["score"] += sgn * w
        out["raisons"].append(
            f"{label} : déviation {out['déviation']['côté']} jusqu'à "
            f"{out['déviation']['extrême']:,.0f}, reprise — {DEV_MEASURE}")
    else:
        out["zone"] = ("bas" if pos <= 0.2 else "haut" if pos >= 0.8 else "milieu")
        if out["zone"] == "bas":
            out["score"] += 1
            out["raisons"].append(f"{label} : prix dans la zone du plancher — {EDGE_MEASURE}")
        elif out["zone"] == "haut":
            out["score"] -= 1
            out["raisons"].append(f"{label} : prix dans la zone du plafond — {EDGE_MEASURE}")
        else:
            out["raisons"].append(f"{label} : prix au milieu du range, pas d'avantage mesuré "
                                  "(« nothing to do at mid-range »)")
    return out


# ===================================================================== mèches de liquidation

def liquidation_wicks(df: pd.DataFrame, tf: str, liq_daily: "pd.DataFrame | None",
                      recent: int = 13) -> list:
    """Longues mèches des `recent` dernières bougies, qualifiées par la règle validée."""
    if df is None or len(df) < 30:
        return []
    wk = WS.detect_wicks(df.tail(200), min_atr=WS.RULE_MIN_ATR)
    if wk.empty:
        return []
    start = len(df.tail(200)) - recent
    out = []
    for w in wk[wk["i"] >= start].itertuples():
        lr = WS.liq_rel(liq_daily, w.at, w.direction) if liq_daily is not None else float("nan")
        c = WS.classify_wick(w.size_atr, lr, w.direction)
        age = len(df.tail(200)) - 1 - w.i
        touched = (df.loc[df.index > w.at, "low"] <= w.half).any() if w.direction == "basse" \
            else (df.loc[df.index > w.at, "high"] >= w.half).any()
        if tf == "1d" and c.get("attendu"):
            c = {**c, "note": c["note"] + " — ATTENTION : règle validée en 1h et 4h seulement, "
                 "les effectifs 1D étaient trop faibles pour conclure."}
        out.append({"tf": tf, "at": w.at, "direction": w.direction, "tip": w.tip,
                    "half": w.half, "size_atr": w.size_atr, "liq_rel": lr, "âge": age,
                    "retestée": bool(touched), "validée": tf in ("1h", "4h"), **c})
    return out


# ===================================================================== synthèse

@dataclass
class Report:
    asof: pd.Timestamp
    price: float
    bias: str
    score: int
    conviction: str
    frames: list
    scenarios: list
    zones: list
    wicks: list = field(default_factory=list)
    context: dict = field(default_factory=dict)
    alerts: list = field(default_factory=list)


def _conviction(score: int) -> str:
    a = abs(score)
    return "forte" if a >= 4 else "moyenne" if a == 3 else "faible" if a == 2 else "aucune"


def assess(d1: pd.DataFrame, h4: pd.DataFrame, h1: "pd.DataFrame | None" = None,
           bounds_1d: "Bounds | None" = None, bounds_4h: "Bounds | None" = None,
           liq_daily: "pd.DataFrame | None" = None, liqmap: "dict | None" = None,
           asof=None) -> Report:
    """Biais HTF à partir de données déjà figées à `asof` (pur)."""
    price = float(h4["close"].iloc[-1]) if h4 is not None and len(h4) else float(d1["close"].iloc[-1])
    b1 = bounds_1d or auto_bounds(d1)
    b4 = bounds_4h or auto_bounds(h4, exclude=12, windows=(120, 180, 240, 360, 480, 720))
    frames = []
    if b1:
        frames.append(read_frame(d1, b1, "1D", lookback=30))
    if b4:
        frames.append(read_frame(h4, b4, "4h", lookback=60))
    score = int(sum(f["score"] for f in frames))
    bias = "haussier" if score >= 2 else "baissier" if score <= -2 else "neutre"

    # L'acceptance d'un déclencheur se lit en clôtures 4h (plus réactives que le 1D).
    for f in frames:
        dv = f.get("déviation")
        if dv and h4 is not None and len(h4):
            side = "above" if dv["côté"] == "sous le plancher" else "below"
            dv["acceptance"] = S.acceptance(h4.tail(12), dv["seuil_acceptance"], side,
                                            min_closes=2)["accepted"]

    wicks = (liquidation_wicks(d1, "1d", liq_daily, recent=5)
             + liquidation_wicks(h4, "4h", liq_daily)
             + (liquidation_wicks(h1, "1h", liq_daily) if h1 is not None else []))

    # ---- zones cibles, chacune justifiée
    zones = []
    if b1:
        zones += [{"prix": b1.floor, "zone": b1.floor_zone, "raison": f"plancher du range 1D ({b1.source})"},
                  {"prix": b1.mid, "zone": None, "raison": "milieu du range 1D (cible d'une déviation reprise)"},
                  {"prix": b1.ceiling, "zone": b1.ceiling_zone, "raison": f"plafond du range 1D ({b1.source})"}]
    if b4 and b1 and (abs(b4.floor / b1.floor - 1) > 0.01 or abs(b4.ceiling / b1.ceiling - 1) > 0.01):
        zones += [{"prix": b4.floor, "zone": b4.floor_zone, "raison": f"plancher du sous-range 4h ({b4.source})"},
                  {"prix": b4.ceiling, "zone": b4.ceiling_zone, "raison": f"plafond du sous-range 4h ({b4.source})"}]
    for f in frames:
        if f["déviation"]:
            zones.append({"prix": f["déviation"]["extrême"], "zone": None,
                          "raison": f"extrême de la déviation {f['cadre']} (invalidation du scénario de reprise)"})
    for w in wicks:
        if w.get("attendu") and not w["retestée"]:
            stat = (f"retest d'abord ~{w['taux']:.0%} des cas contre {w['témoin']:.0%}, "
                    f"fenêtre 8 à 13 bougies" if w["validée"]
                    else "règle non validée en 1D (effectifs trop faibles)")
            zones.append({"prix": w["half"], "zone": None,
                          "raison": (f"50 % d'une mèche de liquidation {w['tf']} ({w['direction']}, "
                                     f"liquidations {w['liq_rel']:.1f}x) : {stat} (âge {w['âge']} bougies)")})
    if liqmap:
        from . import liqmap as LM
        g = liqmap["grid"]
        for r in LM.clusters(g, liqmap["positions"], top_n=2).itertuples():
            zones.append({"prix": r.peak, "zone": (r.low, r.high),
                          "raison": "mur de positions ouvertes (murs 2/2 à ~1 % sur les cartes Hyblock)"})
    zones = sorted(zones, key=lambda z: z["prix"])

    # ---- scénarios
    scen = _scenarios(price, frames, b1, b4, bias)

    # ---- contexte non mesuré
    ctx = {"EMA 50 1D": S.ema_state(d1), "statut": "non mesuré — contexte, poids nul"}

    # ---- alertes
    alerts = []
    for f in frames:
        if f["déviation"] and f["déviation"]["côté"] == "sous le plancher":
            alerts.append(f"{f['cadre']} : déviation sous le plancher en cours — ne pas vendre la "
                          "cassure tant qu'il n'y a pas d'acceptance sous "
                          f"{f['bornes'].floor_zone[0]:,.0f} (erreur du 22/11)")
        if f["déviation"] and f["déviation"]["côté"] == "au-dessus du plafond":
            alerts.append(f"{f['cadre']} : déviation au-dessus du plafond en cours — ne pas acheter "
                          f"la cassure sans acceptance au-dessus de {f['bornes'].ceiling_zone[1]:,.0f}")
    if any(b and b.source == "automatique" for b in (b1, b4)):
        alerts.append("bornes détectées automatiquement : à confronter aux bornes tracées "
                      "(la détection ne retrouve celles de CrypNuevo que 2 fois sur 7)")
    return Report(asof=pd.Timestamp(asof) if asof is not None else d1.index[-1], price=price,
                  bias=bias, score=score, conviction=_conviction(score), frames=frames,
                  scenarios=scen, zones=zones, wicks=wicks, context=ctx, alerts=alerts)


def _scenarios(price: float, frames: list, b1: "Bounds | None", b4: "Bounds | None",
               bias: str) -> list:
    """Deux scénarios opposés, chiffrés : déclencheur (acceptance), cibles, invalidation."""
    if not b1:
        return []
    f1 = next((f for f in frames if f["cadre"] == "1D"), None)
    dev = f1["déviation"] if f1 else None

    def trig(level, side):
        return f"acceptance (2 clôtures 4h) {'au-dessus de' if side == 'up' else 'sous'} {level:,.0f}"

    if dev and dev["côté"] == "sous le plancher":
        up_t = dev["seuil_acceptance"]
        up_trig = trig(up_t, "up") + (" — acquise" if dev["acceptance"] else " — à obtenir")
        up_inval = dev["extrême"]
    else:
        up_t = next((x for x in sorted({b1.floor_zone[1], b1.mid, b1.ceiling_zone[1]}
                                       | ({b4.ceiling} if b4 else set())) if x > price),
                    b1.ceiling_zone[1])
        up_trig, up_inval = trig(up_t, "up"), b1.floor_zone[0]
    if dev and dev["côté"] == "au-dessus du plafond":
        dn_t = dev["seuil_acceptance"]
        dn_trig = trig(dn_t, "dn") + (" — acquise" if dev["acceptance"] else " — à obtenir")
        dn_inval = dev["extrême"]
    else:
        dn_t = next((x for x in sorted({b1.ceiling_zone[0], b1.mid, b1.floor_zone[0]}
                                       | ({b4.floor} if b4 else set()), reverse=True) if x < price),
                    b1.floor_zone[0])
        dn_trig, dn_inval = trig(dn_t, "dn"), b1.ceiling_zone[1]
    up = {"nom": "haussier", "déclencheur": up_trig,
          "cibles": [t for t in (b1.mid, b1.ceiling) if t > max(price, up_t) * 1.005],
          "invalidation": f"acceptance sous {up_inval:,.0f}"}
    dn = {"nom": "baissier", "déclencheur": dn_trig,
          "cibles": [t for t in (b1.mid, b1.floor) if t < min(price, dn_t) * 0.995]
                    or ["sous le range : pas de cible mesurée"],
          "invalidation": f"acceptance au-dessus de {dn_inval:,.0f}"}
    return [up, dn] if bias != "baissier" else [dn, up]


# ===================================================================== rendu texte

def to_text(r: Report) -> str:
    """Rendu tabulaire strict, niveaux toujours justifiés (préférences de Gauthier)."""
    from ..clock import fmt, label
    lines = [f"Biais HTF BTC — {fmt(r.asof)} {label(r.asof)} — prix {r.price:,.0f}",
             f"Biais : {r.bias} (score {r.score:+d}, conviction {r.conviction})", ""]
    lines.append("| Cadre | Bornes | Position | Lecture |")
    lines.append("|---|---|---|---|")
    for f in r.frames:
        b = f["bornes"]
        lines.append(f"| {f['cadre']} | {b.floor:,.0f} – {b.ceiling:,.0f} ({b.source}) | "
                     f"{f['zone']} ({f['position']:.0%}) | {' ; '.join(f['raisons'])} |")
    lines += ["", "| Scénario | Déclencheur | Cibles | Invalidation |", "|---|---|---|---|"]
    for s in r.scenarios:
        cib = " puis ".join(c if isinstance(c, str) else f"{c:,.0f}" for c in s["cibles"]) or "-"
        lines.append(f"| {s['nom']} | {s['déclencheur']} | {cib} | {s['invalidation']} |")
    lines += ["", "Zones :"] + [f"- {z['prix']:,.0f} ({z['raison']})" for z in r.zones]
    if r.alerts:
        lines += ["", "Alertes :"] + [f"- {a}" for a in r.alerts]
    return "\n".join(lines)


# ===================================================================== chargement figé

def load_asof(asof, symbol: str = "BTC/USDT", with_liq: bool = True) -> dict:
    """Données figées à `asof` : seules les bougies **clôturées** avant `asof` entrent."""
    from .. import data as D
    asof = pd.Timestamp(asof)
    if asof.tzinfo is None:
        asof = asof.tz_localize("UTC")
    out = {}
    for tf, dur in (("1d", "1D"), ("4h", "4h"), ("1h", "1h")):
        df = WS.load(symbol, tf, "2020-01-01")
        out[tf] = df[df.index + pd.Timedelta(dur) <= asof]
    out["liq"] = None
    if with_liq:
        liq = D.fetch_liquidations(symbol, "1d", start=pd.Timestamp("2020-01-01", tz="UTC"),
                                   end=asof)
        if liq is not None:
            # journées closes seulement : la valeur quotidienne du jour en cours inclut des
            # liquidations postérieures à `asof` (ce serait regarder le futur). Une mèche du
            # jour même sort donc « liquidations inconnues », ce qui est honnête.
            out["liq"] = liq[liq.index + pd.Timedelta("1D") <= asof]
    return out
