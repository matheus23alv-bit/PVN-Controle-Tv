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

  const INPUTS = ["TV", "HDMI 1", "HDMI 2", "AV"];

  let state = loadState();
  let digitTimer = null;
  let volumeOsdTimer = null;
  let noticeTimer = null;
  let notice = "";

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

  function validIndex(v) {
    return Number.isInteger(v) && v >= 0 && v < CHANNELS.length;
  }

  function sanitize(raw) {
    const s = { ...defaultState };
    if (!raw || typeof raw !== "object") return s;
    if (typeof raw.power === "boolean") s.power = raw.power;
    if (typeof raw.muted === "boolean") s.muted = raw.muted;
    if (validIndex(raw.channelIndex)) s.channelIndex = raw.channelIndex;
    if (validIndex(raw.lastChannelIndex)) s.lastChannelIndex = raw.lastChannelIndex;
    if (Number.isFinite(raw.volume)) s.volume = clampVolume(Math.round(raw.volume));
    if (INPUTS.includes(raw.input)) s.input = raw.input;
    return s;
  }

  function loadState() {
    try {
      return sanitize(JSON.parse(localStorage.getItem(STORAGE_KEY)));
    } catch (e) {
      return { ...defaultState };
    }
  }

  function saveState() {
    try {
      // pendingDigits é transitório: persistir faria o número ficar preso na tela após recarregar
      const { pendingDigits, ...persisted } = state;
      localStorage.setItem(STORAGE_KEY, JSON.stringify(persisted));
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
    clearTimeout(fireIrSignal.timer);
    fireIrSignal.timer = setTimeout(() => el.irLed.classList.remove("active"), 220);

    logIrSignal(label || COMMAND_LABELS[cmd] || cmd);
  }

  function logIrSignal(label) {
    const li = document.createElement("li");
    const b = document.createElement("b");
    const time = document.createElement("time");
    b.textContent = label;
    time.textContent = new Date().toLocaleTimeString("pt-BR", { hour12: false });
    li.append(b, time);
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
        cancelDigits();
      }
    },
    source() {
      if (!state.power) return;
      const i = (INPUTS.indexOf(state.input) + 1) % INPUTS.length;
      state.input = INPUTS[i];
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
        if (!state.pendingDigits) return;
        const target = parseInt(state.pendingDigits, 10);
        const idx = CHANNELS.findIndex((c) => c.num === target);
        if (idx !== -1) changeChannel(idx);
        else showNotice(`Canal ${target} indisponível`);
        state.pendingDigits = "";
        saveState();
        render();
      }, 900);
    },
    "clear-digit"() {
      cancelDigits();
    },
  };

  function cancelDigits() {
    // sem cancelar o timer, a confirmação disparava com dígitos vazios e mostrava "Canal NaN"
    clearTimeout(digitTimer);
    state.pendingDigits = "";
  }

  function changeChannel(newIndex) {
    if (newIndex === state.channelIndex) return;
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

  function showNotice(text) {
    notice = text;
    clearTimeout(noticeTimer);
    noticeTimer = setTimeout(() => {
      notice = "";
      render();
    }, 1600);
  }

  // ---- Renderização ----
  function render() {
    el.tv.dataset.power = state.power ? "on" : "off";

    const ch = currentChannel();
    el.channelNum.textContent = state.pendingDigits || ch.num;
    el.channelName.textContent = notice || ch.name;
    el.channelName.classList.toggle("is-notice", Boolean(notice));

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

  // só estes comandos repetem ao segurar a tecla; os demais (power, mudo, fonte) disparariam em rajada
  const REPEATABLE = new Set(["vol-up", "vol-down", "chan-up", "chan-down", "nav-up", "nav-down", "nav-left", "nav-right"]);

  document.addEventListener("keydown", (e) => {
    if (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA") return;
    if (e.ctrlKey || e.metaKey || e.altKey) return;

    const key = e.key.length === 1 ? e.key.toLowerCase() : e.key;
    let btn = null;
    if (key >= "0" && key <= "9") {
      btn = document.querySelector(`.btn-key[data-digit="${key}"]`);
    } else if (KEY_MAP[key]) {
      btn = document.querySelector(`.btn[data-cmd="${KEY_MAP[key]}"]`);
    }
    if (!btn) return;

    // evita que Espaço/Enter também "cliquem" o botão focado e disparem um segundo comando
    e.preventDefault();
    if (e.repeat && !REPEATABLE.has(btn.dataset.cmd)) return;
    handlePress(btn);
  });

  // ---- Inicialização ----
  tickClock();
  setInterval(tickClock, 5000);
  render();
})();
