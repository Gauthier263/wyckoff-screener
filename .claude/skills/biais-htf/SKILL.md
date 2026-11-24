---
name: biais-htf
description: Biais directionnel haute timeframe (1D / 4h) de BTC — range, déviation, acceptance, mèches de liquidation, deux scénarios chiffrés et zones cibles justifiées, publié en page interactive. À utiliser quand Gauthier demande « biais HTF », « biais 1D », « biais 4h », « trend BTC », « où va BTC cette semaine », « V-shape ou remplissage de mèche », « quelles zones viser », ou le rapport du dimanche soir. Pas pour une analyse de séquence Wyckoff (format canonique, autre procédure), ni pour un suivi intrabougie.
---

# Biais HTF (1D / 4h)

Outil d'aide à la décision : il ne passe jamais d'ordre. Il dit **où** est le prix dans sa
structure HTF, **quelle direction** les règles mesurées soutiennent, et **à quelles
conditions** chaque scénario s'active ou s'invalide.

## Principe : ne citer que ce qui a été mesuré

Chaque élément du rapport vient d'une règle testée sur l'historique, contre un témoin et hors
échantillon. Les chiffres à citer sont dans le code (`screener/htf/bias.py`,
`screener/htf/wick_study.py`) et les études dans `research/` :

| Règle | Ce qu'elle vaut | Étude |
|---|---|---|
| Déviation de range reprise | milieu atteint 55–70 % contre 17–32 % après une cassure installée ; **instable sur BTC 2020–2023** | `research/structure_rules.md` |
| Acceptance (2 clôtures) | filtre de validité d'une cassure, **pas** un signal de direction | idem |
| Extrême de range | zone de réaction (rebond plus fréquent qu'ailleurs), **pas** un signal d'entrée | `research/three_taps.md` |
| Mèche de liquidation (≥ 1,5 ATR, liquidations du jour ≥ 2,6×) | le 50 % est retesté avant le mouvement ~6 fois sur 10 (contre ~4), fenêtre 8–13 bougies ; **le 100 % n'a aucun avantage** ; 1h/4h seulement | `research/wick_rule.md` |
| Murs d'OI | 2/2 à ~1 % sur les cartes Hyblock ; amas de liquidation en **zone** seulement | `research/liqmap_validation.md` |
| Three Taps | la 3e touche n'a rien de particulier ; aucun setup rentable | `research/three_taps.md` |
| EMA 50, sur-extension, sentiment | **non mesurés** : contexte, poids nul | — |

Ne jamais présenter un niveau 50 % de mèche ordinaire comme « probable », ni un 100 % de
mèche comme cible, ni un décompte de touches comme un signal.

## Procédure

1. **Les bornes du range 1D d'abord.** Demander ou reprendre celles que Gauthier trace (ou
   celles d'une analyse récente). La détection automatique ne retrouve les bornes de
   CrypNuevo que 2 fois sur 7 : sans bornes fournies, le rapport le signale en alerte.
2. **Lancer la commande** (heure de Paris pour `--asof`) :
   ```bash
   python -m screener.htf.report --floor 60000 --ceiling 81341 \
       --floor-zone 59000,60600 --ceiling-zone 81000,81500 \
       --html <scratchpad>/biais_htf.html --json <scratchpad>/biais_htf.json
   # --liqmap pour ajouter les murs d'OI (plus lent) ; --asof "2026-11-22 22:00" pour un rejeu
   ```
3. **Publier la page** en Artifact (même fichier = même lien à chaque mise à jour).
4. **Répondre court dans le fil** : le lien, puis le biais et sa conviction, le déclencheur
   du scénario principal avec son état (acquis / à obtenir), l'invalidation, et les alertes.
   Niveaux toujours justifiés entre parenthèses, heure de Paris avec son fuseau.

## Lecture du résultat

- **Neutre** = milieu du range, aucun avantage mesuré. C'est une réponse, pas un échec :
  dans le rejeu des prévisions de CrypNuevo, ses lectures au milieu du range valaient pile ou
  face (11 sur 21). Le dire, et indiquer le niveau à attendre.
- **Conviction faible** (score ±2) = un seul élément mesuré porte le biais. Rappeler la
  réserve de la règle (déviation instable sur BTC 2020–2023).
- **Alerte « ne pas vendre la cassure »** = déviation sous le plancher en cours : c'est
  l'erreur du 22/11. Elle prime sur toute lecture LTF de redistribution tant que
  l'acceptance sous la zone du plancher n'est pas confirmée (alerte rouge, sans blocage —
  choix de Gauthier).
- **Cadre 4h absent** = pas de sous-range horizontal (marché en tendance) : seul le 1D porte
  le biais.

## Limites à rappeler quand elles comptent

- Rejeu sur 33 prévisions : l'outil se prononce 12 fois, juste 8 (67 %, IC 39–86 %) — une
  tendance, pas une performance établie (`research/replay_forecasts.md`).
- Trois de ses quatre erreurs viennent des extrêmes de range (zone de réaction, pas signal).
- Liquidations quotidiennes : elles qualifient la journée de la mèche, pas la mèche.

## Vérifier l'outillage

`python -m screener.htf.health` dit quelle source répond (OHLCV, OI, delta perp,
liquidations, Hyperliquid, Deribit, calendrier, Yahoo, Fear & Greed).
