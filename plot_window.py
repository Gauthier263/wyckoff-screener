"""Vue annotee d'une fenetre precise — lecture Wyckoff manuelle."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

from screener import data as data_mod
from screener.features import add_features

ex = data_mod.get_exchange("binance")
df = add_features(data_mod.fetch_ohlcv(ex, "BTC/USDT", "1h", 300, use_cache=False))
w = df.loc["2026-06-09 15:00":"2026-06-10 22:00"].copy()
w.index = w.index + pd.Timedelta(hours=2)  # affichage en CEST

x = mdates.date2num(w.index.to_pydatetime())
fig, (axp, axv) = plt.subplots(2, 1, figsize=(13, 7.5), sharex=True,
                               gridspec_kw={"height_ratios": [3, 1], "hspace": 0.05})

width = (x[1] - x[0]) * 0.7
for xi, (_, r) in zip(x, w.iterrows()):
    up = r["close"] >= r["open"]
    c = "#26a69a" if up else "#ef5350"
    axp.vlines(xi, r["low"], r["high"], color=c, linewidth=0.7, zorder=1)
    lo, hi = sorted((r["open"], r["close"]))
    axp.add_patch(plt.Rectangle((xi - width/2, lo), width, max(hi-lo, 1e-9),
                                facecolor=c, edgecolor=c, zorder=2))

# Niveaux de la structure
sc_low = 60780.0
res = 62857.99
axp.axhline(sc_low, color="#2ca02c", ls="--", lw=1.0, alpha=0.8)
axp.text(x[0], sc_low, " support / low SC 60780", va="bottom", fontsize=8, color="#1b6b1b")
axp.axhline(res, color="#b08900", ls="-", lw=1.0, alpha=0.8)
axp.text(x[0], res, " resistance test 62858", va="bottom", fontsize=8, color="#7a5c00")

# Annotations d'evenements (index CEST)
def mark(ts, price, label, color, dy):
    xe = mdates.date2num(pd.Timestamp(ts).to_pydatetime())
    axp.scatter([xe], [price], s=130, facecolor="none", edgecolor=color, lw=2, zorder=6)
    axp.annotate(label, (xe, price), textcoords="offset points", xytext=(0, dy),
                 ha="center", fontsize=9, weight="bold", color=color,
                 arrowprops=dict(arrowstyle="-", color=color, lw=0.7))

mark("2026-06-09 20:00", 60780, "SC\n(climax vendeur)", "#2ca02c", -38)
mark("2026-06-10 00:00", 62272, "AR\n(rally auto)", "#1f77b4", 16)
mark("2026-06-10 09:00", 61080, "ST\n(test, vol sec)", "#1f77b4", -36)
mark("2026-06-10 16:00", 61950, "SOS\n(vol x2.3, large)", "#2ca02c", 18)
mark("2026-06-10 19:00", 62858, "test resistance", "#d62728", 14)

axp.set_title("BTC/USDT H1 — 09/06 17h → 10/06 22h CEST : sequence d'accumulation (SC-AR-ST-SOS)",
              fontsize=11, weight="bold")
axp.set_ylabel("Prix"); axp.grid(True, alpha=0.2)

bc = ["#ef5350" if c < o else "#26a69a" for o, c in zip(w["open"], w["close"])]
axv.bar(x, w["volume"].values, width=width, color=bc, alpha=0.6)
axv.plot(x, w["vol_ma"].values, color="#555", lw=0.8, label="vol MA")
axv.plot(x, w["vol_ma"].values * 2.0, color="#d62728", lw=0.8, ls="--", label="seuil climax x2")
axv.set_ylabel("Volume"); axv.grid(True, alpha=0.2); axv.legend(fontsize=7, loc="upper left")
axv.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m %Hh"))
fig.autofmt_xdate(rotation=30)
fig.savefig("chart_btc_window.png", dpi=130, bbox_inches="tight")
print("ok -> chart_btc_window.png")
