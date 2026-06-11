"""
theory_table.py — Mémo « Mémo théorie » : rôle et seuils de validité de chaque
événement Wyckoff, en accumulation ET en distribution, **plus le comportement de
l'Open Interest** attendu à chaque étape.

But (préférence Gauthier) : un récap mémorisable, event par event, pour ancrer ce
qui rend un événement *valide ou non* — volume (vol×), spread (ATR), clôture, et OI.
Les seuils sont lus depuis les `Thresholds` courants (jamais en dur).

Sortie : un fichier **HTML autonome cliquable** (`memo_theorie.html`) — table lisible
dans le navigateur.
"""
from __future__ import annotations

import html

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
            "volx": f"≥ ×{th.climax_vol} (climactique, le + fort)",
            "spread": f"≥ {th.wide_spread_atr} ATR (large)",
            "oi": oi("climax"),
            "cloture": f"{cloture} (rejet → absorption)",
            "valide": f"vol climactique + spread large + clôture {cloture}",
            "invalide": "vol non climactique, ou clôture du mauvais côté",
        },
        {
            "ev": "AR",
            "nom": "Automatic Rally" if acc else "Automatic Reaction",
            "role": "Mouvement réflexe (débouclage). Fixe l'autre borne : la plage est posée.",
            "volx": "EN REPLI (< ×1, idéalement < moyenne)",
            "spread": "indifférent (souvent en repli)",
            "oi": oi("ar"),
            "cloture": "indifférente",
            "valide": "volume EN REPLI ET OI EN REPLI (débouclage)",
            "invalide": "AR à fort volume OU OI en hausse → engagement neuf",
        },
        {
            "ev": "ST",
            "nom": "Secondary Test",
            "role": f"Retour sonder le {borne_climax} : {test_creux}.",
            "volx": f"SEC ≤ ×{th.test_vol} (et < climax)",
            "spread": f"ÉTROIT < {th.wide_spread_atr} ATR",
            "oi": oi("st"),
            "cloture": "neutre (pas de débordement)",
            "valide": "volume sec + borne tenue (pas de cassure)",
            "invalide": f"volume élevé (> ×{th.test_vol}) ou cassure nette",
        },
        {
            "ev": "SPRING" if acc else "UTAD",
            "nom": "Spring" if acc else "Upthrust After Distribution",
            "role": f"Phase C — fausse cassure {'sous le plancher' if acc else 'au-dessus du plafond'} "
                    f"(shakeout) puis rejet : déloge les mains faibles.",
            "volx": "modéré (la cassure ne tient pas)",
            "spread": "pic bref possible",
            "oi": oi("spring"),
            "cloture": f"revient DANS la plage (clv {'≥ 0.5' if acc else '≤ 0.5'})",
            "valide": f"pénétration brève ≈ {th.pen_atr} ATR hors borne + clôture rentrée",
            "invalide": "clôture HORS de la plage = vraie cassure",
        },
        {
            "ev": signe,
            "nom": "Sign of Strength" if acc else "Sign of Weakness",
            "role": f"La {'demande' if acc else 'offre'} prend le contrôle : prélude au "
                    f"{'markup (hausse)' if acc else 'markdown (baisse)'}.",
            "volx": f"SOUTENU ≥ ×{th.sos_vol}",
            "spread": f"≥ {th.wide_spread_atr} ATR (large)",
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
            "spread": "étroit (réaction sans engagement)",
            "oi": oi("lp"),
            "cloture": f"{'creux plus HAUT' if acc else 'sommet plus BAS'} que le climax",
            "valide": f"réaction sèche + {'creux' if acc else 'sommet'} qui tient la borne",
            "invalide": f"volume lourd ou {'nouveau plus-bas' if acc else 'nouveau plus-haut'}",
        },
    ]


