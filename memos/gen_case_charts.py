# -*- coding: utf-8 -*-
"""Graphes annotés réels (3 panneaux prix+résistance / volume+moy / CVD) pour chaque cas
du mémo résistance. Données réelles BTC, index +2h (CEST étiqueté UTC), RGB haute résolution."""
import warnings; warnings.filterwarnings("ignore")
import os, numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import os as _os
_BASE=_os.path.dirname(_os.path.abspath(__file__))
_CHARTS=_os.path.join(_BASE,"charts")

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from PIL import Image
from screener.data import get_exchange, fetch_ohlcv, fetch_taker_delta, fetch_open_interest
from screener.features import add_features, add_absorption

ex = get_exchange("binance")
UP, DN, VOL, CVDC = "#1b6b1b", "#a11", "#5b8fd0", "#173a6b"
_os.makedirs(_CHARTS, exist_ok=True)
CACHE = {}

def build(tf, lim=760):
    if tf in CACHE: return CACHE[tf]
    df = fetch_ohlcv(ex, "BTC/USDT", tf, limit=lim, use_cache=False); df = add_features(df)
    d = fetch_taker_delta("BTC/USDT", tf, limit=lim, ex=ex); df = add_absorption(df, d)
    df["cvd"] = df["delta"].cumsum()
    df.index = df.index + pd.Timedelta(hours=2)
    CACHE[tf] = df; return df

