"""
theory_table.py — Mémo « Mémo théorie » V2 : référentiel Wyckoff complet et
mémorisable.

Sortie : un fichier **HTML autonome cliquable** (`memo_theorie.html`), structuré en
quatre blocs :
  0. **Fondations** — les 3 lois de Wyckoff, l'opérateur composite, les phases A→E,
     la hiérarchie de lecture (volume → OI → tierces, CVD en tête des tierces).
  1. **Tables de référence** — accumulation ET distribution : rôle, seuils de validité
     (vol×, spread/ATR, clôture), comportement d'**OI** et de **CVD** attendu par event.
  2. **Narratif par événement** — une fiche détaillée par event : ce qui se passe, qui
     est en jeu, la psychologie, et la répercussion sur CHAQUE indice (vol×, spread/ATR,
     CLV, OI, CVD, tierces).
  3. **Théorie par indice** — une fiche par indicateur : définition, calcul, ce qu'il
     mesure, son rôle dans la hiérarchie, ce qui est attendu à chaque event, ses pièges.

But (préférence Gauthier) : comprendre le *narratif* de chaque événement et son lien
avec les indices attendus, pour développer des automatismes de lecture. Les seuils sont
lus depuis les `Thresholds` courants (jamais en dur).
"""
from __future__ import annotations

import html

from .events import Thresholds

_SEQ = {
    "accumulation": ["PS", "SC", "AR", "ST", "SPRING", "SOS", "LPS"],
    "distribution": ["PSY", "BC", "AR", "ST", "UTAD", "SOW", "LPSY"],
}

# Comportement d'OI attendu (texte mémo) par schéma + type d'événement.
_OI = {
    ("accumulation", "climax"): "purge du levier — net AMBIGU (shorts neufs ↑ vs longs liquidés ↓)",
    ("accumulation", "ar"): "↓ short covering (rebond SANS engagement neuf)",
    ("accumulation", "st"): "plat / ↓ (offre tarie)",
    ("accumulation", "spring"): "↑ sur la mèche puis ↓ (shorts piégés → squeeze)",
    ("accumulation", "sign"): "↑ avec le prix (longs neufs = markup réel)",
    ("accumulation", "lp"): "plat (back-up sain)",
    ("distribution", "climax"): "purge du levier — net AMBIGU (longs FOMO ↑ vs shorts liquidés ↓)",
    ("distribution", "ar"): "↓ longs liquidés (repli SANS engagement neuf)",
    ("distribution", "st"): "plat / ↓ (demande tarie)",
    ("distribution", "spring"): "↑ au-dessus puis ↓ (longs piégés → squeeze)",
    ("distribution", "sign"): "↑ avec la baisse (shorts neufs = markdown réel)",
    ("distribution", "lp"): "plat (rebond faible)",
}

# Comportement de CVD (flux d'ordres agressifs) attendu par schéma + type d'événement.
_CVD = {
    ("accumulation", "climax"): "↓ FORT (vente agressive) MAIS prix récupère = absorption au plancher",
    ("accumulation", "ar"): "modéré (réflexe/covering, pas de demande agressive)",
    ("accumulation", "st"): "plat / sec (offre tarie, aucune agression)",
    ("accumulation", "spring"): "pic ↓ sur la mèche puis récupération = absorption, shorts piégés",
    ("accumulation", "sign"): "↑ FRANC (demande agressive) — sinon faux SOS / covering",
    ("accumulation", "lp"): "plat / sec (back-up sain, sans agression)",
    ("distribution", "climax"): "↑ FORT (achat agressif/FOMO) MAIS prix cale = absorption au plafond",
    ("distribution", "ar"): "modéré (réflexe/liquidation, pas d'offre agressive)",
    ("distribution", "st"): "plat / sec (demande tarie, aucune agression)",
    ("distribution", "spring"): "prix↑ MAIS CVD plat / divergent = pas de demande = piège confirmé",
    ("distribution", "sign"): "↓ FRANC (offre agressive) — sinon faux SOW / covering",
    ("distribution", "lp"): "plat / sec (rebond faible, sans agression)",
}


def theory_rows(bias: str, th: Thresholds) -> list[dict]:
    """Lignes du mémo pour un schéma, à partir des seuils courants (OI + CVD)."""
    acc = bias == "accumulation"
    borne_climax = "plancher" if acc else "plafond"
    cloture = "haute" if acc else "basse"
    clv_dir = "≥ 0.6 (haute)" if acc else "≤ 0.4 (basse)"
    test_creux = "creux idéalement plus haut" if acc else "sommet idéalement plus bas"
    climax_name = "SC" if acc else "BC"
    prelim_name = "PS" if acc else "PSY"
    signe = "SOS" if acc else "SOW"

    def oi(kind):
        return _OI[(bias, kind)]

    def cvd(kind):
        return _CVD[(bias, kind)]

    return [
        {
            "ev": prelim_name,
            "nom": "Preliminary Support" if acc else "Preliminary Supply",
            "role": f"Premier signe que les mains fortes {'achètent' if acc else 'vendent'} "
                    f"dans {'la baisse' if acc else 'la hausse'} : le mouvement commence à "
                    f"ralentir. Avertissement, pas encore le climax.",
            "volx": "en hausse (participation qui monte)",
            "spread": "qui s'élargit (premiers à-coups)",
            "oi": "premiers " + ("longs" if acc else "shorts") + " qui se positionnent",
            "cvd": "première agression " + ("acheteuse" if acc else "vendeuse") + " visible",
            "cloture": "indécise (le combat commence)",
            "valide": "ralentissement du mouvement + pic de volume isolé",
            "invalide": "le mouvement continue sans réaction = pas encore de PS/PSY",
        },
        {
            "ev": climax_name,
            "nom": "Selling Climax" if acc else "Buying Climax",
            "role": f"Apogée du mouvement : pression {'vendeuse' if acc else 'acheteuse'} "
                    f"panique absorbée par les mains fortes. Fixe le {borne_climax}.",
            "volx": f"≥ ×{th.climax_vol} (climactique, le + fort)",
            "spread": f"≥ {th.wide_spread_atr} ATR (large)",
            "oi": oi("climax"),
            "cvd": cvd("climax"),
            "cloture": f"{cloture} (rejet → absorption)",
            "valide": f"vol climactique + spread large + clôture {cloture} + absorption CVD",
            "invalide": "vol non climactique, ou clôture du mauvais côté",
        },
        {
            "ev": "AR",
            "nom": "Automatic Rally" if acc else "Automatic Reaction",
            "role": "Mouvement réflexe (débouclage). Fixe l'autre borne : la plage est posée.",
            "volx": "EN REPLI (< ×1, idéalement < moyenne)",
            "spread": "indifférent (souvent en repli)",
            "oi": oi("ar"),
            "cvd": cvd("ar"),
            "cloture": "indifférente",
            "valide": "volume EN REPLI ET OI EN REPLI (débouclage), CVD modeste",
            "invalide": "AR à fort volume OU OI en hausse OU CVD franc → engagement neuf",
        },
        {
            "ev": "ST",
            "nom": "Secondary Test",
            "role": f"Retour sonder le {borne_climax} : {test_creux}.",
            "volx": f"SEC ≤ ×{th.test_vol} (et < climax)",
            "spread": f"étroit ≤ {th.narrow_spread_atr} ATR (pas large)",
            "oi": oi("st"),
            "cvd": cvd("st"),
            "cloture": "neutre (pas de débordement)",
            "valide": "volume sec + borne tenue + CVD plat (pas d'agression)",
            "invalide": f"volume élevé (> ×{th.test_vol}) ou cassure nette",
        },
        {
            "ev": "SPRING" if acc else "UTAD",
            "nom": "Spring / Shakeout" if acc else "Upthrust After Distribution",
            "role": f"Phase C — fausse cassure {'sous le plancher' if acc else 'au-dessus du plafond'} "
                    f"(shakeout) puis rejet : déloge et piège les mains faibles.",
            "volx": "modéré→fort (mais la cassure ne tient pas)",
            "spread": "pic bref possible",
            "oi": oi("spring"),
            "cvd": cvd("spring"),
            "cloture": f"revient DANS la plage (clv {'≥ 0.5' if acc else '≤ 0.5'})",
            "valide": f"pénétration brève ≈ {th.pen_atr} ATR hors borne + clôture rentrée"
                      + (" + absorption CVD" if acc else " + CVD divergent (pas de demande)"),
            "invalide": "clôture HORS de la plage = vraie cassure (pas un piège)",
        },
        {
            "ev": signe,
            "nom": "Sign of Strength" if acc else "Sign of Weakness",
            "role": f"Phase D — la {'demande' if acc else 'offre'} prend le contrôle : prélude "
                    f"au {'markup (hausse)' if acc else 'markdown (baisse)'}.",
            "volx": f"SOUTENU ≥ ×{th.sos_vol}",
            "spread": f"≥ {th.wide_spread_atr} ATR (large)",
            "oi": oi("sign"),
            "cvd": cvd("sign"),
            "cloture": f"{cloture} — clv {clv_dir}",
            "valide": f"vol soutenu + spread large + clôture {cloture} + OI↑ + CVD franc",
            "invalide": "vol faible / clôture molle / OI plat / CVD divergent (= squeeze/covering)",
        },
        {
            "ev": "LPS" if acc else "LPSY",
            "nom": "Last Point of Support" if acc else "Last Point of Supply",
            "role": f"Phase D — back-up après le signe : dernier "
                    f"{'appui' if acc else 'rebond'} avant le {'markup' if acc else 'markdown'}.",
            "volx": f"SEC ≤ ×{th.test_vol}",
            "spread": "étroit (réaction sans engagement)",
            "oi": oi("lp"),
            "cvd": cvd("lp"),
            "cloture": f"{'creux plus HAUT' if acc else 'sommet plus BAS'} que le climax",
            "valide": f"réaction sèche + {'creux' if acc else 'sommet'} qui tient la borne + CVD sec",
            "invalide": f"volume lourd ou {'nouveau plus-bas' if acc else 'nouveau plus-haut'}",
        },
    ]


