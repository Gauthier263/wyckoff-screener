# CLAUDE.md — contexte projet

Screener Wyckoff crypto (accumulation/distribution), H1/H4, via ccxt.
Aide à la décision discrétionnaire — **jamais** d'exécution d'ordres automatique.

## Architecture
- `screener/data.py` — ccxt : `build_universe()` (top paires USDT par volume),
  `fetch_ohlcv()` avec cache parquet. `get_exchange("binance")` route les endpoints
  publics vers le miroir `data-api.binance.vision` (spot, non géo-restreint).
  `fetch_open_interest()` — historique d'OI (perp), indexé ts UTC. `source=binance|okx|agg3` :
  **`binance`** (défaut) = **OI Binance live via Coinalyze** (`fetch_coinalyze_oi`, agrégateur
  tiers non géo-bloqué) — **la donnée qui colle à TradingView `BTCUSDT.P`** ; `fapi` Binance
  renvoie 451 ici. Clé gratuite read-only lue depuis l'env `COINALYZE_API_KEY` **ou** le fichier
  `.cache/coinalyze_key` (gitignoré, jamais commité) ; **repli auto sur OKX** si pas de clé/API
  HS. Coinalyze renvoie nativement des **bougies d'OI** (OHLC) et supporte 5m→1d (dont 15m/30m).
  **`okx`** = venue unique (Gate retiré) ; **`agg3`** ajoute l'**OI Binance** via l'archive
  `data.binance.vision` (metrics 5m) + un point **CoinGecko**, **pour la profondeur historique**
  (mode `start`/`end`). Fusion via `_combine_oi` (carry → pas de « falaise »).
  `_oi_series` **rabat les TF non supportées par une venue sur une base 5 min puis resample**
  (ex. OKX refuse 15m/30m → sinon *exclu en silence* ; table `_VENUE_OI_TF`). En **live**,
  l'archive Binance trop en retard (> `_ARCHIVE_MAX_LAG_H`, via `_archive_lag_hours`) est
  **exclue** au lieu d'être reportée à plat — un Binance figé en J-1 masquait la direction
  réelle (agg3 live ≈ OKX). `binance_oi_lag_hours()` expose ce retard ; le panneau OI le
  **signale**. `start`/`end` ciblent l'OI Binance d'un **intervalle historique** (ex. mars)
  via les quotidiens d'archive (téléchargements parallélisés + cache disque immuable) — c'est
  le seul intérêt d'`agg3`, l'archive y reste pleinement utilisée (profondeur).
  `fetch_open_interest_ohlc()` — **bougies OHLC d'OI**. `fetch_binance_oi_archive()` —
  OI Binance brut (mode `days` ou `start`/`end`). **Métriques tierces pour départager
  longs/shorts** (Binance via Coinalyze, `_coinalyze_history`) : `fetch_funding_rate`,
  `fetch_long_short_ratio` ([ratio, pct_long]), `fetch_liquidations` ([long_liq, short_liq]).
  `fetch_taker_delta()` — **delta agressif par barre** (taker_buy − taker_sell, en coin) depuis
  les klines Binance (col 9 `publicGetKlines`), base du CVD/absorption (proxy **spot**).
  Import ccxt paresseux (tests hors-ligne).
- `screener/features.py` — VSA (`add_features`: spread, CLV, ATR, vol_ratio,
  spread_atr), pivots (`swing_points`), `detect_trading_range` → `TradingRange`.
  `add_absorption(df, delta)` — **effort (CVD) vs résultat (prix)** : `delta_z` (flux net en σ),
  `ret_atr`, `absorption` = `−delta_z·(2·clv−1)` (per-barre ; >0 = flux rejeté, <0 = honnête
  confirmé, signe de delta_z = côté absorbant), **`absorption_w`** (même formule sur `win`=3 barres
  = flux cumulé vs clôture dans le range des 3 dernières → **robuste à la TF**, mais
  **COMPLÉMENTAIRE du per-barre, pas un remplaçant** : backtest BTC = abs_w fiable sur la DEMANDE
  aux creux et les mouvements honnêtes, mais **masque** l'absorption d'OFFRE au sommet d'un rallye
  car le contexte multi-barres haussier domine. **Lire les DEUX** ; un désaccord = absorption
  locale), `no_demand`/`no_supply` (prix qui voyage ≥ `move_atr` ATR avec effort faible). Deux
  divergences OPPOSÉES du 2×2 (absorption ≠ no-demand).
  La plage est calculée sur la fenêtre *avant* les `buffer` dernières barres, pour
  qu'un spring récent soit mesuré contre la plage qui le précède.
