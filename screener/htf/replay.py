"""replay.py — rejeu de la carte de liquidité à une date passée, pour calibration.

Gèle toutes les données à un instant `asof` (aucune bougie postérieure n'entre dans le
calcul) et construit la carte. Sert à confronter notre reconstruction aux cartes Hyblock
publiées par CrypNuevo, dont les relevés sont consignés dans `HYBLOCK_REFERENCES`.

`python -m screener.htf.replay` lance la comparaison sur les trois dates de référence.
"""
from __future__ import annotations

import pandas as pd

from .. import data as D
from ..clock import fmt
from . import calibrate as C
from . import liqmap as L

# Relevés lus sur les captures Hyblock publiées par CrypNuevo (cf. research/crypnuevo_tweets.md).
# `asof` = horodatage « Last Updated » de la capture. Les montants en dollars ne sont pas
# repris : ils dépendent de son réglage « max liquidity setting », non reproductible.
HYBLOCK_REFERENCES = [
    {"asof": "2026-11-08T04:14:00Z", "price": 75_885,
     "walls": [76_600], "liq_clusters": [(73_000, 74_700)],
     "note": "mur d'OI 76,6k = résistance ; amas de liquidations 73-74,7k, touché le 12/11"},
    {"asof": "2026-11-15T21:35:00Z", "price": 65_016,
     "walls": [], "liq_clusters": [],
     "note": "606 niveaux de shorts contre 144 de longs : carburant très majoritairement "
             "au-dessus (risque moyen de short squeeze)"},
    # Le widget de la capture affiche « Price: 64541.5 », incohérent avec le marché à cette
    # heure (BTC ~58,9k) ; on retient le prix réel. Le 60 732 du tweet est celui de 20h52 UTC.
    {"asof": "2026-11-22T05:11:00Z", "price": 58_924,
     "walls": [58_600], "liq_clusters": [(65_500, 66_500)],
     "thin_air": [(62_800, 65_800)],
     "note": "mur 58,6k sous le prix ; thin air 62,8-65,8k ; aimant de liquidations 66k"},
]


_TF_MS = {"5m": 300_000, "15m": 900_000, "30m": 1_800_000, "1h": 3_600_000,
          "2h": 7_200_000, "4h": 14_400_000, "1d": 86_400_000}


def fetch_ohlcv_range(ex, symbol: str, timeframe: str, start, end) -> pd.DataFrame:
    """OHLCV sur un intervalle précis, paginé (ccxt plafonne à ~1000 bougies par appel)."""
    step = _TF_MS.get(timeframe, 3_600_000)
    since = int(pd.Timestamp(start).timestamp() * 1000)
    stop = int(pd.Timestamp(end).timestamp() * 1000)
    rows, guard = [], 0
    while since < stop and guard < 50:
        guard += 1
        batch = ex.fetch_ohlcv(symbol, timeframe=timeframe, since=since, limit=1000)
        if not batch:
            break
        rows += [r for r in batch if r[0] <= stop]
        nxt = batch[-1][0] + step
        if nxt <= since:
            break
        since = nxt
    df = pd.DataFrame(rows, columns=["ts", "open", "high", "low", "close", "volume"])
    if df.empty:
        return df.set_index("ts")
    df["ts"] = pd.to_datetime(df["ts"], unit="ms", utc=True)
    return df.drop_duplicates("ts").set_index("ts").sort_index()


# Codes Coinalyze : A Binance, 6 Bybit, 3 OKX. Les heatmaps Hyblock agrègent plusieurs
# bourses (Binance + Bybit + Bitmex) ; comparer notre Binance seul à une de ces cartes
# mélange l'erreur de notre modèle et un écart de couverture.
VENUES = {"binance": "A", "bybit": "6", "okx": "3"}


