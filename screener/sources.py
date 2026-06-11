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

import numpy as np
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

# Périodes Yahoo par intervalle natif (assez d'historique pour ~300 barres analysées).
_YH_PERIOD = {"60m": "180d", "1d": "3y", "1wk": "5y"}
_YH_PERIOD_4H = "360d"  # 1h ré-échantillonné en 4h


def resample_session_ohlcv(df: pd.DataFrame, bars_per_bucket: int = 4) -> pd.DataFrame:
    """Agrège des barres 1h en blocs de `bars_per_bucket` barres **depuis l'ouverture
    de chaque séance** (convention TradingView pour les actions : 4h = 9h30→13h30,
    13h30→clôture).

    Les blocs calendaires UTC découpent la séance n'importe comment (barres « 4h »
    de 2h30 puis 4h selon le titre) → spread et volume non comparables entre barres,
    ce qui fausse la VSA. Ici chaque bloc démarre à l'ouverture : mêmes bornes que
    les plateformes de référence. `df` doit être indexé dans le fuseau de la bourse
    (pas encore converti UTC) pour que le groupement par jour de séance soit correct."""
    if df.empty:
        return df
    rows = []
    for _, day in df.groupby(df.index.date, sort=True):
        for i in range(0, len(day), bars_per_bucket):
            blk = day.iloc[i: i + bars_per_bucket]
            rows.append({
                "ts": blk.index[0],
                "open": float(blk["open"].iloc[0]),
                "high": float(blk["high"].max()),
                "low": float(blk["low"].min()),
                "close": float(blk["close"].iloc[-1]),
                "volume": float(blk["volume"].sum()),
            })
    out = pd.DataFrame(rows).set_index("ts")
    out.index.name = "ts"
    return out


def rescale_intraday_volume(intra: pd.DataFrame, daily: pd.DataFrame) -> pd.DataFrame:
    """Cale le volume intraday Yahoo sur le total quotidien **consolidé**.

    Yahoo intraday n'agrège pas toutes les places (77-94 % du SIP sur les actions US,
    et le manque varie d'un jour à l'autre : facteur mesuré 1,0→2,1 sur AAPL), alors
    que son *daily* est consolidé et exact. On renormalise donc chaque jour de séance :
    le profil intra-journalier reste celui de l'intraday, le niveau quotidien devient
    celui du consolidé (= TradingView). Les deux index doivent être dans le même
    fuseau (celui de la bourse) pour que le groupement par jour soit correct.
    Garde-fou : facteur hors [0.5, 5] (données aberrantes ou trouées) → pas de correction.
    """
    if intra.empty or daily.empty:
        return intra
    out = intra.copy()
    day = pd.Index(out.index.date)
    day_sum = out["volume"].groupby(day).transform("sum").set_axis(out.index)
    dmap = {ts.date(): float(v) for ts, v in daily["volume"].items()}
    target = pd.Series([dmap.get(d, np.nan) for d in day], index=out.index)
    factor = target / day_sum.replace(0, np.nan)
    factor = factor.where((factor >= 0.5) & (factor <= 5.0)).fillna(1.0)
    out["volume"] = out["volume"] * factor
    return out


def _yahoo_history(ticker: str, interval: str, period: str,
                   keep_tz: bool = False) -> pd.DataFrame:
    import yfinance as yf  # import paresseux (tests hors-ligne)

    raw = yf.Ticker(ticker).history(period=period, interval=interval, auto_adjust=False)
    if raw is None or raw.empty:
        return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
    raw = raw.rename(columns=str.lower)
    df = raw[["open", "high", "low", "close", "volume"]].copy()
    if not keep_tz:  # keep_tz : garder le fuseau de la bourse (resample par séance)
        df.index = pd.to_datetime(df.index, utc=True)
    df.index.name = "ts"
    return df


def _yahoo_fetch(ticker: str, timeframe: str, limit: int) -> pd.DataFrame:
    tf = timeframe.lower()
    if tf in ("1h", "60m"):
        base = _yahoo_history(ticker, "60m", _YH_PERIOD["60m"], keep_tz=True)
        daily = _yahoo_history(ticker, "1d", _YH_PERIOD["60m"], keep_tz=True)
        df = rescale_intraday_volume(base, daily)
        df.index = pd.to_datetime(df.index, utc=True)
    elif tf == "4h":
        base = _yahoo_history(ticker, "60m", _YH_PERIOD_4H, keep_tz=True)
        daily = _yahoo_history(ticker, "1d", _YH_PERIOD_4H, keep_tz=True)
        base = rescale_intraday_volume(base, daily)
        df = resample_session_ohlcv(base, 4)
        df.index = pd.to_datetime(df.index, utc=True)
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


# --------------------------------------------------------------------------- #
# Polygon.io — volume SIP consolidé pour les actions US (= celui de TradingView).
# Free tier : 5 req/min, 2 ans d'historique, données fin de séance. Stratégie :
# UNE requête d'agrégats 30 minutes par titre (cache parquet 12 h), depuis laquelle
# H1 / H4 / D1 sont dérivés localement sur les heures de séance régulières (9h30 ET),
# blocs alignés sur l'ouverture → mêmes barres que TradingView.
# --------------------------------------------------------------------------- #
_POLYGON_BASE = "https://api.polygon.io"
_POLYGON_30M_DAYS = 420       # profondeur demandée (≈ 200 barres 4h de séance)
_POLYGON_CACHE_S = 12 * 3600  # données EOD → cache long
_POLYGON_MIN_INTERVAL_S = 12.5  # 5 req/min sur le free tier
_polygon_last_call = 0.0


