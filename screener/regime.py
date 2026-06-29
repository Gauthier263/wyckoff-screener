"""
regime.py — Détecteur d'« état du cours » (régime de marché).

Complément amont des détecteurs d'événements : avant de chercher un setup Wyckoff,
ce module répond à la question « suis-je dans un régime où les niveaux / order
blocks seront respectés ? ». Il classe la fenêtre récente dans un des 7 états
décrits dans `etats_du_cours.html` et renvoie un drapeau `tradable` (gate ON/OFF) :

    RANGE_ON    — plage opérée par le MM (équilibre)        → seul état ON
    TREND       — markup / markdown impulsif (Phase E)       → OFF (ne pas fader)
    CLIMAX      — selling / buying climax en cours           → OFF
    VOL_EXPANSION — expansion de volatilité / news           → OFF
    LOW_LIQ     — vide de liquidité / drift                  → OFF
    CHOP        — bruit sans structure                       → OFF
    LIQUIDATION — cascade de liquidation / déleveraging       → OFF

Tout reste transparent et ajustable (`RegimeThresholds`). L'ordre de lecture suit
la hiérarchie VSA : volume → OI (les métriques tierces restent hors scope ici).
Les états « OFF » les plus aigus priment ; à défaut d'anomalie, on retombe sur
RANGE_ON (plage valide) ou CHOP (pas de structure).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .features import TradingRange

# Libellés FR courts (couleur = sens, cf. CLAUDE.md / etats_du_cours.html)
STATE_LABELS: dict[str, str] = {
    "RANGE_ON": "Plage opérée",
    "TREND": "Markup/Markdown",
    "CLIMAX": "Climax",
    "VOL_EXPANSION": "Expansion volatilité",
    "LOW_LIQ": "Vide de liquidité",
    "CHOP": "Chop / bruit",
    "LIQUIDATION": "Cascade liquidation",
}


@dataclass
class RegimeThresholds:
    """Seuils du classificateur de régime — transparents, ajustables (config.yaml)."""
    recent: int = 12              # barres récentes évaluées pour l'état courant
    climax_window: int = 3        # un climax doit être dans les N dernières barres
    climax_vol: float = 2.0       # vol_ratio d'une barre climactique
    climax_spread_atr: float = 2.0  # spread_atr d'une barre climactique
    wide_spread_atr: float = 1.3  # barre « large »
    atr_expansion: float = 1.8    # ATR_t / ATR_ref pour une expansion de volatilité
    expansion_wide_bars: int = 3  # nb de barres larges (≠ climax isolé)
    low_liq_vol: float = 0.5      # médiane vol_ratio sous laquelle = vide de liquidité
    trend_move_atr: float = 4.0   # déplacement net (en ATR) sur la fenêtre = tendance
    trend_consistency: float = 0.6  # fraction de barres dans le même sens
    liq_oi_drop_pct: float = 2.0  # chute d'OI coin (%) sur la fenêtre = déleveraging


@dataclass
class Regime:
    state: str            # clé de STATE_LABELS
    tradable: bool        # gate ON/OFF (True uniquement pour RANGE_ON)
    why: str              # justification lisible (volume → OI)
    signals: dict         # métriques calculées, pour transparence/ajustement

    @property
    def label(self) -> str:
        return STATE_LABELS.get(self.state, self.state)

    def as_row(self, symbol: str | None = None) -> dict:
        row = {
            "state": self.state,
            "label": self.label,
            "tradable": "ON" if self.tradable else "OFF",
            "why": self.why,
        }
        if symbol is not None:
            return {"symbol": symbol, **row}
        return row


def _align_oi(oi, index: pd.Index):
    """Réaligne une série/DataFrame d'OI sur l'index des barres (même logique que window)."""
    if oi is None or not len(oi):
        return None
    s = oi["oi"] if isinstance(oi, pd.DataFrame) else oi
    return s.reindex(index, method="nearest")


def tag_regime(
    df: pd.DataFrame,
    tr: TradingRange,
    oi=None,
    th: RegimeThresholds | None = None,
) -> Regime:
    """Classe la fenêtre récente de `df` (features VSA déjà calculées) dans un état.

    `tr` : la plage détectée (`detect_trading_range`) sert de contexte d'équilibre.
    `oi` : Open Interest (coin) optionnel — affine LIQUIDATION et la confiance.
    """
    th = th or RegimeThresholds()
    n = len(df)
    if n < max(th.recent, th.climax_window) + 1:
        return Regime("CHOP", False, "données insuffisantes pour classer l'état", {})

    r = min(th.recent, n - 1)
    tail = df.iloc[-r:]
    vr = tail["vol_ratio"].to_numpy(dtype=float)
    sa = tail["spread_atr"].to_numpy(dtype=float)
    ret = tail["ret"].to_numpy(dtype=float)
    atr_last = float(df["atr"].iloc[-1])
    atr_ref = float(df["atr"].iloc[-1 - r])
    close_last = float(df["close"].iloc[-1])
    close_ref = float(df["close"].iloc[-1 - r])

    # --- signaux volume/spread (force primaire) ---
    cw = df.iloc[-th.climax_window:]
    climax_bar = bool(
        ((cw["vol_ratio"] >= th.climax_vol) & (cw["spread_atr"] >= th.climax_spread_atr)).any()
    )
    wide_bars = int(np.nansum(sa >= th.wide_spread_atr))
    atr_ratio = atr_last / atr_ref if atr_ref and not np.isnan(atr_ref) else np.nan
    med_vr = float(np.nanmedian(vr)) if len(vr) else np.nan

    # déplacement net en ATR + cohérence directionnelle
    net_atr = (close_last - close_ref) / atr_last if atr_last and not np.isnan(atr_last) else 0.0
    up = float(np.nanmean(ret > 0)) if len(ret) else 0.0
    down = float(np.nanmean(ret < 0)) if len(ret) else 0.0
    consistency = max(up, down)
    directional = abs(net_atr) >= th.trend_move_atr and consistency >= th.trend_consistency

    # --- OI (le volume ouvre-t-il ou ferme-t-il des positions ?) ---
    oi_aligned = _align_oi(oi, df.index)
    oi_chg_pct = np.nan
    if oi_aligned is not None and len(oi_aligned) > r:
        a, b = float(oi_aligned.iloc[-1]), float(oi_aligned.iloc[-1 - r])
        if b:
            oi_chg_pct = (a - b) / abs(b) * 100.0

    signals = {
        "climax_bar": climax_bar,
        "wide_bars": wide_bars,
        "atr_ratio": None if np.isnan(atr_ratio) else round(atr_ratio, 2),
        "med_vol_ratio": None if np.isnan(med_vr) else round(med_vr, 2),
        "net_move_atr": round(net_atr, 2),
        "directional": directional,
        "oi_chg_pct": None if np.isnan(oi_chg_pct) else round(oi_chg_pct, 2),
        "range_valid": bool(tr.is_valid),
    }

    # ----------------------------------------------------------------- #
    # Classification — états OFF les plus aigus d'abord, puis ON / CHOP.
    # ----------------------------------------------------------------- #

    # 1) LIQUIDATION : OI coin s'effondre + mouvement directionnel large (positions
    #    fermées de force ; à distinguer d'un markdown sain où l'OI monte).
    if (not np.isnan(oi_chg_pct) and oi_chg_pct <= -th.liq_oi_drop_pct
            and directional and wide_bars >= 1):
        sens = "baisse" if net_atr < 0 else "hausse"
        return Regime("LIQUIDATION", False,
                      f"OI coin {oi_chg_pct:+.1f}% (positions fermées de force) + {sens} "
                      f"de {abs(net_atr):.1f} ATR sur barres larges → purge, niveaux ignorés",
                      signals)

    # 2) CLIMAX : barre dominante très volumique + spread très large, très récente.
    if climax_bar:
        return Regime("CLIMAX", False,
                      f"barre climactique récente (vol ≥ ×{th.climax_vol}, spread ≥ "
                      f"{th.climax_spread_atr} ATR) → transfert de panique/euphorie, aucun niveau ne tient",
                      signals)

    # 3) VOL_EXPANSION : ATR qui saute + plusieurs barres larges (repricing, news).
    if (not np.isnan(atr_ratio) and atr_ratio >= th.atr_expansion
            and wide_bars >= th.expansion_wide_bars):
        return Regime("VOL_EXPANSION", False,
                      f"ATR ×{atr_ratio:.1f} + {wide_bars} barres larges → repricing, "
                      f"OB vaporisés (attendre le retour de l'ATR)",
                      signals)

    # 4) LOW_LIQ : volume durablement famélique.
    if not np.isnan(med_vr) and med_vr <= th.low_liq_vol:
        return Regime("LOW_LIQ", False,
                      f"volume médian ×{med_vr:.2f} (carnet fin) → faux respect / fausses "
                      f"cassures, ne pas valider d'OB",
                      signals)

    # 5) TREND : déplacement net directionnel (Phase E) — la plage ne tient pas.
    if directional:
        sens = "markup (hausse)" if net_atr > 0 else "markdown (baisse)"
        return Regime("TREND", False,
                      f"{sens} : {abs(net_atr):.1f} ATR nets, {consistency*100:.0f}% des barres "
                      f"dans le sens → continuation, OB contraires balayés",
                      signals)

    # 6) RANGE_ON : plage valide et aucune anomalie → seul état tradable.
    if tr.is_valid:
        oi_note = "" if np.isnan(oi_chg_pct) else f", OI stable ({oi_chg_pct:+.1f}%)"
        return Regime("RANGE_ON", True,
                      f"équilibre : plage valide, volume normal (méd. ×{med_vr:.2f}), "
                      f"pas d'expansion ni de climax{oi_note} → niveaux/OB défendables",
                      signals)

    # 7) CHOP : pas de plage exploitable, pas de tendance → bruit.
    return Regime("CHOP", False,
                  "ni plage valide ni tendance nette → bruit (whipsaw), pas de structure à trader",
                  signals)
