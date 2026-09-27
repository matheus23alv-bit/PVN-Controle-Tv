"""Testes do Teclado Termux (teclas.py): perfis, arquivo do Termux, troca automática e remoção.

Uso (na pasta teclado-termux): python3 -m unittest testes/test_teclas.py
Cada teste roda o comando num HOME temporário, como no Termux, com um
termux-reload-settings falso que registra cada recarga.
"""
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "source", "teclas.py")
sys.path.insert(0, os.path.dirname(SRC))
import teclas  # noqa: E402

TD_OLD = "[['ESC','1','2','3','4','u','x','UP','ENTER'],['p','n','f','h','q','KEYBOARD','LEFT','DOWN','RIGHT']]"
MINHA = ["# minha config", "extra-keys = [ \\", " ['ESC','/','-','HOME','UP','END'], \\",
         " ['TAB','CTRL','ALT','LEFT','DOWN','RIGHT'] \\", "]", "use-black-ui = true"]


def java_unescape(value):
    """O que o java.util.Properties do Termux faz com \\uXXXX (inclusive pares de emoji)."""
    units = re.sub(r"\\u([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1), 16)), value)
    return units.encode("utf-16", "surrogatepass").decode("utf-16")


def lenient_json(text):
    """Lê o JSON tolerante do org.json (aspas simples e palavras sem aspas), como o Termux."""
    pos = 0

    def ws():
        nonlocal pos
        while pos < len(text) and text[pos].isspace():
            pos += 1

    def value():
        nonlocal pos
        ws()
        ch = text[pos]
        if ch == "[":
            pos += 1
            out = []
            ws()
            if text[pos] == "]":
                pos += 1
                return out
            while True:
                out.append(value())
                ws()
                if text[pos] == ",":
                    pos += 1
                    continue
                assert text[pos] == "]", f"esperava ] em {pos}: {text[pos:pos + 20]}"
                pos += 1
                return out
        if ch == "{":
            pos += 1
            out = {}
            while True:
                ws()
                key = word()
                ws()
                assert text[pos] == ":", f"esperava : em {pos}"
                pos += 1
                out[key] = value()
                ws()
                if text[pos] == ",":
                    pos += 1
                    continue
                assert text[pos] == "}", f"esperava }} em {pos}"
                pos += 1
                return out
        return word()

    def word():
        nonlocal pos
        ws()
        if text[pos] in "'\"":
            q = text[pos]
            end = text.index(q, pos + 1)
            s = text[pos + 1:end]
            pos = end + 1
            return s
        m = re.match(r"[A-Za-z0-9_+\-]+", text[pos:])
        assert m, f"palavra inválida em {pos}: {text[pos:pos + 10]}"
        pos += m.end()
        return m.group(0)

    result = value()
    ws()
    assert pos == len(text), "sobrou texto no fim"
    return result


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = self.tmp.name
        self.bin = os.path.join(self.home, "bin")
        os.makedirs(self.bin)
        self.reloads = os.path.join(self.home, "recargas.log")
        with open(os.path.join(self.bin, "termux-reload-settings"), "w") as f:
            f.write(f"#!/bin/sh\necho recarregou >> '{self.reloads}'\n")
        os.chmod(os.path.join(self.bin, "termux-reload-settings"), 0o755)
        self.props = os.path.join(self.home, ".termux", "termux.properties")

    def tearDown(self):
        self.tmp.cleanup()

    def run_teclas(self, *args, termux=True, reload=True):
        env = dict(os.environ, HOME=self.home, XDG_CONFIG_HOME=os.path.join(self.home, ".config"))
        env.pop("TERMUX_VERSION", None)
        if termux:
            env["TERMUX_VERSION"] = "0.118"
        if reload:
            env["PATH"] = self.bin + ":" + env["PATH"]
        return subprocess.run([sys.executable, SRC, *args], capture_output=True, text=True, env=env,
                              stdin=subprocess.DEVNULL, timeout=30)

    def write(self, lines):
        os.makedirs(os.path.dirname(self.props), exist_ok=True)
        with open(self.props, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")

    def lines(self):
        with open(self.props, encoding="utf-8") as f:
            return f.read().splitlines()

    def keys_lines(self):
        return [x for x in self.lines() if x.startswith("extra-keys")]

    def state(self):
        with open(os.path.join(self.home, ".config", "teclas", "estado.json"), encoding="utf-8") as f:
            return json.load(f)

    def reload_count(self):
        try:
            with open(self.reloads) as f:
                return len(f.read().splitlines())
        except OSError:
            return 0


class TestPerfis(unittest.TestCase):
    def test_cada_perfil_e_lido_pelo_termux(self):
        for name in teclas.PROFILES:
            line = teclas.render(name)
            self.assertTrue(line.isascii(), f"{name}: o arquivo só leva ASCII (\\uXXXX para o resto)")
            rows = lenient_json(java_unescape(line.split("=", 1)[1].strip()))
            self.assertEqual(len(rows), 2, name)
            self.assertEqual(len(rows[0]), len(rows[1]), f"{name}: colunas alinhadas nas duas linhas")

    def test_emojis_e_acentos_voltam_certos(self):
        rows = lenient_json(java_unescape(teclas.render("jogo").split("=", 1)[1]))
        self.assertEqual(rows[0][1], {"key": "1", "display": "🏹"})
        rows = lenient_json(java_unescape(teclas.render("tv").split("=", 1)[1]))
        self.assertEqual(rows[1][1], {"key": "i", "display": "INÍCIO"})
        rows = lenient_json(java_unescape(teclas.render("melhorado").split("=", 1)[1]))
        self.assertEqual(rows[0][6], {"macro": "t v ENTER", "display": "📺"})
        self.assertEqual(rows[0][0]["popup"], {"macro": "CTRL c", "display": "^C"})

    def test_tv_volume_nas_teclas_que_repetem_ao_segurar(self):
        # no Termux, só setas, BKSP, DEL, PGUP e PGDN repetem quando seguradas
        keys = {x["key"]: x["show"] for row in teclas.PROFILES["tv"]["rows"] for x in row}
        self.assertEqual(keys["PGUP"], "VOL+")
        self.assertEqual(keys["PGDN"], "VOL-")

    def test_jogo_tem_as_teclas_do_td(self):
        keys = {x["key"] for row in teclas.PROFILES["jogo"]["rows"] for x in row}
        for key in ("1", "2", "3", "4", "u", "x", "n", "f", "t", "p", "h", "ESC", "ENTER", "KEYBOARD"):
            self.assertIn(key, keys)

    def test_setas_uma_embaixo_da_outra(self):
        for name, prof in teclas.PROFILES.items():
            top = [x["key"] for x in prof["rows"][0]]
            low = [x["key"] for x in prof["rows"][1]]
            self.assertEqual(top.index("UP"), low.index("DOWN"), name)

    def test_nomes_aceitos(self):
        for name, want in (("td", "jogo"), ("Jogo", "jogo"), ("controle", "tv"), ("padrão", "padrao"),
                           ("Padrão melhorado", "melhorado"), ("antes", "original"), ("xyz", None)):
            self.assertEqual(teclas.canon(name), want, name)


class TestArquivo(Base):
    def test_sem_arquivo_cria_so_a_barra(self):
        r = self.run_teclas("melhorado")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("✔ Padrão melhorado", r.stdout)
        self.assertEqual(self.lines(), ["# teclas: melhorado", teclas.render("melhorado")])
        self.assertEqual(self.reload_count(), 1)
        self.assertEqual(teclas.detect(self.lines()), "melhorado")

    def test_barra_propria_em_varias_linhas_e_trocada_por_inteiro(self):
        self.write(MINHA)
        self.run_teclas("jogo")
        lines = self.lines()
        self.assertEqual(len(self.keys_lines()), 1)
        self.assertNotIn("['TAB','CTRL','ALT','LEFT','DOWN','RIGHT'] \\", lines)
        self.assertEqual(lines[0], "# minha config")
        self.assertEqual(lines[-1], "use-black-ui = true", "outras opções ficam no lugar")
        self.assertEqual(lines[1:3], ["# teclas: jogo", teclas.render("jogo")], "a barra fica onde estava")

    def test_original_devolve_a_barra_da_pessoa_exata(self):
        self.write(MINHA)
        self.run_teclas("tv")
        self.run_teclas("melhorado")
        r = self.run_teclas("original")
        self.assertIn("A sua de antes", r.stdout)
        self.assertEqual(self.lines(), MINHA)

    def test_padrao_tira_a_linha(self):
        self.write(MINHA)
        self.run_teclas("padrao")
        self.assertEqual(self.keys_lines(), [])
        self.assertIn("use-black-ui = true", self.lines())

    def test_repetir_nao_duplica_nem_recarrega(self):
        self.run_teclas("jogo")
        r = self.run_teclas("jogo")
        self.assertIn("(já estava)", r.stdout)
        self.assertEqual(len(self.keys_lines()), 1)
        self.assertEqual(self.reload_count(), 1)

    def test_backup_do_arquivo_na_primeira_troca(self):
        self.write(MINHA)
        self.run_teclas("jogo")
        self.run_teclas("tv")
        with open(self.props + ".antes-do-teclas", encoding="utf-8") as f:
            self.assertEqual(f.read().splitlines(), MINHA)

    def test_barra_fixada_pelo_td_31_vira_a_da_pessoa_de_antes(self):
        td = "# instalado pelo tower-defense"
        self.write(["fullscreen = false", td, f"extra-keys = {TD_OLD}", td, "fullscreen = true"])
        with open(self.props + ".antes-do-td", "w", encoding="utf-8") as f:
            f.write("\n".join(MINHA[:5] + ["fullscreen = false"]) + "\n")
        self.assertEqual(teclas.detect(self.lines()), "td-antigo")
        self.run_teclas("melhorado")
        lines = self.lines()
        self.assertEqual(lines[-2:], [td, "fullscreen = true"], "a marca da tela cheia do td fica intacta")
        self.assertEqual(lines.count(td), 1, "a marca da barra antiga do td sai junto")
        self.assertEqual(self.state()["original"], MINHA[1:5])
        self.run_teclas("original")
        self.assertEqual(self.keys_lines(), ["extra-keys = [ \\"])

    def test_perfil_desconhecido(self):
        r = self.run_teclas("xyz")
        self.assertEqual(r.returncode, 2)
        self.assertIn("Perfil desconhecido", r.stdout)

    def test_original_sem_barra_propria_vira_padrao(self):
        self.run_teclas("jogo")
        r = self.run_teclas("original")
        self.assertIn("a de antes é o padrão do Termux", r.stdout)
        self.assertFalse(os.path.exists(self.props), "o arquivo não existia antes: volta a não existir")

    def test_fora_do_termux_avisa_para_recarregar(self):
        r = self.run_teclas("jogo", reload=False)
        self.assertIn("recarregue o Termux", r.stdout)
        self.assertEqual(teclas.detect(self.lines()), "jogo")


class TestTrocaAutomatica(Base):
    def test_entrar_e_sair_devolvem_a_barra_exata(self):
        self.write(MINHA)
        self.run_teclas("--entrar", "jogo")
        self.assertEqual(teclas.detect(self.lines()), "jogo")
        self.run_teclas("--sair")
        self.assertEqual(self.lines(), MINHA)
        self.assertEqual(self.reload_count(), 2)

    def test_fechamento_sem_sair_nao_perde_a_barra_de_volta(self):
        # o app foi morto (sem --sair) e outro abriu: a volta continua sendo a barra do dia a dia
        self.run_teclas("melhorado")
        self.run_teclas("--entrar", "jogo")
        self.run_teclas("--entrar", "tv")
        self.assertEqual(teclas.detect(self.lines()), "tv")
        self.run_teclas("--sair")
        self.assertEqual(teclas.detect(self.lines()), "melhorado")
        self.run_teclas("--sair")
        self.assertEqual(teclas.detect(self.lines()), "melhorado", "segundo --sair não faz nada")

    def test_escolha_manual_cancela_a_volta(self):
        self.run_teclas("--entrar", "tv")
        self.run_teclas("jogo")
        self.run_teclas("--sair")
        self.assertEqual(teclas.detect(self.lines()), "jogo")

    def test_desligada_nao_troca(self):
        self.run_teclas("melhorado")
        r = self.run_teclas("--auto", "nao")
        self.assertIn("desligada", r.stdout)
        self.run_teclas("--entrar", "jogo")
        self.assertEqual(teclas.detect(self.lines()), "melhorado")
        self.run_teclas("--auto", "sim")
        self.run_teclas("--entrar", "jogo")
        self.assertEqual(teclas.detect(self.lines()), "jogo")

    def test_fora_do_termux_o_app_nao_mexe(self):
        self.run_teclas("--entrar", "jogo", termux=False)
        self.assertFalse(os.path.exists(self.props))

    def test_sair_logo_depois_de_entrar_termina_na_barra_de_volta(self):
        # o td fecha rápido: o --sair começa antes do --entrar acabar de recarregar o Termux
        self.run_teclas("melhorado")
        with open(os.path.join(self.bin, "termux-reload-settings"), "w") as f:
            f.write(f"#!/bin/sh\nsleep 0.5\necho recarregou >> '{self.reloads}'\n")
        env = dict(os.environ, HOME=self.home, XDG_CONFIG_HOME=os.path.join(self.home, ".config"),
                   TERMUX_VERSION="0.118", PATH=self.bin + ":" + os.environ["PATH"])
        a = subprocess.Popen([sys.executable, SRC, "--entrar", "jogo"], env=env)
        time.sleep(0.15)
        b = subprocess.Popen([sys.executable, SRC, "--sair"], env=env)
        a.wait(timeout=20)
        b.wait(timeout=20)
        self.assertEqual(teclas.detect(self.lines()), "melhorado")
        self.assertEqual(self.reload_count(), 3, "cada troca recarregou, na ordem")

    def test_perfil_do_app_invalido(self):
        self.assertEqual(self.run_teclas("--entrar", "xyz").returncode, 2)

    def test_estado(self):
        self.run_teclas("melhorado")
        self.run_teclas("--entrar", "tv")
        out = self.run_teclas("--estado").stdout
        self.assertIn("barra: Controle da TV", out)
        self.assertIn("troca automática: sim", out)
        self.assertIn("volta ao fechar o app: Padrão melhorado", out)


class TestRemover(Base):
    def test_remover_devolve_a_barra_e_apaga_o_estado(self):
        self.write(MINHA)
        self.run_teclas("jogo")
        self.run_teclas("--remover")
        self.assertEqual(self.lines(), MINHA)
        self.assertFalse(os.path.exists(self.props + ".antes-do-teclas"))
        self.assertFalse(os.path.exists(os.path.join(self.home, ".config", "teclas")))

    def test_remover_apaga_o_arquivo_que_nao_existia(self):
        self.run_teclas("melhorado")
        self.run_teclas("--remover")
        self.assertFalse(os.path.exists(self.props))

    def test_remover_mantem_o_que_a_pessoa_pos_depois(self):
        self.run_teclas("melhorado")
        with open(self.props, "a", encoding="utf-8") as f:
            f.write("bell-character = ignore\n")
        self.run_teclas("--remover")
        self.assertEqual(self.lines(), ["bell-character = ignore"])


class TestBarraNaoFicaPresa(Base):
    """A barra de um app nunca fica presa: o dono morreu, a barra volta."""

    def morto(self):
        """Um PID que com certeza não existe mais."""
        r = subprocess.run([sys.executable, "-c", "import os; print(os.getpid())"],
                           capture_output=True, text=True, timeout=30)
        return r.stdout.strip()

    def test_dono_morto_devolve_a_barra_na_proxima_chamada(self):
        self.write(MINHA)
        self.run_teclas("--entrar", "jogo", "--dono", self.morto())
        self.assertEqual(teclas.detect(self.lines()), "jogo")
        self.run_teclas("--estado")          # qualquer chamada do teclas recupera
        self.assertEqual(self.lines(), MINHA)

    def test_dono_vivo_mantem_a_barra_do_app(self):
        self.write(MINHA)
        self.run_teclas("--entrar", "jogo", "--dono", str(os.getpid()))
        self.run_teclas("--estado")
        self.assertEqual(teclas.detect(self.lines()), "jogo")

    def test_abrir_outro_app_recupera_a_barra_antes_de_guardar_a_base(self):
        self.write(MINHA)
        self.run_teclas("--entrar", "jogo", "--dono", self.morto())
        self.run_teclas("--entrar", "tv", "--dono", str(os.getpid()))
        self.assertEqual(teclas.detect(self.lines()), "tv")
        self.run_teclas("--sair")
        self.assertEqual(self.lines(), MINHA)   # volta para a da pessoa, não para a do jogo

    def test_sair_solta_a_barra_presa_sem_base_guardada(self):
        self.write(MINHA)
        self.run_teclas("melhorado")            # a escolha da pessoa para o dia a dia
        self.run_teclas("--entrar", "jogo", "--dono", str(os.getpid()))
        st = self.state()                       # o app morreu e levou a base junto
        st.pop("base", None)
        st.pop("dono", None)
        with open(os.path.join(self.home, ".config", "teclas", "estado.json"), "w") as f:
            json.dump(st, f)
        self.run_teclas("--sair")
        self.assertEqual(teclas.detect(self.lines()), "melhorado")

    def test_sair_respeita_a_barra_do_jogo_escolhida_a_mao(self):
        self.write(MINHA)
        self.run_teclas("jogo")                 # a pessoa quis a barra do jogo no dia a dia
        self.run_teclas("--sair")
        self.assertEqual(teclas.detect(self.lines()), "jogo")

    def test_sair_sem_barra_de_app_na_tela_nao_mexe_em_nada(self):
        self.write(MINHA)
        self.run_teclas("--sair")
        self.assertEqual(self.lines(), MINHA)
        self.assertFalse(os.path.exists(self.reloads))

    def test_sair_repetido_nao_muda_mais_nada(self):
        self.write(MINHA)
        self.run_teclas("--entrar", "jogo", "--dono", str(os.getpid()))
        self.run_teclas("--sair")
        depois = self.lines()
        self.run_teclas("--sair")
        self.assertEqual(self.lines(), depois)

    def test_entrar_sem_dono_continua_funcionando(self):
        self.write(MINHA)
        self.run_teclas("--entrar", "jogo")     # versão antiga do td, sem --dono
        self.assertEqual(teclas.detect(self.lines()), "jogo")
        self.assertNotIn("dono", self.state())
        self.run_teclas("--sair")
        self.assertEqual(self.lines(), MINHA)

    def test_escolha_da_pessoa_fica_guardada_para_a_volta(self):
        self.write(MINHA)
        self.run_teclas("melhorado")
        self.assertEqual(self.state().get("escolha"), "melhorado")
        self.run_teclas("tv")
        self.assertEqual(self.state().get("escolha"), "tv")

    def test_dono_zumbi_conta_como_morto(self):
        """Morreu mas o pai ainda não o recolheu: a barra dele tem de voltar."""
        import signal
        filho = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
        try:
            self.write(MINHA)
            self.run_teclas("--entrar", "jogo", "--dono", str(filho.pid))
            filho.send_signal(signal.SIGKILL)
            for _ in range(100):               # espera virar zumbi (sem dar wait: o pai sou eu)
                if teclas._proc(filho.pid)[0] == "Z":
                    break
                time.sleep(0.05)
            self.assertEqual(teclas._proc(filho.pid)[0], "Z", "não virou zumbi")
            self.run_teclas("--estado")
            self.assertEqual(self.lines(), MINHA)
        finally:
            filho.wait(timeout=30)

    def test_outro_processo_com_o_mesmo_numero_nao_segura_a_barra(self):
        """O Android reaproveita PID: número igual, processo diferente, dono morto."""
        self.write(MINHA)
        self.run_teclas("--entrar", "jogo", "--dono", str(os.getpid()))
        st = self.state()
        st["dono_inicio"] = str(int(st["dono_inicio"]) + 100000)   # como se fosse outro processo
        with open(os.path.join(self.home, ".config", "teclas", "estado.json"), "w") as f:
            json.dump(st, f)
        self.run_teclas("--estado")
        self.assertEqual(self.lines(), MINHA)

    def test_fora_do_termux_nao_mexe_no_arquivo(self):
        self.write(MINHA)
        self.run_teclas("--entrar", "jogo", "--dono", self.morto(), termux=False)
        self.assertEqual(self.lines(), MINHA)


class TestLinhaDeComando(Base):
    def test_ajuda_versao_lista(self):
        self.assertIn("teclas <perfil>", self.run_teclas("--ajuda").stdout)
        with open(os.path.join(os.path.dirname(SRC), "VERSION")) as f:
            self.assertEqual(self.run_teclas("--versao").stdout.strip(), f.read().strip())
        out = self.run_teclas("--lista").stdout
        for name in ("melhorado", "jogo", "tv", "padrao", "original"):
            self.assertIn(name, out)

    def test_sem_terminal_mostra_a_ajuda(self):
        r = self.run_teclas()
        self.assertEqual(r.returncode, 0)
        self.assertIn("Uso:", r.stdout)


if __name__ == "__main__":
    unittest.main()
