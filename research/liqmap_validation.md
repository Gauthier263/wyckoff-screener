# Carte de liquidité — ce qu'elle vaut, mesuré sur les cartes Hyblock

Confrontation de `screener/htf/liqmap.py` (reconstruction maison, données gratuites) aux
cartes Hyblock publiées par CrypNuevo, relevées dans `research/crypnuevo_tweets.md`.
Rejeu figé à la date de chaque capture : `python -m screener.htf.replay`.

Paramètres : OI coin Coinalyze 1h, 30 jours de recul, grille 0,1 %, paliers de levier
**calibrés** par `calibrate.fit_leverage_tiers` sur les liquidations réellement exécutées,
séparément pour les longs et pour les shorts.

## Résultat

| Repère de sa carte | Notre carte | Verdict |
|---|---|---|
| 08/11 — mur d'OI **76,6k** (prix 75,87k) | 75 988, bande 75 685–76 216 | **retrouvé**, écart 0,5–0,8 % |
| 08/11 — amas de liquidations **73k–74,7k** | pic 73 010, puis 72 646 et 71 851 | **retrouvé** (pic dans sa zone) |
| 08/11 — « most liquidations to the downside » | skew −0,46 | **sens correct** |
| 22/11 — mur d'OI **58,6k** (prix 58,92k) | 58 983 et 59 278, bande 58 748–59 456 | **retrouvé**, écart 0,3–1,2 % |
| 22/11 — aimant de liquidations **66k** | 61 635, 61 943, 62 192 | **raté**, environ 6 % trop bas |
| 15/11 — carburant très majoritairement **au-dessus** (606 niveaux de shorts contre 144) | skew −0,06 à −0,46 | **raté** (sens inverse) |
| 22/11 — thin air **62,8k–65,8k** | 60 234–72 758 | **trop large** pour servir |

## Lecture

**Fiable : les murs de positions.** Deux dates sur deux, à environ 1 %. C'est la brique la
plus exploitable, et celle qui manquait le 22/11 (« notre grille delta perp × OI dit qui agit
maintenant, pas où est le carburant »).

**Fiable : le carburant du côté où les liquidations tombent vraiment.** Après la
calibration, le 08/11 place son pic à 73 010 dans sa zone 73–74,7k, celle qui sera touchée le
12/11. Avant calibration, nous étions à 67 400, soit 8 % trop bas : la distribution des
leviers était le seul paramètre non mesuré de la chaîne, et c'est lui qui place les amas.

**Non fiable : le côté opposé après un krach.** Les 15 et 22/11, nous sous-estimons le
carburant au-dessus du prix. Cause structurelle : sur ces fenêtres, les liquidations
observées sont massivement des longs (22 616 BTC contre 7 394 de shorts au 22/11), le delta
agressif est vendeur, et notre modèle en déduit peu de shorts liquidables au-dessus. Hyblock
compte des **niveaux** (606 contre 144) et non des quantités, ce qui ne donne pas le même
déséquilibre. Changer le lookback (7, 14 ou 30 jours) n'y change rien.

## Règle d'usage dans le rapport de biais

1. Citer les **murs** avec leur bande, par exemple « mur 59,0k (bande 58,7–59,5k) ».
2. Citer le **carburant** seulement du côté majoritaire des liquidations observées, et
   indiquer la corrélation de calibration de ce côté (`fit`).
3. Ne **pas** citer le skew comme mesure du risque de squeeze tant que le côté opposé n'est
   pas corrigé. Un déséquilibre de notre carte ne vaut pas son « delta liquidations ».
4. Ne **pas** citer la thin air : trop large.

## Tentative de correction du côté haut — résultat négatif, et pourquoi

Trois pistes ont été creusées pour retrouver son aimant à 66k du 22/11. Deux défauts réels
du modèle ont été trouvés et corrigés au passage, mais le repère reste manqué.

1. **Compter les niveaux plutôt que les quantités** (il annonce 606 niveaux de shorts contre
   144 de longs au 15/11). Notre carte en donne 304 contre 145 : le **rapport** est du bon
   ordre, mais les niveaux portent des quantités si faibles que le classement des amas n'en
   est pas changé.
2. **Amorcer le carnet** (`seed_bars`). Défaut réel : le modèle partait d'un carnet vide et
   ne reconstruisait que le *flux* de la fenêtre, pas le *stock*. La masse du profil tombait
   à 2 519 BTC pour un OI réel de 93 611 — les amas lus n'étaient alors que du bruit.
   Corrigé : avec amorçage, la masse remonte à 51 000–67 000 BTC. **Mais** le stock amorcé
   en octobre (prix 82–86k) n'est ensuite ni assez liquidé ni assez soldé, et forme un faux
   mur à 81–86k alors que le prix traite à 59k. Les murs, eux, deviennent faux.
3. **Prise de profit** (`profit_pull`). Deuxième défaut réel : un short ouvert à 86k restait
   indéfiniment en carnet avec le prix à 59k, alors qu'une telle position est soldée. Le
   terme a été ajouté ; il ne suffit pas à vider le haut, parce que le volume de
   renouvellement est calé sur le volume **spot** (environ cinq fois plus faible que le perp).

Conclusion : l'amorçage du stock et le taux de renouvellement sont deux hypothèses opposées
qu'on ne peut pas identifier séparément sur trois points de référence sans sur-ajuster. Les
deux options restent dans le code, **désactivées par défaut** (`seed_bars=0`), et le réglage
par défaut est celui qui est validé ci-dessus. À reprendre avec un volume perp et un jeu de
cartes de référence plus large.
