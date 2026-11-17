"""Testes offline do contrato, da rubrica e da política de decisão da IA Juiz (parecer-juiz-1.0).

Os pareceres de tests/dados/juiz_v1 são SINTÉTICOS (escritos à mão). Estes testes verificam
o contrato e a lógica de decisão; não medem se um LLM real avalia bem. Isso depende de
medir o Juiz contra defeitos injetados e contra avaliadores humanos.
"""
from copy import deepcopy
import io
import json
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch
from urllib.error import HTTPError

from contratos import juiz_v1 as j
from contratos import rubrica_juiz as rubrica
from contratos.plano_v2 import DEPENDENCIAS, ETAPAS
from erros import ErroContrato, ErroGeracao
from gemini import MODELO_PADRAO
from geracao_v2 import AgenteGeminiCompleto, GeradorDePlanoCompleto
from juiz import avaliar_plano, criar_agente_juiz, esquema_api, VERSAO_ESQUEMA_API
from test_gemini import CHAVE, Transporte, envelope

DADOS = Path(__file__).resolve().parent / "dados"
PARECERES = json.loads((DADOS / "juiz_v1" / "pareceres.json").read_text(encoding="utf-8"))
V2 = json.loads((DADOS / "plano_v2" / "fixture_ordenacao.json").read_text(encoding="utf-8"))
PLANO, ENTRADA = V2["plano_esperado"], V2["entrada"]
SPEC_R2 = ("Aderência curricular", "Alinhamento dos objetivos", "Coerência metodológica",
           "Viabilidade", "Avaliação da aprendizagem", "Inclusão")


def parecer(nome):
    return deepcopy(PARECERES[nome])


def regras(erros):
    return {(e["caminho"], e["regra"]) for e in erros}


class AgenteFalso:
    """Devolve saídas roteirizadas; registra o que recebeu. Sem rede."""
    def __init__(self, *saidas):
        self.saidas, self.chamadas = list(saidas), []

    def executar(self, nome, entrada, estado, revisao, *, registro, reparo=None):
        self.chamadas.append({"nome": nome, "estado": deepcopy(estado), "reparo": deepcopy(reparo)})
        registro.update(provedor="falso")
        proximo = self.saidas.pop(0)
        if isinstance(proximo, BaseException):
            raise proximo
        return deepcopy(proximo)


class TestRubrica(TestCase):
    def test_seis_criterios_da_spec_com_rotulos_corretos(self):
        self.assertEqual(tuple(rubrica.RUBRICA[c]["rotulo"] for c in rubrica.CRITERIOS), SPEC_R2)
        self.assertEqual(set(rubrica.RUBRICA), set(rubrica.CRITERIOS))

    def test_cada_criterio_tem_pergunta_indicadores_e_quatro_ancoras(self):
        for c, r in rubrica.RUBRICA.items():
            with self.subTest(criterio=c):
                self.assertTrue(r["pergunta"].endswith("?"))
                self.assertGreaterEqual(len(r["indicadores"]), 3)
                self.assertEqual(set(r["ancoras"]), {0, 1, 2, 3})
                self.assertTrue(set(r["secoes"]) <= set(PLANO), "seção inexistente no PlanoDeAula 2.0")

    def test_instrucao_contem_criterios_componentes_gravidades_e_trata_plano_como_dado(self):
        texto = j.instrucoes()
        for c in rubrica.CRITERIOS:
            self.assertIn(c, texto)
        for nome in ETAPAS:
            self.assertIn(nome, texto)
        for gravidade in rubrica.GRAVIDADES:
            self.assertIn(gravidade, texto)
        self.assertIn("DADOS", texto)
        self.assertIn("NÃO reescreve", texto)

    def test_prompt_inclui_os_indicadores_operacionais_da_rubrica(self):
        texto = j.instrucoes()
        for criterio in rubrica.RUBRICA.values():
            for indicador in criterio["indicadores"]:
                self.assertIn(indicador, texto)

    def test_documentacao_cita_todos_os_criterios_e_versoes(self):
        doc = (DADOS.parents[2] / "docs" / "Rubrica_e_Contrato_IA_Juiz.md").read_text(encoding="utf-8")
        for c in rubrica.CRITERIOS:
            self.assertIn(f"`{c}`", doc)
            self.assertIn(rubrica.RUBRICA[c]["rotulo"], doc)
        for versao in (rubrica.VERSAO, j.VERSAO, j.POLITICA_PRELIMINAR["nome"]):
            self.assertIn(versao, doc)

    def test_responsaveis_apontam_somente_para_componentes_reais(self):
        self.assertTrue(set(rubrica.RESPONSAVEL_POR_SECAO.values()) <= set(ETAPAS))
        self.assertEqual(set(rubrica.RESPONSAVEL_POR_SECAO.values()), set(ETAPAS))


