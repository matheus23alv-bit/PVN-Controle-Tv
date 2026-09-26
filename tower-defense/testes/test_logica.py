"""Testes da lógica do Tower Defense 3 (sem tela). Uso: python3 -m unittest testes/test_logica.py"""
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

SERPENTE = td.builtin_maps()[0]


def rich_game(gold=10_000, mapa=None):
    g = td.Game(mapa or SERPENTE, seed=1)
    g.gold = gold
    return g


def put_enemy(g, kind="normal", progress=0.0, hp=None):
    e = td.Enemy(kind, 1)
    e.progress = progress
    if hp is not None:
        e.hp = e.max_hp = hp
    g.enemies.append(e)
    return e


def spot_next_to_path(g, index):
    """Casa de grama encostada na casa index da trilha."""
    px, py = g.path[index]
    return next((px + dx, py + dy) for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0))
                if g.can_build(px + dx, py + dy))


def mapa(*rows, name="Teste"):
    return td.Mapa(list(rows), name)


def error_of(m):
    _, err = m.check()
    return err


class TestFormatoDoMapa(unittest.TestCase):
    def test_mapas_prontos_sao_jogaveis_e_em_retrato(self):
        for m in td.builtin_maps():
            path, err = m.check()
            self.assertIsNone(err, m.name)
            self.assertEqual((m.w, m.h), (11, 19), m.name)
            self.assertGreaterEqual(len(path), 60, m.name)
            self.assertEqual(len(path), len(set(path)))
            for (x0, y0), (x1, y1) in zip(path, path[1:]):
                self.assertEqual(abs(x0 - x1) + abs(y0 - y1), 1)
            self.assertEqual((m.at(*path[0]), m.at(*path[-1])), ("S", "B"))

    def test_texto_ida_e_volta(self):
        text = "; comentário\nnome: Vale Verde\n\ns######...\n.......#..\n..T....#..\n.~~....#..\n.......b\n"
        m = td.Mapa.from_text(text)
        self.assertEqual(m.name, "Vale Verde")
        self.assertEqual((m.w, m.h), (10, 5))
        self.assertEqual(m.rows()[4], ".......B..", "linha curta é completada com grama")
        self.assertEqual(m.at(0, 0), "S")
        again = td.Mapa.from_text(m.to_text())
        self.assertEqual((again.rows(), again.name), (m.rows(), m.name))

    def test_semente_fica_no_arquivo(self):
        m = td.generate_map(9, 15, 77)
        self.assertIn("semente: 77", m.to_text())
        self.assertEqual(td.Mapa.from_text(m.to_text()).seed, 77)

    def test_erros_de_formato(self):
        with self.assertRaisesRegex(td.MapError, "Letra 'x' desconhecida na linha 2"):
            td.Mapa.from_text("S####\n..x..\n")
        with self.assertRaisesRegex(td.MapError, "pequeno demais"):
            td.Mapa.from_text("S#B\n...\n")
        with self.assertRaisesRegex(td.MapError, "grande demais"):
            td.Mapa.from_text(("." * 25 + "\n") * 6)
        with self.assertRaisesRegex(td.MapError, "não tem mapa"):
            td.Mapa.from_text("nome: vazio\n")


class TestValidacao(unittest.TestCase):
    OK = ["S########.", "........#.", ".B#######.", "..........", ".........."]

    def test_mapa_bom(self):
        self.assertIsNone(error_of(mapa(*self.OK)))

    def test_falta_entrada_e_base(self):
        self.assertEqual(error_of(mapa("..........", *self.OK[1:])).msg, "Falta a entrada (S)")
        self.assertEqual(error_of(mapa(self.OK[0], self.OK[1], "..#######.", *self.OK[3:])).msg, "Falta a base (B)")

    def test_so_uma_entrada_e_uma_base(self):
        e = error_of(mapa(*self.OK[:3], "S.........", self.OK[4]))
        self.assertEqual((e.msg, e.pos), ("Só pode haver uma entrada", (0, 3)))
        e = error_of(mapa(*self.OK[:3], "........B.", self.OK[4]))
        self.assertEqual(e.msg, "Só pode haver uma base")

    def test_entrada_solta(self):
        e = error_of(mapa("S.........", ".#######..", ".B......#.", "........#.", ".#######.."))
        self.assertEqual((e.msg, e.pos), ("A entrada não encosta na trilha", (0, 0)))

    def test_trilha_sem_saida_mostra_a_casa(self):
        e = error_of(mapa("S#####....", "........#.", ".B#######.", "..........", ".........."))
        self.assertEqual((e.msg, e.pos), ("Trilha sem saída em col 6, lin 1", (5, 0)))

    def test_trilha_que_se_divide(self):
        e = error_of(mapa("S########.", "....#...#.", ".B#######.", "..........", ".........."))
        self.assertIn("se divide ou encosta", e.msg)
        self.assertEqual(e.pos, (4, 0))

    def test_voltas_encostadas(self):
        e = error_of(mapa("S########.", "#########.", "B.........", "..........", ".........."))
        self.assertIn("se divide ou encosta", e.msg)

    def test_base_encostada_por_dois_lados(self):
        e = error_of(mapa("S#######..", ".......#..", "..######..", "..B#......", ".........."))
        self.assertIsNotNone(e)
        m = mapa("S#######..", ".......#..", ".B######..", ".#........", "..........")
        self.assertEqual(error_of(m).msg, "A trilha encosta na base por dois lados")

    def test_trilha_solta(self):
        e = error_of(mapa(*self.OK[:4], "...###...."))
        self.assertEqual((e.msg, e.pos), ("Trilha solta em col 4, lin 5", (3, 4)))

    def test_trilha_curta_e_sem_grama(self):
        self.assertEqual(error_of(mapa("S###B", ".....", ".....", ".....", ".....")).msg,
                         "Trilha curta: 5 casas (mínimo 10)")
        e = error_of(mapa("S####", "TTTT#", "B###T", "TT#TT", "TT##T"))
        self.assertIsNotNone(e)
        full = mapa("S########~", "TTTTTTTT#~", "B########~", "TTTTTTTTTT", "~~~~~.~~~~")
        self.assertEqual(error_of(full).msg, "Falta grama para construir torres")

    def test_resultado_fica_guardado_ate_mudar(self):
        m = mapa(*self.OK)
        self.assertIs(m.check()[0], m.check()[0])
        m.put(9, 4, "T")
        self.assertIsNone(m.check()[1])
        m.put(5, 0, ".")
        self.assertIsNotNone(m.check()[1])