def plot_case(cid, title, tf, center, before, after, resist, markers, note=""):
    df = build(tf)
    i = df.index.get_indexer([pd.Timestamp(center, tz="UTC")], method="nearest")[0]
    s, e = max(0, i-before), min(len(df), i+after+1)
    d = df.iloc[s:e].reset_index(); x = np.arange(len(d))
    fig, (a1, a2, a3) = plt.subplots(3, 1, figsize=(15, 12), sharex=True,
                                     gridspec_kw={"height_ratios": [3, 1, 1.1]})
    # --- prix ---
    for k in range(len(d)):
        o,h,l,c = d.open[k], d.high[k], d.low[k], d.close[k]
        col = UP if c>=o else DN
        a1.plot([k,k],[l,h], color=col, lw=1.1, zorder=2)
        a1.add_patch(Rectangle((k-0.3, min(o,c)), 0.6, max(abs(c-o), (d.high.max()-d.low.min())*0.002),
                               facecolor=col, edgecolor=col, zorder=3))
    for lvl, lab in resist:
        a1.axhline(lvl, color=DN, ls="--", lw=1.4, alpha=.8, zorder=1)
        a1.text(len(d)-0.5, lvl, f" {lab}", color=DN, fontsize=10, va="center", fontweight="bold")
    # marqueurs d'événement
    for ts, lab, updown in markers:
        j = d.index[d["ts"] == pd.Timestamp(ts, tz="UTC")].tolist()
        if not j:
            j = [int(np.argmin(np.abs((d["ts"]-pd.Timestamp(ts,tz="UTC")).dt.total_seconds())))]
        k = j[0]
        yv = d.high[k] if updown=="up" else d.low[k]
        off = (d.high.max()-d.low.min())*(0.06 if updown=="up" else -0.06)
        va = "bottom" if updown=="up" else "top"
        a1.annotate(lab, xy=(k, yv), xytext=(k, yv+off), ha="center", va=va, fontsize=11,
                    fontweight="bold", color="#111",
                    arrowprops=dict(arrowstyle="->", color="#111", lw=1.3),
                    bbox=dict(boxstyle="round,pad=0.25", fc="#fffbe6", ec="#bbb"))
        for ax in (a1,a2,a3): ax.axvline(k, color="#888", ls=":", lw=0.9, alpha=.6, zorder=0)
    a1.set_ylabel("Prix (BTC/USDT)"); a1.set_title(title, fontsize=13, fontweight="bold")
    a1.grid(alpha=.15)
    # --- volume (+ RVOL sur les cas BUEC) ---
    a2.bar(x, d.volume, width=0.6, color=VOL, zorder=2)
    a2.plot(x, d.vol_ma, color="#555", lw=1.1, ls="--", label="vol MA")
    a2.set_ylabel("Volume"); a2.legend(loc="upper left", fontsize=8); a2.grid(alpha=.15)
    if cid in ("f2a", "f2b", "f2c"):          # RVOL = volume relatif (vol / vol MA)
        mk_idx = set()
        for _ts, _l, _u in markers:
            _j = d.index[d["ts"] == pd.Timestamp(_ts, tz="UTC")].tolist()
            if _j: mk_idx.add(_j[0])
        _vmax = float(d.volume.max())
        for k in range(len(d)):
            _mk = k in mk_idx
            a2.text(k, d.volume[k] + _vmax * 0.03, f"×{d.vol_ratio[k]:.2f}",
                    ha="center", va="bottom", rotation=90,
                    fontsize=8.4 if _mk else 6.3,
                    color=("#a11" if _mk else "#777"),
                    fontweight=("bold" if _mk else "normal"), zorder=4)
        a2.set_ylim(0, _vmax * 1.45)
        a2.set_ylabel("Volume · RVOL (×vol MA)")
    # --- CVD ---
    a3.plot(x, d.cvd, color=CVDC, lw=1.8, zorder=2)
    a3.set_ylabel("CVD (delta cumulé)"); a3.grid(alpha=.15)
    # ticks dates CEST
    step = max(1, len(d)//10)
    a3.set_xticks(x[::step]); a3.set_xticklabels([t.strftime("%d/%m %Hh") for t in d["ts"][::step]], rotation=0, fontsize=8)
    if note:
        fig.text(0.5, 0.005, note, ha="center", fontsize=9, color="#555", style="italic")
    fig.tight_layout(rect=[0,0.02,1,1])
    p = _os.path.join(_CHARTS, f"{cid}.png"); fig.savefig(p, dpi=170, facecolor="white"); plt.close(fig)
    im = Image.open(p)
    if im.mode != "RGB":
        bg = Image.new("RGB", im.size, "white"); bg.paste(im, mask=im.split()[-1] if "A" in im.mode else None); bg.save(p)
    print(cid, im.size)

CASES = [
 ("r1","R1 · Rejet actif — BTC/USDT H1, 16/07 (rejet depuis 64 777)","1h","2026-07-16 09:00",26,14,
   [(64777,"résist. 64 777")], [("2026-07-16 09:00","R1 Rejet actif","down")],
   "Ouverture pile sur 64 777 puis bougie large de baisse (spread ×2.35, CLV 0.22), vente honnête ; suivie d'un vol ×4.44 baissier."),
 ("r2","R2 · Climax acheteur — BTC/USDT H1, 14/07 (sommet 64 744)","1h","2026-07-14 15:00",26,16,
   [(64744,"résist. 64 744")], [("2026-07-14 17:00","R2 Climax (BC)","up")],
   "Poussée finale vol ×3.8 au sommet 64 744 sans suivi → le climax qui a créé la résistance."),
 ("r3","R3 · Absorption passive — BTC/USDT H1, 14/07 18:00","1h","2026-07-14 18:00",24,14,
   [(64744,"résist. 64 744")], [("2026-07-14 18:00","R3 Absorption","up")],
   "Achat agressif (delta_z +1.05, OI +3.1 %) avalé par un spread étroit ×0.73 au sommet — demande absorbée."),
 ("r4","R4 · Distribution étalée — BTC/USDT H4, 06→13/07 (lower highs sous 64 700)","4h","2026-07-10 12:00",25,18,
   [(64700,"résist. 64 700")], [("2026-07-06 22:00","haut 64 700","up"),("2026-07-11 14:00","lower high 64 504","up"),("2026-07-13 02:00","lower high 64 425 → cassure","down")],
   "Hauts déclinants 64 700 → 64 504 → 64 425 sur volume qui ne s'étend plus — distribution qui plafonne 64 700, puis cassure honnête le 13/07."),
 ("r5","R5 · Épuisement — BTC/USDT H1, 01/07 (top du rebond 58 400→59 457)","1h","2026-07-01 06:00",14,13,
   [(59457,"top 59 457")], [("2026-07-01 06:00","R5 Épuisement","up")],
   "Le rebond depuis 58 400 fait son plus-haut à 59 457 sur vol ×0.50 (sec) + CVD en lower high (Δ −565) → chute −840 (>1.2 ATR)."),
 ("r6","R6 · Upthrust/UTAD — BTC/USDT H1, 15/07 (poke à 65 164)","1h","2026-07-15 15:00",26,14,
   [(64744,"borne 64 744")], [("2026-07-15 15:00","R6 Upthrust (UTAD)","up")],
   "Dépassement au-dessus de la plage (65 164) puis clôture basse (CLV 0.33) → markdown des 16–17/07."),
 ("f1","F1 · En force (SOS) — BTC/USDT H1, 20/07 (cassure 65 108)","1h","2026-07-20 17:00",26,14,
   [(65108,"résist. 65 108")], [("2026-07-20 17:00","F1 SOS","up")],
   "Cassure large vol ×2.83, CLV 0.95, CVD franc (delta_z +1.29) → continuation vers 66 956."),
 ("f2a","F2 · Retest/BUEC ① — BTC/USDT H4, 11→12/06 (cassure 62 858)","4h","2026-06-12 06:00",14,12,
   [(62858,"résist. 62 858")], [("2026-06-11 18:00","cassure","up"),("2026-06-12 06:00","back-up (vol sec)","down")],
   "Cassure de 62 858 (RVOL ×1.24) puis back-up qui teste le niveau à volume sec (RVOL ≤ ×0.80) et tient → continuation à 64 763."),
 ("f2b","F2 · Retest/BUEC ② — BTC/USDT H1, 10/07 (cassure 63 500)","1h","2026-07-10 06:00",8,12,
   [(63500,"résist. 63 500")], [("2026-07-10 03:00","cassure","up"),("2026-07-10 09:00","back-up (vol sec)","down")],
   "Cassure C63 750 (RVOL ×1.67, CVD franc) puis back-up sec (RVOL ×0.81) tenant > 63 500 → continuation à 64 693."),
 ("f2c","F2 · Retest/BUEC ③ — BTC/USDT H1, 02/07 (cassure 61 334)","1h","2026-07-02 16:00",12,11,
   [(61334,"résist. 61 334")], [("2026-07-02 14:00","cassure","up"),("2026-07-02 19:00","back-up (vol sec)","down")],
   "Cassure de 61 334 (C61 543, RVOL ×1.76) puis back-up sec (RVOL ×0.69) qui tient → continuation à 61 900."),
 ("f3","F3 · Sans demande — BTC/USDT H1, 12/07 16:00 (cassure ratée)","1h","2026-07-12 16:00",22,14,
   [(64100,"résist. 64 100")], [("2026-07-12 16:00","F3 No-demand","up")],
   "Poussée au-dessus de 64 100 sur vol ×0.39 (anémique) puis repli sous le niveau — cassure sans demande."),
 ("f4","F4 · Covering/squeeze — BTC/USDT H4, 06/07 22:00","4h","2026-07-06 22:00",16,10,
   [(64700,"résist. 64 700")], [("2026-07-06 22:00","F4 Covering","up")],
   "Spike vers 64 700 sur OI −2.63 % (covering) + CVD plat, clôture rejetée (64 042) → retombe."),
 ("f5","F5 · Grinding — BTC/USDT H4, 13→14/06 (dérive furtive)","4h","2026-06-13 18:00",14,12,
   [(64000,"zone 64 000")], [("2026-06-13 14:00","grind","up")],
   "Petits corps haussiers, volume ×0.46–0.83 régulier, qui grignotent 64 000 sans climax — puis s'effrite."),
]
for c in CASES:
    plot_case(*c)
print("done")

# --- versions "embed" (~1500px) pour l'intégration base64 dans le mémo ---
import glob as _glob
for _p in sorted(_glob.glob(_os.path.join(_CHARTS,"*.png"))):
    if _p.endswith("_embed.png"): continue
    _im=Image.open(_p).convert("RGB"); _w=1500; _h=int(_im.height*_w/_im.width)
    _im.resize((_w,_h),Image.LANCZOS).save(_p.replace(".png","_embed.png"),optimize=True)
print("embeds ok")
