"""Testes da concordância entre avaliadores (Python) e da cópia em JavaScript da mesma conta. Offline."""
import contextlib
import io
import json
from pathlib import Path
import random
import shutil
import subprocess
import tempfile
from unittest import TestCase, skipUnless

import adjudicacao_web as web
import concordancia as c

NODE = shutil.which("node")


def exp(fase="A", itens=None, notas=None, nome="X", dataset="d1"):
    return dict(fase=fase, dataset_id=dataset, avaliador=nome, itens=itens or {}, notas_proprias=notas or {})


class TestKappa(TestCase):
    def test_exemplo_de_livro_kappa_0_4(self):
        a = ["s"] * 25 + ["n"] * 25
        b = ["s"] * 20 + ["n"] * 5 + ["s"] * 10 + ["n"] * 15  # po 0,70; pe 0,50
        self.assertAlmostEqual(c.kappa_nominal(a, b), 0.4)
        self.assertAlmostEqual(c.concordancia_simples(a, b), 0.7)

    def test_concordancia_perfeita_e_total_discordancia(self):
        self.assertAlmostEqual(c.kappa_nominal(list("abab"), list("abab")), 1.0)
        self.assertAlmostEqual(c.kappa_nominal(list("ab"), list("ba")), -1.0)

    def test_indefinido_quando_so_ha_uma_categoria(self):
        self.assertIsNone(c.kappa_nominal(["s"] * 5, ["s"] * 5))
        self.assertIsNone(c.kappa_nominal([], []))
        self.assertIsNone(c.concordancia_simples([], []))

    def test_tamanhos_diferentes_sao_erro(self):
        with self.assertRaises(ValueError):
            c.kappa_nominal(["a"], ["a", "b"])
        with self.assertRaises(ValueError):
            c.kappa_ponderado([1], [1, 2])

    def test_ponderado_extremos_e_a_penalizacao_por_distancia(self):
        self.assertAlmostEqual(c.kappa_ponderado([0, 1, 2, 3], [0, 1, 2, 3]), 1.0)
        self.assertAlmostEqual(c.kappa_ponderado([0, 3], [3, 0]), -1.0)
        perto = c.kappa_ponderado([0, 1, 2, 3, 2, 1], [1, 1, 2, 2, 2, 1])
        longe = c.kappa_ponderado([0, 1, 2, 3, 2, 1], [3, 1, 2, 0, 2, 1])
        self.assertGreater(perto, longe)

    @skipUnless(NODE, "Node não instalado")
    def test_versao_javascript_da_pagina_da_o_mesmo_resultado(self):
        bloco = web.COMUM.split("// <KAPPA>")[1].split("// </KAPPA>")[0]
        rng = random.Random(7)
        casos = []
        for _ in range(40):
            n = rng.randint(2, 30)
            casos.append(dict(a=[rng.randint(0, 3) for _ in range(n)], b=[rng.randint(0, 3) for _ in range(n)]))
        casos.append(dict(a=[2] * 4, b=[2] * 4))  # indefinido
        script = bloco + "\nconst casos=" + json.dumps(casos) + ";\nconst f=v=>v===null?null:(Number.isFinite(v)?v:\"NaN\");console.log(JSON.stringify(casos.map(c=>[f(kappaNominal(c.a,c.b)),f(kappaPonderado(c.a,c.b,4))])));"
        saida = json.loads(subprocess.run([NODE, "-e", script], capture_output=True, text=True, check=True, timeout=30).stdout)
        self.assertEqual(len(saida), len(casos))
        for caso, (kn, kp) in zip(casos, saida):
            for js, py in ((kn, c.kappa_nominal(caso["a"], caso["b"])), (kp, c.kappa_ponderado(caso["a"], caso["b"]))):
                if py is None:
                    self.assertIsNone(js)
                else:
                    self.assertAlmostEqual(js, py, places=9)


class TestComparar(TestCase):
    def test_exportacoes_de_arquivos_diferentes_sao_recusadas(self):
        with self.assertRaises(ValueError):
            c.comparar(exp(dataset="d1"), exp(dataset="d2"))
        with self.assertRaises(ValueError):
            c.comparar(exp("A"), exp("B"))

    def test_conta_itens_comuns_e_lista_divergencias(self):
        e1 = exp(itens={"I01": dict(procedencia="procedente", gravidade="adequada"), "I02": dict(procedencia="parcial"),
                        "I03": dict(procedencia="improcedente")})
        e2 = exp(itens={"I01": dict(procedencia="procedente", gravidade="exagerada"), "I02": dict(procedencia="procedente")})
        r = c.comparar(e1, e2)
        self.assertEqual(r["campos"]["procedencia"]["n"], 2)  # I03 só tem um avaliador
        self.assertAlmostEqual(r["campos"]["procedencia"]["concordancia"], 0.5)
        achadas = {(d["codigo"], d["campo"]) for d in r["divergencias"]}
        self.assertEqual(achadas, {("I02", "procedencia"), ("I01", "gravidade")})

    def test_notas_so_divergem_com_diferenca_de_2_ou_mais(self):
        n1 = {"P1": {"viabilidade": 3, "inclusao": 2, "aderencia_curricular": 0, "comentario": "x"}}
        n2 = {"P1": {"viabilidade": 2, "inclusao": 2, "aderencia_curricular": 2, "comentario": "y"}}
        r = c.comparar(exp(notas=n1), exp(notas=n2))
        self.assertEqual(r["notas_proprias"]["n"], 3)
        self.assertAlmostEqual(r["notas_proprias"]["concordancia"], 1 / 3)
        self.assertAlmostEqual(r["notas_proprias"]["dentro_de_1"], 2 / 3)
        self.assertEqual([(d["codigo"], d["campo"]) for d in r["divergencias"]], [("P1", "aderencia_curricular")])

    def test_ignora_valor_ausente_e_nota_nao_inteira(self):
        e1 = exp(itens={"I01": dict(procedencia=None)}, notas={"P1": {"viabilidade": "3"}})
        e2 = exp(itens={"I01": dict(procedencia="procedente")}, notas={"P1": {"viabilidade": 3}})
        r = c.comparar(e1, e2)
        self.assertEqual((r["campos"]["procedencia"]["n"], r["notas_proprias"]["n"]), (0, 0))

    def test_fase_b_usa_os_campos_presentes(self):
        e1 = exp("B", itens={"R01": dict(deteccao="plena", comentario="a")})
        e2 = exp("B", itens={"R01": dict(deteccao="parcial", comentario="b")})
        r = c.comparar(e1, e2)
        self.assertEqual(list(r["campos"]), ["deteccao"])
        self.assertEqual(len(r["divergencias"]), 1)
        self.assertNotIn("notas_proprias", r)

    def test_cli_codigos_de_saida(self):
        with tempfile.TemporaryDirectory() as t:
            t = Path(t)
            (t / "a.json").write_text(json.dumps(exp(nome="Ana", itens={"I01": dict(procedencia="procedente")})), encoding="utf-8")
            (t / "b.json").write_text(json.dumps(exp(nome="Beto", itens={"I01": dict(procedencia="parcial")})), encoding="utf-8")
            (t / "ruim.json").write_text("{nao é json", encoding="utf-8")
            saida = io.StringIO()
            with contextlib.redirect_stdout(saida):
                self.assertEqual(c.main([str(t / "a.json"), str(t / "b.json")]), 0)
            self.assertIn("Ana × Beto", saida.getvalue())
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(c.main([str(t / "a.json"), str(t / "ruim.json")]), 2)
                self.assertEqual(c.main([str(t / "a.json"), str(t / "nao_existe.json")]), 2)
