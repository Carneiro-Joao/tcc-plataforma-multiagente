"""Consultas, confirmação curricular, revisões e aprovação docente."""
from contextlib import contextmanager
import json
from hashlib import sha256
from pathlib import Path
import sqlite3
import time
from uuid import uuid4
from erros import ErroGeracao
from juiz_servico import ROTULOS, NAO_FAVORAVEL, falhas_graves
from geracao_v2 import GeradorDePlanoCompleto as GeradorDePlano

from rag.search import FONTE, BASE
from rag.termos import TERMOS
from tema import extrair_tema, TemaNaoIdentificado

VERSAO_CATALOGO = "bncc-8ano-v1"
HASH_CATALOGO = sha256((BASE / "data" / "bncc_8ano.json").read_bytes()).hexdigest()

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


# Pedido em andamento parado há mais que isto é tratado como interrompido (ex.: o app foi fechado no meio).
PEDIDO_ABANDONADO_S = 15 * 60
ESTADOS_EM_ANDAMENTO = ("gerando", "avaliando", "regenerando")
AVISO_PROVISORIO = "Avaliação automática e provisória; a decisão final é do professor."


class ErroConsulta(Exception):
    def __init__(self, status, mensagem, codigo=None):
        super().__init__(mensagem)
        self.status = status
        self.codigo = codigo  # identificador estável para a interface (ex.: "tema_nao_identificado")


def texto_valido(valor, nome, limite, codigo=None):
    if not isinstance(valor, str) or not 0 < len(valor.strip()) <= limite:
        raise ErroConsulta(422, f"Informe {nome} com até {limite} caracteres.", codigo)
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
    return dict(ano=ano, tema=texto_valido(dados.get("tema"), "o tema", 800, "tema_invalido"),
                duracao_min=minutos, recursos=texto_valido(dados.get("recursos"), "os recursos", 800),
                tipo=dados["tipo"])


def habilidade_publica(doc):
    campos = ("codigo", "eixo", "objeto_conhecimento", "habilidade", "explicacao", "exemplos")
    return {**{k: doc[k] for k in campos}, "referencia": {
        "documento": FONTE, "arquivo": "BNCCComputacao.pdf",
        "pagina_habilidade": doc["pagina_habilidade"], "pagina_exemplos": doc["pagina_pdf"],
        "versao_catalogo": VERSAO_CATALOGO, "sha256_catalogo": HASH_CATALOGO,
    }}


# Habilidades que pedem programação/automação em computador (texto da BNCC: "usando uma linguagem de programação").
HABILIDADES_COM_COMPUTADOR = ("EF08CO01", "EF08CO02")


