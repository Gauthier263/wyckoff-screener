"""
theory_table.py — Mémo « mémo théorie » : rôle et seuils de validité de chaque
événement Wyckoff, en accumulation ET en distribution, **plus le comportement de
l'Open Interest** attendu à chaque étape.

But (préférence Gauthier) : un récap mémorisable, event par event, pour ancrer ce
qui rend un événement *valide ou non* — volume (vol×), spread (ATR), clôture, et OI.
Les seuils sont lus depuis les `Thresholds` courants (jamais en dur).

Sortie : une **image PNG cliquable** (`memo_theorie.png`).
"""
from __future__ import annotations

import textwrap

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from .events import Thresholds

_SEQ = {
    "accumulation": ["SC", "AR", "ST", "SPRING", "SOS", "LPS"],
    "distribution": ["BC", "AR", "ST", "UTAD", "SOW", "LPSY"],
}

# Comportement d'OI attendu (texte mémo) par schéma + type d'événement.
_OI = {
    ("accumulation", "climax"): "↑ puis purge (shorts agressifs, longs liquidés)",
    ("accumulation", "ar"): "↓ short covering (rebond SANS engagement)",
    ("accumulation", "st"): "plat / ↓ (offre tarie)",
    ("accumulation", "spring"): "↑ sur la mèche puis ↓ (shorts piégés → squeeze)",
    ("accumulation", "sign"): "↑ avec le prix (longs neufs = markup réel)",
    ("accumulation", "lp"): "plat (back-up sain)",
    ("distribution", "climax"): "↑ puis purge (FOMO longs, puis liquidés)",
    ("distribution", "ar"): "↓ longs liquidés (repli SANS engagement)",
    ("distribution", "st"): "plat / ↓ (demande tarie)",
    ("distribution", "spring"): "↑ au-dessus puis ↓ (longs piégés → squeeze)",
    ("distribution", "sign"): "↑ avec la baisse (shorts neufs = markdown réel)",
    ("distribution", "lp"): "plat (rebond faible)",
}


def theory_rows(bias: str, th: Thresholds) -> list[dict]:
    """Lignes du mémo pour un schéma, à partir des seuils courants (incluant l'OI)."""
    acc = bias == "accumulation"
    borne_climax = "plancher" if acc else "plafond"
    cloture = "haute" if acc else "basse"
    clv_dir = "≥ 0.6 (haute)" if acc else "≤ 0.4 (basse)"
    test_creux = "creux idéalement plus haut" if acc else "sommet idéalement plus bas"
    climax_name = "SC" if acc else "BC"
    signe = "SOS" if acc else "SOW"

    def oi(kind):
        return _OI[(bias, kind)]

    return [
        {
            "ev": climax_name,
            "nom": "Selling Climax" if acc else "Buying Climax",
            "role": f"Apogée du mouvement : pression {'vendeuse' if acc else 'acheteuse'} "
                    f"absorbée par les mains fortes. Fixe le {borne_climax}.",
            "volx": f"≥ ×{th.climax_vol} (climactique)",
            "spread": f"≥ {th.wide_spread_atr} ATR",
            "oi": oi("climax"),
            "cloture": f"{cloture} (rejet)",
            "valide": f"vol climactique + spread large + clôture {cloture}",
            "invalide": "vol non climactique / clôture du mauvais côté",
        },
        {
            "ev": "AR",
            "nom": "Automatic Rally" if acc else "Automatic Reaction",
            "role": "Mouvement réflexe (débouclage). Fixe l'autre borne : la plage est posée.",
            "volx": "EN REPLI (< ×1)",
            "spread": "indifférent",
            "oi": oi("ar"),
            "cloture": "indifférente",
            "valide": "volume EN REPLI **et** OI EN REPLI (débouclage)",
            "invalide": "AR à fort volume OU OI en hausse → engagement neuf",
        },
        {
            "ev": "ST",
            "nom": "Secondary Test",
            "role": f"Retour sonder le {borne_climax} : {test_creux}.",
            "volx": f"SEC ≤ ×{th.test_vol}",
            "spread": f"ÉTROIT < {th.wide_spread_atr} ATR",
            "oi": oi("st"),
            "cloture": "neutre",
            "valide": "volume sec + borne tenue",
            "invalide": f"volume élevé (> ×{th.test_vol}) / cassure nette",
        },
        {
            "ev": "SPRING" if acc else "UTAD",
            "nom": "Spring" if acc else "Upthrust After Distrib.",
            "role": f"Phase C — fausse cassure {'sous le plancher' if acc else 'au-dessus du plafond'} "
                    f"(shakeout) puis rejet.",
            "volx": "modéré (cassure non tenue)",
            "spread": "pic bref possible",
            "oi": oi("spring"),
            "cloture": f"revient DANS la plage (clv {'≥ 0.5' if acc else '≤ 0.5'})",
            "valide": f"pénétration ≈ {th.pen_atr} ATR hors borne + clôture rentrée",
            "invalide": "clôture HORS plage = vraie cassure",
        },
        {
            "ev": signe,
            "nom": "Sign of Strength" if acc else "Sign of Weakness",
            "role": f"La {'demande' if acc else 'offre'} prend le contrôle : prélude au "
                    f"{'markup' if acc else 'markdown'}.",
            "volx": f"SOUTENU ≥ ×{th.sos_vol}",
            "spread": f"≥ {th.wide_spread_atr} ATR",
            "oi": oi("sign"),
            "cloture": f"{cloture} — clv {clv_dir}",
            "valide": f"vol soutenu + spread large + clôture {cloture} + OI ↑",
            "invalide": "vol faible / clôture molle / OI plat (short squeeze)",
        },
        {
            "ev": "LPS" if acc else "LPSY",
            "nom": "Last Point of Support" if acc else "Last Point of Supply",
            "role": f"Phase D — back-up après le signe : dernier "
                    f"{'appui' if acc else 'rebond'} avant le {'markup' if acc else 'markdown'}.",
            "volx": f"SEC ≤ ×{th.test_vol}",
            "spread": "étroit",
            "oi": oi("lp"),
            "cloture": f"{'creux plus HAUT' if acc else 'sommet plus BAS'} que le climax",
            "valide": f"réaction sèche + {'creux' if acc else 'sommet'} qui tient la borne",
            "invalide": f"volume lourd / {'nouveau plus-bas' if acc else 'nouveau plus-haut'}",
        },
    ]


