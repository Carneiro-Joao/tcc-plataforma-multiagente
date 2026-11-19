"""IA Juiz integrada à geração (PoC 08): servico.gerar → Juiz → regenerar → entregar. Sem rede. Execute a partir de aula-ia-backend."""
from contextlib import closing, redirect_stdout, redirect_stderr
from copy import deepcopy
import io
import json
import os
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

import app
import juiz_servico
from contratos import juiz_v1
from erros import ErroGeracao
from rag.search import BuscaCurricular
from servico import ErroConsulta, ServicoCurricular, escolher_entrega

FIXTURE = json.loads((Path(__file__).parent / "dados/plano_v2/fixture_ordenacao.json").read_text(encoding="utf-8"))
GRAVADO = json.loads(juiz_servico.PARECER_DEMONSTRACAO.read_text(encoding="utf-8"))
CONTEXTO = dict(ano="8º ano", tema="ordenação", duracao_min=50, recursos="papel e cartões", tipo="Computação desplugada")
NOTA = {"critica": 1, "maior": 2, "menor": 3}


def parecer(*falhas):
    """Parecer válido com as falhas (gravidade, critério, componente) e notas coerentes com elas."""
    p = deepcopy(GRAVADO["parecer"])
    modelo, p["falhas"] = p["falhas"][0], []
    for i, (gravidade, criterio, componente) in enumerate(falhas, 1):
        f = deepcopy(modelo)
        f.update(id=f"F{i}", gravidade=gravidade, criterio=criterio, componente=componente)
        p["falhas"].append(f)
    for a in p["avaliacoes"]:
        a["nota"] = min([NOTA[f["gravidade"]] for f in p["falhas"] if f["criterio"] == a["criterio"]] or [3])
    juiz_v1.validar(p)
    return p


FAVORAVEL = parecer(("menor", "inclusao", "adaptacao"))
UMA_GRAVE = parecer(("maior", "viabilidade", "sequencia"))
DUAS_GRAVES = parecer(("maior", "viabilidade", "sequencia"), ("maior", "inclusao", "adaptacao"))
CRITICA = parecer(("critica", "aderencia_curricular", "objetivos"))


class GeradorFalso:
    """Gerador 'ia' (ou demonstração) sem rede; o roteiro diz quais chamadas falham."""
    def __init__(self, modo="ia", falhas=()):
        self.modo, self.modelo, self.falhas, self.chamadas = modo, "gemini-falso", set(falhas), 0
        self.VERSAO_CONTRATO = "plano-aula-2.0"

    def gerar(self, entrada, revisao):
        self.chamadas += 1
        if self.chamadas in self.falhas:
            raise ErroGeracao("Gemini HTTP 503 (teste)", tipo="http")
        return dict(plano=deepcopy(FIXTURE["plano_esperado"]), modo=self.modo, modelo=self.modelo,
                    contrato="plano-aula-2.0", rastreio=[])


class JuizFalso:
    """Juiz 'groq' sem rede: cada chamada consome o próximo parecer do roteiro (ou uma exceção)."""
    def __init__(self, roteiro, modo="groq"):
        self.roteiro, self.modo, self.chamadas = list(roteiro), modo, []
        self.modelo, self.versao_prompt = "openai/gpt-oss-120b", "juiz-v1.3"

    def avaliar(self, plano, entrada, *, modelo_gerador, revisao, ciclo):
        self.chamadas.append(dict(revisao=revisao, ciclo=ciclo, modelo_gerador=modelo_gerador))
        passo = self.roteiro.pop(0)
        if isinstance(passo, Exception):
            raise passo
        return {"parecer": deepcopy(passo), "decisao": juiz_v1.decidir(passo, ciclo), "modelo_juiz": self.modelo,
                "versao_prompt": self.versao_prompt, "versao_rubrica": juiz_v1.rubrica.VERSAO, "rastreio": [],
                "demonstracao": False}


