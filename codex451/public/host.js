// CODEX 451 — logique de l'écran maître (projeté).
const socket = io();
const $ = (id) => document.getElementById(id);
const LETTERS = ["A", "B", "C", "D", "E", "F"];
let chronoRAF = null;
let lastQuestion = null;

socket.on("connect", () => socket.emit("host:join"));

// --- Lien + QR pour rejoindre ---------------------------------------------
fetch("/join-info").then((r) => r.json()).then(({ url, qr }) => {
  $("join-url").textContent = url;
  if (qr) $("qr").src = qr;
  else $("qr").style.display = "none";
});

// --- Boutons --------------------------------------------------------------
$("btn-start").onclick = () => socket.emit("host:start", { timeLimitMs: Number($("time-select").value) });
$("btn-reveal").onclick = () => socket.emit("host:reveal");
$("btn-next").onclick = () => socket.emit("host:next");
$("btn-reset").onclick = () => { if (confirm("Réinitialiser la partie ?")) socket.emit("host:reset"); };
// Fin de partie : rejouer (questions encore non posées) ou repartir de zéro (banque vierge).
$("btn-rejouer").onclick = () => socket.emit("host:reset");
$("btn-zero").onclick = () => {
  if (confirm("Repartir de zéro ? Toutes les questions de la banque pourront être reposées dès le début.")) {
    socket.emit("host:reset", { clearHistory: true });
  }
};

// --- Gestion des vues -----------------------------------------------------
const VUES = ["lobby", "question", "reveal", "round", "fin"];
function montrer(vue) {
  for (const v of VUES) $("vue-" + v).classList.toggle("cache", v !== vue);
}
function boutons({ start, reveal, next, nextLabel }) {
  $("btn-start").classList.toggle("cache", !start);
  $("btn-reveal").classList.toggle("cache", !reveal);
  $("btn-next").classList.toggle("cache", !next);
  if (nextLabel) $("btn-next").textContent = nextLabel;
}

// --- État initial / reconnexion -------------------------------------------
socket.on("host:state", (s) => {
  if (s.phase === "lobby") { montrer("lobby"); boutons({ start: true }); }
  if (s.timeLimitMs) $("time-select").value = String(s.timeLimitMs);
  if (s.validated) majValide(s.validated);
});

// Compteur de questions validées (proposées aux élèves)
socket.on("host:validated", majValide);
function majValide(v) {
  const total = v._totalValides || 0;
  const el = $("lobby-valide");
  if (!el) return;
  el.classList.toggle("vide", total === 0);
  el.innerHTML = total === 0
    ? `⚠ <b>Aucune question validée.</b> Ouvre « Gérer les questions » pour en proposer aux élèves.`
    : `<b>${total}</b> question(s) validée(s) prêtes à être jouées. <span class="hint">(Gère-les via « Gérer les questions ».)</span>`;
}

// Messages / erreurs côté maître
socket.on("host:notice", ({ type, message }) => {
  const el = $("host-notice");
  el.className = "host-notice " + (type || "erreur");
  el.textContent = message;
  el.classList.remove("cache");
  clearTimeout(window._noticeT);
  window._noticeT = setTimeout(() => el.classList.add("cache"), 6000);
});

// --- Lobby : liste des joueurs --------------------------------------------
socket.on("players", ({ players, alive }) => {
  $("lobby-count").textContent = players.length;
  $("lobby-liste").innerHTML = players.map(puce).join("");
  $("q-alive").textContent = alive;
});
function puce(p) {
  return `<span class="puce ${p.alive ? "" : "mort"}">${esc(p.pseudo)}` +
    (p.score ? ` <span class="pts">${p.score}</span>` : "") + `</span>`;
}

// --- Début de manche ------------------------------------------------------
socket.on("roundStart", (r) => {
  $("q-round").textContent = r.titre;
});

// --- Question -------------------------------------------------------------
socket.on("question", (q) => {
  lastQuestion = q;
  montrer("question");
  boutons({ reveal: true });
  $("q-round").textContent = q.roundTitre;
  $("q-index").textContent = `Question ${q.qIndex + 1} / ${q.qTotal}`;
  $("q-prompt").textContent = q.prompt;
  $("q-zone").innerHTML = renduQuestion(q);
  $("answered").textContent = "0";
  demarrerChrono(q.startAt, q.timeLimitMs);
});

socket.on("answered", ({ answered, total }) => {
  $("answered").textContent = answered;
  $("answered-total").textContent = total;
});

