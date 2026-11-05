# -*- coding: utf-8 -*-
"""Génère memo_comportement_resistance.html — 11 cas MECE, avec schéma bougies SVG,
ligne phase/signaux avant-coureurs, et encart no-demand. Aucune dépendance externe."""

import base64, os
_BASE=os.path.dirname(os.path.abspath(__file__))
_CHARTS=os.path.join(_BASE,"charts")
UP, DN, GREY = "#1b6b1b", "#a11", "#666"

def _b64(cid):
    p = os.path.join(_CHARTS, f"{cid}_embed.png")
    if not os.path.exists(p): return ""
    with open(p, "rb") as f:
        return base64.b64encode(f.read()).decode()

# F2 porte 3 graphes (les 3 BUEC vérifiés) ; les autres cas un seul.
def _charts_html(cid):
    ids = {"f2": ["f2a", "f2b", "f2c"]}.get(cid, [cid])
    return "".join(
        f'<img class="realchart" src="data:image/png;base64,{_b64(i)}" '
        f'alt="graphe annoté réel — {i}" loading="lazy">' for i in ids)

CVDCOL = "#173a6b"
VOLCOL = "#5b8fd0"

def svg(candles, R, vol, cvd, w=340, h=252):
    """3 panneaux : prix (bougies + résistance), volume (barres + moyenne), CVD (ligne).
    candles: (o,h,l,c) ; vol/cvd: listes alignées sur candles."""
    pl, pr = 10, 46
    pt, pB = 14, 138          # panneau prix
    vt, vB = 150, 194         # panneau volume
    ct, cB = 206, 246         # panneau CVD
    lows = [c[2] for c in candles] + [R]
    highs = [c[1] for c in candles] + [R]
    lo, hi = min(lows) - 0.4, max(highs) + 0.4
    def yp(p): return pt + (hi - p) / (hi - lo) * (pB - pt)
    n = len(candles)
    slot = (w - pl - pr) / n
    bw = slot * 0.5
    P = [f'<svg viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" '
         f'xmlns="http://www.w3.org/2000/svg" font-family="sans-serif">']
    # étiquettes de panneaux + séparateurs
    for lbl, yy in (("prix", pt - 4), ("vol", vt - 4), ("CVD", ct - 4)):
        P.append(f'<text x="{pl}" y="{yy:.0f}" font-size="9" fill="{GREY}">{lbl}</text>')
    for ys in (vt - 2, ct - 2):
        P.append(f'<line x1="{pl}" y1="{ys}" x2="{w-pr+2}" y2="{ys}" stroke="#eee" stroke-width="1"/>')
    # résistance
    yR = yp(R)
    P.append(f'<line x1="{pl}" y1="{yR:.1f}" x2="{w-pr+2}" y2="{yR:.1f}" stroke="{DN}" '
             f'stroke-width="1.4" stroke-dasharray="5 3"/>')
    P.append(f'<text x="{w-pr+6}" y="{yR+3.5:.1f}" font-size="10" fill="{DN}">résist.</text>')
    # bougies
    for i, (o, hh, ll, c) in enumerate(candles):
        cx = pl + slot * (i + 0.5)
        col = UP if c >= o else DN
        P.append(f'<line x1="{cx:.1f}" y1="{yp(hh):.1f}" x2="{cx:.1f}" y2="{yp(ll):.1f}" '
                 f'stroke="{col}" stroke-width="1.3"/>')
        yt, yb = yp(max(o, c)), yp(min(o, c))
        P.append(f'<rect x="{cx-bw/2:.1f}" y="{yt:.1f}" width="{bw:.1f}" '
                 f'height="{max(yb-yt,2.0):.1f}" fill="{col}"/>')
    # volume : barres + ligne de moyenne (volume relatif)
    vmax = max(vol) or 1.0
    for i, v in enumerate(vol):
        cx = pl + slot * (i + 0.5)
        bh = v / vmax * (vB - vt - 2)
        P.append(f'<rect x="{cx-bw/2:.1f}" y="{vB-bh:.1f}" width="{bw:.1f}" '
                 f'height="{bh:.1f}" fill="{VOLCOL}"/>')
    vma = sum(vol) / len(vol)
    yvma = vB - vma / vmax * (vB - vt - 2)
    P.append(f'<line x1="{pl}" y1="{yvma:.1f}" x2="{w-pr+2}" y2="{yvma:.1f}" stroke="{GREY}" '
             f'stroke-width="1" stroke-dasharray="3 2"/>')
    P.append(f'<text x="{w-pr+6}" y="{yvma+3:.1f}" font-size="8.5" fill="{GREY}">moy.</text>')
    # CVD : ligne
    clo, chi = min(cvd), max(cvd)
    rng = (chi - clo) or 1.0
    def yc(val): return cB - (val - clo) / rng * (cB - ct - 4)
    pts = " ".join(f'{pl+slot*(i+0.5):.1f},{yc(v):.1f}' for i, v in enumerate(cvd))
    P.append(f'<polyline points="{pts}" fill="none" stroke="{CVDCOL}" stroke-width="1.8"/>')
    for i, v in enumerate(cvd):
        P.append(f'<circle cx="{pl+slot*(i+0.5):.1f}" cy="{yc(v):.1f}" r="1.6" fill="{CVDCOL}"/>')
    P.append('</svg>')
    return "".join(P)

# ---- schémas par cas : (candles, R, caption, vol[], cvd[]) — vol/cvd alignés sur candles ----
SCH = {
 "r1": ([(4,5,3.9,4.9),(4.9,6.4,4.8,6.2),(6.2,7.7,6.1,7.5),(7.5,8.0,5.3,5.5),(5.5,5.8,4.6,4.8)], 8,
        "Rejet : volume qui gonfle sur la bougie rouge, CVD qui plonge AVEC le prix (mouvement honnête).",
        [0.4,0.5,0.62,0.92,0.6], [1,1.7,2.3,0.6,0.1]),
 "r2": ([(3,4,2.9,3.9),(3.9,5.1,3.8,5.0),(5.0,6.1,4.9,6.0),(6.0,9.4,5.9,7.0),(7.0,7.2,5.0,5.3)], 8,
        "Climax : volume ULTRA + CVD qui pique puis se retourne — l'achat agressif est absorbé au sommet.",
        [0.3,0.4,0.5,1.0,0.62], [1,2,3,4,2.2]),
 "r3": ([(6,7,5.9,6.9),(6.9,7.9,6.8,7.6),(7.6,8.05,7.5,7.7),(7.7,8.05,7.55,7.62),(7.62,7.95,7.5,7.55),(7.55,7.6,6.5,6.6)], 8,
        "Absorption : corps étroits, gros volume, mais CVD qui MONTE sans le prix = achat avalé par un mur.",
        [0.5,0.62,0.85,0.9,0.85,0.5], [1,2,3,3.8,4.3,3.6]),
 "r4": ([(5,8.0,4.9,7.5),(7.5,7.6,6.0,6.2),(6.2,7.4,6.1,7.0),(7.0,7.1,5.5,5.7),(5.7,6.9,5.6,6.3),(6.3,6.4,4.8,5.0)], 8,
        "Hauts déclinants + volume qui décroît rebond après rebond ; CVD en lower highs (variante double top = hauts égaux).",
        [0.8,0.4,0.6,0.35,0.45,0.5], [3,1.6,2.3,1.1,1.7,0.9]),
 "r5": ([(5,5.6,4.9,5.5),(5.5,6.2,5.4,6.0),(6.0,6.7,5.9,6.5),(6.5,7.2,6.4,7.0),(7.0,7.6,6.9,7.4),(7.4,8.05,7.35,7.6),(7.6,7.7,6.8,6.9)], 8,
        "Retour dans la zone à volume qui S'ASSÈCHE (≤ ×0.85) ; prix HH mais CVD LH = divergence d'épuisement.",
        [0.5,0.45,0.4,0.34,0.3,0.25,0.3], [1,1.8,2.5,3.0,3.2,2.9,2.5]),
 "r6": ([(6,7,5.9,6.9),(6.9,7.8,6.8,7.6),(7.6,9.1,7.4,7.5),(7.5,7.6,5.5,5.7),(5.7,5.9,4.5,4.7)], 8,
        "Poke AU-DESSUS, clôture SOUS ; CVD SANS expansion sur le poke (pas de demande) puis chute.",
        [0.4,0.5,0.72,0.82,0.6], [1,1.6,1.75,0.5,0.05]),
 "f1": ([(5,6,4.9,5.9),(5.9,6.8,5.8,6.6),(6.6,7.5,6.5,7.3),(7.3,9.3,7.25,9.1),(9.1,9.9,9.0,9.7)], 8,
        "Cassure large verte, clôture au sommet ; volume ≥ ×1.3 et CVD↑ FRANC = vraie demande.",
        [0.4,0.45,0.5,0.95,0.72], [1,1.3,1.6,3.3,3.9]),
 "f2": ([(6,7,5.9,6.9),(6.9,8.9,6.8,8.7),(8.7,8.8,7.95,8.15),(8.15,8.4,8.0,8.25),(8.25,9.3,8.15,9.1)], 8,
        "Cassure sur volume, repli-test à volume SEC qui tient ; CVD plat au retest (pas de vente).",
        [0.5,0.9,0.35,0.3,0.72], [1,2.8,2.7,2.75,3.5]),
 "f3": ([(6.5,7.5,6.4,7.4),(7.4,8.2,7.3,8.05),(8.05,8.2,7.9,8.02),(8.02,8.1,7.8,7.9),(7.9,8.0,7.0,7.1)], 8,
        "Poussée faible à peine au-dessus ; volume FAIBLE + CVD plat = pas de demande, puis échec.",
        [0.5,0.42,0.35,0.3,0.5], [1,1.15,1.2,1.1,0.8]),
 "f4": ([(6,6.5,5.9,6.4),(6.4,6.6,6.3,6.5),(6.5,9.1,6.4,8.9),(8.9,9.1,8.3,8.4),(8.4,8.5,7.5,7.6)], 8,
        "Pic à volume élevé (covering) mais CVD qui pique puis STAGNE ; OI↓ = cassure fragile.",
        [0.3,0.3,0.92,0.5,0.55], [1,1.1,3.0,3.0,2.8]),
 "f5": ([(6.4,6.8,6.3,6.7),(6.7,7.1,6.6,7.0),(7.0,7.5,6.9,7.4),(7.4,7.9,7.3,7.8),(7.8,8.2,7.7,8.1),(8.1,8.5,8.0,8.4),(8.4,8.8,8.3,8.7)], 8,
        "Petits corps réguliers ; volume modeste CONSTANT + CVD légèrement positif persistant (achat furtif).",
        [0.4,0.42,0.45,0.43,0.46,0.44,0.48], [1,1.2,1.4,1.6,1.8,2.0,2.2]),
}

