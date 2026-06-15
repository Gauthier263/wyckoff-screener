// CODEX 451 — éditeur des questions (maître).
const THEMES = [
  ["classes", "Classes grammaticales"],
  ["phrase_types_formes", "Types & formes de phrase"],
  ["fonctions", "Les fonctions"],
  ["expansions_nom", "Les expansions du nom"],
  ["conjugaison", "Conjugaison : temps & modes"],
  ["phrase_complexe", "La phrase complexe"],
  ["subordonnees", "Les subordonnées"],
  ["paroles_rapportees", "Les paroles rapportées"],
  ["valeurs_temps", "Valeurs des temps & concordance"],
  ["lexique", "Le lexique"],
  ["finale", "Finale (style, registres, connecteurs)"],
];
const TYPE_LBL = { qcm: "QCM", vraifaux: "Vrai / Faux", saisie: "Réponse à taper", classer: "Glisser-classer" };
const $ = (id) => document.getElementById(id);

let bank = { questions: [] };
let dirty = false;

init();
async function init() {
  const r = await fetch("/api/bank");
  bank = await r.json();
  render();
}

function setEtat(msg, cls) {
  const el = $("etat");
  el.textContent = msg;
  el.className = "etat " + cls;
}
function marquerModifie() {
  dirty = true;
  setEtat("Modifications non enregistrées — clique sur « Enregistrer ».", "warn");
  majResume();
}
window.addEventListener("beforeunload", (e) => { if (dirty) { e.preventDefault(); e.returnValue = ""; } });

function majResume() {
  const total = bank.questions.length;
  const valides = bank.questions.filter((q) => q.valide).length;
  $("resume").textContent = `${valides} / ${total} validées`;
  // met à jour les compteurs par thème
  document.querySelectorAll("[data-compte]").forEach((el) => {
    const th = el.getAttribute("data-compte");
    const qs = bank.questions.filter((q) => q.theme === th);
    el.textContent = `${qs.filter((q) => q.valide).length} / ${qs.length} validées`;
  });
}

function render() {
  const liste = $("liste");
  liste.innerHTML = "";
  for (const [theme, titre] of THEMES) {
    const qs = bank.questions.filter((q) => q.theme === theme);
    if (!qs.length) continue;
    const bloc = document.createElement("section");
    bloc.className = "theme-bloc";
    const tete = document.createElement("div");
    tete.className = "theme-tete";
    tete.innerHTML = `<h2>${titre}</h2><span class="compte" data-compte="${theme}"></span>`;
    const btnT = document.createElement("button");
    btnT.className = "btn secondaire";
    btnT.textContent = "Valider tout ce thème";
    btnT.onclick = () => { qs.forEach((q) => (q.valide = true)); render(); marquerModifie(); };
    tete.appendChild(btnT);
    bloc.appendChild(tete);
    for (const q of qs) bloc.appendChild(carteQuestion(q));
    liste.appendChild(bloc);
  }
  majResume();
}

function carteQuestion(q) {
  const c = document.createElement("div");
  c.className = "q-edit" + (q.valide ? " valide" : "");

  // En-tête : type, id, bascule "validée"
  const tete = document.createElement("div");
  tete.className = "q-tete";
  tete.innerHTML = `<span class="badge">${TYPE_LBL[q.type] || q.type}</span><span class="badge">diff. ${q.difficulte || "?"}</span><span class="id">${q.id}</span>`;
  const toggle = document.createElement("label");
  toggle.className = "toggle";
  const chk = document.createElement("input");
  chk.type = "checkbox";
  chk.checked = !!q.valide;
  const lbl = document.createElement("span");
  const setLbl = () => { lbl.textContent = q.valide ? "Proposée ✓" : "En attente"; lbl.className = q.valide ? "lbl-on" : "lbl-off"; };
  setLbl();
  chk.onchange = () => { q.valide = chk.checked; c.classList.toggle("valide", q.valide); setLbl(); marquerModifie(); };
  toggle.appendChild(chk);
  toggle.appendChild(lbl);
  tete.appendChild(toggle);
  c.appendChild(tete);

  // Énoncé
  c.appendChild(champTexte("Énoncé", q.prompt, (v) => (q.prompt = v)));

  // Zone réponse selon le type
  if (q.type === "qcm") c.appendChild(zoneQcm(q));
  else if (q.type === "vraifaux") c.appendChild(zoneVraiFaux(q));
  else if (q.type === "saisie") c.appendChild(zoneSaisie(q));
  else if (q.type === "classer") c.appendChild(zoneClasser(q));

  // Explication
  c.appendChild(champTexte("Explication (affichée à la révélation)", q.explication, (v) => (q.explication = v)));
  return c;
}

