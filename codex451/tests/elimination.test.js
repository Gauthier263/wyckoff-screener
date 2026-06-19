// Tests de la courbe d'élimination douce et du renouvellement des questions.
// Lancer : npm test   (node --test)

import { test } from "node:test";
import assert from "node:assert/strict";

import { eliminationSchedule } from "../game/config.js";
import { GameEngine } from "../game/engine.js";

// --- Courbe d'élimination -------------------------------------------------
test("la courbe est non croissante et finit à 1", () => {
  for (const n of [2, 3, 10, 32, 100]) {
    const s = eliminationSchedule(n, 11);
    assert.equal(s.length, 11);
    assert.equal(s[10], 1, "la finale ne laisse qu'un vainqueur");
    for (let i = 1; i < s.length; i++) {
      assert.ok(s[i] <= s[i - 1], `palier croissant interdit (n=${n})`);
      assert.ok(s[i] >= 1 && s[i] <= n, `borne dépassée (n=${n})`);
    }
  }
});

test("on ne descend à 3 finalistes qu'à la manche 9, puis 2, puis 1", () => {
  const s = eliminationSchedule(32, 11); // index 8 = manche 9
  assert.equal(s[8], 3, "manche 9 = 3 finalistes");
  assert.equal(s[9], 2, "manche 10 = duel");
  assert.equal(s[10], 1, "finale = un Gardien");
  // Beaucoup de monde maintenu tôt : la manche 1 garde la grande majorité.
  assert.ok(s[0] >= 28, `manche 1 trop sévère : ${s[0]}`);
});

test("courbe douce attendue pour n=32 et n=10", () => {
  assert.deepEqual(eliminationSchedule(32, 11), [29, 26, 22, 19, 16, 13, 9, 6, 3, 2, 1]);
  assert.deepEqual(eliminationSchedule(10, 11), [9, 8, 8, 7, 6, 5, 5, 4, 3, 2, 1]);
});

test("petits effectifs : personne n'est éliminé avant la finale", () => {
  assert.deepEqual(eliminationSchedule(2, 11), [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1]);
});

// --- Renouvellement des questions ----------------------------------------
function fakeIo() {
  return { to: () => ({ emit() {} }), emit() {}, sockets: { sockets: new Map() } };
}
function bankOf(theme, ids) {
  return { [theme]: ids.map((id, i) => ({ id, theme, valide: true, type: "saisie", difficulte: 1 + (i % 3), prompt: id, accepted: ["x"] })) };
}

test("startRound sert d'abord des questions non encore posées", () => {
  const eng = new GameEngine(fakeIo(), bankOf("classes", ["a", "b", "c", "d", "e", "f"]));
  eng.roundIndex = 0;
  eng.startRound();
  const game1 = eng.roundQuestions.map((q) => q.id);
  assert.equal(game1.length, 3);

  // Nouvelle partie : on rejoue le même thème → questions différentes.
  eng.roundIndex = 0;
  eng.startRound();
  const game2 = eng.roundQuestions.map((q) => q.id);
  assert.equal(game2.length, 3);
  assert.equal(game1.filter((id) => game2.includes(id)).length, 0, "aucune question répétée tant qu'il en reste de neuves");
});

test("clearHistory permet de reposer toute la banque depuis le début", () => {
  const eng = new GameEngine(fakeIo(), bankOf("classes", ["a", "b", "c"]));
  eng.roundIndex = 0;
  eng.startRound();
  const first = eng.roundQuestions.map((q) => q.id).sort();

  eng.hostReset({ clearHistory: true });
  assert.equal(eng.askedIds.size, 0);
  eng.roundIndex = 0;
  eng.startRound();
  const second = eng.roundQuestions.map((q) => q.id).sort();
  assert.deepEqual(first, second, "après remise à zéro, on repropose les mêmes questions");
});

test("un thème trop petit est recyclé plutôt que de bloquer", () => {
  const eng = new GameEngine(fakeIo(), bankOf("classes", ["a", "b", "c"]));
  for (let g = 0; g < 5; g++) {
    eng.roundIndex = 0;
    eng.startRound();
    assert.equal(eng.roundQuestions.length, 3, "toujours 3 questions servies");
  }
});
