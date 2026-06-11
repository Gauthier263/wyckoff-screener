# CLAUDE.md — contexte projet

Screener Wyckoff crypto (accumulation/distribution), H1/H4, via ccxt.
Aide à la décision discrétionnaire — **jamais** d'exécution d'ordres automatique.

## Architecture
- `screener/data.py` — ccxt : `build_universe()` (top paires USDT par volume),
  `fetch_ohlcv()` avec cache parquet. Import ccxt paresseux (tests hors-ligne).
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
  ordonnée (SC→AR→ST→SOS en accumulation, BC→AR→ST→SOW en distribution) sur une
  fenêtre glissante (défaut 30 barres), indépendamment des bornes de la grande plage.
  Complète `events.py` qui ne réagit qu'aux bornes sur les `buffer` dernières barres.
  Chaque `WindowEvent` porte `why` (justification volume+spread calculée sur la barre)
  et `theory` (rappel théorique, dict `THEORY`). AR cherché sur horizon borné après le
  climax (sinon il attrape l'extrême du SOS/SOW final).
- `screener/plot.py` — `plot_window_structure` : rendu PNG d'une structure. Dessine les
  bougies sur une **TF inférieure** que l'analyse (`FINER_TF` : H4→H1, H1→15m, 15m→5m).
  Bornes : **plancher = climax (SC), plafond = AR** (c'est l'AR qui le définit), miroir
  en distribution (plafond = BC, plancher = AR). Les marqueurs sont *recalés sur
  l'extrême réel* de chaque barre d'analyse, retrouvé dans les bougies fines de la
  période (`_wanted_extreme` : SC/ST→creux, AR→sommet, SOS→cassure) → alignement exact
  creux/cassure. Le panneau volume étiquette chaque événement (nom + ×vol_ratio) avec
  lignes-guides verticales. Horodatage en CEST.
- `screener/cli.py` — orchestration + sortie tableau/CSV ; `--mtf` → run_mtf,
  `--window [N]` → run_window (table avec colonnes théorie + volume/spread→thèse),
  `--chart` génère le PNG.

## Screener multi-cours (`python -m screener.scan`)
Couche de *présélection* par-dessus le moteur Wyckoff : balaie un univers fixe
(crypto + actions + matières premières) et remonte les cours dont une formation
acc/dist est **déjà validée par de premiers événements**, propice à une prise de
position. Aide discrétionnaire, pas d'exécution.
- `screener/universe.py` — univers (données seules) : 46 cryptos, 90 actions, 8 MP.
  Tickers selon la source : ccxt `BASE/USDT` (crypto) / Yahoo (`-USD`, parfois suffixé
  d'un id numérique ; actions ; futures MP `=F`). `TF_BY_CLASS` : crypto **4h×1h**,
  actions/MP **1D×4h** (Wyckoff actions = daily ; sessions 6h30 + gaps faussent l'intraday).
  `EXCLUDED` liste les demandés écartés (OpenAI/Infleqtion non cotés, microcaps absents).
- `screener/sources.py` — couche données multi-sources (réutilise `data.py`, n'y touche
  pas). Route crypto→ccxt, actions/MP→Yahoo. Yahoo n'a pas de 4h natif → `resample_ohlcv`
  (1h→4h). `get_spot_exchange` rend **Binance joignable depuis le cloud** : endpoints
  publics routés vers le mirror `data-api.binance.vision` (api.binance.com = HTTP 451
  géo-bloqué), `session.trust_env=True` (sinon SSLError : la CA du proxy TLS est dans le
  bundle système, pas dans certifi), marchés **spot only** (fapi/dapi restent 451).
- `screener/scan.py` — orchestration MTF + ranking. Validité minimale = **Climax+AR+ST**
  (plus strict que `window.is_valid`). `_volume_ok` écarte les actifs à trop de barres
  volume=0 (Yahoo crypto intraday ≈50 % de zéros → VSA inexploitable, d'où ccxt obligatoire
  pour le crypto). Fiabilité = (w_climax·climax + w_test·test + w_complétude) × récence ×
  confluence MTF (1.5/1.25/1.0/0.5). Phase B→C (entrée spring) vs D (entrée LPS/LPSY).
  Pas de R:R pour l'instant (TODO). Tests : `tests/test_scan.py`.
  ```bash
  python -m screener.scan                       # univers complet (crypto ccxt + actions/MP Yahoo)
  python -m screener.scan --classes crypto      # crypto seul, 4h×1h, vrais volumes Binance
  python -m screener.scan --bias accumulation --source yahoo
  ```

## Conventions
- Gauthier préfère une sortie tabulaire stricte, sans prose superflue.
- Heuristiques transparentes et ajustables, jamais de boîte noire.
- Tout nouveau détecteur doit venir avec un test synthétique dans `tests/`.
- **Illustration d'une analyse** (préférences Gauthier) :
  - Embarquer le graphique *inline* dans la réponse avec `![alt](chemin.png)` (pas de
    lien cliquable `[texte](...)`).
  - Bougies en TF inférieure à l'analyse : analyse H1 → bougies 15m, analyse H4 →
    bougies H1 (voir `FINER_TF`).
  - Pour chaque événement détecté : expliquer *pourquoi le volume et le spread*
    confirment la thèse, et rappeler ce que dit la théorie sur cet événement dans le
    schéma (accumulation / distribution) — colonne dédiée.
  - La colonne « théorie » est un **mémo d'apprentissage** : elle inclut les *seuils
    de volume/spread attendus* en théorie pour chaque événement (climax ≥ ×climax_vol,
    test ≤ ×test_vol, SOS/SOW ≥ ×sos_vol, spread vs wide_spread_atr). Texte généré par
    `window._theory(bias, name, th)` à partir des `Thresholds` courants — but : développer
    des automatismes de lecture event par event.

## Commandes
```bash
pip install -r requirements.txt
python -m screener.cli --timeframe 4h --bias both
python -m screener.cli --timeframe 1h --symbols BTC/USDT --window --chart   # séquence + PNG
python -m screener.optimize --timeframe 1h --metric robust   # ou --walk 4
pytest -q
```

## TODO candidats
- Coûts de transaction (frais + slippage) dans le backtest/optimiseur
- Alertes webhook sur nouveau setup (Telegram/Discord)
- Filtrage des setups live par la combinaison validée en OOS
