# Mémo — FORME d'une analyse Wyckoff interactive

Ce mémo ne traite que de la **forme** : comment livrer une analyse en page interactive comme
« BTC 2h Wyckoff » (BTCUSDT 2h, 02/11 05h → 05/11 01h, https://claude.ai/artifact/FcRBFmWwwv7DgygydMKwrR).
**À lire avant toute analyse**, en plus des documents de fond.

**Le fond ne vient pas d'ici.** La lecture Wyckoff (top-down, fractal, grammaire AR/ST, ordre
volume → OI → tierces, OI en coin, CVD, tierces à froid, niveaux justifiés, verdicts) reste
définie par :
- `CLAUDE.md` (conventions + format canonique en 5 sections + interdits) ;
- le mémo théorie (`memos/memo_theorie.html`, seuils et OI attendu par événement) ;
- `memos/doctrine_nuances.md` (nuances apprises en séance) ;
- les analyses précédentes.

La page met ce fond en forme ; elle n'en change rien.

Modèle à recopier : `examples/notes_btc_2h_canonique.json`.

---

## 1. Quand produire la page

| Demande | Livrable |
|---|---|
| Analyse de séquence (« analyse wyckoff BTC 2h depuis… », « fais analyse BTC 3D », « analyse de 2 nov 5h à 5 nov 1h ») | **Page interactive** (défaut, sans que le mot « interactif » soit dit) + mémo théorie |
| « version PNG », « version statique », « image » | PNG (Read inline + SendUserFile) + texte markdown + mémo théorie |
| Question d'état (« où en est BTC », « le niveau X tient ? ») | Réponse courte, pas de page, pas de mémo |
| Correction de la page en cours | Republier **le même fichier** (même lien) |
| Nouvelle analyse | **Nouveau fichier** (nouveau lien) |

Réponse dans le fil après publication : le lien, 2-3 lignes (biais, signal attendu), le mémo
théorie joint. Le détail est dans la page. Pas d'emoji, pas de pastille de couleur.

---

## 2. Prérequis de session

- Démarrer depuis `main` (ou une branche qui le contient).
- Environnement **« Environnement full binance »** : la clé Coinalyze y est enregistrée comme
  *network secret* ; le proxy l'injecte. Le code envoie un placeholder (`proxy-injected`) quand
  `HTTPS_PROXY` est défini. Vérifier : `python -c "from screener.data import fetch_open_interest_ohlc as f; print(f('BTC/USDT','1d',limit=3))"`.
  Si l'OI revient vide → la clé manque : la demander avec `request_credential`
  (hôte `api.coinalyze.net`, en-tête `api_key`), jamais dans le chat.
