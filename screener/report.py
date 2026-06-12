"""
report.py — Modèle de rendu et mise en forme de la présélection.

Sépare la *présentation* (tableau index, fiches détaillées) de la détection (`scan`)
et du cœur Wyckoff (`wyckoff`). Le rendu est orienté **décision** : pour chaque
formation, le contexte, la validation vol×/spread événement par événement (emojis),
et un commentaire critique — de quoi valider ou écarter un setup à la main.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd


@dataclass
class EventCheck:
    name: str
    bars_ago: int
    vol_ratio: float
    spread_atr: float
    clv: float
    flags: list[str]      # ex. ["vol ×2.8 ✅", "spread 1.6 ATR ✅", "clv 0.72 ✅"]
    why: str              # justification volume/spread → thèse (issue de wyckoff.py)
    oi_delta: float | None = None   # ΔOI (%) depuis l'événement précédent (None si indispo)
    oi_note: str = ""               # lecture de l'OI sur cet événement

    def oi_str(self) -> str:
        """ΔOI compact pour les tableaux (vide si indisponible)."""
        if self.oi_delta is None:
            return ""
        if abs(self.oi_delta) < 1:
            return "·OI~"
        return f"·OI{self.oi_delta:+.0f}%"

    def compact(self) -> str:
        """Résumé d'un événement pour le tableau des solides : NOM(×vol·spread·ΔOI)."""
        if self.name == "AR":
            return f"{self.name}(×{self.vol_ratio:.1f}{self.oi_str()})"
        return f"{self.name}(×{self.vol_ratio:.1f}·{self.spread_atr:.1f}ATR{self.oi_str()})"


@dataclass
class PatternReport:
    name: str
    cls: str
    tf: str
    window: int
    schema: str           # accumulation | distribution
    phase: str            # B→C (spring) | D (LPS)
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
        if c.oi_note:
            lines.append(f"        ↳ OI : {c.oi_note}")
    lines.append(f"- 💬 **Critique** : {r.comment}")
    return "\n".join(lines)


def render_solid_table(reports: list[PatternReport]) -> str:
    """Tableau récapitulatif des formations jugées solides : événements validés
    (vol×, spread, ΔOI quand dispo) + lecture critique, une ligne par formation."""
    solides = [r for r in reports if r.verdict.startswith("✅")]
    if not solides:
        return ""
    head = ["Actif", "Cl", "TF·win", "Sch", "Phase", "Prix",
            "Événements (vol×·spread·ΔOI)", "💬 Lecture"]
    rows = ["| " + " | ".join(head) + " |", "|" + "|".join(["---"] * len(head)) + "|"]
    for r in solides:
        seq = " ".join(c.compact() for c in r.events)
        sch = "🟢acc" if r.schema == "accumulation" else "🔴dist"
        cells = [r.name, r.cls[:6], f"{r.tf}·{r.window}", sch, r.phase.split(" ")[0],
                 f"{r.price:g}", seq, r.comment]
        rows.append("| " + " | ".join(str(c).replace("|", "/") for c in cells) + " |")
    return "## Formations solides — détail des événements\n\n" + "\n".join(rows)


def render_report(reports: list[PatternReport]) -> str:
    out = ["# Présélection Wyckoff — patterns en cours\n"]
    n_acc = sum(r.schema == "accumulation" for r in reports)
    n_dist = len(reports) - n_acc
    out.append(f"{len(reports)} formations validées (Climax+AR+ST) — "
               f"🟢 {n_acc} accumulation · 🔴 {n_dist} distribution.\n")
    out.append("## Index\n")
    idx = render_index(reports)
    out.append(idx.to_string(index=False) if not idx.empty else "_(vide)_")
    solid_table = render_solid_table(reports)
    if solid_table:
        out.append("\n\n" + solid_table)
    out.append("\n\n## Détail par formation\n")
    for r in reports:
        out.append(render_detail(r))
        out.append("")
    return "\n".join(out)
