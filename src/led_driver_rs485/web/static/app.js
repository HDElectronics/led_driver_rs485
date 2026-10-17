"use strict";

// Segments lit for each character, standard a–g naming (see index.html).
const SEGMENTS = {
  "0": "abcdef", "1": "bc", "2": "abdeg", "3": "abcdg", "4": "bcfg",
  "5": "acdfg", "6": "acdefg", "7": "abc", "8": "abcdefg", "9": "abcdfg",
  "-": "g",
};
const POLL_MS = 400;

const $ = (id) => document.getElementById(id);
const ui = {
  status: $("status"),
  display: $("display"),
  form: $("countdown-form"),
  port: $("port"),
  portHint: $("port-hint"),
  refresh: $("refresh-ports"),
  seconds: $("seconds"),
  baudrate: $("baudrate"),
  playSound: $("play-sound"),
  start: $("start"),
  stop: $("stop"),
  message: $("message"),
};

let running = false;
let pollTimer = null;

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(body.error || `Server answered ${response.status}.`);
  }
  return body;
}

// ---- Display -------------------------------------------------------------

function showOnDisplay(text, state) {
  const digits = ui.display.querySelectorAll(".digit");
  digits.forEach((digit, i) => {
    const lit = SEGMENTS[text[i]] || "";
    digit.querySelectorAll("[data-segment]").forEach((segment) => {
      segment.classList.toggle("is-lit", lit.includes(segment.dataset.segment));
    });
  });
  ui.display.dataset.state = state;
  ui.display.setAttribute("aria-label", `Display shows ${text}`);
}

const twoDigits = (n) => String(n).padStart(2, "0");

function showPreview() {
  const value = Number(ui.seconds.value);
  const valid = ui.seconds.checkValidity() && ui.seconds.value !== "";
  showOnDisplay(valid ? twoDigits(value) : "--", "idle");
}

// ---- State ---------------------------------------------------------------

const STATUS_TEXT = {
  idle: () => "Ready",
  running: (s) => `Counting down on ${s.port}`,
  finished: () => "Finished",
  stopped: (s) => `Stopped at ${twoDigits(s.remaining)}`,
  error: () => "Countdown failed",
};

function render(state) {
  const wasRunning = running;
  running = state.status === "running";
  ui.status.dataset.state = state.status;
  ui.status.textContent = STATUS_TEXT[state.status](state);

  if (state.status === "error") {
    showOnDisplay("--", "error");
    showMessage(state.error);
  } else if (state.remaining === null) {
    showPreview();
  } else {
    // Only flash on the transition to zero, not when reloading a finished page.
    const flash = state.status !== "finished" || wasRunning;
    showOnDisplay(twoDigits(state.remaining), flash ? state.status : "idle");
  }

  if (running) ui.seconds.value = state.seconds;

  for (const control of [ui.port, ui.refresh, ui.seconds, ui.baudrate, ui.playSound]) {
    control.disabled = running;
  }
  ui.start.disabled = running || !ui.port.value;
  ui.stop.disabled = !running;

  clearTimeout(pollTimer);
  if (running) pollTimer = setTimeout(poll, POLL_MS);
}

async function poll() {
  try {
    const state = await api("/api/countdown");
    showMessage("");
    render(state);
  } catch (error) {
    showMessage(`Lost contact with the server: ${error.message}`);
    pollTimer = setTimeout(poll, POLL_MS * 5);
  }
}

function showMessage(text) {
  ui.message.textContent = text || "";
  ui.message.hidden = !text;
}

// ---- Ports ---------------------------------------------------------------

async function loadPorts() {
  const previous = ui.port.value;
  ui.refresh.disabled = true;
  ui.portHint.textContent = "Looking for USB serial adapters…";
  try {
    const { ports } = await api("/api/ports");
    ui.port.replaceChildren(
      ...ports.map((p) => new Option(`${p.description} (${p.device})`, p.device)),
    );
    if (ports.some((p) => p.device === previous)) ui.port.value = previous;
    ui.portHint.textContent = ports.length
      ? ""
      : "No USB serial adapter found. Plug in the RS485 adapter, then select Refresh.";
  } catch (error) {
    ui.portHint.textContent = `Couldn't list serial ports: ${error.message}`;
  } finally {
    ui.refresh.disabled = running;
    ui.start.disabled = running || !ui.port.value;
  }
}

// ---- Actions -------------------------------------------------------------

ui.form.addEventListener("submit", async (event) => {
  event.preventDefault();
  showMessage("");
  ui.start.disabled = true;
  try {
    render(await api("/api/countdown", {
      method: "POST",
      body: JSON.stringify({
        port: ui.port.value,
        seconds: Number(ui.seconds.value),
        baudrate: Number(ui.baudrate.value),
        play_sound: ui.playSound.checked,
      }),
    }));
  } catch (error) {
    showMessage(error.message);
    ui.start.disabled = !ui.port.value;
  }
});

ui.stop.addEventListener("click", async () => {
  ui.stop.disabled = true;
  try {
    render(await api("/api/countdown/stop", { method: "POST" }));
  } catch (error) {
    showMessage(error.message);
    ui.stop.disabled = !running;
  }
});

ui.refresh.addEventListener("click", loadPorts);

ui.seconds.addEventListener("input", () => {
  if (!running) showPreview();
});

// ---- Start-up ------------------------------------------------------------

showPreview();
loadPorts();
api("/api/countdown")  // picks up a countdown that was started before this page loaded
  .then(render)
  .catch((error) => showMessage(`Couldn't reach the server: ${error.message}`));
