"""
divergence.py — Repérage des paires en consolidation amorçant un *double creux*
(double bottom) ou *double sommet* (double top) confirmé par une **divergence RSI**,
dans une plage ouverte par une réaction avec **climax**.

Lecture Wyckoff/VSA visée :
  Accumulation : après un Selling Climax (réaction qui stoppe la baisse et ouvre la
    plage), le prix revient tester le plancher. Le 2ᵉ creux fait un plus-bas ÉGAL ou
    PLUS BAS (double bottom / undercut) mais sur un volume plus sec ET un RSI PLUS HAUT
    (divergence haussière) : l'offre s'épuise. Un creux plus HAUT avec un RSI plus haut
    n'est PAS une divergence (le prix et le momentum montent ensemble = confirmation).
    Confirmation = cassure de la ligne de cou (sommet intermédiaire) → SOS.
  Distribution : miroir (Buying Climax → double top, sommet égal/plus haut + RSI plus
    bas → divergence baissière → SOW).

« Début de formation » = 2ᵉ pivot récent et ligne de cou pas encore cassée : le
signal est *précoce*, le pattern n'est pas confirmé. Aide à la décision, jamais
d'exécution automatique.

`df` doit déjà porter les features (add_features → colonnes rsi, vol_ratio, atr…).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .events import Thresholds
from .features import TradingRange, swing_points


@dataclass
class DivergenceParams:
    rsi_period: int = 14         # période du RSI (doit matcher add_features)
    min_rsi_div: float = 5.0     # écart RSI mini entre les deux pivots (points)
    double_tol_pct: float = 0.33 # ampleur max de l'undercut du 2e pivot, en fraction de hauteur
    equal_tol_pct: float = 0.003 # bande d'« égalité » des pivots (fraction de prix) : au-delà,
                                 # un 2e creux plus haut (resp. sommet plus bas) n'est plus une divergence
    support_frac: float = 0.33   # « près de la borne » : fraction de hauteur depuis la borne
    recent_bars: int = 8         # le 2ᵉ pivot doit tomber dans les N dernières barres
    left: int = 2                # fractale : barres à gauche d'un pivot
    right: int = 2               # fractale : barres à droite (retard de confirmation)
    # --- mode entrée live (entrer AU 2ᵉ creux, barre courante non confirmée) ---
    min_sep: int = 3             # séparation mini (barres) entre le 1er creux et le test courant
    min_bounce_frac: float = 0.25  # rebond mini entre les deux creux, en fraction de hauteur (vrai « W »)
    zone_atr: float = 0.6        # le test peut dépasser le 1er creux de zone_atr·ATR (côté plage)
    undercut_atr: float = 0.6    # undercut max sous/au-dessus du 1er creux (spring), en ATR
    entry_stop_atr: float = 0.5  # marge du stop au-delà du 2ᵉ creux, en ATR


@dataclass
class Pivot:
    ts: pd.Timestamp
    bars_ago: int
    price: float        # extrême du pivot (creux=low, sommet=high)
    rsi: float
    vol_ratio: float


@dataclass
class DoubleDivergence:
    symbol: str
    bias: str               # accumulation | distribution
    pattern: str            # "double bottom" | "double top"
    climax: str             # "SC" | "BC"
    climax_bars_ago: int
    climax_price: float
    climax_vol_ratio: float
    p1: Pivot               # 1er pivot (le plus ancien)
    p2: Pivot               # 2ᵉ pivot (le plus récent)
    price_diff_pct: float   # (p2 − p1) / p1 × 100  (négatif = 2ᵉ creux plus bas = undercut)
    rsi_div: float          # divergence dans le sens du biais (haussière >0, baissière >0)
    neckline: float         # ligne de cou : sommet (acc) / creux (dist) intermédiaire
    is_forming: bool        # 2ᵉ pivot récent ET ligne de cou non encore cassée
    strength: float         # 0..1
    why: str                # justification volume + divergence (sur les barres)
    theory: str             # rappel théorique + repères chiffrés

    def as_row(self) -> dict:
        return {
            "symbol": self.symbol,
            "pattern": self.pattern,
            "climax": f"{self.climax} (il y a {self.climax_bars_ago})",
            "p1": round(self.p1.price, 4),
            "p2": round(self.p2.price, 4),
            "Δprix_%": round(self.price_diff_pct, 2),
            "rsi1": round(self.p1.rsi, 1),
            "rsi2": round(self.p2.rsi, 1),
            "Δrsi": round(self.rsi_div, 1),
            "neckline": round(self.neckline, 4),
            "forming": "oui" if self.is_forming else "non",
            "p2_bars_ago": self.p2.bars_ago,
            "score": round(self.strength, 3),
            "volume/divergence → thèse": self.why,
            "théorie": self.theory,
        }


def _pivot(win: pd.DataFrame, pos: int, n_win: int, acc: bool) -> Pivot:
    bar = win.iloc[pos]
    vr = float(bar["vol_ratio"]) if not np.isnan(bar["vol_ratio"]) else 1.0
    rs = float(bar["rsi"]) if not np.isnan(bar["rsi"]) else 50.0
    price = float(bar["low"] if acc else bar["high"])
    # `win` est la queue de df (df.iloc[-lookback:]) → sa dernière barre est la dernière
    # de df, donc bars_ago se mesure directement dans la fenêtre.
    bars_ago = n_win - 1 - pos
    return Pivot(ts=win.index[pos], bars_ago=bars_ago, price=price, rsi=rs, vol_ratio=vr)


def _why(acc: bool, p1: Pivot, p2: Pivot, rsi_div: float) -> str:
    side = "vendeurs" if acc else "acheteurs"
    rsi_dir = "plus haut" if acc else "plus bas"
    kind = "creux" if acc else "sommet"
    if acc:
        price_rel = "plus bas" if p2.price < p1.price else "au même niveau"
    else:
        price_rel = "plus haut" if p2.price > p1.price else "au même niveau"
    return (
        f"2ᵉ {kind} {price_rel} ({p2.price:.4g} vs {p1.price:.4g}) mais RSI {rsi_dir} "
        f"({p2.rsi:.0f} vs {p1.rsi:.0f}, Δ{rsi_div:+.0f}) sur volume ×{p2.vol_ratio:.2f} "
        f"(vs ×{p1.vol_ratio:.2f} au 1er) → divergence : le prix n'améliore pas son extrême "
        f"alors que le momentum se retourne, la pression des {side} s'épuise."
    )


def _theory(acc: bool, th: Thresholds, params: DivergenceParams) -> str:
    if acc:
        return (
            "Double creux + divergence RSI haussière. En accumulation, le 2ᵉ test du "
            "plancher (ST/spring après le Selling Climax) fait un creux ÉGAL ou PLUS BAS "
            "mais sur un RSI PLUS HAUT et un volume plus sec : l'offre est absorbée. "
            "(Un creux plus HAUT avec un RSI plus haut n'est pas une divergence mais une "
            f"simple confirmation.) Repères : Δrsi ≥ {params.min_rsi_div:g} pts, volume du "
            f"test sec (≤ ×{th.test_vol}). Confirmation = cassure de la ligne de cou "
            "(sommet intermédiaire) en SOS."
        )
    return (
        "Double sommet + divergence RSI baissière. En distribution, le 2ᵉ test du plafond "
        "(ST/UTAD après le Buying Climax) fait un sommet ÉGAL ou PLUS HAUT mais sur un RSI "
        "PLUS BAS et un volume plus sec : la demande s'épuise. (Un sommet plus BAS avec un "
        "RSI plus bas n'est pas une divergence mais une simple confirmation.) Repères : "
        f"Δrsi ≥ {params.min_rsi_div:g} pts, volume du test sec (≤ ×{th.test_vol}). "
        "Confirmation = cassure de la ligne de cou (creux intermédiaire) en SOW."
    )


def _detect_side(
    symbol: str, df: pd.DataFrame, win: pd.DataFrame, tr: TradingRange,
    th: Thresholds, params: DivergenceParams, bias: str,
) -> DoubleDivergence | None:
    acc = bias == "accumulation"
    n_win = len(win)
    height = tr.height
    if not (height and height > 0):
        return None

    sw = swing_points(win, left=params.left, right=params.right)
    flag = sw["swing_low"] if acc else sw["swing_high"]
    border_tol = params.support_frac * height
    # pivots « près de la borne » (plancher en acc, plafond en dist)
    cand = []
    for pos in np.where(flag.values)[0]:
        extreme = float(win["low"].iloc[pos] if acc else win["high"].iloc[pos])
        near = (extreme <= tr.low + border_tol) if acc else (extreme >= tr.high - border_tol)
        if near:
            cand.append(int(pos))
    if len(cand) < 2:
        return None

    # 2ᵉ pivot = le plus récent ; il doit être « en formation » (récent)
    p2_pos = cand[-1]
    p2 = _pivot(win, p2_pos, n_win, acc)
    if p2.bars_ago > params.recent_bars:
        return None
    # 1er pivot = pivot qualifiant juste avant le 2ᵉ
    p1_pos = cand[-2]
    p1 = _pivot(win, p1_pos, n_win, acc)

    # Le 2e pivot doit rester dans la même zone (double) ET ne PAS améliorer l'extrême
    # dans le sens de la tendance. Un creux PLUS HAUT (resp. sommet plus bas) accompagné
    # d'un RSI qui suit n'est pas une divergence mais une simple confirmation.
    double_tol = params.double_tol_pct * height   # ampleur max de l'undercut (reste un double)
    eq = params.equal_tol_pct * p1.price          # bande d'« égalité » (bruit)
    if acc:
        if p2.price > p1.price + eq:              # 2e creux nettement plus haut → pas de divergence
            return None
        if p1.price - p2.price > double_tol:      # 2e creux trop bas → cassure, plus un double
            return None
    else:
        if p2.price < p1.price - eq:              # 2e sommet nettement plus bas → pas de divergence
            return None
        if p2.price - p1.price > double_tol:
            return None

    # divergence : le RSI part à contre-sens de l'absence d'amélioration du prix
    rsi_div = (p2.rsi - p1.rsi) if acc else (p1.rsi - p2.rsi)
    if rsi_div < params.min_rsi_div:
        return None

    # gate climax : une réaction climactique a ouvert la plage, avant/au 1er pivot
    climax_vr, climax_pos = 0.0, None
    for pos in range(0, p1_pos + 1):
        b = win.iloc[pos]
        vr = float(b["vol_ratio"]) if not np.isnan(b["vol_ratio"]) else 1.0
        extreme = float(b["low"] if acc else b["high"])
        near = (extreme <= tr.low + 0.3 * height) if acc else (extreme >= tr.high - 0.3 * height)
        if vr >= th.climax_vol and near and vr > climax_vr:
            climax_vr, climax_pos = vr, pos
    if climax_pos is None:
        return None
    climax = _pivot(win, climax_pos, n_win, acc)

    # ligne de cou = extrême opposé entre les deux pivots
    seg = win.iloc[p1_pos:p2_pos + 1]
    neckline = float(seg["high"].max() if acc else seg["low"].min())

    last_close = float(df["close"].iloc[-1])
    is_forming = (last_close < neckline) if acc else (last_close > neckline)

    # score : divergence, proximité, qualité climax, récence, assèchement volume
    div_score = float(np.clip(rsi_div / 20.0, 0, 1))
    close_score = float(np.clip(1 - abs(p2.price - p1.price) / double_tol, 0, 1))
    climax_score = float(np.clip((climax_vr - th.climax_vol) / max(th.climax_vol, 1e-9) + 0.5, 0, 1))
    recency = float(0.5 ** (p2.bars_ago / 6.0))
    vol_dry = float(np.clip((p1.vol_ratio - p2.vol_ratio) / max(p1.vol_ratio, 1e-9), 0, 1))
    strength = float(np.clip(
        0.35 * div_score + 0.20 * close_score + 0.15 * climax_score
        + 0.15 * recency + 0.15 * vol_dry, 0, 1))

    return DoubleDivergence(
        symbol=symbol, bias=bias,
        pattern="double bottom" if acc else "double top",
        climax="SC" if acc else "BC",
        climax_bars_ago=climax.bars_ago, climax_price=climax.price,
        climax_vol_ratio=climax_vr,
        p1=p1, p2=p2,
        price_diff_pct=(p2.price - p1.price) / p1.price * 100,
        rsi_div=rsi_div, neckline=neckline, is_forming=is_forming,
        strength=strength,
        why=_why(acc, p1, p2, rsi_div),
        theory=_theory(acc, th, params),
    )


def detect_double_divergence(
    symbol: str, df: pd.DataFrame, tr: TradingRange,
    th: Thresholds | None = None, params: DivergenceParams | None = None,
    lookback: int = 85,
) -> DoubleDivergence | None:
    """Renvoie le meilleur setup double creux/sommet + divergence RSI, ou None.

    On exige une plage valide (consolidation), une réaction climactique l'ayant
    ouverte, deux pivots proches près de la borne et une divergence RSI dans le sens
    du biais. On évalue les deux biais et retient le plus fort.
    """
    th = th or Thresholds()
    params = params or DivergenceParams()
    if tr is None or not tr.is_valid:
        return None
    win = df.iloc[-lookback:] if len(df) > lookback else df
    if len(win) < max(10, 2 * (params.left + params.right) + 2):
        return None

    cands = [
        _detect_side(symbol, df, win, tr, th, params, "accumulation"),
        _detect_side(symbol, df, win, tr, th, params, "distribution"),
    ]
    cands = [c for c in cands if c is not None]
    if not cands:
        return None
    return max(cands, key=lambda c: c.strength)


# --------------------------------------------------------------------------- #
# Mode « entrée live » : entrer AU 2ᵉ creux (barre courante, non confirmée)
# --------------------------------------------------------------------------- #
@dataclass
class FormingEntry:
    symbol: str
    bias: str                # accumulation (long) | distribution (short)
    pattern: str             # "double bottom" | "double top"
    climax: str              # SC | BC
    climax_bars_ago: int
    ref: Pivot               # 1er creux/sommet de référence (confirmé)
    test_ext: float          # extrême de la barre de test courante (low en acc, high en dist)
    test_close: float        # clôture de la barre courante
    test_clv: float
    test_vol_ratio: float
    rsi_ref: float
    rsi_now: float
    rsi_div: float
    neckline: float          # plafond du rebond (acc) / plancher (dist) = cible T1
    limit_level: float       # niveau d'achat/vente limite = zone du 1er creux
    stop: float              # juste au-delà du 2ᵉ creux
    target: float            # = ligne de cou (T1)
    measured: float          # objectif mesuré (hauteur de base projetée, T2)
    rr: float                # ratio risque/récompense jusqu'à la ligne de cou (entrée = clôture)
    confirmed: bool          # rejet haussier/baissier présent sur la barre courante
    strength: float
    why: str
    theory: str

    def as_row(self) -> dict:
        return {
            "symbol": self.symbol,
            "pattern": self.pattern,
            "climax": f"{self.climax} (il y a {self.climax_bars_ago})",
            "creux1" if self.bias == "accumulation" else "sommet1": round(self.ref.price, 6),
            "test": round(self.test_ext, 6),
            "limite": round(self.limit_level, 6),
            "stop": round(self.stop, 6),
            "neckline": round(self.neckline, 6),
            "T2": round(self.measured, 6),
            "R:R": round(self.rr, 2),
            "Δrsi": round(self.rsi_div, 1),
            "confirmé": "oui" if self.confirmed else "limite",
            "score": round(self.strength, 3),
            "volume/divergence → thèse": self.why,
            "théorie": self.theory,
        }


def _entry_why(acc: bool, ref: Pivot, rsi_now: float, rsi_div: float,
               clv: float, vr: float, confirmed: bool) -> str:
    side = "vendeurs" if acc else "acheteurs"
    kind = "creux" if acc else "sommet"
    rsi_dir = "plus haut" if acc else "plus bas"
    state = ("rejet confirmé (clôture " + ("haute" if acc else "basse")
             + f", clv {clv:.2f}) sur volume ×{vr:.2f}") if confirmed else \
            "test en cours, rejet non confirmé → achat/vente en limite sur la zone"
    return (f"retour sur la zone du 1er {kind} ({ref.price:.6g}) avec RSI {rsi_dir} "
            f"({rsi_now:.0f} vs {ref.rsi:.0f}, Δ{rsi_div:+.0f}) → divergence : la pression "
            f"des {side} faiblit au 2ᵉ test ; {state}.")


def _entry_theory(acc: bool, th: Thresholds) -> str:
    if acc:
        return ("Entrée au 2ᵉ creux d'un double bottom (spring/secondary test Wyckoff). "
                "On entre AU test du plancher — pas à la cassure — quand le RSI fait un "
                "creux plus haut (divergence) et que la demande se manifeste (clôture haute, "
                f"volume sec ≤ ×{th.test_vol} ou mèche basse). Risque serré : stop juste sous "
                "le 2ᵉ creux ; cible = ligne de cou puis objectif mesuré. Anticipatif : une "
                "partie des tests échoue, d'où le stop court et l'invalidation sous le support.")
    return ("Entrée au 2ᵉ sommet d'un double top (upthrust/secondary test). On vend AU test "
            "du plafond quand le RSI fait un sommet plus bas (divergence) et que l'offre "
            f"apparaît (clôture basse, volume sec ≤ ×{th.test_vol} ou mèche haute). Stop juste "
            "au-dessus du 2ᵉ sommet ; cible = ligne de cou puis objectif mesuré.")


def _entry_side(symbol: str, df: pd.DataFrame, win: pd.DataFrame, tr: TradingRange,
                th: Thresholds, params: DivergenceParams, bias: str) -> FormingEntry | None:
    acc = bias == "accumulation"
    height = tr.height
    if not (height and height > 0):
        return None
    atr = float(df["atr"].iloc[-1])
    if not atr or np.isnan(atr):
        return None
    n = len(win)

    cur = win.iloc[-1]
    test_ext = float(cur["low"] if acc else cur["high"])
    test_close = float(cur["close"])
    test_open = float(cur["open"])
    clv = float(cur["clv"])
    vr = float(cur["vol_ratio"]) if not np.isnan(cur["vol_ratio"]) else 1.0
    sa = float(cur["spread_atr"]) if not np.isnan(cur["spread_atr"]) else 1.0
    rsi_now = float(cur["rsi"]) if not np.isnan(cur["rsi"]) else 50.0
    prev_close = float(win["close"].iloc[-2]) if n >= 2 else test_close

    # 1er creux/sommet de référence : pivot confirmé le plus récent, près de la borne,
    # séparé d'au moins min_sep barres de la barre de test courante.
    sw = swing_points(win, left=params.left, right=params.right)
    flag = sw["swing_low"] if acc else sw["swing_high"]
    border_tol = params.support_frac * height
    ref_pos = None
    for pos in np.where(flag.values)[0]:
        ext = float(win["low"].iloc[pos] if acc else win["high"].iloc[pos])
        near = (ext <= tr.low + border_tol) if acc else (ext >= tr.high - border_tol)
        if near and (n - 1 - pos) >= params.min_sep:
            ref_pos = int(pos)  # boucle ascendante → garde le plus récent
    if ref_pos is None:
        return None
    ref = _pivot(win, ref_pos, n, acc)

    # climax ayant ouvert la plage, au/avant le 1er creux
    climax_vr, climax_pos = 0.0, None
    for pos in range(0, ref_pos + 1):
        b = win.iloc[pos]
        v = float(b["vol_ratio"]) if not np.isnan(b["vol_ratio"]) else 1.0
        ext = float(b["low"] if acc else b["high"])
        near = (ext <= tr.low + 0.3 * height) if acc else (ext >= tr.high - 0.3 * height)
        if v >= th.climax_vol and near and v > climax_vr:
            climax_vr, climax_pos = v, pos
    if climax_pos is None:
        return None
    climax = _pivot(win, climax_pos, n, acc)

    # rebond entre le 1er creux et maintenant (vrai « W ») → ligne de cou
    seg = win.iloc[ref_pos:n]
    neckline = float(seg["high"].max() if acc else seg["low"].min())
    bounce = (neckline - ref.price) if acc else (ref.price - neckline)
    if bounce < params.min_bounce_frac * height:
        return None

    # la barre courante teste la zone du 1er creux (undercut/spring toléré, reclaim exigé)
    if acc:
        in_zone = (test_ext <= ref.price + params.zone_atr * atr
                   and test_ext >= ref.price - params.undercut_atr * atr)
        reclaim = test_close >= ref.price - 0.10 * atr
    else:
        in_zone = (test_ext >= ref.price - params.zone_atr * atr
                   and test_ext <= ref.price + params.undercut_atr * atr)
        reclaim = test_close <= ref.price + 0.10 * atr
    if not (in_zone and reclaim):
        return None

    # divergence RSI au test courant
    rsi_div = (rsi_now - ref.rsi) if acc else (ref.rsi - rsi_now)
    if rsi_div < params.min_rsi_div:
        return None

    # confirmation de la demande/offre sur la barre courante (remplace la fractale)
    if acc:
        rejection = clv >= th.reclaim_clv
        not_wide_against = not (sa >= th.wide_spread_atr and clv < 0.4)
        momentum = (test_close > test_open) or (test_close >= prev_close)
    else:
        rejection = clv <= (1 - th.reclaim_clv)
        not_wide_against = not (sa >= th.wide_spread_atr and clv > 0.6)
        momentum = (test_close < test_open) or (test_close <= prev_close)
    vol_dry = vr <= th.test_vol * 1.3
    confirmed = bool(rejection and not_wide_against and (vol_dry or momentum))

    # niveaux
    limit_level = ref.price
    if acc:
        stop = test_ext - params.entry_stop_atr * atr
        target = neckline
        measured = neckline + (neckline - ref.price)
        rr = (target - test_close) / (test_close - stop) if test_close > stop else 0.0
        if target <= test_close:
            return None
    else:
        stop = test_ext + params.entry_stop_atr * atr
        target = neckline
        measured = neckline - (ref.price - neckline)
        rr = (test_close - target) / (stop - test_close) if stop > test_close else 0.0
        if target >= test_close:
            return None

    # score : divergence, proximité du test à la zone, demande, rebond, climax, confirmation
    div_s = float(np.clip(rsi_div / 20.0, 0, 1))
    zone_s = float(np.clip(1 - abs(test_ext - ref.price) / (params.zone_atr * atr + 1e-9), 0, 1))
    dem_s = (clv if acc else 1 - clv) * (1.0 if vol_dry else 0.7)
    bounce_s = float(np.clip(bounce / height, 0, 1))
    climax_s = float(np.clip((climax_vr - th.climax_vol) / max(th.climax_vol, 1e-9) + 0.5, 0, 1))
    strength = float(np.clip(0.30 * div_s + 0.20 * zone_s + 0.20 * dem_s
                             + 0.15 * bounce_s + 0.15 * climax_s, 0, 1))
    if confirmed:
        strength = min(1.0, strength + 0.1)

    return FormingEntry(
        symbol=symbol, bias=bias,
        pattern="double bottom" if acc else "double top",
        climax="SC" if acc else "BC",
        climax_bars_ago=climax.bars_ago, ref=ref,
        test_ext=test_ext, test_close=test_close, test_clv=clv, test_vol_ratio=vr,
        rsi_ref=ref.rsi, rsi_now=rsi_now, rsi_div=rsi_div,
        neckline=neckline, limit_level=limit_level, stop=stop, target=target,
        measured=measured, rr=float(rr), confirmed=confirmed, strength=strength,
        why=_entry_why(acc, ref, rsi_now, rsi_div, clv, vr, confirmed),
        theory=_entry_theory(acc, th),
    )


def detect_forming_entry(
    symbol: str, df: pd.DataFrame, tr: TradingRange,
    th: Thresholds | None = None, params: DivergenceParams | None = None,
    lookback: int = 85,
) -> FormingEntry | None:
    """Détecte une entrée AU 2ᵉ creux/sommet : la barre COURANTE teste la zone du 1er
    creux (non confirmée par fractale) avec divergence RSI et, idéalement, rejet de la
    borne. Renvoie le meilleur biais, ou None. Causal : n'utilise que `df` (la dernière
    barre = barre de test) → utilisable en live ET en backtest (df[:t+1])."""
    th = th or Thresholds()
    params = params or DivergenceParams()
    if tr is None or not tr.is_valid:
        return None
    win = df.iloc[-lookback:] if len(df) > lookback else df
    if len(win) < max(12, 2 * (params.left + params.right) + 2):
        return None
    cands = [
        _entry_side(symbol, df, win, tr, th, params, "accumulation"),
        _entry_side(symbol, df, win, tr, th, params, "distribution"),
    ]
    cands = [c for c in cands if c is not None]
    if not cands:
        return None
    return max(cands, key=lambda c: c.strength)
