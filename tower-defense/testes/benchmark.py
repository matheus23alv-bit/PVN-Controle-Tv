"""Mede o custo por quadro da lógica e do desenho em cenário de fim de jogo.

Precisa de um terminal real (usa curses); o resultado sai no stderr. Uso:
  python3 testes/benchmark.py [caminho/td.py] [torres] [inimigos] 2> resultado.txt
"""
import curses
import importlib.util
import os
import random
import sys
import time

here = os.path.dirname(os.path.abspath(__file__))
TD_PATH = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "..", "source", "td.py")
N_TOWERS = int(sys.argv[2]) if len(sys.argv) > 2 else 150
N_ENEMIES = int(sys.argv[3]) if len(sys.argv) > 3 else 70
FRAMES = 300

spec = importlib.util.spec_from_file_location("td", TD_PATH)
td = importlib.util.module_from_spec(spec)
spec.loader.exec_module(td)


def scenario():
    random.seed(7)
    path = td.build_path()
    path_set = set(path)
    game = td.new_game()
    free = [(x, y) for x in range(td.GRID_W) for y in range(td.GRID_H) if (x, y) not in path_set]
    random.shuffle(free)
    for i, (x, y) in enumerate(free[:N_TOWERS]):
        game["towers"].append(td.Tower(x, y, "123"[i % 3]))
    for i in range(N_ENEMIES):
        e = td.Enemy(random.choice(["normal", "fast", "tank"]), 30)
        e.hp = e.max_hp = 1e12
        e.progress = random.uniform(0, len(path) - 2)
        game["enemies"].append(e)
    game["wave_active"] = True
    game["state"]["wave"] = 30
    return path, path_set, game


def bench(stdscr):
    stdscr.nodelay(True)
    path, path_set, game = scenario()

    t0 = time.perf_counter()
    for f in range(FRAMES):
        td.update_towers(game["towers"], game["enemies"], path, f * 0.033, game["state"])
    t_logic = (time.perf_counter() - t0) / FRAMES * 1000

    if hasattr(td, "Jogo"):
        jogo = td.Jogo(stdscr, touch=False)
        jogo.game = game
        draw = jogo.render
    else:
        colors = td.init_colors()
        cursor = [5, 5]

        def draw():
            td.draw(stdscr, path, path_set, game, cursor, "1", "", False, False, colors)

    t0 = time.perf_counter()
    for _ in range(FRAMES):
        draw()
    t_draw = (time.perf_counter() - t0) / FRAMES * 1000
    return t_logic, t_draw


if __name__ == "__main__":
    os.environ.setdefault("ESCDELAY", "25")
    logic, draw = curses.wrapper(bench)
    # stderr: o stdout pertence ao curses e precisa ser um terminal
    out = sys.stderr
    print(f"{os.path.basename(TD_PATH)}  torres={N_TOWERS} inimigos={N_ENEMIES}", file=out)
    print(f"  logica das torres: {logic:6.2f} ms/quadro", file=out)
    print(f"  desenho da tela:   {draw:6.2f} ms/quadro", file=out)
    print(f"  total:             {logic + draw:6.2f} ms/quadro (orcamento a 30 fps: 33 ms)", file=out)
