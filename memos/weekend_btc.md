# Week-end BTC — étude et règle d'usage

Étude du 16/11/2026, Binance spot BTC/USDT. Daily 2019-01 → 2026-11 (411 week-ends), 1h 2024-01
→ 2026-11. Heures en **UTC réel** (nos pages sont en heure de Paris : CET = UTC+1 l'hiver, CEST = UTC+2 l'été). Script : `screener/session.py`
(fonctions) ; chiffres reproduits par les scripts de l'étude (cf. historique de session).

## 1. Volume et amplitude par jour (daily, médianes)

| Jour | Volume / moyenne 28 j | Range / ATR | P(corps ≥ 1 ATR) | P(corps ≥ 1,5 ATR) |
|---|---|---|---|---|
| Lun | 1,02 | 1,04 | 17,1 % | 8,5 % |
| Mar–Ven | 1,01–1,04 | 0,95–0,98 | 13,9–15,6 % | 4,9–6,3 % |
| **Sam** | **0,57** | **0,53** | **3,9 %** | **1,7 %** |
| **Dim** | **0,63** | **0,71** | **6,1 %** | **2,4 %** |

2024 → 2026 : l'écart se creuse (samedi volume 0,47, range 0,45). Cohérent avec la littérature
(Hansen, Kim et Kimbrough 2021 ; Kaiko 2024 : part du week-end dans le volume tombée à ~13 %).

## 2. Bloc week-end (samedi ouverture → dimanche clôture) vs bloc mardi + mercredi

| | Week-end | Mar + Mer |
|---|---|---|
| \|rendement\| médian | 1,37 % | 2,54 % |
| Range médian | 3,79 % | 6,02 % |
| P(≥ +3 %) / P(≥ +5 %) | 12,2 % / 5,4 % | 25,8 % / 11,4 % |
| P(≤ −3 %) / P(≤ −5 %) | 10,7 % / 4,9 % | 17,3 % / 8,0 % |
| P(\|rendement\| ≥ 1,5 ATR) | 4,9 % | 11,4 % |

Un mouvement directionnel (markup ou markdown) est **environ deux fois moins probable** sur un
week-end que sur deux jours de semaine. Il n'est pas exclu : 50 week-ends ≥ +3 % et 43 ≤ −3 %
en 8 ans.

## 3. Ce qui suit un gros week-end

| Week-end | n | Lundi dans le même sens | Lundi → vendredi dans le même sens | Lundi moyen |
|---|---|---|---|---|
| ≥ +3 % | 50 | 54 % | 48 % | +1,2 % |
| ≤ −3 % | 43 | **40 %** | **35 %** | **+1,0 %** |

Un markup de week-end n'a pas de suite fiable (pile ou face). Un **markdown de week-end est plus
souvent repris** le lundi qu'il n'est prolongé.

Plus gros markups de week-end : 02/01/2021 +12,5 % (semaine suivante +23 %), 01/03/2025
+11,8 % (lundi −8,5 %), 18/05/2019 +10,8 % (lundi −2,6 %), 26/10/2019 +10,1 % (lundi −3,4 %),
26/06/2021 +9,9 %, 11/05/2019 +9,3 % (lundi +11,8 %), 11/03/2023 +9,2 % (crise SVB, semaine
+24,5 %). Sur les 12 plus gros, 6 sont repris dès le lundi.

## 4. Séances intrajournalières (1h, 2024 → 2026)

| Séance (UTC) | Volume / même heure en semaine | Range / même heure en semaine | Rvol(20) médian affiché |
|---|---|---|---|
| Samedi | 0,47 | 0,53 | 0,58 |
| Dimanche 00h–20h | 0,47 | 0,57 | **0,91** |
| **Dimanche 20h → lundi 06h** (reprise : CME, Asie) | 0,99–1,11 | 1,10–1,13 | 1,05–1,13 |

Le **Rvol(20) masque le creux** du dimanche (0,91 affiché pour 0,47 réel) : sa moyenne est faite
de barres de week-end. D'où `session.session_rvol` (volume ÷ médiane de la même heure en semaine).

