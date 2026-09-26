"""Testes da codificação IR, perfis, importação e linha de comando.

Uso (na pasta controle-tv): python3 -m unittest testes/test_ir.py
"""
import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "source", "tv.py")
MOCK = os.path.join(HERE, "mock-termux-api")
spec = importlib.util.spec_from_file_location("tv", SRC)
tv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tv)


def pulse_distance_hex(pattern, nbits=32):
    """Lê os bits na ordem de transmissão (espaço longo = 1), como os códigos são publicados."""
    body = pattern[2:]
    bits = "".join("1" if body[2 * i + 1] > 1000 else "0" for i in range(nbits))
    return int(bits, 2)


def sirc_value(pattern, nbits=12):
    return int("".join("1" if pattern[2 + 2 * i] > 900 else "0" for i in range(nbits)), 2)


def manchester_bits(pattern, half, one_is_rise, skip_levels=0):
    """Reconstroi bits Manchester a partir do padrao (liga/desliga alternados)."""
    levels, on = [], True
    for d in pattern:
        levels += [1 if on else 0] * round(d / half)
        on = not on
    levels = levels[skip_levels:]
    if one_is_rise and levels[0] == 1:
        levels = [0] + levels  # RC5: o espaço inicial do 1o bit não é transmitido
    levels += [0] * (len(levels) % 2)
    pairs = [tuple(levels[i:i + 2]) for i in range(0, len(levels), 2)]
    return [(1 if p == (0, 1) else 0) if one_is_rise else (1 if p == (1, 0) else 0) for p in pairs]


# códigos publicados (bits na ordem de transmissão), usados por controles universais e IRremote
PUBLISHED = {
    "LG": {"power": 0x20DF10EF, "vol_up": 0x20DF40BF, "vol_down": 0x20DFC03F, "mute": 0x20DF906F,
           "ch_up": 0x20DF00FF, "ch_down": 0x20DF807F, "input": 0x20DFD02F, "ok": 0x20DF22DD,
           "up": 0x20DF02FD, "down": 0x20DF827D, "left": 0x20DFE01F, "right": 0x20DF609F,
           "back": 0x20DF14EB, "exit": 0x20DFDA25, "menu": 0x20DFC23D, "home": 0x20DF3EC1,
           "info": 0x20DF55AA, "d1": 0x20DF8877, "d5": 0x20DFA857, "d0": 0x20DF08F7},
    "Samsung": {"power": 0xE0E040BF, "vol_up": 0xE0E0E01F, "vol_down": 0xE0E0D02F, "mute": 0xE0E0F00F,
                "ch_up": 0xE0E048B7, "ch_down": 0xE0E008F7, "input": 0xE0E0807F, "menu": 0xE0E058A7,
                "up": 0xE0E006F9, "down": 0xE0E08679, "left": 0xE0E0A659, "right": 0xE0E046B9,
                "ok": 0xE0E016E9, "back": 0xE0E01AE5, "exit": 0xE0E0B44B, "home": 0xE0E09E61,
                "info": 0xE0E0F807, "d1": 0xE0E020DF, "d5": 0xE0E0906F, "d0": 0xE0E08877},
    "Sony": {"power": 0xA90, "vol_up": 0x490, "vol_down": 0xC90, "mute": 0x290, "ch_up": 0x090,
             "ch_down": 0x890, "input": 0xA50, "up": 0x2F0, "down": 0xAF0, "left": 0x2D0,
             "right": 0xCD0, "ok": 0xA70, "home": 0x070, "info": 0x5D0, "d1": 0x010, "d0": 0x910},
}


class TestCodigosPublicados(unittest.TestCase):
    def test_lg_e_samsung_batem_com_os_codigos_publicados(self):
        for brand in ("LG", "Samsung"):
            for key, expected in PUBLISHED[brand].items():
                freq, pattern = tv.encode(tv.BUILTIN[brand][key])
                self.assertEqual(freq, 38000)
                self.assertEqual(pulse_distance_hex(pattern), expected, f"{brand} {key}")

    def test_sony_bate_com_os_codigos_publicados(self):
        for key, expected in PUBLISHED["Sony"].items():
            freq, pattern = tv.encode(tv.BUILTIN["Sony"][key])
            self.assertEqual(freq, 40000)
            self.assertEqual(sirc_value(pattern), expected, f"Sony {key}")

    def test_todos_os_botoes_embutidos_sao_validos_para_o_android(self):
        for brand, keys in tv.BUILTIN.items():
            for key, signal in keys.items():
                freq, pattern = tv.encode(signal)
                self.assertLessEqual(sum(pattern), tv.MAX_PATTERN_US, f"{brand} {key}")
                self.assertEqual(len(pattern) % 2, 1, "padrão termina com pulso ligado")
                self.assertTrue(all(isinstance(v, int) and v > 0 for v in pattern))


