"""Consultas, confirmação curricular, revisões e aprovação docente."""
from contextlib import contextmanager
import json
from pathlib import Path
import sqlite3
from uuid import uuid4
from geracao import GeradorDePlano, ErroGeracao

from rag.search import FONTE

@contextmanager
def abrir_banco(caminho):
    """Confirma ou desfaz a transação e sempre fecha a conexão SQLite."""
    con = sqlite3.connect(caminho, timeout=20)
    try:
        with con:
            yield con
    finally:
        con.close()


TIPOS = ("Computação desplugada", "Aula prática", "Aula teórica", "Projeto")


class ErroConsulta(Exception):
    def __init__(self, status, mensagem):
        super().__init__(mensagem)
        self.status = status


def texto_valido(valor, nome, limite):
    if not isinstance(valor, str) or not 0 < len(valor.strip()) <= limite:
        raise ErroConsulta(422, f"Informe {nome} com até {limite} caracteres.")
    return valor.strip()


def validar_contexto(dados, ano):
    if not isinstance(dados, dict):
        raise ErroConsulta(422, "Informe o contexto da aula.")
    if dados.get("ano") != ano:
        raise ErroConsulta(422, f"O catálogo disponível corresponde ao {ano}.")
    minutos = dados.get("duracao_min")
    if type(minutos) is not int or not 1 <= minutos <= 1440:
        raise ErroConsulta(422, "Informe uma duração inteira de 1 a 1440 minutos.")
    if dados.get("tipo") not in TIPOS:
        raise ErroConsulta(422, "Selecione um tipo de aula válido.")
    return dict(ano=ano, tema=texto_valido(dados.get("tema"), "o tema", 800),
                duracao_min=minutos, recursos=texto_valido(dados.get("recursos"), "os recursos", 800),
                tipo=dados["tipo"])


def habilidade_publica(doc):
    campos = ("codigo", "eixo", "objeto_conhecimento", "habilidade", "explicacao", "exemplos")
    return {**{k: doc[k] for k in campos}, "referencia": {
        "documento": FONTE, "arquivo": "BNCCComputacao.pdf",
        "pagina_habilidade": doc["pagina_habilidade"], "pagina_exemplos": doc["pagina_pdf"],
    }}


def visao(registro):
    dados, codigo = registro
    consulta = json.loads(dados)
    consulta["entrada_geracao"] = None
    if codigo:
        habilidade = next(r["habilidade"] for r in consulta["resultados"] if r["habilidade"]["codigo"] == codigo)
        consulta["entrada_geracao"] = dict(versao="1.0", consulta_id=consulta["id"],
                                          contexto=consulta["contexto"], habilidade=habilidade)
    return consulta