- `screener/events.py` — `detect_events` : SPRING, UTAD, SC, BC, SOS, SOW, ST,
  LPS, LPSY. Seuils dans `Thresholds` (mappés depuis config.yaml).
- `screener/score.py` — `score_symbol` : biais dominant, phase, score composite
  = poids_type × force × récence (demi-vie 4 barres).
- `screener/mtf.py` — `combine_mtf` : confluence HTF (contexte) × LTF (déclencheur).
  Multiplicateur 1.5 / 1.25 / 1.0 / 0.5.
- `screener/backtest.py` — walk-forward sans lookahead. `backtest_features` (coeur
  réutilisable, fenêtre [entry_start, entry_end)), `backtest_symbol`, `aggregate`.
  Entrée à la clôture de t sur déclencheur frais (bars_ago==0), stop ATR + objectif R.
- `screener/optimize.py` — grid-search des seuils. `grid_search` (split IS/OOS),
  `metric_value` (robust = espérance − z·erreur-type ; plancher min_trades),
  `overfit_report` (verdict robuste/fragile/surajustement), `walk_forward` (k plis).
  Features calculées une fois par symbole puis réutilisées sur toute la grille.
- `screener/window.py` — `detect_window_structure` : reconnaît une *séquence* Wyckoff
  ordonnée (Phase A→D) sur une fenêtre glissante (défaut 60 barres), indépendamment des
  bornes de la grande plage. Accumulation : SC→AR→ST→**SPRING**→SOS→**LPS** ;
  distribution : BC→AR→ST→**UTAD**→SOW→**LPSY** (tous optionnels sauf le climax + un
  signe/test). Complète `events.py` qui ne réagit qu'aux bornes sur les `buffer` dernières
  barres. Chaque `WindowEvent` porte `why` (justification volume+spread) et `theory`.
  Détection (ordre interne) : climax → **AR** (rebond réflexe *immédiat*, horizon court,
  on s'arrête dès que l'extrême cale ; validé seulement si volume EN REPLI <1× **et OI en
  repli** si dispo — un rebond volumique/à OI montant est un SOS, pas un AR) → **SOS/SOW**
  (1ʳᵉ poussée large+volumique = *jump across
  the creek* ; détecté avant l'ST/Spring pour les borner en Phase B) → **ST** & **SPRING/
  UTAD** (entre AR et signe) → **LPS/LPSY** (back-up à volume sec après le signe, tenant le
  bon côté de la borne). Événements triés par horodatage avant rendu. `detect_window_structure`
  accepte un `oi` (Open Interest) réaligné sur les barres : confirme l'AR (débouclage → OI
  en repli) et annote `WindowEvent.oi_chg` (ΔOI % sur ~3 barres). `--no-oi` pour désactiver.
- `screener/plot.py` — `plot_window_structure` : rendu PNG d'une structure, **3 panneaux**
  (cours / volume / Open Interest). Bougies **dans la MÊME TF que l'analyse** (H4→bougies H4,
  etc. — pas de TF inférieure). Bornes : **plancher = climax (SC), plafond = AR** (miroir en
  distribution : plafond = BC, plancher = AR ; sans AR → extrême de séquence). Marqueurs sur
  l'extrême réel de la barre (`_wanted_extreme` : SC/ST→creux, AR/SOS→sommet). Panneau
  **volume** : barres + **moyenne (vol MA)** + **étiquette de chaque événement** (nom +
  ×vol_ratio). Panneau **OI** : bougies d'OI agrégé (`fetch_open_interest_ohlc`, source
  `agg3`) **à la MÊME TF que le cours** (vert = OI↑, rouge = OI↓), omis si OI indispo. Traits
  verticaux d'événement (teintés) sur les 3 panneaux. Horodatage en CEST.
- `screener/cli.py` — orchestration + sortie tableau/CSV ; `--mtf` → run_mtf,
  `--window [N]` → run_window (table avec colonnes théorie + volume/spread→thèse),
  `--chart` génère le PNG.
- `screener/theory_table.py` — `build_theory_html` : mémo « Mémo théorie » (**HTML
  cliquable**) listant, pour accumulation ET distribution, le rôle de chaque événement et
  ses seuils de validité (vol×, spread ATR, clôture) **+ le comportement d'OI attendu**.
  Données via `theory_rows(bias, th)` (seuils lus depuis `Thresholds`, jamais en dur).
  `run_window` le régénère à chaque analyse (`memo_theorie.html`).

