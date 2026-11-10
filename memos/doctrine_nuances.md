# Doctrine — nuances de lecture (complément à CLAUDE.md)

Nuances, corrections et règles implicites accumulées au fil des analyses, **non déjà écrites**
dans `CLAUDE.md` ni dans les mémos (`memos/memo_theorie.html`, `memo_comportement_resistance.html`,
`memo_tests_co.html`). Quand un point recoupe un document existant, on y renvoie plutôt que de le
répéter. Format : la règle, puis un exemple daté tiré d'une analyse réelle quand il existe. Aucun
emoji, aucune pastille de couleur (cf. CLAUDE.md).

Dates au format de la session (horizon sim 2026). Les niveaux cités sont ceux des analyses faites
dans la conversation.

## 1 · Lecture du contexte macro

- **La TF supérieure fixe le défaut directionnel, pas seulement le biais.** CLAUDE.md pose « plage
  en downtrend = redistribution par défaut ». Symétrique à retenir : **une plage/pause en UPTREND =
  re-accumulation par défaut** (la continuation prime), tant que la distribution n'est pas *prouvée*
  par la cassure du plancher. Ex. BTC H4 03/10 (range 82,9-87,4k au sommet d'un markup) : défaut
  re-accumulation, mais double-top + rejets climactiques = avertissement distribution, non confirmé
  tant que 82,9k tient.
- **Le détecteur auto (`detect_window_structure`) raisonne bottom-up : le rejeter quand le top-down
  le contredit.** Ex. BTC H4 29/07 : le détecteur sortait « accumulation » (SC→ST→SOS→LPS) alors que
  depuis le pic 66 956 la structure faisait lower highs + lower lows = réaction/redistribution. On
  garde la lecture top-down et on note explicitement le désaccord.
- **Higher-lows en escalier = colonne vertébrale de l'uptrend macro ; nommer le higher-low qui, s'il
  casse, brise la structure.** Ex. BTC 3D 03/11 : higher lows 57 800 → 62 275 → 74 968 → 76 326 ;
  tant que ~74 968 (bas de sept) tient, l'uptrend survit ; en dessous, correction vers le creek 67k.
- **Un SOS/jump across the creek existe à l'échelle hebdo.** Ex. BTC 1W semaine du 17/08 : +23 %
  (62,9k→77,7k), spread ×2.74 = cassure de la base 57,8-67k sur expansion volume+spread = SOS macro.
- **Vérifier la fraîcheur de la donnée à chaque fetch HTF.** L'horloge/les données peuvent sauter
  ou retarder entre deux requêtes (resets de conteneur, lag d'archive). Toujours relire la date de
  la dernière bougie et ne pas supposer la continuité. Observé plusieurs fois (saut 30/07→07/08).

## 2 · Volume / spread

- **Volume relatif (RVOL = vol/vol_ma) à étiqueter par barre sur les cas de lecture fine.** Pour
  illustrer un BUEC, afficher le RVOL de la barre de cassure (élevé) et du back-up (sec) : la
  lecture saute aux yeux. Ex. mémo résistance, F2 : cassure RVOL ×1.67 puis back-up RVOL ×0.81.
- **Sur une bougie HTF, « climax + pas de suivi » suffit à conclure, sans clôture-sur-le-bas
  parfaite.** Un Buying Climax hebdo/3D se lit par le volume ultra + l'absence de continuation (le
  prix ne repart pas), même si la clôture n'est pas au plancher. Ex. BTC 14/07 (64 744, vol ×3.1) :
  climax validé par l'échec à suivre, pas par le CLV.

## 3 · OI (en coin)

- **Seuil de TF où l'OI redevient exploitable événement par événement : ~15m→H4 (cœur), 5m avec
  lissage, Daily seulement sur une journée directionnelle franche, ≥3D non.** Principe sous-jacent :
  l'attribution (prix↑+OI↑ = longs neufs, etc.) ne marche que si **1 bougie ≈ 1 événement cohérent** ;
  au-delà, le ΔOI net mélange des flux opposés. Caler la TF de l'OI sur la durée du mouvement à
  attribuer. (Développé dans la conversation ; non dans CLAUDE.md.)
- **Une liquidation short NE fait PAS monter l'OI.** C'est une fermeture forcée (buy-to-close) → OI
  en baisse ou inchangé. Si l'OI monte pendant un squeeze, la hausse vient des **positions neuves qui
  s'ouvrent par-dessus**, pas des liquidations (qui sont un frein à l'OI). Discriminant : prix↑ + OI↓
  + short liq = covering pur (fragile) ; prix↑ + OI↑ + short liq = longs neufs qui remplacent les
  shorts rincés (plus durable).
