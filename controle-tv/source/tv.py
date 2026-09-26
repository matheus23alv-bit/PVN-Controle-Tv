#!/usr/bin/env python3
"""PVN Controle TV: controle remoto infravermelho no terminal do Termux.

Usa o emissor IR do proprio celular pelo comando termux-infrared-transmit
(pacote termux-api + app Termux:API). Sem dependencias alem do Python.

  tv                     abre o controle na tela
  tv ligar | vol+ | 7    envia um comando e sai (bom para atalhos)
  tv --ajuda             todas as opcoes
"""
import curses
import json
import locale
import os
import queue
import re
import subprocess
import sys
import threading
import time
import unicodedata

APP_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.join(os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config"), "pvn-tv")
PROFILES_DIR = os.path.join(CONFIG_DIR, "perfis")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
MAX_PATTERN_US = 2_000_000  # limite do Android (ConsumerIrManager)


def read_version():
    try:
        with open(os.path.join(APP_DIR, "VERSION"), encoding="utf-8") as f:
            return f.read().strip() or "dev"
    except OSError:
        return "dev"


# ============================================================ protocolos IR
# Cada codificador devolve (frequencia_hz, padrao) em que o padrao alterna
# ligado/desligado em microssegundos, comecando ligado, como o Android espera.

def _bits_lsb(values):
    return [(v >> i) & 1 for v in values for i in range(8)]


def _pulse_distance(bits, header, mark, one, zero):
    pattern = list(header)
    for b in bits:
        pattern += [mark, one if b else zero]
    pattern.append(mark)
    return pattern


def nec(address, command, extended=False):
    """NEC (LG e muitas marcas). extended: endereco de 16 bits (NECext)."""
    if extended or address > 0xFF:
        addr = [address & 0xFF, (address >> 8) & 0xFF]
    else:
        addr = [address & 0xFF, (address ^ 0xFF) & 0xFF]
    lo, hi = command & 0xFF, (command >> 8) & 0xFF
    cmd = [lo, lo ^ 0xFF] if hi in (0, lo ^ 0xFF) else [lo, hi]
    return 38000, _pulse_distance(_bits_lsb(addr + cmd), (9000, 4500), 560, 1690, 560)


def samsung32(address, command):
    """Samsung: endereco repetido, comando e comando invertido."""
    a, c = address & 0xFF, command & 0xFF
    return 38000, _pulse_distance(_bits_lsb([a, a, c, c ^ 0xFF]), (4500, 4500), 560, 1690, 560)


def sirc(address, command, nbits=12):
    """Sony SIRC 12/15/20 bits, enviado 3 vezes como o controle original."""
    addr_bits = {12: 5, 15: 8, 20: 13}[nbits]
    bits = [(command >> i) & 1 for i in range(7)] + [(address >> i) & 1 for i in range(addr_bits)]
    frame = [2400, 600]
    for b in bits:
        frame += [1200 if b else 600, 600]
    frame.pop()  # termina no pulso ligado
    gap = 45000 - sum(frame)  # quadros a cada 45 ms
    pattern = []
    for i in range(3):
        pattern += frame
        if i < 2:
            pattern.append(gap)
    return 40000, pattern


def _levels_to_pattern(levels, unit):
    while levels and levels[0] == 0:
        levels = levels[1:]
    while levels and levels[-1] == 0:
        levels = levels[:-1]
    out, current, run = [], levels[0], 0
    for lv in levels:
        if lv == current:
            run += 1
        else:
            out.append(run * unit)
            current, run = lv, 1
    out.append(run * unit)
    return out


def rc5(address, command, toggle=0):
    """Philips RC5/RC5X (codificacao Manchester, 36 kHz)."""
    field = 0 if command >= 64 else 1
    bits = [1, field, toggle & 1]
    bits += [(address >> i) & 1 for i in range(4, -1, -1)]
    bits += [(command >> i) & 1 for i in range(5, -1, -1)]
    levels = []
    for b in bits:
        levels += [0, 1] if b else [1, 0]
    return 36000, _levels_to_pattern(levels, 889)


def rc6(address, command, toggle=0):
    """Philips RC6 modo 0 (36 kHz)."""
    def bit(b, width=1):
        return [1] * width + [0] * width if b else [0] * width + [1] * width
    levels = [1] * 6 + [0] * 2  # lider: 2664 us ligado, 888 us desligado
    levels += bit(1)
    for b in (0, 0, 0):
        levels += bit(b)
    levels += bit(toggle & 1, 2)
    for value in (address, command):
        for i in range(7, -1, -1):
            levels += bit((value >> i) & 1)
    return 36000, _levels_to_pattern(levels, 444)


ENCODERS = {
    "nec": lambda a, c: nec(a, c),
    "necext": lambda a, c: nec(a, c, extended=True),
    "samsung32": samsung32,
    "sirc": lambda a, c: sirc(a, c, 12),
    "sirc15": lambda a, c: sirc(a, c, 15),
    "sirc20": lambda a, c: sirc(a, c, 20),
    "rc5": rc5,
    "rc5x": rc5,
    "rc6": rc6,
}


def validate_pattern(freq, pattern):
    if not pattern or any((not isinstance(v, int)) or v <= 0 for v in pattern):
        raise ValueError("padrão IR inválido")
    if sum(pattern) > MAX_PATTERN_US:
        raise ValueError("padrão IR maior que 2 s (limite do Android)")
    if not 15000 <= freq <= 100000:
        raise ValueError(f"frequência fora do normal: {freq} Hz")
    return freq, pattern


# ============================================================ teclas e perfis

KEY_LABELS = {
    "power": "Ligar/desligar", "vol_up": "Volume +", "vol_down": "Volume -", "mute": "Mudo",
    "ch_up": "Canal +", "ch_down": "Canal -", "input": "Fonte", "menu": "Menu", "home": "Início",
    "back": "Voltar", "exit": "Exit", "info": "Info", "up": "Cima", "down": "Baixo",
    "left": "Esquerda", "right": "Direita", "ok": "OK",
    **{f"d{i}": f"Dígito {i}" for i in range(10)},
}

# nomes aceitos na linha de comando e nos arquivos importados (normalizados por canon())
ALIASES = {
    "power": ["power", "ligar", "desligar", "liga", "power_on", "on_off", "pwr", "standby", "power_toggle"],
    "vol_up": ["vol_up", "volplus", "vol_plus", "volume_up", "volup", "vol_mais", "volume_plus"],
    "vol_down": ["vol_dn", "vol_down", "volminus", "vol_minus", "volume_down", "voldown", "vol_menos", "volume_minus"],
    "mute": ["mute", "mudo"],
    "ch_up": ["ch_next", "ch_up", "chplus", "ch_plus", "channel_up", "chup", "canal_plus", "canalplus", "prog_plus", "canal_mais"],
    "ch_down": ["ch_prev", "ch_down", "chminus", "ch_minus", "channel_down", "chdown", "canal_minus", "canalminus", "prog_minus", "canal_menos"],
    "input": ["input", "source", "fonte", "entrada", "av", "tv_av", "input_source", "tvav"],
    "menu": ["menu", "settings", "setup", "configuracoes"],
    "home": ["home", "inicio", "smart", "smart_hub", "smarthub"],
    "back": ["back", "return", "voltar", "retornar"],
    "exit": ["exit", "sair_tv"],
    "info": ["info", "display"],
    "up": ["up", "cima", "arrow_up"],
    "down": ["down", "baixo", "arrow_down"],
    "left": ["left", "esquerda", "arrow_left"],
    "right": ["right", "direita", "arrow_right"],
    "ok": ["ok", "enter", "select", "confirmar"],
}
for _i in range(10):
    ALIASES[f"d{_i}"] = [str(_i), f"num_{_i}", f"key_{_i}", f"digit_{_i}", f"btn_{_i}"]
_ALIAS_INDEX = {alias: key for key, names in ALIASES.items() for alias in names}


def canon(name):
    s = unicodedata.normalize("NFKD", name.strip().lower()).encode("ascii", "ignore").decode()
    s = s.replace("+", "plus").replace("-", "minus") if len(s) > 1 else s
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
    return _ALIAS_INDEX.get(s)


def _parsed(proto, address, keys):
    return {k: {"protocol": proto, "address": address, "command": c} for k, c in keys.items()}


# Codigos conferidos bit a bit contra os codigos publicados de cada marca
# (ex.: Samsung ligar = E0E040BF, LG ligar = 20DF10EF, Sony ligar = A90).
BUILTIN = {
    "Samsung": _parsed("samsung32", 0x07, {
        "power": 0x02, "vol_up": 0x07, "vol_down": 0x0B, "mute": 0x0F, "ch_up": 0x12, "ch_down": 0x10,
        "input": 0x01, "menu": 0x1A, "home": 0x79, "back": 0x58, "exit": 0x2D, "info": 0x1F,
        "up": 0x60, "down": 0x61, "left": 0x65, "right": 0x62, "ok": 0x68,
        "d1": 0x04, "d2": 0x05, "d3": 0x06, "d4": 0x08, "d5": 0x09, "d6": 0x0A,
        "d7": 0x0C, "d8": 0x0D, "d9": 0x0E, "d0": 0x11,
    }),
    "LG": _parsed("nec", 0x04, {
        "power": 0x08, "vol_up": 0x02, "vol_down": 0x03, "mute": 0x09, "ch_up": 0x00, "ch_down": 0x01,
        "input": 0x0B, "menu": 0x43, "home": 0x7C, "back": 0x28, "exit": 0x5B, "info": 0xAA,
        "up": 0x40, "down": 0x41, "left": 0x07, "right": 0x06, "ok": 0x44,
        "d1": 0x11, "d2": 0x12, "d3": 0x13, "d4": 0x14, "d5": 0x15, "d6": 0x16,
        "d7": 0x17, "d8": 0x18, "d9": 0x19, "d0": 0x10,
    }),
    "Sony": _parsed("sirc", 0x01, {
        "power": 21, "vol_up": 18, "vol_down": 19, "mute": 20, "ch_up": 16, "ch_down": 17,
        "input": 37, "home": 96, "info": 58, "up": 116, "down": 117, "left": 52, "right": 51, "ok": 101,
        **{f"d{i}": i - 1 for i in range(1, 10)}, "d0": 9,
    }),
}


def parse_ir_file(text):
    """Le um arquivo .ir do Flipper Zero (formato do banco Flipper-IRDB)."""
    blocks, current = [], {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            if current:
                blocks.append(current)
                current = {}
            continue
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        k, v = k.strip().lower(), v.strip()
        if k == "name" and "name" in current:
            blocks.append(current)
            current = {}
        current[k] = v
    if current:
        blocks.append(current)

    keys, skipped = {}, []
    for b in blocks:
        if "name" not in b or "type" not in b:
            continue
        key = canon(b["name"])
        try:
            if b["type"] == "raw":
                freq = int(float(b.get("frequency", "38000")))
                data = [int(x) for x in b["data"].split()]
                signal = {"protocol": "raw", "frequency": freq, "data": data}
            elif b["type"] == "parsed":
                proto = b["protocol"].lower()
                if proto not in ENCODERS:
                    raise ValueError(f"protocolo {b['protocol']} não suportado")
                addr = int.from_bytes(bytes.fromhex(b["address"].replace(" ", "")), "little")
                cmd = int.from_bytes(bytes.fromhex(b["command"].replace(" ", "")), "little")
                signal = {"protocol": proto, "address": addr, "command": cmd}
            else:
                raise ValueError(f"tipo {b['type']} desconhecido")
            encode(signal)
        except (KeyError, ValueError) as e:
            skipped.append(f"{b['name']}: {e}")
            continue
        if key is None:
            skipped.append(f"{b['name']}: nome sem botão equivalente")
            continue
        keys.setdefault(key, signal)
    return keys, skipped


def encode(signal):
    if signal["protocol"] == "raw":
        return validate_pattern(signal["frequency"], list(signal["data"]))
    freq, pattern = ENCODERS[signal["protocol"]](signal["address"], signal["command"])
    return validate_pattern(freq, pattern)


def load_profiles():
    profiles = {name: keys for name, keys in BUILTIN.items()}
    if os.path.isdir(PROFILES_DIR):
        for fn in sorted(os.listdir(PROFILES_DIR)):
            if fn.lower().endswith(".ir"):
                try:
                    with open(os.path.join(PROFILES_DIR, fn), encoding="utf-8") as f:
                        keys, _ = parse_ir_file(f.read())
                except OSError:
                    continue
                if keys:
                    profiles[fn[:-3]] = keys
    return profiles


def load_config():
    try:
        with open(CONFIG_FILE, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def save_config(cfg):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    tmp = CONFIG_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
    os.replace(tmp, CONFIG_FILE)


def import_profile(path, name=None):
    with open(path, encoding="utf-8") as f:
        keys, skipped = parse_ir_file(f.read())
    if not keys:
        raise ValueError("nenhum botão reconhecido no arquivo")
    name = name or os.path.splitext(os.path.basename(path))[0]
    name = re.sub(r"[^\w\- ]+", "", name).strip() or "Minha TV"
    os.makedirs(PROFILES_DIR, exist_ok=True)
    with open(path, encoding="utf-8") as src, open(os.path.join(PROFILES_DIR, name + ".ir"), "w", encoding="utf-8") as dst:
        dst.write(src.read())
    return name, keys, skipped


# ============================================================ emissor

HINT_API = "Instale o pacote: pkg install termux-api"
HINT_APP = "Instale o app Termux:API (mesma loja do Termux) e abra-o uma vez"


class Transmitter:
    def __init__(self, simulate=False):
        self.simulate = simulate
        self.cmd = os.environ.get("TV_IR_CMD", "termux-infrared-transmit")
        self.freq_cmd = os.environ.get("TV_IR_FREQ_CMD", "termux-infrared-frequencies")

    def send(self, freq, pattern, timeout=10):
        if self.simulate:
            return True, f"simulado: {freq // 1000} kHz, {len(pattern)} pulsos"
        try:
            r = subprocess.run([self.cmd, "-f", str(freq), ",".join(map(str, pattern))],
                               capture_output=True, text=True, timeout=timeout, stdin=subprocess.DEVNULL)
        except FileNotFoundError:
            return False, HINT_API
        except subprocess.TimeoutExpired:
            return False, "Termux:API não respondeu. " + HINT_APP
        out = (r.stdout + r.stderr).strip()
        low = out.lower()
        if r.returncode != 0 or "no infrared" in low or "not available" in low or "error" in low:
            if "infrared" in low:
                return False, "Este celular não tem emissor infravermelho"
            return False, out or f"falha ao transmitir (código {r.returncode})"
        return True, f"{freq // 1000} kHz"

    def check(self, timeout=10):
        """(ok, mensagem, faixas) sobre o emissor IR do aparelho."""
        if self.simulate:
            return True, "modo simulado: nenhum sinal sai do celular", []
        try:
            r = subprocess.run([self.freq_cmd], capture_output=True, text=True, timeout=timeout,
                               stdin=subprocess.DEVNULL)
        except FileNotFoundError:
            return False, HINT_API, []
        except subprocess.TimeoutExpired:
            return False, "Termux:API não respondeu. " + HINT_APP, []
        out = r.stdout.strip()
        try:
            ranges = json.loads(out) if out else []
        except ValueError:
            return False, (out or r.stderr.strip() or "resposta inesperada do Termux:API")[:120], []
        if not ranges:
            return False, "Este celular não tem emissor infravermelho", []
        lo = min(x.get("min", 0) for x in ranges) // 1000
        hi = max(x.get("max", 0) for x in ranges) // 1000
        return True, f"emissor IR pronto ({lo}-{hi} kHz)", ranges


class Worker:
    """Envia os sinais fora do laco da tela: o Termux:API leva ~0,3 s por chamada."""

    def __init__(self, tx):
        self.tx = tx
        self.jobs = queue.Queue()
        self.results = queue.Queue()
        threading.Thread(target=self._run, daemon=True).start()

    def check(self):
        # thread propria: sem o app Termux:API a verificacao trava ate o timeout e nao pode atrasar os botoes
        threading.Thread(target=lambda: self.results.put(("check",) + self.tx.check()), daemon=True).start()

    def _run(self):
        while True:
            _, label, freq, pattern = self.jobs.get()
            ok, msg = self.tx.send(freq, pattern)
            self.results.put(("sent", ok, label, msg))


# ============================================================ tela

BUTTON_ROWS = [
    [("power", "LIGAR", "red"), ("mute", "MUDO", "yellow"), ("input", "FONTE", "cyan")],
    [("vol_up", "VOL +", "blue"), ("up", "▲", "white"), ("ch_up", "CH +", "blue")],
    [("left", "◀", "white"), ("ok", "OK", "green"), ("right", "▶", "white")],
    [("vol_down", "VOL -", "blue"), ("down", "▼", "white"), ("ch_down", "CH -", "blue")],
    [("back", "VOLTAR", "magenta"), ("home", "INÍCIO", "magenta"), ("menu", "MENU", "magenta")],
    [("d1", "1", "white"), ("d2", "2", "white"), ("d3", "3", "white")],
    [("d4", "4", "white"), ("d5", "5", "white"), ("d6", "6", "white")],
    [("d7", "7", "white"), ("d8", "8", "white"), ("d9", "9", "white")],
    [("info", "INFO", "cyan"), ("d0", "0", "white"), ("exit", "EXIT", "cyan")],
]

KEYMAP = {
    ord("l"): "power", ord("L"): "power", ord("m"): "mute", ord("M"): "mute", ord("f"): "input",
    ord("+"): "vol_up", ord("="): "vol_up", ord("-"): "vol_down", ord("_"): "vol_down",
    ord("."): "ch_up", ord(">"): "ch_up", ord(","): "ch_down", ord("<"): "ch_down",
    curses.KEY_UP: "up", curses.KEY_DOWN: "down", curses.KEY_LEFT: "left", curses.KEY_RIGHT: "right",
    10: "ok", 13: "ok", curses.KEY_ENTER: "ok", ord(" "): "ok",
    ord("v"): "back", curses.KEY_BACKSPACE: "back", 127: "back", 8: "back",
    ord("i"): "home", ord("n"): "menu", ord("o"): "info", ord("x"): "exit",
    **{ord(str(i)): f"d{i}" for i in range(10)},
}

HELP_LINES = (
    "Toque num botão para enviar o sinal.",
    "Aponte o topo do celular para a TV.",
    "",
    "Teclas:",
    "  l ligar     m mudo      f fonte",
    "  + -  volume      . ,  canal",
    "  setas, Enter=OK, v voltar",
    "  i início  n menu  o info  x exit",
    "  0-9 canal direto",
    "",
    "  t trocar TV     d descobrir TV",
    "  ? ajuda         q sair",
)

COLOR_NAMES = ["red", "yellow", "cyan", "blue", "white", "green", "magenta"]


def safe_addstr(win, y, x, text, attr=0):
    h, w = win.getmaxyx()
    if y < 0 or y >= h or x < 0 or x >= w:
        return
    text = text[: w - x]
    if text:
        try:
            win.addstr(y, x, text, attr)
        except curses.error:
            pass


class App:
    def __init__(self, scr, simulate=False, profile=None):
        self.scr = scr
        self.version = read_version()
        self.worker = Worker(Transmitter(simulate))
        self.profiles = load_profiles()
        self.cfg = load_config()
        wanted = profile or self.cfg.get("perfil")
        self.profile = wanted if wanted in self.profiles else None
        self.screen = "remote" if self.profile else "choose"
        self.ir_ok, self.ir_msg = None, "verificando emissor infravermelho..."
        self.status, self.status_ok = "", True
        self.flash_key, self.flash_until = None, 0.0
        self.hits = []
        self.choose_index = 0
        self.discover_list, self.discover_i = [], 0
        self.done = False
        self._init_curses()
        self.worker.check()

    def _init_curses(self):
        curses.curs_set(0)
        self.scr.keypad(True)
        self.colors = {}
        if curses.has_colors():
            curses.start_color()
            try:
                curses.use_default_colors()
                bg = -1
            except curses.error:
                bg = curses.COLOR_BLACK
            for i, name in enumerate(COLOR_NAMES, start=1):
                curses.init_pair(i, getattr(curses, "COLOR_" + name.upper()), bg)
                self.colors[name] = curses.color_pair(i)
        try:
            # RELEASED precisa estar na mascara: evento de soltar descartado pelo ncurses
            # deixa o getch() bloqueado ate a proxima tecla, ignorando o timeout
            curses.mousemask(curses.BUTTON1_PRESSED | curses.BUTTON1_RELEASED | curses.BUTTON1_CLICKED)
            curses.mouseinterval(0)
        except curses.error:
            pass

    def c(self, name):
        return self.colors.get(name, 0)

    # --------------------------------------------------------- acoes

    def keys(self):
        return self.profiles.get(self.profile, {})

    def press(self, key):
        signal = self.keys().get(key)
        label = KEY_LABELS.get(key, key)
        self.flash_key, self.flash_until = key, time.monotonic() + 0.18
        if signal is None:
            self.status, self.status_ok = f"{label}: esta TV não tem esse código", False
            return
        freq, pattern = encode(signal)
        self.worker.jobs.put(("send", label, freq, pattern))
        self.status, self.status_ok = f"enviando {label}...", True

    def choose(self, name):
        self.profile = name
        self.cfg["perfil"] = name
        try:
            save_config(self.cfg)
        except OSError:
            pass
        self.screen = "remote"
        self.status, self.status_ok = f"TV selecionada: {name}", True

    def start_discover(self):
        self.discover_list = [n for n, k in self.profiles.items() if "power" in k]
        self.discover_i = 0
        self.screen = "discover"
        self._discover_send()

    def _discover_send(self):
        name = self.discover_list[self.discover_i]
        freq, pattern = encode(self.profiles[name]["power"])
        self.worker.jobs.put(("send", f"Ligar ({name})", freq, pattern))

    def discover_answer(self, yes):
        if yes:
            self.choose(self.discover_list[self.discover_i])
            return
        self.discover_i += 1
        if self.discover_i >= len(self.discover_list):
            self.screen = "choose"
            self.status, self.status_ok = "Nenhuma marca embutida reagiu. Importe o arquivo da sua TV.", False
        else:
            self._discover_send()

    # --------------------------------------------------------- entrada

    def on_key(self, k):
        if k == curses.KEY_RESIZE:
            return
        if k == curses.KEY_MOUSE:
            self.on_mouse()
            return
        if self.screen == "help":
            self.screen = "remote" if self.profile else "choose"
            return
        if self.screen == "discover":
            if k in (ord("s"), ord("S"), ord("y"), ord("Y")):
                self.discover_answer(True)
            elif k in (ord("n"), ord("N"), ord(" ")):
                self.discover_answer(False)
            elif k in (ord("q"), 27):
                self.screen = "choose"
            return
        if self.screen == "choose":
            names = list(self.profiles)
            options = len(names) + 1
            if k in (curses.KEY_UP, ord("w")):
                self.choose_index = (self.choose_index - 1) % options
            elif k in (curses.KEY_DOWN, ord("s")):
                self.choose_index = (self.choose_index + 1) % options
            elif k in (10, 13, curses.KEY_ENTER, ord(" ")):
                self._choose_option(self.choose_index)
            elif k == ord("d"):
                self.start_discover()
            elif k in (ord("q"), 27):
                if self.profile:
                    self.screen = "remote"
                else:
                    self.done = True
            return
        # controle
        if k in (ord("q"), ord("Q"), 27):
            self.done = True
        elif k in (ord("?"), ord("h")):
            self.screen = "help"
        elif k in (ord("t"), ord("T")):
            self.screen = "choose"
            names = list(self.profiles)
            self.choose_index = names.index(self.profile) if self.profile in names else 0
        elif k in (ord("d"), ord("D")):
            self.start_discover()
        elif k in KEYMAP:
            self.press(KEYMAP[k])

    def _choose_option(self, idx):
        names = list(self.profiles)
        if idx < len(names):
            self.choose(names[idx])
        else:
            self.start_discover()

    def on_mouse(self):
        try:
            _, mx, my, _, bstate = curses.getmouse()
        except curses.error:
            return
        if not bstate & (curses.BUTTON1_PRESSED | curses.BUTTON1_CLICKED):
            return
        if self.screen == "help":
            self.screen = "remote" if self.profile else "choose"
            return
        for (y0, x0, y1, x1, action) in self.hits:
            if y0 <= my <= y1 and x0 <= mx <= x1:
                action()
                return

    def poll_results(self):
        changed = False
        while True:
            try:
                r = self.results_get()
            except queue.Empty:
                return changed
            changed = True
            if r[0] == "check":
                self.ir_ok, self.ir_msg = r[1], r[2]
            else:
                _, ok, label, msg = r
                self.status, self.status_ok = (f"✓ {label} enviado ({msg})" if ok else f"✗ {label}: {msg}"), ok

    def results_get(self):
        return self.worker.results.get_nowait()

    # --------------------------------------------------------- desenho

    def render(self):
        scr = self.scr
        scr.erase()
        self.hits = []
        h, w = scr.getmaxyx()
        if w < 30 or h < 16:
            for i, line in enumerate(("Tela pequena demais", f"atual {w}x{h}, mínimo 30x16",
                                      "Esconda o teclado ou", "diminua a fonte (pinça)", "q sai")):
                safe_addstr(scr, i, 0, line, curses.A_BOLD if i == 0 else 0)
            scr.refresh()
            return
        width = min(w, 56)
        title = " PVN CONTROLE TV"
        right = f"TV: {self.profile} " if self.profile else ""
        safe_addstr(scr, 0, 0, (title + " " * width)[: width - len(right)] + right, curses.A_REVERSE | curses.A_BOLD)
        ir_attr = self.c("green") if self.ir_ok else (self.c("yellow") if self.ir_ok is None else self.c("red"))
        safe_addstr(scr, 1, 0, ("● " if self.ir_ok else "○ ") + self.ir_msg, ir_attr)

        if self.screen == "remote":
            self._render_remote(h, width)
        elif self.screen == "choose":
            self._render_choose(h, width)
        elif self.screen == "discover":
            self._render_discover(h, width)
        else:
            for i, line in enumerate(HELP_LINES):
                safe_addstr(scr, 3 + i, 0, line, curses.A_BOLD if i == 3 else 0)
            safe_addstr(scr, 4 + len(HELP_LINES), 0, "toque ou tecle para voltar", curses.A_DIM)

        attr = (self.c("green") if self.status_ok else self.c("red")) | curses.A_BOLD
        safe_addstr(scr, h - 1, 0, self.status[: width], attr)
        scr.refresh()

    def _render_remote(self, h, width):
        top = 3
        rows = len(BUTTON_ROWS)
        footer = 2
        tall = h - top - footer >= rows * 3
        bh = 3 if tall else 1
        gap = 1
        bw = (width - 2 * gap) // 3
        available = self.keys()
        flashing = self.flash_key if time.monotonic() < self.flash_until else None
        for r, row in enumerate(BUTTON_ROWS):
            y = top + r * bh
            for col, (key, label, color) in enumerate(row):
                x = col * (bw + gap)
                attr = self.c(color) | curses.A_BOLD
                if key not in available:
                    attr = curses.A_DIM
                if key == flashing:
                    attr |= curses.A_REVERSE
                self._button(y, x, bw, bh, label, attr)
                self.hits.append((y, x, y + bh - 1, x + bw - 1, lambda k=key: self.press(k)))
        hint_y = top + rows * bh
        if hint_y < h - 1:
            safe_addstr(self.scr, hint_y, 0, "t trocar TV  d descobrir  ? ajuda  q sair"[:width], curses.A_DIM)

    def _button(self, y, x, bw, bh, label, attr):
        inner = bw - 2
        text = label.center(inner)[:inner]
        if bh == 3:
            safe_addstr(self.scr, y, x, "╭" + "─" * inner + "╮", attr)
            safe_addstr(self.scr, y + 1, x, "│" + text + "│", attr)
            safe_addstr(self.scr, y + 2, x, "╰" + "─" * inner + "╯", attr)
        else:
            safe_addstr(self.scr, y, x, "[" + text + "]", attr)

    def _render_choose(self, h, width):
        safe_addstr(self.scr, 3, 0, "Qual é a marca da sua TV?", curses.A_BOLD)
        names = list(self.profiles)
        options = [(n, "embutido" if n in BUILTIN else "importado") for n in names]
        options.append(("Descobrir automaticamente", "testa cada marca"))
        for i, (name, note) in enumerate(options):
            y = 5 + i * 2
            if y >= h - 3:
                break
            sel = i == self.choose_index
            attr = (curses.A_REVERSE | curses.A_BOLD) if sel else curses.A_BOLD
            line = f" {name} ".ljust(width - len(note) - 2) + note + " "
            safe_addstr(self.scr, y, 0, line[:width], attr if sel else 0)
            if not sel:
                safe_addstr(self.scr, y, 0, f" {name}", curses.A_BOLD)
            self.hits.append((y, 0, y, width - 1, lambda i=i: self._choose_option(i)))
        tip_y = 5 + len(options) * 2
        for j, line in enumerate(("Outra marca (Philco, TCL, AOC...)?",
                                  "Baixe o arquivo .ir da sua TV no",
                                  "Flipper-IRDB e rode:",
                                  "  tv --importar arquivo.ir")):
            safe_addstr(self.scr, tip_y + j, 0, line[:width], curses.A_DIM)

    def _render_discover(self, h, width):
        name = self.discover_list[self.discover_i]
        total = len(self.discover_list)
        lines = (
            f"Descobrir TV  {self.discover_i + 1} de {total}",
            "",
            "Aponte o celular para a TV.",
            f"Enviei o LIGAR de: {name}",
            "",
            "A TV ligou ou desligou?",
        )
        for i, line in enumerate(lines):
            safe_addstr(self.scr, 3 + i, 0, line[:width], curses.A_BOLD if i in (0, 3) else 0)
        bw = (width - 1) // 2
        y = 3 + len(lines) + 1
        self._button(y, 0, bw, 3, "SIM", self.c("green") | curses.A_BOLD)
        self._button(y, bw + 1, bw, 3, "NÃO, PRÓXIMA", self.c("yellow") | curses.A_BOLD)
        self.hits.append((y, 0, y + 2, bw - 1, lambda: self.discover_answer(True)))
        self.hits.append((y, bw + 1, y + 2, 2 * bw, lambda: self.discover_answer(False)))
        safe_addstr(self.scr, y + 4, 0, "s sim   n próxima   q cancelar"[:width], curses.A_DIM)

    # --------------------------------------------------------- laco

    def run(self):
        dirty = True
        while not self.done:
            self.scr.timeout(60 if (self.flash_key and time.monotonic() < self.flash_until) else 150)
            k = self.scr.getch()
            self.scr.timeout(0)
            while k != -1 and not self.done:
                self.on_key(k)
                dirty = True
                k = self.scr.getch()
            if self.poll_results():
                dirty = True
            if self.flash_key and time.monotonic() >= self.flash_until:
                self.flash_key = None
                dirty = True
            if dirty and not self.done:
                self.render()
                dirty = False


# ============================================================ linha de comando

USAGE = """PVN Controle TV - controle remoto infravermelho pelo Termux

Uso:
  tv                          abre o controle na tela
  tv <botão>                  envia um botão e sai. Ex.: tv ligar, tv vol+, tv 7
  tv --perfil <marca> ...     usa outra TV só desta vez (Samsung, LG, Sony ou importada)
  tv --listar                 mostra as TVs disponíveis
  tv --importar <arq.ir> [--nome <nome>]   importa arquivo do Flipper-IRDB
  tv --diagnostico            confere o emissor infravermelho do celular
  tv --atalhos                cria atalhos na tela inicial (app Termux:Widget)
  tv --simular                abre sem transmitir (para testar num celular sem IR)
  tv --versao | --ajuda

Botões: ligar, mudo, fonte, vol+, vol-, canal+, canal-, cima, baixo, esquerda,
direita, ok, voltar, inicio, menu, info, exit, 0-9
"""

SHORTCUTS = [("TV Ligar", "ligar"), ("TV Volume +", "vol+"), ("TV Volume -", "vol-"),
             ("TV Mudo", "mudo"), ("TV Canal +", "canal+"), ("TV Canal -", "canal-")]


def _take(args, flag):
    if flag in args:
        i = args.index(flag)
        if i + 1 >= len(args):
            raise SystemExit(f"falta o valor de {flag}")
        value = args[i + 1]
        del args[i:i + 2]
        return value
    return None


def cli(argv):
    args = list(argv)
    if "--ajuda" in args or "-h" in args or "--help" in args:
        print(USAGE)
        return 0
    if "--versao" in args or "-v" in args:
        print(read_version())
        return 0
    simulate = "--simular" in args
    args = [a for a in args if a != "--simular"]
    profile = _take(args, "--perfil")
    name = _take(args, "--nome")
    importing = _take(args, "--importar")
    profiles = load_profiles()
    tx = Transmitter(simulate)

    if importing:
        try:
            pname, keys, skipped = import_profile(importing, name)
        except (OSError, ValueError) as e:
            print(f"Não consegui importar: {e}")
            return 1
        cfg = load_config()
        cfg["perfil"] = pname
        save_config(cfg)
        print(f"TV '{pname}' importada com {len(keys)} botões e selecionada.")
        for s in skipped[:10]:
            print(f"  ignorado: {s}")
        return 0

    if "--listar" in args:
        current = load_config().get("perfil")
        for pname, keys in profiles.items():
            mark = "*" if pname == current else " "
            kind = "embutido" if pname in BUILTIN else "importado"
            print(f"{mark} {pname} ({kind}, {len(keys)} botões)")
        return 0

    if "--diagnostico" in args:
        ok, msg, ranges = tx.check()
        print(("OK   " if ok else "ERRO ") + msg)
        if ranges:
            print("     faixas:", ", ".join(f"{r.get('min')}-{r.get('max')} Hz" for r in ranges))
        return 0 if ok else 1

    if "--atalhos" in args:
        folder = os.path.expanduser("~/.shortcuts")
        os.makedirs(folder, exist_ok=True)
        for title, cmd in SHORTCUTS:
            path = os.path.join(folder, title)
            with open(path, "w", encoding="utf-8") as f:
                f.write(f"#!/usr/bin/env sh\nexec tv {cmd}\n")
            os.chmod(path, 0o755)
        print(f"{len(SHORTCUTS)} atalhos criados em ~/.shortcuts.")
        print("Instale o app Termux:Widget e adicione o widget na tela inicial.")
        return 0

    if args:
        key = canon(args[0])
        if key is None:
            print(f"Botão desconhecido: {args[0]}. Veja: tv --ajuda")
            return 2
        pname = profile or load_config().get("perfil")
        if pname not in profiles:
            print("Nenhuma TV escolhida. Abra 'tv' e escolha a marca, ou use --perfil.")
            return 2
        signal = profiles[pname].get(key)
        if signal is None:
            print(f"A TV '{pname}' não tem código para {KEY_LABELS[key]}.")
            return 2
        ok, msg = tx.send(*encode(signal))
        print(("✓ " if ok else "✗ ") + f"{KEY_LABELS[key]} ({pname}): {msg}")
        return 0 if ok else 1

    if profile and profile not in profiles:
        print(f"TV desconhecida: {profile}. Veja: tv --listar")
        return 2
    locale.setlocale(locale.LC_ALL, "")
    curses.wrapper(lambda scr: App(scr, simulate, profile).run())
    return 0


def main():
    os.environ.setdefault("ESCDELAY", "25")
    try:
        return cli(sys.argv[1:])
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())
