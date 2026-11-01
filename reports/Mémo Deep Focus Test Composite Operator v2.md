# Mémo Deep Focus Test Composite Operator — v2

*Le CO teste avant de payer : à quoi sert chaque test Wyckoff, comment le vérifier, comment le trader. BTC perps H1/H4 et or. Version 2, réécrite pour la lisibilité à partir du mémo vérifié du 31/10/2026, pour Gauthier. Aide à la décision discrétionnaire, jamais d'exécution automatique.*

## L'essentiel

1. Un test mesure, il ne construit pas. La cause naît de l'absorption (climax, Phase B) ; le test vérifie qu'il ne reste plus d'offre avant le markup.
2. Le volume d'un test se compare à celui de l'action testée : ST < SC, test < spring, BU < JAC. La moyenne mobile n'est qu'un filtre secondaire.
3. Un test réussi prouve l'absence d'offre, pas la présence de demande. Il faut une réponse en 1 à 3 barres ; sans réponse, c'est de la faiblesse.
4. Règle de Williams : un test volumique est raté par défaut et appelle un re-test. Exception utile en perps : en marché à terme, il peut montrer de la force. L'OI en coin départage.
5. Springs : #3 léger et sec, pas de test requis ; #2 modéré et volumique, on achète le test ; #1 (shakeout), on n'entre que sur un test réussi.
6. On n'achète pas une cassure. Elle n'est confirmée comme JAC qu'après tenue et back-up sec ; sinon c'est peut-être un upthrust.
7. Le LPSY peut se faire sur volume faible ou fort : son critère robuste est le spread étroit et l'échec sous la résistance.
8. Le CO teste parce qu'une grosse position coûte cher : l'impact croît en racine carrée de la taille et reste en partie. Un markup raté se paie deux fois.
9. Stops et liquidations sont le carburant probable des springs et des UTAD, mais les effets mesurés sont modestes : un test incline la probabilité et place le risque, rien de plus.
10. Maturité = séquence accomplie + volume décroissant sur les creux + Phase B au moins aussi longue que la Phase A + test de Phase C sec + réponse. Dans un downtrend, une plage est une redistribution par défaut.
11. Screener : les seuils sont des heuristiques ; il manque un détecteur de test du spring, la classification des springs et des étiquettes conditionnelles pour le SOS.

## 1. Cadre

Un test est le retour du marché sur une zone où l'offre (ou la demande) s'est montrée, pour mesurer ce qu'il en reste. Le Composite Operator (CO), la fiction de Wyckoff d'un opérateur unique derrière le marché, ne marque pas les prix avant d'avoir vérifié. Chez Wyckoff, « test » désigne toute sonde dont on lit la réponse ; le retour sec vers le low du SC ou du spring n'en est que le cas moderne le plus connu. En VSA, c'est une barre qui plonge dans une zone d'offre et reprend sur faible volume.

La validité d'un test se juge en trois niveaux :

