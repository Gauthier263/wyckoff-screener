"""Heure de Paris pour tout l'affichage (CET l'hiver = UTC+1, CEST l'été = UTC+2).

Les données restent en **UTC réel** ; on ne convertit qu'à l'affichage et à la lecture des
heures saisies dans les notes. Remplace l'ancien décalage fixe « +2h CEST » (faux de fin
octobre à fin mars, où Paris est à UTC+1).
"""
from __future__ import annotations

from datetime import datetime

import pandas as pd

TZ = "Europe/Paris"
_FORMATS = ("%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M", "%d/%m/%Y %H:%M", "%d/%m %H:%M",
            "%d/%m %Hh", "%Y-%m-%d %Hh")


def _utc(ts) -> pd.Timestamp:
    ts = pd.Timestamp(ts)
    return ts.tz_localize("UTC") if ts.tzinfo is None else ts.tz_convert("UTC")


def local(ts) -> pd.Timestamp:
    """Timestamp UTC → heure de Paris (aware)."""
    return _utc(ts).tz_convert(TZ)


def fmt(ts, f: str = "%d/%m %H:%M") -> str:
    """Heure de Paris formatée (ex. « 20/11 11:50 »)."""
    return local(ts).strftime(f)


def label(ts) -> str:
    """Nom du fuseau à cette date : « CET » ou « CEST »."""
    return local(ts).tzname()


def wall_sec(ts) -> int:
    """Secondes epoch de l'heure de Paris « étiquetée UTC » : Lightweight Charts affiche en
    UTC, on lui donne donc l'heure murale de Paris."""
    loc = local(ts)
    return int(loc.timestamp()) + int(loc.utcoffset().total_seconds())


def wall_index(idx: pd.DatetimeIndex) -> pd.DatetimeIndex:
    """Index UTC → heure murale de Paris étiquetée UTC (pour matplotlib / scripts)."""
    return _utc_index(idx).tz_convert(TZ).tz_localize(None).tz_localize("UTC")


def _utc_index(idx: pd.DatetimeIndex) -> pd.DatetimeIndex:
    return idx.tz_localize("UTC") if idx.tz is None else idx.tz_convert("UTC")


def parse(s: str, year: int) -> pd.Timestamp:
    """Heure de Paris saisie (« JJ/MM HH:MM », …) → Timestamp UTC réel."""
    s = s.strip()
    for f in _FORMATS:
        try:
            d = datetime.strptime(s, f)
        except ValueError:
            continue
        if "%Y" not in f:
            d = d.replace(year=year)
        return (pd.Timestamp(d).tz_localize(TZ, ambiguous=True, nonexistent="shift_forward")
                .tz_convert("UTC"))
    raise ValueError(f"heure non reconnue : {s!r} (attendu « JJ/MM HH:MM »)")
