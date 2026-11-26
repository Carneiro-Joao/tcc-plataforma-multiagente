"""PoC 10: regeneração informada pelas críticas do Juiz + reescrita de saídas sem acentuação. Sem rede."""
from contextlib import redirect_stdout
import io
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unicodedata
from unittest import TestCase
from unittest.mock import patch
from urllib.error import HTTPError

import acentuacao
import app
import revisao_informada
import sondagem_regeneracao_informada as sondagem
from contratos import plano_v2
from geracao_v2 import AgenteGeminiCompleto, GeradorDePlanoCompleto
from test_gemini import CHAVE, Transporte, envelope
from test_juiz_integrado import Base, FAVORAVEL, UMA_GRAVE

FIXTURE = json.loads((Path(__file__).parent / "dados/plano_v2/fixture_ordenacao.json").read_text(encoding="utf-8"))
SAIDAS = FIXTURE["saidas"]


def sem_acentos(valor):
    if isinstance(valor, str):
        return "".join(c for c in unicodedata.normalize("NFD", valor) if not unicodedata.combining(c))
    if isinstance(valor, dict):
        return {k: sem_acentos(v) for k, v in valor.items()}
    if isinstance(valor, list):
        return [sem_acentos(v) for v in valor]
    return valor


ADAPTACAO_SEM_ACENTO = sem_acentos(SAIDAS["adaptacao"])  # só textos e IDs ASCII: o contrato continua válido


def gerar(respostas, **kw):
    transporte = Transporte(respostas)
    agente = AgenteGeminiCompleto(chave=CHAVE, transporte=transporte, repeticoes_503=0)
    resultado = GeradorDePlanoCompleto("ia", agente=agente, reparos=1, **kw).gerar(FIXTURE["entrada"], 1)
    return resultado, transporte


def normais(ate="adaptacao"):
    ordem = list(plano_v2.ETAPAS)
    return [envelope(SAIDAS[n]) for n in ordem[:ordem.index(ate)]]


def dados(pedido):
    return json.loads(json.loads(pedido.data.decode("utf-8"))["contents"][0]["parts"][0]["text"])


class TestDeteccaoAcentuacao(TestCase):
    def test_detecta_texto_longo_sem_acento_com_palavra_guia(self):
        self.assertEqual(acentuacao.campos_sem_acentuacao(ADAPTACAO_SEM_ACENTO), ["adaptacoes[0].descricao", "adaptacoes[1].descricao"])
        self.assertEqual(acentuacao.campos_sem_acentuacao(SAIDAS["adaptacao"]), [])
        # PoC 11 (deteccao-acentuacao-1.1): campo curto com palavra inequívoca passou a contar (na 1.0 este caso dava []).
        self.assertEqual(acentuacao.campos_sem_acentuacao({"a": "A avaliacao sera feita em duplas."}), ["a"])
        self.assertEqual(acentuacao.campos_sem_acentuacao({"a": "O aluno pratica a analise especifica."}), [])  # curto, só ambíguas
        self.assertEqual(acentuacao.campos_sem_acentuacao(
            {"a": "Os estudantes trabalham em duplas e depois apresentam as listas para toda a turma."}), [])  # sem palavra-guia
        for frase in ("A explicacao do professor ocorre durante a atividade de comparacao dos grupos.",
                      "Os alunos nao usam o quadro durante toda a atividade proposta pelo professor hoje.",
                      "A aula sera dividida em tres partes curtas e o professor acompanha todas elas hoje."):
            with self.subTest(frase=frase):
                self.assertEqual(acentuacao.campos_sem_acentuacao({"x": [{"y": frase}]}), ["x[0].y"])

    def test_texto_com_qualquer_acento_nao_conta(self):
        self.assertEqual(acentuacao.campos_sem_acentuacao(
            {"a": "A explicacao do professor ocorre durante a atividade de comparação dos grupos."}), [])


