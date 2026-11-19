"""Pausa antes do reparo do Juiz no app (achado de 19/11/2026, 13:18: reparo imediato → Groq HTTP 429 por tokens/minuto).
Sem rede. Execute a partir de aula-ia-backend."""
from copy import deepcopy
import json
from pathlib import Path
from unittest import TestCase

import juiz_servico
from erros import ErroContrato
from juiz import avaliar_plano

FIXTURE = json.loads((Path(__file__).parent / "dados/plano_v2/fixture_ordenacao.json").read_text(encoding="utf-8"))
PARECER = json.loads(juiz_servico.PARECER_DEMONSTRACAO.read_text(encoding="utf-8"))["parecer"]


class AgenteRoteirizado:
    """Imita o AgenteGroqJuiz: cada chamada consome o roteiro ('contrato' = Groq rejeitou o JSON; 'ok' = parecer válido)."""
    modelo, versao_prompt, versao_esquema_api = "openai/gpt-oss-120b", "juiz-v1.3", "teste"

    def __init__(self, roteiro, eventos):
        self.roteiro, self.eventos = list(roteiro), eventos

    def executar(self, nome, entrada, estado, revisao, *, registro, reparo=None):
        self.eventos.append(("chamada", bool(reparo)))
        if self.roteiro.pop(0) == "contrato":
            raise ErroContrato("Groq rejeitou o parecer gerado por incompatibilidade com o JSON Schema.")
        return deepcopy(PARECER)


def avaliar(agente, **kw):
    return avaliar_plano(FIXTURE["plano_esperado"], FIXTURE["entrada"], agente, modelo_gerador="g",
                         modelo_juiz=agente.modelo, **kw)


class TestAvaliarPlanoAntesDoReparo(TestCase):
    def test_chamado_uma_vez_antes_da_tentativa_de_reparo(self):
        eventos = []
        r = avaliar(AgenteRoteirizado(["contrato", "ok"], eventos), reparos=1,
                    antes_do_reparo=lambda: eventos.append(("pausa",)))
        self.assertEqual(eventos, [("chamada", False), ("pausa",), ("chamada", True)])
        self.assertEqual(r["parecer"], PARECER)
        self.assertEqual([t["estado"] for t in r["rastreio"]], ["rejeitado", "validado"])

    def test_sem_reparo_necessario_nao_pausa(self):
        eventos = []
        avaliar(AgenteRoteirizado(["ok"], eventos), reparos=1, antes_do_reparo=lambda: eventos.append(("pausa",)))
        self.assertEqual(eventos, [("chamada", False)])

    def test_reparos_zero_nunca_pausa_e_falha_no_contrato(self):
        eventos = []
        with self.assertRaises(ErroContrato):
            avaliar(AgenteRoteirizado(["contrato"], eventos), reparos=0, antes_do_reparo=lambda: eventos.append(("pausa",)))
        self.assertEqual(eventos, [("chamada", False)])

    def test_padrao_dos_experimentos_e_reparo_imediato(self):
        eventos = []
        avaliar(AgenteRoteirizado(["contrato", "ok"], eventos), reparos=1)  # ensaio_juiz não passa antes_do_reparo
        self.assertEqual(eventos, [("chamada", False), ("chamada", True)])


class TestJuizGroqDoApp(TestCase):
    def test_reproduz_19_11_contrato_rejeitado_espera_60_s_e_o_reparo_valida(self):
        eventos = []
        juiz = juiz_servico.JuizGroq(agente=AgenteRoteirizado(["contrato", "ok"], eventos),
                                     dormir=lambda s: eventos.append(("pausa", s)))
        r = juiz.avaliar(FIXTURE["plano_esperado"], FIXTURE["entrada"], modelo_gerador="g", revisao=1, ciclo=0)
        self.assertEqual(eventos, [("chamada", False), ("pausa", 60), ("chamada", True)])
        self.assertEqual((r["modo"], r["decisao"]["proximo_estado"]), ("groq", "em_correcao"))

    def test_pausa_padrao_e_60_s_e_configuravel(self):
        self.assertEqual(juiz_servico.PAUSA_ANTES_DO_REPARO_S, 60)
        eventos = []
        juiz = juiz_servico.JuizGroq(agente=AgenteRoteirizado(["contrato", "ok"], eventos), pausa_reparo_s=5,
                                     dormir=lambda s: eventos.append(("pausa", s)))
        juiz.avaliar(FIXTURE["plano_esperado"], FIXTURE["entrada"], modelo_gerador="g", revisao=1, ciclo=0)
        self.assertIn(("pausa", 5), eventos)

    def test_configuracao_dos_experimentos_inalterada(self):
        self.assertEqual(juiz_servico.REPAROS, 1)
        self.assertEqual(juiz_servico.PARAMETROS_EXPERIMENTOS["versao_prompt"], "juiz-v1.3")
