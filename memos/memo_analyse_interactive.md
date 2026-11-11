# Mémo — FORME d'une analyse Wyckoff interactive

Ce mémo ne traite que de la **forme** : comment livrer une analyse en page interactive.
**À lire avant toute analyse**, en plus des documents de fond.

**Le fond ne vient pas d'ici.** La lecture Wyckoff (top-down, fractal, grammaire AR/ST, ordre
volume → OI → tierces, OI en coin, CVD, tierces à froid, niveaux justifiés, verdicts) reste
définie par :
- `CLAUDE.md` (conventions + format canonique en 5 sections + interdits) ;
- le mémo théorie (`memos/memo_theorie.html`, seuils et OI attendu par événement) ;
- `memos/doctrine_nuances.md` (nuances apprises en séance) ;
- les analyses précédentes.

La page met ce fond en forme ; elle n'en change rien.

**Modèles à recopier** (copie dans le scratchpad, jamais modifiés pour une analyse) :
- `examples/notes_btc_15m_reference.json` : **référence actuelle**, avec toutes les conventions
  (schémas macro et de phase, libellés maison BB / T1 / T2 avec « Pourquoi ce nom », `sense`
  sans attendu). Page correspondante : « BTC 15m Wyckoff », mise à jour du 11/11 11h45,
  https://claude.ai/artifact/8Li5x2XD5SKziiDnMQRSj9.
- `examples/notes_btc_2h_canonique.json` : premier modèle (BTC 2h, 02/11 → 05/11), mis à jour
  aux mêmes conventions.

---

## 1. Quand produire la page

| Demande | Livrable |
|---|---|
| Analyse de séquence (« analyse wyckoff BTC 2h depuis… », « analyse btc 15m », « analyse de 2 nov 5h à 5 nov 1h ») | **Page interactive** (défaut, sans que le mot « interactif » soit dit) + mémo théorie |
| « version PNG », « version statique », « image » | PNG (Read inline + SendUserFile) + texte markdown + mémo théorie |
| Question d'état (« où en est BTC », « le niveau X tient ? », plan d'entrée) | Réponse courte dans le fil, pas de page, pas de mémo |
| Correction de la page en cours | Republier **le même fichier** (même lien) |
| Nouvelle analyse, y compris une mise à jour de la même TF plus tard | **Nouveau fichier** (nouveau lien) ; l'ancienne page reste consultable |

Réponse dans le fil après publication : le lien, quelques lignes (biais, ce qui a changé, signal
attendu, niveaux justifiés), le mémo théorie joint. Le détail est dans la page. Pas d'emoji,
pas de pastille de couleur.

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
| OI coin (bougies) | `fetch_open_interest_ohlc(sym, tf, limit)` | **Coin, jamais USD.** 2h/6h/12h supportés |
| Funding | `fetch_funding_rate(sym, tf, limit)` | Coinalyze |
| Ratio L/S comptes | `fetch_long_short_ratio(sym, tf, limit)` → ratio, pct_long | Compte des **comptes**, pas des montants |
| Liquidations | `fetch_liquidations(sym, tf, limit)` → long_liq, short_liq | En BTC |
| Contexte (macro, phase) | `fetch_ohlcv` en 3D / 1D / 4h | Pour les deux schémas de la section 1 |

