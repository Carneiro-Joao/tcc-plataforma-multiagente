"""Servidor local da prova de conceito. Execute python app.py --help."""
import argparse
from getpass import getpass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
import os
from pathlib import Path
import re
from tempfile import TemporaryDirectory
from urllib.parse import urlsplit
import webbrowser
from rag.search import BASE, BuscaCurricular
from erros import ErroGeracao
from geracao_v2 import AgenteGeminiCompleto, GeradorDePlanoCompleto as GeradorDePlano
from gemini import MODELO_PADRAO
from rede import transporte_ipv4
from servico import ErroConsulta, ServicoCurricular
from juiz_servico import criar_juiz

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
            self.json(e.status, {"erro": str(e), **({"codigo": e.codigo} if getattr(e, "codigo", None) else {})})
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception:
            import traceback
            traceback.print_exc()
            self.json(HTTPStatus.INTERNAL_SERVER_ERROR, {"erro": "A consulta falhou. Confira o terminal do servidor."})

    do_GET = do_POST = responder


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--modo", choices=("lexical", "hibrido"), default="lexical")
    parser.add_argument("--porta", type=int, default=8000)
    parser.add_argument("--gerador", choices=("demonstracao", "ia"), default="demonstracao")
    parser.add_argument("--modelo", default=MODELO_PADRAO, help="Modelo usado com --gerador ia")
    parser.add_argument("--ipv4", action="store_true", help="Usa IPv4 nas chamadas ao Gemini nesta execução.")
    parser.add_argument("--pedir-chave", action="store_true", help="Solicita a chave com entrada oculta se GEMINI_API_KEY não estiver definida; não salva a chave.")
    parser.add_argument("--abrir", action="store_true", help="Abre o protótipo no navegador ao iniciar.")
    parser.add_argument("--banco", type=Path, default=BASE / "local" / "consultas.sqlite3", help="SQLite local para rastreabilidade técnica.")
    parser.add_argument("--temporario", action="store_true", help="Descartar dados ao encerrar; somente para demonstração descartável.")
    parser.add_argument("--reparos", type=int, choices=(0, 1), default=1, help="Reparos de contrato por especialista (não repete erros HTTP).")
    parser.add_argument("--repeticoes-503", type=int, choices=(0, 1, 2), default=2,
                        help="Novas tentativas com espera somente para HTTP 503, por chamada (padrão: 2).")
    parser.add_argument("--limite-diario", type=int, default=8,
                        help="Máximo de planos com IA por dia, contando falhas (padrão: 8; 0 = sem limite).")
    parser.add_argument("--juiz", choices=("groq", "demonstracao", "desligado"), default=None,
                        help="IA Juiz automática após cada geração. Padrão: groq se GROQ_API_KEY estiver definida, senão desligado. "
                             "'demonstracao' usa um parecer real gravado, sem rede.")
    parser.add_argument("--ciclos-juiz", type=int, default=1,
                        help="Regenerações automáticas quando o Juiz não dá parecer favorável (padrão: 1; 0 = não regenera).")
    parser.add_argument("--limite-diario-juiz", type=int, default=8,
                        help="Máximo de avaliações reais do Juiz por dia, contando falhas (padrão: 8; 0 = sem limite).")
    args = parser.parse_args(argv)
    if args.limite_diario < 0:
        parser.error("--limite-diario não pode ser negativo.")
    if args.ciclos_juiz < 0 or args.limite_diario_juiz < 0:
        parser.error("--ciclos-juiz e --limite-diario-juiz não podem ser negativos.")
    tem_chave_groq = bool(os.environ.get("GROQ_API_KEY", "").strip())
    modo_juiz = args.juiz or ("groq" if tem_chave_groq else "desligado")
    try:
        busca = BuscaCurricular(args.modo)
    except (ImportError, OSError, ValueError) as erro:
        parser.exit(1, f"Não foi possível iniciar a busca ({args.modo}): {erro}\n"
                       "Consulte a instalação do modo híbrido no README.md. Para testar sem modelo, use --modo lexical.\n")
    try:
        agente = None
        if args.gerador == "ia":
            chave = os.environ.get("GEMINI_API_KEY", "").strip()
            if args.pedir_chave and not chave:
                print("AulaIA: cole sua chave do Gemini e pressione Enter. A entrada fica oculta e não é salva.", flush=True)
                chave = getpass("Chave Gemini: ").strip()
            agente = AgenteGeminiCompleto(args.modelo, chave=chave,
                                         transporte=transporte_ipv4() if args.ipv4 else None,
                                         repeticoes_503=args.repeticoes_503)
        gerador = GeradorDePlano(args.gerador, args.modelo, agente=agente, reparos=args.reparos)
        juiz = criar_juiz(modo_juiz)
    except (EOFError, KeyboardInterrupt):
        parser.exit(1, "Inicialização cancelada.\n")
    except ErroGeracao as erro:
        parser.exit(1, f"Não foi possível iniciar a geração ou a IA Juiz: {erro}\n")
    try:
        servidor = ThreadingHTTPServer(("127.0.0.1", args.porta), Rotas)
    except OSError as erro:
        parser.exit(1, f"Não foi possível abrir a porta {args.porta}: {erro}\n")
    temporario = TemporaryDirectory(prefix="aulaia-") if args.temporario else None
    banco = Path(temporario.name) / "sessao.sqlite3" if temporario else args.banco
    limite = (args.limite_diario or None) if args.gerador == "ia" else None
    limite_juiz = (args.limite_diario_juiz or None) if modo_juiz == "groq" else None
    servidor.servico = ServicoCurricular(busca, banco, gerador, limite_diario_ia=limite, juiz=juiz,
                                         ciclos_juiz=args.ciclos_juiz, limite_diario_juiz=limite_juiz,
                                         pausa_juiz_s=75 if modo_juiz == "groq" else 0,
                                         pausa_juiz_413_s=120 if modo_juiz == "groq" else 0)
    print("Dados: " + ("somente nesta sessão; ao reiniciar, consulte novamente." if temporario else str(banco)), flush=True)
    if args.gerador == "ia":
        usados, _ = servidor.servico.uso_hoje()
        print(f"Limite: {limite} planos com IA por dia; usados hoje: {usados}." if limite else
              f"Limite diário DESLIGADO (--limite-diario 0); usados hoje: {usados}.", flush=True)
        print(f"Gemini: {args.modelo}; 6 chamadas normais, até {6 * (1 + args.reparos)} com reparos. Use projeto Free Tier no AI Studio.", flush=True)
        print("Conexão Gemini: " + ("IPv4" if args.ipv4 else "automática"), flush=True)
        print(f"HTTP 503: até {args.repeticoes_503} novas tentativas com espera por chamada. "
              f"Limite total com reparos e repetições: {6 * (1 + args.reparos) * (1 + args.repeticoes_503)} requisições.", flush=True)
    if modo_juiz == "desligado":
        print("IA Juiz: DESLIGADA" + ("" if args.juiz else " (GROQ_API_KEY não definida)") +
              "; os planos são entregues com 'avaliação não realizada'.", flush=True)
    else:
        usados_juiz, _ = servidor.servico.uso_juiz_hoje()
        print(f"IA Juiz: {modo_juiz} ({juiz.modelo}, {juiz.versao_prompt}, rubrica 0.1, politica-juiz-prelim-0.1); "
              f"ciclos automáticos: {args.ciclos_juiz}.", flush=True)
        if modo_juiz == "groq":
            print(f"Limite do Juiz: {limite_juiz} avaliações por dia; usadas hoje: {usados_juiz}." if limite_juiz else
                  f"Limite do Juiz DESLIGADO (--limite-diario-juiz 0); usadas hoje: {usados_juiz}.", flush=True)
        else:
            print("IA Juiz em DEMONSTRAÇÃO: parecer real gravado de outro plano, sem rede.", flush=True)
    url = f"http://127.0.0.1:{servidor.server_port}"
    print(f"AulaIA | {url} | busca {args.modo} | geração {args.gerador}", flush=True)
    try:
        if args.abrir:
            webbrowser.open(url)
        servidor.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        servidor.server_close()
        if temporario:
            temporario.cleanup()


if __name__ == "__main__":
    main()
