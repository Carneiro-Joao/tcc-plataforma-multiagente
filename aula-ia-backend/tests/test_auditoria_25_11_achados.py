"""Correções da auditoria de 25/11/2026, segunda parte (C1, C4, C5, C9). Sem rede. Execute a partir de aula-ia-backend."""
from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
import io
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import threading
import time
from unittest import TestCase
from unittest.mock import patch

import acentuacao
import app
import gemini
import gerar_lote
import servico
import teste_gemini
from erros import ErroGeracao
from geracao_v2 import AgenteGeminiCompleto, GeradorDePlanoCompleto
from juiz_servico import JuizDemonstracao
from test_gemini import CHAVE, Transporte, envelope
from test_juiz_integrado import Base, FAVORAVEL, GeradorFalso, UMA_GRAVE
from test_poc10 import ADAPTACAO_SEM_ACENTO, FIXTURE, SAIDAS, gerar, normais


class TestC1ReescritaSoMudaTextos(TestCase):
    """C1: a reescrita de acentuação só é aceita se IDs, números, vínculos e estrutura ficarem iguais aos da saída original."""

    def test_esqueleto_ignora_textos_e_acentos_mas_ve_ids_numeros_e_listas(self):
        a = {"id": "ET1", "titulo": "Introducao", "minutos": 10, "descricao": "A explicacao do professor.", "ids": ["OBJ1"]}
        self.assertTrue(acentuacao.mesma_estrutura(a, dict(a, titulo="Introdução", descricao="Outra explicação, bem diferente.")))
        for mudanca in ({"id": "ET2"}, {"minutos": 15}, {"ids": ["OBJ2"]}, {"ids": ["OBJ1", "OBJ2"]}, {"titulo": "Abertura"}):
            with self.subTest(mudanca=mudanca):
                self.assertFalse(acentuacao.mesma_estrutura(a, dict(a, **mudanca)))
        self.assertFalse(acentuacao.mesma_estrutura(a, {k: v for k, v in a.items() if k != "minutos"}))
        self.assertFalse(acentuacao.mesma_estrutura(a, dict(a, extra="x")))

    def test_reescrita_valida_que_muda_vinculos_e_descartada(self):
        mudada = deepcopy(SAIDAS["adaptacao"])  # acentuada (melhora a acentuação) mas com um vínculo a menos
        mudada["adaptacoes"][0]["objetivos_ids"] = ["OBJ1"]
        # a mudança passa no validador do contrato: sem a regra C1 a reescrita seria aceita
        GeradorDePlanoCompleto("demonstracao").validar_etapa("adaptacao", mudada, FIXTURE["entrada"],
                                                             {n: SAIDAS[n] for n in SAIDAS if n != "adaptacao"})
        resultado, t = gerar(normais() + [envelope(ADAPTACAO_SEM_ACENTO), envelope(mudada)])
        self.assertEqual(len(t.pedidos), 7)
        self.assertEqual(resultado["plano"]["adaptacoes"], ADAPTACAO_SEM_ACENTO["adaptacoes"])
        reg = [r for r in resultado["rastreio"] if r.get("tentativa") == "acentuacao"]
        self.assertEqual([r["estado"] for r in reg], ["descartado"])
        self.assertIn("IDs, números, vínculos ou estrutura", reg[0]["motivo"])

    def test_reescrita_que_so_acentua_continua_aceita(self):
        resultado, _ = gerar(normais() + [envelope(ADAPTACAO_SEM_ACENTO), envelope(SAIDAS["adaptacao"])])
        self.assertEqual(resultado["plano"]["adaptacoes"], SAIDAS["adaptacao"]["adaptacoes"])


class GeradorLento(GeradorFalso):
    """Durante a geração, envelhece `atualizado_em` do pedido e espera: o batimento tem de renová-lo."""

    def __init__(self, banco):
        super().__init__()
        self.banco, self.visto = banco, None

    def gerar(self, entrada, revisao, revisoes=None):
        with servico.abrir_banco(self.banco) as db:
            db.execute("UPDATE pedidos SET atualizado_em = '2000-01-01 00:00:00'")
        prazo = time.monotonic() + 3
        while time.monotonic() < prazo:
            with servico.abrir_banco(self.banco) as db:
                self.visto = db.execute("SELECT atualizado_em FROM pedidos").fetchone()[0]
            if self.visto != "2000-01-01 00:00:00":
                break
            time.sleep(0.02)
        return super().gerar(entrada, revisao, revisoes)