# ─────────────────────────────────────────────────────────────────────────────
# Bloc 0 — Fondations
# ─────────────────────────────────────────────────────────────────────────────
def _foundations_html(th: Thresholds) -> str:
    laws = [
        ("Loi de l'offre et de la demande",
         "Le prix monte quand la demande dépasse l'offre, baisse dans le cas inverse. "
         "Tout l'enjeu est de <b>lire le déséquilibre</b> avant qu'il ne se voie dans le prix — "
         "c'est ce que mesurent volume, OI et CVD."),
        ("Loi de l'effort vs résultat",
         "Le <b>volume est l'effort</b>, le <b>mouvement du prix est le résultat</b>. "
         "Quand l'effort est gros mais le résultat faible (gros volume, prix qui n'avance pas) = "
         "<b>absorption</b> : une main forte agit contre le mouvement apparent. C'est le cœur du VSA, "
         "et ce que le <b>CVD</b> rend visible (agression sans résultat = absorbée)."),
        ("Loi de cause et effet",
         "La durée/ampleur d'une plage (la <b>cause</b>, l'accumulation ou la distribution) détermine "
         "l'ampleur du mouvement qui suit (l'<b>effet</b>, markup ou markdown). Une grande plage "
         "construit une grande cause."),
    ]
    laws_html = "".join(
        f'<div class="card"><h4>{i+1}. {t}</h4><p>{d}</p></div>'
        for i, (t, d) in enumerate(laws))

    phases = [
        ("Phase A — Arrêt", "PS/PSY → climax (SC/BC) → AR → ST. La tendance précédente s'arrête, "
         "la plage se pose (les deux bornes sont fixées)."),
        ("Phase B — Construction", "La « cause » se construit : allers-retours dans la plage, les mains "
         "fortes accumulent/distribuent. Tests répétés des bornes, volume globalement en repli."),
        ("Phase C — Test", "Le piège : <b>Spring</b> (accu, sous le plancher) ou <b>UTAD</b> (distrib, "
         "au-dessus du plafond). Fausse cassure qui déloge les mains faibles avant le vrai mouvement. "
         "<i>Non obligatoire</i> : une plage peut passer par un simple test de la borne, sans spring/upthrust."),
        ("Phase D — Confirmation", "La direction s'affirme : <b>SOS/SOW</b> puis <b>LPS/LPSY</b>. "
         "L'argent neuf entre (OI↑, CVD franc). Série de creux montants (accu) ou sommets descendants (distrib)."),
        ("Phase E — Tendance", "Hors de la plage : <b>markup</b> (hausse) ou <b>markdown</b> (baisse). "
         "La cause se transforme en effet."),
    ]
    phases_html = "".join(
        f'<tr><td class="ev"><b>{html.escape(p)}</b></td><td>{d}</td></tr>'
        for p, d in phases)

    hierarchy = (
        "<b>Toute lecture de suivi respecte cet ordre strict :</b>"
        "<ol>"
        "<li><b>Volume + spread</b> (force primaire) — effort vs résultat sur la barre. "
        "On lit ça <i>en premier</i> et on forme l'hypothèse.</li>"
        "<li><b>Open Interest</b> (coin) — le volume ouvre-t-il ou ferme-t-il des positions ? "
        "Désambiguïse qui agit (longs neufs / shorts neufs / covering / liquidation).</li>"
        "<li><b>Tierces</b>, lues <i>en second temps</i> et <b>à froid</b> pour valider/affaiblir "
        "l'hypothèse (jamais pour forcer le consensus). Dans l'ordre : "
        "<b>CVD</b> (absorption, en tête car flux agressif), puis funding / ratio L-S / liquidations "
        "(positionnement).</li>"
        "</ol>"
        "<b>Règle d'or</b> : ne jamais sauter au tertiaire avant d'avoir lu volume puis OI. Une tierce "
        "qui contredit l'hypothèse <i>est</i> un signal (risque/invalidation), pas un bruit à gommer."
    )

    composite = (
        "L'<b>opérateur composite</b> (Composite Man de Wyckoff) est une fiction utile : on raisonne "
        "comme si un seul gros acteur rationnel (mains fortes / smart money) orchestrait accumulation "
        "et distribution face à la foule (mains faibles, retail). Il <b>accumule bas</b> dans la panique "
        "(achète le SC), fait <b>monter</b> (markup), <b>distribue haut</b> dans l'euphorie (vend le BC), "
        "puis fait <b>baisser</b> (markdown). Chaque événement Wyckoff est une trace de son action : le "
        "climax = il absorbe la capitulation ; le Spring/UTAD = il piège les mains faibles ; le SOS/SOW = "
        "il s'engage enfin dans le sens qu'il a préparé. <b>Lire Wyckoff = suivre ses traces dans le "
        "volume, l'OI et le CVD.</b>"
    )

    return f"""
    <section id="fondations">
      <h2>0 · Fondations</h2>

      <h3>L'opérateur composite (le « pourquoi » de tout)</h3>
      <p>{composite}</p>

      <h3>Les 3 lois de Wyckoff</h3>
      <div class="cards">{laws_html}</div>

      <h3>Le cycle &amp; les phases A→E</h3>
      <p class="muted">Cycle de marché : <b>Accumulation</b> (plage basse) →
      <b>Markup</b> (hausse) → <b>Distribution</b> (plage haute) → <b>Markdown</b> (baisse) → …
      La distribution est le miroir de l'accumulation (mêmes événements, sens inversé).</p>
      <table><tbody>{phases_html}</tbody></table>

      <h3>Hiérarchie de lecture : volume → OI → tierces (CVD en tête)</h3>
      <p>{hierarchy}</p>
      <p class="muted"><b>Note de méthode (honnêteté théorique).</b> Wyckoff classique ne lit que
      <b>PRIX + VOLUME</b> (l'œuvre est antérieure aux marchés à terme/perps). L'<b>OI</b>, le
      <b>CVD</b> et les <b>tierces</b> (funding, ratio L/S, liquidations) sont des <b>extensions
      modernes</b> — des modèles cohérents avec la logique de Wyckoff (suivre l'opérateur composite),
      mais PAS de la doctrine d'origine. Leurs « comportements attendus » par événement sont des
      heuristiques raisonnées, à traiter comme des confirmations <i>à froid</i>, jamais comme des
      vérités absolues.</p>

      <h3 id="topdown">Garde-fous de cadre (à ne jamais oublier)</h3>
      <ul>
        <li><b>Top-down</b> : établir le contexte macro (tendance HTF, position de la plage)
        AVANT d'étiqueter. Une plage dans un downtrend = <b>redistribution par défaut</b>
        jusqu'à preuve du contraire.</li>
        <li><b>Fractal</b> : chaque TF a son schéma complet. Une bougie peut être un événement
        local ET un simple test sur la TF supérieure — déclarer la TF/structure avant d'étiqueter.</li>
        <li><b>AR/ST ancrés sur le climax</b> : l'AR part dans le sens <i>opposé</i> au climax ;
        l'ST <i>reteste</i> le climax. En distribution (climax = BC haut), l'AR réagit vers le BAS
        (borne basse) et l'ST teste vers le HAUT (borne haute). Ne jamais mélanger la grammaire
        d'accumulation dans un cadre distribution.</li>
        <li><b>OI en COIN</b>, jamais en USD (l'USD conflate positions et prix).</li>
      </ul>
    </section>"""


