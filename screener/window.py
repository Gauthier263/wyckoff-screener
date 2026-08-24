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
from .features import swing_points

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


# --------------------------------------------------------------------------- #
# Assèchement de l'offre : consolidation qui coile avant un potentiel markup
# --------------------------------------------------------------------------- #
def _slope(y) -> float:
    """Pente d'une régression linéaire (robuste au bruit vs comparaison barre-à-barre)."""
    y = np.asarray(y, dtype=float)
    y = y[~np.isnan(y)]
    if len(y) < 3:
        return 0.0
    x = np.arange(len(y), dtype=float)
    return float(np.polyfit(x, y, 1)[0])


@dataclass
class SupplyDryup:
    """Consolidation avec **assèchement progressif de l'offre** (miroir : de la demande).

    Détecteur GÉNÉRIQUE, sans contexte macro imposé : le coil est repéré de façon endogène
    (bande de prix + contraction de l'ATR), n'importe où — après un markup, en milieu de
    plage, etc. On y mesure un faisceau de signaux VSA (volume d'abord) qui, ensemble, disent
    que la pression vendeuse se tarit avant une reprise :

      s1  volume des barres OFFENSIVES (baissières en accu) en déclin
      s2  tests réussis (retours au support à volume décroissant, creux non-descendant)
      s3  asymétrie up/down (proxy-CVD : Σ vol·(2·CLV−1) qui monte = demande sous la surface)
      s4  contraction du coil (ATR de la 2ᵉ moitié < 1ʳᵉ moitié = ressort qui se comprime)
      s_spring  climax → spring → test du spring (Phase C, plus haut signal d'épuisement)

    `score` ∈ [0,1] pondère ces signaux (poids VSA : volume primaire). Tout est en unités
    ATR / ratio de volume → **identique en 15m, 1h, 4h** (Wyckoff fractal). Les événements
    internes réutilisent les tags Wyckoff (SC / SPRING / ST) avec leur théorie/justification.
    """
    bias: str
    support: float
    resistance: float
    height_atr: float = np.nan
    coil: bool = False
    n_tests: int = 0
    tests: list[WindowEvent] = field(default_factory=list)
    climax: WindowEvent | None = None
    spring: WindowEvent | None = None
    spring_test: WindowEvent | None = None
    signals: dict[str, float] = field(default_factory=dict)
    score: float = 0.0
    score_min: float = 0.60

    @property
    def events(self) -> list[WindowEvent]:
        evs = list(self.tests)
        for e in (self.climax, self.spring, self.spring_test):
            if e is not None:
                evs.append(e)
        evs.sort(key=lambda e: e.ts)
        return evs

    @property
    def directional(self) -> bool:
        # un assèchement n'est actionnable qu'avec le côté opposé PRÉSENT : demande sous la
        # surface (asymétrie proxy-CVD) OU shakeout de Phase C confirmé (spring + son test).
        return self.signals.get("s3", 0.0) >= 0.3 or (self.spring is not None and self.spring_test is not None)

    @property
    def is_valid(self) -> bool:
        # exploitable = vrai coil + ≥ 2 tests réussis + signal directionnel + score ≥ plancher
        return self.coil and self.n_tests >= 2 and self.directional and self.score >= self.score_min


# Poids des signaux dans le score composite (hiérarchie VSA : volume primaire).
_DRYUP_WEIGHTS = {"s1": 0.25, "s2": 0.25, "s3": 0.20, "s4": 0.15, "s_spring": 0.15}

# Un SPRING est un REJET, pas une simple bougie haussière : le low sous le support doit être
# rejeté par une MÈCHE BASSE dominante (≥ cette fraction du range de la barre). Sinon un gros
# corps vert qui pique sous le support serait pris à tort (cf. META). Calibré : vrais springs
# mèche 53-81 % du range, faux ~25 %. (Miroir : upthrust = mèche HAUTE dominante.)
_SPRING_WICK_FRAC = 0.50


