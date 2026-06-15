// CODEX 451 — logique de la tablette élève.
const socket = io();
const $ = (id) => document.getElementById(id);
const LETTERS = ["A", "B", "C", "D", "E", "F"];

let token = localStorage.getItem("codex451_token") || null;
let pseudo = localStorage.getItem("codex451_pseudo") || "";
let alive = true;
let chronoRAF = null;
let currentQ = null;

const VUES = ["join", "attente", "question", "envoye", "reveal", "mort", "fin"];
function montrer(vue) {
  for (const v of VUES) $("vue-" + v).classList.toggle("cache", v !== vue);
}

// --- Connexion ------------------------------------------------------------
$("pseudo").value = pseudo;
$("btn-join").onclick = rejoindre;
$("pseudo").addEventListener("keydown", (e) => { if (e.key === "Enter") rejoindre(); });

function rejoindre() {
  const val = $("pseudo").value.trim();
  if (!val) { $("join-err").classList.remove("cache"); return; }
  pseudo = val;
  localStorage.setItem("codex451_pseudo", pseudo);
  socket.emit("player:join", { token, pseudo });
}

// Reconnexion automatique si on a déjà un jeton.
socket.on("connect", () => {
  if (token) socket.emit("player:join", { token, pseudo });
});

socket.on("you", (you) => {
  token = you.token;
  localStorage.setItem("codex451_token", token);
  pseudo = you.pseudo;
  alive = you.alive;
  majEntete(you.score);
});

socket.on("state", (s) => {
  $("entete").classList.remove("cache");
  $("attente-pseudo").textContent = pseudo;
  if (s.you) { alive = s.you.alive; majEntete(s.you.score); }
  if (s.phase === "lobby") montrer("attente");
  else if (s.phase === "question" && s.question) {
    afficherQuestion(s.question, s.alreadyAnswered);
  } else if (s.phase === "gameover") {
    /* on attend l'event gameOver */
  } else {
    montrer("attente");
  }
});

function majEntete(score) {
  $("moi-pseudo").textContent = pseudo;
  if (typeof score === "number") $("moi-score").textContent = score;
  const st = $("moi-statut");
  st.textContent = alive ? "Passeur" : "Fantôme";
  st.classList.toggle("fantome", !alive);
}

// --- Question -------------------------------------------------------------
socket.on("question", (q) => afficherQuestion(q, false));

function afficherQuestion(q, dejaRepondu) {
  currentQ = q;
  montrer("question");
  $("q-meta").textContent = `${q.roundTitre} — Question ${q.qIndex + 1}/${q.qTotal}`;
  $("q-prompt").textContent = q.prompt;
  $("q-zone").innerHTML = "";
  demarrerChrono(q.startAt, q.timeLimitMs);
  if (dejaRepondu) { montrer("envoye"); return; }
  if (q.type === "qcm") renduQcm(q);
  else if (q.type === "vraifaux") renduVraiFaux();
  else if (q.type === "saisie") renduSaisie();
  else if (q.type === "classer") renduClasser(q);
}

function envoyer(answer) {
  socket.emit("player:answer", { answer });
  montrer("envoye");
}

function renduQcm(q) {
  const zone = $("q-zone");
  q.options.forEach((o, i) => {
    const b = document.createElement("button");
    b.className = "rep";
    b.innerHTML = `<span class="lettre">${LETTERS[i]}</span>${esc(o)}`;
    b.onclick = () => envoyer(i);
    zone.appendChild(b);
  });
}

function renduVraiFaux() {
  const zone = $("q-zone");
  const mk = (txt, val, cls) => {
    const b = document.createElement("button");
    b.className = "rep " + cls;
    b.innerHTML = `<span class="lettre">${val ? "V" : "F"}</span>${txt}`;
    b.onclick = () => envoyer(val);
    return b;
  };
  zone.appendChild(mk("Vrai", true, "vrai"));
  zone.appendChild(mk("Faux", false, "faux"));
}

function renduSaisie() {
  const zone = $("q-zone");
  zone.innerHTML =
    `<div class="saisie-zone"><input id="saisie-input" placeholder="Ta réponse…" autocomplete="off" />` +
    `<button id="saisie-btn" class="btn">Valider</button></div>`;
  const input = $("saisie-input");
  input.focus();
  const go = () => { if (input.value.trim()) envoyer(input.value.trim()); };
  $("saisie-btn").onclick = go;
  input.addEventListener("keydown", (e) => { if (e.key === "Enter") go(); });
}