class Base(TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.banco = Path(temp.name) / "t.sqlite3"
        self.pausas = []

    def servico(self, roteiro=(), *, gerador=None, ciclos=1, juiz="falso", **kw):
        self.gerador = gerador or GeradorFalso()
        self.juiz = JuizFalso(roteiro) if juiz == "falso" else juiz
        return ServicoCurricular(BuscaCurricular(), self.banco, self.gerador, juiz=self.juiz, ciclos_juiz=ciclos,
                                 dormir=self.pausas.append, **kw)

    def pedido(self, s):
        c = s.consultar({"contexto": CONTEXTO, "consulta": "tema"})
        s.confirmar(c["id"], c["resultados"][0]["habilidade"]["codigo"])
        return c["id"]

    def linhas(self, sql):
        with closing(sqlite3.connect(self.banco)) as db:
            return db.execute(sql).fetchall()


class TestFluxo(Base):
    def test_favoravel_na_primeira_entrega_sem_regenerar(self):
        s = self.servico([FAVORAVEL])
        r = s.gerar(self.pedido(s))
        g, p = r["geracao_atual"], r["pedido_atual"]
        self.assertEqual((g["revisao"], g["avaliacao"]["status"], g["avaliacao"]["rotulo"]), (1, "aguardando_decisao", "Favorável"))
        self.assertEqual(g["avaliacao"]["parecer"], FAVORAVEL)
        self.assertEqual(g["avaliacao"]["aviso"], "Avaliação automática e provisória; a decisão final é do professor.")
        self.assertEqual((p["estado"], p["aviso"], [h["evento"] for h in p["historico"]]), ("pronto", None, ["avaliado"]))
        self.assertEqual(self.gerador.chamadas, 1)
        self.assertEqual(len(self.juiz.chamadas), 1)
        self.assertEqual(self.juiz.chamadas[0]["modelo_gerador"], "gemini-falso")

    def test_nao_favoravel_regenera_e_entrega_a_favoravel(self):
        s = self.servico([UMA_GRAVE, FAVORAVEL])
        r = s.gerar(self.pedido(s))
        g, p = r["geracao_atual"], r["pedido_atual"]
        self.assertEqual((g["revisao"], g["avaliacao"]["rotulo"], p["ciclo"], p["aviso"]), (2, "Favorável", 1, None))
        self.assertEqual([(h["ciclo"], h["rotulo"]) for h in p["historico"]], [(0, "Com ressalvas"), (1, "Favorável")])
        self.assertIn("F1", p["historico"][0]["motivos"][0])
        self.assertEqual(p["historico"][0]["criticas"], [UMA_GRAVE["falhas"][0]["descricao"]])
        self.assertEqual(p["historico"][1]["criticas"], [])
        self.assertEqual([c["ciclo"] for c in self.juiz.chamadas], [0, 1])
        self.assertEqual(self.linhas("SELECT revisao, entregue, pedido_id IS NOT NULL FROM geracoes ORDER BY revisao"),
                         [(1, 0, 1), (2, 1, 1)])
        self.assertEqual(self.linhas("SELECT ciclo, estado, proximo_estado, versao_prompt, modelo, versao_rubrica, politica "
                                     "FROM pareceres ORDER BY ciclo"),
                         [(0, "ok", "em_correcao", "juiz-v1.3", "openai/gpt-oss-120b", "rubrica-juiz-0.1", "politica-juiz-prelim-0.1"),
                          (1, "ok", "aguardando_decisao", "juiz-v1.3", "openai/gpt-oss-120b", "rubrica-juiz-0.1",
                           "politica-juiz-prelim-0.1")])

    def test_nao_favoravel_duas_vezes_entrega_a_com_menos_falhas_graves_com_aviso(self):
        s = self.servico([UMA_GRAVE, DUAS_GRAVES])
        r = s.gerar(self.pedido(s))
        g, p = r["geracao_atual"], r["pedido_atual"]
        self.assertEqual((g["revisao"], g["avaliacao"]["rotulo"]), (1, "Com ressalvas"))
        self.assertIn("nenhuma das 2 versões", p["aviso"])
        self.assertIn("revisão 1", p["aviso"])
        self.assertEqual(self.gerador.chamadas, 2)  # só 1 ciclo automático (padrão)

    def test_empate_de_falhas_graves_entrega_a_mais_recente(self):
        s = self.servico([UMA_GRAVE, UMA_GRAVE])
        self.assertEqual(s.gerar(self.pedido(s))["geracao_atual"]["revisao"], 2)

    def test_critica_regenera_e_rotulo_revisao_recomendada(self):
        s = self.servico([CRITICA, CRITICA])
        r = s.gerar(self.pedido(s))
        self.assertEqual(r["geracao_atual"]["avaliacao"]["rotulo"], "Revisão recomendada")
        self.assertEqual(self.gerador.chamadas, 2)

    def test_dois_ciclos_param_no_primeiro_favoravel(self):
        s = self.servico([UMA_GRAVE, UMA_GRAVE, FAVORAVEL, FAVORAVEL], ciclos=2)
        r = s.gerar(self.pedido(s))
        self.assertEqual((r["geracao_atual"]["revisao"], r["pedido_atual"]["ciclo"]), (3, 2))
        self.assertEqual(len(self.juiz.roteiro), 1)

    def test_ciclos_zero_nao_regenera(self):
        s = self.servico([UMA_GRAVE], ciclos=0)
        r = s.gerar(self.pedido(s))
        self.assertEqual((self.gerador.chamadas, r["geracao_atual"]["avaliacao"]["rotulo"]), (1, "Com ressalvas"))
        self.assertIn("--ciclos-juiz 0", r["pedido_atual"]["aviso"])

    def test_falha_tecnica_do_juiz_entrega_sem_parecer_e_nao_conta_como_parecer(self):
        s = self.servico([ErroGeracao("Groq HTTP 413: grande demais", tipo="http")])
        r = s.gerar(self.pedido(s))
        g, p = r["geracao_atual"], r["pedido_atual"]
        self.assertEqual((g["avaliacao"]["status"], g["avaliacao"]["rotulo"]), ("indisponivel", "Indisponível"))
        self.assertNotIn("parecer", g["avaliacao"])
        self.assertIn("Avaliação indisponível", p["aviso"])
        self.assertEqual(self.gerador.chamadas, 1)  # falha técnica não dispara regeneração
        self.assertEqual(self.linhas("SELECT estado, proximo_estado FROM pareceres"), [("falha", None)])

    def test_excecao_inesperada_do_juiz_tambem_e_falha_tecnica(self):
        s = self.servico([RuntimeError("bug")])
        self.assertEqual(s.gerar(self.pedido(s))["geracao_atual"]["avaliacao"]["status"], "indisponivel")

    def test_falha_do_juiz_na_regeneracao_entrega_a_nova_versao_sem_parecer(self):
        s = self.servico([UMA_GRAVE, ErroGeracao("Groq HTTP 429", tipo="http")])
        r = s.gerar(self.pedido(s))
        self.assertEqual((r["geracao_atual"]["revisao"], r["geracao_atual"]["avaliacao"]["status"]), (2, "indisponivel"))
        self.assertEqual([h["evento"] for h in r["pedido_atual"]["historico"]], ["avaliado", "falha_juiz"])

    def test_juiz_desligado_entrega_com_avaliacao_nao_realizada(self):
        s = self.servico(juiz=None)
        r = s.gerar(self.pedido(s))
        self.assertEqual(r["geracao_atual"]["avaliacao"]["status"], "nao_realizada")
        self.assertEqual(r["pedido_atual"]["historico"][0]["evento"], "juiz_desligado")
        self.assertEqual(self.linhas("SELECT COUNT(*) FROM pareceres"), [(0,)])

    def test_falha_da_primeira_geracao_falha_o_pedido_como_antes(self):
        s = self.servico([FAVORAVEL], gerador=GeradorFalso(falhas={1}))
        cid = self.pedido(s)
        with self.assertRaises(ErroConsulta) as ctx:
            s.gerar(cid)
        self.assertEqual(ctx.exception.status, 502)
        c = s.obter(cid)
        self.assertEqual((c["geracao_atual"]["estado"], c["pedido_atual"]["estado"]), ("falha", "falha"))
        self.assertEqual(self.juiz.chamadas, [])

    def test_falha_na_regeneracao_entrega_a_versao_anterior(self):
        s = self.servico([UMA_GRAVE], gerador=GeradorFalso(falhas={2}))
        r = s.gerar(self.pedido(s))
        self.assertEqual((r["geracao_atual"]["revisao"], r["geracao_atual"]["estado"]), (1, "rascunho"))
        self.assertIn("falhou tecnicamente", r["pedido_atual"]["aviso"])

    def test_gerar_novamente_repete_o_fluxo_e_aprova_so_a_entregue(self):
        s = self.servico([UMA_GRAVE, FAVORAVEL, FAVORAVEL])
        cid = self.pedido(s)
        primeira = s.gerar(cid)["geracao_atual"]
        segunda = s.gerar(cid)["geracao_atual"]
        self.assertEqual((primeira["revisao"], segunda["revisao"]), (2, 3))
        with self.assertRaises(ErroConsulta):
            s.aprovar(primeira["id"])
        self.assertEqual(s.aprovar(segunda["id"])["geracao_atual"]["estado"], "aprovado")
        with self.assertRaises(ErroConsulta) as ctx:
            s.gerar(cid)
        self.assertEqual(ctx.exception.status, 409)

    def test_nao_aprova_nem_gera_durante_pedido_em_andamento(self):
        s = self.servico([FAVORAVEL])
        cid = self.pedido(s)
        gid = s.gerar(cid)["geracao_atual"]["id"]
        with closing(sqlite3.connect(self.banco)) as db, db:
            db.execute("INSERT INTO pedidos (id, consulta_id, estado) VALUES ('p2', ?, 'avaliando')", (cid,))
        for acao in (lambda: s.aprovar(gid), lambda: s.gerar(cid)):
            with self.assertRaises(ErroConsulta) as ctx:
                acao()
            self.assertEqual(ctx.exception.status, 409)

    def test_pedido_parado_ha_muito_tempo_e_tratado_como_interrompido(self):
        s = self.servico([FAVORAVEL])
        cid = self.pedido(s)
        with closing(sqlite3.connect(self.banco)) as db, db:
            db.execute("INSERT INTO pedidos (id, consulta_id, estado, criado_em, atualizado_em) VALUES "
                       "('velho', ?, 'gerando', datetime('now', '-20 minutes'), datetime('now', '-20 minutes'))", (cid,))
        self.assertEqual(s.obter(cid)["pedido_atual"]["estado"], "interrompido")
        self.assertEqual(s.gerar(cid)["pedido_atual"]["estado"], "pronto")


class TestLimitesEPausa(Base):
    def test_pausa_do_groq_antes_da_segunda_chamada_e_maior_depois_de_413(self):
        s = self.servico([UMA_GRAVE, FAVORAVEL], pausa_juiz_s=75)
        s.gerar(self.pedido(s))
        self.assertEqual(len(self.pausas), 1)
        self.assertTrue(70 < self.pausas[0] <= 75, self.pausas)
        self.pausas.clear()
        s2 = self.servico([ErroGeracao("Groq HTTP 413", tipo="http"), FAVORAVEL], pausa_juiz_s=75, pausa_juiz_413_s=120)
        cid = self.pedido(s2)
        s2.gerar(cid)
        s2.gerar(cid)
        self.assertTrue(115 < self.pausas[0] <= 120, self.pausas)

    def test_juiz_de_demonstracao_nao_pausa(self):
        s = self.servico([UMA_GRAVE, FAVORAVEL])
        self.juiz.modo = "demonstracao"
        s.gerar(self.pedido(s))
        self.assertEqual(self.pausas, [])

    def test_limite_do_juiz_conta_falhas_e_entrega_sem_avaliar(self):
        s = self.servico([ErroGeracao("Groq HTTP 400", tipo="http"), FAVORAVEL], limite_diario_juiz=1, pausa_juiz_s=0)
        cid = self.pedido(s)
        s.gerar(cid)  # 1 chamada (com falha) = limite
        r = s.gerar(cid)
        self.assertEqual(len(self.juiz.chamadas), 1)
        self.assertEqual(r["geracao_atual"]["avaliacao"]["status"], "nao_realizada")
        self.assertIn("Limite diário de 1 avaliações da IA Juiz", r["pedido_atual"]["aviso"])
        self.assertEqual(s.uso_juiz_hoje(), (1, 1))

    def test_limite_do_juiz_no_meio_do_fluxo_nao_chama_alem(self):
        s = self.servico([UMA_GRAVE, FAVORAVEL], limite_diario_juiz=1, pausa_juiz_s=0)
        r = s.gerar(self.pedido(s))
        self.assertEqual(len(self.juiz.chamadas), 1)
        self.assertEqual(r["geracao_atual"]["revisao"], 2)
        self.assertEqual(r["geracao_atual"]["avaliacao"]["status"], "nao_realizada")

    def test_demonstracao_nao_conta_no_limite_do_juiz(self):
        s = self.servico([FAVORAVEL, FAVORAVEL], limite_diario_juiz=1)
        self.juiz.modo = "demonstracao"
        cid = self.pedido(s)
        s.gerar(cid)
        s.gerar(cid)
        self.assertEqual((len(self.juiz.chamadas), s.uso_juiz_hoje()[0]), (2, 0))

    def test_limite_de_geracao_conta_regeneracoes_e_para_no_meio(self):
        s = self.servico([UMA_GRAVE, FAVORAVEL], limite_diario_ia=1, pausa_juiz_s=0)
        r = s.gerar(self.pedido(s))
        self.assertEqual(self.gerador.chamadas, 1)
        self.assertIn("Limite diário de gerações", r["pedido_atual"]["aviso"])
        self.assertEqual(r["geracao_atual"]["avaliacao"]["rotulo"], "Com ressalvas")
        s2 = self.servico([UMA_GRAVE, FAVORAVEL], limite_diario_ia=3, pausa_juiz_s=0)
        s2.gerar(self.pedido(s2))
        self.assertEqual(s2.uso_hoje()[0], 3)  # 1 do primeiro serviço + 2 (geração + regeneração)


class TestEscolherEMigracao(TestCase):
    def c(self, ciclo, estado=None, graves=None, avaliado=True):
        return dict(ciclo=ciclo, geracao_id=f"g{ciclo}", revisao=ciclo + 1, avaliado=avaliado, proximo_estado=estado, graves=graves)

    def test_escolher_entrega(self):
        self.assertEqual(escolher_entrega([self.c(0, "em_correcao", 1), self.c(1, avaliado=False)])["ciclo"], 1)
        self.assertEqual(escolher_entrega([self.c(0, "em_correcao", 1), self.c(1, "aguardando_decisao", 0)])["ciclo"], 1)
        self.assertEqual(escolher_entrega([self.c(0, "em_correcao", 1), self.c(1, "em_correcao", 2)])["ciclo"], 0)
        self.assertEqual(escolher_entrega([self.c(0, "em_correcao", 2), self.c(1, "revisao_necessaria", 1)])["ciclo"], 1)
        self.assertEqual(escolher_entrega([self.c(0, "em_correcao", 1), self.c(1, "em_correcao", 1)])["ciclo"], 1)
        self.assertEqual(escolher_entrega([self.c(0, "aguardando_decisao", 0), self.c(1, "em_correcao", 0),
                                           self.c(2, "em_correcao", 0)])["ciclo"], 0)

    def test_banco_antigo_ganha_colunas_e_tabelas_sem_perder_dados(self):
        with TemporaryDirectory() as d:
            banco = Path(d) / "antigo.sqlite3"
            with closing(sqlite3.connect(banco)) as db, db:
                db.execute("CREATE TABLE consultas (id TEXT PRIMARY KEY, dados TEXT NOT NULL, codigo_confirmado TEXT)")
                db.execute("""CREATE TABLE geracoes (id TEXT PRIMARY KEY, consulta_id TEXT NOT NULL, revisao INTEGER NOT NULL,
                              estado TEXT NOT NULL, resultado TEXT, criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                              UNIQUE(consulta_id, revisao))""")
                db.execute("INSERT INTO geracoes (id, consulta_id, revisao, estado) VALUES ('antiga', 'c', 1, 'rascunho')")
            ServicoCurricular(BuscaCurricular(), banco)
            ServicoCurricular(BuscaCurricular(), banco)  # idempotente
            with closing(sqlite3.connect(banco)) as db:
                colunas = {c[1] for c in db.execute("PRAGMA table_info(geracoes)")}
                tabelas = {t[0] for t in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                self.assertTrue({"pedido_id", "ciclo", "entregue"} <= colunas)
                self.assertTrue({"pedidos", "pareceres"} <= tabelas)
                self.assertEqual(db.execute("SELECT id, entregue FROM geracoes").fetchall(), [("antiga", 0)])
                self.assertEqual(ServicoCurricular._geracao_atual(db, "c")["id"], "antiga")

    def test_ciclos_negativos_recusados(self):
        with TemporaryDirectory() as d, self.assertRaises(ValueError):
            ServicoCurricular(BuscaCurricular(), Path(d) / "t.sqlite3", ciclos_juiz=-1)


class TestJuizServico(TestCase):
    def test_demonstracao_usa_parecer_real_gravado_e_marca_demonstracao(self):
        juiz = juiz_servico.criar_juiz("demonstracao")
        r = juiz.avaliar(FIXTURE["plano_esperado"], FIXTURE["entrada"], modelo_gerador="x", revisao=1, ciclo=0)
        self.assertTrue(r["demonstracao"])
        self.assertEqual(r["modo"], "demonstracao")
        self.assertEqual(r["parecer"], GRAVADO["parecer"])
        self.assertEqual((juiz.versao_prompt, juiz.modelo), ("juiz-v1.3", "openai/gpt-oss-120b"))
        self.assertIn("não avalia este plano", r["aviso_demonstracao"])
        self.assertTrue(GRAVADO["fonte"].startswith("aula-ia-backend/local/ensaios_juiz/"))

    def test_groq_usa_a_configuracao_dos_experimentos(self):
        self.assertEqual(juiz_servico.PARAMETROS_EXPERIMENTOS, dict(timeout=90, temperature=0, max_completion_tokens=8192,
                                                                    reasoning_effort="medium", seed=42, versao_prompt="juiz-v1.3"))
        self.assertEqual(juiz_servico.REPAROS, 1)
        recebido = {}
        with patch.object(juiz_servico, "criar_agente_groq_juiz", side_effect=lambda **kw: recebido.update(kw) or
                          type("A", (), {"modelo": "openai/gpt-oss-120b", "versao_prompt": kw["versao_prompt"]})()):
            juiz = juiz_servico.criar_juiz("groq")
        self.assertEqual(recebido, juiz_servico.PARAMETROS_EXPERIMENTOS)
        chamado = {}
        with patch.object(juiz_servico, "avaliar_plano", side_effect=lambda *a, **kw: chamado.update(kw) or {"x": 1}):
            r = juiz.avaliar("plano", "entrada", modelo_gerador="g", revisao=2, ciclo=1)
        self.assertEqual((chamado["reparos"], chamado["ciclos_usados"], chamado["revisao"], chamado["modelo_juiz"]),
                         (1, 1, 2, "openai/gpt-oss-120b"))
        self.assertEqual((r["modo"], r["demonstracao"], r["versao_prompt"]), ("groq", False, "juiz-v1.3"))

    def test_desligado_e_modo_desconhecido(self):
        self.assertIsNone(juiz_servico.criar_juiz("desligado"))
        with self.assertRaises(ValueError):
            juiz_servico.criar_juiz("outro")

    def test_rotulos(self):
        self.assertEqual(juiz_servico.ROTULOS, {"aguardando_decisao": "Favorável", "em_correcao": "Com ressalvas",
                                               "revisao_necessaria": "Revisão recomendada"})
        self.assertEqual(juiz_servico.falhas_graves(DUAS_GRAVES), 2)
        self.assertEqual(juiz_servico.falhas_graves(FAVORAVEL), 0)
        self.assertEqual(juiz_servico.falhas_graves(CRITICA), 1)


class TestApp(TestCase):
    def rodar(self, argv, env):
        """Executa app.main até criar o serviço; captura a saída e o serviço sem abrir porta de verdade."""
        criado = {}

        class ServidorFalso:
            server_port = 0

            def __init__(self, *a):
                criado["servidor"] = self

            def serve_forever(self):
                criado["servico"] = self.servico

            def server_close(self):
                pass
        saida = io.StringIO()
        with TemporaryDirectory() as d, patch.dict(os.environ, env, clear=False), \
                patch.object(app, "ThreadingHTTPServer", ServidorFalso), redirect_stdout(saida):
            if "GROQ_API_KEY" not in env:
                os.environ.pop("GROQ_API_KEY", None)
            app.main(argv + ["--banco", str(Path(d) / "a.sqlite3")])
        return saida.getvalue(), criado["servico"]

    def test_padrao_sem_chave_groq_desliga_e_avisa(self):
        texto, servico = self.rodar(["--gerador", "demonstracao"], {})
        self.assertIsNone(servico.juiz)
        self.assertIn("IA Juiz: DESLIGADA (GROQ_API_KEY não definida)", texto)

    def test_demonstracao_mostra_modo_ciclos_e_nao_pausa(self):
        texto, servico = self.rodar(["--gerador", "demonstracao", "--juiz", "demonstracao", "--ciclos-juiz", "2"], {})
        self.assertEqual((servico.juiz.modo, servico.ciclos_juiz, servico.pausa_juiz_s, servico.limite_diario_juiz),
                         ("demonstracao", 2, 0, None))
        self.assertIn("ciclos automáticos: 2", texto)
        self.assertIn("DEMONSTRAÇÃO", texto)

    def test_padrao_com_chave_groq_liga_groq_com_limite_8_e_pausa_75(self):
        falso = type("J", (), {"modo": "groq", "modelo": "openai/gpt-oss-120b", "versao_prompt": "juiz-v1.3"})()
        with patch.object(app, "criar_juiz", side_effect=lambda modo: falso if modo == "groq" else None) as fabrica:
            texto, servico = self.rodar(["--gerador", "demonstracao"], {"GROQ_API_KEY": "x"})
        fabrica.assert_called_once_with("groq")
        self.assertEqual((servico.limite_diario_juiz, servico.pausa_juiz_s, servico.pausa_juiz_413_s, servico.ciclos_juiz),
                         (8, 75, 120, 1))
        self.assertIn("Limite do Juiz: 8 avaliações por dia; usadas hoje: 0.", texto)

    def test_desligado_explicito_mesmo_com_chave(self):
        texto, servico = self.rodar(["--gerador", "demonstracao", "--juiz", "desligado"], {"GROQ_API_KEY": "x"})
        self.assertIsNone(servico.juiz)
        self.assertNotIn("GROQ_API_KEY não definida", texto)

    def test_valores_negativos_recusados(self):
        for opcao in ("--ciclos-juiz", "--limite-diario-juiz"):
            with self.subTest(opcao=opcao), self.assertRaises(SystemExit), redirect_stderr(io.StringIO()):
                app.main(["--gerador", "demonstracao", opcao, "-1"])
