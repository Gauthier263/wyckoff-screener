"""wick_study.py — la règle des mèches de CrypNuevo, étudiée comme un déséquilibre de liquidité.

La règle, telle qu'il la formule et que Gauthier l'a précisée :

> Une longue mèche (1D, 4h, 1h le plus souvent) est un **déséquilibre de liquidité** : le
> prix a traversé une zone trop vite, sans y échanger. Dans un scénario d'accumulation, si
> le prix doit monter, il ne montera pas **avant** d'avoir retracé 50 % ou 100 % de la
> mèche basse. Inversement en distribution. Le retest peut être immédiat ou prendre
> plusieurs bougies (« 5 à 8 bougies hebdo » pour une mèche 1W).

Trois itérations, chacune ajoutant une dimension que la précédente ignorait :

1. **Délai** (`delays`) : sur un horizon long, en combien de bougies de la timeframe de la
   mèche le 50 % puis le 100 % sont-ils retestés ? Courbe de survie, contre un témoin.
2. **Déséquilibre réel** (`ltf_imbalance`) : avec des bougies plus fines, la zone de la
   mèche a-t-elle vraiment été traversée **sans échange** ? Une mèche à fort volume dans sa
   zone n'est pas un vide : c'est une absorption (un rejet réel, Wyckoff dirait un test).
3. **Contexte** : liquidations sur la mèche, position par rapport au range, structure qui
   tient — et une règle combinée, validée hors échantillon.

Tout ce qui calcule est pur et testé ; le réseau n'intervient que dans `load`.
"""
from __future__ import annotations

import os

import numpy as np
import pandas as pd

from ..data import CACHE_DIR
from ..features import atr

TF_MINUTES = {"5m": 5, "15m": 15, "1h": 60, "4h": 240, "1d": 1440}
# bougie fine utilisée pour radiographier une mèche de chaque timeframe
LTF_FOR = {"1h": "5m", "4h": "15m", "1d": "1h"}


# ============================================================ chargement (seul accès réseau)

def load(symbol: str = "BTC/USDT", timeframe: str = "4h", start="2023-01-01",
         end=None) -> pd.DataFrame:
    """OHLCV paginé avec cache parquet (un fichier par symbole et timeframe)."""
    from .. import data as D

    end = pd.Timestamp(end or pd.Timestamp.now(tz="UTC"))
    if end.tzinfo is None:
        end = end.tz_localize("UTC")
    start = pd.Timestamp(start)
    if start.tzinfo is None:
        start = start.tz_localize("UTC")
    d = os.path.join(CACHE_DIR, "htf")
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, f"klines_{symbol.replace('/', '')}_{timeframe}.parquet")
    have = None
    try:
        have = pd.read_parquet(path)
    except Exception:
        pass
    since = start
    if have is not None and len(have) and have.index[0] <= start:
        since = have.index[-1]
    ex = D.get_exchange("binance")
    step = TF_MINUTES[timeframe] * 60_000
    cur, stop, rows = int(since.timestamp() * 1000), int(end.timestamp() * 1000), []
    while cur < stop:
        batch = ex.fetch_ohlcv(symbol, timeframe=timeframe, since=cur, limit=1000)
        if not batch:
            break
        rows += batch
        nxt = batch[-1][0] + step
        if nxt <= cur:
            break
        cur = nxt
    new = pd.DataFrame(rows, columns=["ts", "open", "high", "low", "close", "volume"])
    if len(new):
        new["ts"] = pd.to_datetime(new["ts"], unit="ms", utc=True)
        new = new.set_index("ts")
    out = pd.concat([have, new]) if have is not None and len(new) else (have if have is not None else new)
    out = out[~out.index.duplicated(keep="last")].sort_index()
    try:
        out.to_parquet(path)
    except Exception:
        pass
    return out[(out.index >= start) & (out.index <= end)]


