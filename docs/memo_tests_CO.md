# Mémo — Les TESTS du Composite Operator

> ⚠️ **Errata** : ce premier mémo contient des erreurs (dates et attributions d'auteurs, définition
> de la barre de test de Williams, « test sec sans réponse = neutre », LPS vs BUEC, origine des
> termes…). Version vérifiée et approfondie : `docs/memo_deep_focus_test_CO.html` (§10 Errata).

Volet « campagne & vérification » de la méthode : comment le CO vérifie qu'une campagne est prête.
Mémos frères : mémo théorie (`theory_table.py` → `memo_theorie.html`) et mémo comportement à la
résistance (UTAD, LPSY, upthrust).

**Seuils chiffrés = ceux du screener** (`config.yaml` → `Thresholds`) :
`test_vol ≤ ×0.85` · `narrow_spread_atr ≤ 0.7` · `climax_vol ≥ ×2.0` · `sos_vol ≥ ×1.3` ·
`wide_spread_atr ≥ 1.3` · `reclaim_clv 0.5`.

> Note d'honnêteté : la doctrine classique (Wyckoff, Evans, Pruden, Williams) = prix + volume.
> OI / CVD / absorption sont nos overlays modernes (cohérents avec la logique du CO, absents des
> textes d'origine). Fiches auteurs = paraphrases, aucune citation verbatim.

---

## 1 · Pourquoi le CO teste

Campagne = **construire la cause** (absorber le flottant) → **vérifier** (le test) → **récolter
l'effet** (markup). Cinq raisons cumulatives :

| # | Raison | Contenu |
|---|---|---|
| 1.1 | **Coût** | En accumulation le CO est faiseur de prix passif ; en markup il devient preneur de prix (lève les offres). Marquer à la hausse avec du flottant restant = offrir une sortie améliorée aux faibles. Markup raté sur offre trop lourde = inventaire trop cher + campagne à replacer plus bas (double coût). |
| 1.2 | **Asymétrie d'information** | Le CO connaît SA position, pas l'offre résiduelle des autres (longs piégés plus haut / overhead supply, shorts en gain, autres opérateurs). Le test est son seul instrument de mesure du monde extérieur. |
| 1.3 | **Fiabilité** | La meilleure réponse est l'**absence de volume**. Un volume présent est ambigu ; un volume absent ne se truque pas. Effort-vs-résultat retourné : pas d'effort vendeur + prix qui tient = plus rien à vendre. |
| 1.4 | **Springboard** | « On the springboard » = préparation complète. C'est un **verdict de tests** : tant que les retours sur la zone basse sont volumiques → pas sur le springboard ; retour sec et tenu → il l'est. |
| 1.5 | **Héritage opérationnel** | Les pools 1910-30 sondaient réellement (vendre un paquet, retirer les bids, acheter bruyamment). Le test wyckoffien = trace sur la bande de ces sondages. Reconnaissance avant l'offensive. |

**Miroir distribution** : offre ↔ demande — le CO distributeur teste s'il reste des acheteurs
(*no demand*) avant le markdown.

---

## 2 · Conditions de validité — les 5 sont TOUTES nécessaires

Test = retour vers une zone où de l'offre s'est manifestée (low de climax, spring, shakeout, borne
cassée) pour mesurer ce qu'il en reste.

| # | Condition | Seuil (screener) | Ce que ça prouve |
|---|---|---|---|
| 1 | Volume **SEC** — sous la moyenne ET < volume du passage précédent sur la zone | `vol_ratio ≤ 0.85` | plus de vendeurs actifs sur la zone |
| 2 | Spread **ÉTROIT** | `spread_atr ≤ 0.7` | ni panique ni poursuite |
| 3 | **Borne tenue** — higher low | `low(test) > low(spring/SC)` | la demande défend plus haut |
| 4 | **Clôture qui répond** | `clv ≥ ~0.5` | les acheteurs reprennent la barre |
| 5 | **Contexte** — suit un événement qui a RETIRÉ de l'offre (climax, spring, shakeout, SOS) | position dans la séquence | un test sans cause ne teste rien |

- **Condition 5 = celle qu'on oublie** : une bougie sèche/étroite au milieu de nulle part n'est PAS
  un test. Séquence d'abord, test ensuite (règle top-down).
- **Crypto (+2)** : **OI plat/↓** sur le test (personne ne s'engage contre la zone) et **absorption
  ≈ 0**. Un « test » avec **OI qui MONTE n'est pas un test** : quelqu'un s'engage, question non réglée.

---

## 3 · Typologie des tests

### 3.1 Vue d'ensemble (accumulation)

| Test | Phase | Ce qu'il teste | Signature valide |
|---|---|---|---|
| **ST** | A→B | zone du SC : panique épuisée ? | vol < climax, spread rétréci, creux ≥ SC |
| **Tests de Phase B** (STs répétés) | B | offre résiduelle à chaque retour sur la borne basse | volume des creux qui **DÉCROÎT** test après test |
| **SPRING** (lui-même un test) | C | test ULTIME : stop-run sous le plancher | pénétration + rejet (3 types, §3.3) |
| **Test du spring** | C | le low du spring : tout est délogé ? | volume ENCORE plus sec que le spring + creux plus haut + clôture ferme |
| **LPS successifs** | D | la demande à chaque repli du canal naissant | replis secs, higher lows en escalier |
| **BUEC** | D→E | la borne FRANCHIE : les vendeurs reviennent-ils ? | retour sec SUR l'ancienne résistance, qui tient |
| **No-supply bar** (VSA) | toutes | version 1 bougie | baisse étroite, vol < 2 barres précédentes, confirmée par la réponse haussière |

**Miroir distribution** : ST du BC · UT (test de la demande en Phase B) · UTAD + son test · LPSY
(test du support cassé = no-demand rally sous la glace).

### 3.2 LPS successifs (Phase D) vs BUEC — à ne pas confondre

Doctrinalement le BUEC est une forme de LPS (Evans), mais ils ne testent ni la même chose, ni au
même endroit, ni au même moment.

| | **LPS successifs** (dans le canal) | **BUEC** (Back-Up to the Edge of the Creek) |
|---|---|---|
| Moment | **AVANT** la cassure de la borne haute (entre spring/test et JAC) | **APRÈS** la cassure (JAC/SOS majeur) — transition D→E |
| Lieu | **dans** la plage : résistances mineures internes devenues supports, mid-range, sommet du spring | **UN** endroit : le bord du creek = ancienne résistance majeure franchie, testée par au-dessus |
| Ce qui est testé | la **demande** : les acheteurs reviennent-ils plus haut ? la demande publique prend-elle le relais ? | le **changement de polarité** : l'ancienne offre a-t-elle disparu ? résistance → support ? |
| Nombre | **plusieurs** (LPS1, LPS2… en escalier) | typiquement **un** (parfois deux) ; beaucoup = la sortie ne tient pas |
| Volume | replis secs (≤ ×0.85), poussées intermédiaires de plus en plus volumiques | retour SEC impératif ; volume vendeur fort au bord = cassure remise en cause (possible upthrust) |
| Invalidation | un LPS casse le low du LPS précédent → retour Phase B (voire C) | clôture **dans** la plage → le JAC a échoué → upthrust de la borne, pas SOS |
| Fonction CO | jauge de maturité : « la demande porte-t-elle ? puis-je franchir ? » | contrôle de sortie : « la sortie est-elle définitive ? » |

Image d'Evans : le scout s'approche du bord N fois et reprend de l'élan (**LPS**), saute avec élan =
volume (**JAC**), puis revient au bord vérifier que la berge tient (**BUEC**). Avant / après le saut.

### 3.3 Les 3 types de spring (Pruden/SMI)

Numérotation variable selon les sources → se fier au **comportement (pénétration × volume)**.
Plus la pénétration est profonde et volumique, plus il restait d'offre, plus la vérification exigée
est lourde.

| Type | Pénétration | Volume | Révèle | Réaction CO | Test |
|---|---|---|---|---|---|
| **#3** effleurement sec (le plus haussier) | minime, quelques fractions d'ATR, souvent en mèche | SEC (≤ moyenne) | plancher déjà vide | feu vert immédiat — il est son propre test | **aucun requis** ; reclaim même barre/suivante, SOS rapide ; souvent la dernière bougie basse |
| **#2** secousse absorbée (standard) | modérée (quelques dixièmes d'ATR), quelques barres sous la borne possibles | moyen à soutenu | il restait de l'offre, achetée d'un bloc — absorbée ≠ épuisée | NE lance PAS le markup ; laisse/provoque le retour au low | **test du spring REQUIS** : volume nettement inférieur + creux plus haut ; séquence typique 3-10 barres |
| **#1** terminal shakeout (le plus violent) | profonde, expansion de spread, parfois plusieurs ATR | FORT à climactique | transfert massif d'offre ; si reclaim rapide = le CO a tout ramassé | vérification **OBLIGATOIRE, parfois multiple** — plus le shakeout est gros, plus la vérif doit être propre | un ou plusieurs retours secs à volume décroissant. Si réponse explosive (squeeze) → test **différé en back-up** sur la zone reconquise |

**Piège type #1** : sans reclaim rapide, ce n'est pas un shakeout mais une vraie cassure → lire la
clôture (réintègre ?) et, en crypto, l'absorption (flux rejeté ?) et l'OI (shorts squeezés ?).

### 3.4 La règle de Tom Williams

**Un test sur volume FORT est un test raté — il devra être re-testé.**

- **Test VSA** : marquer rapidement le prix à la baisse dans une zone de gros volume de vente passé.
  Barre idéale : baisse, spread étroit, volume < 2 barres précédentes, clôture mi-range ou haute —
  « on a ouvert la trappe, rien n'est tombé ».
- **Pourquoi le volume fort invalide** : des vendeurs étaient encore là (même si la clôture tient =
  absorption). Le pro sait qu'il reste de l'offre, pas combien → il ne lance pas de markup au-dessus
  d'une offre non mesurée → il **reviendra** jusqu'à un passage SEC. D'où doubles/triples tests :
  chaque test volumique prend rendez-vous pour le suivant.
- **Conditions annexes** : (a) le **fond** (background) prime — même geste sur fond de distribution =
  piège / no demand ; (b) la **réponse valide** le test — test sec sans réponse = pas de demande =
  neutre ; (c) **test en tendance** = signal de continuation (petite baisse sèche dans un markup).

**Traduction seuils** :
- **Test validé** = `vol_ratio ≤ 0.85` ET vol < vol des 2 barres précédentes ET `clv ≥ 0.5`, sur fond
  de climax/spring récent, suivi d'une **réponse haussière ≤ 3 barres**.
- **Test raté (à re-tester)** = même position mais `vol_ratio ≥ ~1.5` → noter le niveau, attendre le
  retour suivant : c'est LUI qui décide.

---

## 4 · Matrice situation → lecture → réaction du CO → manifestations

Cadre : accumulation présumée, retour sur une zone testée. Symétrique en distribution. On ne voit
jamais le CO, on voit ses traces.

| # | Situation | Lecture | Réaction du CO | Manifestations sur le prix |
|---|---|---|---|---|
| 1 | Volume **SEC** + borne tenue + clôture ferme (≤ ×0.85, ≤ 0.7 ATR, higher low) | offre épuisée, question réglée | **engage le markup** : retire ses ventes de camouflage, remonte ses bids, achète agressivement au marché (1-2 barres calmes de plus possibles) | sous 1-3 barres : bougies de demande à spread croissant, clôtures hautes, volume qui revient sur la hausse ; HH rapides, pas de retour au low ; JAC/SOS vite |
| 2 | Volume **FORT** (≥ ×1.5-2) mais clôture qui **tient** (clv ≥ 0.5) | offre présente mais **absorbée** | prolonge l'absorption (bids passifs échelonnés), ne poursuit pas ; plus tard **retire son soutien** pour provoquer le re-test sec (Williams) | rallye mou sans follow-through, plafond mi-plage, retour sur la zone ; doubles/triples creux à **volume décroissant** = signature de la campagne qui mûrit |
| 3 | Volume **FORT** + clôture **FAIBLE** (clv ≤ 0.3) / borne cassée, pas de reclaim | offre dominante, test échoué | **se retire** : annule ses bids, peut alléger dans les rebonds, laisse chercher plus bas et **replace la campagne** | clôtures sous la zone, rebonds qui calent SOUS l'ancien plancher (LPSY), expansion baissière ; plus tard un nouveau climax plus bas |
| 4 | Test **SEC** mais **aucune réponse** | no supply + no demand : vide des deux côtés | **attend** (laisser mûrir) ou **anime** (achats voyants à volume léger, plus-hauts visibles) | plage qui s'éternise, contraction, volume global ↓ (apathie) ; poussées faible volume sans suite ; surveiller le 1er vrai volume directionnel |
| 5 | **Pas de test** (V-bottom) | vérification incomplète (ou choc exogène) | **teste plus tard** : au 1er repli retire ses bids et laisse retomber vers la borne franchie pour voir qui vend → back-up = test différé | verticalité puis pullback « sans soutien » ; sec + tient la borne = BUEC validé ; retombe dans la plage sur volume = sortie ratée |
| 6 | Tests secs réussis **puis UPTHRUST** de la borne haute | contradiction — **le cadre est peut-être faux** | accumulateur : défend le retour, rachète la baisse ; distributeur : l'upthrust était SON test de la demande, il vend les rebonds | tri dans les barres post-rejet. Accu : stabilisation, HL à volume sec. Distrib : LH, volume sur les BAISSES, anciens LPS qui cassent. **Tenir les deux étiquettes** jusqu'au tri |

---

## 5 · Les tests, pierre angulaire ? — Oui, de la DÉCISION, pas de la CONSTRUCTION

Le moteur = l'absorption (climax + Phase B) : le test ne crée pas de cause, il la mesure. Mais chaque
transition de phase est gardée par un test : ST → tests de Phase B → spring + test → LPS successifs
→ BUEC. **Une campagne est une séquence de portes, chaque porte est un test.**
Pour l'analyste : signal à faible bruit, localisation précise, timing (précède le mouvement qu'il
autorise).

> Le climax fournit la matière première, le test est le **contrôle-qualité**, le markup est la
> livraison. Livrer sans contrôle-qualité = un faux breakout.

---

## 6 · Pondérer davantage les tests réussis — oui, comme confirmateurs

1. **Changement de statut** : spring seul = « possible spring » ; spring + test sec = « spring
   CONFIRMÉ ». Aucun événement de Phase C/D ne passe de possible à confirmé sans son test.
2. **Hiérarchie** : test sec validé > SOS volumique (le SOS peut être du covering ; le test sec ne
   ment pas sur l'absence d'offre). Crypto : on répare le SOS avec OI/CVD ; sur l'or, le test sec
   est l'information n°1.
3. **Cumulatif** : retours successifs à volume décroissant (×3 → ×1.5 → ×0.6) = meilleure preuve de
   maturation. C'est un **gradient**, pas un événement.

**Garde-fous** : (a) test sans cause en amont = poids nul ; (b) test réussi prouve l'absence
d'offre, pas la présence de demande → le poids fort va au couple **test + réponse** ; (c) poids
supérieur = meilleure lecture et invalidation plus nette, jamais confiance aveugle.

---

## 7 · Exemples récents

| Cas | Déroulé | Leçon |
|---|---|---|
| **XAU H4** — test volumique re-testé plus bas | SC1 3 972 (24/06, ×4.4) → ST 25/06 encore fort (×3.2) → retour : SC2/undercut 3 950 (30/06) → retest 3 965 (01/07) ~×1.1, clv 0.67 → réponse ×3.2 jusqu'à 4 117 | test à gros volume = rendez-vous pris ; « test volumique → re-test plus sec → réponse » = déroulé canonique |
| **BTC H1** — terminal shakeout, test différé | spring/shakeout 57 800 (01/07 03:00) : flush sous 58 115 + reclaim violent (absorption_w +1.76, OI −4k) ; pas de retour sec sur 57 800, mais consolidation 58 500–59 090 = test différé (replis ×0.4–0.8, HL, vente absorbée) | réponse immédiate au shakeout → test différé en back-up sur la zone reconquise (§3.3 #1, matrice ligne 5) |
| **BTC H4** — tests de Phase B jamais secs | ST1 58 608 et ST2 58 500 (26/06) à ×2–4, clôtures fermes → jamais de passage sec → aucun go ; plancher re-pressé (SOW 30/06) avant le shakeout 01/07 | tests volumiques répétés = campagne PROLONGÉE ; le go n'existe qu'au passage sec |

---

## 8 · Fiches auteurs

### Richard D. Wyckoff (1873–1934) — l'inventeur du cadre
*Studies in Tape Reading* (1910), le Cours (1931). Projet : rétro-ingénierer les campagnes des gros
opérateurs. **Composite Man** : lire chaque graphique comme la trace d'un opérateur unique. Campagne
en 4 actes ; la préparation est la partie invisible. **Test = opération** (sondage réel), lu sur la
bande ; **springboard** = verdict de tests.
**Nine Buying Tests** (miroir : Nine Selling Tests), paraphrase :
1. objectif de baisse atteint (compte P&F) ; 2. PS, SC, ST présents (Phase A) ; 3. volume ↑ dans les
rallyes, ↓ dans les réactions ; 4. ligne de tendance baissière cassée ; 5. higher lows ; 6. higher
highs ; 7. force relative > marché ; 8. base horizontale (cause P&F suffisante) ; 9. potentiel ≥ 3×
le risque.
→ Tester = vérifier un **faisceau** de conditions (prix, structure, cause, force relative), jamais un
signal isolé.

### Robert G. Evans (†1972) — le pédagogue des frontières
Conférences SMI (années 1940–60), pas de livre. Allégories devenues vocabulaire standard, presque
toutes sur le **franchissement d'une frontière et son test** :
- **Creek** : approches (futurs LPS) → **JAC** avec élan = volume → **BUEC** (vérifier la réception).
- **Ice** (miroir distribution) : la glace craque (SOW), le prix remonte toucher la glace par
  dessous = **LPSY** ; cale dessous à volume sec = markdown validé.
- **Terminal shakeout** : après lui, le test n'est pas optionnel — il prouve que la secousse était
  terminale.

### Henry O. Pruden (1936–2017) — le systématiseur académique
*The Three Skills of Top Trading* (2007), Golden Gate University. Trois compétences : analyse
systémique, reconnaissance de patterns (= Wyckoff), discipline mentale. Superpose un cycle de
psychologie de foule (test sec = le désespoir a fini de vendre). Standardise la grille **A–E** :
C teste l'offre (spring), D teste la demande (LPS) puis la frontière (BUEC). Popularise les springs
**#1/#2/#3** indexés sur l'exigence de test. Le trade JAC/BUEC = setup à plus haute probabilité.

### Tom Williams (1929–2016) — le test réduit à la bougie
*Master the Markets* (1993/2005), fondateur du VSA (TradeGuider). Principes : (1) force sur les
barres de baisse, faiblesse sur les barres de hausse ; (2) **le fond prime**. Test = geste
professionnel provoqué vers une zone précise (≠ no supply passif). Règle du **re-test** sur volume
fort ; test validé seulement par une réponse rapide ; test sur fond de faiblesse = piège ; test aussi
signal de continuation. Nos seuils `test_vol`, `narrow_spread_atr` en sont la traduction.
**Limite** : VSA seul = catalogue d'étiquettes hors structure — sans la grille de campagne, un
« test » n'est qu'une bougie sèche (condition 5, §2).
