"""
decouple.py — Classement des paires les plus *découplées* de la « beta crypto »
(panier BTC+ETH) qui ont néanmoins démontré une *dynamique autonome*.

Deux propriétés distinctes, mesurées séparément (cf. demande Gauthier) :

  A. Décorrélation — l'actif bouge indépendamment du marché. On régresse ses
     log-rendements sur ceux du panier équipondéré BTC/ETH (« beta crypto ») :
         r_alt = alpha + beta * r_bench + eps
     corr / r2 faibles = découplé. On suit aussi la corrélation *glissante*
     (corr_p90) car en régime de krach « tout corrèle » : un bon candidat reste
     découplé sur la plupart des sous-périodes, pas une seule.

  B. Dynamique autonome — quand il bouge seul, produit-il une vraie tendance et
     pas du bruit ? On regarde le *résidu* eps (mouvement propre, beta retirée) :
     rendement idiosyncratique cumulé (idio_ret) et information ratio (idio_ir).
     Quand la paire {BASE}/BTC existe, on ajoute rs_btc_% = sa performance cumulée
     (force relative *réelle* vs BTC, série tradable plus robuste que le résidu).

Garde-fous : on exclut les constituants du panier (BTC, ETH) et les stablecoins
(corr ~ 0 mais aucune dynamique), et on écarte les séries trop figées (illiquides),
dont la décorrélation est un artefact. La liquidité est déjà assurée en amont par
build_universe (top paires par volume).

Score composite, transparent et pondérable :
    score = (1 - |corr|) * idio_ir
high quand l'actif est à la fois *découplé* (1-|corr| élevé) et porté par une
*dérive autonome régulière* (idio_ir élevé).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

# Stablecoins / actifs peggés : corrélation faible mais aucune dynamique propre.
STABLES = {
    "USDT", "USDC", "TUSD", "DAI", "FDUSD", "USDE", "USDD", "PYUSD",
    "BUSD", "GUSD", "USDP", "EURT", "EURS", "USTC", "USD1",
}

# Variantes d'actions tokenisées / pré-marché qui échappent au motif principal.
STOCK_TOKEN_EXTRA = {"NVDAON"}


def is_tokenized_stock(base: str) -> bool:
    """Actions tokenisées listées sur Bitget — elles suivent la bourse, pas le
    crypto, et squattent donc le classement « décorrélé de BTC » par construction.

    Motif Bitget : préfixe `r` + ticker en majuscules (rAAPL, rNVDA, rSOXX…), ou
    préfixe `pre` + majuscules pour le pré-marché (preOPAI…). Les jetons crypto
    sont en majuscules (RSR, RNDR…) ou en casse mixte sans `r`/`pre` initial
    (rsETH, weETH…), donc non capturés.
    """
    if len(base) >= 2 and base[0] == "r" and base[1].isalpha() and base[1:].isupper():
        return True
    if len(base) > 3 and base[:3] == "pre" and base[3:].isupper():
        return True
    return base in STOCK_TOKEN_EXTRA


def log_returns(df: pd.DataFrame) -> pd.Series:
    """Log-rendements de la clôture. Indexés par timestamp."""
    return np.log(df["close"].astype(float)).diff().dropna()


def crypto_beta(returns: dict[str, pd.Series], quote: str = "USDT") -> pd.Series:
    """Panier équipondéré BTC+ETH (« beta crypto ») aligné sur l'index commun.
    Retombe sur BTC seul si ETH absent."""
    legs = [returns[s] for s in (f"BTC/{quote}", f"ETH/{quote}") if s in returns]
    if not legs:
        raise ValueError("Référence beta crypto indisponible (ni BTC ni ETH).")
    frame = pd.concat(legs, axis=1).dropna()
    return frame.mean(axis=1)


def _metrics(r: pd.Series, bench: pd.Series, rolling: int,
             min_bars: int, max_idio_ret: float) -> dict | None:
    """Métriques de décorrélation + dynamique autonome sur l'index commun.

    Garde-fous : historique effectif minimal (`min_bars`, écarte les listings
    trop récents) et plafond de rendement idiosyncratique (`max_idio_ret` en %,
    écarte les pumps déjà consommés / cotations aberrantes type +11000%).
    """
    common = pd.concat([r.rename("r"), bench.rename("b")], axis=1).dropna()
    if len(common) < max(rolling, min_bars):
        return None
    r_, b_ = common["r"], common["b"]

    # Série trop figée (illiquide) : décorrélation artificielle → on écarte.
    if r_.std(ddof=1) == 0 or (r_ == 0).mean() > 0.5:
        return None

    var_b = b_.var(ddof=1)
    beta = float(np.cov(r_, b_, ddof=1)[0, 1] / var_b) if var_b > 0 else np.nan
    corr = float(np.corrcoef(r_, b_)[0, 1])
    r2 = corr ** 2

    # Rendement neutralisé du marché (r - beta*b) : on retire l'exposition à la
    # beta crypto mais on *garde* la dérive propre (alpha). C'est la dynamique
    # autonome — cumulée (idio_ret) et son information ratio (idio_ir).
    idio = r_ - beta * b_
    idio_ret = float(np.expm1(idio.sum()) * 100)               # % cumulé
    # Pump déjà consommé / cotation aberrante : on écarte (non reproductible).
    if not np.isfinite(idio_ret) or abs(idio_ret) > max_idio_ret:
        return None
    idio_ir = float(idio.mean() / idio.std(ddof=1)) if idio.std(ddof=1) else 0.0

    roll = r_.rolling(rolling).corr(b_).dropna()
    corr_p90 = float(roll.abs().quantile(0.90)) if len(roll) else abs(corr)

    score = (1 - abs(corr)) * idio_ir
    return {
        "corr": round(corr, 3),
        "beta": round(beta, 2),
        "r2": round(r2, 3),
        "corr_p90": round(corr_p90, 3),
        "idio_ret_%": round(idio_ret, 1),
        "idio_ir": round(idio_ir, 4),
        "n": int(len(common)),
        "score": round(score, 4),
    }


def rank_decoupled(frames: dict[str, pd.DataFrame], quote: str = "USDT",
                   rolling: int = 60, rs_frames: dict[str, pd.DataFrame] | None = None,
                   min_score: float = 0.0, min_bars: int = 180,
                   max_idio_ret: float = 1000.0) -> pd.DataFrame:
    """Cœur pur (hors-ligne) : à partir des OHLCV par symbole, renvoie le tableau
    classé par découplage × dynamique autonome.

    frames    : {symbol -> OHLCV} incluant BTC/{quote} et idéalement ETH/{quote}.
    rs_frames : {base -> OHLCV de BASE/BTC} optionnel (force relative directe).
    min_bars  : historique effectif minimal (écarte les listings trop récents).
    max_idio_ret : plafond de rendement idiosyncratique en % (écarte les pumps
                   déjà consommés / cotations aberrantes). Garde-fous + exclusions
                   (stablecoins, actions tokenisées) appliqués avant tout classement.
    """
    returns = {s: log_returns(df) for s, df in frames.items() if len(df) > 2}
    bench = crypto_beta(returns, quote=quote)
    bench_syms = {f"BTC/{quote}", f"ETH/{quote}"}
    rs_frames = rs_frames or {}

    rows: list[dict] = []
    for sym, r in returns.items():
        if sym in bench_syms:
            continue
        base = sym.split("/")[0]
        if base in STABLES or is_tokenized_stock(base):
            continue
        m = _metrics(r, bench, rolling=rolling, min_bars=min_bars,
                     max_idio_ret=max_idio_ret)
        if m is None:
            continue

        rs = rs_frames.get(base)
        if rs is not None and len(rs) > 2:
            rs_ret = float(np.expm1(log_returns(rs).sum()) * 100)
            m["rs_btc_%"] = round(rs_ret, 1)
        else:
            m["rs_btc_%"] = np.nan

        rows.append({"symbol": sym, **m})

    if not rows:
        return pd.DataFrame()
    out = pd.DataFrame(rows)
    out = out[out["score"] >= min_score]
    out = out.sort_values("score", ascending=False).reset_index(drop=True)
    cols = ["symbol", "score", "corr", "r2", "corr_p90", "beta",
            "idio_ret_%", "idio_ir", "rs_btc_%", "n"]
    return out[cols]


def most_decoupled(ranked: pd.DataFrame, corr_max: float = 0.30,
                   corr_p90_max: float = 0.45, top: int = 15) -> pd.DataFrame:
    """Famille « vraiment découplée » : faible corrélation *et* qui le reste en
    régime de stress (corr_p90 bas), avec dynamique propre positive. Triée par
    score (découplage × dynamique) pour surfacer les plus *tradables* — les
    quasi-stables sans dynamique tombent en bas."""
    if ranked.empty:
        return ranked
    sub = ranked[(ranked["corr"].abs() <= corr_max)
                 & (ranked["corr_p90"] <= corr_p90_max)
                 & (ranked["idio_ir"] > 0)]
    return sub.sort_values("score", ascending=False).head(top).reset_index(drop=True)


def strongest_dynamics(ranked: pd.DataFrame, top: int = 15) -> pd.DataFrame:
    """Famille « forte dynamique autonome » : meilleure dérive propre (information
    ratio idiosyncratique), indépendamment du degré de corrélation."""
    if ranked.empty:
        return ranked
    return ranked.sort_values("idio_ir", ascending=False).head(top).reset_index(drop=True)


def select_view(ranked: pd.DataFrame, view: str = "score", top: int = 25) -> pd.DataFrame:
    """Aiguille vers une des deux familles tradables, ou le classement global.
    view : "score" (défaut, découplage × dynamique) | "decoupled" | "dynamics"."""
    if view == "decoupled":
        return most_decoupled(ranked, top=top)
    if view == "dynamics":
        return strongest_dynamics(ranked, top=top)
    return ranked.head(top).reset_index(drop=True)


def run_decouple(cfg: dict) -> pd.DataFrame:
    """Orchestration en ligne : récupère les OHLCV via ccxt puis classe l'univers.
    Les paires {BASE}/BTC sont récupérées quand elles existent (force relative)."""
    import sys

    from . import data as data_mod

    ex = data_mod.get_exchange(cfg["exchange"])
    quote = cfg["quote"]
    limit = cfg.get("limit", 1000)
    tf = cfg["timeframe"]

    universe = list(cfg["symbols"]) if cfg.get("symbols") else \
        data_mod.build_universe(ex, quote=quote, top_n=cfg["top"])
    # On s'assure que la référence beta crypto est présente.
    for ref in (f"BTC/{quote}", f"ETH/{quote}"):
        if ref not in universe:
            universe.append(ref)
    print(f"Univers : {len(universe)} paires — découplage beta crypto (BTC+ETH) {tf}",
          file=sys.stderr)

    markets = getattr(ex, "markets", {}) or {}
    frames: dict[str, pd.DataFrame] = {}
    rs_frames: dict[str, pd.DataFrame] = {}
    for i, sym in enumerate(universe, 1):
        try:
            frames[sym] = data_mod.fetch_ohlcv(ex, sym, tf, limit, cfg["use_cache"])
            base = sym.split("/")[0]
            rs_sym = f"{base}/BTC"
            if rs_sym in markets:
                rs_frames[base] = data_mod.fetch_ohlcv(ex, rs_sym, tf, limit, cfg["use_cache"])
        except Exception as e:
            print(f"  [skip] {sym}: {e}", file=sys.stderr)
        if i % 10 == 0:
            print(f"  ...{i}/{len(universe)}", file=sys.stderr)

    out = rank_decoupled(frames, quote=quote, rolling=cfg.get("roll", 60),
                         rs_frames=rs_frames, min_bars=cfg.get("min_bars", 180),
                         max_idio_ret=cfg.get("max_idio_ret", 1000.0))
    return select_view(out, view=cfg.get("view", "score"),
                       top=cfg.get("max_results", 25))
