"use strict";

const SAMPLE = [
  [0,0,0,2,6,0,7,0,1],
  [6,8,0,0,7,0,0,9,0],
  [1,9,0,0,0,4,5,0,0],
  [8,2,0,1,0,0,0,4,0],
  [0,0,4,6,0,2,9,0,0],
  [0,5,0,0,0,3,0,2,8],
  [0,0,9,3,0,0,0,7,4],
  [0,4,0,0,5,0,0,3,6],
  [7,0,3,0,1,8,0,0,0],
];

const el = (id) => document.getElementById(id);
const clone = (grid) => grid.map((row) => row.slice());
const indexOf = (r,c) => r * 9 + c;
const state = {
  puzzle: clone(SAMPLE),
  board: clone(SAMPLE),
  difficulty: "medium",
  selected: null,
  hints: new Set(),
  solved: new Set(),
  history: [],
  busy: false,
  playback: null,
  lastMove: null,
};
const cells = [];

function makeGrid() {
  const root = el("sudoku-board");
  for (let r = 0; r < 9; r++) {
    for (let c = 0; c < 9; c++) {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.setAttribute("role", "gridcell");
      btn.className = "cell";
      btn.dataset.row = r;
      btn.dataset.col = c;
      btn.addEventListener("click", () => {
        if (!state.busy && !state.playback) {
          state.selected = [r,c];
          renderBoard();
        }
      });
      root.append(btn);
      cells.push(btn);
    }
  }
}

function conflictCells() {
  const conflicts = new Set();
  const units = [];
  for (let r = 0; r < 9; r++) units.push(Array.from({length: 9}, (_,c) => [r,c]));
  for (let c = 0; c < 9; c++) units.push(Array.from({length: 9}, (_,r) => [r,c]));
  for (let br = 0; br < 9; br += 3) {
    for (let bc = 0; bc < 9; bc += 3) {
      const unit = [];
      for (let r = br; r < br + 3; r++) for (let c = bc; c < bc + 3; c++) unit.push([r,c]);
      units.push(unit);
    }
  }
  for (const unit of units) {
    const found = new Map();
    for (const [r,c] of unit) {
      const value = state.board[r][c];
      if (!value) continue;
      if (!found.has(value)) found.set(value, []);
      found.get(value).push(indexOf(r,c));
    }
    for (const points of found.values()) if (points.length > 1) points.forEach((p) => conflicts.add(p));
  }
  return conflicts;
}

function renderBoard() {
  const conflicts = conflictCells();
  const [sr, sc] = state.selected || [-1,-1];
  const selValue = sr >= 0 ? state.board[sr][sc] : 0;
  for (let r = 0; r < 9; r++) {
    for (let c = 0; c < 9; c++) {
      const cell = cells[indexOf(r,c)];
      const value = state.board[r][c];
      const key = indexOf(r,c);
      const fixed = state.puzzle[r][c] !== 0;
      const selected = r === sr && c === sc;
      const related = sr >= 0 && (r === sr || c === sc || (Math.floor(r/3) === Math.floor(sr/3) && Math.floor(c/3) === Math.floor(sc/3)));
      cell.textContent = value ? String(value) : "";
      cell.className = "cell";
      if (c === 2 || c === 5) cell.classList.add("box-end");
      if (r === 2 || r === 5) cell.classList.add("row-end");
      if (c === 8) cell.classList.add("last-col");
      if (r === 8) cell.classList.add("last-row");
      if (fixed) cell.classList.add("given");
      if (value && !fixed) cell.classList.add("user-entry");
      if (state.hints.has(key)) cell.classList.add("hint-entry");
      if (state.solved.has(key)) cell.classList.add("solved-entry");
      if (related && !state.playback) cell.classList.add("related");
      if (selValue && selValue === value && !state.playback) cell.classList.add("match");
      if (conflicts.has(key)) cell.classList.add("conflict");
      if (selected && !state.playback) cell.classList.add("selected");
      if (state.playback && state.lastMove && state.lastMove.row === r && state.lastMove.col === c) {
        cell.classList.add(state.lastMove.type === "place" ? "search-place" : "search-backtrack");
      }
      cell.setAttribute("aria-label", `Row ${r+1}, column ${c+1}, ${value || "empty"}${fixed ? ", given" : ""}${conflicts.has(key) ? ", conflict" : ""}`);
      cell.setAttribute("aria-selected", String(selected));
      cell.tabIndex = selected || (!state.selected && r === 0 && c === 0) ? 0 : -1;
    }
  }
  const filled = state.board.flat().filter(Boolean).length;
  const clues = state.puzzle.flat().filter(Boolean).length;
  el("fill-count").textContent = `${filled} / 81 FILLED`;
  el("puzzle-details").textContent = `${state.difficulty.toUpperCase()} · ${clues} CLUES`;
}

