"""Testes dos contratos da PoC 04A (poc04a-0.1). Offline: sem API, sem rede, sem bibliotecas extras.

A tabela de casos (tests/dados/poc04a/casos_estruturais.json) vem do pacote de contratos:
são 27 casos escritos depois da primeira rodada real (respostas reais da API, variações
inválidas de duração e alterações de estrutura). São testes de CARACTERIZAÇÃO: protegem
contra regressão e documentam as decisões do contrato, mas não provam qualidade pedagógica.
"""
import json
from copy import deepcopy
from pathlib import Path
from unittest import TestCase

from contratos.validacao import CONTRATOS, decodificar, validar

DADOS = Path(__file__).resolve().parent / "dados" / "poc04a"
FIXTURE = json.loads((DADOS / "fixture_ordenacao.json").read_text(encoding="utf-8"))
CASOS = json.loads((DADOS / "casos_estruturais.json").read_text(encoding="utf-8"))
POR_NOME = {caso["caso"]: caso for caso in CASOS}
ENTRADA = FIXTURE["entrada"]


def regras(erros):
    return {(e["caminho"], e["regra"]) for e in erros}


def validar_caso(nome):
    caso = POR_NOME[nome]
    return validar(caso["contrato"], caso["entrada"], ENTRADA)


class TestTabelaDeCasos(TestCase):
    def test_tabela_completa(self):
        self.assertEqual(len(CASOS), 27)
        self.assertEqual(len(POR_NOME), 27, "nomes de caso repetidos")
        self.assertTrue({c["contrato"] for c in CASOS} <= set(CONTRATOS))

    def test_cada_caso_tem_o_resultado_esperado(self):
        for caso in CASOS:
            with self.subTest(caso=caso["caso"]):
                erros = validar(caso["contrato"], caso["entrada"], ENTRADA)
                encontrado = "rejeitar" if erros else "aceitar"
                self.assertEqual(encontrado, caso["esperado"], erros)

    def test_rejeicao_sempre_explica_o_caminho_e_a_regra(self):
        for caso in CASOS:
            if caso["esperado"] == "rejeitar":
                with self.subTest(caso=caso["caso"]):
                    erros = validar(caso["contrato"], caso["entrada"], ENTRADA)
                    self.assertTrue(all(e["caminho"] and e["regra"] for e in erros))

    def test_validar_nao_altera_o_que_recebe(self):
        for caso in CASOS:
            with self.subTest(caso=caso["caso"]):
                antes = deepcopy(caso["entrada"])
                validar(caso["contrato"], caso["entrada"], ENTRADA)
                self.assertEqual(antes, caso["entrada"])


class TestFixture(TestCase):
    def test_saidas_sinteticas_e_plano_esperado_sao_validos(self):
        for contrato, saida in FIXTURE["saidas"].items():
            with self.subTest(contrato=contrato):
                self.assertEqual(validar(contrato, saida, ENTRADA), [])
        self.assertEqual(validar("plano", FIXTURE["plano_esperado"], ENTRADA), [])

    def test_plano_esperado_e_a_composicao_das_fontes_unicas(self):
        saidas, contexto, hab = FIXTURE["saidas"], ENTRADA["contexto"], ENTRADA["habilidade"]
        composto = {
            "titulo": "Plano de aula — " + contexto["tema"],
            "habilidade_codigo": hab["codigo"], "habilidade_texto": hab["habilidade"],
            "ano": contexto["ano"], "tema": contexto["tema"],
            "duracao_min": contexto["duracao_min"], "tipo": contexto["tipo"],
            "objetivos": saidas["objetivos"]["objetivos"],
            "metodologia": saidas["metodologia"]["metodologia"],
            "recursos": contexto["recursos"],
            "etapas": saidas["sequencia"]["etapas"],
            "avaliacao": saidas["avaliacao"]["avaliacao"],
            "adaptacoes": saidas["adaptacao"]["adaptacoes"],
        }
        self.assertEqual(composto, FIXTURE["plano_esperado"])


