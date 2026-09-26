#!/usr/bin/env python3
"""Tower Defense de terminal para Termux e Linux.

Sem dependencias externas: usa apenas a biblioteca padrao (curses).
Uso: python td.py [--sem-toque] [--versao] [--ajuda]
"""
import bisect
import curses
import math
import os
import random
import sys
import time

GRID_W = 32
GRID_H = 13
MIN_W = GRID_W
MIN_H = GRID_H + 3
FPS = 30
IDLE_WAIT = 0.25

TOWER_TYPES = {
    "1": {"name": "Arqueiro", "symbol": "A", "cost": 20, "range": 4.0, "damage": 8, "rate": 0.6},
    "2": {"name": "Canhao", "symbol": "C", "cost": 50, "range": 3.0, "damage": 30, "rate": 1.6},
    "3": {"name": "Mago", "symbol": "M", "cost": 35, "range": 6.0, "damage": 14, "rate": 1.0},
}

ENEMY_BASE = {
    "normal": {"hp": 30, "speed": 2.2, "gold": 5, "symbol": "o", "dmg": 1},
    "fast": {"hp": 18, "speed": 4.0, "gold": 6, "symbol": "*", "dmg": 1},
    "tank": {"hp": 90, "speed": 1.2, "gold": 12, "symbol": "@", "dmg": 2},
}

START_GOLD = 120
START_LIFE = 20
SPAWN_INTERVAL = 0.6
HP_GROWTH = 1.18

TOWER_COLOR_KEY = {"1": "archer", "2": "cannon", "3": "mage"}
SELECTOR_WIDTH = 7
SELECTOR_GAP = 2

CONTROLS = (
    "WASD/setas mover  1-3 torre",
    "Enter constroi  x vende  n onda",
    "p pausa  h ajuda  q sai",
)

HELP_LINES = (
    "Mover: setas ou w a s d",
    "Torre: 1 Arqueiro 2 Canhao 3 Mago",
    "Construir: Enter ou Espaco",
    "Toque: move; 2o toque constroi",
    "x vende (devolve metade)",
    "n ou toque no rodape: onda",
    "p pausa   r reinicia (fim)",
    "q sai (q de novo confirma)",
    "",
    "Inimigos: o normal  * rapido",
    "  @ tanque: tira 2 de vida",
    "Proteja a base B!",
)

def read_version():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "VERSION")
    try:
        with open(path, encoding="utf-8") as f:
            return f.read().strip() or "dev"
    except OSError:
        return "dev"


# ---------------------------------------------------------------- logica

def build_path():
    segs = [
        (0, 2, 8, 2),
        (8, 2, 8, 5),
        (8, 5, 20, 5),
        (20, 5, 20, 2),
        (20, 2, 28, 2),
        (28, 2, 28, 8),
        (28, 8, 14, 8),
        (14, 8, 14, 11),
        (14, 11, 30, 11),
    ]
    pts = []
    for i, (x0, y0, x1, y1) in enumerate(segs):
        if x0 == x1:
            step = 1 if y1 >= y0 else -1
            line = [(x0, y) for y in range(y0, y1 + step, step)]
        else:
            step = 1 if x1 >= x0 else -1
            line = [(x, y0) for x in range(x0, x1 + step, step)]
        if i > 0:
            line = line[1:]
        pts.extend(line)
    return pts


class Enemy:
    def __init__(self, kind, wave_num):
        base = ENEMY_BASE[kind]
        scale = HP_GROWTH ** (wave_num - 1)
        self.kind = kind
        self.max_hp = base["hp"] * scale
        self.hp = self.max_hp
        self.speed = base["speed"]
        self.gold = int(base["gold"] * (1 + 0.08 * (wave_num - 1)))
        self.dmg = base["dmg"]
        self.symbol = base["symbol"]
        self.progress = 0.0
        self.alive = True
        self.reached_base = False


class Tower:
    def __init__(self, x, y, type_key):
        self.x = x
        self.y = y
        self.type_key = type_key
        self.last_shot = -999.0
        self.span = None


def enemy_pos(enemy, path):
    i = int(enemy.progress)
    if i >= len(path) - 1:
        return path[-1]
    frac = enemy.progress - i
    x0, y0 = path[i]
    x1, y1 = path[i + 1]
    return (x0 + (x1 - x0) * frac, y0 + (y1 - y0) * frac)


