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
  fenêtre glissante (défaut 60 barres), indépendamment des bornes de la grande plage.
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
- `screener/theory_table.py` — `build_theory_html` : mémo « rappel théorie » (HTML
  cliquable) listant, pour accumulation ET distribution, le rôle de chaque événement
  et ses seuils de validité (vol×, spread ATR, clôture). Seuils lus depuis `Thresholds`
  (jamais en dur). `run_window` le régénère à chaque analyse (`tableau_rappel_theorie.html`).

## Conventions
- Gauthier préfère une sortie tabulaire stricte, sans prose superflue.
- Heuristiques transparentes et ajustables, jamais de boîte noire.
- Tout nouveau détecteur doit venir avec un test synthétique dans `tests/`.
- **Illustration d'une analyse** (préférences Gauthier) :
  - Embarquer le graphique *inline* dans la réponse avec `![alt](chemin.png)` (pas de
    lien cliquable `[texte](...)`). En session distante/web, **livrer le PNG directement
    dans le fil** (outil d'envoi de fichier) — Gauthier veut le voir sans cliquer.
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
  - **Tableau rappel théorie** : à *chaque* demande d'analyse, livrer dans le fil le
    mémo HTML cliquable (`theory_table.build_theory_html` → `tableau_rappel_theorie.html`)
    — rôle + seuils de validité (vol×, ATR) de chaque événement, accumulation et
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
