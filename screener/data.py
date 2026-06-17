"""
data.py — Couche données : récupération OHLCV via ccxt, cache disque, construction
de l'univers (top paires USDT par volume). Aucune clé API requise pour l'OHLCV public.
"""
from __future__ import annotations

import os
import time

import pandas as pd

CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".cache")


def get_exchange(name: str = "binance"):
    import ccxt  # import paresseux : pas requis pour les tests hors-ligne

    klass = getattr(ccxt, name)
    ex = klass({"enableRateLimit": True})
    ex.load_markets()
    return ex


def _scan_tickers(ex, quote: str, exclude: tuple[str, ...]) -> list[tuple[str, str, float]]:
    """Parcourt les tickers et renvoie [(symbol, base, quoteVolume)] filtrés
    (bonne quote, hors tokens à levier et actions tokenisées), triés par volume."""
    from .decouple import is_tokenized_stock

    tickers = ex.fetch_tickers()
    rows: list[tuple[str, str, float]] = []
    for sym, t in tickers.items():
        if not sym.endswith(f"/{quote}"):
            continue
        base = sym.split("/")[0]
        if any(tag in base for tag in exclude):       # tokens à effet de levier
            continue
        if is_tokenized_stock(base):                   # actions tokenisées : hors crypto
            continue
        qv = t.get("quoteVolume") or 0
        rows.append((sym, base, float(qv)))
    rows.sort(key=lambda r: r[2], reverse=True)
    return rows


def scan_universe(ex, quote: str = "USDT", top_n: int = 60,
                  exclude: tuple[str, ...] = ("UP", "DOWN", "BULL", "BEAR")
                  ) -> tuple[list[str], dict[str, float]]:
    """Univers (top_n symboles les plus échangés) + map {base -> volume quote 24h},
    en un seul appel `fetch_tickers`."""
    rows = _scan_tickers(ex, quote, exclude)
    universe = [s for s, _b, _qv in rows[:top_n]]
    vol_map = {b: qv for _s, b, qv in rows}
    return universe, vol_map


def build_universe(ex, quote: str = "USDT", top_n: int = 60,
                   exclude: tuple[str, ...] = ("UP", "DOWN", "BULL", "BEAR")) -> list[str]:
    """Retourne les `top_n` symboles spot {BASE}/{quote} les plus échangés.
    Exclut tokens à levier et actions tokenisées (rAAPL… : suivent la bourse) — sinon
    le top liquidité en est saturé et le screener de découplage les écarte toutes ensuite."""
    return scan_universe(ex, quote, top_n, exclude)[0]


def fetch_market_caps(pages: int = 8, per_page: int = 250) -> dict[str, float]:
    """Map {TICKER -> market cap USD} via CoinGecko (top `pages × per_page` coins,
    classés par capitalisation). En cas d'homonymes de ticker, garde le plus gros
    market cap. Réseau optionnel : renvoie ce qui a pu être récupéré (vide si échec)."""
    import json
    import time
    import urllib.request

    out: dict[str, float] = {}
    for page in range(1, pages + 1):
        url = ("https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd"
               f"&order=market_cap_desc&per_page={per_page}&page={page}")
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "wyckoff-screener"})
            with urllib.request.urlopen(req, timeout=20) as r:
                data = json.load(r)
        except Exception:
            break
        if not data:
            break
        for c in data:
            sym = (c.get("symbol") or "").upper()
            mc = c.get("market_cap") or 0
            if sym and mc and mc > out.get(sym, 0):
                out[sym] = float(mc)
        time.sleep(1.2)   # respecte le rate-limit gratuit
    return out


def fetch_ohlcv(ex, symbol: str, timeframe: str = "1h", limit: int = 300,
                use_cache: bool = True, max_age_s: int = 1800) -> pd.DataFrame:
    os.makedirs(CACHE_DIR, exist_ok=True)
    safe = symbol.replace("/", "_")
    path = os.path.join(CACHE_DIR, f"{ex.id}_{safe}_{timeframe}.parquet")

    if use_cache and os.path.exists(path) and (time.time() - os.path.getmtime(path)) < max_age_s:
        return pd.read_parquet(path)

    raw = ex.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    df = pd.DataFrame(raw, columns=["ts", "open", "high", "low", "close", "volume"])
    df["ts"] = pd.to_datetime(df["ts"], unit="ms", utc=True)
    df = df.set_index("ts")
    if use_cache:
        try:
            df.to_parquet(path)
        except Exception:
            pass  # parquet optionnel ; le screener fonctionne sans cache disque
    return df
