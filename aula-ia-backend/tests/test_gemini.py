"""Testes sem rede: protocolo Gemini, contratos, cotas e rastreio de falhas."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import io
import json
import os
from unittest import TestCase
from unittest.mock import patch
from urllib.error import HTTPError, URLError
from gemini import AgenteGemini, MODELO_PADRAO
from geracao import GeradorDePlano
from erros import ErroGeracao
from test_contratos import FIXTURE

CHAVE = "chave-ficticia-exclusiva-do-teste"


def envelope(saida, **extra):
    texto = saida if isinstance(saida, str) else json.dumps(saida, ensure_ascii=False)
    return {"candidates": [{"finishReason": "STOP", "content": {"parts": [{"text": texto}]}}],
            "modelVersion": MODELO_PADRAO, "usageMetadata": {"promptTokenCount": 10, "candidatesTokenCount": 20, "totalTokenCount": 30}, **extra}


class Transporte:
    def __init__(self, respostas):
        self.respostas = list(respostas)
        self.pedidos = []

    def __call__(self, pedido, timeout):
        self.pedidos.append(pedido)
        proximo = self.respostas.pop(0)
        if isinstance(proximo, BaseException):
            raise proximo
        return io.BytesIO(json.dumps(proximo).encode())


def gerador(respostas, reparos=1):
    transporte = Transporte(respostas)
    agente = AgenteGemini(chave=CHAVE, transporte=transporte)
    return GeradorDePlano("ia", agente=agente, reparos=reparos), transporte


def respostas_validas():
    return [envelope(FIXTURE["saidas"][n]) for n in GeradorDePlano.ESPECIALISTAS]


class TestGemini(TestCase):
    def test_pipeline_cinco_chamadas_e_integrador_local(self):
        pipeline, transporte = gerador(respostas_validas())
        resultado = pipeline.gerar(FIXTURE["entrada"], 0)
        self.assertEqual(resultado["plano"], FIXTURE["plano_esperado"])
        self.assertEqual(len(transporte.pedidos), 5)
        self.assertEqual(resultado["rastreio"][-1]["tipo"], "deterministico")
        self.assertEqual(resultado["avaliacao_pedagogica"], "pendente")
        for nome, pedido in zip(GeradorDePlano.ESPECIALISTAS, transporte.pedidos):
            corpo = json.loads(pedido.data)
            self.assertEqual(pedido.full_url, f"https://generativelanguage.googleapis.com/v1beta/models/{MODELO_PADRAO}:generateContent")
            self.assertEqual(pedido.get_header("X-goog-api-key"), CHAVE)
            self.assertNotIn(CHAVE, pedido.full_url + pedido.data.decode())
            schema = corpo["generationConfig"]["responseFormat"]["text"]["schema"]
            self.assertFalse(schema["additionalProperties"])
            entrada = json.loads(corpo["contents"][0]["parts"][0]["text"])
            self.assertEqual(set(entrada["saidas_anteriores"]), set(GeradorDePlano.DEPENDENCIAS[nome]))
        self.assertNotIn(CHAVE, json.dumps(resultado))

    def test_repara_so_etapa_invalida_preservando_respostas(self):
        respostas = respostas_validas()
        invalida = {"metodologia": {"texto": "errado"}, "recursos": "papel e cartões", "ano": "9º ano"}
        respostas.insert(1, envelope(invalida))
        pipeline, transporte = gerador(respostas)
        resultado = pipeline.gerar(FIXTURE["entrada"], 0)
        self.assertEqual(len(transporte.pedidos), 6)
        trace = resultado["rastreio"]
        self.assertEqual(trace[1]["estado"], "rejeitado")
        self.assertEqual(trace[1]["saida"], invalida)
        self.assertEqual(trace[2]["tentativa"], 2)
        self.assertEqual(trace[1]["entrada"], trace[2]["entrada"])
        dados = json.loads(json.loads(transporte.pedidos[2].data)["contents"][0]["parts"][0]["text"])
        self.assertIn("reparo_estrutural", dados)
        self.assertEqual(resultado["plano"], FIXTURE["plano_esperado"])

    def test_segunda_falha_para_sem_executar_dependentes(self):
        pipeline, transporte = gerador([envelope({}), envelope({})])
        with self.assertRaises(ErroGeracao) as ctx:
            pipeline.gerar(FIXTURE["entrada"], 0)
        self.assertEqual(len(transporte.pedidos), 2)
        self.assertEqual([r["estado"] for r in ctx.exception.rastreio], ["rejeitado", "rejeitado"])

    def test_json_invalido_pode_ser_reparado_uma_vez(self):
        pipeline, transporte = gerador([envelope('{"objetivos":[],"objetivos":[]}')] + respostas_validas())
        resultado = pipeline.gerar(FIXTURE["entrada"], 0)
        self.assertEqual(len(transporte.pedidos), 6)
        self.assertEqual(resultado["rastreio"][0]["tipo_erro"], "contrato")

    def test_sem_reparo_encerra_na_primeira_falha(self):
        pipeline, transporte = gerador([envelope({})], reparos=0)
        with self.assertRaises(ErroGeracao):
            pipeline.gerar(FIXTURE["entrada"], 0)
        self.assertEqual(len(transporte.pedidos), 1)

    def test_http_e_timeout_nao_geram_reparo_nem_vazam_chave(self):
        erros = [HTTPError("https://example.invalid", c, CHAVE, {}, io.BytesIO(CHAVE.encode())) for c in (400, 401, 403, 404, 429, 503)]
        erros += [URLError(CHAVE), TimeoutError(CHAVE)]
        for erro in erros:
            with self.subTest(erro=type(erro).__name__, codigo=getattr(erro, "code", None)):
                pipeline, transporte = gerador([erro])
                with self.assertRaises(ErroGeracao) as ctx:
                    pipeline.gerar(FIXTURE["entrada"], 0)
                self.assertEqual(len(transporte.pedidos), 1)
                self.assertNotIn(CHAVE, str(ctx.exception) + json.dumps(ctx.exception.rastreio))
                self.assertEqual(ctx.exception.rastreio[0]["estado"], "falha")

    def test_bloqueio_e_resposta_truncada_nao_entram_no_plano(self):
        truncado = envelope(FIXTURE["saidas"]["objetivos"])
        truncado["candidates"][0]["finishReason"] = "MAX_TOKENS"
        for raw in ({"promptFeedback": {"blockReason": "SAFETY"}}, {"candidates": []}, truncado, [], {"candidates": [{}]}):
            pipeline, transporte = gerador([raw])
            with self.subTest(raw=raw), self.assertRaises(ErroGeracao):
                pipeline.gerar(FIXTURE["entrada"], 0)
            self.assertEqual(len(transporte.pedidos), 1)

    def test_credencial_ecoada_e_redigida(self):
        pipeline, _ = gerador([envelope({"objetivos": [CHAVE, "Outro"]})])
        with self.assertRaises(ErroGeracao) as ctx:
            pipeline.gerar(FIXTURE["entrada"], 0)
        self.assertNotIn(CHAVE, json.dumps(ctx.exception.rastreio))

    def test_texto_de_pensamento_nao_e_parseado_como_saida(self):
        respostas = respostas_validas()
        respostas[0]["candidates"][0]["content"]["parts"].insert(0, {"text": "raciocínio", "thought": True})
        pipeline, _ = gerador(respostas)
        self.assertEqual(pipeline.gerar(FIXTURE["entrada"], 0)["plano"], FIXTURE["plano_esperado"])

    def test_ausencia_de_chave_nao_usa_outro_provedor(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "nao-usar", "OPENROUTER_API_KEY": "nao-usar"}, clear=True):
            with self.assertRaises(ErroGeracao):
                GeradorDePlano("ia")
            self.assertEqual(GeradorDePlano().gerar(FIXTURE["entrada"], 0)["modo"], "demonstracao")

    def test_rastreios_independentes_em_consultas_concorrentes(self):
        def transporte(pedido, timeout):
            payload = json.loads(pedido.data)
            campo = payload["generationConfig"]["responseFormat"]["text"]["schema"]["required"][0]
            nome = {"etapas": "sequencia", "adaptacoes": "adaptacao"}.get(campo, campo)
            return io.BytesIO(json.dumps(envelope(FIXTURE["saidas"][nome])).encode())
        pipeline = GeradorDePlano("ia", agente=AgenteGemini(chave=CHAVE, transporte=transporte))
        with ThreadPoolExecutor(max_workers=2) as pool:
            resultados = list(pool.map(lambda rev: pipeline.gerar(FIXTURE["entrada"], rev), [1, 2]))
        self.assertEqual([r["revisao"] for r in resultados], [1, 2])
        self.assertTrue(all(len(r["rastreio"]) == 6 for r in resultados))
        resultados[0]["rastreio"][0]["saida"]["objetivos"].clear()
        self.assertEqual(len(resultados[1]["rastreio"][0]["saida"]["objetivos"]), 2)
