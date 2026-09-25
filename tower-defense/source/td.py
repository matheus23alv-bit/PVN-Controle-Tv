#!/usr/bin/env python3
"""Tower Defense de terminal - roda em qualquer Linux/Termux com Python 3.

Sem dependencias externas: usa apenas a biblioteca padrao (curses).
"""
import curses
import math
import os
import random
import time

GRID_W = 32
GRID_H = 13

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
GRID_TOP = 3
MIN_W = 36
MIN_H = GRID_TOP + GRID_H + 5


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


def enemy_pos(enemy, path):
    i = int(enemy.progress)
    if i >= len(path) - 1:
        return path[-1]
    frac = enemy.progress - i
    x0, y0 = path[i]
    x1, y1 = path[i + 1]
    return (x0 + (x1 - x0) * frac, y0 + (y1 - y0) * frac)


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
    for t in towers:
        cfg = TOWER_TYPES[t.type_key]
        if now - t.last_shot < cfg["rate"]:
            continue
        target = None
        best_progress = -1.0
        for e in enemies:
            if not e.alive:
                continue
            ex, ey = enemy_pos(e, path)
            dist = math.hypot(ex - t.x, ey - t.y)
            if dist <= cfg["range"] and e.progress > best_progress:
                target = e
                best_progress = e.progress
        if target is not None:
            target.hp -= cfg["damage"]
            t.last_shot = now
            if target.hp <= 0:
                target.alive = False
                state["gold"] += target.gold
                state["kills"] += 1


def try_place_tower(cursor, towers, path_set, state, selected):
    x, y = cursor
    if (x, y) in path_set:
        return "Nao pode construir no caminho!"
    for t in towers:
        if t.x == x and t.y == y:
            return "Ja existe uma torre aqui!"
    cfg = TOWER_TYPES[selected]
    if state["gold"] < cfg["cost"]:
        return "Ouro insuficiente!"
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


TOWER_COLOR_KEY = {"1": "archer", "2": "cannon", "3": "mage"}

CONTROLS = (
    "WASD/setas mover  1-3 torre",
    "Enter constroi  x vende  n onda",
    "p pausa  q sai",
)


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
        # escrever na última célula da tela move o cursor para fora e gera erro, mas o texto é desenhado
        pass


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


def screen_too_small(stdscr):
    max_y, max_x = stdscr.getmaxyx()
    return max_x < MIN_W or max_y < MIN_H


def draw_too_small(stdscr):
    stdscr.erase()
    max_y, max_x = stdscr.getmaxyx()
    lines = [
        "Tela pequena demais",
        f"atual {max_x}x{max_y}",
        f"minimo {MIN_W}x{MIN_H}",
        "Diminua a fonte",
        "(gesto de pinca)",
        "q sai",
    ]
    for i, line in enumerate(lines):
        safe_addstr(stdscr, i, 0, line, curses.A_BOLD if i == 0 else 0)
    stdscr.refresh()


def draw(stdscr, path, path_set, game, cursor, selected, message, paused, confirm_quit, colors):
    stdscr.erase()
    state = game["state"]
    spawn, base = path[0], path[-1]

    grid = [["." for _ in range(GRID_W)] for _ in range(GRID_H)]
    attrs = [[colors.get("grass", 0) for _ in range(GRID_W)] for _ in range(GRID_H)]

    for (x, y) in path_set:
        grid[y][x] = "#"
        attrs[y][x] = colors.get("path", 0)

    sx, sy = spawn
    grid[sy][sx] = "S"
    attrs[sy][sx] = colors.get("spawn", 0) | curses.A_BOLD
    bx, by = base
    grid[by][bx] = "B"
    attrs[by][bx] = colors.get("base", 0) | curses.A_BOLD

    for t in game["towers"]:
        grid[t.y][t.x] = TOWER_TYPES[t.type_key]["symbol"]
        attrs[t.y][t.x] = colors.get(TOWER_COLOR_KEY[t.type_key], 0) | curses.A_BOLD

    for e in game["enemies"]:
        if not e.alive:
            continue
        ex, ey = enemy_pos(e, path)
        ix = max(0, min(GRID_W - 1, int(round(ex))))
        iy = max(0, min(GRID_H - 1, int(round(ey))))
        grid[iy][ix] = e.symbol
        attrs[iy][ix] = colors.get(e.kind, 0) | curses.A_BOLD

    hud = f" Vida {max(0, state['base_hp'])} Ouro {state['gold']} Onda {state['wave']} Abates {state['kills']}"
    safe_addstr(stdscr, 0, 0, hud.ljust(MIN_W), colors.get("status", 0) | curses.A_REVERSE)

    col = 0
    for k in ("1", "2", "3"):
        c = TOWER_TYPES[k]
        label = f"{k}:{c['symbol']} ${c['cost']}"
        attr = colors.get(TOWER_COLOR_KEY[k], 0)
        if k == selected:
            attr |= curses.A_REVERSE | curses.A_BOLD
        safe_addstr(stdscr, 1, col, label, attr)
        col += len(label) + 2
    safe_addstr(stdscr, 1, col, TOWER_TYPES[selected]["name"], curses.A_BOLD)

    for y in range(GRID_H):
        for x in range(GRID_W):
            a = attrs[y][x]
            if cursor[0] == x and cursor[1] == y:
                a |= curses.A_REVERSE
            safe_addstr(stdscr, GRID_TOP + y, x, grid[y][x], a)

    row = GRID_TOP + GRID_H
    status = ""
    status_attr = curses.A_BOLD | curses.A_REVERSE
    if confirm_quit:
        status = "Sair do jogo? s = sim, n = nao"
    elif game["game_over"]:
        status = f"BASE DESTRUIDA na onda {state['wave']}! r reinicia, q sai"
    elif paused:
        status = "== PAUSADO == (p continua)"
    elif message:
        status, status_attr = message, curses.A_BOLD
    elif not game["wave_active"]:
        status, status_attr = "Pressione n para a proxima onda", 0
    safe_addstr(stdscr, row, 0, status, status_attr)

    for i, line in enumerate(CONTROLS):
        safe_addstr(stdscr, row + 2 + i, 0, line)

    stdscr.refresh()