class TestProtocolos(unittest.TestCase):
    def test_nec_temporizacao(self):
        freq, p = tv.nec(0x04, 0x08)
        self.assertEqual(p[:2], [9000, 4500])
        self.assertEqual(len(p), 2 + 64 + 1)
        self.assertTrue(set(p[2::2]) == {560})

    def test_nec_estendido_usa_endereco_de_16_bits(self):
        _, p = tv.nec(0x7F00, 0x12, extended=True)
        self.assertEqual(pulse_distance_hex(p) >> 16, int(f"{0x00:08b}"[::-1], 2) << 8 | int(f"{0x7F:08b}"[::-1], 2))

    def test_sirc_3_quadros_a_cada_45ms(self):
        _, p = tv.sirc(1, 21)
        frame = 25
        self.assertEqual(len(p), 3 * frame + 2)
        self.assertEqual(sum(p[:frame + 1]), 45000)

    def test_rc5_decodifica_de_volta(self):
        freq, p = tv.rc5(0, 12)
        self.assertEqual(freq, 36000)
        bits = manchester_bits(p, 889, one_is_rise=True)
        self.assertEqual(bits[:14], [1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0])

    def test_rc6_decodifica_de_volta(self):
        freq, p = tv.rc6(0x00, 0x0C)
        self.assertEqual(freq, 36000)
        self.assertEqual(p[:2], [2664, 888])
        levels, on = [], True
        for d in p:
            levels += [1 if on else 0] * round(d / 444)
            on = not on
        levels = levels[8:] + [0] * 2
        bits, i = [], 0
        widths = [1, 1, 1, 1, 2] + [1] * 16
        for w in widths:
            pair = (levels[i], levels[i + w])
            bits.append(1 if pair == (1, 0) else 0)
            i += 2 * w
        self.assertEqual(bits, [1, 0, 0, 0, 0] + [0] * 8 + [0, 0, 0, 0, 1, 1, 0, 0])

    def test_rejeita_padrao_grande_demais(self):
        with self.assertRaises(ValueError):
            tv.validate_pattern(38000, [1_000_000, 1_000_000, 10])


class TestNomes(unittest.TestCase):
    def test_apelidos(self):
        cases = {"ligar": "power", "Power": "power", "vol+": "vol_up", "Vol_dn": "vol_down",
                 "canal+": "ch_up", "Ch_prev": "ch_down", "Source": "input", "início": "home",
                 "Return": "back", "7": "d7", "ENTER": "ok", "xyz": None}
        for name, key in cases.items():
            self.assertEqual(tv.canon(name), key, name)


FLIPPER_SAMPLE = """Filetype: IR signals file
Version: 1
#
name: Power
type: parsed
protocol: NECext
address: 00 7F 00 00
command: 15 EA 00 00
#
name: Vol_up
type: parsed
protocol: NEC
address: 04 00 00 00
command: 02 00 00 00
#
name: Mute
type: raw
frequency: 38000
duty_cycle: 0.330000
data: 9000 4500 560 560 560 1690 560
#
name: Ch_next
type: parsed
protocol: Kaseikyo
address: 80 02 20 00
command: 3D 01 00 00
#
name: Netflix
type: parsed
protocol: Samsung32
address: 07 00 00 00
command: F3 00 00 00
"""


