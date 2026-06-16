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
    import requests

    klass = getattr(ccxt, name)
    opts: dict = {"enableRateLimit": True}
    if name == "binance":
        # Le miroir public de market-data ne sert que le spot : on restreint le
        # chargement des marchés pour éviter les endpoints futures (géo-bloqués).
        opts["options"] = {"fetchMarkets": ["spot"]}
    elif name == "bitget":
        opts["options"] = {"defaultType": "swap"}   # périmètre = perpétuels (futures)
    ex = klass(opts)

    # ccxt embarque son propre bundle certifi ; une session requests standard honore
    # REQUESTS_CA_BUNDLE / SSL_CERT_FILE — indispensable derrière un proxy TLS qui
    # ré-signe le trafic (cas des environnements d'exécution distants).
    ex.session = requests.Session()

    if name == "binance":
        # data-api.binance.vision : miroir public de market-data, non géo-restreint
        # (l'API principale renvoie HTTP 451 depuis certaines régions). Spot only.
        for key, url in ex.urls["api"].items():
            if isinstance(url, str):
                ex.urls["api"][key] = url.replace(
                    "https://api.binance.com", "https://data-api.binance.vision"
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


# Classement cosmétique des sous-jacents RWA (Real World Asset) pour la colonne "type".
_METALS = {"XAU", "XAUT", "XAG", "XPT", "XPD", "PAXG", "COPPER"}
_COMMOD = {"CL", "NATGAS"}
_INDICES = {"SP500", "NDX100", "QQQ", "SPY", "SOXL", "SOXS", "TQQQ", "SQQQ",
            "DXYZ", "KWEB", "INDA", "EWH", "EWJ", "EWT", "EWY", "DFEN"}


def classify_market(base: str, is_rwa: bool) -> str:
    """crypto | metal | commodity | index | stock — d'après le flag RWA Bitget + sous-jacent."""
    if not is_rwa:
        return "crypto"
    if base in _METALS:
        return "metal"
    if base in _COMMOD:
        return "commodity"
    if base in _INDICES:
        return "index"
    return "stock"


def build_futures_universe(ex, quote: str = "USDT", min_quote_volume: float = 5_000_000.0,
                           exclude: tuple[str, ...] = ("UP", "DOWN", "BULL", "BEAR"),
                           include_rwa: bool = True) -> list[tuple[str, str]]:
    """Univers des perpétuels {BASE}/{quote}:{quote} de Bitget.

    On garde **tout le RWA** (actions/métaux/indices/MP — flag `isRwa`) quel que soit son
    volume, et **uniquement les cryptos dont le volume 24h ≥ `min_quote_volume`**.
    Renvoie une liste de (symbole, catégorie). La catégorie vient de `classify_market`.
    """
    tickers = ex.fetch_tickers()
    out: list[tuple[str, str]] = []
    for sym, m in ex.markets.items():
        if m.get("type") != "swap" or m.get("settle") != quote or not m.get("active", True):
            continue
        base = m.get("base", "")
        is_rwa = str(m.get("info", {}).get("isRwa", "")).upper() == "YES"
        cat = classify_market(base, is_rwa)
        if cat == "crypto":
            if any(tag in base for tag in exclude):           # exclut les tokens à levier
                continue
            qv = (tickers.get(sym) or {}).get("quoteVolume") or 0
            if qv < min_quote_volume:                         # exclut le crypto peu liquide
                continue
        elif not include_rwa:
            continue
        out.append((sym, cat))
    return out


def fetch_ohlcv_history(ex, symbol: str, timeframe: str = "1h", total: int = 3000,
                        page: int = 200) -> pd.DataFrame:
    """Récupère un historique profond en **paginant** vers l'avant (Bitget plafonne à ~200
    bougies/appel quand `since` est fixé). Remonte `total` barres avant maintenant.
    Renvoie le même format que `fetch_ohlcv` (index ts UTC). Pas de cache."""
    tf_ms = ex.parse_timeframe(timeframe) * 1000
    now = ex.milliseconds()
    since = now - total * tf_ms
    rows: list = []
    guard = 0
    while since < now and guard < total // page + 5:
        guard += 1
        batch = ex.fetch_ohlcv(symbol, timeframe, since=since, limit=page)
        if not batch:
            break
        rows += batch
        nxt = batch[-1][0] + tf_ms
        if nxt <= since:
            break
        since = nxt
    seen: set = set()
    uniq = [r for r in rows if not (r[0] in seen or seen.add(r[0]))]
    df = pd.DataFrame(uniq, columns=["ts", "open", "high", "low", "close", "volume"])
    df["ts"] = pd.to_datetime(df["ts"], unit="ms", utc=True)
    return df.set_index("ts")


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