# ─────────────────────────────────────────────────────────────────────────────
# Bloc 1 — Tables de référence
# ─────────────────────────────────────────────────────────────────────────────
def _table_html(bias: str, th: Thresholds) -> str:
    acc = bias == "accumulation"
    accent = "#1b6b1b" if acc else "#a11"
    seq = " → ".join(_SEQ[bias])
    head = (f'<h3 style="color:{accent};margin:18px 0 6px">'
            f'{"▲" if acc else "▼"} {bias.upper()} <span style="font-weight:400;'
            f'font-size:.7em;color:#555">({seq})</span></h3>')
    cols = ["Évén.", "Rôle dans la séquence", "Volume (vol×)", "Spread (ATR)",
            "OI attendu", "CVD attendu", "Clôture", "✅ Validé si", "❌ Invalidé si"]
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
            f'<td class="cvd">{html.escape(r["cvd"])}</td>',
            f'<td>{html.escape(r["cloture"])}</td>',
            f'<td class="ok">{html.escape(r["valide"])}</td>',
            f'<td class="ko">{html.escape(r["invalide"])}</td>',
        ]
        body += "<tr>" + "".join(cells) + "</tr>"
    return f'{head}<table><thead><tr>{th_html}</tr></thead><tbody>{body}</tbody></table>'


def _tables_section(th: Thresholds) -> str:
    return f"""
    <section id="tables">
      <h2>1 · Tables de référence (accumulation &amp; distribution)</h2>
      <p class="muted">Confronter chaque observation à ces seuils : c'est le « validé / ambigu /
      non validé » event par event. Les colonnes OI et CVD donnent la signature de flux attendue.</p>
      {_table_html("accumulation", th)}
      {_table_html("distribution", th)}
    </section>"""


