"""
void_scan.py — Classe les paires futures (Bitget) selon l'efficacité de leur marché à
**combler les vides de chute brutale**.

Pour chaque paire de l'univers (RWA = actions/métaux/indices/MP gardés quel que soit le
volume ; cryptos filtrés par volume), on analyse les `last_n` derniers vides de l'historique
et on compte combien se sont récupérés à 50 % et à 90 % dans `horizon` barres. On ne garde
(`verdict = efficace`) que les marchés dont ≥ `keep_pct` % des vides atteignent 90 %.

Usage :
    python -m screener.void_scan --exchange bitget --timeframe 1h --min-volume 5e6
    python -m screener.void_scan --keep-pct 60 --horizon 48 --last-n 20 --csv void_eff.csv
"""
from __future__ import annotations

import argparse
import sys

import pandas as pd

from . import data as data_mod
from .features import add_features
from .liquidity import VoidThresholds, void_efficiency


def scan(cfg: dict) -> pd.DataFrame:
    ex = data_mod.get_exchange(cfg["exchange"])
    if cfg.get("symbols"):
        universe = [(s, "?") for s in cfg["symbols"]]
    else:
        universe = data_mod.build_futures_universe(
            ex, quote=cfg["quote"], min_quote_volume=cfg["min_volume"])
        print(f"Univers : {len(universe)} paires futures {cfg['exchange']} "
              f"(RWA gardés, crypto ≥ {cfg['min_volume']:.0f} {cfg['quote']})", file=sys.stderr)

    th = VoidThresholds(**cfg.get("void", {}))
    rows: list[dict] = []
    for i, (sym, cat) in enumerate(universe, 1):
        try:
            df = data_mod.fetch_ohlcv(ex, sym, cfg["timeframe"], cfg["limit"], cfg["use_cache"])
            df = add_features(df, vol_ma=cfg["vol_ma"], atr_period=cfg["atr_period"])
            e = void_efficiency(df, th=th, horizon=cfg["horizon"], last_n=cfg["last_n"])
            if e["n_voids"] >= cfg["min_voids"]:          # plancher de significativité
                rows.append({"pair": sym, "type": cat, **e})
        except Exception as ex_:
            print(f"  [skip] {sym}: {ex_}", file=sys.stderr)
        if i % 25 == 0:
            print(f"  ...{i}/{len(universe)}", file=sys.stderr)

    table = pd.DataFrame(rows)
    if table.empty:
        return table
    table["verdict"] = table["pct90"].apply(lambda p: "efficace" if p >= cfg["keep_pct"] else "écarté")
    return table.sort_values(["pct90", "pct50", "n_voids"], ascending=False).reset_index(drop=True)


def main() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass
    from .cli import load_config

    cfg = {
        "exchange": "bitget", "quote": "USDT", "timeframe": "1h", "limit": 1000,
        "vol_ma": 20, "atr_period": 14, "use_cache": True, "symbols": [], "void": {},
        "min_volume": 5_000_000.0, "horizon": 48, "last_n": 20, "min_voids": 5, "keep_pct": 60.0,
    }
    cfg.update(load_config())

    ap = argparse.ArgumentParser(description="Classe les paires futures par efficacité de comblement des vides")
    ap.add_argument("--exchange", default=cfg["exchange"])
    ap.add_argument("--timeframe", default=cfg["timeframe"])
    ap.add_argument("--symbols", nargs="*", default=cfg["symbols"])
    ap.add_argument("--limit", type=int, default=cfg["limit"])
    ap.add_argument("--min-volume", type=float, default=cfg["min_volume"], help="volume 24h mini des cryptos")
    ap.add_argument("--horizon", type=int, default=cfg["horizon"], help="barres pour combler le vide")
    ap.add_argument("--last-n", type=int, default=cfg["last_n"], help="nb de vides analysés/paire")
    ap.add_argument("--min-voids", type=int, default=cfg["min_voids"], help="plancher de vides pour classer")
    ap.add_argument("--keep-pct", type=float, default=cfg["keep_pct"], help="%%90 mini pour 'efficace'")
    ap.add_argument("--csv", default="void_efficiency.csv")
    ap.add_argument("--no-cache", action="store_true")
    args = ap.parse_args()

    cfg.update(exchange=args.exchange, timeframe=args.timeframe, symbols=args.symbols,
               limit=args.limit, min_volume=args.min_volume, horizon=args.horizon,
               last_n=args.last_n, min_voids=args.min_voids, keep_pct=args.keep_pct,
               use_cache=not args.no_cache)

    table = scan(cfg)
    if table.empty:
        print("Aucune paire avec assez de vides sur la période."); return
    kept = table[table["verdict"] == "efficace"]
    print(f"\n{len(table)} paires classées | {len(kept)} efficaces (≥ {cfg['keep_pct']:.0f}% des vides "
          f"comblés à 90% sous {cfg['horizon']} barres)\n")
    with pd.option_context("display.max_rows", None, "display.width", 200):
        print(table.to_string(index=False))
    table.to_csv(args.csv, index=False)
    print(f"\n→ Classement complet dans {args.csv}", file=sys.stderr)


if __name__ == "__main__":
    main()