def load_taker_delta(symbol: str = "BTC/USDT", timeframe: str = "4h",
                     start="2020-01-01") -> pd.Series:
    """Delta agressif spot par bougie (taker achat − taker vente, en coin), sur tout
    l'historique (colonne 9 des klines Binance), avec cache parquet.

    `data.fetch_taker_delta` ne lit que les dernières bougies ; ici on pagine avec
    `startTime` pour couvrir 2020 à aujourd'hui. Spot uniquement : le perp n'est pas
    accessible en historique profond depuis cet environnement.
    """
    from .. import data as D

    d = os.path.join(CACHE_DIR, "htf")
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, f"delta_{symbol.replace('/', '')}_{timeframe}.parquet")
    try:
        have = pd.read_parquet(path)["delta"]
    except Exception:
        have = None
    start = pd.Timestamp(start, tz="UTC") if pd.Timestamp(start).tzinfo is None else pd.Timestamp(start)
    cur = int((have.index[-1] if have is not None and len(have) and have.index[0] <= start
               else start).timestamp() * 1000)
    stop = int(pd.Timestamp.now(tz="UTC").timestamp() * 1000)
    ex = D.get_exchange("binance")
    sym = symbol.replace("/", "")
    rows = []
    while cur < stop:
        raw = ex.publicGetKlines({"symbol": sym, "interval": timeframe, "startTime": cur,
                                  "limit": 1000})
        if not raw:
            break
        for r in raw:
            v, tb = float(r[5]), float(r[9])
            rows.append((int(r[0]), tb - (v - tb)))
        nxt = int(raw[-1][0]) + TF_MINUTES[timeframe] * 60_000
        if nxt <= cur:
            break
        cur = nxt
    new = pd.Series({pd.to_datetime(t, unit="ms", utc=True): x for t, x in rows}, dtype=float)
    out = pd.concat([have, new]) if have is not None else new
    out = out[~out.index.duplicated(keep="last")].sort_index()
    out.name = "delta"
    try:
        out.to_frame().to_parquet(path)
    except Exception:
        pass
    return out[out.index >= start]


# ============================================================ détection

def detect_wicks(df: pd.DataFrame, min_atr: float = 1.0, atr_period: int = 14,
                 min_sep: int = 10) -> pd.DataFrame:
    """Longues mèches, une ligne par événement (pur).

    `min_sep` : deux mèches de même sens à moins de `min_sep` bougies sont un seul épisode
    — on garde la plus grande. Sans cela, une zone agitée produirait des grappes de
    mèches aux futurs presque identiques, comptées comme autant d'observations
    indépendantes.

    Colonnes : `i` (position), `at`, `direction` (`basse` = scénario accumulation, `haute`
    = distribution), `base` (bord du corps), `tip` (extrémité), `half`, `close`, `atr`,
    `size_atr`, `wick_share` (part de la mèche dans le range de la bougie).
    """
    a = atr(df, atr_period)
    body_hi = df[["open", "close"]].max(axis=1)
    body_lo = df[["open", "close"]].min(axis=1)
    rng = (df["high"] - df["low"]).replace(0, np.nan)
    out = []
    for direction, size, base, tip in (
            ("basse", body_lo - df["low"], body_lo, df["low"]),
            ("haute", df["high"] - body_hi, body_hi, df["high"])):
        ratio = size / a
        cand = np.flatnonzero((ratio >= min_atr).to_numpy() & np.isfinite(ratio.to_numpy()))
        kept, last = [], -10**9
        for i in cand:
            if i < atr_period:
                continue
            if kept and i - last < min_sep:
                if ratio.iloc[i] > ratio.iloc[kept[-1]]:
                    kept[-1] = i
                    last = i
                continue
            kept.append(i)
            last = i
        for i in kept:
            out.append({"i": int(i), "at": df.index[i], "direction": direction,
                        "base": float(base.iloc[i]), "tip": float(tip.iloc[i]),
                        "half": 0.5 * float(base.iloc[i] + tip.iloc[i]),
                        "close": float(df["close"].iloc[i]), "atr": float(a.iloc[i]),
                        "size_atr": float(ratio.iloc[i]),
                        "wick_share": float(size.iloc[i] / rng.iloc[i])})
    return pd.DataFrame(out).sort_values("i").reset_index(drop=True) if out else pd.DataFrame()