- **Fuseau** : index UTC réel + 2h, étiqueté UTC (convention du repo, « CEST » toute l'année).
  Toutes les heures des notes sont dans cette convention ; le générateur fait le décalage.
- **Vérifier la fraîcheur** : relire l'heure (`date -u`) et la date de la dernière bougie à
  chaque fetch ; la dernière bougie est souvent incomplète (ne pas la lire comme un événement).
- Pour chiffrer un mouvement (zone M), calculer sur le segment : variation de prix, ΔOI coin,
  CVD cumulé, liquidations longs / shorts, % long début → fin, volume moyen.
- Comment interpréter ces données : voir `CLAUDE.md` et `doctrine_nuances.md`.

---

## 4. Le fichier `notes.json`

| Clé | Contenu | Règle |
|---|---|---|
| `page_title` | Nom court de l'onglet (2-4 mots), ex. « BTC 15m Wyckoff » | Pas d'explication après un tiret |
| `title` | `ACTIF TF — séquence et dates` | **Non affiché** sur la page ; sert de référence dans le fichier |
| `subtitle` | Sources (spot / Coinalyze) + fenêtre ou heure de mise à jour | Une phrase, affichée en tête du panneau |
| `bias` | `"distribution"` ou `"accumulation"` | Cadre de la théorie auto |
| `view` | `{"from": "JJ/MM HH:MM", "to": "JJ/MM HH:MM"}` | Vue initiale ≥ 80 bougies |
| `macro` | `{"points": [{"date", "price", "label"}…], "lines": [{"price", "label"}], "caption"}` | Sommets / creux de la tendance primaire jusqu'au prix actuel (dernier point). Placé par `[[macro]]` en tête de la section 1 |
| `phase` | `{"tf", "title", "points": [{"label", "price", "date"}…], "range": {"hi", "lo"}, "phases": [{"from", "to", "label"}], "caption"}` | Épisode Wyckoff à l'échelle intermédiaire ; `from`/`to` = indices de points ; dernier point = « ici ». Placé par `[[phase]]` à la fin de la section 1 |
| `levels[]` | `id` N1…, `price`, `label`, `reason`, `kind`, `from` (optionnel) | `reason` obligatoire (pourquoi ce niveau). Ancrage du pointillé : voir §7 |
| `zones[]` | `id` M1…, `from`, `to`, `label`, `reason`, `kind` | Un mouvement cité = une zone. `reason` chiffrée (prix %, OI %, liq, foule, volume) |
| `events[]` | `id`, `name`, `time`, `where` (high/low), `kind`, `verdict`, `sense`, `theory_of` + `bias` **ou** `theory` ; pour un libellé maison : `full` + `naming` | Voir « Règles des événements » ci-dessous |
| `text` | Les sections, en mini-markdown | Voir §5 |
| `footer` | La phrase « mémo théorie » propre à cette structure | Obligatoire |

**`kind`** (couleur sur le graphe uniquement) : `demand` vert · `supply` rouge · `trap` orange ·
`range` bleu · `pivot` violet.

**Règles des événements**
- **`sense` = observation seulement** : les paramètres d'intérêt qui ne sont pas déjà dans les
  colonnes du tableau (liquidations, OI d'un mouvement, foule, contexte, niveau touché) et ce qui
  fait le verdict. **Jamais « Attendu : … »**. Pas de redondance avec « Théorie ».
- **L'attendu va dans « Théorie »** : automatique via `theory_of` (BC, AR, ST, SOW, UTAD, LPSY,
  SC, SPRING, SOS, LPS) + `bias` de l'événement si son cadre diffère des notes ; sinon `theory`
  écrit à la main, **avec les seuils** (volume ×, ATR, clôture, OI attendu).
- **Acronymes Wyckoff connus** (SC, BC, AR, ST, SOS, SOW, LPS, LPSY, UT, UTAD, spring…) : **jamais
  développés** (pas de `full`).
- **Libellés maison** (BB, T1, T2, ABS…), quand un événement ne correspond à aucune définition
  Wyckoff stricte : nom neutre plutôt que de forcer un ST / spring / LPS, avec
  - `full` : nom développé (affiché « BB : borne basse de la plage 15m ») ;
  - `naming` : onglet dépliable **« Pourquoi ce nom »**, qui écarte une à une les étiquettes
    Wyckoff plausibles (pourquoi pas un SC, un ST, un spring, un LPS…).
- **`verdict`** court : validé / ambigu / non validé / tentative / en cours, avec au plus une
  précision (« validé, OI ambigu »).
- **IDs** : `SP?`, `SOS?` acceptés. Références dans le texte : `{N1}`, `{M2}`, `{SOW}`. Les
  accolades dans `sense` / `reason` sont retirées automatiquement (pas cliquables en tableau).
- Vérifier que chaque chiffre recopié correspond aux données. Bougie en cours : « provisoire »
  et valeurs arrondies (« ≈ +1.8 % »).

---

## 5. Plan du texte (sections `###`, dans cet ordre)

Le contenu de chaque section suit le format canonique de `CLAUDE.md` ; ce plan fixe la mise en
page (titres, emplacement des schémas et des tableaux, navigation).

```
### 1. Contexte macro (top-down)        [[macro]] puis bullets (TF sup., tendance primaire, position, cadre par défaut, conséquence) puis [[phase]]
### 2. Lecture événement par événement   phrase des seuils + [[events]] (le tableau) + bullets {M…}
### Tierces : CVD / absorption           un bullet par événement : observé (delta_z, absorption, absorption_w), verdict en gras
### Tierces : positionnement             synthèse en sens commun + « Lecture froide » (risque)
### 3. Note fractale                     échelle locale / échelles supérieures / confluence ou divergence
### 4. Synthèse                          séquence, scénarios A/B, biais + conviction, verdict (« trop tôt — attendre… »), ce qui a suivi
### 5. Niveaux (justifiés)               [[levels]] (le tableau) + stop, cibles, invalidation
```

Les titres `###` deviennent la barre de navigation : garder des titres courts avant la
parenthèse.

---

## 6. Générer, vérifier, publier

```bash
SP=<scratchpad>
python -m screener.interactive --symbol BTC/USDT --timeframe 15m --no-detect \
  --notes $SP/notes.json --out $SP/btc_15m_interactif.html
python -m screener.theory_table $SP/memo_theorie.html
```

- `--no-detect` : seules les notes sont affichées (le détecteur auto ajouterait des doublons).
- Contrôle du modèle avant publication : relire dans le HTML (objet `D`) les vol×, spread, CLV,
  ΔOI de chaque événement, le `t0` des niveaux, et qu'aucune référence `{…}` n'est restée brute.
- **Un seul coup d'œil** : une capture Playwright desktop (pas d'erreur console) + un contrôle à
  400 px de large (pas de débordement), puis une passe de corrections ; pas de boucle.