## Conventions
- Gauthier préfère une sortie tabulaire stricte, sans prose superflue.
- Heuristiques transparentes et ajustables, jamais de boîte noire.
- Tout nouveau détecteur doit venir avec un test synthétique dans `tests/`.
- **Classification Wyckoff = TOP-DOWN, jamais bottom-up.** Avant toute lecture de séquence,
  établir le **contexte macro** (trend HTF Daily/H4, position de la plage) — c'est lui qui
  décide accu-vs-distrib (une plage après baisse = accumulation *ou* redistribution). **Par
  défaut, une plage dans un downtrend = redistribution** jusqu'à preuve du contraire (la
  continuation prime sur le retournement). Conséquences : (1) tenir **les deux scénarios** en
  parallèle jusqu'à la cassure de la plage ; (2) étiqueter les événements **conditionnellement**
  (« test de résistance = SOS *ou* UTAD selon tenue ») et non fermement avant que le schéma soit
  confirmé ; (3) un **breakout n'est un SOS qu'après tenue + back-up (LPS)** au-dessus — sinon
  c'est une *tentative* (possible upthrust) ; (4) lire l'**OI à travers le cadre + le lieu**
  (OI↑ à la résistance dans un downtrend = demande qui se fait *piéger*, pas signal haussier) ;
  (5) **re-questionner le cadre** dès que le prix fait l'inattendu (un aller-retour = signal de
  réévaluation). Ne jamais *présumer* l'accumulation : il faut la *gagner*.
- **Wyckoff est FRACTAL — séparer les échelles.** Chaque TF a son **schéma complet** : une
  consolidation locale (ex. H1) est une **structure entière** (BC/AR/ST/UTAD/SOW propres) qui,
  sur la TF supérieure (H4/D1), n'est qu'**un seul événement** (ex. un test de Phase B). La
  **même bougie** peut donc être un **BC local** (cadre H1) *et* un **test de Phase B macro**
  (cadre H4) — les deux sont vrais. Règles : (1) **déclarer la TF/structure** avant d'étiqueter ;
  (2) étiqueter **relativement à la plage de CETTE structure** (un BC/UTAD local ≠ ceux de la
  macro ; un BC n'est pas forcément le plus-haut absolu, juste le climax de l'avance *analysée*) ;
  (3) un **UTAD peut dépasser le BC** (plus-haut marginal pour piéger — normal) ; (4) **quand
  Gauthier fixe une TF + fenêtre, analyser à CETTE échelle d'abord**, la TF supérieure servant de
  *contexte/biais* sans écraser les étiquettes locales ; (5) **cartographier l'emboîtement**
  (la structure locale exécute une sous-phase de la supérieure) ; la **confluence** local↔macro
  donne le signal le plus fort. Ne pas plaquer les étiquettes macro sur une analyse locale.