# ============================================================ itération 1 : délai

def first_touch(df: pd.DataFrame, i: int, level: float, side: str, horizon: int):
    """Nombre de bougies jusqu'au premier contact avec `level`, ou None (pur).

    `side="down"` : le prix doit redescendre jusqu'au niveau (low <= level) ;
    `side="up"` : il doit remonter (high >= level). La bougie de la mèche elle-même est
    exclue : on cherche un **retour**.
    """
    fut = df.iloc[i + 1:i + 1 + horizon]
    if fut.empty:
        return None
    hit = (fut["low"] <= level) if side == "down" else (fut["high"] >= level)
    arr = hit.to_numpy()
    return int(np.argmax(arr)) + 1 if arr.any() else None


def delays(df: pd.DataFrame, wicks: pd.DataFrame, horizon: int = 300,
           control_offset: int = 60) -> pd.DataFrame:
    """Délai de retest du 50 % et du 100 %, et du témoin (pur).

    Témoin : la bougie `control_offset` plus tôt, à laquelle on applique le même écart au
    cours (en ATR de cette bougie) que celui du niveau testé. Il dit à quelle vitesse un
    niveau *quelconque* aussi éloigné est touché, dans la même période de marché.
    """
    rows = []
    n = len(df)
    a = atr(df)
    for w in wicks.itertuples():
        if w.i + horizon >= n:
            continue
        side = "down" if w.direction == "basse" else "up"
        r = {"at": w.at, "direction": w.direction, "size_atr": w.size_atr,
             "d50": first_touch(df, w.i, w.half, side, horizon),
             "d100": first_touch(df, w.i, w.tip, side, horizon)}
        j = w.i - control_offset
        if j > 14 and np.isfinite(a.iloc[j]):
            cj, aj = float(df["close"].iloc[j]), float(a.iloc[j])
            k50 = abs(w.close - w.half) / w.atr
            k100 = abs(w.close - w.tip) / w.atr
            sgn = -1 if side == "down" else 1
            r["t50"] = first_touch(df, j, cj + sgn * k50 * aj, side, horizon)
            r["t100"] = first_touch(df, j, cj + sgn * k100 * aj, side, horizon)
        rows.append(r)
    return pd.DataFrame(rows)


def survival(d: pd.Series, checkpoints=(1, 3, 5, 8, 13, 21, 50, 100, 300)) -> dict:
    """Part retestée au plus tard à chaque point de contrôle (pur)."""
    n = len(d)
    if n == 0:
        return {}
    vals = d.dropna().to_numpy()
    return {c: float((vals <= c).sum()) / n for c in checkpoints}


def precedence(df: pd.DataFrame, wicks: pd.DataFrame, target_atr: float = 2.0,
               horizon: int = 120, control_offset: int = 60) -> pd.DataFrame:
    """La règle d'ordre : le retest du 50 % arrive-t-il **avant** le mouvement du scénario ?

    Mouvement du scénario = `target_atr` ATR depuis la clôture de la bougie de mèche, vers
    le haut après une mèche basse (accumulation), vers le bas après une mèche haute
    (distribution). On ne garde que les cas où ce mouvement a eu lieu. Bougie commune aux
    deux événements : `indéterminé`, exclu (sans données intra-bougie on ne tranche pas).
    Le témoin rejoue le calcul sur la bougie `control_offset` plus tôt, même écart en ATR.
    """
    a = atr(df)
    n = len(df)

    def order(i, close, span, k, down):
        lvl = close - k * span if down else close + k * span
        tgt = close + target_atr * span if down else close - target_atr * span
        ia = first_touch(df, i, lvl, "down" if down else "up", horizon)
        ib = first_touch(df, i, tgt, "up" if down else "down", horizon)
        if ib is None:
            return "pas de mouvement"
        if ia is None or ia > ib:
            return "mouvement d'abord"
        if ia < ib:
            return "retest d'abord"
        return "indéterminé"

    rows = []
    for w in wicks.itertuples():
        if w.i + horizon >= n:
            continue
        down = w.direction == "basse"
        k = abs(w.close - w.half) / w.atr
        r = {"at": w.at, "direction": w.direction, "verdict": order(w.i, w.close, w.atr, k, down)}
        j = w.i - control_offset
        if j > 14 and np.isfinite(a.iloc[j]):
            r["témoin"] = order(j, float(df["close"].iloc[j]), float(a.iloc[j]), k, down)
        rows.append(r)
    return pd.DataFrame(rows)


