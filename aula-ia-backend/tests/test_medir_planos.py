"""Regra de medição fixa da PoC07B (medir_planos.py). Sem rede. Execute a partir de aula-ia-backend."""
from contextlib import redirect_stdout
from copy import deepcopy
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

import medir_planos as m

FIXTURE = json.loads((Path(__file__).parent / "dados/plano_v2/fixture_ordenacao.json").read_text(encoding="utf-8"))
LIMPO = "Os estudantes comparam elementos vizinhos e trocam quando estão fora de ordem, até a lista ficar ordenada."


def plano_limpo():
    """Plano válido com todos os textos trocados por uma frase acentuada e sem material."""
    p = deepcopy(FIXTURE["plano_esperado"])
    p["metodologia"] = LIMPO
    p["objetivo_geral"] = LIMPO
    for e in p["desenvolvimento"]:
        e.update(atividade=LIMPO, acao_docente=LIMPO, acao_discente=LIMPO)
    av = p["avaliacao_aprendizagem"]
    av["uso_resultados"] = LIMPO
    for x in av["evidencias"]:
        x.update(criterio=LIMPO, evidencia_esperada=LIMPO)
    for x in av["instrumentos"]:
        x.update(descricao=LIMPO, procedimento=LIMPO)
    for a in p["adaptacoes"]:
        a["descricao"] = LIMPO
    p["conteudos"] = ["Ordenação por comparação"]
    for o in p["objetivos_especificos"]:
        o["descricao"] = LIMPO
    return p


def caso(plano=None, recursos="quadro e pincel", prompts=("especialistas-plano-2.3",), **contexto):
    entrada = deepcopy(FIXTURE["entrada"])
    entrada["contexto"].update(recursos=recursos, **contexto)
    plano = plano or plano_limpo()
    plano["recursos"] = recursos  # o contrato exige cópia exata de contexto.recursos
    return dict(plano=plano, entrada=entrada, modelo_gerador="x",
                origem=dict(tipo="sqlite_real", prompts_gerador=list(prompts)))


class TestH1MaterialAusente(TestCase):
    def test_plano_limpo_nao_viola(self):
        self.assertEqual(m.material_ausente(plano_limpo(), "quadro e pincel"), [])

    def test_cada_radical_do_protocolo_conta_quando_ausente_dos_recursos(self):
        exemplos = {"cartao/cartoes": ["um cartão", "os cartões"], "papel": ["folha de papel"], "baralho": ["um baralho"],
                    "ficha": ["fichas"], "projetor": ["o projetor"], "data show": ["data show"],
                    "computador": ["computadores"], "internet": ["Internet"], "celular": ["celulares"],
                    "quadro/pincel": ["no quadro", "o pincel"], "impress": ["material impresso", "impressão"],
                    "alto-relevo/tatil": ["em alto-relevo", "material tátil"]}
        self.assertEqual(set(exemplos), {nome for nome, _ in m.RADICAIS})
        for nome, frases in exemplos.items():
            for frase in frases:
                p = plano_limpo()
                p["metodologia"] = LIMPO + " Usa " + frase + "."
                with self.subTest(frase=frase):
                    recursos = "celulares" if nome != "celular" else "projetor"
                    self.assertEqual(m.material_ausente(p, recursos), [nome])

    def test_radical_presente_nos_recursos_nao_conta_mesmo_com_acento_e_maiuscula(self):
        p = plano_limpo()
        p["metodologia"] = LIMPO + " Cada dupla recebe cartões e usa o quadro."
        self.assertEqual(m.material_ausente(p, "Quadro e pincel, CARTÕES numerados"), [])
        self.assertEqual(m.material_ausente(p, "quadro e pincel"), ["cartao/cartoes"])

    def test_papel_nao_conta_com_material_impresso(self):
        p = plano_limpo()
        p["metodologia"] = LIMPO + " Entregue a folha de papel."
        self.assertEqual(m.material_ausente(p, "material impresso"), [])
        self.assertEqual(m.material_ausente(p, "quadro e pincel"), ["papel"])

    def test_campos_excluidos_nao_contam(self):
        p = plano_limpo()
        p["recursos"] = "cartões, projetor"
        p["referencias"][0]["titulo"] = "Computador e papel"
        p["habilidade_bncc"]["descricao"] = "celular"
        self.assertEqual(m.material_ausente(p, "quadro e pincel"), [])

    def test_texto_em_campos_aninhados_conta(self):
        p = plano_limpo()
        p["adaptacoes"][0]["descricao"] = "Use fichas ampliadas."
        self.assertEqual(m.material_ausente(p, "projetor"), ["ficha"])