class TestEsquema(TestCase):
    def test_esquema_autocontido_e_fechado(self):
        texto = json.dumps(j.esquema())
        self.assertNotIn("$ref", texto)
        self.assertNotIn("$defs", texto)
        self.assertFalse(j.esquema()["additionalProperties"])

    def test_enums_do_esquema_coincidem_com_o_codigo(self):
        e = j.esquema()["properties"]
        self.assertEqual(tuple(e["avaliacoes"]["items"]["properties"]["criterio"]["enum"]), rubrica.CRITERIOS)
        props = e["falhas"]["items"]["properties"]
        self.assertEqual(tuple(props["componente"]["enum"]), ETAPAS)
        self.assertEqual(set(props["gravidade"]["enum"]), set(rubrica.GRAVIDADES))


class TestValidacao(TestCase):
    def test_pareceres_sinteticos_sao_validos(self):
        for nome in ("favoravel", "correcao", "critico"):
            with self.subTest(parecer=nome):
                self.assertEqual(j.diagnosticar(parecer(nome)), [])

    def test_estrutura_invalida(self):
        def muda(f):
            p = parecer("favoravel")
            f(p)
            return p
        casos = {
            "campo_extra": (muda(lambda p: p.update(decisao="aprovado")), ("/decisao", "campo_extra")),
            "resumo_ausente": (muda(lambda p: p.pop("resumo")), ("/resumo", "campo_ausente")),
            "nota_texto": (muda(lambda p: p["avaliacoes"][0].update(nota="3")), ("/avaliacoes/0/nota", "tipo_invalido")),
            "nota_booleana": (muda(lambda p: p["avaliacoes"][0].update(nota=True)), ("/avaliacoes/0/nota", "tipo_invalido")),
            "nota_decimal": (muda(lambda p: p["avaliacoes"][0].update(nota=2.0)), ("/avaliacoes/0/nota", "tipo_invalido")),
            "nota_acima": (muda(lambda p: p["avaliacoes"][0].update(nota=4)), ("/avaliacoes/0/nota", "limite_invalido")),
            "nota_negativa": (muda(lambda p: p["avaliacoes"][0].update(nota=-1)), ("/avaliacoes/0/nota", "limite_invalido")),
            "cinco_avaliacoes": (muda(lambda p: p["avaliacoes"].pop()), ("/avaliacoes", "quantidade_invalida")),
            "justificativa_vazia": (muda(lambda p: p["avaliacoes"][1].update(justificativa="  ")), ("/avaliacoes/1/justificativa", "texto_vazio")),
            "criterio_inexistente": (muda(lambda p: p["avaliacoes"][0].update(criterio="criatividade")), ("/avaliacoes/0/criterio", "valor_invalido")),
            "componente_inexistente": (muda(lambda p: p["falhas"][0].update(componente="integrador")), ("/falhas/0/componente", "valor_invalido")),
            "gravidade_inexistente": (muda(lambda p: p["falhas"][0].update(gravidade="grave")), ("/falhas/0/gravidade", "valor_invalido")),
            "id_de_falha_invalido": (muda(lambda p: p["falhas"][0].update(id="X1")), ("/falhas/0/id", "formato_invalido")),
            "treze_falhas": (muda(lambda p: p.update(falhas=[dict(p["falhas"][0], id=f"F{i}") for i in range(1, 14)])), ("/falhas", "quantidade_invalida")),
        }
        for nome, (dados, esperado) in casos.items():
            with self.subTest(caso=nome):
                self.assertIn(esperado, regras(j.diagnosticar(dados)))

    def test_raiz_que_nao_e_objeto(self):
        for bruto in ([], "texto", None, 5):
            with self.subTest(bruto=bruto):
                self.assertEqual(regras(j.diagnosticar(bruto)), {("$", "tipo_invalido")})

    def test_criterio_repetido_ou_ausente(self):
        p = parecer("favoravel")
        p["avaliacoes"][1]["criterio"] = p["avaliacoes"][0]["criterio"]
        self.assertEqual(regras(j.diagnosticar(p)), {("/avaliacoes", "criterio_repetido"), ("/avaliacoes", "criterio_ausente")})

    def test_id_de_falha_duplicado(self):
        p = parecer("correcao")
        p["falhas"][1]["id"] = "F1"
        self.assertEqual(regras(j.diagnosticar(p)), {("/falhas/0/id", "id_duplicado"), ("/falhas/1/id", "id_duplicado")})