| Niveau | Critères | Si le critère manque |
|---|---|---|
| **Nécessaire** | cause en amont (climax, spring, shakeout, SOS) · lieu (retour sur la zone de l'action testée) · volume inférieur à celui de l'action testée, en baisse d'un passage à l'autre | ce n'est pas un test |
| **Qualité** | spread qui se resserre sur le swing · creux plus haut (grade A ; léger sous-percement sur volume plus faible = grade B) · clôture au milieu ou en haut | test plus faible, pas forcément raté ; creux plus bas **et** plus volumique = rejet |
| **Validation** | réponse dans le sens attendu en 1 à 3 barres | test sans réponse = faiblesse |

**Comment lire ce mémo.**

- Chaque test a une fiche au même format : une phrase, la question du CO, la signature, la suite, une check-list, la lecture crypto, l'invalidation, le trade et le piège.
- **[H]** marque une heuristique du projet ou un seuil du screener (`config.yaml`). Aucune source ne chiffre le volume en multiples ni le spread en ATR.
- La lecture crypto suit toujours le même ordre : volume et spread, puis OI en coin, puis ratio long/short, funding et liquidations seulement si l'OI est ambigu.
- Chaque prix-clé porte entre parenthèses l'événement ou la borne qui le définit.
- On déclare la TF et le contexte HTF avant d'étiqueter (lecture top-down, structures fractales).

## 2. Penser comme le CO : une grosse position coûte cher, d'où le test

Wyckoff présente le Composite Man comme une fiction utile : il faut étudier le marché comme si tout résultait des opérations d'un seul homme. Il précise lui-même qu'il n'existe pas de Composite Operator. Banquiers, pools, gros opérateurs, *floor traders* et public produisent ensemble le même effet qu'un opérateur unique. Cette partie montre ce que la recherche établit, et ce qui reste une analogie quand on l'applique aux tests.

### 2.1 Le CO connaît sa position, pas l'offre des autres

Le CO sait sa taille, son prix de revient et où sont ses ordres. Il ignore l'offre latente des autres : stops sous les creux, longs piégés plus haut, autres gros opérateurs. La recherche le confirme : l'essentiel de la liquidité est latente et n'apparaît pas dans le carnet. Avant 1934, l'opérateur comblait l'écart par des sondes :

- **achat ou vente-sonde** de 5 000 à 25 000 actions, pour voir avec quelle facilité le marché donne ou absorbe ;
- **retrait du soutien** : Keene laissait le titre seul pour voir s'il tenait ;
- **enquête sur le carnet** : combien est offert sur les cinq points au-dessus ?
- **marquage d'un meneur** puis observation de la réponse du secteur ;
- **raids** pour finir ses achats sur la réaction ; Wyckoff précise que ces poussées sont aussi ses tests.

Les sondes coûtent : Livermore y a laissé 50 000 à 60 000 dollars pendant l'accumulation d'une ligne, et jugeait que ce n'était pas cher. Le petit opérateur ne peut pas sonder, mais il peut lire gratuitement sur son graphique la réponse aux sondes des autres.

### 2.2 L'impact en racine carrée oblige à accumuler lentement et passivement

L'impact d'un gros ordre fractionné (un métaordre) croît comme la racine carrée de sa taille rapportée au volume quotidien ; l'exposant mesuré se situe entre 0,4 et 0,7. Ordre de grandeur : traiter 1 % du volume quotidien déplace le prix d'environ un dixième de sa volatilité quotidienne. La loi est confirmée sur Bitcoin avec plus d'un million de métaordres, sur quatre décennies de taille. Elle dépend peu du calendrier d'exécution.

Calcul illustratif, avec une volatilité quotidienne de BTC supposée à 3 % : acheter 1 % du volume quotidien coûte environ +0,30 % de prix, 10 % environ +0,95 %. Le coût total croît comme la taille à la puissance 1,5 : doubler la taille multiplie le coût par environ 2,8. D'où la stratégie du CO : absorber passivement, tester, puis seulement marquer.

<!-- FIG:campaign_economics -->

Cet impact est en partie **permanent** : après l'exécution, il se stabilise vers les deux tiers du pic, y compris pour des ordres passifs. Marquer les prix avec de l'offre encore présente revient donc à acheter contre son propre impact. Si l'offre latente revient quand le CO cesse d'acheter, le prix retombe et il garde un stock payé trop cher. C'est exactement ce que le test évite.

Ce que la recherche suggère du comportement du CO (par analogie) :

- **Se cacher dans le volume des autres** (le bruit camoufle l'initié, chez Kyle) : climax, paniques, chasses aux stops.
- **Fournir la liquidité plutôt que la prendre** : les initiés à information durable préfèrent les ordres limites. Le CO achète passivement dans les flux forcés (SC, spring), puis devient agressif au SOS et au JAC.
- **Effort sans résultat** : le prix suit le déséquilibre net des ordres, pas le volume brut. Volume élevé et déséquilibre nul (des offres passives absorbent) = prix qui stagne = absorption de Phase B.
- **Le passif laisse des traces** : 44 % du volume d'ordres est caché sur Euronext-Paris, mais les icebergs se détectent et les HFT suivent les ordres informés. Sur le graphique : volume groupé sur les bas, prix qui tient malgré un flux vendeur.
- **Patience** : plus un trader est averse au risque, plus il exécute tôt (Almgren–Chriss). CO patient = plage longue ; CO pressé = accumulation courte et violente (Phase B courte = urgence).

### 2.3 L'inventaire du market maker explique une partie de SC → AR → ST

- Un teneur de marché long d'inventaire cote plus bas pour s'en défaire (Avellaneda–Stoikov). Au **SC**, les fournisseurs de liquidité absorbent la vente forcée et finissent longs ; l'**AR** est un rebond mécanique ; au **ST**, ils écoulent cet inventaire et laissent revenir le prix vers le climax, sur volume plus faible.
- Sur le NYSE, un choc d'inventaire de 100 000 $ crée une pression moyenne de 0,28 %, de demi-vie 0,92 jour. Si une vraie demande absorbe cet inventaire au ST, le surplomb disparaît : équivalent d'une offre épuisée.
- Les échanges de partage de risque s'inversent, les échanges spéculatifs se prolongent : un climax (liquidité forcée) annonce un retournement, un SOS (flux informé) une continuation.

> **À retenir** — Deux lectures du même test peuvent être vraies ensemble : le CO sonde l'offre, et les intermédiaires ramènent leur inventaire à zéro. Un retour plus calme que le climax est compatible avec les deux. Un retour qui gonfle le volume à la baisse n'est compatible avec aucune : il signale une offre nouvelle. En perps, les teneurs de marché sont algorithmiques et couverts ; leurs demi-vies d'inventaire sont probablement bien plus courtes. En H4, un test reflète donc surtout les flux des participants : stops, liquidations, accumulation.

### 2.4 Les stops fournissent la liquidité du spring et de l'upthrust

Les travaux d'Osler sur le marché des changes donnent la mécanique :

- Les supports et résistances publiés arrêtent le cours plus souvent que des niveaux tirés au hasard (60,8 % de rebonds contre 56,2 %). Plus de 70 % de ces niveaux finissent par 0, 96 % par 0 ou 5.
- Les prises de bénéfices se groupent **sur** les chiffres ronds, les stops **juste au-delà** (9 667 ordres d'une grande banque).
- Le franchissement d'un amas de stops accélère la tendance, par vagues, plus fort qu'après des prises de bénéfices (0,061 % contre 0,054 % en 15 minutes). L'effet dure des heures, pas des jours.
- Déclencher les stops des clients est connu et sanctionné : en 2014, la FCA a infligé 1 114 918 000 £ d'amendes à cinq banques, notamment pour ce motif.
- Sur BTC, plus de 10 % des prix finissent par 00.

Le spring, pas à pas (transposition au spring, par analogie) :

1. Le prix perce le plancher de la plage.
2. Les stops vendeurs placés juste en dessous partent en vagues d'ordres au marché : c'est une offre urgente.
3. Le CO les absorbe avec des ordres d'achat passifs. Il obtient de la taille sans faire monter le prix.
4. La clôture revient dans la plage : fort volume, longue mèche basse, clôture haute.
5. Le carburant de stops est consommé.

Le test revient ensuite sur la même zone. Si aucune cascade ne repart (volume et spread faibles), l'offre est épuisée. Si une cascade repart (volume et spread qui s'élargissent à la baisse, clôtures faibles), la poche de stops ou l'offre réelle n'était pas vide : le spring était une cassure. Les vagues d'Osler expliquent qu'un seul *flush* ne vide pas toujours un niveau.

> **Piège** — Les effets mesurés sont modestes : environ 4 à 5 points de pourcentage, sur des heures plutôt que des jours. Plus un niveau est évident (testé souvent), plus les stops s'y accumulent juste au-delà, et plus la cascade est forte s'il finit par céder. « Les tests multiples renforcent un niveau » et « les niveaux évidents se font chasser » sont vrais en même temps.

### 2.5 En perps, les liquidations sont des stops sans discrétion

- Une liquidation est un ordre au marché forcé. Le flux Binance n'en publie qu'une par symbole et par seconde : les totaux lus sont des **planchers**.
- Le 10 octobre 2025, plus grosse journée de liquidations recensée (environ 19,16 Md$), le *mark price* aurait sous-réagi et créé une boucle. La mécanique des plateformes peut donc fabriquer une profondeur de spring artificielle : ne jamais lire la profondeur seule.
- Un *carry* élevé prédit des krachs : +10 % de carry standardisé prédit +22 % de liquidations vendeuses (rapportées à l'OI) le mois suivant. Funding extrême et OI en hausse au SOS = longs encombrés, à risque de *flush*.
- Avant sept cascades BTC (2022–2025), seule régularité : une compression de la variance du flux d'ordres agressifs. Réelle en moyenne, mais ce n'est pas un signal d'entrée.
- En 2019, le *wash trading* dépassait 70 % du volume déclaré sur les plateformes non régulées : lire le volume sur des marchés crédibles (Binance via Coinalyze par défaut dans le projet).

### 2.6 Le CO teste parce qu'un markup raté coûte deux fois

Le test répond à quatre besoins :

- **Vérifier l'offre résiduelle**, sinon le CO garde un stock payé trop cher et reconstruit sa campagne plus bas.
- **Mesurer la demande qui suivra** : sans suiveurs, il jouerait seul, sans acheteurs pour sa distribution future.
- **Récolter de la liquidité bon marché** : stops et ventes paniques (risque : une vraie cassure si personne n'absorbe).
- **Confirmer la polarité après le saut**, sinon un upthrust se déguise en SOS.

> **Penser comme le CO** — Le *springboard* de Wyckoff n'est pas un test, c'est le **résultat** de tests réussis. La position est « sur le tremplin » quand l'opérateur a terminé sa ligne et ramassé toute l'offre flottante à ce niveau. Wyckoff place le début du mouvement de tremplin **au bas de la plage d'accumulation**, pas à la cassure.

### 2.7 Hier les pools sondaient ; aujourd'hui seule la tromperie est interdite

Wyckoff meurt le 7 mars 1934 ; le *Securities Exchange Act* est promulgué le 6 juin 1934. Ce qui a changé (ceci n'est pas un avis juridique) :

- **Ordres-sondes** : un ordre réel qui fait bouger le prix n'est pas en soi une manipulation ; l'interdit porte sur l'intention d'inciter les autres à acheter ou vendre.
- **Soutien affiché puis annulé** : c'est le *spoofing*, interdit (JPMorgan : 920 M$ pour les métaux précieux et les Treasuries, 2008–2016 ; MiCA en Europe depuis le 30/12/2024). La profondeur affichée peut mentir, le volume exécuté ne s'annule pas : c'est l'argument de fond pour lire le volume d'abord, or COMEX compris.
- **Wash sales** : interdits ; en crypto, l'opération *Token Mirrors* (octobre 2024) a mené aux premières poursuites pénales de teneurs de marché. Éviter de lire des tests sur les petites plateformes.
- **Raids** : interdits s'ils visent à tromper ; les flux forcés (stops, liquidations) jouent aujourd'hui ce rôle sans chef d'orchestre.

La recherche tempère le mythe : sur 55 pools de 1929, les données suggèrent des opérateurs informés plutôt que des manipulateurs.

> **À retenir** — Le CO moderne est la somme de quatre acteurs : les métaordres informés exécutés par algorithme, les fournisseurs de liquidité qui gèrent un inventaire, les anticipateurs d'ordres et HFT, et les flux mécaniques forcés (stops, liquidations). Le Composite Man est une heuristique pour lire leur empreinte nette, pas une thèse de complot.

### 2.8 Aucune étude ne valide la méthode entière ; ses briques le sont, modestement

- **Wyckoff comme système** : aucun test à comité de lecture trouvé.
- **Supports et résistances** : ils coïncident avec des pics de profondeur réelle du carnet.
- **Tests répétés** : la probabilité de rebond croît avec le nombre de rebonds antérieurs sur des horizons de 45 à 90 secondes, plus à 180 secondes, et ce n'est pas rentable après coûts.
- **Rentabilité des supports/résistances** : pas d'excès de rendement face au *buy-and-hold*.
- **Data snooping** : Brock, Lakonishok et LeBaron avertissaient déjà que le danger est immense. Après correction sur environ 8 000 règles (Sullivan, Timmermann et White), la performance s'affaiblit hors échantillon.
- **Spring seul** : un backtest amateur (journalier, stop au low − 1 ATR, objectif 2R) donne 41,26 % de gains et −0,13 R en moyenne sur 1 098 trades. Résultat non vérifié (page devenue inaccessible).

> **Penser comme le CO** — Pour un trader H1/H4, un test est une **inclinaison de probabilité plus un point de risque défini**. Le stop se place sous le low du spring, là où la poche de stops a déjà été consommée. Le backtester du dépôt (`screener/optimize.py`, IS/OOS et walk-forward) permet de vérifier sur BTC si « spring + test sec + profil d'OI coin » bat des niveaux arbitraires, sur le modèle du contrôle d'Osler.

## 3. Fiches de tests — accumulation

En accumulation, chaque transition de phase est gardée par un test : le ST ferme la Phase A, les tests de Phase B mesurent l'absorption, le spring et son test (ou un LPS de Phase C) ouvrent la Phase D, les LPS et le back-up valident la sortie. Le schéma montre ce parcours complet et le profil de volume attendu à chaque étape.

<!-- FIG:schema_accumulation -->

| Phase | Test (fiche) | Ce qui est testé | Volume à battre |
|---|---|---|---|
| A | ST (3.1) | l'offre résiduelle au prix de la panique | SC |
| B | ST in Phase B (3.2) | l'offre flottante encore en mains faibles | passage précédent (gradient) |
| B | UA / UT in Phase B (3.3) | l'offre au-dessus de l'AR | réintégration rapide |
| B | ST as SOW (3.4) | l'agressivité des vendeurs | volumique = offre présente |
| C | Spring #3 (3.5) | l'offre sous le support : absente ? | creux récents |
| C | Spring #2 (3.6) | l'offre sous le support : présente mais pas écrasante | en expansion |
| C | Spring #1 / terminal shakeout (3.7) | l'offre écrasante est-elle absorbée ? | climactique |
| C | Test du spring (3.8) | l'offre restante après le spring | spring |
| C | LPS de Phase C (3.9) | l'offre, sur un creux plus haut, sans spring | ST précédents |
| D | SOS mineur (3.10) | la demande suit-elle quand le CO cesse de plafonner ? | réactions |
| D | LPS successifs (3.11) | les acheteurs reviennent-ils plus haut ? | SOS précédent |
| D | JAC / SOS majeur (3.12) | la demande franchit-elle le creek ? | expansion |
| D→E | BU / BUEC (3.13) | la résistance est-elle devenue support ? | JAC |
| E | Test de continuation (3.14) | l'offre est-elle revenue après une poussée ? | poussée testée |
| E | Réaccumulation (3.15) | prises de bénéfices absorbées ou distribution ? | décroissant |

### Lire un test : quatre règles communes à toutes les fiches

**1. Le volume se compare à l'action testée.** La doctrine ne parle pas de moyenne mobile : le ST doit être moins volumique que le SC, le test moins que le spring, le BU moins que le JAC. Le filtre `vol_ratio ≤ 0.85` (volume rapporté à la MA20) n'est qu'un filtre secondaire [H].

**2. Règle de Williams : un test volumique est raté par défaut.** Un test à faible volume dit que le marché est prêt à monter. Un test à volume élevé dit que l'offre est encore là : il donne en général une hausse temporaire, puis un re-test de la même zone, ce qui dessine un « W ». Le seuil « test raté vers ×1.5 » est une convention du projet [H]. Williams admet trois exceptions : mauvaises nouvelles ou shakeout, marché haussier, et surtout **marchés à terme**, où un test volumique peut montrer de la force. Sur perps, c'est donc l'OI en coin qui départage un test volumique. La figure résume les trois issues.

<!-- FIG:test_validity -->

**3. La réponse valide le test.** Un test réussi prouve qu'il n'y a plus d'offre, pas qu'il y a de la demande. La hausse doit venir tout de suite : on attend une réponse en 1 à 3 barres. Sans réponse après 2 à 3 barres, Williams parle de *negative action* : un signe de **faiblesse**, pas un signal neutre. Un test se lit donc sur deux barres : la barre de test et sa confirmation.

**4. La lecture crypto suit un ordre fixe : volume, puis OI en coin, puis tierces.**

- *Volume et spread d'abord* : effort contre résultat, volume relatif, position de la clôture.
- *Puis l'OI, toujours en coin.* L'OI en USD vaut l'OI en coin multiplié par le prix : il monte sur un rallye même quand les positions baissent. Exemple du projet, cassure BTC 64 800 (résistance franchie lors de l'épisode de référence de CLAUDE.md) : OI USD +0,81 %, mais OI coin −0,36 % ; le prix avait monté d'environ 1,17 % sur du *short covering*. En coin, le signe est fiable : de petites variations comptent si elles se suivent sur plusieurs barres.
- *Puis les tierces, seulement si l'OI est ambigu* (OI en hausse à prix plat : longs ou shorts ?). Ratio long/short (chez Binance, un nombre de comptes, pas une taille ; un ratio qui baisse = des shorts entrent), funding (positif = les longs paient), liquidations (des planchers ; proches de zéro = mouvement ordonné).
- *Synthèse* : on lit OI et tierces ensemble pour en tirer un sens commun.

Pour un test : OI coin plat ou en baisse = des positions se ferment, le test est constructif. OI coin en hausse = test **non validé**, ambigu (shorts agressifs ou acheteurs passifs qui absorbent), à départager par les tierces.

<!-- FIG:oi_overlay -->

### Phase A — stopper la baisse et poser les bornes

Après le SC, l'**AR** est le rebond réflexe, bref et rapide, qui fixe la borne haute de la plage. Dans le projet, un AR authentique est du *short covering* : l'OI en coin baisse, et `window.py` refuse l'AR si l'OI monte.

#### 3.1 ST — Secondary Test (Phase A)

**En une phrase.** Après le SC et l'AR, le prix revient vers la zone du climax pour vérifier qu'il n'y reste plus beaucoup d'offre ; le ST clôt la Phase A.

**La question du CO.** Reste-t-il une offre significative au prix où le public a paniqué ? **Pourquoi c'est important.** Le CO a absorbé le climax à bon prix. Si l'offre ressort lourdement, il doit en absorber davantage, et un SC qui n'arrête rien met son stock sous l'eau.

**Signature valide**

- Volume nettement inférieur à celui du SC, ranges qui se resserrent.
- Spread plus étroit que celui du SC.
- Creux en général au niveau du low du SC ou au-dessus ; plusieurs ST sont courants.
- Repères [H] : `vol_ratio ≤ 0.85`, `spread_atr ≤ 0.7` (l'ATR est gonflé par le climax), `clv ≥ 0.5`. Avec un SC à ×2,0, un ST à ×0,85 pèse au plus environ 42,5 % du SC.

**Ce que fait le CO ensuite**

- Réussi : la plage est posée par trois points (low du SC, low du ST, high de l'AR) et l'absorption de Phase B commence. Pour Wyckoff, des prix qui tiennent autour ou au-dessus des bas du climax pendant que le volume se contracte indiquent que la liquidation est finie.
- Raté (volume lourd, spread large, clôture basse) : nouveaux plus-bas ou consolidation prolongée. Fraser ne compte alors la cause P&F qu'à partir du ST.
- Léger sous-percement sur volume faible : Villahermosa y voit un déséquilibre vendeur, Fraser l'accepte ; on garde les deux lectures.

**Vérifier en pratique**

- [ ] Un arrêt identifiable en amont (SC, ou Phase A non climactique). Sans arrêt, pas de ST.
- [ ] Volume et spread du ST inférieurs à ceux du SC ; afficher le ratio vol_ST / vol_SC.
- [ ] Un sous-percement léger se note « ST sous SC », jamais « spring ».
- [ ] Contexte HTF déclaré : dans un downtrend, redistribution par défaut.

**Lecture crypto.** Volume nettement sous le SC. OI coin plat ou en baisse : des positions se ferment. OI coin en hausse pendant que le prix tient : ambigu ; avec un ratio L/S en baisse, un funding négatif et des liquidations nulles, des shorts s'ouvrent dans le support, carburant si la borne tient.

**Invalidation.** Clôture sous le low du SC avec volume et spread en expansion : le SC n'a pas stoppé la baisse. On ré-étiquette, et le décompte P&F ne part plus du SC.

**Trade**

- Entrée : aucune ; la Phase A ne sert pas à chercher de nouveaux trades.
- Stop et objectif : sans objet. On trace le plancher (low du SC, borne basse de la plage) et le plafond (high de l'AR, borne haute), futurs repères d'invalidation et d'objectif.

**Piège fréquent.** Présumer l'accumulation : la plage peut être une accumulation, une redistribution ou rien du tout.

### Phase B — construire la cause en testant les deux bornes

> **Penser comme le CO** — En Phase B, le CO achète en net et plafonne les avances par des ventes : il peut vendre 100 000 actions et en acheter 200 000, soit une accumulation nette de 100 000. Chaque retour sur une borne est un relevé d'inventaire du marché.

Les premiers retours sur la borne basse sont souvent volumiques. Ce qui renseigne, c'est la **pente** du volume d'un passage à l'autre : un volume qui décroît signale la maturation, un volume qui ne baisse pas signale une offre toujours présente.

<!-- FIG:phase_b_gradient -->

#### 3.2 ST in Phase B — tests répétés de la borne basse

**En une phrase.** Pendant la Phase B, le prix revient plusieurs fois sur la borne basse ; la pente du volume d'un passage à l'autre dit si l'offre s'épuise.

**La question du CO.** Combien d'offre flottante reste-t-il en mains faibles, et diminue-t-elle à chaque passage ? **Pourquoi c'est important.** C'est le centre de coût de la campagne. Si l'offre ne baisse pas, la campagne s'allonge ou est abandonnée.

**Signature valide**

- Début de Phase B : oscillations larges et volumiques (normal, ces baisses montrent l'offre). Ensuite, le volume des baisses diminue : le signal est la tendance, pas une barre.
- Oscillations qui se resserrent, clôtures qui s'éloignent des bas.
- Un sous-percement du SC fait partie du modèle (le schéma #1 dessine un ST in B sous le SC).
- La Phase B dure plus longtemps que les Phases A et C.
- Repère [H] : seul le **dernier** passage doit être à `vol_ratio ≤ 0.85` ; les premiers peuvent dépasser ×1.3.

**Ce que fait le CO ensuite**

- Réussi (pente négative) : creux de plus en plus secs, rallyes plus faciles ; la Phase C peut venir.
- Raté (volume croissant sur les creux, clôtures basses) : la Phase B s'allonge, ou la campagne tourne à la redistribution. Si l'offre revient tard, Fraser ré-étiquette C et D en prolongement de B.

**Vérifier en pratique**

- [ ] Relever chaque passage : volume, spread, clôture, creux ; la pente du volume est négative.
- [ ] Volume en hausse sur les rallyes, en baisse sur les réactions (*activity bullish*).
- [ ] Phase B au moins aussi longue que la Phase A avant de créditer une Phase C.

**Lecture crypto.** Un OI coin qui se dégonfle de test en test : débouclage, l'offre ne se réengage pas. Un OI coin en hausse sur un creux plus bas et volumique signale de nouveaux shorts (candidat ST as SOW). Tierces seulement si le prix cale avec un OI en hausse.

**Invalidation.** Un volume des baisses qui grossit avec l'âge de la plage : c'est la signature d'une distribution.

**Trade**

- Entrée : pas de trade au milieu de la plage. Pour trader un extrême, descendre d'unité de temps et chercher une accumulation mineure au bas (Villahermosa).
- Stop et objectif : sans objet sur la TF de la structure ; niveau de travail = plancher (low du SC/ST, la borne testée).

**Piège fréquent.** Exiger `test_vol` dès le début de la Phase B, ou appeler « spring » un creux de Phase B : un spring prématuré, sans cause construite, échoue beaucoup plus souvent.

#### 3.3 UA / UT in Phase B — test de la borne haute en accumulation

**En une phrase.** Pendant la Phase B, le prix perce brièvement le high de l'AR puis rentre dans la plage ; en accumulation, c'est un piège normal, pas un SOS.

Villahermosa dit **UA** (*Upthrust Action*) en accumulation et **UT** en distribution : seule change l'hypothèse de biais. Fraser dit UT dans les deux cas. Si le prix reste au-dessus un moment, on parle de **mSOS**.

**La question du CO.** Combien d'offre y a-t-il au-dessus de l'AR, et comment réagit la demande quand le prix perce ? **Pourquoi c'est important.** Le CO plafonne les avances prématurées par des ventes. Une sortie qui tiendrait trop tôt l'obligerait à acheter plus haut.

**Signature valide**

- Le prix dépasse le high de l'AR sans aller loin, puis rentre dans la plage.
- Volume : aucun seuil dans les sources ; barre de réintégration à clôture faible (`clv ≤ 0.5` [H]).
- Réintégration rapide = UA/UT ; plusieurs clôtures au-dessus = candidat mSOS.

**Ce que fait le CO ensuite**

- Réussi (pour l'accumulateur) : peu d'offre, l'absorption continue. Un UA signale plutôt de la force : si le bas de la plage cède plus tard, on favorise le spring.
- Raté : chute rapide vers un SOW qui casse le bas de la plage ; la distribution progresse vite.

**Vérifier en pratique**

- [ ] Avant tout test de Phase C, une percée est présumée UA/UT, jamais SOS.
- [ ] Compter les clôtures au-dessus du high de l'AR.
- [ ] Repli suivant large et volumique vers le support = lecture distribution.

**Lecture crypto.** OI coin en hausse sur la percée puis réintégration : des acheteurs de cassure entrent et deviendront vendeurs, nourrissant la descente où le CO rachète. OI en baisse : simple rachat de shorts. Pour attribuer un OI en hausse : shorts liquidés sur la mèche et funding qui grimpe = percée alimentée par du forcé.

**Invalidation.** De l'accumulation : un UT suivi d'une chute volumique sous le plancher (low du SC/ST, borne basse), soit un SOW de Phase B. Du UA : le prix tient au-dessus avec un repli sec, on passe en scénario mSOS/SOS.

**Trade**

- Entrée : aucune. On ne shorte pas le UA en hypothèse d'accumulation, et on n'achète pas la cassure.
- Stop et objectif : sans objet. On note le high du UA (extrême du piège, repère pour juger une vraie cassure plus tard).

**Piège fréquent.** Appeler la percée « SOS », ou shorter la résistance en fin d'accumulation.

#### 3.4 ST as SOW — creux plus bas en Phase B

**En une phrase.** Pendant la Phase B, le prix fait un creux plus bas que le SC et le ST : soit les vendeurs sont agressifs, soit les acheteurs manquent.

Villahermosa l'appelle ST as SOW en accumulation, mSOW en distribution ; « ST in B » reste une étiquette neutre.

**La question du CO.** L'offre est-elle encore agressive, ou les acheteurs ont-ils disparu ? **Pourquoi c'est important.** Il reste de l'offre à absorber, et la campagne peut tourner à la redistribution.

**Signature valide**

- Creux plus bas en Phase B, plus probable si le ST de Phase A avait déjà fait un plus-bas.
- Volume et spread en expansion avec clôture basse = offre encore présente ; volume faible = vendeurs absents, lecture plus favorable.
- Profil SOW du screener [H] : `vol_ratio ≥ 1.3`, `spread_atr ≥ 1.3`, `clv ≤ 0.4`.

**Ce que fait le CO ensuite**

- Lecture accumulation : le sous-percement ne produit pas de suivi, se fait re-tester plus sec et devient la nouvelle ligne de support.
- Lecture distribution : force vendeuse ; si le haut de la plage est cassé plus tard, on favorise l'upthrust.

**Vérifier en pratique**

- [ ] Creux plus bas en Phase B, pas en Phase C.
- [ ] Re-test ultérieur du niveau, avec comparaison des volumes.
- [ ] Dans un downtrend, le scénario redistribution prend le dessus.

**Lecture crypto.** OI coin en hausse avec le creux = nouveaux shorts. OI en baisse avec liquidations de longs = purge de longs fragiles, qui peut préparer une absorption. Si le prix cale : ratio L/S en baisse et funding négatif sans rebond = vendeurs en contrôle.

**Invalidation.** De l'accumulation : suivi baissier sans réintégration, volume des baisses qui croît. De la distribution : réintégration rapide puis re-test sec qui tient.

**Trade**

- Entrée : aucune sur la TF de la structure.
- Stop et objectif : sans objet. On redessine le support (low du ST as SOW, nouvelle borne basse effective) et on prépare deux scénarios de Phase C : spring ou cassure.

**Piège fréquent.** Confondre l'étiquette, qui dépend du biais, avec la preuve.

### Phase C — le test ultime de l'offre

> **À retenir** — Numérotation unique dans tout le mémo, la même chez le SMI, Fraser et Villahermosa (aucune inversion trouvée) : **#1 = lourd** (shakeout ou terminal shakeout : pénétration profonde, spread large, volume fort ; test obligatoire) · **#2 = modéré** (pénétration modérée, volume en expansion ; on achète le test) · **#3 = léger** (pénétration faible, spread étroit, volume faible ; pas de test requis). Pruden suit la même gradation sans numéros. Pour Fraser, c'est la signature du volume qui décide du type, donc de l'entrée.

Les trois types se distinguent d'un coup d'œil :

<!-- FIG:springs_types -->

Le *terminal shake-out* est un terme de Wyckoff ; le spring en est le raffinement de l'ère SMI/Evans, comme très probablement sa numérotation.

#### 3.5 Spring #3 — pénétration légère et sèche

**En une phrase.** Le prix enfonce légèrement le support sur volume faible et spread étroit, puis revient dans la plage : aucune offre nouvelle n'est sortie.

**La question du CO.** Si j'enfonce le support, reste-t-il quelqu'un pour vendre ? **Pourquoi c'est important.** Une absence d'offre sur un nouveau plus-bas est la preuve la plus forte d'épuisement, et elle coûte peu. Le risque : prendre pour « sec » un marché simplement vide (week-end, heure creuse d'un marché 24/7).

**Signature valide**

- Après une Phase B mûre, sous le support (low du SC ou plus bas creux de Phase B).
- Volume pas plus haut que celui des creux récents ; spread relativement étroit ; pénétration faible.
- La barre ne clôture pas au plus bas ; retour dans la plage sur la barre ou très vite.
- Repères [H] : `vol_ratio ≤ 0.85`, `spread_atr ≤ 0.7`, `pen_atr ≥ 0.1` ATR (et moins d'environ 0,5 ATR, à calibrer), `clv ≥ 0.5`.

**Ce que fait le CO ensuite**

- Réussi : barres de demande, retour dans la plage, SOS proche. Pas de test requis, mais un test n'est pas rare ; pour le SMI, la confirmation vient de la demande et du retour dans la plage.
- Raté : pas de demande, nouvelle dérive sous le low. Si la réintégration se fait sans barre de demande, on le traite comme un #2 et on attend un test.

**Vérifier en pratique**

- [ ] Phase B mûre ; sinon spring prématuré.
- [ ] Volume « sec » comparé au même créneau horaire des jours précédents.
- [ ] Barres de demande ou rallye de réintégration ensuite.
- [ ] Contexte : se méfier des springs dans un downtrend.

**Lecture crypto.** Volume sec, OI coin quasi inchangé (ni purge de longs, ni nouveaux shorts) ; tierces rarement utiles. Si l'OI monte sur la percée puis que le prix réintègre, ces shorts piégés deviennent du carburant, mais il faut encore la réponse acheteuse.

**Invalidation.** Clôture sous le low du spring avec spread et volume en hausse.

**Trade**

- Entrée : sur la réintégration ou sur la première barre de demande (Fraser : le #3 peut s'acheter tout de suite).
- Stop : sous le low du spring (la poche de stops y a été consommée ; y revenir en clôture signale une offre réelle), avec une marge possible pour un second balayage.
- Objectif : high de l'AR / creek (borne haute de la plage), puis décompte P&F depuis le LPS ; R:R ≥ 3.

**Piège fréquent.** Prendre un marché vide pour une offre épuisée, ou acheter sans réponse de la demande.

#### 3.6 Spring #2 — pénétration modérée, offre absorbée

**En une phrase.** Le support cède plus nettement sur volume en expansion, puis le prix réintègre : de l'offre est sortie et a été absorbée, il reste à vérifier qu'elle est épuisée.

**La question du CO.** Combien d'offre libère la cassure, et ai-je pu tout absorber ? **Pourquoi c'est important.** Le CO achète un bloc d'offre bon marché (stops, vendeurs tardifs). Mais absorbée ne veut pas dire épuisée. C'est le type le plus courant selon le SMI.

**Signature valide**

- Après une Phase B mûre, cassure du support sur une forte poussée de volume, supérieure aux creux récents.
- Bon spread ; pénétration modérée, plus loin sous le low qu'un #3.
- Retour dans la plage ; repères [H] : `0.85 < vol_ratio < 2.0`, `pen_atr ≥ 0.1` ATR, `clv ≥ 0.5`.
- Le test vient souvent dans les une à deux barres suivantes en journalier.

**Ce que fait le CO ensuite**

- Réussi : un test à volume nettement plus faible et à creux plus haut, puis de la demande (fiche 3.8).
- Raté : test à creux plus bas sur volume plus fort ; le processus recommence. Un rallye sans test reste suspect tant que le test n'a pas eu lieu.

**Vérifier en pratique**

- [ ] Volume de la pénétration supérieur aux creux récents.
- [ ] Statut « spring possible » tant que le test n'a pas eu lieu.
- [ ] Test attendu : volume inférieur au spring, creux au-dessus de son low.

**Lecture crypto.** Deux profils : OI coin en baisse avec liquidations de longs (purge, stops consommés), ou OI en hausse sur la cassure puis réintégration (shorts piégés). Pour départager : funding qui plonge vers ou sous zéro, volume des liquidations de longs. OI en baisse + liquidations de longs + réintégration = l'offre forcée a changé de mains.

**Invalidation.** Clôture sous le low du spring sur volume en hausse ; un test à creux plus bas **et** plus volumique ne se trade pas.

**Trade**

- Entrée : sur le test, que Fraser tient pour le meilleur point d'achat. Le SMI admet une position partielle sur le spring, renforcée sur le test.
- Stop : sous le low du spring (le plus bas de la séquence ; le casser invalide le schéma).
- Objectif : creek / high de l'AR (borne haute de la plage), puis décompte P&F ; R:R ≥ 3.

**Piège fréquent.** Acheter la barre de spring en taille pleine, ou juger le test contre la MA20 au lieu du volume du spring.

#### 3.7 Spring #1 / terminal shakeout (et shakeout ordinaire)

**En une phrase.** Chute rapide et profonde sous le support sur volume fort à climactique, puis réintégration ; le geste le plus payant pour le CO, le plus dangereux pour le trader.

Wyckoff appelle *terminal shake-out* cette chute brutale en fin de préparation d'une hausse. Le shakeout **ordinaire** est le même geste en tendance haussière, sans longue préparation (réaccumulation) : la différence est le lieu. Le SMI et Villahermosa en font le spring #1.

**La question du CO.** Ai-je absorbé toute l'offre que la panique et les stops viennent de libérer ? **Pourquoi c'est important.** C'est le plus gros bloc au meilleur prix, mais au début un shakeout ressemble beaucoup à un SOW (une chute à travers la glace).

**Signature valide**

- Fin de longue préparation (terminal) ou tendance haussière (ordinaire).
- Volume fort à climactique, spread en expansion, pénétration profonde, réintégration rapide.
- Premier indice de demande : après la pénétration, le volume reste haut mais les ranges se resserrent.
- Repères [H] : `vol_ratio ≥ 2.0`, `spread_atr ≥ 1.3`, pénétration supérieure à environ 1 ATR (à calibrer).
- Le test peut venir tard (dans un cas du SMI, réaction de 18 jours, rallye de 12).

**Ce que fait le CO ensuite**

- Réussi : forte entrée de demande (ranges larges, volume relativement haut), puis un ou plusieurs tests secs.
- Raté : pas de réintégration ; c'est un SOW, et une nouvelle accumulation devra se construire plus bas.
- Réponse explosive sans retour sur le low : le CO teste plus tard, sur un repli vers la zone reconquise. Ce « test différé en back-up » est une extension du projet [H] ; le SMI ne documente qu'un test tardif après un rallye réactif.

**Vérifier en pratique**

- [ ] Hors fin de préparation ou tendance haussière, présumer un SOW.
- [ ] Statut « possible » jusqu'au test : pour le SMI, tout shakeout doit être testé.
- [ ] Tests à volume décroissant et creux plus haut.
- [ ] Jamais dans un downtrend : y prendre position est extrêmement dangereux.

**Lecture crypto.** OI coin en forte baisse avec pic de liquidations de longs (forcé consommé), ou OI en hausse sur la cassure puis réintégration avec liquidations de shorts (squeeze). Pour départager : funding négatif ou nul ; liquidations lues comme des planchers. Le *mark price* peut sous-réagir et fabriquer de la profondeur.

**Invalidation.** Pas de réintégration ; clôture sous le low du shakeout ; test à creux plus bas sur volume plus fort.

**Trade**

Les écoles divergent : Pruden fait du shakeout un premier point d'entrée (point 8) mais juge le test meilleur (point 10) ; le SMI attend un test réussi ; Fraser ne l'achète pas. Choix du mémo : entrée sur le test réussi seulement.

- Entrée : barre de demande après un test réussi (volume plus faible que le shakeout, creux plus haut).
- Stop : sous le low du shakeout (point de danger de Pruden : sous ce niveau, la purge n'était pas terminale). Stop large, taille réduite.
- Objectif : décompte P&F ; si un R:R ≥ 3 est impossible, on passe.

**Piège fréquent.** Confondre shakeout et SC. Pour Williams, un vrai SC a la même allure, mais avec un marché baissier derrière lui.

> **Penser comme le CO** — Wyckoff décrit le but du terminal shake-out sans détour : effrayer les détenteurs, ramasser les stops placés sous les anciens supports, encourager les ventes à découvert près du bas ; puis enfermer ces shorts et laisser dehors les haussiers qui ont vendu. Peu importe, ajoute-t-il, que le shakeout vienne d'une manipulation ou d'une panique.

#### 3.8 Test du spring (test secondaire du spring ou du shakeout)

**En une phrase.** Après le spring, le prix revient vers son low sur volume plus faible et spread plus étroit ; c'est la dernière mesure de l'offre avant le markup.

**La question du CO.** L'offre délogée par le spring a-t-elle vraiment disparu ? **Pourquoi c'est important.** Le test ne coûte rien s'il réussit ; sans lui, le CO marquerait les prix au-dessus d'une offre non mesurée. Villahermosa en fait un LPS.

**Signature valide**

- Retour vers le low du spring : une à deux barres après un #2 en journalier, parfois des semaines après un shakeout.
- Volume inférieur à celui du spring (critère primaire) ; spread plus étroit.
- Creux plus haut que celui du spring = haute qualité.
- Réponse haussière dans les 1 à 3 barres.
- Repères [H] : `vol_ratio ≤ 0.85`, `spread_atr ≤ 0.7`, `clv ≥ 0.5`.

La qualité se grade selon le creux et le volume :

<!-- FIG:spring_test_grades -->

| Grade | Creux | Volume et spread | Que faire |
|---|---|---|---|
| **A** | plus haut que le spring | inférieur au spring, étroit | acheter après la réponse |
| **B** | léger sous-percement | inférieur au spring, étroit | qualité moindre, tous ne ratent pas : attendre un creux plus haut ou un nouveau test |
| **C** | tenu | égal ou supérieur au spring, ou spread large | test peut-être inachevé : attendre le re-test |
| **D (rejet)** | plus bas | supérieur au spring | ne pas trader : spring raté probable |

**Ce que fait le CO ensuite**

- Réussi : pour le SMI, c'est l'action finale qui confirme le spring ; markup, SOS rapide.
- Raté : le prix réagit sous le spring avant l'arrivée de la demande ; le processus recommence. Si le test est douteux, on attend un second test, qui pèse plus s'il est moins volumique.

**Vérifier en pratique**

- [ ] Un spring identifié en amont, avec son type (#1 ou #2).
- [ ] Volume du test inférieur à celui du spring.
- [ ] Grade noté (A à D).
- [ ] Réponse dans les 1 à 3 barres ; sinon *negative action*.

**Lecture crypto.** OI coin plat ou en légère baisse : pas de nouveaux shorts. Si l'OI monte : OI en hausse + ratio L/S en baisse + flux vendeur lourd = des vendeurs se construisent, le test peut échouer ; OI plat + liquidations nulles + creux plus haut = offre épuisée.

**Invalidation.** Clôture sous le low du spring, ou test de grade D.

**Trade**

- Entrée : clôture de la barre de demande qui suit le test, ou ordre stop au-dessus du high de la barre de test (la confirmation vient à vous).
- Stop : sous le low du spring (point de danger de Pruden : l'offre y a été consommée ; y revenir annule le spring).
- Objectif : creek / high de l'AR (borne haute de la plage), puis décompte P&F depuis le LPS ; R:R ≥ 3.

**Piège fréquent.** Accepter un test plus volumique que le spring.

#### 3.9 LPS de Phase C — test plus haut, sans spring (schéma #2)

**En une phrase.** Sans spring, l'offre est testée plus haut dans la plage, sur un creux plus haut, à volume et spread réduits.

**La question du CO.** Puis-je vérifier l'épuisement de l'offre sans enfoncer le support ? **Pourquoi c'est important.** Pas de stops bon marché à ramasser, mais un fond plus fort. L'information est moins nette ; Pruden préfère le spring, qui nettoie mieux l'offre restante.

**Signature valide**

- Fin de Phase B ou Phase C, creux plus haut que le SC et les ST.
- Volume inférieur à celui du creux précédent testé ; spread qui se resserre.
- Retournement, puis confirmation par un SOS.
- Repères [H] : `vol_ratio ≤ 0.85`, `spread_atr ≤ 0.7`.

**Ce que fait le CO ensuite**

- Réussi : SOS, puis LPS de Phase D.
- Raté : retour sous les creux précédents ; Phase B qui continue, ou spring à venir. Sans SOS, un creux plus haut de Phase B ne se distingue pas d'un LPS de Phase C.

**Vérifier en pratique**

- [ ] Volume inférieur au creux précédent testé.
- [ ] Phase B mûre en amont.
- [ ] Étiquette « LPS C ? » jusqu'au SOS.

**Lecture crypto.** Volume sec, OI coin plat ou en baisse ; si l'OI monte, mêmes tierces que pour le test du spring.

**Invalidation.** Cassure du creux précédent (low du ST de Phase B) sur volume en hausse.

**Trade**

- Entrée : barre de demande au départ du LPS.
- Stop : sous le low du LPS de Phase C (dernier creux défendu par la demande), ou sous le low précédent pour un stop plus large.
- Objectif : creek (borne haute de la plage), puis décompte P&F ; R:R ≥ 3.

**Piège fréquent.** Appeler « LPS » chaque creux plus haut avant le SOS.

### Phase D — la demande prouve qu'elle domine

> **À retenir** — La Phase D alterne des avances (SOS) sur spread et volume croissants, et des réactions (LPS) sur spread et volume réduits. Si ce motif n'apparaît pas, Pruden conseille de ne pas renforcer et d'envisager de clôturer. Le SOS est lui-même un **test de la demande** : chez Wyckoff, le CO pousse des titres à de nouveaux plus-hauts pour attirer les acheteurs extérieurs.

#### 3.10 SOS mineur — progression dans la plage

**En une phrase.** Poussée large et volumique qui reste sous le creek majeur ; elle mesure la demande quand le CO cesse de plafonner les rallyes.

**La question du CO.** Quand je cesse de plafonner, la demande suit-elle ? **Pourquoi c'est important.** Le CO commence à lever des offres. Le risque : un sommet sans suite qui retombe au support. Pruden y voit le saut d'un creek **mineur**.

**Signature valide**

- Après le test de Phase C, dans la plage, sous le creek majeur.
- Volume en hausse par rapport aux réactions, spread large, clôture haute ; une vague, pas une barre isolée.
- Repères [H] : `vol_ratio ≥ 1.3`, `spread_atr ≥ 1.3`, `clv ≥ 0.6` (seuil du code).

**Ce que fait le CO ensuite**

- Réussi : réaction sèche vers un LPS plus haut (fiche 3.11).
- Raté : réaction large et volumique jusqu'au support ; s'il y a de l'offre, retour en Phase B. Sans expansion de volume, Fraser refuse de parler de JAC.

**Vérifier en pratique**

- [ ] Un test de Phase C a précédé.
- [ ] Position : dans la plage (mineur) ou au-dessus du creek (JAC, fiche 3.12).
- [ ] Réaction suivante plus sèche que la poussée.

**Lecture crypto.** OI coin en hausse avec le prix = longs neufs, version forte ; OI coin en baisse = rachat de shorts, version faible (cas BTC 64 800). Pour attribuer : prix en hausse + OI coin en hausse + shorts liquidés + funding contenu = vraie demande qui presse les shorts ; funding qui s'envole avec l'OI = longs encombrés.

**Invalidation.** Réaction large et volumique jusqu'au support ; pic de volume sur le LPS suivant.

**Trade**

- Entrée : aucune sur la barre SOS ; attendre la réaction suivante, le LPS (Villahermosa). La branche majeure du creek reste au-dessus.
- Stop et objectif : sans objet ; le SOS sert à **préparer** l'achat du LPS.

**Piège fréquent.** Appeler « JAC » un SOS mineur et l'acheter, ou lire l'OI en USD.

#### 3.11 LPS successifs — Phase D, dans la plage

**En une phrase.** Après chaque SOS, un repli sec forme un creux plus haut dans la plage : les acheteurs reviennent plus haut à chaque fois.

Malgré le mot *last*, il peut y avoir plusieurs LPS. **Convention du projet** : « LPS » désigne un repli **dans** la plage, avant le JAC ; le repli après le JAC est un BU/BUEC.

**La question du CO.** Les acheteurs reviennent-ils plus haut ? La demande publique prend-elle le relais ? **Pourquoi c'est important.** Le CO laisse respirer sans soutenir ; chaque creux plus haut mesure la demande, un LPS volumique signale de l'offre.

**Signature valide**

- Entre le test de Phase C et le JAC, souvent sur d'anciennes résistances internes ; plusieurs, en escalier.
- Volume inférieur au SOS précédent ; spread étroit ; réaction plus courte que la poussée.
- Le prix ne repasse plus sous le niveau du LPS.
- Repères [H] : `vol_ratio ≤ 0.85`, `spread_atr ≤ 0.7`, `clv ≥ 0.5` au retournement.

**Ce que fait le CO ensuite**

- Réussi : nouvelle poussée, jusqu'au JAC.
- Raté : un LPS casse le low du précédent ; retour en Phase B.

**Vérifier en pratique**

- [ ] Un SOS, même mineur, a précédé.
- [ ] Creux plus haut que le LPS (ou le test) précédent.
- [ ] Volume moyen des poussées supérieur à celui des réactions depuis la Phase C [H].

**Lecture crypto.** OI coin stable ou en légère baisse (prises de bénéfices) ; un OI qui s'effondre pendant la baisse signale des longs qui fuient. Seulement si l'OI est ambigu : funding qui refroidit, liquidations faibles.

**Invalidation.** Cassure du low du LPS précédent (dernier creux plus haut validé) ; pic de volume sur le LPS.

**Trade**

- Entrée : premières barres de demande au retournement.
- Stop : sous le low du LPS (dernier creux défendu par la demande), ou sous le low précédent.
- Objectif : creek en premier relais (borne haute de la plage), puis décompte P&F compté depuis ce LPS ; R:R ≥ 3. On ne renforce qu'une position gagnante.

**Piège fréquent.** Prendre *last* au pied de la lettre, ou confondre un LPS dans la plage avec un BUEC.

#### 3.12 JAC / SOS majeur — franchir le creek

**En une phrase.** La demande franchit le creek (la résistance sinueuse des sommets de la plage) sur expansion de volume et de spread ; c'est une tentative de sortie tant que le back-up n'a pas eu lieu.

**La question du CO.** La demande peut-elle franchir l'offre flottante, et la sortie sera-t-elle acceptée ? **Pourquoi c'est important.** Le CO passe de passif à agressif et paie l'écart. Le risque : une fausse cassure (UT ou UTAD).

**Signature valide**

- Fin de Phase D, au-dessus de la **zone** du creek (une zone, pas un prix ; parfois une branche mineure et une majeure).
- Forte hausse de volume, barres qui s'élargissent, clôture près du haut ; acceptation sur plusieurs barres.
- Repères [H] : `vol_ratio ≥ 1.3`, `spread_atr ≥ 1.3`, `clv ≥ 0.6`, clôture au-dessus du high de la plage.

**Ce que fait le CO ensuite**

- Réussi : BU sec qui tient (fiche 3.13), puis markup.
- Raté : le prix rentre dans la plage ; c'était un upthrust. Si le volume monte mais que le spread se resserre à la cassure (effort sans résultat), on étiquette « SOS ou UTAD selon la tenue ».

**Vérifier en pratique**

- [ ] Séquence C → D accomplie : test de Phase C, au moins un LPS.
- [ ] Statut « tentative » jusqu'à la tenue et au BU.
- [ ] Pas d'effort sans résultat.

**Lecture crypto.** OI coin en hausse avec le prix = longs neufs, version forte ; en baisse = couverture de shorts, version faible qui exige un BU. Pour attribuer un OI en hausse : funding contenu et shorts liquidés = demande réelle ; funding extrême = foule encombrée, risque de *flush*.

**Invalidation.** Réintégration de la plage sur volume ; retour vers le niveau moyen des clôtures de la plage (profil UTAD).

**Trade**

- Entrée : aucune sur la barre de cassure (si elle est fausse, le retournement est rapide). On attend le BU, ou la quatrième entrée de Fraser : la cassure du high du BU/SOS, **après** le BU.
- Stop (entrée après le BU) : sous le low du BU (le test qui a validé le saut).
- Objectif : décompte P&F depuis le LPS ; R:R ≥ 3.

**Piège fréquent.** Acheter la barre de cassure, ou ignorer la branche majeure du creek encore au-dessus.

> **Penser comme le CO** — Le récit d'Evans, relayé par Pruden, contient **deux** reculs. Avant le saut, le scout sonde le bord du ruisseau, voit le flot d'offre se tarir, et recule pour prendre de l'élan : c'est le spring ou le LPS. Après le saut, fatigué, il revient se reposer au bord : c'est le BUEC. La puissance du saut se mesure au spread et au volume.

### Transition D → E — le back-up vérifie la nouvelle polarité

#### 3.13 BU / BUEC — back-up sur l'ancienne résistance

**En une phrase.** Juste après le JAC, le prix revient toucher le creek par le dessus sur volume plus faible et spread étroit ; il vérifie que l'ancienne résistance est devenue support.

Pour Pruden et Wyckoff Analytics, le BU est le **mouvement** de retour et son point bas est un LPS. Fraser (2015) et Villahermosa emploient BUEC et LPS comme synonymes. Une page posthume (1937) du cours de Wyckoff décrivait déjà la chose : au retour sur les anciens sommets, range qui se resserre et volume qui chute, le titre est en « seconde position de tremplin ». La différence avec le LPS de Phase D est une affaire de lieu et de moment :

<!-- FIG:lps_vs_buec -->

**La question du CO.** L'ancienne offre est-elle partie ? **Pourquoi c'est important.** Le repli mêle prises de bénéfices et test d'une offre supplémentaire autour de l'ancienne résistance. S'il échoue, la sortie était un upthrust.

**Signature valide**

- Immédiatement après le JAC, sur le creek touché par le dessus ; peut s'étirer en petite plage plus haute.
- Volume nettement plus léger que le saut ; spread étroit, barres entrelacées.
- Profondeur, deux écoles. Stricte (Fraser 2018, Villahermosa) : pas de retour dans la plage. Tolérante (Fraser 2022) : plus c'est court, mieux c'est, mais un repli plus profond reste haussier ; Pruden place le stop sous le spring.
- Repères [H] : `vol_ratio ≤ 0.85`, `spread_atr ≤ 0.7`, `clv ≥ 0.5` au retournement.

**Ce que fait le CO ensuite**

- Réussi : l'offre ne reprend pas le contrôle ; le markup démarre (Phase E).
- Raté : correction à ranges larges et volume élevé ; c'était un upthrust. Sur un volume moyen, attendre des tests successifs.

**Vérifier en pratique**

- [ ] Volume du BU inférieur à celui du JAC.
- [ ] Pas de clôture dans la plage (stricte), ou tenue au-dessus du dernier creux majeur (tolérante).
- [ ] Un second BU n'a rien d'anormal (« SOS 2 / BUEC 2 » chez Fraser, points 12 et 14 chez Pruden).

**Lecture crypto.** Volume qui sèche, OI coin stable ou en légère baisse (prises de bénéfices) ; un effondrement d'OI signale des longs qui fuient. Seulement si l'OI est ambigu : funding qui refroidit depuis le SOS, liquidations faibles.

**Invalidation.** Stricte : clôture dans la plage sur spread large et volume fort. Tolérante : retour vers le milieu de la plage ou cassure du low du spring. Annoncer l'école choisie.

**Trade**

- Entrée : dans la force des barres de demande au départ du BU.
- Stop serré : sous le low du BU et sous le creek (une réintégration invalide le JAC). Stop structurel : sous le low du spring (invalidation du schéma, choix de Pruden ; dans son cas Nokia, entrée vers 110–115 (zone du BUEC, juste au-dessus du creek majeur, lui-même situé un peu au-dessus de 110) et stop juste sous 100 (niveau du spring)).
- Objectif : décompte P&F depuis le LPS ; R:R ≥ 3.

**Piège fréquent.** Acheter le saut au lieu du BU, ou accepter un BU volumique.

### Phase E — la tendance continue de se tester

#### 3.14 Test de continuation — test en marché haussier (Williams)

**En une phrase.** En tendance haussière, une barre baissière à faible volume revient vers une zone de fort volume récente ; elle vérifie que l'offre de la poussée n'est pas revenue.

**La question du CO.** Après une poussée volumique, l'offre est-elle revenue ? **Pourquoi c'est important.** Après des jours de fort volume haussier, le marché doit souvent se reposer le temps que la vente disparaisse. Le risque : un SOW de tendance.

**Signature valide**

- Tendance haussière établie, ou sortie de plage confirmée (jamais dans un downtrend).
- Barre baissière vers une zone de fort volume récente ; volume inférieur à la poussée testée.
- Clôture au milieu ou en haut (`clv ≥ 0.5` [H]) ; barre suivante haussière.

**Ce que fait le CO ensuite**

- Réussi : reprise de la tendance ; des barres baissières sèches après le dépassement d'une résistance annoncent des prix plus hauts.
- Raté : barre baissière large, volumique, clôture basse (SOW de tendance). Sans réponse : *negative action*.

**Vérifier en pratique**

- [ ] Force dans le *background*.
- [ ] Volume inférieur à la poussée testée ; `vol_ratio ≤ 0.85` [H].
- [ ] Barre suivante haussière (un test se confirme sur deux barres).

**Lecture crypto.** OI coin plat ou en baisse (prises de bénéfices). Seulement si l'OI est ambigu : OI en hausse avec ratio L/S en baisse = shorts contre la tendance, carburant si elle reprend, alerte si une barre d'offre suit.

**Invalidation.** Barre d'offre (spread large, volume fort, clôture basse) sous le low du test.

**Trade**

- Entrée : ordre stop au-dessus du high de la barre de test (la confirmation déclenche l'entrée).
- Stop : sous le low du test, ou sous le low du dernier LPS/BU (dernier support validé).
- Objectif : prochaine résistance, ou décompte de palier ; R:R ≥ 3.

**Piège fréquent.** Acheter ce montage dans un downtrend.

#### 3.15 Réaccumulation — palier (*stepping stone*) en Phase E

**En une phrase.** Plage de pause dans une tendance haussière, où le CO absorbe les prises de bénéfices et renforce ; à distinguer d'une distribution.

**La question du CO.** Ces ventes sont-elles des prises de bénéfices que j'absorbe, ou une distribution ? **Pourquoi c'est important.** Le CO utilise ces pauses pour renforcer ; la confusion est possible dans les deux sens.

**Signature valide**

- N'importe où en Phase E ; un BU peut devenir une telle plage.
- Phase A souvent sans PS, SC et ST nets : elle ressemble plutôt à une Phase A de distribution.
- Chaque baisse vers le support se fait sur moins de volume que la précédente.
- Durée et amplitude plus faibles que la base primaire ; bas de structure vers le tiers ou la moitié de la structure achevée (Fraser).

**Ce que fait le CO ensuite**

- Réussi : spring tardif, SOS au-dessus du sommet de la plage, BUEC, reprise.
- Raté : volume lourd et croissant sur les baisses, sommets plus bas ; c'est une distribution. Le test décisif reste la capacité à dépasser la résistance.

**Vérifier en pratique**

- [ ] Tendance haussière en amont.
- [ ] Volume des baisses décroissant.
- [ ] Les deux scénarios tenus jusqu'à la sortie.

**Lecture crypto.** OI coin en baisse sur les baisses (prises de bénéfices), en hausse à la sortie. Si le prix cale : funding qui se normalise = sain ; funding très élevé + OI en hausse + prix qui cale au sommet = risque de distribution.

**Invalidation.** Volume lourd et croissant sur les baisses ; cassure du bas sans réintégration ; échec sous la résistance.

**Trade**

- Entrée : test du spring tardif, ou BU au-dessus du sommet de la plage.
- Stop : sous le low du spring tardif ou du BU (dernier creux défendu du palier).
- Objectif : décompte de palier (à plus petite case) ; R:R ≥ 3.

**Piège fréquent.** Shorter une réaccumulation prise pour un sommet de distribution, erreur fréquente.

## 4. Micro-tests VSA : la barre de test n'est pas une barre de no supply

La VSA descend de Wyckoff : le syndicat de traders de Beverly Hills pour lequel travaillait Williams lui a fait suivre le cours Wyckoff, et TradeGuider s'est d'abord appelé « Wyckoff VSA ». Mais la VSA étiquette des **barres** à la lumière du *background* (ce que disent les barres précédentes), quand Wyckoff lit une **structure**. Un test VSA n'exige ni AR préalable ni retour au climax : ce n'est pas le ST wyckoffien. La confusion la plus fréquente oppose la barre de test, geste provoqué, et la barre de no supply, état passif :

<!-- FIG:testbar_vs_nosupply -->

#### 4.1 Barre de test (Williams, TradeGuider, Coulling)

**En une phrase.** Pendant la barre, le prix est marqué vite à la baisse dans une zone d'offre antérieure, puis reprend pour clôturer haut sur volume faible.

**La question du CO.** Si je marque vite les prix à la baisse, les vendeurs sortent-ils de l'ombre ? **Pourquoi c'est important.** Le professionnel ne peut pas monter les prix pendant que d'autres vendent dans le même marché sans perdre d'argent. Un volume faible sur le marquage montre peu de ventes ; un volume fort montre que l'offre est là.

**Signature valide**

- Force dans le *background* : SC, *stopping volume*, absorption ou tendance haussière.
- La barre plonge dans une zone de fort volume antérieure (une zone d'offre).
- Mèche basse ; clôture sur ou près du haut (version stricte), au milieu ou en haut (version permissive).
- Volume plus faible que celui de la zone d'offre testée.
- Aucune exigence de range étroit (la remarque de TradeGuider sur un spread étroit « à moindre impact » suit la variante *shakeout* de l'indicateur ; sa portée est ambiguë). Coulling préfère un corps étroit à mèche profonde.
- Bonus : nouveau plus-bas, barre baissière. Non requis : volume inférieur aux deux barres précédentes (critère du no supply).

**Ce que fait le CO ensuite**

- Réussi (volume faible) : le marché est prêt à monter immédiatement.
- Raté (volume élevé) : hausse temporaire, puis re-test de la même zone plus tard ; la forme en W vient de ce re-test d'une zone qui avait trop d'offre.
- Sans réponse dans la barre suivante ou le jour d'après : faiblesse (*negative action*).

**Vérifier en pratique**

- [ ] Force dans le *background* et zone de fort volume antérieure.
- [ ] Volume inférieur à celui de la zone testée (afficher aussi `vol_ratio` [H]).
- [ ] Clôture au milieu ou en haut : `clv ≥ 0.5` [H], idéalement ≥ 0,7 [H] ; ne **pas** exiger `spread_atr ≤ 0.7`.
- [ ] Barre suivante haussière ; sinon *negative action* après 2 à 3 barres.

**Lecture crypto.** C'est ici que joue la nuance de Williams : en marché à terme, un test volumique peut montrer de la force, et TradeGuider admet un volume élevé en futures. Sur perps, le volume seul ne tranche donc pas ; l'OI en coin arbitre. OI en baisse sur un test volumique = fermetures et absorption, plutôt constructif. OI en hausse sur un marquage volumique = nouveaux vendeurs, re-test probable ; si le prix cale, croiser les tierces.

**Invalidation.** Clôture basse sur volume fort sous le low du test. Une barre suivante baissière avec de la faiblesse dans le *background* est un *failed test* au sens de TradeGuider.

**Trade**

- Entrée : ordre stop au-dessus du high de la barre de test (la confirmation vient à vous).
- Stop : sous le low de la barre climactique (l'action testée : sous elle, l'offre n'a pas été absorbée).
- Objectif : borne haute de la structure (première résistance), puis décompte ; R:R ≥ 3.

**Piège fréquent.** Confondre test et no supply, exiger un range étroit, ou prendre un test sur fond de distribution : sans force dans le *background*, il ne veut presque rien dire.

#### 4.2 No supply (absence de pression vendeuse)

**En une phrase.** Barre baissière à volume inférieur aux deux barres précédentes, de préférence étroite, clôture au milieu ou en haut : personne ne vend.

**La question du CO.** Aucune : c'est un état **passif**, pas un geste provoqué. **Pourquoi c'est important.** Un manque de vendeurs n'est pas une demande.

**Signature valide**

- Barre baissière, volume inférieur à celui des deux barres précédentes.
- Spread de préférence étroit, clôture au milieu ou en haut.
- De préférence en tendance haussière ou après de la force.
- Proxy [H] : volume < min(vol[t−1], vol[t−2]), `spread_atr ≤ 0.7`, `clv ≥ 0.5`.

**Ce que fait le CO ensuite**

- Confirmé : la barre suivante monte. Une clôture au milieu ou en haut peut aussi représenter un test (d'où l'indicateur « No Supply/Test »).
- Non confirmé : la barre suivante baisse ; rien n'est prouvé.

**Vérifier en pratique**

- [ ] Barre suivante haussière.
- [ ] Tendance de fond haussière (pas d'achat dans un downtrend).

**Lecture crypto.** Volume plus bas que les deux barres précédentes, OI coin plat. Tierces rarement nécessaires.

**Invalidation.** Barre suivante baissière et volumique.

**Trade**

C'est un déclencheur de **continuation** dans une tendance déjà prouvée (voir fiche 3.14), jamais un retournement à lui seul.

- Entrée : au-dessus du high de la barre de confirmation (la demande a répondu).
- Stop : sous le low de la barre de no supply, ou sous le low du dernier LPS/BU (dernier support validé).
- Objectif : prochaine résistance ; R:R ≥ 3.

**Piège fréquent.** Le prendre pour un test : il n'a ni lieu ni geste.

#### 4.3 No demand (et test de la demande)

**En une phrase.** Barre haussière étroite à volume inférieur aux deux précédentes, clôture au milieu : personne n'achète ; c'est le miroir du no supply.

**La question du CO.** En distribution : reste-t-il des acheteurs pour gêner ma baisse ? Coulling décrit ce test de la demande : le marché est poussé plus haut, souvent sur une nouvelle, et sans demande il revient près de l'ouverture sur un volume très faible. **Pourquoi c'est important.** On vérifie l'absence d'acheteurs professionnels sur la hausse. Le risque : shorter une tendance haussière saine.

**Signature valide**

- Barre haussière à spread étroit, clôture au milieu, volume inférieur aux deux barres précédentes. Elle peut être baissière si son high dépasse celui de la barre précédente.
- Près d'un ancien sommet, ou dans un rallye sous une résistance.
- Proxy [H] : volume < min(vol[t−1], vol[t−2]), `spread_atr ≤ 0.7`, `clv ≤ 0.5`.

**Ce que fait le CO ensuite**

- Confirmé : la barre suivante baisse. Près d'un ancien sommet à gauche, il est très improbable que le marché le franchisse sans demande.
- Raté (pour le distributeur) : un test de la demande raté arrête net la campagne.

**Vérifier en pratique**

- [ ] Barre haussière étroite, volume inférieur aux deux précédentes.
- [ ] Barre suivante baissière : la confirmation précède tout short.
- [ ] Faiblesse dans le *background* (un no demand en tendance haussière est au mauvais endroit).

**Lecture crypto.** Hausse à faible volume, OI coin plat ou en baisse (rachat de shorts sans longs neufs). Si l'OI monte pendant que le prix cale : funding et ratio L/S. Des longs qui entrent sous la résistance sont piégés si la barre suivante baisse.

**Invalidation.** Barre suivante haussière et volumique qui passe l'ancien sommet.

**Trade**

- Entrée short : après la barre baissière de confirmation, seulement sous résistance et sur fond de faiblesse.
- Stop : au-dessus du high de la barre de no demand, ou du sommet testé (la résistance que la demande n'a pas pu franchir).
- Objectif : borne basse de la plage ; R:R ≥ 3.

**Piège fréquent.** Shorter un no demand dans une tendance haussière, ou sans confirmation.

> **Piège** — *Failed test* a trois sens. (A) Un test **volumique** : l'offre est présente, un re-test est attendu. (B) Un test **sans réponse** : *negative action*. (C) L'indicateur TradeGuider « Failed Test » : une barre baissière large sous les plus-bas récents juste après un test. Préciser lequel à chaque usage.

## 5. Fiches de tests — distribution : le CO teste s'il reste des acheteurs

En distribution, tout s'inverse : le CO vend, et il teste s'il reste assez d'acheteurs pour absorber son offre. Distribution, redistribution et réaccumulation se ressemblent. La Phase A d'une redistribution peut ressembler au début d'une accumulation ; celle d'une réaccumulation ressemble plutôt à une distribution. Selon Pruden, la distribution se fait en général plus vite que l'accumulation. Le schéma miroir :

<!-- FIG:schema_distribution -->

| Phase | Test (fiche) | Ce qui est testé |
|---|---|---|
| A | ST du BC (5.1) | la demande résiduelle au sommet |
| B | UT in Phase B, SOW in Phase B (5.2) | la demande de cassure à qui vendre ; la demande sous l'AR |
| C | UTAD (5.3) | le test final de la nouvelle demande au-dessus de la plage |
| C | Test de l'UTAD (5.4) | la demande restante après l'UTAD |
| D | LPSY (5.5) | la difficulté à monter après un SOW |
| D→E | FTI et retour sous la glace (5.6) | la conversion support → résistance |

#### 5.1 ST du BC (Phase A de distribution)

**En une phrase.** Après le BC et l'AR, le prix remonte vers la zone du BC pour mesurer la demande résiduelle au sommet ; ce ST peut prendre la forme d'un upthrust.

**La question du CO.** Reste-t-il assez de demande au sommet pour absorber mon offre ? **Pourquoi c'est important.** Le CO veut vendre sans faire baisser le prix trop tôt. Le risque : une réaccumulation, où le sommet n'en est pas un.

**Signature valide**

- Retour vers la zone du BC ; sommet égal ou un peu plus bas, parfois un léger dépassement (UT).
- Volume : les sources divergent. Pour Wyckoff Analytics, volume et spread baissent à l'approche du BC. Pour Fraser, le sommet du ST est marqué par un volume élevé et des barres de retournement. Réconciliation : volume en baisse sur la **montée**, volume fort sur les **barres de retournement**.
- Clôture faible sur le retournement (`clv ≤ 0.5` [H]).

**Ce que fait le CO ensuite**

- Réussi : retour vers le bas de la plage ; Phase B.
- Raté (sommet accepté au-dessus du BC) : réaccumulation possible ; tenir les deux scénarios.

**Vérifier en pratique**

- [ ] BC identifiable (climactique, clôture faible), puis AR.
- [ ] Sommet au niveau du BC ou plus bas, ou dépassement aussitôt rejeté.
- [ ] Contexte HTF : tendance haussière mûre (distribution) ou baissière (redistribution).

**Lecture crypto.** OI coin en hausse dans la zone du BC avec une clôture faible : des longs s'ouvrent face à l'offre du CO, donc des longs piégés. Dans un downtrend, un OI en hausse à la résistance est une demande qui se fait piéger. Pour l'attribuer : funding élevé + ratio L/S en hausse = foule acheteuse encombrée.

**Invalidation.** Acceptation au-dessus du BC avec un repli sec qui tient : réaccumulation.

**Trade**

- Pour un détenteur : alléger dans les sommets du BC, du ST et des UT (Fraser fait des Phases A et B les zones tactiques de vente).
- Pour un short : pas d'entrée ici ; attendre la Phase D (fiche 5.5).
- Niveaux à tracer : plafond = high du BC (borne haute de la plage) ; plancher = low de l'AR (borne basse).

**Piège fréquent.** Exiger un volume sec alors que Fraser décrit un retournement volumique.

#### 5.2 UT in Phase B (et SOW in Phase B / mSOW)

**En une phrase.** Pendant la Phase B, le prix perce brièvement au-dessus du BC puis échoue ; le CO vend dans la demande des acheteurs de cassure. Le SOW in B est la chute qui casse ensuite le low de l'AR.

**La question du CO.** Puis-je attirer la demande de cassure et lui vendre ? Puis, sur le SOW in B : combien de demande reste-t-il sous l'AR ? **Pourquoi c'est important.** Le CO vend sans coût dans la demande des acheteurs de momentum. Le risque : une vraie sortie (réaccumulation).

**Signature valide**

- Au-dessus du high du BC, et bref : un UT ne s'attarde pas au-dessus de la résistance avant de revenir au support.
- Deux profils de barre. SMI : spread plus étroit, volume plus fort, clôture faible. Williams : volume faible (pas de demande) ou fort (l'offre domine), clôture sur ou près des bas.
- Phase B : volume fort sur les baisses, de plus en plus à chaque baisse depuis la résistance.
- SOW in B : chute qui casse le low de l'AR sur spread et volume accrus.
- Repères [H] : barre de réintégration `clv ≤ 0.5` ; effort sans résultat = `vol_ratio ≥ 1.3` avec `spread_atr` en baisse.

**Ce que fait le CO ensuite**

- Réussi (pour le distributeur) : retour rapide au support, puis SOW sous l'AR, un indice de plus que la distribution est en cours.
- Raté : acceptation au-dessus avec un repli sec (mSOS/SOS d'une réaccumulation).

**Vérifier en pratique**

- [ ] Percée au-dessus du BC puis réintégration rapide, profil SMI ou Williams.
- [ ] Volume plus fort sur les baisses que sur les hausses (*activity bearish*).
- [ ] SOW in B : creux sous l'AR sur volume et spread en hausse.

**Lecture crypto.** OI coin en hausse sur la percée puis réintégration : acheteurs de cassure piégés. Pour l'attribuer : shorts liquidés sur la mèche (stops acheteurs au-dessus du BC), funding qui grimpe, ratio L/S en hausse. Le forcé et le FOMO ont servi de contrepartie au CO.

**Invalidation.** Le prix tient au-dessus du BC plusieurs barres, avec un repli sec.

**Trade**

Shorter l'UT est possible mais risqué : les professionnels sortent souvent ces shorts avec un UT après l'autre, et il est plus sûr d'attendre la Phase D et un LPSY. Si l'on prend le risque, en taille réduite :

- Entrée : sous le low de la barre de réintégration (le rejet est confirmé).
- Stop : au-dessus du high de l'UT (extrême du piège ; y revenir signale une demande réelle).
- Objectif : low de l'AR (borne basse de la plage) ; R:R ≥ 3.

**Piège fréquent.** Shorter chaque UT, ou prendre un UT pour un SOS. Williams rappelle qu'on voit rarement des upthrusts dans les marchés forts.

#### 5.3 UTAD — Upthrust After Distribution

**En une phrase.** En fin de distribution, le prix casse au-dessus du BC et des UT, puis rentre dans la plage ; c'est le test final de la nouvelle demande, le miroir du spring.

**La question du CO.** Après la cassure du plafond, reste-t-il une demande nouvelle capable de tenir ? **Pourquoi c'est important.** Le CO vend aux acheteurs de cassure et aux shorts qui se couvrent : les shorts faibles rendent leurs positions et de nouveaux acheteurs, moins informés, prennent l'offre. Le risque : la cassure tient (JAC d'une réaccumulation).

**Signature valide**

- Fin de plage (Phases A et B accomplies), au-dessus du BC et des UT : l'UTAD dépasse le BC par construction. Il n'est pas obligatoire (schéma de distribution #2).
- Deux profils baissiers selon Pruden : volume faible sans suivi, ou volume fort avec retour au centre de la plage.
- Effort sans résultat : volume en hausse, spread qui se resserre relativement, puis retour vers le niveau moyen des clôtures de la plage. Le spread doit toujours être comparé au volume.
- Repères [H] : `pen_atr ≥ 0.1` ATR ; barre de retour `clv ≤ 0.5`.

**Ce que fait le CO ensuite**

- Réussi : échec dans la plage, puis chute en cascade vers et sous le support. L'offre domine clairement après une cassure du support, ou une baisse sous le milieu de la plage.
- Raté (pour le distributeur) : tenue au-dessus avec un BU sec ; c'était un JAC.
- Ambigu : un upthrust qui retombe au milieu d'une plage trop large pour être une distribution complète (troisième variante de Pruden).

**Vérifier en pratique**

- [ ] Phases A et B accomplies ; sinon c'est un UT de Phase B.
- [ ] Confirmation : cassure sous le milieu de la plage.
- [ ] Étiquette « SOS ou UTAD selon la tenue » tant que la plage n'est pas cassée.

**Lecture crypto.** OI coin en hausse sur la percée (longs de FOMO) puis réintégration : longs piégés. Pour l'attribuer : shorts liquidés à la montée, funding qui monte, puis longs liquidés à la descente. Un flux acheteur net positif sans progrès du prix signale des vendeurs passifs qui absorbent.

**Invalidation.** Tenue au-dessus de la plage avec un BU sec qui ne réintègre pas : JAC/SOS de réaccumulation.

**Trade**

- Entrée : short agressif après la réintégration ; short prudent sur le test de l'UTAD (fiche 5.4) ou sur le LPSY.
- Stop : au-dessus du high de l'UTAD (extrême du piège ; y revenir en clôture signale une demande réelle).
- Objectif : plancher = low de l'AR (borne basse de la plage), puis décompte P&F baissier ; R:R ≥ 3.

**Piège fréquent.** Appeler UTAD une percée de Phase B, ou oublier la lecture réaccumulation : conclure à tort à une distribution est une erreur courante.

#### 5.4 Test de l'UTAD

**En une phrase.** Après l'UTAD, un rallye vers sa zone vérifie qu'il ne reste plus d'acheteurs. Aucune source ne lui donne de critères propres : on les déduit par miroir du test du spring.

**La question du CO.** Un rallye vers le sommet trouve-t-il encore des acheteurs ? **Pourquoi c'est important.** Il confirme l'épuisement de la demande. Le risque : une seconde poussée qui casse vraiment.

**Signature valide** (par miroir du test du spring)

- Après un UTAD réintégré, rallye vers sa zone, en fin de Phase C.
- Volume inférieur à celui de l'UTAD ; spread étroit.
- Sommet plus bas que l'UTAD ; clôture faible ; baisse dans les 1 à 3 barres.
- Repères [H] : `vol_ratio ≤ 0.85`, `spread_atr ≤ 0.7`, `clv ≤ 0.5`.

**Ce que fait le CO ensuite**

- Réussi : SOW, Phase D.
- Raté : nouveau plus-haut sur volume plus fort, début d'une vraie cassure.

**Vérifier en pratique**

- [ ] Un UTAD réintégré en amont.
- [ ] Volume inférieur à l'UTAD, sommet plus bas.
- [ ] Barre baissière de confirmation.

**Lecture crypto.** Rallye sec, OI coin plat ou en baisse (rachats de shorts sans longs neufs). OI en hausse avec un prix qui cale : des longs entrent sous le sommet ; ratio L/S en hausse, funding positif et liquidations faibles = longs encombrés sous la résistance.

**Invalidation.** Clôture au-dessus du high de l'UTAD sur volume.

**Trade**

- Entrée short : sous le low de la barre de rejet.
- Stop : au-dessus du high du test (pivot de Phase C) et du high de l'UTAD (extrême du piège).
- Objectif : low de l'AR (borne basse de la plage), puis décompte P&F ; R:R ≥ 3.

**Piège fréquent.** Exiger ce test quand le marché casse directement : un LPSY peut en tenir lieu.

#### 5.5 LPSY — Last Point of Supply (souvent plusieurs)

**En une phrase.** Après un SOW, un rallye faible à spread étroit échoue sous la résistance ; le CO y écoule ses dernières vagues de distribution.

**La question du CO.** Après mon SOW, le marché a-t-il encore la force de monter ? **Pourquoi c'est important.** Il mesure l'épuisement de la demande. Le risque : un spring qui reprend la plage.

**Signature valide**

- Phase D (et E), rallyes faibles après un SOW, sous la glace ou sous des résistances internes ; plusieurs.
- Spread étroit, rallye sans vigueur, sommet plus bas, clôture faible (`clv ≤ 0.5` [H]).
- Volume faible **ou** fort (Pruden) : faible = demande faible, fort = offre importante. Le volume sec n'est pas requis.
- Chaque rallye est moins robuste que le précédent (BC, ST, UT, LPSY).

**Ce que fait le CO ensuite**

- Réussi : markdown, tendance baissière.
- Raté : le rallye reprend la plage et tient ; scénario spring.
- Ambigu : LPSY à volume fort et clôture moyenne ; attendre le rallye suivant (Pruden juge encore meilleur le rallye qui teste son point 11).

**Vérifier en pratique**

- [ ] Un SOW en amont.
- [ ] Rallye à spread étroit, sommet plus bas, moins robuste que les précédents.
- [ ] Ne pas exiger de volume sec : faible ou fort, les deux sont baissiers si le rallye échoue.

**Lecture crypto.** OI coin en baisse pendant le rallye : simple rachat de shorts, pas de demande nouvelle. OI coin en hausse pendant que le prix cale : ratio L/S en hausse, funding en hausse et liquidations faibles = longs encombrés, donc piégés, carburant pour la baisse suivante.

**Invalidation.** Reprise de la glace (le support cassé) et tenue au-dessus.

**Trade**

- Entrée short : sur la barre de rejet qui marque l'échec du rallye.
- Stop : au-dessus du high du LPSY et de la glace cassée (support devenu résistance).
- Objectif : décompte P&F baissier ; R:R ≥ 3. N'ajouter que si les positions initiales sont en gain.

**Piège fréquent.** Shorter en Phase B au lieu d'attendre le LPSY.

#### 5.6 FTI (chute à travers la glace) et retour sous la glace

**En une phrase.** Le FTI est la cassure du support (la glace) sur spread large et volume fort ; le retour sous la glace est son test : le support cassé est-il devenu résistance ?

Conflit de vocabulaire : dans la tradition Evans relayée par Pruden, *falling through the ice* désigne la **cassure** ; Villahermosa étiquette FTI le **retest** et appelle la cassure SOW majeur. Choix du mémo : FTI = la cassure ; « retour sous la glace » = son test.

**La question du CO.** À la cassure : le support cède-t-il sous l'offre ? Au retour : le support cassé est-il devenu résistance ? **Pourquoi c'est important.** C'est la conversion de polarité. Le risque : un spring, si le prix regagne la glace.

**Signature valide**

- Fin de Phase D, début de Phase E.
- FTI : spread extrêmement large et énorme hausse de volume (cas Nokia chez Pruden). Repères [H] : `vol_ratio ≥ 1.3`, `spread_atr ≥ 1.3`, `clv ≤ 0.4`, clôture sous le low de la plage.
- Une pause suit en général ; puis un rallye arrêté à la surface de la glace, désormais résistance, sur spread étroit et volume en général réduit.

**Ce que fait le CO ensuite**

- Réussi : le prix reste sans ressort sous le support ; un markdown suit.
- Raté : dans le récit de Pruden, le scout a deux chances de remonter au-dessus de la glace (une situation de spring) ; s'il échoue deux fois, il coule.

**Vérifier en pratique**

- [ ] Cassure de la glace sur spread et volume en expansion.
- [ ] Rallye de retour à spread étroit qui échoue sous la glace, sans clôture durable au-dessus.
- [ ] Compter les tentatives de reprise : deux échecs = markdown probable.

**Lecture crypto.** FTI avec OI coin en hausse : de nouveaux shorts, version forte. FTI avec OI coin en baisse et liquidations de longs : cascade de liquidations, version plus fragile qui exige un retest. Au retour, seulement si l'OI est ambigu : funding négatif, ratio L/S, liquidations faibles. OI en hausse à la cassure puis OI plat sur un retour sec = l'offre tient le niveau.

**Invalidation.** Le prix reprend la glace et y tient (scénario spring).

**Trade**

- Entrée short : sur l'échec sous la glace ; le test de la cassure est une occasion de vente à haute probabilité selon Wyckoff Analytics.
- Stop : au-dessus du high du retour et de la glace (support devenu résistance).
- Objectif : décompte P&F baissier ; R:R ≥ 3 ; stop suiveur ensuite.

**Piège fréquent.** Vendre la barre de cassure au lieu du retest, ou mélanger les deux sens de FTI.

## 6. Distinctions : même geste, lieu différent, sens différent

### 6.1 ST, test du spring, LPS de Phase C, LPS de Phase D et BU/BUEC ne testent pas la même chose

| Test | Quand et où | Volume à battre | Ce qui est testé | Entrée |
|---|---|---|---|---|
| ST (Phase A) | après SC et AR, zone du low du SC | SC | l'offre résiduelle de la panique | aucune |
| Test du spring | après le spring, zone de son low, creux plus haut | spring | l'offre délogée par le spring | oui, meilleur point d'achat d'un #2 |
| LPS de Phase C | fin de B ou C, sans spring, creux plus haut que SC et ST | dernier creux volumique | l'offre, sans percer le support | oui |
| LPS de Phase D | après un SOS mineur, **avant** le JAC, dans la plage | SOS précédent | la demande qui revient plus haut | oui, à chaque LPS |
| BU / BUEC | **juste après** le JAC, sur le creek touché par le dessus | JAC | le changement de polarité | oui, le setup « sûr » de Pruden |

Combien en attendre : un ou plusieurs ST ; un test du spring (plusieurs après un #1) ; un LPS de Phase C ; plusieurs LPS de Phase D, en escalier ; souvent un BU, parfois deux.

> **À retenir** — Pour Fraser, un LPS et un spring font le même travail : tester un ancien creux à fort volume. Seul le BU teste autre chose : l'absence d'offre **au-dessus** et la conversion de la résistance en support. La règle du projet « LPS ≠ BUEC » est une convention opérationnelle utile : chez Pruden et Wyckoff Analytics, le low du BU **est** un LPS.

### 6.2 Spring, shakeout et terminal shakeout : le lieu et l'intensité font la différence

| Concept | Contexte | Profondeur et volume | Test requis | Acheter la barre ? |
|---|---|---|---|---|
| Spring #3 | fin de plage d'accumulation | faible, sec | non (mais un test n'est pas rare) | oui pour Fraser ; pour le SMI, attendre la demande et le retour dans la plage |
| Spring #2 | fin de plage | modérée, en expansion | oui | non, ou partiellement (SMI) ; acheter le test |
| Spring #1 = shakeout | fin de plage | profonde, fort | oui, parfois plusieurs | divergence : oui (Pruden, point 8), après test (SMI), jamais (Fraser) |
| Terminal shake-out (Wyckoff) | fin de **longue** préparation | plus profond qu'un spring, fort | oui | comme le #1 |
| Shakeout ordinaire | tendance haussière, réaccumulation | variable, volume variable | oui s'il y a de l'offre sur la barre | après test |
| Shake-out VSA | partout | spread large, fort, clôture sur les hauts | peut devoir être re-testé | — |
| SC (comparaison) | fin de tendance baissière | même allure, marché baissier derrière | ST | non |

> **Piège** — La même barre profonde et volumique s'appelle « #1 », « shakeout » ou « terminal shakeout » selon l'auteur. Le glossaire du SMI fait du terminal shake-out le concept parent du spring ; O'Brien et Villahermosa en font le type #1. Le mécanisme est le même : on retient le comportement (profondeur × volume × vitesse de réintégration).

### 6.3 JAC contre UTAD : la barre de cassure ne tranche pas, la suite tranche

Une même cassure peut finir de deux façons : tenue et BU sec (JAC), ou retour dans la plage (upthrust ou UTAD).

<!-- FIG:jac_vs_utad -->

| Critère | JAC / SOS majeur | UTAD / upthrust |
|---|---|---|
| Contexte HTF | tendance haussière, ou bas de cycle avec accumulation **gagnée** | tendance haussière mûre (distribution) ou downtrend (redistribution, défaut du projet) |
| Séquence | après le test de Phase C et des LPS | après les Phases A et B ; UT en B, UTAD en fin de plage |
| Barre de cassure | spread qui s'élargit, volume en expansion, clôture près du haut | volume en hausse avec spread qui se **resserre**, ou volume faible sans suivi ; clôture faible |
| Acceptation | plusieurs clôtures au-dessus du creek | réintégration rapide |
| Repli suivant | BU sec et étroit qui tient le creek | repli large et volumique qui réintègre |
| OI coin | en hausse avec le prix (longs neufs) ; en baisse = squeeze fragile | en hausse sur la percée puis réintégration = longs piégés |
| Tierces | funding contenu, shorts liquidés | funding qui saute, shorts liquidés sur la mèche, puis longs liquidés |
| Verdict | **après** le BU | **après** la réintégration ou la cassure du milieu de plage |

### 6.4 LPSY contre test de l'UTAD

| Critère | LPSY | Test de l'UTAD |
|---|---|---|
| Moment | après un SOW (Phases D, E) | après l'UTAD (fin de Phase C) |
| Lieu | sous la glace cassée ou sous une résistance interne | vers la zone de l'UTAD, au-dessus ou près du BC |
| Volume | faible ou fort | inférieur à l'UTAD (par miroir) |
| Sommet | plus bas que le rallye précédent | plus bas que l'UTAD |
| Nombre | plusieurs (points 11, 13, 15, 17 chez Pruden) | un |
| Entrée short | sur l'échec ; mieux encore sur le rallye qui teste le point 11 | plus serrée, sous l'UTAD |

### 6.5 Barre de test, no supply et ST wyckoffien

| Critère | Barre de test (VSA) | No supply (VSA) | ST / test wyckoffien |
|---|---|---|---|
| Nature | geste **provoqué** | état **passif** | événement **structurel** (Phases A à C) |
| Lieu | zone de fort volume antérieure | n'importe où, de préférence en tendance haussière | zone de l'action testée (SC, spring) |
| Forme | mèche basse, clôture milieu ou haut | barre baissière, spread étroit | swing de retour, souvent plusieurs barres |
| Volume | faible face à la zone testée (peut être élevé en futures) | inférieur aux deux barres précédentes | inférieur à l'action testée, en baisse d'un test à l'autre |
| Spread | pas d'exigence | étroit | se resserre à l'échelle du swing |
| Confirmation | barre suivante haussière, 2 à 3 barres maximum | barre suivante haussière | réponse puis séquence (SOS) |

### 6.6 Où les sources divergent, et ce que le mémo retient

| Sujet | Positions | Choix du mémo |
|---|---|---|
| Numérotation des springs | SMI, Fraser, Villahermosa : #1 lourd → #3 léger ; Pruden 2006 gradue sans numéros ; aucune inversion trouvée | numérotation SMI partout |
| Acheter le shakeout (#1) | Pruden : premier point d'entrée, mais le test est meilleur ; SMI : très risqué, attendre le test ; Fraser : ne pas l'acheter | entrée sur le test seulement |
| ST sous le low du SC | Wyckoff Analytics : en général au-dessus, dessous = nouveaux plus-bas ou consolidation ; Fraser : réussi au-dessus, au niveau ou en dessous ; Villahermosa : déséquilibre vendeur | qualité moindre, jamais « spring » |
| Volume au ST du BC | Wyckoff Analytics, Pruden : en baisse ; Fraser : volume élevé au retournement | baisse à l'approche, volume au retournement |
| Phase A climactique ? | Wyckoff Analytics, Pruden : pas forcément ; Villahermosa : oui, sous une forme ou une autre | pas obligatoire ; pas de ST sans arrêt |
| BU = LPS ? | Pruden, Wyckoff Analytics : le BU est le mouvement vers un LPS ; Fraser 2015, Villahermosa : synonymes | BU = mouvement ; son low = LPS hors plage |
| Profondeur du BU | stricte (Fraser 2018, Villahermosa) ; tolérante (Fraser 2022, Pruden et son stop sous le spring) | deux stops : serré (creek) ou structurel (spring) |
| Volume du LPSY | Pruden : faible ou fort ; Villahermosa préfère un volume bas | spread étroit + échec |
| FTI | Pruden : la cassure ; Villahermosa : le retest | FTI = la cassure |
| Test à fort volume | Williams : raté, re-test, sauf mauvaises nouvelles, marché haussier, **futures** | « à re-tester », OI coin en arbitre |
| Vocabulaire | *terminal shake-out* et *upthrust* sont dans le cours de Wyckoff ; *spring*, *creek*, *ice*, JAC, BU, UTAD viennent de l'ère SMI/Evans ; les schémas A à E sont postérieurs à 1934 | mécanisme wyckoffien, mots en couches |

## 7. Diagnostic de l'état d'une consolidation

Diagnostiquer une plage, c'est répondre dans l'ordre à une suite de questions : chaque étape est une porte gardée par un test. L'arbre ci-dessous les enchaîne, du contexte HTF jusqu'au back-up.

<!-- FIG:decision_tree -->

### 7.1 Arbre de décision : chaque étape est une porte gardée par un test

| # | Question | Si oui | Si non | Crypto à cette étape |
|---|---|---|---|---|
| 0 | TF, structure et contexte HTF déclarés ? | passer à 1 | déclarer d'abord ; dans un downtrend, redistribution par défaut | — |
| 1 | Un arrêt (SC, ou Phase A non climactique) et un AR qui pose la borne haute ? | Phase A en cours | pas de plage : tendance | AR avec OI coin en baisse |
| 2 | ST moins volumique et moins large que le SC, creux au-dessus du low du SC ? | plage posée, Phase B | nouveaux plus-bas ou consolidation ; P&F depuis le ST | OI coin plat ou en baisse |
| 3 | Volume des creux en baisse, rallyes plus faciles ? | absorption en progrès | Phase B qui s'allonge, ou redistribution | OI qui se dégonfle de test en test |
| 4 | Phase B au moins aussi longue que la Phase A ? | une Phase C devient crédible | spring prématuré probable | — |
| 5 | Un test de Phase C (spring #1, #2, #3 ou LPS C) ? De quel type ? | exigence de test selon le type (3.5 à 3.9) | attendre, ne rien anticiper | profil de liquidations au spring |
| 6 | Test du spring sec, creux plus haut, réponse en 1 à 3 barres ? | *springboard* : cause prête | re-test, ou retour en Phase B | OI coin plat, liquidations quasi nulles |
| 7 | SOS/JAC en expansion, clôture haute au-dessus du creek ? | tentative de sortie : attendre le BU | SOS mineur puis LPS, ou UT ? | OI coin en hausse avec le prix, funding contenu |
| 8 | BU sec qui tient le creek ? | Phase E (markup) | UT/UTAD : scénario redistribution | OI stable, funding qui refroidit |

### 7.2 Grille de maturité : du bruit au springboard

| Critère | Immature | En maturation | Mûr | En sortie |
|---|---|---|---|---|
| Séquence | SC et AR seulement | ST et plusieurs ST in B | test de Phase C réussi | SOS/JAC et BU |
| Volume des creux | volumique, erratique | en baisse | test plus sec que le spring | — |
| vol(dernier test) / vol(SC) [H] | > 1 | entre 1 et 0,5 | < 0,5 | — |
| Oscillations | larges | qui se resserrent | contraction (charnière, apex) | expansion haussière |
| Durée Phase B / Phase A | < 1 | ≈ 1 | ≥ 1 | — |
| Volume rallyes / réactions [H] | < 1 | ≈ 1 | > 1 | > 1 et croissant |
| Réponse aux tests | absente | lente | 1 à 3 barres | immédiate |
| OI coin sur les tests | en hausse (shorts qui s'ouvrent) | plat | plat ou en baisse (débouclage) | en hausse avec le prix |

Les repères doctrinaux sont qualitatifs : le volume des baisses diminue à mesure que l'offre est absorbée, les creux montent, prix et volume se contractent avant le départ, et plus la tendance précédente était forte, plus il faut de tests pour la retourner. Aucune source ne chiffre la baisse de volume ni la durée en barres : les colonnes chiffrées sont des repères [H].

> **À retenir** — La maturité est un **gradient**, pas un événement. Une suite de retours sur la même zone à volume décroissant (par exemple ×3 → ×1,5 → ×0,6, valeurs illustratives [H]) est la meilleure preuve de transfert. TradeGuider dit la même chose à l'échelle de deux barres : un second test moins volumique que le premier pèse davantage.

### 7.3 Accumulation ou redistribution : tenir les deux scénarios jusqu'à la sortie

| Indice | Favorise l'accumulation | Favorise la redistribution |
|---|---|---|
| Contexte HTF | bas de cycle après une baisse prolongée avec climax | plage **dans** un downtrend (défaut du projet) |
| Phase A | SC, AR et ST nets | même allure : une redistribution peut ressembler au début d'une accumulation |
| Volume des baisses | décroissant d'un passage à l'autre | reste lourd et grossit avec l'âge de la plage |
| Test de la borne haute en B | UA à réintégration rapide, ou mSOS | UT suivi d'un SOW volumique qui casse le bas de la plage |
| Creux plus bas en B | sans suivi, re-testé plus sec | volumique, suivi (ST as SOW, mSOW) |
| Rallyes | volume en hausse sur les hausses | volume en hausse sur les baisses |
| Phase C | spring et test sec | UTAD, ou UT sur un sommet plus bas |
| Sortie | JAC et BU sec qui tient | SOW et LPSY, ou JAC qui réintègre (UTAD) |
| OI coin | en baisse sur les tests, en hausse à la sortie | en hausse à la résistance avec funding élevé (demande piégée) |

> **Penser comme le CO** — Tant que le prix n'a pas quitté la plage, on ne peut pas connaître l'intention réelle derrière la cause construite (Villahermosa). Il faut être prêt à tout moment à mettre à jour ses scénarios et ses étiquettes. Dès que le prix fait l'inattendu (un aller-retour, un « test » volumique), on re-questionne le cadre au lieu de plaquer l'étiquette prévue.

### 7.4 Emboîtement fractal : une structure entière sur H1 peut n'être qu'un test sur H4

| Sur H4 (contexte) | Sur H1 (structure locale) | Lecture |
|---|---|---|
| ST in Phase B sur la borne basse | accumulation H1 complète (SC, AR, ST, spring, SOS locaux) | confluence haussière locale ; la Phase B H4 continue |
| UA/UT in B sur la borne haute | distribution H1 complète (BC, UT, SOW locaux) | l'UT H4 s'exécute par une distribution H1 |
| Test du spring H4 | LPS H1 qui tient | confluence maximale : entrée H1, contexte H4 |
| BU H4 | réaccumulation H1 | le BU s'étire en palier |

Règle du projet : on étiquette d'abord à l'échelle fixée par Gauthier ; la TF supérieure donne le biais sans écraser les étiquettes locales.

### 7.5 Les neuf tests d'achat et de vente : deux listes, deux ordres

La plus ancienne liste trouvée est dans le cours de Wyckoff, sur des pages datées de 1937 et signées Wyckoff Associates : elle est donc **posthume**. La version répandue (Wyckoff Analytics, d'après Pruden 2007) **réordonne** les tests d'achat et fusionne PS, SC et ST en un seul test.

**Tests d'achat**

| # | Cours 1937 | Pruden 2007 / Wyckoff Analytics |
|---|---|---|
| 1 | objectif baissier atteint (P&F) | objectif baissier atteint (P&F) |
| 2 | *activity bullish* : volume en hausse sur les rallyes, en baisse sur les réactions | soutien préliminaire, climax de vente, test secondaire |
| 3 | soutien préliminaire | *activity bullish* |
| 4 | plus fort que le marché | tendance baissière cassée |
| 5 | tendance baissière cassée (lignes d'offre percées) | creux plus hauts |
| 6 | supports plus hauts | sommets plus hauts |
| 7 | sommets plus hauts | plus fort que le marché |
| 8 | base en formation (P&F) | base en formation (ligne horizontale) |
| 9 | profit probable estimé supérieur au risque indiqué (*Estimated Probable Profit Exceeds Indicated Risk*) | potentiel au moins 3 fois la perte au stop initial |

**Tests de vente.** La liste de 1937 est le miroir de la liste d'achat : objectif haussier atteint, *activity bearish* (volume en hausse sur les réactions, en baisse sur les rallyes), offre préliminaire, plus faible que le marché, tendance haussière cassée, sommets plus bas, supports plus bas, couronne en formation, profits probables supérieurs au risque indiqué. La version Pruden/Wyckoff Analytics ajoute le climax d'achat à l'offre préliminaire (n°3) et remplace « supports plus bas » par « creux plus bas ».

Comment s'en servir :

- **Un faisceau, pas un signal** : prix, structure, cause P&F et force relative ensemble ; ils définissent la ligne de moindre résistance. Seuls les tests 1 et 9 exigent le P&F.
- **Règle des 3:1** : le profit probable, estimé par l'objectif P&F, doit valoir au moins trois fois le risque d'un stop bien placé.
- **Adaptation crypto** : « plus fort que le marché » = BTC contre la capitalisation totale, ou une altcoin contre BTC ; P&F à case en % ou en ATR.
- **Asymétrie** : dans la liste Pruden/Wyckoff Analytics, l'ordre de vente n'est pas le miroir de l'ordre d'achat, signe probable d'un glissement éditorial.

## 8. Playbook de trading : acheter le test, pas l'événement

Aide à la décision uniquement, jamais d'exécution automatique. Les niveaux sont génériques : en situation réelle, chaque prix cité porte entre parenthèses l'événement ou la borne qui le définit.

### 8.1 Règles communes à tous les montages

- **Ne pas acheter la cassure.** La méthode achète après le back-up qui suit un saut haussier, et vend à découvert après le back-up qui suit un saut baissier (Pruden).
- **Quatre points d'entrée (Fraser)** : spring et test du spring ; LPS (souvent plusieurs) ; BU après la sortie ; cassure du high du BU/SOS.
- **Stops** juste sous le spring, le LPS ou le BU, dans une zone qui a très peu de chances d'être touchée.
- **R:R ≥ 3 avant l'entrée** (test d'achat n°9 et règle du SMI), vérifié sur le premier objectif, le plus conservateur.
- **Objectif P&F** compté depuis le LPS, de droite à gauche, en comptant toujours une phase entière ; projeter depuis le low de la plage et depuis son point médian. Aux objectifs, s'arrêter, regarder, écouter.
- **Case P&F en crypto** : échelle en % (10 % pour BTC sur 2013–2018 chez Rutigliano) ou en ATR (Fraser : renversement de 5 cases, échelle ATR 20) ; à calibrer en H1/H4.
- **Construction** en trois tranches, chacune à un prix plus haut que la précédente ; on ne renforce qu'une position gagnante.
- **Plan de Villahermosa** : stop d'invalidation sous le low du spring (achat) ou au-dessus du high de l'UTAD (vente) ; objectif minimal = hauteur de la plage ; demi-sortie à la première zone de liquidité, stop au point mort à mi-chemin. La structure définit le ratio, jamais l'inverse.

> **Piège** — La configuration de backtest du dépôt (`stop_atr: 1.0`, `rr: 2.0`, entrée sur déclencheur frais) ressemble au seul backtest public trouvé d'un spring seul : 41,26 % de gains, −0,13 R en moyenne (résultat non vérifié). S'il se confirme, il plaide pour déclencher sur le **test** et le **LPS** plutôt que sur l'événement, comme Fraser et Pruden. C'est une hypothèse à tester dans `screener/optimize.py` (walk-forward), pas une conclusion.

### 8.2 Montages par setup

Les deux achats principaux, le test du spring et le BU, se placent ainsi sur la structure. La lecture crypto de chaque montage est celle de la fiche correspondante.

<!-- FIG:playbook_levels -->

**Spring #3 — achat direct**

- Contexte : Phase B mûre ; contexte HTF non baissier, ou accumulation gagnée ; pas d'heure creuse.
- Déclencheur : réintégration de la plage sur volume sec, puis première barre de demande.
- Entrée : clôture de la barre de demande (preuve que la demande répond).
- Stop : sous le low du spring (poche de stops consommée ; y revenir en clôture = offre réelle).
- Objectif : high de l'AR / creek (borne haute de la plage), puis décompte P&F depuis le LPS.

**Test du spring — #2, ou #1 après test**

- Contexte : spring #2 ou #1 identifié ; Phase B mûre.
- Déclencheur : test à volume inférieur au spring, creux plus haut, puis barre de demande dans les 1 à 3 barres.
- Entrée : ordre stop au-dessus du high de la barre de test (la confirmation déclenche), ou clôture de la barre de demande.
- Stop : sous le low du spring (point de danger de Pruden).
- Objectif : creek (borne haute de la plage), puis décompte P&F ; R:R ≥ 3 sur le premier objectif.
- Invalidation : creux plus bas **et** volume plus fort (grade D), ou pas de réponse en 3 barres.

**LPS — de Phase C ou de Phase D, dans la plage**

- Contexte : test de Phase C passé (ou LPS C), SOS en amont.
- Déclencheur : repli sec à creux plus haut, puis barre de demande.
- Entrée : premières barres de demande au retournement.
- Stop : sous le low du LPS (dernier creux défendu par la demande), ou sous le low précédent.
- Objectif : creek en premier relais (borne haute de la plage), puis décompte P&F compté depuis ce LPS.

**BU / BUEC — le setup « sûr » de Pruden**

- Contexte : JAC avec expansion et clôture haute au-dessus du creek.
- Déclencheur : BU sec et étroit sur le creek, puis barre de demande.
- Entrée : dans la force des barres de demande au départ du BU.
- Stop serré : sous le low du BU et sous le creek (une réintégration invalide le JAC). Stop structurel : sous le low du spring (invalidation du schéma, choix de Pruden).
- Objectif : décompte P&F depuis le LPS.

**JAC / SOS majeur — pas d'entrée sur la barre**

- Contexte : séquence C → D accomplie.
- Déclencheur : aucun sur la cassure ; attendre le BU, ou la cassure du high du BU/SOS.
- Entrée : au-dessus du high du BU/SOS, **après** le BU (la sortie a été testée).
- Stop : sous le low du BU (le test qui a validé le saut).
- Objectif : décompte P&F.

**UTAD — short, miroir du spring**

- Contexte : Phases A et B accomplies ; contexte HTF baissier ou tendance haussière mûre.
- Déclencheur : réintégration après la percée ; mieux, test de l'UTAD à sommet plus bas et sec.
- Entrée : sous le low de la barre de rejet.
- Stop : au-dessus du high de l'UTAD (extrême du piège).
- Objectif : low de l'AR (borne basse de la plage), puis décompte P&F baissier.

**LPSY / retour sous la glace — short, miroir du BU**

- Contexte : SOW, ou FTI à travers la glace.
- Déclencheur : rallye à spread étroit qui échoue sous la glace ou sous une résistance interne.
- Entrée : sur la barre de rejet ; encore mieux sur le rallye qui teste le point 11 de Pruden.
- Stop : au-dessus du high du LPSY et de la glace cassée (support devenu résistance).
- Objectif : décompte P&F baissier, puis stop suiveur.

## 9. Seuils du screener et écarts doctrine ↔ code

Constat seulement : le code n'est pas modifié ici.

### 9.1 Les sept seuils sont des heuristiques ; aucune source primaire ne les chiffre

| Seuil (`config.yaml`) | Valeur [H] | Où le code l'applique | Ancrage dans les sources |
|---|---|---|---|
| `climax_vol` | ×2.0 | SC/BC (`events.py` l.97, l.104) ; climax de `window.py` à 0,75 × 2,0 = ×1,5 (l.215) | qualitatif (volume « ultra élevé ») ; ProRealCode : SC > ×2,4, BC > ×3,0 |
| `sos_vol` | ×1.3 | SOS/SOW (`events.py` l.111, l.117 ; `window.py` l.260) | qualitatif ; scripts publics entre ×1,2 et ×2,0 |
| `wide_spread_atr` | 1.3 ATR | SC/BC/SOS/SOW, et aussi **plafond** de spread du ST (`events.py` l.125, l.128 ; `window.py` l.273) | qualitatif |
| `narrow_spread_atr` | 0.7 ATR | **aucun détecteur** ; affiché dans le mémo théorie (`theory_table.py` l.180) et accepté comme clé de grille par `optimize.py` (l.34), sans effet sur la détection | qualitatif |
| `test_vol` | ×0.85 | ST (`events.py` l.125) ; ST à ×0,98 (`window.py` l.273) ; LPS à ×1,1 (l.313) ; LPS/LPSY (`events.py` l.138, l.144) | la doctrine compare à l'action testée, pas à la moyenne |
| `pen_atr` | 0.1 ATR | SPRING/UTAD (`events.py` l.80, l.89 ; `window.py` l.291) | aucune profondeur chiffrée dans les sources |
| `reclaim_clv` | 0.5 | SC/BC (`events.py` l.98, l.105) ; **pas** le spring de `events.py` ; 0,5 codé en dur dans `window.py` (l.287) | clôture au milieu ou en haut (Williams) ; un spring peut clôturer sous la moitié de sa barre, pas au plus bas |

Définitions : CLV = (C − L) / (H − L) (`features.py` l.43). `vol_ratio` = volume / moyenne mobile 20 barres **qui inclut la barre courante** (`features.py` l.45–46) : une barre à 2 fois la moyenne des 19 précédentes s'affiche à environ ×1,9. Les seuils `clv ≥ 0.6` (SOS) et `clv ≤ 0.4` (SOW) cités dans les fiches sont aussi des seuils du code [H]. Le seuil « test raté vers ×1.5 » est une convention du projet [H].

### 9.2 Écarts entre la doctrine et le code actuel

| # | Code actuel | Doctrine | Piste (non appliquée) |
|---|---|---|---|
| 1 | Le ST accepte un spread jusqu'à 1,3 ATR (`events.py` l.125, l.128 ; `window.py` l.273) et le texte théorique l'appelle « étroit » (`window.py` l.72–74 ; `theory_table.py` l.83) | spread qui se resserre | appliquer `narrow_spread_atr` aux tests de swing ; harmoniser le texte |
| 2 | Volume du ST jugé contre la MA20 seule (`events.py` l.122–130 ; `window.py` l.265–277) | vol(ST) < vol(SC), vol(test) < vol(spring) | afficher vol_test / vol_action et l'exiger < 1 |
| 3 | Le docstring annonce AR et TEST (`events.py` l.9–11), mais aucun détecteur AR ni TEST n'existe | — | détecteur « test du spring », avec test synthétique |
| 4 | Type de spring non classé ; bonus de volume (`vol_bonus` 0.6) si le volume dépasse le climax ; `window.py` retient la pénétration la plus profonde (`events.py` l.79–86 ; `window.py` l.279–294) | le type fixe l'exigence de test | classer #1/#2/#3 par le volume ; #1 et #2 → « test requis » |
| 5 | Spring = pénétration + clôture au-dessus du support, sans condition de CLV (`events.py` l.80) | retour dans la plage, pas de clôture au plus bas | appliquer `reclaim_clv`, lu depuis `Thresholds` |
| 6 | ST « près » du support (15 % de la hauteur) ; `window.py` tolère un sous-percement de 2 % (`events.py` l.123–125 ; `window.py` l.272) | grades A, B, C, D | noter le grade du test |
| 7 | Toute barre sèche près du support dans les 5 dernières barres = « ST » (`events.py` l.122–130) | cause en amont nécessaire | exiger un climax, un spring ou un SOS en amont |
| 8 | Aucune confirmation par la réponse (`events.py`, `window.py`) | réponse en 1 à 3 barres, sinon faiblesse | statut « possible » puis « validé » après la réponse |
| 9 | SOS = clôture au-dessus du high de plage + volume + spread, étiqueté ferme sur la barre (`events.py` l.110–114) | on n'achète pas une cassure ; SOS après tenue et BU | étiquette « SOS ? / UTAD ? » jusqu'à la tenue et au BU |
| 10 | Premier SOS = première barre volumique et large, sans condition de franchissement (`window.py` l.250–263) | SOS mineur ≠ JAC | distinguer mSOS (dans la plage) et JAC (au-dessus du creek) |
| 11 | « LPS » = dernière barre sèche au-dessus de la résistance cassée (`events.py` l.134–140) | c'est un BU/BUEC | renommer ou dédoubler (BU contre LPS) |
| 12 | Un seul LPS : réaction la plus profonde ≥ 1 ATR après le SOS, tenue au-dessus du low du climax, volume ≤ ×1,1, sans condition de spread ; texte « back-up à la creek » (`window.py` l.299–316, l.50–51) | LPS multiples ; BU strict ou tolérant | séries de LPS, condition de spread, deux niveaux de profondeur |
| 13 | Un seul ST retenu, le plus sec (`window.py` l.265–277) | gradient de volume sur plusieurs ST | stocker la suite des tests et la pente du volume |
| 14 | Toute percée du haut de plage avec retour = « UTAD », même en Phase B (`events.py` l.88–94) | UTAD = fin de plage ; avant, c'est un UT | condition de position dans la séquence |
| 15 | Le LPSY exige un volume sec ≤ ×0,85 (`events.py` l.141–146) | volume faible ou fort | critère : spread étroit + échec |
| 16 | Climax à ×1,5 sans condition de spread (`window.py` l.209–217) | config : ×2,0 et 1,3 ATR | aligner, ou documenter le relâchement |
| 17 | MA20 glissante en H1 sur un marché 24/7 (`features.py` l.45) | Williams critique le lissage | normaliser par heure de la journée ou jour de la semaine |
| 18 | Backtest à stop 1 ATR et objectif 2R (`config.yaml` l.16–17) | R:R ≥ 3 | tester R:R 3 et une entrée sur test ou LPS |

> **À retenir** — Les détecteurs lisent bien les **actions** (climax, percées, signes), mais pas encore les **tests** au sens de la doctrine : relatifs à l'action testée, gradués, conditionnés par une cause et validés par une réponse. C'est le principal chantier, et chaque nouveau détecteur doit venir avec un test synthétique dans `tests/`.

## 10. Errata du premier mémo (`docs/memo_tests_CO.md`) — les corrections principales

| # | Le premier mémo disait | Correction |
|---|---|---|
| 1 | Les cinq conditions d'un test sont toutes nécessaires | Trois niveaux : nécessaire (cause, lieu, volume < action testée), qualité (spread, creux, clôture), validation (réponse). Un léger sous-percement n'invalide pas |
| 2 | `vol_ratio ≤ 0.85` prouve le volume sec | La doctrine compare le volume à celui de l'action testée ; la MA20 n'est qu'un filtre [H] |
| 3 | Spread étroit ≤ 0,7 ATR nécessaire | Critère de qualité à l'échelle du swing ; aucune exigence pour la barre de test VSA ; le code n'applique pas 0,7 |
| 4 | Un test avec OI qui monte n'est pas un test | OI en hausse = test **non validé**, ambigu ; à départager par ratio L/S, funding, liquidations |
| 5 | Barre de test idéale : baisse, spread étroit, volume < 2 barres précédentes | Ce sont les critères du **no supply** ; pour le test, nouveau plus-bas et barre baissière ne sont que des bonus |
| 6 | Test sec sans réponse = neutre | Faiblesse (*negative action*, Williams) |
| 7 | La numérotation des springs varie selon les sources | Même ordre chez le SMI, Fraser et Villahermosa : #1 lourd → #3 léger ; Pruden 2006 sans numéros |
| 8 | Le BUEC est une forme de LPS selon Evans | Aucun texte d'Evans retrouvé ; l'équivalence vient de Fraser (2015) et Villahermosa ; pour Pruden, le BU est le mouvement vers un LPS |
| 9 | Typiquement un seul BUEC | Souvent un, parfois deux (Fraser, Pruden) ; le BU peut devenir une nouvelle plage |
| 10 | Clôture dans la plage après le BUEC = upthrust | Vrai pour l'école stricte ; l'école tolérante place l'invalidation sous le spring |
| 11 | Le terminal shakeout est une allégorie d'Evans | C'est un terme de Wyckoff ; le spring en est le raffinement SMI/Evans |
| 12 | Le LPSY cale sous la glace à volume sec | Volume faible ou fort (Pruden) |
| 13 | Les neuf tests d'achat sont de Wyckoff, dans l'ordre courant | Plus ancienne liste : cours de 1937, posthume, dans un autre ordre ; l'ordre courant est celui de Pruden 2007 |
| 14 | Le test est le seul instrument de mesure du CO | Faux : enquête sur le carnet, sondages de courtiers, nouvelles servaient aussi de tests |
| 15 | Test sec validé > SOS volumique ; test d'un spring #2 en 3 à 10 barres | Non sourcés : le premier est une heuristique du projet [H] ; pour le second, Fraser montre un test dès le lendemain ou dans les deux jours |

Ces corrections concernent aussi la règle « Tests du Composite Operator » de `CLAUDE.md`, aujourd'hui alignée sur ce mémo (faiblesse au lieu de neutre, OI en hausse = non validé, spread = critère de qualité).

## 11. Conclusion : le test est une mesure relative, conditionnelle et validée par la suite

Le premier mémo traitait le test comme une barre sèche près d'un support. Les sources en font une mesure **relative** (volume contre l'action testée), **conditionnelle** (pas de test sans cause), **graduée** (A à D, un sous-percement toléré) et **validée par la réponse** (sans hausse en 1 à 3 barres, c'est de la faiblesse). Le type de spring fixe l'exigence de test. L'économie des métaordres explique pourquoi un opérateur rationnel teste, mais la recherche ne mesure que des avantages modestes : un test sert d'abord à **placer le risque** là où l'offre a déjà été consommée, ensuite seulement à prédire.

Pour les perps BTC, l'apport le plus solide est la nuance de Williams sur les marchés à terme : un test volumique peut y être de la force, et l'OI en coin le départage au lieu de le condamner. Pour le screener, l'écart principal n'est pas un seuil mal réglé : les détecteurs lisent les actions, pas encore les tests (priorités en §9.2, chacune à valider hors échantillon contre des niveaux arbitraires). Le mémo `memo_theorie.html` reste la référence rapide des seuils, événement par événement.

## 12. Glossaire FR/EN

| Français | English | Définition courte |
|---|---|---|
| Absorption | Absorption | achat passif de l'offre sans hausse du prix (effort sans résultat) |
| Rebond automatique | Automatic Rally (AR) | rebond réflexe après le climax ; fixe l'autre borne de la plage |
| Fond | Background | ce que disent les barres précédentes ; conditionne tout signal VSA |
| Back-up | Back-Up (BU), Back-Up to the Edge of the Creek (BUEC) | repli sec après le JAC sur l'ancienne résistance ; son low est un LPS |
| Climax acheteur / vendeur | Buying / Selling Climax (BC / SC) | extrême de tendance sur volume et spread extrêmes ; fixe le plafond / le plancher |
| CLV | Close Location Value | (C − L) / (H − L), position de la clôture dans la barre |
| Composite Operator (CO) | Composite Man / Operator | fiction d'un opérateur unique derrière le marché |
| Ruisseau | Creek | résistance sinueuse reliant les sommets de la plage |
| Chute à travers la glace | Fall Through the Ice (FTI) | cassure du support (ici) ; le retest chez Villahermosa |
| Glace | Ice | support sinueux sous les creux ; devient résistance après la cassure |
| Saut du ruisseau | Jump Across the Creek (JAC) | SOS majeur qui franchit le creek sur expansion de volume |
| Dernier point d'appui | Last Point of Support (LPS) | creux d'une réaction sèche (Phase C, Phase D, ou low du BU) |
| Dernier point d'offre | Last Point of Supply (LPSY) | rallye faible à spread étroit après un SOW |
| Action négative | Negative action | test sans réponse en 2 à 3 barres = faiblesse |
| Pas d'offre / pas de demande | No supply / No demand | barre baissière / haussière à volume inférieur aux deux précédentes |
| Test secondaire | Secondary Test (ST) | retour vers la zone du climax (sec en Phase A ; en Phase B, c'est la pente du volume qui compte) |
| Secousse | Shakeout | poussée baissière brutale ; *terminal* en fin de préparation, *ordinaire* en tendance haussière |
| Signe de force / faiblesse | Sign of Strength / Weakness (SOS / SOW) | poussée large et volumique dans le sens de la sortie |
| Ressort #1 / #2 / #3 | Spring #1 / #2 / #3 | fausse cassure du support, graduée par l'offre libérée (#1 lourd → #3 léger) |
| Tremplin | Springboard | fin de préparation, au bas de la plage ; résultat des tests |
| Barre de test | Test (test bar) | marquage à la baisse dans une zone d'offre, qui reprend sur faible volume |
| Upthrust / UA | Upthrust (UT) / Upthrust Action (UA) | percée du haut de plage qui ne tient pas (UA en accumulation chez Villahermosa) |
| Upthrust après distribution | Upthrust After Distribution (UTAD) | test final de la demande au-dessus de la plage, en fin de distribution |

## 13. Points non vérifiés

- Dates de Robert G. Evans (1904–1976) : une seule source ; qui dirigeait l'enseignement entre 1934 et 1951 reste discuté (Stanlaws ou Evans).
- Pruden : année de naissance (1935 ou 1936) ; contenu du livre de 2007 (dont une éventuelle numérotation des springs) non consulté.
- Glossaire du SMI : citations obtenues par un outil de récupération, en partie corroborées par des reproductions tierces.
- Page « Spring » de Villahermosa (protégée) : spring prématuré, UA qui favorise le spring, ST as SOW qui favorise l'upthrust, marge sous le low du spring ; et sa position de 2026 sur le volume « secondaire ».
- Portée exacte de la phrase TradeGuider sur le spread étroit « à moindre impact » (PDF en ligne révisé en 2021).
- Backtest du spring seul (41,26 %, −0,13 R) : page inaccessible.
- Sous-réaction du *mark price* le 10 octobre 2025 (article vu en extrait) ; impact permanent des ordres passifs (résumé seulement).
- Demi-vies d'inventaire des teneurs de marché en perps : probablement plus courtes qu'au NYSE, non mesuré.
- Épisode BTC 64 800 : repris de `CLAUDE.md`, données non recontrôlées.
- Weis : extrait de l'éditeur seulement ; Coulling : copie non officielle.

## 14. Bibliographie commentée

**Sources primaires**

- R. D. Wyckoff, *Studies in Tape Reading* (« Rollo Tape »), 1910 — tests comme points critiques ; une opération en trois parties. [archive.org](https://archive.org/details/studiesintaperea00wyckrich)
- R. D. Wyckoff, *How I Trade and Invest in Stocks and Bonds*, 1922 — le projet de rétro-ingénierie des gros opérateurs. [archive.org](https://archive.org/details/cu31924031269552)
- *The Richard D. Wyckoff Method of Trading and Investing in Stocks*, cours ©1931–33, édition 1937 — Composite Man, sondes, *secondary reaction*, springboard, terminal shake-out, upthrust, neuf tests (pages de 1937). [archive.org](https://archive.org/details/WyckoffMethodOfTapeReading)
- Wyckoff, *Tape Reading and Active Trading*, ©1932 — tests et réponses ; « il n'y a pas de Composite Operator ». [archive.org](https://archive.org/details/TheRichardD.WyckoffMethodOfTradingInStocks)
- E. Lefèvre, *Reminiscences of a Stock Operator*, 1923 — coût des sondes, Keene. [Gutenberg](https://www.gutenberg.org/ebooks/60979)

**Tradition SMI / Evans, Pruden, Wyckoff Analytics, Fraser, Villahermosa, Weis**

- Wyckoff SMI, glossaire et blog de J. O'Brien — types de spring, exigence et qualité des tests, ice, UTAD. [glossaire](https://wyckoffsmi.com/wyckoff-glossery/) · [Test of Springs](https://wyckoffsmi.com/test-of-springs/) · [histoire](https://wyckoffsmi.com/history-of-wyckoff-stock-market-institute/)
- H. Pruden & M. von Lichtenstein, « Wyckoff Schematics », *Market Technician* n°55, 2006 — jump et back-up, creek et ice, points d'entrée, cas Nokia ; meilleure source de seconde main sur Evans. [PDF](https://www.wyckoffanalytics.com/wp-content/uploads/2019/09/WyckoffSchematics-VisualTemplatesForMarketTimingDecisions.pdf)
- H. Pruden, *The Three Skills of Top Trading*, Wiley, 2007 — neuf tests (connus via StockCharts) ; non consulté.
- R. Bogomazov & M. Lipsett, « The Wyckoff Method: A Tutorial » (schémas édités par Pruden), StockCharts / Wyckoff Analytics — définitions de référence, neuf tests, décompte P&F. [ChartSchool](https://chartschool.stockcharts.com/table-of-contents/market-analysis/wyckoff-analysis-articles/the-wyckoff-method-a-tutorial)
- A. Rutigliano, « Trading the Crypto Market with the Wyckoff Method », 2020 — UA, P&F en % sur BTC. [PDF](https://www.wyckoffanalytics.com/index.php?pda_v3_pf=%2F_pda%2F2020%2F07%2FTrading-The-Crypto-Market-with-the-Wyckoff-Method-1.pdf)
- B. Fraser, *Wyckoff Power Charting* (StockCharts, 2015–2022) — action et test, types de spring et entrées, LPS de Phase C, JAC/BUEC, distribution. [Action – Test](https://articles.stockcharts.com/article/articles-wyckoff-2016-09-action--test)
- R. Villahermosa, « Profundizando en los Springs », *TheTicker* n°1, 2018, et tradingwyckoff.com — typologie des springs, UA, ST as SOW, LPS, FTI. [PDF](https://tradingwyckoff.com/assets/TICKER1.pdf)
- D. Weis, *Trades About to Happen*, 2013 — provenance des schémas et du vocabulaire. [extrait](https://content.e-bookshelf.de/media/reading/L-802008-2fe9f872b5.pdf)

**VSA**

- T. Williams, *Master the Markets*, 4ᵉ éd., 2009 — test, re-test, *negative action*, nuance futures, no supply et no demand. [PDF](https://www.tradeguider.com/mtm_251058.pdf)
- G. Holmes, *VSA System Explained*, TradeGuider — définitions des indicateurs (Basic Test, No Supply, No Demand). [PDF](https://www.tradeguider.com/customer/pdf/VSA_System_explained.pdf)
- A. Coulling, *A Complete Guide to Volume Price Analysis*, ch. 5 — test de la demande, test raté. [copie](https://online.flipbuilder.com/frkvo/xdvc/files/basic-html/page45.html)

**Microstructure et marchés**

- Tóth et al., *Phys. Rev. X*, 2011 ; Donier & Bonart (Bitcoin) ; Farmer et al. — loi en racine carrée, impact permanent. [arXiv](https://arxiv.org/pdf/1105.1694)
- Kyle 1985 ; Kaniel & Liu 2006 ; Cont, Kukanov & Stoikov ; Avellaneda & Stoikov 2008 ; Hendershott & Menkveld 2014 ; Campbell, Grossman & Wang 1993 — camouflage, ordres limites, déséquilibre d'ordres, inventaire du teneur de marché.
- C. Osler, 2000, 2003, 2005 — groupement des stops et cascades (marché des changes). [SR 150](https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr150.pdf)
- Garzarelli et al. 2014 ; Kavajecz & Odders-White 2004 ; Sullivan, Timmermann & White 1999 ; Jiang, Mahoney & Mei — ce que la recherche valide des niveaux, et les pools de 1929.

**Crypto, données, régulation**

- Binance API et Coinalyze API — définitions des données (coin contre USD, comptes contre taille, planchers de liquidations). [Coinalyze](https://api.coinalyze.net/v1/doc/)
- BIS WP 1087 « Crypto carry » ; Garcia Seuma 2026 (prépublication) ; Cong et al. ; Urquhart 2017 — carry, cascades, *wash trading*, chiffres ronds. [BIS](https://www.bis.org/publ/work1087.htm)
- Textes américains (15 U.S.C. §78i, 7 U.S.C. §6c), CFTC, FCA, MiCA art. 91, DOJ — ce qui est interdit aujourd'hui.
- ProRealCode et autres implémentations publiques — fourchettes de seuils, aucune doctrinale.
