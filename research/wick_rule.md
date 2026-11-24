# La règle des mèches — reconstruite en cinq itérations

Rejouer : `python -m screener.htf.wick_study --symbols BTC/USDT,ETH/USDT,SOL/USDT,XRP/USDT`
Code : `screener/htf/wick_study.py` (règle : `classify_wick`, `liq_rel`, `RULE_*`).

## La règle de départ

Celle de CrypNuevo, précisée par Gauthier :

> Une longue mèche (1D, 4h, 1h le plus souvent) est un **déséquilibre de liquidité** : le prix
> a traversé une zone trop vite, sans y échanger. Dans un scénario d'accumulation, si le prix
> doit monter, il ne montera pas **avant** d'avoir retracé 50 % ou 100 % de la mèche basse.
> Inversement en distribution. Le retest peut être immédiat ou prendre plusieurs bougies
> (« 5 à 8 bougies hebdo » pour une mèche 1W, tweet du 08/02).

C'est une règle d'**ordre** et de **délai**, pas une probabilité de remplissage : une étude
antérieure qui mesurait le simple remplissage ne la testait pas.

## Méthode commune

- **Mèches** : au moins 1,5 ATR ; les grappes (mèches de même sens à moins de 10 bougies)
  comptent pour un seul épisode, la plus grande en ATR.
- **Ordre** : lequel arrive d'abord, le retour sur le 50 % de la mèche, ou un mouvement de
  2 ATR dans le sens du scénario (vers le haut après une mèche basse, vers le bas après une
  mèche haute) ? Seuls les cas où le mouvement a eu lieu comptent.
- **Délai** : nombre de bougies jusqu'au retest, sur un horizon long (500 bougies en 1h,
  300 en 4h), pour ne pas déclarer « jamais » un retest simplement tardif.
- **Témoin** : la bougie 60 positions plus tôt, à laquelle on applique le même écart en ATR
  et la même cible. Il dit ce que ferait un niveau quelconque aussi éloigné.
- **Intervalles de Wilson** sur chaque taux.

## Itération 1 — le délai

Sur BTC et ETH, 1h et 4h, 2020–2026 :

- le 50 % est retesté avec une **avance nette sur le témoin dans les premières bougies**
  (BTC 1h, mèche basse : 0,44 contre 0,29 après 3 bougies) ;
- délai médian du retest : **3 à 6 bougies** pour le 50 %, **13 à 25** pour le 100 % ;
- **l'avance disparaît après 13 à 21 bougies** : si le prix n'est pas revenu vite, il est
  parti, et la mèche n'a plus rien de particulier ;
- **le 100 % n'a d'avance à aucun moment** ;
- en 1D, 5 à 13 mèches par actif : rien n'est mesurable.

## Itération 2 — le vrai déséquilibre, avec des bougies fines

Chaque mèche est radiographiée avec les bougies 5 min (mèches 1h) ou 15 min (mèches 4h) :
quelle part du volume de la bougie mère est tombée dans la zone de la mèche, rapportée à la
part de la zone dans le range ? Densité < 1 : zone **traversée sans échange** ; densité > 1 :
volume **concentré** dans la zone (absorption).

Sur 1 132 mèches :

| Classe | n | Retest d'abord | Témoin |
|---|---|---|---|
| Vide (densité ≤ 0,97) | 378 | **0,63** [0,57–0,68] | 0,48 |
| Moyenne | 377 | 0,60 | 0,56 |
| Absorption (densité ≥ 1,10) | 377 | 0,52 | **0,56** |

Une mèche d'absorption n'a aucun avantage : la zone a été traitée — Wyckoff dirait un test
—, il n'y a rien à rééquilibrer. Ce résultat **s'érodera** aux contrôles suivants.

## Itération 3 — le contexte, et un sur-ajustement

Facteurs ajoutés : volume relatif de la bougie, flux agressif spot vers la mèche (delta
taker sur tout l'historique), **liquidations du jour** du côté de la mèche (Coinalyze,
quotidien depuis 2020), position par rapport au range, tendance (EMA 50).

Sur l'apprentissage (BTC/ETH 2020–2024), quatre facteurs donnaient +0,18 à +0,21 sur le
témoin : vide, agression, liquidations, mèche restée dans le range. Combinés en un score à
trois conditions, ils formaient un beau gradient (de −0,24 à +0,30). **Sur 2025–2026, jamais
vu, le gradient a disparu** (−0,03 à −0,04 pour 0, 1 et 2 conditions). Trois seuils choisis
sur les données mêmes où l'on mesure : du sur-ajustement.

## Itération 4 — chaque facteur seul, hors échantillon

