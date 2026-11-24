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
2. **La règle des mèches était mal formulée, puis mal contrôlée.** Elle ne dit pas « la
   mèche sera remplie » mais « le retracement **précède** le mouvement ». Mesurer le simple
   remplissage ne testait pas la règle. Et le premier témoin construit pour elle était
   bogué : « même distance, côté opposé » retombait exactement sur le niveau testé, d'où
   deux colonnes identiques. Le témoin est désormais une barre ordinaire antérieure.
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

## 1. Mèches — voir `research/wick_rule.md`

La règle des mèches a été reprise en cinq itérations dans un document dédié, après la
précision de Gauthier : c'est une règle d'**ordre** (le retest précède le mouvement) fondée
sur un **déséquilibre de liquidité**. Résultat : elle ne vaut que pour les **mèches de
liquidation** (≥ 1,5 ATR, journée de liquidations ≥ 2,6× la médiane), où le 50 % est retesté
d'abord dans environ six cas sur dix contre quatre pour un niveau quelconque, validé sur
BTC, ETH, SOL et XRP, en et hors échantillon. Une mèche ordinaire n'a aucun avantage.

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

## 4. Three Taps — voir `research/three_taps.md`

Mesuré comme un trade sur quatre actifs et trois timeframes, avec deux protocoles d'entrée et
deux stops (dont le sien, en acceptance). Les touches d'un extrême de range battent toujours
un point pris au hasard, mais **la troisième n'a rien de particulier**, et le trade type
(stop sous la touche, cible au mid-range) **n'est rentable dans aucune configuration**. Son
règle de timing tient pour une entrée au contact, pas sur reprise.

## Ce que ces mesures changent pour le skill

1. **Acceptance** : critère de confirmation de premier rang, le mieux établi. Présenté
   comme filtre de validité, jamais comme direction.
2. **Déviation** : critère de premier rang, avec sa statistique et sa réserve affichées
   (instable sur BTC 2020–2023).
3. **Three Taps** : un extrême de range est une zone de réaction, pas un signal ; le décompte
   des touches n'est pas affiché comme information. Voir `research/three_taps.md`.
4. **Mèches** : seulement les mèches de liquidation, avec leur taux (environ 6 sur 10
   contre 4) et leur fenêtre (8 à 13 bougies) ; le 50 %, jamais le 100 % ; une mèche
   ordinaire est un simple repère graphique. Voir `research/wick_rule.md`.

## Limites qui subsistent

- Deux actifs seulement, très corrélés : ETH n'est pas un contrôle totalement indépendant
  de BTC.
- La détection de range a ses propres paramètres ; d'autres réglages donneraient d'autres
  effectifs. Les écarts mesurés y résistent, mais pas les catégories à moins de trente cas.
- Le témoin des mèches est symétrique en distance, pas en contexte : il ne tient pas compte
  du fait qu'une mèche se forme après un mouvement, donc dans un état de marché particulier.
- Aucune correction pour les tests multiples : en mesurant trois règles sur plusieurs
  catégories, un écart apparent sur un petit effectif peut n'être que du bruit.
