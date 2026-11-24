"""sources.py — couche données du biais HTF : sources gratuites, sans clé payante.

Chaque source se découpe en deux : un *fetcher* (réseau, caché sur disque) et un
*parser* **pur** `_parse_*` testable hors-ligne. Toute panne réseau renvoie une
structure vide plutôt qu'une exception : le biais se calcule alors sans cette brique
et le rapport dit laquelle manque.

Sources (toutes vérifiées joignables depuis l'environnement, 24/11/2026) :

- **Hyperliquid** (`api.hyperliquid.xyz`, `stats-data.hyperliquid.xyz`) — positions perp
  **réelles** des plus gros comptes, avec leur **vrai prix de liquidation**. Le leaderboard
  public donne ~46 700 adresses ; le top 1 000 par equity pèse ~87 % du capital. C'est la
  seule ancre *observée* de la carte de liquidation (tout le reste est estimé).
- **SmartMoney** (`api.smartmoneyapi.com`) — liquidations **réalisées** par niveau de prix
  (Binance, OKX, Bybit, Bitget), sans clé. Dit où le carburant a **déjà été consommé**
  (« liquidation cluster hit ») — l'inverse d'une heatmap prévisionnelle.
- **Deribit** (`www.deribit.com`) — OI des options BTC par strike : max pain et murs de
  strikes, qui agissent en aimants/résistances autour des expirations.
- **ForexFactory JSON** (`nfs.faireconomy.media`) — calendrier macro de la semaine
  (CPI, FOMC, NFP…) avec niveau d'impact : la *fenêtre* de volatilité, jamais la direction.
- **Yahoo Finance** (`query1.finance.yahoo.com`) — S&P 500, NVDA (corrélation « risk
  appetite ») et `BTC=F` (futures CME, pour les gaps week-end historiques).
- **alternative.me** — Fear & Greed, lu à contre-courant.
"""
from __future__ import annotations

import json
import os
import time
import urllib.request

import pandas as pd

from ..data import CACHE_DIR

HL_INFO = "https://api.hyperliquid.xyz/info"
HL_LEADERBOARD = "https://stats-data.hyperliquid.xyz/Mainnet/leaderboard"
SMARTMONEY_BASE = "https://api.smartmoneyapi.com/v1"
DERIBIT_BASE = "https://www.deribit.com/api/v2/public"
MACRO_CALENDAR = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
YAHOO_CHART = "https://query1.finance.yahoo.com/v8/finance/chart"
FNG_URL = "https://api.alternative.me/fng/"

# En-tête neutre : aucune donnée personnelle (nom, e-mail, projet) ne sort d'ici.
_UA = "wyckoff-screener/1.0 (research client)"


def _cache_path(key: str) -> str:
    d = os.path.join(CACHE_DIR, "htf")
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, key + ".json")


