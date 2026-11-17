"""Regressão offline da variante V01 derivada do caso SQLite real (RD-002)."""
from copy import deepcopy
from pathlib import Path
from unittest import TestCase

from casos_juiz import carregar_caso, hash_json


RAIZ = Path(__file__).resolve().parents[2]
CASO_BASE = RAIZ / "experimentos" / "juiz" / "casos" / "ordenacao_real_994c4cd5.json"
VARIANTE = RAIZ / "experimentos" / "juiz" / "casos" / "ordenacao_variante_evi2_desalinhada_01.json"


class TestVarianteControladaJuiz(TestCase):
    def test_casos_passam_no_contrato_mecanico_e_hashes(self):
        base = carregar_caso(CASO_BASE)
        var = carregar_caso(VARIANTE)
        self.assertEqual(base["origem"]["tipo"], "sqlite_real")
        self.assertEqual(var["origem"]["tipo"], "variante_controlada")
        self.assertEqual(var["origem"]["plano_base_sha256"], hash_json(base["plano"]))
        self.assertEqual(var["origem"]["plano_sha256"], hash_json(var["plano"]))
        self.assertEqual(var["origem"]["entrada_sha256"], hash_json(var["entrada"]))
        self.assertEqual(var["origem"]["entrada_base_sha256"], hash_json(base["entrada"]))

    def test_apenas_texto_esperado_da_evi2_foi_alterado(self):
        base = carregar_caso(CASO_BASE)
        var = carregar_caso(VARIANTE)
        self.assertEqual(var["entrada"], base["entrada"])
        self.assertEqual(var["modelo_gerador"], base["modelo_gerador"])
        self.assertEqual(var["revisao"], base["revisao"])
        texto_original = base["plano"]["avaliacao_aprendizagem"]["evidencias"][1]["evidencia_esperada"]
        texto_variante = var["plano"]["avaliacao_aprendizagem"]["evidencias"][1]["evidencia_esperada"]
        self.assertNotEqual(texto_original, texto_variante)
        self.assertEqual(var["plano"]["avaliacao_aprendizagem"]["evidencias"][1]["id"], "EVI2")
        self.assertEqual(var["plano"]["avaliacao_aprendizagem"]["evidencias"][1]["objetivo_id"], "OBJ2")
        copia = deepcopy(var["plano"])
        copia["avaliacao_aprendizagem"]["evidencias"][1]["evidencia_esperada"] = texto_original
        self.assertEqual(copia, base["plano"])