def polygon_key() -> str:
    if os.environ.get("POLYGON_API_KEY"):
        return os.environ["POLYGON_API_KEY"]
    try:
        import yaml
        with open("config.yaml", encoding="utf-8") as f:
            return (yaml.safe_load(f) or {}).get("polygon_api_key", "") or ""
    except Exception:
        return ""


def _polygon_raw_30m(ticker: str, key: str) -> pd.DataFrame:
    """Agrégats 30 min ajustés (sort asc, limite max) sur _POLYGON_30M_DAYS jours."""
    global _polygon_last_call
    import requests

    wait = _POLYGON_MIN_INTERVAL_S - (time.time() - _polygon_last_call)
    if wait > 0:
        time.sleep(wait)
    end = pd.Timestamp.utcnow().date()
    start = end - pd.Timedelta(days=_POLYGON_30M_DAYS)
    url = (f"{_POLYGON_BASE}/v2/aggs/ticker/{ticker}/range/30/minute/"
           f"{start}/{end}?adjusted=true&sort=asc&limit=50000&apiKey={key}")
    r = requests.get(url, timeout=30)
    _polygon_last_call = time.time()
    r.raise_for_status()
    results = r.json().get("results") or []
    if not results:
        return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
    df = pd.DataFrame(results)[["t", "o", "h", "l", "c", "v"]]
    df.columns = ["ts", "open", "high", "low", "close", "volume"]
    df["ts"] = pd.to_datetime(df["ts"], unit="ms", utc=True)
    return df.set_index("ts")


def _polygon_cached_30m(ticker: str, use_cache: bool) -> pd.DataFrame:
    key = polygon_key()
    if not key:
        raise RuntimeError("POLYGON_API_KEY absente")
    os.makedirs(data_mod.CACHE_DIR, exist_ok=True)
    path = os.path.join(data_mod.CACHE_DIR, f"polygon_{ticker}_30m.parquet")
    if use_cache and os.path.exists(path) and (time.time() - os.path.getmtime(path)) < _POLYGON_CACHE_S:
        try:
            return pd.read_parquet(path)
        except Exception:
            pass
    df = _polygon_raw_30m(ticker, key)
    if use_cache and not df.empty:
        try:
            df.to_parquet(path)
        except Exception:
            pass
    return df


def polygon_session_frames(raw_30m: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    """Dérive H1 / H4 / D1 depuis des agrégats 30 min : filtre les heures de séance
    régulières (9h30→16h ET, comme TradingView par défaut) puis agrège en blocs
    alignés sur l'ouverture. Renvoie un index UTC."""
    if raw_30m.empty:
        return raw_30m
    et = raw_30m.tz_convert("America/New_York")
    rth = et.between_time("09:30", "15:59")
    tf = timeframe.lower()
    if tf in ("1h", "60m"):
        out = resample_session_ohlcv(rth, 2)    # 2 × 30 min
    elif tf == "4h":
        out = resample_session_ohlcv(rth, 8)    # 8 × 30 min = 9h30→13h30, 13h30→16h
    elif tf in ("1d", "1day", "d"):
        out = resample_session_ohlcv(rth, 13)   # séance entière (13 × 30 min)
    else:
        raise ValueError(f"timeframe Polygon non supporté : {timeframe}")
    out.index = out.index.tz_convert("UTC")
    return out


def _polygon_fetch(ticker: str, timeframe: str, limit: int, use_cache: bool) -> pd.DataFrame:
    ticker = ticker.replace("-", ".")  # classes d'actions : Yahoo BRK-B → Polygon BRK.B
    raw = _polygon_cached_30m(ticker, use_cache)
    return polygon_session_frames(raw, timeframe).tail(limit)


def source_for(asset: Asset, mode: str) -> str:
    """Résout la source effective pour un actif selon le mode demandé.

    mode='yahoo'  → tout via Yahoo (fonctionne partout, y compris crypto en `-USD`).
    mode='ccxt'   → crypto via ccxt ; actions US via Polygon si clé présente
                    (volume SIP consolidé), sinon Yahoo ; non-US et MP via Yahoo.
    mode='auto'   → identique à 'ccxt'.
    """
    if mode == "yahoo":
        return "yahoo"
    if asset.cls == "crypto" and asset.ccxt:
        return "ccxt"
    # Polygon free = actions US uniquement (pas de suffixe de place, pas de futures).
    if asset.cls == "equity" and "." not in asset.yahoo and polygon_key():
        return "polygon"
    return "yahoo"


def fetch(asset: Asset, timeframe: str, limit: int, *, mode: str = "yahoo",
          ex=None, use_cache: bool = True) -> pd.DataFrame:
    """Récupère l'OHLCV d'un actif sur la TF voulue via la source résolue."""
    src = source_for(asset, mode)
    if src == "ccxt":
        return data_mod.fetch_ohlcv(ex, asset.ccxt, timeframe=timeframe,
                                    limit=limit, use_cache=use_cache)
    if src == "polygon":
        try:
            df = _polygon_fetch(asset.yahoo, timeframe, limit, use_cache)
            if not df.empty:
                return df
        except Exception:
            pass  # repli Yahoo : un raté Polygon ne casse pas le scan
    return _cached_yahoo(asset.yahoo, timeframe, limit, use_cache)
