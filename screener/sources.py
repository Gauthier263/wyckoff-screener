"""
sources.py — Couche données du screener : OHLCV via ccxt, deux exchanges.

  - **Binance** (spot) pour les cryptos — endpoints publics routés vers le mirror
    `data-api.binance.vision` (api.binance.com = HTTP 451 géo-bloqué depuis le cloud).
  - **Bitget** (perp futures USDT) pour actions tokenisées, métaux et MP.

Les deux exchanges partagent le même correctif d'environnement : `session.trust_env`
+ bundle CA système (sinon le proxy TLS provoque une SSLCertVerificationError). Tout
passe par `data.fetch_ohlcv` (cache parquet), que l'on ne modifie pas.
"""
from __future__ import annotations

import os
import time

import pandas as pd

from . import data as data_mod
from .universe import Asset

_BINANCE_DATA_MIRROR = "https://data-api.binance.vision"


def _apply_env_fixes(ex):
    """Rend l'exchange joignable depuis cet environnement (proxy TLS interceptant)."""
    ex.session.trust_env = True
    ca = os.environ.get("REQUESTS_CA_BUNDLE") or os.environ.get("SSL_CERT_FILE")
    if ca:
        ex.session.verify = ca
    return ex


def get_spot_exchange(name: str = "binance"):
    """Exchange ccxt spot (Binance) prêt à l'emploi : endpoints publics vers le mirror
    (contre le 451), bundle CA système, marchés spot only (fapi/dapi restent 451)."""
    import ccxt

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
    _apply_env_fixes(ex)
    ex.load_markets()
    return ex


def get_bitget_exchange():
    """Exchange ccxt Bitget en perp futures USDT (actions tokenisées, métaux, MP)."""
    import ccxt

    ex = ccxt.bitget({
        "enableRateLimit": True,
        "timeout": 30000,
        "options": {"defaultType": "swap"},
    })
    _apply_env_fixes(ex)
    ex.load_markets()
    return ex


def get_okx_exchange():
    """Exchange ccxt OKX en perp futures USDT — source de l'**Open Interest historique**
    (Bitget n'en fournit pas ; OKX liste les mêmes sous-jacents et expose ~12 j d'OI
    horaire). Sert uniquement à enrichir la lecture des événements, pas le prix."""
    import ccxt

    ex = ccxt.okx({
        "enableRateLimit": True,
        "timeout": 30000,
        "options": {"defaultType": "swap"},
    })
    _apply_env_fixes(ex)
    ex.load_markets()
    return ex


def build_exchanges(assets: list[Asset]) -> dict:
    """Instancie les exchanges nécessaires : prix via Binance/Bitget, OI via OKX (optionnel)."""
    exchanges: dict = {}
    if any(a.source == "binance" for a in assets):
        exchanges["binance"] = get_spot_exchange("binance")
    if any(a.source == "bitget" for a in assets):
        exchanges["bitget"] = get_bitget_exchange()
    try:  # OI best-effort : son absence ne casse pas le scan
        exchanges["okx"] = get_okx_exchange()
    except Exception:
        pass
    return exchanges


def fetch(asset: Asset, timeframe: str, limit: int, *, exchanges: dict,
          use_cache: bool = True):
    """Récupère l'OHLCV d'un actif sur la TF voulue via l'exchange de sa source."""
    ex = exchanges[asset.source]
    return data_mod.fetch_ohlcv(ex, asset.symbol, timeframe=timeframe,
                                limit=limit, use_cache=use_cache)


def fetch_open_interest(base: str, *, exchanges: dict, limit: int = 300,
                        use_cache: bool = True, max_age_s: int = 1800):
    """Série d'Open Interest (notionnel USD) horaire pour `base`, via OKX, indexée UTC.

    Renvoie une `pd.Series` (ou None si OKX indisponible / paire absente). Cache parquet.
    L'OI sert à lire le *flux* entre événements (nouveaux positionnements vs débouclage),
    pas le niveau absolu — l'enrichissement reste best-effort."""
    ex = exchanges.get("okx")
    if ex is None:
        return None
    symbol = f"{base}/USDT:USDT"
    if symbol not in ex.markets:
        return None

    path = os.path.join(data_mod.CACHE_DIR, f"okxoi_{base}.parquet")
    if use_cache and os.path.exists(path) and (time.time() - os.path.getmtime(path)) < max_age_s:
        try:
            return pd.read_parquet(path)["oi"]
        except Exception:
            pass
    try:
        raw = ex.fetch_open_interest_history(symbol, "1h", limit=limit)
    except Exception:
        return None
    pts = {pd.to_datetime(p["timestamp"], unit="ms", utc=True): float(p["openInterestValue"])
           for p in raw if p.get("openInterestValue")}
    if not pts:
        return None
    s = pd.Series(pts).sort_index()
    s.index.name = "ts"
    s.name = "oi"
    if use_cache:
        try:
            s.to_frame().to_parquet(path)
        except Exception:
            pass
    return s
