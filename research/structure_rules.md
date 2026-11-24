# Les règles de structure, mesurées — et une qui ne tient pas

Chaque règle reprise de CrypNuevo est une affirmation statistique déguisée. Mesurée sur
l'historique BTC complet avec `python -m screener.htf.rules_study`, en 4h sur 3 ans
(6 570 bougies) et en 1D sur 6 ans (2 190 bougies).

**Le point de méthode qui décide de tout : le groupe témoin.** Dire « 88 % des mèches se
remplissent » ne prouve rien tant qu'on ne sait pas à quelle fréquence un niveau
*quelconque*, à la même distance, est touché dans le même délai. Sans témoin, on mesure la
volatilité du marché et on l'attribue à la figure. Pour chaque mèche, le témoin est un
niveau fictif placé à la **même distance du prix, du côté opposé**.

## 1. Remplissage des mèches — la règle ne tient pas

« Long wicks tend to fill sooner rather than later, at least the 50 % level. » C'est sa
stratégie préférée, citée dans 48 des 158 entrées du relevé.

**En 4h, horizon 60 barres :**

| Mèche | Taille | n | Remplie 50 % | **Témoin 50 %** | Remplie 100 % | **Témoin 100 %** |
|---|---|---|---|---|---|---|
| basse | 1–1,5 ATR | 128 | 0,88 | **0,93** | 0,79 | **0,84** |
| basse | 1,5–2 ATR | 17 | 0,88 | 0,88 | 0,71 | 0,71 |
| haute | 1–1,5 ATR | 82 | 0,84 | **0,88** | 0,72 | **0,82** |
| haute | 1,5–2 ATR | 17 | 1,00 | 0,76 | 1,00 | 0,65 |

**En 1D, horizon 30 barres :**

| Mèche | Taille | n | Remplie 50 % | Témoin 50 % | Remplie 100 % | Témoin 100 % |
|---|---|---|---|---|---|---|
| basse | 1–1,5 ATR | 21 | 0,86 | 0,76 | 0,67 | 0,67 |
| basse | 1,5–2 ATR | 11 | 0,91 | 0,82 | 0,55 | **0,73** |
| haute | 1–1,5 ATR | 20 | 1,00 | 0,80 | 0,85 | 0,55 |

**Verdict : non confirmée.** Sur les deux seules catégories où l'échantillon est suffisant
(mèches de 1 à 1,5 ATR, n = 128 et 82 en 4h), le taux de remplissage est **inférieur au
témoin**. Autrement dit, viser le 50 % d'une mèche ne vaut pas mieux que viser un niveau
pris au hasard à la même distance — et un peu moins bien. Le taux élevé en valeur absolue
(84 à 88 %) ne dit rien d'autre que « le prix revient souvent sur ses pas en 60 barres ».

Les catégories où la mèche semble battre le témoin (hautes de 1,5 à 2 ATR en 4h : 1,00
contre 0,76 ; hautes en 1D : 1,00 contre 0,80) comptent 17 et 20 cas. C'est trop peu pour
en faire une règle, et l'asymétrie haut/bas n'a pas d'explication mécanique évidente.

**Conséquence pour le skill** : ne pas construire le biais sur le remplissage des mèches,
ni citer un objectif « 50 % de la mèche » comme s'il était probable. On peut mentionner le
niveau comme repère graphique, en disant qu'il n'a pas d'avantage mesuré.

## 2. Déviation de range — la règle la plus solide

Une sortie du range suivie d'un retour dedans, contre une sortie qui s'installe.

| Cas | n (4h) | Milieu atteint | n (1D) | Milieu atteint |
|---|---|---|---|---|
| Cassure installée | 331 | **0,32** | 151 | **0,17** |
| Déviation sous le plancher | 147 | **0,70** | 74 | **0,55** |
| Déviation au-dessus du plafond | 131 | **0,63** | 51 | 0,43 |

**Verdict : confirmée, et nettement.** Après une déviation, le prix rejoint le milieu du
range deux fois plus souvent qu'après une cassure installée, sur les deux timeframes et
avec des effectifs suffisants. C'est exactement la lecture qui manquait le 22/11 : la mèche
à 55 130 sortait sous le plancher annuel puis y revenait.

En 1D, le rendement médian d'une déviation sous le plancher est de +1,96 % à 30 jours,
contre −0,53 % pour une déviation au-dessus du plafond : l'asymétrie va dans le sens d'un
marché haussier sur la période, à ne pas prendre pour une loi.

## 3. Acceptance — confirmée, mais pas pour la raison attendue

| État | Côté | n (4h) | A continué | **Est revenu** |
|---|---|---|---|---|
| Acceptance | au-dessus | 224 | 0,81 | **0,34** |
| Mèche seule | au-dessus | 40 | 0,78 | **1,00** |
| Acceptance | en dessous | 156 | 0,89 | **0,40** |
| Mèche seule | en dessous | 56 | 0,86 | **1,00** |

**Verdict : confirmée, mais son utilité n'est pas celle qu'on croit.** L'acceptance ne
prédit pas mieux la **continuation** qu'une simple mèche : 81 % contre 78 %, écart
négligeable. En revanche, après une mèche seule, le prix repasse le niveau dans **100 %**
des cas, contre 34 à 40 % après une acceptance.

Autrement dit : l'acceptance ne dit pas « ça va monter », elle dit « ça ne va pas revenir
tout de suite ». C'est un **filtre anti-faux-signal**, pas un signal directionnel. La règle
« jamais sur une mèche » est donc juste, pour une raison plus précise que l'intuition.

À noter : en 4h, le rendement médian après une acceptance au-dessus est **négatif**
(−0,68 % à 30 barres). Accepter au-dessus d'un plafond ne garantit nullement la poursuite
de la hausse.

## Ce que ces mesures changent pour le skill

1. **Déviation** : critère de premier rang, avec sa statistique affichée.
2. **Acceptance** : critère de confirmation, présenté comme filtre et non comme direction.
3. **Mèches** : rétrogradées au rang de repère graphique, sans objectif probabiliste.

## Limites

- Un seul actif, une seule période. BTC 2020–2026 contient deux marchés haussiers et deux
  krachs ; rien ne dit que ces taux tiennent ailleurs.
- La détection de range (`structure.find_range`) a ses propres paramètres ; d'autres
  réglages donneraient d'autres effectifs. Les écarts mesurés sont assez larges pour y
  résister, mais pas les cas à moins de trente observations.
- Le témoin des mèches est symétrique en distance, pas en contexte : il ne tient pas compte
  du fait qu'une mèche se forme après un mouvement, donc dans un état de marché particulier.
