"""
sources.py — Couche données multi-sources pour le screener.

Route la récupération OHLCV selon la classe d'actif :
  - crypto  → ccxt (exchange spot, ex. binance) *si accessible*, sinon Yahoo (`-USD`).
  - action / matière première → Yahoo Finance (yfinance).

Yahoo ne fournit pas d'intervalle 4h natif : on récupère le 1h et on ré-échantillonne.
Toutes les fonctions renvoient un DataFrame colonnes ['open','high','low','close',
'volume'] indexé par timestamp UTC — strictement le format attendu par `add_features`.

Aucune modification de `data.py` : ce module le réutilise pour le chemin ccxt et ajoute
le chemin Yahoo + un cache parquet partagé.
"""
from __future__ import annotations

import os
import time

import pandas as pd

from . import data as data_mod
from .universe import Asset

# Mirror de données publiques Binance : non géo-bloqué (api.binance.com renvoie 451
# depuis les IP cloud), sert les klines/tickers spot avec les volumes réels.
_BINANCE_DATA_MIRROR = "https://data-api.binance.vision"


def get_spot_exchange(name: str = "binance"):
    """Exchange ccxt spot prêt à l'emploi *dans cet environnement*.

    Trois ajustements rendent Binance joignable ici :
      - routage des endpoints publics vers le mirror `data-api.binance.vision`
        (api.binance.com est géo-bloqué → HTTP 451 depuis le cloud) ;
      - `session.trust_env = True` pour que la session ccxt utilise le bundle CA
        système (`REQUESTS_CA_BUNDLE`), faute de quoi le proxy TLS de l'environnement
        provoque une SSLCertVerificationError ;
      - chargement des marchés *spot uniquement* (les endpoints futures fapi/dapi
        restent géo-bloqués et ne nous servent pas).
    """
    import ccxt  # import paresseux

    klass = getattr(ccxt, name)
    ex = klass({
        "enableRateLimit": True,
        "timeout": 30000,
        "options": {"defaultType": "spot", "fetchMarkets": ["spot"]},
    })
    if name == "binance":
        for key in ("public", "v1"):
            if key in ex.urls["api"]:
                ex.urls["api"][key] = ex.urls["api"][key].replace(
                    "https://api.binance.com", _BINANCE_DATA_MIRROR)
    ex.session.trust_env = True
    ca = os.environ.get("REQUESTS_CA_BUNDLE") or os.environ.get("SSL_CERT_FILE")
    if ca:
        ex.session.verify = ca
    ex.load_markets()
    return ex

_AGG = {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}

# Périodes Yahoo par intervalle natif (assez d'historique pour ~300 barres analysées).
_YH_PERIOD = {"60m": "180d", "1d": "3y", "1wk": "5y"}
_YH_PERIOD_4H = "360d"  # 1h ré-échantillonné en 4h


def resample_ohlcv(df: pd.DataFrame, rule: str = "4h") -> pd.DataFrame:
    """Agrège des barres fines en barres plus larges (OHLCV correct)."""
    out = df.resample(rule, label="left", closed="left").agg(_AGG).dropna()
    return out


def _yahoo_history(ticker: str, interval: str, period: str) -> pd.DataFrame:
    import yfinance as yf  # import paresseux (tests hors-ligne)

    raw = yf.Ticker(ticker).history(period=period, interval=interval, auto_adjust=False)
    if raw is None or raw.empty:
        return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
    raw = raw.rename(columns=str.lower)
    df = raw[["open", "high", "low", "close", "volume"]].copy()
    df.index = pd.to_datetime(df.index, utc=True)
    df.index.name = "ts"
    return df


def _yahoo_fetch(ticker: str, timeframe: str, limit: int) -> pd.DataFrame:
    tf = timeframe.lower()
    if tf in ("1h", "60m"):
        df = _yahoo_history(ticker, "60m", _YH_PERIOD["60m"])
    elif tf == "4h":
        base = _yahoo_history(ticker, "60m", _YH_PERIOD_4H)
        df = resample_ohlcv(base, "4h")
    elif tf in ("1d", "1day", "d"):
        df = _yahoo_history(ticker, "1d", _YH_PERIOD["1d"])
    elif tf in ("1w", "1wk", "1week"):
        df = _yahoo_history(ticker, "1wk", _YH_PERIOD["1wk"])
    else:
        raise ValueError(f"timeframe Yahoo non supporté : {timeframe}")
    return df.tail(limit)


def _cached_yahoo(ticker: str, timeframe: str, limit: int,
                  use_cache: bool, max_age_s: int = 1800) -> pd.DataFrame:
    if not use_cache:
        return _yahoo_fetch(ticker, timeframe, limit)
    os.makedirs(data_mod.CACHE_DIR, exist_ok=True)
    safe = ticker.replace("=", "_").replace(".", "_")
    path = os.path.join(data_mod.CACHE_DIR, f"yahoo_{safe}_{timeframe}.parquet")
    if os.path.exists(path) and (time.time() - os.path.getmtime(path)) < max_age_s:
        try:
            return pd.read_parquet(path)
        except Exception:
            pass
    df = _yahoo_fetch(ticker, timeframe, limit)
    try:
        df.to_parquet(path)
    except Exception:
        pass  # cache optionnel
    return df


def source_for(asset: Asset, mode: str) -> str:
    """Résout la source effective pour un actif selon le mode demandé.

    mode='yahoo'  → tout via Yahoo (fonctionne partout, y compris crypto en `-USD`).
    mode='ccxt'   → crypto via ccxt, actions/MP via Yahoo.
    mode='auto'   → identique à 'ccxt' (crypto exchange si dispo, sinon Yahoo en repli).
    """
    if mode == "yahoo":
        return "yahoo"
    if asset.cls == "crypto" and asset.ccxt:
        return "ccxt"
    return "yahoo"


def fetch(asset: Asset, timeframe: str, limit: int, *, mode: str = "yahoo",
          ex=None, use_cache: bool = True) -> pd.DataFrame:
    """Récupère l'OHLCV d'un actif sur la TF voulue via la source résolue."""
    src = source_for(asset, mode)
    if src == "ccxt":
        return data_mod.fetch_ohlcv(ex, asset.ccxt, timeframe=timeframe,
                                    limit=limit, use_cache=use_cache)
    return _cached_yahoo(asset.yahoo, timeframe, limit, use_cache)