# ─────────────────────────────────────────────────────────────────────────────
# Bloc 2 — Narratif détaillé par événement
# ─────────────────────────────────────────────────────────────────────────────
def _event_narratives(th: Thresholds) -> list[dict]:
    """Fiches détaillées. Chaque fiche : récit + tableau indice→attendu→pourquoi."""
    return [
        # ── ACCUMULATION ────────────────────────────────────────────────────
        {
            "id": "ps", "schema": "accumulation", "phase": "Phase A",
            "title": "PS — Preliminary Support (Soutien préliminaire)",
            "story":
                "Après un long markdown, les premières mains fortes commencent à acheter. Le marché "
                "ne retourne pas encore — c'est un <b>avertissement</b> que la baisse fatigue. La foule "
                "est encore vendeuse/short et pessimiste ; les mains fortes profitent de cette offre "
                "abondante pour prendre leurs premières positions sans faire monter le prix.",
            "who":
                "Mains fortes = premiers acheteurs discrets. Foule = encore short/vendeuse, en gain sur "
                "la baisse, persuadée que ça continue.",
            "indices": [
                ("Volume", "en hausse, premiers pics", "la participation augmente : des acheteurs absorbent l'offre"),
                ("Spread/ATR", "qui s'élargit ponctuellement", "premiers à-coups, le calme du markdown se rompt"),
                ("CLV", "des clôtures qui commencent à remonter", "les acheteurs reprennent le contrôle de certaines barres"),
                ("OI", "premiers longs qui se positionnent (ou shorts qui allègent)", "de l'argent neuf entre côté achat"),
                ("CVD", "première agression acheteuse visible", "des market-buys soutiennent le prix, la baisse ralentit"),
                ("Tierces", "funding très négatif, crowd short", "le pessimisme extrême = carburant haussier latent"),
            ],
            "trap": "Ne pas confondre avec un simple palier : le PS n'est validé qu'avec un pic de volume "
                    "isolé et un ralentissement net. Il PRÉCÈDE le climax, il ne le remplace pas.",
        },
        {
            "id": "sc", "schema": "accumulation", "phase": "Phase A",
            "title": "SC — Selling Climax (Climax vendeur)",
            "story":
                "Le sommet de la panique. La capitulation des mains faibles est maximale : tout le monde "
                "vend en même temps, souvent sur une mèche violente. <b>Les mains fortes absorbent</b> "
                "cette avalanche d'offre — elles achètent tout ce qui se vend. Le prix plonge puis "
                "<b>récupère dans la même barre</b> (clôture loin du bas) : c'est la signature de "
                "l'absorption. Le SC <b>fixe le plancher</b> de la future plage.",
            "who":
                "Mains faibles = capitulent (vente panique, stops déclenchés, longs liquidés). Mains "
                "fortes = absorbent agressivement au plancher.",
            "indices": [
                ("Volume", f"≥ ×{th.climax_vol} (climactique, le + fort de la séquence)",
                 "effort vendeur maximal — mais c'est justement là que l'absorption se produit"),
                ("Spread/ATR", f"≥ {th.wide_spread_atr} ATR, très large",
                 "amplitude énorme = capitulation, le prix parcourt une grande distance"),
                ("CLV", f"≥ reclaim_clv ({th.reclaim_clv}) : clôture moitié haute",
                 "le prix récupère DANS la barre = absorption visible (effort vs résultat). Une clôture sur le bas n'est pas encore validée SC par le détecteur : l'absorption se lira alors sur l'AR"),
                ("OI", "purge du levier, net ambigu (shorts neufs ↑ vs longs liquidés ↓)",
                 "le bas attire de nouveaux shorts (piégés) ET flush les derniers longs ; le NET dépend de qui domine — un deleveraging fait BAISSER l'OI, des shorts agressifs le font MONTER. Lire avec les tierces"),
                ("CVD", "↓ FORT (vente agressive massive) MAIS prix qui récupère",
                 "L'ABSORPTION par excellence : énorme agression vendeuse sans résultat baissier durable"),
                ("Tierces", "funding négatif, longs liquidés massifs, crowd short",
                 "flush forcé des longs + shorts encombrés = base d'un futur squeeze"),
            ],
            "trap": "Un climax SANS absorption (clôture sur le bas, clv faible, pas de récupération) n'est "
                    "pas un SC mais une continuation : la capitulation n'a pas trouvé d'acheteur. Attendre "
                    "l'AR pour confirmer que le plancher tient.",
        },
        {
            "id": "ar-acc", "schema": "accumulation", "phase": "Phase A",
            "title": "AR — Automatic Rally (Rallye automatique)",
            "story":
                "Une fois la vente épuisée au SC, le prix <b>rebondit mécaniquement</b> : plus personne "
                "pour vendre, les shorts du markdown rachètent leurs positions (short covering). Ce n'est "
                "PAS de la demande convaincue — c'est un réflexe. L'AR <b>fixe le plafond</b> de la plage. "
                "Avec le SC, les deux bornes sont posées.",
            "who":
                "Shorts qui couvrent (rachètent) + quelques acheteurs réflexes. PAS encore d'engagement "
                "directionnel des mains fortes.",
            "indices": [
                ("Volume", "EN REPLI (< moyenne)", "un rebond réflexe ne mobilise pas de gros volume ; s'il est volumique, c'est un SOS, pas un AR"),
                ("Spread/ATR", "souvent en repli", "mouvement moins violent que le climax"),
                ("CLV", "indifférente", "le rebond peut clôturer haut sans signifier de la vraie demande"),
                ("OI", "↓ short covering : les shorts ferment", "preuve que le rebond est un débouclage, pas de l'argent neuf"),
                ("CVD", "modéré (covering, pas de demande agressive)", "la hausse est portée par le rachat des shorts (covering), pas par une demande agressive nouvelle"),
                ("Tierces", "short liqs possibles sur le rebond", "les shorts trop tôt se font sortir, alimentant le rebond"),
            ],
            "trap": "Un AR à fort volume OU à OI montant n'est PAS un AR : c'est déjà un signe de force "
                    "(des longs s'engagent). NB théorie : classiquement l'AR peut être un rallye "
                    "VIGOUREUX — son essence est l'épuisement vendeur + le réflexe/covering, pas le "
                    "« faible volume » ; le critère volume-en-repli + OI-en-repli est le filtre "
                    "OPÉRATIONNEL du screener pour le distinguer d'un SOS.",
        },
        {
            "id": "st-acc", "schema": "accumulation", "phase": "Phase A/B",
            "title": "ST — Secondary Test (Test secondaire)",
            "story":
                "Le prix <b>revient sonder le plancher</b> (la zone du SC) pour vérifier que l'offre est "
                "épuisée. Idéalement il fait un <b>creux plus haut</b> sur un <b>volume sec</b> : plus "
                "personne ne veut vendre à ce niveau. C'est la validation que le plancher tient et que la "
                "Phase B (construction) peut se dérouler.",
            "who":
                "Vendeurs résiduels (faibles) vs absence d'offre. Les mains fortes observent que le "
                "marché ne baisse plus malgré le test.",
            "indices": [
                ("Volume", f"SEC ≤ ×{th.test_vol} (et < climax)", "l'offre est tarie : peu de transactions pour faire baisser"),
                ("Spread/ATR", f"ÉTROIT < {th.narrow_spread_atr} ATR", "petit range = pas de pression, le marché s'assèche"),
                ("CLV", "neutre, pas de débordement", "ni capitulation ni euphorie : équilibre"),
                ("OI", "plat / ↓ (offre tarie)", "pas de nouvel engagement vendeur"),
                ("CVD", "plat / sec (aucune agression)", "personne n'attaque le plancher de façon agressive"),
                ("Tierces", "funding qui se normalise", "le pessimisme extrême se dégonfle doucement"),
            ],
            "trap": "Un ST à volume élevé ou qui casse nettement le plancher invalide le test : l'offre "
                    "n'est pas épuisée. Plusieurs ST peuvent se succéder en Phase B.",
        },
        {
            "id": "spring", "schema": "accumulation", "phase": "Phase C",
            "title": "SPRING / Shakeout (Ressort)",
            "story":
                "Le <b>piège final</b> avant la hausse. Le prix casse brièvement <b>sous le plancher</b> "
                "pour déclencher les stops des longs et attirer de nouveaux shorts (qui croient à la "
                "cassure baissière), puis <b>récupère vite dans la plage</b>. Les mains fortes ramassent "
                "la liquidité offerte par les mains faibles délogées. C'est le test ultime de l'offre : "
                "si personne ne suit la cassure, la voie est libre pour le markup.",
            "who":
                "Mains faibles = stoppées (longs) ou piégées (nouveaux shorts). Mains fortes = absorbent "
                "le shakeout et déclenchent ensuite le squeeze.",
            "indices": [
                ("Volume", "modéré→fort, mais la cassure NE TIENT PAS", "faible volume + pénétration minime = le plus haussier (offre épuisée) ; un shakeout à fort volume qui récupère reste valide mais demande confirmation"),
                ("Spread/ATR", "pic bref possible sur la mèche", "le mouvement de piège peut être violent mais éphémère"),
                ("CLV", f"clôture qui revient DANS la plage (clv ≥ {th.reclaim_clv})", "le rejet de la cassure = la signature du spring"),
                ("OI", "↑ sur la mèche (shorts piégés) puis ↓ (squeeze)", "les nouveaux shorts de la cassure se font liquider en remontant"),
                ("CVD", "pic ↓ sur la mèche puis récupération = absorption", "vente agressive sur la cassure absorbée → shorts piégés"),
                ("Tierces", "short liqs sur la récupération, funding qui peut passer négatif", "le squeeze des shorts piégés alimente la reprise"),
            ],
            "trap": "Si la clôture reste SOUS le plancher (clv faible, pas de récupération), ce n'est pas "
                    "un spring mais une VRAIE cassure : la redistribution gagne. Tout l'art est de "
                    "distinguer le piège (rejet rapide + absorption CVD) de la cassure (suivi vendeur).",
        },
        {
            "id": "sos", "schema": "accumulation", "phase": "Phase D",
            "title": "SOS — Sign of Strength / Jump Across the Creek",
            "story":
                "La <b>demande prend enfin le contrôle</b>. Le prix franchit la résistance de la plage "
                "(le « creek ») sur un <b>volume soutenu, un spread large, une clôture haute</b>. C'est le "
                "premier vrai signe que les mains fortes s'engagent : de l'argent neuf entre (OI↑) porté "
                "par une demande agressive (CVD↑). Prélude au markup.",
            "who":
                "Mains fortes = s'engagent à l'achat ouvertement. Shorts résiduels = squeezés. Foule = "
                "commence à peine à y croire.",
            "indices": [
                ("Volume", f"SOUTENU ≥ ×{th.sos_vol}", "il faut de la vraie demande pour franchir et tenir la résistance"),
                ("Spread/ATR", f"≥ {th.wide_spread_atr} ATR (large)", "expansion de range = conviction, pas un grignotage"),
                ("CLV", "haute (≥ 0.6)", "le prix clôture près du haut = les acheteurs dominent la barre"),
                ("OI", "↑ avec le prix (longs neufs)", "argent neuf à l'achat = markup réel, PAS un simple covering"),
                ("CVD", "↑ FRANC (demande agressive) — sinon faux SOS", "un SOS sans CVD↑ = porté par du covering = cassure fragile (piège)"),
                ("Tierces", "funding passe positif, short liqs (squeeze)", "la bascule du positionnement confirme l'engagement"),
            ],
            "trap": "Un breakout n'est un VRAI SOS qu'avec OI↑ ET CVD↑. Sans argent neuf agressif, c'est "
                    "un covering = upthrust potentiel (faux SOS). Confirmer avec le back-up (LPS) qui tient "
                    "au-dessus de la résistance.",
        },
        {
            "id": "lps", "schema": "accumulation", "phase": "Phase D",
            "title": "LPS — Last Point of Support (Dernier point de soutien)",
            "story":
                "Après le SOS, le prix <b>recule en douceur</b> vers la résistance franchie (devenue "
                "support) sur un <b>volume sec</b> : c'est le « back-up to the edge of the creek ». Un "
                "<b>creux plus haut</b> qui tient = dernière occasion d'embarquer avant le markup. "
                "L'absence d'offre sur ce repli confirme la force.",
            "who":
                "Quelques preneurs de profit (faible) vs mains fortes qui tiennent. Pas de retour des "
                "vendeurs = la voie est libre.",
            "indices": [
                ("Volume", f"SEC ≤ ×{th.test_vol}", "un back-up sain ne mobilise pas de volume : pas d'offre"),
                ("Spread/ATR", "étroit", "réaction sans engagement, le marché respire"),
                ("CLV", "creux plus HAUT que le climax/spring", "structure haussière : higher low"),
                ("OI", "plat (back-up sain)", "pas de débouclage ni d'engagement nouveau, simple respiration"),
                ("CVD", "plat / sec", "aucune agression vendeuse sur le repli = l'offre a disparu"),
                ("Tierces", "calmes, funding légèrement positif", "positionnement sain, pas d'excès"),
            ],
            "trap": "Un LPS à volume lourd ou qui fait un nouveau plus-bas (sous le SOS) casse la "
                    "structure : la force n'est pas confirmée. Le LPS doit tenir le bon côté de la borne.",
        },
        # ── DISTRIBUTION ────────────────────────────────────────────────────
        {
            "id": "psy", "schema": "distribution", "phase": "Phase A",
            "title": "PSY — Preliminary Supply (Offre préliminaire)",
            "story":
                "Après un long markup, les premières mains fortes commencent à <b>vendre dans la "
                "hausse</b>. Le marché ne retourne pas encore — c'est un <b>avertissement</b> que la "
                "hausse fatigue. La foule est euphorique et achète ; les mains fortes profitent de cette "
                "demande abondante pour écouler leurs positions sans faire chuter le prix.",
            "who":
                "Mains fortes = premiers vendeurs discrets. Foule = euphorique, FOMO, persuadée que ça "
                "monte encore.",
            "indices": [
                ("Volume", "en hausse, premiers pics", "la participation augmente : des vendeurs absorbent la demande"),
                ("Spread/ATR", "qui s'élargit ponctuellement", "premiers à-coups, la hausse régulière se heurte à de l'offre"),
                ("CLV", "des clôtures qui commencent à faiblir", "les vendeurs reprennent le contrôle de certaines barres"),
                ("OI", "premiers shorts qui se positionnent (ou longs qui allègent)", "de l'argent neuf entre côté vente"),
                ("CVD", "première agression vendeuse visible", "des market-sells plafonnent le prix, la hausse ralentit"),
                ("Tierces", "funding très positif, crowd long", "l'euphorie extrême = carburant baissier latent"),
            ],
            "trap": "Ne pas confondre avec une simple pause : le PSY n'est validé qu'avec un pic de volume "
                    "isolé et un ralentissement net. Il PRÉCÈDE le climax.",
        },
        {
            "id": "bc", "schema": "distribution", "phase": "Phase A",
            "title": "BC — Buying Climax (Climax acheteur)",
            "story":
                "Le sommet de l'euphorie. La foule achète en panique (FOMO), souvent sur une mèche "
                "parabolique. <b>Les mains fortes distribuent</b> dans cette demande — elles vendent tout "
                "ce qui s'achète. Le prix grimpe puis <b>cale dans la même barre</b> (clôture loin du "
                "haut) : signature de l'absorption (par l'offre cette fois). Le BC <b>fixe le plafond</b> "
                "de la future plage.",
            "who":
                "Mains faibles = FOMO (achat euphorique, breakout buyers). Mains fortes = distribuent "
                "agressivement au plafond.",
            "indices": [
                ("Volume", f"≥ ×{th.climax_vol} (climactique, le + fort)", "effort acheteur maximal — mais c'est là que la distribution se produit"),
                ("Spread/ATR", f"≥ {th.wide_spread_atr} ATR, très large", "amplitude énorme = euphorie, grande distance parcourue"),
                ("CLV", f"≤ {round(1 - th.reclaim_clv, 2)} : clôture moitié basse", "le prix cale DANS la barre = l'offre a absorbé (effort vs résultat). Une clôture sur le haut n'est pas encore validée BC : l'absorption se lira sur l'AR"),
                ("OI", "purge du levier, net ambigu (longs FOMO ↑ vs shorts liquidés ↓)", "le haut attire de nouveaux longs (piégés) ET flush les shorts ; le NET dépend de qui domine. Lire avec les tierces"),
                ("CVD", "↑ FORT (achat agressif/FOMO) MAIS prix qui cale", "ABSORPTION : énorme agression acheteuse sans résultat haussier durable"),
                ("Tierces", "funding très positif, shorts liquidés, crowd long", "longs encombrés au sommet = base d'un futur markdown"),
            ],
            "trap": "Un climax SANS absorption (clôture sur le haut, suivi acheteur) n'est pas un BC mais "
                    "une continuation haussière. Attendre l'AR pour confirmer que le plafond tient.",
        },
        {
            "id": "ar-dist", "schema": "distribution", "phase": "Phase A",
            "title": "AR — Automatic Reaction (Réaction automatique)",
            "story":
                "Une fois l'achat épuisé au BC, le prix <b>retombe mécaniquement</b> : plus personne pour "
                "acheter, les longs en retard liquident. Réflexe, pas de l'offre convaincue. L'AR <b>fixe "
                "le plancher</b> de la plage. Avec le BC, les deux bornes sont posées. <b>Attention au "
                "cadre</b> : ici l'AR va vers le BAS (opposé au climax-haut).",
            "who":
                "Longs qui liquident + quelques vendeurs réflexes. PAS encore d'engagement directionnel "
                "des mains fortes côté short.",
            "indices": [
                ("Volume", "EN REPLI (< moyenne)", "un repli réflexe ne mobilise pas de gros volume ; s'il est volumique, c'est un SOW"),
                ("Spread/ATR", "souvent en repli", "mouvement moins violent que le climax"),
                ("CLV", "indifférente", "le repli peut clôturer bas sans signifier de la vraie offre"),
                ("OI", "↓ longs liquidés : les longs ferment", "preuve que le repli est un débouclage, pas de l'argent neuf short"),
                ("CVD", "modéré (liquidation, pas d'offre agressive)", "la baisse est portée par la liquidation des longs, pas par une offre agressive qui ouvre des shorts neufs"),
                ("Tierces", "long liqs possibles sur le repli", "les longs en retard se font sortir, alimentant la baisse"),
            ],
            "trap": "Un AR à fort volume OU à OI montant (shorts neufs) n'est pas un AR : c'est déjà un "
                    "SOW. Et NE JAMAIS lire ce climax-bas comme un « SC » : dans un cadre distribution, "
                    "c'est l'AR-bas, et le rallye qui suit est un ST vers la borne haute.",
        },
        {
            "id": "st-dist", "schema": "distribution", "phase": "Phase A/B",
            "title": "ST — Secondary Test (Test secondaire)",
            "story":
                "Le prix <b>remonte sonder le plafond</b> (la zone du BC) pour vérifier que la demande est "
                "épuisée. Idéalement il fait un <b>sommet plus bas</b> sur un <b>volume sec</b> : plus "
                "personne ne veut acheter à ce niveau. C'est la validation que le plafond tient (offre "
                "confirmée) et que la Phase B se déroule.",
            "who":
                "Acheteurs résiduels (faibles) vs absence de demande. Les mains fortes observent que le "
                "marché ne monte plus malgré le test.",
            "indices": [
                ("Volume", f"SEC ≤ ×{th.test_vol} (et < climax)", "la demande est tarie : peu de transactions pour faire monter"),
                ("Spread/ATR", f"ÉTROIT < {th.narrow_spread_atr} ATR", "petit range = pas de pression acheteuse"),
                ("CLV", "neutre, pas de débordement", "équilibre, mais le sommet plus bas trahit l'offre"),
                ("OI", "plat / ↓ (demande tarie)", "pas de nouvel engagement acheteur"),
                ("CVD", "plat / sec (aucune agression)", "personne n'attaque le plafond de façon agressive"),
                ("Tierces", "funding qui reste positif/élevé", "les longs encore encombrés = fragilité"),
            ],
            "trap": "Un ST qui dépasse franchement le BC sur volume peut être un UTAD (Phase C) plutôt "
                    "qu'un simple test. Le sommet plus bas (lower high) confirme l'offre.",
        },
        {
            "id": "utad", "schema": "distribution", "phase": "Phase C",
            "title": "UTAD — Upthrust After Distribution (Faux-haut)",
            "story":
                "Le <b>piège final</b> avant la baisse. Le prix casse brièvement <b>au-dessus du "
                "plafond</b> pour déclencher les stops des shorts et attirer de nouveaux longs (breakout "
                "buyers qui croient à la cassure haussière), puis <b>rejette vite dans la plage</b>. Les "
                "mains fortes vendent la liquidité offerte par les mains faibles. Test ultime de la "
                "demande : si personne ne suit la cassure, la voie est libre pour le markdown.",
            "who":
                "Mains faibles = stoppées (shorts) ou piégées (nouveaux longs/FOMO breakout). Mains "
                "fortes = distribuent dans l'upthrust et déclenchent ensuite la baisse.",
            "indices": [
                ("Volume", "modéré→fort, mais la cassure NE TIENT PAS", "un upthrust peut se faire sur volume (FOMO) ou faible (personne ne suit)"),
                ("Spread/ATR", "pic bref possible sur la mèche", "le mouvement de piège peut être violent mais éphémère"),
                ("CLV", f"clôture qui revient DANS la plage (clv ≤ {th.reclaim_clv})", "le rejet de la cassure = la signature de l'upthrust"),
                ("OI", "↑ au-dessus (longs piégés) puis ↓ (squeeze)", "les nouveaux longs de la cassure se font liquider en redescendant"),
                ("CVD", "prix↑ MAIS CVD plat/divergent = pas de demande", "LA divergence clé : le prix monte sans achat agressif = piège confirmé"),
                ("Tierces", "long liqs sur la rejection, funding qui peut pointer", "les longs piégés se font flusher en redescendant"),
            ],
            "trap": "Si la clôture tient AU-DESSUS du plafond sur OI↑ + CVD↑, ce n'est pas un upthrust "
                    "mais un vrai SOS (accumulation) : le cadre bascule. Tout l'art = distinguer le piège "
                    "(rejet + CVD divergent) du vrai breakout (suivi + CVD franc).",
        },
        {
            "id": "sow", "schema": "distribution", "phase": "Phase D",
            "title": "SOW — Sign of Weakness / Break of the Ice",
            "story":
                "L'<b>offre prend le contrôle</b>. Le prix casse le support de la plage (la « glace ») sur "
                "un <b>volume soutenu, un spread large, une clôture basse</b>. Premier vrai signe que les "
                "mains fortes s'engagent à la vente : argent neuf short (OI↑) porté par une offre "
                "agressive (CVD↓). Prélude au markdown.",
            "who":
                "Mains fortes = s'engagent à la vente ouvertement. Longs résiduels = liquidés. Foule = "
                "commence à paniquer.",
            "indices": [
                ("Volume", f"SOUTENU ≥ ×{th.sos_vol}", "il faut de la vraie offre pour casser et tenir sous le support"),
                ("Spread/ATR", f"≥ {th.wide_spread_atr} ATR (large)", "expansion de range = conviction vendeuse"),
                ("CLV", "basse (≤ 0.4)", "le prix clôture près du bas = les vendeurs dominent la barre"),
                ("OI", "↑ avec la baisse (shorts neufs)", "argent neuf à la vente = markdown réel, PAS une simple liquidation de longs"),
                ("CVD", "↓ FRANC (offre agressive) — sinon faux SOW", "un SOW sans CVD↓ = porté par de la liquidation = cassure fragile"),
                ("Tierces", "funding passe négatif, long liqs", "la bascule du positionnement confirme l'engagement vendeur"),
            ],
            "trap": "Une cassure baissière n'est un VRAI SOW qu'avec OI↑ (shorts neufs) ET CVD↓ (offre "
                    "agressive). Sans ça, c'est de la liquidation de longs = rebond probable. Confirmer "
                    "avec le LPSY.",
        },
        {
            "id": "lpsy", "schema": "distribution", "phase": "Phase D",
            "title": "LPSY — Last Point of Supply (Dernier point d'offre)",
            "story":
                "Après le SOW, le prix <b>rebondit faiblement</b> vers le support cassé (devenu "
                "résistance) sur un <b>volume sec</b>. Un <b>sommet plus bas</b> qui cale = dernière "
                "occasion de vendre avant le markdown. L'absence de demande sur ce rebond confirme la "
                "faiblesse.",
            "who":
                "Quelques rachats de shorts (faible) vs mains fortes qui pressent. Pas de retour des "
                "acheteurs = la voie est libre pour la baisse.",
            "indices": [
                ("Volume", f"SEC ≤ ×{th.test_vol}", "un rebond faible ne mobilise pas de volume : pas de demande"),
                ("Spread/ATR", "étroit", "rebond sans engagement"),
                ("CLV", "sommet plus BAS que le climax/UTAD", "structure baissière : lower high"),
                ("OI", "plat (rebond faible)", "pas d'engagement nouveau, simple respiration"),
                ("CVD", "plat / sec", "aucune agression acheteuse sur le rebond = la demande a disparu"),
                ("Tierces", "funding négatif qui se maintient", "positionnement short qui s'installe"),
            ],
            "trap": "Un LPSY qui repasse au-dessus de la résistance sur OI↑/CVD↑ invalide la faiblesse : "
                    "possible reprise. Le LPSY doit tenir le bon côté (sous la borne).",
        },
    ]


