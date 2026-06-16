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


# Venues d'OI atteignables (Binance fapi / Bybit géo-bloqués dans cet environnement).
OI_VENUES = ("okx", "gate")


def _oi_series(ex, symbol: str, timeframe: str, limit: int) -> "pd.Series | None":
    """Série d'Open Interest (valeur USD) d'un exchange ccxt, indexée ts UTC."""
    base, quote = symbol.split("/")
    perp = f"{base}/{quote}:{quote}"          # ex. BTC/USDT -> BTC/USDT:USDT
    if perp not in ex.markets:
        return None
    hist = ex.fetch_open_interest_history(perp, timeframe, limit=limit)
    rows = {pd.to_datetime(h["timestamp"], unit="ms", utc=True):
            (h.get("openInterestValue") or h.get("openInterestAmount")) for h in hist}
    s = pd.Series(rows).dropna().sort_index()
    return s if len(s) else None


def _aggregate_oi(symbol: str, timeframe: str, limit: int, source: str) -> "pd.Series | None":
    """Somme (USD) de l'OI sur plusieurs venues, alignée sur l'union des horodatages.

    `source` : 'agg' (OKX+Gate), 'okx', 'gate'. openInterestValue est en USD partout,
    donc additionnable. Tolérant : ignore une venue en panne.
    """
    import ccxt  # import paresseux

    venues = {"okx": ("okx",), "gate": ("gate",)}.get(source, OI_VENUES)
    series = []
    for name in venues:
        try:
            ex = getattr(ccxt, name)({"enableRateLimit": True})
            ex.load_markets()
            s = _oi_series(ex, symbol, timeframe, limit)
            if s is not None:
                series.append(s.rename(name))
        except Exception:
            continue
    if not series:
        return None
    if len(series) == 1:
        return series[0]
    # union des horodatages, chaque venue complétée (carry) avant la somme
    df = pd.concat(series, axis=1).sort_index().ffill().bfill()
    return df.sum(axis=1)


def fetch_open_interest(symbol: str, timeframe: str = "1h", limit: int = 300,
                        source: str = "agg") -> "pd.DataFrame | None":
    """Historique d'Open Interest (perp) aligné sur les barres, indexé ts UTC (col `oi`).

    OI = donnée *futures* ; Binance `fapi` et Bybit sont géo-restreints ici. Source par
    défaut = **agrégat OKX + Gate** (valeurs USD sommées). Tolérant aux pannes : renvoie
    None si indisponible — l'analyse fonctionne alors sans OI.
    """
    try:
        agg = _aggregate_oi(symbol, timeframe, limit, source)
        return None if agg is None else pd.DataFrame({"oi": agg})
    except Exception:
        return None


# Conversion timeframe ccxt -> fréquence pandas pour le resampling des bougies d'OI.
_TF_FREQ = {"1m": "1min", "5m": "5min", "15m": "15min", "30m": "30min",
            "1h": "1h", "4h": "4h", "1d": "1D"}


def fetch_open_interest_ohlc(symbol: str, timeframe: str = "1h", limit: int = 300,
                             source: str = "agg", fine: str = "5m") -> "pd.DataFrame | None":
    """Bougies OHLC d'Open Interest agrégé : on agrège l'OI *fin* (5m) multi-venues puis on
    le resample en `timeframe` (open=1ʳᵉ, high=max, low=min, close=dernière obs de la période).
    Retourne un DataFrame [open, high, low, close] (Md$ bruts en USD) indexé ts UTC, ou None.
    """
    try:
        fine_limit = min(1000, max(limit * 12, 300))   # ~12 obs 5m par barre 1h
        agg = _aggregate_oi(symbol, fine, fine_limit, source)
        if agg is None:
            return None
        freq = _TF_FREQ.get(timeframe, "1h")
        ohlc = agg.resample(freq).agg(["first", "max", "min", "last"]).dropna()
        ohlc.columns = ["open", "high", "low", "close"]
        return ohlc if len(ohlc) else None
    except Exception:
        return None