- **Pattern « OI qui gonfle puis se flush à chaque test d'un plafond » = longs piégés à répétition =
  signature de distribution.** Ex. BTC H4 02/10 : à chaque poussée vers 87k l'OI monte (longs neufs)
  puis se flush sur le rejet (−2.79 % le 02/10 14:00) ; répété = l'offre distribue au plafond.
- **Disponibilité OI Coinalyze à connaître :** (a) couverture **fine aux basses TF** — en 2h,
  `fetch_open_interest` ne remonte que ~3 jours ; `fetch_open_interest_ohlc` couvre davantage
  (ex. 84/150 barres le 03/11). (b) **Coinalyze couvre certains alts hors Binance** via perps
  agrégés (ex. VELVET : `VELVETUSDT_PERP.A`, `.6`, `.4`, `.S`) → OI dispo pour des alts où le prix
  vient de gate/mexc. Sommer les perps pour un OI agrégé.

- **Prix↓ + OI↑ = des positions s'ouvrent des DEUX côtés** (chaque contrat a un long et un short).
  Ne jamais écrire seulement « longs piégés » ni seulement « shorts qui ouvrent » : la question est
  *qui agresse et qui perd*, à trancher avec CVD + ratio L/S + liquidations. Ex. BTC 2h 02/11 06h →
  03/11 08h : prix −2,3 %, OI coin +4,6 %, CVD plat (−158), delta_z +2.54 sur le SOW, comptes 68 → 73 %
  long, 442 BTC de longs liquidés → **shorts posés (offre passive) face à des longs qui achètent la
  baisse et perdent** (liquidés ensuite : 250 BTC le 04/11, 1 216 le 05/11). Limites : le ratio compte
  des comptes, pas des montants ; le CVD est spot.
- **Squeeze ≠ SOS.** Volume et spread hors norme au-dessus d'une borne avec OI coin↓ + gros short liq
  = débouclage forcé, pas de demande neuve → « tentative », possible upthrust. Ex. BTC 2h 04/11 16h :
  ×4.00, 3.42 ATR, OI −1.86 %, 976 BTC de shorts liquidés → upthrust / LPSY 3D confirmé le 05/11.

## 4 · Tierces (CVD, funding, L/S, liquidations)

- **Lire ensemble `absorption` + `delta_z` + `clv` quand ils se contredisent** : le signe d'`absorption`
  dit qui gagne, le signe de `delta_z` dit quel côté était agressif. Cas utiles :
  - `delta_z < 0` (vente agressive) + `clv` haut + `absorption > 0` = **la demande absorbe l'offre**
    (haussier). Ex. BTC H2 03/11 04:00 : dz −3.53, abs +1.28, clôture mid-haute à 76,5k = support
    défendu par absorption.
  - `delta_z > 0` (achat agressif) + `clv` bas + `absorption > 0` = **l'offre absorbe la demande**
    (baissier). Ex. BTC H2 02/11 16:00 : dz +2.54, abs +1.22, clôture basse à ~78k = offre au plafond
    du rebond.
