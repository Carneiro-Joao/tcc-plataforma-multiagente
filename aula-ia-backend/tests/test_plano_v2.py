"""Contrato completo: mutações inválidas, relações, isolamento e protocolo simulado."""
from copy import deepcopy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from urllib.error import URLError
from contratos import plano_v2 as c
from erros import ErroContrato, ErroGeracao
from geracao_v2 import AgenteGeminiCompleto, GeradorDePlanoCompleto, esquema_gemini
from rag.search import BuscaCurricular
from servico import ServicoCurricular, ErroConsulta, abrir_banco, habilidade_publica
from test_gemini import Transporte, envelope, CHAVE

FIXTURE_V2 = json.loads((Path(__file__).parent / 'dados/plano_v2/fixture_ordenacao.json').read_text(encoding='utf-8'))


def respostas():
    return [envelope(FIXTURE_V2['saidas'][nome]) for nome in c.ETAPAS]


def pipeline(respostas_api=None, reparos=1):
    transporte = Transporte(respostas() if respostas_api is None else respostas_api)
    agente = AgenteGeminiCompleto(chave=CHAVE, transporte=transporte)
    return GeradorDePlanoCompleto('ia', agente=agente, reparos=reparos), transporte


class TestPlanoCompleto(TestCase):
    def setUp(self):
        self.entrada = deepcopy(FIXTURE_V2['entrada'])
        self.plano = deepcopy(FIXTURE_V2['plano_esperado'])
        self.estado = deepcopy(FIXTURE_V2['saidas'])

    def rejeita(self, regra):
        diagnosticos = c.diagnosticar('plano', self.plano, self.entrada)
        self.assertIn(regra, [d['regra'] for d in diagnosticos], diagnosticos)
        self.assertTrue(all(d['caminho'] for d in diagnosticos))

    def test_onze_secoes_e_fixture_preservada(self):
        self.assertEqual(set(self.plano), {'identificacao','habilidade_bncc','conteudos','objetivo_geral',
            'objetivos_especificos','metodologia','recursos','desenvolvimento','avaliacao_aprendizagem','adaptacoes','referencias'})
        original = deepcopy((self.entrada, self.estado))
        self.assertEqual(c.integrar(self.entrada, self.estado), self.plano)
        self.assertEqual((self.entrada, self.estado), original)
        c.validar('plano', self.plano, self.entrada)
        habilidade = next(h for h in BuscaCurricular().documentos if h['codigo']=='EF08CO03')
        self.assertEqual(habilidade_publica(habilidade), self.entrada['habilidade'])

    def test_nao_coage_minutos_nem_metodologia(self):
        for valor in ('8', 8.0, True, None, 0, -1):
            with self.subTest(valor=valor):
                self.plano = deepcopy(FIXTURE_V2['plano_esperado'])
                self.plano['desenvolvimento'][0]['minutos'] = valor
                self.rejeita('tipo_invalido' if type(valor) is not int else 'limite_invalido')
        self.plano = deepcopy(FIXTURE_V2['plano_esperado'])
        self.plano['metodologia'] = {'texto':'não deve converter'}
        self.rejeita('tipo_invalido')

    def test_campos_ausentes_extras_e_textos_vazios(self):
        del self.plano['objetivo_geral']
        self.rejeita('campo_ausente')
        self.plano = deepcopy(FIXTURE_V2['plano_esperado'])
        self.plano['desenvolvimento'][0]['inventado'] = 'x'
        self.rejeita('campo_extra')
        del self.plano['desenvolvimento'][0]['inventado']
        self.plano['objetivo_geral'] = ' \n '
        self.rejeita('texto_vazio')

    def test_invariantes_da_entrada_e_fonte(self):
        alvos = [('identificacao','ano'),('identificacao','tema'),('identificacao','tipo'),
                 ('identificacao','titulo'),('habilidade_bncc','codigo'),('habilidade_bncc','descricao'),
                 ('habilidade_bncc','eixo'),('habilidade_bncc','objeto_conhecimento')]
        for grupo, campo in alvos:
            with self.subTest(campo=campo):
                self.plano = deepcopy(FIXTURE_V2['plano_esperado'])
                self.plano[grupo][campo] += ' alterado'
                self.rejeita('entrada_preservada')
        self.plano = deepcopy(FIXTURE_V2['plano_esperado'])
        self.plano['habilidade_bncc']['referencia']['sha256_catalogo'] = '0'*64
        self.rejeita('entrada_preservada')
        self.plano = deepcopy(FIXTURE_V2['plano_esperado'])
        self.plano['referencias'][0]['titulo'] = 'Fonte inventada'
        self.rejeita('entrada_preservada')
        self.plano = deepcopy(FIXTURE_V2['plano_esperado'])
        self.plano['recursos'] += ', projetor'
        self.rejeita('entrada_preservada')

    def test_ids_duplicados_e_referencias_inexistentes(self):
        self.plano['objetivos_especificos'][1]['id'] = 'OBJ1'
        self.rejeita('id_duplicado')
        self.plano = deepcopy(FIXTURE_V2['plano_esperado'])
        self.plano['desenvolvimento'][0]['evidencias_ids'] = ['EVI99']
        self.rejeita('referencia_inexistente')
        self.plano = deepcopy(FIXTURE_V2['plano_esperado'])
        self.plano['adaptacoes'][0]['etapas_ids'] = ['ET99']
        self.rejeita('referencia_inexistente')

    def test_todos_objetivos_tem_evidencia(self):
        self.plano['avaliacao_aprendizagem']['evidencias'][1]['objetivo_id'] = 'OBJ1'
        self.rejeita('cobertura_incompleta')

    def test_todas_evidencias_tem_atividade(self):
        for etapa in self.plano['desenvolvimento']:
            etapa['objetivos_ids'] = ['OBJ1']
            etapa['evidencias_ids'] = ['EVI1']
        self.rejeita('cobertura_incompleta')

    def test_objetivo_da_etapa_corresponde_as_evidencias(self):
        self.plano['desenvolvimento'][0]['objetivos_ids'] = ['OBJ1']
        self.rejeita('vinculo_objetivo_evidencia_incoerente')

    def test_avaliacao_cobre_evidencias_e_usa_etapas_corretas(self):
        instrumento = self.plano['avaliacao_aprendizagem']['instrumentos'][0]
        instrumento['evidencias_ids'] = ['EVI1']
        self.rejeita('cobertura_incompleta')
        instrumento['evidencias_ids'] = ['EVI1','EVI2']
        instrumento['etapas_ids'] = ['ET1']
        self.plano['desenvolvimento'][0]['objetivos_ids'] = ['OBJ1']
        self.plano['desenvolvimento'][0]['evidencias_ids'] = ['EVI1']
        self.rejeita('evidencia_fora_das_etapas')

    def test_adaptacao_preserva_vinculos(self):
        self.plano['desenvolvimento'][0]['objetivos_ids'] = ['OBJ1']
        self.plano['desenvolvimento'][0]['evidencias_ids'] = ['EVI1']
        self.plano['adaptacoes'][0]['objetivos_ids'] = ['OBJ2']
        self.plano['adaptacoes'][0]['etapas_ids'] = ['ET1']
        self.rejeita('objetivo_fora_das_etapas')

    def test_soma_exata(self):
        self.plano['desenvolvimento'][0]['minutos'] += 1
        self.rejeita('soma_duracao')

    def test_dependencia_ausente_nao_e_inventada(self):
        del self.estado['avaliacao_preliminar']
        with self.assertRaises(ErroContrato): c.integrar(self.entrada, self.estado)

    def test_entrada_sem_proveniencia_falha_antes_da_api(self):
        del self.entrada['habilidade']['referencia']
        gerador, transporte = pipeline()
        with self.assertRaises(ErroContrato): gerador.gerar(self.entrada,0)
        self.assertEqual(len(transporte.pedidos),0)

    def test_simulacao_curta_e_revisao_sem_mudar_catalogo(self):
        for tempo in (1,2,3,45,50,1440):
            with self.subTest(tempo=tempo):
                self.entrada['contexto']['duracao_min'] = tempo
                r = GeradorDePlanoCompleto().gerar(self.entrada,1)
                c.validar('plano',r['plano'],self.entrada)
                self.assertEqual(len(r['rastreio']),7)
                self.assertEqual(r['avaliacao_pedagogica'],'pendente')

    def test_seis_chamadas_e_duas_passagens_de_avaliacao(self):
        gerador, transporte = pipeline()
        r = gerador.gerar(self.entrada,0)
        self.assertEqual(r['contrato'],c.VERSAO)
        self.assertEqual(r['plano'],self.plano)
        self.assertEqual(len(transporte.pedidos),6)
        self.assertEqual([a['agente'] for a in r['rastreio']],list(c.ETAPAS)+['integrador'])
        for nome, pedido in zip(c.ETAPAS,transporte.pedidos):
            corpo = json.loads(pedido.data)
            dados = json.loads(corpo['contents'][0]['parts'][0]['text'])
            self.assertEqual(set(dados['saidas_anteriores']),set(c.DEPENDENCIAS[nome]))
            self.assertEqual(corpo['generationConfig']['responseFormat']['text']['schema'],esquema_gemini(nome))
        self.assertNotIn(CHAVE,json.dumps(r))

    def test_schema_gemini_preserva_estrutura_e_contrato_local(self):
        original = deepcopy(c.SCHEMA)
        restricoes = {'minItems', 'maxItems', 'minimum', 'maximum', 'minLength', 'maxLength', 'pattern', 'uniqueItems'}

        def conferir(local, enviado):
            self.assertEqual(enviado['type'], local['type'])
            self.assertFalse(restricoes & enviado.keys())
            if restricoes & local.keys():
                self.assertTrue(enviado['description'])
            if local['type'] == 'object':
                self.assertEqual(enviado['required'], local['required'])
                self.assertFalse(enviado['additionalProperties'])
                self.assertEqual(set(enviado['properties']), set(local['properties']))
                for campo in local['properties']:
                    conferir(local['properties'][campo], enviado['properties'][campo])
            elif local['type'] == 'array':
                conferir(local['items'], enviado['items'])

        for nome in c.ETAPAS:
            with self.subTest(agente=nome):
                conferir(c.esquema(nome), esquema_gemini(nome))
        self.assertEqual(c.SCHEMA, original)
        sequencia = esquema_gemini('sequencia')['properties']['etapas']
        self.assertIn('Quantidade máxima de itens: 12.', sequencia['description'])
        self.assertIn('Valor mínimo: 1.', sequencia['items']['properties']['minutos']['description'])

    def test_limites_locais_bloqueiam_respostas_apos_simplificar_schema_api(self):
        casos = [('minutos', 0, 'limite_invalido'),
                 ('id', 'fase-1', 'formato_invalido'),
                 ('objetivos_ids', [], 'quantidade_invalida'),
                 ('objetivos_ids', ['OBJ1', 'OBJ1'], 'item_duplicado'),
                 ('atividade', ' ', 'texto_vazio')]
        for campo, valor, regra in casos:
            with self.subTest(campo=campo, valor=valor):
                ruim = deepcopy(self.estado['sequencia'])
                ruim['etapas'][0][campo] = valor
                gerador, transporte = pipeline(respostas()[:3] + [envelope(ruim)], reparos=0)
                with self.assertRaises(ErroContrato) as ctx:
                    gerador.gerar(self.entrada, 0)
                rejeitada = ctx.exception.rastreio[-1]
                self.assertEqual(rejeitada['estado'], 'rejeitado')
                self.assertIn(regra, [d['regra'] for d in rejeitada['diagnosticos']])
                self.assertEqual(len(transporte.pedidos), 4)

    def test_reparo_local_conserva_tentativa_e_dependencias(self):
        lista = respostas()
        ruim = deepcopy(self.estado['sequencia'])
        ruim['etapas'][0]['minutos'] += 2
        lista.insert(3,envelope(ruim))
        gerador, transporte = pipeline(lista)
        r = gerador.gerar(self.entrada,0)
        self.assertEqual(len(transporte.pedidos),7)
        self.assertEqual(r['plano'],self.plano)
        rejeitada, reparada = r['rastreio'][3:5]
        self.assertEqual(rejeitada['estado'],'rejeitado')
        self.assertEqual(rejeitada['entrada'],reparada['entrada'])
        self.assertEqual(reparada['tentativa'],2)
        self.assertEqual(rejeitada['saida'],ruim)

    def test_limite_de_reparo_e_parada_de_dependentes(self):
        gerador, transporte = pipeline(respostas()[:3]+[envelope({}),envelope({})])
        with self.assertRaises(ErroContrato) as e: gerador.gerar(self.entrada,0)
        self.assertEqual(len(transporte.pedidos),5)
        self.assertEqual(e.exception.rastreio[-1]['agente'],'sequencia')
        self.assertEqual(e.exception.rastreio[-1]['tentativa'],2)

    def test_maximo_de_doze_chamadas_com_reparo_em_todas(self):
        lista = [v for r in respostas() for v in (envelope({}),r)]
        gerador, transporte = pipeline(lista)
        self.assertEqual(gerador.gerar(self.entrada,0)['plano'],self.plano)
        self.assertEqual(len(transporte.pedidos),12)

    def test_falha_parcial_persistida_e_versao_anterior_lida(self):
        with TemporaryDirectory() as pasta:
            gerador, _ = pipeline(respostas()[:3]+[URLError('falha simulada')])
            banco = Path(pasta)/'teste.sqlite3'
            servico = ServicoCurricular(BuscaCurricular(),banco,gerador=gerador)
            consulta = servico.consultar({'contexto':self.entrada['contexto'],'consulta':'catalogo'})
            servico.confirmar(consulta['id'],'EF08CO03')
            with self.assertRaises(ErroConsulta): servico.gerar(consulta['id'])
            falha = servico.obter(consulta['id'])['geracao_atual']
            self.assertEqual(falha['estado'],'falha')
            self.assertEqual(len(falha['resultado']['rastreio']),4)
            self.assertNotIn('plano',falha['resultado'])
            with self.assertRaises(ErroConsulta): servico.aprovar(falha['id'])
            from test_contratos import FIXTURE
            legado={'contrato':'poc04a-0.1','plano':FIXTURE['plano_esperado']}
            with abrir_banco(banco) as db:
                db.execute("UPDATE geracoes SET estado='rascunho', resultado=? WHERE id=?",(json.dumps(legado),falha['id']))
            reaberto = ServicoCurricular(BuscaCurricular(),banco)
            self.assertEqual(reaberto.obter(consulta['id'])['geracao_atual']['resultado'],legado)