def detect_supply_dryup(
    df: pd.DataFrame, th: Thresholds | None = None, oi=None, lookback: int = 40,
    bias: str = "accumulation", max_coil_atr: float = 10.0, score_min: float = 0.60,
) -> SupplyDryup:
    """Cherche, sur la fenêtre récente, une consolidation où l'offre s'assèche (accu) ou la
    demande s'assèche (dist). Aucun niveau à fournir : le coil et son support/résistance sont
    déduits des barres. `df` doit porter les features (add_features). `oi` optionnel n'annote
    que ΔOI par événement (la lecture OI/tierces sera une couche ultérieure).
    """
    th = th or Thresholds()
    acc = bias == "accumulation"
    full = df.iloc[-lookback:]
    nf = len(full)
    if nf < 12:
        return SupplyDryup(bias, np.nan, np.nan)

    # --- Coil ENDOGÈNE : on part de la dernière barre et on étend vers l'arrière tant que
    # l'amplitude (max_high − min_low) reste bornée en ATR. Un markup/markdown antérieur fait
    # exploser l'amplitude → il est naturellement exclu, isolant la consolidation récente. --- #
    atr_seed = float(np.nanmedian(full["atr"].values[-max(5, nf // 4):]))
    if np.isnan(atr_seed) or atr_seed <= 0:
        atr_seed = (float(full["high"].max()) - float(full["low"].min())) / max(nf, 1)
    highs, lows = full["high"].values, full["low"].values
    closes = full["close"].values
    c_end = float(closes[-1])
    mh, ml, start = highs[-1], lows[-1], nf - 1
    for i in range(nf - 2, -1, -1):
        nh, nl = max(mh, highs[i]), min(ml, lows[i])
        rng = nh - nl
        # (a) amplitude bornée en ATR ; (b) LATÉRALITÉ : le prix ne progresse pas net —
        # une dérive (|close_i − close_fin|) qui dépasse ~0.6× l'amplitude trahit une
        # tendance (markup/markdown antérieur) → on coupe la consolidation là.
        if rng > max_coil_atr * atr_seed:
            break
        if rng >= 1.5 * atr_seed and abs(c_end - float(closes[i])) > 0.6 * rng:
            break
        mh, ml, start = nh, nl, i
    win = full.iloc[start:]
    n = len(win)

    atr_ref = float(np.nanmedian(win["atr"].values))
    if np.isnan(atr_ref) or atr_ref <= 0:
        atr_ref = atr_seed
    # Support/résistance = MÉDIANE du cluster de pivots (le plancher/plafond réellement testé) —
    # robuste à un reliquat de markup en tête de fenêtre (ses quelques pivots ne pèsent pas
    # contre le cluster du coil). Repli sur quantiles si trop peu de pivots.
    sw = swing_points(win, left=2, right=2)
    lo_piv = win["low"].values[sw["swing_low"].values]
    hi_piv = win["high"].values[sw["swing_high"].values]
    support = float(np.median(lo_piv)) if len(lo_piv) >= 2 else float(win["low"].quantile(0.15))
    resistance = float(np.median(hi_piv)) if len(hi_piv) >= 2 else float(win["high"].quantile(0.85))
    height_atr = (resistance - support) / atr_ref if atr_ref else np.inf
    tol_lvl = 1.0 * atr_ref              # « au contact » du support/résistance : ≤ 1 ATR
    inband = float(((win["close"] >= support - atr_ref) & (win["close"] <= resistance + atr_ref)).mean())
    coil = n >= 8 and 0 < height_atr <= max_coil_atr and inband >= 0.60
    res = SupplyDryup(bias, support, resistance, height_atr=height_atr, coil=coil, score_min=score_min)
    if not coil:
        return res

    oi_aligned = None
    if oi is not None and len(oi):
        s = oi["oi"] if isinstance(oi, pd.DataFrame) else oi
        oi_aligned = s.reindex(df.index, method="nearest")

    base = len(df) - nf + start          # offset global du 1er bar du coil

    def g(pos: int) -> int:              # position locale (coil) -> index global (df)
        return base + pos

    def annotate(ev: WindowEvent) -> WindowEvent:
        if oi_aligned is not None:
            ev.oi_chg = _oi_pct(oi_aligned, df.index.get_loc(ev.ts), 3)
        return ev

    clv = win["clv"].values
    vr = np.where(np.isnan(win["vol_ratio"].values), 1.0, win["vol_ratio"].values)
    # côté « offensif » à assécher : offre = barres à clôture basse (accu), demande = hautes (dist)
    offensive = (clv < 0.5) if acc else (clv >= 0.5)

    # --- s1 : volume offensif en déclin (l'offre/demande qui « parle » s'affaiblit) ---- #
    off_vr = vr[offensive]
    s1 = 0.0
    if len(off_vr) >= 4:
        h = len(off_vr) // 2
        v0, v1 = float(np.mean(off_vr[:h])), float(np.mean(off_vr[h:]))
        s1 = float(np.clip((v0 - v1) / max(v0, 1e-9) / 0.5, 0, 1))  # −50 % de volume → 1.0

    # --- s3 : asymétrie up/down (proxy-CVD) : Σ vol·(2·CLV−1) qui monte (accu) --------- #
    signed = vr * (2.0 * clv - 1.0)
    cum = np.cumsum(signed)
    sl = _slope(cum) * (1 if acc else -1)   # accu : cumul haussier ; dist : baissier
    s3 = float(np.clip(sl / 0.15, 0, 1))

    # --- s4 : contraction du coil (ATR 2ᵉ moitié < 1ʳᵉ moitié = ressort qui se comprime) - #
    atrv = win["atr"].values
    h = n // 2
    a0, a1 = float(np.nanmedian(atrv[:h])), float(np.nanmedian(atrv[h:]))
    s4 = float(np.clip((a0 - a1) / max(a0, 1e-9) / 0.4, 0, 1))  # −40 % d'ATR → 1.0

    # --- s2 : tests réussis = TOUCHES distinctes de la zone de support/résistance à volume
    # DÉCROISSANT. On groupe les barres consécutives « au contact » en une touche (représentée
    # par sa barre extrême), séparée des suivantes par une sortie de zone. Plus robuste que des
    # pivots fractals dans le bruit. Support-indépendant : c'est la SÉQUENCE d'assèchement qui
    # compte, pas un seuil absolu (le 1ᵉʳ test peut être volumique ; l'important est qu'il tarisse).
    # La pénétration profonde (spring) sort de la zone → exclue ici, traitée en Phase C. #
    break_tol_test = 0.4 * atr_ref
    highs_w, lows_w = win["high"].values, win["low"].values

    def in_zone(j: int) -> bool:
        if acc:
            return support - break_tol_test <= lows_w[j] <= support + tol_lvl
        return resistance - tol_lvl <= highs_w[j] <= resistance + break_tol_test

    touches: list[int] = []            # index (local) de la barre extrême de chaque touche
    j = 0
    while j < n:
        if not in_zone(j):
            j += 1
            continue
        best = j
        while j < n and in_zone(j):
            if (lows_w[j] < lows_w[best]) if acc else (highs_w[j] > highs_w[best]):
                best = j
            j += 1
        touches.append(best)

    tests: list[WindowEvent] = []
    prev_vol, prev_ext = np.inf, None
    for t in touches:
        vt = float(vr[t])
        ext = float(lows_w[t] if acc else highs_w[t])
        holds = prev_ext is None or (ext >= prev_ext - 0.15 * atr_ref if acc
                                     else ext <= prev_ext + 0.15 * atr_ref)
        if vt <= prev_vol * 1.1 and holds:
            tests.append(annotate(_mk(df, g(t), "ST", bias, th)))
            prev_vol, prev_ext = vt, ext
    s2 = float(np.clip(len(tests) / 3.0, 0, 1))

    # --- s_spring : climax (optionnel) → spring → test du spring (Phase C) ------------- #
    # Spring (accu) : pénétration brève sous le support puis clôture revenue dans la bande.
    spring = spring_test = climax = None
    spr_pos, spr_best = None, None
    for j in range(n):
        b = win.iloc[j]
        # Le spring/upthrust doit RECLÔTURER DANS LA PLAGE (support ≤ close ≤ résistance) :
        # une bougie qui pénètre la borne mais clôture DE L'AUTRE CÔTÉ de la plage est une
        # CASSURE (breakout climactique), pas un shakeout — ex. ONT ×17.3 qui casse au-dessus
        # de la résistance. En plus du rejet (clv) et du retour du bon côté de la borne pénétrée.
        # ET le low/high pénétré doit être REJETÉ par une MÈCHE dominante (≥ _SPRING_WICK_FRAC du
        # range) : un gros CORPS haussier qui pique sous le support n'est pas un rejet, juste une
        # bougie haussière (cf. META). La mèche ≥ 50 % implique déjà clv ≥ 0.5.
        o, c = float(b["open"]), float(b["close"])
        rng_bar = float(b["high"]) - float(b["low"])
        in_range = support <= c <= resistance
        if acc:
            pen = support - float(b["low"])
            lower_wick = min(o, c) - float(b["low"])
            recl = in_range and c >= support and rng_bar > 0 and lower_wick >= _SPRING_WICK_FRAC * rng_bar
        else:
            pen = float(b["high"]) - resistance
            upper_wick = float(b["high"]) - max(o, c)
            recl = in_range and c <= resistance and rng_bar > 0 and upper_wick >= _SPRING_WICK_FRAC * rng_bar
        if pen >= th.pen_atr * atr_ref and recl and (spr_best is None or pen > spr_best):
            spr_best, spr_pos = pen, j
    if spr_pos is not None:
        spring = annotate(_mk(df, g(spr_pos), "SPRING" if acc else "UTAD", bias, th))
        spr_ext = float(win.iloc[spr_pos]["low"] if acc else win.iloc[spr_pos]["high"])
        # test du spring : après le spring, retour au support à volume SEC, extrême non dépassé
        best_v = None
        for j in range(spr_pos + 1, n):
            b = win.iloc[j]
            vj = float(vr[j])
            if acc:
                near = float(b["low"]) <= support + tol_lvl and float(b["low"]) >= spr_ext - 0.1 * atr_ref
                holds = float(b["close"]) >= support
            else:
                near = float(b["high"]) >= resistance - tol_lvl and float(b["high"]) <= spr_ext + 0.1 * atr_ref
                holds = float(b["close"]) <= resistance
            if near and holds and vj <= th.test_vol and (best_v is None or vj < best_v):
                best_v, spring_test = vj, annotate(_mk(df, g(j), "ST", bias, th))
    # Climax optionnel : barre large + volume climactique faisant l'extrême, en début de coil.
    head = win.iloc[: max(3, n // 2)]
    cpos = int(head["low"].values.argmin() if acc else head["high"].values.argmax())
    cbar = win.iloc[cpos]
    cvr = float(vr[cpos])
    csa = float(cbar["spread_atr"]) if not np.isnan(cbar["spread_atr"]) else 1.0
    if cvr >= th.climax_vol and csa >= th.wide_spread_atr:
        climax = annotate(_mk(df, g(cpos), "SC" if acc else "BC", bias, th))
    s_spring = 0.5 * (spring is not None) + 0.5 * (spring_test is not None)

    signals = {"s1": s1, "s2": s2, "s3": s3, "s4": s4, "s_spring": s_spring}
    score = float(sum(_DRYUP_WEIGHTS[k] * v for k, v in signals.items()))

    res.n_tests = len(tests)
    res.tests = tests
    res.climax, res.spring, res.spring_test = climax, spring, spring_test
    res.signals = signals
    res.score = score
    return res
