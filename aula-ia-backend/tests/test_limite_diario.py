"""Limite diário de gerações com IA (servico.gerar e app --limite-diario). Sem rede. Execute a partir de aula-ia-backend."""
from contextlib import closing, ExitStack
from copy import deepcopy
import io
import json
import os
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

import app
from rag.search import BuscaCurricular
from servico import ErroConsulta, ServicoCurricular

FIXTURE = json.loads((Path(__file__).parent / "dados/plano_v2/fixture_ordenacao.json").read_text(encoding="utf-8"))
CONTEXTO = dict(ano="8º ano", tema="ordenação", duracao_min=50, recursos="papel e cartões", tipo="Computação desplugada")


class GeradorFalso:
    """Imita o gerador: modo 'ia' ou 'demonstracao'; pode falhar como uma chamada recusada."""
    def __init__(self, modo="ia", falhar=False):
        self.modo, self.falhar, self.chamadas = modo, falhar, 0

    def gerar(self, entrada, revisao):
        from erros import ErroGeracao
        self.chamadas += 1
        if self.falhar:
            raise ErroGeracao("Gemini HTTP 429 (teste)", tipo="cota")
        return dict(plano=deepcopy(FIXTURE["plano_esperado"]), modo=self.modo, contrato="plano-aula-2.0", rastreio=[])


class TestLimiteDiario(TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.banco = Path(temp.name) / "t.sqlite3"

    def servico(self, limite, **kw):
        return ServicoCurricular(BuscaCurricular(), self.banco, GeradorFalso(**kw), limite_diario_ia=limite)

    def nova_consulta(self, s):
        c = s.consultar({"contexto": CONTEXTO, "consulta": "tema"})
        s.confirmar(c["id"], c["resultados"][0]["habilidade"]["codigo"])
        return c["id"]

    def test_bloqueia_a_partir_do_limite_sem_chamar_a_ia(self):
        s = self.servico(2)
        for _ in range(2):
            s.gerar(self.nova_consulta(s))
        with self.assertRaises(ErroConsulta) as e:
            s.gerar(self.nova_consulta(s))
        self.assertEqual(e.exception.status, 429)
        self.assertIn("Limite de 2 planos", str(e.exception))
        self.assertEqual(s.gerador.chamadas, 2)  # a 3ª nem chegou ao provedor
        self.assertEqual(s.uso_hoje(), (2, 2))

    def test_regenerar_o_mesmo_plano_tambem_conta(self):
        s = self.servico(2)
        cid = self.nova_consulta(s)
        s.gerar(cid)
        s.gerar(cid)  # "Gerar outra versão"
        with self.assertRaises(ErroConsulta):
            s.gerar(cid)

    def test_falhas_contam_porque_gastam_chamadas(self):
        s = self.servico(2, falhar=True)
        for _ in range(2):
            with self.assertRaises(ErroConsulta) as e:
                s.gerar(self.nova_consulta(s))
            self.assertEqual(e.exception.status, 502)
        with self.assertRaises(ErroConsulta) as e:
            s.gerar(self.nova_consulta(s))
        self.assertEqual(e.exception.status, 429)

    def test_geracoes_de_outro_dia_nao_contam(self):
        s = self.servico(1)
        s.gerar(self.nova_consulta(s))
        with closing(sqlite3.connect(self.banco)) as db, db:
            db.execute("UPDATE geracoes SET criado_em = datetime('now', '-2 days')")
        s.gerar(self.nova_consulta(s))  # não levanta
        self.assertEqual(s.uso_hoje()[0], 1)

    def test_demonstracao_nao_conta_nem_e_limitada(self):
        demo = self.servico(1, modo="demonstracao")
        for _ in range(3):
            demo.gerar(self.nova_consulta(demo))
        self.assertEqual(demo.uso_hoje()[0], 0)
        ia = self.servico(1)  # mesmo banco: as 3 de demonstração não ocupam a cota da IA
        ia.gerar(self.nova_consulta(ia))

    def test_cota_da_ia_esgotada_nao_bloqueia_a_demonstracao(self):
        ia = self.servico(1)
        ia.gerar(self.nova_consulta(ia))
        demo = self.servico(1, modo="demonstracao")
        demo.gerar(self.nova_consulta(demo))  # não levanta: demonstração não usa a API

    def test_sem_limite_quando_none(self):
        s = self.servico(None)
        for _ in range(4):
            s.gerar(self.nova_consulta(s))
        self.assertEqual(s.uso_hoje(), (4, None))


class TestOpcaoDoApp(TestCase):
    def setUp(self):
        self.ctx = ExitStack()
        self.addCleanup(self.ctx.close)
        self.ctx.enter_context(patch.dict(os.environ, {"GEMINI_API_KEY": "chave-ficticia-do-teste"}, clear=True))
        self.saida = self.ctx.enter_context(patch("sys.stdout", new_callable=io.StringIO))
        self.servico = self.ctx.enter_context(patch("app.ServicoCurricular"))
        self.servico.return_value.uso_hoje.return_value = (3, 8)
        servidor = self.ctx.enter_context(patch("app.ThreadingHTTPServer")).return_value
        servidor.server_port = 8000
        servidor.serve_forever.side_effect = KeyboardInterrupt()

    def limite_passado(self, argv):
        app.main(argv)
        return self.servico.call_args.kwargs["limite_diario_ia"]

    def test_padrao_8_com_ia_e_aviso_ao_iniciar(self):
        self.assertEqual(self.limite_passado(["--gerador", "ia"]), 8)
        self.assertIn("Limite: 8 planos com IA por dia; usados hoje: 3.", self.saida.getvalue())

    def test_valor_escolhido_e_zero_desliga(self):
        self.assertEqual(self.limite_passado(["--gerador", "ia", "--limite-diario", "8"]), 8)
        self.assertIsNone(self.limite_passado(["--gerador", "ia", "--limite-diario", "0"]))
        self.assertIn("DESLIGADO", self.saida.getvalue())

    def test_demonstracao_nao_recebe_limite(self):
        self.assertIsNone(self.limite_passado(["--gerador", "demonstracao"]))

    def test_negativo_e_recusado(self):
        with patch("sys.stderr", new_callable=io.StringIO), self.assertRaises(SystemExit):
            app.main(["--gerador", "ia", "--limite-diario", "-1"])
