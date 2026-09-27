#!/usr/bin/env python3
"""Teclado Termux: troca a barra de teclas extras do Termux entre perfis.

Perfis: padrão melhorado (uso diário), jogo (Tower Defense), TV (controle
infravermelho), padrão do Termux e a barra que a pessoa tinha antes. O tv e o
td chamam "teclas --entrar <perfil>" ao abrir e "teclas --sair" ao fechar.
Só mexe na linha extra-keys do ~/.termux/termux.properties.
"""
import curses
import fcntl
import json
import locale
import os
import re
import shutil
import subprocess
import sys
import unicodedata

APP_DIR = os.path.dirname(os.path.abspath(__file__))
PROPS = os.path.expanduser("~/.termux/termux.properties")
BACKUP = PROPS + ".antes-do-teclas"
TD_BACKUP = PROPS + ".antes-do-td"          # backup do instalador do Tower Defense 3.1
TD_MARKER = "# instalado pelo tower-defense"  # o td 3.1 fixava a barra do jogo com esta marca
MARK = "# teclas: "                           # "# teclas: <perfil>" logo acima da linha extra-keys
NO_FILE = "# teclas: arquivo nao existia"
CONFIG_DIR = os.path.join(os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config"), "teclas")
STATE_FILE = os.path.join(CONFIG_DIR, "estado.json")
LOCK_FILE = os.path.join(CONFIG_DIR, ".trava")


def read_version():
    try:
        with open(os.path.join(APP_DIR, "VERSION"), encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return "?"


def is_termux():
    return bool(os.environ.get("TERMUX_VERSION")) or os.path.isdir("/data/data/com.termux/files")


# ============================================================ perfis

def k(key=None, show=None, popup=None, macro=None):
    """Uma tecla da barra. popup: tecla ao deslizar para cima (texto ou {"macro", "show"})."""
    return {"key": key, "show": show, "popup": popup, "macro": macro}


PROFILES = {
    "melhorado": {
        "name": "Padrão melhorado",
        "info": "📺 abre a TV e 🏰 o jogo; deslize para cima: ^C, ~, |, PGUP, PGDN, limpar, colar",
        "short": "📺 TV, 🏰 jogo, deslize p/ cima",
        "rows": [
            [k("ESC", popup={"macro": "CTRL c", "show": "^C"}), k("/", popup="~"), k("-", popup="|"),
             k("HOME", popup="PGUP"), k("UP"), k("END", popup="PGDN"),
             k(macro="t v ENTER", show="📺"), k(macro="t d ENTER", show="🏰")],
            [k("TAB", popup={"macro": "CTRL l", "show": "limpar"}), k("CTRL"), k("ALT"),
             k("LEFT"), k("DOWN"), k("RIGHT"), k("KEYBOARD", popup="PASTE"),
             k(macro="t e c l a s ENTER", show="TECLAS")],
        ],
    },
    "jogo": {
        "name": "Jogo (Tower Defense)",
        "info": "torres 1-4, melhorar, vender, onda, 2×, mira e pausa",
        "short": "torres, onda, mira, pausa",
        "rows": [
            [k("ESC"), k("1", "🏹"), k("2", "💣"), k("3", "🔮"), k("4", "🌀"),
             k("u", "⏫"), k("x", "💲"), k("UP"), k("ENTER", "OK")],
            [k("p", "||"), k("n", "ONDA"), k("f", "⏩"), k("t", "🎯"), k("h", "?"),
             k("KEYBOARD"), k("LEFT"), k("DOWN"), k("RIGHT")],
        ],
    },
    "tv": {
        "name": "Controle da TV",
        "info": "segure VOL+ ou VOL- para repetir; setas, OK e canais",
        "short": "segure VOL para repetir",
        "rows": [
            [k("ESC", "SAIR"), k("l", "LIGAR"), k("m", "MUDO"), k("f", "FONTE"), k("PGUP", "VOL+"),
             k(".", "CH+"), k("BKSP", "VOLTAR"), k("UP"), k("ENTER", "OK")],
            [k("KEYBOARD"), k("i", "INÍCIO"), k("n", "MENU"), k("o", "INFO"), k("PGDN", "VOL-"),
             k(",", "CH-"), k("LEFT"), k("DOWN"), k("RIGHT")],
        ],
    },
}
# a barra que vem com o Termux (usada quando não há extra-keys no arquivo)
TERMUX_DEFAULT = [[k("ESC"), k("/"), k("-"), k("HOME"), k("UP"), k("END"), k("PGUP")],
                  [k("TAB"), k("CTRL"), k("ALT"), k("LEFT"), k("DOWN"), k("RIGHT"), k("PGDN")]]
CHOICES = ["melhorado", "jogo", "tv", "padrao", "original"]
NAMES = {"padrao": "Padrão do Termux", "original": "A sua de antes", "personalizada": "Personalizada",
         "td-antigo": "Jogo (fixada pelo td 3.1)", **{p: v["name"] for p, v in PROFILES.items()}}
INFO = {"padrao": "a barra que vem com o Termux", "original": "a barra que você usava antes do teclas"}
ALIASES = {
    "melhorado": "melhorado", "padrao-melhorado": "melhorado", "normal": "melhorado", "diario": "melhorado",
    "jogo": "jogo", "game": "jogo", "td": "jogo", "tower-defense": "jogo",
    "tv": "tv", "controle": "tv", "controle-tv": "tv",
    "padrao": "padrao", "termux": "padrao", "padrao-termux": "padrao",
    "original": "original", "antes": "original", "minha": "original",
}
APP_PROFILES = ("jogo", "tv")  # entram só enquanto o app está aberto

SPECIAL = {"ESC", "TAB", "CTRL", "ALT", "FN", "HOME", "END", "PGUP", "PGDN", "INS", "DEL", "BKSP", "UP",
           "DOWN", "LEFT", "RIGHT", "ENTER", "SPACE", "KEYBOARD", "DRAWER", "PASTE"}
LABELS = {"ESC": "ESC", "TAB": "TAB", "CTRL": "CTRL", "ALT": "ALT", "HOME": "HOME", "END": "END",
          "PGUP": "PGUP", "PGDN": "PGDN", "UP": "↑", "DOWN": "↓", "LEFT": "←", "RIGHT": "→",
          "ENTER": "↲", "BKSP": "⌫", "KEYBOARD": "⌨", "PASTE": "COLAR", "DEL": "DEL", "SPACE": "␣"}


def canon(name):
    s = unicodedata.normalize("NFKD", name.strip().lower()).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return ALIASES.get(s)


def _quote(text):
    """Texto entre aspas simples; o que não é ASCII vira \\uXXXX, que o Termux lê em qualquer versão."""
    out = []
    for ch in text:
        if ord(ch) < 128:
            out.append(ch)
        else:
            b = ch.encode("utf-16-be")
            out += ["\\u%02x%02x" % (b[i], b[i + 1]) for i in range(0, len(b), 2)]
    return "'" + "".join(out) + "'"


def _token(key):
    return key if key in SPECIAL else _quote(key)


def _popup(p):
    if isinstance(p, dict):
        return "{macro: %s, display: %s}" % (_quote(p["macro"]), _quote(p["show"]))
    return _token(p)


def render_key(key):
    if key["macro"]:
        return "{macro: %s, display: %s}" % (_quote(key["macro"]), _quote(key["show"]))
    if not key["show"] and not key["popup"]:
        return _token(key["key"])
    parts = ["key: " + _token(key["key"])]
    if key["show"]:
        parts.append("display: " + _quote(key["show"]))
    if key["popup"]:
        parts.append("popup: " + _popup(key["popup"]))
    return "{" + ", ".join(parts) + "}"


def render(profile):
    """A linha extra-keys do perfil, no formato do termux.properties."""
    rows = PROFILES[profile]["rows"]
    return "extra-keys = [" + ", ".join("[" + ", ".join(render_key(x) for x in row) + "]" for row in rows) + "]"


def label(key):
    return key["show"] or LABELS.get(key["key"], key["key"])


# ============================================================ termux.properties

def read_lines(path=PROPS):
    try:
        with open(path, encoding="utf-8") as f:
            return f.read().splitlines()
    except OSError:
        return []


def write_lines(lines, path=PROPS):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp-teclas"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n" if lines else "")
    os.replace(tmp, path)


_KEY_RE = re.compile(r"^\s*extra-keys\s*[=:\s]")


def _continues(line):
    """A linha termina com uma barra invertida sem par: o valor segue na próxima."""
    s = line.rstrip()
    return (len(s) - len(s.rstrip("\\"))) % 2 == 1


def _is_mark(line):
    return line.startswith(MARK) or line.strip() == TD_MARKER


def find_blocks(lines):
    """[(início, fim)] de cada atribuição extra-keys (fim exclusivo), com a marca logo acima, se houver."""
    blocks, i = [], 0
    while i < len(lines):
        line = lines[i]
        comment = line.strip().startswith(("#", "!"))
        end = i + 1
        if not comment:  # comentário não continua na linha de baixo
            while end < len(lines) and _continues(lines[end - 1]):
                end += 1
        if not comment and _KEY_RE.match(line):
            start = i - 1 if i > 0 and _is_mark(lines[i - 1]) else i
            blocks.append((start, end))
        i = end
    return blocks


def current_block(lines):
    """As linhas da última atribuição extra-keys (a que vale), com a marca; [] se não houver."""
    blocks = find_blocks(lines)
    if not blocks:
        return []
    a, b = blocks[-1]
    return lines[a:b]


def block_value(block):
    """O valor da atribuição, numa linha só (para comparar)."""
    body = [x for x in block if not _is_mark(x)]
    if not body:
        return None
    parts = []
    for x in body:
        x = x.strip()
        if _continues(x):
            x = x[:-1]
        parts.append(x)
    text = re.sub(r"^extra-keys\s*[=:]?", "", " ".join(parts).strip())
    return re.sub(r"\s+", "", text)


TD_OLD_VALUE = "[['ESC','1','2','3','4','u','x','UP','ENTER'],['p','n','f','h','q','KEYBOARD','LEFT','DOWN','RIGHT']]"


def detect(lines=None):
    """Qual barra está no arquivo: um perfil, "padrao", "td-antigo" ou "personalizada"."""
    block = current_block(read_lines() if lines is None else lines)
    value = block_value(block)
    if value is None:
        return "padrao"
    for p in PROFILES:
        if value == block_value([render(p)]):
            return p
    if value == TD_OLD_VALUE and any(x.strip() == TD_MARKER for x in block):
        return "td-antigo"
    return "personalizada"


def replace_block(lines, block):
    """Tira todas as atribuições extra-keys (e as marcas delas) e põe o bloco no lugar da primeira."""
    blocks = find_blocks(lines)
    at = blocks[0][0] if blocks else len(lines)
    out = [line for i, line in enumerate(lines) if not any(a <= i < b for a, b in blocks)]
    return out[:at] + list(block) + out[at:]


def block_for(profile, state):
    if profile == "padrao":
        return []
    if profile == "original":
        return list(state.get("original") or [])
    return [MARK + profile, render(profile)]


# ============================================================ estado

def load_state():
    try:
        with open(STATE_FILE, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
    except (OSError, ValueError):
        pass
    return {}


def save_state(state):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    tmp = STATE_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=1)
    os.replace(tmp, STATE_FILE)


def auto_on(state):
    return state.get("auto", True) is not False


def _proc(pid):
    """Estado e hora de início do processo, de /proc/<pid>/stat. ("", "") se não existe.

    A hora de início distingue o app que pediu a barra de outro processo que pegou o
    mesmo número depois (o Android reaproveita PID).
    """
    try:
        with open(f"/proc/{int(pid)}/stat", encoding="utf-8", errors="replace") as f:
            data = f.read()
    except (OSError, ValueError):
        return "", ""
    # o nome do processo vem entre parênteses e pode ter espaços: conta a partir do último ")"
    fields = data[data.rfind(")") + 1:].split()
    if len(fields) < 21:
        return "", ""
    return fields[0], fields[19]   # estado (R, S, Z...) e starttime


def _vivo(pid, inicio=None):
    """O app que pediu a barra ainda está rodando?

    Um processo zumbi (morreu, o pai ainda não o recolheu) conta como morto: a barra
    dele tem de voltar. inicio é a hora de início guardada quando ele pediu a barra.
    """
    try:
        pid = int(pid)
    except (TypeError, ValueError):
        return False
    if pid <= 0:
        return False
    estado, agora = _proc(pid)
    if estado:
        if estado == "Z":
            return False                      # zumbi: já morreu
        return not inicio or agora == inicio  # mesmo número, outro processo: o dono morreu
    if not os.path.isdir("/proc"):
        try:
            os.kill(pid, 0)                   # sem /proc: só dá para saber se existe
        except ProcessLookupError:
            return False
        except OSError:
            return True
        return True
    return False


def _recuperar(state):
    """Devolve a barra quando o app que a pediu morreu sem avisar (Android encerrou, bateria).

    Roda com a trava já tomada. Devolve True se o arquivo mudou.
    """
    if "base" not in state or "dono" not in state:
        return False
    if _vivo(state["dono"], state.get("dono_inicio")):
        return False
    base = state.pop("base")
    state.pop("dono", None)
    state.pop("dono_inicio", None)
    return _write_block(state, base, read_lines())


class Lock:
    """Uma troca por vez: o td fecha e o "--sair" começa antes do "--entrar" terminar."""

    def __enter__(self):
        os.makedirs(CONFIG_DIR, exist_ok=True)
        self.f = open(LOCK_FILE, "w")
        fcntl.flock(self.f, fcntl.LOCK_EX)
        return self

    def __exit__(self, *exc):
        fcntl.flock(self.f, fcntl.LOCK_UN)
        self.f.close()


def _td_original():
    """A barra de antes do td 3.1, tirada do backup que o instalador dele fez."""
    lines = read_lines(TD_BACKUP)
    if not lines or lines[0].startswith("# td: arquivo nao existia"):
        return []
    return [x for x in current_block(lines) if x.strip() != TD_MARKER]


def remember_original(state, lines):
    """Na primeira troca, guarda a barra da pessoa e um backup do arquivo."""
    if "original" in state:
        return
    block = current_block(lines)
    if any(x.strip() == TD_MARKER for x in block):
        state["original"] = _td_original()
    elif any(x.startswith(MARK) for x in block):
        state["original"] = []  # estado perdido: a barra do teclas não é a original
    else:
        state["original"] = block
    if not os.path.exists(BACKUP):
        os.makedirs(os.path.dirname(BACKUP), exist_ok=True)
        if os.path.exists(PROPS):
            shutil.copyfile(PROPS, BACKUP)
        else:
            with open(BACKUP, "w", encoding="utf-8") as f:
                f.write(NO_FILE + "\n")


def reload_termux():
    exe = shutil.which("termux-reload-settings")
    if not exe:
        return False
    try:
        subprocess.run([exe], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, timeout=15)
    except (OSError, subprocess.SubprocessError):
        return False
    return True


def _write_block(state, block, lines):
    new = replace_block(lines, block)
    if new != lines:
        if not new and read_lines(BACKUP)[:1] == [NO_FILE]:
            try:
                os.remove(PROPS)
            except OSError:
                pass
        else:
            write_lines(new)
        return True
    return False


def apply(profile):
    """Troca a barra pelo perfil escolhido pela pessoa. Devolve True se o arquivo mudou."""
    with Lock():
        state = load_state()
        state.pop("base", None)  # escolha manual: nada para voltar depois
        state.pop("dono", None)
        state.pop("dono_inicio", None)
        if profile in CHOICES:
            state["escolha"] = profile  # escolha da pessoa: para onde voltar, e o que ela quis de propósito
        lines = read_lines()
        remember_original(state, lines)
        changed = _write_block(state, block_for(profile, state), lines)
        save_state(state)
        if changed:
            reload_termux()
        return changed


def enter(profile, owner=None):
    """O tv ou o td abriu: põe a barra dele e guarda a atual para voltar.

    owner é o PID do app. Serve para devolver a barra se ele morrer sem chamar --sair.
    """
    if not is_termux():
        return False
    with Lock():
        state = load_state()
        if not auto_on(state):
            return False
        _recuperar(state)   # sobrou barra de um app que morreu: devolve antes de guardar a base
        lines = read_lines()
        remember_original(state, lines)
        if detect(lines) not in APP_PROFILES:  # vindo de outro app (ou de um fechamento sem --sair): mantém a base
            state["base"] = current_block(lines)
        if owner is not None:
            state["dono"] = owner
            state["dono_inicio"] = _proc(owner)[1]
        else:
            state.pop("dono", None)
            state.pop("dono_inicio", None)
        changed = _write_block(state, block_for(profile, state), lines)
        save_state(state)
        if changed:
            reload_termux()
        return changed


def leave():
    """O tv ou o td fechou: volta a barra que estava antes dele."""
    if not is_termux():
        return False
    with Lock():
        state = load_state()
        if "base" not in state:
            # Nada guardado para voltar. Se a barra na tela é de um app e não foi a pessoa
            # que a escolheu, ela ficou presa (app encerrado pelo Android, estado perdido):
            # volta para a escolha da pessoa. Se ela escolheu essa barra de propósito
            # (teclas jogo), fica como está.
            lines = read_lines()
            atual = detect(lines)
            if atual not in APP_PROFILES or state.get("escolha") == atual:
                return False
            state.pop("dono", None)
            state.pop("dono_inicio", None)
            changed = _write_block(state, block_for(state.get("escolha", "original"), state), lines)
            save_state(state)
            if changed:
                reload_termux()
            return changed
        base = state.pop("base")
        state.pop("dono", None)
        state.pop("dono_inicio", None)
        changed = _write_block(state, base, read_lines())
        save_state(state)
        if changed:
            reload_termux()
        return changed


def sanear():
    """Devolve a barra se o app que a pediu morreu sem avisar. Roda em toda chamada do teclas."""
    if not is_termux():
        return False
    with Lock():
        state = load_state()
        changed = _recuperar(state)
        if changed or "dono" not in state:
            save_state(state)
        if changed:
            reload_termux()
        return changed


def set_auto(on):
    with Lock():
        state = load_state()
        state["auto"] = bool(on)
        save_state(state)


def remove():
    """Desinstalação: devolve a barra que a pessoa tinha e apaga o estado."""
    with Lock():
        state = load_state()
        changed = False
        if "original" in state:
            changed = _write_block(state, state["original"], read_lines())
        elif detect() in PROFILES:
            changed = _write_block(state, [], read_lines())
        try:
            os.remove(BACKUP)
        except OSError:
            pass
        if changed:
            reload_termux()
    shutil.rmtree(CONFIG_DIR, ignore_errors=True)
    return changed


def available():
    """As escolhas do menu; "A sua de antes" só aparece se a pessoa tinha uma barra própria."""
    state = load_state()
    mine = bool(state["original"]) if "original" in state else detect() == "personalizada"
    return [c for c in CHOICES if c != "original" or mine]


def now_choice():
    """A barra atual como escolha do menu: a da pessoa aparece como "A sua de antes"."""
    now = detect()
    if now == "personalizada":
        state = load_state()
        if "original" not in state or block_value(state["original"]) == block_value(current_block(read_lines())):
            return "original"
    return now


# ============================================================ tela

def cell_width(ch):
    if unicodedata.combining(ch) or ch in "‍️":
        return 0
    return 2 if unicodedata.east_asian_width(ch) in "WF" else 1


def text_width(s):
    return sum(cell_width(c) for c in s)


def clip(s, cells):
    out, w = "", 0
    for ch in s:
        cw = cell_width(ch)
        if w + cw > cells:
            break
        out += ch
        w += cw
    return out


def put(win, y, x, text, attr=0):
    h, w = win.getmaxyx()
    if y < 0 or y >= h or x >= w:
        return
    text = clip(text, w - x - (1 if y == h - 1 else 0))
    if text:
        try:
            win.addstr(y, x, text, attr)
        except curses.error:
            pass


def preview_rows(choice):
    if choice in PROFILES:
        return PROFILES[choice]["rows"]
    if choice == "padrao":
        return TERMUX_DEFAULT
    return None


class Menu:
    def __init__(self, scr):
        self.scr = scr
        self.version = read_version()
        self.sel = 0
        self.status, self.status_ok = "", True
        self.hits = []
        self.done = False
        curses.curs_set(0)
        scr.keypad(True)
        self.colors = {}
        if curses.has_colors():
            curses.start_color()
            try:
                curses.use_default_colors()
                bg = -1
            except curses.error:
                bg = curses.COLOR_BLACK
            for i, name in enumerate(("green", "yellow", "cyan", "red", "magenta"), start=1):
                curses.init_pair(i, getattr(curses, "COLOR_" + name.upper()), bg)
                self.colors[name] = curses.color_pair(i)
        try:
            curses.mousemask(curses.BUTTON1_PRESSED | curses.BUTTON1_RELEASED | curses.BUTTON1_CLICKED)
            curses.mouseinterval(0)
        except curses.error:
            pass
        now = now_choice()
        choices = available()
        if now in choices:
            self.sel = choices.index(now)

    def c(self, name):
        return self.colors.get(name, 0)

    def use(self, choice):
        self.status, self.status_ok = f"aplicando {NAMES[choice]}...", True
        self.draw()
        apply(choice)
        where = "o Termux recarregou" if shutil.which("termux-reload-settings") else "recarregue o Termux"
        self.status, self.status_ok = f"✔ {NAMES[choice]}; {where}", True

    def toggle_auto(self):
        on = not auto_on(load_state())
        set_auto(on)
        self.status, self.status_ok = ("✔ troca automática ligada" if on else "troca automática desligada"), True

    def on_key(self, ch):
        choices = available()
        self.sel = min(self.sel, len(choices) - 1)
        if ch in (ord("q"), ord("Q"), 27):
            self.done = True
        elif ch in (curses.KEY_UP, ord("w")):
            self.sel = (self.sel - 1) % len(choices)
        elif ch in (curses.KEY_DOWN, ord("s")):
            self.sel = (self.sel + 1) % len(choices)
        elif ch in (10, 13, curses.KEY_ENTER, ord(" ")):
            self.use(choices[self.sel])
        elif ord("1") <= ch < ord("1") + len(choices):
            self.sel = ch - ord("1")
            self.use(choices[self.sel])
        elif ch in (ord("a"), ord("A")):
            self.toggle_auto()
        elif ch == curses.KEY_MOUSE:
            try:
                _, mx, my, _, bstate = curses.getmouse()
            except curses.error:
                return
            if bstate & (curses.BUTTON1_PRESSED | curses.BUTTON1_CLICKED):
                for y0, y1, action in self.hits:
                    if y0 <= my <= y1:
                        action()
                        return

    def _select_and_use(self, i):
        self.sel = i
        self.use(available()[i])

    def draw(self):
        scr = self.scr
        scr.erase()
        self.hits = []
        h, w = scr.getmaxyx()
        if w < 30 or h < 12:
            put(scr, 0, 0, "Tela pequena demais", curses.A_BOLD)
            put(scr, 1, 0, f"atual {w}x{h}, mínimo 30x12")
            put(scr, 2, 0, "q sai")
            scr.refresh()
            return
        width = min(w, 60)
        title = " TECLADO DO TERMUX"
        ver = f"{self.version} "
        put(scr, 0, 0, title + " " * (width - text_width(title) - len(ver)) + ver, curses.A_REVERSE | curses.A_BOLD)
        now = now_choice()
        state = load_state()
        put(scr, 1, 0, f" Agora: {NAMES.get(now, now)}", self.c("green") | curses.A_BOLD)
        choices = available()
        self.sel = min(self.sel, len(choices) - 1)
        room = h - 2 - 1  # sobra depois do título e da linha de estado
        two = room >= len(choices) * 2 + 3 + 4  # descrição embaixo de cada escolha
        y = 3 if room > len(choices) + 4 else 2
        for i, c in enumerate(choices):
            sel = i == self.sel
            mark = " ✔" if c == now else ""
            name = f" {i + 1}  {NAMES[c]}"
            line = name + " " * max(1, width - text_width(name) - text_width(mark) - 1) + mark + " "
            put(scr, y, 0, line, (curses.A_REVERSE | curses.A_BOLD) if sel else curses.A_BOLD)
            y0 = y
            if two:
                y += 1
                info = PROFILES[c]["info"] if c in PROFILES else INFO[c]
                if text_width(info) > width - 5:
                    info = PROFILES[c]["short"] if c in PROFILES else info
                put(scr, y, 4, clip(info, width - 5), curses.A_DIM)
            self.hits.append((y0, y, lambda i=i: self._select_and_use(i)))
            y += 1
        y += 1
        on = auto_on(state)
        if y < h - 2:
            put(scr, y, 0, f" Troca automática: {'SIM' if on else 'NÃO'}", (self.c("green") if on else self.c("yellow")) | curses.A_BOLD)
            y0 = y
            if y + 1 < h - 2:
                y += 1
                if on:
                    tip = "tv e td trocam a barra ao abrir e voltam ao sair" if width >= 50 else "tv e td trocam ao abrir e voltam"
                else:
                    tip = "tv e td não mexem na barra"
                put(scr, y, 1, clip(tip, width - 2), curses.A_DIM)
            self.hits.append((y0, y, self.toggle_auto))
            y += 2
        rows = preview_rows(choices[self.sel])
        if rows and y + len(rows) + 1 < h - 1:
            put(scr, y, 1, "Prévia:", curses.A_DIM)
            y += 1
            for row in rows:
                cw = max(3, (width - 1) // len(row))
                x = 1
                for key in row:
                    lab = clip(label(key), cw - 1)
                    pad = cw - 1 - text_width(lab)
                    put(scr, y, x, " " * (pad // 2) + lab + " " * (pad - pad // 2), curses.A_REVERSE)
                    x += cw
                y += 1
            y += 1
        elif choices[self.sel] == "original" and y + 2 < h - 1:
            put(scr, y, 1, "Prévia: a barra que estava no seu termux.properties", curses.A_DIM)
            y += 2
        if y < h - 1:
            put(scr, y, 1, clip("toque usa · ↑↓ Enter · a troca automática · q sai"
                                if width >= 52 else "toque usa · a troca automática · q sai", width - 2), curses.A_DIM)
        attr = (self.c("green") if self.status_ok else self.c("red")) | curses.A_BOLD
        put(scr, h - 1, 0, self.status, attr)
        scr.refresh()

    def run(self):
        while not self.done:
            self.draw()
            ch = self.scr.getch()
            if ch == curses.KEY_RESIZE:
                continue
            self.on_key(ch)


# ============================================================ linha de comando

USAGE = """Teclado Termux - troca a barra de teclas extras do Termux

Uso:
  teclas                  menu na tela (toque para escolher)
  teclas <perfil>         troca na hora: melhorado, jogo, tv, padrao ou original
  teclas --estado         mostra a barra atual e a troca automática
  teclas --auto sim|nao   liga ou desliga a troca automática do tv e do td
  teclas --lista          mostra os perfis
  teclas --versao | --ajuda

Perfis:
  melhorado   barra do dia a dia: 📺 abre a TV, 🏰 o jogo, TECLAS abre este menu;
              deslize para cima: ^C, ~, |, PGUP, PGDN, limpar a tela, colar
  jogo        Tower Defense: torres 1-4, melhorar, vender, onda, 2×, mira, pausa
  tv          controle da TV: segure VOL+ ou VOL- para repetir
  padrao      a barra que vem com o Termux
  original    a barra que você tinha antes do teclas

Com a troca automática ligada, o tv e o td põem a barra deles ao abrir
(teclas --entrar <perfil> --dono <processo>) e devolvem a anterior ao fechar
(teclas --sair). A barra de um app nunca fica presa: se ele for encerrado pelo
Android sem chamar --sair, a barra volta na primeira vez que o teclas rodar.
"""


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    # antes de tudo: se o td ou o tv foi encerrado pelo Android sem devolver a barra,
    # ela volta agora. Assim a barra de um app nunca fica presa no Termux da pessoa.
    if args[:1] != ["--entrar"]:   # o --entrar já recupera por dentro, com a trava tomada
        sanear()
    if not args:
        if not sys.stdin.isatty():
            print(USAGE)
            return 0
        os.environ.setdefault("ESCDELAY", "25")
        locale.setlocale(locale.LC_ALL, "")
        try:
            curses.wrapper(lambda scr: Menu(scr).run())
        except KeyboardInterrupt:
            return 130
        return 0
    cmd = args[0]
    if cmd in ("--ajuda", "-h", "--help"):
        print(USAGE)
        return 0
    if cmd in ("--versao", "-v"):
        print(read_version())
        return 0
    if cmd == "--lista":
        for c in CHOICES:
            print(f"{c:10} {NAMES[c]}: {PROFILES[c]['info'] if c in PROFILES else INFO[c]}")
        return 0
    if cmd == "--estado":
        state = load_state()
        now = now_choice()
        print(f"barra: {NAMES.get(now, now)}")
        print(f"troca automática: {'sim' if auto_on(state) else 'não'}")
        if "base" in state:
            print("volta ao fechar o app: " + NAMES.get(detect(state["base"]), "a barra anterior"))
            if "dono" in state:
                vivo = _vivo(state["dono"], state.get("dono_inicio"))
                print(f"app que pediu a barra: processo {state['dono']}"
                      + ("" if vivo else " (já encerrado: a barra volta agora)"))
        return 0
    if cmd == "--auto":
        value = args[1].strip().lower() if len(args) > 1 else ""
        if value not in ("sim", "s", "nao", "não", "n", "on", "off"):
            print("Uso: teclas --auto sim|nao")
            return 2
        set_auto(value in ("sim", "s", "on"))
        print("troca automática " + ("ligada" if value in ("sim", "s", "on") else "desligada"))
        return 0
    if cmd == "--entrar":
        profile = canon(args[1]) if len(args) > 1 else None
        if profile not in PROFILES:
            return 2
        owner = None
        if "--dono" in args:
            i = args.index("--dono")
            if i + 1 < len(args):
                owner = args[i + 1]
        enter(profile, owner)
        return 0
    if cmd == "--sair":
        leave()
        return 0
    if cmd == "--remover":
        remove()
        print("barra de teclas original de volta")
        return 0
    profile = canon(cmd)
    if profile is None:
        print(f"Perfil desconhecido: {cmd}. Use: melhorado, jogo, tv, padrao ou original")
        return 2
    if profile == "original" and "original" not in available():
        print("Você não tinha uma barra própria: a de antes é o padrão do Termux.")
        profile = "padrao"
    changed = apply(profile)
    note = "" if changed else " (já estava)"
    if changed and not shutil.which("termux-reload-settings"):
        note = "; recarregue o Termux para ver"
    print(f"✔ {NAMES[profile]}{note}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