def _event_cards_html(th: Thresholds) -> str:
    cards = ""
    cur_schema = None
    for ev in _event_narratives(th):
        if ev["schema"] != cur_schema:
            cur_schema = ev["schema"]
            acc = cur_schema == "accumulation"
            accent = "#1b6b1b" if acc else "#a11"
            cards += (f'<h3 style="color:{accent};margin-top:22px">'
                      f'{"▲ ACCUMULATION" if acc else "▼ DISTRIBUTION"}</h3>')
        acc = ev["schema"] == "accumulation"
        accent = "#1b6b1b" if acc else "#a11"
        rows = "".join(
            f'<tr><td class="ev2"><b>{html.escape(ind)}</b></td>'
            f'<td class="exp">{att}</td>'
            f'<td>{pourquoi}</td></tr>'
            for ind, att, pourquoi in ev["indices"])
        cards += f"""
        <div class="card event" id="ev-{ev['id']}">
          <h4 style="color:{accent}">{html.escape(ev['title'])}
            <span class="phase">{ev['phase']}</span></h4>
          <p><b>Ce qui se passe.</b> {ev['story']}</p>
          <p class="who"><b>Qui est en jeu.</b> {ev['who']}</p>
          <table class="ind"><thead><tr><th>Indice</th><th>Attendu</th>
            <th>Pourquoi (le narratif → l'indice)</th></tr></thead>
            <tbody>{rows}</tbody></table>
          <p class="trap"><b>Piège / invalidation.</b> {ev['trap']}</p>
        </div>"""
    return f"""
    <section id="events">
      <h2>2 · Narratif détaillé par événement</h2>
      <p class="muted">Pour chaque événement : le récit (ce qui se passe, qui agit), puis la
      répercussion attendue sur chaque indice. C'est le lien narratif → indices qu'il faut
      mémoriser pour lire vite.</p>
      {cards}
    </section>"""