class TestImportacao(unittest.TestCase):
    def test_le_arquivo_do_flipper(self):
        keys, skipped = tv.parse_ir_file(FLIPPER_SAMPLE)
        self.assertEqual(set(keys), {"power", "vol_up", "mute"})
        self.assertEqual(keys["power"], {"protocol": "necext", "address": 0x7F00, "command": 0xEA15})
        self.assertEqual(keys["mute"]["data"][:2], [9000, 4500])
        self.assertTrue(any("Kaseikyo" in s for s in skipped))
        self.assertTrue(any("Netflix" in s for s in skipped))
        freq, p = tv.encode(keys["power"])
        self.assertEqual(pulse_distance_hex(p) & 0xFFFF, int(f"{0x15:08b}"[::-1], 2) << 8 | int(f"{0xEA:08b}"[::-1], 2))

    def test_importa_e_aparece_nos_perfis(self):
        with tempfile.TemporaryDirectory() as d:
            old = (tv.CONFIG_DIR, tv.PROFILES_DIR, tv.CONFIG_FILE)
            tv.CONFIG_DIR, tv.PROFILES_DIR, tv.CONFIG_FILE = d, os.path.join(d, "perfis"), os.path.join(d, "c.json")
            try:
                src = os.path.join(d, "Philco PTV32.ir")
                with open(src, "w") as f:
                    f.write(FLIPPER_SAMPLE)
                name, keys, _ = tv.import_profile(src)
                self.assertEqual(name, "Philco PTV32")
                self.assertIn("Philco PTV32", tv.load_profiles())
            finally:
                tv.CONFIG_DIR, tv.PROFILES_DIR, tv.CONFIG_FILE = old


class TestLinhaDeComando(unittest.TestCase):
    def run_tv(self, *args, env_extra=None, path_mock=True):
        with tempfile.TemporaryDirectory() as home:
            log = os.path.join(home, "ir.log")
            env = dict(os.environ, HOME=home, XDG_CONFIG_HOME=os.path.join(home, ".config"), TV_MOCK_LOG=log)
            env["PATH"] = (MOCK + os.pathsep if path_mock else "") + "/usr/bin:/bin"
            env.update(env_extra or {})
            r = subprocess.run([sys.executable, SRC, *args], capture_output=True, text=True, env=env, timeout=30)
            sent = ""
            if os.path.exists(log):
                with open(log) as f:
                    sent = f.read()
            return r, sent

    def test_envia_botao_pela_linha_de_comando(self):
        r, sent = self.run_tv("--perfil", "LG", "ligar")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue(sent.startswith("-f 38000 9000,4500,"))
        self.assertIn("✓ Ligar/desligar (LG)", r.stdout)

    def test_sem_tv_escolhida_orienta(self):
        r, sent = self.run_tv("ligar")
        self.assertEqual(r.returncode, 2)
        self.assertIn("Nenhuma TV escolhida", r.stdout)
        self.assertEqual(sent, "")

    def test_sem_termux_api_orienta_a_instalar(self):
        r, _ = self.run_tv("--perfil", "Samsung", "mudo", path_mock=False)
        self.assertEqual(r.returncode, 1)
        self.assertIn("pkg install termux-api", r.stdout)

    def test_diagnostico_sem_emissor(self):
        r, _ = self.run_tv("--diagnostico", env_extra={"TV_MOCK_SEM_IR": "1"})
        self.assertEqual(r.returncode, 1)
        self.assertIn("não tem emissor infravermelho", r.stdout)

    def test_diagnostico_com_emissor(self):
        r, _ = self.run_tv("--diagnostico")
        self.assertEqual(r.returncode, 0)
        self.assertIn("emissor IR pronto (30-60 kHz)", r.stdout)

    def test_app_termux_api_sem_resposta(self):
        tx = tv.Transmitter()
        tx.cmd = os.path.join(MOCK, "termux-infrared-transmit")
        os.environ["TV_MOCK_TRAVAR"] = "1"
        try:
            ok, msg = tx.send(38000, [5], timeout=1)
        finally:
            del os.environ["TV_MOCK_TRAVAR"]
        self.assertFalse(ok)
        self.assertIn("Termux:API", msg)

    def test_atalhos_do_widget(self):
        with tempfile.TemporaryDirectory() as home:
            env = dict(os.environ, HOME=home)
            subprocess.run([sys.executable, SRC, "--atalhos"], capture_output=True, env=env, check=True)
            files = sorted(os.listdir(os.path.join(home, ".shortcuts")))
            self.assertIn("TV Ligar", files)
            self.assertTrue(os.access(os.path.join(home, ".shortcuts", "TV Ligar"), os.X_OK))

    def test_versao(self):
        r, _ = self.run_tv("--versao")
        with open(os.path.join(HERE, "..", "source", "VERSION")) as f:
            self.assertEqual(r.stdout.strip(), f.read().strip())


if __name__ == "__main__":
    unittest.main()