class TestH2SemAcentos(TestCase):
    SEM = "A observacao do professor sera registrada durante a atividade de comparacao entre os grupos da turma."

    def test_campo_longo_sem_acento_com_palavra_guia_conta(self):
        p = plano_limpo()
        p["avaliacao_aprendizagem"]["uso_resultados"] = self.SEM
        self.assertEqual(m.campos_sem_acento(p), ["avaliacao_aprendizagem.uso_resultados"])

    def test_sem_palavra_guia_nao_conta(self):
        p = plano_limpo()
        p["metodologia"] = "Os estudantes trabalham em duplas e depois apresentam suas listas para toda a turma reunida."
        self.assertEqual(m.campos_sem_acento(p), [])

    def test_com_algum_acento_nao_conta(self):
        p = plano_limpo()
        p["metodologia"] = self.SEM + " Até logo."
        self.assertEqual(m.campos_sem_acento(p), [])

    def test_acento_em_maiuscula_tambem_conta_como_acento(self):
        p = plano_limpo()
        p["metodologia"] = "A OBSERVACAO DO PROFESSOR SERA REGISTRADA NA ATIVIDADE DE COMPARACAO. É ASSIM."
        self.assertEqual(m.campos_sem_acento(p), [])

    def test_ate_60_caracteres_nao_conta_e_61_conta(self):
        p = plano_limpo()
        base = "a observacao e simples "
        p["metodologia"] = (base * 3)[:60]
        self.assertEqual(m.campos_sem_acento(p), [])
        p["metodologia"] = (base * 3)[:61]
        self.assertEqual(m.campos_sem_acento(p), ["metodologia"])

    def test_palavra_guia_e_palavra_inteira(self):
        p = plano_limpo()
        p["metodologia"] = "Os grupos montam a naocao e as aposentadorias da turma em grupos pequenos e organizados."
        self.assertEqual(m.campos_sem_acento(p), [])
        p["metodologia"] = "Os grupos fazem a reavaliacao do canao e da subcomparacao em grupos pequenos e organizados."
        self.assertEqual(m.campos_sem_acento(p), [])
        for guia in m.PALAVRAS_GUIA:
            p["metodologia"] = f"Os grupos fazem a tarefa {guia} com calma e em silencio durante toda a aula de hoje."
            with self.subTest(guia=guia):
                self.assertEqual(m.campos_sem_acento(p), ["metodologia"])

    def test_campos_excluidos_nao_contam(self):
        p = plano_limpo()
        p["recursos"] = self.SEM
        self.assertEqual(m.campos_sem_acento(p), [])


class TestMedirCasoECarregar(TestCase):
    def test_medida_completa_de_plano_valido(self):
        r = m.medir_caso(caso(recursos="papel e cartões", duracao_min=FIXTURE["entrada"]["contexto"]["duracao_min"]))
        self.assertEqual((r["h1"], r["h2"], r["minutos_ok"], r["contrato_ok"]), (False, False, True, True))

    def test_minutos_e_contrato_detectam_soma_errada(self):
        p = plano_limpo()
        p["desenvolvimento"][0]["minutos"] += 5
        r = m.medir_caso(caso(p))
        self.assertFalse(r["minutos_ok"])
        self.assertFalse(r["contrato_ok"])
        self.assertEqual(r["minutos"], FIXTURE["entrada"]["contexto"]["duracao_min"] + 5)

    def test_contrato_quebrado_estruturalmente_nao_derruba_a_medicao(self):
        p = plano_limpo()
        del p["objetivo_geral"]
        self.assertFalse(m.medir_caso(caso(p))["contrato_ok"])

    def test_carregar_agrupa_por_prompt_filtra_pelas_entradas_e_conta(self):
        ctx = FIXTURE["entrada"]["contexto"]
        entrada_protocolo = dict(tema=ctx["tema"], tipo=ctx["tipo"], duracao_min=ctx["duracao_min"],
                                 recursos="quadro e pincel", habilidade=FIXTURE["entrada"]["habilidade"]["codigo"])
        com_cartao = plano_limpo()
        com_cartao["metodologia"] += " Use cartões."
        with TemporaryDirectory() as d:
            for nome, c in {"a.json": caso(prompts=("especialistas-plano-2.2",)),
                            "b.json": caso(com_cartao),
                            "c.json": caso(),
                            "fora.json": caso(recursos="papel")}.items():
                (Path(d) / nome).write_text(json.dumps(c, ensure_ascii=False), encoding="utf-8")
            grupos, ignorados = m.carregar(d, [entrada_protocolo])
            self.assertEqual(ignorados, ["fora.json"])
            self.assertEqual(sorted(grupos), ["especialistas-plano-2.2", "especialistas-plano-2.3"])
            self.assertEqual([a for a, *_ in grupos["especialistas-plano-2.3"]], ["b.json", "c.json"])
            tabela = m.tabela(grupos)
            self.assertIn("| especialistas-plano-2.3 | 2 | 1/2 | 0/2 | 2/2 | 2/2 |", tabela)
            self.assertIn("| especialistas-plano-2.2 | 1 | 0/1 | 0/1 | 1/1 | 1/1 |", tabela)
            self.assertIn("cartao/cartoes", m.detalhe(grupos))
            sem_filtro, nada = m.carregar(d)
            self.assertEqual((len(sem_filtro["especialistas-plano-2.3"]), nada), (3, []))

    def test_main_nao_sobrescreve_saida(self):
        with TemporaryDirectory() as d:
            (Path(d) / "c.json").write_text(json.dumps(caso(), ensure_ascii=False), encoding="utf-8")
            saida = Path(d) / "rel.md"
            with redirect_stdout(io.StringIO()):
                self.assertEqual(m.main(["--pasta", d, "--saida", str(saida)]), 0)
                primeiro = saida.read_text(encoding="utf-8")
                from contextlib import redirect_stderr
                with redirect_stderr(io.StringIO()):
                    self.assertEqual(m.main(["--pasta", d, "--saida", str(saida)]), 2)
            self.assertEqual(saida.read_text(encoding="utf-8"), primeiro)
