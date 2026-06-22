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
  Import ccxt paresseux (tests hors-ligne).
- `screener/features.py` — VSA (`add_features`: spread, CLV, ATR, vol_ratio,
  spread_atr), pivots (`swing_points`), `detect_trading_range` → `TradingRange`.
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
- **Ordre d'analyse imposé (hiérarchie VSA) : volume → OI → métriques tierces.** Toute lecture
  de suivi se fait *dans cet ordre* : (1) le **volume/spread** d'abord (la force primaire :
  effort vs résultat, vol×, clôture/CLV) ; (2) puis l'**OI** (le volume ouvre-t-il ou ferme-t-il
  des positions ?) ; (3) puis, **seulement quand nécessaire** (OI ambigu / prix qui cale), les
  **métriques tierces** (ratio long/short, funding, liquidations). Ne jamais sauter au tertiaire
  avant d'avoir lu volume puis OI. **Synthèse :** une fois l'ordre respecté, **lire OI coin +
  tierces ensemble** comme un tout cohérent (en dégager un *sens commun*) plutôt que de les
  lister séparément — ex. « prix↑ + OI coin↑ + shorts liquidés + funding contenu = vraie
  demande qui squeeze les shorts ». Le volume reste traité en premier (force primaire).
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
- **Illustration d'une analyse** (préférences Gauthier) :
  - Embarquer le graphique *inline* dans la réponse avec `![alt](chemin.png)` (pas de
    lien cliquable `[texte](...)`). En session distante/web, **livrer le PNG directement
    dans le fil** (outil d'envoi de fichier) — Gauthier veut le voir sans cliquer.
  - **Bougies dans la MÊME TF que l'analyse** (analyse H4 → bougies H4, H1 → bougies H1).
  - **Fenêtre : minimum 80 bougies** (du contexte autour de la zone analysée), quitte à ne
    commenter qu'une **partie plus récente** du graphe. **TF choisie librement** selon ce qui
    est le plus pertinent pour la lecture.
  - **Code couleur texte↔graphe** : préfixer les mots-clés du texte inline d'une pastille
    de couleur assortie à la couleur de l'élément sur le graphe. **Forme = type** : **ronds
    pour les ÉVÉNEMENTS** (🟢🟠🔵🟣🔴) · **carrés pour les NIVEAUX de prix** (🟩🟧🟦🟪🟥).
    Palette fixe (couleur = sens) : **vert** demande/force (SC, SOS, OI coin↑) · **rouge**
    offre/résistance (BC, SOW, distribution) · **orange** piège/faux signal (faux SOS, UTAD,
    upthrust) · **bleu** bornes de plage / support / repli (LPS) · **violet** spring / pivot /
    Phase C. Mêmes couleurs sur les marqueurs du graphe.
  - **Alignement des étiquettes** (bug récurrent des scripts ad hoc) : les bougies sont
    décalées +2h en gardant `tz=UTC` ; les timestamps d'événements doivent l'être *aussi*
    (`pd.Timestamp('HH:MM', tz='UTC')` = heure CEST étiquetée UTC), JAMAIS `+02:00` (que
    matplotlib reconvertit → étiquette 2 bougies trop à gauche). Vérifier l'alignement.
  - Toujours : panneau **volume avec moyenne (vol MA) + étiquettes d'événements** (nom +
    ×vol_ratio), et panneau **OI à la MÊME TF que le cours** (jamais une TF d'OI différente).
  - Pour chaque événement détecté : expliquer *pourquoi le volume et le spread*
    confirment la thèse, et rappeler ce que dit la théorie sur cet événement dans le
    schéma (accumulation / distribution) — colonne dédiée.
  - La colonne « théorie » est un **mémo d'apprentissage** : elle inclut les *seuils
    de volume/spread attendus* en théorie pour chaque événement (climax ≥ ×climax_vol,
    test ≤ ×test_vol, SOS/SOW ≥ ×sos_vol, spread vs wide_spread_atr). Texte généré par
    `window._theory(bias, name, th)` à partir des `Thresholds` courants — but : développer
    des automatismes de lecture event par event.
  - **Mémo théorie** : à *chaque* demande d'analyse, livrer dans le fil le **HTML
    cliquable** (`theory_table.build_theory_html` → `memo_theorie.html`) — rôle + seuils de
    validité (vol×, ATR, clôture) + OI attendu de chaque événement, accumulation et
    distribution, pour mémoriser ce qui rend un événement valide ou non. À la **fin** de
    chaque analyse, proposer explicitement à Gauthier de pouvoir y référer.

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
