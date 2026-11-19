"""Inicialização do protótipo: chave em memória e transporte escolhido no CLI."""
from contextlib import ExitStack
import io
import os
from unittest import TestCase
from unittest.mock import Mock, patch
import app
from geracao_v2 import AgenteGeminiCompleto


class TestInicializacao(TestCase):
    def setUp(self):
        self.contexto = ExitStack()
        self.addCleanup(self.contexto.close)
        self.contexto.enter_context(patch.dict(os.environ, {}, clear=True))
        self.saida = self.contexto.enter_context(patch('sys.stdout', new_callable=io.StringIO))
        self.pedir = self.contexto.enter_context(patch('app.getpass', return_value='chave-ficticia-do-teste'))
        self.abrir = self.contexto.enter_context(patch('app.webbrowser.open'))
        self.transporte = Mock()
        self.criar_transporte = self.contexto.enter_context(patch('app.transporte_ipv4', return_value=self.transporte))
        self.servico = self.contexto.enter_context(patch('app.ServicoCurricular'))
        self.servico.return_value.uso_hoje.return_value = (0, 5)
        self.servidor = self.contexto.enter_context(patch('app.ThreadingHTTPServer')).return_value
        self.servidor.server_port = 8000
        self.servidor.serve_forever.side_effect = KeyboardInterrupt()

    def test_ia_ipv4_com_chave_oculta_abre_prototipo(self):
        app.main(['--gerador', 'ia', '--ipv4', '--pedir-chave', '--abrir'])
        gerador = self.servico.call_args.args[2]
        self.assertEqual(gerador.modo, 'ia')
        self.assertIsInstance(gerador.agente, AgenteGeminiCompleto)
        self.assertIs(gerador.agente.transporte, self.transporte)
        self.assertEqual(gerador.agente.repeticoes_503, 2)
        self.assertEqual(gerador.agente.chave, 'chave-ficticia-do-teste')
        self.assertNotIn('chave-ficticia-do-teste', self.saida.getvalue())
        self.assertNotIn('GEMINI_API_KEY', os.environ)
        self.pedir.assert_called_once()
        self.abrir.assert_called_once_with('http://127.0.0.1:8000')
        self.servidor.serve_forever.assert_called_once()
        self.servidor.server_close.assert_called_once()

    def test_chave_do_ambiente_dispensa_nova_solicitacao(self):
        with patch.dict(os.environ, {'GEMINI_API_KEY': 'chave-ficticia-do-ambiente'}):
            app.main(['--gerador', 'ia', '--ipv4', '--pedir-chave', '--repeticoes-503', '0'])
        self.pedir.assert_not_called()
        self.abrir.assert_not_called()
        self.assertEqual(self.servico.call_args.args[2].agente.chave, 'chave-ficticia-do-ambiente')
        self.assertEqual(self.servico.call_args.args[2].agente.repeticoes_503, 0)
        self.assertNotIn('chave-ficticia-do-ambiente', self.saida.getvalue())

    def test_demonstracao_dispensa_chave_e_transporte(self):
        app.main(['--gerador', 'demonstracao', '--ipv4', '--pedir-chave'])
        self.assertEqual(self.servico.call_args.args[2].modo, 'demonstracao')
        self.pedir.assert_not_called()
        self.criar_transporte.assert_not_called()
        self.abrir.assert_not_called()
