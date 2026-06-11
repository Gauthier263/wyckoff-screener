"""
theory_table.py — Mémo « rappel théorie » : rôle et seuils de validité de chaque
événement Wyckoff, en accumulation ET en distribution.

But (préférence Gauthier) : un récap mémorisable, event par event, pour ancrer ce
qui rend un événement *valide ou non* — surtout en termes de volume (vol×) et de
spread (en ATR). Les seuils sont lus depuis les `Thresholds` courants pour rester
synchronisés avec la config / l'optimiseur ; aucune valeur en dur.

Sortie : un fichier HTML autonome (table cliquable, lisible dans le navigateur).
"""
from __future__ import annotations

import html

from .events import Thresholds

# Ordre canonique des séquences.
_SEQ = {
    "accumulation": ["SC", "AR", "ST", "SOS"],
    "distribution": ["BC", "AR", "ST", "SOW"],
}

_FULLNAME = {
    "SC": "Selling Climax", "AR_acc": "Automatic Rally", "ST": "Secondary Test",
    "SOS": "Sign of Strength", "BC": "Buying Climax", "AR_dist": "Automatic Reaction",
    "SOW": "Sign of Weakness",
}


def _rows(bias: str, th: Thresholds) -> list[dict]:
    """Construit les lignes du tableau pour un schéma, à partir des seuils courants."""
    acc = bias == "accumulation"
    borne_climax = "plancher" if acc else "plafond"
    borne_ar = "plafond" if acc else "plancher"
    cloture = "haute" if acc else "basse"
    clv_dir = "≥ 0.6 (haute)" if acc else "≤ 0.4 (basse)"
    test_creux = "creux idéalement plus haut" if acc else "sommet idéalement plus bas"
    climax_name = "SC" if acc else "BC"
    signe = "SOS" if acc else "SOW"

    return [
        {
            "ev": climax_name,
            "nom": _FULLNAME[climax_name],
            "role": f"Apogée du mouvement : la pression {'vendeuse' if acc else 'acheteuse'} "
                    f"euphorique est absorbée par les mains fortes. Fixe le {borne_climax}.",
            "volx": f"≥ ×{th.climax_vol} (climactique, le + fort de la séquence)",
            "spread": f"≥ {th.wide_spread_atr} ATR (large)",
            "cloture": f"{cloture} (rejet → absorption)",
            "valide": f"volume climactique + spread large + clôture {cloture}",
            "invalide": "volume non climactique, ou clôture du mauvais côté (pas de rejet)",
        },
        {
            "ev": "AR",
            "nom": _FULLNAME["AR_acc"] if acc else _FULLNAME["AR_dist"],
            "role": f"Mouvement réflexe une fois la partie épuisée. Fixe le {borne_ar} : "
                    "les deux bornes de la plage sont posées.",
            "volx": "EN NETTE BAISSE (idéalement < moyenne, ×< 1)",
            "spread": "indifférent (souvent en repli)",
            "cloture": "indifférente",
            "valide": "volume qui retombe (confirme l'épuisement)",
            "invalide": "AR à FORT volume → épuisement non confirmé, structure douteuse",
        },
        {
            "ev": "ST",
            "nom": _FULLNAME["ST"],
            "role": f"Retour sonder le {borne_climax} pour vérifier que la pression s'est "
                    f"tarie : {test_creux}.",
            "volx": f"SEC ≤ ×{th.test_vol} (et < climax)",
            "spread": f"ÉTROIT < {th.wide_spread_atr} ATR",
            "cloture": "neutre (peu importe, pas de débordement)",
            "valide": "volume sec + borne tenue (pas de nouveau débordement franc)",
            "invalide": f"volume élevé (> ×{th.test_vol}) ou cassure nette de la borne",
        },
        {
            "ev": "SPRING" if acc else "UTAD",
            "nom": "Spring" if acc else "Upthrust After Distribution",
            "role": f"Phase C — fausse cassure {'sous le plancher' if acc else 'au-dessus du plafond'} "
                    f"(shakeout) puis rejet : déloge les mains faibles avant le signe directionnel.",
            "volx": "modéré (la cassure ne tient pas)",
            "spread": "pic bref possible",
            "cloture": f"revient DANS la plage (clv {'≥ 0.5' if acc else '≤ 0.5'} = rejet)",
            "valide": f"pénétration brève ≈ {th.pen_atr} ATR hors borne + clôture rentrée",
            "invalide": "clôture HORS de la plage = vraie cassure (pas un piège)",
        },
        {
            "ev": signe,
            "nom": _FULLNAME[signe],
            "role": f"La {'demande' if acc else 'offre'} prend le contrôle : "
                    f"prélude à la phase de {'hausse (markup)' if acc else 'baisse (markdown)'}.",
            "volx": f"SOUTENU ≥ ×{th.sos_vol}",
            "spread": f"≥ {th.wide_spread_atr} ATR (large)",
            "cloture": f"{cloture} — clv {clv_dir}",
            "valide": f"volume soutenu + spread large + clôture {cloture}",
            "invalide": "volume faible ou clôture molle (clv au mauvais bout)",
        },
        {
            "ev": "LPS" if acc else "LPSY",
            "nom": "Last Point of Support" if acc else "Last Point of Supply",
            "role": f"Phase D — back-up après le signe : dernier "
                    f"{'appui' if acc else 'rebond'} avant le {'markup' if acc else 'markdown'}.",
            "volx": f"SEC ≤ ×{th.test_vol}",
            "spread": "étroit (réaction sans engagement)",
            "cloture": f"{'creux plus HAUT' if acc else 'sommet plus BAS'} que le climax",
            "valide": f"réaction sèche + {'creux qui tient le support' if acc else 'sommet qui tient la résistance'}",
            "invalide": f"volume lourd ou {'nouveau plus-bas sous le plancher' if acc else 'nouveau plus-haut au-dessus du plafond'}",
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
            "Clôture", "✅ Validé si", "❌ Invalidé si"]
    th_html = "".join(f"<th>{c}</th>" for c in cols)
    body = ""
    for r in _rows(bias, th):
        cells = [
            f'<td class="ev" style="color:{accent}"><b>{r["ev"]}</b><br>'
            f'<span class="full">{html.escape(r["nom"])}</span></td>',
            f'<td>{html.escape(r["role"])}</td>',
            f'<td class="num">{html.escape(r["volx"])}</td>',
            f'<td class="num">{html.escape(r["spread"])}</td>',
            f'<td>{html.escape(r["cloture"])}</td>',
            f'<td class="ok">{html.escape(r["valide"])}</td>',
            f'<td class="ko">{html.escape(r["invalide"])}</td>',
        ]
        body += "<tr>" + "".join(cells) + "</tr>"
    return f'{head}<table><thead><tr>{th_html}</tr></thead><tbody>{body}</tbody></table>'


def build_theory_html(th: Thresholds | None = None,
                      out_path: str = "tableau_rappel_theorie.html") -> str:
    """Écrit le mémo HTML (accumulation + distribution) et renvoie le chemin."""
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
      td.ok{color:#1b6b1b}
      td.ko{color:#a11}
      tr:nth-child(even) td{background:#fcfcfc}
      .legend{margin-top:8px;font-size:.82em;color:#555}
    </style>"""
    seuils = (f"climax_vol=×{th.climax_vol} · sos_vol=×{th.sos_vol} · "
              f"test_vol=×{th.test_vol} · wide_spread_atr={th.wide_spread_atr} ATR · "
              f"narrow_spread_atr={th.narrow_spread_atr} ATR")
    doc = f"""<!doctype html><html lang="fr"><head><meta charset="utf-8">
    <title>Tableau rappel théorie — Wyckoff</title>{style}</head><body>
    <h1>Tableau rappel théorie — Wyckoff</h1>
    <p class="sub">Rôle et seuils de validité de chaque événement. Seuils courants :
    {html.escape(seuils)}</p>
    {_table_html("accumulation", th)}
    {_table_html("distribution", th)}
    <p class="legend">Mémo : <b>climax</b> = volume le plus fort + spread large + clôture
    de rejet (pose une borne). <b>AR</b> = réflexe à volume qui retombe (pose l'autre
    borne) ; un AR volumique invalide l'épuisement. <b>ST</b> = re-test à volume sec,
    borne tenue. <b>SOS/SOW</b> = signe directionnel à volume soutenu + spread large,
    clôture du bon côté → déclencheur.</p>
    </body></html>"""
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(doc)
    return out_path


if __name__ == "__main__":
    import sys
    out = sys.argv[1] if len(sys.argv) > 1 else "tableau_rappel_theorie.html"
    print(build_theory_html(out_path=out))