- **AR/ST sont ANCRÉS sur le climax — cohérence de cadre obligatoire.** L'AR part toujours
  dans le sens **opposé** au climax, et l'ST **reteste le climax** :
  - **Accumulation** (climax = **SC**, bas) : **AR** rebondit **vers le HAUT** → fixe la **borne
    haute** ; **ST** reteste **vers le bas** (le SC) → borne basse.
  - **Distribution** (climax = **BC**, haut) : **AR** réagit **vers le BAS** → fixe la **borne
    basse** ; **ST** reteste **vers le HAUT** (le BC) → **borne haute** (un lower high qui cale
    sous le BC = offre confirmée).
  **Erreur à NE PLUS refaire** : importer la grammaire d'accumulation (climax-bas = « SC » →
  rallye = « AR-haut ») dans une structure qu'on a classée **distribution**. Dans un cadre
  distribution, un **climax-bas suivi d'un rallye** se lit **AR-bas (borne basse) puis ST-haut
  (test de la borne haute)** — JAMAIS « SC puis AR ». Avant d'étiqueter un rebond « AR », se
  demander : *quel climax l'ancre, et de quel côté ?* Si le cadre est distribution, le test de
  la résistance est un **ST/UTAD**, pas un AR. Tenir les deux jeux d'étiquettes en parallèle
  tant que la plage n'est pas cassée (cf. top-down), mais ne jamais **mélanger** les deux
  grammaires dans un même cadre committé.
  - **L'OI sur le rebond DÉSAMBIGUÏSE accumulation vs redistribution — c'est toute la nuance du
    début.** Le prix seul ne distingue pas les deux : il faut lire **QUI porte le rebond** via
    l'OI coin. Décomposer le rebond climax→test en phases :
    · **prix↑ + OI↓ = short covering** = « rebond effectif » : les shorts du markdown se
      rachètent, la pression vendeuse s'épuise. **Constructif / AMBIGU — ne confirme PAS la
      distribution** (penche même vers l'accumulation : le carburant baissier se retire).
    · **prix↑ + OI↑ = nouveaux longs** : demande qui entre. Au **test de la résistance** dans un
      downtrend = **demande piégée** = signature **redistribution** (ces longs deviennent le
      carburant du markdown suivant, liquidés ensuite).
    La distribution n'est **confirmée** que si le test de la borne haute est porté par des
    **nouveaux longs (OI↑) qui échouent**, suivi de la cassure. Un rebond entièrement en
    covering (OI↓) laisse le scénario **ouvert**. Ex. BTC H8 15/06 : rebond AR-bas→ST en 2
    phases — Phase 1 covering (prix +4,1 % / OI −3,4 %, ambigu) puis Phase 2 new longs (prix
    +5,8 % / OI +6,8 %, piégés au test) → redistribution gagnée à la cassure du 24/06. Toujours
    annoter ces phases sur le panneau OI quand un rebond porte la décision accu-vs-distrib.
- **Ordre d'analyse imposé (hiérarchie VSA) : volume → OI → métriques tierces.** Toute lecture
  de suivi se fait *dans cet ordre* : (1) le **volume/spread** d'abord (la force primaire :
  effort vs résultat, vol×, clôture/CLV) ; (2) puis l'**OI** (le volume ouvre-t-il ou ferme-t-il
  des positions ?) ; (3) puis, **seulement quand nécessaire** (OI ambigu / prix qui cale), les
  **métriques tierces** (ratio long/short, funding, liquidations). Ne jamais sauter au tertiaire
  avant d'avoir lu volume puis OI. **Synthèse :** une fois l'ordre respecté, **lire OI coin +
  tierces ensemble** comme un tout cohérent (en dégager un *sens commun*) plutôt que de les
  lister séparément — ex. « prix↑ + OI coin↑ + shorts liquidés + funding contenu = vraie
  demande qui squeeze les shorts ». Le volume reste traité en premier (force primaire).
  **Lecture FROIDE, jamais orientée vers la thèse** : le « sens commun » n'est pas un outil
  pour *valider* ce qu'on veut voir. Si les tierces **contredisent ou affaiblissent** la thèse
  établie par volume+OI, le **relater explicitement** comme **risque / invalidation partielle**
  (ex. « le tableau penche distribution, MAIS funding négatif + crowd déjà short = carburant
  haussier latent, la thèse est fragilisée »). Ne jamais tordre les tierces pour forcer le
  consensus : une divergence tierce **est** un signal, pas un bruit à gommer.
