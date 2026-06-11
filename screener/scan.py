"""
scan.py — Screener multi-cours Wyckoff (crypto + actions + matières premières).

Balaie l'univers et, pour chaque actif, analyse **chaque timeframe séparément**
(crypto : H1 et H4 ; actions/MP : H4 et D1) en variant aussi la fenêtre, afin de ne
pas passer à côté d'une structure visible sur une échelle et pas sur l'autre. Aucune
confluence, aucun score de fiabilité : le but est de **fournir les éléments de décision**.

Pour chaque schéma valide (Climax + AR + ST au minimum) on rend :
  - le **contexte** : une accumulation suit toujours un *markdown* stoppé par un climax,
    une distribution un *markup* — prérequis Wyckoff vérifié explicitement ;
  - la **validation événement par événement** : vol×, spread/ATR, clv confrontés aux
    seuils attendus, avec emojis ✅ / ⚠️ / ❌ ;
  - un **commentaire critique** qui pèse forces et faiblesses, à charge pour l'opérateur
    de trancher.

Réutilise la couche données/API (`sources.py`, ccxt via mirror Binance + Yahoo) et le
moteur de détection de séquence (`window.py`). N'écrit rien d'automatique.

Usage :
    python -m screener.scan                       # tout l'univers
    python -m screener.scan --classes crypto      # crypto seul (H1 + H4)
    python -m screener.scan --bias accumulation
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from . import sources
from .events import Thresholds
from .features import add_features
from .universe import Asset, EXCLUDED, build_assets
from .window import WindowEvent, WindowStructure, detect_window_structure

# Fenêtres d'analyse balayées par timeframe (on garde la meilleure structure trouvée).
WINDOWS = (30, 45, 60)
# Garde-fou qualité : fraction max de barres à volume nul tolérée (Yahoo crypto intraday
# ≈50 % de zéros → VSA inexploitable ; le crypto passe donc par ccxt/Binance).
MAX_ZERO_VOL_FRAC = 0.35
# Contexte : amplitude mini du markdown/markup *précédant* le climax (prérequis Wyckoff).
CTX_LOOKBACK = 25       # barres examinées avant le climax
CTX_TREND_MIN = 0.05    # |variation| mini (5 %) pour valider un markdown / markup


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


# --------------------------------------------------------------------------- #
# Modèle de rendu
# --------------------------------------------------------------------------- #
@dataclass
class EventCheck:
    name: str
    bars_ago: int
    vol_ratio: float
    spread_atr: float
    clv: float
    flags: list[str]      # ex. ["vol ×2.8 ✅", "spread 1.6 ATR ✅", "clv 0.72 ✅"]
    why: str              # justification volume/spread → thèse (issue de window.py)


@dataclass
class PatternReport:
    name: str
    cls: str
    tf: str
    window: int
    schema: str
    phase: str
    context_emoji: str
    context_text: str
    events: list[EventCheck]
    verdict: str          # ✅ solide | ⚠️ à surveiller | ❌ douteux
    comment: str
    last_bars_ago: int
    price: float
    sequence: str = field(default="")
    struct: object = field(default=None, repr=False)   # WindowStructure (pour le tracé)
    asset: object = field(default=None, repr=False)     # Asset (pour les bougies fines)

    def index_row(self) -> dict:
        return {
            "actif": self.name,
            "classe": self.cls,
            "tf": self.tf,
            "win": self.window,
            "schéma": ("🟢 acc" if self.schema == "accumulation" else "🔴 dist"),
            "phase": self.phase.split(" ")[0],
            "contexte": self.context_emoji,
            "séquence": self.sequence,
            "récence": f"il y a {self.last_bars_ago}",
            "verdict": self.verdict,
        }


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


# --------------------------------------------------------------------------- #
# Contexte Wyckoff : markdown avant accumulation / markup avant distribution
# --------------------------------------------------------------------------- #
def _context(df: pd.DataFrame, struct: WindowStructure) -> tuple[str, str, bool]:
    """Vérifie le mouvement *précédant* le climax. Renvoie (emoji, texte, ok)."""
    climax = next((e for e in struct.events if e.name in ("SC", "BC")), None)
    if climax is None:
        return "❔", "climax introuvable", False
    idx = len(df) - 1 - climax.bars_ago
    start = max(0, idx - CTX_LOOKBACK)
    if idx - start < 8:
        return "❔", "historique insuffisant avant le climax", False
    c0 = float(df["close"].iloc[start])
    c1 = float(df["close"].iloc[idx])
    move = (c1 - c0) / c0 if c0 else 0.0
    n = idx - start
    acc = struct.bias == "accumulation"
    if acc:
        if move <= -CTX_TREND_MIN:
            return "✅", f"markdown préalable {move*100:+.1f}% sur {n} barres → climax d'arrêt cohérent", True
        return "❌", f"pas de markdown net avant le SC ({move*100:+.1f}%) → prérequis d'accumulation non rempli", False
    else:
        if move >= CTX_TREND_MIN:
            return "✅", f"markup préalable {move*100:+.1f}% sur {n} barres → climax d'arrêt cohérent", True
        return "❌", f"pas de markup net avant le BC ({move*100:+.1f}%) → prérequis de distribution non rempli", False


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
    # Contexte = prérequis dur
    if not ctx_ok:
        bullets.append("contexte manquant (" + ctx_text.split(" → ")[0] + ")")
        weak += 2
    # Climax
    if climax:
        if climax.vol_ratio >= th.climax_vol and climax.spread_atr >= th.wide_spread_atr:
            bullets.append(f"climax franc (vol ×{climax.vol_ratio:.1f}, spread large)")
        else:
            bullets.append(f"climax peu convaincant (vol ×{climax.vol_ratio:.1f})")
            weak += 1
    # Test
    if test:
        if test.vol_ratio <= th.test_vol:
            bullets.append(f"test bien sec (vol ×{test.vol_ratio:.2f}) → {'offre' if acc else 'demande'} tarie")
        else:
            bullets.append(f"test à volume élevé (×{test.vol_ratio:.2f}) → "
                           f"{'offre' if acc else 'demande'} encore présente, test peu probant")
            weak += 1
    # Complétude / phase
    if has_signal:
        bullets.append(f"{'SOS' if acc else 'SOW'} imprimé → {'markup' if acc else 'markdown'} amorcé (phase D)")
    else:
        bullets.append("pas encore de signe directionnel → structure jeune, attendre la cassure")
    # Récence
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
    need = max(WINDOWS) + cfg["vol_ma"] + 5
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
    ctx_emoji, ctx_text, ctx_ok = _context(df, struct)
    ordered = sorted(struct.events, key=lambda e: e.bars_ago, reverse=True)
    checks = [_check_event(e, acc, th) for e in ordered]
    verdict, comment = _verdict_and_comment(struct, ctx_ok, ctx_text, checks, th)
    last = min(struct.events, key=lambda e: e.bars_ago)

    return PatternReport(
        name=asset.name, cls=asset.cls, tf=tf, window=window, schema=struct.bias,
        phase=_phase(struct), context_emoji=ctx_emoji, context_text=ctx_text,
        events=checks, verdict=verdict, comment=comment,
        last_bars_ago=last.bars_ago, price=_round_price(last.price),
        sequence=" → ".join(c.name for c in checks),
        struct=struct, asset=asset,
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
    # Tri : verdict (solide → douteux), puis récence.
    order = {"✅ solide": 0, "⚠️ à surveiller": 1, "❌ douteux": 2}
    reports.sort(key=lambda r: (order.get(r.verdict, 3), r.last_bars_ago))
    return reports


# --------------------------------------------------------------------------- #
# Rendu
# --------------------------------------------------------------------------- #
def render_index(reports: list[PatternReport]) -> pd.DataFrame:
    return pd.DataFrame([r.index_row() for r in reports])


def render_detail(r: PatternReport) -> str:
    head = "🟢 ACCUMULATION" if r.schema == "accumulation" else "🔴 DISTRIBUTION"
    lines = [
        f"### {head} — {r.name} ({r.cls}) · {r.tf} · fenêtre {r.window} · {r.verdict}",
        f"- **Phase** : {r.phase}",
        f"- **Contexte** {r.context_emoji} : {r.context_text}",
        f"- **Séquence** (du + ancien au + récent) :",
    ]
    for c in r.events:
        flags = " · ".join(c.flags)
        lines.append(f"    - `{c.name}` il y a {c.bars_ago} barres — {flags}")
        lines.append(f"        ↳ {c.why}")
    lines.append(f"- 💬 **Critique** : {r.comment}")
    return "\n".join(lines)


def render_report(reports: list[PatternReport]) -> str:
    out = ["# Présélection Wyckoff — patterns en cours\n"]
    n_acc = sum(r.schema == "accumulation" for r in reports)
    n_dist = len(reports) - n_acc
    out.append(f"{len(reports)} formations validées (Climax+AR+ST) — "
               f"🟢 {n_acc} accumulation · 🔴 {n_dist} distribution.\n")
    out.append("## Index\n")
    idx = render_index(reports)
    out.append(idx.to_string(index=False) if not idx.empty else "_(vide)_")
    out.append("\n\n## Détail par formation\n")
    for r in reports:
        out.append(render_detail(r))
        out.append("")
    return "\n".join(out)


def main() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass

    from .cli import load_config
    cfg = {
        "exchange": "binance", "limit": 400, "vol_ma": 20, "atr_period": 14,
        "use_cache": True, "bias": "both", "thresholds": {}, "source": "ccxt",
        "classes": None,
    }
    file_cfg = load_config()
    cfg["vol_ma"] = file_cfg.get("vol_ma", cfg["vol_ma"])
    cfg["atr_period"] = file_cfg.get("atr_period", cfg["atr_period"])
    cfg["thresholds"] = file_cfg.get("thresholds", {})
    cfg["exchange"] = file_cfg.get("exchange", cfg["exchange"])

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
