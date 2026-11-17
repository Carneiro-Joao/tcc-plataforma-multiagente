"""O contorno IPv4 mantém TLS, isolamento e erros de conexão visíveis."""
import socket
import ssl
from unittest import TestCase
from unittest.mock import Mock, patch
from rede import _conectar_ipv4, _ConexaoHTTPSIPv4


ENDERECOS = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("192.0.2.1", 443)),
             (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("192.0.2.2", 443))]


class TestRede(TestCase):
    def test_ipv4_preserva_hostname_e_verificacao_tls(self):
        contexto = ssl.create_default_context()
        conexao = _ConexaoHTTPSIPv4("generativelanguage.googleapis.com", timeout=7, context=contexto)
        socket_falso = Mock()
        with patch("rede.socket.getaddrinfo", return_value=ENDERECOS) as resolver, \
             patch("rede.socket.create_connection", return_value=socket_falso) as conectar, \
             patch.object(contexto, "wrap_socket") as tls:
            conexao.connect()
        resolver.assert_called_once_with("generativelanguage.googleapis.com", 443, socket.AF_INET, socket.SOCK_STREAM)
        conectar.assert_called_once_with(("192.0.2.1", 443), 7, None)
        tls.assert_called_once_with(socket_falso, server_hostname="generativelanguage.googleapis.com")
        self.assertTrue(contexto.check_hostname)
        self.assertEqual(contexto.verify_mode, ssl.CERT_REQUIRED)

    def test_tenta_outro_ipv4_apenas_se_socket_nao_conectou(self):
        socket_falso = Mock()
        with patch("rede.socket.getaddrinfo", return_value=ENDERECOS), \
             patch("rede.socket.create_connection", side_effect=[ConnectionRefusedError(), socket_falso]) as conectar:
            resultado = _conectar_ipv4(("example.invalid", 443), 9, None)
        self.assertIs(resultado, socket_falso)
        self.assertEqual(conectar.call_count, 2)
        conectar.assert_called_with(("192.0.2.2", 443), 9, None)

    def test_falha_de_conexao_nao_e_ocultada(self):
        erro = ConnectionResetError(10054, "conexão encerrada")
        with patch("rede.socket.getaddrinfo", return_value=ENDERECOS), \
             patch("rede.socket.create_connection", side_effect=erro):
            with self.assertRaises(ConnectionResetError) as ctx:
                _conectar_ipv4(("example.invalid", 443), 9, None)
        self.assertIs(ctx.exception, erro)

    def test_resolucao_sem_ipv4_informa_falha(self):
        with patch("rede.socket.getaddrinfo", return_value=[]):
            with self.assertRaisesRegex(OSError, "Nenhum endereço IPv4"):
                _conectar_ipv4(("example.invalid", 443), 9, None)
