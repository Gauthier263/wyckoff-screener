# Les règles de structure, mesurées — et quatre corrections de méthode

Chaque règle reprise de CrypNuevo est une affirmation statistique déguisée. Mesurée avec
`python -m screener.htf.rules_study`, sur BTC 4h (2020–2026, coupé en deux sous-périodes)
et sur **ETH 4h** (2020–2026, 13 140 bougies) comme jeu de contrôle indépendant.

## Les quatre corrections qui ont changé les résultats

La première version de cette étude donnait des chiffres flatteurs et faux. Ce qui les a
corrigés, dans l'ordre d'importance :

1. **Observations indépendantes.** J'échantillonnais tous les 6 barres avec un horizon de
   60 : deux observations voisines partageaient 54 barres de futur sur 60. Le « n = 331 »
   valait une trentaine d'observations réelles. Le pas vaut désormais l'horizon.
2. **Groupe témoin pour les mèches.** Dire « 88 % des mèches se remplissent » ne prouve
   rien tant qu'on ne sait pas à quelle fréquence un niveau *quelconque*, à la même
   distance, est touché dans le même délai. Le témoin est un niveau fictif placé à la même
   distance du prix, du côté opposé.
3. **Biais de construction sur l'acceptance.** « Après une mèche seule, le prix repasse le
   niveau dans 100 % des cas » était un artefact : une mèche seule se définit par
   l'absence de clôture au-delà, donc le prix est déjà en deçà au moment du test et
   « revient » dès la première barre. Les deux états sont maintenant comparés sur la même
   question, posée symétriquement : où est le prix à la fin de l'horizon ?
4. **Intervalles de confiance (Wilson) partout.** « 1,00 » sur deux cas s'affiche
   `1.00 [0.34-1.00]`, ce qui le disqualifie à la lecture.

Un bug a aussi été corrigé au passage : le test « le milieu est-il atteint » mêlait `and`,
`or` et un ternaire `if/else` dans une seule expression. Il donnait le bon résultat par
accident de précédence, mais aurait cassé à la première modification.

## 1. Remplissage des mèches — pas d'avantage mesurable

« Long wicks tend to fill sooner rather than later, at least the 50 % level. » C'est sa
stratégie préférée, citée dans 48 des 158 entrées du relevé.

**ETH 4h, 6 ans — le plus gros échantillon disponible :**

| Mèche | Taille | n | Remplie 50 % | Témoin 50 % |
|---|---|---|---|---|
| basse | 1–1,5 ATR | **224** | 0,88 [0,83–0,92] | 0,86 [0,81–0,90] |
| haute | 1–1,5 ATR | **122** | 0,93 [0,88–0,97] | 0,89 [0,82–0,93] |
| basse | 1,5–2 ATR | 33 | 0,88 [0,73–0,95] | 0,76 [0,59–0,87] |
| haute | 1,5–2 ATR | 21 | 0,90 [0,71–0,97] | 0,67 [0,45–0,83] |

**Verdict : non confirmée pour les mèches courantes.** Sur les deux catégories à fort
effectif (n = 224 et 122), l'écart avec le témoin est de 2 à 4 points et les intervalles se
superposent presque entièrement. Viser le 50 % d'une mèche ne vaut pas mieux que viser un
niveau pris au hasard à la même distance. Le taux de 88 % ne dit rien d'autre que « le prix
revient souvent sur ses pas ». Sur BTC, le témoin fait même légèrement **mieux** que la
mèche (0,93 contre 0,88 ; 0,88 contre 0,84).

**Une piste, pas une règle : les mèches hautes de 1,5 à 2 ATR.** BTC donne 1,00 contre un
témoin à 0,76 (n = 17), ETH donne 0,90 contre 0,67 (n = 21). Deux actifs indépendants, même
sens, même ampleur — mais 38 cas au total. À surveiller, pas à exploiter.

## 2. Déviation de range — confirmée sur ETH, instable sur l'historique BTC