def load_frozen(asof, lookback_days: int = 30, timeframe: str = "1h",
                symbol: str = "BTC/USDT", venues=("binance",)):
    """OHLCV, OI coin et delta perp figés à `asof` (rien après n'est chargé).

    `venues` somme l'OI et le delta agressif de plusieurs bourses, pour se comparer à une
    carte multi-exchange. Une bourse qui ne répond pas est simplement ignorée.
    """
    end = pd.Timestamp(asof, tz="UTC")
    start = end - pd.Timedelta(days=lookback_days)
    ex = D.get_exchange("binance")
    df = fetch_ohlcv_range(ex, symbol, timeframe, start, end)

    ois, deltas = [], []
    for v in venues:
        code = VENUES.get(v, v)
        o = D.fetch_coinalyze_oi(symbol, timeframe, start=start, end=end, usd=False,
                                 exch=code)
        if isinstance(o, pd.DataFrame):
            o = o.iloc[:, 0]
        if o is not None and len(o):
            ois.append(o)
        d = D.fetch_perp_taker_delta(symbol, timeframe, start=start, end=end, exch=code)
        if d is not None and len(d):
            deltas.append(d)
    oi = (pd.concat(ois, axis=1).sum(axis=1, min_count=1).sort_index()
          if ois else None)
    delta = (pd.concat(deltas, axis=1).sum(axis=1, min_count=1).sort_index()
             if deltas else None)
    return df, oi, delta


def replay(asof, lookback_days: int = 30, timeframe: str = "1h",
           calibrated: bool = True, **kw) -> dict:
    """Carte figée à `asof`. Avec `calibrated`, les paliers de levier sont ajustés sur les
    liquidations réellement exécutées de la fenêtre au lieu d'être postulés."""
    df, oi, delta = load_frozen(asof, lookback_days, timeframe)
    if df.empty or oi is None or len(oi) == 0:
        raise RuntimeError(f"données indisponibles pour {asof}")
    if calibrated and "leverage_tiers" not in kw:
        end = pd.Timestamp(asof, tz="UTC")
        obs = C.observed_liquidations("BTC/USDT", timeframe,
                                      end - pd.Timedelta(days=lookback_days), end, df.index)
        if obs is not None:
            fitted = C.fit_leverage_tiers(df, oi, delta, obs, step_pct=0.002)
            kw["leverage_tiers"] = fitted["tiers"]
            kw["unlevered_frac"] = fitted["unlevered_frac"]
            m = L.build_map(df, oi, delta, **kw)
            m["calibration"] = fitted
            return m
    return L.build_map(df, oi, delta, **kw)


def _near(value: float, targets, tol_pct: float = 0.01) -> bool:
    return any(abs(value / t - 1.0) <= tol_pct for t in targets)


def compare(ref: dict, lookback_days: int = 30, timeframe: str = "1h",
            tol_pct: float = 0.01, **kw) -> dict:
    """Compare notre carte au relevé Hyblock d'une date. Renvoie les deux lectures côte à côte."""
    m = replay(ref["asof"], lookback_days, timeframe, **kw)
    g = m["grid"]
    pos = L.clusters(g, m["positions"], top_n=4)
    up = L.clusters(g, m["liq_short"], top_n=4)     # carburant au-dessus (shorts liquidés)
    dn = L.clusters(g, m["liq_long"], top_n=4)      # carburant en dessous (longs liquidés)
    air = L.thin_air(g, m["positions"], m["price"], "up")
    sq = L.squeeze_delta(m["liq_long"], m["liq_short"], g, m["price"])
    walls = list(pos["peak"]) if not pos.empty else []
    fuel = [c for c in (list(up["peak"]) if not up.empty else [])]
    return {
        "asof": ref["asof"], "price_ours": round(m["price"]), "price_ref": ref.get("price"),
        "walls_ours": [round(w) for w in walls],
        "walls_ref": ref.get("walls", []),
        "walls_ok": all(_near(w, walls, tol_pct) for w in ref.get("walls", [])) if walls else False,
        "fuel_up_ours": [round(x) for x in fuel],
        "fuel_down_ours": [round(x) for x in (list(dn["peak"]) if not dn.empty else [])],
        "liq_ref": ref.get("liq_clusters", []),
        "thin_air_ours": [(round(r.low), round(r.high)) for r in air.head(2).itertuples()],
        "thin_air_ref": ref.get("thin_air", []),
        "skew": round(sq["skew"], 3),
        "note": ref["note"],
    }


def main():
    rows = []
    for ref in HYBLOCK_REFERENCES:
        try:
            rows.append(compare(ref))
        except Exception as e:
            rows.append({"asof": ref["asof"], "note": f"échec : {type(e).__name__}: {e}"})
    for r in rows:
        print("=" * 78)
        for k, v in r.items():
            print(f"{k:>16} : {v}")


if __name__ == "__main__":
    main()