# ---- ligne « contexte de marché + phase Wyckoff + signaux avant-coureurs » par cas ----
PHZ = {
 "r1": "<b>Contexte de marché :</b> downtrend / markdown (l'offre défend les rebonds) ou plafond d'un marché qui distribue — régime baissier ou range tenu par les vendeurs. <b>Phase Wyckoff :</b> B/C d'une distribution (ST/SOW naissant). <b>Signaux avant-coureurs :</b> approche sur volume qui monte mais spread qui se contracte, mèches hautes, CVD qui plafonne.",
 "r2": "<b>Contexte de marché :</b> <b>fin de bull market / sommet de cycle</b> — euphorie, parabole, sentiment unanime haussier, news au zénith. Le blow-off d'un markup sur-étendu. <b>Phase Wyckoff :</b> A (le climax qui stoppe la tendance). <b>Signaux avant-coureurs :</b> accélération parabolique, expansion spread+volume, écart prix/moyenne extrême, funding qui s'envole.",
 "r3": "<b>Contexte de marché :</b> transition <b>markup → distribution</b> — le marché commence à topper en douceur, l'institutionnel vend dans la force sans drama ; souvent régime range/choppy où un niveau est défendu. <b>Phase Wyckoff :</b> B de distribution. <b>Signaux avant-coureurs :</b> volume élevé sans progrès répété, spread qui se contracte à l'approche, CVD qui monte mais pas le prix.",
 "r4": "<b>Contexte de marché :</b> la <b>phase de distribution du cycle</b> — le marché roule du haussier vers le baissier sur des semaines, sentiment encore haussier mais qui s'effrite, dérive latérale-baissière. <b>Phase Wyckoff :</b> B→D de distribution. <b>Signaux avant-coureurs :</b> hauts déclinants, volume décroissant sur les rebonds, rallyes no-demand, plage qui s'aplatit.",
 "r5": "<b>Contexte de marché :</b> <b>bull trend mûr / fin de markup</b> — la tendance est vieille, participation en baisse, peu d'acheteurs neufs, complaisance ; grind de faible conviction juste avant le top. <b>Phase Wyckoff :</b> fin de D. <b>Signaux avant-coureurs :</b> divergence prix HH / CVD LH, volume qui décline sur les nouveaux hauts, corps qui rétrécissent, momentum qui diverge.",
 "r6": "<b>Contexte de marché :</b> <b>sommet de marché / distribution après un gros markup</b> — range de topping volatil, longs encombrés, chasses de liquidité ; aussi au sommet d'un rebond de bear market (redistribution). <b>Phase Wyckoff :</b> C (test terminal, UTAD). <b>Signaux avant-coureurs :</b> plage mûre, stops massés au-dessus d'un plus-haut évident, upthrusts mineurs en amont, ST en lower high, souvent après une phase d'absorption (R3).",
 "f1": "<b>Contexte de marché :</b> <b>début-à-milieu de markup</b> — bull trend frais après accumulation, cassure d'une base, régime risk-on avec vraie participation. <b>Phase Wyckoff :</b> C→D. <b>Signaux avant-coureurs :</b> spring / dernier test réussi, séchage du volume dans la base, higher lows qui se resserrent, absorption de la demande aux creux, CVD en higher lows.",
 "f2": "<b>Contexte de marché :</b> <b>confirmation d'un nouveau markup</b> — début de bull trend juste après la sortie d'accumulation, régime risk-on constructif. <b>Phase Wyckoff :</b> D. <b>Signaux avant-coureurs :</b> SOS déjà en place, volume qui sèche sur le pullback, no-supply, premier higher low au-dessus du niveau cassé.",
 "f3": "<b>Contexte de marché :</b> marché <b>range/choppy ou fin de cycle</b> où le retail chasse les breakouts sans l'institutionnel ; typique des rebonds de bear market — régime sans sponsor. <b>Phase Wyckoff :</b> B/C prématurée (faux départ). <b>Signaux avant-coureurs :</b> volume déjà anémique à l'approche, pas de higher lows constructifs, CVD plat.",
 "f4": "<b>Contexte de marché :</b> <b>après un markdown / capitulation</b> (fortement shorté) ou rebond de bear market — survendu, shorts encombrés, funding négatif, mean-reversion. <b>Phase Wyckoff :</b> souvent A d'un range (après SC/climax). <b>Signaux avant-coureurs :</b> OI très élevé + funding négatif + crowd short massé, puis un déclencheur (news / liquidations en chaîne).",
 "f5": "<b>Contexte de marché :</b> <b>accumulation discrète</b> — base-building en basse volatilité avant une tendance, ou dérive peu liquide ; régime calme, pré-tendance. <b>Phase Wyckoff :</b> D d'accumulation furtive. <b>Signaux avant-coureurs :</b> séchage de volatilité, petits higher lows persistants, delta légèrement positif régulier, absence de climax.",
}

