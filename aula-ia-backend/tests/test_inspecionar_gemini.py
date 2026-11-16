"""Inspeção local distingue simulação, falha, consumo desconhecido e contrato legado."""
from copy import deepcopy
from unittest import TestCase
from inspecionar_gemini import inspecionar
from geracao import GeradorDePlano
from geracao_v2 import GeradorDePlanoCompleto
from test_plano_v2 import FIXTURE_V2, pipeline
from test_contratos import FIXTURE


def documento(resultado, entrada):
    return {'versao':resultado['contrato'],'modo':resultado['modo'],'entrada':entrada,
            'rodadas':[{'rodada':1,'status':'ok',**resultado}]}


class TestInspecao(TestCase):
    def test_simulacao_nao_e_chamada_real(self):
        r = GeradorDePlanoCompleto().gerar(FIXTURE_V2['entrada'],0)
        resumo = inspecionar(documento(r,FIXTURE_V2['entrada']))
        self.assertEqual(resumo['modo_declarado'],'demonstracao')
        rodada = resumo['rodadas'][0]
        self.assertEqual(rodada['chamadas_gemini_registradas'],0)
        self.assertEqual(rodada['validacao_final'],'válido e igual à integração das etapas')

    def test_metadados_e_ausencia_de_usage(self):
        g,_ = pipeline()
        r = g.gerar(FIXTURE_V2['entrada'],0)
        r['rastreio'][0].pop('usage')
        rodada = inspecionar(documento(r,FIXTURE_V2['entrada']))['rodadas'][0]
        self.assertEqual(rodada['chamadas_gemini_registradas'],6)
        self.assertEqual(rodada['chamadas_com_usage'],5)
        self.assertEqual(rodada['tokens_conhecidos'],150)
        self.assertIsNone(rodada['etapas'][0]['tokens'])

    def test_plano_alterado_e_detectado(self):
        r = GeradorDePlanoCompleto().gerar(FIXTURE_V2['entrada'],0)
        r['plano']['objetivo_geral'] = 'Alterado após integração'
        resumo = inspecionar(documento(r,FIXTURE_V2['entrada']))
        self.assertIn('INVÁLIDO',resumo['rodadas'][0]['validacao_final'])

    def test_conteudo_bruto_invalido_bloqueia_dependentes(self):
        g,_ = pipeline()
        r = g.gerar(FIXTURE_V2['entrada'],0)
        r['rastreio'][0]['conteudo_bruto']='JSON inválido'
        rodada = inspecionar(documento(r,FIXTURE_V2['entrada']))['rodadas'][0]
        self.assertTrue(rodada['etapas'][0]['diagnosticos'])
        self.assertEqual(rodada['validacao_final'],'não há plano completo validado')

    def test_legacy_e_versao_desconhecida(self):
        r = GeradorDePlano().gerar(FIXTURE['entrada'],0)
        resumo = inspecionar(documento(r,FIXTURE['entrada']))
        self.assertEqual(resumo['rodadas'][0]['validacao_final'],'válido e igual à integração das etapas')
        d = documento(r,FIXTURE['entrada']);d['versao']='inexistente'
        with self.assertRaises(ValueError): inspecionar(d)