function champTexte(label, valeur, onChange) {
  const d = document.createElement("div");
  d.className = "champ";
  const l = document.createElement("label");
  l.textContent = label;
  const t = document.createElement("textarea");
  t.value = valeur || "";
  t.oninput = () => { onChange(t.value); marquerModifie(); };
  d.appendChild(l);
  d.appendChild(t);
  return d;
}

function zoneQcm(q) {
  const d = document.createElement("div");
  d.className = "champ";
  d.innerHTML = `<label>Choix (coche la bonne réponse)</label>`;
  const opts = document.createElement("div");
  opts.className = "opts";
  (q.options || []).forEach((opt, i) => {
    const ligne = document.createElement("div");
    ligne.className = "opt-ligne";
    const radio = document.createElement("input");
    radio.type = "radio";
    radio.name = "sol-" + q.id;
    radio.checked = q.solution === i;
    radio.onchange = () => { q.solution = i; marquerModifie(); maj(); };
    const txt = document.createElement("input");
    txt.type = "text";
    txt.value = opt;
    txt.oninput = () => { q.options[i] = txt.value; marquerModifie(); };
    const tag = document.createElement("span");
    tag.className = "juste";
    const maj = () => (tag.textContent = q.solution === i ? "← juste" : "");
    maj();
    ligne.appendChild(radio);
    ligne.appendChild(txt);
    ligne.appendChild(tag);
    opts.appendChild(ligne);
  });
  d.appendChild(opts);
  return d;
}

function zoneVraiFaux(q) {
  const d = document.createElement("div");
  d.className = "champ";
  d.innerHTML = `<label>Bonne réponse</label>`;
  const box = document.createElement("div");
  box.className = "vf-choix";
  for (const [val, txt] of [[true, "Vrai"], [false, "Faux"]]) {
    const l = document.createElement("label");
    const r = document.createElement("input");
    r.type = "radio";
    r.name = "vf-" + q.id;
    r.checked = q.solution === val;
    r.onchange = () => { q.solution = val; marquerModifie(); };
    l.appendChild(r);
    l.appendChild(document.createTextNode(" " + txt));
    box.appendChild(l);
  }
  d.appendChild(box);
  return d;
}

function zoneSaisie(q) {
  const d = document.createElement("div");
  d.className = "champ";
  d.innerHTML = `<label>Réponses acceptées (une par ligne — casse et accents ignorés)</label>`;
  const t = document.createElement("textarea");
  t.value = (q.accepted || []).join("\n");
  t.oninput = () => {
    q.accepted = t.value.split("\n").map((s) => s.trim()).filter(Boolean);
    marquerModifie();
  };
  const aide = document.createElement("div");
  aide.className = "aide";
  aide.textContent = "La 1re ligne est la réponse « modèle » affichée à la révélation.";
  d.appendChild(t);
  d.appendChild(aide);
  return d;
}

function zoneClasser(q) {
  const d = document.createElement("div");
  d.className = "champ";
  d.innerHTML = `<label>Classement attendu</label>`;
  const lbl = Object.fromEntries((q.buckets || []).map((b) => [b.id, b.label]));
  const ro = document.createElement("div");
  ro.className = "classer-ro";
  ro.innerHTML = (q.items || []).map((it) => `• <b>${escapeHtml(it.texte)}</b> → ${escapeHtml(lbl[q.solution?.[it.id]] || "?")}`).join("<br>") +
    `<div class="aide">L'édition fine d'un « glisser-classer » se fait dans data/questions.json. Ici tu peux ajuster l'énoncé, l'explication et la validation.</div>`;
  d.appendChild(ro);
  return d;
}

function escapeHtml(s) { return String(s ?? "").replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c])); }

// --- Boutons globaux ------------------------------------------------------
$("btn-tout-valider").onclick = () => { bank.questions.forEach((q) => (q.valide = true)); render(); marquerModifie(); };
$("btn-tout-devalider").onclick = () => { bank.questions.forEach((q) => (q.valide = false)); render(); marquerModifie(); };
$("btn-save").onclick = enregistrer;
$("btn-save2").onclick = enregistrer;

async function enregistrer() {
  setEtat("Enregistrement…", "warn");
  try {
    const r = await fetch("/api/bank", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ questions: bank.questions }),
    });
    const data = await r.json();
    if (!r.ok || !data.ok) throw new Error(data.error || "Erreur serveur");
    dirty = false;
    const v = data.validated?._totalValides ?? bank.questions.filter((q) => q.valide).length;
    setEtat(`Enregistré ✓ — ${v} question(s) validée(s) sont maintenant proposées aux élèves.`, "ok");
    majResume();
  } catch (e) {
    setEtat("Échec de l'enregistrement : " + e.message, "err");
  }
}