class TestGerador(unittest.TestCase):
    def test_sempre_jogavel_em_todos_os_tamanhos(self):
        for w, h in td.MAP_SIZES:
            for seed in range(120):
                m = td.generate_map(w, h, seed)
                path, err = m.check()
                self.assertIsNone(err, (w, h, seed))
                self.assertEqual((m.w, m.h), (w, h))
                self.assertGreaterEqual(len(path), w * h // 5)

    def test_mesma_semente_mesmo_mapa(self):
        self.assertEqual(td.generate_map(11, 19, 5).rows(), td.generate_map(11, 19, 5).rows())
        self.assertNotEqual(td.generate_map(11, 19, 5).rows(), td.generate_map(11, 19, 6).rows())

    def test_enfeites_longe_da_trilha(self):
        for seed in range(60):
            m = td.generate_map(11, 19, seed)
            path = m.check()[0]
            for x, y in m.find("T") + m.find("~"):
                self.assertGreaterEqual(min(max(abs(x - px), abs(y - py)) for px, py in path), 2, (seed, x, y))


class TestArquivosDeMapa(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old = td.MAPS_DIR
        td.MAPS_DIR = os.path.join(self.tmp.name, "mapas")

    def tearDown(self):
        td.MAPS_DIR = self.old
        self.tmp.cleanup()

    def test_salvar_listar_renomear(self):
        m = td.generate_map(11, 19, 3)
        path = td.save_user_map(m, "  Vale   do Sol  ")
        self.assertTrue(path.endswith("vale-do-sol.mapa"))
        self.assertEqual(m.name, "Vale do Sol")
        mine = td.user_maps()
        self.assertEqual([x.name for x in mine], ["Vale do Sol"])
        self.assertEqual(mine[0].rows(), m.rows())
        self.assertEqual(td.find_map(td.map_ref(mine[0])).rows(), m.rows())
        new = td.save_user_map(mine[0], "Vale Ágil", mine[0].file)
        self.assertFalse(os.path.exists(path), "o arquivo antigo sai quando renomeia")
        self.assertTrue(new.endswith("vale-agil.mapa"))
        self.assertEqual(td.resolve_map("vale ágil").name, "Vale Ágil")

    def test_nomes_recusados(self):
        m = td.generate_map(11, 19, 3)
        with self.assertRaisesRegex(td.MapError, "mapa pronto"):
            td.save_user_map(m, "serpente")
        with self.assertRaisesRegex(td.MapError, "Digite um nome"):
            td.save_user_map(m, "   ")
        td.save_user_map(m, "Meu")
        with self.assertRaisesRegex(td.MapError, "Já existe"):
            td.save_user_map(td.generate_map(11, 19, 4), "meu")

    def test_arquivo_quebrado_nao_derruba_a_lista(self):
        os.makedirs(td.MAPS_DIR)
        with open(os.path.join(td.MAPS_DIR, "ruim.mapa"), "w") as f:
            f.write("S#?#B\n")
        td.save_user_map(td.generate_map(9, 15, 1), "Bom")
        self.assertEqual([m.name for m in td.user_maps()], ["Bom"])
        self.assertEqual(td.next_map_name(), "Meu mapa 1")

    def test_mapa_pronto_pelo_nome(self):
        self.assertTrue(td.resolve_map("Rio").builtin)
        self.assertEqual(td.find_map("pronto:espiral").name, "Espiral")
        with self.assertRaises(td.MapError):
            td.resolve_map("não existe")


class TestEditor(unittest.TestCase):
    def new(self):
        return td.Editor(td.Mapa(["." * 11] * 19, "Novo"))

    def test_entrada_e_cantos_da_trilha(self):
        ed = self.new()
        self.assertEqual(ed.tool, "S")
        self.assertIn("cantos", ed.paint(1, 0))
        self.assertEqual(ed.tool, "#", "a entrada já liga a ferramenta Trilha")
        ed.paint(1, 5)
        ed.paint(8, 5)
        self.assertEqual(ed.mapa.rows()[5], ".########..")
        self.assertEqual([ed.mapa.at(1, y) for y in range(6)], ["S", "#", "#", "#", "#", "#"])
        ed.paint(8, 12)
        ed.tool = "B"
        ed.paint(8, 16)
        path, err = ed.mapa.check()
        self.assertIsNone(err)
        self.assertEqual(len(path), 24)

    def test_fora_da_linha_pinta_so_a_casa(self):
        ed = self.new()
        ed.paint(1, 0)
        ed.paint(4, 4)
        self.assertEqual(ed.mapa.find("#"), [(4, 4)])

    def test_tocar_na_trilha_continua_dela(self):
        ed = self.new()
        ed.paint(1, 0)
        ed.paint(1, 5)
        ed.paint(5, 5)
        self.assertEqual(ed.paint(1, 3), "Continuando a trilha daqui")
        ed.paint(4, 3)
        self.assertEqual(ed.mapa.rows()[3], ".####......")

    def test_desfazer_redimensionar_limpar_gerar(self):
        ed = self.new()
        ed.paint(1, 0)
        ed.paint(1, 5)
        before = ed.mapa.rows()
        ed.tool = "~"
        ed.paint(5, 5)
        self.assertTrue(ed.undo())
        self.assertEqual(ed.mapa.rows(), before)
        ed.resize(9, 15)
        self.assertEqual((ed.mapa.w, ed.mapa.h), (9, 15))
        self.assertEqual(ed.mapa.at(1, 0), "S", "o desenho é mantido ao encolher")
        ed.undo()
        self.assertEqual((ed.mapa.w, ed.mapa.h), (11, 19))
        ed.clear()
        self.assertEqual(ed.mapa.find("S"), [])
        seed = ed.generate(9)
        self.assertEqual(ed.mapa.rows(), td.generate_map(11, 19, 9).rows())
        self.assertEqual(seed, 9)
        self.assertTrue(ed.dirty)
        while ed.undo():
            pass
        self.assertEqual(ed.mapa.rows(), ["." * 11] * 19)
        self.assertFalse(ed.undo())

    def test_so_uma_entrada_e_uma_base(self):
        ed = self.new()
        ed.paint(1, 0)
        ed.tool = "S"
        ed.paint(5, 0)
        self.assertEqual(ed.mapa.find("S"), [(5, 0)])
        ed.tool = "B"
        ed.paint(3, 9)
        ed.paint(4, 10)
        self.assertEqual(ed.mapa.find("B"), [(4, 10)])


class TestTorres(unittest.TestCase):
    def test_regras_de_construcao(self):
        g = rich_game(100)
        grass = g.mapa.find(".")[0]
        self.assertEqual(g.build(*g.path[3], "1"), (False, "Não dá para construir na trilha"))
        self.assertEqual(g.build(*g.mapa.find("T")[0], "1"), (False, "Não dá para construir na árvore"))
        self.assertTrue(g.build(*grass, "2")[0])
        self.assertEqual(g.gold, 50)
        self.assertFalse(g.build(*grass, "1")[0])
        g.gold = 10
        ok, msg = g.build(*g.mapa.find(".")[1], "3")
        self.assertFalse(ok)
        self.assertIn("35", msg)
        rio = td.Game(td.resolve_map("Rio"))
        self.assertEqual(rio.build(*rio.mapa.find("~")[0], "1"), (False, "Não dá para construir na água"))

    def test_melhorar_ate_o_nivel_3(self):
        g = rich_game(1000)
        spot = g.mapa.find(".")[0]
        g.build(*spot, "3")
        t = g.towers[spot]
        d1, r1 = t.damage, t.range
        self.assertEqual(t.upgrade_cost, int(35 * 0.7))
        self.assertTrue(g.upgrade(*spot)[0])
        self.assertEqual(t.level, 2)
        self.assertGreater(t.damage, d1)
        self.assertGreater(t.range, r1)
        self.assertIsNone(t.span)
        self.assertTrue(g.upgrade(*spot)[0])
        self.assertFalse(g.upgrade(*spot)[0])
        self.assertEqual(t.spent, 35 + int(35 * 0.7) + int(35 * 2.2))

    def test_vender_devolve_metade_do_gasto(self):
        g = rich_game(1000)
        spot = g.mapa.find(".")[0]
        g.build(*spot, "1")
        g.upgrade(*spot)
        before = g.gold
        self.assertTrue(g.sell(*spot)[0])
        self.assertEqual(g.gold - before, (20 + int(20 * 0.7)) // 2)
        self.assertNotIn(spot, g.towers)

    def test_mira_no_mais_adiantado_e_respeita_cadencia(self):
        g = rich_game()
        spot = spot_next_to_path(g, 20)
        g.build(*spot, "3")
        a = put_enemy(g, progress=19.0, hp=1000)
        b = put_enemy(g, progress=21.0, hp=1000)
        g._fire()
        self.assertLess(b.hp, 1000)
        self.assertEqual(a.hp, 1000)
        hp = b.hp
        g._fire()
        self.assertEqual(b.hp, hp, "tiro antes do tempo de recarga")

    def test_canhao_atinge_vizinhos_pela_metade(self):
        g = rich_game()
        g.build(*spot_next_to_path(g, 20), "2")
        a = put_enemy(g, progress=20.0, hp=1000)
        b = put_enemy(g, progress=19.6, hp=1000)
        far = put_enemy(g, progress=2.0, hp=1000)
        g._fire()
        dmg = td.TOWERS["2"]["dmg"]
        self.assertAlmostEqual(1000 - a.hp, dmg)
        self.assertAlmostEqual(1000 - b.hp, dmg * 0.5)
        self.assertEqual(far.hp, 1000)

    def test_vortice_deixa_lento_chefe_resiste_morcego_imune(self):
        g = rich_game()
        spot = spot_next_to_path(g, 20)
        g.build(*spot, "4")
        e = put_enemy(g, progress=20.0, hp=1000)
        bat = put_enemy(g, "morcego", progress=20.2, hp=1000)
        g._fire()
        self.assertEqual(e.slow_factor, 0.5)
        self.assertEqual(bat.slow_factor, 1.0)
        self.assertLess(bat.slow_until, g.time)
        boss = put_enemy(g, "chefe", progress=20.5, hp=10_000)
        g.towers[spot].last = -999
        g._fire()
        self.assertEqual(boss.slow_factor, 0.8)
        p0 = e.progress
        g._step(0.5)
        self.assertAlmostEqual(e.progress - p0, e.speed * 0.5 * 0.5, places=6)

    def test_casco_da_tartaruga_e_o_mago_fura(self):
        g = rich_game()
        spot = spot_next_to_path(g, 20)
        g.build(*spot, "1")
        t = put_enemy(g, "tartaruga", progress=20.0, hp=1000)
        g._fire()
        self.assertAlmostEqual(1000 - t.hp, 6 - 4)
        g.towers[spot].level = 3  # 13.2 de dano
        g.towers[spot].last = -999
        g._fire()
        self.assertAlmostEqual(1000 - t.hp, 2 + 13.2 - 4)
        g.sell(*spot)
        g.build(*spot, "3")
        before = t.hp
        g._fire()
        self.assertAlmostEqual(before - t.hp, 10, msg="o Mago ignora o casco")
        g.sell(*spot)
        g.build(*spot, "4")
        before = t.hp
        g._fire()
        self.assertAlmostEqual(before - t.hp, 4 * 0.25, msg="dano mínimo de 25%")

    def test_fantasma_so_o_mago_ve_quando_some(self):
        g = rich_game()
        spot = spot_next_to_path(g, 20)
        g.build(*spot, "1")
        ghost = put_enemy(g, "fantasma", progress=20.0, hp=1000)
        g.time = 3.0  # fase 0: visível de 0 a 2,5 s, some de 2,5 a 3,7 s
        self.assertTrue(ghost.hidden(g.time))
        g._fire()
        self.assertEqual(ghost.hp, 1000, "Arqueiro não vê o fantasma sumido")
        g.time = 4.0
        self.assertFalse(ghost.hidden(g.time))
        g._fire()
        self.assertLess(ghost.hp, 1000)
        g.sell(*spot)
        g.build(*spot, "3")
        g.time = 6.5
        hp = ghost.hp
        self.assertTrue(ghost.hidden(g.time))
        g._fire()
        self.assertLess(ghost.hp, hp, "o Mago vê o fantasma sumido")

    def test_lesma_se_cura_so_sem_apanhar(self):
        g = rich_game()
        slug = put_enemy(g, "lesma", progress=0.0, hp=100)
        slug.hp = 50
        slug.last_hit = 0.0
        g.time = 0.0
        g._step(0.5)
        self.assertEqual(slug.hp, 50, "apanhou há menos de 1 s")
        for _ in range(20):
            g._step(0.05)
        self.assertGreater(slug.hp, 50)
        g._step(30)
        self.assertEqual(slug.hp, 100, "não passa da vida máxima")

    def test_dragao_ferido_chama_3_ratos_uma_vez(self):
        g = rich_game()
        g.wave = 5
        spot = spot_next_to_path(g, 20)
        g.build(*spot, "2")
        boss = put_enemy(g, "chefe", progress=20.0, hp=30)
        g._fire()
        self.assertTrue(boss.summoned)
        rats = [e for e in g.enemies if e.kind == "rapido"]
        self.assertEqual(len(rats), 3)
        self.assertTrue(all(r.progress < boss.progress for r in rats))
        self.assertEqual(rats[0].max_hp, td.ENEMIES["rapido"]["hp"] * td.HP_GROWTH ** 4)
        g.towers[spot].last = -999
        boss.hp = boss.max_hp * 0.4 + 30
        g._fire()
        self.assertEqual(len([e for e in g.enemies if e.kind == "rapido"]), 3)
        self.assertTrue(any(fx.kind == "summon" for fx in g.effects))

    def test_abate_da_ouro_e_efeitos(self):
        g = rich_game(0)
        spot = spot_next_to_path(g, 20)
        g.towers[spot] = td.Tower(*spot, "2")
        e = put_enemy(g, progress=20.0, hp=1)
        g._fire()
        self.assertFalse(e.alive)
        self.assertEqual((g.gold, g.kills), (e.gold, 1))
        kinds = sorted(fx.kind for fx in g.effects)
        self.assertEqual(kinds, ["boom", "corpse", "dmg", "gold", "kill", "shot"])
        self.assertIn(f"+{e.gold}", [fx.text for fx in g.effects])
        self.assertEqual(g.towers[spot].kills, 1)


def spec_key(mode, e, j, ex, ey, t):
    """Especificação da mira, escrita à parte do jogo: menor chave = alvo preferido."""
    if mode == "forte":
        return (-e.hp, -e.progress, -j)
    if mode == "perto":
        return (math.hypot(ex - t.x, ey - t.y), -e.progress, -j)
    return (-e.progress, -j)


def brute_force_fire(g):
    """Gabarito: testa todas as torres contra todos os inimigos (versão lenta)."""
    ready = [t for t in g.towers.values() if g.time - t.last >= t.rate]
    alive = sorted((e for e in g.enemies if e.alive), key=lambda e: e.progress)
    positions = [g.enemy_pos(e) for e in alive]
    for t in ready:
        cands = []
        for j, (e, (ex, ey)) in enumerate(zip(alive, positions)):
            visible = t.key == td.MAGE or not e.hidden(g.time)
            if e.alive and visible and math.hypot(ex - t.x, ey - t.y) <= t.range:
                cands.append((spec_key(t.mode, e, j, ex, ey, t), j))
        cands.sort()
        n = 2 if t.key == "1" and t.level == 3 else 1
        for _, j in cands[:n]:
            g._hit(t, alive[j], positions[j][0], positions[j][1], alive, positions)
        if cands:
            t.last = g.time


class TestMiraOtimizada(unittest.TestCase):
    def test_igual_ao_gabarito_em_400_cenarios(self):
        rnd = random.Random(7)
        maps = td.builtin_maps() + [td.generate_map(w, h, 11) for w, h in td.MAP_SIZES]
        for n in range(400):
            g = td.Game(maps[n % len(maps)], seed=n)
            g.gold = 10_000
            g.time = rnd.uniform(5, 20)
            free = g.mapa.find(".")
            for x, y in rnd.sample(free, rnd.randint(1, min(30, len(free)))):
                t = td.Tower(x, y, rnd.choice("1234"))
                t.level = rnd.randint(1, 3)
                t.mode = rnd.choice(td.TARGET_MODES)
                t.last = rnd.choice([-999.0, g.time - 0.2])
                g.towers[(x, y)] = t
            for _ in range(rnd.randint(0, 40)):
                e = td.Enemy(rnd.choice(list(td.ENEMIES)), rnd.randint(1, 20), rng=rnd)
                e.progress = rnd.uniform(0, len(g.path) - 1.01)
                e.hp = rnd.uniform(1, e.max_hp)
                g.enemies.append(e)
            ref = copy.deepcopy(g)
            g._fire()
            brute_force_fire(ref)
            self.assertEqual([(e.kind, round(e.hp, 6), e.alive, e.slow_factor, e.freeze_until) for e in g.enemies],
                             [(e.kind, round(e.hp, 6), e.alive, e.slow_factor, e.freeze_until) for e in ref.enemies])
            self.assertEqual((g.gold, g.kills), (ref.gold, ref.kills))
            self.assertEqual([(t.kills, round(t.dealt, 6), t.last) for t in g.towers.values()],
                             [(t.kills, round(t.dealt, 6), t.last) for t in ref.towers.values()])


class TestOndas(unittest.TestCase):
    def test_composicao_e_desbloqueio(self):
        rng = random.Random(3)
        self.assertEqual(len(td.make_wave(1, rng)), 6)
        self.assertEqual(len(td.make_wave(30, rng)), 60 + 4)
        self.assertEqual(set(td.make_wave(1, rng)), {"normal"})
        for n in range(1, 25):
            kinds = set()
            for _ in range(5):
                kinds |= set(td.make_wave(n, rng))
            for k in kinds - {"chefe"}:
                self.assertGreaterEqual(n, td.ENEMIES[k]["wave"], (n, k))
        late = set()
        for _ in range(5):
            late |= set(td.make_wave(12, rng))
        self.assertEqual(late, set(td.ENEMIES) - {"chefe"})
        self.assertEqual(td.make_wave(5, rng).count("chefe"), 1)
        self.assertEqual(td.make_wave(10, rng).count("chefe"), 2)
        self.assertEqual(td.make_wave(7, rng).count("chefe"), 0)

    def test_previa_e_a_proxima_onda(self):
        g = td.Game(seed=4)
        preview = list(g.next_queue)
        g.next_wave()
        self.assertEqual(g.queue, preview)
        self.assertEqual(len(g.next_queue), 8)

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
        put_enemy(g, "tanque", progress=len(g.path) - 1.01)
        g.update(0.5)
        self.assertEqual(g.life, 1)
        self.assertGreater(g.leak_until, g.time)
        put_enemy(g, "chefe", progress=len(g.path) - 1.01)
        g.update(0.5)
        self.assertTrue(g.over)
        self.assertEqual(g.life, 0)

    def test_passo_grande_igual_a_varios_pequenos(self):
        def run(steps, dt):
            g = td.Game(seed=5)
            g.gold = 500
            g.build(*spot_next_to_path(g, 10), "3")
            g.build(*spot_next_to_path(g, 25), "1")
            g.wave = 7
            g.next_queue = td.make_wave(8, g.rng)
            g.next_wave()
            for _ in range(steps):
                g.update(dt)
            return (g.gold, g.kills, g.life, [(e.kind, round(e.progress, 6), round(e.hp, 6)) for e in g.enemies])
        self.assertEqual(run(8, 0.25), run(40, 0.05))

    def test_velocidade_2x(self):
        g = td.Game()
        e = put_enemy(g)
        g.speed = 2
        g.update(0.2)
        self.assertAlmostEqual(e.progress, e.speed * 0.4, places=6)

    def test_monstros_andam_em_ritmos_diferentes(self):
        rng = random.Random(1)
        speeds = [td.Enemy("normal", 1, rng=rng).speed for _ in range(200)]
        base = td.ENEMIES["normal"]["speed"]
        self.assertTrue(all(base * 0.94 <= s <= base * 1.06 for s in speeds))
        self.assertGreater(len(set(round(s, 4) for s in speeds)), 150)

    def test_tutorial_marca_casas_boas(self):
        for m in td.builtin_maps():
            g = td.Game(m, tutorial=True)
            mage, archer = td.tutorial_spots(g)
            self.assertTrue(g.can_build(*mage) and g.can_build(*archer))
            self.assertNotEqual(mage, archer)


class TestNivel3EMira(unittest.TestCase):
    def setUp(self):
        self.g = rich_game()
        self.spot = spot_next_to_path(self.g, 20)

    def tower(self, key, level=3):
        self.g.build(*self.spot, key)
        t = self.g.towers[self.spot]
        t.level = level
        t.span = None
        return t

    def test_arqueiro_nivel_3_atira_em_2(self):
        t = self.tower("1")
        a = put_enemy(self.g, progress=20.0, hp=1000)
        b = put_enemy(self.g, progress=19.5, hp=1000)
        c = put_enemy(self.g, progress=19.0, hp=1000)
        self.g._fire()
        self.assertEqual([round(1000 - e.hp, 6) for e in (a, b, c)], [round(t.damage, 6)] * 2 + [0])
        self.assertAlmostEqual(t.dps, t.damage * 2 / t.rate)

    def test_canhao_nivel_3_explode_mais_longe(self):
        for level, hit in ((1, False), (3, True)):
            g = rich_game()
            spot = spot_next_to_path(g, 20)
            g.build(*spot, "2")
            g.towers[spot].level = level
            target = put_enemy(g, progress=20.0, hp=1000)
            near = put_enemy(g, progress=18.6, hp=1000)  # 1,4 casa atrás
            g._fire()
            self.assertLess(target.hp, 1000)
            self.assertEqual(near.hp < 1000, hit, level)

    def test_mago_nivel_3_atravessa_quem_vem_atras(self):
        t = self.tower("3")
        target = put_enemy(self.g, "tartaruga", progress=21.0, hp=1000)
        behind = put_enemy(self.g, "tartaruga", progress=20.2, hp=1000)
        far = put_enemy(self.g, progress=17.0, hp=1000)
        self.g._fire()
        self.assertAlmostEqual(1000 - target.hp, t.damage)
        self.assertAlmostEqual(1000 - behind.hp, t.damage, msg="dano cheio e sem casco")
        self.assertEqual(far.hp, 1000)
        self.assertTrue(any(fx.kind == "beam" for fx in self.g.effects))

    def test_mago_nivel_2_nao_atravessa(self):
        self.tower("3", level=2)
        put_enemy(self.g, progress=21.0, hp=1000)
        behind = put_enemy(self.g, progress=20.2, hp=1000)
        self.g._fire()
        self.assertEqual(behind.hp, 1000)

    def test_vortice_nivel_3_congela_o_alvo(self):
        self.tower("4")
        e = put_enemy(self.g, progress=20.0, hp=1000)
        self.g._fire()
        self.assertGreater(e.freeze_until, self.g.time)
        p0 = e.progress
        self.g._step(0.3)
        self.assertEqual(e.progress, p0, "congelado não anda")
        self.g._step(0.3)
        self.assertGreater(e.progress, p0)
        for kind in ("chefe", "morcego"):
            g = rich_game()
            spot = spot_next_to_path(g, 20)
            g.build(*spot, "4")
            g.towers[spot].level = 3
            other = put_enemy(g, kind, progress=20.0, hp=10_000)
            g._fire()
            self.assertLess(other.freeze_until, g.time, kind)

    def test_morcego_mostra_imune(self):
        self.tower("4", level=1)
        put_enemy(self.g, "morcego", progress=20.0, hp=1000)
        self.g._fire()
        self.assertIn("imune", [fx.text for fx in self.g.effects if fx.kind == "immune"])

    def test_modos_de_mira(self):
        t = self.tower("1", level=1)
        weak = put_enemy(self.g, progress=20.6, hp=30)
        strong = put_enemy(self.g, progress=19.4, hp=500)
        self.g._fire()
        self.assertLess(weak.hp, 30, "primeiro: o mais adiantado")
        self.assertEqual(self.g.cycle_mode(*self.spot), (True, "Arqueiro mira: o de mais vida"))
        t.last = -999
        self.g._fire()
        self.assertLess(strong.hp, 500, "forte: o de mais vida")
        self.g.cycle_mode(*self.spot)
        self.assertEqual(t.mode, "perto")
        self.g.cycle_mode(*self.spot)
        self.assertEqual(t.mode, "primeiro")
        self.assertFalse(self.g.cycle_mode(0, 0)[0])

    def test_mira_perto(self):
        t = self.tower("3", level=1)
        t.mode = "perto"
        ex, ey = self.g.path[20]
        near_idx = min(range(len(self.g.path)), key=lambda i: math.hypot(self.g.path[i][0] - t.x, self.g.path[i][1] - t.y))
        near = put_enemy(self.g, progress=float(near_idx), hp=1000)
        ahead = put_enemy(self.g, progress=float(near_idx) + 2.5, hp=1000)
        self.g._fire()
        self.assertLess(near.hp, 1000)
        self.assertEqual(ahead.hp, 1000)

    def test_upgrade_ao_nivel_3_anuncia_a_habilidade(self):
        self.g.build(*self.spot, "2")
        self.g.upgrade(*self.spot)
        ok, msg = self.g.upgrade(*self.spot)
        self.assertEqual(msg, "Canhão nível 3: explosão maior")


class TestEfeitos(unittest.TestCase):
    def test_duracao_em_tempo_real(self):
        g = rich_game()
        f1 = g.fx("kill", 1, 1, 0.3)
        g.speed = 2
        f2 = g.fx("kill", 1, 1, 0.3, delay=0.1)
        self.assertAlmostEqual(f1.t1 - f1.t0, 0.3)
        self.assertAlmostEqual(f2.t1 - f2.t0, 0.6, msg="em 2x o relógio do jogo corre 2x")
        self.assertAlmostEqual(f2.t0 - g.time, 0.2)

    def test_numero_de_dano_soma_os_tiros(self):
        g = rich_game()
        spot = spot_next_to_path(g, 20)
        g.build(*spot, "1")
        t = put_enemy(g, "tartaruga", progress=20.0, hp=1000)
        g._fire()
        g.time += 0.2
        g.towers[spot].last = -999
        g._fire()
        nums = [fx for fx in g.effects if fx.kind == "dmg"]
        self.assertEqual(len(nums), 1)
        self.assertEqual(nums[0].text, "-4")
        self.assertTrue(nums[0].muted, "casco deixa o número cinza")
        g.time += 0.5
        g.towers[spot].last = -999
        g._fire()
        self.assertEqual(len([fx for fx in g.effects if fx.kind == "dmg"]), 2)
        self.assertEqual(round(g.towers[spot].dealt, 6), 6.0)

    def test_eventos_para_vibrar_e_faixas(self):
        g = td.Game(seed=1)
        g.next_wave()
        self.assertIn("ONDA 1", [fx.text for fx in g.effects if fx.kind == "banner"])
        g.queue = ["chefe"]
        g.update(0.1)
        self.assertIn("chefe", g.events)
        boss = g.enemies[-1]
        boss.progress = len(g.path) - 1.01
        g.update(0.2)
        self.assertIn("vazou", g.events)
        self.assertGreater(g.shake_until, g.time)

    def test_chefe_morto_tem_faixa(self):
        g = rich_game()
        g.wave = 5
        spot = spot_next_to_path(g, 20)
        g.build(*spot, "2")
        put_enemy(g, "chefe", progress=20.0, hp=1)
        g._fire()
        self.assertIn("chefe_morto", g.events)
        self.assertTrue(any(fx.kind == "banner" and fx.text.startswith("chefe_morto:") for fx in g.effects))

    def test_sem_visual_nao_cria_efeitos(self):
        g = td.Game(seed=1, visual=False)
        g.gold = 1000
        g.build(*spot_next_to_path(g, 5), "2")
        g.next_wave()
        for _ in range(200):
            g.update(0.1)
        self.assertEqual((g.effects, g.events), ([], []))
        self.assertGreater(g.kills, 0)


class TestTextoCurto(unittest.TestCase):
    def test_numeros_curtos(self):
        self.assertEqual([td.short_num(n) for n in (7, 999, 1000, 1726, 9999, 12345, 2_500_000)],
                         ["7", "999", "1k", "1,7k", "10k", "12k", "2M"])

    def test_primeira_versao_que_cabe(self):
        self.assertEqual(td.fit(["texto longo demais", "curto"], 10), "curto")
        self.assertEqual(td.fit(["cabe"], 10), "cabe")
        self.assertEqual(td.fit(["nenhum cabe aqui", "nem este aqui"], 6), "nem es")

    def test_erro_de_mapa_tem_versao_curta(self):
        e = error_of(mapa("S#####....", "........#.", ".B#######.", "..........", ".........."))
        self.assertEqual(e.short, "Sem saída: c6 l1")
        self.assertLessEqual(td.text_width(" ✘ " + e.short), 30)


class TestTela(unittest.TestCase):
    def test_escala_para_a_tela_do_celular(self):
        cases = {(50, 46): 2, (53, 54): 2, (26, 32): 1, (90, 70): 3, (60, 46): 2}
        for (h, w), k in cases.items():
            L = td.compute_layout(h, w, 11, 19)
            self.assertEqual(L.k, k, (w, h))
            self.assertGreaterEqual(L.left, 0)
            self.assertGreaterEqual(L.top, 2)
            self.assertLessEqual(L.top + L.k * 19, L.panel_y, "mapa não invade o painel")
            self.assertEqual(L.bars_y + 2 * L.bar, h, "barras encostadas embaixo")
        self.assertIsNone(td.compute_layout(22, 46, 11, 19))
        self.assertIsNone(td.compute_layout(50, 28, 11, 19))
        self.assertEqual(td.min_size(11, 19), (30, 24))

    def test_toque_acha_a_casa_certa(self):
        for h, w in ((50, 46), (26, 32), (90, 70)):
            L = td.compute_layout(h, w, 11, 19)
            for x, y in ((0, 0), (5, 9), (10, 18)):
                row, col = L.anchor(x, y)
                self.assertEqual(L.tile_at(row, col), (x, y))
                self.assertEqual(L.tile_at(row, col + 1), (x, y), "o emoji ocupa 2 colunas")
            self.assertIsNone(L.tile_at(L.top - 1, L.left))

    def test_meio_caminho_fica_entre_as_casas(self):
        L = td.compute_layout(50, 46, 11, 19)
        a, b, mid = L.anchor(3, 5), L.anchor(4, 5), L.anchor(3.5, 5)
        self.assertEqual(mid[1], (a[1] + b[1]) // 2)
        self.assertEqual(L.anchor(3, 5.5)[0], L.anchor(3, 5)[0] + 1)


class TestConfiguracaoETexto(unittest.TestCase):
    def test_salva_e_le_config(self):
        with tempfile.TemporaryDirectory() as d:
            old = (td.CONFIG_DIR, td.CONFIG_FILE)
            td.CONFIG_DIR, td.CONFIG_FILE = d, os.path.join(d, "c.json")
            try:
                td.save_config({"recordes": {"abc": {"onda": 7, "abates": 90}}, "emoji": False})
                self.assertEqual(td.load_config()["recordes"]["abc"]["onda"], 7)
            finally:
                td.CONFIG_DIR, td.CONFIG_FILE = old

    def test_largura_de_emoji(self):
        self.assertEqual(td.text_width("💗20"), 4)
        self.assertEqual(td.clip("🏹🏹🏹", 5), "🏹🏹")
        for key, c in td.TOWERS.items():
            self.assertEqual(td.text_width(c["emoji"]), 2, key)
        for key, c in td.ENEMIES.items():
            self.assertEqual(td.text_width(c["emoji"]), 2, key)
            self.assertEqual(len(c["text"]), 1, key)
        for key, (emoji, text) in td.GLYPHS.items():
            self.assertEqual((td.text_width(emoji), len(text)), (2, 2), key)
        for k in (1, 2, 3):
            for c in td.TILES:
                self.assertEqual([td.text_width(r) for r in td.texture(c, 3, 4, k)], [2 * k] * k)

    def test_quebra_de_linha(self):
        lines = td.wrap("Os monstros saem da 🚪 e seguem a trilha até o 🏰.", 16)
        self.assertTrue(all(td.text_width(ln) <= 16 for ln in lines))
        self.assertEqual(" ".join(lines), "Os monstros saem da 🚪 e seguem a trilha até o 🏰.")


if __name__ == "__main__":
    unittest.main()