def alertas_recursos(consulta):
    """Avisos determinísticos (não bloqueiam): habilidade confirmada que pede computador sem computador nos recursos."""
    entrada = consulta.get("entrada_geracao")
    if not entrada:
        return []
    codigo = entrada["habilidade"]["codigo"]
    recursos = entrada["contexto"]["recursos"].lower()
    if codigo in HABILIDADES_COM_COMPUTADOR and "computador" not in recursos:
        return [dict(codigo="habilidade_sem_computador",
                     mensagem=f"A habilidade {codigo} pede automatizar soluções com uma linguagem de programação, mas "
                              "“computadores” não está nos recursos marcados. O plano tende a ficar só no papel.")]
    return []


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
    def __init__(self, busca, banco, gerador=None, limite_diario_ia=None, juiz=None, ciclos_juiz=1,
                 limite_diario_juiz=None, pausa_juiz_s=75, pausa_juiz_413_s=120, dormir=time.sleep):
        self.busca = busca
        self.gerador = gerador or GeradorDePlano()
        # Máximo de gerações com IA por dia (data local), contando falhas: cada tentativa gasta chamadas pagas. None = sem limite.
        self.limite_diario_ia = limite_diario_ia
        # IA Juiz (PoC 08): etapa automática depois de cada geração. None = desligado (plano entregue sem avaliação).
        if type(ciclos_juiz) is not int or ciclos_juiz < 0:
            raise ValueError("ciclos_juiz deve ser inteiro >= 0.")
        self.juiz, self.ciclos_juiz, self.limite_diario_juiz = juiz, ciclos_juiz, limite_diario_juiz
        self.pausa_juiz_s, self.pausa_juiz_413_s, self.dormir = pausa_juiz_s, pausa_juiz_413_s, dormir
        self._ultimo_juiz = None  # (instante monotônico, foi_413) da última chamada real ao Juiz neste processo
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
            colunas = {c[1] for c in db.execute("PRAGMA table_info(geracoes)")}
            for nome, tipo in (("pedido_id", "TEXT"), ("ciclo", "INTEGER"), ("entregue", "INTEGER NOT NULL DEFAULT 0")):
                if nome not in colunas:  # migração sem perder dados: bancos antigos ganham as colunas novas
                    db.execute(f"ALTER TABLE geracoes ADD COLUMN {nome} {tipo}")
            db.execute("""CREATE TABLE IF NOT EXISTS pedidos
                          (id TEXT PRIMARY KEY, consulta_id TEXT NOT NULL, estado TEXT NOT NULL,
                           ciclo INTEGER NOT NULL DEFAULT 0, geracao_entregue TEXT, aviso TEXT, historico TEXT,
                           criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                           atualizado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                           FOREIGN KEY (consulta_id) REFERENCES consultas(id))""")
            db.execute("""CREATE TABLE IF NOT EXISTS pareceres
                          (id TEXT PRIMARY KEY, geracao_id TEXT NOT NULL, ciclo INTEGER NOT NULL,
                           criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                           estado TEXT NOT NULL CHECK (estado IN ('ok', 'falha')), proximo_estado TEXT,
                           versao_prompt TEXT, modelo TEXT, versao_rubrica TEXT, politica TEXT, resultado TEXT,
                           FOREIGN KEY (geracao_id) REFERENCES geracoes(id))""")

    def _vocabulario(self):
        return [t for lista in TERMOS.values() for t in lista] + [d["objeto_conhecimento"] for d in self.busca.documentos]

    def consultar(self, pedido):
        contexto = validar_contexto(pedido.get("contexto"), self.busca.ano)
        # O professor pode escrever uma frase inteira. Busca, plano e tela usam só o tema; a frase fica em pedido_original.
        # (Buscar com a frase inteira trazia habilidades erradas por palavras de ruído como "quero" e "ensinar".)
        pedido_original = contexto["tema"]
        try:
            achado = extrair_tema(pedido_original, self._vocabulario())
        except TemaNaoIdentificado as erro:
            raise ErroConsulta(422, str(erro), "tema_nao_identificado")
        contexto["tema"] = achado["tema"]
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
        consulta = dict(id=uuid4().hex, contexto=contexto, pedido_original=pedido_original,
                        origem_tema=achado["origem"], consulta=modo,
                        metodo=self.busca.modo if modo == "tema" else "catalogo", resultados=resultados)
        dados = json.dumps(consulta, ensure_ascii=False)
        with abrir_banco(self.banco) as db:
            db.execute("INSERT INTO consultas (id, dados) VALUES (?, ?)", (consulta["id"], dados))
        return self.obter(consulta["id"])

    @staticmethod
    def _geracao_atual(db, id_consulta):
        """Geração mostrada ao professor: a entregue pelo último pedido; linhas antigas (sem pedido) valem como entregues."""
        row = db.execute("""SELECT id, revisao, estado, resultado, criado_em FROM geracoes
                            WHERE consulta_id = ? AND (entregue = 1 OR pedido_id IS NULL)
                            ORDER BY revisao DESC LIMIT 1""",
                         (id_consulta,)).fetchone()
        if row is None:
            return None
        ident, revisao, estado, resultado, criado = row
        atual = dict(id=ident, revisao=revisao, estado=estado,
                     resultado=json.loads(resultado) if resultado else None, criado_em=criado)
        atual["avaliacao"] = ServicoCurricular._avaliacao(db, ident)
        return atual

    @staticmethod
    def _avaliacao(db, id_geracao):
        """Último parecer da geração + rótulo para o professor; sem parecer → 'não realizada'; falha técnica → 'indisponível'."""
        row = db.execute("""SELECT estado, proximo_estado, resultado, ciclo FROM pareceres WHERE geracao_id = ?
                            ORDER BY criado_em DESC, rowid DESC LIMIT 1""", (id_geracao,)).fetchone()
        if row is None:
            return dict(status="nao_realizada", rotulo="Avaliação não realizada", aviso=AVISO_PROVISORIO)
        estado, proximo, resultado, ciclo = row
        dados = json.loads(resultado) if resultado else {}
        if estado != "ok":  # falha técnica: NUNCA conta como parecer
            return dict(status="indisponivel", rotulo="Indisponível", erro=dados.get("erro"),
                        tipo_erro=dados.get("tipo_erro"), aviso=AVISO_PROVISORIO)
        return dict(status=proximo, rotulo=ROTULOS.get(proximo, proximo), ciclo=ciclo, parecer=dados.get("parecer"),
                    decisao=dados.get("decisao"), modelo=dados.get("modelo_juiz"), versao_prompt=dados.get("versao_prompt"),
                    versao_rubrica=dados.get("versao_rubrica"), demonstracao=bool(dados.get("demonstracao")),
                    aviso_demonstracao=dados.get("aviso_demonstracao"), aviso=AVISO_PROVISORIO)

    @staticmethod
    def _pedido_atual(db, id_consulta):
        row = db.execute("""SELECT id, estado, ciclo, geracao_entregue, aviso, historico, criado_em, atualizado_em,
                                   (julianday('now') - julianday(atualizado_em)) * 86400
                            FROM pedidos WHERE consulta_id = ? ORDER BY criado_em DESC, rowid DESC LIMIT 1""",
                         (id_consulta,)).fetchone()
        if row is None:
            return None
        ident, estado, ciclo, entregue, aviso, historico, criado, atualizado, idade = row
        if estado in ESTADOS_EM_ANDAMENTO and idade > PEDIDO_ABANDONADO_S:
            estado, aviso = "interrompido", "O pedido foi interrompido (o app pode ter sido fechado). Gere novamente."
        return dict(id=ident, estado=estado, ciclo=ciclo, geracao_entregue=entregue, aviso=aviso,
                    historico=json.loads(historico) if historico else [], criado_em=criado, atualizado_em=atualizado,
                    em_andamento=estado in ESTADOS_EM_ANDAMENTO)

    @classmethod
    def _ler(cls, db, id_consulta):
        registro = db.execute("SELECT dados, codigo_confirmado FROM consultas WHERE id = ?",
                              (id_consulta,)).fetchone()
        if registro is None:
            raise ErroConsulta(404, "Consulta não encontrada. Faça uma nova consulta.")
        consulta = visao(registro)
        consulta["geracao_atual"] = cls._geracao_atual(db, id_consulta)
        consulta["pedido_atual"] = cls._pedido_atual(db, id_consulta)
        consulta["alertas"] = alertas_recursos(consulta)
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


    @staticmethod
    def _geracoes_ia_hoje(db):
        return db.execute("""SELECT COUNT(*) FROM geracoes
                             WHERE date(criado_em, 'localtime') = date('now', 'localtime')
                               AND (estado = 'processando' OR json_extract(resultado, '$.modo') = 'ia')""").fetchone()[0]

    @staticmethod
    def _pareceres_juiz_hoje(db):
        """Chamadas reais ao Juiz hoje (data local), CONTANDO falhas técnicas. Demonstração não conta."""
        return db.execute("""SELECT COUNT(*) FROM pareceres
                             WHERE date(criado_em, 'localtime') = date('now', 'localtime')
                               AND json_extract(resultado, '$.modo') = 'groq'""").fetchone()[0]

    def uso_hoje(self):
        """(gerações com IA hoje, limite) — para o aviso ao iniciar o app."""
        with abrir_banco(self.banco) as db:
            return self._geracoes_ia_hoje(db), self.limite_diario_ia

    def uso_juiz_hoje(self):
        """(avaliações reais do Juiz hoje, limite)."""
        with abrir_banco(self.banco) as db:
            return self._pareceres_juiz_hoje(db), self.limite_diario_juiz

    def _limite_geracao_atingido(self, db):
        usa_ia = getattr(self.gerador, "modo", None) == "ia"
        return usa_ia and self.limite_diario_ia is not None and self._geracoes_ia_hoje(db) >= self.limite_diario_ia

    def _limite_juiz_atingido(self, db):
        reais = getattr(self.juiz, "modo", None) == "groq"
        return reais and self.limite_diario_juiz is not None and self._pareceres_juiz_hoje(db) >= self.limite_diario_juiz

    def _atualizar_pedido(self, id_pedido, **campos):
        if "historico" in campos:
            campos["historico"] = json.dumps(campos["historico"], ensure_ascii=False)
        sets = ", ".join(f"{k} = ?" for k in campos)
        with abrir_banco(self.banco) as db:
            db.execute(f"UPDATE pedidos SET {sets}, atualizado_em = CURRENT_TIMESTAMP WHERE id = ?",
                       (*campos.values(), id_pedido))

    def gerar(self, id_consulta):
        """Um pedido do professor: gerar → IA Juiz → (regenerar o plano inteiro, até ciclos_juiz) → entregar.

        Todas as gerações e todos os pareceres ficam gravados; a geração entregue é marcada (entregue = 1).
        Falha técnica do Juiz nunca conta como parecer: o plano é entregue com "avaliação indisponível".
        """
        with abrir_banco(self.banco) as db:
            db.execute("BEGIN IMMEDIATE")
            consulta = self._ler(db, id_consulta)
            entrada = consulta["entrada_geracao"]
            if not entrada:
                raise ErroConsulta(409, "Confirme uma habilidade antes de gerar o plano.")
            pedido = consulta["pedido_atual"]
            processando = db.execute("SELECT 1 FROM geracoes WHERE consulta_id = ? AND estado = 'processando' "
                                     "AND pedido_id IS NULL", (id_consulta,)).fetchone()
            if (pedido and pedido["em_andamento"]) or processando:
                raise ErroConsulta(409, "Já existe uma geração em andamento para esta consulta.")
            anterior = consulta["geracao_atual"]
            if anterior and anterior["estado"] == "aprovado":
                raise ErroConsulta(409, "Este plano foi aprovado. Faça uma nova consulta para gerar outro.")
            if self._limite_geracao_atingido(db):
                raise ErroConsulta(429, f"Limite de {self.limite_diario_ia} planos com IA por dia atingido (tentativas com falha "
                                        "também contam). Volte amanhã ou reinicie o app com --limite-diario maior.")
            id_pedido = uuid4().hex
            db.execute("INSERT INTO pedidos (id, consulta_id, estado) VALUES (?, ?, 'gerando')", (id_pedido, id_consulta))

        candidatos, historico, aviso = [], [], None
        ciclos = self.ciclos_juiz if self.juiz else 0
        for ciclo in range(ciclos + 1):
            if ciclo > 0:
                with abrir_banco(self.banco) as db:
                    limite = self._limite_geracao_atingido(db)
                if limite:
                    aviso = "Limite diário de gerações atingido antes da nova versão; entregue a melhor versão já avaliada."
                    historico.append(dict(ciclo=ciclo, evento="limite_geracao"))
                    break
                self._atualizar_pedido(id_pedido, estado="regenerando", ciclo=ciclo, historico=historico)
            try:
                gid, revisao, resultado = self._gerar_uma(id_consulta, entrada, id_pedido, ciclo)
            except ErroConsulta as erro:
                historico.append(dict(ciclo=ciclo, evento="falha_geracao", erro=str(erro)))
                if not candidatos:
                    self._atualizar_pedido(id_pedido, estado="falha", aviso=str(erro), historico=historico)
                    raise
                aviso = "A nova versão falhou tecnicamente; entregue a melhor versão anterior."
                break
            item = dict(ciclo=ciclo, geracao_id=gid, revisao=revisao, avaliado=False, proximo_estado=None, graves=None)
            candidatos.append(item)
            if not self.juiz:
                historico.append(dict(ciclo=ciclo, geracao_id=gid, revisao=revisao, evento="juiz_desligado"))
                break
            with abrir_banco(self.banco) as db:
                limite = self._limite_juiz_atingido(db)
            if limite:
                aviso = (f"Limite diário de {self.limite_diario_juiz} avaliações da IA Juiz atingido; "
                         "esta versão foi entregue sem avaliação.")
                historico.append(dict(ciclo=ciclo, geracao_id=gid, revisao=revisao, evento="limite_juiz"))
                break
            self._atualizar_pedido(id_pedido, estado="avaliando", ciclo=ciclo, historico=historico)
            avaliado = self._avaliar(gid, revisao, resultado, entrada, ciclo)
            if avaliado.get("falha"):
                aviso = "Avaliação indisponível (falha técnica da IA Juiz); o plano foi entregue sem parecer."
                historico.append(dict(ciclo=ciclo, geracao_id=gid, revisao=revisao, evento="falha_juiz",
                                      erro=avaliado["erro"], tipo_erro=avaliado["tipo_erro"]))
                break
            decisao = avaliado["decisao"]
            item.update(avaliado=True, proximo_estado=decisao["proximo_estado"], graves=falhas_graves(avaliado["parecer"]))
            historico.append(dict(ciclo=ciclo, geracao_id=gid, revisao=revisao, evento="avaliado",
                                  proximo_estado=decisao["proximo_estado"], rotulo=ROTULOS[decisao["proximo_estado"]],
                                  motivos=decisao["motivos"], falhas_graves=item["graves"],
                                  criticas=[f["descricao"] for f in avaliado["parecer"]["falhas"]
                                            if f["gravidade"] in ("maior", "critica")][:3]))
            if decisao["proximo_estado"] not in NAO_FAVORAVEL:
                break

        entregue = escolher_entrega(candidatos)
        if aviso is None and entregue["avaliado"] and entregue["proximo_estado"] in NAO_FAVORAVEL:
            if len(candidatos) > 1:
                aviso = (f"A IA Juiz não deu parecer favorável a nenhuma das {len(candidatos)} versões; foi entregue a com menos "
                         f"falhas graves (revisão {entregue['revisao']}). Revise antes de aprovar.")
            elif ciclos == 0:
                aviso = "A IA Juiz recomenda ajustes; a regeneração automática está desligada (--ciclos-juiz 0)."
        with abrir_banco(self.banco) as db:
            db.execute("UPDATE geracoes SET entregue = 1 WHERE id = ?", (entregue["geracao_id"],))
        self._atualizar_pedido(id_pedido, estado="pronto", geracao_entregue=entregue["geracao_id"], aviso=aviso,
                               historico=historico)
        return self.obter(id_consulta)

    def _gerar_uma(self, id_consulta, entrada, id_pedido, ciclo):
        """Uma geração completa (5 especialistas + integrador), em nova revisão. Falha → ErroConsulta(502)."""
        with abrir_banco(self.banco) as db:
            db.execute("BEGIN IMMEDIATE")
            revisao = db.execute("SELECT COALESCE(MAX(revisao), 0) + 1 FROM geracoes WHERE consulta_id = ?",
                                 (id_consulta,)).fetchone()[0]
            id_geracao = uuid4().hex
            db.execute("INSERT INTO geracoes (id, consulta_id, revisao, estado, pedido_id, ciclo) "
                       "VALUES (?, ?, ?, 'processando', ?, ?)", (id_geracao, id_consulta, revisao, id_pedido, ciclo))
        try:
            resultado = self.gerador.gerar(entrada, revisao)
        except Exception as erro:
            conhecido = isinstance(erro, ErroGeracao)
            mensagem = str(erro) if conhecido else "Falha interna na geração."
            falha = {"erro": mensagem, "tipo_erro": erro.tipo if conhecido else "interno",
                     "rastreio": erro.rastreio if conhecido else [], "revisao": revisao,
                     "contrato": getattr(self.gerador, "VERSAO_CONTRATO", None),
                     "modo": getattr(self.gerador, "modo", None), "modelo": getattr(self.gerador, "modelo", None)}
            with abrir_banco(self.banco) as db:
                # A falha da 1ª versão é a que o professor vê (como antes); a de uma regeneração fica só no histórico.
                db.execute("UPDATE geracoes SET estado = 'falha', resultado = ?, entregue = ? "
                           "WHERE id = ? AND estado = 'processando'",
                           (json.dumps(falha, ensure_ascii=False), 1 if ciclo == 0 else 0, id_geracao))
            raise ErroConsulta(502, mensagem) from None
        with abrir_banco(self.banco) as db:
            db.execute("UPDATE geracoes SET estado = 'rascunho', resultado = ? WHERE id = ? AND estado = 'processando'",
                       (json.dumps(resultado, ensure_ascii=False), id_geracao))
        return id_geracao, revisao, resultado

    def _avaliar(self, id_geracao, revisao, resultado, entrada, ciclo):
        """Chama o Juiz (com a pausa exigida pelo Groq entre chamadas) e grava o parecer ou a falha técnica."""
        from contratos import juiz_v1
        from groq_juiz import sanitizar
        real = getattr(self.juiz, "modo", None) == "groq"
        if real and self._ultimo_juiz is not None:
            instante, foi_413 = self._ultimo_juiz
            espera = (self.pausa_juiz_413_s if foi_413 else self.pausa_juiz_s) - (time.monotonic() - instante)
            if espera > 0:
                self.dormir(espera)
        modelo_gerador = resultado.get("modelo") or getattr(self.gerador, "modelo", None) or "desconhecido"
        try:
            dados = self.juiz.avaliar(resultado["plano"], entrada, modelo_gerador=modelo_gerador, revisao=revisao, ciclo=ciclo)
            estado, proximo = "ok", dados["decisao"]["proximo_estado"]
        except Exception as erro:  # falha técnica (HTTP 400/413/429, recusa, contrato após reparo): nunca vira parecer
            conhecido = isinstance(erro, ErroGeracao)
            dados = dict(falha=True, erro=str(erro) if conhecido else "Falha interna na avaliação.",
                         tipo_erro=getattr(erro, "tipo", "interno"), rastreio=getattr(erro, "rastreio", []))
            estado, proximo = "falha", None
        if real:  # a próxima chamada respeita a pausa (maior depois de HTTP 413)
            self._ultimo_juiz = (time.monotonic(), estado == "falha" and "413" in dados["erro"])
        dados.update(modo=getattr(self.juiz, "modo", None))
        dados = sanitizar(dados)
        with abrir_banco(self.banco) as db:
            db.execute("""INSERT INTO pareceres (id, geracao_id, ciclo, estado, proximo_estado, versao_prompt, modelo,
                                                 versao_rubrica, politica, resultado) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                       (uuid4().hex, id_geracao, ciclo, estado, proximo, getattr(self.juiz, "versao_prompt", None),
                        getattr(self.juiz, "modelo", None), juiz_v1.rubrica.VERSAO, juiz_v1.POLITICA_PRELIMINAR["nome"],
                        json.dumps(dados, ensure_ascii=False)))
        return dados

    def aprovar(self, id_geracao):
        """Aprovação humana. O parecer do Juiz é consultivo: o professor decide."""
        with abrir_banco(self.banco) as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT consulta_id, estado FROM geracoes WHERE id = ?", (id_geracao,)).fetchone()
            if row is None:
                raise ErroConsulta(404, "Plano não encontrado.")
            id_consulta, estado = row
            if estado not in ("rascunho", "aprovado"):
                raise ErroConsulta(409, "O plano ainda não está pronto para aprovação.")
            pedido = self._pedido_atual(db, id_consulta)
            if pedido and pedido["em_andamento"]:
                raise ErroConsulta(409, "Aguarde o fim da geração e da avaliação antes de aprovar.")
            atual = self._geracao_atual(db, id_consulta)
            if atual["id"] != id_geracao:
                raise ErroConsulta(409, "Somente a versão entregue mais recente pode ser aprovada.")
            db.execute("UPDATE geracoes SET estado = 'aprovado' WHERE id = ?", (id_geracao,))
        return self.obter(id_consulta)


def escolher_entrega(candidatos):
    """Versão entregue ao professor.

    - A última não foi avaliada (Juiz desligado, falha técnica ou limite): entrega a última.
    - Alguma favorável: a favorável mais recente.
    - Nenhuma favorável: a com MENOS falhas graves (maior/crítica); empate → a mais recente.
    """
    ultimo = candidatos[-1]
    if not ultimo["avaliado"]:
        return ultimo
    favoraveis = [c for c in candidatos if c["avaliado"] and c["proximo_estado"] not in NAO_FAVORAVEL]
    if favoraveis:
        return favoraveis[-1]
    avaliados = [c for c in candidatos if c["avaliado"]]
    return min(reversed(avaliados), key=lambda c: c["graves"])