# ---- contenu des cartes (prose conservée de la V2) ----
CARDS = [
("r1","bear","R1 · Rejet actif","— Clean rejection / wide down-bar",
 [("vsa","VSA"),("w","Wyckoff (type SOW)")],("bear","baissier"),
 "Le prix approche la résistance et une <b>bougie large de baisse</b> la renvoie, clôture sur le bas. L'offre <b>agressive</b> (au marché) prend le contrôle : elle pousse, le prix suit — <i>résultat</i> aligné sur l'<i>effort</i>, pas d'absorption.",
 "spread ≥ 1.3 ATR · CLV ≤ 0.2–0.3 · volume ≥ moyenne (souvent ×1.3+) · <b><code>absorption</code> &lt; 0</b> (honnête baissier) · CVD↓ <b>en phase</b> avec le prix.",
 "De <b>gros vendeurs (composite / mains fortes)</b> frappent l'offre au marché : ils ont décidé de <b>défendre le niveau</b> et le montrent sans se cacher. En face, les <b>longs retail</b> entrés tard se font courir dessus. Signature : offre <b>active et assumée</b> (≠ le mur passif de R3). À la réaction sur une <b>zone d'offre connue</b> ou en prise de profit franche.",
 "L'offre reprend la main = <b>redistribution</b> ; continuation baissière attendue.",
 "Prise de profit / pullback. Surveiller un <b>higher low</b> ensuite — un rejet ne casse pas un uptrend.",
 "La borne haute tient ; retour vers le bas de plage.",
 "Turn immédiat et franc ; le niveau se renforce à chaque rejet net répété.",
 "Barre de type SOW / ST-haut qui échoue sous la borne. <b>En lower timeframe (fractal) :</b> cette seule bougie de rejet est une <b>distribution complète en miniature</b> — son sommet = un micro-BC/UTAD (avec ses propres AR/ST en 5m/1m), et l'effondrement vers la clôture basse = le micro-SOW/markdown. Un rejet H4 se lit comme une distribution entière en 5m."),

("r2","bear","R2 · Climax acheteur","— Buying Climax (blow-off)",
 [("w","Wyckoff"),("vsa","VSA")],("bear","baissier (à terme)"),
 "Bougie d'<b>expansion finale</b> : volume climactique, très large spread haussier, <b>clôture milieu/bas</b>. La dernière vague d'achat public est engloutie par l'offre au sommet.",
 "volume <b>≥ ×2.0</b> · spread large ≥ 1.3 ATR · CLV ≤ 0.5 (malgré une bougie haussière) · CVD : forte poussée d'achat agressif <b>sans progrès</b> / qui se retourne · <code>absorption</code> &gt; 0 possible.",
 "Le <b>retail en FOMO</b> (euphorie, news, parabole) achète le sommet ; le <b>composite DISTRIBUE</b> dans cette demande — il vide son inventaire à bon prix. Le volume climactique <b>est</b> le transfert mains fortes → mains faibles. Différence avec R5 : ici un <b>pic d'agression</b> (blow-off), pas une extinction discrète. En <b>fin de markup étendu</b>, sur parabole ou pic de news.",
 "Climax de couverture en fin de rebond ; le markdown reprend derrière.",
 "Le cas emblématique : <b>épuisement de la demande</b>, top de Phase A → AR suit.",
 "Faux breakout climactique au plafond ; distribution qui s'accélère.",
 "<b>Stoppe</b> la tendance haussière et amorce le topping ; pas le turn final mais son point de départ (AR puis ST/UTAD).",
 "BC = événement de <b>Phase A</b> ; son plus-haut fixe le <b>plafond de la plage</b>. (BC « bougie » VSA ≠ BC « événement » Wyckoff.) <b>En lower timeframe :</b> la bougie climactique EST une <b>distribution complète déroulée</b> — la montée = micro-markup, le sommet = micro-BC, puis micro AR/ST/UTAD, et la clôture qui rate le haut = le début du micro-markdown. Le « climax » d'une TF haute est un schéma Wyckoff entier sur la TF basse."),

("r3","bear","R3 · Absorption passive","— Churn / absorption top",
 [("vsa","VSA"),("of","order-flow (iceberg)")],("bear","baissier"),
 "<b>Effort sans résultat</b> : volume élevé mais spread étroit et <b>aucun progrès</b> vers le haut, clôture milieu. Un <b>mur passif</b> avale l'achat agressif — le prix piétine sous la résistance.",
 "volume élevé MAIS spread <b>étroit ≤ 0.7 ATR</b> · progrès net ≈ 0 · <b><code>absorption</code> &gt; 0 avec <code>delta_z</code> &gt; 0</b> (offre qui absorbe) · CVD : gros delta d'achat <b>sans gain de prix</b>.",
 "Le <b>composite pose un gros ordre limite passif (iceberg)</b> et absorbe l'achat <b>sans bouger le prix</b> — il <b>cache son intention</b> : il vend en douce en laissant venir les acheteurs. Le retail achète « la force » sans voir le mur. Signature : offre <b>passive et dissimulée</b> (≠ l'offre active de R1). En <b>distribution silencieuse de Phase B</b>, niveau « défendu » testé plusieurs fois.",
 "L'offre reprend vite au plafond ; redistribution confirmée si une cassure de support suit.",
 "Distribution en cours : l'offre institutionnelle plafonne sans casser encore. Signe précoce.",
 "Plafond défendu par un mur ; si le mur est <i>consommé</i>, le breakout devient possible.",
 "Turn souvent <b>différé de plusieurs barres</b> (le mur tient d'abord, puis lâche). Distribution.",
 "« No result from effort » ; précède typiquement un SOW."),

("r4","bear","R4 · Distribution étalée","— Rolling top / double-triple top (variante)",
 [("w","Wyckoff"),("ta","charting (double top)")],("bear","baissier"),
 "L'offre est écoulée <b>sur plusieurs barres</b>, dans les rebonds successifs. <b>Deux variantes du même mécanisme :</b> <b>hauts déclinants</b> (rolling top) ou <b>hauts ≈ égaux</b> (double/triple top, confirmé à la cassure de la neckline). La faiblesse est dans la <b>structure</b>, pas une bougie.",
 "multi-swing · volume qui <b>décroît</b> rebond après rebond · rallyes = <code>no_demand</code> · CVD : <b>lower highs</b> sur le delta cumulé · cassure de neckline (double top) sur vol ≥ ×1.3 = confirmation.",
 "Le <b>composite écoule graduellement</b> dans chaque rebond — il ne veut <b>pas casser le prix d'un coup</b> (ça déprimerait ses ventes), donc il distribue par paquets en laissant le retail racheter creux et « breakouts ». Chaque rallye plus faible = moins d'acheteurs frais. Signature : distribution <b>patiente et diffuse</b> (≠ le climax en une bougie de R2). En <b>Phase B/C</b>, sommet arrondi, sans catalyseur haussier. <b>C'est la config de BTC à 64 700.</b>",
 "Redistribution : très baissier, chaque lower high recharge l'offre.",
 "Distribution de fin de tendance (ST → LPSY) ; retournement en douceur.",
 "Échec répété à la borne haute ; les tops déclinants « abaissent » la borne.",
 "Markdown <b>graduel</b> ; le signal est dans la géométrie + volume qui sèche. Variante double top : rien n'est confirmé <b>tant que la neckline tient</b>.",
 "Séquence ST → (SOW) → LPSY, Phase B→D. Le double/triple top = même phénomène en charting classique (Edwards &amp; Magee)."),

("r5","bear","R5 · Épuisement","— Exhaustion top / CVD divergence",
 [("of","order-flow"),("vsa","VSA (No Demand / EoRM)")],("bear","baissier"),
 "Le prix <b>revient dans la zone de résistance mais SANS volume</b> : higher high marginal alors que le CVD fait un <b>lower high</b> — la demande agressive <b>s'épuise</b> (elle <i>fond</i>, elle ne frappe pas un mur). La montée n'est plus portée par l'achat, seulement par l'inertie et l'<b>absence temporaire d'offre</b> (cf. §0 bis, no-demand).",
 "prix HH marginal / <b>CVD LH</b> (divergence) · <b>volume nettement SOUS la moyenne sur le retour</b> (≤ ×0.85, souvent <b>×0.5–0.7</b>), en <b>assèchement barre après barre</b> — c'est le <b>volume relatif faible</b> qui signe l'épuisement (≠ absorption = <i>mur</i> à gros volume) · <code>absorption</code> per-barre souvent neutre, <b>le tell est multi-barres</b>.",
 "Personne ne « pousse » : la <b>cohorte acheteuse</b> (suiveurs de tendance, longs tardifs) est <b>à bout</b>. En <b>distribution</b>, c'est souvent le <b>composite qui ramène délibérément le prix dans la zone de résistance</b> — un <b>retour à volume sec</b> — pour <b>vérifier qu'il ne reste plus de demande</b> (et écouler un dernier paquet) : si le retour se fait <b>sans volume</b>, l'offre aura la voie libre pour le markdown. Signature : <b>absence de demande</b> (≠ présence d'offre de R1/R3). En tendance mature, faible participation.",
 "Rebond qui meurt faute d'acheteurs ; le markdown reprend sans rejet violent.",
 "Épuisement de fin de tendance : la hausse manque de carburant. Signe précoce.",
 "La borne haute n'attire plus d'agression — désintérêt pour le niveau.",
 "Reversal <b>par manque de carburant</b>, plus <b>mou</b> qu'un rejet net ou un upthrust ; le turn peut traîner. Guetter la bascule du CVD + une 1ʳᵉ bougie de faiblesse.",
 "« L'effort ne produit plus de résultat » / No Demand / End of a Rising Market. En distribution, ce <b>retour à volume sec dans la zone = un Secondary Test (ST) — voire un LPSY s'il est tardif — qui échoue</b> : le composite confirme l'absence de demande avant de laisser filer le markdown. <b>Distinguer épuisement (le flux s'estompe) d'absorption (le flux frappe un mur).</b>"),

("r6","bear","R6 · Faux franchissement","— Upthrust / UTAD / bull trap",
 [("w","Wyckoff"),("vsa","VSA"),("of","liquidity grab")],("bear","baissier (fort)"),
 "<b>Plus-haut marginal AU-DESSUS de la résistance</b>, spread large, puis <b>clôture sur le bas</b> et reversal en 1–3 barres. Piège les acheteurs de breakout et déclenche les stops. Version <b>terminale</b> (au-dessus de <i>toute</i> la plage, Phase C) = <b>UTAD</b>. <i>(Résolution « ratée » d'un franchissement — les cartes F* y renvoient.)</i>",
 "poke au-dessus · CLV ≤ 0.3 · volume moyen-à-fort · CVD <b>sans expansion</b> / divergent · <code>absorption</code> &gt; 0 (achat piégé rejeté) OU <code>no_demand</code> (poke sans flux).",
 "Le cas le plus <b>manipulé</b> : le <b>composite pousse DÉLIBÉRÉMENT</b> au-dessus de la résistance pour <b>déclencher les stops</b> et <b>attirer les acheteurs de breakout</b>, puis récolte cette liquidité pour remplir ses <b>ventes/shorts</b> — et lâche. Le retail qui « achète la cassure » est le carburant. Signature : offre <b>active + engineering de liquidité</b> (≠ la simple absence d'acheteurs de R5/F3). Au <b>test de Phase C</b>, là où des stops sont massés au-dessus de plus-hauts évidents.",
 "Piège de rebond : « faire semblant » de casser pour aspirer des longs avant de repartir bas.",
 "Ambigu — <b>à distinguer d'un spring</b> : perce puis <b>revient et tient</b> = shakeout/continuation ; perce puis <b>rejette</b> = upthrust. La clôture tranche.",
 "Le cas roi : <b>UTAD</b>, le déclencheur short le plus fort.",
 "Reversal net, souvent rapide ; les <b>longs piégés</b> = carburant baissier. Une <b>mèche au-dessus qui reclôture dessous</b> = le tell.",
 "UT ordinaire (Phase B) vs <b>UTAD</b> (Phase C, terminal, au-dessus de toute la plage). Ne pas appeler « UTAD » n'importe quel poke. <b>En lower timeframe :</b> le poke-puis-rejet est une <b>micro-distribution</b> — le prix marque au-dessus de la ligne (micro Phase D up), toppe (micro-BC), puis micro-SOW de retour ; le piège se construit comme une distribution complète en 5m/1m, ce qui explique la brutalité du reversal."),

("f1","bull","F1 · En force","— Sign of Strength / Jump Across the Creek",
 [("w","Wyckoff (SOS ≡ JAC)")],("bull","haussier"),
 "Mouvement haussier <b>décisif</b> : large spread, clôture sur le haut, rallye rapide. La demande <b>agressive</b> pousse et le prix suit — mouvement honnête.",
 "volume <b>≥ ×1.3</b> (souvent bien plus) · spread ≥ 1.3 ATR · CLV ≥ 0.7 · <b><code>absorption</code> &lt; 0</b> (honnête haussier) · <b>CVD↑ FRANC</b>. Un SOS <b>sans</b> CVD↑ = covering, faux SOS (voir F4).",
 "Le <b>composite initie à l'achat de façon agressive</b> — les mains fortes <b>marquent le prix à la hausse</b> après avoir accumulé ; parfois des <b>shorts piégés qui se couvrent DANS de la vraie demande</b> ajoutent du carburant (≠ F4 où le covering est <i>seul</i>). Le retail suit une <b>vraie impulsion institutionnelle</b>. Signature : demande <b>active et nouvelle</b> (OI↑ + CVD↑). En <b>Phase D de markup</b>, sortie d'accumulation.",
 "Méfiance : un SOS isolé peut être un rebond de redistribution. <b>Exiger la tenue + le back-up.</b>",
 "Le vrai « jump » : plus haute proba de continuation. Chercher le LPS.",
 "Cassure de borne — à confirmer par un back-up (sinon upthrust R6).",
 "Demande au contrôle ; continuation attendue. <b>Non confirmé</b> tant qu'il n'a pas tenu + back-upé (F2).",
 "SOS <b>≡</b> JAC (« saut du ruisseau », Evans). Phase C→D. <i>Note gap :</i> un breakaway gap sur gros volume = variante de F1 ; s'il se comble = piège (R6)."),

("f2","bull","F2 · Retest qui tient","— Break-and-retest / BUEC / LPS / flip",
 [("w","Wyckoff (BUEC ≡ LPS)"),("of","flip en support")],("bull","haussier (fort)"),
 "Le prix casse <b>sur volume</b>, puis <b>revient tester la borne</b> (devenue support) sur <b>volume sec</b>, et <b>tient</b> (higher low). La résistance devient support : <b>changement de polarité</b>. L'offre a disparu — le retest le prouve.",
 "cassure sur vol ≥ ×1.3, PUIS <b>retest sur volume SEC</b> (≈ ×0.4–0.6 du SOS) · <b>higher low</b> au-dessus du niveau · <code>no_supply</code> sur le pullback · <code>absorption</code> ≥ 0 au retest · CVD : pas de vente agressive au retest.",
 "Après le saut du ruisseau, le prix revient et <b>AUCUNE offre ne se présente</b> : les <b>mains faibles sont déjà sorties</b>, le <b>composite tient sa position</b> (il en profite pour ajouter). Le retest sec <b>prouve le contrôle du composite</b>. Signature : <b>offre absente</b> (no-supply). En <b>Phase D</b>, premier higher low au-dessus du niveau cassé.",
 "Un retest qui tient <b>au-dessus</b> d'une résistance cassée = le <b>premier vrai signe de changement de cadre</b> (accu qui se gagne).",
 "Confirmation textbook du SOS ; entrée long à moindre risque.",
 "Valide la sortie de plage : la borne cassée tient en support.",
 "Continuation la <b>plus fiable</b> ; le retest sec = l'offre est épuisée. C'est le <i>vrai</i> « back-up » (sans cassure tenue, pas de back-up).",
 "BUEC <b>≡</b> LPS (« retour au bord du ruisseau »). Phase D."),

("f3","bear","F3 · Sans demande","— No-demand breakout / suspect breakout",
 [("vsa","VSA")],("bear","suspect"),
 "Le prix passe au-dessus de la borne sur <b>volume faible/décroissant</b>, spread étroit, clôture faible. La cassure existe sur le graphe mais <b>personne ne l'accompagne</b>.",
 "volume <b>FAIBLE</b> (&lt; moyenne, souvent &lt; ×0.85) · spread étroit · CLV faible · CVD <b>plat</b> · <code>absorption</code> ≈ 0 ou &gt; 0 (achat absent/rejeté).",
 "Poussée du <b>retail seul</b> / chasseurs de breakout, <b>sans relais institutionnel</b> : le <b>composite est ABSENT</b> — il n'achète pas. Échec <b>passif</b> par manque d'acheteurs — <b>à distinguer de R6</b> : ici personne ne manipule, il n'y a simplement <b>pas de demande</b> (R6 = le composite pousse <i>activement</i> pour piéger). Sur une <b>résistance évidente</b> où le retail se rue « sur le breakout », sans catalyseur.",
 "Quasi toujours un <b>piège</b> en formation (deviendra R6).",
 "Parfois un grind qui finit par tenir (F5) — départager par la <b>tenue</b>, pas la bougie de cassure.",
 "Candidat upthrust ; <b>taux d'échec élevé</b>.",
 "Suspect ; <b>devient souvent un faux breakout (R6)</b>. Ne pas poursuivre une cassure sans demande.",
 "No Demand à la cassure — l'inverse d'un SOS. <i>Note gap :</i> un exhaustion gap qui se comble = variante de F3/R6."),

("f4","amb","F4 · Sur covering / squeeze","— Squeeze-driven breakout",
 [("of","order-flow (lecture OI)")],("amb","selon l'OI"),
 "Cassure <b>brutale</b> à départager : <b>short covering</b> (rachat de shorts, offre qui se retire) ou <b>nouvelle demande</b> (longs qui entrent) ? <b>L'OI en coin tranche</b> — le cas où la lecture OI est décisive.",
 "<b>covering</b> = prix↑ + <b>OI↓</b> (coin) + pic de CVD puis stagnation → <b>fragile</b> ; <b>nouvelle demande</b> = prix↑ + <b>OI↑</b> + CVD soutenu → <b>durable</b> (= F1). Croiser : short_liq en pic = squeeze forcé ; funding.",
 "Ce sont des <b>shorts CONTRAINTS de se racheter</b> (liquidations en cascade) qui propulsent la cassure — <b>pas de nouvelle demande initiatrice</b>. Le composite peut ne pas être impliqué ; c'est un <b>mouvement mécanique de couverture</b>. Une fois les shorts liquidés, <b>plus personne pour acheter</b> → le prix retombe (redevient R6). Signature : OI en <b>baisse</b>. Après un <b>niveau très shorté</b>, crowd short encombré, funding négatif.",
 "Souvent covering pur : <b>ambigu — ne confirme PAS un retournement</b> (penche même vers l'accu : le carburant baissier se retire). Ne pas lire haussier trop vite.",
 "Si OI↑ + demande soutenue = vraie continuation (bascule vers F1).",
 "Le covering peut <b>percer</b> mais rarement <b>tenir</b> sans relais de demande.",
 "Covering seul = cassure <b>fragile</b> qui retombe (R6) ; nouvelle demande = cassure <b>durable</b> (F1). Le <i>signe</i> de l'OI en coin est le discriminant.",
 "Nuance OI du rebond : prix↑ + OI↓ = short covering (« rebond effectif », constructif mais ambigu)."),

("f5","amb","F5 · En grinding","— Slow-grind breakout (accumulation furtive)",
 [("loose","jargon"),("of","order-flow")],("amb","ambigu"),
 "De <b>petites bougies</b> qui rampent au-dessus de la borne sur volume modeste mais <b>persistant</b> / delta légèrement positif ; <b>pas de bougie large unique</b>. Ni climax, ni rejet — une dérive contrôlée.",
 "corps petits · volume modeste <b>régulier</b> · CVD légèrement positif <b>persistant</b> · <code>absorption</code> faible · pas de climax ni de mèche de rejet.",
 "Le <b>composite accumule / marque discrètement en petits paquets</b> pour <b>ne pas se faire repérer</b> (furtif) — le delta légèrement positif persistant trahit qu'<b>un acheteur travaille en silence</b>. À distinguer de F3 : ici <b>demande réelle mais dissimulée</b> (delta+ persistant), là <b>aucune demande</b> (delta plat). En <b>conditions peu liquides</b> ou accumulation furtive.",
 "Souvent une dérive sans conviction qui finit par casser vers le bas.",
 "Peut être une <b>accumulation discrète</b> = constructif <b>SI ça tient</b>.",
 "Ambigu : peut dériver et échouer, ou lentement transformer la borne en support.",
 "<b>Ambigu par nature</b> — trancher par la <b>tenue</b> et le delta cumulé : tient plusieurs barres = réel ; s'effrite = faux (R6).",
 "Pas de définition canonique (jargon). Proche d'une accumulation « silencieuse » si delta et tenue confirment."),
]

