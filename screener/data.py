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
    # ccxt impose le bundle certifi à requests, qui ignore alors REQUESTS_CA_BUNDLE.
    # Derrière un proxy d'egress (CA d'entreprise), on repointe sur le bundle système.
    # Derrière un proxy d'egress (CA d'entreprise), ccxt force certifi et ignore
    # REQUESTS_CA_BUNDLE. ccxt calcule `verify = self.verify and self.validateServerSsl` :
    # c'est donc `validateServerSsl` qui doit porter le chemin du bundle système.
    ca = os.environ.get("REQUESTS_CA_BUNDLE") or os.environ.get("SSL_CERT_FILE")
    if ca and os.path.exists(ca):
        ex.verify = ca
        ex.validateServerSsl = ca
        if getattr(ex, "session", None) is not None:
            ex.session.verify = ca
    ex.load_markets()
    return ex


def build_universe(ex, quote: str = "USDT", top_n: int = 60,
                   exclude: tuple[str, ...] = ("UP", "DOWN", "BULL", "BEAR"),
                   kind: str = "crypto") -> list[str]:
    """Retourne les `top_n` symboles {BASE}/{quote} les plus échangés.

    `kind` filtre la nature de l'actif (Bitget marque les actions tokenisées par
    info.areaSymbol) : "crypto" (défaut, exclut les xStocks), "xstock" (uniquement
    les xStocks), "all" (aucun filtre). Indispensable sur Bitget où les xStocks
    affichent un quoteVolume aberrant qui les place en tête du classement.
    """
    tickers = ex.fetch_tickers()
    rows = []
    for sym, t in tickers.items():
        if not sym.endswith(f"/{quote}"):
            continue
        base = sym.split("/")[0]
        if any(tag in base for tag in exclude):  # exclut les tokens à effet de levier
            continue
        if kind != "all":
            is_x = is_tokenized_stock(ex, sym)
            if (kind == "crypto") == is_x:       # crypto→exclut xStock ; xstock→ne garde qu'eux
                continue
        qv = t.get("quoteVolume") or 0
        rows.append((sym, qv))
    rows.sort(key=lambda r: r[1], reverse=True)
    return [s for s, _ in rows[:top_n]]


def is_tokenized_stock(ex, symbol: str) -> bool:
    """True si `symbol` est une action tokenisée (xStock Bitget), pas une crypto.
    Bitget marque ces marchés par info.areaSymbol == 'yes'. Sur les autres exchanges
    le champ est absent → False (tout est considéré crypto)."""
    m = ex.markets.get(symbol) or {}
    return str((m.get("info") or {}).get("areaSymbol", "")).lower() == "yes"


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
