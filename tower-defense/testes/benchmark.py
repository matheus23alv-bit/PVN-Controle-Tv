"""Mede o custo por quadro da lógica e do desenho do Tower Defense 3 em fim de jogo.

Precisa de um terminal real (usa curses); o resultado sai no stderr. Uso:
  python3 testes/benchmark.py [caminho/td.py] [torres] [inimigos] 2> resultado.txt
"""
import curses
import importlib.util
import locale
import os
import random
import sys
import time

here = os.path.dirname(os.path.abspath(__file__))
TD_PATH = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "..", "source", "td.py")
N_TOWERS = int(sys.argv[2]) if len(sys.argv) > 2 else 60
N_ENEMIES = int(sys.argv[3]) if len(sys.argv) > 3 else 60
FRAMES = 300

spec = importlib.util.spec_from_file_location("td", TD_PATH)
td = importlib.util.module_from_spec(spec)
spec.loader.exec_module(td)


def scenario():
    rnd = random.Random(7)
    g = td.Game(seed=7)
    free = g.mapa.find(".")
    for x, y in rnd.sample(free, min(N_TOWERS, len(free))):
        t = td.Tower(x, y, rnd.choice("1234"))
        t.level = rnd.randint(1, 3)
        g.towers[(x, y)] = t
    for _ in range(N_ENEMIES):
        e = td.Enemy(rnd.choice(list(td.ENEMIES)), 30, rng=rnd)
        e.hp = e.max_hp = 1e12
        e.progress = rnd.uniform(0, len(g.path) - 2)
        e.speed = 0
        g.enemies.append(e)
    g.wave, g.wave_active = 30, True
    return g


def fire_frame(g):
    for t in g.towers.values():
        t.last = -999.0  # pior caso: todas as torres prontas para atirar em todo quadro
    g._fire()
    g.time += 0.05
    g.effects = [f for f in g.effects if f.t1 > g.time]


def bench(scr):
    g = scenario()
    g.visual = False
    t0 = time.perf_counter()
    for _ in range(FRAMES):
        fire_frame(g)
    logic = (time.perf_counter() - t0) / FRAMES * 1000

    app = td.App(scr, emoji=True, touch=False, start="play")
    app.game = scenario()
    app.cursor, app.cursor_moved = [5, 9], True
    t0 = time.perf_counter()
    for _ in range(FRAMES):
        fire_frame(app.game)  # com tiros, explosões, números de dano e abates na tela
        app.render()
    total = (time.perf_counter() - t0) / FRAMES * 1000
    return logic, total - logic, len(app.game.effects)


if __name__ == "__main__":
    os.environ.setdefault("ESCDELAY", "25")
    locale.setlocale(locale.LC_ALL, "")
    logic, draw, fx = curses.wrapper(bench)
    out = sys.stderr  # o stdout pertence ao curses e precisa ser um terminal
    print(f"{os.path.basename(TD_PATH)}  torres={N_TOWERS} inimigos={N_ENEMIES} efeitos na tela={fx}", file=out)
    print(f"  lógica (todas as torres atirando): {logic:6.2f} ms/quadro", file=out)
    print(f"  efeitos + desenho, 256 cores:      {draw:6.2f} ms/quadro", file=out)
    print(f"  total: {logic + draw:6.2f} ms/quadro (orçamento a 20 quadros/s: 50 ms)", file=out)
