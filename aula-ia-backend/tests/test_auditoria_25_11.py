"""Correções da auditoria de 25/11/2026 (C2, C3, C6, C7, C8). Sem rede. Execute a partir de aula-ia-backend."""
from copy import deepcopy
import json
from pathlib import Path
from unittest import TestCase

import acentuacao
from geracao_v2 import AgenteGeminiCompleto, GeradorDePlanoCompleto
from test_gemini import CHAVE, Transporte, envelope
from contratos import plano_v2

FIXTURE = json.loads((Path(__file__).parent / "dados/plano_v2/fixture_ordenacao.json").read_text(encoding="utf-8"))
RECURSOS_SEM_ACENTO = "quadro e pincel, material didatico impresso e fichas com a sequencia numerica para pratica em duplas"


class TestC2RecursosNaoDisparamReescrita(TestCase):
    """C2: `recursos` é cópia exata do que o professor digitou; reescrevê-lo seria sempre descartado pelo validador."""

    def test_detector_ignora_recursos_e_continua_vendo_os_outros_campos(self):
        saida = {"metodologia": "A explicacao do professor ocorre durante a atividade de comparacao dos grupos.",
                 "recursos": RECURSOS_SEM_ACENTO}
        self.assertEqual(acentuacao.campos_sem_acentuacao(saida), ["metodologia"])
        self.assertEqual(acentuacao.campos_sem_acentuacao({"recursos": RECURSOS_SEM_ACENTO}), [])
        # só a chave exata "recursos" é ignorada; outro campo com o mesmo texto continua detectado
        self.assertEqual(acentuacao.campos_sem_acentuacao({"recursos_extras": RECURSOS_SEM_ACENTO}), ["recursos_extras"])
        self.assertEqual(acentuacao.campos_sem_acentuacao({"outros_recursos": RECURSOS_SEM_ACENTO}), ["outros_recursos"])

    def test_gerador_nao_faz_chamada_extra_por_recursos_digitados_sem_acento(self):
        entrada = deepcopy(FIXTURE["entrada"])
        entrada["contexto"]["recursos"] = RECURSOS_SEM_ACENTO
        saidas = deepcopy(FIXTURE["saidas"])
        saidas["metodologia"]["recursos"] = RECURSOS_SEM_ACENTO
        transporte = Transporte([envelope(saidas[n]) for n in plano_v2.ETAPAS])
        agente = AgenteGeminiCompleto(chave=CHAVE, transporte=transporte, repeticoes_503=0)
        resultado = GeradorDePlanoCompleto("ia", agente=agente, reparos=1).gerar(entrada, 1)
        self.assertEqual(len(transporte.pedidos), 6)
        self.assertEqual(resultado["plano"]["recursos"], RECURSOS_SEM_ACENTO)
        self.assertFalse([r for r in resultado["rastreio"] if r.get("tentativa") == "acentuacao"])
