# CLAUDE.md — contexte projet

Screener Wyckoff crypto (accumulation/distribution), H1/H4, via ccxt.
Aide à la décision discrétionnaire — **jamais** d'exécution d'ordres automatique.

## Architecture
- `screener/data.py` — ccxt : `build_universe()` (top paires USDT par volume),
  `fetch_ohlcv()` avec cache parquet. `get_exchange("binance")` route les endpoints
  publics vers le miroir `data-api.binance.vision` (spot, non géo-restreint).
  `fetch_open_interest()` — historique d'OI (perp) **agrégé multi-venues** (valeurs USD
  sommées). `source=agg3|agg|okx|gate` : `agg`=OKX+Gate ; **`agg3`** (défaut CLI) ajoute
  l'**OI Binance** via l'archive `data.binance.vision` (metrics 5m, non géo-bloqué ;
  `fapi`/Bybit le sont) + un point **CoinGecko** courant pour combler le retard ~1j, avec
  **repli auto** sur `agg` si l'archive tombe. Fusion via `_combine_oi` (carry → pas de
  « falaise »). `start`/`end` ciblent l'OI Binance d'un **intervalle historique** (ex. mars)
  via les quotidiens d'archive (téléchargements parallélisés + cache disque immuable).
  `fetch_open_interest_ohlc()` — **bougies OHLC d'OI agrégé**. `fetch_binance_oi_archive()` —
  OI Binance brut (mode `days` ou `start`/`end`). Import ccxt paresseux (tests hors-ligne).
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
- **Illustration d'une analyse** (préférences Gauthier) :
  - Embarquer le graphique *inline* dans la réponse avec `![alt](chemin.png)` (pas de
    lien cliquable `[texte](...)`). En session distante/web, **livrer le PNG directement
    dans le fil** (outil d'envoi de fichier) — Gauthier veut le voir sans cliquer.
  - **Bougies dans la MÊME TF que l'analyse** (analyse H4 → bougies H4, H1 → bougies H1).
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
