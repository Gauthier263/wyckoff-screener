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
    axp.axhline(floor, color="#2ca02c", ls="--", lw=1.0, alpha=0.85)
    axp.text(x[0], floor, f" {floor_lbl} {floor:.0f}", va="bottom", fontsize=8, color="#1b6b1b")
    axp.axhline(ceil, color="#b08900", ls="-", lw=1.0, alpha=0.85)
    axp.text(x[0], ceil, f" {ceil_lbl} {ceil:.0f}", va="bottom", fontsize=8, color="#7a5c00")

    # Marqueurs d'événements + lignes-guides verticales (price <-> volume)
    for name, e in ev.items():
        xe, price = pts[name]
        col = _EVENT_COLOR.get(name, "#555")
        axp.axvline(xe, color=col, lw=0.6, alpha=0.25, zorder=0)
        axp.scatter([xe], [price], s=150, facecolor="none", edgecolor=col, lw=2.2, zorder=6)
        dy = 20 if name in ("AR", "SOS", "SOW") else -36
        axp.annotate(name, (xe, price), textcoords="offset points", xytext=(0, dy),
                     ha="center", fontsize=10, weight="bold", color=col,
                     arrowprops=dict(arrowstyle="-", color=col, lw=0.8))

    seq = " → ".join(e.name for e in struct.events)
    axp.set_title(f"{symbol} — structure {struct.bias.upper()} ({seq})  |  analyse {analysis_tf}, "
                  f"bougies {fine_tf} ({tz_label})", fontsize=11, weight="bold")
    axp.set_ylabel("Prix"); axp.grid(True, alpha=0.2)
    # marge verticale pour que les marqueurs/étiquettes ne mordent pas le titre
    plo, phi = float(sub["low"].min()), float(sub["high"].max())
    axp.set_ylim(plo - (phi - plo) * 0.08, phi + (phi - plo) * 0.10)

    # Volume + étiquettes d'événements pour repérage
    bc = ["#ef5350" if c < o else "#26a69a" for o, c in zip(sub["open"], sub["close"])]
    axv.bar(x, sub["volume"].values, width=width, color=bc, alpha=0.6)
    axv.plot(x, sub["vol_ma"].values, color="#555", lw=0.8, label="vol MA")
    vmax = float(sub["volume"].max())
    for name, e in ev.items():
        xe, _ = pts[name]
        col = _EVENT_COLOR.get(name, "#555")
        axv.axvline(xe, color=col, lw=0.6, alpha=0.25, zorder=0)
        axv.annotate(f"{name}\n×{e.vol_ratio:.1f}", (xe, vmax), textcoords="offset points",
                     xytext=(0, 4), ha="center", va="bottom", fontsize=7.5, weight="bold", color=col)
    axv.set_ylim(0, vmax * 1.28)
    axv.set_ylabel("Volume"); axv.grid(True, alpha=0.2); axv.legend(fontsize=7, loc="upper left")
    axv.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m %Hh"))
    fig.autofmt_xdate(rotation=30)
    fig.savefig(out_path, dpi=130, bbox_inches="tight")
    plt.close(fig)
    return out_path


