"use strict";

/*
 * THavalon in-person frontend.
 *
 * A small framework-free single-page app over the REST API. It surfaces every
 * piece of API functionality needed to run a game face-to-face:
 *   - rolling a standard or custom game (POST /names)
 *   - re-opening a recent game (POST /currentgames) or joining by id
 *   - a pass-the-phone reveal of each player's secret role + information
 *     (GET /game/info/{id})
 *   - a full-table "Do Not Open" reference
 *   - ending a game (POST /gameover/{id})
 */

// Same-origin API by default (the FastAPI app serves this page under /app).
const API_BASE = "";

const SUPPORTED_COUNTS = [5, 7, 8, 10];

// Custom-role options. Keys match what the server accepts (aliases such as
// "Lovers" and "Duplicate Roles" are expanded server-side). `def` is the
// default checked state, mirroring the original frontend.
const ROLE_OPTIONS = {
  good: [
    { key: "Merlin", def: true },
    { key: "Percival", def: true },
    { key: "Lone Percival", def: false },
    { key: "Guinevere", def: true },
    { key: "Lovers", def: true },
    { key: "Lone Lovers", def: false },
    { key: "Arthur", def: true },
    { key: "Galahad", def: false },
    { key: "Lancelot", def: true },
    { key: "Titania", def: true },
    { key: "Nimue", def: false },
    { key: "Gawain", def: false },
  ],
  evil: [
    { key: "Mordred", def: true },
    { key: "Morgana", def: true },
    { key: "Maelegant", def: true },
    { key: "Oberon", def: true },
    { key: "Agravaine", def: true },
    { key: "Colgrevance", def: true },
  ],
  special: [{ key: "Duplicate Roles", def: false }],
};

// ----- App state (kept across re-renders of the home screen) ----------------

const draft = {
  players: [],
  useCustom: false,
  custom: defaultCustom(),
};

function defaultCustom() {
  const m = {};
  for (const group of Object.values(ROLE_OPTIONS)) {
    for (const opt of group) m[opt.key] = opt.def;
  }
  return m;
}

// Last fetched game, cached so the reveal overlay needn't refetch.
let currentGame = { id: null, players: [] };

// Monotonic render token; lets an async page render bail out if the route
// changed (or another navigation started) while a fetch was in flight.
let renderSeq = 0;

// ----- Tiny helpers ---------------------------------------------------------

const view = () => document.getElementById("view");

function esc(s) {
  return String(s).replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])
  );
}

async function api(path, options) {
  const res = await fetch(API_BASE + path, options);
  const text = await res.text();
  return text ? JSON.parse(text) : null;
}

function postJSON(path, body) {
  return api(path, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify(body),
  });
}

function flattenInfo(info) {
  // The API groups information into buckets; in-person play shows them as one
  // flat list, matching the original frontend.
  const order = ["alerts", "rolePresent", "seen", "pairSeen", "perfect"];
  const out = [];
  for (const key of order) {
    if (Array.isArray(info[key])) out.push(...info[key]);
  }
  // Include any unexpected future buckets too.
  for (const key of Object.keys(info)) {
    if (!order.includes(key) && Array.isArray(info[key])) out.push(...info[key]);
  }
  return out;
}

// ----- Router ---------------------------------------------------------------

function go(hash) {
  if (location.hash === hash) render();
  else location.hash = hash;
}

