"""Testes do incremento de geração e aprovação docente (sem acesso à internet)."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from geracao import GeradorDePlano, ErroGeracao, distribuicao_tempo
from rag.search import BuscaCurricular
from servico import ErroConsulta, ServicoCurricular

CONTEXTO = dict(ano="8º ano", tema="quero ensinar ordenação", duracao_min=50,
                recursos="papel e cartões", tipo="Computação desplugada")


class TestGeracao(TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.db = Path(temp.name) / "test.sqlite3"
        self.servico = ServicoCurricular(BuscaCurricular(), self.db)
        self.consulta = self.servico.consultar({"consulta": "tema", "contexto": CONTEXTO})
        self.id = self.consulta["id"]

    def confirmar(self):
        return self.servico.confirmar(self.id, "EF08CO03")

    def test_impede_geracao_sem_confirmacao(self):
        with self.assertRaises(ErroConsulta) as ctx:
            self.servico.gerar(self.id)
        self.assertEqual(ctx.exception.status, 409)
        self.assertIsNone(self.servico.obter(self.id)["geracao_atual"])

    def test_gera_plano_com_tempo_exato_e_rastreio(self):
        self.confirmar()
        consulta = self.servico.gerar(self.id)
        geracao = consulta["geracao_atual"]
        self.assertEqual(geracao["estado"], "rascunho")
        resultado = geracao["resultado"]
        self.assertEqual(resultado["modo"], "demonstracao")
        self.assertEqual(resultado["plano"]["habilidade_codigo"], "EF08CO03")
        self.assertEqual(sum(e["minutos"] for e in resultado["plano"]["etapas"]), 50)
        self.assertEqual([r["agente"] for r in resultado["rastreio"]], list(GeradorDePlano.ORDEM))
        self.assertEqual(self.servico.obter(self.id)["geracao_atual"], geracao)
        self.assertEqual(ServicoCurricular(BuscaCurricular(), self.db).obter(self.id)["geracao_atual"], geracao)

    def test_regenerar_modifica_roteiro_sem_alterar_habilidade(self):
        self.confirmar()
        primeiro = self.servico.gerar(self.id)["geracao_atual"]
        segundo = self.servico.gerar(self.id)["geracao_atual"]
        self.assertEqual(segundo["revisao"], 2)
        self.assertNotEqual(primeiro["id"], segundo["id"])
        self.assertNotEqual(primeiro["resultado"]["plano"]["etapas"], segundo["resultado"]["plano"]["etapas"])
        self.assertEqual(segundo["resultado"]["plano"]["habilidade_codigo"], "EF08CO03")
        with self.assertRaises(ErroConsulta) as ctx:
            self.servico.aprovar(primeiro["id"])
        self.assertEqual(ctx.exception.status, 409)

    def test_aprovar_humanamente_e_bloquear_regeneracao(self):
        self.confirmar()
        geracao = self.servico.gerar(self.id)["geracao_atual"]
        aprovado = self.servico.aprovar(geracao["id"])["geracao_atual"]
        self.assertEqual(aprovado["estado"], "aprovado")
        self.assertEqual(self.servico.aprovar(geracao["id"])["geracao_atual"], aprovado)
        with self.assertRaises(ErroConsulta) as ctx:
            self.servico.gerar(self.id)
        self.assertEqual(ctx.exception.status, 409)

    def test_gera_com_duracoes_curtas(self):
        for total in [1, 2, 3, 4, 5, 11, 50, 51, 60, 1440]:
            with self.subTest(total=total):
                self.assertEqual(sum(distribuicao_tempo(total)), total)
                self.assertTrue(all(n >= 1 for n in distribuicao_tempo(total)))

    def test_falha_registrada_sem_aprovar_geracao_invalida(self):
        class Invalido:
            def gerar(self, entrada, revisao):
                raise ErroGeracao("Falha de validação de saída")
        self.confirmar()
        servico = ServicoCurricular(BuscaCurricular(), self.db, gerador=Invalido())
        with self.assertRaises(ErroConsulta) as ctx:
            servico.gerar(self.id)
        self.assertEqual(ctx.exception.status, 502)
        falha = servico.obter(self.id)["geracao_atual"]
        self.assertEqual(falha["estado"], "falha")
        self.assertNotIn("plano", falha["resultado"])
        with self.assertRaises(ErroConsulta):
            servico.aprovar(falha["id"])
        self.assertEqual(self.servico.gerar(self.id)["geracao_atual"]["revisao"], 2)

    def test_aprovacao_de_id_inexistente(self):
        with self.assertRaises(ErroConsulta) as ctx:
            self.servico.aprovar("0" * 32)
        self.assertEqual(ctx.exception.status, 404)

    def test_concorrencia_em_geracao(self):
        import threading
        entrou = threading.Event()
        liberar = threading.Event()
        class Lento:
            def gerar(self, entrada, revisao):
                entrou.set()
                liberar.wait(3)
                return GeradorDePlano().gerar(entrada, revisao)
        self.confirmar()
        servico = ServicoCurricular(BuscaCurricular(), self.db, gerador=Lento())
        with ThreadPoolExecutor(max_workers=2) as pool:
            tarefa = pool.submit(servico.gerar, self.id)
            self.assertTrue(entrou.wait(3))
            with self.assertRaises(ErroConsulta) as ctx:
                servico.gerar(self.id)
            self.assertEqual(ctx.exception.status, 409)
            liberar.set()
            self.assertEqual(tarefa.result()["geracao_atual"]["estado"], "rascunho")