- **Niveaux toujours justifiés** : chaque prix-clé cité (déclencheur, stop, objectif,
  invalidation) doit être **accompagné, entre parenthèses, de la raison qui en fait un niveau
  clé** (ex. « 62 272 (plancher = low du SC, borne basse de la plage) », « 62 500 (haut du coil
  5m, l'offre y plafonne les rebonds) »). Jamais un chiffre nu : Gauthier veut savoir *pourquoi
  ce niveau* — quel événement Wyckoff, quelle borne, quel comportement volume/OI le définit.
- **OI en COIN, jamais en USD, pour lire les positions.** L'OI en USD = OI_coin × prix
  **conflate positions et prix** : une hausse de prix gonfle l'OI USD même quand les positions
  *baissent* → faux signal *précisément quand le prix bouge* (ex. cassure BTC 64 800 : OI USD
  +0.81 % « demande » alors que l'OI coin faisait −0.36 % = **short covering**). Toujours lire
  la **direction** de l'OI en **coin** (`fetch_open_interest`/`_ohlc` défaut `usd=False`,
  Coinalyze `convert_to_usd=false`) — c'est ce qu'affiche TradingView (« Intérêt ouvert » en
  BTC). L'USD ne sert qu'à donner un ordre de grandeur de notional, jamais à lire un Δ.
  **En coin, le *signe* est fiable** → on prend en compte les **petits Δ** (pas de seuil de
  bruit) en les pesant par leur **cohérence** : une dérive suivie sur plusieurs barres (ex.
  −0.05/−0.07/−0.12 % = short covering réel) compte, une barre isolée minuscule moins.
- **OI ambigu → croiser systématiquement 3 métriques tierces.** Prix+OI seuls sont
  **ambigus quand le prix cale** (OI↑ à prix plat = longs *ou* shorts qui ouvrent — impossible
  à trancher). Dans **toute lecture d'OI**, dès que le prix stagne / qu'une hausse d'OI doit
  être attribuée, croiser avec : **ratio long/short** (`fetch_long_short_ratio` — ratio↓ = des
  shorts entrent), **funding** (`fetch_funding_rate` — positif = longs majoritaires/paient),
  **liquidations** (`fetch_liquidations` — long_liq vs short_liq ; ≈0 = mouvement ordonné, pas
  de flush forcé). Ne jamais affirmer « longs piégés / shorts qui pressent » sur le seul couple
  prix+OI : confirmer avec ces tells (toutes Binance via Coinalyze, mêmes clé/repli que l'OI).
- **CVD (Cumulative Volume Delta) — tierce d'ABSORPTION, lue en première parmi les tierces.**
  Le CVD = somme cumulée du delta (acheteurs agressifs − vendeurs agressifs), où le delta par
  barre = `taker_buy − taker_sell` (taker_buy = col 9 des klines Binance `publicGetKlines`,
  taker_sell = volume total − taker_buy). C'est du **flux d'ordres agressifs** → la tierce la
  plus proche du volume primaire, donc **traitée en tête des tierces** (avant funding/L-S/liq).
  **Job unique : détecter l'absorption via la divergence prix↔CVD** :
  · **prix↑ + CVD plat/↓** = hausse sans demande agressive (passive/covering) → **offre absorbe
    la demande = signe de distribution / faiblesse** ;
  · **prix↓ + CVD plat/↑** (ou grosse vente agressive mais prix qui tient/récupère) = **demande
    absorbe l'offre = signe d'accumulation / absorption au plancher** ;
  · **prix et CVD en phase** = mouvement « honnête », **pas d'absorption, signal non concluant**.
  **Quantifié** via `features.add_absorption(df, fetch_taker_delta(...))` : colonne `absorption`
  (`−delta_z·(2·clv−1)`, >0 = flux rejeté ; delta_z<0 = demande absorbe (haussier), delta_z>0 =
  offre absorbe (baissier)) + **`absorption_w`** (version 3 barres, stable d'une TF à l'autre —
  ex. SC 58 115 : abs per-barre −0.68 (H8) à −3.85 (H1) mais `absorption_w` +0.18→+0.41 homogène).
  **Citer les DEUX, complémentaires** (backtest BTC) : per-barre = rejet d'**une** bougie (fiable
  100% des deux côtés mais fragile à la TF) ; `absorption_w` = contexte multi-barres robuste à la
  TF (fiable sur DEMANDE/honnêtes, mais **masque l'absorption d'OFFRE au sommet d'un rallye**).
  **Formule prouvée symétrique** (test miroir, écart 10⁻¹³ : aucun bug de signe) — la fenêtre
  dilue un rejet isolé dans une tendance forte des DEUX côtés ; ça touche plus l'offre car les
  rallyes BTC sont plus directionnels (~+1 ATR) que les descentes (~−0.5 ATR). À un sommet, lire
  le per-barre. Désaccord (per-barre >0, abs_w <0) = absorption **locale** dans un mouvement de fond. Plus
  `no_demand`/`no_supply` (prix qui voyage sans flux = l'**autre** divergence). Citer la valeur
  et/ou le flag event par event. Lecture **froide** (cf. tierces) : confirme / affaiblit / renforce une
  thèse, **ou rien d'exploitable** — ne jamais forcer. **Caveat** : CVD calculé en **spot** (miroir vision ; perp
  `fapi` 451-bloqué) = proxy du flux ; une divergence **CVD spot vs OI perp** est elle-même
  lisible (spot achète / perp déboucle). Ex. BTC H8 : rallye 59 131→67 292 = prix +6 236 / CVD
  +1 023 (rallye sans demande agressive → confirme distribution) ; barre SC 58 115 = vente
  agressive (delta −1 822) mais prix qui récupère (absorption au plancher → affaiblit la
  continuation baissière). **Fuseau horaire — OBLIGATOIRE de vérifier** : `publicGetKlines`
  renvoie les **mêmes open times UTC réel** que `fetch_ohlcv` (vérifié : timestamps + close
  identiques bougie par bougie, écart 0) → appliquer le **même décalage +2h** (`index += 2h`,
  tz=UTC) qu'au prix et à l'OI. Ne jamais laisser le CVD sur un fuseau différent : une barre
  CVD décalée fausse la lecture de divergence. Toujours réaligner sur l'index des bougies prix.
- **Illustration d'une analyse** (préférences Gauthier) :
  - **TOUJOURS afficher le graphe via l'outil Read sur le PNG — sans exception.** En session
    distante/web, c'est l'**ouverture du PNG avec Read** qui l'affiche **en GRAND directement
    dans le fil** ; `SendUserFile` ne le livre qu'en **pièce jointe plus petite**. Donc pour
    CHAQUE graphe, à CHAQUE fois : (1) **Read le PNG** → grand rendu inline (obligatoire,
    systématique, jamais omis — c'est ce qui le rend grand) ; (2) **SendUserFile** le même PNG
    → version téléchargeable. **Ne JAMAIS se contenter de SendUserFile seul** (sinon le graphe
    reste petit). Le Read inline n'est pas optionnel : c'est la règle par défaut pour tout
    graphe livré. Pas de lien cliquable `[texte](...)`.
  - **Bougies dans la MÊME TF que l'analyse** (analyse H4 → bougies H4, H1 → bougies H1).
  - **Fenêtre : minimum 80 bougies** (du contexte autour de la zone analysée), quitte à ne
    commenter qu'une **partie plus récente** du graphe. **TF choisie librement** selon ce qui
    est le plus pertinent pour la lecture.
  - **PAS de code couleur emoji dans le texte** (🟢🔴🔵🟣🟠🟩🟥 etc. bannis du corps de
    l'analyse). Les couleurs restent sur le graphe uniquement (marqueurs, flèches, traits
    verticaux). Dans le texte, nommer directement l'événement sans pastille.
  - **Alignement des étiquettes** (bug récurrent des scripts ad hoc) : les bougies sont
    décalées +2h en gardant `tz=UTC` ; les timestamps d'événements doivent l'être *aussi*
    (`pd.Timestamp('HH:MM', tz='UTC')` = heure CEST étiquetée UTC), JAMAIS `+02:00` (que
    matplotlib reconvertit → étiquette 2 bougies trop à gauche). Vérifier l'alignement.
  - Toujours : panneau **volume avec moyenne (vol MA) + étiquettes d'événements** (nom +
    ×vol_ratio), et panneau **OI à la MÊME TF que le cours** (jamais une TF d'OI différente).
  - **Panneau OI = BOUGIES OHLC, jamais une ligne.** L'OI se trace en **chandeliers de la
    MÊME TF que le cours** (vert = OI↑ sur la barre, rouge = OI↓), comme `plot.py`. Source
    `fetch_open_interest_ohlc` (défaut coin, `usd=False`). Pour la profondeur historique
    (archive Binance en USD), **construire les bougies d'OI en coin** (O/H/L/C de l'OI_coin
    sur chaque barre, OI_coin = OI_usd / prix) — ne jamais se contenter d'une courbe lissée.
  - **Export PNG = RGB haute résolution** (clic-pour-agrandir fiable côté web). Toujours :
    `savefig(..., dpi=200, bbox_inches='tight', facecolor='white')` **puis aplatir
    RGBA→RGB sur fond blanc via PIL** (un PNG en RGBA n'active pas toujours le zoom au clic).
    Vérifier `Image.open(...).mode == 'RGB'` avant de livrer.
  - Pour chaque événement détecté : expliquer *pourquoi le volume et le spread*
    confirment la thèse, et rappeler ce que dit la théorie sur cet événement dans le
    schéma (accumulation / distribution) — colonne dédiée.
  - La colonne « théorie » est un **mémo d'apprentissage** : elle inclut les *seuils
    de volume/spread attendus* en théorie pour chaque événement (climax ≥ ×climax_vol,
    test ≤ ×test_vol, SOS/SOW ≥ ×sos_vol, spread vs wide_spread_atr). Texte généré par
    `window._theory(bias, name, th)` à partir des `Thresholds` courants — but : développer
    des automatismes de lecture event par event.
  - **Mémo théorie** : à *chaque* demande d'analyse, **livrer obligatoirement** dans le fil
    le **HTML cliquable** (`theory_table.build_theory_html` → `memo_theorie.html`) via
    SendUserFile — rôle + seuils de validité (vol×, ATR, clôture) + OI attendu de chaque
    événement, accumulation et distribution. Ce mémo est le référentiel pour confronter les
    observations du tableau aux seuils théoriques. **À la fin de chaque analyse**, rappeler
    en une phrase ce que ce mémo permet de vérifier pour CETTE structure spécifique (ex.
    « Le mémo théorie est joint — il permet ici de vérifier les seuils vol× qui distinguent
    un vrai SOS d'un faux SOS / covering »). Ne pas juste "proposer" de s'y référer :
    le livrer systématiquement.

## Format canonique des analyses Wyckoff texte

Structure imposée pour toute analyse Wyckoff manuelle (ad hoc ou sur demande).
**Gauthier valide ce format** — ne jamais en dévier sans raison explicite.

### Mots-clés déclencheurs
Le format complet (graphe bougies OI + mémo théorie + 5 sections) se déclenche dès que la
demande contient **« analyse wyckoff » / « analyse de la séquence »** sur un actif. Forme
canonique : **`analyse wyckoff [ACTIF] [TF] [depuis quand]`** (ex. « analyse wyckoff BTCUSDT
H8 depuis 02/06 »). Les 3 paramètres utiles :
- **Actif** (obligatoire) — BTCUSDT.P, XAU, VELVET…
- **TF** (optionnel) — H8, H1, 5m, 3m… ; à défaut, choisir celle qui colle le mieux à la lecture.
- **Fenêtre / point de départ** (optionnel) — « depuis 02/06 », « depuis 16h » ; à défaut,
  remonter au début de structure pertinent (≥ 80 bougies).

**Distinguer du suivi rapide** : une simple question d'état (« où en est BTC », « réactualise
sur la dernière bougie », « le niveau X tient ? ») n'est PAS une analyse de séquence → réponse
courte, sans dérouler les 5 sections ni regénérer le mémo. Le format lourd est réservé aux
**analyses de séquence**.

### Livrables dans le fil
1. PNG du graphe (via SendUserFile — jamais un lien cliquable)
2. HTML mémo théorie (via SendUserFile — `memo_theorie.html`)

### Corps de l'analyse — sections numérotées dans cet ordre

**Titre en en-tête** : `ACTIF TF — description courte de la séquence et des dates`

**1. Contexte macro (top-down)**
Toujours en premier, avant toute étiquette. Identifier :
- Tendance HTF (Daily/H4) : plus-hauts/plus-bas, sommet de référence, amplitude du markdown
- Position dans le cycle : la plage est-elle après montée ou après baisse ?
- Classification par défaut : redistribution si downtrend, à défaut de preuve contraire
- Conséquence sur les étiquettes (conditionnel tant que la plage n'est pas cassée)

**2. Lecture événement par événement**
Tableau obligatoire. Chaque ligne confronte ce qui est observé aux seuils théoriques de
l'événement (vol×, spread/ATR, CLV attendus selon `Thresholds`). La colonne "Lecture" doit
dire : (a) ce que la théorie attend pour cet événement, (b) ce qu'on observe, (c) si c'est
validé ou non. C'est le cœur pédagogique : développer les automatismes event par event.

Colonnes selon disponibilité des données :

— VSA pur (OI indisponible, ex. XAU) :
`Événement | Heure CEST | Prix | vol× | spread/ATR | CLV | Lecture VSA`

La colonne "Lecture VSA" inclut systématiquement : seuil théorique attendu pour cet
événement (ex. SC : vol ≥ climax_vol×, spread large, clv ≤ 0.3 pour capitulation pure) +
valeur observée + verdict (validé / ambigu / non validé).

— Avec OI (ex. BTC via Coinalyze) :
`Événement | Heure CEST | Prix | vol× | spread/ATR | CLV | Volume + OI = sens`

La colonne "Volume + OI = sens" dit la signature théorique attendue (ex. AR : OI en repli
attendu = débouclage) + ce qu'on observe + interprétation (covering / nouveaux longs /
nouveaux shorts / liq forcée).

Le **CVD** ne va PAS dans le tableau événement (c'est une tierce) : il est lu après, en
section "Confirmation tierce" (1. CVD/absorption), pour confirmer/affaiblir les lignes ci-dessus.

**Confirmation tierce — deux lectures froides** (après le tableau, quand OI ambigu ou quand
les tierces ont été consultées). Vient *en second temps* valider / affaiblir / renforcer les
hypothèses du tableau — ou conclure qu'il n'y a rien d'exploitable.

1. **CVD / absorption** (flux d'ordres agressifs, lu en premier car le plus proche du volume).
   **Hors du tableau événement** (sinon il devient co-primaire et casse l'ordre volume→OI→tierces
   + le tableau s'alourdit + le delta 1 barre est bruité), mais structuré en **mini-liste
   event-ancrée** — PAS un paragraphe global. Pour chaque événement où le CVD parle, une ligne :
   `Événement — théorie (CVD attendu) — observé (Δ CVD / divergence) — verdict`.
   Attentes théoriques par event :
   · **SC/climax** : vente agressive massive (CVD↓ fort) **mais** absorption (prix qui récupère)
     = climax absorbé → constructif ;
   · **SOS** : exige **CVD↑ franc** (demande agressive) ; un SOS sans CVD↑ = covering, faux SOS ;
   · **SOW** : **CVD↓ franc** en phase avec le prix = offre agressive réelle ;
   · **UTAD / upthrust** : prix↑ **mais CVD plat/divergent** = pas de demande = piège confirmé ;
   · **AR / ST** : CVD plat/modeste attendu (réflexe, pas d'agression).
   **Chiffrer avec `add_absorption`** (cf. `data.fetch_taker_delta` + `features.add_absorption`,
   même décalage +2h que le prix) : citer pour chaque event la valeur `absorption` (>0 = flux
   rejeté ; signe de delta_z = côté) **OU** le flag `no_demand`/`no_supply` (prix qui voyage sans
   flux — l'autre divergence, que l'absorption ne voit pas). Toujours distinguer les deux :
   *absorption* = effort fort rejeté ; *no-demand* = résultat fort sans effort.
   La divergence décisive est souvent **multi-barres** (sur un swing), pas 1 bougie — la signaler
   comme telle (per-barre l'absorption est bruitée). Conclure chaque ligne par l'un des 4 cas :
   **confirme distrib / confirme accu / affaiblit / rien d'exploitable**. CVD = spot (proxy).

2. **Positionnement — synthèse en sens commun** (funding, ratio L/S, liquidations) :
   ne pas lister séparément. Les lire ensemble pour un sens unique en une ou deux phrases : ex.
   « Liquidations nulles des deux côtés + funding négatif + crowd 68% long = rebond en covering
   volontaire, pas un squeeze forcé — longs encombrés = fragilité dominante ».

Les tierces confirment ou infirment ce que le tableau a établi ; elles ne s'y substituent pas,
et se lisent **à froid** (cf. interdits : ne jamais tordre une tierce pour forcer le consensus).
**Lecture froide, pas de biais de confirmation** : l'objectif n'est PAS de faire converger les
tierces vers la thèse. Trois cas à traiter honnêtement : (a) elles **confirment** → on renforce ;
(b) elles **affaiblissent** → relater le risque (« la thèse tient mais X la fragilise ») ;
(c) elles **contredisent** → relater l'**invalidation possible** depuis l'angle tierce, et
réévaluer. Forcer le consensus = faute. Une tierce divergente est un signal à part entière.

Chaque ligne = un seul événement, lecture factuelle et concise.

**3. Note fractale**
Comment cette structure locale (LTF) s'insère dans la TF supérieure.
Préciser : quelle sous-phase macro elle représente. Ne pas plaquer les étiquettes macro.

**4. Synthèse** (ou "Structure identifiée")
- Séquence identifiée : SC → AR → ST → … (Phase A/B/C/D selon avancement)
- Biais directionnel et degré de conviction (avec la raison)
- Si verdict impossible : dire explicitement "trop tôt — attendre [tel signal]"

**5. Niveaux (justifiés)**
Bullet points — format : `prix (raison qui en fait un niveau clé)`. Toujours inclure :
- Plafond (résistance, AR, rejet)
- Support interne / pivot
- Plancher (SC low, borne basse confirmée)
- Stop (au-dessus/en dessous de quel événement Wyckoff, et pourquoi)
- Cibles (avec les étapes intermédiaires)
- Invalidation (ce qui remettrait en cause le biais)

**Fin de chaque analyse** : rappeler en une phrase ce que le mémo théorie permet de
vérifier pour CETTE structure spécifique (ex. « Le mémo théorie est joint — utile ici
pour vérifier les seuils vol× qui distinguent un vrai SOS d'un covering »).

### Ce qui est interdit dans le format
- Code couleur emoji dans le texte (🟢🔴 etc.)
- Niveaux sans justification entre parenthèses
- Étiquetter l'accumulation sans preuve (toujours "à gagner")
- Sauter la section contexte macro
- Analyser bottom-up (étiquettes avant cadre)
- Omettre le mémo théorie HTML (livré à chaque analyse, sans exception)
- Décrire un événement sans confronter aux seuils théoriques (vol×, spread/ATR,
  CLV, OI attendu) — l'observation seule ne suffit pas, le "validé / ambigu /
  non validé" doit être explicite
- Lister les métriques tierces en bullets séparés : elles se lisent ensemble
  pour produire un sens commun en une phrase synthèse
- Tordre les tierces pour forcer le consensus de la thèse : si elles affaiblissent
  ou contredisent, relater le risque / l'invalidation (lecture froide, pas de
  biais de confirmation)

## Commandes
```bash
pip install -r requirements.txt
python -m screener.cli --timeframe 4h --bias both
python -m screener.cli --timeframe 1h --symbols BTC/USDT --window --chart   # séquence + PNG (fenêtre défaut 60)
python -m screener.optimize --timeframe 1h --metric robust   # ou --walk 4
pytest -q
```

## TODO candidats
- Coûts de transaction (frais + slippage) dans le backtest/optimiseur
- Alertes webhook sur nouveau setup (Telegram/Discord)
- Filtrage des setups live par la combinaison validée en OOS