function render() {
  closeOverlay();
  const seq = ++renderSeq;
  const hash = location.hash || "#/";
  const gameMatch = hash.match(/^#\/game\/([^/]+)$/);
  if (gameMatch) {
    renderGame(decodeURIComponent(gameMatch[1]), seq);
  } else {
    renderHome();
  }
  window.scrollTo(0, 0);
}

window.addEventListener("hashchange", render);
window.addEventListener("DOMContentLoaded", render);

// ----- Home screen ----------------------------------------------------------

function renderHome() {
  const count = draft.players.length;
  const valid = SUPPORTED_COUNTS.includes(count);
  view().innerHTML = `
    <h1 class="flourish">Assemble the Table</h1>
    <h2>Name the knights, then deal their fates</h2>
    <div id="error-slot"></div>

    <div class="card">
      <form id="add-player-form" autocomplete="off">
        <label class="field" for="player-name">Player name</label>
        <div class="row">
          <input type="text" id="player-name" maxlength="30" placeholder="e.g. Alice" />
          <button type="submit" class="grow0 btn-primary">Add</button>
        </div>
      </form>
      <p class="count-hint ${valid ? "valid" : ""}">
        ${count} player${count === 1 ? "" : "s"} &middot; supported sizes: 5, 7, 8, 10
      </p>
      <ul class="players-list">
        ${draft.players
          .map(
            (name, i) => `
          <li>
            <span class="pname"><span class="num">${i + 1}.</span>${esc(name)}</span>
            <button class="icon-btn" data-remove="${i}" aria-label="Remove ${esc(
              name
            )}">&times;</button>
          </li>`
          )
          .join("")}
      </ul>
    </div>

    <div class="card">
      <div class="toggle-row">
        <span class="lbl"><strong>Custom roles</strong><small>Pick the role pool yourself</small></span>
        <label class="switch">
          <input type="checkbox" id="use-custom" ${draft.useCustom ? "checked" : ""} />
          <span class="slider"></span>
        </label>
      </div>
      <div id="custom-panel" style="display:${draft.useCustom ? "block" : "none"}">
        ${renderRoleGroup("Good", ROLE_OPTIONS.good)}
        ${renderRoleGroup("Evil", ROLE_OPTIONS.evil)}
        ${renderRoleGroup("Options", ROLE_OPTIONS.special)}
      </div>
    </div>

    <button id="roll-btn" class="btn-primary btn-block">Deal Roles</button>

    <div class="card" style="margin-top:24px">
      <h3>Open an existing game</h3>
      <form id="join-form" autocomplete="off">
        <div class="row">
          <input type="text" id="join-id" placeholder="Game ID" />
          <button type="submit" class="grow0">Open</button>
        </div>
      </form>
      <div class="group-title">Recent games</div>
      <div id="recent" class="recent-list"><span class="muted">Loading…</span></div>
    </div>
  `;

  // Add player
  const addForm = document.getElementById("add-player-form");
  const nameInput = document.getElementById("player-name");
  addForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const err = addPlayer(nameInput.value);
    if (err) return showError(err);
    nameInput.value = "";
    renderHome();
    document.getElementById("player-name").focus();
  });

  // Remove player
  view().querySelectorAll("[data-remove]").forEach((btn) =>
    btn.addEventListener("click", () => {
      draft.players.splice(Number(btn.dataset.remove), 1);
      renderHome();
    })
  );

  // Custom toggle
  document.getElementById("use-custom").addEventListener("change", (e) => {
    draft.useCustom = e.target.checked;
    document.getElementById("custom-panel").style.display = draft.useCustom
      ? "block"
      : "none";
  });

  // Role switches
  view().querySelectorAll("[data-role]").forEach((input) =>
    input.addEventListener("change", (e) => {
      draft.custom[input.dataset.role] = e.target.checked;
    })
  );

  document.getElementById("roll-btn").addEventListener("click", rollGame);

  document.getElementById("join-form").addEventListener("submit", (e) => {
    e.preventDefault();
    const id = document.getElementById("join-id").value.trim();
    if (id) openGame(id);
  });

  loadRecent();
}

function renderRoleGroup(title, options) {
  return `
    <div class="group-title">${title}</div>
    <div class="role-grid">
      ${options
        .map(
          (opt) => `
        <div class="toggle-row">
          <span class="lbl">${esc(opt.key)}</span>
          <label class="switch">
            <input type="checkbox" data-role="${esc(opt.key)}" ${
            draft.custom[opt.key] ? "checked" : ""
          } />
            <span class="slider"></span>
          </label>
        </div>`
        )
        .join("")}
    </div>`;
}