// Classer : on tape un item puis une catégorie pour l'y placer.
function renduClasser(q) {
  const assign = {};
  let selected = null;
  const zone = $("q-zone");

  function dessiner() {
    const items = q.items.map((it) =>
      `<span class="cl-item ${selected === it.id ? "choisi" : ""} ${assign[it.id] ? "place" : ""}" data-item="${it.id}">${esc(it.texte)}</span>`
    ).join("");
    const buckets = q.buckets.map((b) => {
      const dedans = q.items.filter((it) => assign[it.id] === b.id)
        .map((it) => `<span class="place-dedans" data-item="${it.id}">${esc(it.texte)}</span>`).join("");
      return `<div class="cl-bucket" data-bucket="${b.id}"><div class="titre">${esc(b.label)}</div><div class="contenu">${dedans}</div></div>`;
    }).join("");
    const tousPlaces = q.items.every((it) => assign[it.id]);
    zone.innerHTML =
      `<p class="classer-consigne">Touche une étiquette, puis sa catégorie.</p>` +
      `<div class="classer-items">${items}</div>` +
      `<div class="classer-buckets">${buckets}</div>` +
      `<button id="cl-valider" class="btn btn-valider" ${tousPlaces ? "" : "disabled"}>Valider le classement</button>`;
    // étiquettes (libres ou déjà placées) → sélection
    zone.querySelectorAll("[data-item]").forEach((el) => {
      el.onclick = () => { selected = el.getAttribute("data-item"); dessiner(); };
    });
    // catégories → placement
    zone.querySelectorAll("[data-bucket]").forEach((el) => {
      el.onclick = () => { if (selected) { assign[selected] = el.getAttribute("data-bucket"); selected = null; dessiner(); } };
    });
    $("cl-valider").onclick = () => envoyer(assign);
  }
  dessiner();
}

// --- Chrono ---------------------------------------------------------------
function demarrerChrono(startAt, total) {
  cancelAnimationFrame(chronoRAF);
  const jauge = $("chrono");
  function tick() {
    const reste = Math.max(0, total - (Date.now() - startAt));
    jauge.style.width = (reste / total) * 100 + "%";
    if (reste > 0) chronoRAF = requestAnimationFrame(tick);
  }
  tick();
}

// --- Révélation -----------------------------------------------------------
socket.on("reveal", (r) => {
  cancelAnimationFrame(chronoRAF);
  if (!r.you) return;
  alive = r.you.alive;
  majEntete(r.you.score);
  if (!r.you.answered && !alive) { /* fantôme qui n'a pas joué */ }
  montrer("reveal");
  const vue = $("vue-reveal");
  const bon = r.you.correct;
  vue.classList.toggle("bon", bon);
  vue.classList.toggle("mauvais", !bon);
  $("reveal-icone").textContent = !r.you.answered ? "⏳" : bon ? "🔥" : "💨";
  $("reveal-titre").textContent = !r.you.answered ? "Trop tard !" : bon ? "Bonne réponse !" : "Raté…";
  $("reveal-points").textContent = bon && r.you.points ? "+" + r.you.points + " pts" : "";
  $("reveal-explication").textContent = r.explication || "";
  $("reveal-rang").textContent = r.you.rank ? `Tu es ${r.you.rank}${r.you.rank === 1 ? "er" : "e"} — ${r.you.score} pts` : `${r.you.score} pts`;
});

// --- Élimination ----------------------------------------------------------
socket.on("eliminated", ({ finalScore }) => {
  alive = false;
  majEntete(finalScore);
  montrer("mort");
  $("mort-score").textContent = finalScore + " pts";
});

// --- Fin de partie --------------------------------------------------------
socket.on("gameOver", ({ winner }) => {
  cancelAnimationFrame(chronoRAF);
  montrer("fin");
  const gagne = winner && alive && winner.pseudo === pseudo;
  $("vue-fin").classList.toggle("gagnant", !!gagne);
  $("fin-icone").textContent = gagne ? "🦅" : "📖";
  $("fin-titre").textContent = gagne ? "Tu es le Gardien du Codex !" : "Partie terminée";
  $("fin-detail").textContent = winner ? `Vainqueur : ${winner.pseudo} (${winner.score} pts)` : "";
});

socket.on("reset", () => { alive = true; montrer("attente"); majEntete(0); });

function esc(s) { return String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c])); }
