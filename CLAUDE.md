# CLAUDE.md — contexte projet

Screener Wyckoff multi-cours (accumulation/distribution) : crypto H1/H4 + actions/MP
H4/D1. **Détection de pattern uniquement** — aide à la décision discrétionnaire, jamais
d'exécution d'ordres. Tout l'ancien moteur d'analyse profonde (backtest/optimize/mtf/
score/cli/detect_events) a été retiré pour recentrer le code sur la détection.

## Architecture (chaîne de détection)
- `screener/data.py` — ccxt bas niveau : `fetch_ohlcv()` avec cache parquet, import ccxt
  paresseux (tests hors-ligne). Utilisé par `sources` et `plot`.
- `screener/features.py` — VSA (`add_features`: spread, CLV, ATR, vol_ratio, spread_atr).
- `screener/wyckoff.py` — **cœur unique de détection**. `Thresholds` (seuils VSA) +
  `detect_window_structure` : reconnaît une *séquence* ordonnée (SC→AR→ST→SOS en
  accumulation, BC→AR→ST→SOW en distribution) sur une fenêtre glissante. Chaque
  `WindowEvent` porte `why` (justification volume+spread sur la barre) et `theory`
  (rappel + seuils attendus). `assess_context` calcule la **variation avant le climax**
  (prérequis Wyckoff : markdown avant accumulation, markup avant distribution), portée par
  `WindowStructure.context_move`/`context_ok`. AR cherché sur horizon borné après le climax
  (sinon il attrape l'extrême du SOS/SOW final). Seule définition d'un événement Wyckoff.
- `screener/report.py` — modèle de rendu (`EventCheck`, `PatternReport`) + mise en forme
  (`render_index`, `render_detail`, `render_report`). Sépare présentation et détection.
- `screener/plot.py` — `plot_window_structure` : rendu PNG d'une structure. Dessine les
  bougies sur une **TF inférieure** que l'analyse (`FINER_TF` : H4→H1, H1→15m, 15m→5m).
  Bornes : **plancher = climax (SC), plafond = AR**, miroir en distribution. Les marqueurs
  sont *recalés sur l'extrême réel* de chaque barre d'analyse, retrouvé dans les bougies
  fines (`_wanted_extreme` : SC/ST→creux, AR→sommet, SOS→cassure). Bougies fines injectables
  via `fine_df` (actions Yahoo) ou récupérées via ccxt. Horodatage CEST.

## Screener multi-cours (`python -m screener.scan`)
Couche de *présélection* par-dessus le moteur Wyckoff : balaie un univers fixe
(crypto + actions + matières premières) et remonte les formations acc/dist validées.
**Pas de confluence ni de score de fiabilité** : chaque timeframe est analysé
*séparément* (on varie TF + fenêtres pour ne pas manquer une structure), et le rendu
donne les **éléments de décision** à l'opérateur. Aide discrétionnaire, pas d'exécution.
- `screener/universe.py` — univers (données seules) : 46 cryptos, 90 actions, 8 MP.
  Tickers selon la source : ccxt `BASE/USDT` (crypto) / Yahoo (`-USD`, parfois suffixé
  d'un id numérique ; actions ; futures MP `=F`). `TF_SET_BY_CLASS` : crypto **H1 et H4**,
  actions/MP **H4 et D1** — analysés indépendamment. `EXCLUDED` liste les demandés écartés
  (OpenAI/Infleqtion non cotés, microcaps absents).
- `screener/sources.py` — couche données multi-sources (réutilise `data.py`, n'y touche
  pas). Route crypto→ccxt ; **actions US→Polygon.io si clé** (`POLYGON_API_KEY` ou
  `config.yaml: polygon_api_key`) : volume SIP consolidé = TradingView, 1 requête
  d'agrégats 30 min/titre (throttle 5 req/min, cache 12 h) dont on dérive H1/H4/D1 sur
  les heures de séance (`polygon_session_frames`, RTH 9h30→16h ET) ; sinon Yahoo.
  Actions non-US/MP→Yahoo. Le 4h actions est **aligné sur l'ouverture de séance**
  (`resample_session_ohlcv`, convention TradingView : 9h30→13h30, 13h30→clôture) — les
  blocs calendaires UTC faussaient la VSA. Sans clé Polygon, le volume intraday Yahoo
  est **recalé chaque jour sur le daily consolidé** (`rescale_intraday_volume` : Yahoo
  intraday = 77-94 % du SIP, facteur variable jour à jour 1,0→2,1, mais son daily est
  exact → profil intraday conservé, niveau quotidien = TradingView ; garde-fou facteur
  [0.5,5]). L'intraday Yahoo de Séoul/Tokyo est lacunaire (Σ1h/1d≈0,5-0,7) →
  `Asset.timeframes()` restreint `.KS`/`.T` au D1.
  `get_spot_exchange` rend **Binance joignable depuis le cloud** : endpoints
  publics routés vers le mirror `data-api.binance.vision` (api.binance.com = HTTP 451
  géo-bloqué), `session.trust_env=True` (sinon SSLError : la CA du proxy TLS est dans le
  bundle système, pas dans certifi), marchés **spot only** (fapi/dapi restent 451).
- `screener/scan.py` — pour chaque (actif, TF) : balaie `WINDOWS` (30/45/60) et garde la
  meilleure séquence valide (**Climax+AR+ST** mini ; `_volume_ok` écarte les séries à trop
  de barres volume=0 → ccxt obligatoire pour le crypto). Rend trois choses :
  (1) **contexte** `_context` — une accumulation suit un *markdown* stoppé par le climax,
  une distribution un *markup* (prérequis Wyckoff vérifié sur les `CTX_LOOKBACK` barres
  *avant* le climax) ; (2) **validation événementielle** `_check_event` — vol×, spread/ATR,
  clv confrontés aux `Thresholds`, emojis ✅/⚠️/❌, + la justification `why` de `window.py` ;
  (3) **verdict + commentaire critique** `_verdict_and_comment` (✅ solide / ⚠️ à surveiller /
  ❌ douteux ; contexte manquant = disqualifiant). Sortie : index + fiches détaillées en
  markdown (`rapport_wyckoff.md`). Phase B→C (entrée spring) vs D (LPS/LPSY). Tests :
  `tests/test_scan.py`.
  ```bash
  python -m screener.scan                       # univers complet (crypto ccxt + actions/MP Yahoo)
  python -m screener.scan --classes crypto      # crypto seul, H1 + H4, vrais volumes Binance
  python -m screener.scan --bias accumulation
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
    `wyckoff._theory(bias, name, th)` à partir des `Thresholds` courants — but : développer
    des automatismes de lecture event par event.

## Commandes
```bash
pip install -r requirements.txt
python -m screener.scan                       # univers complet
python -m screener.scan --classes crypto      # crypto seul (H1 + H4)
python -m screener.scan --bias accumulation
pytest -q
```

## TODO candidats
- Signaux résumés (🔴 prioritaires / 🟡 à surveiller / ⚪ RAS) dérivés des verdicts.
- Calcul entrée/stop ATR/objectif → R:R par setup.
- Alertes webhook sur nouveau setup (Telegram/Discord).