def tower_span(tower, path):
    # um inimigo entre path[i] e path[i+1] esta a no maximo 1 celula de path[i]
    reach = TOWER_TYPES[tower.type_key]["range"] + 1
    idx = [i for i, (x, y) in enumerate(path) if math.hypot(x - tower.x, y - tower.y) <= reach]
    return (idx[0], idx[-1]) if idx else (0, -1)


def make_wave(wave_num):
    count = 5 + wave_num * 2
    kinds = []
    for _ in range(count):
        roll = random.random()
        if roll < 0.15 and wave_num > 2:
            kinds.append("tank")
        elif roll < 0.35:
            kinds.append("fast")
        else:
            kinds.append("normal")
    return kinds


def update_enemies(enemies, path, dt, state):
    for e in enemies:
        if not e.alive:
            continue
        e.progress += e.speed * dt
        if e.progress >= len(path) - 1:
            e.alive = False
            e.reached_base = True
            state["base_hp"] -= e.dmg


def update_towers(towers, enemies, path, now, state):
    ready = [t for t in towers if now - t.last_shot >= TOWER_TYPES[t.type_key]["rate"]]
    if not ready or not enemies:
        return
    alive = sorted((e for e in enemies if e.alive), key=lambda e: e.progress)
    progress = [e.progress for e in alive]
    positions = [enemy_pos(e, path) for e in alive]
    for t in ready:
        if t.span is None:
            t.span = tower_span(t, path)
        lo, hi = t.span
        cfg = TOWER_TYPES[t.type_key]
        r2 = cfg["range"] ** 2
        # do inimigo mais adiantado para tras, apenas na faixa do caminho que a torre alcanca
        j = bisect.bisect_left(progress, hi + 1) - 1
        stop = bisect.bisect_left(progress, lo)
        while j >= stop:
            e = alive[j]
            if e.alive:
                ex, ey = positions[j]
                if (ex - t.x) ** 2 + (ey - t.y) ** 2 <= r2:
                    e.hp -= cfg["damage"]
                    t.last_shot = now
                    if e.hp <= 0:
                        e.alive = False
                        state["gold"] += e.gold
                        state["kills"] += 1
                    break
            j -= 1


def try_place_tower(cursor, towers, path_set, state, selected):
    x, y = cursor
    if (x, y) in path_set:
        return "Nao pode construir no caminho!"
    for t in towers:
        if t.x == x and t.y == y:
            return "Ja existe uma torre aqui!"
    cfg = TOWER_TYPES[selected]
    if state["gold"] < cfg["cost"]:
        return f"Ouro insuficiente (${cfg['cost']})"
    state["gold"] -= cfg["cost"]
    towers.append(Tower(x, y, selected))
    return f"{cfg['name']} construida!"


def try_sell_tower(cursor, towers, state):
    x, y = cursor
    for i, t in enumerate(towers):
        if t.x == x and t.y == y:
            refund = TOWER_TYPES[t.type_key]["cost"] // 2
            state["gold"] += refund
            towers.pop(i)
            return f"Torre vendida (+{refund} ouro)"
    return "Nenhuma torre aqui."


def new_game():
    return {
        "state": {"gold": START_GOLD, "base_hp": START_LIFE, "wave": 0, "kills": 0},
        "towers": [],
        "enemies": [],
        "wave_queue": [],
        "spawn_timer": 0.0,
        "wave_active": False,
        "game_over": False,
    }


# ------------------------------------------------------------- interface

def init_colors():
    if not curses.has_colors():
        return {}
    curses.start_color()
    try:
        curses.use_default_colors()
        bg = -1
    except curses.error:
        bg = curses.COLOR_BLACK
    pairs = {
        "grass": (curses.COLOR_GREEN, bg),
        "path": (curses.COLOR_WHITE, bg),
        "archer": (curses.COLOR_CYAN, bg),
        "cannon": (curses.COLOR_YELLOW, bg),
        "mage": (curses.COLOR_MAGENTA, bg),
        "normal": (curses.COLOR_RED, bg),
        "fast": (curses.COLOR_YELLOW, bg),
        "tank": (curses.COLOR_RED, bg),
        "base": (curses.COLOR_BLUE, bg),
        "spawn": (curses.COLOR_GREEN, bg),
        "status": (curses.COLOR_WHITE, bg),
    }
    attrs = {}
    for idx, (name, (fg, bgc)) in enumerate(pairs.items(), start=1):
        try:
            curses.init_pair(idx, fg, bgc)
            attrs[name] = curses.color_pair(idx)
        except curses.error:
            attrs[name] = 0
    return attrs


