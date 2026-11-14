"""Regressões dos achados OpenRouter, usando o validador de produção."""
from copy import deepcopy
import json
from pathlib import Path
from unittest import TestCase
from contratos import SCHEMA, Validador, validar, integrar, ler_json
from erros import ErroContrato

FIXTURES = Path(__file__).parent / "fixtures"
FIXTURE = json.loads((FIXTURES / "fixture_ordenacao.json").read_text(encoding="utf-8"))


class TestContratos(TestCase):
    def test_27_casos_da_revisao(self):
        Validador.check_schema(SCHEMA)
        casos = json.loads((FIXTURES / "casos_estruturais.json").read_text(encoding="utf-8"))
        self.assertEqual(len(casos), 27)
        for caso in casos:
            with self.subTest(caso=caso["caso"]):
                if caso["esperado"] == "aceitar":
                    validar(caso["contrato"], caso["entrada"], FIXTURE["entrada"])
                else:
                    with self.assertRaises(ErroContrato):
                        validar(caso["contrato"], caso["entrada"], FIXTURE["entrada"])

    def test_integracao_preserva_catalogo_e_todos_os_campos(self):
        estado = deepcopy(FIXTURE["saidas"])
        plano = integrar(FIXTURE["entrada"], estado)
        self.assertEqual(plano, FIXTURE["plano_esperado"])
        plano["etapas"][0]["minutos"] = 999
        self.assertEqual(estado, FIXTURE["saidas"])

    def test_json_estrito(self):
        for invalido in ('{"a":1,"a":2}', '{"a":NaN}', '{"a":Infinity}', '```json\n{}\n```', '{} texto', ''):
            with self.subTest(invalido=invalido), self.assertRaises(ErroContrato):
                ler_json(invalido)
        self.assertEqual(ler_json('{"a": 1}'), {"a": 1})

    def test_recusa_float_e_bool_em_minutos(self):
        for valor in (5.0, True, "5"):
            saida = deepcopy(FIXTURE["saidas"]["sequencia"])
            saida["etapas"][0]["minutos"] = valor
            with self.subTest(valor=valor), self.assertRaises(ErroContrato):
                validar("sequencia", saida, FIXTURE["entrada"])