class TestDiagnosticos(TestCase):
    """Cada falha da rodada real precisa apontar o caminho e a regra, para o reparo limitado."""

    def test_metodologia_real_tem_onze_campos_extras(self):
        extras = {c for c, r in regras(validar_caso("resposta_real_metodologia")) if r == "campo_extra"}
        self.assertEqual(extras, {"ano", "codigo_habilidade", "duracao_min", "eixo", "exemplos",
                                  "explicacao_habilidade", "habilidade", "objetivo_revisao",
                                  "objetivos", "tema", "tipo"})

    def test_adaptacoes_reais_vieram_como_objetos(self):
        erros = validar_caso("resposta_real_adaptacao")
        self.assertEqual(regras(erros), {("adaptacoes/0", "tipo_invalido"), ("adaptacoes/1", "tipo_invalido")})
        self.assertTrue(all(e["esperado"] == "string" and e["recebido"] == "object" for e in erros))

    def test_integrador_real_falha_na_estrutura_antes_de_chegar_a_consistencia(self):
        erros = regras(validar_caso("resposta_real_integrador"))
        self.assertIn(("metodologia", "tipo_invalido"), erros)
        self.assertIn(("adaptacoes/0", "tipo_invalido"), erros)

    def test_integrador_real_tambem_alterou_ano_e_tema(self):
        plano = deepcopy(POR_NOME["resposta_real_integrador"]["entrada"])
        plano["metodologia"], plano["adaptacoes"] = "texto", ["a", "b"]  # só corrige a estrutura
        erros = validar("plano", plano, ENTRADA)
        self.assertEqual(regras(erros), {("ano", "entrada_preservada"), ("tema", "entrada_preservada")})

    def test_avaliacao_inventada_passa_na_estrutura(self):
        # Limite documentado: o contrato não detecta resultado fictício (papel da IA Juiz).
        self.assertEqual(validar_caso("resposta_real_avaliacao"), [])

    def test_minutos_nao_sofrem_coercao(self):
        for nome, tipo in (("duracao_string", "string"), ("duracao_booleana", "boolean"),
                           ("duracao_decimal", "number"), ("duracao_float_integral", "number")):
            with self.subTest(caso=nome):
                erros = validar_caso(nome)
                self.assertIn(("etapas/0/minutos", "tipo_invalido"), regras(erros))
                self.assertEqual(erros[0]["recebido"], tipo)

    def test_minutos_zero_e_negativo(self):
        for nome in ("duracao_zero", "duracao_negativa"):
            self.assertIn(("etapas/0/minutos", "minimo"), regras(validar_caso(nome)))

    def test_soma_incorreta_informa_esperado_e_recebido(self):
        erros = validar_caso("soma_incorreta")
        self.assertEqual(regras(erros), {("etapas", "soma_duracao")})
        self.assertEqual(erros[0]["esperado"], 50)
        self.assertNotEqual(erros[0]["recebido"], 50)

    def test_campo_extra_dentro_de_etapa(self):
        self.assertEqual(regras(validar_caso("campo_extra_aninhado")), {("etapas/0/tempo_extra", "campo_extra")})

    def test_entrada_confirmada_nao_pode_ser_alterada(self):
        self.assertEqual(regras(validar_caso("tema_alterado")), {("tema", "entrada_preservada")})
        self.assertEqual(regras(validar_caso("habilidade_reescrita")), {("habilidade_texto", "entrada_preservada")})
        self.assertEqual(regras(validar_caso("recursos_alterados")), {("recursos", "recursos_confirmados")})

    def test_quantidades(self):
        base = FIXTURE["saidas"]
        casos = (("objetivos", {"objetivos": ["só um"]}, "objetivos", "2 a 4"),
                 ("objetivos", {"objetivos": ["a", "b", "c", "d", "e"]}, "objetivos", "2 a 4"),
                 ("adaptacao", {"adaptacoes": ["a", "b", "c"]}, "adaptacoes", "2"),
                 ("adaptacao", {"adaptacoes": ["a"]}, "adaptacoes", "2"))
        for contrato, dados, caminho, esperado in casos:
            with self.subTest(contrato=contrato, dados=dados):
                erros = validar(contrato, dados, ENTRADA)
                self.assertEqual(regras(erros), {(caminho, "quantidade_invalida")})
                self.assertEqual(erros[0]["esperado"], esperado)
        self.assertEqual(regras(validar("sequencia", {"etapas": []}, ENTRADA)), {("etapas", "quantidade_invalida")})
        self.assertEqual(validar("objetivos", base["objetivos"], ENTRADA), [])

    def test_texto_so_com_espacos_e_invalido_mas_o_original_nao_e_reescrito(self):
        dados = {"avaliacao": "  \n\t "}
        erros = validar("avaliacao", dados, ENTRADA)
        self.assertEqual(regras(erros), {("avaliacao", "texto_vazio")})
        self.assertEqual(dados, {"avaliacao": "  \n\t "})
        self.assertEqual(validar("avaliacao", {"avaliacao": "  texto com margem  "}, ENTRADA), [])

    def test_raiz_que_nao_e_objeto(self):
        for bruto in ([], "texto", 5, None):
            with self.subTest(bruto=bruto):
                self.assertEqual(regras(validar("objetivos", bruto, ENTRADA)), {("$", "tipo_invalido")})

    def test_consistencia_so_e_avaliada_com_estrutura_valida(self):
        dados = {"etapas": [{"etapa": "A", "minutos": 10, "atividade": "x", "extra": 1}]}  # soma errada E campo extra
        self.assertEqual(regras(validar("sequencia", dados, ENTRADA)), {("etapas/0/extra", "campo_extra")})

    def test_campos_ausentes_sao_apontados_por_nome(self):
        erros = validar("plano", {}, ENTRADA)
        self.assertEqual({c for c, r in regras(erros) if r == "campo_ausente"}, set(FIXTURE["plano_esperado"]))

    def test_contrato_desconhecido(self):
        with self.assertRaises(ValueError):
            validar("juiz", {}, ENTRADA)


