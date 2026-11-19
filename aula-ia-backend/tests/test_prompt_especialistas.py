"""Prompt dos especialistas: versão 2.3 (sem 'cartões já preparados') e 2.2 preservada. Sem rede. Execute a partir de aula-ia-backend."""
from copy import deepcopy
import json
from pathlib import Path
from unittest import TestCase

from contratos import plano_v2 as c
import geracao_v2
from geracao_v2 import AgenteGeminiCompleto, GeradorDePlanoCompleto, VERSAO_PROMPT, VERSOES_PROMPT
from test_gemini import Transporte, envelope, CHAVE

FIXTURE_V2 = json.loads((Path(__file__).parent / "dados/plano_v2/fixture_ordenacao.json").read_text(encoding="utf-8"))


def gerar(versao=None):
    transporte = Transporte([envelope(FIXTURE_V2["saidas"][n]) for n in c.ETAPAS])
    kw = {} if versao is None else {"versao_prompt": versao}
    gerador = GeradorDePlanoCompleto("ia", agente=AgenteGeminiCompleto(chave=CHAVE, transporte=transporte, **kw))
    resultado = gerador.gerar(deepcopy(FIXTURE_V2["entrada"]), 0)
    sistemas = [json.loads(p.data)["systemInstruction"]["parts"][0]["text"] for p in transporte.pedidos]
    return resultado, sistemas


class TestPromptEspecialistas(TestCase):
    def test_padrao_e_2_3_e_fica_registrado_no_rastreio(self):
        self.assertEqual(VERSAO_PROMPT, "especialistas-plano-2.3")
        resultado, _ = gerar()
        versoes = {a.get("versao_prompt") for a in resultado["rastreio"] if a["agente"] != "integrador"}
        self.assertEqual(versoes, {"especialistas-plano-2.3"})

    def test_2_3_nao_sugere_cartoes_e_proibe_material_fora_da_lista(self):
        _, sistemas = gerar()
        self.assertEqual(len(sistemas), 6)
        for texto in sistemas:
            self.assertNotIn("cartões", texto)
            self.assertNotIn("já preparad", texto.replace('"já está preparado"', ""))
            self.assertIn("Use somente os recursos listados em contexto.recursos", texto)
            self.assertIn("acentuação correta", texto)

    def test_2_2_preservada_identica_para_reprodutibilidade(self):
        resultado, sistemas = gerar("especialistas-plano-2.2")
        self.assertTrue(all("manipulação de cartões já preparados, sem acrescentar recursos." in t for t in sistemas))
        self.assertEqual({a.get("versao_prompt") for a in resultado["rastreio"] if a["agente"] != "integrador"},
                         {"especialistas-plano-2.2"})

    def test_instrucao_de_cada_especialista_mantida_nas_duas_versoes(self):
        for versao, instrucoes in VERSOES_PROMPT.items():
            self.assertEqual(set(instrucoes), set(c.ETAPAS) - {"integrador"} if "integrador" in c.ETAPAS else set(c.ETAPAS))
            for nome, texto in instrucoes.items():
                self.assertTrue(texto.startswith(VERSOES_PROMPT["especialistas-plano-2.2"][nome].split(" Só exija")[0]), (versao, nome))
        self.assertIs(geracao_v2.INSTRUCOES, VERSOES_PROMPT[VERSAO_PROMPT])

    def test_versao_desconhecida_e_recusada(self):
        with self.assertRaises(ValueError):
            AgenteGeminiCompleto(chave=CHAVE, versao_prompt="especialistas-plano-9.9")
