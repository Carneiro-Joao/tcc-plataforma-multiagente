"""Regressões da escolha curricular. Execute a partir de aula-ia-backend."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, skipUnless
import os

from rag.search import BuscaCurricular
from servico import ErroConsulta, ServicoCurricular

CONTEXTO = dict(ano="8º ano", tema="quero ensinar ordenação", duracao_min=50,
                recursos="papel e cartões", tipo="Computação desplugada")


class TestFluxo(TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.path = Path(temp.name) / "consulta.sqlite3"
        self.servico = ServicoCurricular(BuscaCurricular(), self.path)

    def consultar(self, modo="tema", **mudancas):
        return self.servico.consultar({"contexto": {**CONTEXTO, **mudancas}, "consulta": modo})

    def test_consulta_e_contrato(self):
        consulta = self.consultar()
        self.assertIsNone(consulta["entrada_geracao"])
        primeiro = consulta["resultados"][0]["habilidade"]
        self.assertEqual(primeiro["codigo"], "EF08CO03")
        self.assertEqual(primeiro["habilidade"], "Utilizar algoritmos clássicos de manipulação sobre listas.")
        self.assertEqual(primeiro["referencia"]["pagina_exemplos"], 53)
        self.assertEqual(primeiro["referencia"]["pagina_habilidade"], 52)
        self.assertIsNone(consulta["resultados"][0]["pontuacao"]["score_semantico"])
        id_ = consulta["id"]
        confirmado = self.servico.confirmar(id_, "EF08CO03")
        self.assertEqual(confirmado["entrada_geracao"]["contexto"], CONTEXTO)
        self.assertEqual(confirmado["entrada_geracao"]["habilidade"], primeiro)
        self.assertEqual(confirmado, ServicoCurricular(BuscaCurricular(), self.path).obter(id_))

    def test_catalogo_manual(self):
        consulta = self.consultar("catalogo")
        self.assertEqual(len(consulta["resultados"]), 11)
        dado = self.servico.confirmar(consulta["id"], "EF08CO09")["entrada_geracao"]
        self.assertEqual(dado["habilidade"]["codigo"], "EF08CO09")
        self.assertEqual(dado["habilidade"]["referencia"]["pagina_habilidade"], 54)

    def test_invalido(self):
        for dados in [dict(ano="9º ano"), dict(tema=" "), dict(recursos=""), dict(tipo=""),
                      dict(duracao_min=0), dict(duracao_min=True), dict(duracao_min=1.5)]:
            with self.subTest(dados=dados), self.assertRaises(ErroConsulta) as erro:
                self.consultar(**dados)
            self.assertEqual(erro.exception.status, 422)

    def test_sem_resultados(self):
        self.assertEqual(self.consultar(tema="zzzzzz")["resultados"], [])

    def test_so_confirma_candidato_retornado(self):
        consulta = self.consultar()
        for codigo in ["inventada", "EF08CO09"]:
            with self.subTest(codigo=codigo), self.assertRaises(ErroConsulta) as erro:
                self.servico.confirmar(consulta["id"], codigo)
            self.assertEqual(erro.exception.status, 422)
        self.assertIsNone(self.servico.obter(consulta["id"])["entrada_geracao"])

    def test_repeticao_e_concorrencia(self):
        consulta = self.consultar("catalogo")
        id_ = consulta["id"]

        def executar(codigo):
            try:
                return self.servico.confirmar(id_, codigo)["entrada_geracao"]["habilidade"]["codigo"]
            except ErroConsulta as erro:
                return erro.status

        with ThreadPoolExecutor(2) as pool:
            saidas = list(pool.map(executar, ["EF08CO01", "EF08CO02"]))
        vencedor = self.servico.obter(id_)["entrada_geracao"]["habilidade"]["codigo"]
        self.assertCountEqual(saidas, [vencedor, 409])
        self.assertEqual(executar(vencedor), vencedor)

    def test_outra_consulta_nao_altera_a_primeira(self):
        c1 = self.consultar()
        self.servico.confirmar(c1["id"], "EF08CO03")
        c2 = self.consultar(tema="privacidade", recursos="quadro")
        self.assertNotEqual(c1["id"], c2["id"])
        self.assertIsNone(c2["entrada_geracao"])
        self.assertEqual(self.servico.obter(c1["id"])["entrada_geracao"]["contexto"], CONTEXTO)


@skipUnless(os.environ.get("TESTAR_HIBRIDO") == "1", "Ative TESTAR_HIBRIDO=1 para carregar o modelo.")
class TestRankingOriginal(TestCase):
    def test_modelo_e_embeddings_anexados(self):
        busca = BuscaCurricular("hibrido")
        resultados = busca.buscar(CONTEXTO["tema"])
        self.assertEqual([r["codigo"] for r in resultados],
                         ["EF08CO03", "EF08CO11", "EF08CO01", "EF08CO04", "EF08CO02"])
        self.assertAlmostEqual(resultados[0]["score_semantico"], 0.3898, delta=0.00015)
        self.assertAlmostEqual(resultados[0]["score_final"], 0.7398, delta=0.00015)
