# Mémo — produire une analyse Wyckoff interactive

Référence complète pour refaire une analyse comme la page « BTC 2h Wyckoff »
(BTCUSDT 2h, 02/11 05h → 05/11 01h, https://claude.ai/artifact/FcRBFmWwwv7DgygydMKwrR).
**À lire avant toute analyse.** `CLAUDE.md` fixe les règles ; ce mémo les regroupe dans l'ordre
du travail, avec les commandes, le gabarit et les pièges déjà rencontrés.

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

## 3. Données (même TF que l'analyse, heures CEST)

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
- **TF ≥ 3D** : VSA pur (OI/CVD non attribuables bougie par bougie). Pour lire l'OI d'un
  mouvement 3D, descendre en Daily sur les journées directionnelles franches.

Seuils (`Thresholds`, config.yaml) : climax ≥ ×2.0 · test ≤ ×0.85 · SOS/SOW ≥ ×1.3 ·
spread large ≥ 1.3 ATR. Les citer, ne jamais les coder en dur dans le texte sans les relire.

---

## 4. Lecture (le fond ne change jamais)

1. **Top-down d'abord.** Tendance primaire + TF supérieure avant toute étiquette. Plage dans un
   downtrend = **redistribution par défaut** ; plage dans un uptrend = re-accumulation par défaut.
   L'accumulation se **gagne** ; étiquettes conditionnelles (« SOS ? », « Spring ? ») tant que
   la plage n'est pas cassée et retestée.
2. **Fractal.** Déclarer la TF ; étiqueter par rapport à la plage de CETTE structure ; dire en
   section 3 quel événement unique elle représente sur la TF supérieure.
3. **Grammaire cohérente.** En distribution : BC → AR **bas** → ST **haut**. Jamais « SC puis AR »
   dans un cadre distribution. Un passage au-dessus d'une borne n'est un SOS qu'après tenue +
   back-up ; sinon « tentative ».
4. **Ordre volume → OI → tierces.** Chaque événement : seuil attendu, observé, verdict
   (validé / ambigu / non validé / tentative).
5. **OI en coin, lu avec le lieu** :
   - prix↑ + OI↓ = rachat de shorts (covering) → ambigu, ne confirme pas la distribution ;
   - prix↑ + OI↑ = positions neuves → au test d'une résistance en downtrend, demande piégée ;
   - **prix↓ + OI↑ = des positions s'ouvrent des DEUX côtés** (chaque contrat a un long et un
     short). La question est *qui agresse et qui perd*. Trancher avec CVD + ratio L/S +
     liquidations. Exemple M2 : CVD plat (−158) sur −2,3 %, delta_z +2.54 sur le SOW, comptes
     68 → 73 % long, 442 BTC de longs liquidés → **shorts posés (passifs) face à des longs qui
     achètent la baisse et perdent**. Écrire les deux côtés, ne jamais dire seulement « longs
     piégés » quand l'OI monte sur une baisse.
   - Une liquidation de shorts fait **baisser** l'OI (fermeture forcée) : si l'OI monte pendant
     un squeeze, ce sont des positions neuves par-dessus.
6. **Tierces à froid.** CVD en mini-liste par événement (confirme distrib / confirme accu /
   affaiblit / rien d'exploitable) ; positionnement en une synthèse « sens commun ». Toute tierce
   qui affaiblit la thèse est écrite comme risque (ex. foule à 58 % long = carburant haussier).
7. **Niveaux justifiés** : chaque prix avec la raison (événement, borne, comportement vol/OI).
8. **Hors fenêtre** : si la fenêtre demandée est passée, ajouter « Ce qui a suivi » (zone M
   dédiée) qui valide ou invalide les scénarios, séparé du verdict « à l'heure de fin ».

---

## 5. Le fichier `notes.json`

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
| `events[]` | `id`, `name`, `time`, `where` (high/low), `kind`, `verdict`, `sense`, `theory_of`, `bias` | `sense` = colonne « Volume + OI = sens » (attendu → observé → interprétation). vol×/spread/CLV/ΔOI sont lus automatiquement sur la barre |
| `text` | Les sections, en mini-markdown | Voir §6 |
| `footer` | La phrase « mémo théorie » propre à cette structure | Obligatoire |

- **`kind`** (couleur sur le graphe uniquement) : `demand` vert · `supply` rouge · `trap` orange ·
  `range` bleu · `pivot` violet.
- **`theory_of`** : clé du mémo théorie (BC, AR, ST, SOW, UTAD, LPSY, SC, SPRING, SOS, LPS) ;
  `bias` sur l'événement si son cadre diffère des notes (ex. Spring ? → `accumulation`).
  Événement hors liste (ex. « Absorption ») → écrire `theory` à la main.
- **IDs** : `SP?`, `SOS?` acceptés. Références dans le texte : `{N1}`, `{M2}`, `{SOW}`.
- Vérifier chaque chiffre du `sense` et des zones contre les données (pas de valeur de tête).

---

## 6. Plan du texte (sections `###`, dans cet ordre)

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

## 7. Générer, vérifier, publier

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

## 8. Ce que le générateur fait déjà (ne pas le refaire à la main)

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

## 9. Pièges déjà rencontrés

| Piège | Parade |
|---|---|
| OI 2h faux / tronqué | Corrigé dans `data.py` ; si une nouvelle TF apparaît, l'ajouter à `_TF_MIN`, `_COINALYZE_INTERVAL`, `_TF_FREQ` et à la base fine de `fetch_open_interest_ohlc` |
| Clé Coinalyze absente (401) | `request_credential` sur `api.coinalyze.net`, en-tête `api_key` |
| Niveau hors des données chargées (ex. 74 968 du 14/09 en 2h) | Le pointillé part de la gauche : normal ; le dire si utile |
| Niveau dont le prix n'est pas un high/low exact | Mettre `from` (heure CEST de la bougie d'origine) |
| « Longs piégés » quand l'OI monte sur une baisse | Écrire les deux côtés : shorts neufs (passifs ou agressifs selon CVD) face à des longs neufs ; attribuer avec CVD + L/S + liquidations |
| Liquidations de shorts + OI qui monte | Positions neuves par-dessus, pas les liquidations |
| Dernière bougie incomplète | Ne pas l'étiqueter ; signaler la clôture attendue |
| Squeeze lu comme SOS | SOS exige OI coin↑ (longs neufs) + tenue + back-up ; sinon « tentative » |
| Titre d'onglet trop long | `page_title` court ; le long va dans `title` |
| Tableau qui déborde | Verdicts courts (« validé, OI ambigu ») |

---

## 10. Où sont les règles

- `CLAUDE.md` : règles de fond (top-down, fractal, grammaire AR/ST, OI coin, tierces à froid,
  CVD, niveaux justifiés), format canonique en 5 sections, interdits, « Format interactif (défaut) ».
- `memos/doctrine_nuances.md` : nuances de lecture apprises en séance.
- `memos/memo_theorie.html` (généré) : seuils et OI attendu par événement.
- `screener/interactive.py` + `tests/test_interactive.py` : le rendu et ses tests.
- Ce mémo : la procédure complète et les pièges. **Toute nouvelle convention validée par
  Gauthier sur la page s'ajoute ici et dans le code** (sinon une prochaine session l'oubliera).
