// CODEX 451 — machine d'états du jeu (autorité serveur).
// Le serveur (server.js) câble les sockets, l'engine détient tout l'état.

import { CONFIG, eliminationSchedule } from "./config.js";
import { isCorrect, pointsFor } from "./scoring.js";

const PHASES = { LOBBY: "lobby", QUESTION: "question", REVEAL: "reveal", ROUND_END: "roundEnd", GAME_OVER: "gameover" };

// Retire la solution avant d'envoyer une question aux tablettes.
function publicQuestion(q, meta) {
  const base = {
    id: q.id,
    type: q.type,
    prompt: q.prompt,
    theme: q.theme,
    ...meta,
  };
  if (q.type === "qcm") base.options = q.options;
  if (q.type === "classer") {
    base.items = q.items;
    base.buckets = q.buckets;
  }
  return base;
}

export class GameEngine {
  constructor(io, bankByTheme) {
    this.io = io;
    this.bank = bankByTheme; // { theme: [questions...] }
    this.players = new Map(); // token -> player
    this.phase = PHASES.LOBBY;
    this.roundIndex = 0;
    this.qIndex = 0;
    this.timeLimitMs = CONFIG.timeLimitMs;
    this.roundQuestions = []; // questions de la manche courante
    this.schedule = []; // survivants visés après chaque manche
    this.current = null; // question courante (complète)
    this.startAt = 0;
    this.answers = new Map(); // token -> { answer, atMs, correct, points, scored }
    this.timer = null;
    this.askedIds = new Set(); // questions déjà posées (mémoire entre parties)
  }

  // ---- Joueurs -----------------------------------------------------------
  join(socket, { token, pseudo }) {
    let player = token && this.players.get(token);
    if (player) {
      // Reconnexion : on conserve score / état.
      player.connected = true;
      player.socketId = socket.id;
      if (pseudo) player.pseudo = pseudo;
    } else {
      token = token || cryptoToken();
      const startedAlive = this.phase === PHASES.LOBBY; // arrivé après le début => fantôme
      player = {
        token,
        pseudo: (pseudo || "Passeur").slice(0, 24),
        score: 0,
        streak: 0,
        alive: startedAlive,
        joinedLate: !startedAlive,
        eliminatedRound: null,
        connected: true,
        socketId: socket.id,
      };
      this.players.set(token, player);
    }
    socket.data.token = token;
    socket.join("players");
    socket.emit("you", this.publicPlayer(player, true));
    socket.emit("state", this.snapshot(player));
    this.broadcastPlayers();
    return player;
  }

  disconnect(socket) {
    const token = socket.data.token;
    const p = token && this.players.get(token);
    if (p) {
      p.connected = false;
      this.broadcastPlayers();
    }
  }

  publicPlayer(p, withToken = false) {
    const out = {
      pseudo: p.pseudo,
      score: p.score,
      alive: p.alive,
      streak: p.streak,
      connected: p.connected,
      joinedLate: p.joinedLate,
    };
    if (withToken) out.token = p.token;
    return out;
  }

  leaderboard() {
    return [...this.players.values()]
      .map((p) => this.publicPlayer(p))
      .sort((a, b) => b.score - a.score || b.alive - a.alive);
  }

  alivePlayers() {
    return [...this.players.values()].filter((p) => p.alive);
  }

  // Nombre de questions VALIDÉES (proposables) par thème.
  validatedCounts() {
    const out = {};
    for (const round of CONFIG.rounds) {
      const pool = this.bank[round.theme] || [];
      out[round.theme] = { total: pool.length, valides: pool.filter((q) => q.valide).length };
    }
    out._totalValides = Object.values(out).reduce((s, x) => s + (x.valides || 0), 0);
    return out;
  }