function status(message, kind = "") {
  el("status").className = "status" + (kind ? ` ${kind}` : "");
  el("status-text").textContent = message;
}
function setStats(stats = null) {
  el("stat-nodes").textContent = stats ? Number(stats.nodes).toLocaleString() : "—";
  el("stat-placements").textContent = stats ? Number(stats.placements).toLocaleString() : "—";
  el("stat-backtracks").textContent = stats ? Number(stats.backtracks).toLocaleString() : "—";
  el("stat-time").textContent = stats ? `${Number(stats.elapsed_ms).toFixed(2)} ms` : "—";
}
function setWorking(working) {
  state.busy = working;
  updateControls();
}
function updateControls() {
  const locked = state.busy || Boolean(state.playback);
  for (const id of ["solve-btn","visualize-btn","hint-btn","new-btn","reset-btn","undo-btn","check-btn"]) {
    el(id).disabled = locked;
  }
  for (const btn of document.querySelectorAll(".diff-btn, .number-pad button")) btn.disabled = locked;
  if (!locked) el("undo-btn").disabled = state.history.length === 0;
}
function clearAnalysis() {
  state.solved.clear();
  state.lastMove = null;
  setStats();
  el("playback").hidden = true;
}
function enter(value, fromHint = false, r = null, c = null) {
  if (state.busy || state.playback) return;
  if (r === null || c === null) {
    if (!state.selected) { status("Select an empty cell first."); return; }
    [r,c] = state.selected;
  }
  if (state.puzzle[r][c] !== 0) { status("Given numbers cannot be changed."); return; }
  const old = state.board[r][c];
  if (old === value) return;
  const idx = indexOf(r,c);
  state.history.push({r,c,old, oldHint: state.hints.has(idx), oldSolved: state.solved.has(idx)});
  state.board[r][c] = value;
  state.hints.delete(idx);
  if (fromHint) state.hints.add(idx);
  clearAnalysis();
  state.selected = [r,c];
  renderBoard();
  updateControls();
  const count = conflictCells().size;
  if (count) status(`${count} conflicting cell${count === 1 ? "" : "s"} highlighted. Each digit must be unique in its row, column and box.`, "error");
  else if (state.board.flat().every(Boolean)) status("Board is full! Use Check to verify the solution.");
  else status(fromHint ? `AI hint: row ${r+1}, column ${c+1} is ${value}.` : "Entry saved. Keep going!");
}
function undo() {
  if (state.busy || state.playback || !state.history.length) return;
  const move = state.history.pop();
  const {r,c,old,oldHint,oldSolved} = move;
  const idx = indexOf(r,c);
  state.board[r][c] = old;
  state.hints.delete(idx);
  if (oldHint) state.hints.add(idx);
  clearAnalysis();
  if (oldSolved) state.solved.add(idx);
  state.selected = [r,c];
  renderBoard();
  updateControls();
  status("Last move undone.");
}
function reset() {
  if (state.busy || state.playback) return;
  state.board = clone(state.puzzle);
  state.history = [];
  state.hints.clear();
  state.selected = null;
  clearAnalysis();
  renderBoard();
  updateControls();
  status("Puzzle reset. You have a fresh start!");
}