# ============================================================ itération 2 : vrai déséquilibre

def ltf_imbalance(ltf: pd.DataFrame, t0: pd.Timestamp, t1: pd.Timestamp,
                  lo: float, hi: float) -> dict:
    """Radiographie d'une mèche avec les bougies fines de sa bougie mère (pur).

    On répartit le volume de chaque bougie fine uniformément sur son propre range, puis on
    regarde quelle part du volume total de la bougie mère tombe dans la zone [lo, hi] de la
    mèche, rapportée à la part de la zone dans le range total. Résultat :

    - `vol_density` < 1 : la zone a été **traversée sans échange** — un vrai vide, le
      déséquilibre dont parle la règle ;
    - `vol_density` > 1 : la zone a concentré le volume — une **absorption**, la zone a été
      traitée, il n'y a rien à « rééquilibrer ».

    `bars_in_zone` : nombre de bougies fines qui ont touché la zone ; `minutes` est ce même
    temps passé. Une mèche formée en une ou deux bougies fines est un aller-retour éclair.
    """
    seg = ltf[(ltf.index >= t0) & (ltf.index < t1)]
    if seg.empty or hi <= lo:
        return {"vol_density": np.nan, "bars_in_zone": np.nan, "vol_share": np.nan}
    p_lo, p_hi = float(seg["low"].min()), float(seg["high"].max())
    if p_hi <= p_lo:
        return {"vol_density": np.nan, "bars_in_zone": np.nan, "vol_share": np.nan}
    total = float(seg["volume"].sum())
    in_zone = 0.0
    touched = 0
    for r in seg.itertuples():
        span = r.high - r.low
        ov = max(0.0, min(r.high, hi) - max(r.low, lo))
        if ov > 0 or (span == 0 and lo <= r.low <= hi):
            touched += 1
        if span > 0:
            in_zone += r.volume * ov / span
        elif lo <= r.low <= hi:
            in_zone += r.volume
    share_vol = in_zone / total if total > 0 else np.nan
    share_px = (hi - lo) / (p_hi - p_lo)
    return {"vol_density": share_vol / share_px if share_px > 0 else np.nan,
            "bars_in_zone": touched, "vol_share": share_vol}


def annotate_imbalance(wicks: pd.DataFrame, ltf: pd.DataFrame, tf: str) -> pd.DataFrame:
    """Ajoute à chaque mèche sa radiographie fine (`vol_density`, `bars_in_zone`)."""
    step = pd.Timedelta(minutes=TF_MINUTES[tf])
    rows = []
    for w in wicks.itertuples():
        lo, hi = sorted((w.tip, w.base))
        rows.append(ltf_imbalance(ltf, w.at, w.at + step, lo, hi))
    return pd.concat([wicks.reset_index(drop=True), pd.DataFrame(rows)], axis=1)


# ============================================================ outils de lecture

def wilson(k: int, n: int, z: float = 1.96) -> tuple:
    if n <= 0:
        return (np.nan, np.nan)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    m = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - m), min(1.0, c + m))


def rate(mask) -> str:
    mask = pd.Series(mask).astype(bool)
    k, n = int(mask.sum()), int(len(mask))
    if n == 0:
        return "-"
    lo, hi = wilson(k, n)
    return f"{k / n:.2f} [{lo:.2f}-{hi:.2f}]"