# ─────────────────────────────────────────────────────────────────────────────
# Bloc 3 — Théorie par indice
# ─────────────────────────────────────────────────────────────────────────────
def _indicator_cards(th: Thresholds) -> list[dict]:
    return [
        {
            "id": "vol", "name": "Volume (vol×)", "rank": "Force PRIMAIRE — lue en 1er",
            "def": "Le volume = quantité échangée sur la barre. <b>vol×</b> (vol_ratio) = volume de la "
                   "barre ÷ sa moyenne mobile. Un vol× de 2 = deux fois le volume habituel.",
            "mesure": "La <b>participation / l'effort</b>. C'est l'« effort » de la loi effort-vs-résultat : "
                      "beaucoup de volume = beaucoup d'intérêt à ce niveau (climax, signe) ; peu de volume "
                      "= désintérêt (test, back-up).",
            "role": "Force primaire : on la lit AVANT tout le reste et on forme l'hypothèse dessus. "
                    "Aucune tierce ne prime sur le volume.",
            "attendu": [
                ("Climax (SC/BC)", f"≥ ×{th.climax_vol} (le + fort)"),
                ("Signe (SOS/SOW)", f"≥ ×{th.sos_vol} (soutenu)"),
                ("Test / LPS / LPSY", f"≤ ×{th.test_vol} (sec)"),
                ("AR", "en repli (< moyenne)"),
                ("Spring/UTAD", "modéré→fort mais sans suivi"),
            ],
            "piege": "Un gros volume sans résultat (prix qui n'avance pas) = absorption, pas de la force : "
                     "toujours croiser avec le résultat (spread, clôture) et le CVD.",
        },
        {
            "id": "spread", "name": "Spread / ATR (spread_atr)", "rank": "Force PRIMAIRE (avec le volume)",
            "def": "Le spread = amplitude de la barre (high − low). <b>spread_atr</b> = spread ÷ ATR "
                   "(Average True Range) : l'amplitude normalisée par la volatilité récente.",
            "mesure": "La <b>conviction / l'expansion de range</b>. C'est le « résultat » brut : un spread "
                      "large = le prix a parcouru beaucoup (climax, signe directionnel) ; un spread étroit "
                      "= compression, indécision (test, ressort qui se comprime).",
            "role": "Primaire, lu avec le volume. Large + gros volume = mouvement de conviction ; "
                    "étroit + volume sec = assèchement (test).",
            "attendu": [
                ("Climax (SC/BC)", f"≥ {th.wide_spread_atr} ATR (très large)"),
                ("Signe (SOS/SOW)", f"≥ {th.wide_spread_atr} ATR (large)"),
                ("Test / LPS / LPSY", f"≤ {th.narrow_spread_atr} ATR (étroit)"),
                ("Spring/UTAD", "pic bref possible sur la mèche"),
            ],
            "piege": "Spread large + volume FAIBLE = mouvement suspect (peu de participation pour une "
                     "grande amplitude) → souvent un piège ou un trou de liquidité, pas de la vraie force.",
        },
        {
            "id": "clv", "name": "CLV (Close Location Value)", "rank": "Force PRIMAIRE (qualité de barre)",
            "def": "CLV = (close − low) ÷ (high − low), borné et clippé sur <b>[0, 1]</b> : <b>0</b> = "
                   "clôture sur le bas, <b>1</b> = clôture sur le haut, <b>0.5</b> = milieu (convention "
                   "du screener — ce n'est pas la variante Williams [−1, +1]).",
            "mesure": "<b>Qui gagne la barre à la clôture.</b> CLV haut = les acheteurs ont repris le "
                      "contrôle en fin de barre (rejet du bas) ; CLV bas = les vendeurs dominent (rejet du "
                      "haut). C'est le détail qui révèle l'absorption sur une barre de climax.",
            "role": "Primaire : affine la lecture volume+spread. Une grosse barre de baisse qui clôture "
                    "HAUT (clv élevé) = absorption (SC) ; une grosse barre de hausse qui clôture BAS = "
                    "distribution (BC).",
            "attendu": [
                ("SC (accu)", f"≥ reclaim_clv ({th.reclaim_clv}) : moitié haute = récupération/absorption"),
                ("BC (distrib)", f"≤ {round(1 - th.reclaim_clv, 2)} : moitié basse = cale/absorption par l'offre"),
                ("SOS", "≥ 0.6 (clôture forte exigée par le détecteur)"),
                ("SOW", "≤ 0.4 (clôture faible exigée par le détecteur)"),
                ("Spring", f"revient dans la plage, clv ≥ {th.reclaim_clv}"),
                ("UTAD", f"revient dans la plage, clv ≤ {th.reclaim_clv}"),
            ],
            "piege": "Le CLV d'une seule barre peut tromper (mèche). Le confirmer sur la barre suivante et "
                     "avec le contexte (où dans la plage, quel événement).",
        },
        {
            "id": "oi", "name": "Open Interest (OI, en coin)", "rank": "Confirmation SECONDAIRE — lue en 2e",
            "def": "L'OI = nombre total de contrats perp ouverts (positions non encore clôturées). "
                   "<b>Toujours lu en COIN</b> (ex. BTC), jamais en USD (l'USD = coin × prix conflate "
                   "positions et prix → faux signal quand le prix bouge).",
            "mesure": "<b>Le volume ouvre-t-il ou ferme-t-il des positions ?</b> Quatre signatures : "
                      "prix↑ + OI↑ = <b>longs neufs</b> ; prix↑ + OI↓ = <b>short covering</b> ; "
                      "prix↓ + OI↑ = <b>shorts neufs</b> ; prix↓ + OI↓ = <b>liquidation de longs</b>.",
            "role": "Secondaire : après le volume, désambiguïse QUI agit. Distingue l'argent neuf "
                    "(engagement directionnel) du simple débouclage (covering/liquidation).",
            "attendu": [
                ("Climax", "purge du levier — net AMBIGU (neufs ↑ vs liquidés ↓), lire avec tierces"),
                ("AR", "↓ (débouclage : covering en accu, liquidation en distrib)"),
                ("ST / LPS / LPSY", "plat (pas d'engagement)"),
                ("Spring/UTAD", "↑ sur la mèche (piégés) puis ↓ (squeeze)"),
                ("SOS", "↑ avec le prix (longs neufs)"),
                ("SOW", "↑ avec la baisse (shorts neufs)"),
            ],
            "piege": "OI↑ à prix plat est ambigu (longs OU shorts qui ouvrent) → croiser avec ratio L/S, "
                     "funding, liquidations. En coin, le SIGNE est fiable même sur de petits Δ (peser par "
                     "la cohérence sur plusieurs barres).",
        },
        {
            "id": "cvd", "name": "CVD (Cumulative Volume Delta)", "rank": "TIERCE d'absorption — lue en 1re des tierces",
            "def": "CVD = somme cumulée du <b>delta</b> par barre, où delta = volume des acheteurs "
                   "agressifs (taker buy) − volume des vendeurs agressifs (taker sell). Mesure le flux "
                   "d'ordres <b>au marché</b> (ceux qui « franchissent le spread »).",
            "mesure": "<b>L'agression directionnelle réelle.</b> Surtout : l'<b>absorption</b>, via la "
                      "divergence prix↔CVD. prix↑ + CVD plat/↓ = hausse sans demande agressive (offre "
                      "absorbe) → faiblesse/distribution ; prix↓ + CVD plat/↑ (ou vente agressive mais prix "
                      "qui tient) = demande absorbe l'offre → accumulation ; prix et CVD en phase = "
                      "mouvement « honnête », pas d'absorption (non concluant).",
            "role": "Tierce, mais lue en TÊTE des tierces (la plus proche du volume primaire). Vient EN "
                    "SECOND TEMPS, à froid, confirmer/affaiblir l'hypothèse du tableau. 4 verdicts : "
                    "confirme distrib / confirme accu / affaiblit / rien d'exploitable.",
            "attendu": [
                ("SC", "↓ fort mais prix récupère = absorption (constructif)"),
                ("BC", "↑ fort mais prix cale = absorption par l'offre"),
                ("SOS", "↑ FRANC (sinon faux SOS / covering)"),
                ("SOW", "↓ FRANC (sinon faux SOW / liquidation)"),
                ("UTAD/upthrust", "prix↑ mais CVD plat/divergent = piège"),
                ("AR / ST", "plat / modeste (réflexe, pas d'agression)"),
            ],
            "piege": "CVD calculé en SPOT (le perp fapi est géo-bloqué) = proxy du flux. La divergence "
                     "décisive est souvent MULTI-BARRES (sur un swing), pas une bougie. Vérifier le fuseau "
                     "(même +2h que le prix). Une divergence CVD spot vs OI perp est elle-même lisible.",
        },
        {
            "id": "absorption", "name": "Absorption & No-demand (effort vs résultat)",
            "rank": "TIERCE dérivée du CVD — quantifie l'absorption",
            "def": "Deux lectures chiffrées de la loi <b>effort (CVD) vs résultat (prix)</b>, à partir "
                   "du flux agressif. <b>EFFORT</b> = <code>delta_z</code> = delta ÷ écart-type glissant "
                   "(le flux net en σ, signe = côté). <b>RÉSULTAT</b> = soit <code>clv_s = 2·clv − 1</code> "
                   "(clôture dans le range), soit <code>ret_atr = (close − open)/atr</code> (déplacement). "
                   "<b>absorption = −delta_z · clv_s</b> ; <b>no_demand/no_supply</b> = prix qui voyage "
                   "(|ret_atr| ≥ ~1 ATR) avec un effort faible (|delta_z| ≤ ~0.5σ).",
            "mesure": "<b>Deux divergences OPPOSÉES</b> du 2×2 effort/résultat : "
                      "(1) <b>Absorption</b> = effort fort mais flux <i>rejeté</i> (gros delta, clôture "
                      "contraire) → quelqu'un encaisse passivement. (2) <b>No-demand / No-supply</b> = "
                      "résultat fort mais effort <i>absent</i> (le prix bouge sans participation agressive). "
                      "L'absorption ne voit PAS le no-demand et vice-versa — d'où les deux.",
            "role": "Tierce, dérivée du CVD (donc lue après volume+OI, à froid). Confirme/affaiblit "
                    "l'hypothèse du tableau. <b>absorption > 0</b> : delta_z < 0 = demande absorbe l'offre "
                    "(haussier) ; delta_z > 0 = offre absorbe la demande (baissier). <b>≈ 0</b> = mouvement "
                    "honnête.",
            "attendu": [
                ("SC / Spring (accu)", "absorption > 0 côté demande (vente rejetée au plancher)"),
                ("BC / UTAD (distrib)", "absorption > 0 côté offre, OU no_demand (achat rejeté / hausse sans flux)"),
                ("SOS / SOW honnêtes", "absorption ≈ 0 ou négatif (effort ET résultat alignés)"),
                ("Markup/markdown passif", "no_demand (hausse sans achat) / no_supply (baisse sans vente)"),
            ],
            "piege": "Per-barre c'est BRUITÉ — l'absorption se lit mieux sur un SWING. Relatif et "
                     "dépendant de la TF/de l'actif (le σ glissant est la référence). CVD = spot (proxy). "
                     "Ne pas confondre absorption (flux rejeté) et no-demand (prix sans flux) : ce sont "
                     "deux signaux distincts.",
        },
        {
            "id": "funding", "name": "Funding rate", "rank": "TIERCE de positionnement",
            "def": "Paiement périodique entre longs et shorts sur les perpétuels, qui arrime le perp au "
                   "spot. <b>Positif</b> = les longs paient les shorts (longs majoritaires/avides) ; "
                   "<b>négatif</b> = les shorts paient (shorts majoritaires).",
            "mesure": "<b>L'encombrement et le coût du positionnement.</b> Un funding très positif = longs "
                      "surchargés (carburant baissier latent : ils paient pour tenir) ; très négatif = "
                      "shorts surchargés (carburant haussier : squeeze potentiel).",
            "role": "Tierce, à croiser quand l'OI est ambigu ou que le prix cale. À lire à froid : un "
                    "funding qui contredit la thèse = risque à relater.",
            "attendu": [
                ("Bas de marché (SC/accu)", "très négatif = shorts encombrés (squeeze à venir)"),
                ("Haut de marché (BC/distrib)", "très positif = longs encombrés (markdown à venir)"),
                ("SOS confirmé", "bascule vers positif (longs s'engagent)"),
                ("SOW confirmé", "bascule vers négatif (shorts s'engagent)"),
            ],
            "piege": "Le funding mesure le POSITIONNEMENT, pas la direction immédiate. Un extrême est un "
                     "signal de fragilité/contrarian, pas un timing.",
        },
        {
            "id": "lsr", "name": "Ratio Long/Short", "rank": "TIERCE de positionnement",
            "def": "Rapport entre comptes/positions longs et shorts (ex. ratio 2 = deux fois plus de longs "
                   "que de shorts ; pct_long 70% = 70% du côté long).",
            "mesure": "<b>Le positionnement de la foule.</b> Un ratio très élevé = crowd long (souvent "
                      "retail) → contrarian baissier ; ratio bas = crowd short → contrarian haussier.",
            "role": "Tierce de confirmation. Sert surtout à attribuer un OI ambigu : ratio qui baisse "
                    "pendant que l'OI monte = des shorts entrent.",
            "attendu": [
                ("Climax/piège", "crowd du mauvais côté (longs au sommet, shorts au plancher)"),
                ("Vraie tendance (Phase E)", "le crowd se retrouve à contre-pied, liquidé progressivement"),
            ],
            "piege": "Distinguer le ratio « tous comptes » (retail, contrarian) du ratio « top traders » "
                     "(smart money). À lire à froid : un crowd déjà positionné dans le sens de la thèse "
                     "est une FRAGILITÉ, pas une confirmation.",
        },
        {
            "id": "liq", "name": "Liquidations", "rank": "TIERCE de positionnement",
            "def": "Fermetures FORCÉES de positions à effet de levier (margin call). On lit séparément "
                   "<b>long_liq</b> (longs liquidés) et <b>short_liq</b> (shorts liquidés).",
            "mesure": "<b>Les flushs forcés / squeezes.</b> Un pic de long_liq = cascade de longs sortis de "
                      "force (capitulation, accélère la baisse) ; pic de short_liq = squeeze de shorts "
                      "(accélère la hausse). ≈ 0 des deux côtés = mouvement ordonné, pas de flush.",
            "role": "Tierce. Confirme la violence et le côté d'un mouvement : un SC/spring s'accompagne de "
                    "long_liq massives ; un SOS/squeeze de short_liq.",
            "attendu": [
                ("SC (accu)", "long_liq massives (flush de la capitulation)"),
                ("BC (distrib)", "short_liq (les shorts trop tôt essorés dans la hausse)"),
                ("Spring", "short_liq sur la récupération (shorts piégés)"),
                ("UTAD", "long_liq sur la rejection (longs piégés)"),
                ("Mouvement ordonné", "≈ 0 des deux côtés (pas de flush forcé)"),
            ],
            "piege": "Des liquidations nulles pendant un mouvement = il est VOLONTAIRE (pas de squeeze "
                     "forcé) → souvent moins durable qu'un flush. Lire avec funding + ratio pour le sens "
                     "commun (ex. covering volontaire vs squeeze forcé).",
        },
    ]