class TestInvariantesNotaFalha(TestCase):
    """O Juiz não pode se contradizer: a nota e as falhas do mesmo critério precisam concordar."""

    def i(self, p, regra):
        self.assertIn(regra, {r for _, r in regras(j.diagnosticar(p))})

    def test_nota_3_com_falha_maior(self):
        p = parecer("favoravel")
        p["falhas"][0].update(gravidade="maior")
        p["avaliacoes"][5]["nota"] = 3
        self.i(p, "nota_alta_com_falha_grave")

    def test_nota_baixa_so_com_falha_menor(self):
        p = parecer("correcao")
        p["falhas"][0]["gravidade"] = "menor"
        self.i(p, "nota_baixa_sem_falha_grave")

    def test_nota_2_sem_nenhuma_falha(self):
        p = parecer("favoravel")
        p["falhas"] = []
        self.i(p, "nota_sem_falha")

    def test_falha_critica_com_nota_2(self):
        p = parecer("critico")
        p["avaliacoes"][0]["nota"] = 2
        self.i(p, "critica_exige_nota_baixa")

    def test_nota_3_com_falha_menor_e_permitida(self):
        p = parecer("favoravel")
        p["avaliacoes"][0]["nota"] = 3
        p["falhas"].append(dict(p["falhas"][0], id="F2", criterio=rubrica.CRITERIOS[0], gravidade="menor"))
        self.assertEqual(j.diagnosticar(p), [])

    def test_invariantes_so_sao_avaliadas_com_estrutura_valida(self):
        p = parecer("correcao")
        p["falhas"][0]["gravidade"] = "grave"
        self.assertEqual(regras(j.diagnosticar(p)), {("/falhas/0/gravidade", "valor_invalido")})

    def test_validar_levanta_erro_de_contrato_com_diagnosticos(self):
        p = parecer("favoravel")
        p["resumo"] = ""
        with self.assertRaises(ErroContrato) as ctx:
            j.validar(p)
        self.assertTrue(ctx.exception.diagnosticos)