  // ---- Contrôles prof ----------------------------------------------------
  hostStart(opts = {}) {
    if (this.phase !== PHASES.LOBBY) return;
    if (opts.timeLimitMs) this.timeLimitMs = Number(opts.timeLimitMs);
    const racers = this.alivePlayers();
    if (racers.length === 0) {
      this.io.to("host").emit("host:notice", { type: "erreur", message: "Aucun joueur connecté." });
      return;
    }
    if (this.validatedCounts()._totalValides === 0) {
      this.io.to("host").emit("host:notice", {
        type: "erreur",
        message: "Aucune question validée. Ouvre « Gérer les questions » pour en valider.",
      });
      return;
    }
    this.schedule = eliminationSchedule(racers.length, CONFIG.rounds.length);
    this.roundIndex = 0;
    this.startRound();
  }

  startRound() {
    // On ne propose que les questions validées par le maître ; les thèmes sans
    // question validée sont sautés automatiquement.
    while (this.roundIndex < CONFIG.rounds.length) {
      const round = CONFIG.rounds[this.roundIndex];
      const validated = (this.bank[round.theme] || []).filter((q) => q.valide);
      // On privilégie les questions PAS ENCORE POSÉES : rejouer = nouvelles questions.
      let pool = validated.filter((q) => !this.askedIds.has(q.id));
      if (pool.length < CONFIG.questionsPerRound && validated.length > 0) {
        // Stock neuf épuisé pour ce thème : on le recycle pour pouvoir continuer.
        for (const q of validated) this.askedIds.delete(q.id);
        pool = validated.slice();
      }
      pool.sort((a, b) => (a.difficulte || 1) - (b.difficulte || 1));
      this.roundQuestions = pool.slice(0, CONFIG.questionsPerRound);
      for (const q of this.roundQuestions) this.askedIds.add(q.id);
      if (this.roundQuestions.length > 0) break;
      this.roundIndex += 1;
    }
    if (this.roundIndex >= CONFIG.rounds.length) {
      this.gameOver();
      return;
    }
    const round = CONFIG.rounds[this.roundIndex];
    this.qIndex = 0;
    this.io.to("host").emit("roundStart", {
      roundIndex: this.roundIndex,
      titre: round.titre,
      finale: !!round.finale,
      totalRounds: CONFIG.rounds.length,
      questionsInRound: this.roundQuestions.length,
      survivorsTarget: this.schedule[this.roundIndex],
    });
    this.startQuestion();
  }

  startQuestion() {
    const q = this.roundQuestions[this.qIndex];
    if (!q) return;
    this.current = q;
    this.answers = new Map();
    this.startAt = Date.now();
    this.phase = PHASES.QUESTION;
    const meta = {
      roundIndex: this.roundIndex,
      roundTitre: CONFIG.rounds[this.roundIndex].titre,
      qIndex: this.qIndex,
      qTotal: this.roundQuestions.length,
      timeLimitMs: this.timeLimitMs,
      startAt: this.startAt,
    };
    this.io.to("players").emit("question", publicQuestion(q, meta));
    this.io.to("host").emit("question", publicQuestion(q, meta));
    clearTimeout(this.timer);
    this.timer = setTimeout(() => this.reveal(), this.timeLimitMs);
    this.broadcastAnswered();
  }

  playerAnswer(token, answer) {
    if (this.phase !== PHASES.QUESTION) return;
    const p = this.players.get(token);
    if (!p) return;
    if (this.answers.has(token)) return; // une seule réponse
    const atMs = Date.now();
    const correct = isCorrect(this.current, answer);
    const timeLeftMs = Math.max(0, this.timeLimitMs - (atMs - this.startAt));
    const scored = p.alive; // les fantômes jouent pour s'entraîner, hors classement
    const pts = scored ? pointsFor({ correct, timeLeftMs, totalMs: this.timeLimitMs, streak: p.streak + (correct ? 1 : 0) }) : 0;
    this.answers.set(token, { answer, atMs, correct, points: pts, scored });
    // Accusé de réception privé (sans dire si c'est juste — révélation plus tard).
    const sock = this.io.sockets.sockets.get(p.socketId);
    if (sock) sock.emit("answerAck", { received: true });
    this.broadcastAnswered();
    // Révélation anticipée si tous les vivants connectés ont répondu.
    const aliveConnected = this.alivePlayers().filter((x) => x.connected);
    const answeredAlive = aliveConnected.filter((x) => this.answers.has(x.token));
    if (aliveConnected.length > 0 && answeredAlive.length >= aliveConnected.length) {
      this.reveal();
    }
  }