def _indicator_cards_html(th: Thresholds) -> str:
    cards = ""
    for ind in _indicator_cards(th):
        rows = "".join(
            f'<tr><td class="ev2">{html.escape(ev)}</td><td>{att}</td></tr>'
            for ev, att in ind["attendu"])
        cards += f"""
        <div class="card indic" id="ind-{ind['id']}">
          <h4>{html.escape(ind['name'])} <span class="phase">{ind['rank']}</span></h4>
          <p><b>Définition.</b> {ind['def']}</p>
          <p><b>Ce qu'il mesure.</b> {ind['mesure']}</p>
          <p><b>Son rôle.</b> {ind['role']}</p>
          <table class="ind"><thead><tr><th>Événement</th><th>Attendu</th></tr></thead>
            <tbody>{rows}</tbody></table>
          <p class="trap"><b>Piège / caveat.</b> {ind['piege']}</p>
        </div>"""
    return f"""
    <section id="indices">
      <h2>3 · Théorie par indice</h2>
      <p class="muted">Pour chaque indicateur : définition, ce qu'il mesure, son rôle dans la
      hiérarchie, ce qui est attendu à chaque événement, et ses pièges.</p>
      {cards}
    </section>"""


# ─────────────────────────────────────────────────────────────────────────────
# Assemblage
# ─────────────────────────────────────────────────────────────────────────────
def _toc_html() -> str:
    return """
    <nav class="toc">
      <b>Sommaire</b>
      <ol>
        <li><a href="#fondations">Fondations</a> — lois, opérateur composite, phases, hiérarchie</li>
        <li><a href="#tables">Tables de référence</a> — accumulation &amp; distribution (vol×, spread, OI, CVD)</li>
        <li><a href="#events">Narratif par événement</a> —
          <a href="#ev-sc">SC</a> · <a href="#ev-ar-acc">AR</a> · <a href="#ev-st-acc">ST</a> ·
          <a href="#ev-spring">Spring</a> · <a href="#ev-sos">SOS</a> · <a href="#ev-lps">LPS</a> ·
          <a href="#ev-bc">BC</a> · <a href="#ev-utad">UTAD</a> · <a href="#ev-sow">SOW</a> ·
          <a href="#ev-lpsy">LPSY</a></li>
        <li><a href="#indices">Théorie par indice</a> —
          <a href="#ind-vol">Volume</a> · <a href="#ind-spread">Spread</a> · <a href="#ind-clv">CLV</a> ·
          <a href="#ind-oi">OI</a> · <a href="#ind-cvd">CVD</a> ·
          <a href="#ind-absorption">Absorption</a> · <a href="#ind-funding">Funding</a> ·
          <a href="#ind-lsr">L/S</a> · <a href="#ind-liq">Liquidations</a></li>
      </ol>
    </nav>"""


