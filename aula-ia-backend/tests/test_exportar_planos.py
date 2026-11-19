"""exportar_planos.py: exporta todos os planos reais do SQLite, em leitura, sem sobrescrever. Execute a partir de aula-ia-backend."""
from contextlib import closing, redirect_stdout, redirect_stderr
import io
import json
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch
import os

from casos_juiz import carregar_caso
from exportar_planos import _slug, exportar_todos, listar_geracoes, main

FIXTURE = json.loads((Path(__file__).parent / "dados" / "plano_v2" / "fixture_ordenacao.json").read_text(encoding="utf-8"))


class TestExportarPlanos(TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.raiz = Path(self.temp.name)
        self.banco = self.raiz / "dados.sqlite3"
        self.entrada = FIXTURE["entrada"]
        with closing(sqlite3.connect(self.banco)) as db, db:
            db.executescript("CREATE TABLE consultas(id TEXT,dados TEXT,codigo_confirmado TEXT);"
                             "CREATE TABLE geracoes(id TEXT,consulta_id TEXT,revisao INTEGER,estado TEXT,resultado TEXT,criado_em TEXT);")

    def inserir(self, gid, consulta, tema, estado="rascunho", modo="ia", revisao=1, criado="2026-11-18 10:00:00", plano=None, tema_do_plano=True):
        contexto = {**self.entrada["contexto"], "tema": tema}
        dados = {"contexto": contexto, "resultados": [{"habilidade": self.entrada["habilidade"]}]}
        plano = plano or json.loads(json.dumps(FIXTURE["plano_esperado"]))
        if plano["identificacao"]["tema"] != tema and tema_do_plano:
            plano["identificacao"].update(tema=tema, titulo=f"Plano de aula — {tema}")
        resultado = dict(plano=plano, modo=modo, contrato="plano-aula-2.0", modelo="modelo-de-teste",
                         provedor="simulado", rastreio=[])
        with closing(sqlite3.connect(self.banco)) as db, db:
            if not db.execute("SELECT 1 FROM consultas WHERE id=?", (consulta,)).fetchone():
                db.execute("INSERT INTO consultas VALUES(?,?,?)", (consulta, json.dumps(dados), self.entrada["habilidade"]["codigo"]))
            db.execute("INSERT INTO geracoes VALUES(?,?,?,?,?,?)", (gid, consulta, revisao, estado, json.dumps(resultado), criado))

    def test_exporta_so_planos_reais_validos_e_explica_os_pulados(self):
        self.inserir("aaaaaaaa-1", "c1", "Ordenação")
        self.inserir("bbbbbbbb-2", "c2", "Recursão", estado="aprovado", criado="2026-11-18 11:00:00")
        self.inserir("cccccccc-3", "c3", "Demo", modo="demonstracao")
        self.inserir("dddddddd-4", "c4", "Falhou", estado="falha")
        exportados, pulados = exportar_todos(self.banco, self.raiz / "saida")
        self.assertEqual([e[1] for e in exportados], ["Ordenação", "Recursão"])
        self.assertEqual(carregar_caso(exportados[1][0])["plano"]["identificacao"]["tema"], "Recursão")
        self.assertEqual(sorted(p[1] for p in pulados), ["Demo", "Falhou"])
        self.assertTrue(all(p[2] for p in pulados))  # todo pulo traz motivo
        for arquivo, _, _ in exportados:
            self.assertTrue(carregar_caso(arquivo)["plano"]["objetivo_geral"])  # arquivo válido e relê pelo validador

    def test_nome_do_arquivo_tem_tema_revisao_e_id(self):
        self.inserir("abcd1234-x", "c1", "Árvores e Grafos!", revisao=3)
        (arquivo, _, _), = exportar_todos(self.banco, self.raiz / "saida")[0]
        self.assertEqual(arquivo.name, "arvores-e-grafos_r3_abcd1234.json")

    def test_nao_sobrescreve_e_nao_modifica_o_banco(self):
        self.inserir("aaaaaaaa-1", "c1", "Ordenação")
        antes = self.banco.read_bytes()
        exportar_todos(self.banco, self.raiz / "saida")
        exportados, pulados = exportar_todos(self.banco, self.raiz / "saida")  # 2ª vez
        self.assertEqual(exportados, [])
        self.assertIn("não sobrescrito", pulados[0][2])
        self.assertEqual(self.banco.read_bytes(), antes)

    def test_credencial_no_caso_impede_exportar(self):
        plano = json.loads(json.dumps(FIXTURE["plano_esperado"]))
        plano["metodologia"] = "use a chave AIzaSyA1234567890abcdefghijklmnopqrstuv no passo 1"
        self.inserir("aaaaaaaa-1", "c1", "Ordenação", plano=plano)
        exportados, pulados = exportar_todos(self.banco, self.raiz / "saida")
        self.assertEqual(exportados, [])
        self.assertEqual(len(pulados), 1)
        self.assertFalse((self.raiz / "saida").exists() and list((self.raiz / "saida").iterdir()))

    def test_chave_gemini_ou_groq_no_texto_impede_exportar(self):
        for i, segredo in enumerate(("AIzaSyA1234567890abcdefghijklmnopqrstuv", "gsk_abcdefghij1234567890")):
            plano = json.loads(json.dumps(FIXTURE["plano_esperado"]))
            plano["metodologia"] = f"texto {segredo} texto"
            self.inserir(f"seg{i}", f"cs{i}", "Ordenação", plano=plano)
        exportados, pulados = exportar_todos(self.banco, self.raiz / "saida")
        self.assertEqual((len(exportados), len(pulados)), (0, 2))
        self.assertTrue(all("credencial" in p[2] for p in pulados))

    def test_regex_propria_pega_chave_mesmo_sem_o_sanitizar_do_juiz(self):
        # Segunda camada: se o sanitizar() do Juiz mudar, a regex do exportador continua barrando as chaves.
        for i, segredo in enumerate(("AIzaSyA1234567890abcdefghijklmnopqrstuv", "gsk_abcdefghij1234567890")):
            plano = json.loads(json.dumps(FIXTURE["plano_esperado"]))
            plano["metodologia"] = f"texto {segredo} texto"
            self.inserir(f"sem{i}", f"cz{i}", "Ordenação", plano=plano)
        with patch("exportar_planos.sanitizar", lambda valor: valor):
            exportados, pulados = exportar_todos(self.banco, self.raiz / "saida")
        self.assertEqual((len(exportados), len(pulados)), (0, 2))

    def test_plano_que_viola_o_contrato_e_pulado_sem_derrubar_o_lote(self):
        ruim = json.loads(json.dumps(FIXTURE["plano_esperado"]))
        ruim["identificacao"]["tema"] = "Outro tema"  # difere do contexto: o contrato recusa
        self.inserir("ruim0001", "c1", "Ordenação", plano=ruim, criado="2026-11-18 09:00:00", tema_do_plano=False)
        self.inserir("bom00001", "c2", "Recursão", criado="2026-11-18 10:00:00")
        exportados, pulados = exportar_todos(self.banco, self.raiz / "saida")
        self.assertEqual([e[1] for e in exportados], ["Recursão"])
        self.assertEqual([p[1] for p in pulados], ["Ordenação"])

    def test_listar_em_ordem_de_criacao_com_tema(self):
        self.inserir("g2", "c2", "Segundo", criado="2026-11-18 12:00:00")
        self.inserir("g1", "c1", "Primeiro", criado="2026-11-18 09:00:00")
        self.assertEqual([g[5] for g in listar_geracoes(self.banco)], ["Primeiro", "Segundo"])

    def test_listar_nao_cria_banco_inexistente(self):
        ausente = self.raiz / "ausente.sqlite3"
        with self.assertRaises(sqlite3.OperationalError):
            listar_geracoes(ausente)
        self.assertFalse(ausente.exists())

    def test_chave_do_ambiente_no_texto_impede_exportar(self):
        plano = json.loads(json.dumps(FIXTURE["plano_esperado"]))
        plano["metodologia"] = "texto valorSecretoDeTeste123456 texto"
        self.inserir("amb00001", "c1", "Ordenação", plano=plano)
        with patch.dict(os.environ, {"GROQ_API_KEY": "valorSecretoDeTeste123456"}):
            exportados, pulados = exportar_todos(self.banco, self.raiz / "saida")
        self.assertEqual((len(exportados), len(pulados)), (0, 1))

    def test_consulta_corrompida_aparece_com_tema_interrogacao_e_e_pulada(self):
        with closing(sqlite3.connect(self.banco)) as db, db:
            db.execute("INSERT INTO consultas VALUES(?,?,?)", ("cx", "isto não é json", "EF08CO03"))
            db.execute("INSERT INTO geracoes VALUES(?,?,?,?,?,?)", ("quebrado1", "cx", 1, "rascunho", "{}", "2026-11-18 08:00:00"))
        self.assertEqual(listar_geracoes(self.banco)[0][5], "?")
        exportados, pulados = exportar_todos(self.banco, self.raiz / "saida")
        self.assertEqual((len(exportados), len(pulados)), (0, 1))

    def test_slug(self):
        self.assertEqual(_slug("Ordenação"), "ordenacao")
        self.assertEqual(_slug("???"), "plano")
        self.assertEqual(len(_slug("a" * 100)), 40)

    def test_main_codigos_de_saida(self):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            self.assertEqual(main(["--banco", str(self.raiz / "nao_existe.sqlite3"), "--saida", str(self.raiz / "s")]), 2)
            self.assertEqual(main(["--banco", str(self.banco), "--saida", str(self.raiz / "s")]), 1)  # vazio
            self.inserir("aaaaaaaa-1", "c1", "Ordenação")
            self.assertEqual(main(["--banco", str(self.banco), "--saida", str(self.raiz / "s")]), 0)
        self.assertIn("Exportados: 1", out.getvalue())
        self.assertIn("banco não encontrado", err.getvalue())
