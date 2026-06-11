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
    ("accumulation", "SPRING"): "Spring — fausse cassure sous le plancher (shakeout) puis "
        "rejet : déloge les dernières mains faibles avant le markup. Phase C.",
    ("accumulation", "LPS"): "Last Point of Support — back-up à la creek après le SOS : "
        "creux plus haut sur volume sec, dernier appui avant la hausse.",
    ("distribution", "UTAD"): "Upthrust After Distribution — fausse cassure au-dessus du "
        "plafond puis rejet : piège les acheteurs avant le markdown. Phase C.",
    ("distribution", "LPSY"): "Last Point of Supply — pullback après le SOW : sommet plus "
        "bas sur volume sec, dernier rebond avant la baisse.",
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
    elif name in ("SPRING", "UTAD"):
        rep = (f"Repère : pénétration BRÈVE hors borne (≈ {th.pen_atr} ATR) puis CLÔTURE qui "
               f"revient dans la plage (rejet, clv {'≥ 0.5' if acc else '≤ 0.5'}) — la cassure ne tient pas.")
    elif name in ("LPS", "LPSY"):
        rep = (f"Repère : réaction à volume SEC (≤ ×{th.test_vol}) ; "
               f"{'creux plus HAUT tenant le support' if acc else 'sommet plus BAS tenant la résistance'} "
               f"(le bon côté de la borne cassée).")
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
    oi_chg: float = np.nan  # variation d'Open Interest sur ~3 barres (%), si disponible


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
    if name in ("SPRING", "UTAD"):
        borne = "plancher" if acc else "plafond"
        piege = "vendeurs" if acc else "acheteurs"
        return (f"vol ×{vr:.2f} + pénétration sous le {borne} puis clôture revenue dans la plage "
                f"(clv {clv:.2f}) → fausse cassure : {piege} piégés, la borne tient." if acc else
                f"vol ×{vr:.2f} + pénétration au-dessus du {borne} puis clôture revenue dans la plage "
                f"(clv {clv:.2f}) → fausse cassure : {piege} piégés, la borne tient.")
    if name in ("LPS", "LPSY"):
        cote = "creux plus haut tenant le support" if acc else "sommet plus bas tenant la résistance"
        return (f"vol ×{vr:.2f} (sec) + {cote} → dernier point d'appui avant la "
                f"{'hausse (markup)' if acc else 'baisse (markdown)'}.")
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
    elif name in ("ST", "LPS", "LPSY"):
        s = np.clip(0.5 * (1 - vr), 0, 1)
    elif name in ("SPRING", "UTAD"):
        s = np.clip(0.35 + 0.4 * (clv if acc else 1 - clv), 0, 1)
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
def _oi_pct(oi_aligned, gi: int, k: int = 3) -> float:
    """Variation d'OI (%) sur `k` barres se terminant à l'index global `gi`. NaN si indispo."""
    if oi_aligned is None or gi - k < 0:
        return np.nan
    a, b = float(oi_aligned.iloc[gi]), float(oi_aligned.iloc[gi - k])
    if np.isnan(a) or np.isnan(b) or b == 0:
        return np.nan
    return (a / b - 1.0) * 100.0