def _http_json(url: str, payload: "dict | None" = None, timeout: int = 30):
    data = json.dumps(payload).encode() if payload is not None else None
    headers = {"User-Agent": _UA}
    if data is not None:
        headers["content-type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def _cached_json(key: str, url: str, payload=None, ttl: float = 300.0, timeout: int = 30):
    """Appel réseau avec cache disque de `ttl` secondes. En cas d'échec, sert le cache
    périmé s'il existe (mieux vaut une donnée datée qu'aucune), sinon None."""
    path = _cache_path(key)
    try:
        age = time.time() - os.path.getmtime(path)
        if age < ttl:
            with open(path) as f:
                return json.load(f)
    except Exception:
        pass
    try:
        out = _http_json(url, payload, timeout)
    except Exception:
        try:
            with open(path) as f:
                return json.load(f)
        except Exception:
            return None
    try:
        with open(path, "w") as f:
            json.dump(out, f)
    except Exception:
        pass
    return out


# --------------------------------------------------------------------------- Hyperliquid

def _parse_leaderboard(payload, top_n: int = 1000) -> list:
    """Adresses du leaderboard triées par equity décroissante (pur, testable)."""
    rows = payload.get("leaderboardRows", payload) if isinstance(payload, dict) else payload
    if not isinstance(rows, list):
        return []
    out = []
    for r in rows:
        addr = r.get("ethAddress") or r.get("user")
        if not addr:
            continue
        try:
            eq = float(r.get("accountValue") or 0.0)
        except (TypeError, ValueError):
            continue
        out.append((addr, eq))
    out.sort(key=lambda x: x[1], reverse=True)
    return [a for a, _ in out[:top_n]]


def _parse_clearinghouse(states, coin: str = "BTC") -> pd.DataFrame:
    """États `clearinghouseState` -> positions sur `coin` (pur, testable).

    Colonnes : `size` (signé, + = long), `side`, `entry`, `liq_px` (prix de liquidation
    **réel** renvoyé par le protocole, None si aucun), `leverage`, `notional`.
    Un compte en *cross margin* a un prix de liquidation très éloigné du prix spot : c'est
    une information, pas un bug — ces positions ne nourrissent aucun amas proche.
    """
    rows = []
    for st in states:
        if not isinstance(st, dict):
            continue
        for ap in st.get("assetPositions", []) or []:
            po = (ap or {}).get("position") or {}
            if po.get("coin") != coin:
                continue
            try:
                size = float(po.get("szi") or 0.0)
            except (TypeError, ValueError):
                continue
            if size == 0:
                continue
            liq = po.get("liquidationPx")
            lev = (po.get("leverage") or {})
            rows.append({
                "size": size,
                "side": "long" if size > 0 else "short",
                "entry": _f(po.get("entryPx")),
                "liq_px": _f(liq),
                "leverage": _f(lev.get("value")),
                "margin": lev.get("type"),
                "notional": abs(size) * (_f(po.get("entryPx")) or 0.0),
            })
    return pd.DataFrame(rows, columns=["size", "side", "entry", "liq_px",
                                       "leverage", "margin", "notional"])


def _f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def fetch_hyperliquid_positions(coin: str = "BTC", top_n: int = 600,
                                workers: int = 8, ttl: float = 900.0) -> pd.DataFrame:
    """Positions perp réelles des `top_n` plus gros comptes Hyperliquid sur `coin`.

    ~600 comptes en ~25 s avec 8 fils. Renvoie un DataFrame vide si l'API est
    injoignable. Donnée **publique on-chain** : aucune information personnelle.
    """
    from concurrent.futures import ThreadPoolExecutor

    lb = _cached_json("hl_leaderboard", HL_LEADERBOARD, ttl=3600.0, timeout=60)
    if not lb:
        return _parse_clearinghouse([], coin)
    addrs = _parse_leaderboard(lb, top_n)
    key = f"hl_states_{coin}_{top_n}"
    path = _cache_path(key)
    try:
        if time.time() - os.path.getmtime(path) < ttl:
            with open(path) as f:
                return _parse_clearinghouse(json.load(f), coin)
    except Exception:
        pass

    def one(a):
        try:
            return _http_json(HL_INFO, {"type": "clearinghouseState", "user": a}, 20)
        except Exception:
            return None

    with ThreadPoolExecutor(workers) as ex:
        states = [s for s in ex.map(one, addrs) if s]
    try:
        with open(path, "w") as f:
            json.dump(states, f)
    except Exception:
        pass
    return _parse_clearinghouse(states, coin)


# --------------------------------------------------------------------------- SmartMoney

def _parse_realized_liquidations(payload) -> pd.DataFrame:
    """Clusters de liquidations **réalisées** par niveau de prix (pur, testable)."""
    if not isinstance(payload, dict):
        return pd.DataFrame(columns=["price", "notional", "long_notional",
                                     "short_notional", "count", "dominant_side"])
    cl = payload.get("clusters") or []
    df = pd.DataFrame(cl)
    for c in ("price", "notional", "long_notional", "short_notional", "count", "dominant_side"):
        if c not in df.columns:
            df[c] = None
    return df[["price", "notional", "long_notional", "short_notional",
               "count", "dominant_side"]].sort_values("price").reset_index(drop=True)


def fetch_realized_liquidations(symbol: str = "BTC", window_minutes: int = 240,
                                buckets: int = 50, ttl: float = 300.0) -> pd.DataFrame:
    """Liquidations **déjà exécutées** par niveau de prix (multi-exchanges, sans clé).

    Sert à savoir quels amas ont été **consommés** : un amas touché n'attire plus le prix.
    """
    url = (f"{SMARTMONEY_BASE}/liquidations/heatmap?symbol={symbol}"
           f"&window_minutes={int(window_minutes)}&price_buckets={int(buckets)}")
    return _parse_realized_liquidations(
        _cached_json(f"sm_heatmap_{symbol}_{window_minutes}_{buckets}", url, ttl=ttl))


# --------------------------------------------------------------------------- Deribit

def _parse_deribit_options(payload) -> pd.DataFrame:
    """`get_book_summary_by_currency` -> OI par (expiry, strike, type) (pur, testable)."""
    res = payload.get("result", payload) if isinstance(payload, dict) else payload
    rows = []
    for it in res or []:
        name = it.get("instrument_name") or ""
        parts = name.split("-")
        if len(parts) != 4:
            continue
        _, expiry, strike, kind = parts
        try:
            strike = float(strike)
        except ValueError:
            continue
        rows.append({
            "expiry": expiry,
            "strike": strike,
            "type": "call" if kind.upper() == "C" else "put",
            "oi": _f(it.get("open_interest")) or 0.0,
            "mark_iv": _f(it.get("mark_iv")),
            "underlying": _f(it.get("underlying_price")),
        })
    return pd.DataFrame(rows, columns=["expiry", "strike", "type", "oi",
                                       "mark_iv", "underlying"])


def max_pain(options: pd.DataFrame, expiry: "str | None" = None) -> "float | None":
    """Strike qui minimise la valeur intrinsèque totale des options (pur, testable).

    Le *max pain* est le prix où le plus gros notionnel d'options expire sans valeur :
    un aimant connu autour des grosses expirations, jamais une prévision à lui seul.
    """
    if options is None or options.empty:
        return None
    df = options if expiry is None else options[options["expiry"] == expiry]
    if df.empty:
        return None
    strikes = sorted(df["strike"].unique())
    calls = df[df["type"] == "call"]
    puts = df[df["type"] == "put"]
    best, best_pain = None, None
    for s in strikes:
        pain = float(((s - calls["strike"]).clip(lower=0) * calls["oi"]).sum()
                     + ((puts["strike"] - s).clip(lower=0) * puts["oi"]).sum())
        if best_pain is None or pain < best_pain:
            best, best_pain = s, pain
    return best


def strike_walls(options: pd.DataFrame, expiry: "str | None" = None,
                 top_n: int = 5) -> pd.DataFrame:
    """Strikes portant le plus d'OI (murs d'options) — pur, testable."""
    if options is None or options.empty:
        return pd.DataFrame(columns=["strike", "oi", "call_oi", "put_oi"])
    df = options if expiry is None else options[options["expiry"] == expiry]
    if df.empty:
        return pd.DataFrame(columns=["strike", "oi", "call_oi", "put_oi"])
    g = df.groupby("strike").apply(
        lambda x: pd.Series({
            "oi": float(x["oi"].sum()),
            "call_oi": float(x.loc[x["type"] == "call", "oi"].sum()),
            "put_oi": float(x.loc[x["type"] == "put", "oi"].sum()),
        }), include_groups=False)
    return (g.sort_values("oi", ascending=False).head(top_n)
             .reset_index().sort_values("strike").reset_index(drop=True))


def fetch_deribit_options(currency: str = "BTC", ttl: float = 900.0) -> pd.DataFrame:
    url = f"{DERIBIT_BASE}/get_book_summary_by_currency?currency={currency}&kind=option"
    return _parse_deribit_options(_cached_json(f"deribit_{currency}", url, ttl=ttl, timeout=60))


def fetch_dvol(currency: str = "BTC", days: int = 30, ttl: float = 3600.0) -> pd.Series:
    """Indice de volatilité implicite Deribit (DVOL), bougies journalières."""
    end = int(time.time() * 1000)
    start = end - days * 86400_000
    url = (f"{DERIBIT_BASE}/get_volatility_index_data?currency={currency}"
           f"&start_timestamp={start}&end_timestamp={end}&resolution=1D")
    payload = _cached_json(f"dvol_{currency}_{days}", url, ttl=ttl)
    data = ((payload or {}).get("result") or {}).get("data") or []
    if not data:
        return pd.Series(dtype=float)
    idx = pd.to_datetime([r[0] for r in data], unit="ms", utc=True)
    return pd.Series([float(r[4]) for r in data], index=idx, name="dvol")


# --------------------------------------------------------------------------- Macro

_MACRO_KEYWORDS = ("CPI", "FOMC", "Federal Funds", "Non-Farm", "NFP", "PPI", "PCE",
                   "Unemployment", "GDP", "Powell", "Retail Sales", "Jobless")


def _parse_macro_calendar(payload, currencies=("USD",),
                          impacts=("High",)) -> pd.DataFrame:
    """Calendrier ForexFactory -> événements filtrés (pur, testable).

    Donne la **fenêtre** de volatilité attendue, jamais la direction : un CPI ne dit pas
    si le prix monte, il dit quand le marché bougera.
    """
    rows = []
    for e in payload or []:
        if not isinstance(e, dict):
            continue
        if currencies and e.get("country") not in currencies:
            continue
        if impacts and e.get("impact") not in impacts:
            continue
        ts = pd.to_datetime(e.get("date"), errors="coerce", utc=True)
        if pd.isna(ts):
            continue
        rows.append({"time": ts, "title": e.get("title"), "impact": e.get("impact"),
                     "forecast": e.get("forecast"), "previous": e.get("previous")})
    df = pd.DataFrame(rows, columns=["time", "title", "impact", "forecast", "previous"])
    return df.sort_values("time").reset_index(drop=True)


def fetch_macro_calendar(currencies=("USD",), impacts=("High",),
                         ttl: float = 3600.0) -> pd.DataFrame:
    return _parse_macro_calendar(
        _cached_json("macro_week", MACRO_CALENDAR, ttl=ttl), currencies, impacts)


# --------------------------------------------------------------------------- Yahoo

def _parse_yahoo_chart(payload) -> pd.DataFrame:
    """Réponse Yahoo `chart` -> OHLCV indexé en UTC (pur, testable)."""
    cols = ["open", "high", "low", "close", "volume"]
    try:
        r = payload["chart"]["result"][0]
        q = r["indicators"]["quote"][0]
        idx = pd.to_datetime(r["timestamp"], unit="s", utc=True)
    except Exception:
        return pd.DataFrame(columns=cols)
    df = pd.DataFrame({c: q.get(c) for c in cols}, index=idx)
    return df.dropna(how="all")


def fetch_yahoo(symbol: str = "^GSPC", interval: str = "1d",
                range_: str = "6mo", ttl: float = 1800.0) -> pd.DataFrame:
    """OHLCV Yahoo. `^GSPC` = S&P 500, `NVDA`, `BTC=F` = futures CME (gaps week-end)."""
    sym = urllib.parse.quote(symbol, safe="")
    url = f"{YAHOO_CHART}/{sym}?interval={interval}&range={range_}"
    return _parse_yahoo_chart(_cached_json(f"yahoo_{sym}_{interval}_{range_}", url, ttl=ttl))


# --------------------------------------------------------------------------- Sentiment

def _parse_fng(payload) -> pd.Series:
    data = (payload or {}).get("data") or []
    if not data:
        return pd.Series(dtype=float)
    idx = pd.to_datetime([int(d["timestamp"]) for d in data], unit="s", utc=True)
    return pd.Series([float(d["value"]) for d in data], index=idx,
                     name="fear_greed").sort_index()


def fetch_fear_greed(limit: int = 90, ttl: float = 3600.0) -> pd.Series:
    return _parse_fng(_cached_json(f"fng_{limit}", f"{FNG_URL}?limit={limit}", ttl=ttl))