### Détail heure par heure du dimanche soir (1h, 2024 → 2026, volume / range ÷ même heure en semaine)

| Heure (CET) | 15h–20h | 21h | **22h** | **23h** | **00h** | 01h–03h | 04h–09h |
|---|---|---|---|---|---|---|---|
| Volume | 0,33–0,44 | 0,55 | **0,86** | **1,36** | **1,30** | 1,22–1,09 | ≈ 1,0–1,1 |
| Range | 0,42–0,58 | 0,64 | 0,92 | 1,39 | 1,53 | 1,31–1,13 | ≈ 1,0 |

La reprise **commence vers 21h–22h CET** et culmine **de 23h à 01h CET** : réouverture du forex
(dimanche 17h à New York = 23h CET), ouverture de la semaine en Océanie puis au Japon (Sydney 9h =
23h CET, Tokyo 9h = 01h CET), réouverture des futures BTC du CME (dimanche 17h à Chicago = 00h CET),
clôture de la bougie hebdomadaire (00h UTC = 01h CET). Le seuil « 21h CET » des règles ci-dessous est
le début de la montée ; l'activité pleine arrive une à deux heures plus tard.

## 5. Fiabilité des cassures (clôture 1h hors de la plage des 24 h)

| Séance de la cassure | n | Suite ≥ 2 ATR en 12 h | Retour dans la plage en 12 h |
|---|---|---|---|
| Semaine | 1 030 | 41,8 % | 66,3 % |
| **Week-end (sam → dim 20h UTC)** | 287 | 44,6 % | **75,6 %** |
| Reprise (dim 20h → lun 06h UTC) | 148 | **52,7 %** | 63,5 % |

Les cassures de week-end reviennent plus souvent dans la plage (mèches, chasses aux stops). La
reprise du dimanche soir / lundi matin donne les cassures les plus suivies.

## 6. Exception : le week-end n'est pas toujours creux

Week-end du 14–15/11/2026 : volume daily ×2,22 (samedi) et ×1,87 (dimanche) de la moyenne 28 j,
markdown de −4,3 %. Le Rvol(20) 1h affichait ×0,4 dimanche après-midi (base gonflée par le
crash), alors que le Rvol séance valait ×1,0 à ×2,3 : **le volume restait supérieur à une heure
de semaine normale**. Toujours vérifier le Rvol séance avant de conclure « week-end creux ».

## 7. Règle d'usage (quand utile uniquement)

**Activer** la lecture séance si : la dernière bougie, la position suivie ou un événement clé
tombe entre samedi 00h et lundi 06h UTC (samedi 01h → lundi 07h CET, 02h → 08h CEST l'été), ou si l'analyse porte sur
un mouvement de week-end. **Sinon, ne rien écrire.**

Quand elle est active :
1. **Une ligne de séance** (page de suivi : section « État » ; analyse Wyckoff : bullet
   « Calendrier » en section 1) : séance, Rvol séance de la dernière bougie, et ce qu'on en tire.
2. **Volume** : citer le Rvol séance à côté du Rvol(20) pour les barres de week-end ; un « test à
   volume sec » le dimanche ne vaut que si le Rvol séance est aussi bas.
3. **Cassure de week-end** : la traiter comme **tentative** (76 % reviennent dans la plage) ;
   la confirmation se cherche à la reprise (dimanche 21h → lundi 07h CET, 22h → 08h CEST l'été).
4. **Objectifs** : sur un week-end creux, réduire l'ambition (mouvement ≥ 3 % : ~11 % de chance)
   ou décaler l'attente à la reprise ; après un markdown de week-end ≥ 3 %, le lundi reprend
   plus souvent qu'il ne prolonge (40 % de suite) : risque pour un short pris en fin de week-end.
5. **Lecture froide** : si le Rvol séance est normal ou élevé (week-end de crash, actu), le dire
   et ne pas appliquer la décote.