- **Le % long de la foule est un tell de RISQUE à seuils :** ~55 % long = équilibré/neutre
  (BTC 03/10) ; **70-73 % long = encombré** → risque baissier latent même quand l'absorption est
  constructive (VELVET 73 % le 23/08 ; BTC 71 % le 03/11). Un book très long au-dessus d'un support
  = carburant d'un flush si le support casse. À relater comme fragilité, jamais à gommer.
- **CVD indisponible hors Binance (delta taker = klines Binance).** Pour un alt pris sur gate/mexc
  (VELVET) ou pour l'or : pas de CVD → VSA pur côté flux, même si l'OI Coinalyze, lui, existe pour
  certains alts. Ne pas confondre « OI dispo » et « CVD dispo ».
- **Quand une tierce ne revient pas (funding vide, OI partiel), le dire, ne pas inventer.** Observé
  (funding vide sur un fetch BTC) : on note l'indisponibilité et on s'appuie sur le reste.

## 5 · Étiquetage des événements

- **« Back-up profond » est un abus de langage.** Un back-up (BUEC) est **peu profond par
  construction** et **présuppose un SOS/JAC accompli** : il teste une cassure *qui a eu lieu*. Sans
  franchissement tenu, parler de « back-up » est prématuré — c'est une simple réaction. Un repli qui
  ré-entre dans la plage = cassure échouée (upthrust), pas un back-up. (Corrigé en séance ; détaillé
  dans `memo_tests_co.html` §3.2 LPS vs BUEC.)
- **Distinguer trois comportements au même niveau de résistance** (grille MECE complète dans
  `memo_comportement_resistance.html`) : rejet actif (offre agressive, pas de dépassement), absorption
  passive (mur/iceberg, gros volume spread étroit), faux franchissement/upthrust (dépasse puis
  clôture dessous). Ne pas les appeler tous « rejet ».
- **Un événement local (H1/15m) a son propre schéma complet qui n'est qu'un point sur la TF
  supérieure** (fractal, déjà dans CLAUDE.md). Nuance pratique vérifiée : le « rejet 87k » lu en H4
  le 02/10 était, en 15m/H1, une **micro-distribution entière** (micro-BC/upthrust + SOW). Toujours
  pouvoir descendre d'une TF pour confirmer la micro-structure d'un événement HTF.

## 6 · Niveaux

- **Un niveau n'est pas une ligne mais une bande** (étagère de clôtures/opens + lows de réaction
  répétés). Ex. BTC 62 272 : défini par la shelf 08/07 (clôture/open 62 278) + clôtures répétées
  62 210/62 288/62 300, confirmé par un low exact 62 272 qui rebondit. Citer l'origine (quel
  événement/shelf) et traiter comme une zone ±30 pts.
- **Critère de confirmation = clôture de la TF d'analyse, pas la mèche.** Exiger la clôture H4 (ou la
  TF analysée) sous/au-dessus d'un niveau filtre les chasses de stops ; une mèche qui perce puis
  reclôture du bon côté = balayage, pas cassure. Compromis assumé : robustesse contre réactivité
  (pour une gestion serrée, surveiller la clôture d'une TF inférieure). Ex. BTC 62 272 percé en mèche
  (low 62 164) puis reclôturé au-dessus = niveau tenu en clôture.

## 7 · Format de sortie

- **Analyses macro HTF (3D, hebdo) = VSA pur, 2 panneaux `figsize=(17,12.5)`, marqueurs sur les
  événements de CYCLE** (top de cycle, SC/crash, spring du bas, SOS breakout, markup high, lower
  high). Niveaux = bornes de cycle (top, zone de distribution précédente, base/bas de cycle, creek).
  OI/CVD omis à ces TF (cf. §3). Modèle suivi pour BTC 3D et 1W.
- **Marqueurs d'événements : timestamp en CEST étiqueté UTC** (`pd.Timestamp('...', tz='UTC')` sur un
  index décalé +2h), jamais `+02:00`. Rappel critique de CLAUDE.md, source de bug récurrent dans les
  scripts ad hoc — vérifié à chaque graphe.
