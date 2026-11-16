"""Contexte de séance (week-end / reprise du lundi) pour le VSA BTC.

Étude 2019→2026 (Binance spot, cf. memos/weekend_btc.md) :
- samedi / dimanche jusqu'à 20h UTC : volume ≈ 0,47× la même heure en semaine, range ≈ 0,55× ;
- dimanche 20h UTC → lundi 06h UTC (reprise : CME, Asie) : volume et range revenus ≈ 1× ;
- cassures de week-end : 76 % reviennent dans la plage sous 12 h (66 % en semaine).

Le Rvol(20) habituel s'adapte au week-end (sa moyenne est faite de barres de week-end) et
masque cette faiblesse : un Rvol ×1.3 un dimanche ne vaut qu'environ ×0.6 d'une heure de
semaine. `session_rvol` mesure le volume contre la **même heure UTC en semaine**.
"""
from __future__ import annotations

import pandas as pd

SESSIONS = ("Semaine", "Sam", "Dim", "Reprise dim. soir / lun. matin")


def session_of(ts: pd.Timestamp) -> str:
    """Séance d'un horodatage en **UTC réel** (pas l'index décalé +2h)."""
    d, h = ts.dayofweek, ts.hour
    if d == 5:
        return "Sam"
    if d == 6:
        return "Dim" if h < 20 else "Reprise dim. soir / lun. matin"
    if d == 0 and h < 6:
        return "Reprise dim. soir / lun. matin"
    return "Semaine"


def is_thin(ts: pd.Timestamp) -> bool:
    """True si la barre tombe dans la séance creuse (samedi → dimanche 20h UTC)."""
    return session_of(ts) in ("Sam", "Dim")


def session_rvol(df: pd.DataFrame, lookback_days: int = 28) -> pd.Series:
    """Volume de chaque barre ÷ médiane du volume à la **même heure UTC** sur les barres de
    semaine des `lookback_days` jours précédents (index en UTC réel, TF intrajournalière).
    Barre de semaine ≈ 1 en moyenne ; barre de dimanche typique ≈ 0,5."""
    vol = df["volume"]
    wk = pd.Series([session_of(t) == "Semaine" for t in df.index], index=df.index)
    out = pd.Series(float("nan"), index=df.index)
    key = df.index.hour * 60 + df.index.minute
    for k in pd.unique(key):
        m = key == k
        v = vol[m].where(wk[m])
        base = v.rolling(f"{lookback_days}D", min_periods=3).median().shift(1)
        out[m] = (vol[m] / base.ffill()).values
    return out
