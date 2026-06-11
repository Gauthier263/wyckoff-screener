"""
plot.py — Rendu graphique des structures détectées.

Convention demandée : on détecte la structure sur la TF d'analyse, mais on dessine
les bougies sur une **TF inférieure** pour plus de détail (H4→H1, H1→15m, 15m→5m).
Le graphique est sauvé en PNG ; la couche appelante l'embarque inline.
"""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

from . import data as data_mod
from .window import WindowStructure

# TF d'analyse -> TF de dessin des bougies (plus fine)
FINER_TF = {"1d": "4h", "4h": "1h", "1h": "15m", "30m": "5m", "15m": "5m", "5m": "1m"}

# Durée d'une barre d'analyse (pour retrouver l'extrême réel dans les bougies fines)
_TF_TD = {"1d": pd.Timedelta(days=1), "4h": pd.Timedelta(hours=4), "1h": pd.Timedelta(hours=1),
          "30m": pd.Timedelta(minutes=30), "15m": pd.Timedelta(minutes=15),
          "5m": pd.Timedelta(minutes=5)}

_EVENT_COLOR = {"SC": "#2ca02c", "SOS": "#2ca02c", "AR": "#1f77b4", "ST": "#1f77b4",
                "BC": "#d62728", "SOW": "#d62728"}

# Pour chaque événement : sur quel extrême de barre poser le marqueur ("low"/"high").
# SC→creux (plancher), AR→sommet du rebond (plafond), ST→re-test de la borne,
# SOS→sommet de la cassure. Miroir en distribution.
def _wanted_extreme(name: str, acc: bool) -> str:
    table = {
        "SC": "low", "BC": "high",
        "AR": "high" if acc else "low",
        "ST": "low" if acc else "high",
        "SOS": "high", "SOW": "low",
    }
    return table.get(name, "low")


def _candles(ax, df, width):
    x = mdates.date2num(df.index.to_pydatetime())
    for xi, (_, r) in zip(x, df.iterrows()):
        up = r["close"] >= r["open"]
        c = "#26a69a" if up else "#ef5350"
        ax.vlines(xi, r["low"], r["high"], color=c, linewidth=0.7, zorder=1)
        lo, hi = sorted((r["open"], r["close"]))
        ax.add_patch(plt.Rectangle((xi - width / 2, lo), width, max(hi - lo, 1e-9),
                                   facecolor=c, edgecolor=c, zorder=2))
    return x


