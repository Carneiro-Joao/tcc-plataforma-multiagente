"""Transporte HTTPS IPv4 opcional, sem alterar a resolução global do processo."""
from http.client import HTTPSConnection
import socket
from urllib import request


def _conectar_ipv4(endereco, timeout, origem):
    host, porta = endereco
    ultimo_erro = None
    for _, _, _, _, destino in socket.getaddrinfo(host, porta, socket.AF_INET, socket.SOCK_STREAM):
        try:
            return socket.create_connection(destino, timeout, origem)
        except OSError as exc:
            ultimo_erro = exc
    if ultimo_erro is not None:
        raise ultimo_erro
    raise OSError("Nenhum endereço IPv4 disponível para o serviço.")


class _ConexaoHTTPSIPv4(HTTPSConnection):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apenas a abertura do socket muda. Host, SNI e verificação do
        # certificado continuam sob responsabilidade de HTTPSConnection.
        self._create_connection = _conectar_ipv4


class _HandlerHTTPSIPv4(request.HTTPSHandler):
    def https_open(self, pedido):
        return self.do_open(_ConexaoHTTPSIPv4, pedido, context=self._context)


def transporte_ipv4():
    """Preserva proxies configurados e não repete requisições HTTP."""
    return request.build_opener(_HandlerHTTPSIPv4()).open
