"""Testes da lógica do Tower Defense 2 (sem tela). Uso: python3 -m unittest testes/test_logica.py"""
import copy
import importlib.util
import math
import os
import random
import tempfile
import unittest

TD_PATH = os.environ.get("TD_PATH", os.path.join(os.path.dirname(__file__), "..", "source", "td.py"))
spec = importlib.util.spec_from_file_location("td", TD_PATH)
td = importlib.util.module_from_spec(spec)
spec.loader.exec_module(td)

GRASS = next((x, y) for y in range(td.H) for x in range(td.W) if (x, y) not in td.PATH_SET)


def rich_game(gold=10_000):
    g = td.Game(seed=1)
    g.gold = gold
    return g


def put_enemy(g, kind="normal", progress=0.0, hp=None):
    e = td.Enemy(kind, 1)
    e.progress = progress
    if hp is not None:
        e.hp = e.max_hp = hp
    g.enemies.append(e)
    return e


class TestMapa(unittest.TestCase):
    def test_trilha_continua_sem_cruzar_e_dentro_do_mapa(self):
        self.assertEqual(len(td.PATH), 65)
        self.assertEqual(len(td.PATH), len(td.PATH_SET))
        for (x0, y0), (x1, y1) in zip(td.PATH, td.PATH[1:]):
            self.assertEqual(abs(x0 - x1) + abs(y0 - y1), 1)
        for x, y in td.PATH:
            self.assertTrue(0 <= x < td.W and 0 <= y < td.H)

    def test_cabe_no_celular_em_retrato(self):
        self.assertLessEqual(td.MIN_W, 40)