class TestDecisao(TestCase):
    def test_parecer_favoravel_aguarda_decisao_humana_e_nunca_aprova(self):
        d = j.decidir(parecer("favoravel"))
        self.assertEqual(d["proximo_estado"], "aguardando_decisao")
        self.assertEqual(d["componentes_a_corrigir"], [])
        self.assertNotIn("aprovado", d["proximo_estado"])

    def test_falha_maior_leva_a_correcao_e_aponta_so_o_componente_responsavel(self):
        d = j.decidir(parecer("correcao"))
        self.assertEqual(d["proximo_estado"], "em_correcao")
        self.assertEqual(d["componentes_a_corrigir"], ["sequencia"])  # a falha menor em metodologia não conta
        self.assertEqual(d["componentes_invalidados"], ["sequencia", "avaliacao_final", "adaptacao"])
        self.assertEqual(d["falhas_que_motivam"], ["F1"])

    def test_caso_critico_vai_direto_a_revisao_necessaria(self):
        d = j.decidir(parecer("critico"))
        self.assertEqual(d["proximo_estado"], "revisao_necessaria")
        self.assertIn("F1", d["motivos"][0])

    def test_caso_critico_pode_ser_tratado_como_corrigivel_se_a_politica_mudar(self):
        d = j.decidir(parecer("critico"), politica={"critica_exige_revisao_humana": False})
        self.assertEqual(d["proximo_estado"], "em_correcao")
        self.assertEqual(d["componentes_a_corrigir"], ["objetivos"])
        self.assertEqual(d["componentes_invalidados"], list(ETAPAS))

    def test_limite_de_ciclos_esgotado_leva_a_revisao_necessaria(self):
        self.assertEqual(j.decidir(parecer("correcao"), ciclos_usados=1)["proximo_estado"], "em_correcao")
        self.assertEqual(j.decidir(parecer("correcao"), ciclos_usados=2)["proximo_estado"], "revisao_necessaria")
        self.assertEqual(j.decidir(parecer("correcao"), ciclos_usados=1, politica={"limite_ciclos": 1})["proximo_estado"], "revisao_necessaria")

    def test_limite_de_ciclos_nao_afeta_parecer_favoravel(self):
        self.assertEqual(j.decidir(parecer("favoravel"), ciclos_usados=5)["proximo_estado"], "aguardando_decisao")

    def test_politica_mais_rigorosa_exige_corrigir_criterio_nota_2(self):
        d = j.decidir(parecer("favoravel"), politica={"nota_minima": 3})
        self.assertEqual(d["proximo_estado"], "em_correcao")
        self.assertEqual(d["componentes_a_corrigir"], ["adaptacao"])

    def test_componentes_saem_na_ordem_do_pipeline(self):
        p = parecer("correcao")
        p["falhas"] = [dict(p["falhas"][0], id="F1", componente="adaptacao"),
                       dict(p["falhas"][0], id="F2", componente="objetivos")]
        self.assertEqual(j.decidir(p)["componentes_a_corrigir"], ["objetivos", "adaptacao"])

    def test_decidir_valida_o_parecer_e_nao_altera_a_entrada(self):
        p = parecer("correcao")
        antes = deepcopy(p)
        j.decidir(p)
        self.assertEqual(p, antes)
        p["falhas"][0]["gravidade"] = "menor"
        with self.assertRaises(ErroContrato):
            j.decidir(p)

    def test_politica_e_registrada_e_marcada_como_preliminar(self):
        self.assertEqual(j.decidir(parecer("favoravel"))["politica"], j.POLITICA_PRELIMINAR["nome"])
        self.assertIn("preliminar", j.POLITICA_PRELIMINAR["status"])


class TestInvalidacao(TestCase):
    def test_fecho_pelo_grafo_de_dependencias(self):
        esperado = {
            ("objetivos",): list(ETAPAS),
            ("avaliacao_preliminar",): list(ETAPAS[1:]),
            ("metodologia",): ["metodologia", "sequencia", "avaliacao_final", "adaptacao"],
            ("sequencia",): ["sequencia", "avaliacao_final", "adaptacao"],
            ("avaliacao_final",): ["avaliacao_final", "adaptacao"],
            ("adaptacao",): ["adaptacao"],
            ("adaptacao", "metodologia"): ["metodologia", "sequencia", "avaliacao_final", "adaptacao"],
            (): [],
        }
        for entrada, saida in esperado.items():
            with self.subTest(componentes=entrada):
                self.assertEqual(j.invalidados(entrada), saida)

    def test_so_invalida_quem_depende_do_corrigido(self):
        for nome in ETAPAS:
            for invalido in j.invalidados([nome]):
                self.assertTrue(invalido == nome or nome in DEPENDENCIAS[invalido] or
                                any(d in j.invalidados([nome]) for d in DEPENDENCIAS[invalido]))


