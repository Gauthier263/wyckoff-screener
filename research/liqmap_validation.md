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

Cinq configurations mesurées sur le même jeu de points :

| Configuration | Bon côté | Amas à ±1,5 % | Erreur médiane | Murs |
|---|---|---|---|---|
| Agresseur, Binance | 26 % | 26 % | 3,58 % | 2/2 |
| Contrarian, Binance | 65 % | 30 % | 2,38 % | 2/2 |
| **+ horodatages exacts des captures (défaut)** | 61 % | **30 %** | **2,04 %** | 2/2 |
| + Binance et Bybit | **73 %** | 5 % | 2,71 % | 2/2 |
| + calibration sur les mêmes bourses | 68 % | 9 % | 2,47 % | 2/2 |

Lecture :

- **Les murs de positions tiennent partout** : 2 sur 2, à 0,35 % et 0,50 % (76 600 → 75 912,
  58 600 → 59 397). Seule brique solide — mais seulement **deux points de contrôle**, les
  deux seules captures « Open Positions » disponibles.
- **Le côté du carburant est fiable aux deux tiers**, et l'ajout de Bybit l'améliore
  (61 % → 73 %) : plus de couverture, meilleure vue d'ensemble.
- **Le placement précis des amas est mauvais dans toutes les configurations.** Au mieux
  30 % à ±1,5 %, erreur médiane 2 %. Aucun réglage essayé ne renverse cela.

On pourrait retenir une configuration par métrique — multi-bourses pour le côté, Binance
pour le placement. Sur 22 points, ce serait du sur-ajustement déguisé. Le défaut reste donc
**Binance seul**, qui a la plus faible erreur médiane ; `--match-venues` reste disponible
pour qui veut privilégier le côté.

## Quatre corrections, dont trois venues des points de contrôle

1. **Le côté était inversé** (détail ci-dessous) : 26 % → 65 %.
2. **Les horodatages étaient ceux des tweets**, pas des cartes (« Last Updated ») : écarts
   de 1 à 5 heures. Erreur médiane 2,38 % → 2,04 %.
3. **Les couvertures diffèrent** : les heatmaps agrègent Binance + Bybit + Bitmex, les
   Liquidation Levels et Open Positions sont Binance seul. Une part de l'écart ne venait
   pas du modèle. Coinalyze n'expose pas Bitmex : le rapprochement reste partiel.
4. **Calibrer sur les mêmes bourses que l'OI** : prêter aux positions Bybit les paliers de
   levier de Binance faisait tomber le placement à 5 %. Corrigé, il remonte à 9 %.

Deux bugs du dépôt, sans rapport direct avec ce chantier, sont tombés en chemin :
`fetch_liquidations` renvoyait des BTC et non des dollars, et **toutes les requêtes Bybit
revenaient vides en silence** (symbole `BTCUSDT.6` et non `BTCUSDT_PERP.6`), soit 58 % du
volume de Binance absent de l'OI, des liquidations, du delta perp, du funding et du ratio
long/short.

## La découverte principale : le côté était inversé

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