class TestC4BatimentoDoPedido(Base):
    """C4: pedido lento mas vivo não pode aparecer como "interrompido" nem liberar um 2º pedido em paralelo."""

    def test_geracao_lenta_tem_atualizado_em_renovado(self):
        with patch.object(servico, "BATIMENTO_S", 0.05):
            s = self.servico([FAVORAVEL], gerador=GeradorLento(self.banco))
            r = s.gerar(self.pedido(s))
        self.assertNotEqual(self.gerador.visto, "2000-01-01 00:00:00")
        self.assertEqual(r["pedido_atual"]["estado"], "pronto")

    def test_batimento_para_no_fim_e_nao_reabre_pedido_pronto(self):
        with patch.object(servico, "BATIMENTO_S", 0.02):
            s = self.servico([FAVORAVEL])
            s.gerar(self.pedido(s))
            self.assertFalse([t for t in threading.enumerate() if t.name.startswith("batimento-")])
        self.assertEqual(self.linhas("SELECT estado FROM pedidos"), [("pronto",)])

    def test_pedido_sem_batimento_continua_interrompido_depois_de_15_min(self):
        s = self.servico([FAVORAVEL])
        cid = self.pedido(s)
        s.gerar(cid)
        with servico.abrir_banco(self.banco) as db:
            db.execute("UPDATE pedidos SET estado = 'gerando', atualizado_em = datetime('now', '-16 minutes')")
        self.assertEqual(s.obter(cid)["pedido_atual"]["estado"], "interrompido")


class TestC5DemonstracaoNaoInformaRegeneracao(Base):
    """C5: o parecer de demonstração é de outro plano; a regeneração não pode mandar as críticas dele ao gerador."""

    def test_juiz_de_demonstracao_regenera_sem_criticas_e_registra_o_motivo(self):
        s = self.servico(juiz=JuizDemonstracao())
        r = s.gerar(self.pedido(s))
        self.assertEqual(self.gerador.revisoes_recebidas, [None, None])
        reg = [h for h in r["pedido_atual"]["historico"] if h["evento"] == "regenerando"]
        self.assertEqual((reg[0]["modo"], reg[0]["criticas_usadas"], reg[0]["motivo"]),
                         ("cega", [], servico.MOTIVO_CEGA_DEMONSTRACAO))

    def test_juiz_real_continua_informando(self):
        s = self.servico([UMA_GRAVE, FAVORAVEL])
        r = s.gerar(self.pedido(s))
        self.assertIsNotNone(self.gerador.revisoes_recebidas[1])
        reg = [h for h in r["pedido_atual"]["historico"] if h["evento"] == "regenerando"]
        self.assertEqual(reg[0]["modo"], "informada")
        self.assertNotIn("motivo", reg[0])


class TestC9PadraoDe503(TestCase):
    """C9: a classe repete HTTP 503 como o site (2); só a sondagem de terminal desliga de propósito."""

    def test_classe_app_e_lote_usam_o_mesmo_padrao(self):
        self.assertEqual(gemini.REPETICOES_503_PADRAO, 2)
        self.assertEqual(AgenteGeminiCompleto(chave=CHAVE).repeticoes_503, 2)
        self.assertEqual(gemini.AgenteGemini(chave=CHAVE).repeticoes_503, 2)
        with patch.dict(os.environ, {"GEMINI_API_KEY": CHAVE}):
            self.assertEqual(GeradorDePlanoCompleto("ia").agente.repeticoes_503, 2)
        self.assertIs(app.REPETICOES_503_PADRAO, gemini.REPETICOES_503_PADRAO)
        self.assertIs(gerar_lote.REPETICOES_503_PADRAO, gemini.REPETICOES_503_PADRAO)

    def test_app_sem_opcao_repete_503_duas_vezes(self):
        class Falso:
            server_port = 0

            def __init__(self, *a):
                pass

            def serve_forever(self):
                Falso.servico = self.servico

            def server_close(self):
                pass
        ambiente = {k: v for k, v in os.environ.items() if k != "GROQ_API_KEY"} | {"GEMINI_API_KEY": CHAVE}
        with TemporaryDirectory() as d, patch.dict(os.environ, ambiente, clear=True), \
                patch.object(app, "ThreadingHTTPServer", Falso), redirect_stdout(io.StringIO()):
            app.main(["--gerador", "ia", "--banco", str(Path(d) / "a.sqlite3")])
        self.assertEqual(Falso.servico.gerador.agente.repeticoes_503, 2)

    def test_sondagem_de_terminal_continua_sem_repetir(self):
        recebidos = []

        def agente_falso(*a, **kw):
            recebidos.append(kw)
            raise ErroGeracao("parar aqui", tipo="configuracao")
        with patch.object(teste_gemini, "AgenteGeminiCompleto", agente_falso), redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()), \
                self.assertRaises(SystemExit):
            teste_gemini.main([])
        self.assertEqual(recebidos[0]["repeticoes_503"], 0)
