"""
scan.py — Screener multi-cours Wyckoff (crypto + actions + matières premières).

Balaie l'univers et, pour chaque actif, analyse **chaque timeframe séparément**
(crypto : H1 et H4 ; actions/MP : H4 et D1) en variant aussi la fenêtre, afin de ne
pas passer à côté d'une structure visible sur une échelle et pas sur l'autre. Aucune
confluence, aucun score de fiabilité : le but est de **fournir les éléments de décision**.

Pour chaque schéma valide (Climax + AR + ST au minimum) on rend, via `report` :
  - le **contexte** (markdown avant accumulation / markup avant distribution) — calculé
    par `wyckoff.assess_context`, prérequis Wyckoff porté par la structure ;
  - la **validation événement par événement** (vol×, spread/ATR, clv vs seuils, emojis) ;
  - un **verdict + commentaire critique**, à charge pour l'opérateur de trancher.

Détection : `wyckoff` (cœur unique). Données/API : `sources`. Tracé : `plot`.

Usage :
    python -m screener.scan                       # tout l'univers
    python -m screener.scan --classes crypto      # crypto seul (H1 + H4)
    python -m screener.scan --bias accumulation
"""
from __future__ import annotations

import argparse
import math
import sys

import numpy as np
import pandas as pd

from . import sources
from .features import add_features
from .report import EventCheck, PatternReport, render_report
from .universe import Asset, EXCLUDED, build_assets
from .wyckoff import Thresholds, WindowEvent, WindowStructure, detect_window_structure

# Fenêtres d'analyse balayées par timeframe (on garde la meilleure structure trouvée).
WINDOWS = (30, 45, 60)
# Garde-fou qualité : fraction max de barres à volume nul tolérée (Yahoo crypto intraday
# ≈50 % de zéros → VSA inexploitable ; le crypto passe donc par ccxt/Binance).
MAX_ZERO_VOL_FRAC = 0.35


def load_config(path: str = "config.yaml") -> dict:
    try:
        import yaml
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except (FileNotFoundError, ImportError):
        return {}


# --------------------------------------------------------------------------- #
# Helpers de validation (emojis)
# --------------------------------------------------------------------------- #
def _ge(val: float, thr: float, tol: float = 0.15) -> str:
    """✅ si val ≥ seuil, ⚠️ si proche, ❌ sinon."""
    if val >= thr:
        return "✅"
    return "⚠️" if val >= thr * (1 - tol) else "❌"


def _le(val: float, thr: float, tol: float = 0.15) -> str:
    """✅ si val ≤ seuil, ⚠️ si proche, ❌ sinon."""
    if val <= thr:
        return "✅"
    return "⚠️" if val <= thr * (1 + tol) else "❌"


def _round_price(p: float) -> float:
    if p == 0 or np.isnan(p):
        return 0.0
    return float(f"{p:.5g}")


def has_min_sequence(struct: WindowStructure) -> bool:
    """Schéma minimal exploitable : Climax + AR + ST présents."""
    names = {e.name for e in struct.events}
    return bool({"SC", "BC"} & names) and "AR" in names and "ST" in names


def _volume_ok(df: pd.DataFrame, window: int) -> bool:
    v = df["volume"].iloc[-window:]
    if len(v) == 0:
        return False
    return float((v.fillna(0) <= 0).mean()) <= MAX_ZERO_VOL_FRAC


def _phase(struct: WindowStructure) -> str:
    names = {e.name for e in struct.events}
    if {"SOS", "SOW"} & names:
        side = "LPS" if struct.bias == "accumulation" else "LPSY"
        return f"D — signe imprimé, entrée {side}"
    return "B→C — test validé, entrée spring/test"


def _context(struct: WindowStructure) -> tuple[str, str, bool]:
    """Met en forme le contexte porté par la structure (emoji, texte, ok)."""
    move, n = struct.context_move, struct.context_bars
    acc = struct.bias == "accumulation"
    if math.isnan(move):
        return "❔", "historique insuffisant avant le climax", False
    kind = "markdown" if acc else "markup"
    if struct.context_ok:
        return "✅", f"{kind} préalable {move*100:+.1f}% sur {n} barres → climax d'arrêt cohérent", True
    prereq = "d'accumulation" if acc else "de distribution"
    return "❌", f"pas de {kind} net avant le {'SC' if acc else 'BC'} ({move*100:+.1f}%) → prérequis {prereq} non rempli", False


