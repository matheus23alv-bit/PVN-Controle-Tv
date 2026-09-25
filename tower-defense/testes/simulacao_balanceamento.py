"""Simula partidas com um jogador automático para medir o balanceamento.

Uso: python3 testes/simulacao_balanceamento.py [caminho/td.py] [partidas]
"""
import importlib.util
import os
import random
import statistics
import sys

here = os.path.dirname(os.path.abspath(__file__))
td = None


def load(td_path):
    global td
    spec = importlib.util.spec_from_file_location("td", td_path)
    td = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(td)
    return td


def cover_score(cell, path):
    return sum(1 for p in path if (p[0] - cell[0]) ** 2 + (p[1] - cell[1]) ** 2 <= 9)


def play(strategy, seed, max_waves=40, dt=0.1):
    random.seed(seed)
    path = td.build_path()
    path_set = set(path)
    spots = sorted(
        ((x, y) for x in range(td.GRID_W) for y in range(td.GRID_H) if (x, y) not in path_set),
        key=lambda c: -cover_score(c, path),
    )
    state = {"gold": td.START_GOLD, "base_hp": td.START_LIFE, "wave": 0, "kills": 0}
    towers, now = [], 0.0
    for wave in range(1, max_waves + 1):
        # compra entre ondas, sempre no melhor ponto livre
        while True:
            key = strategy(towers)
            cost = td.TOWER_TYPES[key]["cost"]
            free = [s for s in spots if all((t.x, t.y) != s for t in towers)]
            if state["gold"] < cost or not free:
                break
            td.try_place_tower(list(free[0]), towers, path_set, state, key)
        state["wave"] = wave
        queue, enemies, timer = td.make_wave(wave), [], 0.0
        while queue or enemies:
            timer -= dt
            if timer <= 0 and queue:
                enemies.append(td.Enemy(queue.pop(0), wave))
                timer = td.SPAWN_INTERVAL
            td.update_enemies(enemies, path, dt, state)
            td.update_towers(towers, enemies, path, now, state)
            enemies = [e for e in enemies if e.alive]
            now += dt
            if state["base_hp"] <= 0:
                return wave, len(towers)
    return max_waves, len(towers)


STRATEGIES = {
    "so Arqueiro": lambda t: "1",
    "so Canhao": lambda t: "2",
    "so Mago": lambda t: "3",
    "misto 1-3-2": lambda t: "132"[len(t) % 3],
}

if __name__ == "__main__":
    td_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "..", "source", "td.py")
    runs = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    load(td_path)
    print(f"Arquivo: {td_path}  |  {runs} partidas por estrategia\n")
    print(f"{'estrategia':<14}{'onda media':>11}{'min':>6}{'max':>6}{'torres':>8}")
    for name, fn in STRATEGIES.items():
        res = [play(fn, seed) for seed in range(runs)]
        waves = [r[0] for r in res]
        print(f"{name:<14}{statistics.mean(waves):>11.1f}{min(waves):>6}{max(waves):>6}{statistics.mean(r[1] for r in res):>8.1f}")
