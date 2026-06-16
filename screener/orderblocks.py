"""
orderblocks.py — Détection d'Order Blocks au sens ICT et évaluation de leur « respect ».

Idée (ICT) : un Order Block est l'empreinte d'un acteur institutionnel — la dernière
bougie de sens *opposé* juste avant un mouvement d'impulsion fort (« displacement »).
  - OB haussier : dernière bougie baissière avant une impulsion ↑
  - OB baissier : dernière bougie haussière avant une impulsion ↓
Un OB est « réussi » (présence institutionnelle) si, une fois le prix *de retour* dans
la zone (mitigation), il **rebondit franchement** sans la clôturer au travers.

Choix validés (transparents, ajustables — jamais de boîte noire) :
  - displacement = course nette de l'impulsion ≥ `displacement_atr` × ATR (k·ATR seul,
    sans exigence de FVG/MSS) ;
  - zone = corps de la bougie (open↔close) par défaut, ou mèches (low↔high) ;
  - rebond « réussi » mesuré par le MFE (excursion favorable max) en multiples d'ATR :
    on **stocke le MFE brut** pour que le seuil `reaction_R` soit re-jouable a posteriori ;
  - invalidation = **clôture du corps** au travers de la zone (les mèches, chasses de
    liquidité, ne cassent pas l'OB).

Causal, sans lookahead : un OB n'est confirmé qu'une fois son impulsion formée, et son
évaluation ne lit que des barres postérieures.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class OBThresholds:
    displacement_atr: float = 2.0   # course nette de l'impulsion, en ATR (le « k »)
    impulse_window: int = 3         # nb de barres max pour réaliser l'impulsion
    zone: str = "body"              # "body" (open↔close) | "wick" (low↔high)
    reaction_R: float = 1.5         # seuil de rebond « réussi » (MFE en ATR)
    max_wait: int = 40              # barres max d'attente d'un retest (sinon non testé)


@dataclass
class OrderBlock:
    idx: int            # index entier de la bougie OB dans le df
    bias: str           # "bullish" | "bearish"
    top: float          # borne haute de la zone
    bottom: float       # borne basse de la zone
    atr: float          # ATR à la formation (normalise le MFE)
    displacement: float # course nette de l'impulsion, en ATR
    impulse_extreme: float  # sommet (bullish) / creux (bearish) de l'impulsion

    # Rempli par evaluate_order_block (NaN/None tant que non évalué) :
    outcome: str = "non_évalué"     # "respecté" | "cassé" | "tiède" | "non_testé"
    test_i: int | None = None       # barre de la 1re mitigation
    mfe_R: float = 0.0              # rebond max après retest, en ATR
    hit_swing: bool = False         # le rebond a-t-il atteint l'extrême de l'impulsion

    @property
    def tested(self) -> bool:
        return self.outcome in ("respecté", "cassé", "tiède")


def detect_order_blocks(feat: pd.DataFrame, th: OBThresholds | None = None) -> list[OrderBlock]:
    """
    Parcourt tout l'historique et renvoie les OB confirmés (impulsion réalisée).
    `feat` doit porter la colonne 'atr' (cf. features.add_features).
    """
    th = th or OBThresholds()
    o = feat["open"].to_numpy(float)
    h = feat["high"].to_numpy(float)
    l = feat["low"].to_numpy(float)
    c = feat["close"].to_numpy(float)
    a = feat["atr"].to_numpy(float)
    n = len(feat)
    W = th.impulse_window
    obs: list[OrderBlock] = []

    # i = bougie OB candidate ; l'impulsion se déploie sur [i+1, i+W].
    for i in range(1, n - W):
        atr_i = a[i]
        if not atr_i or np.isnan(atr_i):
            continue

        down = c[i] < o[i]          # bougie baissière → OB haussier potentiel
        up = c[i] > o[i]            # bougie haussière → OB baissier potentiel
        end = min(i + W, n - 1)

        # OB haussier : dernière bougie baissière (la suivante repart à la hausse) avant ↑
        if down and c[i + 1] > o[i + 1]:
            peak = h[i + 1 : end + 1].max()
            displacement = (peak - l[i]) / atr_i
            if displacement >= th.displacement_atr:
                top, bottom = (o[i], c[i]) if th.zone == "body" else (h[i], l[i])
                obs.append(OrderBlock(i, "bullish", float(top), float(bottom),
                                      float(atr_i), float(displacement), float(peak)))

        # OB baissier : dernière bougie haussière (la suivante repart à la baisse) avant ↓
        if up and c[i + 1] < o[i + 1]:
            trough = l[i + 1 : end + 1].min()
            displacement = (h[i] - trough) / atr_i
            if displacement >= th.displacement_atr:
                top, bottom = (c[i], o[i]) if th.zone == "body" else (h[i], l[i])
                obs.append(OrderBlock(i, "bearish", float(top), float(bottom),
                                      float(atr_i), float(displacement), float(trough)))

    return obs


def evaluate_order_block(feat: pd.DataFrame, ob: OrderBlock,
                         th: OBThresholds | None = None) -> OrderBlock:
    """
    Cherche la 1re mitigation (retour dans la zone) puis mesure le rebond.

      respecté : le MFE atteint `reaction_R`·ATR avant toute clôture au travers ;
      cassé    : une clôture de corps traverse la zone avant d'atteindre le seuil ;
      tiède    : retesté mais ni l'un ni l'autre (données épuisées, réaction molle) ;
      non_testé: jamais revenu dans la zone dans `max_wait` barres.
    """
    th = th or OBThresholds()
    h = feat["high"].to_numpy(float)
    l = feat["low"].to_numpy(float)
    c = feat["close"].to_numpy(float)
    n = len(feat)
    atr = ob.atr

    # On n'attend la mitigation qu'après l'extrême de l'impulsion (le prix s'est éloigné).
    start = ob.idx + 1
    if ob.bias == "bullish":
        peak_j = start + int(np.argmax(h[start : min(start + th.impulse_window, n)]))
        scan_from = peak_j + 1
    else:
        trough_j = start + int(np.argmin(l[start : min(start + th.impulse_window, n)]))
        scan_from = trough_j + 1

    # 1) Première mitigation dans la fenêtre d'attente
    test_i = None
    for j in range(scan_from, min(scan_from + th.max_wait, n)):
        if ob.bias == "bullish" and l[j] <= ob.top:
            test_i = j
            break
        if ob.bias == "bearish" and h[j] >= ob.bottom:
            test_i = j
            break
    if test_i is None:
        ob.outcome = "non_testé"
        return ob

    # 2) Rebond : MFE en ATR jusqu'à invalidation (clôture du corps au travers)
    mfe_R = 0.0
    max_hi, min_lo = -np.inf, np.inf
    outcome = "tiède"
    for j in range(test_i, n):
        max_hi, min_lo = max(max_hi, h[j]), min(min_lo, l[j])
        if ob.bias == "bullish":
            mfe_R = max(mfe_R, (h[j] - ob.top) / atr)
            if mfe_R >= th.reaction_R:
                outcome = "respecté"
                break
            if c[j] < ob.bottom:               # corps clôture sous la zone → cassé
                outcome = "cassé"
                break
        else:
            mfe_R = max(mfe_R, (ob.bottom - l[j]) / atr)
            if mfe_R >= th.reaction_R:
                outcome = "respecté"
                break
            if c[j] > ob.top:                  # corps clôture au-dessus de la zone → cassé
                outcome = "cassé"
                break

    ob.outcome = outcome
    ob.test_i = test_i
    ob.mfe_R = float(mfe_R)
    ob.hit_swing = bool(max_hi >= ob.impulse_extreme if ob.bias == "bullish"
                        else min_lo <= ob.impulse_extreme)
    return ob


def analyze_order_blocks(feat: pd.DataFrame, th: OBThresholds | None = None) -> list[OrderBlock]:
    """Détecte puis évalue tous les OB d'un symbole."""
    th = th or OBThresholds()
    return [evaluate_order_block(feat, ob, th) for ob in detect_order_blocks(feat, th)]
