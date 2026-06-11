"""
scan.py — Screener multi-cours par-dessus le moteur Wyckoff existant.

Objectif : balayer une centaine de cours (crypto + actions + matières premières) et
présélectionner ceux dont une formation d'**accumulation** ou de **distribution** est
*déjà validée par de premiers événements* — donc propice à une prise de position.

Définition retenue (cf. discussion avec Gauthier) :
  - Validité minimale d'un schéma = **Climax + AR + ST** présents sur la fenêtre récente
    du timeframe déclencheur (LTF). En-dessous, on ne retient pas.
  - Confluence MTF : le contexte HTF doit idéalement pointer le même biais (réutilise la
    logique de `mtf.py`, multiplicateur 1.5 / 1.25 / 1.0 / 0.5).
  - Phase / timing d'entrée :
        B→C  (Climax+AR+ST, pas encore de signe directionnel) → entrée au *spring/test*.
        D    (SOS/SOW déjà imprimé)                            → entrée au *LPS/LPSY*.
  - Pas de calcul d'entrée/stop/objectif/R:R pour l'instant (feature ultérieure).

Score de **fiabilité** (transparent, pondérations ajustables ci-dessous) :
    fiabilité = (w_climax·qualité_climax + w_test·qualité_test + w_complétude·complétude)
                × récence × confluence_MTF

Aucune modification du code existant : ce module s'ajoute par-dessus `window.py`,
`features.py`, `mtf.py` et la couche `sources.py`.

Usage :
    python -m screener.scan                        # tout l'univers, source Yahoo
    python -m screener.scan --classes crypto       # crypto seul
    python -m screener.scan --source ccxt           # crypto via exchange, reste Yahoo
    python -m screener.scan --bias accumulation
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass

import numpy as np
import pandas as pd

from . import sources
from .events import Thresholds
from .features import add_features
from .universe import TF_BY_CLASS, Asset, EXCLUDED, build_assets
from .window import WindowStructure, detect_window_structure

# Pondérations du score de fiabilité (ajustables — heuristiques transparentes).
W_CLIMAX = 0.4
W_TEST = 0.3
W_COMPLETE = 0.3
RECENCY_HALFLIFE = 6.0  # barres : demi-vie de la décote de récence
# Multiplicateurs de confluence MTF (mêmes valeurs que mtf.py).
CONFL_TRIGGER = 1.5   # HTF aligné + signe directionnel LTF
CONFL_ALIGNED = 1.25  # HTF aligné, sans signe directionnel
CONFL_NEUTRAL = 1.0   # HTF sans contexte net
CONFL_CONFLICT = 0.5  # HTF en conflit avec LTF
# Garde-fou qualité : fraction max de barres à volume nul tolérée sur la fenêtre.
# (Yahoo renvoie ~50 % de barres horaires crypto à volume 0 → VSA inexploitable ;
# le crypto doit donc passer par ccxt/Binance. Cf. sources.get_spot_exchange.)
MAX_ZERO_VOL_FRAC = 0.35
# Contexte HTF de repli (quand la séquence Wyckoff complète n'est pas détectée sur le HTF,
# typiquement le 4h crypto où le volume du climax est trop lissé). On lit alors un *biais
# de contexte* léger — tendance + position dans la plage — fidèle au prérequis Wyckoff :
# une distribution est précédée d'une hausse (prix perché), une accumulation d'une baisse.
HTF_CTX_LOOKBACK = 40   # barres HTF pour juger tendance + position
HTF_CTX_POS_HI = 0.55   # position ≥ → haut de plage (favorable distribution en B→C)
HTF_CTX_POS_LO = 0.45   # position ≤ → bas de plage (favorable accumulation en B→C)
HTF_CTX_TREND = 0.03    # |variation nette| mini sur la fenêtre pour trancher une tendance


def _volume_ok(df: pd.DataFrame, window: int) -> bool:
    """Écarte les actifs dont trop de barres récentes ont un volume nul/absent."""
    v = df["volume"].iloc[-window:]
    if len(v) == 0:
        return False
    zero_frac = float((v.fillna(0) <= 0).mean())
    return zero_frac <= MAX_ZERO_VOL_FRAC


def _round_price(p: float) -> float:
    """Arrondi à ~5 chiffres significatifs (lisible pour BTC comme pour SHIB)."""
    if p == 0 or np.isnan(p):
        return 0.0
    return float(f"{p:.5g}")


@dataclass
class ScanResult:
    name: str
    cls: str
    tf: str              # couple HTF×LTF utilisé pour l'analyse
    schema: str          # accumulation | distribution
    phase: str           # B→C (spring) | D (LPS)
    reliability: float
    confluence: float
    htf_bias: str
    events: str          # séquence détectée, ordonnée
    climax_x: float      # volume du climax (×moyenne)
    test_x: float        # volume du test (×moyenne, sec)
    last_event: str
    bars_ago: int        # récence du dernier événement (barres LTF)
    price: float

    def as_row(self) -> dict:
        return {
            "actif": self.name,
            "classe": self.cls,
            "tf": self.tf,
            "schéma": self.schema,
            "phase": self.phase,
            "fiab.": round(self.reliability, 3),
            "confl.": self.confluence,
            "htf": self.htf_bias,
            "séquence": self.events,
            "climax_×": round(self.climax_x, 2),
            "test_×": round(self.test_x, 2),
            "dernier": self.last_event,
            "il y a (barres)": self.bars_ago,
            "prix": self.price,
        }


def has_min_sequence(struct: WindowStructure) -> bool:
    """Schéma minimal exploitable : Climax + AR + ST présents."""
    names = {e.name for e in struct.events}
    climax = bool({"SC", "BC"} & names)
    return climax and "AR" in names and "ST" in names


def _is_phase_d(struct: WindowStructure) -> bool:
    """Phase D = signe directionnel imprimé (SOS/SOW) → markup/markdown en cours."""
    return bool({"SOS", "SOW"} & {e.name for e in struct.events})


def _phase(struct: WindowStructure) -> str:
    if _is_phase_d(struct):
        side = "LPS" if struct.bias == "accumulation" else "LPSY"
        return f"D (signe imprimé — entrée {side})"
    return "B→C (test validé — entrée spring/test)"


def htf_context_bias(df: pd.DataFrame, ltf_bias: str, phase_d: bool,
                     lookback: int = HTF_CTX_LOOKBACK) -> str:
    """Biais de *contexte* HTF léger, en repli de la séquence Wyckoff complète.

    Lit la tendance nette et la position dans la plage sur la fenêtre HTF, et tranche
    selon la phase du déclencheur LTF :
      - phase D (markdown/markup lancé) : la tendance HTF récente doit *confirmer* la
        direction (HTF qui baisse → distribution, qui monte → accumulation) ;
      - phase B→C (retournement en formation) : on exige une position extrême + une
        tendance préalable cohérente (perché après une hausse → distribution ; tassé
        après une baisse → accumulation).
    Renvoie 'accumulation' | 'distribution' | 'neutral'. `ltf_bias` n'est pas utilisé
    directement (le contexte reste indépendant) mais documente l'intention d'appel.
    """
    win = df.iloc[-lookback:]
    lo, hi = float(win["low"].min()), float(win["high"].max())
    rng = hi - lo
    if rng <= 0 or len(win) < 6:
        return "neutral"
    last = float(win["close"].iloc[-1])
    pos = (last - lo) / rng
    early = float(win["close"].iloc[: max(3, lookback // 3)].mean())
    prior = (last - early) / early if early else 0.0

    if phase_d:
        if prior <= -HTF_CTX_TREND:
            return "distribution"
        if prior >= HTF_CTX_TREND:
            return "accumulation"
        return "neutral"
    if prior >= HTF_CTX_TREND and pos >= HTF_CTX_POS_HI:
        return "distribution"
    if prior <= -HTF_CTX_TREND and pos <= HTF_CTX_POS_LO:
        return "accumulation"
    return "neutral"


def _confluence(htf_bias: str, ltf: WindowStructure) -> tuple[float, str]:
    """Multiplicateur de confluence à partir du biais HTF (séquence ou contexte) ×
    déclencheur LTF (réutilise l'échelle de mtf.combine_mtf)."""
    has_signal = bool({"SOS", "SOW"} & {e.name for e in ltf.events})
    if htf_bias in ("accumulation", "distribution"):
        if htf_bias == ltf.bias:
            return (CONFL_TRIGGER if has_signal else CONFL_ALIGNED), htf_bias
        return CONFL_CONFLICT, htf_bias
    return CONFL_NEUTRAL, "—"


def _recency(struct: WindowStructure) -> float:
    """Décote exponentielle sur la récence du dernier événement de la séquence."""
    if not struct.events:
        return 0.0
    bars_ago = min(e.bars_ago for e in struct.events)
    return float(0.5 ** (bars_ago / RECENCY_HALFLIFE))


def _reliability(struct: WindowStructure, confl_mult: float) -> tuple[float, dict]:
    by_name = {e.name: e for e in struct.events}
    climax = by_name.get("SC") or by_name.get("BC")
    test = by_name.get("ST")
    climax_q = climax.strength if climax else 0.0
    test_q = test.strength if test else 0.0
    has_ar = "AR" in by_name
    has_signal = bool({"SOS", "SOW"} & set(by_name))
    completeness = 0.6 + 0.2 * has_ar + 0.2 * has_signal
    base = W_CLIMAX * climax_q + W_TEST * test_q + W_COMPLETE * completeness
    score = base * _recency(struct) * confl_mult
    meta = {
        "climax_x": climax.vol_ratio if climax else float("nan"),
        "test_x": test.vol_ratio if test else float("nan"),
    }
    return float(score), meta


def analyze_asset(asset: Asset, cfg: dict) -> ScanResult | None:
    htf_tf, ltf_tf = TF_BY_CLASS[asset.cls]
    th = Thresholds(**cfg.get("thresholds", {}))
    window = cfg.get("window", 30)
    need = window + cfg["vol_ma"] + 5

    df_l = sources.fetch(asset, ltf_tf, cfg["limit"], mode=cfg["source"],
                         ex=cfg.get("_ex"), use_cache=cfg["use_cache"])
    if df_l is None or len(df_l) < need or not _volume_ok(df_l, window):
        return None
    df_l = add_features(df_l, vol_ma=cfg["vol_ma"], atr_period=cfg["atr_period"])
    struct_l = detect_window_structure(df_l, lookback=window, th=th)
    if not has_min_sequence(struct_l):
        return None

    # Contexte HTF (best-effort : son absence ne disqualifie pas, confluence neutre).
    # On tente d'abord la séquence Wyckoff complète ; si elle est neutre (cas du 4h crypto,
    # climax trop lissé), on retombe sur le biais de contexte léger (tendance + position).
    htf_bias_ctx = "neutral"
    df_h = sources.fetch(asset, htf_tf, cfg["limit"], mode=cfg["source"],
                         ex=cfg.get("_ex"), use_cache=cfg["use_cache"])
    if df_h is not None and len(df_h) >= need:
        df_h = add_features(df_h, vol_ma=cfg["vol_ma"], atr_period=cfg["atr_period"])
        struct_h = detect_window_structure(df_h, lookback=window, th=th)
        htf_bias_ctx = struct_h.bias
        if htf_bias_ctx == "neutral":
            htf_bias_ctx = htf_context_bias(df_h, struct_l.bias, _is_phase_d(struct_l))

    confl_mult, htf_bias = _confluence(htf_bias_ctx, struct_l)
    reliability, meta = _reliability(struct_l, confl_mult)

    ordered = sorted(struct_l.events, key=lambda e: e.bars_ago, reverse=True)
    seq = " → ".join(e.name for e in ordered)
    last = min(struct_l.events, key=lambda e: e.bars_ago)

    return ScanResult(
        name=asset.name, cls=asset.cls, tf=f"{htf_tf}×{ltf_tf}",
        schema=struct_l.bias, phase=_phase(struct_l),
        reliability=reliability, confluence=confl_mult, htf_bias=htf_bias, events=seq,
        climax_x=meta["climax_x"], test_x=meta["test_x"],
        last_event=last.name, bars_ago=last.bars_ago, price=_round_price(last.price),
    )


def run_scan(cfg: dict) -> pd.DataFrame:
    assets = build_assets(cfg.get("classes"))
    if cfg["source"] in ("ccxt", "auto") and any(a.cls == "crypto" for a in assets):
        try:
            cfg["_ex"] = sources.get_spot_exchange(cfg.get("exchange", "binance"))
        except Exception as e:
            print(f"  [ccxt indisponible : {e} — crypto intraday écarté (volume Yahoo "
                  f"inexploitable)]", file=sys.stderr)
            cfg["source"] = "yahoo"

    print(f"Univers : {len(assets)} actifs — source {cfg['source']}", file=sys.stderr)
    results: list[ScanResult] = []
    for i, a in enumerate(assets, 1):
        try:
            r = analyze_asset(a, cfg)
            if r and r.reliability > 0:
                results.append(r)
        except Exception as e:  # un actif qui échoue ne casse pas le scan
            print(f"  [skip] {a.name} ({a.yahoo}): {e}", file=sys.stderr)
        if i % 20 == 0:
            print(f"  ...{i}/{len(assets)}", file=sys.stderr)

    if cfg.get("bias") and cfg["bias"] != "both":
        results = [r for r in results if r.schema == cfg["bias"]]
    results.sort(key=lambda r: r.reliability, reverse=True)
    results = results[: cfg["max_results"]]
    return pd.DataFrame([r.as_row() for r in results])


def main() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass

    from .cli import load_config
    cfg = {
        "exchange": "binance", "limit": 300, "vol_ma": 20, "atr_period": 14,
        "max_results": 30, "use_cache": True, "bias": "both", "window": 30,
        "thresholds": {}, "source": "ccxt", "classes": None,
    }
    file_cfg = load_config()
    cfg["vol_ma"] = file_cfg.get("vol_ma", cfg["vol_ma"])
    cfg["atr_period"] = file_cfg.get("atr_period", cfg["atr_period"])
    cfg["thresholds"] = file_cfg.get("thresholds", {})
    cfg["exchange"] = file_cfg.get("exchange", cfg["exchange"])

    p = argparse.ArgumentParser(
        description="Screener Wyckoff multi-cours (crypto + actions + matières premières)")
    p.add_argument("--classes", nargs="*", choices=["crypto", "equity", "commodity"],
                   default=None, help="classes à scanner (toutes par défaut)")
    p.add_argument("--source", choices=["yahoo", "ccxt", "auto"], default="ccxt",
                   help="ccxt = crypto via Binance (volumes réels) + actions/MP via Yahoo ; "
                        "yahoo = tout via Yahoo (crypto intraday non fiable)")
    p.add_argument("--bias", choices=["accumulation", "distribution", "both"], default="both")
    p.add_argument("--window", type=int, default=cfg["window"], help="fenêtre d'analyse (barres)")
    p.add_argument("--limit", type=int, default=cfg["limit"])
    p.add_argument("--max-results", type=int, default=cfg["max_results"])
    p.add_argument("--no-cache", action="store_true")
    p.add_argument("--csv", default="screener.csv")
    args = p.parse_args()

    cfg.update(source=args.source, bias=args.bias, window=args.window, limit=args.limit,
               max_results=args.max_results, use_cache=not args.no_cache,
               classes=tuple(args.classes) if args.classes else None)

    table = run_scan(cfg)
    if EXCLUDED:
        skipped = ", ".join(f"{k} ({v})" for k, v in EXCLUDED.items())
        print(f"\nÉcartés de l'univers : {skipped}", file=sys.stderr)
    if table.empty:
        print("Aucune formation validée (Climax+AR+ST) avec les seuils actuels.")
        return
    with pd.option_context("display.max_rows", None, "display.width", 240):
        print(table.to_string(index=False))
    table.to_csv(args.csv, index=False)
    print(f"\n→ Présélection écrite dans {args.csv}", file=sys.stderr)


if __name__ == "__main__":
    main()
