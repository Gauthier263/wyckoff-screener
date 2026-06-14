"""
liquidity.py — Détecteur de "liquidity void de chute brutale" (façon ICT + mean-reversion).

On cherche une **baisse subite et anormale** (displacement vendeur violent) qui ouvre une
inefficience de prix — un *vide de liquidité* — que le marché tend à venir **rééquilibrer
rapidement** (snap-back / V-recovery), typiquement après une cascade de liquidations ou un
stop-run mécanique (et non une vraie nouvelle fondamentale).

Critères issus de la recherche (sources expertes ICT / microstructure / quant) :
  ÉTAGE A — chute anormale (sur la barre) :
    • rendement z-score ROBUSTE (médiane + MAD, pas σ qui s'auto-masque sur un spike) ≤ ret_z ;
    • amplitude range/ATR ≥ drop_atr ; corps/range ≥ body_frac (vraie barre one-sided) ;
    • volume ≥ vol_ratio_min × moyenne (liquidité *consommée*, signature de cascade).
  ÉTAGE C — réversion (barres suivantes) :
    • on suit la **récupération** du prix vers le haut du vide (fill_frac/fill_status) ;
    • `reclaimed` = clôture revenue au-dessus de l'ouverture de la chute sous `reclaim_bars`
      barres (snap-back précoce = bonus).
  ÉTAGE D — anti « couteau qui tombe » :
    • `in_uptrend` (clôture > MA longue) : on ne privilégie le rééquilibrage que hors downtrend
      — le filtre de tendance est le plus robuste de la littérature. Pénalise le score sinon.

Réserve honnête : le comblement *rapide* n'est pas garanti (≈60 % des inefficiences intraday
restent ouvertes sur la session) ; ce score est une aide à la décision, pas un automate.

`df` doit déjà porter les features (features.add_features : atr, vol_ratio, ret).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd

FillStatus = Literal["open", "partial", "filled"]

_THEORY = (
    "Vide de chute brutale — une baisse violente one-sided (cascade de liquidations / "
    "stop-run) traverse le prix sans contrepartie et laisse une inefficience. Thèse : "
    "l'offre forcée s'épuise, les acheteurs reviennent au rabais → le prix tend à "
    "remonter rééquilibrer le vide (mean-reversion / V-recovery). D'autant plus probable "
    "que la chute est mécanique (pas fondamentale) et qu'on n'est pas en downtrend établi."
)


@dataclass
class VoidThresholds:
    ret_z: float = -2.5          # z-score robuste du rendement (chute anormale)
    drop_atr: float = 1.8        # amplitude range/ATR de la barre de chute
    body_frac: float = 0.6       # corps/range mini (one-sided, vrai displacement)
    vol_ratio_min: float = 3.0   # volume ≥ ×moyenne (liquidité consommée / climax)
    z_window: int = 50           # fenêtre médiane/MAD pour le z robuste
    trend_ma: int = 100          # MA longue pour le gate de tendance
    reclaim_bars: int = 3        # fenêtre de snap-back (clôture > open de la chute)
    partial_floor: float = 0.1   # récupération sous ce seuil = bruit (vide encore "open")
    fill_threshold: float = 1.0  # part récupérée à partir de laquelle le vide est "filled"
    max_dist_atr: float = 4.0    # horizon de proximité (prix→vide) pour le screening


@dataclass
class LiquidityVoid:
    ts: pd.Timestamp         # barre de la chute (origine du vide)
    top: float               # haut du vide = niveau d'avant-chute (cible de récupération)
    bottom: float            # bas du vide = extrême de la chute
    size_atr: float          # amplitude de la chute en ATR
    ret_z: float             # z-score robuste du rendement (négatif)
    vol_ratio: float         # volume de la barre de chute (× moyenne)
    body_frac: float         # corps/range (degré one-sided)
    created_ago: int         # barres depuis la chute (0 = dernière clôturée)
    fill_frac: float         # part récupérée vers le haut du vide [0..1+]
    fill_status: FillStatus
    dist_atr: float          # distance prix courant → bord du vide, en ATR (0 = dedans)
    reclaimed: bool          # snap-back précoce observé (clôture > open sous reclaim_bars)
    in_uptrend: bool         # gate de tendance (clôture de la chute > MA longue)
    score: float             # anomalie × réversion × fraîcheur × proximité × part restante
    why: str
    theory: str

    @property
    def mid(self) -> float:
        return (self.top + self.bottom) / 2


def _recency(bars_ago: int, half_life: float = 8.0) -> float:
    return float(0.5 ** (bars_ago / half_life))


def _proximity(dist_atr: float, scale: float = 2.0) -> float:
    return float(0.5 ** (max(dist_atr, 0.0) / scale))


def _robust_z(ret: pd.Series, window: int) -> pd.Series:
    """z-score robuste : (x − médiane) / (1.4826 × MAD) sur fenêtre glissante.
    Préféré au z classique : un spike ne gonfle pas l'échelle (pas d'auto-masquage)."""
    med = ret.rolling(window).median()
    mad = ret.rolling(window).apply(lambda a: np.median(np.abs(a - np.median(a))), raw=True)
    scale = (1.4826 * mad).replace(0, np.nan)
    return (ret - med) / scale


@dataclass
class DropSignal:
    """Barre de chute anormale (Étage A + gate de tendance), 100 % causale : ne dépend
    que de df[:i+1]. Partagée par le screener (detect_voids) et le backtest."""
    i: int
    ts: pd.Timestamp
    top: float
    bottom: float
    size_atr: float
    ret_z: float
    vol_ratio: float
    body_frac: float
    in_uptrend: bool


def drop_signals(df: pd.DataFrame, th: VoidThresholds | None = None,
                 start: int | None = None) -> list[DropSignal]:
    """Repère les barres de chute brutale anormale (sans lookahead). `start` borne le
    début du scan (défaut = z_window). Les features (z robuste, MA) sont *trailing* donc
    un signal en `i` n'utilise que le passé — utilisable tel quel en backtest."""
    th = th or VoidThresholds()
    n = len(df)
    if n < th.z_window + 2:
        return []
    ret = df["ret"] if "ret" in df else df["close"].pct_change()
    z = _robust_z(ret, th.z_window).values
    sma = df["close"].rolling(th.trend_ma, min_periods=th.trend_ma // 2).mean().values
    o, h, l, c = df["open"].values, df["high"].values, df["low"].values, df["close"].values
    atr, vr_col = df["atr"].values, df["vol_ratio"].values

    s = max(th.z_window, start if start is not None else th.z_window)
    out: list[DropSignal] = []
    for i in range(s, n):
        a = float(atr[i])
        if not a or np.isnan(a) or c[i] >= o[i]:           # barre baissière uniquement
            continue
        zi = float(z[i]) if not np.isnan(z[i]) else 0.0
        if zi > th.ret_z:                                   # chute pas assez anormale
            continue
        top, bottom = float(h[i]), float(l[i])
        rng = top - bottom
        if rng <= 0:
            continue
        size_atr = rng / a
        body_frac = abs(float(o[i]) - float(c[i])) / rng
        vr = float(vr_col[i]) if not np.isnan(vr_col[i]) else 1.0
        if size_atr < th.drop_atr or body_frac < th.body_frac or vr < th.vol_ratio_min:
            continue
        in_uptrend = bool(np.isnan(sma[i]) or c[i] > sma[i])
        out.append(DropSignal(i, df.index[i], top, bottom, size_atr, zi, vr, body_frac, in_uptrend))
    return out


def detect_voids(
    df: pd.DataFrame, th: VoidThresholds | None = None, lookback: int = 120
) -> list[LiquidityVoid]:
    """Détecte les vides de chute brutale sur la fenêtre récente et suit leur récupération.

    Renvoie tous les vides détectés (chacun avec statut, distance au prix, score). Les
    vides entièrement récupérés ont un score nul. Trié par score décroissant.
    """
    th = th or VoidThresholds()
    n = len(df)
    sigs = drop_signals(df, th, start=max(th.z_window, n - lookback))
    if not sigs:
        return []
    o, c, h = df["open"].values, df["close"].values, df["high"].values
    close_now, atr_now = float(c[-1]), float(df["atr"].values[-1])
    voids: list[LiquidityVoid] = []

    for sg in sigs:
        i = sg.i
        top, bottom = sg.top, sg.bottom
        # --- Récupération : remontée vers le haut du vide (barres postérieures) ---
        # mesurée depuis la clôture de la chute (là où le prix a été laissé), pas la mèche
        ref = float(c[i])
        span = top - ref
        post_h = h[i + 1:]
        recovered = (float(post_h.max()) - ref) / span if (len(post_h) and span > 0) else 0.0
        fill_frac = float(max(recovered, 0.0))
        status: FillStatus = ("filled" if fill_frac >= th.fill_threshold
                              else "partial" if fill_frac > th.partial_floor else "open")

        # snap-back précoce : clôture repassée au-dessus de l'ouverture de la chute
        end = min(i + 1 + th.reclaim_bars, n)
        reclaimed = bool(np.any(c[i + 1:end] >= o[i])) if end > i + 1 else False

        if close_now > top:
            dist_atr = (close_now - top) / atr_now if atr_now else np.inf
        elif close_now < bottom:
            dist_atr = (bottom - close_now) / atr_now if atr_now else np.inf
        else:
            dist_atr = 0.0

        created_ago = n - 1 - i
        anomaly = (0.5 * min(abs(sg.ret_z) / 4.0, 1.0)
                   + 0.25 * min(sg.size_atr / 3.0, 1.0)
                   + 0.25 * min(sg.vol_ratio / 5.0, 1.0))
        remaining = max(0.0, 1.0 - fill_frac)
        score = (anomaly * remaining * _recency(created_ago) * _proximity(float(dist_atr))
                 * (1.25 if reclaimed else 1.0) * (1.0 if sg.in_uptrend else 0.5))

        voids.append(LiquidityVoid(
            ts=sg.ts, top=top, bottom=bottom, size_atr=sg.size_atr, ret_z=sg.ret_z,
            vol_ratio=sg.vol_ratio, body_frac=sg.body_frac, created_ago=created_ago,
            fill_frac=round(fill_frac, 3), fill_status=status, dist_atr=round(float(dist_atr), 2),
            reclaimed=reclaimed, in_uptrend=sg.in_uptrend, score=round(float(score), 4),
            why=_why(sg.ret_z, sg.size_atr, sg.vol_ratio, sg.body_frac, fill_frac, status,
                     reclaimed, sg.in_uptrend),
            theory=_THEORY,
        ))

    voids.sort(key=lambda v: v.score, reverse=True)
    return voids


def _why(z: float, size_atr: float, vr: float, body_frac: float,
         fill_frac: float, status: FillStatus, reclaimed: bool, in_uptrend: bool) -> str:
    fill_txt = {
        "open": "vide intact (0 % récupéré) → rééquilibrage entier attendu",
        "partial": f"récupéré à {fill_frac * 100:.0f}% → réversion en cours, reste ouvert",
        "filled": "déjà rééquilibré (≥ 100 %) → vide purgé",
    }[status]
    snap = "snap-back précoce confirmé" if reclaimed else "pas encore de snap-back"
    trend = "hors downtrend (fade crédible)" if in_uptrend else "EN DOWNTREND (risque couteau qui tombe)"
    return (f"chute z={z:.1f} · {size_atr:.1f} ATR · corps {body_frac * 100:.0f}% · vol ×{vr:.1f} "
            f"→ liquidité consommée (cascade probable). {fill_txt} ; {snap} ; {trend}.")
