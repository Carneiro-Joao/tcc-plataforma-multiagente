import contextlib
import io
from pathlib import Path
import sys
import tempfile
import textwrap
import unittest
from unittest import mock

import relatorio_testes as rt

SUITE_FALSA = {
    "test_passa.py": """
        import unittest
        class A(unittest.TestCase):
            def test_um(self): self.assertTrue(True)
            def test_dois(self):
                "Descrição curta."
                self.assertEqual(1, 1)
    """,
    "test_problemas.py": """
        import unittest
        class B(unittest.TestCase):
            def test_falha(self): self.assertEqual("<b>x</b>", "y")
            def test_erro(self): raise RuntimeError("boom")
            @unittest.skip("sem motivo")
            def test_ignorado(self): pass
            @unittest.expectedFailure
            def test_esperada(self): self.fail()
            @unittest.expectedFailure
            def test_inesperado(self): pass
            def test_sub(self):
                for i in range(2):
                    with self.subTest(i=i):
                        self.assertEqual(i, 0)
    """,
    "test_quebrado.py": "import modulo_que_nao_existe_xyz\n",
}


def montar(arquivos):
    pasta = tempfile.TemporaryDirectory()
    for nome, corpo in arquivos.items():
        Path(pasta.name, nome).write_text(textwrap.dedent(corpo), encoding="utf-8")
    return pasta


class RelatorioTestes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pasta = montar(SUITE_FALSA)
        cls.dados = rt.executar(cls.pasta.name)
        cls.por_metodo = {r["metodo"]: r for r in cls.dados["registros"]}

    @classmethod
    def tearDownClass(cls):
        cls.pasta.cleanup()

    def test_status_de_cada_tipo(self):
        esperado = {"test_um": "ok", "test_dois": "ok", "test_falha": "falha", "test_erro": "erro",
                    "test_ignorado": "ignorado", "test_esperada": "falha_esperada",
                    "test_inesperado": "sucesso_inesperado", "test_sub": "falha"}
        for metodo, status in esperado.items():
            with self.subTest(metodo):
                self.assertEqual(self.por_metodo[metodo]["status"], status)

    def test_contagem_total(self):
        c = self.dados["contagem"]
        self.assertEqual(self.dados["total"], 9)
        self.assertEqual((c["ok"], c["falha"], c["erro"], c["ignorado"], c["falha_esperada"], c["sucesso_inesperado"]),
                         (2, 2, 2, 1, 1, 1))  # 2 falhas = test_falha+test_sub; 2 erros = test_erro + import quebrado
        self.assertEqual(sum(c.values()), self.dados["total"])

    def test_subteste_falho_registra_detalhe(self):
        r = self.por_metodo["test_sub"]
        self.assertEqual(len(r["subtestes"]), 1)
        self.assertIn("i=1", r["detalhe"])

    def test_descricao_curta_capturada(self):
        self.assertEqual(self.por_metodo["test_dois"]["descricao"], "Descrição curta.")

    def test_modulo_nao_importavel_fica_visivel(self):
        quebrado = [r for r in self.dados["registros"] if r["modulo"].startswith("test_quebrado")]
        self.assertEqual(len(quebrado), 1)
        self.assertEqual(quebrado[0]["classe"], "Falha ao importar")
        self.assertEqual(quebrado[0]["status"], "erro")
        self.assertIn("modulo_que_nao_existe_xyz", quebrado[0]["detalhe"])

    def test_nao_aprovado_com_problemas(self):
        self.assertFalse(rt.aprovado(self.dados))

    def test_aprovado_so_com_ok_e_ignorado(self):
        with montar({"test_a.py": SUITE_FALSA["test_passa.py"]}) as p:
            dados = rt.executar(p)
        self.assertTrue(rt.aprovado(dados))

    def test_sem_testes_nao_e_aprovado(self):
        with tempfile.TemporaryDirectory() as p:
            dados = rt.executar(p)
        self.assertEqual(dados["total"], 0)
        self.assertFalse(rt.aprovado(dados))
        self.assertIn("NENHUM TESTE EXECUTADO", rt.renderizar_html(dados))

    def test_filtro_por_texto_sem_diferenciar_maiusculas(self):
        with montar(SUITE_FALSA) as p:
            dados = rt.executar(p, "TEST_PASSA")
        self.assertEqual(dados["total"], 2)
        self.assertTrue(rt.aprovado(dados))

    def test_limpa_modulos_e_caminho(self):
        antes = list(sys.path)
        with montar({"test_zzlimpeza.py": SUITE_FALSA["test_passa.py"]}) as p:
            rt.executar(p)
        self.assertNotIn("test_zzlimpeza", sys.modules)
        self.assertEqual(sys.path, antes)

    def test_registros_de_um_teste_por_vez_com_tempo(self):
        for r in self.dados["registros"]:
            self.assertGreaterEqual(r["tempo_ms"], 0)
        ids = [r["id"] for r in self.dados["registros"]]
        self.assertEqual(len(ids), len(set(ids)))