- `pip install -r requirements.txt` (ccxt absent par défaut).
- OKX est bloqué depuis le cloud : le repli OKX ne sert pas ici. TradingView n'est pas
  joignable (pas d'API, pas de connexion au compte) : Coinalyze est la source.

---

## 3. Données à charger pour la page (même TF que l'analyse, heures CEST)

| Donnée | Fonction | Remarques |
|---|---|---|
| Bougies prix | `get_exchange('binance').fetch_ohlcv('BTC/USDT', tf, limit=300)` | Spot Binance (miroir vision). `add_features` → vol_ratio, spread_atr, clv, atr, vol_ma |
| CVD / absorption | `fetch_taker_delta(sym, tf, 300)` → `add_absorption(df, delta.reindex(df.index))` | Spot (proxy). Colonnes delta, delta_z, absorption, absorption_w, no_demand/no_supply |
| OI coin (bougies) | `fetch_open_interest_ohlc(sym, tf, limit)` | **Coin, jamais USD.** 2h/6h/12h supportés (bug corrigé : avant, 2h tombait en 5 min resamplé 1h) |
| Funding | `fetch_funding_rate(sym, tf, limit)` | Coinalyze |
| Ratio L/S comptes | `fetch_long_short_ratio(sym, tf, limit)` → ratio, pct_long | Compte des **comptes**, pas des montants |
| Liquidations | `fetch_liquidations(sym, tf, limit)` → long_liq, short_liq | En BTC |

- **Fuseau** : index UTC réel + 2h, étiqueté UTC (convention du repo, « CEST » toute l'année).
  Toutes les heures des notes sont dans cette convention ; le générateur fait le décalage.
- **Vérifier la fraîcheur** : relire la date de la dernière bougie à chaque fetch ; la dernière
  bougie est souvent incomplète (ne pas la lire comme un événement).
- Quelles données lire et comment les interpréter (TF ≥ 3D en VSA pur, seuils `Thresholds`…) :
  voir `CLAUDE.md` et `doctrine_nuances.md`. Ici, seulement ce qu'il faut pour remplir la page.

---

## 4. Le fichier `notes.json`

Partir de `examples/notes_btc_2h_canonique.json` (copie dans le scratchpad, pas dans le repo).

| Clé | Contenu | Règle |
|---|---|---|
| `title` | `ACTIF TF — séquence et dates` | En-tête canonique, affiché en haut |
| `page_title` | Nom court de l'onglet (2-4 mots), ex. « BTC 2h Wyckoff » | Pas d'explication après un tiret |
| `subtitle` | Sources (spot / Coinalyze) + fenêtre analysée | Une phrase |
| `bias` | `"distribution"` ou `"accumulation"` | Cadre de la théorie auto |
| `view` | `{"from": "JJ/MM HH:MM", "to": "JJ/MM HH:MM"}` | Vue initiale ≥ 80 bougies |
| `levels[]` | `id` N1…, `price`, `label`, `reason`, `kind`, `from` (optionnel) | `reason` obligatoire. Le pointillé part de la bougie dont le high/low vaut le prix (± 0.02 %) ; sinon `from` ; sinon toute la largeur |
| `zones[]` | `id` M1…, `from`, `to`, `label`, `reason`, `kind` | Un mouvement cité = une zone. `reason` chiffrée (prix %, OI %, liq, foule) |
| `events[]` | `id`, `name`, `time`, `where` (high/low), `kind`, `verdict`, `sense`, `theory_of`, `bias` | `sense` = colonne « Volume + OI = sens » du format canonique (contenu : cf. `CLAUDE.md`). vol×/spread/CLV/ΔOI sont lus automatiquement sur la barre |
| `text` | Les sections, en mini-markdown | Voir §5 |
| `footer` | La phrase « mémo théorie » propre à cette structure | Obligatoire |

- **`kind`** (couleur sur le graphe uniquement) : `demand` vert · `supply` rouge · `trap` orange ·
  `range` bleu · `pivot` violet.
- **`theory_of`** : clé du mémo théorie (BC, AR, ST, SOW, UTAD, LPSY, SC, SPRING, SOS, LPS) ;
  `bias` sur l'événement si son cadre diffère des notes (ex. Spring ? → `accumulation`).
  Événement hors liste (ex. « Absorption ») → écrire `theory` à la main.
- **IDs** : `SP?`, `SOS?` acceptés. Références dans le texte : `{N1}`, `{M2}`, `{SOW}`.
- Vérifier que chaque chiffre recopié dans `sense` et les zones correspond aux données.

---

## 5. Plan du texte (sections `###`, dans cet ordre)

Le contenu de chaque section suit le format canonique de `CLAUDE.md` ; ce plan fixe seulement
la mise en page (titres, emplacement des tableaux, navigation).

```
### 1. Contexte macro (top-down)        bullets : TF sup., tendance primaire, position, cadre par défaut, conséquence
### 2. Lecture événement par événement   phrase des seuils + ligne [[events]] (le tableau) + bullets {M…}
### Tierces : CVD / absorption           un bullet par événement : attendu, observé (delta_z, absorption, absorption_w), verdict en gras
### Tierces : positionnement             synthèse en sens commun + « Lecture froide » (risque)
### 3. Note fractale                     échelle locale / échelle supérieure / confluence ou divergence
### 4. Synthèse                          séquence, scénarios A/B, biais + conviction, verdict (« trop tôt — attendre… »), ce qui a suivi
### 5. Niveaux (justifiés)               ligne [[levels]] (le tableau) + stop, cibles, invalidation
```

`[[events]]` et `[[levels]]` placent les tableaux à cet endroit. Les titres `###` deviennent la
barre de navigation : garder des titres courts avant la parenthèse.

---

## 6. Générer, vérifier, publier

```bash
SP=<scratchpad>
python -m screener.interactive --symbol BTC/USDT --timeframe 2h --no-detect \
  --notes $SP/notes.json --out $SP/btc_2h_interactif.html
python -m screener.theory_table $SP/memo_theorie.html   # ou build_theory_html(out_path=...)
```

- `--no-detect` : seules les notes sont affichées (le détecteur auto ajouterait des événements
  en doublon).
- Contrôle du modèle avant publication : relire dans le HTML (objet `D`) les vol×, spread, CLV,
  ΔOI de chaque événement et le `t0` des niveaux.
- **Un seul coup d'œil** : une capture Playwright desktop (et pas d'erreur console), puis une
  passe de corrections ; pas de boucle.
- Publier avec l'outil Artifact (`icon: chart` au premier publish, `description` d'une phrase).
  Envoyer `memo_theorie.html` avec SendUserFile.