# ---- exemples réels (métriques vérifiées sur données BTC, dates CEST) ----
EX = {
 "r1": "<b>BTC/USDT H1 — 16/07 09:00 (rejet depuis ~64 780).</b> Ouverture pile sur la résistance (64 777) puis bougie large de baisse, spread <b>×2.35</b>, <b>CLV 0.22</b> (clôture près du bas), vol ×1.45, <code>absorption</code> −0.60, delta_z −1.07 (vente honnête) ; barre suivante à <b>vol ×4.44</b> en continuation baissière. Théorie R1 (spread large + CLV bas + abs &lt; 0) → <b>validé</b> : l'offre agressive renvoie le prix depuis la résistance.",
 "r2": "<b>BTC/USDT — 14/07 (le sommet 64 744).</b> Poussée finale sur vol <b>×3.1 (H4) / ×3.8 (H1 17:00)</b>, spread ×3.1, OI en repli, qui a <b>marqué LE sommet puis s'est retournée</b>. Le tell climax vs SOS = <b>l'absence de suivi</b> (le prix n'est jamais reparti) → c'est ce climax qui a créé la résistance 64 700 de toute la séquence.",
 "r3": "<b>BTC/USDT H1 — 14/07 18:00 (~64 730, juste sous le sommet 64 744).</b> Achat agressif (delta_z <b>+1.05</b>, <b>OI +3.1 %</b> = nouveaux longs) MAIS <b>spread ×0.73</b> (étroit) et aucun progrès, <code>absorption</code> +0.16. Théorie R3 (gros effort acheteur avalé par un mur, résultat nul) → <b>validé</b> : demande absorbée à la résistance (longs piégés), puis rollover.",
 "r4": "<b>BTC/USDT H4 — 14→17/07.</b> Le sommet <b>64 744</b> (14/07) puis des rebonds <b>déclinants sur volume en repli</b> (~64 6xx, ~64 4xx) — la distribution étalée qui a plafonné 64 700. Théorie R4 (hauts déclinants + volume décroissant + rallyes no-demand) → <b>validé</b> ; c'est le cas dominant de la structure actuelle.",
 "r5": "<b>BTC/USDT H1 — 01/07 06:00 (~59 457).</b> Plus-haut sur vol <b>×0.50</b> (sec) alors que le CVD fait un <b>lower high</b> (Δ −565), suivi d'une <b>chute de 840 pts (&gt; 1.2 ATR)</b>. Théorie R5 (higher high à volume qui s'assèche + divergence CVD → reversal) → <b>validé</b> : épuisement de la demande (sommet local, le prix se retourne faute d'acheteurs).",
 "r6": "<b>BTC/USDT H1 — 15/07 15:00 (poke à 65 164).</b> Dépassement <b>au-dessus de la plage</b> (haut 65 164 &gt; 64 744) sur vol ×2.7, <b>CLV 0.33</b> (clôture dans le bas), puis reversal → le grand markdown des 16–17/07. Théorie R6/UTAD (poke au-dessus de TOUTE la plage + clôture basse + reversal) → <b>validé</b> : le test terminal de la distribution.",
 "f1": "<b>BTC/USDT H1 — 20/07 17:00 (cassure de 65 108).</b> Bougie large (spread ×2.33), <b>CLV 0.95</b> (clôture au sommet), vol <b>×2.83</b>, delta_z <b>+1.29 (CVD franc)</b>, <code>absorption</code> −1.15 (honnête) ; continuation vers 65 8xx puis <b>66 956 (21/07)</b>. Théorie F1/SOS (vol ≥ ×1.3 + CVD↑ franc + clôture haute) → <b>validé</b> : vraie demande, jump across the creek.",
 "f2": "<b>Trois BUEC vérifiés</b> (cassure d'un vrai pivot → back-up sec qui tient → continuation, tout séquentiel) :<br>• <b>H4 11→12/06</b> : cassure de 62 858 (11/06 18:00, C63 606, vol ×1.24) → back-up qui <b>teste le niveau</b> (12/06, low ~62 830–63 100) sur vol ≤ ×0.80 → continuation à <b>64 763</b>.<br>• <b>H1 10/07 03:00</b> : cassure C63 750 (vol ×1.67, delta_z +1.99) → back-up 05:00–09:00 sur vol ×0.51–0.81 tenant &gt; 63 500 → continuation à <b>64 693</b>.<br>• <b>H1 02/07 14:00</b> : cassure de 61 334 (C61 543, vol ×1.76) → back-up 19:00 sur vol ×0.69 → continuation à 61 900.<br>Théorie F2/BUEC (retest à volume sec = no-supply, higher low qui tient) → <b>validé</b> les trois fois.",
 "f3": "<b>BTC/USDT H1 — 12/07 16:00 (cassure ratée de ~64 100).</b> Poussée au-dessus du niveau sur vol <b>×0.39</b> (anémique), CLV 0.74, sans demande, puis <b>repli sous 64 100</b> dans les barres suivantes. Théorie F3/No-Demand (cassure sur volume faible → échec) → <b>validé</b> : personne derrière, la cassure retombe (devient un R6).",
 "f4": "<b>BTC/USDT H4 — 06/07 22:00.</b> Spike vers <b>64 700</b> puis clôture 64 042 (rejeté, CLV 0.41), porté par un <b>OI −2.63 %</b> (coin) = <b>short covering</b>, CVD plat (delta_z +0.04) ; retombe ensuite (07/07 → 63 100). Théorie F4 (prix↑ + OI↓ = covering → fragile) → <b>validé</b> : cassure sans nouvelle demande, elle ne tient pas.",
 "f5": "<b>BTC/USDT H4 — 13→14/06 (64 296 → 64 545).</b> Suite de petits corps haussiers, spread ~×0.67, vol <b>~×0.73 régulier</b>, qui grignotent un plus-haut sans climax. Théorie F5/grinding (petits corps + volume modeste constant + pas de climax) → <b>validé</b> : dérive furtive (constructif seulement si ça tient).",
}


