"""
ob_screen.py — Shortlist de paires à forte « présence institutionnelle » (sens ICT).

Pour chaque paire, on détecte tous les Order Blocks (orderblocks.py), on mesure le taux
de respect de leurs retests, et on classe l'univers. Une paire dont les OB sont
*retestés et respectés* trahit des acteurs qui défendent leurs niveaux ; une paire qui
traverse ses OB sans réagir est écartée.

Le score de tri reprend l'esprit robuste de optimize.metric_value : taux de respect
**pénalisé par l'erreur-type** (un fort taux sur 5 tests vaut moins qu'un taux moyen sur
50), avec un plancher d'échantillon `min_tests`.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass

import numpy as np
import pandas as pd

from .features import add_features
from .orderblocks import OBThresholds, analyze_order_blocks

_FR = {"bullish": "haussier", "bearish": "baissier"}


@dataclass
class OBStats:
    symbol: str
    n_ob: int               # OB détectés
    n_test: int             # OB effectivement retestés
    respect_rate: float     # respecté / testé, en %
    avg_R: float            # MFE moyen des OB testés (amplitude du rebond)
    med_R: float
    swing_rate: float       # % de testés ayant atteint l'extrême de l'impulsion
    fresh: str              # dernier OB non encore mité (signal live)
    score: float            # respect_rate pénalisé par l'erreur-type (borne basse)
    kind: str = "crypto"    # "crypto" | "xstock" (action tokenisée Bitget)

    def as_row(self) -> dict:
        return {
            "symbol": self.symbol,
            "n_ob": self.n_ob,
            "n_test": self.n_test,
            "respect%": round(self.respect_rate, 1),
            "avg_R": round(self.avg_R, 2),
            "med_R": round(self.med_R, 2),
            "swing%": round(self.swing_rate, 1),
            "fresh_OB": self.fresh,
            "score": round(self.score, 3),
        }


def _robust_score(p: float, n: int, min_tests: int, z: float = 1.0) -> float:
    """Borne basse du taux de respect ~ p − z·erreur-type. 0 sous le plancher."""
    if n < min_tests:
        return 0.0
    se = np.sqrt(p * (1 - p) / n) if n > 0 else 0.0
    return float(max(0.0, p - z * se))


def _fmt(x: float) -> str:
    return f"{x:.6g}"


def _respect_rate(obs) -> tuple[float, int]:
    """Taux de respect (%) et nombre d'OB testés, à partir d'une liste d'OrderBlock."""
    tested = [o for o in obs if o.tested]
    if not tested:
        return float("nan"), 0
    p = sum(1 for o in tested if o.outcome == "respecté") / len(tested)
    return 100 * p, len(tested)


def fresh_order_blocks(symbol: str, feat: pd.DataFrame, th: OBThresholds,
                       kind: str = "crypto") -> list[dict]:
    """Renvoie une ligne par OB **non encore mité** (niveau vierge à surveiller en live).

    `dist%` = distance du dernier prix à la zone, du bon côté (prix au-dessus d'un OB
    haussier-support, sous un OB baissier-résistance) : plus elle est faible, plus le
    retest est imminent. `respect%` rappelle la fiabilité historique des OB du symbole.
    """
    obs = analyze_order_blocks(feat, th)
    n = len(feat)
    price = float(feat["close"].iloc[-1])
    respect, n_test = _respect_rate(obs)
    rows = []
    for o in obs:
        if o.outcome != "non_testé":
            continue
        bars_ago = n - 1 - o.idx
        if bars_ago > th.max_wait:               # trop ancien = niveau périmé
            continue
        dist = (price - o.top) if o.bias == "bullish" else (o.bottom - price)
        rows.append({
            "symbol": symbol,
            "bias": _FR[o.bias],
            "zone": f"{_fmt(o.bottom)}–{_fmt(o.top)}",
            "price": _fmt(price),
            "bars_ago": bars_ago,
            "displ_ATR": round(o.displacement, 2),
            "dist%": round(100 * dist / price, 2),
            "respect%": round(respect, 1) if respect == respect else None,
            "n_test": n_test,
            "_kind": kind,
        })
    return rows


def screen_symbol(symbol: str, feat: pd.DataFrame, th: OBThresholds,
                  min_tests: int = 5) -> OBStats | None:
    obs = analyze_order_blocks(feat, th)
    if not obs:
        return None

    tested = [o for o in obs if o.tested]
    n_test = len(tested)
    respected = [o for o in tested if o.outcome == "respecté"]
    p = len(respected) / n_test if n_test else 0.0
    rs = np.array([o.mfe_R for o in tested], dtype=float)

    # Dernier OB non encore mité (le plus récent) = niveau à surveiller en live
    n = len(feat)
    pending = [o for o in obs if o.outcome == "non_testé"]
    if pending:
        last = max(pending, key=lambda o: o.idx)
        fresh = f"{_FR[last.bias]}, il y a {n - 1 - last.idx} barres"
    else:
        fresh = "—"

    return OBStats(
        symbol=symbol,
        n_ob=len(obs),
        n_test=n_test,
        respect_rate=100 * p,
        avg_R=float(rs.mean()) if n_test else 0.0,
        med_R=float(np.median(rs)) if n_test else 0.0,
        swing_rate=100 * np.mean([o.hit_swing for o in tested]) if n_test else 0.0,
        fresh=fresh,
        score=100 * _robust_score(p, n_test, min_tests),
    )