class ServicoCurricular:
    def __init__(self, busca, banco, gerador=None):
        self.busca = busca
        self.gerador = gerador or GeradorDePlano()
        self.banco = Path(banco)
        self.banco.parent.mkdir(parents=True, exist_ok=True)
        with abrir_banco(self.banco) as db:
            db.execute("""CREATE TABLE IF NOT EXISTS consultas
                          (id TEXT PRIMARY KEY, dados TEXT NOT NULL, codigo_confirmado TEXT)""")
            db.execute("""CREATE TABLE IF NOT EXISTS geracoes
                          (id TEXT PRIMARY KEY, consulta_id TEXT NOT NULL, revisao INTEGER NOT NULL,
                           estado TEXT NOT NULL, resultado TEXT,
                           criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                           UNIQUE(consulta_id, revisao),
                           FOREIGN KEY (consulta_id) REFERENCES consultas(id))""")

    def consultar(self, pedido):
        contexto = validar_contexto(pedido.get("contexto"), self.busca.ano)
        modo = pedido.get("consulta", "tema")
        if modo == "catalogo":
            docs = self.busca.documentos
        elif modo == "tema":
            docs = self.busca.buscar(contexto["tema"])
        else:
            raise ErroConsulta(422, "Escolha a consulta por tema ou o catálogo completo.")
        resultados = []
        for doc in docs:
            detalhe = None
            if modo == "tema":
                detalhe = {k: doc[k] for k in ("score_semantico", "bonus", "score_final")}
            resultados.append(dict(habilidade=habilidade_publica(doc), pontuacao=detalhe))
        consulta = dict(id=uuid4().hex, contexto=contexto, consulta=modo,
                        metodo=self.busca.modo if modo == "tema" else "catalogo", resultados=resultados)
        dados = json.dumps(consulta, ensure_ascii=False)
        with abrir_banco(self.banco) as db:
            db.execute("INSERT INTO consultas (id, dados) VALUES (?, ?)", (consulta["id"], dados))
        return self.obter(consulta["id"])

    @staticmethod
    def _geracao_atual(db, id_consulta):
        row = db.execute("""SELECT id, revisao, estado, resultado, criado_em FROM geracoes
                            WHERE consulta_id = ? ORDER BY revisao DESC LIMIT 1""",
                         (id_consulta,)).fetchone()
        if row is None:
            return None
        ident, revisao, estado, resultado, criado = row
        return dict(id=ident, revisao=revisao, estado=estado,
                    resultado=json.loads(resultado) if resultado else None, criado_em=criado)

    @classmethod
    def _ler(cls, db, id_consulta):
        registro = db.execute("SELECT dados, codigo_confirmado FROM consultas WHERE id = ?",
                              (id_consulta,)).fetchone()
        if registro is None:
            raise ErroConsulta(404, "Consulta não encontrada. Faça uma nova consulta.")
        consulta = visao(registro)
        consulta["geracao_atual"] = cls._geracao_atual(db, id_consulta)
        return consulta

    def obter(self, id_consulta):
        with abrir_banco(self.banco) as db:
            return self._ler(db, id_consulta)

    def confirmar(self, id_consulta, codigo):
        with abrir_banco(self.banco) as db:
            db.execute("BEGIN IMMEDIATE")
            consulta = self._ler(db, id_consulta)
            if codigo not in [r["habilidade"]["codigo"] for r in consulta["resultados"]]:
                raise ErroConsulta(422, "Escolha uma das habilidades retornadas pela consulta.")
            anterior = consulta["entrada_geracao"]
            if anterior and anterior["habilidade"]["codigo"] != codigo:
                raise ErroConsulta(409, "Esta consulta já foi confirmada. Inicie uma nova consulta.")
            db.execute("UPDATE consultas SET codigo_confirmado = ? WHERE id = ?", (codigo, id_consulta))
            return self._ler(db, id_consulta)


    def gerar(self, id_consulta):
        """Reserva uma revisão antes da chamada ao provedor; uma por vez por consulta."""
        with abrir_banco(self.banco) as db:
            db.execute("BEGIN IMMEDIATE")
            consulta = self._ler(db, id_consulta)
            entrada = consulta["entrada_geracao"]
            if not entrada:
                raise ErroConsulta(409, "Confirme uma habilidade antes de gerar o plano.")
            anterior = consulta["geracao_atual"]
            if anterior and anterior["estado"] == "processando":
                raise ErroConsulta(409, "Já existe uma geração em andamento para esta consulta.")
            if anterior and anterior["estado"] == "aprovado":
                raise ErroConsulta(409, "Este plano foi aprovado. Faça uma nova consulta para gerar outro.")
            revisao = anterior["revisao"] + 1 if anterior else 1
            id_geracao = uuid4().hex
            db.execute("INSERT INTO geracoes (id, consulta_id, revisao, estado) VALUES (?, ?, ?, 'processando')",
                       (id_geracao, id_consulta, revisao))
        try:
            resultado = self.gerador.gerar(entrada, revisao)
        except Exception as erro:
            conhecido = isinstance(erro, ErroGeracao)
            mensagem = str(erro) if conhecido else "Falha interna na geração."
            falha = {"erro": mensagem, "tipo_erro": erro.tipo if conhecido else "interno",
                     "rastreio": erro.rastreio if conhecido else [], "revisao": revisao}
            with abrir_banco(self.banco) as db:
                db.execute("UPDATE geracoes SET estado = 'falha', resultado = ? WHERE id = ? AND estado = 'processando'",
                           (json.dumps(falha, ensure_ascii=False), id_geracao))
            raise ErroConsulta(502, mensagem) from None
        with abrir_banco(self.banco) as db:
            db.execute("UPDATE geracoes SET estado = 'rascunho', resultado = ? WHERE id = ? AND estado = 'processando'",
                       (json.dumps(resultado, ensure_ascii=False), id_geracao))
        return self.obter(id_consulta)

    def aprovar(self, id_geracao):
        """Aprovação humana, distinta da IA Juiz ainda não implementada."""
        with abrir_banco(self.banco) as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT consulta_id, estado FROM geracoes WHERE id = ?", (id_geracao,)).fetchone()
            if row is None:
                raise ErroConsulta(404, "Plano não encontrado.")
            id_consulta, estado = row
            if estado not in ("rascunho", "aprovado"):
                raise ErroConsulta(409, "O plano ainda não está pronto para aprovação.")
            atual = self._geracao_atual(db, id_consulta)
            if atual["id"] != id_geracao:
                raise ErroConsulta(409, "Somente a versão mais recente pode ser aprovada.")
            db.execute("UPDATE geracoes SET estado = 'aprovado' WHERE id = ?", (id_geracao,))
        return self.obter(id_consulta)