- Publier avec l'outil Artifact (`icon: chart` au premier publish, `description` d'une phrase).
  Envoyer `memo_theorie.html` avec SendUserFile.

---

## 7. Rendu de la page (déjà codé dans `interactive.py`, ne pas le refaire à la main)

**Page**
- **Thème clair (fond blanc) par défaut**, même si l'appareil est en sombre ; sombre via ◐.
- **Pas de titre** : l'en-tête ne garde que « dernier prix @ heure (CEST) » et les boutons
  (« Masquer / Afficher zones M », « Vue initiale », « Tout », ◐).
- Panneau de droite : barre de navigation par section, sous-titre, texte, pied mémo théorie.
- Références et tableaux sans pastille de couleur (la couleur vit sur le graphe).

**Graphe**
- Lightweight Charts : prix / volume + vol MA / **OI coin en bougies**, même TF, zoom/pan.
- **Panneau du cours agrandi**, volume et OI réduits (rapport 4.6 / 0.8 / 1.0).
- **Pas de ligne pointillée du dernier prix** (seule l'étiquette d'axe reste).
- Niveaux = **pointillés qui partent de leur bougie d'origine** (sommet ou creux), hors
  autoscale. Ancrage : bougie dont le high/low vaut le prix (± 0.02 %), sinon `from`, sinon
  toute la largeur.
- Marqueurs d'événement = **nom seul** (le ×vol est dans le tableau).
- **Pas de verticales** au repos (seul l'événement cliqué / survolé en a une).
- **Pas de vignettes** sous les mouvements (réactivables : `"thumbs": true`).
- Rectangles des zones M, masquables par le bouton (zone cliquée toujours visible ; choix
  mémorisé par navigateur).

**Schémas de la section 1**
- **Schéma de tendance macro** (`[[macro]]`) : sommets / creux de la tendance primaire,
  segments verts en hausse, rouges en baisse, niveaux en pointillé, dernier point = prix actuel.
- **Schéma de phase Wyckoff** (`[[phase]]`) : l'épisode complet à l'échelle intermédiaire,
  événements **avec leur prix** (2e ligne, en k), plage en pointillé, bandes de phases A-E,
  point « ici ». But : voir d'un coup d'œil dans quelle phase on est.
  **Choix de l'échelle, à chaque analyse, avant de tracer** : parmi 3D, Daily et 4h, prendre
  celle où l'épisode en cours forme une **structure complète et lisible** : le climax qui l'ouvre
  (BC ou SC) est visible, au moins 4 événements jalonnent les phases, le prix actuel s'y place
  clairement. Écarter une échelle où l'épisode tient en 2-3 bougies (souvent la 3D sur un épisode
  court) ou où il est noyé dans le bruit (souvent la 4h sur un épisode long). Indiquer l'échelle
  dans `phase.tf` (affichée au-dessus du schéma). Ex. BTC 15m du 11/11 : Daily retenue
  (distribution 79 800–87 396 du 21/09 au 11/11 lisible ; en 3D ~17 bougies peu détaillées, en
  4h trop fragmenté).

