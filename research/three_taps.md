# Le Three Taps, mesuré comme un trade

Code : `screener/htf/taps_study.py` (tests : `tests/test_htf_taps_study.py`).

## La règle, dans ses mots

Relevé `research/crypnuevo_tweets.md`, 07/06 à 04/11/2026 :

1. Trois touches d'un extrême de range — « low forms, low swept (deviation), low retest » —,
   la deuxième ou la troisième pouvant être une **déviation** qui chasse les stops (14/06).
2. Après la troisième, retour **au moins au mid-range** (07/06, 04/10).
3. **Timing** : la troisième doit venir assez tard après la deuxième, sinon elle n'attire pas
   assez de liquidité et la cassure devient plus probable (21/06) ; trade refusé pour cette
   raison le 25/06, faute de « S/R flip ».
4. L'invalidation est l'**acceptance** sous le niveau, pas une mèche (28/06).

## Traduction en trade

À chaque touche *k* d'un plancher (plafond par miroir des prix, symétrie garantie) : entrée,
stop, cible au mid-range du range qui précède et contient les touches. Paramètres fixés a
priori, jamais optimisés.

- **Protocoles d'entrée** : `contact` (premier contact, stop sous les touches précédentes —
  le trader naïf que la déviation chasse) et `reprise` (déviation sous le niveau, puis
  clôture de retour au-dessus — sa méthode).
- **Stops** : `mèche` (sortie dès qu'une mèche touche le stop, perte de 1 R) et `acceptance`
  (sa méthode : deux clôtures consécutives sous le stop, sortie au prix de la seconde — la
  perte peut dépasser 1 R).
- **Témoin** : même géométrie en ATR et même stop, 60 bougies plus tôt.
- **Jeux** : apprentissage BTC/ETH 2020–2024, test BTC/ETH 2025–2026, vierge SOL/XRP ; 1h, 4h
  et 1D ; 17 498 trades candidats par type de stop.

## Résultats

**Espérance en R, avec intervalle de confiance à 95 %** (extrait ; touches 2 et 3) :

| Stop | Protocole | Touche | Apprentissage | Test | Vierge | Témoin (vierge) |
|---|---|---|---|---|---|---|
| mèche | contact | 2 | −0,12 [−0,23 ; −0,02] | −0,03 | −0,05 | −0,28 |
| mèche | contact | 3 | −0,04 [−0,17 ; +0,08] | −0,10 | −0,09 | −0,31 |
| mèche | reprise | 2 | +0,01 [−0,09 ; +0,12] | −0,08 | −0,05 | −0,36 |
| mèche | reprise | 3 | −0,00 [−0,13 ; +0,12] | −0,12 | **+0,03** [−0,10 ; +0,16] | −0,27 |
| acceptance | contact | 3 | −0,19 | −0,05 | −0,21 | −0,65 |
| acceptance | reprise | 3 | −0,10 | −0,15 | −0,13 | −0,52 |

**Timing de la 3e touche — écart d'espérance au témoin, stop en acceptance :**

| Protocole | 3e touche | Apprentissage | Test | Vierge |
|---|---|---|---|---|
| contact | à temps | **+0,74** | **+0,68** | **+0,59** |
| contact | trop rapide | +0,43 | +0,56 | +0,11 |
| reprise | à temps | +0,57 | +0,30 | +0,38 |
| reprise | trop rapide | +0,57 | +1,17 | +0,40 |

## Verdict

1. **Les extrêmes de range sont un lieu d'avantage relatif** : toutes les configurations
   battent leur témoin, sur les trois jeux. C'est cohérent avec la déviation de range
   (`research/structure_rules.md`).
2. **La troisième touche n'a rien de particulier** : elle ne fait pas mieux que la
   deuxième, ni au contact ni sur reprise, quel que soit le stop. C'est la touche d'un
   extrême qui compte, pas son rang.
3. **Le trade type n'est pas rentable en absolu.** Avec un stop sous la touche et une cible
   au mid-range, aucune configuration n'a d'espérance positive dont l'intervalle exclut
   zéro. Le témoin de même géométrie perd 0,3 à 1 R : la géométrie elle-même est
   défavorable, et l'avantage du lieu ne suffit pas à la compenser.
4. **Son stop en acceptance** relève la réussite (0,38–0,55 contre 0,24–0,45) mais alourdit
   les pertes ; l'espérance absolue baisse.
5. **Son timing est confirmé pour une entrée au contact** (troisième touche à temps nettement
   meilleure sur les trois jeux), **pas pour une entrée sur reprise**, qui filtre déjà le
   risque de cassure.
6. **Entrer sur reprise** améliore un peu le résultat et évite 11 à 14 % de déviations
   jamais reprises.

## Ce que le skill en retient

- Un extrême de range est une **zone** où un rebond est plus probable qu'ailleurs. Il entre
  dans le biais comme zone cible ou zone de réaction, pas comme signal d'entrée.
- Le décompte des touches ne s'affiche pas comme un signal : « troisième touche » n'apporte
  aucune information mesurable.
- Aucun setup « Three Taps » n'est présenté comme à espérance positive.
- Si une entrée est discutée à un extrême : sur reprise après déviation, et au contact
  seulement si la troisième touche n'est pas trop rapide.

## Limites

- Géométrie fixe (cible au mid-range, stop sous la touche) : ses trades réels utilisent des
  entrées échelonnées, plusieurs cibles et un contexte (liquidations, déviation HTF) que ce
  test n'inclut pas.
- Une combinaison avec la règle des mèches de liquidation (la touche est-elle une mèche de
  liquidation ?) est une piste, à tester sur un jeu vierge pour ne pas sur-ajuster.
- Quatre cryptos corrélées ; pas de frais ni de glissement, qui dégraderaient encore
  l'espérance.
