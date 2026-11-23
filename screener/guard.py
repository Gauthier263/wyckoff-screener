"""Garde-fou avant un trade (A1) et unité de temps de structure (A8).

Né du post-mortem des shorts du dimanche 22/11/2026 : deux shorts pris sur une plage 5 min de
501 points, qui ne faisait que 0,8 ATR à l'échelle 1h, celle de la structure. Les stops étaient
à 0,2–0,3 ATR 1h, la séance était creuse, et le spring de 03h puis la poussée de 04h ont balayé
les niveaux. Ce module rend les contrôles explicites et chiffrés. Ce n'est **pas** une boîte
noire : chaque point dit ce qu'il mesure, la valeur observée et le seuil.

- :func:`structure_tf` : choisit l'unité de temps qui commande (plage du climax ≥ 5 ATR, 20 à
  80 bougies). Un niveau tiré d'une plage < 1 ATR de cette unité = « niveau interne, ne pas
  trader seul ».
- :func:`check_trade` : verdict vert / orange / rouge sur 9 points (8 du garde-fou A1 + la
  règle de niveau A8). Aide à la décision : le verdict **alerte**, il n'empêche rien.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from screener.features import atr as _atr
from screener.session import is_thin, session_of

MIN_HEIGHT_ATR = 5.0       # plage de structure : au moins 5 ATR de haut…
BARS_RANGE = (20, 80)      # … et 20 à 80 bougies de long
TARGET_BARS = 50           # à égalité, l'unité la plus proche de ~50 bougies
LEVEL_MIN_ATR = 1.0        # niveau tiré d'une plage < 1 ATR de structure = bruit
STOP_MARGIN_ATR = 0.5      # stop au-delà de l'invalidation d'au moins 0,5 ATR
WICK_CLEAR_ATR = 0.25      # stop pas collé (< 0,25 ATR) à l'extrême des 24 h
MIN_RR = 2.0               # gain à la 1re cible ≥ 2 × le risque
EDGE_FRAC = 0.25           # short dans le quart haut, long dans le quart bas
MAX_ATTEMPTS = 2           # 1re ou 2e tentative dans ce sens le même jour


def _n(x: float) -> str:
    """Prix à la française : « 55 130 »."""
    return f"{x:,.0f}".replace(",", "\u202f")


def _as_utc(ts) -> pd.Timestamp:
    """Horodatage → UTC aware (un horodatage naïf est lu comme de l'UTC réel)."""
    ts = pd.Timestamp(ts)
    return ts.tz_localize("UTC") if ts.tzinfo is None else ts.tz_convert("UTC")


# --------------------------------------------------------------------------- #
# A8 — unité de temps de structure
# --------------------------------------------------------------------------- #
@dataclass
class TfStat:
    tf: str
    bars: int
    atr: float
    height: float
    height_atr: float
    eligible: bool


@dataclass
class StructureTF:
    tf: str
    atr: float
    low: float
    high: float
    bars: int
    height_atr: float
    eligible: bool                    # False = aucune unité ne remplit les deux critères
    table: list[TfStat] = field(default_factory=list)

    def is_internal(self, span: float) -> bool:
        """Plage d'origine d'un niveau (en points) < 1 ATR de structure → niveau interne."""
        return span < LEVEL_MIN_ATR * self.atr

    def header(self) -> str:
        """Ligne d'en-tête imposée en tête de chaque analyse / suivi."""
        tag = "" if self.eligible else " (aucune unité ne remplit 5 ATR / 20–80 bougies : la plus proche)"
        return (f"Unité de structure : {self.tf} (ATR {_n(self.atr)} ; plage "
                f"{_n(self.low)}–{_n(self.high)} = {f"{self.height_atr:.1f}".replace(".", ",")} ATR, "
                f"{self.bars} bougies){tag}. Niveau < {_n(self.atr * LEVEL_MIN_ATR)} points "
                f"= interne, ne pas trader seul.")


def structure_tf(frames: dict[str, pd.DataFrame], start, end=None,
                 atr_period: int = 14) -> StructureTF:
    """Choisit l'unité de temps de structure parmi ``frames`` ({"5m": df, "1h": df, …}, index
    en UTC réel) pour la plage qui commence à ``start`` (le climax) et finit à ``end``.

    Pour chaque unité : hauteur de la plage (max high − min low) en ATR de l'unité (ATR à la
    dernière barre de la fenêtre) et nombre de bougies. Éligible si hauteur ≥ 5 ATR et 20 à 80
    bougies ; parmi les éligibles, celle dont le nombre de bougies est le plus proche de 50.
    Si aucune n'est éligible, la plus proche de la bande de bougies (signalée)."""
    start = _as_utc(start)
    end = _as_utc(end) if end is not None else None
    stats: list[tuple[TfStat, float, float]] = []
    for tf, df in frames.items():
        a = _atr(df, atr_period)
        step = df.index.to_series().diff().median() if len(df) > 1 else pd.Timedelta(0)
        m = df.index + step > start                 # inclut la bougie qui contient `start`
        if end is not None:
            m &= df.index <= end
        w = df[m]
        if w.empty:
            continue
        a_end = float(a.loc[w.index[-1]])
        if not a_end == a_end or a_end <= 0:     # NaN : pas assez d'historique
            continue
        lo, hi = float(w["low"].min()), float(w["high"].max())
        h_atr = (hi - lo) / a_end
        ok = h_atr >= MIN_HEIGHT_ATR and BARS_RANGE[0] <= len(w) <= BARS_RANGE[1]
        stats.append((TfStat(tf, len(w), a_end, hi - lo, h_atr, ok), lo, hi))
    if not stats:
        raise ValueError("aucune unité de temps ne couvre la fenêtre demandée")
    elig = [s for s in stats if s[0].eligible]
    if elig:
        best = min(elig, key=lambda s: abs(s[0].bars - TARGET_BARS))
    else:
        def gap(s):
            n = s[0].bars
            return max(BARS_RANGE[0] - n, n - BARS_RANGE[1], 0)
        best = min(stats, key=lambda s: (gap(s), -s[0].height_atr))
    b, lo, hi = best
    return StructureTF(b.tf, b.atr, lo, hi, b.bars, b.height_atr, bool(elig),
                       [s[0] for s in stats])


# --------------------------------------------------------------------------- #
# A1 — garde-fou
# --------------------------------------------------------------------------- #
OK, KO, UNKNOWN = "ok", "ko", "?"
CRITICAL = ("cadre", "niveau", "stop", "gain/risque", "tentatives")


@dataclass
class Point:
    key: str
    status: str            # ok / ko / ?
    detail: str


@dataclass
class GuardResult:
    verdict: str           # vert / orange / rouge
    points: list[Point]
    breakeven: float
    partial: float
    risk: float

    def summary(self) -> str:
        n_ok = sum(p.status == OK for p in self.points)
        ko = [p.key for p in self.points if p.status == KO]
        tail = f" — en défaut : {', '.join(ko)}" if ko else ""
        return f"Garde-fou : {self.verdict.upper()} ({n_ok}/{len(self.points)}){tail}"


def check_trade(*, side: str, entry: float, stop: float, target: float,
                when, struct: StructureTF,
                frame_bias: str | None = None,
                invalidation: float | None = None,
                level_span: float | None = None,
                recent_extreme: float | None = None,
                attempts_before: int | None = None,
                mirror_plan: str | None = None) -> GuardResult:
    """Verdict sur un trade envisagé.

    side            "short" / "long"
    entry/stop/target  prix ; ``target`` = 1re cible
    when            horodatage de l'entrée (UTC réel)
    struct          résultat de :func:`structure_tf` (ATR + bornes de la plage de structure)
    frame_bias      biais de l'unité de structure : "bear" / "bull" / "neutral"
    invalidation    prix qui invalide la thèse (UT, borne de plage) ; le stop doit être au-delà
    level_span      hauteur (points) de la plage dont viennent l'entrée et le stop
    recent_extreme  plus-haut 24 h (short) ou plus-bas 24 h (long) : zone de stops évidente
    attempts_before tentatives déjà prises dans ce sens aujourd'hui (cf. journal.attempts_today)
    mirror_plan     texte du scénario inverse (spring / upthrust) ; None = non écrit

    Rouge si un point critique (cadre, niveau, stop, gain/risque, tentatives) est en défaut ;
    orange si un point non critique est en défaut ou si un point critique est inconnu ; vert
    sinon. Le point « protection du gain » est toujours rempli : on fournit les prix."""
    side = side.lower()
    if side not in ("short", "long"):
        raise ValueError("side = short ou long")
    sgn = 1 if side == "short" else -1          # short : stop au-dessus, cible en dessous
    a = struct.atr
    risk = (stop - entry) * sgn
    if risk <= 0:
        raise ValueError("stop du mauvais côté de l'entrée")
    pts: list[Point] = []

    # 1. cadre
    pos = (entry - struct.low) / (struct.high - struct.low) if struct.high > struct.low else 0.5
    at_edge = pos >= 1 - EDGE_FRAC if side == "short" else pos <= EDGE_FRAC
    want = "bear" if side == "short" else "bull"
    if frame_bias is None:
        pts.append(Point("cadre", UNKNOWN, "biais de l'unité de structure non fourni"))
    elif frame_bias == want or at_edge:
        why = "dans le sens du cadre" if frame_bias == want else "trade de borne"
        pts.append(Point("cadre", OK, f"cadre {struct.tf} {frame_bias} — {why}"))
    else:
        pts.append(Point("cadre", KO, f"cadre {struct.tf} {frame_bias} contre un {side} "
                                      f"hors borne : pas de continuation"))
    # 2. niveau (A8)
    if level_span is None:
        pts.append(Point("niveau", UNKNOWN, "hauteur de la plage d'origine du niveau non fournie"))
    else:
        ok = not struct.is_internal(level_span)
        pts.append(Point("niveau", OK if ok else KO,
                         f"plage d'origine {level_span:.0f} pts = {level_span / a:.2f} ATR "
                         f"{struct.tf} (seuil {LEVEL_MIN_ATR:g})"
                         + ("" if ok else " : niveau interne")))
    # 3. position dans la plage
    zone = "quart haut" if side == "short" else "quart bas"
    pts.append(Point("position", OK if at_edge else KO,
                     f"entrée à {pos:.0%} de la plage {struct.tf} ({zone} attendu)"))
    # 4. séance
    ts = _as_utc(when)
    thin = is_thin(ts)
    pts.append(Point("séance", KO if thin else OK,
                     f"{session_of(ts)}" + (" : séance creuse, taille réduite et stop plus large"
                                            if thin else "")))
    # 5. stop
    det, st = [], OK
    if invalidation is None:
        st = UNKNOWN
        det.append("invalidation non fournie")
    else:
        margin = (stop - invalidation) * sgn
        det.append(f"marge au-delà de l'invalidation {margin:+.0f} pts = {margin / a:+.2f} ATR "
                   f"(≥ {STOP_MARGIN_ATR:g})")
        if margin < STOP_MARGIN_ATR * a:
            st = KO
    if recent_extreme is not None:
        gap = abs(stop - recent_extreme)
        det.append(f"à {gap:.0f} pts de l'extrême 24 h ({gap / a:.2f} ATR)")
        if gap < WICK_CLEAR_ATR * a:
            st = KO
            det.append("stop collé à une zone de stops évidente")
    det.append(f"risque {risk:.0f} pts = {risk / a:.2f} ATR")
    pts.append(Point("stop", st, " ; ".join(det)))
    # 6. gain/risque
    reward = (entry - target) * sgn
    rr = reward / risk
    pts.append(Point("gain/risque", OK if rr >= MIN_RR else KO,
                     f"{rr:.2f} R à la 1re cible (≥ {MIN_RR:g})"))
    # 7. tentatives
    if attempts_before is None:
        pts.append(Point("tentatives", UNKNOWN, "nombre de tentatives du jour inconnu"))
    else:
        n = attempts_before + 1
        pts.append(Point("tentatives", OK if n <= MAX_ATTEMPTS else KO,
                         f"tentative n° {n} dans ce sens aujourd'hui (max {MAX_ATTEMPTS})"))
    # 8. protection du gain
    be = entry - sgn * risk
    part = entry - sgn * 2 * risk
    pts.append(Point("protection", OK, f"stop au point mort quand le prix touche {be:.0f} (+1 R) ; partiel à {part:.0f} (+2 R)"))
    # 9. plan miroir
    pts.append(Point("miroir", OK if mirror_plan else KO,
                     mirror_plan or "scénario inverse non écrit"))

    crit_ko = any(p.status == KO and p.key in CRITICAL for p in pts)
    crit_unk = any(p.status == UNKNOWN and p.key in CRITICAL for p in pts)
    other_ko = any(p.status == KO and p.key not in CRITICAL for p in pts)
    verdict = "rouge" if crit_ko else ("orange" if (other_ko or crit_unk) else "vert")
    return GuardResult(verdict, pts, be, part, risk)
