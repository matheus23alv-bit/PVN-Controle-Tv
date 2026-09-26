#!/usr/bin/env python3
"""Tower Defense para o terminal do Termux.

Um arquivo, so biblioteca padrao (curses). Jogue pelo toque ou pelo teclado.
  td                abre o menu
  td --tutorial     comeca direto no tutorial
  td --sem-emoji    desenha com letras (para celulares que desalinham emojis)
  td --sem-toque    desativa o toque na tela
"""
import bisect
import curses
import json
import locale
import math
import os
import random
import sys
import time
import unicodedata

APP_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.join(os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config"), "td-termux")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

W, H = 18, 12                    # mapa em casas; cada casa ocupa 2 colunas do terminal
MIN_W, MIN_H = 2 * W + 2, H + 5  # borda + HUD + seletor + status
FPS = 20
IDLE_WAIT = 0.25

PATH_SEGS = [(0, 1, 15, 1), (15, 1, 15, 4), (15, 4, 2, 4), (2, 4, 2, 7),
             (2, 7, 15, 7), (15, 7, 15, 10), (15, 10, 1, 10)]

TOWERS = {
    "1": {"name": "Arqueiro", "emoji": "🏹", "text": "A", "cost": 20, "range": 3.0, "dmg": 6, "rate": 0.5,
          "info": "rápido, alvo único"},
    "2": {"name": "Canhão", "emoji": "💣", "text": "C", "cost": 50, "range": 2.3, "dmg": 20, "rate": 1.4,
          "splash": 1.1, "info": "explode e atinge vizinhos"},
    "3": {"name": "Mago", "emoji": "🔮", "text": "M", "cost": 35, "range": 4.0, "dmg": 10, "rate": 0.9,
          "info": "maior alcance"},
    "4": {"name": "Vórtice", "emoji": "🌀", "text": "V", "cost": 40, "range": 2.6, "dmg": 4, "rate": 0.8,
          "slow": 0.5, "slow_time": 1.6, "slow_area": 1.2, "info": "deixa lento quem está perto"},
}
ENEMIES = {
    "normal": {"name": "Invasor", "emoji": "👾", "text": "o", "hp": 28, "speed": 1.5, "gold": 4, "dmg": 1},
    "rapido": {"name": "Rato", "emoji": "🐀", "text": "*", "hp": 15, "speed": 2.6, "gold": 4, "dmg": 1},
    "tanque": {"name": "Ogro", "emoji": "👹", "text": "@", "hp": 100, "speed": 0.85, "gold": 10, "dmg": 2},
    "chefe": {"name": "Dragão", "emoji": "🐉", "text": "&", "hp": 520, "speed": 0.6, "gold": 50, "dmg": 5},
}
START_GOLD = 100
START_LIFE = 20
SPAWN_INTERVAL = 0.7
HP_GROWTH = 1.16
MAX_LEVEL = 3
STEP = 0.05  # passo maximo da simulacao, para nada atravessar alcance entre quadros

LEVEL_BG = {2: 65, 3: 136}
TEXT_COLORS = {"1": 51, "2": 226, "3": 201, "4": 39, "normal": 160, "rapido": 124, "tanque": 52, "chefe": 201}

GLYPHS = {  # emoji / texto, sempre 2 colunas
    "spawn": ("🚪", "S "), "base": ("🏰", "B "), "kill": ("💥", "x "), "mark": ("✨", "<>"),
    "life": ("💗", "V:"), "gold": ("💰", "$:"), "wave": ("🌊", "O:"), "kills": ("💀", "K:"),
    "trophy": ("🏆", "* "), "party": ("🎉", "! "), "fast": ("⏩", ">>"),
}


def read_version():
    try:
        with open(os.path.join(APP_DIR, "VERSION"), encoding="utf-8") as f:
            return f.read().strip() or "dev"
    except OSError:
        return "dev"


def build_path():
    pts = []
    for i, (x0, y0, x1, y1) in enumerate(PATH_SEGS):
        x, y = x0, y0
        line = [(x, y)]
        while (x, y) != (x1, y1):
            x += (x1 > x) - (x1 < x)
            y += (y1 > y) - (y1 < y)
            line.append((x, y))
        pts += line if i == 0 else line[1:]
    return pts


PATH = build_path()
PATH_SET = set(PATH)


def load_config():
    try:
        with open(CONFIG_FILE, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def save_config(cfg):
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        tmp = CONFIG_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
        os.replace(tmp, CONFIG_FILE)
    except OSError:
        pass


# ================================================================ logica

class Tower:
    def __init__(self, x, y, key):
        self.x, self.y, self.key = x, y, key
        self.level = 1
        self.spent = TOWERS[key]["cost"]
        self.last = -999.0
        self.span = None

    @property
    def cfg(self):
        return TOWERS[self.key]

    @property
    def damage(self):
        return self.cfg["dmg"] * (1 + 0.6 * (self.level - 1))

    @property
    def range(self):
        return self.cfg["range"] + 0.4 * (self.level - 1)

    @property
    def rate(self):
        return self.cfg["rate"]

    @property
    def upgrade_cost(self):
        return None if self.level >= MAX_LEVEL else int(self.cfg["cost"] * 0.7 * self.level)

    @property
    def refund(self):
        return self.spent // 2


class Enemy:
    def __init__(self, kind, wave, hp_scale=1.0):
        base = ENEMIES[kind]
        self.kind = kind
        self.max_hp = base["hp"] * (HP_GROWTH ** (wave - 1)) * hp_scale
        self.hp = self.max_hp
        self.speed = base["speed"]
        self.gold = int(base["gold"] * (1 + 0.02 * (wave - 1)))
        self.dmg = base["dmg"]
        self.progress = 0.0
        self.alive = True
        self.leaked = False
        self.slow_until = -1.0
        self.slow_factor = 1.0
        self.hit_until = -1.0


def enemy_pos(e):
    i = int(e.progress)
    if i >= len(PATH) - 1:
        return PATH[-1]
    f = e.progress - i
    (x0, y0), (x1, y1) = PATH[i], PATH[i + 1]
    return x0 + (x1 - x0) * f, y0 + (y1 - y0) * f


def tower_span(t):
    # um inimigo entre as casas i e i+1 fica a no maximo 1 casa de PATH[i]
    reach = t.range + 1
    idx = [i for i, (x, y) in enumerate(PATH) if math.hypot(x - t.x, y - t.y) <= reach]
    return (idx[0], idx[-1]) if idx else (0, -1)


def make_wave(n, rng):
    kinds = []
    for _ in range(min(4 + 2 * n, 60)):
        r = rng.random()
        if r < 0.15 and n >= 3:
            kinds.append("tanque")
        elif r < 0.40 and n >= 2:
            kinds.append("rapido")
        else:
            kinds.append("normal")
    if n % 5 == 0:
        kinds += ["chefe"] * (n // 10 + 1)
    return kinds


class Game:
    def __init__(self, seed=None, tutorial=False):
        self.rng = random.Random(seed)
        self.tutorial = tutorial
        self.gold, self.life, self.wave, self.kills = START_GOLD, START_LIFE, 0, 0
        self.towers = {}
        self.enemies, self.queue = [], []
        self.spawn_timer = 0.0
        self.wave_active = False
        self.over = False
        self.time = 0.0
        self.speed = 1
        self.effects = []  # (x, y, ate_quando)

    # ------------------------------------------------------ acoes
    def can_build(self, x, y):
        return 0 <= x < W and 0 <= y < H and (x, y) not in PATH_SET and (x, y) not in self.towers

    def build(self, x, y, key):
        if (x, y) in PATH_SET:
            return False, "Não dá para construir na trilha"
        if (x, y) in self.towers:
            return False, "Já tem torre aqui"
        cfg = TOWERS[key]
        if self.gold < cfg["cost"]:
            return False, f"Falta ouro: {cfg['name']} custa {cfg['cost']}"
        self.gold -= cfg["cost"]
        self.towers[(x, y)] = Tower(x, y, key)
        return True, f"{cfg['name']} construído"

    def upgrade(self, x, y):
        t = self.towers.get((x, y))
        if t is None:
            return False, "Nenhuma torre aqui"
        cost = t.upgrade_cost
        if cost is None:
            return False, f"{t.cfg['name']} já está no nível máximo"
        if self.gold < cost:
            return False, f"Falta ouro: melhorar custa {cost}"
        self.gold -= cost
        t.spent += cost
        t.level += 1
        t.span = None
        return True, f"{t.cfg['name']} agora é nível {t.level}"

    def sell(self, x, y):
        t = self.towers.pop((x, y), None)
        if t is None:
            return False, "Nenhuma torre aqui"
        self.gold += t.refund
        return True, f"{t.cfg['name']} vendido (+{t.refund})"

    def next_wave(self):
        if self.over:
            return False, ""
        if self.wave_active or self.enemies:
            return False, "Aguarde o fim da onda"
        self.wave += 1
        self.queue = ["normal"] * 4 if self.tutorial else make_wave(self.wave, self.rng)
        self.wave_active = True
        self.spawn_timer = 0.0
        return True, f"Onda {self.wave}!"

    # ------------------------------------------------------ tempo
    def update(self, dt):
        dt *= self.speed
        while dt > 1e-9 and not self.over:
            step = min(dt, STEP)
            self._step(step)
            dt -= step

    def _step(self, dt):
        self.time += dt
        if self.wave_active:
            self.spawn_timer -= dt
            if self.spawn_timer <= 0 and self.queue:
                scale = 0.6 if self.tutorial else 1.0
                self.enemies.append(Enemy(self.queue.pop(0), self.wave, scale))
                self.spawn_timer = SPAWN_INTERVAL
        end = len(PATH) - 1
        for e in self.enemies:
            if not e.alive:
                continue
            f = e.slow_factor if self.time < e.slow_until else 1.0
            e.progress += e.speed * f * dt
            if e.progress >= end:
                e.alive = False
                e.leaked = True
                self.life -= e.dmg
        self._fire()
        self.enemies = [e for e in self.enemies if e.alive]
        if self.effects:
            self.effects = [fx for fx in self.effects if fx[2] > self.time]
        if self.wave_active and not self.queue and not self.enemies:
            self.wave_active = False
            self.gold += 3 + self.wave
        if self.life <= 0:
            self.life = 0
            self.over = True

    def _fire(self):
        ready = [t for t in self.towers.values() if self.time - t.last >= t.rate]
        if not ready or not self.enemies:
            return
        alive = sorted((e for e in self.enemies if e.alive), key=lambda e: e.progress)
        progress = [e.progress for e in alive]
        positions = [enemy_pos(e) for e in alive]
        for t in ready:
            if t.span is None:
                t.span = tower_span(t)
            lo, hi = t.span
            r2 = t.range ** 2
            j = bisect.bisect_left(progress, hi + 1) - 1
            stop = bisect.bisect_left(progress, lo)
            while j >= stop:
                e = alive[j]
                if e.alive:
                    ex, ey = positions[j]
                    if (ex - t.x) ** 2 + (ey - t.y) ** 2 <= r2:
                        self._hit(t, e, ex, ey, alive, positions)
                        t.last = self.time
                        break
                j -= 1

    def _hit(self, t, target, tx, ty, alive, positions):
        cfg = t.cfg
        dmg = t.damage
        hits = [(target, dmg)]
        if "splash" in cfg:
            s2 = cfg["splash"] ** 2
            for e, (ex, ey) in zip(alive, positions):
                if e is not target and e.alive and (ex - tx) ** 2 + (ey - ty) ** 2 <= s2:
                    hits.append((e, dmg * 0.5))
        if "slow" in cfg:
            a2 = cfg["slow_area"] ** 2
            for e, (ex, ey) in zip(alive, positions):
                if e.alive and (ex - tx) ** 2 + (ey - ty) ** 2 <= a2:
                    e.slow_until = self.time + cfg["slow_time"]
                    e.slow_factor = max(cfg["slow"], 0.8) if e.kind == "chefe" else cfg["slow"]
        for e, d in hits:
            e.hp -= d
            e.hit_until = self.time + 0.08
            if e.hp <= 0 and e.alive:
                e.alive = False
                self.gold += e.gold
                self.kills += 1
                x, y = enemy_pos(e)
                self.effects.append((int(round(x)), int(round(y)), self.time + 0.3))


# ================================================================ tutorial

TUTORIAL_MAGE = (12, 3)
TUTORIAL_ARCHER = (4, 5)


def _tut_steps():
    return [
        {"text": ["Os monstros saem da {spawn} e seguem", "a trilha de terra até o {base}.",
                  "Não deixe nenhum chegar lá!"],
         "marks": [PATH[0], PATH[-1]], "wait": None},
        {"text": ["Escolha o Mago: toque em 3{t3}", "lá em cima (ou aperte 3)."],
         "marks": [], "wait": lambda a: a.selected == "3"},
        {"text": ["Toque na casa {mark} para levar o", "cursor até ela. Toque de novo", "para construir."],
         "marks": [TUTORIAL_MAGE], "wait": lambda a: TUTORIAL_MAGE in a.game.towers},
        {"text": ["O verde claro é o alcance do Mago.", "Chame a onda: toque na barra", "verde aqui embaixo (ou n)."],
         "marks": [], "wait": lambda a: a.game.wave >= 1},
        {"text": ["Cada monstro derrotado dá {gold}.", "Se algum chegar ao {base}, você", "perde {life}. Espere a onda acabar."],
         "marks": [], "wait": lambda a: a.game.wave >= 1 and not a.game.wave_active},
        {"text": ["Agora o Arqueiro: toque em 1{t1}", "e construa na casa {mark}."],
         "marks": [TUTORIAL_ARCHER], "wait": lambda a: TUTORIAL_ARCHER in a.game.towers,
         "setup": lambda a: setattr(a.game, "gold", max(a.game.gold, 20))},
        {"text": ["Toque 2 vezes no Mago para", "melhorar (ou cursor nele + u).", "Nível maior = mais dano e alcance."],
         "marks": [TUTORIAL_MAGE], "wait": lambda a: a.game.towers.get(TUTORIAL_MAGE) and a.game.towers[TUTORIAL_MAGE].level >= 2,
         "setup": lambda a: setattr(a.game, "gold", max(a.game.gold, 28))},
        {"text": ["Mais: x vende, f acelera {fast},", "p ou toque no topo: pausa.", "4{t4} Vórtice deixa monstros lentos."],
         "marks": [], "wait": None},
        {"text": ["Pronto {party} Agora é pra valer:", "as ondas crescem e a cada 5", "vem um chefe {boss}. Boa sorte!"],
         "marks": [], "wait": None},
    ]


# ================================================================ tela

def cell_width(ch):
    if unicodedata.combining(ch) or ch in "️‍":
        return 0
    return 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1


def text_width(s):
    return sum(cell_width(c) for c in s)


def clip(s, cells):
    out, used = [], 0
    for c in s:
        w = cell_width(c)
        if used + w > cells:
            break
        out.append(c)
        used += w
    return "".join(out)


BASIC = {  # equivalente em 8 cores para terminais sem 256 cores
    16: 0, 22: 2, 28: 2, 64: 2, 70: 2, 114: 2, 137: 3, 143: 3, 179: 3, 101: 7, 196: 1, 208: 1,
    220: 3, 226: 3, 229: 7, 231: 7, 235: 0, 236: 0, 238: 0, 240: 0, 244: 7, 250: 7, 255: 7, -1: -1,
}


class Palette:
    def __init__(self):
        self.pairs = {}
        self.ok = curses.has_colors()
        if self.ok:
            curses.start_color()
            try:
                curses.use_default_colors()
            except curses.error:
                pass
            self.full = curses.COLORS >= 256
        self.next_id = 1

    def __call__(self, fg=-1, bg=-1, bold=False):
        if not self.ok:
            return curses.A_BOLD if bold else 0
        if not self.full:
            fg, bg = BASIC.get(fg, 7), BASIC.get(bg, 0)
        key = (fg, bg)
        if key not in self.pairs:
            if self.next_id >= curses.COLOR_PAIRS:
                return curses.A_BOLD if bold else 0
            try:
                curses.init_pair(self.next_id, fg, bg)
            except curses.error:
                return 0
            self.pairs[key] = curses.color_pair(self.next_id)
            self.next_id += 1
        return self.pairs[key] | (curses.A_BOLD if bold else 0)


def put(win, y, x, text, attr=0):
    h, w = win.getmaxyx()
    if y < 0 or y >= h or x < 0 or x >= w:
        return
    text = clip(text, w - x)
    if text:
        try:
            win.addstr(y, x, text, attr)
        except curses.error:
            pass  # a ultima celula da tela gera erro, mas o texto e desenhado


MENU_ITEMS = [("play", "Jogar"), ("tutorial", "Tutorial"), ("help", "Como jogar"),
              ("options", "Opções"), ("quit", "Sair")]


class App:
    def __init__(self, scr, emoji=None, touch=None, start=None):
        self.scr = scr
        self.version = read_version()
        self.cfg = load_config()
        self.emoji = self.cfg.get("emoji", True) if emoji is None else emoji
        self.touch = self.cfg.get("toque", True) if touch is None else touch
        self.pal = None
        self.screen = "menu"
        self.menu_i = 0 if self.cfg.get("tutorial_visto") else 1  # primeira vez: Tutorial selecionado
        self.opt_i = 0
        self.help_scroll = 0
        self.game = None
        self.tut = None
        self.tut_i = 0
        self.overlay = None  # "pause" | "over"
        self.overlay_i = 0
        self.new_record = False
        self.selected = "1"
        self.cursor = [8, 5]
        self.cursor_moved = False
        self.message, self.message_until = "", 0.0
        self.hits = []
        self.done = False
        self.anim = 0.0
        self.too_small = False
        self._init_curses()
        if start == "tutorial":
            self.start_game(tutorial=True)
        elif start == "play":
            self.start_game()

    def _init_curses(self):
        curses.curs_set(0)
        self.scr.keypad(True)
        self.pal = Palette()
        self.apply_touch()

    def apply_touch(self):
        try:
            if self.touch:
                # RELEASED na mascara: um evento de soltar descartado pelo ncurses
                # deixa o getch() bloqueado ate a proxima tecla, ignorando o timeout
                curses.mousemask(curses.BUTTON1_PRESSED | curses.BUTTON1_RELEASED | curses.BUTTON1_CLICKED)
                curses.mouseinterval(0)
            else:
                curses.mousemask(0)
        except curses.error:
            pass

    def g(self, name):
        return GLYPHS[name][0 if self.emoji else 1]

    def tower_glyph(self, key):
        return TOWERS[key]["emoji"] if self.emoji else TOWERS[key]["text"] + " "

    def enemy_glyph(self, kind):
        return ENEMIES[kind]["emoji"] if self.emoji else ENEMIES[kind]["text"] + " "

    def say(self, text, secs=2.0):
        self.message, self.message_until = text, time.monotonic() + secs

    # ------------------------------------------------------ estados
    def start_game(self, tutorial=False):
        self.game = Game(tutorial=tutorial)
        self.overlay = None
        self.new_record = False
        self.selected = "1"
        self.cursor = [8, 5]
        self.cursor_moved = False
        self.message = ""
        self.screen = "game"
        self.tut = _tut_steps() if tutorial else None
        self.tut_i = 0

    def tut_step(self):
        return self.tut[self.tut_i] if self.tut and self.tut_i < len(self.tut) else None

    def tut_advance(self):
        self.tut_i += 1
        step = self.tut_step()
        if step is None:
            self.cfg["tutorial_visto"] = True
            save_config(self.cfg)
            self.start_game()
            self.say("Boa sorte! Chame a onda quando quiser", 3)
        elif "setup" in step:
            step["setup"](self)

    def check_tutorial(self):
        step = self.tut_step()
        if step and step["wait"] and step["wait"](self):
            self.tut_advance()

    def finish_game(self):
        g = self.game
        rec = self.cfg.get("recorde", {"onda": 0, "abates": 0})
        if not g.tutorial and (g.wave, g.kills) > (rec.get("onda", 0), rec.get("abates", 0)):
            self.cfg["recorde"] = {"onda": g.wave, "abates": g.kills}
            save_config(self.cfg)
            self.new_record = True
        self.overlay = "over"
        self.overlay_i = 0

    # ------------------------------------------------------ acoes no mapa
    def act_on_cursor(self):
        g = self.game
        x, y = self.cursor
        if (x, y) in g.towers:
            ok, msg = g.upgrade(x, y)
        else:
            ok, msg = g.build(x, y, self.selected)
        self.say(msg)

    def tap_cell(self, x, y):
        if [x, y] == self.cursor:
            self.act_on_cursor()
        else:
            self.cursor = [x, y]
            self.cursor_moved = True

    def move_cursor(self, k, ch):
        dx = (k == curses.KEY_RIGHT or ch in ("d", "D")) - (k == curses.KEY_LEFT or ch in ("a", "A"))
        dy = (k == curses.KEY_DOWN or ch in ("s", "S")) - (k == curses.KEY_UP or ch in ("w", "W"))
        self.cursor = [min(W - 1, max(0, self.cursor[0] + dx)), min(H - 1, max(0, self.cursor[1] + dy))]
        self.cursor_moved = True

    def open_pause(self):
        self.overlay, self.overlay_i = "pause", 0

    def call_wave(self):
        g = self.game
        if g.tutorial and self.tut_step() and self.tut_i < 3:
            self.say("Siga o tutorial primeiro")
            return
        ok, msg = g.next_wave()
        if msg:
            self.say(msg, 1.5)

    # ------------------------------------------------------ entrada
    def on_key(self, k):
        if k == curses.KEY_RESIZE:
            return
        if k == curses.KEY_MOUSE:
            self.on_mouse()
            return
        ch = chr(k) if 0 <= k < 256 else ""
        if self.too_small:
            if ch in ("q", "Q"):
                self.done = True
            return
        handler = getattr(self, "key_" + (self.overlay or self.screen))
        handler(k, ch)

    def _nav(self, k, ch, i, n):
        if k in (curses.KEY_UP,) or ch in ("w", "W", "k"):
            return (i - 1) % n
        if k in (curses.KEY_DOWN,) or ch in ("s", "S", "j"):
            return (i + 1) % n
        return i

    def key_menu(self, k, ch):
        self.menu_i = self._nav(k, ch, self.menu_i, len(MENU_ITEMS))
        if k in (10, 13, curses.KEY_ENTER) or ch == " ":
            self.menu_choose(self.menu_i)
        elif ch in ("q", "Q") or k == 27:
            self.done = True

    def menu_choose(self, i):
        action = MENU_ITEMS[i][0]
        if action == "play":
            self.start_game()
        elif action == "tutorial":
            self.start_game(tutorial=True)
        elif action == "help":
            self.screen, self.help_scroll = "help", 0
        elif action == "options":
            self.screen, self.opt_i = "options", 0
        else:
            self.done = True

    def options(self):
        rec = self.cfg.get("recorde")
        return [
            ("emoji", f"Emojis: {'SIM' if self.emoji else 'NÃO (letras)'}"),
            ("touch", f"Toque na tela: {'SIM' if self.touch else 'NÃO'}"),
            ("reset", "Zerar recorde" + (f" (onda {rec['onda']})" if rec else "")),
            ("back", "Voltar"),
        ]

    def key_options(self, k, ch):
        opts = self.options()
        self.opt_i = self._nav(k, ch, self.opt_i, len(opts))
        if k in (10, 13, curses.KEY_ENTER) or ch == " ":
            self.option_choose(self.opt_i)
        elif ch in ("q", "Q") or k in (27, curses.KEY_BACKSPACE, 127):
            self.screen = "menu"

    def option_choose(self, i):
        action = self.options()[i][0]
        if action == "emoji":
            self.emoji = not self.emoji
            self.cfg["emoji"] = self.emoji
        elif action == "touch":
            self.touch = not self.touch
            self.cfg["toque"] = self.touch
            self.apply_touch()
        elif action == "reset":
            self.cfg.pop("recorde", None)
            self.say("Recorde zerado")
        else:
            self.screen = "menu"
            return
        save_config(self.cfg)

    def key_help(self, k, ch):
        if k == curses.KEY_DOWN or ch in ("s", "j"):
            self.help_scroll += 1
        elif k == curses.KEY_UP or ch in ("w", "k"):
            self.help_scroll = max(0, self.help_scroll - 1)
        else:
            self.screen = "menu"

    def key_game(self, k, ch):
        g = self.game
        step = self.tut_step()
        if step and step["wait"] is None and (k in (10, 13, curses.KEY_ENTER) or ch == " "):
            self.tut_advance()
            return
        if ch in ("q", "Q", "p", "P") or k == 27:
            self.open_pause()
        elif ch in ("h", "H", "?"):
            self.screen, self.help_scroll = "help_game", 0
        elif ch in ("1", "2", "3", "4"):
            self.selected = ch
        elif k in (curses.KEY_UP, curses.KEY_DOWN, curses.KEY_LEFT, curses.KEY_RIGHT) or ch in "wWaAsSdD" and ch:
            self.move_cursor(k, ch)
        elif k in (10, 13, curses.KEY_ENTER) or ch == " ":
            self.act_on_cursor()
        elif ch in ("u", "U"):
            ok, msg = g.upgrade(*self.cursor)
            self.say(msg)
        elif ch in ("x", "X"):
            ok, msg = g.sell(*self.cursor)
            self.say(msg)
        elif ch in ("n", "N"):
            self.call_wave()
        elif ch in ("f", "F"):
            g.speed = 2 if g.speed == 1 else 1
            self.say(f"Velocidade {g.speed}x", 1.2)

    def key_help_game(self, k, ch):
        if k == curses.KEY_DOWN or ch in ("s", "j"):
            self.help_scroll += 1
        elif k == curses.KEY_UP or ch in ("w", "k"):
            self.help_scroll = max(0, self.help_scroll - 1)
        else:
            self.screen = "game"

    PAUSE_ITEMS = [("resume", "Continuar"), ("restart", "Reiniciar partida"), ("menu", "Menu principal")]
    OVER_ITEMS = [("restart", "Jogar de novo"), ("menu", "Menu principal")]

    def overlay_items(self):
        return self.PAUSE_ITEMS if self.overlay == "pause" else self.OVER_ITEMS

    def key_pause(self, k, ch):
        items = self.overlay_items()
        self.overlay_i = self._nav(k, ch, self.overlay_i, len(items))
        if k in (10, 13, curses.KEY_ENTER) or ch == " ":
            self.overlay_choose(self.overlay_i)
        elif ch in ("p", "P") or k == 27:
            self.overlay = None
        elif ch in ("q", "Q"):
            self.overlay_choose(len(items) - 1)

    key_over = key_pause

    def overlay_choose(self, i):
        action = self.overlay_items()[i][0]
        tutorial = self.game.tutorial if self.game else False
        if action == "resume":
            self.overlay = None
        elif action == "restart":
            self.start_game(tutorial=tutorial)
        else:
            self.overlay = None
            self.screen = "menu"
            self.game = None

    def on_mouse(self):
        try:
            _, mx, my, _, bstate = curses.getmouse()
        except curses.error:
            return
        if not bstate & (curses.BUTTON1_PRESSED | curses.BUTTON1_CLICKED):
            return
        if self.too_small:
            return
        for (y0, x0, y1, x1, action) in reversed(self.hits):
            if y0 <= my <= y1 and x0 <= mx <= x1:
                action()
                return

    # ------------------------------------------------------ desenho
    def busy(self):
        if self.message and time.monotonic() < self.message_until:
            return True
        g = self.game
        if self.screen == "game" and g and not self.overlay:
            return g.wave_active or bool(g.enemies) or bool(g.effects) or self.tut_step() is not None
        return False

    def render(self):
        scr = self.scr
        scr.erase()
        self.hits = []
        h, w = scr.getmaxyx()
        self.too_small = w < MIN_W or h < MIN_H
        if self.too_small:
            lines = ["Tela pequena demais", f"atual {w}x{h}", f"mínimo {MIN_W}x{MIN_H}",
                     "Esconda o teclado ou", "diminua a fonte (pinça)", "q sai"]
            for i, line in enumerate(lines):
                put(scr, i, 0, line, curses.A_BOLD if i == 0 else 0)
            scr.refresh()
            return
        getattr(self, "draw_" + self.screen)(h, w)
        if self.overlay:
            self.hits = []  # com a janela aberta, so os botoes dela respondem ao toque
            self.draw_overlay(h, w)
        scr.refresh()

    def center(self, y, text, attr=0, w=None):
        w = w or min(self.scr.getmaxyx()[1], MIN_W)
        x = max(0, (w - text_width(text)) // 2)
        put(self.scr, y, x, text, attr)
        return x

    def button(self, y, x, width, label, attr, action):
        put(self.scr, y, x, clip(label.center(width), width), attr)
        self.hits.append((y, x, y, x + width - 1, action))

    def draw_menu(self, h, w):
        P = self.pal
        cw = MIN_W
        title = f"{self.g('base')}  TOWER DEFENSE  {self.g('base')}"
        self.center(1, title, P(220, -1, True), cw)
        self.center(2, "edição Termux", P(244), cw)
        # faixa animada: um monstro andando pela trilha
        pos = int(self.anim * 3) % (W + 4) - 2
        for tx in range(W):
            x = 1 + tx * 2
            put(self.scr, 4, x, "· " if (tx * 7) % 6 == 0 else "  ", P(34, 28))
            put(self.scr, 5, x, "  ", P(-1, 137))
        put(self.scr, 4, 1 + 12 * 2, self.tower_glyph("3"), P(250, 28, True))
        if 0 <= pos < W:
            put(self.scr, 5, 1 + pos * 2, self.enemy_glyph("normal"), P(196, 137, True))
        seen = self.cfg.get("tutorial_visto")
        for i, (action, label) in enumerate(MENU_ITEMS):
            y = 7 + i * 2
            text = f"  {label}" + ("   (comece aqui)" if action == "tutorial" and not seen else "")
            sel = i == self.menu_i
            attr = P(16, 220, True) if sel else P(255, 236)
            self.button(y, 2, cw - 4, "", attr, lambda i=i: self.menu_choose(i))
            put(self.scr, y, 3, ("▶" if sel else " ") + text, attr)
        rec = self.cfg.get("recorde")
        rec_text = f"{self.g('trophy')} Recorde: onda {rec['onda']} · {rec['abates']} abates" if rec else "Sem recorde ainda"
        self.center(8 + len(MENU_ITEMS) * 2, rec_text, P(229), cw)
        self.center(h - 1, f"v{self.version}  ·  setas + Enter ou toque", P(244), cw)

    def help_lines(self):
        t, e = self.tower_glyph, self.enemy_glyph
        lines = [("COMO JOGAR", True),
                 (f"Monstros saem da {self.g('spawn')} e andam até", False),
                 (f"o {self.g('base')}. Construa torres na grama.", False),
                 ("", False), ("TORRES", True)]
        for k, c in TOWERS.items():
            lines.append((f"{k} {t(k)} {c['name']:<9}{c['cost']:>3} ouro", False))
            lines.append((f"     {c['info']}", False))
        lines += [("", False), ("MONSTROS", True)]
        for kind, c in ENEMIES.items():
            lines.append((f"{e(kind)} {c['name']:<8} vida {c['hp']:<4} dano {c['dmg']}", False))
        lines += [("", False), ("TOQUE", True),
                  ("casa: move · de novo: constrói", False),
                  ("torre 2x: melhora (até nível 3)", False),
                  ("barra de baixo: chama a onda", False),
                  ("topo: pausa", False),
                  ("", False), ("TECLAS", True),
                  ("setas/wasd  1-4 torre  Enter", False),
                  ("u melhora  x vende  n onda", False),
                  ("f acelera  p pausa  h ajuda", False),
                  ("", False), ("qualquer tecla volta", False)]
        return lines

    def draw_help(self, h, w):
        lines = self.help_lines()
        self.help_scroll = min(self.help_scroll, max(0, len(lines) - h + 1))
        P = self.pal
        for i, (text, strong) in enumerate(lines[self.help_scroll:self.help_scroll + h - 1]):
            put(self.scr, i, 1, text, P(220, -1, True) if strong else P(255))
        if len(lines) > h - 1:
            put(self.scr, h - 1, 1, "↑↓ rola · outra tecla volta", P(244))
        self.hits.append((0, 0, h - 1, w - 1, lambda: setattr(self, "screen", "menu" if self.screen == "help" else "game")))

    draw_help_game = draw_help

    def draw_options(self, h, w):
        P = self.pal
        self.center(1, "OPÇÕES", P(220, -1, True))
        for i, (action, label) in enumerate(self.options()):
            y = 3 + i * 2
            sel = i == self.opt_i
            attr = P(16, 220, True) if sel else P(255, 236)
            self.button(y, 2, MIN_W - 4, "", attr, lambda i=i: self.option_choose(i))
            put(self.scr, y, 3, ("▶ " if sel else "  ") + label, attr)
        put(self.scr, 12, 2, "Use NÃO em Emojis se as figuras", P(244))
        put(self.scr, 13, 2, "aparecerem desalinhadas no mapa.", P(244))
        if self.message and time.monotonic() < self.message_until:
            put(self.scr, 15, 2, self.message, P(114, -1, True))

    def draw_game(self, h, w):
        g, P = self.game, self.pal
        top, left = 3, 1
        # HUD (tocar abre a pausa)
        hud = (f" {self.g('life')}{g.life:<3} {self.g('gold')}{g.gold:<5} {self.g('wave')}{g.wave:<3}"
               f" {self.g('kills')}{g.kills}")
        if g.speed == 2:
            hud += f" {self.g('fast')}"
        put(self.scr, 0, 0, clip(hud + " " * MIN_W, MIN_W - 4) + " ||", P(255, 235, True))
        self.hits.append((0, 0, 0, MIN_W - 1, self.open_pause))
        # seletor de torres
        x = 0
        for k, c in TOWERS.items():
            label = f"{k}{self.tower_glyph(k)}{c['cost']}"
            sel = k == self.selected
            attr = P(16, 220, True) if sel else P(250, 236)
            put(self.scr, 1, x, " " + label + " ", attr)
            wlab = text_width(label) + 2
            self.hits.append((1, x, 1, x + wlab - 1, lambda k=k: setattr(self, "selected", k)))
            x += wlab + 1
        name = TOWERS[self.selected]["name"]
        if x + len(name) <= MIN_W:
            put(self.scr, 1, x, name, P(220, -1, True))
        # moldura
        border = P(101)
        put(self.scr, top - 1, 0, "╭" + "─" * (2 * W) + "╮", border)
        put(self.scr, top + H, 0, "╰" + "─" * (2 * W) + "╯", border)
        for ty in range(H):
            put(self.scr, top + ty, 0, "│", border)
            put(self.scr, top + ty, left + 2 * W, "│", border)
        self.draw_map(top, left)
        # status (toque chama a onda)
        self.draw_status(top + H + 1, h)

    def range_cells(self):
        g = self.game
        cx, cy = self.cursor
        t = g.towers.get((cx, cy))
        if t is None and not self.cursor_moved:
            return set()
        r = t.range if t else (TOWERS[self.selected]["range"] if g.can_build(cx, cy) else 0)
        if not r:
            return set()
        return {(x, y) for x in range(W) for y in range(H) if (x - cx) ** 2 + (y - cy) ** 2 <= r * r}

    def draw_map(self, top, left):
        g, P = self.game, self.pal
        now = g.time
        in_range = self.range_cells()
        cells = {}
        for (x, y), t in g.towers.items():
            # fundo mostra o nivel: 2 esverdeado, 3 dourado
            cells[(x, y)] = (self.tower_glyph(t.key), TEXT_COLORS[t.key], LEVEL_BG.get(t.level))
        cells[PATH[0]] = (self.g("spawn"), 255, None)
        cells[PATH[-1]] = (self.g("base"), 255, None)
        for e in g.enemies:
            ex, ey = enemy_pos(e)
            pos = (int(round(ex)), int(round(ey)))
            bg = None
            ratio = e.hp / e.max_hp
            if now < e.hit_until:
                bg = 231
            elif ratio < 0.35:
                bg = 196
            elif ratio < 0.7:
                bg = 208
            cells[pos] = (self.enemy_glyph(e.kind), TEXT_COLORS[e.kind], bg)
        for (x, y, _) in g.effects:
            cells[(x, y)] = (self.g("kill"), 226, None)
        step = self.tut_step()
        blink = int(time.monotonic() * 3) % 2 == 0
        marks = set(step["marks"]) if step else set()
        for y in range(H):
            for x in range(W):
                on_path = (x, y) in PATH_SET
                if on_path:
                    bg = 179 if (x, y) in in_range else 137
                else:
                    bg = 70 if (x, y) in in_range else 28
                glyph, fg, special = cells.get((x, y), ("  ", -1, None))
                if glyph == "  " and not on_path and (x * 7 + y * 13) % 6 == 0:
                    glyph, fg = "· ", (76 if (x, y) in in_range else 34)  # textura de grama
                if special is not None:
                    bg = special
                    if not self.emoji and glyph.strip() and special in (196, 208, 231):
                        fg = 16  # letra preta sobre o fundo de monstro ferido
                if (x, y) in marks and blink:
                    bg = 226
                    if glyph == "  ":
                        glyph = self.g("mark")
                if [x, y] == self.cursor:
                    bg = 226 if not self.emoji or glyph != "  " else 220
                attr = P(fg if (not self.emoji or glyph == "· ") else -1, bg, glyph != "· ")
                if not self.emoji and [x, y] == self.cursor:
                    attr = P(16, 226, True)
                sx = left + 2 * x
                put(self.scr, top + y, sx, glyph if text_width(glyph) == 2 else (glyph + " ")[:2], attr)
                self.hits.append((top + y, sx, top + y, sx + 1, lambda x=x, y=y: self.tap_cell(x, y)))

    def draw_status(self, y, h):
        g, P = self.game, self.pal
        step = self.tut_step()
        if step:
            lines = [ln.format(spawn=self.g("spawn"), base=self.g("base"), mark=self.g("mark"),
                               gold=self.g("gold"), life=self.g("life"), fast=self.g("fast"),
                               party=self.g("party"), boss=self.enemy_glyph("chefe"),
                               t1=self.tower_glyph("1"), t3=self.tower_glyph("3"), t4=self.tower_glyph("4"))
                     for ln in step["text"]]
            header = f"TUTORIAL {self.tut_i + 1}/{len(self.tut)}"
            put(self.scr, y, 0, clip(header + " " * MIN_W, MIN_W), P(16, 114, True))
            for i, ln in enumerate(lines):
                if y + 1 + i < h:
                    put(self.scr, y + 1 + i, 1, ln, P(255, -1, True))
            if step["wait"] is None and y + 1 + len(lines) < h:
                self.button(y + 1 + len(lines), 1, MIN_W - 2, "Toque aqui ou Enter para seguir ▶",
                            P(16, 220, True), self.tut_advance)
            elif self.tut_i == 3 and y + 1 + len(lines) < h:
                self.button(y + 1 + len(lines), 1, MIN_W - 2, "▶ Chamar onda", P(16, 114, True), self.call_wave)
            elif self.message and time.monotonic() < self.message_until and y + 1 + len(lines) < h:
                put(self.scr, y + 1 + len(lines), 1, self.message, P(229, -1, True))
            return
        # linha 1: acao principal / mensagem
        if self.message and time.monotonic() < self.message_until:
            put(self.scr, y, 0, clip(" " + self.message + " " * MIN_W, MIN_W), P(229, 238, True))
        elif not g.wave_active and not g.enemies and not g.over:
            self.button(y, 0, MIN_W, f"▶ Toque aqui ou n: onda {g.wave + 1}", P(16, 114, True), self.call_wave)
        else:
            left = len(g.queue) + len(g.enemies)
            put(self.scr, y, 0, clip(f" Onda {g.wave}: faltam {left}" + " " * MIN_W, MIN_W), P(250, 236))
        # linha 2: o que o cursor mostra
        if y + 1 < h:
            cx, cy = self.cursor
            t = g.towers.get((cx, cy))
            if t:
                up = t.upgrade_cost
                info = f"{self.tower_glyph(t.key)} nv{t.level} dano {t.damage:.0f} alc {t.range:.1f}"
                info += f" · u:{up}" if up else " · máx"
                info += f" x:+{t.refund}"
            elif (cx, cy) in PATH_SET:
                info = "Trilha: não dá para construir"
            else:
                c = TOWERS[self.selected]
                info = f"{self.tower_glyph(self.selected)} {c['name']} {c['cost']}: {c['info']}"
            put(self.scr, y + 1, 1, info, P(250))
        if y + 2 < h:
            put(self.scr, y + 2, 1, "u melhora x vende f acelera h ajuda", P(244))

    def draw_overlay(self, h, w):
        P = self.pal
        g = self.game
        box_w = MIN_W - 6
        x0 = 3
        if self.overlay == "pause":
            title = ["PAUSA"]
        else:
            title = [f"{self.enemy_glyph('chefe')} A BASE CAIU!", f"Onda {g.wave} · {g.kills} abates"]
            if self.new_record:
                title.append(f"{self.g('trophy')} Novo recorde!")
        items = self.overlay_items()
        height = len(title) + 2 + len(items) * 2
        y0 = max(2, 3 + (H - height) // 2)
        frame = P(220, 236, True)
        put(self.scr, y0, x0, "╭" + "─" * (box_w - 2) + "╮", frame)
        for i in range(1, height):
            put(self.scr, y0 + i, x0, "│" + " " * (box_w - 2) + "│", frame)
        put(self.scr, y0 + height, x0, "╰" + "─" * (box_w - 2) + "╯", frame)
        for i, t in enumerate(title):
            tx = x0 + max(1, (box_w - text_width(t)) // 2)
            put(self.scr, y0 + 1 + i, tx, t, P(255, 236, True))
        for i, (action, label) in enumerate(items):
            y = y0 + len(title) + 2 + i * 2
            sel = i == self.overlay_i
            attr = P(16, 220, True) if sel else P(255, 238, True)
            self.button(y, x0 + 2, box_w - 4, label, attr, lambda i=i: self.overlay_choose(i))

    # ------------------------------------------------------ laco
    def run(self):
        last = frame = time.monotonic()
        was_busy = True  # garante o primeiro desenho
        while not self.done:
            if self.screen == "menu" and not self.overlay:
                wait = 0.15  # animacao do menu devagar: poupa bateria
            elif self.busy():
                wait = 1 / FPS - (time.monotonic() - frame)
            else:
                wait = IDLE_WAIT
            self.scr.timeout(max(0, int(wait * 1000)))
            k = self.scr.getch()
            self.scr.timeout(0)
            had_input = False
            while k != -1 and not self.done:
                self.on_key(k)
                had_input = True
                k = self.scr.getch()
            if self.done:
                break
            frame = now = time.monotonic()
            dt = min(now - last, 0.25)
            last = now
            self.anim += dt
            if self.screen == "game" and self.game and not self.overlay and not self.too_small:
                self.game.update(dt)
                if self.tut:
                    self.check_tutorial()
                if self.game and self.game.over and self.overlay is None:
                    self.finish_game()
            busy = self.busy() or (self.screen == "menu" and not self.overlay)
            # parado e sem tecla: nada mudou na tela, entao nao redesenha (poupa bateria)
            if had_input or busy or was_busy:
                self.render()
            was_busy = busy


USAGE = """Tower Defense para o terminal do Termux

Uso: td [opções]
  --tutorial    começa direto no tutorial
  --jogar       começa direto uma partida
  --sem-emoji   desenha com letras (se os emojis desalinharem)
  --sem-toque   desativa o toque na tela
  --versao      mostra a versão
  --ajuda       mostra esta ajuda
"""


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    if "--versao" in args or "-v" in args:
        print(read_version())
        return 0
    if "--ajuda" in args or "-h" in args:
        print(USAGE)
        return 0
    os.environ.setdefault("ESCDELAY", "25")
    locale.setlocale(locale.LC_ALL, "")
    emoji = False if "--sem-emoji" in args else None
    touch = False if "--sem-toque" in args else None
    start = "tutorial" if "--tutorial" in args else ("play" if "--jogar" in args else None)
    curses.wrapper(lambda scr: App(scr, emoji, touch, start).run())
    return 0


if __name__ == "__main__":
    sys.exit(main())
