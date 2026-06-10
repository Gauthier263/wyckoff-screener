# Wyckoff Screener (crypto)

Screener d'événements Wyckoff d'**accumulation** et de **distribution** sur les
marchés crypto, en H1/H4, via [ccxt](https://github.com/ccxt/ccxt) (données OHLCV
publiques, aucune clé API requise).

> ⚠️ Outil d'**aide à la décision** discrétionnaire, pas un automate d'exécution.
> Les détecteurs sont des heuristiques VSA transparentes et ajustables — ils
> signalent des zones à regarder, pas des ordres à passer.

## Installation
```bash
pip install -r requirements.txt
```

## Lancer le screen
```bash
# Scan des 60 paires USDT les plus liquides en H1 (défaut config.yaml)
python -m screener.cli

# H4, top 80, accumulation seulement
python -m screener.cli --timeframe 4h --top 80 --bias accumulation

# Liste manuelle, sans cache
python -m screener.cli --symbols BTC/USDT ETH/USDT SOL/USDT --no-cache
```
Sortie : tableau classé dans le terminal + `watchlist.csv`.

## Confluence multi-timeframe
Le HTF donne le contexte (dans quelle campagne on est), le LTF le déclencheur.
```bash
python -m screener.cli --mtf            # défaut : 4h → 1h (config.yaml: timeframes)
```
Multiplicateur appliqué au score LTF : HTF aligné + déclencheur = ×1.5 ;
HTF aligné = ×1.25 ; HTF neutre = ×1.0 ; conflit HTF/LTF = ×0.5.

## Backtest
Walk-forward, sans lookahead : détection sur l'historique jusqu'à `t`, puis
simulation des sorties. Entrées sur déclencheurs (long : SPRING/SOS/LPS ;
short : UTAD/SOW/LPSY), stop en ATR, objectif en multiple de risque (R).
```bash
python -m screener.backtest --symbols BTC/USDT ETH/USDT --timeframe 1h \
    --stop-atr 1.0 --rr 2.0 --max-hold 30 --limit 1000
```
Sortie : stats par type d'événement (n, win%, R moyen = espérance, profit factor)
+ `backtest_trades.csv`. Sert à calibrer `thresholds` et à savoir *quels événements
te rapportent réellement*.

## Optimisation des seuils (grid-search + out-of-sample)
Laisse le backtest **choisir** les seuils, sans surajuster : on optimise sur le début
de l'historique (in-sample) et on valide sur la fin, jamais vue (out-of-sample).
```bash
# split simple 60/40, métrique robuste (défaut)
python -m screener.optimize --timeframe 1h --top 40 --limit 1500

# validation plus stricte : walk-forward 4 plis glissants
python -m screener.optimize --walk 4 --timeframe 4h
```
Métriques (`--metric`) : `robust` (espérance pénalisée par l'erreur d'échantillonnage,
défaut), `expectancy`, `profit_factor`. Garde-fous : plancher `--min-trades`, rapport
IS vs OOS, et un **verdict** ✅ robuste / ⚠️ fragile / ❌ surajustement. La grille
complète est exportée (`optimize_results.csv`) pour inspecter la stabilité du top —
un top serré autour des mêmes paramètres est plus fiable qu'un top dispersé.

> ⚠️ Un bon résultat OOS réduit le risque de surajustement, il ne le supprime pas :
> l'historique crypto est court et les régimes changent. Recalibre périodiquement.

## Colonnes de sortie
| colonne | sens |
|---|---|
| `bias` | accumulation / distribution |
| `phase` | estimation de phase Wyckoff (B/C/D) |
| `top_event` | événement le plus fort × récent |
| `bars_ago` | ancienneté de l'événement (0 = dernière barre) |
| `score` | score composite (poids type × force × récence) |
| `dist_supp_%` / `dist_res_%` | distance au support / à la résistance de la plage |
| `events` | tous les événements détectés sur le symbole |

## Événements détectés
- **Accumulation** : SC (selling climax), ST, **SPRING**, SOS, LPS
- **Distribution** : BC (buying climax), ST, **UTAD**, SOW, LPSY

## Réglage
Tout est dans `config.yaml` (section `thresholds`). Les leviers les plus utiles :
- `climax_vol` / `sos_vol` : sensibilité au volume
- `wide_spread_atr` : ce qui compte comme barre « large »
- `pen_atr` : profondeur mini d'un spring/upthrust hors borne
- `lookback` / `buffer` : taille de la plage et fenêtre d'événements récents

## Structure
```
screener/
  data.py      # ccxt : univers + OHLCV + cache
  features.py  # VSA, ATR, pivots, détection de plage
  events.py    # détecteurs Wyckoff
  score.py     # agrégation + scoring + phase
  mtf.py       # confluence multi-timeframe
  backtest.py  # backtest walk-forward + stats par événement
  optimize.py  # grid-search des seuils + validation IS/OOS + walk-forward
  cli.py       # orchestration (screen + --mtf)
tests/         # tests sur données synthétiques (pytest -q)
```

## Pistes d'extension (idéales pour Claude Code)
- Alertes (webhook Telegram/Discord) sur nouveau setup
- Export vers ton dashboard TradingView / journal de trades
- Détection de plage par clustering de pivots plutôt que min/max
- Coûts de transaction (frais + slippage) dans le backtest
- Filtrage des setups live par les seuils validés en OOS