function addPlayer(raw) {
  const name = (raw || "").trim();
  if (!name) return null;
  if (/[/?#\\.]/.test(name)) return "Name contains invalid characters (/ ? # \\ .).";
  if (name.length > 30) return "Names must be 30 characters or fewer.";
  if (draft.players.some((p) => p.trim() === name)) return "Duplicate names are not allowed.";
  draft.players.push(name);
  return null;
}

async function rollGame() {
  clearError();
  const names = draft.players.slice();
  if (!SUPPORTED_COUNTS.includes(names.length)) {
    return showError("Games are supported for 5, 7, 8, or 10 players.");
  }
  const body = { names };
  if (draft.useCustom) {
    body.custom = { ...draft.custom };
    body.duplicates = !!draft.custom["Duplicate Roles"];
  }
  const btn = document.getElementById("roll-btn");
  btn.disabled = true;
  btn.textContent = "Dealing…";
  try {
    const data = await postJSON("/names", body);
    if (data && data.error) return showError(data.error);
    if (data && data.id) {
      go("#/game/" + encodeURIComponent(data.id));
    } else {
      showError("Unexpected response from server.");
    }
  } catch (e) {
    showError("Could not reach the server.");
  } finally {
    btn.disabled = false;
    btn.textContent = "Deal Roles";
  }
}

async function openGame(id) {
  clearError();
  try {
    const exists = await api("/isGame/" + encodeURIComponent(id), { method: "GET" });
    if (exists) go("#/game/" + encodeURIComponent(id));
    else showError(`No game found with id "${id}".`);
  } catch (e) {
    showError("Could not reach the server.");
  }
}

async function loadRecent() {
  const box = document.getElementById("recent");
  try {
    const ids = await postJSON("/currentgames", { numGames: 8 });
    if (!ids || ids.length === 0) {
      box.innerHTML = '<span class="muted">No recent games.</span>';
      return;
    }
    box.innerHTML = ids
      .map((id) => `<button data-open="${esc(id)}">${esc(id)}</button>`)
      .join("");
    box.querySelectorAll("[data-open]").forEach((b) =>
      b.addEventListener("click", () => go("#/game/" + encodeURIComponent(b.dataset.open)))
    );
  } catch (e) {
    box.innerHTML = '<span class="muted">Could not load recent games.</span>';
  }
}

// ----- Game screen ----------------------------------------------------------

async function renderGame(id, seq) {
  view().innerHTML = '<div class="spinner">Loading game…</div>';
  let game;
  try {
    game = await api("/game/info/" + encodeURIComponent(id), { method: "GET" });
  } catch (e) {
    if (seq !== renderSeq) return;
    view().innerHTML =
      '<div class="error">Could not reach the server.</div>' +
      '<button class="btn-block" onclick="location.hash=\'#/\'">Back</button>';
    return;
  }
  // Bail out if the user navigated elsewhere while this fetch was in flight.
  if (seq !== renderSeq) return;
  if (!Array.isArray(game) || game.length === 0) {
    view().innerHTML =
      `<div class="error">No game found with id "${esc(id)}".</div>` +
      '<button class="btn-block" onclick="location.hash=\'#/\'">Back to home</button>';
    return;
  }

  currentGame = { id, players: game };
  const starter = game[0].name;

  view().innerHTML = `
    <div class="gameid-bar">
      <span><small>Game ID</small><span class="gid">${esc(id)}</span></span>
      <button id="copy-btn" class="grow0">Copy link</button>
    </div>

    <div class="start-banner">
      <small>Starting player</small>
      <strong>${esc(starter)}</strong>
    </div>

    <h2>Tap your name to learn your fate</h2>
    <div class="player-buttons">
      ${game
        .map(
          (p, i) => `
        <button data-player="${i}" class="${i === 0 ? "is-start" : ""}">
          ${esc(p.name)}
        </button>`
        )
        .join("")}
    </div>

    <button id="dno-btn" class="btn-block" style="margin-top:20px">Do Not Open (full table)</button>
    <button id="end-btn" class="btn-block btn-danger">End game</button>
    <button class="btn-block btn-ghost" onclick="location.hash='#/'">Back to home</button>
  `;

  document.getElementById("copy-btn").addEventListener("click", copyLink);
  view().querySelectorAll("[data-player]").forEach((btn) =>
    btn.addEventListener("click", () => revealPlayer(Number(btn.dataset.player)))
  );
  document.getElementById("dno-btn").addEventListener("click", showDoNotOpen);
  document.getElementById("end-btn").addEventListener("click", () => endGame(id));
}

async function copyLink() {
  const btn = document.getElementById("copy-btn");
  const url = location.href;
  try {
    await navigator.clipboard.writeText(url);
  } catch (e) {
    const ta = document.createElement("textarea");
    ta.value = url;
    document.body.appendChild(ta);
    ta.select();
    try {
      document.execCommand("copy");
    } catch (_) {}
    document.body.removeChild(ta);
  }
  btn.textContent = "Copied!";
  setTimeout(() => (btn.textContent = "Copy link"), 1500);
}

async function endGame(id) {
  if (!window.confirm("End this game? It will be removed from the server.")) return;
  const btn = document.getElementById("end-btn");
  btn.disabled = true;
  btn.textContent = "Ending…";
  try {
    await postJSON("/gameover/" + encodeURIComponent(id), { record: false });
  } catch (e) {
    btn.disabled = false;
    btn.textContent = "End game";
    window.alert("Could not end the game. Please try again.");
    return;
  }
  go("#/");
}

// ----- Reveal / overlay -----------------------------------------------------

function ensureOverlay() {
  let el = document.getElementById("overlay");
  if (!el) {
    el = document.createElement("div");
    el.id = "overlay";
    el.className = "overlay";
    document.body.appendChild(el);
  }
  document.body.style.overflow = "hidden";
  return el;
}

function closeOverlay() {
  const el = document.getElementById("overlay");
  if (el) el.remove();
  document.body.style.overflow = "";
}

function revealPlayer(index) {
  const player = currentGame.players[index];
  if (!player) return;
  // Each player is on their own phone, so show the role card directly.
  showRevealCard(player);
}

function showRevealCard(player) {
  const el = ensureOverlay();
  const team = (player.allegiance || "").toLowerCase() === "evil" ? "evil" : "good";
  const infos = flattenInfo(player.information || {});
  const infoHtml = infos.length
    ? `<ul class="info-list">${infos.map((i) => `<li>${esc(i)}</li>`).join("")}</ul>`
    : '<p class="info-empty">You have no additional information.</p>';
  el.innerHTML = `
    <div class="overlay-inner">
      <div class="reveal-card">
        <div class="reveal-head ${team}">
          <div class="who">${esc(player.name)}, you are</div>
          <div class="role">${esc(player.role)}</div>
          <span class="team">${esc(player.allegiance)}</span>
        </div>
        <div class="reveal-body">
          <p class="desc">${esc(player.description)}</p>
          ${infoHtml}
        </div>
      </div>
      <button id="done-btn" class="btn-primary btn-block" style="margin-top:16px">Done — hide</button>
    </div>`;
  document.getElementById("done-btn").addEventListener("click", closeOverlay);
}

function showDoNotOpen() {
  // Privacy gate: the full table reveal is one tap away from spoiling the game,
  // so require an explicit confirmation first.
  const el = ensureOverlay();
  el.innerHTML = `
    <div class="overlay-inner gate">
      <h1>Do Not Open</h1>
      <p class="muted">This reveals every player's role and clues. Only open this
      after the game is over.</p>
      <button id="dno-reveal" class="btn-danger btn-block big">Reveal full table</button>
      <button id="dno-cancel" class="btn-block btn-ghost">Cancel</button>
    </div>`;
  document.getElementById("dno-reveal").addEventListener("click", showFullTable);
  document.getElementById("dno-cancel").addEventListener("click", closeOverlay);
}

function showFullTable() {
  const el = ensureOverlay();
  const rows = currentGame.players
    .map((p) => {
      const infos = flattenInfo(p.information || {});
      const list = infos.length
        ? `<ul>${infos.map((i) => `<li>${esc(i)}</li>`).join("")}</ul>`
        : "";
      return `<li><span class="name">${esc(p.name)}</span> — <span class="role">${esc(
        p.role
      )} (${esc(p.allegiance)})</span>${list}</li>`;
    })
    .join("");
  el.innerHTML = `
    <div class="overlay-inner">
      <h1 class="center">Do Not Open</h1>
      <p class="center muted">Every role and clue at the table.</p>
      <ul class="dno-list">${rows}</ul>
      <button id="dno-close" class="btn-primary btn-block" style="margin-top:16px">Close</button>
    </div>`;
  document.getElementById("dno-close").addEventListener("click", closeOverlay);
}

// ----- Errors ---------------------------------------------------------------

function showError(msg) {
  const slot = document.getElementById("error-slot");
  if (slot) {
    slot.innerHTML = `<div class="error">${esc(msg)}</div>`;
    slot.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }
}

function clearError() {
  const slot = document.getElementById("error-slot");
  if (slot) slot.innerHTML = "";
}