def safe_addstr(win, y, x, text, attr=0):
    max_y, max_x = win.getmaxyx()
    if y < 0 or y >= max_y or x < 0 or x >= max_x:
        return
    text = text[: max_x - x]
    if not text:
        return
    try:
        win.addstr(y, x, text, attr)
    except curses.error:
        # escrever na ultima celula da tela gera erro, mas o texto e desenhado
        pass


def screen_too_small(stdscr):
    max_y, max_x = stdscr.getmaxyx()
    return max_x < MIN_W or max_y < MIN_H


def compute_layout(height):
    top = 3 if height > MIN_H else 2
    status = top + GRID_H
    controls = status + 2 if height >= status + 2 + len(CONTROLS) else None
    return {"top": top, "status": status, "controls": controls}


def hud_text(state, width):
    hp, gold, wave, kills = max(0, state["base_hp"]), state["gold"], state["wave"], state["kills"]
    full = f" Vida {hp} Ouro {gold} Onda {wave} Abates {kills}"
    if len(full) <= width:
        return full
    return f" Vida {hp} ${gold} Onda {wave} Abt {kills}"


def draw_too_small(stdscr):
    stdscr.erase()
    max_y, max_x = stdscr.getmaxyx()
    lines = (
        "Tela pequena demais",
        f"atual {max_x}x{max_y}",
        f"minimo {MIN_W}x{MIN_H}",
        "Esconda o teclado ou",
        "diminua a fonte (pinca)",
        "q sai",
    )
    for i, line in enumerate(lines):
        safe_addstr(stdscr, i, 0, line, curses.A_BOLD if i == 0 else 0)
    stdscr.refresh()


def enable_mouse():
    try:
        avail, _ = curses.mousemask(curses.BUTTON1_PRESSED | curses.BUTTON1_CLICKED)
        curses.mouseinterval(0)
        return bool(avail)
    except curses.error:
        return False