# --------------------------------------------------------------------------- #
# Validation événement par événement
# --------------------------------------------------------------------------- #
def _check_event(e: WindowEvent, acc: bool, th: Thresholds) -> EventCheck:
    flags: list[str] = []
    vr, sa, clv = e.vol_ratio, e.spread_atr, e.clv
    if e.name in ("SC", "BC"):
        flags.append(f"vol ×{vr:.2f} {_ge(vr, th.climax_vol)} (climax ≥{th.climax_vol})")
        flags.append(f"spread {sa:.2f} ATR {_ge(sa, th.wide_spread_atr)} (large)")
        flags.append(f"clv {clv:.2f} {('✅' if (clv >= 0.5) == acc else '⚠️')} "
                     f"({'clôture haute' if acc else 'clôture basse'})")
    elif e.name == "AR":
        flags.append(f"vol ×{vr:.2f} {_le(vr, 1.2)} (en repli)")
    elif e.name == "ST":
        flags.append(f"vol ×{vr:.2f} {_le(vr, th.test_vol)} (sec ≤{th.test_vol})")
        flags.append(f"spread {sa:.2f} ATR {_le(sa, th.wide_spread_atr)} (étroit)")
    elif e.name in ("SOS", "SOW"):
        flags.append(f"vol ×{vr:.2f} {_ge(vr, th.sos_vol)} (signe ≥{th.sos_vol})")
        flags.append(f"spread {sa:.2f} ATR {_ge(sa, th.wide_spread_atr)} (large)")
        ok_dir = (clv >= 0.6) if acc else (clv <= 0.4)
        flags.append(f"clv {clv:.2f} {'✅' if ok_dir else '⚠️'} ({'haute' if acc else 'basse'})")
    return EventCheck(e.name, e.bars_ago, vr, sa, clv, flags, e.why)


def _verdict_and_comment(struct: WindowStructure, ctx_ok: bool, ctx_text: str,
                         checks: list[EventCheck], th: Thresholds) -> tuple[str, str]:
    acc = struct.bias == "accumulation"
    by = {c.name: c for c in checks}
    climax = by.get("SC") or by.get("BC")
    test = by.get("ST")
    has_signal = bool({"SOS", "SOW"} & set(by))
    last_ba = min(c.bars_ago for c in checks)

    bullets: list[str] = []
    weak = 0
    if not ctx_ok:
        bullets.append("contexte manquant (" + ctx_text.split(" → ")[0] + ")")
        weak += 2
    if climax:
        if climax.vol_ratio >= th.climax_vol and climax.spread_atr >= th.wide_spread_atr:
            bullets.append(f"climax franc (vol ×{climax.vol_ratio:.1f}, spread large)")
        else:
            bullets.append(f"climax peu convaincant (vol ×{climax.vol_ratio:.1f})")
            weak += 1
    if test:
        if test.vol_ratio <= th.test_vol:
            bullets.append(f"test bien sec (vol ×{test.vol_ratio:.2f}) → {'offre' if acc else 'demande'} tarie")
        else:
            bullets.append(f"test à volume élevé (×{test.vol_ratio:.2f}) → "
                           f"{'offre' if acc else 'demande'} encore présente, test peu probant")
            weak += 1
    if has_signal:
        bullets.append(f"{'SOS' if acc else 'SOW'} imprimé → {'markup' if acc else 'markdown'} amorcé (phase D)")
    else:
        bullets.append("pas encore de signe directionnel → structure jeune, attendre la cassure")
    if last_ba > 12:
        bullets.append(f"déclencheur ancien (il y a {last_ba} barres) → possiblement périmé")
        weak += 1
    else:
        bullets.append(f"déclencheur récent (il y a {last_ba} barres)")

    if not ctx_ok:
        verdict = "❌ douteux"
    elif weak == 0:
        verdict = "✅ solide"
    else:
        verdict = "⚠️ à surveiller"
    return verdict, " ; ".join(bullets) + "."


# --------------------------------------------------------------------------- #
# Analyse d'un (actif, timeframe)
# --------------------------------------------------------------------------- #
def _best_structure(df: pd.DataFrame, th: Thresholds) -> tuple[WindowStructure, int] | None:
    """Balaie les fenêtres et retourne la meilleure structure valide (la plus complète,
    puis la plus récente). None si aucune."""
    best = None
    for w in WINDOWS:
        if len(df) < w + 5:
            continue
        s = detect_window_structure(df, lookback=w, th=th)
        if not has_min_sequence(s):
            continue
        last_ba = min(e.bars_ago for e in s.events)
        key = (len(s.events), -last_ba)
        if best is None or key > best[0]:
            best = (key, s, w)
    if best is None:
        return None
    return best[1], best[2]


