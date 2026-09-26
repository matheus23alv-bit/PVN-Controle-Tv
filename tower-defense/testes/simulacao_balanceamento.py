"""Simula partidas com jogadores automáticos para medir o balanceamento.

Uso: python3 testes/simulacao_balanceamento.py [caminho/td.py] [partidas]
"""
import importlib.util
import math
import os
import statistics
import sys

here = os.path.dirname(os.path.abspath(__file__))
td = None


def load(path):
    global td
    spec = importlib.util.spec_from_file_location("td", path)
    td = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(td)
    return td


def best_spots(key):
    r = td.TOWERS[key]["range"]
    free = [(x, y) for x in range(td.W) for y in range(td.H) if (x, y) not in td.PATH_SET]
    return sorted(free, key=lambda c: -sum(1 for p in td.PATH if math.hypot(p[0] - c[0], p[1] - c[1]) <= r))


def play(order, seed, upgrade=False, max_waves=50, dt=0.1):
    """order: sequencia de torres a comprar em rodizio. upgrade: melhora antes de construir nova."""
    g = td.Game(seed=seed)
    spots = {k: best_spots(k) for k in td.TOWERS}
    n = 0
    while g.wave < max_waves:
        while True:  # gasta o ouro entre as ondas
            if upgrade:
                cands = [t for t in g.towers.values() if t.upgrade_cost and t.upgrade_cost <= g.gold]
                if cands:
                    t = min(cands, key=lambda t: t.upgrade_cost)
                    g.upgrade(t.x, t.y)
                    continue
            key = order[n % len(order)]
            if g.gold < td.TOWERS[key]["cost"]:
                break
            spot = next((s for s in spots[key] if g.can_build(*s)), None)
            if spot is None:
                break
            g.build(*spot, key)
            n += 1
        g.next_wave()
        while (g.wave_active or g.enemies) and not g.over:
            g.update(dt)
        if g.over:
            return g.wave, len(g.towers)
    return max_waves, len(g.towers)


STRATEGIES = {
    "so Arqueiro": ("1", False), "so Canhao": ("2", False), "so Mago": ("3", False),
    "so Vortice": ("4", False), "misto M-A-C-V": ("3124", False), "misto + melhorar": ("3124", True),
}

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "..", "source", "td.py")
    runs = int(sys.argv[2]) if len(sys.argv) > 2 else 8
    load(path)
    print(f"{os.path.basename(path)} | HP_GROWTH={td.HP_GROWTH} | {runs} partidas por estrategia\n")
    print(f"{'estrategia':<18}{'onda media':>11}{'min':>6}{'max':>6}{'torres':>8}")
    for name, (order, up) in STRATEGIES.items():
        res = [play(order, s, up) for s in range(runs)]
        w = [r[0] for r in res]
        print(f"{name:<18}{statistics.mean(w):>11.1f}{min(w):>6}{max(w):>6}{statistics.mean(r[1] for r in res):>8.1f}")