class TestDecodificacao(TestCase):
    """Verificações de sintaxe que pertencem ao parser, antes do contrato (cenário I11)."""

    def ok(self, texto):
        dados, erros = decodificar(texto)
        self.assertEqual(erros, [], texto)
        return dados

    def falha(self, texto, regra):
        dados, erros = decodificar(texto)
        self.assertIsNone(dados, texto)
        self.assertEqual([e["regra"] for e in erros], [regra], texto)

    def test_objeto_valido_com_espacos_ao_redor_e_unicode(self):
        self.assertEqual(self.ok('  \n{"adaptacoes": ["ação", "não"]}\n '), {"adaptacoes": ["ação", "não"]})

    def test_recusa_texto_fora_do_json(self):
        self.falha('Segue o JSON: {"a": 1}', "json_invalido")
        self.falha('{"a": 1} Espero ter ajudado.', "json_invalido")
        self.falha('```json\n{"a": 1}\n```', "json_invalido")

    def test_recusa_resposta_vazia_ou_truncada(self):
        self.falha("", "json_invalido")
        self.falha('{"etapas": [{"etapa": "A", "minutos": 1', "json_invalido")

    def test_recusa_chaves_duplicadas_inclusive_aninhadas(self):
        self.falha('{"a": 1, "a": 2}', "chave_duplicada")
        self.falha('{"etapas": [{"minutos": 1, "minutos": 2}]}', "chave_duplicada")

    def test_recusa_nan_e_infinitos(self):
        for texto in ('{"a": NaN}', '{"a": Infinity}', '{"a": -Infinity}', '{"a": 1e999}'):
            with self.subTest(texto=texto):
                self.falha(texto, "constante_nao_finita")

    def test_recusa_raiz_que_nao_e_objeto(self):
        for texto in ("[]", '"texto"', "5", "null"):
            with self.subTest(texto=texto):
                self.falha(texto, "raiz_nao_objeto")

    def test_recusa_entrada_que_nao_e_texto(self):
        self.falha_tipo(None)
        self.falha_tipo(b'{"a": 1}')

    def falha_tipo(self, valor):
        dados, erros = decodificar(valor)
        self.assertIsNone(dados)
        self.assertEqual([e["regra"] for e in erros], ["tipo_invalido"])

    def test_numero_inteiro_continua_inteiro(self):
        dados = self.ok('{"minutos": 5, "decimal": 5.5}')
        self.assertIs(type(dados["minutos"]), int)
        self.assertIs(type(dados["decimal"]), float)
