"""Contratos de versão: v1.2 imutável e v1.3 sem regressão estrutural.

Não chama GroqCloud e não comprova qualidade pedagógica do modelo real.
"""
from hashlib import sha256
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from contratos import juiz_v1 as contrato
from casos_juiz import carregar_caso
from ensaio_juiz import executar_ensaio
from groq_juiz import AgenteGroqJuiz, MODELO_PADRAO
from juiz import avaliar_plano


RAIZ = Path(__file__).resolve().parents[2]
REAL = RAIZ / "experimentos" / "juiz" / "casos" / "ordenacao_real_994c4cd5.json"
PARECERES = Path(__file__).parent / "dados" / "juiz_v1" / "pareceres.json"
CHAVE = "gsk" + "_chave_sintetica_teste"  # montada: sem padrão literal de chave no arquivo
SHA_V12 = "f93058ca002d0718955d7ff391c77d3343030cd41005c8cf6732dd7f251280b5"


class TestPromptsVersionados(TestCase):
    def test_v12_byte_a_byte_identico_ao_usado_nos_ensaios_originais(self):
        self.assertEqual(
            sha256(contrato.instrucoes("juiz-v1.2").encode("utf-8")).hexdigest(),
            SHA_V12
        )

    def test_default_v13_preserva_rubrica_esquema_politica_e_nao_vaza_casos(self):
        self.assertEqual(contrato.VERSAO_PROMPT, "juiz-v1.3")
        self.assertEqual(contrato.instrucoes(), contrato.instrucoes("juiz-v1.3"))
        self.assertEqual(contrato.VERSAO, "parecer-juiz-1.0")
        self.assertEqual(contrato.rubrica.VERSAO, "rubrica-juiz-0.1")
        self.assertEqual(contrato.POLITICA_PRELIMINAR["nome"], "politica-juiz-prelim-0.1")
        a = contrato.instrucoes("juiz-v1.3")
        b = contrato.instrucoes("juiz-v1.2")
        self.assertIn("Auditoria conceitual obrigatória", a)
        self.assertIn("simulando mentalmente um caso mínimo", a)
        self.assertIn("componente sequencia", a)
        self.assertNotIn("Auditoria conceitual obrigatória", b)
        self.assertNotIn("Bubble", a[a.index("Auditoria conceitual obrigatória"):])
        self.assertNotIn("V01", a)
        self.assertNotIn("V02", a)
        for c in contrato.CRITERIOS:
            self.assertIn(c, a)

    def test_rejeita_versao_inexistente(self):
        for invalida in ("juiz-v1.4", "", 42, {}, False):
            with self.subTest(versao=invalida), self.assertRaises(ValueError):
                contrato.instrucoes(invalida)
        with self.assertRaises(ValueError):
            AgenteGroqJuiz(chave=CHAVE, versao_prompt="inexistente")

    def test_validacao_local_registra_versao_e_hash_sem_api(self):
        with TemporaryDirectory() as pasta:
            for versao in contrato.VERSOES_PROMPT:
                with self.subTest(versao=versao):
                    res, destino = executar_ensaio(REAL, pasta,
                        somente_validar=True, versao_prompt=versao,
                        fabrica=lambda **_: self.fail("Nao instanciar provedor"))
                    self.assertEqual(res["status"], "validado_localmente")
                    self.assertEqual(res["versao_prompt"], versao)
                    self.assertEqual(res["prompt_sha256"],
                        sha256(contrato.instrucoes(versao).encode()).hexdigest())
                    self.assertEqual(res["metricas"]["chamadas_http"], 0)
                    self.assertEqual(json.loads(destino.read_text())["versao_prompt"], versao)

    def test_groq_mock_recebe_e_registra_mesma_versao(self):
        caso = carregar_caso(REAL)
        parecer = json.loads(PARECERES.read_text(encoding="utf-8"))["favoravel"]
        for versao in contrato.VERSOES_PROMPT:
            with self.subTest(versao=versao):
                calls = []
                class Resposta(io.BytesIO):
                    status = 200
                    headers = {}
                def transporte(req, timeout):
                    calls.append(json.loads(req.data))
                    envelope = {
                        "id": "teste-versionamento", "model": MODELO_PADRAO,
                        "choices": [{"message": {
                            "role": "assistant", "content": json.dumps(parecer)
                        }, "finish_reason": "stop"}]
                    }
                    return Resposta(json.dumps(envelope).encode("utf-8"))
                agente = AgenteGroqJuiz(chave=CHAVE, transporte=transporte,
                                      versao_prompt=versao)
                res = avaliar_plano(caso["plano"], caso["entrada"], agente,
                    modelo_gerador=caso["modelo_gerador"], modelo_juiz=MODELO_PADRAO)
                self.assertEqual(len(calls), 1)
                self.assertEqual(calls[0]["messages"][0]["content"],
                                 contrato.instrucoes(versao))
                self.assertEqual(res["rastreio"][0]["versao_prompt"], versao)
                self.assertEqual(res["decisao"]["proximo_estado"], "aguardando_decisao")
