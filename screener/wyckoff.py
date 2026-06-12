"""
wyckoff.py — Cœur unique de détection Wyckoff du screener.

Reconnaît une **séquence ordonnée** d'événements sur une fenêtre glissante :

  Accumulation  : SC  → AR → ST → SOS   (plancher défendu puis détente haussière)
  Distribution  : BC  → AR → ST → SOW   (plafond vendu puis cassure baissière)

et vérifie le **contexte** qui la précède (prérequis Wyckoff) : une accumulation
suit un *markdown* stoppé par le climax, une distribution un *markup*.

Tout est transparent et ajustable (seuils `Thresholds`). Chaque `WindowEvent` porte
deux textes : `why` (pourquoi volume+spread confirment le rôle, calculé sur la barre)
et `theory` (rappel de ce que dit la théorie sur cet événement dans le schéma).

C'est la *seule* définition d'un événement Wyckoff dans le projet : la table
récapitulative et les graphiques en dérivent directement.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from .features import swing_points

# Contexte : amplitude mini du markdown/markup *précédant* le climax (prérequis Wyckoff).
CTX_LOOKBACK = 25       # barres examinées avant le climax
CTX_TREND_MIN = 0.05    # |variation| mini (5 %) pour valider un markdown / markup
# Géométrie des retournements (AR, ST) : pivots locaux, pas extrêmes de fenêtre.
PIVOT_RIGHT = 2         # barres de confirmation d'un pivot (fractale)
AR_MIN_ATR = 1.0        # amplitude mini du rebond automatique depuis le climax (en ATR)


# --------------------------------------------------------------------------- #
# Seuils des détecteurs (heuristiques VSA transparentes et ajustables)
# --------------------------------------------------------------------------- #
@dataclass
class Thresholds:
    climax_vol: float = 2.0       # vol_ratio pour un climax (SC/BC)
    sos_vol: float = 1.3          # vol_ratio pour SOS/SOW
    wide_spread_atr: float = 1.3  # spread_atr d'une barre « large »
    narrow_spread_atr: float = 0.7
    test_vol: float = 0.85        # vol_ratio plafond pour un test/ST (volume sec)
    pen_atr: float = 0.1          # pénétration mini hors borne, en ATR
    reclaim_clv: float = 0.5      # clôture au-dessus/dessous du milieu de barre


# --------------------------------------------------------------------------- #
# Rappels théoriques (par schéma + événement)
# --------------------------------------------------------------------------- #
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
    context_move: float = float("nan")   # variation nette avant le climax (prérequis)
    context_bars: int = 0

    @property
    def is_valid(self) -> bool:
        names = {e.name for e in self.events}
        # un schéma exploitable = au moins le climax + un signe directionnel/test
        climax = {"SC", "BC"} & names
        follow = {"SOS", "SOW", "ST"} & names
        return bool(climax and follow)

    @property
    def context_ok(self) -> bool:
        """Le mouvement précédant le climax respecte le prérequis Wyckoff
        (markdown avant accumulation, markup avant distribution)."""
        if math.isnan(self.context_move):
            return False
        if self.bias == "accumulation":
            return self.context_move <= -CTX_TREND_MIN
        if self.bias == "distribution":
            return self.context_move >= CTX_TREND_MIN
        return False


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
    atr_ref = float(cbar["atr"]) if not np.isnan(cbar["atr"]) else 0.02 * abs(c_extreme)

    # Pivots de la fenêtre (fractales) : l'AR et le ST sont des *retournements locaux*,
    # pas des extrêmes sur une fenêtre — c'est ce qui les recale au bon endroit.
    sw = swing_points(win, left=1, right=PIVOT_RIGHT)
    swing_hi = np.where(sw["swing_high"].values)[0]
    swing_lo = np.where(sw["swing_low"].values)[0]

    # 2) AR : PREMIER pivot de réaction après le climax (le rebond réflexe immédiat),
    # d'amplitude ≥ AR_MIN_ATR·ATR, le climax restant l'extrême jusque-là. Pas l'argmax
    # de la fenêtre (qui attraperait un sommet/creux plus tardif d'un markup/markdown).
    horizon = max(2, n // 2)
    ar_pivots = swing_hi if acc else swing_lo
    apos = None
    for i in ar_pivots:
        if not (cpos < i <= cpos + horizon):
            continue
        seg = win.iloc[cpos:i + 1]  # le climax doit rester l'extrême jusqu'à l'AR
        if acc and float(seg["low"].min()) < c_extreme - 1e-9:
            continue
        if (not acc) and float(seg["high"].max()) > c_extreme + 1e-9:
            continue
        extreme = float(win["high"].iloc[i] if acc else win["low"].iloc[i])
        amp = (extreme - c_extreme) if acc else (c_extreme - extreme)
        if amp >= AR_MIN_ATR * atr_ref:
            apos = i
            break
    if apos is None:
        return WindowStructure(bias, lo, hi)  # pas de réaction franche → pas de structure
    events.append(_mk(df, len(df) - n + apos, "AR", bias, th))

    # 3) ST : PREMIER pivot creux (acc) / sommet (dist) après l'AR, près de la borne,
    # sans cassure (higher-low / lower-high), volume sec et spread étroit. On prend le
    # premier vrai test au creux/sommet, pas la barre la plus sèche au milieu d'un mouvement.
    st_pivots = swing_lo if acc else swing_hi
    st_pos = None
    for j in st_pivots:
        if j <= apos:
            continue
        b = win.iloc[j]
        extreme = float(b["low"] if acc else b["high"])
        near = abs(extreme - c_extreme) <= tol
        no_break = (extreme >= c_extreme - 0.1 * tol) if acc else (extreme <= c_extreme + 0.1 * tol)
        vr = float(b["vol_ratio"]) if not np.isnan(b["vol_ratio"]) else 1.0
        sa = float(b["spread_atr"]) if not np.isnan(b["spread_atr"]) else 1.0
        if near and no_break and vr <= th.test_vol * 1.15 and sa <= th.wide_spread_atr:
            st_pos = j
            break
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


def assess_context(df: pd.DataFrame, struct: WindowStructure) -> tuple[float, int]:
    """Variation nette sur les `CTX_LOOKBACK` barres *avant* le climax (prérequis Wyckoff).
    Renvoie (variation relative, nb de barres mesurées) ; (nan, n) si historique trop court."""
    climax = next((e for e in struct.events if e.name in ("SC", "BC")), None)
    if climax is None:
        return float("nan"), 0
    idx = len(df) - 1 - climax.bars_ago
    start = max(0, idx - CTX_LOOKBACK)
    if idx - start < 8:
        return float("nan"), idx - start
    c0 = float(df["close"].iloc[start])
    c1 = float(df["close"].iloc[idx])
    move = (c1 - c0) / c0 if c0 else 0.0
    return move, idx - start


def detect_window_structure(
    df: pd.DataFrame, lookback: int = 30, th: Thresholds | None = None
) -> WindowStructure:
    """Renvoie le schéma (accumulation/distribution) dominant sur la fenêtre récente,
    contexte (markdown/markup préalable) compris. Neutre si aucune séquence valide.

    `df` doit déjà porter les features (add_features)."""
    th = th or Thresholds()
    cand = [_scan(df, lookback, th, "accumulation"), _scan(df, lookback, th, "distribution")]
    cand = [c for c in cand if c.is_valid]
    if not cand:
        return WindowStructure("neutral", np.nan, np.nan)
    best = max(cand, key=lambda c: c.score)
    best.context_move, best.context_bars = assess_context(df, best)
    return best