def _scan(df: pd.DataFrame, lookback: int, th: Thresholds, bias: str,
          oi_aligned=None) -> WindowStructure:
    win = df.iloc[-lookback:]
    n = len(win)
    if n < 8:
        return WindowStructure(bias, np.nan, np.nan)
    acc = bias == "accumulation"
    lo, hi = float(win["low"].min()), float(win["high"].max())
    rng = hi - lo
    tol = 0.20 * rng if rng > 0 else np.inf
    head_end = max(3, int(0.6 * n))

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
    c_extreme = float(cbar["low"] if acc else cbar["high"])
    atr_ref = float(cbar["atr"]) if not np.isnan(cbar["atr"]) else (rng / n if n else 1.0)
    events: list[WindowEvent] = [_mk(df, gi, "SC" if acc else "BC", bias, th)]

    def g(pos: int) -> int:  # position locale (dans win) -> index global (dans df)
        return len(df) - n + pos

    # 2) AR : sommet/creux du REBOND RÉFLEXE IMMÉDIAT après le climax. Horizon court ;
    # on s'arrête dès que le mouvement cale (l'extrême cesse de progresser), pour ne pas
    # attraper la poussée (SOS/JAC) plus tardive. L'AR n'est *validé* que si le volume
    # est EN REPLI (< 1×) — un rebond volumique est une poussée, pas un AR.
    ar_horizon = max(3, min(n // 4, 8))
    apos = cpos
    best_ext = None
    for j in range(cpos + 1, min(n, cpos + 1 + ar_horizon)):
        ext = float(win.iloc[j]["high"] if acc else win.iloc[j]["low"])
        if best_ext is None or (ext > best_ext if acc else ext < best_ext):
            best_ext, apos = ext, j
        else:
            break  # le rebond cale : pic réflexe atteint
    ar_vr = float(win.iloc[apos]["vol_ratio"]) if not np.isnan(win.iloc[apos]["vol_ratio"]) else 1.0
    # Confirmation OI : un AR authentique est un rebond de débouclage (short covering en
    # acc / liquidation de longs en dist) → OI en REPLI. Si l'OI est dispo et MONTE, on
    # refuse l'AR (comme un AR à fort volume). Indispo → on retombe sur le seul volume.
    ar_oi_ok = True
    ar_oi_d = _oi_pct(oi_aligned, g(apos), 3)
    if not np.isnan(ar_oi_d):
        ar_oi_ok = ar_oi_d < 0
    if apos > cpos and ar_vr < 1.0 and ar_oi_ok:
        events.append(_mk(df, g(apos), "AR", bias, th))

    # 3) SOS / SOW : PREMIÈRE poussée large et volumique dans le sens du biais après l'AR
    # (le « jump across the creek »). On la détecte AVANT l'ST/Spring pour pouvoir les
    # borner en Phase B (avant le signe) ; garder la *première* laisse place au LPS ensuite.
    sig_pos = None
    for j in range(apos + 1, n):
        b = win.iloc[j]
        vr = float(b["vol_ratio"]) if not np.isnan(b["vol_ratio"]) else 1.0
        sa = float(b["spread_atr"]) if not np.isnan(b["spread_atr"]) else 1.0
        clv = float(b["clv"])
        ok = (clv >= 0.6) if acc else (clv <= 0.4)
        if vr >= th.sos_vol and sa >= th.wide_spread_atr and ok:
            sig_pos = j
            break
    phase_b_end = sig_pos if sig_pos is not None else n  # ST/Spring se cherchent avant le signe

    # 4) ST : entre l'AR et le signe, retour près du climax sur volume sec, sans nouvel extrême franc
    st_pos, best = None, None
    for j in range(apos + 1, phase_b_end):
        b = win.iloc[j]
        near = (abs(float(b["low"]) - c_extreme) <= tol) if acc else (abs(float(b["high"]) - c_extreme) <= tol)
        vr = float(b["vol_ratio"]) if not np.isnan(b["vol_ratio"]) else 1.0
        sa = float(b["spread_atr"]) if not np.isnan(b["spread_atr"]) else 1.0
        no_break = (float(b["low"]) >= c_extreme - 0.1 * tol) if acc else (float(b["high"]) <= c_extreme + 0.1 * tol)
        if near and vr <= th.test_vol * 1.15 and sa <= th.wide_spread_atr and no_break:
            if best is None or vr < best:
                best, st_pos = vr, j
    if st_pos is not None:
        events.append(_mk(df, g(st_pos), "ST", bias, th))

    # 5) SPRING / UTAD (Phase C) : fausse cassure de la borne du climax puis clôture revenue
    # dans la plage (rejet), entre l'AR et le signe. On retient la pénétration la plus nette.
    spr_pos, spr_best = None, None
    for j in range(apos + 1, phase_b_end):
        b = win.iloc[j]
        clv = float(b["clv"])
        if acc:
            pen = c_extreme - float(b["low"])
            recl = float(b["close"]) >= c_extreme and clv >= 0.5
        else:
            pen = float(b["high"]) - c_extreme
            recl = float(b["close"]) <= c_extreme and clv <= 0.5
        if pen >= th.pen_atr * atr_ref and recl and (spr_best is None or pen > spr_best):
            spr_best, spr_pos = pen, j
    if spr_pos is not None:
        events.append(_mk(df, g(spr_pos), "SPRING" if acc else "UTAD", bias, th))

    if sig_pos is not None:
        events.append(_mk(df, g(sig_pos), "SOS" if acc else "SOW", bias, th))

        # 6) LPS / LPSY (Phase D) : après le SOS, réaction (back-up) à volume sec qui TIENT
        # du bon côté de la borne — creux plus haut (acc) / sommet plus bas (dist). On prend
        # le point de réaction le plus marqué (≥ 1 ATR de repli depuis l'extrême du SOS).
        sos_ext = float(win.iloc[sig_pos]["high"] if acc else win.iloc[sig_pos]["low"])
        lps_pos, react = None, None
        for j in range(sig_pos + 1, n):
            b = win.iloc[j]
            vr = float(b["vol_ratio"]) if not np.isnan(b["vol_ratio"]) else 1.0
            if acc:
                depth, ext, holds = sos_ext - float(b["low"]), float(b["low"]), float(b["low"]) > c_extreme
                deeper = react is None or ext < react
            else:
                depth, ext, holds = float(b["high"]) - sos_ext, float(b["high"]), float(b["high"]) < c_extreme
                deeper = react is None or ext > react
            if depth >= atr_ref and holds and vr <= th.test_vol * 1.3 and deeper:
                react, lps_pos = ext, j
        if lps_pos is not None:
            events.append(_mk(df, g(lps_pos), "LPS" if acc else "LPSY", bias, th))

    if oi_aligned is not None:
        for e in events:
            e.oi_chg = _oi_pct(oi_aligned, df.index.get_loc(e.ts), 3)

    events.sort(key=lambda e: e.ts)
    score = float(sum(e.strength for e in events))
    return WindowStructure(bias, lo, hi, events, score)


def detect_window_structure(
    df: pd.DataFrame, lookback: int = 30, th: Thresholds | None = None, oi=None
) -> WindowStructure:
    """Renvoie le schéma (accumulation/distribution) dominant sur la fenêtre récente.

    `df` doit déjà porter les features (add_features). On évalue les deux biais et on
    retient celui dont la séquence est la plus complète/forte ; neutre si aucun.
    `oi` (DataFrame/Series d'Open Interest, optionnel) est réaligné sur l'index des barres
    et sert à confirmer l'AR (rebond de débouclage → OI en repli) et à annoter ΔOI.
    """
    th = th or Thresholds()
    oi_aligned = None
    if oi is not None and len(oi):
        s = oi["oi"] if isinstance(oi, pd.DataFrame) else oi
        oi_aligned = s.reindex(df.index, method="nearest")
    cand = [_scan(df, lookback, th, "accumulation", oi_aligned),
            _scan(df, lookback, th, "distribution", oi_aligned)]
    cand = [c for c in cand if c.is_valid]
    if not cand:
        return WindowStructure("neutral", np.nan, np.nan)
    return max(cand, key=lambda c: c.score)