def card_html(c):
    cid, cls, tfr, ten, tags, badge, dfn, foot, actors, dn, up, rg, impl, wyk = c
    tagh = "".join(f'<span class="tag {t}">{x}</span>' for t, x in tags)
    bcls, btxt = badge
    schem, R, cap, vol, cvd = SCH[cid]
    fig = (f'<div class="fig">{svg(schem, R, vol, cvd)}'
           f'<div class="cap">{cap}</div></div>')
    phz = f'<div class="phz">{PHZ[cid]}</div>'
    return f'''<div class="card {cls}" id="{cid}">
<h4>{tfr} <span class="en">{ten}</span> {tagh}<span class="badge {bcls}">{btxt}</span></h4>
{fig}
<p class="def"><b>Définition.</b> {dfn}</p>
<div class="foot"><b>Empreinte.</b> {foot}</div>
<div class="actors"><span class="lbl">Qui agit — contexte participants</span>{actors}</div>
{phz}
<div class="ctx">
<div class="c dn"><b>Downtrend</b>{dn}</div>
<div class="c up"><b>Uptrend</b>{up}</div>
<div class="c rg"><b>Range</b>{rg}</div>
</div>
<p class="impl"><b>Implication cours.</b> {impl}</p>
<p class="wyk"><b>Lien Wyckoff.</b> {wyk}</p>
<div class="ex"><span class="lbl">Exemple réel (données vérifiées)</span>{EX[cid]}
{_charts_html(cid)}</div>
</div>'''

P1 = "".join(card_html(c) for c in CARDS if c[0].startswith("r"))
P2 = "".join(card_html(c) for c in CARDS if c[0].startswith("f"))

