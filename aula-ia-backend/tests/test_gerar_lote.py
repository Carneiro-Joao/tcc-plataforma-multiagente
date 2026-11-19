"""Lote de geração (gerar_lote.py) e as entradas do protocolo PoC07B. Sem rede. Execute a partir de aula-ia-backend."""
from contextlib import closing, redirect_stdout
from copy import deepcopy
import io
import json
from pathlib import Path
import re
import sqlite3
from tempfile import TemporaryDirectory
from unittest import TestCase

import gerar_lote
from erros import ErroGeracao
from rag.search import BuscaCurricular
from servico import ServicoCurricular

RAIZ = Path(__file__).resolve().parents[2]
ENTRADAS = RAIZ / "experimentos" / "geracao" / "poc07b_entradas.json"
PROTOCOLO = RAIZ / "docs" / "PoC07B_Prompt_2_3.md"
FIXTURE = json.loads((Path(__file__).parent / "dados/plano_v2/fixture_ordenacao.json").read_text(encoding="utf-8"))
UMA = dict(tema="Ordenação", tipo="Aula prática", duracao_min=50, recursos="quadro e pincel", habilidade="EF08CO03")


class GeradorRoteirizado:
    """Gerador 'ia' falso: cada chamada consome o próximo item do roteiro ("ok" ou uma mensagem de erro)."""
    modo, modelo, VERSAO_CONTRATO = "ia", "falso", "plano-aula-2.0"

    def __init__(self, roteiro):
        self.roteiro, self.entradas = list(roteiro), []

    def gerar(self, entrada, revisao):
        self.entradas.append((deepcopy(entrada), revisao))
        passo = self.roteiro.pop(0) if self.roteiro else "ok"
        if passo != "ok":
            raise ErroGeracao(passo, tipo="http")
        return dict(plano=deepcopy(FIXTURE["plano_esperado"]), modo="ia", contrato="plano-aula-2.0", rastreio=[])


class TestEntradasDoProtocolo(TestCase):
    def test_entradas_sao_exatamente_a_tabela_do_protocolo(self):
        linhas = [l for l in PROTOCOLO.read_text(encoding="utf-8").splitlines() if re.match(r"^\| \d \|", l)]
        tabela = []
        for l in linhas:
            _, tema, tipo, duracao, recursos, habilidade = [c.strip() for c in l.strip("|").split("|")]
            tabela.append(dict(tema=tema, tipo=tipo, duracao_min=int(duracao), recursos=recursos, habilidade=habilidade))
        self.assertEqual(len(tabela), 5)
        self.assertEqual(gerar_lote.ler_entradas(ENTRADAS), tabela)

    def test_ler_entradas_recusa_campo_faltando_sobrando_ou_tipo_errado(self):
        with TemporaryDirectory() as d:
            arq = Path(d) / "e.json"
            for ruim in ([], [dict(UMA, extra=1)], [{k: v for k, v in UMA.items() if k != "habilidade"}],
                         [dict(UMA, duracao_min="50")], [dict(UMA, duracao_min=0)], [dict(UMA, tema="  ")], ["x"]):
                arq.write_text(json.dumps(ruim), encoding="utf-8")
                with self.subTest(ruim=ruim), self.assertRaises(ValueError):
                    gerar_lote.ler_entradas(arq)
            arq.write_text(json.dumps({"entradas": [dict(UMA, ano="8º ano")]}), encoding="utf-8")
            self.assertEqual(gerar_lote.ler_entradas(arq)[0]["ano"], "8º ano")