def build_theory_html(th: Thresholds | None = None,
                      out_path: str = "memo_theorie.html") -> str:
    """Écrit le mémo HTML V2 (fondations + tables + narratifs + indices) et renvoie le chemin."""
    th = th or Thresholds()
    style = """
    <style>
      :root{--acc:#1b6b1b;--dis:#a11;--ink:#222;--mut:#666}
      body{font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;
           margin:0;color:var(--ink);background:#fff;line-height:1.5}
      .wrap{max-width:1180px;margin:0 auto;padding:24px}
      h1{font-size:1.5em;margin:0 0 4px}
      h2{font-size:1.25em;margin:30px 0 10px;padding-bottom:5px;border-bottom:2px solid #eee}
      h3{font-size:1.05em;margin:18px 0 8px}
      h4{margin:0 0 8px;font-size:1em}
      .sub{color:var(--mut);margin:0 0 14px;font-size:.9em}
      .muted{color:var(--mut);font-size:.9em}
      table{border-collapse:collapse;width:100%;margin:8px 0 12px;font-size:.85em}
      th,td{border:1px solid #ddd;padding:7px 9px;vertical-align:top;text-align:left}
      th{background:#f4f4f4;font-weight:600}
      td.ev,td.ev2{white-space:nowrap;font-weight:600}
      td.ev .full{font-size:.8em;color:var(--mut);font-weight:400}
      td.num{font-variant-numeric:tabular-nums;background:#fafafa}
      td.oi{background:#eef5ff;color:#234}
      td.cvd{background:#fff4e8;color:#6a3d00}
      td.exp{background:#fafafa;font-weight:600}
      td.ok{color:var(--acc)}
      td.ko{color:var(--dis)}
      tr:nth-child(even) td{background:#fcfcfc}
      tr:nth-child(even) td.oi{background:#e7f0fc}
      tr:nth-child(even) td.cvd{background:#fdebd6}
      .toc{background:#f7f9fc;border:1px solid #e2e8f0;border-radius:8px;padding:12px 18px;margin:14px 0 4px;font-size:.9em}
      .toc ol{margin:6px 0 0;padding-left:20px}
      .toc a{color:#2456a6;text-decoration:none}
      .toc a:hover{text-decoration:underline}
      .cards{display:block}
      .card{border:1px solid #e3e3e3;border-radius:8px;padding:14px 16px;margin:12px 0;background:#fff}
      .card.event{border-left:4px solid #ccc}
      .card .phase{font-size:.72em;color:var(--mut);font-weight:400;border:1px solid #ddd;
           border-radius:10px;padding:1px 8px;margin-left:6px;white-space:nowrap}
      .card .who{color:#444}
      .card .trap{background:#fff7f7;border-left:3px solid var(--dis);padding:6px 10px;
           margin:8px 0 0;font-size:.92em;border-radius:0 4px 4px 0}
      table.ind{font-size:.84em;margin:8px 0}
      @media print{
        .card{page-break-inside:avoid}
        h2{page-break-before:always}
        .toc{display:none}
      }
    </style>"""
    seuils = (f"climax_vol=×{th.climax_vol} · sos_vol=×{th.sos_vol} · "
              f"test_vol=×{th.test_vol} · wide_spread_atr={th.wide_spread_atr} ATR · "
              f"narrow_spread_atr={th.narrow_spread_atr} ATR · pen_atr={th.pen_atr} ATR · "
              f"reclaim_clv={th.reclaim_clv}")
    doc = f"""<!doctype html><html lang="fr"><head><meta charset="utf-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>Mémo théorie Wyckoff V2 — événements, indices, OI &amp; CVD</title>{style}</head>
    <body><div class="wrap">
    <h1>Mémo théorie Wyckoff — V2</h1>
    <p class="sub">Événements (accumulation &amp; distribution), narratif détaillé, et théorie de
    chaque indice (volume, spread/ATR, CLV, OI, CVD, tierces). Seuils courants :
    {html.escape(seuils)}</p>
    {_toc_html()}
    {_foundations_html(th)}
    {_tables_section(th)}
    {_event_cards_html(th)}
    {_indicator_cards_html(th)}
    <p class="muted" style="margin-top:24px;border-top:1px solid #eee;padding-top:10px">
    Mémo régénéré à chaque analyse depuis les <code>Thresholds</code> courants — les seuils
    affichés sont donc toujours ceux utilisés par le screener. Lecture : volume → OI → tierces
    (CVD en tête), à froid, sans forcer le consensus.</p>
    </div></body></html>"""
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(doc)
    return out_path


if __name__ == "__main__":
    import sys
    out = sys.argv[1] if len(sys.argv) > 1 else "memo_theorie.html"
    print(build_theory_html(out_path=out))
