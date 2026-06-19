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
                "BC": "#d62728", "SOW": "#d62728", "SPRING": "#9467bd", "UTAD": "#9467bd",
                "LPS": "#17a2b8", "LPSY": "#17a2b8"}


def _fmt_price(v: float) -> str:
    """Formate un prix selon sa magnitude (BTC à 62000 comme un alt à 0.0689)."""
    a = abs(v)
    if a >= 1000:
        return f"{v:,.0f}"
    if a >= 1:
        return f"{v:.2f}"
    if a >= 0.01:
        return f"{v:.4f}"
    return f"{v:.6f}"

# Pour chaque événement : sur quel extrême de barre poser le marqueur ("low"/"high").
# SC→creux (plancher), AR→sommet du rebond (plafond), ST→re-test de la borne,
# SOS→sommet de la cassure. Miroir en distribution.
def _wanted_extreme(name: str, acc: bool) -> str:
    table = {
        "SC": "low", "BC": "high",
        "AR": "high" if acc else "low",
        "ST": "low" if acc else "high",
        "SOS": "high", "SOW": "low",
        "SPRING": "low", "UTAD": "high",   # pénétration sous/au-dessus de la borne
        "LPS": "low", "LPSY": "high",      # creux/sommet de la réaction (back-up)
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
    oi_source: str = "okx", oi_ohlc=None,
) -> str:
    """Dessine la structure `struct` détectée en `analysis_tf`, **dans la même TF** (bougies
    `analysis_tf`), sur l'intervalle couvert par les événements. Trois panneaux : cours,
    volume (avec moyenne + étiquettes d'événements) et Open Interest agrégé (bougies, **même
    TF que le cours**). Le panneau OI est omis si l'OI est indisponible."""
    ex = ex or data_mod.get_exchange("binance")
    df = data_mod.fetch_ohlcv(ex, symbol, analysis_tf, limit, use_cache=False)

    # bornes temporelles : du climax au dernier événement, avec un peu de marge
    ts = [e.ts for e in struct.events]
    span = max(ts) - min(ts)
    pad = span * 0.12 if span.total_seconds() else _TF_TD.get(analysis_tf, pd.Timedelta(hours=1)) * 3
    sub_utc = df.loc[min(ts) - pad: max(ts) + pad].copy()
    if len(sub_utc) < 3:
        sub_utc = df.iloc[-60:].copy()
    delta = pd.Timedelta(hours=tz_hours)
    sub = sub_utc.copy()
    sub.index = sub.index + delta

    from .features import add_features
    sub = add_features(sub)

    # Open Interest agrégé, BOUGIES À LA MÊME TF que le cours, sur la même fenêtre.
    if oi_ohlc is None:
        try:
            oi_ohlc = data_mod.fetch_open_interest_ohlc(
                symbol, analysis_tf, source=oi_source,
                start=sub_utc.index[0], end=sub_utc.index[-1])
        except Exception:
            oi_ohlc = None
    has_oi = oi_ohlc is not None and len(oi_ohlc) > 0
    if has_oi:
        oi_ohlc = oi_ohlc.copy()
        oi_ohlc.index = oi_ohlc.index + delta
        oi_ohlc = (oi_ohlc[(oi_ohlc.index >= sub.index[0]) & (oi_ohlc.index <= sub.index[-1])] / 1e9)
        has_oi = len(oi_ohlc) > 0

    x = mdates.date2num(sub.index.to_pydatetime())
    width = (x[1] - x[0]) * 0.7 if len(x) > 1 else 0.01
    if has_oi:
        fig, (axp, axv, axo) = plt.subplots(3, 1, figsize=(13.5, 9.2), sharex=True,
                                            gridspec_kw={"height_ratios": [3, 1, 1.4], "hspace": 0.06})
    else:
        fig, (axp, axv) = plt.subplots(2, 1, figsize=(13.5, 7.5), sharex=True,
                                       gridspec_kw={"height_ratios": [3, 1], "hspace": 0.06})
        axo = None
    panels = [axp, axv] + ([axo] if has_oi else [])
    fig.patch.set_facecolor("white")
    _candles(axp, sub, width)

    acc = struct.bias == "accumulation"
    ev = {e.name: e for e in struct.events}

    # Bougies même TF que les événements → marqueur posé sur l'extrême réel de LA barre.
    def locate(e):
        want = _wanted_extreme(e.name, acc)
        return (mdates.date2num((e.ts + delta).to_pydatetime()),
                e.bar_high if want == "high" else e.bar_low)

    pts = {name: locate(e) for name, e in ev.items()}

    # Bornes de la micro-plage : plancher = climax, plafond = AR (c'est l'AR qui le définit).
    # Sans AR détecté, on retombe sur l'extrême de la SÉQUENCE (post-climax) plutôt que sur
    # le haut/bas de fenêtre, qui pourrait inclure des prix d'avant le climax.
    if acc:
        floor, floor_lbl = ev["SC"].bar_low, "plancher (SC)"
        if "AR" in ev:
            ceil, ceil_lbl = ev["AR"].bar_high, "plafond (AR)"
        else:
            ceil, ceil_lbl = max(e.bar_high for e in struct.events), "plafond (séq.)"
    else:
        ceil, ceil_lbl = ev["BC"].bar_high, "plafond (BC)"
        if "AR" in ev:
            floor, floor_lbl = ev["AR"].bar_low, "plancher (AR)"
        else:
            floor, floor_lbl = min(e.bar_low for e in struct.events), "plancher (séq.)"
    line_col = "#1f77b4"  # bleu, pointillé, trait fin pour les deux bornes
    for yv, lbl in ((floor, floor_lbl), (ceil, ceil_lbl)):
        axp.axhline(yv, color=line_col, ls="--", lw=0.6, alpha=0.8)
        below = yv == floor
        # Prix de la borne en BLEU sur l'échelle (gouttière des ticks), aligné avec les
        # graduations noires existantes — même axe des prix.
        axp.annotate(_fmt_price(yv), xy=(0.0, yv), xycoords=axp.get_yaxis_transform(),
                     xytext=(-4, 0), textcoords="offset points", va="center", ha="right",
                     fontsize=8, weight="bold", color=line_col, clip_on=False)
        # Nom de la borne (plancher/plafond + source) à gauche DANS le graphe, côté ouvert
        # de la ligne, sur fond blanc pour ne pas chevaucher les bougies.
        axp.annotate(lbl, xy=(0.0, yv), xycoords=axp.get_yaxis_transform(),
                     xytext=(4, -2 if below else 2), textcoords="offset points",
                     va="top" if below else "bottom", ha="left", fontsize=8, color=line_col,
                     bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.7))

    # Marqueurs d'événements : rond + acronyme, légèrement écartés de la mèche pour
    # ne pas la chevaucher. Sommet → marqueur/label au-dessus ; creux → en dessous.
    yr = float(sub["high"].max() - sub["low"].min()) or 1.0
    gap = yr * 0.06
    for name, e in ev.items():
        xe, price = pts[name]
        col = _EVENT_COLOR.get(name, "#555")
        up = _wanted_extreme(name, acc) == "high"
        y = price + (gap if up else -gap)
        dy = 30 if up else -38
        # Trait vertical fin et discret, teinté de la couleur de l'événement (vert/bleu…),
        # identique sur tous les panneaux (cours/volume/OI) pour délimiter les phases.
        for axx in panels:
            axx.axvline(xe, color=col, ls=":", lw=0.7, alpha=0.4, zorder=0)
        axp.annotate(name, (xe, y), textcoords="offset points", xytext=(0, dy),
                     ha="center", fontsize=10, weight="bold", color=col,
                     arrowprops=dict(arrowstyle="-", color=col, lw=0.8))

    seq = " → ".join(e.name for e in struct.events)
    axp.set_title(f"{symbol} — structure {struct.bias.upper()} ({seq})  |  analyse {analysis_tf}, "
                  f"bougies {analysis_tf} ({tz_label})", fontsize=11, weight="bold")
    axp.set_ylabel("Prix"); axp.grid(True, alpha=0.2)
    # marge verticale pour que les marqueurs/étiquettes ne mordent pas le titre
    plo, phi = float(sub["low"].min()), float(sub["high"].max())
    axp.set_ylim(plo - (phi - plo) * 0.28, phi + (phi - plo) * 0.24)

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

    # Panneau Open Interest agrégé — bougies à la MÊME TF (vert = OI↑/positions ouvertes,
    # rouge = OI↓/positions fermées).
    if has_oi:
        xo = mdates.date2num(oi_ohlc.index.to_pydatetime())
        ow = (xo[1] - xo[0]) * 0.7 if len(xo) > 1 else width
        for xi, (_, r) in zip(xo, oi_ohlc.iterrows()):
            c = "#26a69a" if r["close"] >= r["open"] else "#ef5350"
            axo.vlines(xi, r["low"], r["high"], color=c, lw=0.8, zorder=1)
            lo, hi = sorted((r["open"], r["close"]))
            axo.add_patch(plt.Rectangle((xi - ow / 2, lo), ow, max(hi - lo, 1e-9),
                                        facecolor=c, edgecolor=c, zorder=2))
        olo, ohi = float(oi_ohlc["low"].min()), float(oi_ohlc["high"].max())
        axo.set_ylim(olo - (ohi - olo) * 0.12, ohi + (ohi - olo) * 0.12)
        axo.set_ylabel("OI agg. (Md$)"); axo.grid(True, alpha=0.2)
        # Composition affichée. Sur agg3 live, si l'archive Binance est périmée (J-1) elle
        # est exclue (fix #2) → on le signale ; sinon (okx) c'est la venue unique.
        label = "OI OKX (perp)" if oi_source == "okx" else f"OI {oi_source}"
        compo = f"{label} — vert=OI↑ (ouvertures) · rouge=OI↓ (fermetures)"
        if oi_source == "agg3":
            try:
                lag = data_mod.binance_oi_lag_hours(symbol)
            except Exception:
                lag = None
            if lag is None or lag > data_mod._ARCHIVE_MAX_LAG_H:
                compo += "  |  Binance archive périmée → direction = OKX live"
            else:
                compo += "  |  OKX + Binance"
        axo.annotate(compo, (0.5, 0.04), xycoords="axes fraction", ha="center",
                     fontsize=7, color="#666")

    panels[-1].xaxis.set_major_formatter(mdates.DateFormatter("%d/%m %Hh"))
    fig.autofmt_xdate(rotation=30)
    fig.savefig(out_path, dpi=130, bbox_inches="tight")
    plt.close(fig)
    return out_path