class TestExecutarLote(TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.banco = Path(temp.name) / "t.sqlite3"
        self.pausas, self.mensagens = [], []

    def rodar(self, entradas, roteiro=(), limite=None):
        self.gerador = GeradorRoteirizado(roteiro)
        servico = ServicoCurricular(BuscaCurricular(), self.banco, self.gerador, limite_diario_ia=limite)
        return gerar_lote.executar_lote(entradas, servico, dormir=self.pausas.append, saida=self.mensagens.append)

    def geracoes(self):
        with closing(sqlite3.connect(self.banco)) as db:
            return db.execute("SELECT g.revisao, g.estado, c.codigo_confirmado FROM geracoes g "
                              "JOIN consultas c ON c.id = g.consulta_id ORDER BY g.criado_em").fetchall()

    def test_caminho_feliz_confirma_a_habilidade_indicada_e_pausa_entre_planos(self):
        entradas = [UMA, dict(UMA, tema="Listas", habilidade="EF08CO02"), dict(UMA, tema="Programação", habilidade="EF08CO01")]
        linhas, parou = self.rodar(entradas)
        self.assertIsNone(parou)
        self.assertEqual([l["situacao"] for l in linhas], ["ok"] * 3)
        self.assertEqual([e["habilidade"]["codigo"] for e, _ in self.gerador.entradas], ["EF08CO03", "EF08CO02", "EF08CO01"])
        self.assertEqual(self.pausas, [30, 30])  # entre planos, não depois do último
        self.assertEqual([r[0] for r in self.geracoes()], [1, 1, 1])
        self.assertEqual(len(self.mensagens), 3)
        self.assertIn("#1 Ordenação | Aula prática | ok | tentativas: 1", self.mensagens[0])

    def test_contexto_enviado_e_o_da_entrada(self):
        self.rodar([dict(UMA, recursos="projetor, computadores", duracao_min=90, tipo="Aula teórica")])
        contexto = self.gerador.entradas[0][0]["contexto"]
        self.assertEqual((contexto["recursos"], contexto["duracao_min"], contexto["tipo"], contexto["ano"]),
                         ("projetor, computadores", 90, "Aula teórica", "8º ano"))

    def test_habilidade_fora_da_busca_usa_catalogo(self):
        linhas, _ = self.rodar([dict(UMA, habilidade="EF08CO10")])
        self.assertEqual((linhas[0]["situacao"], linhas[0]["modo_consulta"]), ("ok", "catalogo"))
        self.assertEqual(self.gerador.entradas[0][0]["habilidade"]["codigo"], "EF08CO10")
        linhas, _ = self.rodar([UMA])
        self.assertEqual(linhas[0]["modo_consulta"], "tema")

    def test_falha_tecnica_espera_60_e_refaz_uma_vez_com_consulta_nova_revisao_1(self):
        linhas, parou = self.rodar([UMA, UMA], roteiro=["Gemini HTTP 503: indisponível", "ok", "ok"])
        self.assertIsNone(parou)
        self.assertEqual((linhas[0]["situacao"], linhas[0]["tentativas"]), ("ok", 2))
        self.assertEqual(self.pausas, [60, 30])
        self.assertEqual(self.geracoes(), [(1, "falha", "EF08CO03"), (1, "rascunho", "EF08CO03"), (1, "rascunho", "EF08CO03")])
        self.assertEqual(linhas[0]["erros"], ["502: Gemini HTTP 503: indisponível"])

    def test_duas_falhas_na_mesma_linha_seguem_para_a_proxima(self):
        linhas, parou = self.rodar([UMA, UMA], roteiro=["Contrato inválido", "Gemini HTTP 400: recusada", "ok"])
        self.assertIsNone(parou)
        self.assertEqual([(l["situacao"], l["tentativas"]) for l in linhas], [("falha", 2), ("ok", 1)])
        self.assertEqual(len(self.gerador.entradas), 3)  # nunca uma terceira tentativa na mesma linha

    def test_duas_cotas_seguidas_param_tudo(self):
        linhas, parou = self.rodar([UMA, UMA, UMA], roteiro=["Gemini HTTP 429: Cota", "Gemini HTTP 429: Cota"])
        self.assertIn("429", parou)
        self.assertEqual(len(linhas), 1)
        self.assertEqual(len(self.gerador.entradas), 2)
        self.assertTrue(self.mensagens[-1].startswith("PARADO"))

    def test_cota_isolada_nao_para(self):
        linhas, parou = self.rodar([UMA, UMA], roteiro=["Gemini HTTP 429: Cota", "ok", "ok"])
        self.assertIsNone(parou)
        self.assertEqual([l["situacao"] for l in linhas], ["ok", "ok"])

    def test_cotas_separadas_por_sucesso_nao_param(self):
        linhas, parou = self.rodar([UMA, UMA], roteiro=["Gemini HTTP 429: Cota", "ok", "Gemini HTTP 429: Cota", "ok"])
        self.assertIsNone(parou)

    def test_limite_diario_do_app_para_o_lote_sem_chamar_o_gerador(self):
        linhas, parou = self.rodar([UMA, UMA, UMA], limite=1)
        self.assertEqual(parou, "limite diário atingido")
        self.assertEqual([l["situacao"] for l in linhas], ["ok", "limite diário"])
        self.assertEqual(len(self.gerador.entradas), 1)

    def test_nao_apaga_geracoes_existentes(self):
        self.rodar([UMA])
        antes = self.geracoes()
        self.rodar([UMA])
        self.assertEqual(self.geracoes()[:1], antes)
        self.assertEqual(len(self.geracoes()), 2)

    def test_eh_cota(self):
        self.assertTrue(gerar_lote.eh_cota("Gemini HTTP 429: Cota ou limite"))
        self.assertTrue(gerar_lote.eh_cota("cota excedida"))
        self.assertFalse(gerar_lote.eh_cota("Gemini HTTP 503: indisponível"))


class TestMain(TestCase):
    def test_somente_validar_roda_tudo_sem_rede_e_sem_tocar_o_banco_real(self):
        with TemporaryDirectory() as d:
            banco = Path(d) / "real.sqlite3"
            saida = io.StringIO()
            with redirect_stdout(saida):
                codigo = gerar_lote.main(["--entradas", str(ENTRADAS), "--somente-validar", "--banco", str(banco)],
                                         dormir=lambda s: self.fail("não deve pausar em --somente-validar"))
            self.assertEqual(codigo, 0, saida.getvalue())
            self.assertFalse(banco.exists())
            self.assertIn("Resumo: 5/5 planos gerados.", saida.getvalue())
            self.assertEqual(saida.getvalue().count("| ok |"), 5)

    def test_modo_real_respeita_o_limite_diario_no_banco_indicado(self):
        """Protege a cota: no modo real o lote usa --limite-diario e para quando o dia acaba (sem rede: gerador falso)."""
        from unittest.mock import patch
        with TemporaryDirectory() as d:
            banco, entradas = Path(d) / "real.sqlite3", Path(d) / "e.json"
            entradas.write_text(json.dumps([UMA, UMA, UMA]), encoding="utf-8")
            falso = GeradorRoteirizado([])
            saida = io.StringIO()
            with patch.object(gerar_lote, "montar_gerador", return_value=falso), redirect_stdout(saida):
                codigo = gerar_lote.main(["--entradas", str(entradas), "--banco", str(banco), "--limite-diario", "2"],
                                         dormir=lambda s: None)
            self.assertEqual(codigo, 3, saida.getvalue())
            self.assertEqual(len(falso.entradas), 2)
            self.assertIn("limite diário atingido", saida.getvalue())
            self.assertIn("Limite: 2 planos com IA por dia; usados hoje: 0; cabem: 2.", saida.getvalue())
            self.assertTrue(banco.exists())

    def test_limite_zero_ou_negativo_e_recusado(self):
        for valor in ("0", "-1"):
            with self.subTest(valor=valor), self.assertRaises(SystemExit), redirect_stdout(io.StringIO()):
                import contextlib
                with contextlib.redirect_stderr(io.StringIO()):
                    gerar_lote.main(["--entradas", str(ENTRADAS), "--limite-diario", valor, "--somente-validar"])