| Facteur | Apprentissage 2020–24 | Test 2025–26 |
|---|---|---|
| Liquidations du jour ≥ 2,6× | +0,21 | **+0,14** (sans : −0,07) |
| Vide (densité ≤ 0,95) | +0,18 | +0,10 (sans : −0,06) |
| Agression (flux) | +0,19 | **−0,09** |
| Dans le range | +0,19 | **−0,01** |
| Grande mèche (≥ 2 ATR) | +0,12 | −0,03 |
| **Toutes mèches** | +0,07 | **−0,02** |

Une mèche quelconque n'a **aucun** avantage en 2025–2026. Deux facteurs résistent.

## Itération 5 — contrôle vierge : SOL et XRP

Seuils figés sur BTC/ETH 2020–2024, appliqués sans retouche à deux actifs que l'étude n'avait
jamais touchés (956 mèches) :

| Mèches | n | Retest d'abord | Témoin | Écart |
|---|---|---|---|---|
| **Liquidations du jour ≥ 2,6×** | 387 | 0,56 [0,50–0,62] | 0,42 | **+0,14** |
| sans | 569 | 0,53 | 0,54 | −0,01 |
| Vide (densité ≤ 0,95) | 244 | 0,53 | 0,47 | +0,06 (sans : +0,04) |
| Ni l'un ni l'autre | 433 | 0,52 | 0,55 | −0,03 |

Les liquidations donnent **le même +0,14** sur deux jeux indépendants. Le vide s'érode à
chaque contrôle (+0,18, +0,10, +0,06) : il ne tient pas seul.

## La règle retenue

> **Après une longue mèche (≥ 1,5 ATR, 1h ou 4h) formée un jour de liquidations forcées du
> côté de la mèche (≥ 2,6 fois leur médiane des 30 jours), le prix retest le 50 % de la
> mèche avant d'effectuer le mouvement du scénario dans environ six cas sur dix**, contre
> quatre sur dix pour un niveau quelconque placé aussi loin.

Sur les 736 mèches de liquidation des quatre actifs :

| Scénario | Retest du 50 % d'abord | Témoin |
|---|---|---|
| Accumulation (mèche basse) | **0,62** [0,57–0,67] | 0,44 |
| Distribution (mèche haute) | **0,54** [0,46–0,62] | 0,40 |

- **Délai** : médiane 4 bougies, trois quarts des retests sous 15 (1h) à 18 (4h) bougies.
  L'avance sur le témoin culmine vers 5 bougies (0,56 contre 0,41) et s'éteint vers 13 à 21.
- **Le 100 %** n'a d'avance dans aucun cas : ne jamais l'annoncer comme probable.
- **Sans liquidations**, une longue mèche n'a aucun avantage (0,53 contre 0,54).

**Le mécanisme.** Une mèche de liquidation est un mouvement **forcé** : des positions
fermées d'office, sans intention d'acheter ni de vendre à ces prix. Elle traverse une zone où
aucune liquidité réelle ne s'est construite. C'est exactement le « mouvement de marché trop
rapide » de la règle — et c'est ce mouvement-là, pas la forme de la bougie, qui appelle un
retour.

## Ce que l'étude change à la règle de CrypNuevo

1. **Elle n'est pas une loi** : même dans les meilleures conditions, le prix part sans
   retester le 50 % dans environ 40 % des cas. « Il ne montera pas avant » est trop fort.
2. **Elle ne vaut que pour les mèches de liquidation.** C'est le filtre qui manquait.
3. **Le 50 %, pas le 100 %.**
4. **Une fenêtre courte** : l'essentiel se joue dans les 8 à 13 bougies.
5. **Son exception du 22/11** (« mèche de liquidation sous le range, peut rester non
   remplie ») n'est **pas confirmée** : les mèches hors range avec liquidations se
   retracent aussi d'abord (+0,23 en apprentissage, +0,16 en test). Le 22/11 lui-même est
   simplement tombé dans les quatre cas sur dix où le mouvement part d'abord.

## Limites

- Quatre actifs crypto, très corrélés entre eux ; aucun actif d'une autre classe.
- Les liquidations sont celles de Binance (Coinalyze), qui n'en publie qu'un échantillon :
  le seuil de 2,6× est relatif et doit le rester.
- Les liquidations sont quotidiennes : elles qualifient la **journée** de la mèche, pas la
  mèche elle-même. En 4h elles existent depuis décembre 2025 seulement ; un affinage à
  l'heure sera possible quand l'historique sera plus long.
- Le seuil de 2,6× vient du tercile haut de l'apprentissage ; il n'a pas été optimisé, et ne
  doit pas l'être sur les données de test.
- Le témoin contrôle la distance et la période, pas le contexte exact de la mèche.
