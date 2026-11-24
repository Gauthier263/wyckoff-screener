# Carte de liquidité — ce qu'elle vaut, mesuré sur 23 cartes Hyblock

Confrontation de `screener/htf/liqmap.py` (reconstruction maison, données gratuites) aux
cartes Hyblock publiées par CrypNuevo de janvier à novembre 2026, relevées dans
`research/crypnuevo_tweets.md` et transcrites en points de contrôle dans
`screener/htf/references.py`.

Banc : `python -m screener.htf.validate --timeframe 4h --lookback 30`. Il gèle nos données
à la date de chaque capture, construit la carte, et mesure l'écart. L'OI Coinalyze remonte
à janvier 2026 en 4h, ce qui rend les 23 relevés rejouables (en 1h il ne couvre que
84 jours).

Ces relevés ne sont pas des vérités absolues : ce sont les lectures d'un professionnel sur
un outil payant dont la méthode n'est pas publiée, transcrites à l'œil. Ils servent à
mesurer un **placement**, pas à recopier un chiffre.

## Résultat

| Mesure | Score | Lecture |
|---|---|---|
| **Murs de positions** placés à ±1,5 % | **100 %** (2 / 2) | 76 600 → 75 912 (0,50 %) ; 58 600 → 59 397 (0,35 %) |
| **Bon côté** du prix pour l'amas le plus dense | **65 %** (15 / 23) | deux fois sur trois |
| Erreur **médiane** de placement des amas | **2,4 %** | |
| Amas placés à ±1,5 % | 30 % (7 / 23) | |
| Amas tombant dans sa bande annoncée | 22 % (5 / 23) | |
| Sens du comptage de niveaux | 50 % (2 / 4) | |

## La découverte qui a tout changé : le côté était inversé

Premier passage : les amas tombaient du bon côté **26 %** du temps. Le hasard donnerait
50 %. Une erreur aussi régulière n'est pas du bruit, c'est un signe inversé.

Cause, et c'est une règle de la doctrine mal appliquée : **le delta agressif dit qui frappe
au marché, pas qui ouvre la position à levier qui sera liquidée.** Pendant une chute, les
ventes agressives sont surtout des longs qui sortent ou qui sont liquidés ; la position
neuve à fort levier se prend en face, chez celui qui achète le creux. Le modèle lisait
« delta négatif donc des shorts ouvrent », et plaçait donc le carburant au-dessus alors
qu'il était en dessous.

`side_split` a désormais deux modes. `contrarian` (défaut) place la position liquidable en
face de l'agresseur ; `aggressor` conserve l'ancien comportement pour pouvoir rejouer la
comparaison. Effet mesuré : bon côté 26 % → **65 %**, erreur médiane 3,6 % → **2,4 %**.
Deux mesures secondaires se dégradent (amas dans la bande 35 % → 22 %, sens du comptage
75 % → 50 %) : le gain n'est pas universel.

## Règle d'usage dans le rapport de biais

1. **Murs** : à citer avec leur bande, par exemple « mur 59,0k (bande 58,7–59,5k) ». C'est
   la brique la plus sûre — mais elle ne repose que sur **2 points de contrôle**, ce qui
   est trop peu pour en faire une certitude. Toute capture supplémentaire est précieuse.
2. **Amas de liquidations** : à citer comme une **zone**, jamais comme un prix. Formuler
   « du carburant au-dessus, vers 61 à 66k », pas « l'aimant est à 66,0k ». L'erreur
   médiane est de 2,4 %, soit environ 1 500 $ sur un BTC à 60k.
3. **Côté** : fiable deux fois sur trois. Utilisable comme biais, jamais seul.
4. **Ne pas citer** le skew comme mesure de risque de squeeze, ni la thin air (trop large).

## Deux défauts corrigés, deux options laissées désactivées

- **Carnet par palier de levier** (acquis) : chaque position connaît son prix de
  liquidation et disparaît quand il est franchi. Sans cela, un long entré à 76k survivait
  à un prix tombé à 59k, et les murs restaient collés en haut.
- **Renouvellement** (acquis) : une part du volume ferme et rouvre à OI constant. Rappel de
  doctrine, **OI stable ≠ absence de rotation**.
- **Amorçage du carnet** `seed_bars` (désactivé) : le modèle partait d'un carnet vide et ne
  reconstruisait que le flux de la fenêtre, pas le stock — masse de 2 519 BTC pour un OI
  réel de 93 611. Avec amorçage la masse est juste, mais le stock ancien forme un faux mur
  loin du prix et les murs deviennent faux.
- **Prise de profit** `profit_pull` (actif, insuffisant) : un short ouvert à 86k ne tient
  pas jusqu'à 59k. Le terme existe mais ne purge pas assez, le renouvellement étant calé
  sur le volume **spot**, environ cinq fois plus faible que le perp.

## Ce qui reste à faire

- Caler le renouvellement sur le **volume perp** et non spot.
- Plus de points de contrôle sur les **murs** : 2 est insuffisant.
- Des captures **Coinglass** sur des dates déjà couvertes par Hyblock : l'écart entre deux
  fournisseurs dirait quelle part de l'erreur vient de nous, et quelle part de leurs
  propres modèles — qui ne sont pas la vérité non plus.