# Colonnes du mémo : (titre, largeur fraction). Somme ≈ 1.
_COLS = [("Évén.", 0.10), ("Rôle", 0.23), ("Vol×", 0.10), ("Spread", 0.07),
         ("OI attendu", 0.16), ("Clôture", 0.11), ("✓ Validé  /  ✗ Invalidé", 0.23)]
_ACCENT = {"accumulation": "#1b6b1b", "distribution": "#a11"}


def _wrap(text: str, frac: float, total_chars: int) -> list[str]:
    width = max(6, int(frac * total_chars))
    out: list[str] = []
    for part in str(text).replace("**", "").split("\n"):
        out += textwrap.wrap(part, width) or [""]
    return out


def build_theory_image(th: Thresholds | None = None,
                       out_path: str = "memo_theorie.png") -> str:
    """Rend le mémo (accumulation + distribution + OI) en PNG et renvoie le chemin."""
    th = th or Thresholds()
    total_chars = 150  # densité de caractères sur toute la largeur (réglage du wrap)

    # 1) Pré-calcule les lignes et la hauteur (en "lignes de texte") de chaque bloc.
    blocks: list[tuple] = [("header",)]
    for bias in ("accumulation", "distribution"):
        blocks.append(("section", bias))
        for r in theory_rows(bias, th):
            cells = [f"{r['ev']} · {r['nom']}", r["role"], r["volx"], r["spread"],
                     r["oi"], r["cloture"], f"✓ {r['valide']}\n✗ {r['invalide']}"]
            wrapped = [_wrap(c, _COLS[i][1], total_chars) for i, c in enumerate(cells)]
            blocks.append(("row", bias, wrapped, max(len(w) for w in wrapped)))

    unit = []  # hauteur de chaque bloc en lignes
    for b in blocks:
        unit.append(1.4 if b[0] == "header" else 1.3 if b[0] == "section" else b[3] + 0.8)
    total = sum(unit)

    # 2) Rendu.
    fig = plt.figure(figsize=(15.5, max(6.0, total * 0.34)))
    ax = fig.add_axes([0.006, 0.01, 0.988, 0.93]); ax.axis("off")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    xs, x = [], 0.0
    for _, frac in _COLS:
        xs.append(x); x += frac

    y, H = 1.0, 1.0 / total
    for b, u in zip(blocks, unit):
        h = u * H
        ytop, ymid, ybot = y, y - 0.5 * (u * H), y - h
        if b[0] == "header":
            ax.add_patch(plt.Rectangle((0, ybot), 1, h, color="#f2f2f2"))
            for i, (name, _) in enumerate(_COLS):
                ax.text(xs[i] + 0.004, ymid, name, va="center", ha="left",
                        fontsize=8.5, weight="bold", color="#333")
            ax.axhline(ybot, color="#444", lw=1.0)
        elif b[0] == "section":
            bias = b[1]
            ax.add_patch(plt.Rectangle((0, ybot), 1, h, color=_ACCENT[bias], alpha=0.12))
            seq = " → ".join(_SEQ[bias])
            ax.text(0.006, ymid, f"{bias.upper()}   ({seq})", va="center", ha="left",
                    fontsize=9.5, weight="bold", color=_ACCENT[bias])
        else:
            bias, wrapped = b[1], b[2]
            for i, _ in enumerate(_COLS):
                col = _ACCENT[bias] if i == 0 else "#222"
                weight = "bold" if i == 0 else "normal"
                ax.text(xs[i] + 0.004, ymid, "\n".join(wrapped[i]), va="center", ha="left",
                        fontsize=7.2, color=col, weight=weight, linespacing=1.15)
            ax.axhline(ybot, color="#e2e2e2", lw=0.5)
        y = ybot

    for x0 in xs[1:]:
        ax.axvline(x0, color="#ededed", lw=0.5)
    seuils = (f"Seuils : climax ×{th.climax_vol} · sos ×{th.sos_vol} · test ×{th.test_vol} · "
              f"spread large {th.wide_spread_atr} ATR · pénétration {th.pen_atr} ATR. "
              f"OI = Open Interest (perp).")
    fig.suptitle("Mémo théorie — Wyckoff + Open Interest", fontsize=13.5, weight="bold", y=0.995)
    fig.text(0.006, 0.965, seuils, fontsize=7.5, color="#666")
    fig.savefig(out_path, dpi=140, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return out_path


if __name__ == "__main__":
    import sys
    out = sys.argv[1] if len(sys.argv) > 1 else "memo_theorie.png"
    print(build_theory_image(out_path=out))
