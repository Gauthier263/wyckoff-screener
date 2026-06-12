# Wyckoff Screener

Screener Wyckoff multi-cours d'**accumulation** et de **distribution** : 91 paires USDT
24/7 (46 cryptos + 35 actions tokenisées + 7 métaux + 3 matières premières), analysées
en H1 et H4. Pour chaque actif et chaque timeframe analysé *séparément*, il remonte les
formations validées (Climax → AR → ST …) et fournit les **éléments de décision** :
contexte, validation volume/spread événement par événement, verdict critique.

> ⚠️ Outil d'**aide à la décision** discrétionnaire, pas un automate d'exécution.
> Les détecteurs sont des heuristiques VSA transparentes et ajustables.

## Installation
```bash
pip install -r requirements.txt
```

## Lancer le screener
```bash
python -m screener.scan                                    # univers complet (91 actifs)
python -m screener.scan --classes crypto                   # crypto seul
python -m screener.scan --classes equity metal commodity   # Bitget seul
python -m screener.scan --bias accumulation                # un seul biais
```
Sortie : un rapport markdown (`rapport_wyckoff.md`) — index trié par verdict, puis une
fiche par formation (contexte, séquence vol×/spread, commentaire critique).

## Sources de données
Tout passe par ccxt, sur des paires USDT continues (volume crypto-natif fiable) :
- **Crypto** → Binance spot (mirror `data-api.binance.vision`).
- **Actions tokenisées, métaux, matières premières** → Bitget (perp futures `BASE/USDT:USDT`).

Les deux exchanges appliquent le même correctif d'environnement (`trust_env` + bundle CA
système) pour passer le proxy TLS et la géo-restriction.

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
  universe.py  # univers fixe (91 paires USDT) : Binance crypto + Bitget actions/métaux/MP
  sources.py   # données ccxt : deux exchanges (Binance, Bitget) + routage
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
