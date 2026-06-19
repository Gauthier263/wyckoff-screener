// CODEX 451 — serveur local de classe.
// Lance : `npm start`  puis les tablettes ouvrent http://<IP-du-PC>:3000/play
// L'écran maître (projeté) : http://localhost:3000/

import http from "node:http";
import { readFileSync, writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import os from "node:os";

import express from "express";
import { Server } from "socket.io";
import QRCode from "qrcode";

import { CONFIG } from "./game/config.js";
import { GameEngine } from "./game/engine.js";

const __dirname = dirname(fileURLToPath(import.meta.url));
const BANK_PATH = join(__dirname, "data", "questions.json");

// --- Banque de questions, groupée par thème -------------------------------
let bankRaw = JSON.parse(readFileSync(BANK_PATH, "utf8"));
function groupByTheme(questions) {
  const by = {};
  for (const q of questions) (by[q.theme] ||= []).push(q);
  return by;
}

// --- App / serveur ---------------------------------------------------------
const app = express();
const server = http.createServer(app);
const io = new Server(server);
const engine = new GameEngine(io, groupByTheme(bankRaw.questions));

app.use(express.json({ limit: "4mb" }));
app.use(express.static(join(__dirname, "public")));

app.get("/", (_req, res) => res.sendFile(join(__dirname, "public", "host.html")));
app.get("/play", (_req, res) => res.sendFile(join(__dirname, "public", "play.html")));
app.get("/admin", (_req, res) => res.sendFile(join(__dirname, "public", "admin.html")));

// --- Éditeur : lire / enregistrer la banque -------------------------------
app.get("/api/bank", (_req, res) => res.json(bankRaw));

app.post("/api/bank", (req, res) => {
  const questions = req.body?.questions;
  if (!Array.isArray(questions) || questions.length === 0) {
    return res.status(400).json({ ok: false, error: "Format invalide." });
  }
  bankRaw = { ...bankRaw, questions };
  try {
    writeFileSync(BANK_PATH, JSON.stringify(bankRaw, null, 2) + "\n", "utf8");
  } catch (e) {
    return res.status(500).json({ ok: false, error: "Écriture impossible : " + e.message });
  }
  engine.setBank(groupByTheme(questions));
  res.json({ ok: true, validated: engine.validatedCounts() });
});

// Adresse LAN + QR code, pour que les élèves rejoignent en un scan.
function lanAddress() {
  for (const iface of Object.values(os.networkInterfaces())) {
    for (const net of iface || []) {
      if (net.family === "IPv4" && !net.internal) return net.address;
    }
  }
  return "localhost";
}

app.get("/join-info", async (_req, res) => {
  const url = `http://${lanAddress()}:${CONFIG.port}/play`;
  let qr = null;
  try {
    qr = await QRCode.toDataURL(url, { margin: 1, width: 320 });
  } catch {
    /* QR optionnel */
  }
  res.json({ url, qr });
});

// --- Sockets ---------------------------------------------------------------
io.on("connection", (socket) => {
  // Écran maître
  socket.on("host:join", () => {
    socket.join("host");
    socket.emit("host:state", engine.hostSnapshot());
    engine.broadcastPlayers();
  });
  socket.on("host:start", (opts) => engine.hostStart(opts || {}));
  socket.on("host:reveal", () => engine.reveal());
  socket.on("host:next", () => engine.hostNext());
  socket.on("host:reset", (opts) => engine.hostReset(opts || {}));

  // Élève
  socket.on("player:join", (data) => engine.join(socket, data || {}));
  socket.on("player:answer", (data) => {
    if (socket.data.token) engine.playerAnswer(socket.data.token, data?.answer);
  });

  socket.on("disconnect", () => engine.disconnect(socket));
});

server.listen(CONFIG.port, () => {
  const url = `http://${lanAddress()}:${CONFIG.port}`;
  console.log("\n🔥  CODEX 451 — Les Derniers Passeurs");
  console.log("──────────────────────────────────────");
  console.log(`   Écran maître (projeté) : ${url}/  (ou http://localhost:${CONFIG.port}/)`);
  console.log(`   Tablettes des élèves   : ${url}/play`);
  console.log(`   Gérer les questions    : ${url}/admin`);
  const valides = engine.validatedCounts()._totalValides;
  console.log(`   Banque : ${bankRaw.questions.length} questions (${valides} validée(s) / proposée(s)).`);
  if (valides === 0) console.log(`   ⚠ Aucune question validée : ouvre /admin pour en proposer aux élèves.`);
  console.log("──────────────────────────────────────\n");
});
