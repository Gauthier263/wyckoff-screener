"""
plot_scan.py — Illustration des résultats du screener Wyckoff.

Rejoue l'analyse (features + plage + événements) sur une liste de symboles et
produit un PNG par paire : prix (chandeliers), plage de trading (support/résistance/
milieu), marqueurs d'événements détectés, et volume coloré par vol_ratio.

    python plot_scan.py --timeframe 1h --symbols BTC/USDT ETH/USDT
"""
from __future__ import annotations

import argparse

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np

from screener import data as data_mod
from screener.cli import load_config
from screener.events import Thresholds, detect_events
from screener.features import add_features, detect_trading_range, swing_points

# Couleur par famille d'événement
EVENT_COLORS = {
    "SPRING": "#2ca02c", "SC": "#2ca02c", "SOS": "#2ca02c", "ST": "#1f77b4",
    "LPS": "#17becf", "UTAD": "#d62728", "BC": "#d62728", "SOW": "#d62728",
    "LPSY": "#ff7f0e",
}


def draw_candles(ax, df) -> None:
    """Chandeliers simples (pas de dépendance mplfinance)."""
    x = mdates.date2num(df.index.to_pydatetime())
    width = (x[1] - x[0]) * 0.7 if len(x) > 1 else 0.02
    for xi, (_, row) in zip(x, df.iterrows()):
        up = row["close"] >= row["open"]
        color = "#26a69a" if up else "#ef5350"
        ax.vlines(xi, row["low"], row["high"], color=color, linewidth=0.6, zorder=1)
        lo, hi = sorted((row["open"], row["close"]))
        ax.add_patch(plt.Rectangle((xi - width / 2, lo), width, max(hi - lo, 1e-9),
                                   facecolor=color, edgecolor=color, linewidth=0.5, zorder=2))


def plot_symbol(symbol: str, df, cfg: dict, out_path: str) -> dict:
    df = add_features(df, vol_ma=cfg["vol_ma"], atr_period=cfg["atr_period"])
    df = swing_points(df, left=3, right=3)
    tr = detect_trading_range(df, lookback=cfg["lookback"], buffer=cfg["buffer"])
    th = Thresholds(**cfg.get("thresholds", {}))
    events = detect_events(df, tr, buffer=cfg["buffer"], th=th)

    # On affiche la dernière fenêtre pertinente : lookback + un peu de marge
    view = df.iloc[-(cfg["lookback"] + cfg["buffer"] + 10):]
    x = mdates.date2num(view.index.to_pydatetime())

    fig, (axp, axv) = plt.subplots(
        2, 1, figsize=(13, 7.5), sharex=True,
        gridspec_kw={"height_ratios": [3, 1], "hspace": 0.05},
    )
    fig.patch.set_facecolor("white")

    draw_candles(axp, view)

    # Plage de trading
    if tr.is_valid:
        axp.axhspan(tr.low, tr.high, color="#ffe082", alpha=0.18, zorder=0)
        for y, lbl, ls in [(tr.high, f"Résistance {tr.high:.2f}", "-"),
                           (tr.mid, f"Milieu {tr.mid:.2f}", "--"),
                           (tr.low, f"Support {tr.low:.2f}", "-")]:
            axp.axhline(y, color="#b08900", linestyle=ls, linewidth=1.0, alpha=0.8, zorder=1)
            axp.text(x[0], y, f" {lbl}", va="bottom", ha="left", fontsize=8, color="#7a5c00")

    # Marqueurs d'événements. On entoure chaque barre concernée et on décale les
    # étiquettes verticalement pour éviter le chevauchement quand plusieurs events
    # tombent sur des barres voisines au même prix (ex. série de ST).
    for rank, ev in enumerate(sorted(events, key=lambda e: e.bars_ago)):
        ts = view.index[-1 - ev.bars_ago]
        xe = mdates.date2num(ts.to_pydatetime())
        col = EVENT_COLORS.get(ev.name, "#555555")
        axp.scatter([xe], [ev.price], s=120, marker="o", facecolor="none",
                    edgecolor=col, linewidth=1.8, zorder=5)
        lbl = f"{ev.name} {ev.bias[:4]} f={ev.strength:.2f} (t-{ev.bars_ago})"
        # étiquettes empilées vers le haut, ancrées à droite pour ne pas sortir du cadre
        axp.annotate(lbl, (xe, ev.price), textcoords="offset points",
                     xytext=(8, 18 + 16 * rank), ha="left", fontsize=8,
                     color=col, weight="bold",
                     arrowprops=dict(arrowstyle="-", color=col, lw=0.6, alpha=0.6))
    seen = {e.name for e in events}

    title = f"{symbol} — {cfg['timeframe']}  |  plage {'valide' if tr.is_valid else 'invalide'}"
    if events:
        title += f"  |  events: {', '.join(sorted(seen))}"
    axp.set_title(title, fontsize=11, weight="bold")
    axp.set_ylabel("Prix")
    axp.grid(True, alpha=0.2)

    # Volume coloré par vol_ratio
    vr = view["vol_ratio"].fillna(1.0).values
    width = (x[1] - x[0]) * 0.7 if len(x) > 1 else 0.02
    bar_colors = ["#ef5350" if c < o else "#26a69a"
                  for o, c in zip(view["open"], view["close"])]
    axv.bar(x, view["volume"].values, width=width, color=bar_colors, alpha=0.55, zorder=2)
    # Repère seuil climax sur la vol_ma
    axv.plot(x, view["vol_ma"].values, color="#555", linewidth=0.8, label="vol MA")
    axv.plot(x, view["vol_ma"].values * th.climax_vol, color="#d62728", linewidth=0.8,
             linestyle="--", label=f"seuil climax x{th.climax_vol}")
    axv.set_ylabel("Volume")
    axv.grid(True, alpha=0.2)
    axv.legend(fontsize=7, loc="upper left")

    axv.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d %H:%M"))
    fig.autofmt_xdate(rotation=30)
    fig.tight_layout()
    fig.savefig(out_path, dpi=130, bbox_inches="tight")
    plt.close(fig)

    return {"symbol": symbol, "valid_range": tr.is_valid,
            "events": [(e.name, e.bias, e.bars_ago, round(e.strength, 3)) for e in events],
            "out": out_path}


def main() -> None:
    cfg = {
        "exchange": "binance", "quote": "USDT", "timeframe": "1h", "limit": 300,
        "lookback": 80, "buffer": 5, "vol_ma": 20, "atr_period": 14,
        "use_cache": True, "thresholds": {},
    }
    cfg.update(load_config())

    p = argparse.ArgumentParser()
    p.add_argument("--timeframe", default=cfg["timeframe"])
    p.add_argument("--symbols", nargs="*", default=["BTC/USDT", "ETH/USDT"])
    p.add_argument("--no-cache", action="store_true")
    args = p.parse_args()
    cfg.update(timeframe=args.timeframe, use_cache=not args.no_cache)

    ex = data_mod.get_exchange(cfg["exchange"])
    for sym in args.symbols:
        df = data_mod.fetch_ohlcv(ex, sym, timeframe=cfg["timeframe"],
                                  limit=cfg["limit"], use_cache=cfg["use_cache"])
        slug = sym.replace("/", "").lower()
        out = f"chart_{slug}_{cfg['timeframe']}.png"
        info = plot_symbol(sym, df, cfg, out)
        print(f"{info['symbol']:10s} range_valide={info['valid_range']} "
              f"events={info['events']} -> {info['out']}")


if __name__ == "__main__":
    main()
