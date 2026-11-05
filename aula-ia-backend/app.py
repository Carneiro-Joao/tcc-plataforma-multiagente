"""Servidor local da prova de conceito. Execute python app.py --help."""
import argparse
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
from pathlib import Path
import re
from urllib.parse import urlsplit
from rag.search import BASE, BuscaCurricular
from geracao import GeradorDePlano, ErroGeracao
from servico import ErroConsulta, ServicoCurricular

DIST = BASE.parent / "aula-ia" / "dist"
CONSULTA = re.compile(r"/api/consultas/([0-9a-f]{32})(?:/(confirmar|entrada-geracao|gerar))?")
APROVACAO = re.compile(r"/api/geracoes/([0-9a-f]{32})/aprovar")


class Rotas(BaseHTTPRequestHandler):
    def enviar(self, status, conteudo, tipo):
        self.send_response(status)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(conteudo)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(conteudo)

    def json(self, status, objeto):
        self.enviar(status, json.dumps(objeto, ensure_ascii=False).encode(), "application/json; charset=utf-8")

    def corpo(self):
        if self.headers.get_content_type() != "application/json":
            raise ErroConsulta(415, "Envie o pedido como JSON.")
        try:
            tamanho = int(self.headers.get("Content-Length", 0))
            if not 0 < tamanho <= 16384:
                raise ErroConsulta(413, "Tamanho da requisição inválido.")
            dados = json.loads(self.rfile.read(tamanho))
        except (ValueError, UnicodeError):
            raise ErroConsulta(400, "JSON inválido.") from None
        if not isinstance(dados, dict):
            raise ErroConsulta(400, "Envie um objeto JSON.")
        return dados

    def atender(self):
        rota = urlsplit(self.path).path
        servico = self.server.servico
        if self.command == "POST" and rota == "/api/consultas":
            return self.json(201, servico.consultar(self.corpo()))
        aprovar = APROVACAO.fullmatch(rota)
        if self.command == "POST" and aprovar:
            return self.json(200, servico.aprovar(aprovar.group(1)))
        match = CONSULTA.fullmatch(rota)
        if match:
            ident, acao = match.groups()
            if self.command == "POST" and acao == "confirmar":
                return self.json(200, servico.confirmar(ident, self.corpo().get("codigo")))
            if self.command == "POST" and acao == "gerar":
                self.corpo()  # exige JSON válido, mesmo que vazio
                return self.json(201, servico.gerar(ident))
            if self.command == "GET" and acao in (None, "entrada-geracao"):
                consulta = servico.obter(ident)
                if acao and not consulta["entrada_geracao"]:
                    raise ErroConsulta(409, "Confirme uma habilidade antes da geração.")
                return self.json(200, consulta["entrada_geracao"] if acao else consulta)
        if self.command == "GET":
            if rota == "/fonte/BNCCComputacao.pdf":
                arquivo = BASE / "data" / "BNCCComputacao.pdf"
            elif rota == "/":
                arquivo = DIST / "index.html"
            elif re.fullmatch(r"/(?:assets/)?[\w.-]+", rota):
                arquivo = (DIST / rota[1:]).resolve()
            else:
                arquivo = None
            if arquivo and arquivo.is_file():
                tipos_web = {".js": "text/javascript", ".css": "text/css", ".pdf": "application/pdf"}
                tipo = tipos_web.get(arquivo.suffix) or mimetypes.guess_type(str(arquivo))[0] or "application/octet-stream"
                return self.enviar(200, arquivo.read_bytes(), tipo)
        raise ErroConsulta(404, "Recurso não encontrado.")

    def responder(self):
        try:
            self.atender()
        except ErroConsulta as e:
            self.json(e.status, {"erro": str(e)})
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception:
            import traceback
            traceback.print_exc()
            self.json(HTTPStatus.INTERNAL_SERVER_ERROR, {"erro": "A consulta falhou. Confira o terminal do servidor."})

    do_GET = do_POST = responder


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--modo", choices=("lexical", "hibrido"), default="lexical")
    parser.add_argument("--porta", type=int, default=8000)
    parser.add_argument("--gerador", choices=("demonstracao", "ia"), default="demonstracao")
    parser.add_argument("--modelo", default="gpt-4o-mini", help="Modelo usado com --gerador ia")
    parser.add_argument("--banco", type=Path, default=BASE / "local" / "consultas.sqlite3")
    args = parser.parse_args()
    try:
        busca = BuscaCurricular(args.modo)
    except (ImportError, OSError, ValueError) as erro:
        parser.exit(1, f"Não foi possível iniciar a busca ({args.modo}): {erro}\n"
                       "Consulte a instalação do modo híbrido no README.md. Para testar sem modelo, use --modo lexical.\n")
    try:
        gerador = GeradorDePlano(args.gerador, args.modelo)
    except ErroGeracao as erro:
        parser.exit(1, f"Não foi possível iniciar a geração: {erro}\n")
    servidor = ThreadingHTTPServer(("127.0.0.1", args.porta), Rotas)
    servidor.servico = ServicoCurricular(busca, args.banco, gerador)
    print(f"AulaIA | http://127.0.0.1:{servidor.server_port} | busca {args.modo} | geração {args.gerador}", flush=True)
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        servidor.server_close()


if __name__ == "__main__":
    main()
