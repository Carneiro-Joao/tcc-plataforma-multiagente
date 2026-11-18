"""Testes do analisador de séries do Juiz. Offline.

Os resultado.json usados aqui são produzidos pelo PRÓPRIO executar_ensaio, com agentes falsos que devolvem
pareceres sintéticos; assim o analisador é testado contra o formato real, e não contra um formato suposto.
Os pareceres são sintéticos: provam a lógica de classificação, não o comportamento de um LLM.
"""
from copy import deepcopy
import json
from pathlib import Path
import shutil
import tempfile
from unittest import TestCase

import analisar_serie as a
from casos_juiz import carregar_caso, hash_json
from contratos import juiz_v1 as contrato
from contratos.plano_v2 import ETAPAS
from ensaio_juiz import executar_ensaio
from erros import ErroGeracao
from groq_juiz import MODELO_PADRAO

RAIZ = Path(__file__).resolve().parents[2]
CASO = {n: f"experimentos/juiz/casos/{nome}.json" for n, nome in {
    "V03": "ordenacao_variante_projetor_nao_confirmado_03", "V04": "ordenacao_variante_adaptacao_generica_04",
    "V05": "ordenacao_variante_conteudo_periferico_05", "V06": "ordenacao_variante_perturbacao_neutra_06",
    "BASE": "ordenacao_real_994c4cd5", "V01": "ordenacao_variante_evi2_desalinhada_01"}.items()}
NOTA_POR_GRAVIDADE = {"critica": 0, "maior": 1, "menor": 2}


def regra(n):
    return json.loads((RAIZ / "experimentos/juiz/pontuacao" / f"{n}.json").read_text(encoding="utf-8"))


def parecer(*falhas):
    """falhas: (criterio, componente, gravidade, texto). A nota de cada critério sai das falhas (invariantes do contrato)."""
    lista = [dict(id=f"F{i}", criterio=c, componente=comp, gravidade=g, descricao=t,
                  correcao_sugerida="Revisar o trecho apontado, sem reescrever o plano.")
             for i, (c, comp, g, t) in enumerate(falhas, 1)]
    avaliacoes = []
    for c in contrato.CRITERIOS:
        gravs = [f["gravidade"] for f in lista if f["criterio"] == c]
        nota = min((NOTA_POR_GRAVIDADE[g] for g in gravs), default=3)
        texto = (f"Critério {c}: {len(gravs)} ressalva(s) registrada(s) em OBJ1 e ET2." if gravs
                 else f"Critério {c} atendido: OBJ1, ET2 e EVI1 sustentam a avaliação.")
        avaliacoes.append(dict(criterio=c, nota=nota, justificativa=texto))
    return dict(avaliacoes=avaliacoes, falhas=lista, resumo="Resumo sintético do parecer.")


class Agente:
    modelo = MODELO_PADRAO
    versao_esquema_api = "teste"

    def __init__(self, saida):
        self.saida = saida

    def executar(self, nome, entrada, estado, revisao, *, registro, reparo=None):
        registro["usage"] = {"prompt_tokens": 5000, "completion_tokens": 2000, "total_tokens": 7000}
        if isinstance(self.saida, BaseException):
            raise self.saida
        return deepcopy(self.saida)


