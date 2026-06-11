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
    opts = {"enableRateLimit": True}
    if name == "binance":
        # Le screener ne lit que des données publiques (OHLCV/tickers, jamais d'ordre) :
        # on limite aux marchés spot pour éviter les endpoints futures (fapi, parfois
        # géo-bloqués) qui n'apportent rien ici.
        opts["options"] = {"fetchMarkets": ["spot"]}
    ex = klass(opts)
    if name == "binance":
        # Route les endpoints publics vers le miroir officiel data-only de Binance :
        # mêmes données et mêmes volumes, sans clé API, et non géo-restreint —
        # api.binance.com renvoie 451 dans certaines régions (ex. cet environnement).
        # Surchargeable via BINANCE_PUBLIC_URL si le miroir est indisponible.
        ex.urls["api"]["public"] = os.environ.get(
            "BINANCE_PUBLIC_URL", "https://data-api.binance.vision/api/v3"
        )
    ex.load_markets()
    return ex


def build_universe(ex, quote: str = "USDT", top_n: int = 60,
                   exclude: tuple[str, ...] = ("UP", "DOWN", "BULL", "BEAR")) -> list[str]:
    """Retourne les `top_n` symboles spot {BASE}/{quote} les plus échangés."""
    tickers = ex.fetch_tickers()
    rows = []
    for sym, t in tickers.items():
        if not sym.endswith(f"/{quote}"):
            continue
        base = sym.split("/")[0]
        if any(tag in base for tag in exclude):  # exclut les tokens à effet de levier
            continue
        qv = t.get("quoteVolume") or 0
        rows.append((sym, qv))
    rows.sort(key=lambda r: r[1], reverse=True)
    return [s for s, _ in rows[:top_n]]


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


def fetch_open_interest(symbol: str, timeframe: str = "1h", limit: int = 300,
                        exchange: str = "okx") -> "pd.DataFrame | None":
    """Historique d'Open Interest (perp) aligné sur les barres, indexé ts UTC (col `oi`).

    L'OI est une donnée *futures* : Binance `fapi` est géo-restreint dans certains
    environnements, donc source par défaut = OKX (perp `BASE/QUOTE:QUOTE`). Tolérant
    aux pannes : renvoie None si indisponible — l'analyse fonctionne alors sans OI.
    """
    try:
        import ccxt  # import paresseux

        ex = getattr(ccxt, exchange)({"enableRateLimit": True})
        ex.load_markets()
        base, quote = symbol.split("/")
        perp = f"{base}/{quote}:{quote}"          # ex. BTC/USDT -> BTC/USDT:USDT
        if perp not in ex.markets:
            return None
        hist = ex.fetch_open_interest_history(perp, timeframe, limit=limit)
        rows = [(pd.to_datetime(h["timestamp"], unit="ms", utc=True),
                 h.get("openInterestValue") or h.get("openInterestAmount")) for h in hist]
        oi = pd.DataFrame(rows, columns=["ts", "oi"]).dropna().set_index("ts").sort_index()
        return oi if len(oi) else None
    except Exception:
        return None
