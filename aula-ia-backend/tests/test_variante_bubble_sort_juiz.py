"""Regressões da V02: inversão da comparação no Bubble Sort em ET2."""
from copy import deepcopy
from pathlib import Path
from unittest import TestCase

from casos_juiz import carregar_caso, hash_json


RAIZ = Path(__file__).resolve().parents[2]
CASO_BASE = RAIZ / "experimentos" / "juiz" / "casos" / "ordenacao_real_994c4cd5.json"
V02 = RAIZ / "experimentos" / "juiz" / "casos" / "ordenacao_variante_bubble_sort_comparacao_invertida_02.json"


class TestVarianteBubbleSortV02(TestCase):
    def test_valida_contrato_e_rastreia_origem(self):
        base = carregar_caso(CASO_BASE)
        var = carregar_caso(V02)
        self.assertEqual(base["origem"]["tipo"], "sqlite_real")
        self.assertEqual(var["origem"]["tipo"], "variante_controlada")
        self.assertEqual(var["origem"]["id_variante"], "V02-BUBBLE-COMPARACAO-INVERTIDA")
        self.assertEqual(var["origem"]["campo_alterado"], "plano.desenvolvimento[1].acao_discente")
        self.assertEqual(var["origem"]["plano_base_sha256"], hash_json(base["plano"]))
        self.assertEqual(var["origem"]["entrada_base_sha256"], hash_json(base["entrada"]))
        self.assertEqual(var["origem"]["plano_sha256"], hash_json(var["plano"]))
        self.assertEqual(var["origem"]["entrada_sha256"], hash_json(var["entrada"]))

    def test_alterou_somente_acao_discente_et2(self):
        base = carregar_caso(CASO_BASE)
        var = carregar_caso(V02)
        self.assertEqual(var["entrada"], base["entrada"])
        self.assertEqual(var["modelo_gerador"], base["modelo_gerador"])
        self.assertEqual(var["revisao"], base["revisao"])
        self.assertEqual(var["plano"]["desenvolvimento"][1]["id"], "ET2")
        anterior = base["plano"]["desenvolvimento"][1]["acao_discente"]
        injetado = var["plano"]["desenvolvimento"][1]["acao_discente"]
        self.assertNotEqual(anterior, injetado)
        self.assertIn("esquerda for menor que o número da direita", injetado)
        self.assertIn("sequência crescente", injetado)
        copia = deepcopy(var["plano"])
        copia["desenvolvimento"][1]["acao_discente"] = anterior
        self.assertEqual(copia, base["plano"])