class RenderizacaoHtml(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pasta = montar(SUITE_FALSA)
        cls.dados = rt.executar(cls.pasta.name)
        cls.html = rt.renderizar_html(cls.dados)

    @classmethod
    def tearDownClass(cls):
        cls.pasta.cleanup()

    def test_escapa_html_da_mensagem_de_falha(self):
        self.assertNotIn("<b>x</b>", self.html)
        self.assertIn("&lt;b&gt;x&lt;/b&gt;", self.html)

    def test_banner_com_problema_e_acessibilidade(self):
        self.assertIn("HÁ TESTES COM PROBLEMA", self.html)
        self.assertIn('role="status"', self.html)
        self.assertIn('lang="pt-BR"', self.html)
        self.assertIn('aria-label="Buscar teste"', self.html)
        self.assertIn("prefers-color-scheme:dark", self.html)

    def test_banner_de_sucesso_menciona_ignorados(self):
        with montar({"test_a.py": SUITE_FALSA["test_problemas.py"].replace("self.assertEqual(i, 0)", "pass")
                     .replace("self.fail()", "raise AssertionError()").replace("def test_falha(self): self.assertEqual(\"<b>x</b>\", \"y\")", "def test_falha(self): pass")
                     .replace("def test_erro(self): raise RuntimeError(\"boom\")", "def test_erro(self): pass")
                     .replace("@unittest.expectedFailure\n            def test_inesperado", "def test_inesperado")}) as p:
            dados = rt.executar(p)
        self.assertTrue(rt.aprovado(dados), dados["contagem"])
        self.assertIn("TODOS OS TESTES PASSARAM (1 ignorado)", rt.renderizar_html(dados))

    def test_sem_recursos_externos(self):
        self.assertNotIn("http://", self.html)
        self.assertNotIn("https://", self.html)
        self.assertNotIn("<link", self.html)
        self.assertNotIn("src=", self.html)

    def test_modulo_com_problema_abre_sozinho(self):
        self.assertIn('<details class="modulo" open><summary>test_problemas', self.html)
        self.assertIn('<details class="modulo"><summary>test_passa', self.html)

    def test_estrutura_equilibrada(self):
        for tag in ("details", "div", "main", "pre"):
            self.assertEqual(self.html.count(f"<{tag}"), self.html.count(f"</{tag}>"), tag)

    def test_sucesso_inesperado_conta_como_problema(self):
        with montar({"test_a.py": """
            import unittest
            class C(unittest.TestCase):
                @unittest.expectedFailure
                def test_x(self): pass
        """}) as p:
            dados = rt.executar(p)
        self.assertEqual(dados["contagem"]["sucesso_inesperado"], 1)
        self.assertFalse(rt.aprovado(dados))
        self.assertIn("HÁ TESTES COM PROBLEMA", rt.renderizar_html(dados))
        self.assertIn("test_x", rt.resumo_console(dados))

    def test_saida_dos_testes_nao_vaza_para_o_terminal(self):
        with montar({"test_a.py": """
            import unittest
            class C(unittest.TestCase):
                def test_x(self): print("RUIDO_NO_TERMINAL")
        """}) as p:
            saida = io.StringIO()
            with contextlib.redirect_stdout(saida):
                rt.executar(p)
        self.assertNotIn("RUIDO_NO_TERMINAL", saida.getvalue())

    def test_humanizar(self):
        self.assertEqual(rt.humanizar("test_valida_plano_ok"), "Valida plano ok")


class LinhaDeComando(unittest.TestCase):
    def rodar(self, *args):
        saida = io.StringIO()
        with contextlib.redirect_stdout(saida), contextlib.redirect_stderr(io.StringIO()):
            codigo = rt.main(list(args))
        return codigo, saida.getvalue()

    def test_codigo_0_e_arquivo_gravado(self):
        with montar({"test_a.py": SUITE_FALSA["test_passa.py"]}) as p, tempfile.TemporaryDirectory() as d:
            alvo = Path(d, "sub", "r.html")
            with mock.patch.object(rt.webbrowser, "open") as abrir:
                codigo, saida = self.rodar("--pasta-testes", p, "--saida", str(alvo), "--sem-abrir")
            self.assertEqual(codigo, 0)
            self.assertTrue(alvo.read_text(encoding="utf-8").startswith("<!doctype html>"))
            abrir.assert_not_called()
            self.assertIn("RESULTADO: OK", saida)

    def test_codigo_1_com_falhas(self):
        with montar(SUITE_FALSA) as p, tempfile.TemporaryDirectory() as d:
            codigo, saida = self.rodar("--pasta-testes", p, "--saida", str(Path(d, "r.html")), "--sem-abrir")
        self.assertEqual(codigo, 1)
        self.assertIn("COM PROBLEMAS", saida)

    def test_codigo_2_sem_testes_e_pasta_inexistente(self):
        with tempfile.TemporaryDirectory() as p, tempfile.TemporaryDirectory() as d:
            self.assertEqual(self.rodar("--pasta-testes", p, "--saida", str(Path(d, "r.html")), "--sem-abrir")[0], 2)
        self.assertEqual(self.rodar("--pasta-testes", "/nao/existe/xyz")[0], 2)

    def test_nao_sobrescreve_relatorio_existente(self):
        with montar({"test_a.py": SUITE_FALSA["test_passa.py"]}) as p, tempfile.TemporaryDirectory() as d:
            alvo = Path(d, "r.html")
            alvo.write_text("ORIGINAL", encoding="utf-8")
            codigo, _ = self.rodar("--pasta-testes", p, "--saida", str(alvo), "--sem-abrir")
            self.assertEqual(codigo, 2)
            self.assertEqual(alvo.read_text(encoding="utf-8"), "ORIGINAL")

    def test_abre_navegador_quando_pedido(self):
        with montar({"test_a.py": SUITE_FALSA["test_passa.py"]}) as p, tempfile.TemporaryDirectory() as d:
            with mock.patch.object(rt.webbrowser, "open") as abrir:
                self.rodar("--pasta-testes", p, "--saida", str(Path(d, "r.html")))
            abrir.assert_called_once()
            self.assertTrue(abrir.call_args[0][0].startswith("file:"))

    def test_resumo_lista_problemas(self):
        with montar(SUITE_FALSA) as p:
            texto = rt.resumo_console(rt.executar(p))
        self.assertIn("test_falha", texto)
        self.assertIn("Testes: 9", texto)


if __name__ == "__main__":
    unittest.main()
