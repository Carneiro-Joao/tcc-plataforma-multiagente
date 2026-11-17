"""O iniciador não grava credenciais e usa a configuração de rede validada."""
import io
import os
from unittest import TestCase
from unittest.mock import patch
import iniciar_prototipo


class TestIniciador(TestCase):
    def test_chave_da_janela_so_existe_durante_servidor(self):
        def servidor(argumentos):
            self.assertEqual(argumentos, ['--modo', 'lexical', '--gerador', 'ia', '--ipv4', '--abrir'])
            self.assertEqual(os.environ['GEMINI_API_KEY'], 'chave-ficticia-da-janela')
        with patch.dict(os.environ, {}, clear=True), \
             patch('iniciar_prototipo.solicitar_chave', return_value='chave-ficticia-da-janela'), \
             patch('iniciar_prototipo.iniciar_servidor', side_effect=servidor), \
             patch('sys.stdout', new_callable=io.StringIO) as saida:
            self.assertEqual(iniciar_prototipo.main(), 0)
            self.assertNotIn('GEMINI_API_KEY', os.environ)
            self.assertNotIn('chave-ficticia-da-janela', saida.getvalue())

    def test_cancelar_janela_nao_inicia_servidor(self):
        with patch.dict(os.environ, {}, clear=True), \
             patch('iniciar_prototipo.solicitar_chave', return_value=None), \
             patch('iniciar_prototipo.iniciar_servidor') as servidor, \
             patch('sys.stdout', new_callable=io.StringIO):
            self.assertEqual(iniciar_prototipo.main(), 0)
            servidor.assert_not_called()
            self.assertNotIn('GEMINI_API_KEY', os.environ)

    def test_preserva_chave_do_terminal_sem_solicitar_novamente(self):
        with patch.dict(os.environ, {'GEMINI_API_KEY': 'chave-ficticia-do-terminal'}, clear=True), \
             patch('iniciar_prototipo.solicitar_chave') as solicitar, \
             patch('iniciar_prototipo.iniciar_servidor', side_effect=SystemExit(1)):
            with self.assertRaises(SystemExit):
                iniciar_prototipo.main()
            solicitar.assert_not_called()
            self.assertEqual(os.environ['GEMINI_API_KEY'], 'chave-ficticia-do-terminal')
