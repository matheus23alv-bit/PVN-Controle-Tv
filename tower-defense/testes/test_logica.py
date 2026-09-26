"""Testes da lógica do jogo (sem interface). Uso: python3 -m unittest testes/test_logica.py"""
import copy
import importlib.util
import math
import os
import random
import unittest

TD_PATH = os.environ.get("TD_PATH", os.path.join(os.path.dirname(__file__), "..", "source", "td.py"))
spec = importlib.util.spec_from_file_location("td", TD_PATH)
td = importlib.util.module_from_spec(spec)
spec.loader.exec_module(td)


def fresh_state(gold=1000):
    return {"gold": gold, "base_hp": td.START_LIFE, "wave": 0, "kills": 0}


class TestCaminho(unittest.TestCase):
    def setUp(self):
        self.path = td.build_path()

    def test_dentro_do_grid(self):
        for x, y in self.path:
            self.assertTrue(0 <= x < td.GRID_W and 0 <= y < td.GRID_H, (x, y))

    def test_continuo(self):
        for (x0, y0), (x1, y1) in zip(self.path, self.path[1:]):
            self.assertEqual(abs(x0 - x1) + abs(y0 - y1), 1, ((x0, y0), (x1, y1)))

    def test_sem_autointersecao(self):
        self.assertEqual(len(self.path), len(set(self.path)))


class TestTorres(unittest.TestCase):
    def setUp(self):
        self.path = td.build_path()
        self.path_set = set(self.path)
        self.free = next((x, y) for x in range(td.GRID_W) for y in range(td.GRID_H) if (x, y) not in self.path_set)

    def test_nao_constroi_no_caminho(self):
        state, towers = fresh_state(), []
        td.try_place_tower(list(self.path[5]), towers, self.path_set, state, "1")
        self.assertEqual(towers, [])

    def test_nao_empilha(self):
        state, towers = fresh_state(), []
        td.try_place_tower(list(self.free), towers, self.path_set, state, "1")
        td.try_place_tower(list(self.free), towers, self.path_set, state, "2")
        self.assertEqual(len(towers), 1)

    def test_ouro_insuficiente(self):
        state, towers = fresh_state(gold=10), []
        td.try_place_tower(list(self.free), towers, self.path_set, state, "2")
        self.assertEqual((towers, state["gold"]), ([], 10))

    def test_desconta_e_devolve_metade(self):
        state, towers = fresh_state(gold=100), []
        td.try_place_tower(list(self.free), towers, self.path_set, state, "2")
        self.assertEqual(state["gold"], 50)
        td.try_sell_tower(list(self.free), towers, state)
        self.assertEqual((towers, state["gold"]), ([], 75))

    def test_mira_no_inimigo_mais_avancado(self):
        tower = td.Tower(9, 4, "3")
        a, b = td.Enemy("normal", 1), td.Enemy("normal", 1)
        a.progress, b.progress = 8.0, 12.0
        td.update_towers([tower], [a, b], self.path, now=10.0, state=fresh_state())
        self.assertLess(b.hp, b.max_hp)
        self.assertEqual(a.hp, a.max_hp)

    def test_respeita_cadencia(self):
        tower = td.Tower(9, 4, "1")
        e = td.Enemy("tank", 1)
        e.progress = 10.0
        st = fresh_state()
        td.update_towers([tower], [e], self.path, 10.0, st)
        td.update_towers([tower], [e], self.path, 10.1, st)
        self.assertEqual(e.hp, e.max_hp - td.TOWER_TYPES["1"]["damage"])

    def test_abate_da_ouro(self):
        tower = td.Tower(9, 4, "2")
        e = td.Enemy("fast", 1)
        e.progress = 10.0
        st = fresh_state(gold=0)
        td.update_towers([tower], [e], self.path, 10.0, st)
        self.assertFalse(e.alive)
        self.assertEqual((st["gold"], st["kills"]), (e.gold, 1))


def reference_update_towers(towers, enemies, path, now, state):
    """Mira original da v1.0.x (O(torres x inimigos)), usada como gabarito."""
    for t in towers:
        cfg = td.TOWER_TYPES[t.type_key]
        if now - t.last_shot < cfg["rate"]:
            continue
        target, best = None, -1.0
        for e in enemies:
            if not e.alive:
                continue
            ex, ey = td.enemy_pos(e, path)
            if math.hypot(ex - t.x, ey - t.y) <= cfg["range"] and e.progress > best:
                target, best = e, e.progress
        if target is not None:
            target.hp -= cfg["damage"]
            t.last_shot = now
            if target.hp <= 0:
                target.alive = False
                state["gold"] += target.gold
                state["kills"] += 1


class TestMiraOtimizadaEquivalente(unittest.TestCase):
    def test_mesmo_resultado_que_a_mira_original(self):
        rnd = random.Random(2026)
        path = td.build_path()
        free = [(x, y) for x in range(td.GRID_W) for y in range(td.GRID_H) if (x, y) not in set(path)]
        for _ in range(500):
            towers = [td.Tower(x, y, rnd.choice("123")) for x, y in rnd.sample(free, rnd.randint(1, 40))]
            for t in towers:
                t.last_shot = rnd.choice([-999.0, 9.5, 9.9])
            enemies = []
            for _ in range(rnd.randint(0, 50)):
                e = td.Enemy(rnd.choice(["normal", "fast", "tank"]), rnd.randint(1, 20))
                e.progress = rnd.uniform(0, len(path) - 1.001)
                e.hp = rnd.uniform(1, 40)
                enemies.append(e)
            a_t, a_e = copy.deepcopy(towers), copy.deepcopy(enemies)
            b_t, b_e = copy.deepcopy(towers), copy.deepcopy(enemies)
            sa, sb = fresh_state(0), fresh_state(0)
            reference_update_towers(a_t, a_e, path, 10.0, sa)
            td.update_towers(b_t, b_e, path, 10.0, sb)
            self.assertEqual(sa, sb)
            self.assertEqual([(e.hp, e.alive) for e in a_e], [(e.hp, e.alive) for e in b_e])
            self.assertEqual([t.last_shot for t in a_t], [t.last_shot for t in b_t])


class TestInimigosEOndas(unittest.TestCase):
    def test_chegar_na_base_tira_vida(self):
        path = td.build_path()
        st = fresh_state()
        tank = td.Enemy("tank", 1)
        tank.progress = len(path) - 1.01
        td.update_enemies([tank], path, 1.0, st)
        self.assertEqual(st["base_hp"], td.START_LIFE - 2)
        self.assertFalse(tank.alive)

    def test_tamanho_da_onda(self):
        for w in (1, 5, 10):
            self.assertEqual(len(td.make_wave(w)), 5 + 2 * w)

    def test_tanques_so_a_partir_da_onda_3(self):
        random.seed(1)
        for _ in range(200):
            self.assertNotIn("tank", td.make_wave(1) + td.make_wave(2))

    def test_vida_cresce_exponencialmente(self):
        hp = [td.Enemy("normal", w).max_hp for w in (1, 11, 21)]
        self.assertGreater(hp[2] / hp[1], 1.5)
        self.assertAlmostEqual(hp[2] / hp[1], hp[1] / hp[0], places=6)


class TestPartida(unittest.TestCase):
    def test_nova_partida_e_independente(self):
        g1 = td.new_game()
        g1["state"]["base_hp"] = 0
        g1["game_over"] = True
        g2 = td.new_game()
        self.assertEqual(g2["state"]["base_hp"], td.START_LIFE)
        self.assertFalse(g2["game_over"])
        self.assertIsNot(g1["towers"], g2["towers"])


if __name__ == "__main__":
    unittest.main()
