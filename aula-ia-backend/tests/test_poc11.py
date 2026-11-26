"""PoC 11: acento em campos curtos (títulos) + recomendação ao professor quando a entrada tem conflito. Sem rede."""
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

import acentuacao
from geracao_v2 import GeradorDePlanoCompleto
from rag.search import BuscaCurricular
from servico import ServicoCurricular, alertas_recursos
from test_gemini import envelope
from test_poc10 import SAIDAS, dados, gerar, normais

SEQUENCIA_TITULO_SEM_ACENTO = deepcopy(SAIDAS["sequencia"])
SEQUENCIA_TITULO_SEM_ACENTO["etapas"][1]["titulo"] = "Demonstracao"  # original: "Demonstração"; o resto da saída tem acento


class TestAcentoEmCampoCurto(TestCase):
    def test_titulo_curto_com_palavra_inequivoca_conta(self):
        for titulo in ("Introducao ao Conceito e Elemento Central", "Execucao Completa e Fechamento da Busca Binaria",
                       "Simulacao", "O que nao fazer", "Revisao final"):
            with self.subTest(titulo=titulo):
                self.assertEqual(acentuacao.campos_sem_acentuacao({"etapas": [{"titulo": titulo}]}), ["etapas[0].titulo"])

    def test_campo_curto_com_palavra_ambigua_ou_acentuado_nao_conta(self):
        for titulo in ("O aluno pratica", "Analise de dados", "Sequencia de passos", "Ate o fim", "Introdução ao Conceito",
                       "Problema inicial", "OBJ1", "ET2"):
            with self.subTest(titulo=titulo):
                self.assertEqual(acentuacao.campos_sem_acentuacao({"titulo": titulo}), [])

    def test_campo_longo_mantem_a_regra_ampla(self):
        longo = "Os estudantes praticam a logica de comparacao em duplas durante toda a atividade da aula de hoje"
        self.assertEqual(acentuacao.campos_sem_acentuacao({"t": longo.replace("comparacao", "troca")}), ["t"])  # só "logica"
        self.assertEqual(acentuacao.campos_sem_acentuacao({"t": "O aluno pratica"}), [])  # curto: "pratica" não basta
        self.assertEqual(acentuacao.campos_sem_acentuacao({"recursos": "Introducao"}), [])  # copiado do contexto (C2)
        self.assertEqual(acentuacao.VERSAO, "deteccao-acentuacao-1.2")

    def test_titulo_sem_acento_recebe_reescrita_no_gerador(self):
        depois = [envelope(SAIDAS["avaliacao_final"]), envelope(SAIDAS["adaptacao"])]
        resultado, t = gerar(normais("sequencia") + [envelope(SEQUENCIA_TITULO_SEM_ACENTO), envelope(SAIDAS["sequencia"])] + depois)
        self.assertEqual(len(t.pedidos), 7)
        self.assertEqual(dados(t.pedidos[4])["reparo_estrutural"]["diagnosticos"], [{"caminho": "etapas[1].titulo", "regra": "sem_acentuacao"}])
        self.assertEqual(resultado["plano"]["desenvolvimento"][1]["titulo"], "Demonstração")
        reg = [r for r in resultado["rastreio"] if r.get("tentativa") == "acentuacao"]
        self.assertEqual([(r["agente"], r["estado"], r["regra"]) for r in reg], [("sequencia", "validado", "deteccao-acentuacao-1.2")])


class TestRecomendacaoAoProfessor(TestCase):
    def consulta(self, codigo, recursos, tipo):
        return {"entrada_geracao": {"habilidade": {"codigo": codigo}, "contexto": {"recursos": recursos, "tipo": tipo}}}

    def codigos(self, *args):
        return [a["codigo"] for a in alertas_recursos(self.consulta(*args))]

    def test_regras(self):
        for codigo in ("EF08CO01", "EF08CO02"):
            with self.subTest(codigo=codigo):
                # cenário 4 do lote de 25/11: teórica, sem computador → as duas recomendações
                self.assertEqual(self.codigos(codigo, "quadro e pincel, projetor", "Aula teórica"),
                                 ["habilidade_sem_computador", "habilidade_aula_teorica"])
                self.assertEqual(self.codigos(codigo, "computadores", "Aula teórica"), ["habilidade_aula_teorica"])
                self.assertEqual(self.codigos(codigo, "material impresso", "Aula prática"), ["habilidade_sem_computador"])
                self.assertEqual(self.codigos(codigo, "projetor, computadores", "Aula prática"), [])
                self.assertEqual(self.codigos(codigo, "computadores", "Projeto"), [])
        self.assertEqual(self.codigos("EF08CO03", "quadro e pincel", "Aula teórica"), [])
        self.assertEqual(self.codigos("EF08CO10", "quadro e pincel", "Aula teórica"), [])

    def test_cada_alerta_tem_mensagem_e_recomendacao_com_a_habilidade(self):
        for a in alertas_recursos(self.consulta("EF08CO02", "quadro e pincel", "Aula teórica")):
            with self.subTest(codigo=a["codigo"]):
                self.assertIn("EF08CO02", a["mensagem"])
                self.assertIn("EF08CO02", a["recomendacao"])
                self.assertIn("gere de novo", a["recomendacao"])
                self.assertIn("outra habilidade", a["recomendacao"])

    def test_aparece_na_consulta_e_nao_bloqueia_a_geracao(self):
        with TemporaryDirectory() as d:
            s = ServicoCurricular(BuscaCurricular(), Path(d) / "t.sqlite3", GeradorDePlanoCompleto("demonstracao"))
            c = s.consultar({"contexto": {"ano": "8º ano", "tema": "listas", "duracao_min": 50, "tipo": "Aula teórica",
                                          "recursos": "quadro e pincel, projetor"}, "consulta": "catalogo"})
            s.confirmar(c["id"], "EF08CO02")
            r = s.gerar(c["id"])
            self.assertEqual(r["geracao_atual"]["estado"], "rascunho")
            self.assertEqual([a["codigo"] for a in r["alertas"]], ["habilidade_sem_computador", "habilidade_aula_teorica"])