**Tableaux**
- **Événements** : colonnes Évt / Prix / Rvol (`×1.39`) / Spread (`1.05 ATR`) / Clôture
  (`CLV 0.76`) / ΔOI (`−0.48 %`, calculé sur la barre) / Verdict, **sans date ni heure**.
  Ligne de détail : nom développé (libellés maison seulement), `sense`, onglet « Pourquoi ce nom »
  (libellés maison), onglet « Théorie ». **Sur téléphone, le verdict passe dans la ligne de
  détail** (le tableau tient en 400 px).
- **Niveaux** : ID, prix, pourquoi ce niveau.

**Interactions**
- Clic sur une référence du texte → le graphe se recentre et surligne.
- **Clic sur le graphe**, par ordre de priorité :
  1. un pointillé de niveau (± 6 px, sur sa portion tracée) → sa ligne du tableau Niveaux ;
  2. une bougie d'événement (± 1 bougie, près de son marqueur) → sa ligne du tableau Événements ;
  3. un rectangle de zone M visible → le passage du texte qui la cite.
  La cible défile au centre et est surlignée un instant.

---

## 8. Pièges de forme déjà rencontrés

| Piège | Parade |
|---|---|
| OI 2h faux / tronqué | Corrigé dans `data.py` ; une nouvelle TF s'ajoute à `_TF_MIN`, `_COINALYZE_INTERVAL`, `_TF_FREQ` et à la base fine de `fetch_open_interest_ohlc` |
| Clé Coinalyze absente (401) | `request_credential` sur `api.coinalyze.net`, en-tête `api_key` |
| Niveau hors des données chargées | Le pointillé part de la gauche : normal ; le dire si utile |
| Niveau dont le prix n'est pas un high/low exact | Mettre `from` (heure CEST de la bougie d'origine) |
| Niveau de TF supérieure hors des données : l'ancrage auto accroche une bougie récente qui frôle le prix | Mettre un `from` antérieur au début des données |
| Événement sans définition Wyckoff stricte | Libellé maison + `full` + `naming` ; ne jamais forcer un ST / spring / LPS |
| « Attendu : … » dans `sense` | Le déplacer dans `theory` (ou laisser la théorie auto) |
| Tableau qui déborde sur téléphone | Verdicts courts ; vérifier à 400 px |
| Chiffres d'une bougie en cours qui changent avant publication | « Provisoire » + valeurs arrondies |
| `{M2}` dans `sense` / `reason` | Accolades retirées automatiquement |
| Étiquettes du schéma coupées au bord | Marges du SVG déjà élargies ; garder des libellés courts |

---

## 9. Où sont les règles

| Sujet | Document |
|---|---|
| **Fond** : lecture Wyckoff, format canonique, interdits | `CLAUDE.md` |
| **Fond** : seuils et OI attendu par événement | `memos/memo_theorie.html` |
| **Fond** : nuances apprises en séance | `memos/doctrine_nuances.md` |
| **Forme** : livraison en page interactive | ce mémo |
| **Forme** : modèles de notes | `examples/notes_btc_15m_reference.json`, `examples/notes_btc_2h_canonique.json` |
| **Forme** : le rendu et ses tests | `screener/interactive.py`, `tests/test_interactive.py` |

Règle de rangement : une nouvelle préférence **de forme** validée par Gauthier (rendu, mise en
page, interaction, présentation des événements) s'ajoute ici et dans le code ; une nouvelle règle
**de fond** (lecture, interprétation) va dans `CLAUDE.md` ou `doctrine_nuances.md`, jamais ici.