class TestReescritaDeAcentuacaoNoGerador(TestCase):
    def test_saida_sem_acento_recebe_uma_reescrita_e_a_versao_acentuada_entra_no_plano(self):
        resultado, t = gerar(normais() + [envelope(ADAPTACAO_SEM_ACENTO), envelope(SAIDAS["adaptacao"])])
        self.assertEqual(len(t.pedidos), 7)
        self.assertEqual(resultado["plano"]["adaptacoes"][0]["descricao"], SAIDAS["adaptacao"]["adaptacoes"][0]["descricao"])
        reparo = dados(t.pedidos[-1])["reparo_estrutural"]
        self.assertIn("acentuação", reparo["instrucao"])
        self.assertEqual(reparo["resposta_anterior"], ADAPTACAO_SEM_ACENTO)
        reg = [r for r in resultado["rastreio"] if r.get("tentativa") == "acentuacao"]
        self.assertEqual([(r["agente"], r["estado"]) for r in reg], [("adaptacao", "validado")])
        self.assertEqual(revisao_informada.saidas_do_rastreio(resultado["rastreio"])["adaptacao"], SAIDAS["adaptacao"])

    def test_reescrita_que_nao_melhora_mantem_a_original_e_nao_derruba(self):
        piorada = json.loads(json.dumps(ADAPTACAO_SEM_ACENTO))
        piorada["adaptacoes"][0]["descricao"] += " A explicacao continua sem acento nesta versao reescrita."
        resultado, t = gerar(normais() + [envelope(ADAPTACAO_SEM_ACENTO), envelope(piorada)])
        self.assertEqual(resultado["plano"]["adaptacoes"], ADAPTACAO_SEM_ACENTO["adaptacoes"])
        self.assertEqual([r["estado"] for r in resultado["rastreio"] if r.get("tentativa") == "acentuacao"], ["descartado"])
        # a regeneração informada usa a versão que entrou no plano, não a reescrita descartada
        self.assertEqual(revisao_informada.saidas_do_rastreio(resultado["rastreio"])["adaptacao"], ADAPTACAO_SEM_ACENTO)

    def test_falha_http_na_reescrita_mantem_a_original_e_nao_derruba(self):
        erro = HTTPError("https://x", 503, "indisponivel", {}, io.BytesIO(b'{"error":{"message":"x"}}'))
        resultado, _ = gerar(normais() + [envelope(ADAPTACAO_SEM_ACENTO), erro])
        self.assertEqual(resultado["plano"]["adaptacoes"], ADAPTACAO_SEM_ACENTO["adaptacoes"])

    def test_saidas_acentuadas_nao_geram_chamada_extra(self):
        _, t = gerar(normais() + [envelope(SAIDAS["adaptacao"])])
        self.assertEqual(len(t.pedidos), 6)

    def test_pode_ser_desligada_e_nao_roda_na_demonstracao(self):
        _, t = gerar(normais() + [envelope(ADAPTACAO_SEM_ACENTO)], corrigir_acentuacao=False)
        self.assertEqual(len(t.pedidos), 6)
        self.assertFalse(GeradorDePlanoCompleto("demonstracao").corrigir_acentuacao)
        self.assertTrue(GeradorDePlanoCompleto("ia", agente=object()).corrigir_acentuacao)


