"""liqmap.py — carte des positions ouvertes et des liquidations estimées, par niveau de prix.

Reconstruit, à partir de nos seules données gratuites, les deux vues que CrypNuevo lit chez
Hyblock : **Open Positions** (où sont les positions → murs et « thin air ») et la **heatmap de
liquidations** (où est le carburant → aimants). Heuristiques transparentes et ajustables,
jamais une boîte noire : chaque hypothèse est un paramètre nommé.

Deux notions à ne pas confondre
-------------------------------
- **Positions ouvertes** : l'OI (en **coin**, jamais en USD — l'USD confond positions et prix)
  rangé par *prix d'ouverture*. Un contrat perp a toujours un long **et** un short : ce profil
  n'a donc **pas de côté**. C'est bien ce qu'affiche « Open Positions » chez Hyblock, en une
  seule couleur. Ses pics sont des **murs** (beaucoup de monde engagé, prix qui s'y défend),
  ses creux de la **« thin air »** (rien pour freiner).
- **Liquidations** : elles, ont un côté. On ne trace que le côté **initiateur** (celui qui a
  frappé au marché, identifié par le delta agressif perp) : en face se tient le plus souvent
  un teneur de marché couvert, qui ne se fait pas liquider.

Construction, barre par barre
-----------------------------
- **ΔOI > 0** : positions ouvertes sur la barre, déposées uniformément sur les niveaux
  traversés [low, high]. Leur côté initiateur vient de `side_split(delta, volume)`.
  Chaque dépôt sème ses niveaux de liquidation : `p·(1 − 1/L)` pour un long initiateur,
  `p·(1 + 1/L)` pour un short, réparti sur des **paliers de levier** pondérés.
- **ΔOI < 0** : positions fermées. On les **retire** du profil — c'est ce qui manquait au
  prototype du 22/11, qui ne faisait qu'empiler et divergeait donc du vrai. Le retrait est
  pondéré par la proximité du prix (on solde plus volontiers près de son entrée) et par
  l'ancienneté, et il efface les niveaux de liquidation dans la même proportion.
- **Niveau de liquidation franchi** par la barre : le carburant y a brûlé, le niveau est
  effacé (« liquidation cluster hit »). La position correspondante, elle, est déjà retirée
  par le ΔOI négatif de cette même barre : pas de double comptage.

Limites, à dire dans toute analyse qui s'en sert
------------------------------------------------
- La répartition des leviers est une **hypothèse**, pas une mesure : aucune bourse ne publie
  le levier par position.
- Le côté initiateur est **estimé** ; une barre à flux ambigu se répartit moitié-moitié.
- La carte dit où sont les *positions*, pas où sont les *ordres* : elle ne remplace pas un
  carnet.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

# Paliers de levier et leur poids (somme = 1). Les petits leviers dominent en nombre mais
# leurs niveaux de liquidation sont loin ; les gros leviers font les amas proches du prix.
DEFAULT_LEVERAGE_TIERS = {5: 0.18, 10: 0.24, 20: 0.26, 25: 0.12, 50: 0.14, 100: 0.06}


def price_grid(low: float, high: float, step_pct: float = 0.001) -> np.ndarray:
    """Grille de prix à pas géométrique (`step_pct` = 0.1 % par défaut)."""
    if not (high > low > 0):
        return np.array([])
    n = max(1, int(np.ceil(np.log(high / low) / np.log1p(step_pct))))
    return low * (1.0 + step_pct) ** np.arange(n + 1)


def _bucket(grid: np.ndarray, price: float) -> int:
    return int(np.clip(np.searchsorted(grid, price) - 1, 0, len(grid) - 1))


def side_split(delta: float, volume: float, sensitivity: float = 2.0,
               mode: str = "contrarian") -> float:
    """Part des nouvelles positions **liquidables** qui sont longues, dans [0, 1] (pur).

    Le delta agressif de la barre (taker achat − taker vente) dit **qui frappe au marché**,
    pas qui ouvre la position à levier qui sera liquidée plus tard. Pendant une chute, les
    ventes agressives sont surtout des longs qui sortent ou qui sont liquidés ; la position
    neuve à fort levier est prise en face, par celui qui achète le creux. C'est la même
    nuance que la grille delta perp × OI de la doctrine : un delta ne nomme pas un ouvreur.

    - `mode="contrarian"` (défaut) : la position neuve liquidable est **opposée** à
      l'agresseur. Mesuré sur 23 cartes Hyblock de 2026, ce choix donne le bon côté
      74 % du temps, contre 26 % pour l'autre — voir `research/liqmap_validation.md`.
    - `mode="aggressor"` : l'agresseur est l'ouvreur. Conservé pour pouvoir rejouer la
      comparaison, jamais comme réglage par défaut.

    Un flux nul, un volume nul ou une valeur illisible donnent 0.5, c'est-à-dire « on ne
    tranche pas » — jamais une direction inventée.
    """
    if not volume or volume <= 0 or delta is None or not np.isfinite(delta):
        return 0.5
    r = float(np.clip(sensitivity * delta / volume, -1.0, 1.0))
    if mode == "contrarian":
        r = -r
    return 0.5 + 0.5 * r


def build_map(df: pd.DataFrame, oi: pd.Series, delta: "pd.Series | None" = None,
              step_pct: float = 0.001, half_life_bars: float = 240.0,
              close_proximity_atr: float = 1.5, churn_frac: float = 0.01,
              drift_frac: float = 0.05, unlevered_frac: float = 0.45,
              seed_bars: int = 0, profit_pull: float = 3.0, profit_scale: float = 0.10,
              side_mode: str = "contrarian",
              leverage_tiers: "dict | None" = None) -> dict:
    """Carte des positions ouvertes et des liquidations estimées.

    `df` : OHLCV (index UTC, colonnes open/high/low/close/volume) ; `oi` : OI en **coin**
    réaligné sur `df` ; `delta` : delta agressif perp par barre (coin), facultatif.

    Le carnet suivi est une matrice **prix d'ouverture × palier de levier × côté**. Chaque
    case connaît donc son propre prix de liquidation, et disparaît quand le prix le franchit :
    c'est ce qui empêche un long entré à 75k de survivre à un prix tombé à 59k.

    `churn_frac` : part du volume de chaque barre qui **renouvelle** des positions (fermeture
    et ouverture simultanées, OI inchangé). Sans ce terme, un OI stable serait lu comme
    « rien n'a bougé ». Rappel de doctrine : **OI stable ≠ absence de rotation**.
    `drift_frac` : part des fermetures répartie uniformément sur tout le carnet, le reste
    étant concentré près du prix. Sans elle, une position loin du prix ne serait jamais
    soldée volontairement.
    `leverage_tiers` : soit `{levier: poids}`, soit `{"long": {...}, "short": {...}}` pour
    des profils distincts par côté — c'est ce que produit `calibrate.fit_leverage_tiers`.
    `seed_bars` : nombre de barres de **préchauffage** servant à amorcer le carnet avec
    l'OI déjà ouvert au début de la fenêtre, réparti au prorata du volume de ces barres.
    Sans amorçage, on ne reconstruit que le *flux* de la fenêtre et non le *stock* : la
    masse du profil tombe alors à quelques milliers de BTC pour un OI réel de 92 000, et
    les amas lus ne sont plus que du bruit.
    `side_mode` : voir `side_split` — qui, de l'agresseur ou de sa contrepartie, porte la
    position liquidable. Le défaut `contrarian` est celui que mesure le banc de validation.
    `profit_pull` / `profit_scale` : force et échelle de la prise de profit. Une position
    en gain de `profit_scale` (10 % par défaut) est `1 + profit_pull` fois plus susceptible
    d'être soldée qu'une position à l'équilibre. Sans ce terme, les shorts ouverts très haut
    survivent à toute la baisse et forment de faux murs loin au-dessus du marché.
    `unlevered_frac` : nombre, ou `{"long": x, "short": y}`. Part des positions **sans
    niveau de liquidation atteignable** —
    cross margin largement collatéralisé, couverture, teneur de marché. Les positions
    réelles lues sur Hyperliquid le confirment : les gros comptes en cross affichent des
    prix de liquidation très éloignés du marché. Sans ce palier, tout ce qui est loin du
    prix finit liquidé et le profil se tasse en un pic sur le prix courant, ce qui ne
    distingue plus un mur d'un vide.

    Renvoie un dict :
      - `grid`      : grille de prix ;
      - `positions` : OI restant par niveau d'ouverture (en coin, **sans côté** : un contrat
        perp a toujours un long et un short) ;
      - `liq_long`, `liq_short` : carburant de liquidation par niveau (en coin), côté
        initiateur ;
      - `price`, `asof` : dernier prix et dernier horodatage pris en compte ;
      - `burned_long`, `burned_short` : carburant consommé en route (diagnostic).
    """
    tiers = leverage_tiers or DEFAULT_LEVERAGE_TIERS
    df = df.dropna(subset=["high", "low", "close"])
    if df.empty:
        raise ValueError("OHLCV vide")
    oi = oi.reindex(df.index).astype(float)
    delta = delta.reindex(df.index).astype(float) if delta is not None else None

    grid = price_grid(float(df["low"].min()) * 0.90, float(df["high"].max()) * 1.10, step_pct)
    n = len(grid)
    if n == 0:
        raise ValueError("grille de prix vide")

    # `leverage_tiers` accepte un dict unique (mêmes paliers des deux côtés) ou
    # {"long": {...}, "short": {...}} : les longs et les shorts n'ont pas le même profil de
    # levier, et les confondre déplace les amas (vérifié sur le 22/11).
    if set(tiers) == {"long", "short"}:
        by_side = {s: dict(tiers[s]) for s in ("long", "short")}
    else:
        by_side = {"long": dict(tiers), "short": dict(tiers)}
    if isinstance(unlevered_frac, dict):
        unlev = {s: float(np.clip(unlevered_frac.get(s, 0.0), 0.0, 1.0))
                 for s in ("long", "short")}
    else:
        u = float(np.clip(unlevered_frac, 0.0, 1.0))
        unlev = {"long": u, "short": u}
    by_side = {s: {L_: w * (1.0 - unlev[s]) for L_, w in by_side[s].items()}
               for s in ("long", "short")}
    levs = sorted(set(by_side["long"]) | set(by_side["short"]))
    # carnet[side][k] : quantité ouverte au niveau d'entrée i, au levier levs[k]
    book = {"long": np.zeros((len(levs), n)), "short": np.zeros((len(levs), n))}
    # positions sans liquidation atteignable, suivies à part (elles ne brûlent jamais)
    safe = np.zeros(n)
    age = np.zeros(n)
    burned = {"long": 0.0, "short": 0.0}
    # série temporelle du carburant brûlé par barre et par côté : c'est elle qu'on confronte
    # aux liquidations réellement exécutées pour calibrer la distribution des leviers.
    burn_ts = {"long": np.zeros(len(df)), "short": np.zeros(len(df))}
    shifts = {"long": np.array([1.0 - 1.0 / L for L in levs]),
              "short": np.array([1.0 + 1.0 / L for L in levs])}
    mean_unlev = 0.5 * (unlev["long"] + unlev["short"])

    atr = (df["high"] - df["low"]).rolling(14, min_periods=1).mean()
    vol = df["volume"] if "volume" in df.columns else pd.Series(1.0, index=df.index)
    prev_oi = None

    start_i = 0
    seed = int(np.clip(seed_bars, 0, max(len(df) - 2, 0)))
    if seed > 0:
        head = df.iloc[:seed]
        oi0 = oi.iloc[:seed].dropna()
        if len(oi0):
            w0 = np.zeros(n)
            hv = head["volume"] if "volume" in head.columns else pd.Series(1.0, index=head.index)
            for j in range(seed):
                r = head.iloc[j]
                a, b = sorted((_bucket(grid, r["low"]), _bucket(grid, r["high"])))
                sp = np.arange(a, b + 1)
                w0[sp] += float(hv.iloc[j]) / len(sp)
            if w0.sum() > 0:
                add0 = float(oi0.iloc[-1]) * w0 / w0.sum()
                for s_ in ("long", "short"):
                    for k, L_ in enumerate(levs):
                        w_ = by_side[s_].get(L_, 0.0)
                        if w_:
                            book[s_][k] += add0 * 0.5 * w_
                    safe += add0 * 0.5 * unlev[s_]
        start_i = seed
        prev_oi = float(oi.iloc[:seed].dropna().iloc[-1]) if len(oi0) else None

    for i in range(start_i, len(df)):
        row = df.iloc[i]
        cur = oi.iloc[i]
        if not np.isfinite(cur):
            continue
        if prev_oi is None:
            prev_oi = cur
            continue
        d_oi, prev_oi = cur - prev_oi, cur

        # Zone balayée : le prix est continu, on part de la clôture précédente, sinon un
        # saut entre deux barres laisserait derrière lui des positions fantômes.
        prev_close = float(df["close"].iloc[i - 1])
        lo_b = min(float(row["low"]), prev_close)
        hi_b = max(float(row["high"]), prev_close)

        # 1. liquidations : toute entrée dont le prix de liquidation est balayé disparaît.
        for s in ("long", "short"):
            for k, sh in enumerate(shifts[s]):
                hit = (grid * sh >= lo_b) & (grid * sh <= hi_b)
                if hit.any():
                    q = float(book[s][k][hit].sum())
                    burned[s] += q
                    burn_ts[s][i] += q
                    book[s][k][hit] = 0.0

        positions = book["long"].sum(axis=0) + book["short"].sum(axis=0) + safe
        total = float(positions.sum())

        churn = min(float(churn_frac) * float(vol.iloc[i]), total)
        opened_qty = max(d_oi, 0.0) + churn
        closed_qty = max(-d_oi, 0.0) + churn

        # 2. fermetures volontaires : près du prix, en gain, et une dérive uniforme.
        if closed_qty > 0 and total > 0:
            prox = np.exp(-0.5 * ((grid - row["close"])
                                  / (max(float(atr.iloc[i]), 1e-9) * close_proximity_atr)) ** 2)
            aged = np.minimum(1.0 + age / max(half_life_bars, 1e-9), 2.0)
            # gain latent, par côté : un short ouvert à 86k avec le prix à 59k est très en
            # profit et finit par être soldé. Sans ce terme, il resterait indéfiniment dans
            # le carnet et formerait un faux mur loin au-dessus du marché.
            px = float(row["close"])
            pnl = {"long": (px - grid) / np.maximum(grid, 1e-9),
                   "short": (grid - px) / np.maximum(grid, 1e-9)}
            w_side, taken = {}, {}
            for s_ in ("long", "short"):
                pull = 1.0 + profit_pull * np.clip(pnl[s_] / max(profit_scale, 1e-9), 0.0, 3.0)
                base = book[s_].sum(axis=0)
                w_side[s_] = base * ((1.0 - drift_frac) * prox + drift_frac) * aged * pull
            w_safe = safe * ((1.0 - drift_frac) * prox + drift_frac) * aged
            wtot = sum(w_side.values()) + w_safe
            denom = float(wtot.sum())
            if denom <= 0:
                wtot = positions.copy()
                w_side = {s_: book[s_].sum(axis=0) for s_ in ("long", "short")}
                w_safe = safe.copy()
                denom = float(wtot.sum()) or 1.0
            for s_ in ("long", "short"):
                base = book[s_].sum(axis=0)
                take = np.minimum(base, closed_qty * w_side[s_] / denom)
                with np.errstate(invalid="ignore", divide="ignore"):
                    keep = np.where(base > 0, 1.0 - take / np.maximum(base, 1e-12), 1.0)
                book[s_] *= keep
            take_s = np.minimum(safe, closed_qty * w_safe / denom)
            with np.errstate(invalid="ignore", divide="ignore"):
                keep_s = np.where(safe > 0, 1.0 - take_s / np.maximum(safe, 1e-12), 1.0)
            safe = safe - take_s
            positions = book["long"].sum(axis=0) + book["short"].sum(axis=0) + safe
            age = age * np.where(positions > 0, 1.0, 0.0)

        # 3. ouvertures, déposées sur les niveaux traversés par la barre.
        if opened_qty > 0:
            b_lo, b_hi = sorted((_bucket(grid, row["low"]), _bucket(grid, row["high"])))
            span = np.arange(b_lo, b_hi + 1)
            w = np.zeros(n)
            w[span] = 1.0 / len(span)
            add = opened_qty * w
            tot = positions + add
            with np.errstate(invalid="ignore", divide="ignore"):
                age = np.where(tot > 0, age * positions / np.maximum(tot, 1e-12), 0.0)
            d_i = float(delta.iloc[i]) if delta is not None else float("nan")
            p_long = side_split(d_i, float(vol.iloc[i]), mode=side_mode)
            for s, part in (("long", p_long), ("short", 1.0 - p_long)):
                if part <= 0:
                    continue
                for k, L_ in enumerate(levs):
                    w_ = by_side[s].get(L_, 0.0)
                    if w_:
                        book[s][k] += add * part * w_
                safe += add * part * unlev[s]

        age = np.where((book["long"].sum(axis=0) + book["short"].sum(axis=0) + safe) > 0,
                       age + 1.0, 0.0)

    # projection du carnet restant sur les niveaux de liquidation
    liq = {"long": np.zeros(n), "short": np.zeros(n)}
    for s in ("long", "short"):
        for k, sh in enumerate(shifts[s]):
            qty = book[s][k]
            nz = np.nonzero(qty)[0]
            for b in nz:
                liq[s][_bucket(grid, grid[b] * sh)] += qty[b]

    return {"grid": grid,
            "positions": book["long"].sum(axis=0) + book["short"].sum(axis=0) + safe,
            "liq_long": liq["long"], "liq_short": liq["short"],
            "burned_long": burned["long"], "burned_short": burned["short"],
            "burn_long_ts": pd.Series(burn_ts["long"], index=df.index),
            "burn_short_ts": pd.Series(burn_ts["short"], index=df.index),
            "price": float(df["close"].iloc[-1]), "asof": df.index[-1]}


def clusters(grid: np.ndarray, values: np.ndarray, top_n: int = 6,
             merge_pct: float = 0.004) -> pd.DataFrame:
    """Regroupe les niveaux voisins en amas et renvoie les `top_n` plus denses (pur).

    `merge_pct` : deux niveaux distants de moins de 0.4 % appartiennent au même amas.
    """
    cols = ["low", "high", "peak", "value", "share"]
    if len(grid) == 0 or float(np.sum(values)) <= 0:
        return pd.DataFrame(columns=cols)
    total = float(np.sum(values))
    used = np.zeros(len(grid), dtype=bool)
    out = []
    for idx in np.argsort(values)[::-1]:
        if used[idx] or values[idx] <= 0:
            continue
        p = grid[idx]
        band = (grid >= p * (1 - merge_pct)) & (grid <= p * (1 + merge_pct)) & ~used
        if not band.any():
            continue
        used |= band
        v = float(values[band].sum())
        out.append({"low": float(grid[band].min()), "high": float(grid[band].max()),
                    "peak": float(p), "value": v, "share": v / total})
        if len(out) >= top_n:
            break
    return pd.DataFrame(out, columns=cols).sort_values("value", ascending=False).reset_index(drop=True)


def thin_air(grid: np.ndarray, values: np.ndarray, price: float, side: str = "up",
             quantile: float = 0.25, min_width_pct: float = 0.01) -> pd.DataFrame:
    """Zones de **faible** densité au-dessus (`up`) ou en dessous (`down`) du prix (pur).

    « Low OI = thin air » : rien n'y freine le prix, il les traverse vite.
    """
    cols = ["low", "high", "width_pct"]
    if len(grid) == 0:
        return pd.DataFrame(columns=cols)
    mask = grid > price if side == "up" else grid < price
    if not mask.any():
        return pd.DataFrame(columns=cols)
    g, v = grid[mask], values[mask]
    # quantile sur TOUS les niveaux du côté lu, zéros compris : un vide n'est un vide que
    # comparé à ce qui l'entoure, et exclure les zéros ferait disparaître les vrais trous.
    thr = float(np.quantile(v, quantile)) if len(v) else 0.0
    low = v <= thr
    runs, start = [], None
    for i, flag in enumerate(low):
        if flag and start is None:
            start = i
        elif not flag and start is not None:
            runs.append((g[start], g[i - 1]))
            start = None
    if start is not None:
        runs.append((g[start], g[-1]))
    rows = [{"low": float(a), "high": float(b), "width_pct": float(b / a - 1.0)}
            for a, b in runs if a > 0 and b / a - 1.0 >= min_width_pct]
    return (pd.DataFrame(rows, columns=cols)
            .sort_values("width_pct", ascending=False).reset_index(drop=True))


def squeeze_delta(liq_long: np.ndarray, liq_short: np.ndarray, grid: np.ndarray,
                  price: float, within_pct: float = 0.15) -> dict:
    """Déséquilibre du carburant autour du prix (pur).

    Analogue de son « delta liquidations » : liquidations de shorts au-dessus du prix
    (carburant haussier, car un short liquidé rachète) contre liquidations de longs en
    dessous (carburant baissier), dans une bande de `within_pct`. Nos montants sont en
    **coin**, pas en dollars : ses seuils (18, 25, 30 Md$) tiennent à son réglage « max
    liquidity » et ne se transposent pas — on lit le **ratio**, à recalibrer en centiles
    historiques.
    """
    up = (grid > price) & (grid <= price * (1 + within_pct))
    dn = (grid < price) & (grid >= price * (1 - within_pct))
    short_fuel = float(liq_short[up].sum())
    long_fuel = float(liq_long[dn].sum())
    tot = short_fuel + long_fuel
    return {"short_fuel_up": short_fuel, "long_fuel_down": long_fuel,
            "ratio": (short_fuel / long_fuel) if long_fuel > 0 else float("inf"),
            "skew": ((short_fuel - long_fuel) / tot) if tot > 0 else 0.0}
