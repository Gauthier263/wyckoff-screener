"""
divergence.py — Repérage des paires en consolidation amorçant un *double creux*
(double bottom) ou *double sommet* (double top) confirmé par une **divergence RSI**,
dans une plage ouverte par une réaction avec **climax**.

Lecture Wyckoff/VSA visée :
  Accumulation : après un Selling Climax (réaction qui stoppe la baisse et ouvre la
    plage), le prix revient tester le plancher. Si ce 2ᵉ creux tient au même niveau
    (≈ double bottom) sur un volume plus sec ET un RSI plus haut (divergence
    haussière), l'offre s'épuise : chaque test trouve moins de vendeurs. Confirmation
    = cassure de la ligne de cou (sommet intermédiaire) → SOS.
  Distribution : miroir (Buying Climax → double top → divergence baissière → SOW).

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
    double_tol_pct: float = 0.33 # proximité des deux pivots, en fraction de la hauteur de plage
    support_frac: float = 0.33   # « près de la borne » : fraction de hauteur depuis la borne
    recent_bars: int = 8         # le 2ᵉ pivot doit tomber dans les N dernières barres
    left: int = 2                # fractale : barres à gauche d'un pivot
    right: int = 2               # fractale : barres à droite (retard de confirmation)


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
    return (
        f"2ᵉ {'creux' if acc else 'sommet'} ≈ 1er ({p2.price:.4g} vs {p1.price:.4g}) "
        f"mais RSI {rsi_dir} ({p2.rsi:.0f} vs {p1.rsi:.0f}, Δ{rsi_div:+.0f}) sur volume "
        f"×{p2.vol_ratio:.2f} (vs ×{p1.vol_ratio:.2f} au 1er) → la pression des {side} "
        f"s'épuise : chaque test de la borne en trouve moins."
    )


def _theory(acc: bool, th: Thresholds, params: DivergenceParams) -> str:
    if acc:
        return (
            "Double creux + divergence RSI haussière. En accumulation, le 2ᵉ test du "
            "plancher (ST/spring après le Selling Climax) sur momentum plus haut et "
            "volume plus sec trahit l'absorption de l'offre par les mains fortes. "
            f"Repères : 2ᵉ creux à ±{params.double_tol_pct:.0%} de la hauteur de plage du 1er, "
            f"Δrsi ≥ {params.min_rsi_div:g} pts, volume du test sec (≤ ×{th.test_vol}). "
            "Confirmation = cassure de la ligne de cou (sommet intermédiaire) en SOS."
        )
    return (
        "Double sommet + divergence RSI baissière. En distribution, le 2ᵉ test du "
        "plafond (ST/UTAD après le Buying Climax) sur momentum plus bas et volume plus "
        "sec trahit l'épuisement de la demande. "
        f"Repères : 2ᵉ sommet à ±{params.double_tol_pct:.0%} de la hauteur de plage du 1er, "
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

    # proximité des deux pivots (≈ double bottom/top)
    double_tol = params.double_tol_pct * height
    if abs(p2.price - p1.price) > double_tol:
        return None

    # divergence dans le sens du biais
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