  broadcastAnswered() {
    const aliveConnected = this.alivePlayers().filter((x) => x.connected).length;
    let answered = 0;
    for (const p of this.alivePlayers()) if (this.answers.has(p.token)) answered++;
    this.io.to("host").emit("answered", { answered, total: aliveConnected });
  }

  reveal() {
    if (this.phase !== PHASES.QUESTION) return;
    clearTimeout(this.timer);
    this.phase = PHASES.REVEAL;
    const q = this.current;

    // Applique les scores et séries pour les joueurs vivants.
    for (const p of this.players.values()) {
      const a = this.answers.get(p.token);
      if (!p.alive) continue;
      if (a && a.correct) {
        p.streak += 1;
        p.score += a.points;
      } else {
        p.streak = 0;
      }
    }

    // Distribution des réponses (pour l'écran maître).
    const distribution = this.answerDistribution(q);

    const revealPublic = {
      id: q.id,
      type: q.type,
      solution: q.solution ?? null,
      accepted: q.accepted ?? null,
      explication: q.explication || "",
      distribution,
    };
    this.io.to("host").emit("reveal", { ...revealPublic, leaderboard: this.leaderboard() });

    // Résultat personnalisé par joueur connecté.
    const rankedTokens = [...this.players.values()]
      .sort((a, b) => b.score - a.score || b.alive - a.alive)
      .map((p) => p.token);
    for (const p of this.players.values()) {
      if (!p.connected) continue;
      const sock = this.io.sockets.sockets.get(p.socketId);
      if (!sock) continue;
      const a = this.answers.get(p.token);
      const rank = rankedTokens.indexOf(p.token) + 1;
      sock.emit("reveal", {
        ...revealPublic,
        you: {
          answered: !!a,
          correct: a ? a.correct : false,
          points: a && p.alive ? a.points : 0,
          score: p.score,
          streak: p.streak,
          alive: p.alive,
          rank: rank > 0 ? rank : null,
        },
      });
    }
  }

  answerDistribution(q) {
    if (q.type === "qcm") {
      const counts = (q.options || []).map(() => 0);
      for (const a of this.answers.values()) {
        const i = Number(a.answer);
        if (i >= 0 && i < counts.length) counts[i]++;
      }
      return { kind: "qcm", counts };
    }
    if (q.type === "vraifaux") {
      let vrai = 0, faux = 0;
      for (const a of this.answers.values()) (a.answer ? vrai++ : faux++);
      return { kind: "vraifaux", vrai, faux };
    }
    let correct = 0, total = 0;
    for (const a of this.answers.values()) {
      total++;
      if (a.correct) correct++;
    }
    return { kind: "libre", correct, total };
  }

  hostNext() {
    if (this.phase === PHASES.REVEAL) {
      this.qIndex += 1;
      if (this.qIndex < this.roundQuestions.length) {
        this.startQuestion();
      } else {
        this.endRound();
      }
    } else if (this.phase === PHASES.ROUND_END) {
      this.roundIndex += 1;
      if (this.roundIndex >= CONFIG.rounds.length || this.alivePlayers().length <= 1) {
        this.gameOver();
      } else {
        this.startRound();
      }
    }
  }