function renduQuestion(q) {
  if (q.type === "qcm") {
    return q.options.map((o, i) => `<div class="opt"><span class="lettre">${LETTERS[i]}</span>${esc(o)}</div>`).join("");
  }
  if (q.type === "vraifaux") {
    return `<div class="opt"><span class="lettre">V</span>Vrai</div><div class="opt"><span class="lettre">F</span>Faux</div>`;
  }
  if (q.type === "saisie") {
    return `<div class="opt">✍️ Réponse à saisir sur la tablette</div>`;
  }
  if (q.type === "classer") {
    const items = q.items.map((it) => `<span class="puce">${esc(it.texte)}</span>`).join(" ");
    const buckets = q.buckets.map((b) => `<span class="puce">${esc(b.label)}</span>`).join(" ");
    return `<div class="opt">À classer : ${items}</div><div class="opt">Catégories : ${buckets}</div>`;
  }
  return "";
}

// --- Chronomètre (le Limier approche) -------------------------------------
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
  montrer("reveal");
  boutons({ next: true, nextLabel: "Suivant ▶" });
  $("r-solution").innerHTML = texteSolution(r);
  $("r-explication").textContent = r.explication || "";
  $("r-distribution").innerHTML = renduDistribution(r);
  $("r-leaderboard").innerHTML = renduLeaderboard(r.leaderboard);
});

function texteSolution(r) {
  const q = lastQuestion || {};
  if (r.type === "qcm" && q.options) return "✔ " + esc(q.options[r.solution]);
  if (r.type === "vraifaux") return "✔ " + (r.solution ? "Vrai" : "Faux");
  if (r.type === "saisie") return "✔ " + esc((r.accepted || [])[0] || "");
  if (r.type === "classer" && q.items && q.solution) {
    const lbl = Object.fromEntries((q.buckets || []).map((b) => [b.id, b.label]));
    return "✔ " + q.items.map((it) => `${esc(it.texte)} → ${esc(lbl[r.solution[it.id]] || "")}`).join(" · ");
  }
  return "✔";
}

function renduDistribution(r) {
  const d = r.distribution || {};
  const q = lastQuestion || {};
  if (d.kind === "qcm" && q.options) {
    const max = Math.max(1, ...d.counts);
    return q.options.map((o, i) =>
      `<div class="barre-rep ${i === r.solution ? "bonne" : ""}"><span class="lbl">${LETTERS[i]}. ${esc(o)}</span>` +
      `<span class="jauge"><span style="width:${(d.counts[i] / max) * 100}%"></span></span><span class="n">${d.counts[i]}</span></div>`
    ).join("");
  }
  if (d.kind === "vraifaux") {
    const max = Math.max(1, d.vrai, d.faux);
    const row = (lbl, n, bonne) => `<div class="barre-rep ${bonne ? "bonne" : ""}"><span class="lbl">${lbl}</span><span class="jauge"><span style="width:${(n / max) * 100}%"></span></span><span class="n">${n}</span></div>`;
    return row("Vrai", d.vrai, r.solution === true) + row("Faux", d.faux, r.solution === false);
  }
  if (d.kind === "libre") {
    return `<div class="barre-rep bonne"><span class="lbl">Bonnes réponses</span><span class="jauge"><span style="width:${d.total ? (d.correct / d.total) * 100 : 0}%"></span></span><span class="n">${d.correct}/${d.total}</span></div>`;
  }
  return "";
}

function renduLeaderboard(list, limit = 12) {
  return (list || []).slice(0, limit).map((p, i) =>
    `<li class="${p.alive ? "" : "mort"} ${i === 0 ? "top1" : ""}"><span class="rang">${i + 1}</span><span class="nom">${esc(p.pseudo)}</span><span class="score">${p.score}</span></li>`
  ).join("");
}

// --- Fin de manche --------------------------------------------------------
socket.on("roundEnd", (r) => {
  montrer("round");
  boutons({ next: true, nextLabel: r.isLast ? "Couronner le vainqueur 🦅" : "Manche suivante ▶" });
  $("round-titre").textContent = r.titre;
  $("round-elimines").innerHTML = r.eliminated.length
    ? r.eliminated.map((p) => `<span class="puce mort brule">${esc(p.pseudo)} <span class="pts">${p.score}</span></span>`).join("")
    : `<span class="puce">Personne — tout le monde survit !</span>`;
  $("round-survivants-n").textContent = r.survivors.length;
  $("round-survivants").innerHTML = r.survivors.map((p) => `<span class="puce">${esc(p.pseudo)} <span class="pts">${p.score}</span></span>`).join("");
});

// --- Victoire -------------------------------------------------------------
socket.on("gameOver", ({ winner, leaderboard }) => {
  montrer("fin");
  boutons({ start: false, reveal: false, next: false });
  $("winner").textContent = winner ? winner.pseudo : "—";
  $("fin-leaderboard").innerHTML = renduLeaderboard(leaderboard, 10);
});

socket.on("reset", () => { montrer("lobby"); boutons({ start: true }); });

function esc(s) { return String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c])); }
