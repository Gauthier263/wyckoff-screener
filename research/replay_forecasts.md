# Rejeu du moteur de biais sur les prévisions datées de CrypNuevo

Rejouer : `python -m screener.htf.forecasts` · Code : `screener/htf/bias.py`,
`screener/htf/forecasts.py`.

## Protocole

- **33 prévisions directionnelles** BTC de janvier à novembre 2026, transcrites depuis
  `research/crypnuevo_tweets.md` : direction, cible, invalidation quand il la donne, et les
  bornes de range qu'il trace ce jour-là. Les lectures neutres sont écartées.
- À chaque date, le moteur est **figé** : seules les bougies clôturées avant l'heure du tweet,
  et les liquidations des journées closes, entrent dans le calcul.
- Deux versions : avec **ses bornes** (on teste la logique de décision) et avec les bornes
  **automatiques** (on teste aussi la détection).
- **Juge commun** : le sens du premier mouvement de 5 % du prix après la prévision. Il note
  sa direction et celle de l'outil de la même façon, indépendamment de leurs cibles.

## Le cas du 22/11 à 22h CET

Avec ses bornes (60 000 / 81 341), le moteur sort : **déviation sous le plancher jusqu'à
55 130, reprise ; biais haussier ; déclencheur : acceptance au-dessus de 60 600 (acquise en
4h) ; cibles 70 650 puis 81 300 ; invalidation : acceptance sous 55 130 ; alerte « ne pas
vendre la cassure »**. C'est sa lecture, et celle qui aurait évité le short. Le prix a fait
64 603 le lendemain.

## Résultat

| Qui | Bonne direction | IC 95 % |
|---|---|---|
| CrypNuevo, toutes prévisions | 18 / 33 = **55 %** | 38–70 % |
| Outil (ses bornes), quand il se prononce | 8 / 12 = **67 %** | 39–86 % |
| CrypNuevo, sur ces mêmes 12 dates | 7 / 12 = 58 % | 32–81 % |
| CrypNuevo, quand l'outil reste neutre | 11 / 21 = **52 %** | 32–72 % |
| Outil (bornes automatiques) | 5 / 9 = 56 % | 27–81 % |

Sa propre cible est atteinte avant son invalidation dans 16 cas sur 29 résolus (55 %).

## Lecture

1. **L'outil se prononce rarement** : 12 fois sur 33. Il reste neutre au milieu du range,
   faute d'avantage mesuré à cet endroit.
2. **Quand il reste neutre, les prévisions de CrypNuevo valent pile ou face** (52 %).
   C'est l'information la plus utile du rejeu : les situations où l'outil n'a pas d'avis
   sont celles où personne n'a d'avantage.
3. **Quand il se prononce, il a raison deux fois sur trois.** Mais douze cas ne permettent
   pas de conclure : l'intervalle va de 39 à 86 %. C'est une tendance, pas une preuve.
4. **Les bornes automatiques dégradent le résultat** (56 % sur 9). La détection des bornes
   reste le maillon faible ; les bornes tracées par l'analyste doivent primer.

## Les quatre erreurs de l'outil, et ce qu'elles disent

| Date | Outil | Ce qui s'est passé | Lecture |
|---|---|---|---|
| 21/06 | haussier (déviation 1D reprise, prix en bas du sous-range) | nouvelle jambe sous 60k avant la montée vers le mid en août | juste à terme, faux sur le premier mouvement de 5 % |
| 13/09 | baissier (prix en haut du range) | poussée à 81,9k | un extrême de range est une zone de réaction, pas un signal |
| 27/09 | haussier (cassure du plafond acceptée) | repli | l'acceptance valide une cassure, elle ne dit pas la direction suivante (mesuré) |
| 08/11 | haussier (prix au plancher du sous-range 75,8k) | cassure vers 73k | même cause qu'au 13/09 |

Trois des quatre erreurs viennent du poids donné aux **extrêmes de range**, que l'étude
Three Taps avait déjà qualifiés de zone de réaction plutôt que de signal. Réduire ce poids
serait tentant ; sur douze cas, ce serait du sur-ajustement. C'est noté, pas appliqué.

## Deux défauts du moteur trouvés par le rejeu, corrigés

- **Épisode le plus récent** : un franchissement du plafond fin octobre masquait la sortie
  sous le plancher de la semaine du 22/11.
- **Déviation accomplie** : une déviation dont la cible (le milieu) a déjà été atteinte ne
  compte plus. Au 15/11, la sortie au-dessus du plafond de fin octobre restait « active »
  alors que le prix avait traversé le milieu de 82k à 62k.

## Limites

- 33 prévisions, 12 prises de position de l'outil : aucun résultat de ce rejeu n'est
  statistiquement établi. Il montre un comportement, il ne prouve pas une performance.
- Le juge du premier mouvement de 5 % ne suit pas ses horizons (parfois deux mois) : il
  favorise les lectures de court terme.
- Les bornes sont les siennes : le rejeu « ses bornes » est optimiste sur la partie
  détection. En usage réel, c'est à l'analyste de tracer ses bornes.