def analyze_tf(asset: Asset, tf: str, cfg: dict) -> PatternReport | None:
    th = Thresholds(**cfg.get("thresholds", {}))
    df = sources.fetch(asset, tf, cfg["limit"], mode=cfg["source"],
                       ex=cfg.get("_ex"), use_cache=cfg["use_cache"])
    if df is None or len(df) < min(WINDOWS) + cfg["vol_ma"] + 5 or not _volume_ok(df, min(WINDOWS)):
        return None
    df = add_features(df, vol_ma=cfg["vol_ma"], atr_period=cfg["atr_period"])
    found = _best_structure(df, th)
    if found is None:
        return None
    struct, window = found

    acc = struct.bias == "accumulation"
    ctx_emoji, ctx_text, ctx_ok = _context(struct)
    ordered = sorted(struct.events, key=lambda e: e.bars_ago, reverse=True)
    checks = [_check_event(e, acc, th) for e in ordered]
    verdict, comment = _verdict_and_comment(struct, ctx_ok, ctx_text, checks, th)
    last = min(struct.events, key=lambda e: e.bars_ago)

    return PatternReport(
        name=asset.name, cls=asset.cls, tf=tf, window=window, schema=struct.bias,
        phase=_phase(struct), context_emoji=ctx_emoji, context_text=ctx_text,
        events=checks, verdict=verdict, comment=comment,
        last_bars_ago=last.bars_ago, price=_round_price(last.price),
        sequence=" → ".join(c.name for c in checks), struct=struct, asset=asset,
    )


def plot_report(r: PatternReport, cfg: dict, out_path: str) -> str:
    """Trace la structure d'un PatternReport (bougies en TF inférieure), source-aware :
    bougies fines via ccxt (crypto) ou Yahoo (actions/MP)."""
    from .plot import FINER_TF, plot_window_structure
    fine_tf = FINER_TF.get(r.tf, r.tf)
    fine = sources.fetch(r.asset, fine_tf, 1500, mode=cfg["source"],
                         ex=cfg.get("_ex"), use_cache=cfg["use_cache"])
    return plot_window_structure(r.name, r.tf, r.struct, out_path,
                                 ex=cfg.get("_ex"), fine_df=fine)


def run_scan(cfg: dict) -> list[PatternReport]:
    assets = build_assets(cfg.get("classes"))
    if cfg["source"] in ("ccxt", "auto") and any(a.cls == "crypto" for a in assets):
        try:
            cfg["_ex"] = sources.get_spot_exchange(cfg.get("exchange", "binance"))
        except Exception as e:
            print(f"  [ccxt indisponible : {e} — crypto écarté]", file=sys.stderr)
            cfg["source"] = "yahoo"

    print(f"Univers : {len(assets)} actifs", file=sys.stderr)
    reports: list[PatternReport] = []
    for i, a in enumerate(assets, 1):
        for tf in a.timeframes():
            try:
                r = analyze_tf(a, tf, cfg)
                if r is not None:
                    reports.append(r)
            except Exception as e:
                print(f"  [skip] {a.name} {tf} ({a.yahoo}): {e}", file=sys.stderr)
        if i % 20 == 0:
            print(f"  ...{i}/{len(assets)}", file=sys.stderr)

    if cfg.get("bias") and cfg["bias"] != "both":
        reports = [r for r in reports if r.schema == cfg["bias"]]
    order = {"✅ solide": 0, "⚠️ à surveiller": 1, "❌ douteux": 2}
    reports.sort(key=lambda r: (order.get(r.verdict, 3), r.last_bars_ago))
    return reports


def main() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass

    cfg = {
        "exchange": "binance", "limit": 400, "vol_ma": 20, "atr_period": 14,
        "use_cache": True, "bias": "both", "thresholds": {}, "source": "ccxt",
        "classes": None,
    }
    file_cfg = load_config()
    for k in ("vol_ma", "atr_period", "thresholds", "exchange"):
        if k in file_cfg:
            cfg[k] = file_cfg[k]

    p = argparse.ArgumentParser(
        description="Screener Wyckoff multi-cours — analyse par timeframe, éléments de décision")
    p.add_argument("--classes", nargs="*", choices=["crypto", "equity", "commodity"], default=None)
    p.add_argument("--source", choices=["yahoo", "ccxt", "auto"], default="ccxt")
    p.add_argument("--bias", choices=["accumulation", "distribution", "both"], default="both")
    p.add_argument("--limit", type=int, default=cfg["limit"])
    p.add_argument("--no-cache", action="store_true")
    p.add_argument("--md", default="rapport_wyckoff.md", help="fichier rapport markdown")
    args = p.parse_args()

    cfg.update(source=args.source, bias=args.bias, limit=args.limit,
               use_cache=not args.no_cache,
               classes=tuple(args.classes) if args.classes else None)

    reports = run_scan(cfg)
    if EXCLUDED:
        skipped = ", ".join(f"{k} ({v})" for k, v in EXCLUDED.items())
        print(f"\nÉcartés de l'univers : {skipped}", file=sys.stderr)
    if not reports:
        print("Aucune formation validée (Climax+AR+ST) avec les seuils actuels.")
        return
    report = render_report(reports)
    print(report)
    with open(args.md, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\n→ Rapport écrit dans {args.md}", file=sys.stderr)


if __name__ == "__main__":
    main()
