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


def build_exchanges(assets: list[Asset]) -> dict:
    """Instancie les exchanges nécessaires selon les sources présentes dans l'univers."""
    exchanges: dict = {}
    if any(a.source == "binance" for a in assets):
        exchanges["binance"] = get_spot_exchange("binance")
    if any(a.source == "bitget" for a in assets):
        exchanges["bitget"] = get_bitget_exchange()
    return exchanges


def fetch(asset: Asset, timeframe: str, limit: int, *, exchanges: dict,
          use_cache: bool = True):
    """Récupère l'OHLCV d'un actif sur la TF voulue via l'exchange de sa source."""
    ex = exchanges[asset.source]
    return data_mod.fetch_ohlcv(ex, asset.symbol, timeframe=timeframe,
                                limit=limit, use_cache=use_cache)
