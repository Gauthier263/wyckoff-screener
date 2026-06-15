// CODEX 451 — génère une page de RELECTURE imprimable à partir d'un fichier
// de questions. Usage :
//   npm run revision                 -> relit data/propositions.json
//   node game/revision.js data/questions.json
// Produit RELECTURE.html à la racine du projet : à ouvrir dans un navigateur.

import { readFileSync, writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { CONFIG } from "./config.js";

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, "..");
const target = process.argv[2] || join(ROOT, "data", "propositions.json");
const bank = JSON.parse(readFileSync(target, "utf8"));

const TYPE_LBL = { qcm: "QCM", vraifaux: "Vrai / Faux", saisie: "Réponse à taper", classer: "Glisser-classer" };
const THEME_LBL = Object.fromEntries(CONFIG.rounds.map((r) => [r.theme, r.titre]));

function esc(s) {
  return String(s ?? "").replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));
}

// Réponse correcte mise en forme, lisible par un humain.
function bonneReponse(q) {
  if (q.type === "qcm") return esc(q.options?.[q.solution] ?? "?");
  if (q.type === "vraifaux") return q.solution ? "VRAI" : "FAUX";
  if (q.type === "saisie") return esc((q.accepted || [])[0] ?? "?");
  if (q.type === "classer") {
    const lbl = Object.fromEntries((q.buckets || []).map((b) => [b.id, b.label]));
    return (q.items || []).map((it) => `${esc(it.texte)} → ${esc(lbl[q.solution?.[it.id]] ?? "?")}`).join("<br>");
  }
  return "?";
}

// Détails complémentaires selon le type.
function details(q) {
  if (q.type === "qcm") {
    return `<div class="meta">Choix proposés : ${(q.options || []).map((o, i) => `${i === q.solution ? "<b>" : ""}${esc(o)}${i === q.solution ? " ✓</b>" : ""}`).join(" · ")}</div>`;
  }
  if (q.type === "saisie") {
    return `<div class="meta">Réponses acceptées (tolérance casse/accents) : ${(q.accepted || []).map((a) => `« ${esc(a)} »`).join(", ")}</div>`;
  }
  return "";
}

const byTheme = {};
for (const q of bank.questions) (byTheme[q.theme] ||= []).push(q);

const counts = {};
for (const q of bank.questions) counts[q.type] = (counts[q.type] || 0) + 1;
const n = bank.questions.length;
const pctQcm = Math.round((counts.qcm || 0) / n * 100);

let body = "";
for (const round of CONFIG.rounds) {
  const qs = byTheme[round.theme];
  if (!qs) continue;
  body += `<section><h2>${esc(THEME_LBL[round.theme] || round.theme)}</h2>`;
  for (const q of qs) {
    body += `<article class="q ${q.type}">
      <div class="tags"><span class="tag">${TYPE_LBL[q.type] || q.type}</span><span class="tag diff">difficulté ${q.difficulte || "?"}</span><span class="id">${esc(q.id)}</span></div>
      <div class="prompt">${esc(q.prompt)}</div>
      ${details(q)}
      <div class="rep"><span class="rep-lbl">✅ Bonne réponse :</span> ${bonneReponse(q)}</div>
      <div class="expl">💡 ${esc(q.explication || "")}</div>
      <div class="corrige">Correction éventuelle : _______________________________________________</div>
    </article>`;
  }
  body += `</section>`;
}

const html = `<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8">
<title>CODEX 451 — Relecture des questions</title>
<style>
  body { font-family: Georgia, "Times New Roman", serif; max-width: 900px; margin: 0 auto; padding: 24px; color: #1a1a1a; }
  h1 { color: #c0390a; }
  .resume { background: #fff3e8; border: 1px solid #f0c9ab; border-radius: 8px; padding: 12px 16px; margin-bottom: 24px; }
  h2 { margin-top: 36px; border-bottom: 2px solid #c0390a; padding-bottom: 4px; color: #7a2406; }
  .q { border: 1px solid #ddd; border-radius: 8px; padding: 12px 16px; margin: 14px 0; page-break-inside: avoid; }
  .q.qcm { background: #fbfbfb; }
  .tags { font-size: 12px; color: #666; margin-bottom: 6px; }
  .tag { background: #eee; border-radius: 4px; padding: 1px 7px; margin-right: 6px; }
  .tag.diff { background: #e7eefb; }
  .id { float: right; color: #aaa; font-family: monospace; }
  .prompt { font-size: 17px; font-weight: bold; margin: 4px 0; }
  .meta { font-size: 14px; color: #444; margin: 6px 0; }
  .rep { margin: 8px 0; font-size: 16px; }
  .rep-lbl { color: #137a39; font-weight: bold; }
  .expl { font-size: 14px; color: #555; font-style: italic; }
  .corrige { margin-top: 10px; font-size: 13px; color: #999; }
  @media print { .q { border-color: #bbb; } }
</style></head><body>
<h1>🔥 CODEX 451 — Relecture des questions</h1>
<div class="resume">
  <b>${n} questions</b> à valider · répartition : ${Object.entries(counts).map(([t, k]) => `${TYPE_LBL[t] || t} ${k} (${Math.round(k / n * 100)}%)`).join(" · ")}.<br>
  Part de QCM : <b>${pctQcm}%</b> (objectif : ≤ 20 %).<br>
  Lis chaque question, vérifie la « ✅ Bonne réponse » et les réponses acceptées. Note tes corrections sur la ligne prévue (ou dis-les-moi directement), puis je les intègre au jeu.
</div>
${body}
</body></html>`;

const out = join(ROOT, "RELECTURE.html");
writeFileSync(out, html, "utf8");
console.log(`Page de relecture générée : ${out}`);
console.log(`${n} questions — QCM ${pctQcm}% (objectif ≤ 20%).`);