  endRound() {
    this.phase = PHASES.ROUND_END;
    const target = this.schedule[this.roundIndex] ?? 1;
    const alive = this.alivePlayers().sort((a, b) => b.score - a.score);
    const eliminated = [];
    if (alive.length > target) {
      const condemned = alive.slice(target);
      for (const p of condemned) {
        p.alive = false;
        p.eliminatedRound = this.roundIndex;
        eliminated.push(this.publicPlayer(p));
        const sock = this.io.sockets.sockets.get(p.socketId);
        if (sock) sock.emit("eliminated", { round: this.roundIndex, finalScore: p.score });
      }
    }
    const survivors = this.alivePlayers().map((p) => this.publicPlayer(p)).sort((a, b) => b.score - a.score);
    const payload = {
      roundIndex: this.roundIndex,
      titre: CONFIG.rounds[this.roundIndex].titre,
      target,
      eliminated: eliminated.sort((a, b) => b.score - a.score),
      survivors,
      leaderboard: this.leaderboard(),
      isLast: this.roundIndex >= CONFIG.rounds.length - 1 || this.alivePlayers().length <= 1,
    };
    this.io.to("host").emit("roundEnd", payload);
    this.io.to("players").emit("roundEnd", { roundIndex: this.roundIndex, survivors });
  }

  gameOver() {
    this.phase = PHASES.GAME_OVER;
    clearTimeout(this.timer);
    const ranked = this.leaderboard();
    const winner = ranked.find((p) => p.alive) || ranked[0] || null;
    this.io.emit("gameOver", { winner, leaderboard: ranked });
  }

  hostReset(opts = {}) {
    clearTimeout(this.timer);
    this.phase = PHASES.LOBBY;
    this.roundIndex = 0;
    this.qIndex = 0;
    this.current = null;
    this.answers = new Map();
    this.roundQuestions = [];
    this.schedule = [];
    // Rejeu normal : on GARDE la mémoire des questions posées (nouvelles questions).
    // « Repartir de zéro » (clearHistory) : on repropose toute la banque depuis le début.
    if (opts.clearHistory) this.askedIds.clear();
    for (const p of this.players.values()) {
      p.score = 0;
      p.streak = 0;
      p.alive = p.connected; // tous les connectés repartent en course
      p.joinedLate = false;
      p.eliminatedRound = null;
    }
    this.io.emit("reset", {});
    this.broadcastPlayers();
  }

  // ---- Diffusion / état --------------------------------------------------
  broadcastPlayers() {
    const list = [...this.players.values()].map((p) => this.publicPlayer(p));
    this.io.to("host").emit("players", {
      players: list.sort((a, b) => b.score - a.score),
      count: list.length,
      connected: list.filter((p) => p.connected).length,
      alive: list.filter((p) => p.alive).length,
    });
  }

  // Instantané pour la reconnexion d'un client.
  snapshot(player) {
    const snap = { phase: this.phase, you: this.publicPlayer(player, true) };
    if (this.phase === PHASES.QUESTION && this.current) {
      snap.question = publicQuestion(this.current, {
        roundIndex: this.roundIndex,
        roundTitre: CONFIG.rounds[this.roundIndex].titre,
        qIndex: this.qIndex,
        qTotal: this.roundQuestions.length,
        timeLimitMs: this.timeLimitMs,
        startAt: this.startAt,
      });
      snap.alreadyAnswered = this.answers.has(player.token);
    }
    return snap;
  }

  // Instantané pour l'écran maître qui (re)charge.
  hostSnapshot() {
    return {
      phase: this.phase,
      roundIndex: this.roundIndex,
      totalRounds: CONFIG.rounds.length,
      timeLimitMs: this.timeLimitMs,
      players: this.leaderboard(),
      validated: this.validatedCounts(),
    };
  }

  // Recharge la banque après une modification via l'éditeur, et informe l'hôte.
  setBank(bankByTheme) {
    this.bank = bankByTheme;
    this.io.to("host").emit("host:validated", this.validatedCounts());
  }
}

function cryptoToken() {
  return "p_" + Math.random().toString(36).slice(2) + Date.now().toString(36);
}
