// CODEX 451 — paramètres réglables du jeu.
// Tout est modifiable ici sans toucher au reste du code.

export const CONFIG = {
  port: Number(process.env.PORT) || 3000,

  // Durée par défaut d'une question (ms). Réglable aussi en direct par le prof.
  timeLimitMs: 20000,

  // Barème.
  scoring: {
    base: 500, // points garantis pour une bonne réponse
    speedMax: 500, // bonus max si réponse instantanée (dégressif jusqu'à 0)
    streakStep: 50, // bonus par bonne réponse consécutive
    streakCap: 5, // plafond du multiplicateur de série
  },

  // Nombre de questions tirées par manche.
  questionsPerRound: 3,

  // Programme des manches : difficulté croissante. Chaque manche cible un thème
  // de la banque (data/questions.json). La dernière est la FINALE en mort subite.
  rounds: [
    { theme: "classes", titre: "Manche 1 — Les classes grammaticales" },
    { theme: "phrase_types_formes", titre: "Manche 2 — Types & formes de phrase" },
    { theme: "fonctions", titre: "Manche 3 — Les fonctions" },
    { theme: "expansions_nom", titre: "Manche 4 — Les expansions du nom" },
    { theme: "conjugaison", titre: "Manche 5 — Conjugaison : temps & modes" },
    { theme: "phrase_complexe", titre: "Manche 6 — La phrase complexe" },
    { theme: "subordonnees", titre: "Manche 7 — Les subordonnées" },
    { theme: "paroles_rapportees", titre: "Manche 8 — Les paroles rapportées" },
    { theme: "valeurs_temps", titre: "Manche 9 — Valeurs des temps & concordance" },
    { theme: "lexique", titre: "Manche 10 — Le lexique" },
    { theme: "finale", titre: "FINALE — Le Codex (style, registres, connecteurs)", finale: true },
  ],
};

// Calcule combien de Passeurs survivent APRÈS chaque manche, de façon adaptative
// au nombre réel de joueurs présents. Courbe DOUCE : on garde beaucoup de monde
// en jeu, déclin linéaire régulier de n vers 3, puis paliers finaux 3 → 2 → 1.
// On ne descend donc à 3 finalistes qu'à l'avant-avant-dernière manche.
export function eliminationSchedule(playerCount, numRounds) {
  const n = Math.max(1, playerCount);
  const sched = [];
  const podiumRound = Math.max(1, numRounds - 2); // manche (1-indexée) où l'on vise 3
  for (let i = 1; i <= numRounds; i++) {
    let target;
    if (i >= numRounds) target = 1;            // finale : un seul Gardien du Codex
    else if (i === numRounds - 1) target = 2;  // duel juste avant la finale
    else if (i >= podiumRound) target = 3;     // palier des 3 finalistes
    else target = Math.round(n - (n - 3) * (i / podiumRound)); // déclin doux n → 3
    target = Math.max(1, Math.min(n, target));
    sched.push(target);
  }
  // Force une suite strictement non croissante.
  for (let i = 1; i < numRounds; i++) {
    if (sched[i] > sched[i - 1]) sched[i] = sched[i - 1];
  }
  return sched;
}
