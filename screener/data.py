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

# Minutes par timeframe (planification des limites de téléchargement / du resampling).
_TF_MIN = {"5m": 5, "15m": 15, "30m": 30, "1h": 60, "4h": 240, "1d": 1440}

# TF réellement acceptées par chaque venue pour l'**historique d'OI**. OKX ne sert que
# 5m/1h/1d : demander 15m/30m lève une erreur côté ccxt → la venue était jusqu'ici
# *silencieusement exclue* de l'agrégat (bug). On rabat ces TF sur une base 5 min puis
# on resample (fix #1). Les venues absentes de la table tentent directement le TF demandé.
_VENUE_OI_TF = {"okx": {"5m", "1h", "1d"}}


def _archive_days(now, days=4, start=None, end=None, cap=400) -> list:
    """Liste des dates 'YYYY-MM-DD' à récupérer (jours *passés* uniquement, ≤ veille).

    Mode intervalle si `start`/`end` fournis (historique lointain) ; sinon les `days`
    derniers jours. Borné à `cap` jours. Fonction pure (testable hors-ligne).
    """
    def _naive(ts):
        ts = pd.Timestamp(ts)
        return ts.tz_convert("UTC").tz_localize(None) if ts.tzinfo else ts

    last = _naive(now).normalize() - pd.Timedelta(days=1)      # archive en retard ~1j
    if start is not None or end is not None:
        e = min(_naive(end).normalize() if end is not None else last, last)
        s = _naive(start).normalize() if start is not None else e - pd.Timedelta(days=days - 1)
    else:
        e, s = last, last - pd.Timedelta(days=days - 1)
    if s > e:
        return []
    rng = pd.date_range(s, e, freq="D")[-cap:]
    return [d.strftime("%Y-%m-%d") for d in rng]


def fetch_binance_oi_archive(symbol: str = "BTC/USDT", days: int = 4,
                             start=None, end=None) -> "pd.Series | None":
    """OI Binance (perp USDⓂ) depuis l'archive `data.binance.vision` — fichiers *metrics*
    quotidiens (`sum_open_interest_value`, USD, pas de 5 min). Même miroir non géo-bloqué
    que le spot, donc accessible là où `fapi` renvoie 451. **Retard ~1 jour**.

    `start`/`end` (timestamps) ciblent un **intervalle historique** (ex. mars) ; sinon les
    `days` derniers jours. Binance ne publie ces metrics qu'en *quotidien* (pas de fichier
    mensuel) → on balaie les jours, **téléchargements parallélisés** et **cache disque**
    (`.cache/binance_oi/`, fichiers passés immuables). Série indexée ts UTC, ou None.
    """
    import io
    import zipfile
    from concurrent.futures import ThreadPoolExecutor

    import requests  # apporté par ccxt ; respecte REQUESTS_CA_BUNDLE (CA egress)

    base, quote = symbol.split("/")
    sym = f"{base}{quote}"
    cache_dir = os.path.join(CACHE_DIR, "binance_oi")
    os.makedirs(cache_dir, exist_ok=True)
    dates = _archive_days(pd.Timestamp.now(tz="UTC"), days=days, start=start, end=end)

    def _one(d):
        fname = f"{sym}-metrics-{d}.zip"
        path = os.path.join(cache_dir, fname)
        content = None
        if os.path.exists(path):                       # cache hit (jour passé = immuable)
            try:
                with open(path, "rb") as f:
                    content = f.read()
            except Exception:
                content = None
        if content is None:
            url = f"https://data.binance.vision/data/futures/um/daily/metrics/{sym}/{fname}"
            try:
                r = requests.get(url, timeout=20)
                if r.status_code != 200:
                    return None
                content = r.content
                try:
                    with open(path, "wb") as f:
                        f.write(content)
                except Exception:
                    pass  # cache best-effort
            except Exception:
                return None
        try:
            zf = zipfile.ZipFile(io.BytesIO(content))
            df = pd.read_csv(io.BytesIO(zf.read(zf.namelist()[0])))
            return pd.Series(df["sum_open_interest_value"].astype(float).values,
                             index=pd.to_datetime(df["create_time"], utc=True))
        except Exception:
            return None

    if not dates:
        return None
    with ThreadPoolExecutor(max_workers=8) as pool:
        parts = [s for s in pool.map(_one, dates) if s is not None]
    if not parts:
        return None
    out = pd.concat(parts).sort_index()
    return out[~out.index.duplicated(keep="last")]