HTML = f'''<!doctype html><html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Mémo — Comportement du prix à une résistance</title>
<style>
  :root{{--acc:#1b6b1b;--dis:#a11;--amb:#8a6d00;--ink:#222;--mut:#666}}
  body{{font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;margin:0;color:var(--ink);background:#fff;line-height:1.55}}
  .wrap{{max-width:1180px;margin:0 auto;padding:24px}}
  h1{{font-size:1.55em;margin:0 0 4px}}
  h2{{font-size:1.28em;margin:34px 0 10px;padding-bottom:6px;border-bottom:2px solid #eee}}
  h3{{font-size:1.08em;margin:20px 0 8px}}
  h4{{margin:0 0 6px;font-size:1.02em}}
  h4 .en{{font-size:.82em;color:var(--mut);font-weight:500;font-style:italic}}
  .sub{{color:var(--mut);margin:0 0 14px;font-size:.92em}}
  .muted{{color:var(--mut);font-size:.9em}}
  p{{margin:7px 0}}
  table{{border-collapse:collapse;width:100%;margin:8px 0 12px;font-size:.85em}}
  th,td{{border:1px solid #ddd;padding:7px 9px;vertical-align:top;text-align:left}}
  th{{background:#f4f4f4;font-weight:600}}
  td.k{{white-space:nowrap;font-weight:600}}
  tr:nth-child(even) td{{background:#fcfcfc}}
  .toc{{background:#f7f9fc;border:1px solid #e2e8f0;border-radius:8px;padding:12px 18px;margin:14px 0 4px;font-size:.9em}}
  .toc a{{color:#2456a6;text-decoration:none}}.toc a:hover{{text-decoration:underline}}
  .toc ul{{margin:6px 0;padding-left:20px;columns:2}}
  .lead{{background:#fbfcfe;border:1px solid #e6ebf2;border-radius:8px;padding:14px 18px;margin:12px 0}}
  .leg{{background:#f2f6fb;border:1px solid #d5e2f0;border-radius:8px;padding:11px 16px;margin:12px 0;font-size:.88em}}
  .tree{{background:#fbfcfe;border:1px solid #e6ebf2;border-radius:8px;padding:8px 18px;margin:12px 0;font-size:.9em}}
  .tree ul{{margin:4px 0;padding-left:20px}}
  .tree>ul>li{{margin:8px 0}}
  .tree a{{text-decoration:none;color:#1b3a5c}}.tree a:hover{{text-decoration:underline}}
  .qa{{background:#fef9f3;border:1px solid #f0e0c8;border-radius:8px;padding:14px 18px;margin:12px 0}}
  .qa h3{{margin-top:0;color:#7a5200}}
  .card{{border:1px solid #e3e3e3;border-radius:9px;padding:14px 16px;margin:14px 0;background:#fff}}
  .card.bear{{border-left:4px solid var(--dis)}}
  .card.bull{{border-left:4px solid var(--acc)}}
  .card.amb{{border-left:4px solid var(--amb)}}
  .badge{{font-size:.72em;font-weight:700;border-radius:10px;padding:1px 9px;margin-left:4px;color:#fff;white-space:nowrap}}
  .badge.bear{{background:var(--dis)}}.badge.bull{{background:var(--acc)}}.badge.amb{{background:var(--amb)}}
  .tag{{font-size:.68em;font-weight:600;border-radius:9px;padding:1px 7px;margin-left:3px;white-space:nowrap;border:1px solid #ccc;color:#555;background:#f6f6f6}}
  .tag.w{{border-color:#9db;color:#264;background:#eef7f1}}
  .tag.vsa{{border-color:#c9a;color:#639;background:#f5eefb}}
  .tag.of{{border-color:#9bd;color:#246;background:#eef3fb}}
  .tag.ta{{border-color:#cba;color:#750;background:#fbf5ee}}
  .tag.loose{{border-color:#ccc;color:#888;background:#f2f2f2}}
  .fig{{float:right;margin:0 0 8px 14px;text-align:center}}
  .fig svg{{border:1px solid #eee;border-radius:6px;background:#fff}}
  .fig .cap{{max-width:340px;font-size:.76em;color:var(--mut);margin-top:3px;font-style:italic;text-align:left}}
  .foot{{background:#fafafa;border:1px solid #eee;border-radius:6px;padding:7px 10px;font-size:.9em;margin:8px 0}}
  .foot b{{color:#333}}
  .actors{{background:#fff8ef;border:1px solid #f0e2cc;border-radius:6px;padding:7px 10px;font-size:.88em;margin:8px 0}}
  .actors b{{color:#7a5200}}
  .actors .lbl{{display:block;font-size:.78em;text-transform:uppercase;letter-spacing:.04em;color:#a07400;margin-bottom:2px;font-weight:700}}
  .phz{{background:#f2f6fb;border:1px solid #dbe6f2;border-radius:6px;padding:7px 10px;font-size:.86em;margin:8px 0;color:#2a3f55}}
  .phz b{{color:#1b3a5c}}
  .ex{{background:#eef7f0;border:1px solid #cfe6d4;border-radius:6px;padding:7px 10px;font-size:.86em;margin:9px 0 2px;color:#20402a}}
  .ex .lbl{{display:block;font-size:.78em;text-transform:uppercase;letter-spacing:.04em;color:#2f7a44;margin-bottom:2px;font-weight:700}}
  .ex b{{color:#173a22}} .ex code{{background:#dcefe0}}
  .realchart{{width:100%;max-width:100%;height:auto;border:1px solid #cfe6d4;border-radius:6px;margin:9px 0 0;display:block}}
  .ctx{{display:flex;gap:8px;margin:9px 0;flex-wrap:wrap;clear:both}}
  .ctx .c{{flex:1;min-width:210px;border:1px solid #e6e6e6;border-radius:6px;padding:7px 10px;font-size:.86em}}
  .ctx .c.dn{{background:#fdf2f2;border-color:#f2d4d4}}
  .ctx .c.up{{background:#f1f8f1;border-color:#d2e8d2}}
  .ctx .c.rg{{background:#f6f6f9;border-color:#e0e0ea}}
  .ctx .c b{{display:block;font-size:.82em;text-transform:uppercase;letter-spacing:.04em;color:var(--mut);margin-bottom:2px}}
  .impl{{margin:8px 0 2px}}.impl b{{color:#333}}
  .wyk{{font-size:.87em;color:#555;border-top:1px dashed #ddd;padding-top:6px;margin-top:9px}}
  code{{background:#f2f2f2;border-radius:4px;padding:0 4px;font-size:.9em}}
  .kbd{{font-variant-numeric:tabular-nums}}
  @media print{{.card{{page-break-inside:avoid}}h2{{page-break-before:always}}.toc{{display:none}}}}
</style></head>
<body><div class="wrap">

<h1>Mémo — Comportement du prix à une résistance</h1>
<p class="sub">Les comportements possibles quand l'<b>offre arrive à une résistance</b> : les
<b>retournements</b> (le prix cale et se retourne) et les <b>franchissements</b> (le prix casse).
Chaque cas : schéma 3 panneaux (bougies + ligne de résistance, volume vs moyenne, CVD), label canonique (EN) + nom FR, empreinte
volume/spread/CLV, <b>« qui agit »</b> (retail / composite), <b>contexte de marché (cycle/régime) +
phase Wyckoff + signaux avant-coureurs</b>, lecture par contexte macro, implication cours, et lien
Wyckoff, un <b>exemple réel vérifié</b> et son <b>graphe annoté réel</b> (3 panneaux prix/volume/CVD,
données BTC, dates CEST). Tags d'origine —
<span class="tag w">Wyckoff</span> <span class="tag vsa">VSA</span>
<span class="tag of">order-flow</span> <span class="tag ta">charting classique</span>
<span class="tag loose">jargon</span>.</p>

<div class="toc">
<b>Sommaire</b>
<ul>
<li><a href="#fond">0 · Fondations — le principe unique</a></li>
<li><a href="#nodemand">0 bis · No-demand : pourquoi le prix monte sans demande ?</a></li>
<li><a href="#synth">Synthèse — arbre de décision + table récap</a></li>
<li><a href="#p1">Partie 1 — Les retournements (6)</a>
  <ul style="columns:1">
    <li><a href="#r1">R1 · Rejet actif</a></li><li><a href="#r2">R2 · Climax acheteur</a></li>
    <li><a href="#r3">R3 · Absorption passive</a></li><li><a href="#r4">R4 · Distribution étalée</a></li>
    <li><a href="#r5">R5 · Épuisement</a></li><li><a href="#r6">R6 · Faux franchissement / UTAD</a></li>
  </ul></li>
<li><a href="#p2">Partie 2 — Les franchissements (5)</a>
  <ul style="columns:1">
    <li><a href="#f1">F1 · En force (SOS / JAC)</a></li><li><a href="#f2">F2 · Retest qui tient</a></li>
    <li><a href="#f3">F3 · Sans demande</a></li><li><a href="#f4">F4 · Sur covering / squeeze</a></li>
    <li><a href="#f5">F5 · En grinding</a></li>
  </ul></li>
<li><a href="#eq">Annexe A — Table d'équivalence des vocabulaires</a></li>
<li><a href="#pieges">Annexe B — Pièges de labeling</a></li>
<li><a href="#btc">Application — BTC à 64 700 (juillet 2026)</a></li>
</ul>
</div>

<div class="leg">
<b>Comment lire les schémas (3 panneaux).</b>
<b>Prix</b> : bougies (vert = clôture ≥ ouverture, rouge = clôture &lt; ouverture) +
<b>ligne rouge pointillée = résistance</b>.
<b>Vol</b> : volume par barre (bleu) + <b>ligne pointillée « moy. » = volume moyen</b> → barre
au-dessus = volume fort, en dessous = <b>volume faible</b> (c'est le <i>volume relatif</i> qui compte).
<b>CVD</b> : delta cumulé (flux agressif net) — c'est sa <b>divergence avec le prix</b> qui parle
(prix qui monte + CVD qui baisse/plafonne = pas de demande réelle).
</div>

<h2 id="fond">0 · Fondations — le principe unique</h2>
<div class="lead">
<p><b>Ce qui définit une résistance.</b> Une zone (jamais une ligne au rasoir) où l'offre a
historiquement plafonné le prix : une étagère de clôtures/opens, la borne haute d'une plage, un
ancien plancher cassé, un plus-haut de référence. On la lit toujours comme une <b>bande</b>.</p>
<p><b>Le principe qui gouverne tout : effort vs résultat.</b> À une résistance, il y a <i>toujours</i>
de l'offre (preneurs de profit, anciens longs, shorts). La question n'est jamais « y a-t-il de
l'offre ? » — il y en a toujours. La question est : <b>cette offre est-elle avalée (le prix tient ou
passe) ou fait-elle tomber le prix ?</b> Et surtout : <b>qui</b> est de chaque côté — le composite
accumule-t-il, distribue-t-il, ou piège-t-il ?</p>
<p><b>L'opérateur composite vs le retail.</b> Wyckoff lit le marché comme un jeu entre le <b>Composite
Operator</b> (institutions / mains fortes, qui accumulent bas et distribuent haut) et le <b>public</b>
(retail, qui achète haut en FOMO et vend bas en panique). Le bloc « Qui agit » de chaque carte
explicite cette signature.</p>
<p><b>Deux familles de blocage</b> (retournement) : l'<b>absorption</b> — l'agression frappe un
<i>mur passif</i> d'ordres limites (iceberg), gros volume mais le prix ne bouge pas — et
l'<b>épuisement</b> — l'agression <i>s'estompe</i>, le volume fond. <b>Deux familles de
franchissement</b> : <b>en force</b> (demande agressive, CVD↑ franc) et <b>par retrait de l'offre</b>
(no-supply : l'offre disparaît, le prix dérive au-dessus sans effort).</p>
<p><b>Ordre de lecture (hiérarchie VSA) : volume → OI → CVD/tierces.</b> Chiffrage de référence :
<span class="kbd">climax ≥ ×2.0 · SOS ≥ ×1.3 · test ≤ ×0.85 · spread large ≥ 1.3 ATR · spread étroit
≤ 0.7 ATR · CLV reclaim ≥ 0.5</span>. <code>absorption</code> : <b>&gt; 0 = flux rejeté</b>,
<b>&lt; 0 = mouvement honnête</b>. <b>Règle par défaut : résistance dans un downtrend =
redistribution jusqu'à preuve du contraire.</b></p>
</div>

<h2 id="nodemand" style="border:none;margin-bottom:0">0 bis · No-demand : pourquoi le prix monte sans demande ?</h2>
<div class="qa">
<p><b>La question.</b> Sur une barre <i>no-demand</i>, le prix MONTE alors qu'on dit qu'il n'y a « pas
de demande ». Contradiction apparente — et est-ce que ça veut dire qu'il n'y a pas d'offre non plus ?</p>
<p><b>Le prix ne monte pas grâce à l'achat — il monte parce que l'offre s'est momentanément
retirée.</b> Le prix est le point où un ordre d'achat rencontre un ordre de vente. Si les vendeurs
<b>retirent leurs offres</b> (ils attendent plus haut, ou le composite ne défend pas encore le
niveau), il suffit d'un <b>tout petit achat</b> pour faire glisser le prix jusqu'à l'offre suivante,
plus haute. Résultat : <b>prix qui monte + volume faible</b> = la signature exacte du no-demand. Le
mouvement flotte « dans le vide » du carnet, il n'est pas <i>poussé</i> par de la demande.</p>
<p><b>Alors, pas d'offre non plus ? Oui — mais localement et temporairement.</b> À cet instant précis
l'offre est <b>mince</b> (c'est pour ça que le prix dérive si facilement sur peu de volume). Mais
c'est une absence <b>passagère</b> : les vendeurs se sont écartés, ils n'ont pas disparu. Le poids
du diagnostic porte donc sur l'<b>autre</b> jambe — la demande manquante :</p>
<ul>
<li><b>Ce qui compte, c'est l'absence de DEMANDE professionnelle.</b> Dans un contexte où une vraie
avance exigerait de l'achat institutionnel pour se poursuivre, un up-bar à volume faible dit que
<b>le smart money n'est PAS en train d'acheter</b>. La montée n'a pas de sponsor — elle est creuse.</li>
<li><b>C'est fragile parce que l'offre va revenir.</b> Dès que les vendeurs re-postent leurs offres
(ou que le composite se remet à distribuer), il n'y a <b>aucun acheteur sérieux dessous</b> pour
absorber — et le prix retombe. Le no-demand est donc lu <b>dans une résistance / après une hausse</b>
comme le tell que le mouvement haut n'a plus de carburant.</li>
</ul>
<p><b>Le miroir — no-supply.</b> L'inverse exact : une barre de <b>baisse à volume faible</b> = le
prix descend mais <b>aucune vente agressive</b> = l'offre est absente = <b>haussier</b> (les mains
fortes ne lâchent pas). Même mécanique de carnet, sens opposé.</p>
<p><b>À retenir.</b> No-demand ≠ « le prix monte donc c'est fort ». No-demand = « le prix monte
<i>faute d'offre</i>, mais <b>sans achat pour le soutenir</b> » → creux, non confirmé, retournement
probable quand l'offre revient. C'est l'une des deux divergences effort-vs-résultat (l'absorption
étant l'autre) — voir R5, où le no-demand est le mécanisme d'un rebond d'épuisement.</p>
</div>

<h2 id="synth">Synthèse — arbre de décision + table récap</h2>
<p class="sub">Partir de l'observation live pour router vers le bon cas, puis vérifier avec la table.</p>
<div class="tree">
<p><b>L'offre arrive à la résistance. Le prix CASSE-t-il (clôture au-dessus) ou est-il REPOUSSÉ ?</b></p>
<ul>
<li><b>REPOUSSÉ → retournement</b>
  <ul>
  <li>Mèche AU-DESSUS de la ligne puis clôture dessous ? → <a href="#r6"><b>R6 Upthrust</b></a> (CVD sans expansion)</li>
  <li>Volume ÉNORME (≥ ×2), très large bougie, clôture qui rate le haut ? → <a href="#r2"><b>R2 Climax</b></a></li>
  <li>Gros volume mais spread ÉTROIT, aucun progrès, CVD↑ sans le prix ? → <a href="#r3"><b>R3 Absorption</b></a></li>
  <li>Bougie large ROUGE franche, volume qui gonfle, CVD↓ en phase ? → <a href="#r1"><b>R1 Rejet actif</b></a></li>
  <li>Volume qui S'ASSÈCHE (≤ ×0.85), higher high mou, CVD en lower high ? → <a href="#r5"><b>R5 Épuisement</b></a></li>
  <li>Plusieurs rebonds en LOWER HIGHS sur des barres, volume décroissant ? → <a href="#r4"><b>R4 Distribution étalée</b></a></li>
  </ul></li>
<li><b>CASSE → franchissement</b>
  <ul>
  <li>Volume ≥ ×1.3 + CVD↑ FRANC + clôture haute ? → <a href="#f1"><b>F1 En force</b></a></li>
  <li>Cassure puis RETEST à volume SEC qui tient (higher low) ? → <a href="#f2"><b>F2 Retest / BUEC</b></a></li>
  <li>Volume FAIBLE, CVD plat, personne derrière ? → <a href="#f3"><b>F3 Sans demande</b></a> (souvent → R6)</li>
  <li>OI↓ + pic de CVD puis stagnation (rachat de shorts) ? → <a href="#f4"><b>F4 Squeeze / covering</b></a></li>
  <li>Petits corps réguliers, delta+ persistant, pas de climax ? → <a href="#f5"><b>F5 Grinding</b></a></li>
  </ul></li>
</ul>
</div>
<table>
<thead><tr><th>Cas</th><th>Volume relatif</th><th>CVD</th><th>Tell décisif</th><th>Verdict</th></tr></thead>
<tbody>
<tr><td class="k">R1 Rejet actif</td><td>fort sur le rejet</td><td>↓ en phase</td><td>bougie large rouge, clôture au plancher</td><td>baissier</td></tr>
<tr><td class="k">R2 Climax</td><td>≥ ×2 climactique</td><td>pic puis se retourne</td><td>blow-off, clôture qui rate le haut</td><td>baissier (à terme)</td></tr>
<tr><td class="k">R3 Absorption</td><td>fort, spread étroit</td><td>↑ SANS le prix</td><td>effort sans résultat (mur passif)</td><td>baissier</td></tr>
<tr><td class="k">R4 Distribution étalée</td><td>décroissant</td><td>lower highs</td><td>hauts déclinants multi-barres</td><td>baissier</td></tr>
<tr><td class="k">R5 Épuisement</td><td><b>≤ ×0.85, s'assèche</b></td><td>lower high (diverge)</td><td>retour dans la zone SANS volume</td><td>baissier</td></tr>
<tr><td class="k">R6 Upthrust</td><td>moyen-fort</td><td>sans expansion</td><td>mèche au-dessus, clôture sous</td><td>baissier (fort)</td></tr>
<tr><td class="k">F1 En force</td><td>≥ ×1.3</td><td>↑ FRANC</td><td>cassure large, clôture haute</td><td>haussier</td></tr>
<tr><td class="k">F2 Retest / BUEC</td><td>cassure forte, retest sec</td><td>plat au retest</td><td>higher low qui tient au-dessus</td><td>haussier (fort)</td></tr>
<tr><td class="k">F3 Sans demande</td><td>faible</td><td>plat</td><td>cassure sans personne derrière</td><td>suspect</td></tr>
<tr><td class="k">F4 Squeeze / covering</td><td>pic puis stagne</td><td>pic puis stagne</td><td>OI↓ (rachat de shorts)</td><td>fragile</td></tr>
<tr><td class="k">F5 Grinding</td><td>modeste, constant</td><td>+ légère persistante</td><td>grignotage furtif, pas de climax</td><td>ambigu</td></tr>
</tbody></table>

<h2 id="p1">Partie 1 — Les retournements à la résistance</h2>
<p class="sub">Le prix cale et se retourne <b>sans franchir durablement</b>. Six mécanismes distincts,
du plus franc (offre agressive) au plus manipulé (piège au-dessus).</p>
{P1}

<h2 id="p2">Partie 2 — Les franchissements de la résistance</h2>
<p class="sub">Le prix <b>casse</b>. Cinq mécanismes distincts, classés par <b>qui/quoi porte la
cassure</b>. Un franchissement qui <b>échoue</b> = <b><a href="#r6">R6 (upthrust)</a></b>, non redoublé
ici. Un breakout n'est un <i>vrai</i> SOS qu'<b>après tenue + back-up</b>.</p>
{P2}

<h2 id="eq">Annexe A — Table d'équivalence des vocabulaires</h2>
<p class="sub">Le même phénomène, plusieurs noms selon l'école — pour cross-labeliser sans confondre
doctrine et jargon.</p>
<table>
<thead><tr><th>Phénomène</th><th>Wyckoff <span class="tag w">W</span></th>
<th>VSA <span class="tag vsa">VSA</span></th><th>Order-flow <span class="tag of">OF</span></th>
<th>Charting <span class="tag ta">TA</span></th></tr></thead>
<tbody>
<tr><td class="k">Faux breakout qui piège les longs</td><td>Upthrust / UTAD</td><td>Upthrust (bougie)</td><td>False breakout / bull trap / stop-run</td><td>(échec, sans nom)</td></tr>
<tr><td class="k">Vrai breakout en conviction</td><td>SOS / JAC</td><td>up-bar large, gros vol, clôture haute</td><td>break-and-go / delta positif</td><td>breakout valide</td></tr>
<tr><td class="k">Retest qui tient</td><td>LPS / BUEC</td><td>No Supply sur le pullback</td><td>break-and-retest / flip en support</td><td>throwback qui tient</td></tr>
<tr><td class="k">Offre avalée, pas de progrès</td><td>« no result from effort »</td><td>Churn / effort-vs-résultat</td><td>Absorption / iceberg</td><td>(sans nom)</td></tr>
<tr><td class="k">La demande s'épuise au sommet</td><td>demande épuisée (Phase A)</td><td>No Demand / End of Rising Market</td><td>Exhaustion / divergence CVD</td><td>top à volume déclinant</td></tr>
<tr><td class="k">Sommet climactique (blow-off)</td><td>Buying Climax (Phase A)</td><td>Buying Climax (bougie)</td><td>pic d'épuisement acheteur</td><td>climax / blow-off</td></tr>
</tbody></table>

<h2 id="pieges">Annexe B — Pièges de labeling (à ne jamais confondre)</h2>
<table>
<thead><tr><th>Piège</th><th>La règle</th></tr></thead>
<tbody>
<tr><td class="k">« AR » ambigu</td><td>Automatic <b>Rally</b> (accumulation, HAUT) vs Automatic <b>Reaction</b> (distribution, BAS). Même sigle, sens opposé.</td></tr>
<tr><td class="k">« BC » — granularité</td><td>Buying Climax = <b>événement de Phase A</b> en Wyckoff, <b>bougie unique</b> en VSA.</td></tr>
<tr><td class="k">Upthrust vs UTAD</td><td>Upthrust <b>ordinaire</b> (Phase B) ≠ <b>UTAD</b> (Phase C, <b>terminal, au-dessus de TOUTE la plage</b>).</td></tr>
<tr><td class="k">SOS ≡ JAC, LPS ≡ BUEC</td><td>Synonymes exacts (métaphore du ruisseau d'Evans). Aucune différence doctrinale.</td></tr>
<tr><td class="k">Creek vs Ice</td><td><b>Creek</b> = résistance franchie vers le HAUT (accu). <b>Ice</b> = support cassé vers le BAS (distrib).</td></tr>
<tr><td class="k">Absorption vs Épuisement</td><td><b>Absorption</b> (R3) = mur passif (gros volume, pas de mouvement). <b>Épuisement</b> (R5) = l'agression s'estompe (volume qui fond).</td></tr>
<tr><td class="k">Sans demande (F3) vs Upthrust (R6)</td><td><b>F3</b> = <b>absence</b> passive d'acheteurs. <b>R6</b> = le composite pousse <b>activement</b> pour piéger. Passif vs manipulé.</td></tr>
<tr><td class="k">« 50–70 % des breakouts échouent »</td><td>Heuristique répétée mais <b>non sourcée rigoureusement</b> — à citer comme intuition, pas comme un fait.</td></tr>
</tbody></table>

<h2 id="btc">Application — BTC/USDT à 64 700 (juillet 2026)</h2>
<div class="lead">
<p><b>Contexte (top-down).</b> Plage sous le sommet macro (ST-haut 67 292) ; le prix a rallié vers
64 700 puis y a buté. Par défaut, résistance testée dans un cadre non haussier confirmé =
<b>redistribution jusqu'à preuve du contraire</b>.</p>
<table>
<thead><tr><th>Ce qu'on observe</th><th>Cas du mémo</th><th>Lecture participants</th></tr></thead>
<tbody>
<tr><td class="k">Triple lower high 64 700 → 64 608 → 64 425</td><td><b>R4 · Distribution étalée</b> (lower highs)</td><td>Le composite écoule dans chaque rebond ; le retail rachète des breakouts de plus en plus faibles.</td></tr>
<tr><td class="k">Bougie 13/07 00:00 : chute large, CLV ≈ 0.05, vol ×1.7, <code>absorption</code> −3.1</td><td><b>R1 · Rejet actif</b></td><td>Offre <b>agressive assumée</b> (absorption &lt; 0 = honnête) — pas un mur passif.</td></tr>
<tr><td class="k">OI +6 % (100→106 k coin) sur la baisse ; longs liquidés ; foule 62 % long</td><td>signature <b>distribution</b> (≠ F4 covering)</td><td>Shorts <b>neufs</b> qui gagnent + longs piégés — l'OI <b>monte</b>, l'inverse d'un covering (F4 = OI↓).</td></tr>
<tr><td class="k">Aucun SOS avec CVD↑ franc ; aucun retest tenu au-dessus de 64 700</td><td><b>F1 / F2 absents</b></td><td>Le composite ne <b>marque pas à la hausse</b> — 64 700 n'a jamais été cassé ni tenu.</td></tr>
</tbody></table>
<p><b>Verdict via la grille.</b> BTC est en <b>Partie 1</b>, combinant <b>R4</b> (distribution étalée,
dominant) et <b>R1</b> (rejet actif du 13/07). <b>Aucun cas de Partie 2</b> valide. Pour basculer
haussier : <b>F1</b> (SOS de 64 700, CVD↑ franc, OI↑, vol ≥ ×1.3) <b>puis F2</b> (retest tenu). Tant
qu'ils sont absents, la grille penche distribution, et <b>61 705</b> (higher low = ligne du markup)
reste le juge de paix.</p>
</div>

<p class="muted" style="margin-top:24px;border-top:1px solid #eee;padding-top:10px">
Mémo de référence — 11 comportements du prix à une résistance, chacun avec schéma bougies, mécanisme,
participants, phase probable et signaux avant-coureurs. Lecture volume → OI (coin) → CVD/tierces, à
froid. Sources : Wyckoff (SMI / Evans / opérateur composite), VSA (Tom Williams <i>Master the
Markets</i>, Coulling), order-flow (absorption / exhaustion / iceberg), charting (Edwards &amp; Magee).</p>

</div></body></html>'''

with open(os.path.join(_BASE, "memo_comportement_resistance.html"), "w", encoding="utf-8") as f:
    f.write(HTML)
print("written", len(HTML), "bytes")
