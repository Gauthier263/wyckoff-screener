// CODEX 451 — validation de la banque de questions.
// Usage : `npm run check`  (ou `node game/validate.js`)
// Vérifie la cohérence de data/questions.json et l'alignement avec les manches.

import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { CONFIG } from "./config.js";

const __dirname = dirname(fileURLToPath(import.meta.url));
const bank = JSON.parse(readFileSync(join(__dirname, "..", "data", "questions.json"), "utf8"));

const errors = [];
const ids = new Set();
const byTheme = {};

for (const [i, q] of bank.questions.entries()) {
  const where = `Q[${i}] (id=${q.id ?? "?"})`;
  if (!q.id) errors.push(`${where} : id manquant`);
  if (q.id && ids.has(q.id)) errors.push(`${where} : id en double`);
  ids.add(q.id);
  if (!q.theme) errors.push(`${where} : theme manquant`);
  if (!q.prompt) errors.push(`${where} : prompt manquant`);
  if (!q.explication) errors.push(`${where} : explication manquante`);
  (byTheme[q.theme] ||= 0);
  byTheme[q.theme]++;

  switch (q.type) {
    case "qcm":
      if (!Array.isArray(q.options) || q.options.length < 2)
        errors.push(`${where} : qcm doit avoir au moins 2 options`);
      if (typeof q.solution !== "number" || q.solution < 0 || q.solution >= (q.options?.length ?? 0))
        errors.push(`${where} : solution (index) hors limites`);
      break;
    case "vraifaux":
      if (typeof q.solution !== "boolean") errors.push(`${where} : vraifaux doit avoir une solution booléenne`);
      break;
    case "saisie":
      if (!Array.isArray(q.accepted) || q.accepted.length === 0)
        errors.push(`${where} : saisie doit fournir des réponses acceptées`);
      break;
    case "classer":
      if (!Array.isArray(q.items) || !Array.isArray(q.buckets) || !q.solution)
        errors.push(`${where} : classer doit avoir items, buckets et solution`);
      else {
        const bucketIds = new Set(q.buckets.map((b) => b.id));
        for (const it of q.items) {
          if (!(it.id in q.solution)) errors.push(`${where} : item « ${it.id} » sans solution`);
          else if (!bucketIds.has(q.solution[it.id]))
            errors.push(`${where} : solution de « ${it.id} » pointe vers un bucket inconnu`);
        }
      }
      break;
    default:
      errors.push(`${where} : type inconnu « ${q.type } »`);
  }
}

// Chaque manche a-t-elle assez de questions ?
for (const round of CONFIG.rounds) {
  const n = byTheme[round.theme] || 0;
  if (n < CONFIG.questionsPerRound)
    errors.push(`Manche « ${round.theme} » : ${n} question(s) pour ${CONFIG.questionsPerRound} attendues`);
}

console.log(`Banque : ${bank.questions.length} questions, ${Object.keys(byTheme).length} thèmes.`);
for (const round of CONFIG.rounds) {
  console.log(`  - ${round.theme.padEnd(22)} ${byTheme[round.theme] || 0} questions`);
}

if (errors.length) {
  console.error(`\n❌ ${errors.length} problème(s) :`);
  for (const e of errors) console.error("   " + e);
  process.exit(1);
}
console.log("\n✅ Banque valide.");