def run_ob_screen(cfg: dict) -> dict[str, pd.DataFrame]:
    """Charge l'univers, classe les paires par respect des Order Blocks ICT.

    Renvoie deux tableaux séparés : 'crypto' et 'xstocks' (actions tokenisées Bitget),
    car ces dernières — fortement teneur-de-marché — dominent artificiellement le respect
    des OB et écraseraient les vraies cryptos dans un classement unique.
    """
    from . import data as data_mod

    mt = cfg.get("market")
    ex = data_mod.get_exchange(cfg["exchange"], mt)
    if cfg["symbols"]:
        universe = cfg["symbols"]
    else:
        universe = (data_mod.build_universe(ex, quote=cfg["quote"], top_n=cfg["top"],
                                            kind="crypto", market_type=mt)
                    + data_mod.build_universe(ex, quote=cfg["quote"], top_n=cfg["top"],
                                              kind="xstock", market_type=mt))
        print(f"Univers : {len(universe)} paires {cfg['quote']} {mt or 'spot'} sur "
              f"{cfg['exchange']} (crypto + hors-crypto) — Order Blocks ICT {cfg['timeframe']}",
              file=sys.stderr)
    th = OBThresholds(**cfg.get("ob", {}))
    min_tests = cfg.get("ob_min_tests", 5)

    results: list[OBStats] = []
    for i, sym in enumerate(universe, 1):
        try:
            df = data_mod.fetch_ohlcv(ex, sym, cfg["timeframe"], cfg["limit"], cfg["use_cache"])
            feat = add_features(df, vol_ma=cfg["vol_ma"], atr_period=cfg["atr_period"])
            s = screen_symbol(sym, feat, th, min_tests)
            if s and s.n_test > 0:
                s.kind = "xstock" if data_mod.is_tokenized_stock(ex, sym) else "crypto"
                results.append(s)
        except Exception as e:
            print(f"  [skip] {sym}: {e}", file=sys.stderr)
        if i % 10 == 0:
            print(f"  ...{i}/{len(universe)}", file=sys.stderr)

    results.sort(key=lambda s: s.score, reverse=True)
    out = {}
    for kind in ("crypto", "xstock"):
        grp = [s for s in results if s.kind == kind][: cfg["max_results"]]
        out["xstocks" if kind == "xstock" else kind] = pd.DataFrame([s.as_row() for s in grp])
    return out


def run_ob_fresh(cfg: dict) -> dict[str, pd.DataFrame]:
    """Watchlist des OB frais (non mités) à surveiller pour un retest, triés par fraîcheur.
    Deux tableaux séparés crypto / hors-crypto, comme `run_ob_screen`."""
    from . import data as data_mod

    mt = cfg.get("market")
    ex = data_mod.get_exchange(cfg["exchange"], mt)
    if cfg["symbols"]:
        universe = cfg["symbols"]
    else:
        universe = (data_mod.build_universe(ex, quote=cfg["quote"], top_n=cfg["top"],
                                            kind="crypto", market_type=mt)
                    + data_mod.build_universe(ex, quote=cfg["quote"], top_n=cfg["top"],
                                              kind="xstock", market_type=mt))
        print(f"Univers : {len(universe)} paires {cfg['quote']} {mt or 'spot'} sur "
              f"{cfg['exchange']} — OB frais à retester {cfg['timeframe']}", file=sys.stderr)
    th = OBThresholds(**cfg.get("ob", {}))

    rows: list[dict] = []
    for i, sym in enumerate(universe, 1):
        try:
            df = data_mod.fetch_ohlcv(ex, sym, cfg["timeframe"], cfg["limit"], cfg["use_cache"])
            feat = add_features(df, vol_ma=cfg["vol_ma"], atr_period=cfg["atr_period"])
            kind = "xstock" if data_mod.is_tokenized_stock(ex, sym) else "crypto"
            rows += fresh_order_blocks(sym, feat, th, kind)
        except Exception as e:
            print(f"  [skip] {sym}: {e}", file=sys.stderr)
        if i % 10 == 0:
            print(f"  ...{i}/{len(universe)}", file=sys.stderr)

    out = {}
    for kind in ("crypto", "xstock"):
        grp = [r for r in rows if r["_kind"] == kind]
        df = pd.DataFrame([{k: v for k, v in r.items() if k != "_kind"} for r in grp])
        if not df.empty:
            df = df.sort_values(["bars_ago", "dist%"]).head(cfg["max_results"]).reset_index(drop=True)
        out["xstocks" if kind == "xstock" else kind] = df
    return out