def _oi_series(ex, symbol: str, timeframe: str, limit: int) -> "pd.Series | None":
    """Série d'Open Interest (valeur USD) d'un exchange ccxt, indexée ts UTC.

    Fix #1 : si la venue ne sert pas le `timeframe` demandé en historique d'OI (ex. OKX
    refuse 15m/30m), on récupère une base **5 min** et on la resample — la venue n'est plus
    *silencieusement exclue* de l'agrégat. Repli déclenché par `_VENUE_OI_TF` ou par toute
    erreur ccxt sur le premier appel.
    """
    base, quote = symbol.split("/")
    perp = f"{base}/{quote}:{quote}"          # ex. BTC/USDT -> BTC/USDT:USDT
    if perp not in ex.markets:
        return None

    def _fetch(tf, lim):
        hist = ex.fetch_open_interest_history(perp, tf, limit=lim)
        rows = {pd.to_datetime(h["timestamp"], unit="ms", utc=True):
                (h.get("openInterestValue") or h.get("openInterestAmount")) for h in hist}
        return pd.Series(rows).dropna().sort_index()

    supported = _VENUE_OI_TF.get(getattr(ex, "id", ""))
    fallback = supported is not None and timeframe not in supported
    s = None
    if not fallback:
        try:
            s = _fetch(timeframe, limit)
        except Exception:
            fallback = True                   # la venue refuse ce TF → repli 5 min
    if fallback or s is None or not len(s):
        lim5 = min(1500, max(limit * _TF_MIN.get(timeframe, 60) // 5, 300))
        try:
            s5 = _fetch("5m", lim5)
        except Exception:
            return None
        s = s5 if timeframe == "5m" else s5.resample(_TF_FREQ.get(timeframe, "1h")).last().dropna()
    return s if s is not None and len(s) else None


def _combine_oi(series: list) -> "pd.Series | None":
    """Somme plusieurs séries d'OI (USD) sur l'union des horodatages, chaque venue étant
    *carry-forward/back* avant la somme → pas de « falaise » quand une venue (ex. Binance,
    en retard d'archive) ne couvre pas les périodes récentes."""
    series = [s for s in series if s is not None and len(s)]
    if not series:
        return None
    if len(series) == 1:
        return series[0]
    df = pd.concat(series, axis=1).sort_index().ffill().bfill()
    return df.sum(axis=1)


def _coingecko_oi(symbol: str, venue: str = "Binance (Futures)") -> "float | None":
    """OI courant (USD) d'une venue via CoinGecko (snapshot temps réel, sans historique).
    Sert à combler le gap du jour de l'archive Binance. None si indispo."""
    try:
        import requests

        base, quote = symbol.split("/")
        want = f"{base}{quote}"
        d = requests.get("https://api.coingecko.com/api/v3/derivatives"
                         "?include_tickers=unexpired", timeout=15).json()
        for x in d:
            if x.get("market") == venue and str(x.get("symbol")) == want and x.get("open_interest"):
                return float(x["open_interest"])
    except Exception:
        return None
    return None


# Au-delà de ce retard, l'archive Binance est jugée trop périmée pour l'intraday *live*.
_ARCHIVE_MAX_LAG_H = 6


def _archive_lag_hours(series, now) -> "float | None":
    """Retard (heures) du dernier point d'une série d'archive vs `now`. None si vide."""
    if series is None or not len(series):
        return None
    return (pd.Timestamp(now) - series.index[-1]) / pd.Timedelta(hours=1)


def binance_oi_lag_hours(symbol: str = "BTC/USDT") -> "float | None":
    """Retard (heures) de l'archive OI Binance vs maintenant — sert au panneau OI à
    signaler quand le composant Binance est périmé. None si l'archive est indisponible."""
    try:
        return _archive_lag_hours(fetch_binance_oi_archive(symbol, days=2),
                                  pd.Timestamp.now(tz="UTC"))
    except Exception:
        return None


def _binance_oi_series(symbol: str, timeframe: str, limit: int,
                       start=None, end=None) -> "pd.Series | None":
    """OI Binance résolu sur la grille `timeframe` : archive 5 min (data.binance.vision)
    resamplée. `start`/`end` ciblent un intervalle historique ; sinon span déduit de `limit`.
    Point courant CoinGecko ajouté en bout pour combler le retard ~1j (sauf fenêtre passée).

    Fix #2 : en mode **live** (ni `start` ni `end`), si l'archive a plus de
    `_ARCHIVE_MAX_LAG_H` heures de retard, on **renvoie None** plutôt que de la reporter à
    plat (carry-forward) dans l'agrégat. Un Binance figé en J-1 masquait la direction réelle
    de l'OI live → agg3 live se réduit alors au live OKX+Gate, qui colle aux venues.
    """
    if start is not None or end is not None:
        s5 = fetch_binance_oi_archive(symbol, start=start, end=end)
    else:
        days = int(min(8, max(2, (limit * _TF_MIN.get(timeframe, 60)) / 1440 + 1)))
        s5 = fetch_binance_oi_archive(symbol, days=days)
    if s5 is None:
        return None
    if start is None and end is None:                         # live : refuse l'archive périmée
        lag = _archive_lag_hours(s5, pd.Timestamp.now(tz="UTC"))
        if lag is not None and lag > _ARCHIVE_MAX_LAG_H:
            return None
    freq = _TF_FREQ.get(timeframe, "1h")
    bn = s5.resample(freq).last().dropna()
    if end is None:                                            # gap du jour (live uniquement)
        cur = _coingecko_oi(symbol)
        if cur is not None:
            bn.loc[pd.Timestamp.now(tz="UTC").floor(freq)] = cur
            bn = bn.sort_index()
    return bn if len(bn) else None


def _aggregate_oi(symbol: str, timeframe: str, limit: int, source: str,
                  start=None, end=None) -> "pd.Series | None":
    """Somme (USD) de l'OI multi-venues, alignée sur l'union des horodatages.

    `source` : 'agg' (OKX+Gate), 'agg3' (Binance archive + OKX + Gate), 'okx', 'gate'.
    `agg3` ajoute l'OI Binance (archive + point CoinGecko) ; si l'archive est indisponible,
    il **se replie automatiquement** sur OKX+Gate. openInterestValue est en USD partout.
    """
    import ccxt  # import paresseux

    ccxt_venues = {"okx": ("okx",), "gate": ("gate",)}.get(source, OI_VENUES)
    series = []
    for name in ccxt_venues:
        try:
            ex = getattr(ccxt, name)({"enableRateLimit": True})
            ex.load_markets()
            series.append(_oi_series(ex, symbol, timeframe, limit))
        except Exception:
            continue
    if source == "agg3":
        try:
            series.append(_binance_oi_series(symbol, timeframe, limit, start, end))  # None → repli
        except Exception:
            pass
    return _combine_oi(series)


def fetch_open_interest(symbol: str, timeframe: str = "1h", limit: int = 300,
                        source: str = "agg", start=None, end=None) -> "pd.DataFrame | None":
    """Historique d'Open Interest (perp) aligné sur les barres, indexé ts UTC (col `oi`).

    OI = donnée *futures* ; Binance `fapi` et Bybit sont géo-restreints ici. `source` :
    'agg' (OKX+Gate), 'agg3' (Binance archive + OKX + Gate, repli auto sur agg si l'archive
    tombe), 'okx', 'gate'. `start`/`end` ciblent l'OI Binance d'un **intervalle historique**
    (ex. mars, via les quotidiens d'archive). Tolérant : None si indisponible (analyse sans OI).
    """
    try:
        agg = _aggregate_oi(symbol, timeframe, limit, source, start, end)
        return None if agg is None else pd.DataFrame({"oi": agg})
    except Exception:
        return None


# Conversion timeframe ccxt -> fréquence pandas pour le resampling des bougies d'OI.
_TF_FREQ = {"1m": "1min", "5m": "5min", "15m": "15min", "30m": "30min",
            "1h": "1h", "4h": "4h", "1d": "1D"}


def fetch_open_interest_ohlc(symbol: str, timeframe: str = "1h", limit: int = 300,
                             source: str = "agg", fine: str | None = None,
                             start=None, end=None) -> "pd.DataFrame | None":
    """Bougies OHLC d'Open Interest agrégé : on agrège l'OI *fin* multi-venues puis on le
    resample en `timeframe` (open=1ʳᵉ, high=max, low=min, close=dernière obs de la période).
    Retourne un DataFrame [open, high, low, close] (USD) indexé ts UTC, ou None.

    `fine` (granularité source) est choisie selon `timeframe` : 5m pour les TF fines, 1h
    pour les TF ≥ 4h (couvre ~12 j sur OKX/Gate). `start`/`end` ciblent une fenêtre historique.
    """
    try:
        if fine is None:
            fine = "5m" if timeframe in ("5m", "15m", "30m", "1h") else "1h"
        fine_min = {"5m": 5, "1h": 60}.get(fine, 5)
        tf_min = {"5m": 5, "15m": 15, "30m": 30, "1h": 60, "4h": 240, "1d": 1440}.get(timeframe, 60)
        fine_limit = min(1000, max(int(limit * tf_min / fine_min), 300))
        agg = _aggregate_oi(symbol, fine, fine_limit, source, start, end)
        if agg is None:
            return None
        freq = _TF_FREQ.get(timeframe, "1h")
        ohlc = agg.resample(freq).agg(["first", "max", "min", "last"]).dropna()
        ohlc.columns = ["open", "high", "low", "close"]
        return ohlc if len(ohlc) else None
    except Exception:
        return None

