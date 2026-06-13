"""
liquidity.py — Détecteur de Fair Value Gaps (FVG) / liquidity voids façon ICT.

Concept (Smart Money / ICT) : lors d'un mouvement d'expansion violent (*displacement*),
le prix se déplace si vite qu'il laisse une zone *peu tradée* — un déséquilibre. Le
motif canonique est le **Fair Value Gap** sur 3 bougies : le `low` de la 3ᵉ bougie ne
recouvre pas le `high` de la 1ʳᵉ (FVG haussier), ou inversement (FVG baissier). La barre
du milieu est la bougie de déplacement.

Thèse exploitable : le marché tend à **revenir rééquilibrer** (rebalance) ce vide. On
screene donc les vides **non comblés** que le prix est susceptible de revisiter, en
privilégiant ceux qui sont proches du prix courant (cible de retour la plus probable).

Tout reste transparent et ajustable (`VoidThresholds`) — aide à la décision
discrétionnaire, jamais d'exécution automatique. Réutilise les colonnes VSA déjà
calculées par `features.add_features` (atr, spread_atr, vol_ratio).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd

Direction = Literal["bullish", "bearish"]
FillStatus = Literal["unfilled", "partial", "filled"]


@dataclass
class VoidThresholds:
    min_gap_atr: float = 0.4         # hauteur mini du gap, en ATR (en-dessous = micro-imbalance/bruit)
    displacement_atr: float = 1.2    # spread/ATR mini de la bougie centrale (vrai déplacement)
    vol_ratio_min: float = 1.0       # vol_ratio attendu sur le déplacement (bonus de qualité)
    fill_threshold: float = 1.0      # fraction de comblement à partir de laquelle le vide est "filled"
    max_dist_atr: float = 4.0        # horizon de proximité pour le screening (distance prix→vide)


# Rappel théorique ICT, par direction.
_THEORY: dict[Direction, str] = {
    "bullish": "FVG haussier — déplacement acheteur qui laisse un vide sous le prix. "
        "Théorie ICT : zone de demande inefficiente ; le prix tend à y revenir combler "
        "le déséquilibre (rebalance) avant de poursuivre. Support potentiel sur retour.",
    "bearish": "FVG baissier — déplacement vendeur qui laisse un vide au-dessus du prix. "
        "Théorie ICT : zone d'offre inefficiente ; le prix tend à remonter rééquilibrer "
        "le vide avant de poursuivre. Résistance potentielle sur retour.",
}


@dataclass
class LiquidityVoid:
    direction: Direction
    top: float               # bord supérieur du vide
    bottom: float            # bord inférieur du vide
    size_atr: float          # hauteur du vide rapportée à l'ATR (qualité du déplacement)
    created_ago: int         # barres depuis la création (0 = dernière barre clôturée)
    fill_frac: float         # fraction comblée [0..1+], mesurée jusqu'au présent
    fill_status: FillStatus
    dist_atr: float          # distance prix courant → bord proche du vide, en ATR (0 = dedans)
    vol_ratio: float         # vol_ratio de la bougie de déplacement
    spread_atr: float        # spread/ATR de la bougie de déplacement
    score: float             # qualité × fraîcheur × proximité (vides non comblés)
    why: str                 # justification (déplacement + comblement)
    theory: str              # mémo ICT

    @property
    def mid(self) -> float:
        return (self.top + self.bottom) / 2


def _recency(bars_ago: int, half_life: float = 8.0) -> float:
    """Décroissance exponentielle : un vide récent est une cible plus crédible."""
    return float(0.5 ** (bars_ago / half_life))


def _proximity(dist_atr: float, scale: float = 2.0) -> float:
    """Décroissance avec la distance : un vide proche du prix est plus actionnable."""
    return float(0.5 ** (max(dist_atr, 0.0) / scale))


def detect_voids(
    df: pd.DataFrame, th: VoidThresholds | None = None, lookback: int = 120
) -> list[LiquidityVoid]:
    """Détecte les FVG (3 bougies) sur la fenêtre récente et suit leur comblement.

    `df` doit déjà porter les features (add_features : atr, spread_atr, vol_ratio).
    Renvoie tous les vides détectés, chacun avec son statut de comblement, sa distance
    au prix courant et un score (les vides entièrement comblés ont un score nul).
    Trié par score décroissant.
    """
    th = th or VoidThresholds()
    n = len(df)
    if n < 4:
        return []

    win_start = max(1, n - lookback)
    highs = df["high"].values
    lows = df["low"].values
    atr = df["atr"].values
    close = float(df["close"].iloc[-1])
    atr_now = float(df["atr"].iloc[-1])
    voids: list[LiquidityVoid] = []

    # m = index de la bougie centrale (déplacement). FVG confirmé une fois m+1 clôturée.
    for m in range(win_start, n - 1):
        a = float(atr[m])
        if not a or np.isnan(a):
            continue
        h_prev, l_next = float(highs[m - 1]), float(lows[m + 1])
        h_next, l_prev = float(highs[m + 1]), float(lows[m - 1])

        direction: Direction | None = None
        if l_next > h_prev:                       # FVG haussier : gap (h_prev, l_next)
            direction, bottom, top = "bullish", h_prev, l_next
        elif h_next < l_prev:                     # FVG baissier : gap (h_next, l_prev)
            direction, bottom, top = "bearish", h_next, l_prev
        if direction is None:
            continue

        size = top - bottom
        size_atr = size / a
        if size_atr < th.min_gap_atr:
            continue

        bar = df.iloc[m]
        sa = float(bar["spread_atr"]) if not np.isnan(bar["spread_atr"]) else 0.0
        vr = float(bar["vol_ratio"]) if not np.isnan(bar["vol_ratio"]) else 1.0
        if sa < th.displacement_atr:              # pas un vrai déplacement → on ignore
            continue

        # --- Comblement : barres postérieures à la confirmation (m+2 .. présent) ---
        post = df.iloc[m + 2:]
        if direction == "bullish":
            deepest = float(post["low"].min()) if len(post) else top
            fill_frac = (top - deepest) / size
        else:
            highest = float(post["high"].max()) if len(post) else bottom
            fill_frac = (highest - bottom) / size
        fill_frac = float(max(fill_frac, 0.0))
        if fill_frac >= th.fill_threshold:
            status: FillStatus = "filled"
        elif fill_frac > 0:
            status = "partial"
        else:
            status = "unfilled"

        # --- Distance prix courant → bord proche du vide (0 si le prix est dedans) ---
        if close > top:
            dist_atr = (close - top) / atr_now if atr_now else np.inf
        elif close < bottom:
            dist_atr = (bottom - close) / atr_now if atr_now else np.inf
        else:
            dist_atr = 0.0

        created_ago = n - 1 - (m + 1)             # la confirmation est en m+1
        # Score : qualité (taille + volume) × fraîcheur × proximité, annulé si comblé.
        quality = min(size_atr, 3.0) / 3.0 * (1.0 if vr >= th.vol_ratio_min else 0.7)
        remaining = max(0.0, 1.0 - fill_frac)     # part du vide encore ouverte
        score = quality * _recency(created_ago) * _proximity(dist_atr) * remaining

        voids.append(LiquidityVoid(
            direction=direction, top=top, bottom=bottom, size_atr=size_atr,
            created_ago=created_ago, fill_frac=round(fill_frac, 3), fill_status=status,
            dist_atr=round(float(dist_atr), 2), vol_ratio=vr, spread_atr=sa,
            score=round(float(score), 4),
            why=_why(direction, size_atr, vr, sa, fill_frac, status, th),
            theory=_THEORY[direction],
        ))

    voids.sort(key=lambda v: v.score, reverse=True)
    return voids


def _why(direction: Direction, size_atr: float, vr: float, sa: float,
         fill_frac: float, status: FillStatus, th: VoidThresholds) -> str:
    side = "acheteur" if direction == "bullish" else "vendeur"
    vol_txt = (f"vol ×{vr:.2f} (≥ {th.vol_ratio_min} → déplacement appuyé)"
               if vr >= th.vol_ratio_min else f"vol ×{vr:.2f} (déplacement sur faible volume)")
    fill_txt = {
        "unfilled": "vide intact (0 % comblé) → cible de rééquilibrage entière",
        "partial": f"comblé à {fill_frac * 100:.0f}% → rééquilibrage partiel, reste ouvert",
        "filled": "déjà rééquilibré (≥ 100 %) → déséquilibre purgé",
    }[status]
    return (f"déplacement {side} : spread {sa:.2f} ATR (large) + gap {size_atr:.2f} ATR, "
            f"{vol_txt}. {fill_txt}.")