class Jogo:
    def __init__(self, stdscr, touch=True):
        self.scr = stdscr
        self.colors = init_colors()
        self.path = build_path()
        self.path_set = set(self.path)
        self.touch = touch and enable_mouse()
        self.version = read_version()
        self.selected = "1"
        self.cursor = [GRID_W // 2, GRID_H // 2]
        while tuple(self.cursor) in self.path_set:
            self.cursor[0] += 1
        self.help = False
        self.quit_confirm = False
        self.too_small = False
        self.done = False
        self.message = ""
        self.message_timer = 0.0
        self.layout = compute_layout(self.scr.getmaxyx()[0])
        self.background = self._build_background()
        self.reset()

    def reset(self):
        self.game = new_game()
        self.paused = False
        self.clock = 0.0

    def _build_background(self):
        g, c = self.colors, curses
        grid = [[(".", g.get("grass", 0)) for _ in range(GRID_W)] for _ in range(GRID_H)]
        for (x, y) in self.path:
            grid[y][x] = ("#", g.get("path", 0))
        sx, sy = self.path[0]
        bx, by = self.path[-1]
        grid[sy][sx] = ("S", g.get("spawn", 0) | c.A_BOLD)
        grid[by][bx] = ("B", g.get("base", 0) | c.A_BOLD)
        return grid

    # ----------------------------------------------------------- acoes

    def say(self, text):
        self.message = text
        self.message_timer = 1.5

    def running(self):
        return not (self.paused or self.quit_confirm or self.help or self.too_small or self.game["game_over"])

    def busy(self):
        moving = self.game["wave_active"] or self.game["enemies"]
        return (self.running() and moving) or self.message_timer > 0

    def build(self):
        if self.game["game_over"]:
            return
        if self.paused:
            return
        self.say(try_place_tower(self.cursor, self.game["towers"], self.path_set, self.game["state"], self.selected))

    def sell(self):
        if self.game["game_over"]:
            return
        if self.paused:
            return
        self.say(try_sell_tower(self.cursor, self.game["towers"], self.game["state"]))

    def next_wave(self):
        g = self.game
        if g["game_over"]:
            return
        if self.paused:
            return
        if g["wave_active"] or g["enemies"]:
            self.say("Aguarde o fim da onda")
            return
        g["state"]["wave"] += 1
        g["wave_queue"] = make_wave(g["state"]["wave"])
        g["wave_active"] = True
        g["spawn_timer"] = 0.0

    def restart(self):
        self.reset()
        self.say("Nova partida!")

    def request_quit(self):
        if self.game["game_over"] or self.game["state"]["wave"] == 0:
            self.done = True
        else:
            self.quit_confirm = True

    # ---------------------------------------------------------- entrada

    def key(self, k):
        if k == curses.KEY_RESIZE:
            return
        if k == curses.KEY_MOUSE:
            self.mouse()
            return
        ch = chr(k) if 0 <= k < 256 else ""
        is_quit = ch in ("q", "Q") or k == 27

        if self.quit_confirm:
            # qualquer tecla que nao seja q/Esc cancela: evita sair ao apertar "s" para descer
            self.done = is_quit
            self.quit_confirm = False
            return
        if self.too_small:
            self.done = is_quit
            return
        if self.help:
            self.help = False
            return
        if is_quit:
            self.request_quit()
        elif ch in ("h", "H", "?"):
            self.help = True
        elif ch in ("r", "R") and self.game["game_over"]:
            self.restart()
        elif ch in ("1", "2", "3"):
            self.selected = ch
        elif ch in ("p", "P"):
            if not self.game["game_over"]:
                self.paused = not self.paused
        elif k in (curses.KEY_UP, ord("w"), ord("W")):
            self.cursor[1] = max(0, self.cursor[1] - 1)
        elif k in (curses.KEY_DOWN, ord("s"), ord("S")):
            self.cursor[1] = min(GRID_H - 1, self.cursor[1] + 1)
        elif k in (curses.KEY_LEFT, ord("a"), ord("A")):
            self.cursor[0] = max(0, self.cursor[0] - 1)
        elif k in (curses.KEY_RIGHT, ord("d"), ord("D")):
            self.cursor[0] = min(GRID_W - 1, self.cursor[0] + 1)
        elif k in (10, 13, curses.KEY_ENTER, ord(" ")):
            self.build()
        elif ch in ("x", "X"):
            self.sell()
        elif ch in ("n", "N"):
            self.next_wave()

    def mouse(self):
        try:
            _, mx, my, _, bstate = curses.getmouse()
        except curses.error:
            return
        if not bstate & (curses.BUTTON1_PRESSED | curses.BUTTON1_CLICKED):
            return
        if self.quit_confirm:
            self.quit_confirm = False
            return
        if self.too_small:
            return
        if self.help:
            self.help = False
            return
        top = self.layout["top"]
        if top <= my < top + GRID_H and 0 <= mx < GRID_W:
            cell = [mx, my - top]
            if cell == self.cursor:
                self.build()
            else:
                self.cursor = cell
        elif my == 1:
            slot = mx // (SELECTOR_WIDTH + SELECTOR_GAP)
            if slot < 3 and mx % (SELECTOR_WIDTH + SELECTOR_GAP) < SELECTOR_WIDTH:
                self.selected = "123"[slot]
        elif my == self.layout["status"]:
            if self.game["game_over"]:
                self.restart()
            else:
                self.next_wave()

    # ------------------------------------------------------------ tempo

    def tick(self, dt):
        g = self.game
        state = g["state"]
        if self.running():
            self.clock += dt
            if g["wave_active"]:
                g["spawn_timer"] -= dt
                if g["spawn_timer"] <= 0 and g["wave_queue"]:
                    g["enemies"].append(Enemy(g["wave_queue"].pop(0), state["wave"]))
                    g["spawn_timer"] = SPAWN_INTERVAL
            update_enemies(g["enemies"], self.path, dt, state)
            update_towers(g["towers"], g["enemies"], self.path, self.clock, state)
            g["enemies"] = [e for e in g["enemies"] if e.alive]
            if g["wave_active"] and not g["wave_queue"] and not g["enemies"]:
                g["wave_active"] = False
            if state["base_hp"] <= 0:
                g["game_over"] = True
        if self.message_timer > 0:
            self.message_timer -= dt
            if self.message_timer <= 0:
                self.message = ""

    # ----------------------------------------------------------- desenho

    def status_line(self):
        g, state = self.game, self.game["state"]
        strong = curses.A_BOLD | curses.A_REVERSE
        if self.quit_confirm:
            return "Sair? q = sim, outra tecla = nao", strong
        if g["game_over"]:
            return f"Base caiu na onda {state['wave']}! r=reinicia", strong
        if self.paused:
            return "PAUSADO - p continua", strong
        if self.message:
            return self.message, curses.A_BOLD
        if not g["wave_active"] and not g["enemies"]:
            return "n ou toque aqui: proxima onda", 0
        return "", 0

    def render(self):
        scr = self.scr
        if self.too_small:
            draw_too_small(scr)
            return
        height, width = scr.getmaxyx()
        self.layout = lay = compute_layout(height)
        scr.erase()
        c = self.colors

        safe_addstr(scr, 0, 0, hud_text(self.game["state"], width).ljust(min(width, 40)),
                    c.get("status", 0) | curses.A_REVERSE)

        col = 0
        for k in ("1", "2", "3"):
            cfg = TOWER_TYPES[k]
            label = f"{k}:{cfg['symbol']} ${cfg['cost']}".ljust(SELECTOR_WIDTH)
            attr = c.get(TOWER_COLOR_KEY[k], 0)
            if k == self.selected:
                attr |= curses.A_REVERSE | curses.A_BOLD
            safe_addstr(scr, 1, col, label, attr)
            col += SELECTOR_WIDTH + SELECTOR_GAP
        name = TOWER_TYPES[self.selected]["name"]
        if col + len(name) <= width:
            safe_addstr(scr, 1, col, name, curses.A_BOLD)

        if self.help:
            self._draw_help(lay["top"])
        else:
            self._draw_grid(lay["top"])

        text, attr = self.status_line()
        safe_addstr(scr, lay["status"], 0, text, attr)
        if lay["controls"] is not None:
            for i, line in enumerate(CONTROLS):
                safe_addstr(scr, lay["controls"] + i, 0, line)
        scr.refresh()

    def _draw_grid(self, top):
        c = self.colors
        cells = [row[:] for row in self.background]
        for t in self.game["towers"]:
            cells[t.y][t.x] = (TOWER_TYPES[t.type_key]["symbol"],
                               c.get(TOWER_COLOR_KEY[t.type_key], 0) | curses.A_BOLD)
        for e in self.game["enemies"]:
            if e.alive:
                ex, ey = enemy_pos(e, self.path)
                ix = max(0, min(GRID_W - 1, int(round(ex))))
                iy = max(0, min(GRID_H - 1, int(round(ey))))
                cells[iy][ix] = (e.symbol, c.get(e.kind, 0) | curses.A_BOLD)
        cx, cy = self.cursor
        ch, a = cells[cy][cx]
        cells[cy][cx] = (ch, a | curses.A_REVERSE)

        # agrupa celulas vizinhas com o mesmo atributo: menos chamadas ao curses por quadro
        for y, row in enumerate(cells):
            start, run, run_attr = 0, [], row[0][1]
            for x, (ch, a) in enumerate(row):
                if a != run_attr:
                    safe_addstr(self.scr, top + y, start, "".join(run), run_attr)
                    start, run, run_attr = x, [], a
                run.append(ch)
            safe_addstr(self.scr, top + y, start, "".join(run), run_attr)

    def _draw_help(self, top):
        safe_addstr(self.scr, top, 0, f"AJUDA  Tower Defense v{self.version}", curses.A_BOLD | curses.A_REVERSE)
        for i, line in enumerate(HELP_LINES[: GRID_H - 1]):
            safe_addstr(self.scr, top + 1 + i, 0, line)

    # ------------------------------------------------------------- laco

    def run(self):
        curses.curs_set(0)
        self.scr.keypad(True)
        last = frame_start = time.monotonic()
        while not self.done:
            self.too_small = screen_too_small(self.scr)
            if self.busy():
                wait = 1 / FPS - (time.monotonic() - frame_start)
            else:
                # parado: dorme ate chegar uma tecla, sem redesenhar 30x por segundo
                wait = IDLE_WAIT
            self.scr.timeout(max(0, int(wait * 1000)))
            k = self.scr.getch()
            self.scr.timeout(0)
            # le todas as teclas acumuladas: segurar uma tecla nao cria fila atrasada
            while k != -1 and not self.done:
                self.key(k)
                k = self.scr.getch()
            if self.done:
                break
            frame_start = now = time.monotonic()
            dt = min(now - last, 0.25)
            last = now
            self.too_small = screen_too_small(self.scr)
            self.tick(dt)
            self.render()


def play(stdscr, touch=True):
    Jogo(stdscr, touch).run()


USAGE = """Tower Defense de terminal

Uso: td [opcoes]
  --sem-toque   desativa o toque na tela (use se o Termux nao abrir o teclado)
  --versao      mostra a versao
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
    # sem isso o curses espera ~1 s apos Esc para distinguir de teclas especiais
    os.environ.setdefault("ESCDELAY", "25")
    touch = "--sem-toque" not in args
    curses.wrapper(play, touch)
    return 0


if __name__ == "__main__":
    sys.exit(main())