class TestConfiguracaoJuiz(TestCase):
    def test_politicas_invalidas_sao_recusadas_antes_de_chamar_o_agente(self):
        casos = [[], False, "padrao", {"nota_minma": 3}, {"nome": " "}, {"status": None},
                 {"nota_minima": True}, {"nota_minima": 4}, {"nota_minima": -1},
                 {"nota_minima": 2.0}, {"limite_ciclos": -1}, {"limite_ciclos": True},
                 {"limite_ciclos": "2"}, {"critica_exige_revisao_humana": "false"},
                 {"gravidades_que_exigem_correcao": "maior"},
                 {"gravidades_que_exigem_correcao": ["grave"]},
                 {"gravidades_que_exigem_correcao": ["maior", "maior"]},
                 {"gravidades_que_exigem_correcao": [{}]}]
        for politica in casos:
            with self.subTest(politica=politica):
                agente = AgenteFalso(parecer("favoravel"))
                with self.assertRaises(ValueError):
                    avaliar_plano(PLANO, ENTRADA, agente, modelo_gerador="gemini-a",
                                  modelo_juiz="gemini-b", politica=politica)
                self.assertEqual(agente.chamadas, [])
                with self.assertRaises(ValueError):
                    j.decidir(parecer("favoravel"), politica=politica)

    def test_contadores_invalidos_nao_consumem_chamadas(self):
        for campo in ("ciclos_usados", "revisao"):
            for valor in (-1, True, 1.5, "1", None):
                with self.subTest(campo=campo, valor=valor):
                    agente = AgenteFalso(parecer("favoravel"))
                    with self.assertRaises(ValueError):
                        avaliar_plano(PLANO, ENTRADA, agente, modelo_gerador="gemini-a",
                                      modelo_juiz="gemini-b", **{campo: valor})
                    self.assertEqual(agente.chamadas, [])
                    if campo == "ciclos_usados":
                        with self.assertRaises(ValueError):
                            j.decidir(parecer("favoravel"), ciclos_usados=valor)

    def test_limite_zero_encaminha_falha_corrigivel_para_revisao(self):
        d = j.decidir(parecer("correcao"), politica={"limite_ciclos": 0})
        self.assertEqual(d["proximo_estado"], "revisao_necessaria")

    def test_politica_do_resultado_e_a_mesma_usada_no_inicio(self):
        politica = {"nota_minima": 3, "gravidades_que_exigem_correcao": ["maior", "critica"]}
        class Mutante(AgenteFalso):
            def executar(self, *args, **kwargs):
                politica["nota_minima"] = 0
                politica["gravidades_que_exigem_correcao"].clear()
                return super().executar(*args, **kwargs)
        r = avaliar_plano(PLANO, ENTRADA, Mutante(parecer("favoravel")),
                          modelo_gerador="gemini-a", modelo_juiz="gemini-b", politica=politica)
        self.assertEqual(r["decisao"]["proximo_estado"], "em_correcao")
        self.assertEqual(r["politica"]["nota_minima"], 3)
        self.assertEqual(r["politica"]["gravidades_que_exigem_correcao"], ("maior", "critica"))
        self.assertEqual(r["rastreio"][0]["politica"], r["politica"])