| Jeu | Cassure installée | Déviation haute | Déviation basse |
|---|---|---|---|
| BTC 2020–2023 | 0,44 [0,30–0,60] n=36 | 0,56 [0,34–0,75] n=18 | 0,53 [0,31–0,74] n=17 |
| BTC 2023–2026 | 0,29 [0,15–0,47] n=28 | 0,67 [0,44–0,84] n=18 | 0,67 [0,42–0,85] n=15 |
| **ETH 2020–2026** | **0,22 [0,15–0,32] n=86** | **0,63 [0,48–0,76] n=41** | **0,68 [0,50–0,81] n=31** |

**Verdict : confirmée, avec une réserve.** Sur ETH, où l'échantillon est trois fois plus
grand, l'écart est franc et les intervalles sont disjoints : après une déviation, le prix
rejoint le milieu du range trois fois plus souvent qu'après une cassure installée. Sur BTC
récent, même ordre de grandeur.

**Mais elle ne tient pas sur BTC 2020–2023** : 0,53 et 0,56 contre 0,44, intervalles
largement chevauchants. Une règle qui échoue sur une moitié de l'historique ne peut pas
être présentée comme une loi. Qu'elle se généralise à un autre actif est un meilleur
argument que sa tenue sur deux périodes du même actif — cela reste un faisceau, pas une
preuve.

## 3. Acceptance — confirmée, et c'est le résultat le plus stable

Où se trouve le prix à la fin de l'horizon, selon qu'il y a eu acceptance ou simple mèche :

| Jeu | Acceptance (au-dessus) | Mèche seule (au-dessus) | Acceptance (en dessous) | Mèche seule (en dessous) |
|---|---|---|---|---|
| BTC 2020–2023 | 0,70 [0,55–0,82] n=40 | 0,45 [0,21–0,72] n=11 | 0,76 [0,63–0,86] n=51 | 0,50 [0,22–0,78] n=8 |
| BTC 2023–2026 | 0,79 [0,65–0,89] n=43 | 0,29 [0,08–0,64] n=7 | 0,72 [0,54–0,85] n=29 | 0,31 [0,13–0,58] n=13 |
| ETH 2020–2026 | 0,85 [0,77–0,90] n=118 | 0,14 [0,04–0,40] n=14 | 0,84 [0,75–0,90] n=99 | 0,21 [0,09–0,43] n=19 |

**Verdict : confirmée sur les trois jeux.** Après une acceptance, le prix est encore du bon
côté 7 à 8,5 fois sur 10 ; après une simple mèche, 1,4 à 5 fois sur 10. Les intervalles sont
disjoints sur BTC récent et sur ETH. C'est la règle la plus robuste des trois.

Attention cependant : l'acceptance dit « le niveau est franchi pour de bon », pas « le prix
va continuer dans ce sens ». Le rendement médian après une acceptance au-dessus d'un
plafond est **négatif** sur BTC (−1,52 % et −0,67 %). C'est un filtre de validité de
cassure, pas un signal directionnel.

## Ce que ces mesures changent pour le skill

1. **Acceptance** : critère de confirmation de premier rang, le mieux établi. Présenté
   comme filtre de validité, jamais comme direction.
2. **Déviation** : critère de premier rang, avec sa statistique et sa réserve affichées
   (instable sur BTC 2020–2023).
3. **Mèches** : repère graphique sans objectif probabiliste. Le niveau 50 % peut être
   tracé, mais on ne dira pas qu'il est « probable ».

## Limites qui subsistent

- Deux actifs seulement, très corrélés : ETH n'est pas un contrôle totalement indépendant
  de BTC.
- La détection de range a ses propres paramètres ; d'autres réglages donneraient d'autres
  effectifs. Les écarts mesurés y résistent, mais pas les catégories à moins de trente cas.
- Le témoin des mèches est symétrique en distance, pas en contexte : il ne tient pas compte
  du fait qu'une mèche se forme après un mouvement, donc dans un état de marché particulier.
- Aucune correction pour les tests multiples : en mesurant trois règles sur plusieurs
  catégories, un écart apparent sur un petit effectif peut n'être que du bruit.
