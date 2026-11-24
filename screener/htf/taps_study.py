"""taps_study.py — le Three Taps de CrypNuevo, mesuré comme un trade.

Sa règle, dans ses mots (relevé `research/crypnuevo_tweets.md`, 07/06 à 04/11/2026) :

1. Trois touches d'un extrême de range — « low forms, low swept (deviation), low retest » —,
   la deuxième ou la troisième pouvant être une **déviation** qui chasse les stops.
2. Après la troisième, retour **au moins au mid-range**.
3. **Timing** : la troisième touche doit venir assez tard après la deuxième ; trop proche,
   elle n'attire pas assez de liquidité et la cassure devient plus probable.
4. Revisiter trop vite un plus bas local mène plutôt à la cassure qu'au double creux.

Traduction en trade, sans regard vers le futur : à chaque touche *k* du plancher, on achète à
la clôture de la bougie qui touche ; stop sous le plus bas atteint depuis la première touche
(moins un quart d'ATR) ; cible au milieu entre le niveau et le plus haut atteint depuis la
première touche. Issue : la cible est-elle atteinte avant le stop ?

Si la règle est juste, la touche 3 doit battre les touches 1 et 2, une déviation dans la
séquence doit aider, et une troisième touche trop rapide doit faire pire. Le plafond est
traité par **miroir** (prix inversés), ce qui garantit une logique strictement symétrique.

Paramètres fixés **a priori**, jamais optimisés sur les données mesurées.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..features import atr, swing_points


def mirror(df: pd.DataFrame) -> pd.DataFrame:
    """Prix inversés : un plafond devient un plancher (pur). Les volumes sont conservés."""
    out = df.copy()
    out["open"], out["close"] = -df["open"], -df["close"]
    out["high"], out["low"] = -df["low"], -df["high"]
    return out


def tap_trades(df: pd.DataFrame, pivot: int = 5, touch_atr: float = 0.5,
               bounce_atr: float = 2.0, min_height_atr: float = 4.0,
               break_atr: float = 1.0, dev_atr: float = 0.25, stop_atr: float = 0.25,
               max_span: int = 200, horizon: int = 200, max_taps: int = 4,
               lookback: int = 60, stop_mode: str = "meche") -> pd.DataFrame:
    """Trades « achat à la touche k » sur toutes les séquences de touches d'un plancher (pur).

    - **Touche 1** : un plus bas pivot (`pivot` bougies de chaque côté). Comme un pivot n'est
      confirmé que `pivot` bougies plus tard, le trade n°1 entre à ce moment-là, pas avant.
    - **Touches suivantes** : un retour à moins de `touch_atr` ATR du niveau, après une
      remontée d'au moins `bounce_atr` ATR (sinon c'est la même touche qui se prolonge).
    - **Déviation** : une touche qui passe sous le niveau de plus de `dev_atr` ATR.
    - **Fin de séquence** : deux clôtures consécutives à plus de `break_atr` ATR sous le plus
      bas des touches (cassure installée), ou `max_span` bougies écoulées.
    - Le **range** court du plus haut des `lookback` bougies précédant la touche 1 jusqu'à
      l'entrée : il existe avant la première touche (c'est la structure qui a amené le prix
      au plancher), sans quoi la touche 1 n'aurait aucun mid-range. Une touche n'est tradée
      que si ce range fait au moins `min_height_atr` ATR.

    Deux protocoles d'entrée par touche (colonne `protocole`) :

    - `contact` : entrée au premier contact avec la zone, stop sous le plus bas des touches
      précédentes. C'est le trader naïf — celui dont la déviation chasse les stops.
    - `reprise` : sa méthode. La touche passe sous le niveau (déviation), puis une bougie
      clôture de nouveau au-dessus : entrée à cette clôture, stop sous le plus bas de la
      déviation. Sans reprise, la ligne porte `issue = "pas de reprise"` et aucun trade : on
      la garde pour savoir combien de déviations ne sont jamais reprises.

    Colonnes : `k`, `protocole`, `at`, `entry`, `stop`, `target`, `r` (gain potentiel en R),
    `issue` (`cible`, `stop`, `indéterminé` si les deux dans la même bougie, `ouvert`,
    `pas de reprise`), `bars` (délai jusqu'à l'issue), `deviation_avant` (une touche
    antérieure était déjà une déviation), `gap_prev`, `gap_prev2`, `early` (pour k ≥ 3 :
    écart (k-1→k) < moitié de (k-2→k-1)).
    """
    if df is None or len(df) < 3 * pivot + 20:
        return pd.DataFrame()
    a = atr(df).to_numpy()
    lo, hi, cl = df["low"].to_numpy(), df["high"].to_numpy(), df["close"].to_numpy()
    sw = swing_points(df, pivot, pivot)["swing_low"].to_numpy()
    n = len(df)
    rows = []
    busy_until = -1           # une séquence en cours interdit d'en ouvrir une autre dedans

    for i0 in np.flatnonzero(sw):
        if i0 <= busy_until or not np.isfinite(a[i0]) or a[i0] <= 0:
            continue
        level = lo[i0]
        taps = [i0]
        dev = False
        end = min(n - 1, i0 + max_span)
        j = i0 + 1
        left_zone = False
        broke_run = 0
        while j <= end:
            aj = a[j] if np.isfinite(a[j]) else a[i0]
            floor = min(lo[t] for t in taps)
            # cassure installée : deux clôtures sous le plus bas des touches - break_atr
            if cl[j] < floor - break_atr * aj:
                broke_run += 1
                if broke_run >= 2:
                    break
            else:
                broke_run = 0
            if hi[j] >= level + bounce_atr * aj:
                left_zone = True
            if left_zone and lo[j] <= level + touch_atr * aj:
                taps.append(j)
                left_zone = False
                if lo[j] < level - dev_atr * aj:
                    dev = True
                if len(taps) >= max_taps:
                    break
            j += 1
        busy_until = j

        def outcome(entry_i, entry, stop, target):
            """Issue et résultat en R. `stop_mode="meche"` : stop touché par une mèche,
            perte de 1 R. `stop_mode="acceptance"` : sa méthode, sortie seulement après
            deux clôtures consécutives sous le stop, au prix de la seconde — la perte
            peut alors dépasser 1 R, mais une mèche de chasse aux stops ne fait pas sortir."""
            fut_hi = hi[entry_i + 1:entry_i + 1 + horizon]
            fut_lo = lo[entry_i + 1:entry_i + 1 + horizon]
            fut_cl = cl[entry_i + 1:entry_i + 1 + horizon]
            risk = entry - stop
            hit_t = np.flatnonzero(fut_hi >= target)
            ft = hit_t[0] if len(hit_t) else None
            if stop_mode == "acceptance":
                below = fut_cl < stop
                fs = next((x for x in range(1, len(below)) if below[x] and below[x - 1]), None)
                exit_px = fut_cl[fs] if fs is not None else None
            else:
                hit_s = np.flatnonzero(fut_lo <= stop)
                fs = hit_s[0] if len(hit_s) else None
                exit_px = stop
            if ft is None and fs is None:
                return "ouvert", None, (fut_cl[-1] - entry) / risk if len(fut_cl) else 0.0
            if fs is None or (ft is not None and ft < fs):
                return "cible", int(ft) + 1, (target - entry) / risk
            if ft is None or fs < ft:
                return "stop", int(fs) + 1, (exit_px - entry) / risk
            return "indéterminé", None, None

        for k, t in enumerate(taps, start=1):
            gaps = [taps[x] - taps[x - 1] for x in range(1, k)]
            base = {"k": k, "deviation_avant": any(
                        lo[taps[x]] < level - dev_atr * a[taps[x]]
                        for x in range(k - 1) if np.isfinite(a[taps[x]])),
                    "gap_prev": gaps[-1] if gaps else None,
                    "gap_prev2": gaps[-2] if len(gaps) >= 2 else None,
                    "early": bool(len(gaps) >= 2 and gaps[-1] < 0.5 * gaps[-2])}
            # épisode de la touche : du premier contact jusqu'à la sortie de zone
            ep_end = t
            while ep_end + 1 < n and ep_end + 1 <= t + max_span:
                aj = a[ep_end + 1] if np.isfinite(a[ep_end + 1]) else a[t]
                if hi[ep_end + 1] >= level + bounce_atr * aj:
                    break
                ep_end += 1

            # --- protocole « contact » : entrée au premier contact (k=1 : à la confirmation
            # du pivot), stop sous le plus bas atteint depuis la touche 1.
            entry_i = t + pivot if k == 1 else t
            if entry_i < n - 1 and np.isfinite(a[entry_i]) and a[entry_i] > 0:
                at_ = a[entry_i]
                seg_hi = hi[max(0, i0 - lookback):entry_i + 1].max()
                if seg_hi - level >= min_height_atr * at_:
                    entry = cl[entry_i]
                    stop = lo[i0:entry_i + 1].min() - stop_atr * at_
                    target = level + 0.5 * (seg_hi - level)
                    if stop < entry < target:
                        issue, bars, res = outcome(entry_i, entry, stop, target)
                        rows.append({**base, "protocole": "contact", "at": df.index[entry_i],
                                     "entry": float(entry), "stop": float(stop),
                                     "target": float(target),
                                     "r": float((target - entry) / (entry - stop)),
                                     "issue": issue, "bars": bars, "result_r": res,
                                     "deviation": False})

            # --- protocole « reprise » (sa méthode) : la touche passe sous le niveau de plus
            # de dev_atr ATR (chasse aux stops), puis une bougie clôture de nouveau au-dessus
            # du niveau : on entre à cette clôture, stop sous le plus bas de la déviation.
            if k == 1:
                continue
            dev_i = None
            for x in range(t, ep_end + 1):
                ax = a[x] if np.isfinite(a[x]) else a[t]
                if lo[x] < level - dev_atr * ax:
                    dev_i = x
                    break
            if dev_i is None:
                continue
            rec = None
            for x in range(dev_i, min(n - 1, ep_end + 1)):
                if cl[x] > level:
                    rec = x
                    break
            if rec is None:
                rows.append({**base, "protocole": "reprise", "at": df.index[dev_i],
                             "entry": None, "stop": None, "target": None, "r": None,
                             "issue": "pas de reprise", "bars": None, "result_r": None,
                             "deviation": True})
                continue
            at_ = a[rec] if np.isfinite(a[rec]) else a[t]
            seg_hi = hi[max(0, i0 - lookback):rec + 1].max()
            if seg_hi - level < min_height_atr * at_:
                continue
            entry = cl[rec]
            stop = lo[t:rec + 1].min() - stop_atr * at_
            target = level + 0.5 * (seg_hi - level)
            if not (stop < entry < target):
                continue
            issue, bars, res = outcome(rec, entry, stop, target)
            rows.append({**base, "protocole": "reprise", "at": df.index[rec],
                         "entry": float(entry), "stop": float(stop), "target": float(target),
                         "r": float((target - entry) / (entry - stop)),
                         "issue": issue, "bars": bars, "result_r": res, "deviation": True})
    return pd.DataFrame(rows)


def both_sides(df: pd.DataFrame, **kw) -> pd.DataFrame:
    """Planchers (côté `plancher`, achats) et plafonds par miroir (côté `plafond`, ventes)."""
    a = tap_trades(df, **kw)
    b = tap_trades(mirror(df), **kw)
    if not a.empty:
        a["côté"] = "plancher"
    if not b.empty:
        b["côté"] = "plafond"
        for c in ("entry", "stop", "target"):
            b[c] = -b[c]
    return pd.concat([a, b], ignore_index=True) if len(a) or len(b) else pd.DataFrame()


def expectancy(g: pd.DataFrame) -> float:
    """Espérance en R des trades tranchés (pur).

    Utilise `result_r` quand il existe (perte réelle, qui peut dépasser 1 R avec un stop
    en clôture) ; sinon +R si la cible est atteinte, −1 sinon.
    """
    t = g[g["issue"].isin(("cible", "stop"))]
    if t.empty:
        return float("nan")
    if "result_r" in t and t["result_r"].notna().all():
        return float(t["result_r"].mean())
    return float(np.where(t["issue"] == "cible", t["r"], -1.0).mean())