class TestTorres(unittest.TestCase):
    def test_regras_de_construcao(self):
        g = rich_game(100)
        self.assertFalse(g.build(*td.PATH[3], "1")[0])
        self.assertTrue(g.build(*GRASS, "2")[0])
        self.assertEqual(g.gold, 50)
        self.assertFalse(g.build(*GRASS, "1")[0])
        g.gold = 10
        ok, msg = g.build(GRASS[0] + 1, GRASS[1], "3")
        self.assertFalse(ok)
        self.assertIn("35", msg)

    def test_melhorar_ate_o_nivel_3(self):
        g = rich_game(1000)
        g.build(*GRASS, "3")
        t = g.towers[GRASS]
        d1, r1 = t.damage, t.range
        self.assertEqual(t.upgrade_cost, int(35 * 0.7))
        self.assertTrue(g.upgrade(*GRASS)[0])
        self.assertEqual(t.level, 2)
        self.assertGreater(t.damage, d1)
        self.assertGreater(t.range, r1)
        self.assertIsNone(t.span)
        self.assertTrue(g.upgrade(*GRASS)[0])
        self.assertFalse(g.upgrade(*GRASS)[0])
        self.assertEqual(t.spent, 35 + int(35 * 0.7) + int(35 * 0.7 * 2))

    def test_vender_devolve_metade_do_gasto(self):
        g = rich_game(1000)
        g.build(*GRASS, "1")
        g.upgrade(*GRASS)
        before = g.gold
        self.assertTrue(g.sell(*GRASS)[0])
        self.assertEqual(g.gold - before, (20 + int(20 * 0.7)) // 2)
        self.assertNotIn(GRASS, g.towers)

    def test_mira_no_mais_adiantado_e_respeita_cadencia(self):
        g = rich_game()
        g.build(4, 5, "3")
        a = put_enemy(g, progress=20.0, hp=1000)
        b = put_enemy(g, progress=26.0, hp=1000)
        g._fire()
        self.assertLess(b.hp, 1000)
        self.assertEqual(a.hp, 1000)
        hp = b.hp
        g._fire()
        self.assertEqual(b.hp, hp, "tiro antes do tempo de recarga")

    def test_canhao_atinge_vizinhos_pela_metade(self):
        g = rich_game()
        g.build(4, 5, "2")
        a = put_enemy(g, progress=29.0, hp=1000)  # casa (4,4), ao lado da torre
        b = put_enemy(g, progress=28.6, hp=1000)
        far = put_enemy(g, progress=5.0, hp=1000)
        g._fire()
        dmg = td.TOWERS["2"]["dmg"]
        self.assertAlmostEqual(1000 - a.hp, dmg)
        self.assertAlmostEqual(1000 - b.hp, dmg * 0.5)
        self.assertEqual(far.hp, 1000)

    def test_vortice_deixa_lento_e_chefe_resiste(self):
        g = rich_game()
        g.build(4, 5, "4")
        e = put_enemy(g, progress=29.0, hp=1000)
        g._fire()
        self.assertEqual(e.slow_factor, 0.5)
        boss = put_enemy(g, "chefe", progress=29.5, hp=10_000)
        g.towers[(4, 5)].last = -999
        g._fire()
        self.assertEqual(boss.slow_factor, 0.8)
        p0 = e.progress
        g._step(0.5)
        self.assertAlmostEqual(e.progress - p0, e.speed * 0.5 * 0.5, places=6)

    def test_abate_da_ouro_e_efeito(self):
        g = rich_game(0)
        g.build = None  # nao usado
        g.towers[(4, 5)] = td.Tower(4, 5, "2")
        e = put_enemy(g, progress=29.0, hp=1)
        g._fire()
        self.assertFalse(e.alive)
        self.assertEqual((g.gold, g.kills), (e.gold, 1))
        self.assertEqual(len(g.effects), 1)


def brute_force_fire(g):
    """Gabarito: testa todas as torres contra todos os inimigos (versão lenta)."""
    ready = [t for t in g.towers.values() if g.time - t.last >= t.rate]
    alive = sorted((e for e in g.enemies if e.alive), key=lambda e: e.progress)
    positions = [td.enemy_pos(e) for e in alive]
    for t in ready:
        best = None
        for e, (ex, ey) in zip(alive, positions):
            if e.alive and math.hypot(ex - t.x, ey - t.y) <= t.range:
                best = (e, ex, ey)
        if best:
            g._hit(t, best[0], best[1], best[2], alive, positions)
            t.last = g.time


class TestMiraOtimizada(unittest.TestCase):
    def test_igual_ao_gabarito_em_400_cenarios(self):
        rnd = random.Random(7)
        free = [(x, y) for x in range(td.W) for y in range(td.H) if (x, y) not in td.PATH_SET]
        for _ in range(400):
            g = rich_game()
            g.time = 10.0
            for x, y in rnd.sample(free, rnd.randint(1, 30)):
                t = td.Tower(x, y, rnd.choice("1234"))
                t.level = rnd.randint(1, 3)
                t.last = rnd.choice([-999.0, 9.8])
                g.towers[(x, y)] = t
            for _ in range(rnd.randint(0, 40)):
                put_enemy(g, rnd.choice(list(td.ENEMIES)), rnd.uniform(0, len(td.PATH) - 1.01), rnd.uniform(1, 40))
            ref = copy.deepcopy(g)
            g._fire()
            brute_force_fire(ref)
            self.assertEqual([(round(e.hp, 6), e.alive, e.slow_factor) for e in g.enemies],
                             [(round(e.hp, 6), e.alive, e.slow_factor) for e in ref.enemies])
            self.assertEqual((g.gold, g.kills), (ref.gold, ref.kills))


class TestOndas(unittest.TestCase):
    def test_composicao(self):
        rng = random.Random(3)
        self.assertEqual(len(td.make_wave(1, rng)), 6)
        self.assertEqual(len(td.make_wave(30, rng)), 60 + 4)
        for n in (1, 2):
            self.assertNotIn("tanque", td.make_wave(n, rng))
        self.assertNotIn("rapido", td.make_wave(1, rng))
        self.assertEqual(td.make_wave(5, rng).count("chefe"), 1)
        self.assertEqual(td.make_wave(10, rng).count("chefe"), 2)
        self.assertEqual(td.make_wave(7, rng).count("chefe"), 0)

    def test_so_uma_onda_por_vez_e_bonus_no_fim(self):
        g = td.Game(seed=2)
        self.assertTrue(g.next_wave()[0])
        self.assertEqual(g.next_wave(), (False, "Aguarde o fim da onda"))
        g.queue.clear()
        g.enemies.clear()
        gold = g.gold
        g._step(0.01)
        self.assertFalse(g.wave_active)
        self.assertEqual(g.gold, gold + 3 + 1)

    def test_tutorial_tem_onda_fraca(self):
        g = td.Game(tutorial=True)
        g.next_wave()
        self.assertEqual(g.queue, ["normal"] * 4)

    def test_monstro_que_chega_tira_vida_e_encerra(self):
        g = td.Game()
        g.life = 3
        put_enemy(g, "tanque", progress=len(td.PATH) - 1.01)
        g.update(0.5)
        self.assertEqual(g.life, 1)
        put_enemy(g, "chefe", progress=len(td.PATH) - 1.01)
        g.update(0.5)
        self.assertTrue(g.over)
        self.assertEqual(g.life, 0)

    def test_passo_grande_igual_a_varios_pequenos(self):
        def run(steps, dt):
            g = td.Game(seed=5)
            g.build(4, 5, "3")
            g.build(12, 3, "1")
            g.next_wave()
            for _ in range(steps):
                g.update(dt)
            return (g.gold, g.kills, g.life, [round(e.progress, 6) for e in g.enemies])
        self.assertEqual(run(4, 0.25), run(20, 0.05))

    def test_velocidade_2x(self):
        g = td.Game()
        e = put_enemy(g)
        g.speed = 2
        g.update(0.2)
        self.assertAlmostEqual(e.progress, e.speed * 0.4, places=6)


class TestConfiguracaoETexto(unittest.TestCase):
    def test_salva_e_le_config(self):
        with tempfile.TemporaryDirectory() as d:
            old = (td.CONFIG_DIR, td.CONFIG_FILE)
            td.CONFIG_DIR, td.CONFIG_FILE = d, os.path.join(d, "c.json")
            try:
                td.save_config({"recorde": {"onda": 7, "abates": 90}, "emoji": False})
                self.assertEqual(td.load_config()["recorde"]["onda"], 7)
            finally:
                td.CONFIG_DIR, td.CONFIG_FILE = old

    def test_largura_de_emoji(self):
        self.assertEqual(td.text_width("💗20"), 4)
        self.assertEqual(td.clip("🏹🏹🏹", 5), "🏹🏹")
        for key, c in td.TOWERS.items():
            self.assertEqual(td.text_width(c["emoji"]), 2, key)
        for key, c in td.ENEMIES.items():
            self.assertEqual(td.text_width(c["emoji"]), 2, key)
        for key, (emoji, text) in td.GLYPHS.items():
            self.assertEqual((td.text_width(emoji), len(text)), (2, 2), key)


if __name__ == "__main__":
    unittest.main()
