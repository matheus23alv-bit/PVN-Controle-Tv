(function () {
  "use strict";

  const STORAGE_KEY = "pvn-controle-tv:state";
  const MAX_LOG = 8;
  const MAX_VOLUME = 100;
  const CHANNELS = [
    { num: 1, name: "Canal 1" },
    { num: 2, name: "Canal 2" },
    { num: 3, name: "Canal 3" },
    { num: 4, name: "Canal 4" },
    { num: 5, name: "Canal 5" },
    { num: 6, name: "Canal 6" },
    { num: 7, name: "Canal 7" },
    { num: 8, name: "Canal 8" },
    { num: 9, name: "Canal 9" },
    { num: 10, name: "Canal 10" },
    { num: 11, name: "Canal 11" },
    { num: 12, name: "Canal 12" },
  ];

  const COMMAND_LABELS = {
    power: "POWER",
    source: "FONTE",
    mute: "MUDO",
    "vol-up": "VOL +",
    "vol-down": "VOL -",
    "chan-up": "CH +",
    "chan-down": "CH -",
    "nav-up": "NAV ▲",
    "nav-down": "NAV ▼",
    "nav-left": "NAV ◀",
    "nav-right": "NAV ▶",
    ok: "OK",
    back: "VOLTAR",
    home: "INÍCIO",
    menu: "MENU",
    "last-channel": "ÚLTIMO CANAL",
    "clear-digit": "APAGAR",
    digit: "DÍGITO",
  };

  const defaultState = {
    power: false,
    channelIndex: 0,
    lastChannelIndex: 0,
    volume: 20,
    muted: false,
    input: "TV",
    pendingDigits: "",
  };

  let state = loadState();
  let digitTimer = null;
  let volumeOsdTimer = null;

  const el = {
    tv: document.getElementById("tv"),
    screen: document.getElementById("screen"),
    channelNum: document.getElementById("channelNum"),
    channelName: document.getElementById("channelName"),
    channelPlate: document.getElementById("channelPlate"),
    osdVolume: document.getElementById("osdVolume"),
    osdVolumeFill: document.getElementById("osdVolumeFill"),
    osdVolumeVal: document.getElementById("osdVolumeVal"),
    osdVolumeIcon: document.getElementById("osdVolumeIcon"),
    osdMute: document.getElementById("osdMute"),
    osdInput: document.getElementById("osdInput"),
    osdClock: document.getElementById("osdClock"),
    irLed: document.getElementById("irLed"),
    irLogList: document.getElementById("irLogList"),
    remote: document.getElementById("remote"),
  };

  function loadState() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return { ...defaultState };
      const parsed = JSON.parse(raw);
      return { ...defaultState, ...parsed };
    } catch (e) {
      return { ...defaultState };
    }
  }

  function saveState() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    } catch (e) {
      /* localStorage indisponível (modo privado, quota) — segue sem persistir */
    }
  }

  function clampVolume(v) {
    return Math.max(0, Math.min(MAX_VOLUME, v));
  }

  function currentChannel() {
    return CHANNELS[state.channelIndex];
  }

  // ---- Emissão do sinal infravermelho (simulado) ----
  function fireIrSignal(cmd, label) {
    el.irLed.classList.remove("active");
    // força reflow para reiniciar a animação em cliques consecutivos rápidos
    void el.irLed.offsetWidth;
    el.irLed.classList.add("active");

    logIrSignal(label || COMMAND_LABELS[cmd] || cmd);
  }

  function logIrSignal(label) {
    const li = document.createElement("li");
    const time = new Date().toLocaleTimeString("pt-BR", { hour12: false });
    li.innerHTML = `<b>${label}</b><time>${time}</time>`;
    el.irLogList.appendChild(li);

    while (el.irLogList.children.length > MAX_LOG) {
      el.irLogList.removeChild(el.irLogList.firstChild);
    }
  }

  // ---- Ações ----
  const actions = {
    power() {
      state.power = !state.power;
      if (!state.power) {
        state.muted = false;
        state.pendingDigits = "";
      }
    },
    source() {
      if (!state.power) return;
      const inputs = ["TV", "HDMI 1", "HDMI 2", "AV"];
      const i = (inputs.indexOf(state.input) + 1) % inputs.length;
      state.input = inputs[i];
    },
    mute() {
      if (!state.power) return;
      state.muted = !state.muted;
      showVolumeOsd(true);
    },
    "vol-up"() {
      if (!state.power) return;
      state.muted = false;
      state.volume = clampVolume(state.volume + 2);
      showVolumeOsd();
    },
    "vol-down"() {
      if (!state.power) return;
      state.muted = false;
      state.volume = clampVolume(state.volume - 2);
      showVolumeOsd();
    },
    "chan-up"() {
      if (!state.power) return;
      changeChannel((state.channelIndex + 1) % CHANNELS.length);
    },
    "chan-down"() {
      if (!state.power) return;
      changeChannel((state.channelIndex - 1 + CHANNELS.length) % CHANNELS.length);
    },
    "last-channel"() {
      if (!state.power) return;
      changeChannel(state.lastChannelIndex);
    },
    "nav-up"() {},
    "nav-down"() {},
    "nav-left"() {},
    "nav-right"() {},
    ok() {},
    back() {},
    home() {
      if (!state.power) return;
      state.input = "TV";
    },
    menu() {},
    digit(digit) {
      if (!state.power) return;
      state.pendingDigits = (state.pendingDigits + digit).slice(-2);
      clearTimeout(digitTimer);
      digitTimer = setTimeout(() => {
        const target = parseInt(state.pendingDigits, 10);
        const idx = CHANNELS.findIndex((c) => c.num === target);
        if (idx !== -1) changeChannel(idx);
        state.pendingDigits = "";
        render();
      }, 900);
    },
    "clear-digit"() {
      state.pendingDigits = "";
    },
  };

  function changeChannel(newIndex) {
    state.lastChannelIndex = state.channelIndex;
    state.channelIndex = newIndex;
  }

  function showVolumeOsd(instant) {
    el.osdVolume.classList.add("show");
    clearTimeout(volumeOsdTimer);
    volumeOsdTimer = setTimeout(() => {
      el.osdVolume.classList.remove("show");
    }, instant ? 1400 : 1800);
  }

  // ---- Renderização ----
  function render() {
    el.tv.dataset.power = state.power ? "on" : "off";

    const ch = currentChannel();
    el.channelNum.textContent = state.pendingDigits || ch.num;
    el.channelName.textContent = ch.name;

    el.osdInput.textContent = state.input;

    const effectiveVolume = state.muted ? 0 : state.volume;
    el.osdVolumeFill.style.width = effectiveVolume + "%";
    el.osdVolumeVal.textContent = effectiveVolume;
    el.osdVolumeIcon.textContent = state.muted ? "🔇" : effectiveVolume === 0 ? "🔈" : effectiveVolume < 50 ? "🔉" : "🔊";
    el.osdMute.classList.toggle("show", state.muted);

    el.remote.classList.toggle("is-off", !state.power);
  }

  function tickClock() {
    el.osdClock.textContent = new Date().toLocaleTimeString("pt-BR", {
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  // ---- Eventos ----
  function handlePress(button) {
    const cmd = button.dataset.cmd;
    if (!cmd) return;

    button.classList.add("pressed");
    setTimeout(() => button.classList.remove("pressed"), 130);

    let label = COMMAND_LABELS[cmd];

    if (cmd === "digit") {
      const digit = button.dataset.digit;
      actions.digit(digit);
      label = `DÍGITO ${digit}`;
    } else if (actions[cmd]) {
      actions[cmd]();
    }

    fireIrSignal(cmd, label);
    saveState();
    render();
  }

  document.querySelectorAll(".btn[data-cmd]").forEach((btn) => {
    btn.addEventListener("click", () => handlePress(btn));
  });

  const KEY_MAP = {
    " ": "power",
    Enter: "ok",
    ArrowUp: "nav-up",
    ArrowDown: "nav-down",
    ArrowLeft: "nav-left",
    ArrowRight: "nav-right",
    "+": "vol-up",
    "-": "vol-down",
    m: "mute",
    Backspace: "back",
    Escape: "home",
  };

  document.addEventListener("keydown", (e) => {
    if (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA") return;

    if (e.key >= "0" && e.key <= "9") {
      const btn = document.querySelector(`.btn-key[data-digit="${e.key}"]`);
      if (btn) handlePress(btn);
      return;
    }

    const cmd = KEY_MAP[e.key];
    if (!cmd) return;
    const btn = document.querySelector(`.btn[data-cmd="${cmd}"]`);
    if (btn) handlePress(btn);
  });

  // ---- Inicialização ----
  tickClock();
  setInterval(tickClock, 1000 * 30);
  render();
})();
