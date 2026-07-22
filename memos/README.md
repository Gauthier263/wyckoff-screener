# Mémos Wyckoff

Documents de référence (HTML autonomes, cliquables hors-ligne) produits pour le screener.

## Contenu

| Fichier | Sujet | Source |
|---|---|---|
| `memo_theorie.html` | Théorie Wyckoff : fondations (3 lois, opérateur composite, phases A→E), tables événements accu/distrib avec seuils vol×/spread/CLV + OI + CVD + absorption, narratifs, fiches par indice. | Généré par `../screener/theory_table.py` (`build_theory_html`). |
| `memo_comportement_resistance.html` | Comportement du prix à une résistance : 11 cas MECE (6 retournements + 5 franchissements), schéma 3 panneaux, empreinte chiffrée, « qui agit » (retail/composite), contexte de marché + phase + signaux avant-coureurs, exemple réel BTC vérifié + graphe annoté. Arbre de décision + table récap. | Généré par `build_memo_resistance.py`. |
| `memo_tests_co.html` | Les tests du Composite Operator : pourquoi il teste, anatomie d'un test, LPS vs BUEC, les 3 springs, règle Tom Williams, matrice de réaction, fiches auteurs (Wyckoff/Evans/Pruden/Williams). | Statique (édité à la main). |
| `charts/*.png` | Graphes annotés réels (3 panneaux prix+résistance / volume+moyenne / CVD) pour chaque cas du mémo résistance. `*_embed.png` = versions réduites intégrées en base64 dans le HTML. | Généré par `gen_case_charts.py`. |

## Régénérer

Depuis la racine du repo (dépendances : `requirements.txt`, clé Coinalyze pour l'OI cf. `CLAUDE.md`) :

```bash
# mémo théorie
python -m screener.theory_table memos/memo_theorie.html

# graphes des cas réels (fetch BTC ccxt + CVD/OI) puis mémo résistance
python memos/gen_case_charts.py            # -> memos/charts/*.png (+ *_embed.png)
python memos/build_memo_resistance.py      # -> memos/memo_comportement_resistance.html
```

Les données réelles des exemples proviennent de `screener.data` (BTC/USDT via le miroir
`data-api.binance.vision`, delta taker pour le CVD, OI via Coinalyze) ; toutes les métriques
citées dans les mémos sont vérifiées sur ces données, jamais inventées.

## Note

`memo_comportement_resistance.html` embarque ses 11 graphes en base64 (fichier ~2,8 Mo, autonome,
aucun lien externe) — il s'ouvre tel quel dans un navigateur.
