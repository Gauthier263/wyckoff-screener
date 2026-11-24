"""structure.py — structure de prix haute timeframe : la base du biais.

Reconstitue, de façon testable hors-ligne, les repères que CrypNuevo pose avant toute
lecture (cf. `research/crypnuevo_methode.md`) :

- **ranges emboîtés** : bornes et milieu, du range majeur au sous-range courant ;
- **déviation** : sortie du range suivie d'un retour dedans — un spring ou un upthrust à
  l'échelle de la timeframe lue ;
- **acceptance** : un niveau n'est franchi qu'après des **clôtures** du bon côté, jamais sur
  une mèche. C'est la règle qui manquait le 22/11 ;
- **Three Taps** : trois touches d'un extrême, dont une déviation, avec le **timing** du
  troisième (trop proche du deuxième, il n'accumule pas assez de liquidité) ;
- **mèches** : longues mèches et leurs niveaux 50 % et 100 %, avec leur statut de
  remplissage ;
- **EMA 50** et sur-extension, sur la timeframe lue.

Tout est **pur** : des DataFrames OHLCV entrent, des objets simples sortent. Aucune de ces
fonctions ne touche au réseau, et chacune a son test synthétique.

Vocabulaire : ces objets ne portent pas d'étiquette Wyckoff. Une déviation sous un plancher
*peut* être un spring, mais le dire exige le contexte (volume, OI, cadre top-down). Ici on
mesure la géométrie ; `events.py` et `window.py` nomment.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from ..features import atr, swing_points


# --------------------------------------------------------------------------- niveaux

def cluster_levels(values, tol_pct: float = 0.004) -> list:
    """Regroupe des prix voisins en niveaux (pur).

    Renvoie une liste de dicts `{price, touches, lo, hi}`, triée par nombre de touches
    décroissant : un niveau n'existe que parce que le prix y est revenu.
    """
    vals = sorted(float(v) for v in values if np.isfinite(v))
    if not vals:
        return []
    groups, cur = [], [vals[0]]
    for v in vals[1:]:
        if v <= cur[-1] * (1.0 + tol_pct):
            cur.append(v)
        else:
            groups.append(cur)
            cur = [v]
    groups.append(cur)
    out = [{"price": float(np.median(g)), "touches": len(g),
            "lo": float(min(g)), "hi": float(max(g))} for g in groups]
    return sorted(out, key=lambda d: (-d["touches"], -d["price"]))


# --------------------------------------------------------------------------- ranges

@dataclass
class Range:
    low: float
    high: float
    touches_low: int = 0
    touches_high: int = 0
    start: "pd.Timestamp | None" = None
    end: "pd.Timestamp | None" = None

    @property
    def mid(self) -> float:
        return 0.5 * (self.low + self.high)

    @property
    def height_pct(self) -> float:
        return self.high / self.low - 1.0 if self.low > 0 else float("nan")

    def position(self, price: float) -> float:
        """Position du prix dans le range, 0 = plancher, 1 = plafond (peut sortir de [0,1])."""
        span = self.high - self.low
        return float((price - self.low) / span) if span > 0 else float("nan")

    def zone(self, price: float, edge_pct: float = 0.15) -> str:
        """`bas`, `milieu` ou `haut` — « nothing to do at mid-range »."""
        p = self.position(price)
        if not np.isfinite(p):
            return "indéterminé"
        if p <= edge_pct:
            return "bas"
        if p >= 1.0 - edge_pct:
            return "haut"
        return "milieu"


def find_range(df: pd.DataFrame, left: int = 3, right: int = 3,
               tol_pct: float = 0.006, min_touches: int = 2) -> "Range | None":
    """Range dominant d'une fenêtre : les niveaux les plus retouchés en haut et en bas.

    Contrairement à `features.detect_trading_range`, qui cherche une plage latérale
    récente pour le screener, on retient ici les **bornes les plus défendues** de toute la
    fenêtre, même si le prix les a quittées : c'est ainsi que se lit un range annuel.
    """
    if df is None or len(df) < 2 * (left + right) + 5:
        return None
    sw = swing_points(df, left, right)
    highs = cluster_levels(sw.loc[sw["swing_high"], "high"], tol_pct)
    lows = cluster_levels(sw.loc[sw["swing_low"], "low"], tol_pct)
    if not highs or not lows:
        return None
    top = max((h for h in highs if h["touches"] >= min_touches),
              key=lambda d: (d["touches"], d["price"]), default=highs[0])
    bot = min((l for l in lows if l["touches"] >= min_touches),
              key=lambda d: (-d["touches"], d["price"]), default=lows[0])
    if top["price"] <= bot["price"]:
        return None
    return Range(low=bot["price"], high=top["price"],
                 touches_low=bot["touches"], touches_high=top["touches"],
                 start=df.index[0], end=df.index[-1])


def nested_ranges(df: pd.DataFrame, windows=(None, 180, 60), **kw) -> list:
    """Ranges emboîtés, du plus large au plus serré (`None` = toute la fenêtre).

    Il lit un range annuel en Daily **et** un sous-range de quelques semaines : les deux
    coexistent, et c'est l'emboîtement qui situe le prix.
    """
    out = []
    for w in windows:
        sub = df if w is None else df.tail(int(w))
        r = find_range(sub, **kw)
        if r is not None:
            out.append(r)
    return out


# --------------------------------------------------------------------------- acceptance

def acceptance(df: pd.DataFrame, level: float, side: str = "above",
               min_closes: int = 2, lookback: int = 10) -> dict:
    """Le niveau est-il *accepté*, c'est-à-dire tenu en **clôture** ? (pur)

    « Acceptance comes from a solid retest/consolidation of said area » : une mèche ne
    valide rien. On compte les clôtures du bon côté sur les `lookback` dernières barres,
    et on exige `min_closes` clôtures **consécutives** pour parler d'acceptance.

    Renvoie `{accepted, consecutive, closes_beyond, wicked_only, bars}`. `wicked_only` est
    vrai quand le prix a dépassé le niveau en séance sans jamais y clôturer : c'est la
    signature d'une déviation, pas d'une cassure.
    """
    tail = df.tail(int(lookback))
    if tail.empty:
        return {"accepted": False, "consecutive": 0, "closes_beyond": 0,
                "wicked_only": False, "bars": 0}
    beyond = tail["close"] > level if side == "above" else tail["close"] < level
    touched = (tail["high"] > level) if side == "above" else (tail["low"] < level)
    run = 0
    for v in reversed(beyond.tolist()):
        if v:
            run += 1
        else:
            break
    return {"accepted": run >= int(min_closes), "consecutive": int(run),
            "closes_beyond": int(beyond.sum()),
            "wicked_only": bool(touched.any() and not beyond.any()),
            "bars": int(len(tail))}


# --------------------------------------------------------------------------- déviation

@dataclass
class Deviation:
    side: str                 # "sous le plancher" / "au-dessus du plafond"
    level: float
    extreme: float
    extreme_at: "pd.Timestamp | None"
    bars_out: int
    reclaimed: bool
    reclaimed_at: "pd.Timestamp | None" = None
    depth_pct: float = 0.0


def detect_deviation(df: pd.DataFrame, rng: Range, max_bars_out: int = 10,
                     min_depth_pct: float = 0.001) -> "Deviation | None":
    """Sortie du range suivie d'un retour dedans, sur la fin de la fenêtre (pur).

    C'est la lecture qui manquait le 22/11 : la mèche à 55 130 sortait sous le plancher du
    range annuel puis y revenait. À l'échelle Daily, une telle déviation est un **signal de
    réévaluation**, pas une cassure. On ne l'étiquette pas « spring » ici : il y faut le
    contexte.
    """
    if df is None or df.empty or rng is None:
        return None
    candidates = []
    for side, level, out_mask, extreme_col in (
            ("sous le plancher", rng.low, df["low"] < rng.low * (1 - min_depth_pct), "low"),
            ("au-dessus du plafond", rng.high, df["high"] > rng.high * (1 + min_depth_pct), "high")):
        if not out_mask.any():
            continue
        idx = np.flatnonzero(out_mask.to_numpy())
        # dernier épisode de sortie contigu (tolérance d'une barre rentrée)
        start = idx[-1]
        for j in range(len(idx) - 1, 0, -1):
            if idx[j] - idx[j - 1] <= 2:
                start = idx[j - 1]
            else:
                break
        seg = df.iloc[start:]
        extreme = float(seg[extreme_col].min() if side.startswith("sous")
                        else seg[extreme_col].max())
        at = seg[extreme_col].idxmin() if side.startswith("sous") else seg[extreme_col].idxmax()
        after = df.loc[at:]
        back = ((after["close"] > level) if side.startswith("sous")
                else (after["close"] < level))
        reclaimed = bool(back.any())
        bars_out = int(out_mask.iloc[start:].sum())
        depth = abs(extreme / level - 1.0)
        candidates.append((start, bars_out, Deviation(
            side=side, level=float(level), extreme=extreme, extreme_at=at,
            bars_out=bars_out, reclaimed=reclaimed,
            reclaimed_at=(after.index[back.argmax()] if reclaimed else None),
            depth_pct=float(depth))))
    if not candidates:
        return None
    # on ne retient que l'épisode le plus RÉCENT : c'est lui qui décrit l'état actuel.
    # S'il a duré trop longtemps, c'est une cassure installée et non une déviation —
    # et dans ce cas un épisode plus ancien de l'autre côté ne doit pas le masquer.
    start, bars_out, dev = max(candidates, key=lambda c: c[0])
    return None if bars_out > max_bars_out else dev


# --------------------------------------------------------------------------- mèches

@dataclass
class Wick:
    direction: str            # "basse" ou "haute"
    at: "pd.Timestamp"
    base: float               # corps : max(open, close) pour une mèche haute
    tip: float                # extrémité de la mèche
    atr_ratio: float
    half: float = field(init=False)
    filled_half: bool = False
    filled_full: bool = False
    bars_to_half: "int | None" = None

    def __post_init__(self):
        self.half = 0.5 * (self.base + self.tip)


def find_wicks(df: pd.DataFrame, min_atr: float = 1.0, atr_period: int = 14,
               lookback: int = 60) -> list:
    """Longues mèches et leur remplissage à 50 % et 100 % (pur).

    « Long wicks tend to fill sooner rather than later, at least the 50 % level. » On ne
    décide pas ici si elle se remplira : on mesure ce qui s'est passé depuis. L'étude
    statistique de la règle est dans `research/structure_rules.md`.
    """
    if df is None or len(df) < atr_period + 2:
        return []
    a = atr(df, atr_period)
    body_hi = df[["open", "close"]].max(axis=1)
    body_lo = df[["open", "close"]].min(axis=1)
    up = (df["high"] - body_hi) / a
    dn = (body_lo - df["low"]) / a
    out = []
    window = df.tail(int(lookback))
    for ts in window.index:
        for direction, ratio, base, tip in (
                ("haute", float(up.get(ts, np.nan)), float(body_hi[ts]), float(df.at[ts, "high"])),
                ("basse", float(dn.get(ts, np.nan)), float(body_lo[ts]), float(df.at[ts, "low"]))):
            if not np.isfinite(ratio) or ratio < min_atr:
                continue
            w = Wick(direction=direction, at=ts, base=base, tip=tip, atr_ratio=ratio)
            after = df.loc[df.index > ts]
            if len(after):
                # Remplir une mèche, c'est revenir la parcourir depuis le corps vers son
                # extrémité : une mèche HAUTE se remplit en remontant, une mèche BASSE en
                # redescendant. Le 50 % est le milieu corps-extrémité.
                if direction == "haute":
                    w.filled_half = bool((after["high"] >= w.half).any())
                    w.filled_full = bool((after["high"] >= w.tip).any())
                    hit = after.index[after["high"] >= w.half]
                else:
                    w.filled_half = bool((after["low"] <= w.half).any())
                    w.filled_full = bool((after["low"] <= w.tip).any())
                    hit = after.index[after["low"] <= w.half]
                if len(hit):
                    w.bars_to_half = int(df.index.get_loc(hit[0]) - df.index.get_loc(ts))
            out.append(w)
    return sorted(out, key=lambda w: w.atr_ratio, reverse=True)


# --------------------------------------------------------------------------- three taps

@dataclass
class Taps:
    level: float
    side: str                 # "plancher" ou "plafond"
    times: list
    prices: list
    deviation_index: "int | None"
    gaps: list                # écarts en barres entre touches successives
    third_too_early: bool

    @property
    def count(self) -> int:
        return len(self.times)


def detect_taps(df: pd.DataFrame, level: float, side: str = "plancher",
                tol_pct: float = 0.008, min_gap: int = 3,
                early_ratio: float = 0.5) -> "Taps | None":
    """Touches successives d'un extrême, avec le **timing** du troisième (pur).

    « If we get the three taps pattern, the third hit should ideally come later and not
    almost immediately after the second. Otherwise it won't draw in enough liquidity. »
    `third_too_early` est vrai quand l'écart deux→trois est plus court que `early_ratio`
    fois l'écart un→deux.
    """
    if df is None or df.empty or not np.isfinite(level):
        return None
    if side == "plancher":
        hit = df["low"] <= level * (1 + tol_pct)
        price_col, dev_cmp = "low", lambda p: p < level * (1 - tol_pct)
    else:
        hit = df["high"] >= level * (1 - tol_pct)
        price_col, dev_cmp = "high", lambda p: p > level * (1 + tol_pct)
    idx = np.flatnonzero(hit.to_numpy())
    if len(idx) == 0:
        return None
    groups, cur = [], [idx[0]]
    for i in idx[1:]:
        if i - cur[-1] <= min_gap:
            cur.append(i)
        else:
            groups.append(cur)
            cur = [i]
    groups.append(cur)
    times, prices, best = [], [], []
    for g in groups:
        sub = df.iloc[g]
        j = sub[price_col].idxmin() if side == "plancher" else sub[price_col].idxmax()
        times.append(j)
        prices.append(float(df.at[j, price_col]))
        best.append(int(df.index.get_loc(j)))
    dev = next((k for k, p in enumerate(prices) if dev_cmp(p)), None)
    gaps = [best[k + 1] - best[k] for k in range(len(best) - 1)]
    early = bool(len(gaps) >= 2 and gaps[1] < early_ratio * gaps[0])
    return Taps(level=float(level), side=side, times=times, prices=prices,
                deviation_index=dev, gaps=gaps, third_too_early=early)


# --------------------------------------------------------------------------- EMA

def ema_state(df: pd.DataFrame, period: int = 50, atr_period: int = 14) -> dict:
    """EMA 50 de la timeframe lue, écart du prix en ATR, pente (pur).

    « Price is very overextended from the EMAs so we should get a quick recovery. »
    `stretch_atr` mesure cette sur-extension ; `slope_pct` donne le sens de la tendance.
    """
    if df is None or len(df) < period:
        return {"ema": None, "stretch_atr": None, "slope_pct": None, "above": None}
    e = df["close"].ewm(span=period, adjust=False).mean()
    a = atr(df, atr_period)
    last = float(df["close"].iloc[-1])
    ema = float(e.iloc[-1])
    span = max(float(a.iloc[-1]), 1e-9)
    prev = float(e.iloc[-min(len(e), period // 2 + 1)])
    return {"ema": ema, "stretch_atr": (last - ema) / span,
            "slope_pct": (ema / prev - 1.0) if prev else None, "above": last > ema}
