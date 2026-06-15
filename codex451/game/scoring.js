// CODEX 451 — barème, normalisation et validation des réponses.

import { CONFIG } from "./config.js";

// Normalise une saisie libre : minuscules, sans accents, espaces compactés,
// ponctuation de bord retirée. Permet une auto-correction tolérante.
export function normalize(str) {
  return String(str ?? "")
    .toLowerCase()
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "") // enlève les accents
    .replace(/[.,;:!?'"«»()]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

// Vérifie une réponse selon le type de question. `answer` vient du client.
export function isCorrect(question, answer) {
  switch (question.type) {
    case "qcm":
      return Number(answer) === Number(question.solution);

    case "vraifaux":
      return Boolean(answer) === Boolean(question.solution);

    case "saisie": {
      const got = normalize(answer);
      if (!got) return false;
      return (question.accepted || []).some((a) => normalize(a) === got);
    }

    case "classer": {
      // answer = { itemId: bucketId, ... } ; solution = même structure.
      if (!answer || typeof answer !== "object") return false;
      const sol = question.solution || {};
      const keys = Object.keys(sol);
      if (keys.length === 0) return false;
      return keys.every((k) => String(answer[k]) === String(sol[k]));
    }

    default:
      return false;
  }
}

// Points pour une bonne réponse, fonction du temps restant et de la série.
export function pointsFor({ correct, timeLeftMs, totalMs, streak }) {
  if (!correct) return 0;
  const { base, speedMax, streakStep, streakCap } = CONFIG.scoring;
  const ratio = totalMs > 0 ? Math.max(0, Math.min(1, timeLeftMs / totalMs)) : 0;
  const speed = Math.round(speedMax * ratio);
  const streakBonus = streakStep * Math.min(Math.max(0, streak), streakCap);
  return base + speed + streakBonus;
}