async function request(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: {"Content-Type":"application/json", ...(options.headers || {})},
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || `Request failed (${response.status}).`);
  return data;
}
function ensureValid() {
  if (conflictCells().size) {
    status("Resolve the highlighted duplicate digits before using the AI solver.", "error");
    return false;
  }
  return true;
}
async function runSolve(visualize) {
  if (state.busy || state.playback || !ensureValid()) return;
  setWorking(true);
  status(visualize ? "Finding a solution and recording search decisions…" : "Running optimized CSP search…");
  try {
    const original = clone(state.board);
    const result = await request("/api/solve", {method:"POST", body:JSON.stringify({board: original, trace: visualize})});
    setWorking(false);
    if (visualize && result.trace.length) {
      state.playback = {
        trace: result.trace,
        solution: result.solution,
        stats: result.stats,
        index: 0,
        countPlaced: 0,
        countRemoved: 0,
        timer: null,
      };
      el("playback").hidden = false;
      state.selected = null;
      state.lastMove = null;
      setStats({nodes:0,placements:0,backtracks:0,elapsed_ms:result.stats.elapsed_ms});
      updateControls();
      status(`Visualizing ${result.trace.length.toLocaleString()} search decisions. Green = placement; pink = backtrack.`);
      renderBoard();
      nextStep();
    } else {
      applySolution(result.solution, result.stats);
      status("Solved! All 81 cells satisfy Sudoku constraints.", "success");
    }
  } catch (e) {
    status(e.message || "Could not solve the board.", "error");
    setWorking(false);
  }
}
function applySolution(solution, stats) {
  for (let r = 0; r < 9; r++) for (let c = 0; c < 9; c++) {
    if (!state.puzzle[r][c]) state.solved.add(indexOf(r,c));
  }
  state.board = clone(solution);
  state.hints.clear();
  state.history = [];
  state.selected = null;
  state.playback = null;
  state.lastMove = null;
  el("playback").hidden = true;
  setStats(stats);
  renderBoard();
  updateControls();
}
function nextStep() {
  const play = state.playback;
  if (!play) return;
  if (play.index >= play.trace.length) { completePlayback(); return; }
  const step = play.trace[play.index++];
  state.board[step.row][step.col] = step.type === "place" ? step.value : 0;
  state.lastMove = step;
  if (step.type === "place") play.countPlaced++;
  else play.countRemoved++;
  setStats({
    nodes: Math.min(play.stats.nodes, play.countPlaced + 1),
    placements: play.countPlaced,
    backtracks: play.countRemoved,
    elapsed_ms: play.stats.elapsed_ms,
  });
  el("step-counter").textContent = `${play.index.toLocaleString()} / ${play.trace.length.toLocaleString()}`;
  el("progress-fill").style.width = `${(play.index/play.trace.length)*100}%`;
  el("move-description").textContent = step.type === "place"
    ? `Trying ${step.value} at row ${step.row+1}, column ${step.col+1} · depth ${step.depth}`
    : `Dead end! Remove ${step.value} at row ${step.row+1}, column ${step.col+1}`;
  renderBoard();
  const speed = Number(el("speed").value);
  const delay = Math.round(380 * Math.pow(.035, speed/100));
  play.timer = window.setTimeout(nextStep, delay);
}
function completePlayback() {
  const play = state.playback;
  if (!play) return;
  clearTimeout(play.timer);
  const capped = play.stats.trace_capped;
  const solution = play.solution;
  const stats = play.stats;
  applySolution(solution, stats);
  status(capped ? "Solved! The visual trace was capped for performance; the full search completed." : "Search complete! The algorithm found a valid Sudoku solution.", "success");
}
async function hint() {
  if (state.busy || state.playback || !ensureValid()) return;
  setWorking(true);
  status("Finding a valid value for your next move…");
  try {
    const data = await request("/api/hint", {
      method:"POST", body:JSON.stringify({board:state.board,selected:state.selected}),
    });
    setWorking(false);
    if (data.complete) { status("The puzzle is already complete!", "success"); return; }
    enter(data.value, true, data.row, data.col);
  } catch (e) { setWorking(false); status(e.message, "error"); }
}
async function check() {
  if (state.busy || state.playback || !ensureValid()) return;
  setWorking(true);
  status("Checking your entries…");
  try {
    const data = await request("/api/check", {method:"POST",body:JSON.stringify({board:state.board})});
    status(data.message, data.valid ? "success" : "error");
  } catch (e) { status(e.message, "error"); }
  finally { setWorking(false); }
}
async function newPuzzle(difficulty = state.difficulty) {
  if (state.busy || state.playback) return;
  setWorking(true);
  status(`Generating a unique ${difficulty} puzzle…`);
  try {
    const data = await request(`/api/puzzle?difficulty=${encodeURIComponent(difficulty)}`);
    state.puzzle = clone(data.puzzle);
    state.board = clone(data.puzzle);
    state.difficulty = difficulty;
    state.selected = null;
    state.history = [];
    state.hints.clear();
    clearAnalysis();
    document.querySelectorAll(".diff-btn").forEach((btn) => {
      btn.classList.toggle("active", btn.dataset.difficulty === difficulty);
    });
    renderBoard();
    status(`New ${difficulty} puzzle ready with ${data.clues} given cells. Good luck!`, "success");
  } catch (e) { status(e.message || "Could not generate a puzzle.", "error"); }
  finally { setWorking(false); }
}
function registerHandlers() {
  document.querySelectorAll(".diff-btn").forEach((btn) => btn.addEventListener("click", () => newPuzzle(btn.dataset.difficulty)));
  document.querySelectorAll(".number-pad button").forEach((btn) => btn.addEventListener("click", () => enter(Number(btn.dataset.digit))));
  el("new-btn").addEventListener("click", () => newPuzzle());
  el("reset-btn").addEventListener("click", reset);
  el("undo-btn").addEventListener("click", undo);
  el("check-btn").addEventListener("click", check);
  el("solve-btn").addEventListener("click", () => runSolve(false));
  el("visualize-btn").addEventListener("click", () => runSolve(true));
  el("hint-btn").addEventListener("click", hint);
  el("skip-btn").addEventListener("click", completePlayback);
  document.addEventListener("keydown", (event) => {
    if (event.metaKey || event.ctrlKey || event.altKey || event.target.matches("input,textarea,select")) return;
    if (state.busy || state.playback) return;
    const key = event.key;
    if (/^[1-9]$/.test(key)) { event.preventDefault(); enter(Number(key)); return; }
    if (key === "Backspace" || key === "Delete" || key === "0") { event.preventDefault(); enter(0); return; }
    if (["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight"].includes(key)) {
      event.preventDefault();
      let [r,c] = state.selected || [0,0];
      if (key === "ArrowUp") r = (r+8)%9;
      if (key === "ArrowDown") r = (r+1)%9;
      if (key === "ArrowLeft") c = (c+8)%9;
      if (key === "ArrowRight") c = (c+1)%9;
      state.selected = [r,c];
      renderBoard();
      cells[indexOf(r,c)].focus({preventScroll:true});
    }
  });
}
makeGrid();
registerHandlers();
renderBoard();
updateControls();
