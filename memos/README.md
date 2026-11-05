# Mémos Wyckoff

Documents de référence (HTML autonomes, cliquables hors-ligne) produits pour le screener.

## Contenu

Tous les mémos du projet sont réunis ici (avant : dispersés sur plusieurs branches).
Les HTML sont autonomes (images intégrées) et s'ouvrent dans un navigateur ; pour les
lire sur téléphone, les publier en page (lien claude.ai) plutôt que d'envoyer le fichier.

### Doctrine (à lire en premier)

| Fichier | Sujet | Source |
|---|---|---|
| `doctrine_nuances.md` | Nuances de lecture apprises en conversation, erreurs corrigées, cas limites, préférences de format. Complément de `CLAUDE.md`. | Rédigé par la session Daily le 05/11/2026 avant résumé de sa mémoire. |
| `memo_theorie.html` | Théorie Wyckoff : fondations (3 lois, opérateur composite, phases A→E), tables événements accu/distrib avec seuils vol×/spread/CLV + OI + CVD + absorption, narratifs, fiches par indice. | Généré par `../screener/theory_table.py` (`build_theory_html`), seuils courants. |

### Événements et tests

| Fichier | Sujet | Source |
|---|---|---|
| `memo_tests_co.html` | Les tests du Composite Operator : pourquoi il teste, anatomie d'un test, LPS vs BUEC, les 3 springs, règle Tom Williams, matrice de réaction, fiches auteurs. | Statique (session Daily). |
| `deep_focus_test_co/` | Mémo Deep Focus « Tests du Composite Operator », v2 (HTML, PDF A4 imprimable, Markdown) ; `memo_tests_CO.md` ; `notes_de_recherche/` (doctrine Wyckoff/Evans, Phases A-B, C, D-E, VSA Williams, microstructure, playbook, journal de vérification) ; `versions/` = v1. | Session « Composite operator tests », branche `great-hawking`, 31/10 → 02/11/2026. |
| `memo_upthrust_accu_vs_distrib.html` | Upthrust dans une accumulation vs UTAD de distribution : comment les distinguer. | Session « Upthrust dans l'accumulation », branche `upthrust-accumulation`, 22/07/2026. |
| `memo_micro_accumulation_buec.html` | Timing de la micro-accumulation après BUEC (offre latente, primitives). | Session « Mémo assèchement », branche `micro-accumulation-timing`, 21/08/2026. |

### Niveaux, résistances, régimes

| Fichier | Sujet | Source |
|---|---|---|
| `memo_comportement_resistance.html` | Comportement du prix à une résistance : 11 cas (6 retournements + 5 franchissements), empreinte chiffrée, arbre de décision, exemples BTC réels annotés. | Généré par `build_memo_resistance.py` (session Daily). |
| `niveaux/` | Niveaux de résistance en position longue (HTML + PDF, exemples réels dans `img/`). | Session « memo-niveaux - relié à Coinalyze », branche `resistance-levels-methodology`, 22/07/2026. |
| `memo_etats_du_cours.html` | États du cours : régimes de marché et order blocks (lecture Wyckoff). | Session « Market phases and order block identification », branche `vibrant-ramanujan`, 29/06/2026. |
| `charts/*.png` | Graphes annotés réels pour chaque cas du mémo résistance (`*_embed.png` = versions intégrées en base64). | Généré par `gen_case_charts.py`. |

Les mémos repris d'autres branches sont copiés **tels quels** (contenu non modifié). Les
plus anciens peuvent contenir des pastilles de couleur : la règle actuelle (aucune pastille
nulle part) s'applique aux nouvelles productions.

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