- **Suivi vs analyse de séquence :** une mise à jour (« mets à jour analyse btc ») = graphe rafraîchi
  + lecture focalisée (ce qui a changé, niveaux, biais), **sans dérouler les 5 sections ni re-livrer
  le mémo**. Le format lourd est réservé aux analyses de séquence. (CLAUDE.md distingue les deux ;
  nuance : une « mise à jour » mérite quand même un graphe à jour, pas qu'un paragraphe.)
- **Index cliquable des mémos ≠ les mémos eux-mêmes.** Les Artifacts publiés sont des instantanés
  figés : modifier le repo ne les met pas à jour. Pour synchroniser, republier l'Artifact (même
  chemin de fichier dans la même session = URL conservée ; sinon passer l'URL existante). Préférence
  Gauthier : garder l'URL stable.

## 8 · Erreurs passées à ne pas refaire

- **Vérifier l'ISSUE d'un exemple Wyckoff, pas seulement la forme de la barre.** Les premiers
  exemples du mémo résistance étaient faux parce que la détection validait la forme mais pas le
  résultat. Corrections (séance mémo V8) : un **BUEC** doit être une séquence continue
  cassure→back-up immédiat→continuation (le retest de 06/07 appariait un *autre* markup plus tard —
  faux) ; un **sommet d'épuisement** doit *réellement se retourner* (le HH du 19/07 est reparti à la
  hausse — faux, remplacé par 01/07 06:00) ; une **cassure ratée** doit *réellement échouer*
  (12/07 16:00 repasse sous le niveau — bon) ; une **distribution étalée** doit avoir des hauts
  *déclinants* (14-17/07 faisait un higher high le 15/07 — faux ; vrai triple-lower-high = 06→13/07) ;
  une **absorption** doit être *au plafond*, pas en milieu de baisse (corrigé vers 14/07 18:00).
- **Ne pas importer la grammaire d'accumulation dans un cadre classé distribution** (SC/AR vs
  BC/AR — détaillé dans CLAUDE.md « AR/ST ancrés sur le climax »). Rappel car facile à refaire sous
  pression.
- **Ne pas affirmer une « asymétrie structurelle » de la formule d'absorption :** elle est prouvée
  symétrique (test miroir 1e-13) ; un désaccord per-barre vs `absorption_w` vient du *contexte de
  marché* (rallyes plus directionnels que les baisses), pas d'un bug de signe. (Déjà dans CLAUDE.md ;
  listé ici car c'était une affirmation fausse corrigée en séance.)
- **Ne pas étiqueter l'accumulation sans la gagner.** Une base sur apathie (volume ET OI qui
  drainent) n'est PAS une accumulation tant qu'aucune demande fraîche ne se construit. Ex. VELVET
  23/08 : SC + higher lows mais OI −25 % (26,5M→20M) + 73 % long = base ambiguë à biais baissier, pas
  une accumulation propre.

## 9 · Questions restées ouvertes

- **Seuil de filtrage week-end pour les perps d'actifs non-24/7.** Pour l'or, CLAUDE.md impose de
  filtrer Sam/Dim (volume week-end ~11 % de la semaine). Pour le perp pétrole MEXC (UKOIL), le volume
  week-end était ~58 % de la semaine → choix fait de **ne pas** filtrer (instrument réellement actif
  24/7) mais caveat posé (le Brent sous-jacent ferme → gap possible au lundi). Seuil exact à partir
  duquel on filtre : non tranché.
- **Ré-vérification des exemples datés du `memo_tests_co.html` §7** (ex. BTC shakeout 57 800 du
  01/07) : repris de la version uploadée par Gauthier, **non re-vérifiés sur données** — à croiser si
  on veut les durcir.
- **CVD pour les alts/or :** proxy spot indisponible hors Binance. Piste ouverte : un CVD agrégé
  multi-exchange via une autre source, non implémenté.