class TestAvaliarPlano(TestCase):
    def avaliar(self, agente, **kw):
        base = dict(modelo_gerador="gemini-a", modelo_juiz="gemini-b")
        return avaliar_plano(PLANO, ENTRADA, agente, **{**base, **kw})

    def test_fluxo_feliz(self):
        agente = AgenteFalso(parecer("favoravel"))
        r = self.avaliar(agente)
        self.assertEqual(r["contrato"], "parecer-juiz-1.0")
        self.assertEqual(r["decisao"]["proximo_estado"], "aguardando_decisao")
        self.assertEqual([t["estado"] for t in r["rastreio"]], ["validado"])
        self.assertEqual(len(agente.chamadas), 1)
        self.assertEqual(agente.chamadas[0]["estado"], {"plano": PLANO})  # o Juiz recebe só o plano integrado
        self.assertTrue(r["modelo_distinto_do_gerador"])
        self.assertIsNone(r["versao_esquema_api"])  # o agente falso não declara uma projeção Gemini

    def test_rejeita_plano_invalido_ou_incompativel_antes_da_avaliacao(self):
        casos = [(None, deepcopy(ENTRADA)), ({}, deepcopy(ENTRADA)), (deepcopy(PLANO), {})]
        for campo in ("recursos", "objetivo_geral"):
            plano = deepcopy(PLANO)
            plano[campo] = "ADULTERADO" if campo == "recursos" else " "
            casos.append((plano, deepcopy(ENTRADA)))
        plano = deepcopy(PLANO)
        plano["desenvolvimento"][0]["minutos"] += 1
        casos.append((plano, deepcopy(ENTRADA)))
        entrada = deepcopy(ENTRADA)
        entrada["habilidade"]["codigo"] = "OUTRA_HABILIDADE"
        casos.append((deepcopy(PLANO), entrada))
        legado = json.loads((DADOS / "poc04a" / "fixture_ordenacao.json").read_text(encoding="utf-8"))
        casos.append((legado["plano_esperado"], legado["entrada"]))
        for i, (plano, entrada) in enumerate(casos):
            with self.subTest(caso=i):
                agente = AgenteFalso(parecer("favoravel"))
                with self.assertRaises(ErroContrato):
                    avaliar_plano(plano, entrada, agente, modelo_gerador="gemini-a", modelo_juiz="gemini-b")
                self.assertEqual(agente.chamadas, [])

    def test_rastreio_preserva_plano_revisao_e_politica_em_falha(self):
        with self.assertRaises(ErroGeracao) as ctx:
            self.avaliar(AgenteFalso(ErroGeracao("Indisponível", tipo="http")), revisao=3, ciclos_usados=1)
        reg = ctx.exception.rastreio[0]
        self.assertEqual(reg["entrada"]["saidas_anteriores"], {"plano": PLANO})
        self.assertEqual(reg["entrada"]["contexto"], ENTRADA["contexto"])
        self.assertEqual(reg["revisao"], 3)
        self.assertEqual(reg["ciclos_usados"], 1)
        self.assertEqual(reg["politica"], j.POLITICA_PRELIMINAR)
        self.assertEqual(reg["versao_rubrica"], rubrica.VERSAO)

    def test_sinaliza_quando_juiz_e_gerador_sao_o_mesmo_modelo(self):
        r = self.avaliar(AgenteFalso(parecer("favoravel")), modelo_juiz="gemini-a")
        self.assertFalse(r["modelo_distinto_do_gerador"])

    def test_nao_altera_o_plano_avaliado(self):
        antes = deepcopy(PLANO)
        self.avaliar(AgenteFalso(parecer("critico")))
        self.assertEqual(PLANO, antes)

    def test_agente_que_tenta_alterar_o_plano_recebido_nao_afeta_o_original(self):
        class Mutante(AgenteFalso):
            def executar(self, nome, entrada, estado, revisao, *, registro, reparo=None):
                estado["plano"]["identificacao"]["tema"] = "ADULTERADO"
                entrada["contexto"]["tema"] = "ADULTERADO"
                return super().executar(nome, entrada, estado, revisao, registro=registro, reparo=reparo)
        antes_plano, antes_entrada = deepcopy(PLANO), deepcopy(ENTRADA)
        self.avaliar(Mutante(parecer("favoravel")))
        self.assertEqual(PLANO, antes_plano)
        self.assertEqual(ENTRADA, antes_entrada)

    def test_um_reparo_tecnico_reaproveita_a_mesma_entrada(self):
        invalido = parecer("favoravel")
        invalido["decisao"] = "aprovado"
        agente = AgenteFalso(invalido, parecer("favoravel"))
        r = self.avaliar(agente)
        self.assertEqual([t["estado"] for t in r["rastreio"]], ["rejeitado", "validado"])
        self.assertIn(("/decisao", "campo_extra"), {(d["caminho"], d["regra"]) for d in r["rastreio"][0]["diagnosticos"]})
        self.assertIsNone(agente.chamadas[0]["reparo"])
        self.assertTrue(agente.chamadas[1]["reparo"]["diagnosticos"])
        self.assertEqual(agente.chamadas[0]["estado"], agente.chamadas[1]["estado"])

    def test_reparos_esgotados_levantam_erro_com_rastreio(self):
        invalido = parecer("favoravel")
        invalido.pop("resumo")
        with self.assertRaises(ErroContrato) as ctx:
            self.avaliar(AgenteFalso(invalido, invalido))
        self.assertEqual([t["estado"] for t in ctx.exception.rastreio], ["rejeitado", "rejeitado"])

    def test_sem_reparos_faz_uma_unica_tentativa(self):
        invalido = parecer("favoravel")
        invalido.pop("resumo")
        agente = AgenteFalso(invalido, parecer("favoravel"))
        with self.assertRaises(ErroContrato):
            self.avaliar(agente, reparos=0)
        self.assertEqual(len(agente.chamadas), 1)

    def test_erro_de_provedor_nao_e_repetido_e_preserva_rastreio(self):
        agente = AgenteFalso(ErroGeracao("Gemini HTTP 429", tipo="http"), parecer("favoravel"))
        with self.assertRaises(ErroGeracao) as ctx:
            self.avaliar(agente)
        self.assertEqual(len(agente.chamadas), 1)
        self.assertEqual(ctx.exception.rastreio[0]["estado"], "falha")

    def test_ciclos_usados_chegam_a_decisao(self):
        r = self.avaliar(AgenteFalso(parecer("correcao")), ciclos_usados=2)
        self.assertEqual(r["decisao"]["proximo_estado"], "revisao_necessaria")

    def test_reparos_invalidos(self):
        for valor in (2, -1, True, "1"):
            with self.subTest(valor=valor), self.assertRaises(ValueError):
                self.avaliar(AgenteFalso(), reparos=valor)