def main(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.keypad(True)
    colors = init_colors()

    path = build_path()
    path_set = set(path)

    game = new_game()
    cursor = [GRID_W // 2, GRID_H // 2]
    while tuple(cursor) in path_set:
        cursor[0] += 1

    selected = "1"
    paused = False
    confirm_quit = False
    message = ""
    message_timer = 0.0
    last_time = time.time()

    while True:
        now = time.time()
        dt = min(now - last_time, 0.25)
        last_time = now
        too_small = screen_too_small(stdscr)

        key = stdscr.getch()
        ch = chr(key) if 0 <= key < 256 else ""
        state = game["state"]

        if key == -1 or key == curses.KEY_RESIZE:
            pass
        elif confirm_quit:
            if ch in ("s", "S", "y", "Y"):
                break
            if ch in ("n", "N") or key == 27:
                confirm_quit = False
        elif too_small:
            if ch in ("q", "Q"):
                break
        elif ch in ("q", "Q") or key == 27:
            if game["game_over"] or state["wave"] == 0:
                break
            confirm_quit = True
        elif ch in ("r", "R") and game["game_over"]:
            game = new_game()
            paused = False
            message = "Nova partida!"
            message_timer = 1.5
        elif ch in ("1", "2", "3"):
            selected = ch
        elif ch in ("p", "P"):
            if not game["game_over"]:
                paused = not paused
        elif key in (curses.KEY_UP, ord("w"), ord("W")):
            cursor[1] = max(0, cursor[1] - 1)
        elif key in (curses.KEY_DOWN, ord("s"), ord("S")):
            cursor[1] = min(GRID_H - 1, cursor[1] + 1)
        elif key in (curses.KEY_LEFT, ord("a"), ord("A")):
            cursor[0] = max(0, cursor[0] - 1)
        elif key in (curses.KEY_RIGHT, ord("d"), ord("D")):
            cursor[0] = min(GRID_W - 1, cursor[0] + 1)
        elif key in (10, 13, curses.KEY_ENTER, ord(" ")):
            if not game["game_over"] and not paused:
                message = try_place_tower(cursor, game["towers"], path_set, state, selected)
                message_timer = 1.5
        elif ch in ("x", "X"):
            if not game["game_over"] and not paused:
                message = try_sell_tower(cursor, game["towers"], state)
                message_timer = 1.5
        elif ch in ("n", "N"):
            if not game["wave_active"] and not game["enemies"] and not game["game_over"] and not paused:
                state["wave"] += 1
                game["wave_queue"] = make_wave(state["wave"])
                game["wave_active"] = True
                game["spawn_timer"] = 0.0

        state = game["state"]
        running = not (paused or confirm_quit or too_small or game["game_over"])
        if running:
            if game["wave_active"]:
                game["spawn_timer"] -= dt
                if game["spawn_timer"] <= 0 and game["wave_queue"]:
                    game["enemies"].append(Enemy(game["wave_queue"].pop(0), state["wave"]))
                    game["spawn_timer"] = SPAWN_INTERVAL

            update_enemies(game["enemies"], path, dt, state)
            update_towers(game["towers"], game["enemies"], path, now, state)
            game["enemies"] = [e for e in game["enemies"] if e.alive]

            if game["wave_active"] and not game["wave_queue"] and not game["enemies"]:
                game["wave_active"] = False

            if state["base_hp"] <= 0:
                game["game_over"] = True

        if message_timer > 0:
            message_timer -= dt
            if message_timer <= 0:
                message = ""

        if too_small:
            draw_too_small(stdscr)
        else:
            draw(stdscr, path, path_set, game, cursor, selected, message, paused, confirm_quit, colors)

        time.sleep(0.03)


if __name__ == "__main__":
    # sem isso o curses espera ~1s após Esc para distinguir de sequências de teclas especiais
    os.environ.setdefault("ESCDELAY", "25")
    curses.wrapper(main)