def _table_html(bias: str, th: Thresholds) -> str:
    acc = bias == "accumulation"
    accent = "#1b6b1b" if acc else "#a11"
    seq = " → ".join(_SEQ[bias])
    head = (f'<h2 style="color:{accent};margin:18px 0 6px">'
            f'{"📈" if acc else "📉"} {bias.upper()} <span style="font-weight:400;'
            f'font-size:.7em;color:#555">({seq})</span></h2>')
    cols = ["Évén.", "Rôle dans la séquence", "Volume (vol×)", "Spread (ATR)",
            "OI attendu", "Clôture", "✅ Validé si", "❌ Invalidé si"]
    th_html = "".join(f"<th>{c}</th>" for c in cols)
    body = ""
    for r in theory_rows(bias, th):
        cells = [
            f'<td class="ev" style="color:{accent}"><b>{r["ev"]}</b><br>'
            f'<span class="full">{html.escape(r["nom"])}</span></td>',
            f'<td>{html.escape(r["role"])}</td>',
            f'<td class="num">{html.escape(r["volx"])}</td>',
            f'<td class="num">{html.escape(r["spread"])}</td>',
            f'<td class="oi">{html.escape(r["oi"])}</td>',
            f'<td>{html.escape(r["cloture"])}</td>',
            f'<td class="ok">{html.escape(r["valide"])}</td>',
            f'<td class="ko">{html.escape(r["invalide"])}</td>',
        ]
        body += "<tr>" + "".join(cells) + "</tr>"
    return f'{head}<table><thead><tr>{th_html}</tr></thead><tbody>{body}</tbody></table>'


def build_theory_html(th: Thresholds | None = None,
                      out_path: str = "memo_theorie.html") -> str:
    """Écrit le mémo HTML (accumulation + distribution + OI) et renvoie le chemin."""
    th = th or Thresholds()
    style = """
    <style>
      body{font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;
           margin:24px;color:#222;background:#fff}
      h1{font-size:1.4em;margin:0 0 4px}
      .sub{color:#666;margin:0 0 14px;font-size:.9em}
      table{border-collapse:collapse;width:100%;margin-bottom:10px;font-size:.86em}
      th,td{border:1px solid #ddd;padding:7px 9px;vertical-align:top;text-align:left}
      th{background:#f4f4f4;font-weight:600}
      td.ev{white-space:nowrap}
      td.ev .full{font-size:.8em;color:#666;font-weight:400}
      td.num{font-variant-numeric:tabular-nums;background:#fafafa}
      td.oi{background:#eef5ff;color:#234}
      td.ok{color:#1b6b1b}
      td.ko{color:#a11}
      tr:nth-child(even) td{background:#fcfcfc}
      tr:nth-child(even) td.oi{background:#e7f0fc}
      .legend{margin-top:8px;font-size:.82em;color:#555}
    </style>"""
    seuils = (f"climax_vol=×{th.climax_vol} · sos_vol=×{th.sos_vol} · "
              f"test_vol=×{th.test_vol} · wide_spread_atr={th.wide_spread_atr} ATR · "
              f"pen_atr={th.pen_atr} ATR · narrow_spread_atr={th.narrow_spread_atr} ATR")
    doc = f"""<!doctype html><html lang="fr"><head><meta charset="utf-8">
    <title>Mémo théorie — Wyckoff + Open Interest</title>{style}</head><body>
    <h1>Mémo théorie — Wyckoff + Open Interest</h1>
    <p class="sub">Rôle, seuils de validité et comportement d'OI de chaque événement.
    Seuils courants : {html.escape(seuils)}</p>
    {_table_html("accumulation", th)}
    {_table_html("distribution", th)}
    <p class="legend">Mémo : <b>climax</b> = volume le plus fort + spread large + clôture
    de rejet (pose une borne) — OI ↑ puis purge. <b>AR</b> = réflexe à volume <i>et OI</i>
    qui retombent (débouclage / short-covering) ; un AR volumique ou à OI montant invalide
    l'épuisement. <b>ST</b> = re-test à volume sec, borne tenue. <b>Spring/UTAD</b> = fausse
    cassure rejetée (shorts/longs piégés). <b>SOS/SOW</b> = signe directionnel à volume
    soutenu + spread large + <b>OI en hausse</b> (argent neuf, pas un simple squeeze).
    <b>LPS/LPSY</b> = back-up sec qui tient la borne. <b>OI</b> = Open Interest (perp).</p>
    </body></html>"""
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(doc)
    return out_path


if __name__ == "__main__":
    import sys
    out = sys.argv[1] if len(sys.argv) > 1 else "memo_theorie.html"
    print(build_theory_html(out_path=out))
