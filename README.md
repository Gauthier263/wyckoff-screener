# Wyckoff Screener

Screener Wyckoff multi-cours d'**accumulation** et de **distribution** : crypto (H1/H4),
actions et matières premières (H4/D1). Pour chaque actif et chaque timeframe analysé
*séparément*, il remonte les formations validées (Climax → AR → ST …) et fournit les
**éléments de décision** : contexte, validation volume/spread événement par événement,
verdict critique.

> ⚠️ Outil d'**aide à la décision** discrétionnaire, pas un automate d'exécution.
> Les détecteurs sont des heuristiques VSA transparentes et ajustables.

## Installation
```bash
pip install -r requirements.txt
```

## Lancer le screener
```bash
python -m screener.scan                       # univers complet (crypto + actions + MP)
python -m screener.scan --classes crypto      # crypto seul (H1 + H4)
python -m screener.scan --bias accumulation   # un seul biais
python -m screener.scan --source yahoo        # tout via Yahoo (sans Binance)
```
Sortie : un rapport markdown (`rapport_wyckoff.md`) — index trié par verdict, puis une
fiche par formation (contexte, séquence vol×/spread, commentaire critique).

## Sources de données
- **Crypto** → ccxt/Binance (mirror `data-api.binance.vision`, volumes réels).
- **Actions US** → Polygon.io si une clé est fournie (`POLYGON_API_KEY` ou
  `config.yaml: polygon_api_key`, volume SIP consolidé = TradingView) ; sinon Yahoo
  avec volume intraday recalé sur le daily consolidé.
- **Actions non-US / matières premières** → Yahoo (4h aligné sur l'ouverture de séance ;
  Séoul/Tokyo en D1 seul, intraday lacunaire).

## Ce que produit chaque formation
- **Schéma & phase** : accumulation/distribution, B→C (entrée spring) ou D (entrée LPS).
- **Contexte** : markdown avant une accumulation, markup avant une distribution
  (prérequis Wyckoff vérifié sur les barres précédant le climax).
- **Validation événementielle** : pour SC/BC, AR, ST, SOS/SOW → vol×, spread/ATR, clv
  confrontés aux seuils, avec ✅ / ⚠️ / ❌.
- **Verdict** : ✅ solide / ⚠️ à surveiller / ❌ douteux + commentaire critique.

## Réglage
Tout est dans `config.yaml` (section `thresholds`) : `climax_vol`, `sos_vol`,
`wide_spread_atr`, `test_vol`… Les seuils sont les mêmes partout (un seul détecteur).

## Structure
```
screener/
  universe.py  # univers fixe (46 cryptos, 90 actions, 8 MP) + timeframes par classe
  sources.py   # données multi-sources : ccxt / Yahoo (recalé) / Polygon
  data.py      # ccxt bas niveau + cache OHLCV
  features.py  # VSA : spread, CLV, ATR, vol_ratio
  wyckoff.py   # cœur unique : Thresholds + détection de séquence + contexte
  scan.py      # orchestration + validation + verdict
  report.py    # modèle de rendu + mise en forme markdown
  plot.py      # graphiques (bougies TF inférieure, marqueurs, volume)
tests/         # tests synthétiques (pytest -q)
```

## Pistes d'extension
- Signaux résumés (🔴 prioritaires / 🟡 à surveiller / ⚪ RAS) dérivés des verdicts.
- Entrée / stop ATR / objectif → ratio bénéfice-risque par setup.
- Alertes webhook (Telegram/Discord) sur nouveau setup.
