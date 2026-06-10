"""
window.py — Détection de structure Wyckoff sur une *fenêtre glissante*.

Complément au détecteur d'événements de `events.py`. Là où `detect_events` ne
réagit qu'aux bornes de la grande plage et sur les `buffer` dernières barres, ce
module reconnaît une **séquence ordonnée** (climax → rebond auto → test → signe
directionnel) à l'intérieur d'une fenêtre récente, même si elle s'est jouée au
milieu du lookback. Il identifie le schéma dominant :

  Accumulation  : SC  → AR → ST → SOS   (plancher défendu puis détente haussière)
  Distribution  : BC  → AR → ST → SOW   (plafond vendu puis cassure baissière)

Tout reste transparent et ajustable (seuils `Thresholds`). Chaque événement porte
deux textes : `why` (pourquoi volume+spread confirment le rôle, calculé sur la
barre) et `theory` (rappel de ce que dit la théorie Wyckoff sur cet événement
dans le schéma détecté).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from .events import Thresholds

# --------------------------------------------------------------------------- #
# Rappels théoriques (par schéma + événement)
# --------------------------------------------------------------------------- #
# Description "manuel Wyckoff" de chaque événement.
_THEORY_DESC: dict[tuple[str, str], str] = {
    ("accumulation", "SC"): "Selling Climax — apogée de la baisse : l'offre paniquée "
        "est absorbée par les mains fortes. Fixe le plancher de la plage.",
    ("accumulation", "AR"): "Automatic Rally — rebond réflexe une fois les vendeurs "
        "épuisés ; en fixe le plafond. Les deux bornes de la plage sont posées.",
    ("accumulation", "ST"): "Secondary Test — on revient sonder le plancher pour "
        "vérifier que l'offre s'est tarie : creux idéalement plus haut.",
    ("accumulation", "SOS"): "Sign of Strength — poussée large et volumique : la "
        "demande prend le contrôle, prélude à la phase de hausse (markup).",
    ("distribution", "BC"): "Buying Climax — apogée de la hausse : la demande euphorique "
        "est absorbée par les mains fortes qui distribuent. Fixe le plafond.",
    ("distribution", "AR"): "Automatic Reaction — repli réflexe une fois les acheteurs "
        "épuisés ; en fixe le plancher. Les deux bornes de la plage sont posées.",
    ("distribution", "ST"): "Secondary Test — on revient sonder le plafond : sommet "
        "idéalement plus bas = demande épuisée.",
    ("distribution", "SOW"): "Sign of Weakness — cassure du support sur volume large : "
        "l'offre prend le contrôle, prélude à la phase de baisse (markdown).",
}


def _theory(bias: str, name: str, th: Thresholds) -> str:
    """Description Wyckoff + repère chiffré des seuils volume/spread *attendus* en
    théorie pour cet événement. But : développer des automatismes de lecture."""
    desc = _THEORY_DESC[(bias, name)]
    acc = bias == "accumulation"
    close_dir = "haute" if acc else "basse"
    if name in ("SC", "BC"):
        rep = (f"Repère : volume CLIMACTIQUE (≥ ×{th.climax_vol} la moyenne, le plus fort "
               f"de la séquence) + spread LARGE (≥ {th.wide_spread_atr} ATR) + clôture {close_dir} "
               f"(rejet → absorption).")
    elif name == "AR":
        rep = ("Repère : volume EN NETTE BAISSE (le mouvement n'est pas soutenu, idéalement "
               "sous la moyenne) — un AR à fort volume invaliderait l'épuisement.")
    elif name == "ST":
        rep = (f"Repère : volume SEC (≤ ×{th.test_vol}, et inférieur au climax) + spread ÉTROIT "
               f"(< {th.wide_spread_atr} ATR). Plus le volume est faible, meilleur est le test.")
    else:  # SOS / SOW
        rep = (f"Repère : volume SOUTENU (≥ ×{th.sos_vol}) + spread LARGE (≥ {th.wide_spread_atr} ATR) "
               f"+ clôture {close_dir} (clv {'≥ 0.6' if acc else '≤ 0.4'}) confirmant la direction.")
    return f"{desc} {rep}"


@dataclass
class WindowEvent:
    name: str            # SC, AR, ST, SOS / BC, AR, ST, SOW
    bias: str            # accumulation | distribution
    ts: pd.Timestamp
    bars_ago: int
    price: float         # clôture de la barre
    bar_high: float      # extrême haut de la barre (pour placer plafond / marqueurs)
    bar_low: float       # extrême bas de la barre (pour placer plancher / marqueurs)
    vol_ratio: float
    spread_atr: float
    clv: float
    strength: float
    why: str             # justification volume + spread, calculée sur la barre
    theory: str          # rappel théorique


@dataclass
class WindowStructure:
    bias: str            # accumulation | distribution | neutral
    low: float
    high: float
    events: list[WindowEvent] = field(default_factory=list)
    score: float = 0.0

    @property
    def is_valid(self) -> bool:
        names = {e.name for e in self.events}
        # un schéma exploitable = au moins le climax + un signe directionnel/test
        climax = {"SC", "BC"} & names
        follow = {"SOS", "SOW", "ST"} & names
        return bool(climax and follow)


# --------------------------------------------------------------------------- #
# Justifications volume/spread (texte calculé sur la barre)
# --------------------------------------------------------------------------- #
def _why(name: str, acc: bool, vr: float, sa: float, clv: float, th: Thresholds) -> str:
    side_eff = "vendeur" if acc else "acheteur"
    side_dom = "demande" if acc else "offre"
    close_dir = "haute" if acc else "basse"
    if name in ("SC", "BC"):
        return (f"vol ×{vr:.2f} (≥ climax {th.climax_vol}) + spread {sa:.2f} ATR (large) "
                f"+ clôture {close_dir} (clv {clv:.2f}) → effort {side_eff} maximal *absorbé* : "
                f"la pression est encaissée par la partie adverse.")
    if name == "AR":
        return (f"vol ×{vr:.2f} (en repli) → mouvement réflexe sans engagement : les "
                f"opérateurs épuisés ne suivent pas, ce qui révèle l'autre borne de la plage.")
    if name == "ST":
        return (f"vol ×{vr:.2f} (sec, ≤ test {th.test_vol}) + spread {sa:.2f} ATR (étroit) → "
                f"le retour vers le climax ne trouve plus de {('offre' if acc else 'demande')} : "
                f"test réussi, déséquilibre prêt à se résoudre.")
    if name in ("SOS", "SOW"):
        return (f"vol ×{vr:.2f} (≥ signe {th.sos_vol}) + spread {sa:.2f} ATR (large) + clôture "
                f"{close_dir} (clv {clv:.2f}) → {side_dom} dominante, déséquilibre directionnel confirmé.")
    return ""


def _mk(df, i, name, bias, th) -> WindowEvent:
    bar = df.iloc[i]
    vr = float(bar["vol_ratio"]) if not np.isnan(bar["vol_ratio"]) else 1.0
    sa = float(bar["spread_atr"]) if not np.isnan(bar["spread_atr"]) else 1.0
    clv = float(bar["clv"])
    acc = bias == "accumulation"
    # force heuristique simple, bornée 0..1
    if name in ("SC", "BC"):
        s = np.clip(0.3 + 0.2 * (vr - th.climax_vol) + 0.3 * (clv if acc else 1 - clv), 0, 1)
    elif name in ("SOS", "SOW"):
        s = np.clip(0.4 + 0.1 * (vr - th.sos_vol) + 0.3 * (clv if acc else 1 - clv), 0, 1)
    elif name == "ST":
        s = np.clip(0.5 * (1 - vr), 0, 1)
    else:  # AR
        s = 0.5
    return WindowEvent(
        name=name, bias=bias, ts=df.index[i], bars_ago=len(df) - 1 - i,
        price=float(bar["close"]), bar_high=float(bar["high"]), bar_low=float(bar["low"]),
        vol_ratio=vr, spread_atr=sa, clv=clv,
        strength=float(s), why=_why(name, acc, vr, sa, clv, th),
        theory=_theory(bias, name, th),
    )


# --------------------------------------------------------------------------- #
# Recherche d'un schéma pour un biais donné
# --------------------------------------------------------------------------- #
def _scan(df: pd.DataFrame, lookback: int, th: Thresholds, bias: str) -> WindowStructure:
    win = df.iloc[-lookback:]
    n = len(win)
    if n < 8:
        return WindowStructure(bias, np.nan, np.nan)
    acc = bias == "accumulation"
    lo, hi = float(win["low"].min()), float(win["high"].max())
    rng = hi - lo
    tol = 0.20 * rng if rng > 0 else np.inf
    head_end = max(3, int(0.6 * n))
    events: list[WindowEvent] = []

    # 1) CLIMAX dans la première moitié : extrême + volume climactique + clôture rejetée
    head = win.iloc[:head_end]
    cpos = int(head["low"].values.argmin() if acc else head["high"].values.argmax())
    cbar = win.iloc[cpos]
    cvr = float(cbar["vol_ratio"]) if not np.isnan(cbar["vol_ratio"]) else 1.0
    cclv = float(cbar["clv"])
    climax_ok = cvr >= 0.75 * th.climax_vol and ((cclv >= 0.4) if acc else (cclv <= 0.6))
    if not climax_ok:
        return WindowStructure(bias, lo, hi)
    gi = len(df) - n + cpos  # index global
    events.append(_mk(df, gi, "SC" if acc else "BC", bias, th))
    c_extreme = float(cbar["low"] if acc else cbar["high"])

    # 2) AR : extrême opposé du *rebond initial*. On borne l'horizon de recherche
    # juste après le climax (sinon on attraperait l'extrême du SOS/SOW final).
    horizon = max(2, n // 3)
    after = win.iloc[cpos + 1: cpos + 1 + horizon]
    if len(after) >= 1:
        apos_local = int(after["high"].values.argmax() if acc else after["low"].values.argmin())
        apos = cpos + 1 + apos_local
        events.append(_mk(df, len(df) - n + apos, "AR", bias, th))
    else:
        apos = cpos

    # 3) ST : après l'AR, retour près du climax sur volume sec, sans nouvel extrême franc
    st_pos = None
    best = None
    for j in range(apos + 1, n):
        b = win.iloc[j]
        near = (abs(float(b["low"]) - c_extreme) <= tol) if acc else (abs(float(b["high"]) - c_extreme) <= tol)
        vr = float(b["vol_ratio"]) if not np.isnan(b["vol_ratio"]) else 1.0
        sa = float(b["spread_atr"]) if not np.isnan(b["spread_atr"]) else 1.0
        no_break = (float(b["low"]) >= c_extreme - 0.1 * tol) if acc else (float(b["high"]) <= c_extreme + 0.1 * tol)
        if near and vr <= th.test_vol * 1.15 and sa <= th.wide_spread_atr and no_break:
            if best is None or vr < best:
                best, st_pos = vr, j
    if st_pos is not None:
        events.append(_mk(df, len(df) - n + st_pos, "ST", bias, th))

    # 4) SOS / SOW : après le test (ou l'AR), poussée large et volumique dans le sens du biais
    start = (st_pos if st_pos is not None else apos) + 1
    sig_pos = None
    for j in range(start, n):
        b = win.iloc[j]
        vr = float(b["vol_ratio"]) if not np.isnan(b["vol_ratio"]) else 1.0
        sa = float(b["spread_atr"]) if not np.isnan(b["spread_atr"]) else 1.0
        clv = float(b["clv"])
        ok = (clv >= 0.6) if acc else (clv <= 0.4)
        if vr >= th.sos_vol and sa >= th.wide_spread_atr and ok:
            sig_pos = j  # on garde le dernier (le plus récent)
    if sig_pos is not None:
        events.append(_mk(df, len(df) - n + sig_pos, "SOS" if acc else "SOW", bias, th))

    score = float(sum(e.strength for e in events))
    return WindowStructure(bias, lo, hi, events, score)


def detect_window_structure(
    df: pd.DataFrame, lookback: int = 30, th: Thresholds | None = None
) -> WindowStructure:
    """Renvoie le schéma (accumulation/distribution) dominant sur la fenêtre récente.

    `df` doit déjà porter les features (add_features). On évalue les deux biais et on
    retient celui dont la séquence est la plus complète/forte ; neutre si aucun.
    """
    th = th or Thresholds()
    cand = [_scan(df, lookback, th, "accumulation"), _scan(df, lookback, th, "distribution")]
    cand = [c for c in cand if c.is_valid]
    if not cand:
        return WindowStructure("neutral", np.nan, np.nan)
    return max(cand, key=lambda c: c.score)