def plot_double_divergence(
    symbol: str, analysis_tf: str, res, out_path: str,
    ex=None, tz_hours: int = 2, tz_label: str = "CEST", limit: int = 1000,
    rsi_period: int = 14,
) -> str:
    """Rendu d'un setup double creux/sommet + divergence RSI (`res` = DoubleDivergence).

    Panneau prix : bougies en TF inférieure (`FINER_TF`), bornes du double creux/sommet,
    ligne de cou, et la *droite des extrêmes* reliant les deux pivots. Panneau RSI :
    RSI de la TF d'analyse + la **droite de divergence** reliant le RSI des deux pivots
    (montante = haussière, descendante = baissière) — la preuve visuelle de la thèse.
    """
    from .features import add_features

    fine_tf = FINER_TF.get(analysis_tf, analysis_tf)
    ex = ex or data_mod.get_exchange("binance")
    fine = data_mod.fetch_ohlcv(ex, symbol, fine_tf, limit, use_cache=False)
    coarse = data_mod.fetch_ohlcv(ex, symbol, analysis_tf, limit, use_cache=False)
    coarse = add_features(coarse, rsi_period=rsi_period)

    acc = res.bias == "accumulation"
    td = _TF_TD.get(analysis_tf, pd.Timedelta(hours=1))
    delta = pd.Timedelta(hours=tz_hours)

    # ts du climax retrouvé via bars_ago (mesuré depuis la dernière barre)
    ci = max(0, len(coarse) - 1 - int(res.climax_bars_ago))
    climax_ts = coarse.index[ci]
    p1_ts, p2_ts = res.p1.ts, res.p2.ts
    key_ts = [climax_ts, p1_ts, p2_ts]

    span = max(key_ts) - min(key_ts)
    pad = span * 0.18 if span.total_seconds() else td * 5
    t0, t1 = min(key_ts) - pad, max(key_ts) + pad + td * 3  # marge après le 2e pivot

    sub = fine.loc[t0:t1].copy()
    if len(sub) < 3:
        sub = fine.iloc[-80:].copy()
    sub.index = sub.index + delta
    sub = add_features(sub)
    csub = coarse.loc[t0:t1].copy()
    csub.index = csub.index + delta

    x = mdates.date2num(sub.index.to_pydatetime())
    width = (x[1] - x[0]) * 0.7 if len(x) > 1 else 0.01
    fig, (axp, axr) = plt.subplots(2, 1, figsize=(13, 7.5), sharex=True,
                                   gridspec_kw={"height_ratios": [3, 1.3], "hspace": 0.05})
    fig.patch.set_facecolor("white")
    _candles(axp, sub, width)

    # Recale chaque pivot sur l'extrême RÉEL de la barre d'analyse, dans les bougies fines.
    want = "low" if acc else "high"

    def locate(ts):
        start = ts + delta
        seg = sub.loc[start: start + td - pd.Timedelta(seconds=1)]
        if len(seg) == 0:
            return mdates.date2num(start.to_pydatetime()), None
        if want == "low":
            t, price = seg["low"].idxmin(), float(seg["low"].min())
        else:
            t, price = seg["high"].idxmax(), float(seg["high"].max())
        return mdates.date2num(t.to_pydatetime()), price

    xc, pc = locate(climax_ts); pc = pc if pc is not None else res.climax_price
    x1, pr1 = locate(p1_ts);    pr1 = pr1 if pr1 is not None else res.p1.price
    x2, pr2 = locate(p2_ts);    pr2 = pr2 if pr2 is not None else res.p2.price

    col_c = "#2ca02c" if acc else "#d62728"
    # ligne de cou
    axp.axhline(res.neckline, color="#b08900", ls="-", lw=1.0, alpha=0.85)
    axp.text(x[0], res.neckline, f" ligne de cou {res.neckline:.4g}", va="bottom",
             fontsize=8, color="#7a5c00")
    # droite reliant les deux extrêmes (le « double » au niveau du prix)
    axp.plot([x1, x2], [pr1, pr2], color="#1f77b4", ls="--", lw=1.5, alpha=0.9, zorder=5)
    lbl1, lbl2 = ("creux 1", "creux 2") if acc else ("sommet 1", "sommet 2")
    # quand le climax tient sur la même barre que le 1er pivot, on fusionne les marqueurs
    same = climax_ts == p1_ts
    markers = [(x2, pr2, lbl2, "#1f77b4")]
    if same:
        markers.insert(0, (xc, pc, f"{res.climax} ({lbl1})", col_c))
    else:
        markers.insert(0, (x1, pr1, lbl1, "#1f77b4"))
        markers.insert(0, (xc, pc, res.climax, col_c))
    dy = 18 if not acc else -34
    for xx, pp, lab, c in markers:
        axp.scatter([xx], [pp], s=150, facecolor="none", edgecolor=c, lw=2.2, zorder=6)
        axp.annotate(lab, (xx, pp), textcoords="offset points", xytext=(0, dy), ha="center",
                     fontsize=9, weight="bold", color=c,
                     arrowprops=dict(arrowstyle="-", color=c, lw=0.8))

    forming = "en formation" if res.is_forming else "ligne de cou cassée"
    axp.set_title(f"{symbol} — {res.pattern.upper()} + divergence RSI "
                  f"{('haussière' if acc else 'baissière')} ({forming})  |  analyse "
                  f"{analysis_tf}, bougies {fine_tf} ({tz_label})", fontsize=11, weight="bold")
    axp.set_ylabel("Prix"); axp.grid(True, alpha=0.2)
    plo, phi = float(sub["low"].min()), float(sub["high"].max())
    # marge généreuse du côté des pivots pour que les étiquettes ne soient pas rognées
    bot = 0.18 if acc else 0.08
    top = 0.10 if acc else 0.18
    axp.set_ylim(plo - (phi - plo) * bot, phi + (phi - plo) * top)

    # --- Panneau RSI (TF d'analyse) + droite de divergence ---
    xr = mdates.date2num(csub.index.to_pydatetime())
    axr.plot(xr, csub["rsi"].values, color="#6a3d9a", lw=1.1, label=f"RSI({rsi_period})")
    axr.axhline(70, color="#bbb", ls=":", lw=0.8)
    axr.axhline(30, color="#bbb", ls=":", lw=0.8)
    axr.axhline(50, color="#e2e2e2", lw=0.6)
    xr1 = mdates.date2num((p1_ts + delta).to_pydatetime())
    xr2 = mdates.date2num((p2_ts + delta).to_pydatetime())
    div_col = "#2ca02c" if acc else "#d62728"
    axr.plot([xr1, xr2], [res.p1.rsi, res.p2.rsi], color=div_col, ls="--", lw=2.0,
             zorder=5, label=f"divergence Δ{res.rsi_div:+.0f}")
    axr.scatter([xr1, xr2], [res.p1.rsi, res.p2.rsi], s=70, color="#1f77b4", zorder=6)
    for xx, rv in [(xr1, res.p1.rsi), (xr2, res.p2.rsi)]:
        axr.annotate(f"{rv:.0f}", (xx, rv), textcoords="offset points", xytext=(0, 6),
                     ha="center", fontsize=8, weight="bold", color="#1f77b4")
    axr.set_ylabel("RSI"); axr.set_ylim(0, 100); axr.grid(True, alpha=0.2)
    axr.legend(fontsize=7, loc="upper left")
    axr.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m %Hh"))
    fig.autofmt_xdate(rotation=30)
    fig.savefig(out_path, dpi=130, bbox_inches="tight")
    plt.close(fig)
    return out_path