class TestRevisaoInformadaNoGerador(TestCase):
    def test_so_a_regeneracao_leva_as_criticas_e_o_prompt_de_sistema_nao_muda(self):
        parecer = {"falhas": [dict(id="F1", componente="sequencia", gravidade="maior", criterio="viabilidade",
                                   descricao="ET2 longa demais", correcao_sugerida="Dividir a ET2")]}
        rastreio = [dict(agente=n, estado="validado", saida=SAIDAS[n]) for n in plano_v2.ETAPAS]
        revisoes = revisao_informada.montar_revisoes(rastreio, parecer)
        _, t1 = gerar([envelope(SAIDAS[n]) for n in plano_v2.ETAPAS])
        transporte = Transporte([envelope(SAIDAS[n]) for n in plano_v2.ETAPAS])
        agente = AgenteGeminiCompleto(chave=CHAVE, transporte=transporte, repeticoes_503=0)
        informada = GeradorDePlanoCompleto("ia", agente=agente).gerar(FIXTURE["entrada"], 2, revisoes=revisoes)
        for nome, p1, p2 in zip(plano_v2.ETAPAS, t1.pedidos, transporte.pedidos):
            with self.subTest(nome=nome):
                self.assertNotIn("revisao_pedagogica", dados(p1))
                self.assertEqual(dados(p2)["revisao_pedagogica"], revisoes[nome])
                c1, c2 = json.loads(p1.data.decode("utf-8")), json.loads(p2.data.decode("utf-8"))
                self.assertEqual(c1["systemInstruction"], c2["systemInstruction"])
        self.assertEqual(revisoes["sequencia"]["falhas_deste_componente"][0]["correcao_sugerida"], "Dividir a ET2")
        self.assertEqual(revisoes["sequencia"]["versao_anterior"], SAIDAS["sequencia"])
        self.assertEqual(revisoes["objetivos"]["falhas_deste_componente"], [])
        self.assertEqual(len(revisoes["objetivos"]["outras_falhas"]), 1)
        self.assertEqual(sum(1 for r in informada["rastreio"] if r.get("revisao_pedagogica")), 6)

    def test_texto_e_o_mesmo_testado_na_sondagem(self):
        self.assertEqual(revisao_informada.INSTRUCAO, sondagem.INSTRUCAO)
        self.assertEqual(revisao_informada.VERSAO, "revisao-informada-1.0")

    def test_saidas_do_rastreio_pega_a_ultima_validada(self):
        rastreio = [dict(agente="objetivos", estado="validado", saida={"v": 1}), dict(agente="objetivos", estado="rejeitado", saida={"v": 2}),
                    dict(agente="objetivos", estado="validado", saida={"v": 3}), dict(agente="integrador", estado="validado", saida={})]
        self.assertEqual(revisao_informada.saidas_do_rastreio(rastreio), {"objetivos": {"v": 3}})
        rastreio += [dict(agente="objetivos", estado="descartado", saida={"v": 4})]  # ex.: reescrita de acento descartada
        self.assertEqual(revisao_informada.saidas_do_rastreio(rastreio), {"objetivos": {"v": 3}})


class TestServico(Base):
    def test_regeneracao_informada_recebe_as_criticas_da_versao_avaliada(self):
        s = self.servico([UMA_GRAVE, FAVORAVEL])
        r = s.gerar(self.pedido(s))
        primeira, segunda = self.gerador.revisoes_recebidas
        self.assertIsNone(primeira)  # 1ª geração: chamada normal
        self.assertEqual(set(segunda), set(plano_v2.ETAPAS))
        self.assertEqual([f["id"] for f in segunda["sequencia"]["falhas_deste_componente"]], ["F1"])
        self.assertEqual(segunda["sequencia"]["versao"], "revisao-informada-1.0")
        reg = [h for h in r["pedido_atual"]["historico"] if h["evento"] == "regenerando"]
        self.assertEqual((reg[0]["modo"], reg[0]["criticas_usadas"]), ("informada", ["F1"]))

    def test_regeneracao_cega_continua_disponivel(self):
        s = self.servico([UMA_GRAVE, FAVORAVEL], regeneracao="cega")
        r = s.gerar(self.pedido(s))
        self.assertEqual(self.gerador.revisoes_recebidas, [None, None])
        reg = [h for h in r["pedido_atual"]["historico"] if h["evento"] == "regenerando"]
        self.assertEqual((reg[0]["modo"], reg[0]["versao_revisao"], reg[0]["criticas_usadas"]), ("cega", None, []))

    def test_modo_invalido_recusado(self):
        with self.assertRaises(ValueError):
            self.servico(regeneracao="outra")


class TestApp(TestCase):
    def rodar(self, argv):
        class Falso:
            server_port = 0

            def __init__(self, *a):
                pass

            def serve_forever(self):
                Falso.servico = self.servico

            def server_close(self):
                pass
        saida = io.StringIO()
        with TemporaryDirectory() as d, patch.object(app, "ThreadingHTTPServer", Falso), redirect_stdout(saida):
            app.main(argv + ["--gerador", "demonstracao", "--juiz", "demonstracao", "--banco", str(Path(d) / "a.sqlite3")])
        return saida.getvalue(), Falso.servico

    def test_padrao_informada_e_opcao_cega(self):
        texto, servico = self.rodar([])
        self.assertEqual(servico.regeneracao, "informada")
        self.assertIn("regeneração informada pelas críticas do Juiz (revisao-informada-1.0)", texto)
        texto, servico = self.rodar(["--regeneracao", "cega"])
        self.assertEqual(servico.regeneracao, "cega")
        self.assertIn("regeneração cega", texto)
