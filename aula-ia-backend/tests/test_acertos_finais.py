"""Acertos finais da PoC 08 (Fase 5): demonstração sem cartões fora dos recursos, código de erro do tema,
credencial no ensaio_juiz exportar e alerta habilidade × recursos. Sem rede. Execute a partir de aula-ia-backend."""
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread
from unittest import TestCase
from unittest.mock import patch
from urllib import error, request
from http.server import ThreadingHTTPServer

import ensaio_juiz
from app import Rotas
from geracao_v2 import GeradorDePlanoCompleto
from rag.search import BuscaCurricular
from servico import ErroConsulta, ServicoCurricular, alertas_recursos

CONTEXTO = dict(ano="8º ano", tema="ordenação", duracao_min=50, tipo="Aula prática", recursos="quadro e pincel")


def texto_do_plano(plano):
    return json.dumps({k: v for k, v in plano.items() if k != "recursos"}, ensure_ascii=False).lower()


class TestDemonstracaoSemCartoes(TestCase):
    def gerar(self, recursos):
        with TemporaryDirectory() as d:
            s = ServicoCurricular(BuscaCurricular(), Path(d) / "t.sqlite3", GeradorDePlanoCompleto("demonstracao"))
            c = s.consultar({"contexto": dict(CONTEXTO, recursos=recursos), "consulta": "tema"})
            s.confirmar(c["id"], "EF08CO03")
            return s.gerar(c["id"])["geracao_atual"]["resultado"]["plano"]

    def test_sem_cartoes_nos_recursos_nao_cita_cartoes_nem_ja_preparada(self):
        for recursos in ("quadro e pincel", "material impresso", "projetor, computadores"):
            with self.subTest(recursos=recursos):
                texto = texto_do_plano(self.gerar(recursos))
                self.assertNotIn("cart", texto)
                self.assertNotIn("já preparad", texto)
                self.assertIn("lista de números", texto)

    def test_com_cartoes_nos_recursos_mantem_o_texto_antigo(self):
        for recursos in ("papel e cartões", "Cartões numerados", "cartoes"):
            with self.subTest(recursos=recursos):
                self.assertIn("cartões numerados", texto_do_plano(self.gerar(recursos)))


class TestCodigoDoErroDoTema(TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.servico = ServicoCurricular(BuscaCurricular(), Path(temp.name) / "t.sqlite3")

    def test_servico_marca_o_codigo(self):
        casos = {"quero preparar uma aula bem legal": "tema_nao_identificado", "": "tema_invalido", "x" * 801: "tema_invalido"}
        for tema, codigo in casos.items():
            with self.subTest(tema=tema[:20]), self.assertRaises(ErroConsulta) as ctx:
                self.servico.consultar({"contexto": dict(CONTEXTO, tema=tema), "consulta": "tema"})
            self.assertEqual((ctx.exception.status, ctx.exception.codigo), (422, codigo))

    def test_outros_erros_sem_codigo_de_tema(self):
        with self.assertRaises(ErroConsulta) as ctx:
            self.servico.consultar({"contexto": dict(CONTEXTO, tipo="Outro"), "consulta": "tema"})
        self.assertIsNone(ctx.exception.codigo)

    def test_http_devolve_o_codigo_no_json(self):
        class Silencioso(Rotas):
            def log_message(self, *a):
                pass
        servidor = ThreadingHTTPServer(("127.0.0.1", 0), Silencioso)
        servidor.servico = self.servico
        thread = Thread(target=servidor.serve_forever, daemon=True)
        thread.start()
        try:
            def post(contexto):
                req = request.Request(f"http://127.0.0.1:{servidor.server_port}/api/consultas", method="POST",
                                      data=json.dumps({"contexto": contexto, "consulta": "tema"}).encode(),
                                      headers={"Content-Type": "application/json"})
                try:
                    r = request.urlopen(req, timeout=5)
                except error.HTTPError as e:
                    r = e
                with r:
                    return r.status, json.load(r)
            status, corpo = post(dict(CONTEXTO, tema="quero preparar uma aula bem legal"))
            self.assertEqual((status, corpo["codigo"]), (422, "tema_nao_identificado"))
            status, corpo = post(dict(CONTEXTO, tipo="Outro"))
            self.assertEqual(status, 422)
            self.assertNotIn("codigo", corpo)
        finally:
            servidor.shutdown()
            servidor.server_close()
            thread.join()


class TestEnsaioExportarCredencial(TestCase):
    def test_exportar_recusa_chave_gemini_que_o_sanitizar_nao_conhece(self):
        caso = {"plano": {"texto": "AIza" + "x" * 35}}
        with TemporaryDirectory() as d, patch.object(ensaio_juiz, "exportar_sqlite", return_value=caso), \
                redirect_stdout(io.StringIO()) as saida:
            destino = Path(d) / "caso.json"
            codigo = ensaio_juiz.main(["exportar", "--banco", "x.sqlite3", "--geracao-id", "g", "--saida", str(destino)])
            self.assertEqual(codigo, 1)
            self.assertFalse(destino.exists())
        self.assertIn("credencial", saida.getvalue())
        self.assertNotIn("AIza", saida.getvalue())


class TestAlertaHabilidadeRecursos(TestCase):
    def consulta(self, codigo, recursos):
        return {"entrada_geracao": {"habilidade": {"codigo": codigo}, "contexto": {"recursos": recursos}}}

    def test_alerta(self):
        for codigo in ("EF08CO01", "EF08CO02"):
            with self.subTest(codigo=codigo):
                alertas = alertas_recursos(self.consulta(codigo, "material impresso"))
                self.assertEqual([a["codigo"] for a in alertas], ["habilidade_sem_computador"])
                self.assertIn(codigo, alertas[0]["mensagem"])
                self.assertEqual(alertas_recursos(self.consulta(codigo, "projetor, Computadores")), [])
        self.assertEqual(alertas_recursos(self.consulta("EF08CO03", "material impresso")), [])
        self.assertEqual(alertas_recursos({"entrada_geracao": None}), [])

    def test_alerta_aparece_na_consulta_confirmada_e_nao_bloqueia(self):
        with TemporaryDirectory() as d:
            s = ServicoCurricular(BuscaCurricular(), Path(d) / "t.sqlite3", GeradorDePlanoCompleto("demonstracao"))
            c = s.consultar({"contexto": dict(CONTEXTO, tema="programação", recursos="material impresso"), "consulta": "catalogo"})
            self.assertEqual(s.obter(c["id"])["alertas"], [])
            confirmada = s.confirmar(c["id"], "EF08CO01")
            self.assertEqual(confirmada["alertas"][0]["codigo"], "habilidade_sem_computador")
            self.assertEqual(s.gerar(c["id"])["geracao_atual"]["estado"], "rascunho")
