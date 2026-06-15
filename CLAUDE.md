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
  `--void` → `backtest_void_features` : teste la thèse « chute brutale → comblement du
  vide » (entrée LONG à la clôture de la chute, stop ATR, cible = `fill_target` × hauteur
  du vide ; trades étiquetés void_up/void_down selon le gate de tendance). Conclusion
  empirique : l'edge n'existe que **hors downtrend** (void_up), tient en OOS ; void_down =
  couteau qui tombe (à exclure).
- `screener/optimize.py` — grid-search des seuils. `grid_search` (split IS/OOS),
  `metric_value` (robust = espérance − z·erreur-type ; plancher min_trades),
  `overfit_report` (verdict robuste/fragile/surajustement), `walk_forward` (k plis).
  Features calculées une fois par symbole puis réutilisées sur toute la grille.
  `--void` (`mode="void"`) optimise les seuils du détecteur de vides (`DEFAULT_VOID_GRID` :
  ret_z, vol_ratio_min, fill_target, stop_atr) via `_make_runner` qui route vers
  `backtest_void_features` ; force `require_uptrend=True` (segment exploitable).
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
- `screener/liquidity.py` — détecteur de **liquidity void de chute brutale** (ICT + mean-reversion).
  `detect_voids` repère une **baisse subite anormale** (displacement vendeur) sur UNE barre :
  z-score ROBUSTE du rendement (médiane+MAD, pas σ) ≤ `ret_z`, range/ATR ≥ `drop_atr`,
  corps/range ≥ `body_frac` (one-sided), volume ≥ `vol_ratio_min` (liquidité consommée).
  Suit la **récupération** vers le haut du vide (mesurée depuis la *clôture* de la chute :
  `fill_frac`/`fill_status` open/partial/filled, plancher `partial_floor` anti-bruit),
  le **snap-back** précoce (`reclaimed`, clôture > open sous `reclaim_bars`), le **gate de
  tendance** (`in_uptrend`, clôture > MA `trend_ma` — anti couteau qui tombe) et la
  **distance prix→vide** en ATR. Score = anomalie(z,taille,vol) × part restante × fraîcheur
  (demi-vie 8) × proximité × bonus snap-back × pénalité downtrend → vide purgé/downtrend ↓.
  Seuils dans `VoidThresholds` (mappés depuis config.yaml `void:`). Chaque vide porte `why`,
  `theory` (mémo mean-reversion) et `ts` (barre de chute, pour le chart).
- `screener/plot.py` — `plot_voids` : rendu PNG des vides de chute d'un symbole. Chaque vide
  = **zone ombrée verte** (récupération attendue) de la barre de chute jusqu'au présent (haut
  = niveau d'avant-chute = cible, bas = extrême) ; opacité ∝ part non récupérée. Bougies en
  TF inférieure (`FINER_TF`), ligne de prix courant, horodatage CEST.
- `screener/cli.py` — orchestration + sortie tableau/CSV ; `--mtf` → run_mtf,
  `--window [N]` → run_window (table avec colonnes théorie + volume/spread→thèse),
  `--void [N]` → run_void (vides de chute brutale encore ouverts proches du prix, colonnes
  chute→thèse + théorie ; `--chart` → un PNG par symbole du top via `plot_voids` ;
  `--exploitable` → ne garde que le segment rentable en backtest : hors downtrend
  (`in_uptrend`) + prix au bord du vide (`dist_atr ≤ exploit_dist_atr`, défaut 1.0)).

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
python -m screener.cli --timeframe 1h --symbols BTC/USDT --void --chart     # FVG/voids ICT non comblés + PNG
python -m screener.backtest --void --fill-target 0.5 --require-uptrend       # backtest thèse comblement
python -m screener.optimize --timeframe 1h --metric robust   # ou --walk 4
pytest -q
```

## TODO candidats
- Coûts de transaction (frais + slippage) dans le backtest/optimiseur
- Alertes webhook sur nouveau setup (Telegram/Discord)
- Filtrage des setups live par la combinaison validée en OOS
