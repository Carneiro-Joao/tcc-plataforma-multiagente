"""Transporte simulado; estes testes não medem a qualidade pedagógica do GPT-OSS."""
from copy import deepcopy
from email.message import Message
import io
import json
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch
from urllib.error import HTTPError, URLError

from contratos import juiz_v1 as contrato
from erros import ErroContrato, ErroGeracao
from groq_juiz import AgenteGroqJuiz, ENDPOINT, MODELO_PADRAO, _SemRedirecionamento
from juiz import avaliar_plano, criar_agente_groq_juiz

DADOS = Path(__file__).parent / "dados"
FIXTURE = json.loads((DADOS / "plano_v2/fixture_ordenacao.json").read_text(encoding="utf-8"))
PARECERES = json.loads((DADOS / "juiz_v1/pareceres.json").read_text(encoding="utf-8"))
CHAVE = "gsk_segredo_apenas_de_teste"


def envelope(parecer=None, **ajustes):
    raw = dict(id="chatcmpl-teste", model=MODELO_PADRAO, system_fingerprint="fp-teste",
               choices=[dict(finish_reason="stop", message={"role": "assistant", "content": json.dumps(
                   parecer if parecer is not None else PARECERES["favoravel"], ensure_ascii=False)})],
               usage=dict(prompt_tokens=100, completion_tokens=80, total_tokens=180,
                          queue_time=0.01, prompt_time=0.1, completion_time=0.2, total_time=0.31))
    raw.update(ajustes)
    return json.dumps(raw, ensure_ascii=False).encode("utf-8")


class Resposta(io.BytesIO):
    status = 200
    headers = {"x-request-id": "req-teste", "x-ratelimit-remaining-tokens": "9999"}


class Transporte:
    def __init__(self, *saidas):
        self.saidas, self.chamadas = list(saidas), []

    def __call__(self, req, timeout):
        self.chamadas.append((req, timeout))
        saida = self.saidas.pop(0)
        if isinstance(saida, Exception):
            raise saida
        return Resposta(saida)


def avaliar(transporte, reparos=0, **kwargs):
    agente = AgenteGroqJuiz(chave=CHAVE, transporte=transporte, **kwargs)
    return avaliar_plano(FIXTURE["plano_esperado"], FIXTURE["entrada"], agente,
                          modelo_gerador="gemini-3.5-flash-lite", modelo_juiz=MODELO_PADRAO, reparos=reparos)