class TestJuizComTransporteGeminiSimulado(TestCase):
    """Usa o AgenteGemini real com transporte falso: confere o que SERIA enviado à API."""

    def test_requisicao_leva_esquema_e_instrucao_do_juiz_e_o_plano_como_dado(self):
        transporte = Transporte([envelope(parecer("favoravel"))])
        agente = criar_agente_juiz(chave=CHAVE, transporte=transporte)
        r = avaliar_plano(PLANO, ENTRADA, agente, modelo_gerador=MODELO_PADRAO, modelo_juiz=MODELO_PADRAO)
        self.assertEqual(r["decisao"]["proximo_estado"], "aguardando_decisao")
        self.assertFalse(r["modelo_distinto_do_gerador"])
        pedido = transporte.pedidos[0]
        corpo = json.loads(pedido.data)
        self.assertEqual(corpo["generationConfig"]["responseFormat"]["text"]["schema"], esquema_api())
        self.assertEqual(r["versao_esquema_api"], VERSAO_ESQUEMA_API)
        self.assertEqual(agente.versao_esquema_api, VERSAO_ESQUEMA_API)
        self.assertIn("AVALIADOR independente", corpo["systemInstruction"]["parts"][0]["text"])
        dados = json.loads(corpo["contents"][0]["parts"][0]["text"])
        self.assertEqual(dados["saidas_anteriores"], {"plano": PLANO})
        self.assertNotIn(CHAVE, pedido.full_url + pedido.data.decode())
        self.assertEqual(r["rastreio"][0]["versao_contrato"], "parecer-juiz-1.0")
        self.assertEqual(r["rastreio"][0]["versao_prompt"], "juiz-v1.1")
        self.assertEqual(r["rastreio"][0]["versao_esquema_api"], VERSAO_ESQUEMA_API)
        self.assertNotIn(CHAVE, json.dumps(r))

    def test_esquema_projetado_preserva_estrutura_e_limites_seguem_locais(self):
        original = j.esquema()
        api = esquema_api()
        self.assertEqual(j.esquema(), original)
        def comparar(local, remoto):
            self.assertEqual(local["type"], remoto["type"])
            for limite in ("minItems", "maxItems", "minimum", "maximum", "minLength", "maxLength",
                           "pattern", "enum", "uniqueItems"):
                self.assertNotIn(limite, remoto)
                if limite in local:
                    self.assertTrue(remoto.get("description"))
            if local["type"] == "object":
                self.assertEqual(local["required"], remoto["required"])
                self.assertFalse(remoto["additionalProperties"])
                self.assertEqual(set(local["properties"]), set(remoto["properties"]))
                for campo, regra in local["properties"].items():
                    comparar(regra, remoto["properties"][campo])
            elif local["type"] == "array":
                comparar(local["items"], remoto["items"])
        comparar(original, api)
        casos = (("avaliacoes", "nota", 4, "limite_invalido"),
                 ("falhas", "gravidade", "grave", "valor_invalido"),
                 ("falhas", "id", "X1", "formato_invalido"),
                 ("avaliacoes", "criterio", "criatividade", "valor_invalido"))
        for lista, campo, valor, regra in casos:
            with self.subTest(campo=campo):
                invalido = parecer("favoravel")
                invalido[lista][0][campo] = valor
                transporte = Transporte([envelope(invalido), envelope(parecer("favoravel"))])
                r = avaliar_plano(PLANO, ENTRADA, criar_agente_juiz(chave=CHAVE, transporte=transporte),
                                  modelo_gerador=MODELO_PADRAO, modelo_juiz=MODELO_PADRAO)
                self.assertEqual([t["estado"] for t in r["rastreio"]], ["rejeitado", "validado"])
                self.assertIn(regra, [d["regra"] for d in r["rastreio"][0]["diagnosticos"]])

    def test_valores_permitidos_viram_orientacao_textual(self):
        props = esquema_api()["properties"]["falhas"]["items"]["properties"]
        self.assertEqual(props["gravidade"]["description"], "Valores permitidos: critica, maior, menor.")
        for componente in ETAPAS:
            self.assertIn(componente, props["componente"]["description"])
        for criterio in rubrica.CRITERIOS:
            self.assertIn(criterio, props["criterio"]["description"])

    def test_modelo_declarado_diferente_do_agente_e_recusado_sem_http(self):
        transporte = Transporte([])
        agente = criar_agente_juiz(chave=CHAVE, transporte=transporte)
        with self.assertRaises(ValueError):
            avaliar_plano(PLANO, ENTRADA, agente, modelo_gerador=MODELO_PADRAO, modelo_juiz="gemini-outro")
        self.assertEqual(transporte.pedidos, [])

    def test_503_repetido_so_quando_configurado_e_preserva_auditoria(self):
        for repeticoes in (0, 1, 2):
            with self.subTest(repeticoes=repeticoes), patch("gemini.time.sleep") as espera:
                falha = HTTPError("https://exemplo.invalid", 503, "Indisponível", {}, io.BytesIO(b'{}'))
                transporte = Transporte([falha, envelope(parecer("favoravel"))])
                agente = criar_agente_juiz(chave=CHAVE, transporte=transporte, repeticoes_503=repeticoes)
                if repeticoes:
                    r = avaliar_plano(PLANO, ENTRADA, agente, modelo_gerador=MODELO_PADRAO, modelo_juiz=MODELO_PADRAO)
                    self.assertEqual(len(r["rastreio"]), 1)
                    self.assertEqual(r["rastreio"][0]["chamadas_http"], 2)
                    self.assertEqual(len(r["rastreio"][0]["falhas_http_transitorias"]), 1)
                    self.assertEqual(espera.call_count, 1)
                else:
                    with self.assertRaises(ErroGeracao) as ctx:
                        avaliar_plano(PLANO, ENTRADA, agente, modelo_gerador=MODELO_PADRAO, modelo_juiz=MODELO_PADRAO)
                    self.assertEqual(ctx.exception.rastreio[0]["chamadas_http"], 1)
                    self.assertEqual(len(transporte.pedidos), 1)
                    espera.assert_not_called()

    def test_plano_do_pipeline_atual_e_avaliado_sem_refazer_especialistas(self):
        transporte_gerador = Transporte([envelope(V2["saidas"][nome]) for nome in ETAPAS])
        gerador = GeradorDePlanoCompleto("ia", agente=AgenteGeminiCompleto(chave=CHAVE, transporte=transporte_gerador))
        resultado = gerador.gerar(deepcopy(ENTRADA), 2)
        original = deepcopy(resultado)
        for caso, estado in (("favoravel", "aguardando_decisao"), ("correcao", "em_correcao"),
                             ("critico", "revisao_necessaria")):
            with self.subTest(caso=caso):
                transporte_juiz = Transporte([envelope(parecer(caso))])
                r = avaliar_plano(resultado["plano"], ENTRADA,
                                  criar_agente_juiz(chave=CHAVE, transporte=transporte_juiz),
                                  modelo_gerador=resultado["modelo"], modelo_juiz=MODELO_PADRAO,
                                  revisao=resultado["revisao"])
                self.assertEqual(r["decisao"]["proximo_estado"], estado)
                self.assertEqual(r["revisao"], 2)
                self.assertEqual(len(transporte_juiz.pedidos), 1)
        self.assertEqual(len(transporte_gerador.pedidos), 6)
        self.assertEqual(resultado, original)
