let STATE = null;

async function fetchState() {
  const res = await fetch("/state");
  STATE = await res.json();
  render();
}

async function sendCommand(cmd) {
  const res = await fetch("/command", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({cmd})
  });
  const data = await res.json();
  STATE = data.state;
  render();
}

async function startNewRound() {
  const res = await fetch("/new_round", { method: "POST" });
  const data = await res.json();
  STATE = data.state;
  render();
}

function renderHands() {
  const container = document.getElementById("hands");
  container.innerHTML = "";

  const active = STATE.active_player_index;

  STATE.hands.forEach((h, i) => {
    const handDiv = document.createElement("div");
    const isActiveHand = (active === i);

    handDiv.className = "hand" + (isActiveHand ? " active" : " inactive-hand");

    const name = document.createElement("div");
    name.className = "name";
    name.textContent = `${h.player_name} (visible: ${h.visible_score} points)`;
    handDiv.appendChild(name);

    const grid = document.createElement("div");
    grid.className = "grid";

    h.cards.slice(0, 6).forEach((c, idx) => {
      const cell = document.createElement("div");
      cell.className = "card";
      const imgSrc = `/static/cards/${c.image}`;
      cell.innerHTML = `
        <div class="mono">${idx}</div>
        <img src="${imgSrc}" class="cardImg">
        `;

      cell.onclick = () => {
        // only allow actions on the active hand
        if (!isActiveHand) return;

        if (STATE.phase === "setup") {
          sendCommand(`flip ${idx}`);
          return;
        }

        if (STATE.phase === "play") {
          if (STATE.pending_drawn) {
            sendCommand(`swap ${idx}`);
          }
          return;
        }
      };

      grid.appendChild(cell);
    });

    handDiv.appendChild(grid);
    container.appendChild(handDiv);
  });
}

function renderStatusLine() {
  const discard = STATE.discard_top ? STATE.discard_top.short : "(empty)";
  const drawn = STATE.pending_drawn ? STATE.pending_drawn.long : "(none)";
  document.getElementById("statusLine").textContent =
    `Phase: ${STATE.phase} | Round: ${STATE.round_number} | Cycle: ${STATE.cycle_number} | ` +
    `Deck: ${STATE.deck_count} | Discard top: ${discard} | Drawn: ${drawn}`;
}

function setEnabled(el, enabled) {
  el.classList.toggle("disabled", !enabled);
}

function renderPiles() {
  const deckPile = document.getElementById("deckPile");
  const discardPile = document.getElementById("discardPile");
  const drawnArea = document.getElementById("drawnArea");

  document.getElementById("deckCount").textContent = `${STATE.deck_count} cards`;

  const hasPending = !!STATE.pending_drawn;

  // --- Deck image ---
  const deckImg = document.getElementById("deckImg");
  deckImg.src = "/static/cards/back.png";

  // --- Discard image ---
  const discardImg = document.getElementById("discardImg");
  if (STATE.discard_top) {
    discardImg.src = `/static/cards/${STATE.discard_top.image}`;
    document.getElementById("discardTop").textContent = STATE.discard_top.short;
  } else {
    discardImg.src = "/static/cards/back.png";
    document.getElementById("discardTop").textContent = "(empty)";
  }

    const drawnImg = document.getElementById("drawnImg");
  const drawnPlaceholder = document.getElementById("drawnPlaceholder");

  if (hasPending) {
    drawnImg.src = `/static/cards/${STATE.pending_drawn.image}`;
    drawnImg.style.display = "block";
    drawnPlaceholder.style.display = "none";
  } else {
    drawnImg.removeAttribute("src");
    drawnImg.style.display = "none";
    drawnPlaceholder.style.display = "block";
  }


  const inPlay = (STATE.phase === "play");

  setEnabled(deckPile, inPlay && !hasPending);
  setEnabled(discardPile, inPlay && (hasPending || (STATE.discard_top !== null)));
  setEnabled(drawnArea, inPlay && hasPending);

  deckPile.onclick = () => {
    if (!inPlay || hasPending) return;
    sendCommand("draw deck");
  };

  discardPile.onclick = () => {
    if (!inPlay) return;
    if (hasPending) sendCommand("discard");
    else sendCommand("draw discard");
  };

  drawnArea.onclick = () => {
    if (!inPlay || !hasPending) return;
    sendCommand("discard");
  };
}

function renderControls() {
  const controls = document.getElementById("controls");
  controls.innerHTML = "";

  const helpBtn = document.createElement("button");
  helpBtn.textContent = "Help";
  helpBtn.onclick = () => alert(
    "Setup: click 2 cards for the current player.\n" +
    "Play: click Deck/Discard to draw. Then click a hand card to swap, or click Discard/Drawn to discard the drawn card."
  );
  controls.appendChild(helpBtn);

  if (STATE.phase === "round_over") {
    const next = document.createElement("button");
    next.textContent = "Start Next Round";
    next.onclick = () => startNewRound();
    controls.appendChild(next);

    const stop = document.createElement("button");
    stop.textContent = "Stop";
    stop.onclick = () => alert("Close the tab/window to stop (or Ctrl+C the server).");
    controls.appendChild(stop);
  }

  if (STATE.phase === "game_over") {
    const done = document.createElement("div");
    done.textContent = "Game over. Refresh page to start a new game (or restart server).";
    controls.appendChild(done);
  }
}

function renderLog() {
  const log = document.getElementById("log");
  const msgs = STATE.messages || [];
  if (!msgs.length) {
    log.textContent = "(no messages)";
    return;
  }
  log.innerHTML = msgs.slice(-6).map(m => `<div>${escapeHtml(m)}</div>`).join("");
}

function escapeHtml(s) {
  return String(s)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function render() {
  renderHands();
  renderStatusLine();
  renderPiles();
  renderControls();
  renderLog();
}

fetchState();