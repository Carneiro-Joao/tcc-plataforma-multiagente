"""Regressão do HTTP 400 real: gramática menor sem relaxar o contrato local."""
from copy import deepcopy
import io
import json
from unittest import TestCase
from urllib.error import HTTPError
from contratos import plano_v2 as c
from contratos.esquema_gemini import esquema_api, VERSAO_ESQUEMA_API
from erros import ErroContrato, ErroGeracao
from test_plano_v2 import pipeline, respostas, FIXTURE_V2
from test_gemini import envelope


def http400(mensagem, razao=None):
    corpo = {'error': {'code':400,'status':'INVALID_ARGUMENT','message':mensagem}}
    if razao: corpo['error']['details'] = [{'reason':razao}]
    return HTTPError('https://generativelanguage.googleapis.com/',400,'Bad Request',{},io.BytesIO(json.dumps(corpo).encode()))


def conferir_estrutura(teste, completo, remoto):
    teste.assertEqual(completo['type'],remoto['type'])
    teste.assertTrue(set(remoto) <= {'type','description','properties','required','additionalProperties','items'})
    if completo['type']=='object':
        teste.assertEqual(set(completo['properties']),set(remoto['properties']))
        teste.assertEqual(completo['required'],remoto['required'])
        teste.assertFalse(remoto['additionalProperties'])
        for k,v in completo['properties'].items(): conferir_estrutura(teste,v,remoto['properties'][k])
    if completo['type']=='array': conferir_estrutura(teste,completo['items'],remoto['items'])


class TestEsquemaGemini(TestCase):
    def test_payload_das_seis_chamadas_preserva_campos_tipos_e_obrigatoriedade(self):
        original = deepcopy(c.SCHEMA)
        gerador, transporte = pipeline()
        resultado = gerador.gerar(FIXTURE_V2['entrada'],0)
        for nome,pedido,reg in zip(c.ETAPAS,transporte.pedidos,resultado['rastreio']):
            schema = json.loads(pedido.data)['generationConfig']['responseFormat']['text']['schema']
            conferir_estrutura(self,c.esquema(nome),schema)
            self.assertEqual(reg['versao_esquema_api'],VERSAO_ESQUEMA_API)
        self.assertEqual(c.SCHEMA,original)
        self.assertEqual(resultado['plano'],FIXTURE_V2['plano_esperado'])

    def test_limites_ficam_explicitos_no_schema_local_e_na_descricao_remota(self):
        remoto=esquema_api('sequencia')['properties']['etapas']
        local=c.esquema('sequencia')['properties']['etapas']
        self.assertEqual(local['maxItems'],12)
        self.assertIn('Quantidade máxima de itens: 12.',remoto['description'])
        self.assertNotIn('maxItems',remoto)
        self.assertIn('minimum',local['items']['properties']['minutos'])
        self.assertNotIn('minimum',remoto['items']['properties']['minutos'])
        remoto['items']['properties'].clear()
        self.assertIn('minutos',esquema_api('sequencia')['properties']['etapas']['items']['properties'])

    def test_validacao_local_rejeita_respostas_fora_das_regras_removidas_da_api(self):
        base=FIXTURE_V2['saidas']['sequencia']
        mutantes=[]
        d=deepcopy(base);d['etapas'][0]['minutos']=0;mutantes.append((d,'limite_invalido'))
        d=deepcopy(base);d['etapas'][0]['id']='ET0';mutantes.append((d,'formato_invalido'))
        d=deepcopy(base);d['etapas'][0]['titulo']=' ';mutantes.append((d,'texto_vazio'))
        d=deepcopy(base);d['etapas'][0]['objetivos_ids']=['OBJ1','OBJ1'];mutantes.append((d,'item_duplicado'))
        d=deepcopy(base);d['etapas']=[deepcopy(base['etapas'][0]) for _ in range(13)];mutantes.append((d,'quantidade_invalida'))
        d=deepcopy(base);d['etapas'][0]['minutos']+=1;mutantes.append((d,'soma_duracao'))
        for saida,regra in mutantes:
            with self.subTest(regra=regra):
                lista=respostas();lista[3]=envelope(saida)
                gerador, transporte=pipeline(lista,reparos=0)
                with self.assertRaises(ErroContrato) as erro: gerador.gerar(FIXTURE_V2['entrada'],0)
                self.assertIn(regra,[d['regra'] for d in erro.exception.diagnosticos])
                self.assertEqual(len(transporte.pedidos),4)
                self.assertEqual(erro.exception.rastreio[-1]['estado'],'rejeitado')

    def test_erro_real_de_complexidade_preserva_tres_sucessos_e_nao_repete(self):
        mensagem='The specified schema produces a constraint that has too many states for serving.'
        gerador, transporte=pipeline(respostas()[:3]+[http400(mensagem)])
        with self.assertRaises(ErroGeracao) as erro: gerador.gerar(FIXTURE_V2['entrada'],0)
        self.assertEqual(erro.exception.tipo,'esquema_api')
        self.assertIn('complexidade',str(erro.exception))
        self.assertEqual(len(transporte.pedidos),4)
        self.assertEqual([a['estado'] for a in erro.exception.rastreio],['validado']*3+['falha'])
        self.assertIn(mensagem,erro.exception.rastreio[-1]['erro_corpo'])

    def test_diagnostica_chave_invalida_sem_mudar_outros_erros_http(self):
        for mensagem,razao,tipo in [('API key not valid.','API_KEY_INVALID','autenticacao'),('Outro erro',None,'http')]:
            with self.subTest(tipo=tipo):
                gerador, transporte=pipeline([http400(mensagem,razao)])
                with self.assertRaises(ErroGeracao) as erro: gerador.gerar(FIXTURE_V2['entrada'],0)
                self.assertEqual(erro.exception.tipo,tipo)
                self.assertEqual(len(transporte.pedidos),1)
