# CLAUDE.md — contexte projet

Screener Wyckoff multi-cours (accumulation/distribution), **tout en H1/H4 sur des paires
24/7 via ccxt**. **Détection de pattern uniquement** — aide à la décision discrétionnaire,
jamais d'exécution d'ordres. Tout l'ancien moteur d'analyse profonde (backtest/optimize/
mtf/score/cli/detect_events) et la couche Yahoo/Polygon ont été retirés.

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
  fines (`_wanted_extreme` : SC/ST→creux, AR→sommet, SOS→cassure). Bougies fines injectées
  via `fine_df` (récupérées par `sources.fetch`). Horodatage CEST.

## Screener multi-cours (`python -m screener.scan`)
Couche de *présélection* par-dessus le moteur Wyckoff : balaie un univers fixe
(crypto + actions tokenisées + métaux + MP) et remonte les formations acc/dist validées.
**Pas de confluence ni de score de fiabilité** : chaque timeframe est analysé
*séparément* (on varie TF + fenêtres pour ne pas manquer une structure), et le rendu
donne les **éléments de décision** à l'opérateur. Aide discrétionnaire, pas d'exécution.
- `screener/universe.py` — univers (données seules), **91 actifs, tous en paires USDT
  24/7** : 46 cryptos (Binance spot, `BASE/USDT`) + 35 actions tokenisées + 7 métaux +
  3 MP (Bitget perp futures, `BASE/USDT:USDT`). `Asset(name, cls, symbol, source)` ;
  `source` ∈ {binance, bitget}. `TIMEFRAMES = ("1h","4h")` pour toutes les classes (pas
  de séance → pas de D1 ni de recalage).
- `screener/sources.py` — données via ccxt, trois exchanges (réutilise `data.fetch_ohlcv`,
  n'y touche pas). `get_spot_exchange` (Binance, crypto) et `get_bitget_exchange` (Bitget
  swap, actions/métaux/MP) partagent `_apply_env_fixes` : `session.trust_env=True` + bundle
  CA système (sinon SSLError : la CA du proxy TLS n'est pas dans certifi). Binance route ses
  endpoints publics vers le mirror `data-api.binance.vision` (api.binance.com = HTTP 451
  géo-bloqué), spot only. `build_exchanges` instancie ce qu'il faut ; `fetch` route par
  `asset.source`. **Open Interest** : Bitget n'a pas d'historique OI ; `get_okx_exchange`
  + `fetch_open_interest(base)` récupèrent ~12 j d'OI horaire (notionnel USD) du même
  sous-jacent sur OKX (33/45 paires ; best-effort, None sinon). Sert à lire le *flux*
  inter-événements, pas le prix.
- `screener/scan.py` — pour chaque (actif, TF) : balaie `WINDOWS` (30/45/60) et garde la
  meilleure séquence valide (**Climax+AR+ST** mini ; `_volume_ok` écarte les séries à trop
  de barres volume=0 → ccxt obligatoire pour le crypto). Rend trois choses :
  (1) **contexte** `_context` — une accumulation suit un *markdown* stoppé par le climax,
  une distribution un *markup* (prérequis Wyckoff vérifié sur les `CTX_LOOKBACK` barres
  *avant* le climax) ; (2) **validation événementielle** `_check_event` — vol×, spread/ATR,
  clv confrontés aux `Thresholds`, emojis ✅/⚠️/❌, + la justification `why` de `wyckoff.py` ;
  (3) **verdict + commentaire critique** `_verdict_and_comment` (✅ solide / ⚠️ à surveiller /
  ❌ douteux ; contexte manquant = disqualifiant). **OI** : `_event_oi_deltas` calcule le ΔOI
  *entre événements* (vs ~6 barres avant pour le climax), `_oi_reading` en donne la lecture
  Wyckoff (AR : rachat de shorts/OI↓ = rebond réflexe conforme vs OI↑ = vrais acheteurs ;
  SOS/SOW : OI↑ = signe réel vs OI↓ = simple débouclage). Sortie : index + **tableau des
  solides** (`report.render_solid_table` : événements vol×·spread·ΔOI + lecture) + fiches
  détaillées en markdown (`rapport_wyckoff.md`). Phase B→C (entrée spring) vs D (LPS/LPSY).
  Tests : `tests/test_scan.py`.
  ```bash
  python -m screener.scan                       # univers complet (91 actifs, Binance + Bitget)
  python -m screener.scan --classes equity metal commodity   # Bitget seul
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
