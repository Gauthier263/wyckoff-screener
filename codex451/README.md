# 🔥 CODEX 451 — Les Derniers Passeurs

Jeu de grammaire **multijoueur** pour une classe de 3e, dans un univers de
science-fiction inspiré de *Fahrenheit 451* (Ray Bradbury).

> 2099. Le *Ministère de la Clarté* brûle la langue complexe. Les élèves sont
> les **Passeurs**, une résistance qui mémorise la grammaire pour sauver les
> livres. À chaque manche, les plus faibles sont *effacés* (leur livre brûle).
> Le dernier debout devient le **Gardien du Codex**.

## Principe
- Les questions sont **pilotées par le professeur** depuis un écran projeté (type Kahoot).
- Chaque **manche porte sur un thème grammatical**, de plus en plus difficile.
- Score **en direct** = bonne réponse + bonus de rapidité + bonus de série.
- **Élimination par paliers (douce)** : à la fin de chaque manche, les derniers du
  classement sont éliminés (le nombre s'adapte au nombre d'élèves présents). La
  courbe garde **beaucoup de monde en jeu** : on ne descend à **3 finalistes qu'à la
  manche 9**, puis 2 (manche 10), puis 1 (finale).
- Les éliminés deviennent **fantômes** : ils continuent à jouer pour s'entraîner,
  hors classement.
- La **finale** oppose les survivants jusqu'au vainqueur.

## Thèmes couverts (11 manches)
Classes grammaticales · types & formes de phrase · fonctions · expansions du nom ·
conjugaison (temps & modes) · phrase complexe · subordonnées · paroles rapportées ·
valeurs des temps & concordance · lexique · **finale** (figures de style, registres,
connecteurs, modalisateurs).

Formats de questions : **QCM**, **Vrai/Faux**, **glisser-classer** (toucher pour
ranger), **saisie de texte** (auto-correction tolérante : casse et accents ignorés).

## Lancer le jeu (sur le PC du professeur)
```bash
cd codex451
npm install
npm start
```
Le terminal affiche deux adresses :
- **Écran maître** (à projeter) : `http://localhost:3000/`
- **Tablettes des élèves** : `http://<IP-du-PC>:3000/play`

Les tablettes doivent être sur **le même réseau Wi-Fi** que le PC.
L'écran maître affiche un **QR code** : les élèves le scannent, choisissent un
pseudo, et c'est parti.

> Astuce : si le QR ne marche pas, l'élève tape l'adresse `http://<IP>:3000/play`
> à la main. L'IP est indiquée au démarrage et sur l'écran maître.

## Déroulé d'une partie (côté professeur)
1. Les élèves rejoignent → ils apparaissent dans le lobby.
2. **Lancer la partie**.
3. Pour chaque question : le chrono tourne. Tu peux **Révéler** dès que tout le
   monde a répondu (sinon révélation automatique à la fin du temps).
4. La bonne réponse + l'explication s'affichent, ainsi que le classement.
5. **Suivant** pour enchaîner ; en fin de manche, l'écran montre les éliminés et
   les survivants.
6. À la fin : couronnement du **Gardien du Codex**.

Bouton **Réinitialiser** : remet la partie à zéro (les connectés repartent en jeu).

### Rejouer plusieurs fois (questions renouvelées)
À l'écran de victoire, deux boutons :
- **🔄 Rejouer (nouvelles questions)** : relance une partie en proposant en priorité
  les questions **pas encore posées**. On peut ainsi enchaîner plusieurs parties sans
  retomber sur les mêmes questions (quand un thème est épuisé, il est recyclé).
- **♻️ Repartir de zéro (banque vierge)** : oublie l'historique → toute la banque
  validée peut être reposée depuis le début (utile pour une nouvelle classe).

> L'historique des questions posées vit tant que le serveur tourne ; il est aussi
> remis à zéro si tu arrêtes puis relances `npm start`.

## Valider / modifier les questions (page « Gérer les questions »)
**Une question n'est proposée aux élèves que si le maître l'a validée.** Au
départ, toutes les questions sont « en attente ».

Depuis l'écran maître, clique sur **⚙ Gérer les questions** (ou ouvre
`http://localhost:3000/admin`). Sur cette page tu peux, **question par question** :
- lire l'énoncé, la bonne réponse et l'explication,
- **modifier** le texte, les choix, la bonne réponse, les réponses acceptées,
- **valider** (bascule « Proposée ✓ ») ou laisser « En attente ».

Boutons pratiques : **Valider tout ce thème**, **Tout valider**, **Tout retirer**.
Clique enfin sur **💾 Enregistrer** : les modifications sont écrites dans
`data/questions.json` et prises en compte immédiatement par le jeu.

> Astuce de démarrage : pour jouer tout de suite, ouvre /admin → **Tout valider**
> → **Enregistrer**. Tu pourras affiner ensuite.

### Page de relecture imprimable
`npm run revision` génère `RELECTURE.html` (à ouvrir dans un navigateur) : la liste
complète des questions avec réponses et explications, pratique pour relire/imprimer.

### Tests
`npm test` (utilise `node --test`) vérifie la courbe d'élimination douce et le
renouvellement des questions d'une partie à l'autre.

### Format des questions (`data/questions.json`)
| type | champs |
|------|--------|
| `qcm` | `options` (liste) + `solution` (index de la bonne, à partir de 0) |
| `vraifaux` | `solution` (`true`/`false`) |
| `saisie` | `accepted` (liste de réponses acceptées ; casse/accents/apostrophes ignorés) |
| `classer` | `items` `[{id,texte}]`, `buckets` `[{id,label}]`, `solution` `{idItem: idBucket}` |

Commun à toutes : `theme`, `difficulte` (1-3), `prompt`, `explication`, `valide`
(`true` = proposée aux élèves). Composition de la banque : ~10 % de QCM, le reste
surtout en **saisie** (réponse à taper). Après édition manuelle, vérifie : `npm run check`.

## Réglages
Dans [`game/config.js`](game/config.js) : durée par question (aussi réglable en
direct), barème, nombre de questions par manche, ordre et thèmes des manches,
courbe d'élimination.

## Architecture
```
codex451/
├── server.js            # serveur Express + Socket.io (autorité de jeu)
├── game/
│   ├── config.js        # réglages + courbe d'élimination
│   ├── scoring.js       # barème, normalisation, validation des réponses
│   ├── engine.js        # machine d'états (ne sert que les questions validées)
│   ├── validate.js      # `npm run check` : valide la banque
│   └── revision.js      # `npm run revision` : page RELECTURE.html imprimable
├── data/questions.json  # banque (champ `valide` par question)
└── public/
    ├── host.html/.js/.css   # écran maître projeté
    ├── play.html/.js/.css   # tablette élève
    ├── admin.html/.js/.css  # « Gérer les questions » (valider / modifier)
    └── shared.css           # thème Fahrenheit 451
```
Le serveur fait autorité (chrono, scores, éliminations). Les tablettes mémorisent
un jeton : en cas de coupure Wi-Fi, l'élève **se reconnecte** sans perdre son score.