class TestGroqJuiz(TestCase):
    def test_requisicao_realusa_contrato_prompt_e_parametros(self):
        t = Transporte(envelope())
        r = avaliar(t)
        req, timeout = t.chamadas[0]
        body = json.loads(req.data)
        self.assertEqual(req.full_url, ENDPOINT)
        self.assertEqual(req.get_header("Authorization"), "Bearer " + CHAVE)
        self.assertEqual(req.get_method(), "POST")
        self.assertEqual(timeout, 90)
        self.assertEqual(body["model"], MODELO_PADRAO)
        self.assertEqual(body["messages"][0]["content"], contrato.instrucoes())
        self.assertEqual(body["response_format"]["json_schema"]["schema"], contrato.esquema())
        self.assertTrue(body["response_format"]["json_schema"]["strict"])
        self.assertFalse(body["include_reasoning"])
        self.assertEqual(body["temperature"], 0)
        self.assertEqual(body["max_completion_tokens"], 8192)
        self.assertEqual(body["seed"], 42)
        self.assertEqual(r["decisao"]["proximo_estado"], "aguardando_decisao")
        self.assertNotIn(CHAVE, json.dumps(r))

    def test_decisoes_existentes_sem_alterar_plano(self):
        antes = deepcopy(FIXTURE)
        for nome, esperado in (("favoravel", "aguardando_decisao"), ("correcao", "em_correcao"),
                                ("critico", "revisao_necessaria")):
            with self.subTest(nome=nome):
                t = Transporte(envelope(PARECERES[nome]))
                r = avaliar(t)
                self.assertEqual(r["decisao"]["proximo_estado"], esperado)
                self.assertEqual(len(t.chamadas), 1)
        self.assertEqual(FIXTURE, antes)

    def test_metricas_e_versoes_preservadas(self):
        r = avaliar(Transporte(envelope()))["rastreio"][0]
        self.assertEqual(r["usage"]["total_tokens"], 180)
        self.assertEqual(r["versao_prompt"], contrato.VERSAO_PROMPT)
        self.assertEqual(r["versao_rubrica"], contrato.rubrica.VERSAO)
        self.assertEqual(r["modelo_respondeu"], MODELO_PADRAO)
        self.assertEqual(r["response_id"], "chatcmpl-teste")
        self.assertEqual(r["headers_metricas"]["x-request-id"], "req-teste")
        self.assertGreaterEqual(r["latencia_s"], 0)

    def test_usage_ausente_nao_e_zero(self):
        r = avaliar(Transporte(envelope(usage=None)))
        self.assertIsNone(r["rastreio"][0]["usage"])

    def test_chave_vem_do_ambiente_e_fabrica_explicita(self):
        with patch.dict("os.environ", {"GROQ_API_KEY": CHAVE}, clear=True):
            self.assertIsInstance(criar_agente_groq_juiz(), AgenteGroqJuiz)

    def test_sem_chave_nao_usa_gemini(self):
        with patch.dict("os.environ", {"GEMINI_API_KEY": "outro-provedor"}, clear=True):
            with self.assertRaises(ErroGeracao) as cm:
                criar_agente_groq_juiz()
        self.assertEqual(cm.exception.tipo, "configuracao")

    def test_parametros_invalidos(self):
        for kw in ({"modelo": "outro"}, {"timeout": 0}, {"timeout": float("nan")},
                   {"temperature": float("inf")}, {"temperature": True}, {"temperature": 3},
                   {"max_completion_tokens": 0}, {"max_completion_tokens": True},
                   {"reasoning_effort": "ultra"}, {"seed": -1}, {"seed": True}):
            with self.subTest(kw=kw), self.assertRaises(ErroGeracao):
                AgenteGroqJuiz(chave=CHAVE, **kw)

    def test_http_sem_retry_com_redacao_e_retry_after(self):
        for status in (400, 401, 403, 404, 429, 500, 503, 302):
            headers = Message()
            headers["Retry-After"] = "20"
            headers["x-request-id"] = "request-1"
            exc = HTTPError(ENDPOINT, status, "erro", headers, io.BytesIO(CHAVE.encode()))
            t = Transporte(exc)
            with self.subTest(status=status), self.assertRaises(ErroGeracao) as cm:
                avaliar(t)
            r = cm.exception.rastreio[0]
            self.assertEqual(len(t.chamadas), 1)
            self.assertEqual(r["http_status"], status)
            self.assertEqual(r["headers_metricas"]["retry-after"], "20")
            self.assertNotIn(CHAVE, json.dumps(r) + str(cm.exception))
            self.assertEqual(cm.exception.tipo, "http")

    def test_timeout_e_erro_de_rede(self):
        for exc in (TimeoutError(CHAVE), URLError(CHAVE), ConnectionError(CHAVE)):
            with self.subTest(exc=type(exc).__name__), self.assertRaises(ErroGeracao) as cm:
                avaliar(Transporte(exc))
            self.assertEqual(cm.exception.tipo, "transporte")
            self.assertNotIn(CHAVE, json.dumps(cm.exception.rastreio))

    def test_nao_redireciona_authorization(self):
        self.assertIsNone(_SemRedirecionamento().redirect_request(None, None, 302, "", {}, "https://outro.test"))

    def test_envelopes_invalidos(self):
        invalidos = [b"<html>falha</html>", b"\xff", b"[]", b"x" * 1_000_001,
                     envelope(choices=[]), envelope(choices=[{}, {}]), envelope(choices=[None]),
                     envelope(choices=[{"message": None, "finish_reason": "stop"}]),
                     envelope(choices=[{"message": {"content": None}, "finish_reason": "stop"}]),
                     envelope(model="modelo-diferente")]
        for raw in invalidos:
            with self.subTest(tamanho=len(raw)), self.assertRaises(ErroGeracao) as cm:
                avaliar(Transporte(raw))
            self.assertEqual(cm.exception.tipo, "resposta_api")

    def test_recusa_e_truncamento_nao_aprovam(self):
        for motivo, message, tipo in (("stop", {"refusal": "Recusado", "content": None}, "bloqueio"),
                                      ("content_filter", {}, "bloqueio"),
                                      ("length", {"content": "{\"avaliacoes\":"}, "resposta_incompleta"),
                                      ("tool_calls", {"content": "{}"}, "resposta_incompleta")):
            with self.subTest(motivo=motivo), self.assertRaises(ErroGeracao) as cm:
                avaliar(Transporte(envelope(choices=[dict(finish_reason=motivo, message=message)])))
            self.assertEqual(cm.exception.tipo, tipo)

    def test_json_invalido_e_chaves_duplicadas_rejeitados(self):
        for texto in ("nao-json", '{"resumo":"a","resumo":"b"}'):
            with self.subTest(texto=texto), self.assertRaises(ErroContrato):
                avaliar(Transporte(envelope(choices=[dict(finish_reason="stop", message={"content": texto})])))

    def test_validacao_local_rejeita_semantica_do_contrato(self):
        p = deepcopy(PARECERES["favoravel"])
        p["avaliacoes"][0]["nota"] = 0  # sem falha grave correspondente
        with self.assertRaises(ErroContrato) as cm:
            avaliar(Transporte(envelope(p)))
        self.assertTrue(cm.exception.diagnosticos)
        self.assertEqual(cm.exception.rastreio[0]["estado"], "rejeitado")

    def test_reparo_tecnico_opt_in_com_mesmo_plano(self):
        t = Transporte(envelope({}), envelope())
        r = avaliar(t, reparos=1)
        self.assertEqual(len(r["rastreio"]), 2)
        dados = [json.loads(json.loads(req.data)["messages"][1]["content"]) for req, _ in t.chamadas]
        self.assertEqual(dados[0]["saidas_anteriores"], dados[1]["saidas_anteriores"])
        self.assertIn("reparo_estrutural", dados[1])

    def test_limite_reparo_nao_repete_indefinidamente(self):
        t = Transporte(envelope({}), envelope({}))
        with self.assertRaises(ErroContrato) as cm:
            avaliar(t, reparos=1)
        self.assertEqual(len(cm.exception.rastreio), 2)

    def test_credencial_ecoada_e_rejeitada_sem_vazar(self):
        p = deepcopy(PARECERES["favoravel"])
        p["resumo"] = CHAVE
        with self.assertRaises(ErroGeracao) as cm:
            avaliar(Transporte(envelope(p)))
        self.assertNotIn(CHAVE, json.dumps(cm.exception.rastreio))

    def test_plano_invalido_nao_chama_api(self):
        t = Transporte()
        a = AgenteGroqJuiz(chave=CHAVE, transporte=t)
        with self.assertRaises(ErroContrato):
            avaliar_plano({}, FIXTURE["entrada"], a, modelo_gerador="gemini-3.5-flash-lite", modelo_juiz=MODELO_PADRAO)
        self.assertEqual(t.chamadas, [])