---

## 7. Ce que le générateur fait déjà (ne pas le refaire à la main)

- Graphe Lightweight Charts : prix / volume + vol MA / **OI coin en bougies**, même TF, zoom/pan,
  boutons « Vue initiale », « Tout », thème clair/sombre.
- Niveaux = **pointillés qui partent de leur bougie d'origine** (sommet ou creux), hors autoscale.
- **Pas de vignettes** sous les mouvements (réactivables : `"thumbs": true`).
- **Pas de verticales** d'événement au repos (seul l'événement cliqué/survolé en a une).
- Marqueurs = **nom seul** (le ×vol est dans le tableau).
- Bouton **« Masquer / Afficher zones M »** (zone cliquée toujours visible ; choix mémorisé).
- **Clic sur une bougie d'événement** (± 1) → défile jusqu'à sa ligne du tableau, surlignée.
- **Clic sur un pointillé de niveau** (± 6 px) → défile jusqu'à sa ligne Niveaux (prioritaire).
- Clic sur une référence du texte → le graphe se recentre et surligne.
- Tableau événements : vol×, spread/ATR, CLV, ΔOI % (calculé), verdict, ligne « sens »,
  bouton « Théorie » (rôle + seuils depuis `Thresholds`).
- Navigation par section, sous-titre, pied mémo théorie, vue initiale = `view`.
- Références et tableaux sans pastille de couleur (la couleur vit sur le graphe).

---

## 8. Pièges de forme déjà rencontrés

| Piège | Parade |
|---|---|
| OI 2h faux / tronqué | Corrigé dans `data.py` ; si une nouvelle TF apparaît, l'ajouter à `_TF_MIN`, `_COINALYZE_INTERVAL`, `_TF_FREQ` et à la base fine de `fetch_open_interest_ohlc` |
| Clé Coinalyze absente (401) | `request_credential` sur `api.coinalyze.net`, en-tête `api_key` |
| Niveau hors des données chargées (ex. 74 968 du 14/09 en 2h) | Le pointillé part de la gauche : normal ; le dire si utile |
| Niveau dont le prix n'est pas un high/low exact | Mettre `from` (heure CEST de la bougie d'origine) |
| Niveau d'une TF supérieure dont l'origine est hors des données (ex. 74 968 du 14/09 en 1h) : l'ancrage auto peut accrocher une bougie récente qui frôle le prix (± 0.02 %) | Mettre un `from` antérieur au début des données : le pointillé part du bord gauche |
| Titre d'onglet trop long | `page_title` court ; le long va dans `title` |
| Tableau qui déborde | Verdicts courts (« validé, OI ambigu ») |
| Chiffres d'une bougie en cours qui changent avant publication | Écrire « provisoire » et des valeurs arrondies (« ≈ +1.8 % ») dans `sense`, pas la valeur exacte du moment |
| `{M2}` dans `sense` / `reason` | Les tableaux n'ont pas de références cliquables : les accolades sont retirées automatiquement (seul le texte les rend cliquables) |

---

## 9. Où sont les règles

| Sujet | Document |
|---|---|
| **Fond** : lecture Wyckoff, format canonique, interdits | `CLAUDE.md` |
| **Fond** : seuils et OI attendu par événement | `memos/memo_theorie.html` |
| **Fond** : nuances apprises en séance | `memos/doctrine_nuances.md` |
| **Forme** : livraison en page interactive | ce mémo |
| **Forme** : le rendu et ses tests | `screener/interactive.py`, `tests/test_interactive.py` |

Règle de rangement : une nouvelle préférence **de forme** validée par Gauthier (rendu, mise en
page, interaction) s'ajoute ici et dans le code ; une nouvelle règle **de fond** (lecture,
interprétation) va dans `CLAUDE.md` ou `doctrine_nuances.md`, jamais ici.
