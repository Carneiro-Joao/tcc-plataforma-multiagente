"""Integração com o validador preexistente, sem duplicar seu conjunto de testes."""
from copy import deepcopy
from unittest import TestCase
from unittest.mock import patch
from contratos.execucao import integrar, validar, ler_json, esquema
from contratos.validacao import CONTRATOS
from erros import ErroContrato
from test_contratos import FIXTURE, CASOS


class TestIntegracaoContratos(TestCase):
    def test_composicao_exata_sem_alterar_as_fontes(self):
        estado = deepcopy(FIXTURE["saidas"])
        plano = integrar(FIXTURE["entrada"], estado)
        self.assertEqual(plano, FIXTURE["plano_esperado"])
        plano["etapas"][0]["minutos"] = 999
        self.assertEqual(estado, FIXTURE["saidas"])

    def test_adaptador_preserva_diagnosticos_existentes(self):
        diagnosticos = [{"caminho": "etapas", "regra": "soma_duracao", "esperado": 50, "recebido": 45}]
        with patch('contratos.execucao.diagnosticar', return_value=diagnosticos) as func:
            with self.assertRaises(ErroContrato) as ctx:
                validar('sequencia', {}, FIXTURE['entrada'])
        func.assert_called_once_with('sequencia', {}, FIXTURE['entrada'])
        self.assertEqual(ctx.exception.diagnosticos, diagnosticos)

    def test_parser_da_integracao_recusa_overflow_e_duplicidade(self):
        for texto, regra in (('{"x":1e999}', 'constante_nao_finita'), ('{"x":1,"x":2}', 'chave_duplicada')):
            with self.subTest(regra=regra), self.assertRaises(ErroContrato) as ctx:
                ler_json(texto)
            self.assertEqual(ctx.exception.diagnosticos[0]['regra'], regra)

    def test_schema_enviado_expoe_os_mesmos_campos(self):
        for nome in CONTRATOS:
            esperado = FIXTURE['plano_esperado'] if nome == 'plano' else FIXTURE['saidas'][nome]
            with self.subTest(contrato=nome):
                s = esquema(nome)
                self.assertEqual(set(s['required']), set(esperado))
                self.assertEqual(set(s['properties']), set(esperado))
                self.assertFalse(s['additionalProperties'])

    def test_adaptador_executa_os_mesmos_27_casos(self):
        for caso in CASOS:
            with self.subTest(caso=caso['caso']):
                if caso['esperado'] == 'aceitar':
                    validar(caso['contrato'], caso['entrada'], FIXTURE['entrada'])
                else:
                    with self.assertRaises(ErroContrato):
                        validar(caso['contrato'], caso['entrada'], FIXTURE['entrada'])
