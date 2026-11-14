"""Fluxo HTTP real em localhost, com transporte Gemini simulado."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread
from unittest import TestCase
from urllib import error, request
from http.server import ThreadingHTTPServer
from app import Rotas
from servico import ServicoCurricular
from rag.search import BuscaCurricular
from test_contratos import FIXTURE
from test_gemini import gerador, respostas_validas, envelope


class RotasSilenciosas(Rotas):
    def log_message(self, *args):
        pass


class TestHTTP(TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.servidor = ThreadingHTTPServer(("127.0.0.1", 0), RotasSilenciosas)
        self.servidor.servico = ServicoCurricular(BuscaCurricular(), Path(self.temp.name) / "teste.sqlite3")
        self.thread = Thread(target=self.servidor.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.fechar)
        self.base = f"http://127.0.0.1:{self.servidor.server_port}"

    def fechar(self):
        self.servidor.shutdown()
        self.servidor.server_close()
        self.thread.join()

    def api(self, rota, dados=None):
        req = request.Request(self.base + rota, data=json.dumps(dados).encode() if dados is not None else None,
                              headers={"Content-Type": "application/json"})
        try:
            resposta = request.urlopen(req, timeout=5)
        except error.HTTPError as e:
            resposta = e
        with resposta:
            return resposta.status, json.load(resposta)

    def consultar_confirmar(self):
        status, consulta = self.api("/api/consultas", {"consulta": "tema", "contexto": FIXTURE["entrada"]["contexto"]})
        self.assertEqual(status, 201)
        rota = f"/api/consultas/{consulta['id']}"
        self.assertEqual(self.api(rota + "/confirmar", {"codigo": "EF08CO03"})[0], 200)
        return rota

    def test_gemini_ate_aprovacao_humana(self):
        pipeline, transporte = gerador(respostas_validas())
        self.servidor.servico.gerador = pipeline
        rota = self.consultar_confirmar()
        status, consulta = self.api(rota + "/gerar", {})
        self.assertEqual(status, 201)
        geracao = consulta["geracao_atual"]
        self.assertEqual(geracao["estado"], "rascunho")
        self.assertEqual(geracao["resultado"]["plano"], FIXTURE["plano_esperado"])
        self.assertEqual(len(transporte.pedidos), 5)
        status, consulta = self.api(f"/api/geracoes/{geracao['id']}/aprovar", {})
        self.assertEqual(status, 200)
        self.assertEqual(consulta["geracao_atual"]["estado"], "aprovado")
        self.assertEqual(self.api(rota + "/gerar", {})[0], 409)

    def test_falha_visivel_e_nova_tentativa(self):
        pipeline, _ = gerador([envelope({}), envelope({})] + respostas_validas())
        self.servidor.servico.gerador = pipeline
        rota = self.consultar_confirmar()
        self.assertEqual(self.api(rota + "/gerar", {})[0], 502)
        status, consulta = self.api(rota)
        self.assertEqual(status, 200)
        falha = consulta["geracao_atual"]
        self.assertEqual(falha["estado"], "falha")
        self.assertEqual(len(falha["resultado"]["rastreio"]), 2)
        self.assertNotIn("plano", falha["resultado"])
        self.assertEqual(self.api(f"/api/geracoes/{falha['id']}/aprovar", {})[0], 409)
        status, consulta = self.api(rota + "/gerar", {})
        self.assertEqual(status, 201)
        self.assertEqual(consulta["geracao_atual"]["revisao"], 2)
