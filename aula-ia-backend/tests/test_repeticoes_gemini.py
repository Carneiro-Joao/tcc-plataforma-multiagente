"""503 transitório: espera limitada, rastreio e preservação das etapas anteriores."""
from contextlib import ExitStack
import io
import json
from unittest import TestCase
from unittest.mock import call, patch
from urllib.error import HTTPError, URLError
from erros import ErroGeracao
from test_contratos import FIXTURE
from test_gemini import CHAVE, gerador, respostas_validas


def indisponivel(codigo=503):
    corpo = {"error": {"code": codigo, "message": "This model is currently experiencing high demand. " + CHAVE}}
    return HTTPError("https://example.invalid", codigo, "erro", {}, io.BytesIO(json.dumps(corpo).encode()))


class TestRepeticoesGemini(TestCase):
    def setUp(self):
        contexto = ExitStack()
        self.addCleanup(contexto.close)
        self.esperar = contexto.enter_context(patch('gemini.time.sleep'))
        contexto.enter_context(patch('gemini.random.uniform', return_value=0.25))

    def test_recupera_etapa_sem_reexecutar_etapas_anteriores(self):
        respostas = respostas_validas()
        respostas[1:1] = [indisponivel(), indisponivel()]
        pipeline, transporte = gerador(respostas, repeticoes_503=2)
        resultado = pipeline.gerar(FIXTURE['entrada'], 0)
        self.assertEqual(resultado['plano'], FIXTURE['plano_esperado'])
        self.assertEqual(len(transporte.pedidos), 7)
        self.assertEqual(len(resultado['rastreio']), 6)
        self.assertEqual(resultado['rastreio'][0]['chamadas_http'], 1)
        registro = resultado['rastreio'][1]
        self.assertEqual(registro['chamadas_http'], 3)
        self.assertEqual(registro['http_status'], 200)
        self.assertNotIn('erro_corpo', registro)
        self.assertEqual([f['http_status'] for f in registro['falhas_http_transitorias']], [503, 503])
        self.assertTrue(all(p is transporte.pedidos[1] for p in transporte.pedidos[1:4]))
        self.assertEqual(self.esperar.call_args_list, [call(2.25), call(4.25)])
        self.assertNotIn(CHAVE, json.dumps(resultado))

    def test_encerra_apos_tres_503_sem_executar_dependentes(self):
        pipeline, transporte = gerador([indisponivel() for _ in range(3)], repeticoes_503=2)
        with self.assertRaises(ErroGeracao) as ctx:
            pipeline.gerar(FIXTURE['entrada'], 0)
        self.assertEqual(len(transporte.pedidos), 3)
        self.assertEqual(len(ctx.exception.rastreio), 1)
        registro = ctx.exception.rastreio[0]
        self.assertEqual(registro['http_status'], 503)
        self.assertEqual(registro['chamadas_http'], 3)
        self.assertEqual(len(registro['falhas_http_transitorias']), 2)
        self.assertEqual(self.esperar.call_count, 2)
        self.assertIn('3 tentativas', str(ctx.exception))
        self.assertIn('alta demanda', str(ctx.exception))
        self.assertNotIn(CHAVE, str(ctx.exception) + json.dumps(ctx.exception.rastreio))

    def test_outros_erros_encerram_sem_repeticao(self):
        for erro in [indisponivel(c) for c in (400, 401, 403, 404, 429, 500)] + [URLError('falha'), TimeoutError()]:
            with self.subTest(erro=type(erro).__name__, codigo=getattr(erro, 'code', None)):
                pipeline, transporte = gerador([erro], repeticoes_503=2)
                with self.assertRaises(ErroGeracao):
                    pipeline.gerar(FIXTURE['entrada'], 0)
                self.assertEqual(len(transporte.pedidos), 1)
        self.esperar.assert_not_called()

    def test_padrao_do_adaptador_preserva_sondagem_sem_repeticoes(self):
        pipeline, transporte = gerador([indisponivel()])
        with self.assertRaises(ErroGeracao):
            pipeline.gerar(FIXTURE['entrada'], 0)
        self.assertEqual(len(transporte.pedidos), 1)
        self.esperar.assert_not_called()
