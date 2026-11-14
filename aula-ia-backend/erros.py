"""Erros públicos sem credenciais e com rastreio da execução interrompida."""


class ErroGeracao(Exception):
    def __init__(self, mensagem, tipo="geracao"):
        super().__init__(mensagem)
        self.tipo = tipo
        self.rastreio = []


class ErroContrato(ErroGeracao):
    def __init__(self, mensagem):
        super().__init__(mensagem, tipo="contrato")
