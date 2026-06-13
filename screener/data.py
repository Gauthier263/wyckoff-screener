"""
data.py — Couche données : récupération OHLCV via ccxt, cache disque, construction
de l'univers (top paires USDT par volume). Aucune clé API requise pour l'OHLCV public.
"""
from __future__ import annotations

import os
import time

import pandas as pd

CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".cache")


def get_exchange(name: str = "binance", mirror: str | None = None,
                 spot_only: bool = True):
    """Instancie un exchange ccxt (OHLCV public, sans clé API).

    `mirror` : hôte de remplacement pour les données publiques Binance lorsque
    `api.binance.com` est géo-bloqué (ex. `data-api.binance.vision`, le miroir
    officiel des klines/tickers). Sans effet sur les autres exchanges.

    Derrière un proxy TLS d'entreprise (CA personnalisé exposé via `REQUESTS_CA_BUNDLE`
    / `SSL_CERT_FILE`), on fait confiance à ce CA — sinon aucun changement de comportement.
    """
    import ccxt  # import paresseux : pas requis pour les tests hors-ligne

    opts: dict = {"enableRateLimit": True}
    if spot_only and name == "binance":
        opts["options"] = {"fetchMarkets": ["spot"]}  # évite fapi/dapi (hors miroir)
    ex = getattr(ccxt, name)(opts)

    ca = os.environ.get("REQUESTS_CA_BUNDLE") or os.environ.get("SSL_CERT_FILE")
    if ca:
        ex.verify = ca
        try:
            ex.session.trust_env = True
            ex.session.verify = ca
        except Exception:
            pass

    if mirror:
        host = mirror if mirror.startswith("http") else f"https://{mirror}"
        api = ex.urls.get("api")
        if isinstance(api, dict):
            for k, v in list(api.items()):
                if isinstance(v, str):
                    api[k] = v.replace("https://api.binance.com", host)
            ex.urls["api"] = api

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