class Base(TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.pasta = self.tmp / "ensaios"
        self.pasta.mkdir()

    def rodar(self, chave_caso, saida, somente_validar=False):
        r, _ = executar_ensaio(RAIZ / CASO[chave_caso], self.pasta, somente_validar=somente_validar,
                               fabrica=lambda **kw: Agente(saida))
        return r

    def analisar(self, n, baseline=None):
        return a.analisar(self.pasta, regra(n), baseline)


V03_PLENA = ("viabilidade", "sequencia", "maior", "ET1 exige projeção e internet, não confirmados nos recursos.")


class TestPontuacaoDeteccao(Base):
    def nivel(self, n, *falhas):
        for antigo in self.pasta.iterdir():  # uma execução por vez: no mesmo segundo a ordem das pastas é aleatória
            shutil.rmtree(antigo)
        self.rodar(n, parecer(*falhas))
        return self.analisar(n)["linhas"][0]["pontuacao"]

    def test_plena(self):
        p = self.nivel("V03", V03_PLENA)
        self.assertEqual((p["nivel"], p["falhas_do_alvo"], p["gravidades"]), ("plena", ["F1"], ["maior"]))
        self.assertFalse(p["resultado_negativo_provavel"])

    def test_parcial_por_gravidade_menor(self):
        self.assertEqual(self.nivel("V03", ("viabilidade", "sequencia", "menor", "ET1 depende de projeção."))["nivel"], "parcial")

    def test_parcial_por_criterio_alternativo(self):
        p = self.nivel("V03", ("coerencia_metodologica", "sequencia", "maior", "ET1 contradiz a demonstração com cartões."))
        self.assertEqual(p["nivel"], "parcial")

    def test_gravidade_critica_vai_para_adjudicacao_humana(self):
        p = self.nivel("V03", ("viabilidade", "sequencia", "critica", "ET1 é inexequível."))
        self.assertEqual(p["nivel"], "a_adjudicar")
        self.assertIn("gravidade", p["motivo"])

    def test_ausente_quando_aponta_outra_coisa_e_da_nota_alta(self):
        p = self.nivel("V03", ("avaliacao_aprendizagem", "avaliacao_preliminar", "maior", "EVI1 é vaga."))
        self.assertEqual(p["nivel"], "ausente")
        self.assertEqual(p["falhas_fora_do_alvo"], ["F1"])
        self.assertTrue(p["resultado_negativo_provavel"])  # viabilidade ficou 3 e o máximo esperado era 2

    def test_criterio_e_componente_certos_mas_sem_citar_o_alvo_nao_contam(self):
        p = self.nivel("V03", ("viabilidade", "sequencia", "maior", "ET2 é longa demais para o tempo."))
        self.assertEqual((p["nivel"], p["falhas_do_alvo"], p["falhas_fora_do_alvo"]), ("ausente", [], ["F1"]))

    def test_v04_plena_e_parcial(self):
        self.assertEqual(self.nivel("V04", ("inclusao", "adaptacao", "maior", "ADP2 é genérica."))["nivel"], "plena")
        self.assertEqual(self.nivel("V04", ("inclusao", "adaptacao", "menor", "ADP2 é pouco específica."))["nivel"], "parcial")

    def test_v05_aceita_critica_ou_maior_e_trata_coerencia_como_parcial(self):
        for g in ("critica", "maior"):
            self.assertEqual(self.nivel("V05", ("aderencia_curricular", "sequencia", g, "ET2 trata de história dos computadores."))["nivel"], "plena")
        self.assertEqual(self.nivel("V05", ("coerencia_metodologica", "sequencia", "maior", "ET2 é incoerente."))["nivel"], "parcial")
        self.assertEqual(self.nivel("V05", ("aderencia_curricular", "sequencia", "menor", "ET2 é periférica."))["nivel"], "a_adjudicar")

    def test_nota_acima_do_esperado_e_registrada(self):
        p = self.nivel("V05", ("aderencia_curricular", "sequencia", "menor", "ET2 é periférica."))
        self.assertEqual(p["notas_acima_do_esperado"], {"aderencia_curricular": 2})


class TestControleV06(Base):
    def setUp(self):
        super().setUp()
        self.fa = ("avaliacao_aprendizagem", "avaliacao_preliminar", "maior", "EVI1 é vaga demais.")

    def test_sem_baseline_nao_inventa_comparacao(self):
        self.rodar("V06", parecer(self.fa))
        p = self.analisar("V06")["linhas"][0]["pontuacao"]
        self.assertIsNone(p["pares_novos_vs_baseline"])
        self.assertIsNone(p["decisao_igual_ao_baseline"])

    def test_estavel_quando_repete_o_conjunto_de_falhas_do_baseline(self):
        for _ in range(3):
            self.rodar("BASE", parecer(self.fa))
        self.rodar("V06", parecer(self.fa))
        analise = self.analisar("V06", self.pasta)
        p = analise["linhas"][0]["pontuacao"]
        self.assertEqual((analise["n_baseline"], p["pares_novos_vs_baseline"], p["critica_ou_maior_nova"], p["decisao_igual_ao_baseline"]),
                         (3, [], False, True))

    def test_instavel_quando_surge_falha_maior_nova_e_muda_a_decisao(self):
        self.rodar("BASE", parecer())  # baseline sem falhas -> aguardando_decisao
        self.rodar("V06", parecer(("aderencia_curricular", "objetivos", "maior", "O objetivo geral foi reformulado e ficou vago.")))
        p = self.analisar("V06", self.pasta)["linhas"][0]["pontuacao"]
        self.assertEqual(p["pares_novos_vs_baseline"], [("aderencia_curricular", "objetivos")])
        self.assertTrue(p["critica_ou_maior_nova"])
        self.assertFalse(p["decisao_igual_ao_baseline"])
        self.assertEqual(p["falhas_que_citam_a_reformulacao"], ["F1"])

    def test_baseline_vem_so_do_caso_original(self):
        self.rodar("V01", parecer(self.fa))  # outra variante não é baseline
        self.assertEqual(self.analisar("V06", self.pasta)["n_baseline"], 0)


class TestBaselineCompativel(Base):
    """Controle só vale se for do MESMO plano e da MESMA configuração (prompt, modelo, rubrica, parâmetros)."""
    fa = ("aderencia_curricular", "objetivos", "maior", "ET1 depende de projeção e internet.")

    def alterar(self, pasta_ensaio, **campos):
        arq = pasta_ensaio / "resultado.json"
        d = json.loads(arq.read_text(encoding="utf-8"))
        for k, v in campos.items():
            d[k] = v
        arq.write_text(json.dumps(d), encoding="utf-8")

    def base(self, n=1, **campos):
        antes = set(self.pasta.iterdir())
        for _ in range(n):
            self.rodar("BASE", parecer(self.fa))
        novos = sorted(set(self.pasta.iterdir()) - antes)
        if campos:
            for pasta_ensaio in novos:
                self.alterar(pasta_ensaio, **campos)
        return novos

    def test_tres_controles_de_prompts_diferentes_nao_viram_tres_baselines(self):
        for versao in ("juiz-v1.1", "juiz-v1.2"):
            self.base(1, versao_prompt=versao)
        self.rodar("V06", parecer(self.fa))
        atual = self.base(1)  # mesma configuração da série
        analise = self.analisar("V06", self.pasta)
        self.assertEqual(analise["n_baseline"], 1 + 0)  # só o controle da configuração atual
        self.assertEqual(sum(analise["baseline_descartados"].values()), 2)
        self.assertTrue(any("versao_prompt" in m for m in analise["baseline_descartados"]))
        self.assertTrue(atual)

    def test_controle_de_outro_plano_e_descartado(self):
        self.base(1, plano_sha256="0" * 64)
        self.base(1)
        self.rodar("V06", parecer(self.fa))
        analise = self.analisar("V06", self.pasta)
        self.assertEqual(analise["n_baseline"], 1)
        self.assertEqual(analise["baseline_descartados"], {"outro plano (hash diferente)": 1})

    def test_controle_de_outro_modelo_ou_parametros_e_descartado(self):
        self.base(1, modelo_juiz="outro/modelo")
        self.base(1, parametros={"temperature": 1})
        self.base(1, modo="somente_validar")
        self.rodar("V06", parecer(self.fa))
        analise = self.analisar("V06", self.pasta)
        self.assertEqual(analise["n_baseline"], 0)
        self.assertEqual(sum(analise["baseline_descartados"].values()), 3)

    def test_controle_de_outra_politica_de_decisao_e_descartado(self):
        self.base(1, politica={"nome": "politica-juiz-outra"})
        self.rodar("V06", parecer(self.fa))
        analise = self.analisar("V06", self.pasta)
        self.assertEqual(analise["n_baseline"], 0)
        self.assertTrue(any("politica" in m for m in analise["baseline_descartados"]))

    def test_relatorio_informa_descartes_e_configuracao(self):
        self.base(1, versao_prompt="juiz-v1.1")
        self.rodar("V06", parecer(self.fa))
        texto = a.renderizar_relatorio(self.analisar("V06", self.pasta))
        self.assertIn("Controle descartado", texto)
        self.assertIn("versao_prompt", texto)
        self.assertIn("Configuração da série", texto)
        self.assertIn("insuficiente", texto)

    def test_serie_com_configuracoes_misturadas_nao_seleciona_baseline(self):
        self.base(3)
        for _ in range(2):
            self.rodar("V06", parecer(self.fa))
        antigos = sorted(p for p in self.pasta.iterdir() if "variante" in (self.lerorigem(p).get("tipo") or ""))
        self.alterar(antigos[0], versao_prompt="juiz-v1.1")
        analise = self.analisar("V06", self.pasta)
        self.assertEqual(analise["n_baseline"], 0)
        self.assertTrue(any("mistura" in x for x in analise["avisos"]))

    def lerorigem(self, pasta_ensaio):
        return json.loads((pasta_ensaio / "resultado.json").read_text(encoding="utf-8")).get("origem") or {}

    def test_sem_pareceres_da_variante_nao_chuta_baseline(self):
        self.base(3)
        analise = self.analisar("V06", self.pasta)
        self.assertEqual(analise["n_baseline"], 0)
        self.assertTrue(any("Nenhum baseline" in x for x in analise["avisos"]))

    def test_antes_da_serie_versao_do_prompt_conta_so_os_controles_daquela_versao(self):
        self.base(2, versao_prompt="juiz-v1.1")
        self.base(1, versao_prompt="juiz-v1.3")
        analise = a.analisar(self.pasta, regra("V06"), self.pasta, "juiz-v1.3")
        self.assertEqual(analise["n_baseline"], 1)
        self.assertTrue(any("juiz-v1.3" in x for x in analise["avisos"]))
        self.assertEqual(a.analisar(self.pasta, regra("V06"), self.pasta, "juiz-v9")["n_baseline"], 0)
        self.assertEqual(a.analisar(self.pasta, regra("V06"), self.pasta)["n_baseline"], 0)

    def test_deteccao_expoe_trecho_e_nao_confirma_semantica(self):
        self.rodar("V03", parecer(("viabilidade", "sequencia", "maior", "ET1 está longa demais para o tempo da aula.")))
        p = self.analisar("V03")["linhas"][0]["pontuacao"]
        self.assertEqual(p["nivel"], "plena")  # mecânico: ID + critério + componente + gravidade
        self.assertFalse(p["semantica_confirmada"])
        self.assertIn("longa demais", p["trechos_do_alvo"]["F1"])
        self.assertIn("NÃO confirma", a.renderizar_relatorio(self.analisar("V03")))


class TestSeparacaoDeExecucoes(Base):
    def test_falha_tecnica_nao_entra_no_denominador(self):
        self.rodar("V03", parecer(V03_PLENA))
        self.rodar("V03", ErroGeracao("Groq HTTP 429: limite de tokens por minuto", tipo="http"))
        analise = self.analisar("V03")
        self.assertEqual((len(analise["linhas"]), len(analise["falhas_tecnicas"]), analise["n_execucoes"]), (1, 1, 2))
        self.assertEqual(analise["falhas_tecnicas"][0]["tipo"], "http")
        self.assertIn("429", analise["falhas_tecnicas"][0]["erro"])

    def test_validacao_local_e_outras_variantes_sao_ignoradas(self):
        self.rodar("V03", parecer(V03_PLENA), somente_validar=True)
        self.rodar("V04", parecer(("inclusao", "adaptacao", "maior", "ADP2 é genérica.")))
        analise = self.analisar("V03")
        self.assertEqual((analise["n_execucoes"], len(analise["linhas"]), len(analise["falhas_tecnicas"])), (1, 0, 0))

    def test_arquivo_corrompido_vira_aviso_e_nao_derruba_a_analise(self):
        self.rodar("V03", parecer(V03_PLENA))
        ruim = self.pasta / "20260101T000000Z-ruim"
        ruim.mkdir()
        (ruim / "resultado.json").write_text("{ não é json", encoding="utf-8")
        analise = self.analisar("V03")
        self.assertEqual(len(analise["linhas"]), 1)
        self.assertTrue(any("ruim" in x for x in analise["avisos"]))

    def test_pasta_inexistente_ou_vazia(self):
        analise = a.analisar(self.tmp / "nao_existe", regra("V03"))
        self.assertEqual((analise["linhas"], analise["falhas_tecnicas"]), ([], []))
        self.assertIn("Sem pareceres válidos", a.renderizar_relatorio(analise))


class TestAuditorias(Base):
    def auditar(self, p):
        self.rodar("V03", p)
        return {o["regra"]: o for o in self.analisar("V03")["linhas"][0]["auditoria"]}

    def trocar(self, p, criterio, texto):
        p = deepcopy(p)
        next(x for x in p["avaliacoes"] if x["criterio"] == criterio)["justificativa"] = texto
        return p

    def test_parecer_limpo_nao_gera_observacoes(self):
        self.rodar("V03", parecer(V03_PLENA))
        self.assertEqual(self.analisar("V03")["linhas"][0]["auditoria"], [])

    def test_id_inexistente(self):
        obs = self.auditar(self.trocar(parecer(V03_PLENA), "inclusao", "Atende, como mostram ADP1 e ET7."))
        self.assertEqual(obs["id_inexistente"]["detalhe"], "ET7")

    def test_soma_de_minutos_no_texto(self):
        obs = self.auditar(self.trocar(parecer(V03_PLENA), "viabilidade", "ET1 e ET2 somam 15 + 35 = 50 minutos, cabendo na aula."))
        self.assertIn("15 + 35", obs["soma_de_minutos_no_texto"]["detalhe"])
        obs = self.auditar(self.trocar(parecer(V03_PLENA), "viabilidade", "A soma das etapas fecha os 50 min informados em ET1 e ET2."))
        self.assertIn("soma_de_minutos_no_texto", obs)

    def test_nota_3_sem_citar_id_do_plano(self):
        obs = self.auditar(self.trocar(parecer(V03_PLENA), "inclusao", "Está tudo adequado neste critério."))
        self.assertEqual(obs["nota_3_sem_id_do_plano"]["onde"], "avaliacoes/inclusao")

    def test_justificativa_repetida(self):
        p = parecer(V03_PLENA)
        for c in ("inclusao", "alinhamento_objetivos"):
            p = self.trocar(p, c, "Texto idêntico copiado entre critérios (ET1).")
        self.assertIn("justificativa_repetida", self.auditar(p))

    def test_componente_provavelmente_errado(self):
        obs = self.auditar(parecer(("viabilidade", "adaptacao", "maior", "ET1 exige projeção.")))
        self.assertIn("sequencia", obs["componente_provavelmente_errado"]["detalhe"])

    def test_componente_coerente_com_um_dos_ids_citados_nao_e_marcado(self):
        self.rodar("V03", parecer(("avaliacao_aprendizagem", "avaliacao_preliminar", "maior", "EVI2 não demonstra o que OBJ2 pede.")))
        regras = {o["regra"] for o in self.analisar("V03")["linhas"][0]["auditoria"]}
        self.assertNotIn("componente_provavelmente_errado", regras)

    def test_sem_caso_json_nao_audita_e_avisa_no_relatorio(self):
        self.rodar("V03", parecer(V03_PLENA))
        for pasta in self.pasta.iterdir():
            (pasta / "caso.json").unlink()
        analise = self.analisar("V03")
        self.assertIsNone(analise["linhas"][0]["auditoria"])
        self.assertIn("Sem `caso.json`", a.renderizar_relatorio(analise))


class TestRelatorioECli(Base):
    def test_relatorio_tem_denominadores_aviso_e_falhas_tecnicas(self):
        self.rodar("V03", parecer(V03_PLENA))
        self.rodar("V03", parecer(("viabilidade", "sequencia", "menor", "ET1 depende de projeção.")))
        self.rodar("V03", ErroGeracao("Groq HTTP 400", tipo="http"))
        texto = a.renderizar_relatorio(self.analisar("V03"))
        for esperado in ("V03-RECURSO-NAO-CONFIRMADO", "pareceres válidos: **2**", "falhas técnicas: **1**", "plena: 1/2",
                         "parcial: 1/2", "Não substitui a leitura humana", "Falhas técnicas (separadas dos pareceres)",
                         "7000 a 7000", "não** entram como detecção"):
            self.assertIn(esperado, texto)

    def test_relatorio_do_controle_alerta_baseline_insuficiente(self):
        self.rodar("BASE", parecer())
        self.rodar("V06", parecer())
        texto = a.renderizar_relatorio(self.analisar("V06", self.pasta))
        self.assertIn("insuficiente: o protocolo pede 3", texto)

    def test_cli_grava_sem_sobrescrever(self):
        self.rodar("V03", parecer(V03_PLENA))
        saida = self.tmp / "relatorio.md"
        argv = ["--pasta", str(self.pasta), "--regra", str(RAIZ / "experimentos/juiz/pontuacao/V03.json"), "--saida", str(saida)]
        self.assertEqual(a.main(argv), 0)
        antes = saida.read_text(encoding="utf-8")
        self.assertIn("plena: 1/1", antes)
        self.assertEqual(a.main(argv), 2)
        self.assertEqual(saida.read_text(encoding="utf-8"), antes)

    def test_cli_regra_invalida(self):
        ruim = self.tmp / "ruim.json"
        ruim.write_text("{}", encoding="utf-8")
        self.assertEqual(a.main(["--pasta", str(self.pasta), "--regra", str(ruim)]), 2)


class TestArquivosDePontuacao(TestCase):
    def test_uma_regra_por_variante_ligada_a_hipotese_pre_registrada(self):
        for n in ("V03", "V04", "V05", "V06"):
            r = regra(n)
            spec = json.loads((RAIZ / r["fonte"]["especificacao"]).read_text(encoding="utf-8"))
            protocolo = (RAIZ / r["fonte"]["protocolo"]).read_text(encoding="utf-8")
            with self.subTest(variante=n):
                self.assertEqual(r["id_variante"], spec["id_variante"])
                self.assertEqual(r["fonte"]["sha256_hipotese"], hash_json(spec["hipotese"]))
                self.assertIn(r["fonte"]["sha256_hipotese"], protocolo)

    def test_regras_de_deteccao_batem_com_o_texto_da_hipotese(self):
        import re
        ids = lambda t: set(re.findall(r"`([a-z_]+)`", t))
        for n in ("V03", "V04", "V05"):
            r = regra(n)
            spec = json.loads((RAIZ / r["fonte"]["especificacao"]).read_text(encoding="utf-8"))
            caso = carregar_caso(RAIZ / spec["arquivo_caso"])
            with self.subTest(variante=n):
                self.assertEqual(r["tipo"], "deteccao")
                self.assertEqual(set(r["pleno"]["criterios"]), ids(spec["hipotese"]["criterio_esperado"]))
                self.assertEqual(set(r["pleno"]["componentes"]), ids(spec["hipotese"]["componente_esperado"]))
                self.assertTrue(set(r["pleno"]["componentes"]) <= set(ETAPAS))
                self.assertTrue(set(r["pleno"]["criterios"]) <= set(contrato.CRITERIOS))
                self.assertTrue(set(r["ids_alvo"]) <= a.ids_do_plano(caso["plano"]))
                for c in r["nota_maxima"]:
                    self.assertIn(c, contrato.CRITERIOS)

    def test_alvo_corresponde_ao_campo_alterado(self):
        esperado = {"V03": "desenvolvimento[0]", "V04": "adaptacoes[1]", "V05": "desenvolvimento[1]"}
        for n, trecho in esperado.items():
            r = regra(n)
            spec = json.loads((RAIZ / r["fonte"]["especificacao"]).read_text(encoding="utf-8"))
            self.assertIn(trecho, spec["campo"])
            caso = carregar_caso(RAIZ / spec["arquivo_caso"])
            self.assertTrue(all(i in a.ids_do_plano(caso["plano"]) for i in r["ids_alvo"]))

    def test_v06_e_controle_com_termos_validos(self):
        r = regra("V06")
        self.assertEqual(r["tipo"], "controle")
        import re
        for termo in r["termos_da_reformulacao"]:
            re.compile(termo)