def plot_window_structure(
    symbol: str, analysis_tf: str, struct: WindowStructure, out_path: str,
    ex=None, tz_hours: int = 2, tz_label: str = "CEST", limit: int = 1000,
) -> str:
    """Dessine la structure `struct` (détectée en `analysis_tf`) avec des bougies en
    TF inférieure, sur l'intervalle couvert par les événements."""
    fine_tf = FINER_TF.get(analysis_tf, analysis_tf)
    ex = ex or data_mod.get_exchange("binance")
    fine = data_mod.fetch_ohlcv(ex, symbol, fine_tf, limit, use_cache=False)

    # bornes temporelles : du climax au dernier événement, avec un peu de marge
    ts = [e.ts for e in struct.events]
    span = max(ts) - min(ts)
    pad = span * 0.12 if span.total_seconds() else pd.Timedelta(hours=2)
    sub = fine.loc[min(ts) - pad: max(ts) + pad].copy()
    if len(sub) < 3:
        sub = fine.iloc[-60:].copy()
    sub.index = sub.index + pd.Timedelta(hours=tz_hours)

    from .features import add_features
    sub = add_features(sub)

    x = mdates.date2num(sub.index.to_pydatetime())
    width = (x[1] - x[0]) * 0.7 if len(x) > 1 else 0.01
    fig, (axp, axv) = plt.subplots(2, 1, figsize=(13, 7.5), sharex=True,
                                   gridspec_kw={"height_ratios": [3, 1], "hspace": 0.05})
    fig.patch.set_facecolor("white")
    _candles(axp, sub, width)

    acc = struct.bias == "accumulation"
    ev = {e.name: e for e in struct.events}
    td = _TF_TD.get(analysis_tf, pd.Timedelta(hours=1))
    delta = pd.Timedelta(hours=tz_hours)

    # Place chaque marqueur sur l'extrême RÉEL de la barre d'analyse, retrouvé dans
    # les bougies fines couvrant la période [ts, ts+td) -> alignement exact creux/cassure.
    def locate(e):
        want = _wanted_extreme(e.name, acc)
        start = e.ts + delta
        seg = sub.loc[start: start + td - pd.Timedelta(seconds=1)]
        if len(seg) == 0:
            return mdates.date2num(start.to_pydatetime()), (e.bar_low if want == "low" else e.bar_high)
        if want == "low":
            t, price = seg["low"].idxmin(), float(seg["low"].min())
        else:
            t, price = seg["high"].idxmax(), float(seg["high"].max())
        return mdates.date2num(t.to_pydatetime()), price

    pts = {name: locate(e) for name, e in ev.items()}

    # Bornes de la micro-plage : plancher = climax, plafond = AR (c'est l'AR qui le définit).
    if acc:
        floor = ev["SC"].bar_low
        ceil = ev["AR"].bar_high if "AR" in ev else struct.high
        floor_lbl, ceil_lbl = "plancher (SC)", "plafond (AR)"
    else:
        ceil = ev["BC"].bar_high
        floor = ev["AR"].bar_low if "AR" in ev else struct.low
        floor_lbl, ceil_lbl = "plancher (AR)", "plafond (BC)"
    line_col = "#1f77b4"  # bleu, pointillé, trait fin pour les deux bornes
    for yv, lbl in ((floor, floor_lbl), (ceil, ceil_lbl)):
        axp.axhline(yv, color=line_col, ls="--", lw=0.6, alpha=0.8)
        # Étiquette posée hors de l'aire de tracé (bord droit) : ne chevauche jamais
        # les bougies ni les mèches.
        axp.annotate(f"{lbl} {yv:.0f}", xy=(1.0, yv), xycoords=axp.get_yaxis_transform(),
                     xytext=(6, 0), textcoords="offset points", va="center", ha="left",
                     fontsize=8, color=line_col, clip_on=False)

    # Marqueurs d'événements : rond + acronyme, légèrement écartés de la mèche pour
    # ne pas la chevaucher. Sommet → marqueur/label au-dessus ; creux → en dessous.
    yr = float(sub["high"].max() - sub["low"].min()) or 1.0
    gap = yr * 0.04
    for name, e in ev.items():
        xe, price = pts[name]
        col = _EVENT_COLOR.get(name, "#555")
        up = _wanted_extreme(name, acc) == "high"
        y = price + (gap if up else -gap)
        axp.scatter([xe], [y], s=150, facecolor="none", edgecolor=col, lw=1.2, zorder=6)
        dy = 22 if up else -30
        axp.annotate(name, (xe, y), textcoords="offset points", xytext=(0, dy),
                     ha="center", fontsize=10, weight="bold", color=col,
                     arrowprops=dict(arrowstyle="-", color=col, lw=0.8))

    seq = " → ".join(e.name for e in struct.events)
    axp.set_title(f"{symbol} — structure {struct.bias.upper()} ({seq})  |  analyse {analysis_tf}, "
                  f"bougies {fine_tf} ({tz_label})", fontsize=11, weight="bold")
    axp.set_ylabel("Prix"); axp.grid(True, alpha=0.2)
    # marge verticale pour que les marqueurs/étiquettes ne mordent pas le titre
    plo, phi = float(sub["low"].min()), float(sub["high"].max())
    axp.set_ylim(plo - (phi - plo) * 0.20, phi + (phi - plo) * 0.16)

    # Volume + étiquettes d'événements pour repérage
    bc = ["#ef5350" if c < o else "#26a69a" for o, c in zip(sub["open"], sub["close"])]
    axv.bar(x, sub["volume"].values, width=width, color=bc, alpha=0.6)
    axv.plot(x, sub["vol_ma"].values, color="#555", lw=0.8, label="vol MA")
    vmax = float(sub["volume"].max())
    vol_arr = sub["volume"].values
    for name, e in ev.items():
        xe, _ = pts[name]
        col = _EVENT_COLOR.get(name, "#555")
        # Ancre l'étiquette juste au-dessus de SA barre (pas du sommet commun) : les
        # événements à faible volume descendent et se décollent du trait noir (vol MA).
        i = int((abs(x - xe)).argmin())
        bar_y = float(vol_arr[i])
        axv.annotate(f"{name}\n×{e.vol_ratio:.1f}", (xe, bar_y), textcoords="offset points",
                     xytext=(0, 10), ha="center", va="bottom", fontsize=7.5, weight="bold", color=col)
    axv.set_ylim(0, vmax * 1.42)
    axv.set_ylabel("Volume"); axv.grid(True, alpha=0.2); axv.legend(fontsize=7, loc="upper left")
    axv.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m %Hh"))
    fig.autofmt_xdate(rotation=30)
    fig.savefig(out_path, dpi=130, bbox_inches="tight")
    plt.close(fig)
    return out_path
