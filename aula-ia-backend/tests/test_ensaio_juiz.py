"""Persistência, proveniência e CLI; nenhuma chamada real nos testes."""
from copy import deepcopy
from contextlib import closing, redirect_stdout
from hashlib import sha256
import io
import json
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import Mock, patch

from casos_juiz import carregar_caso, exportar_sqlite, hash_json, salvar_novo, validar_caso
from ensaio_juiz import executar_ensaio, main, metricas
from groq_juiz import AgenteGroqJuiz
from test_groq_juiz import CHAVE, FIXTURE, Transporte, envelope

REAL = Path(__file__).resolve().parents[2] / "experimentos/juiz/casos/ordenacao_real_994c4cd5.json"


def sintetico():
    return dict(plano=deepcopy(FIXTURE["plano_esperado"]), entrada=deepcopy(FIXTURE["entrada"]),
                modelo_gerador="sintetico-sem-LLM", revisao=1, origem={"tipo": "sintetica"})


class TestEnsaioJuiz(TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.caso = self.base / "caso.json"
        salvar_novo(self.caso, sintetico())

    def test_sucesso_persiste_parecer_rastreio_versoes_e_hashes(self):
        antes = self.caso.read_bytes()
        t = Transporte(envelope())
        fabrica = lambda **kw: AgenteGroqJuiz(chave=CHAVE, transporte=t, **kw)
        r, arquivo = executar_ensaio(self.caso, self.base, fabrica=fabrica)
        salvo = json.loads(arquivo.read_text(encoding="utf-8"))
        self.assertEqual(salvo, r)
        self.assertEqual(r["status"], "sucesso")
        self.assertEqual(r["origem"]["tipo"], "sintetica")
        self.assertEqual(r["metricas"]["total_tokens_conhecido"], 180)
        self.assertEqual(r["ciclos_pedagogicos_executados"], 0)
        self.assertEqual(r["aprovacao_docente"], "nao_alterada")
        self.assertEqual(r["arquivo_caso_sha256"], sha256(antes).hexdigest())
        self.assertEqual(self.caso.read_bytes(), antes)
        self.assertTrue((arquivo.parent / "inicio.json").is_file())
        self.assertEqual(carregar_caso(arquivo.parent / "caso.json"), carregar_caso(self.caso))
        self.assertIn("groq_juiz.py", r["codigo"]["arquivos_sha256"])
        self.assertNotIn(CHAVE, arquivo.read_text(encoding="utf-8"))

    def test_falha_contrato_preserva_resposta_e_diagnosticos(self):
        t = Transporte(envelope({}))
        r, arquivo = executar_ensaio(self.caso, self.base,
                                    fabrica=lambda **kw: AgenteGroqJuiz(chave=CHAVE, transporte=t, **kw))
        self.assertEqual(r["status"], "falha")
        self.assertEqual(r["tipo_erro"], "contrato")
        self.assertTrue(r["diagnosticos"])
        self.assertEqual(r["rastreio"][0]["conteudo_bruto"], "{}")
        self.assertTrue(arquivo.exists())
        self.assertEqual(len(t.chamadas), 1)

    def test_sem_chave_grava_falha_sem_rede(self):
        with patch.dict("os.environ", {}, clear=True):
            r, arquivo = executar_ensaio(self.caso, self.base)
        self.assertEqual(r["status"], "falha")
        self.assertEqual(r["tipo_erro"], "configuracao")
        self.assertEqual(r["metricas"]["chamadas_http"], 0)
        self.assertIsNone(r["metricas"]["total_tokens_conhecido"])
        self.assertTrue(arquivo.exists())

    def test_somente_validar_nao_constroi_agente(self):
        f = Mock(side_effect=AssertionError("não chamar"))
        r, _ = executar_ensaio(self.caso, self.base, somente_validar=True, fabrica=f)
        self.assertEqual(r["status"], "validado_localmente")
        f.assert_not_called()

    def test_caso_invalido_persiste_falha_sem_api(self):
        self.caso.write_text("{}", encoding="utf-8")
        f = Mock()
        r, arquivo = executar_ensaio(self.caso, self.base, fabrica=f)
        self.assertEqual(r["status"], "falha")
        self.assertTrue(arquivo.exists())
        f.assert_not_called()

    def test_arquivo_ausente_fica_registrado(self):
        r, arquivo = executar_ensaio(self.base / "ausente.json", self.base)
        self.assertEqual(r["status"], "falha")
        self.assertTrue(arquivo.exists())

    def test_repeticoes_geram_diretorios_distintos(self):
        _, a = executar_ensaio(self.caso, self.base, somente_validar=True)
        _, b = executar_ensaio(self.caso, self.base, somente_validar=True)
        self.assertNotEqual(a, b)

    def test_salvar_nao_sobrescreve(self):
        with self.assertRaises(FileExistsError):
            salvar_novo(self.caso, {})
        self.assertEqual(carregar_caso(self.caso), sintetico())

    def test_hash_detecta_edicao_do_original(self):
        c = carregar_caso(REAL)
        c["plano"]["objetivo_geral"] += " alteração"
        with self.assertRaisesRegex(ValueError, "Hash de plano"):
            validar_caso(c)

    def test_caso_real_e_o_da_revisao_nao_a_fixture(self):
        c = carregar_caso(REAL)
        self.assertEqual(c["origem"]["geracao_id"], "994c4cd51d944ca6a1344b15366c3971")
        self.assertEqual(hash_json(c["plano"]), "1b3bfddcee405c918e70d91faf1cd931419b71be84e5556885fe05b4dfec352d")
        self.assertEqual([e["minutos"] for e in c["plano"]["desenvolvimento"]], [15, 35])
        self.assertNotEqual(c["plano"], FIXTURE["plano_esperado"])
        self.assertIn("maior número", c["plano"]["avaliacao_aprendizagem"]["evidencias"][0]["evidencia_esperada"])

    def test_metricas_parciais_nao_inventam_custo(self):
        m = metricas([{"chamadas_http": 1, "usage": {"total_tokens": 30}}, {"chamadas_http": 1}])
        self.assertEqual(m["total_tokens_conhecido"], 30)
        self.assertEqual(m["respostas_com_usage"], 1)
        self.assertIsNone(m["prompt_tokens_conhecido"])
        self.assertIsNone(m["custo_informado"])

    def test_cli_codigos_saida(self):
        with redirect_stdout(io.StringIO()), patch.dict("os.environ", {}, clear=True):
            base = ["avaliar", "--caso", str(self.caso), "--destino", str(self.base)]
            self.assertEqual(main(base + ["--somente-validar"]), 0)
            self.assertEqual(main(base), 1)

    def test_segredo_na_entrada_nao_vaza_nem_chama_api(self):
        c = sintetico()
        c["plano"]["objetivo_geral"] += CHAVE
        self.caso.write_text(json.dumps(c), encoding="utf-8")
        f = Mock()
        r, arquivo = executar_ensaio(self.caso, self.base, fabrica=f)
        self.assertEqual(r["status"], "falha")
        self.assertNotIn(CHAVE, arquivo.read_text(encoding="utf-8"))
        self.assertFalse((arquivo.parent / "caso.json").exists())
        f.assert_not_called()


class TestExportacaoSQLite(TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.banco = Path(self.temp.name) / "dados.sqlite3"
        self.entrada = FIXTURE["entrada"]
        consulta = {"contexto": self.entrada["contexto"], "resultados": [{"habilidade": self.entrada["habilidade"]}]}
        self.resultado = dict(plano=FIXTURE["plano_esperado"], modo="ia", contrato="plano-aula-2.0",
                              modelo="modelo-simulado-no-teste", provedor="simulado", rastreio=[])
        with closing(sqlite3.connect(self.banco)) as db, db:
            db.executescript("CREATE TABLE consultas(id TEXT,dados TEXT,codigo_confirmado TEXT);"
                             "CREATE TABLE geracoes(id TEXT,consulta_id TEXT,revisao INTEGER,estado TEXT,resultado TEXT,criado_em TEXT);")
            db.execute("INSERT INTO consultas VALUES(?,?,?)", ("consulta-teste", json.dumps(consulta), self.entrada["habilidade"]["codigo"]))
            db.execute("INSERT INTO geracoes VALUES(?,?,?,?,?,?)", ("id-teste", "consulta-teste", 1, "rascunho", json.dumps(self.resultado), "2026-11-17 00:00:00"))

    def test_exporta_exatamente_sem_modificar_banco(self):
        antes = self.banco.read_bytes()
        c = exportar_sqlite(self.banco, "id-teste")
        self.assertEqual(c["plano"], self.resultado["plano"])
        self.assertEqual(c["origem"]["estado_original"], "rascunho")
        self.assertEqual(c["origem"]["resultado_sqlite_sha256"], sha256(json.dumps(self.resultado).encode()).hexdigest())
        self.assertEqual(self.banco.read_bytes(), antes)

    def test_id_ausente_e_banco_ausente_nao_criam_dados(self):
        with self.assertRaises(ValueError):
            exportar_sqlite(self.banco, "outro-id")
        ausente = self.banco.parent / "ausente.sqlite3"
        with self.assertRaises(sqlite3.Error):
            exportar_sqlite(ausente, "id-teste")
        self.assertFalse(ausente.exists())

    def test_falha_e_demonstracao_nao_viram_plano_real(self):
        for campo, valor in (("estado", "falha"), ("resultado", json.dumps({**self.resultado, "modo": "demonstracao"}))):
            with closing(sqlite3.connect(self.banco)) as db, db:
                db.execute("UPDATE geracoes SET estado='rascunho'")
                db.execute(f"UPDATE geracoes SET {campo}=?", (valor,))
            with self.subTest(campo=campo), self.assertRaises(ValueError):
                exportar_sqlite(self.banco, "id-teste")
