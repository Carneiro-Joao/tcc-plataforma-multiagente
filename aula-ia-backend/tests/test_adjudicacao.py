"""Testes do gerador das páginas de adjudicação humana. Offline.

Os ensaios são produzidos pelo PRÓPRIO executar_ensaio com agentes falsos (mesmo formato dos reais).
Os pareceres são sintéticos: provam seleção, cegamento e geração dos arquivos, não a qualidade do Juiz.
"""
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from unittest import TestCase, skipUnless

import adjudicacao as adj
import adjudicacao_web as web
from ensaio_juiz import executar_ensaio
from erros import ErroGeracao
from test_analisar_serie import Agente, CASO, parecer

RAIZ = Path(__file__).resolve().parents[2]
NODE = shutil.which("node")
F_ET1 = ("viabilidade", "sequencia", "maior", "ET1 exige projeção e internet, não confirmados nos recursos.")
F_OUTRA = ("aderencia_curricular", "objetivos", "maior", "O plano só trabalha Bubble sort.")
F_HTML = ("coerencia_metodologica", "sequencia", "menor", "Quebra </script><b>x</b> & \"aspas\" 'simples'.")


class Base(TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.pasta = self.tmp / "ensaios"
        self.pasta.mkdir()

    def rodar(self, chave, *falhas, **kw):
        r, pasta = executar_ensaio(RAIZ / CASO[chave], self.pasta, fabrica=lambda **k: Agente(parecer(*falhas)), **kw)
        self.ultima = Path(pasta) if Path(pasta).is_dir() else Path(pasta).parent
        return r

    def pastas(self):
        return sorted(p for p in self.pasta.iterdir())

    def alterar(self, pasta, **campos):
        arq = pasta / "resultado.json"
        d = json.loads(arq.read_text(encoding="utf-8"))
        d.update(campos)
        arq.write_text(json.dumps(d), encoding="utf-8")

    def popular(self):
        for chave in ("BASE", "V03", "V06"):
            for _ in range(2):
                self.rodar(chave, F_ET1 if chave == "V03" else F_OUTRA, F_HTML)

    def montar(self, seed=42):
        sel, _ = adj.coletar(self.pasta)
        return adj.montar(sel, adj.carregar_specs(RAIZ / "experimentos/juiz/variantes"), seed)


class TestColetar(Base):
    def test_agrupa_controle_e_variantes_e_avisa_o_que_falta(self):
        self.popular()
        sel, avisos = adj.coletar(self.pasta)
        self.assertEqual({g: len(v) for g, v in sel.items()}, {"CONTROLE": 2, "V03": 2, "V06": 2})
        self.assertTrue(any("V04" in a and "V05" in a for a in avisos))

    def test_ignora_falha_tecnica_outro_prompt_e_validacao_local(self):
        self.rodar("V03", F_ET1)
        self.rodar("V03", F_ET1, somente_validar=True)  # modo validacao_local
        self.rodar("V03", F_ET1)
        self.alterar(self.ultima, versao_prompt="juiz-v1.2")
        executar_ensaio(RAIZ / CASO["V03"], self.pasta, fabrica=lambda **k: Agente(ErroGeracao("falha técnica simulada")))
        sel, _ = adj.coletar(self.pasta)
        self.assertEqual(len(sel["V03"]), 1)

    def test_variantes_antigas_v01_v02_ficam_de_fora(self):
        self.rodar("V01", F_OUTRA)
        self.rodar("V03", F_ET1)
        sel, _ = adj.coletar(self.pasta)
        self.assertEqual(set(sel), {"V03"})

    def test_controle_de_outro_plano_nao_entra(self):
        self.rodar("V06", F_OUTRA)
        self.rodar("BASE", F_OUTRA)
        self.rodar("BASE", F_OUTRA)
        self.alterar(self.ultima, plano_sha256="0" * 64)
        sel, _ = adj.coletar(self.pasta)
        self.assertEqual(len(sel["CONTROLE"]), 1)

    def test_sem_variantes_aceita_qualquer_controle_do_plano_original(self):
        self.rodar("BASE", F_OUTRA)
        sel, _ = adj.coletar(self.pasta)
        self.assertEqual(len(sel["CONTROLE"]), 1)

    def test_avisa_quando_mistura_configuracoes(self):
        self.rodar("V03", F_ET1)
        self.rodar("V03", F_ET1)
        self.alterar(self.ultima, modelo_juiz="outro/modelo")
        _, avisos = adj.coletar(self.pasta)
        self.assertTrue(any("configurações" in a for a in avisos))


class TestCegamento(Base):
    def setUp(self):
        super().setUp()
        self.popular()
        self.A, self.B, self.chave = self.montar()
        self.texto = json.dumps(self.A, ensure_ascii=False)

    def test_fase_a_nao_contem_nada_que_identifique_variante_ou_execucao(self):
        proibidos = ["V03", "V06", "V04", "variante", "CONTROLE", "controle", "id_variante", "sqlite", "plano_sha256"]
        proibidos += [e.name for e in self.pastas()] + [e.name.split("-")[1] for e in self.pastas()]
        proibidos += [h["plano_sha256"] for h in self.chave["planos"].values()]
        for termo in proibidos:
            with self.subTest(termo):
                self.assertNotIn(termo, self.texto)

    def test_itens_e_planos_tem_codigos_opacos_e_campos_minimos(self):
        self.assertTrue(all(re.fullmatch(r"I\d\d", i["codigo"]) for i in self.A["itens"]))
        self.assertTrue(all(re.fullmatch(r"P\d", p["codigo"]) for p in self.A["planos"]))
        self.assertEqual(set(self.A["itens"][0]), {"codigo", "plano", "criterio", "componente", "gravidade", "descricao", "correcao"})
        self.assertEqual(set(self.A["planos"][0]), {"codigo", "plano", "entrada"})

    def test_todas_as_criticas_validas_entram_e_a_chave_as_liga_de_volta(self):
        total = 6 * 2  # 3 grupos x 2 pareceres x 2 falhas
        self.assertEqual(len(self.A["itens"]), total)
        self.assertEqual(len(self.chave["itens"]), total)
        for item in self.A["itens"]:
            ligacao = self.chave["itens"][item["codigo"]]
            bruto = json.loads((self.pasta / ligacao["pasta"] / "resultado.json").read_text(encoding="utf-8"))
            falha = next(f for f in bruto["resultado"]["parecer"]["falhas"] if f["id"] == ligacao["falha_id"])
            self.assertEqual((falha["descricao"], falha["criterio"], falha["componente"], falha["gravidade"]),
                             (item["descricao"], item["criterio"], item["componente"], item["gravidade"]))
            self.assertEqual(ligacao["plano"], item["plano"])

    def test_itens_agrupados_por_plano_e_um_plano_por_hash(self):
        planos = [i["plano"] for i in self.A["itens"]]
        self.assertEqual(planos, sorted(planos))
        self.assertEqual(len(self.A["planos"]), 3)  # original, V03 e V06 têm planos diferentes
        self.assertEqual(len({p["codigo"] for p in self.A["planos"]}), 3)

    def test_ordem_embaralhada_mas_reprodutivel(self):
        A2, _, _ = self.montar(42)
        self.assertEqual(self.A, A2)
        outros = {json.dumps(self.montar(s)[0]["itens"]) for s in range(1, 8)}
        self.assertGreater(len(outros), 1)

    def test_a_ordem_dos_planos_e_a_das_criticas_variam_com_a_semente(self):
        mapas, ordens = set(), set()
        for seed in range(1, 12):
            A, _, chave = self.montar(seed)
            mapas.add(json.dumps({c: v["plano_sha256"] for c, v in chave["planos"].items()}, sort_keys=True))
            ordens.add(json.dumps([(chave["itens"][i["codigo"]]["pasta"], chave["itens"][i["codigo"]]["falha_id"], i["plano"]) for i in A["itens"]]))
        self.assertGreater(len(mapas), 1)  # P1, P2... não seguem uma ordem fixa dos hashes
        self.assertGreater(len(ordens), 1)
        # dentro de um plano a ordem não é a das execuções (pasta, falha): há semente em que difere
        def difere(seed):
            A, _, chave = self.montar(seed)
            for plano in {i["plano"] for i in A["itens"]}:
                real = [(chave["itens"][i["codigo"]]["pasta"], chave["itens"][i["codigo"]]["falha_id"]) for i in A["itens"] if i["plano"] == plano]
                if real != sorted(real):
                    return True
            return False
        self.assertTrue(any(difere(s) for s in range(1, 12)))

    def test_codigo_do_item_nao_revela_o_grupo(self):
        self.assertTrue(all(re.fullmatch(r"I\d\d", c) for c in self.chave["itens"]))
        self.assertEqual(sorted(self.chave["itens"]), [f"I{k:02d}" for k in range(1, 13)])

    def test_dataset_id_muda_quando_o_conteudo_muda(self):
        self.rodar("V03", F_OUTRA)
        self.assertNotEqual(self.montar()[0]["dataset_id"], self.A["dataset_id"])

    def test_fase_b_classifica_v06_como_controle_e_traz_o_defeito(self):
        self.assertEqual(self.B["grupos"]["V03"]["tipo"], "defeito")
        self.assertEqual(self.B["grupos"]["V06"]["tipo"], "controle")
        self.assertIn("projet", self.B["grupos"]["V03"]["descricao"].lower() + self.B["grupos"]["V03"]["valor_novo"].lower())
        self.assertEqual([p["grupo"] for p in self.B["pareceres"]], ["V03", "V03", "V06", "V06"])
        self.assertEqual(set(self.chave["pareceres"]), {p["codigo"] for p in self.B["pareceres"]})

    def test_sem_especificacao_da_variante_falha_com_mensagem_clara(self):
        sel, _ = adj.coletar(self.pasta)
        with self.assertRaises(ErroGeracao):
            adj.montar(sel, {}, 1)


class TestArquivos(Base):
    def test_gera_quatro_arquivos_e_nao_sobrescreve(self):
        self.popular()
        saida = self.tmp / "saida"
        r = adj.gerar(self.pasta, saida)
        self.assertEqual({Path(a).name for a in r["arquivos"]},
                         {"adjudicacao_A_cega.html", "adjudicacao_B_informada.html", "adjudicacao_comparar.html", "chave_de_codigos.json"})
        self.assertEqual((r["planos"], r["itens"], r["pareceres_b"]), (3, 12, 4))
        marca = saida / "adjudicacao_A_cega.html"
        marca.write_text("ORIGINAL", encoding="utf-8")
        with self.assertRaises(ErroGeracao):
            adj.gerar(self.pasta, saida)
        self.assertEqual(marca.read_text(encoding="utf-8"), "ORIGINAL")

    def test_gravar_novo_recusa_arquivo_existente(self):
        alvo = self.tmp / "ja_existe.txt"
        alvo.write_text("ORIGINAL", encoding="utf-8")
        with self.assertRaises(FileExistsError):
            adj.gravar_novo(alvo, "NOVO")
        self.assertEqual(alvo.read_text(encoding="utf-8"), "ORIGINAL")
        adj.gravar_novo(self.tmp / "novo.txt", "ok")
        self.assertEqual((self.tmp / "novo.txt").read_text(encoding="utf-8"), "ok")

    def test_pasta_sem_pareceres_e_erro(self):
        with self.assertRaises(ErroGeracao):
            adj.gerar(self.pasta, self.tmp / "s")

    def test_cli_codigos_de_saida(self):
        import contextlib
        import io
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(adj.main(["--ensaios", str(self.pasta), "--saida", str(self.tmp / "x")]), 2)
        self.popular()
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(adj.main(["--ensaios", str(self.pasta), "--saida", str(self.tmp / "y")]), 0)

    def test_html_incorpora_dados_sem_quebrar_o_script_e_sem_rede(self):
        self.popular()
        r = adj.gerar(self.pasta, self.tmp / "s")
        for arq in r["arquivos"]:
            if not arq.endswith(".html"):
                continue
            html = Path(arq).read_text(encoding="utf-8")
            with self.subTest(Path(arq).name):
                self.assertEqual(html.count("</script>"), 1)  # o </script> do texto do Juiz foi escapado
                self.assertNotRegex(html, r"https?://")
                self.assertNotIn("<link", html)
                self.assertNotIn("src=", html)
                dados = json.loads(re.search(r"const DATA=(.*?);\n", html, re.S).group(1))
                alvo = dados["A"] if "A" in dados else dados
                texto = json.dumps(alvo, ensure_ascii=False)
                self.assertIn("</script><b>x</b>", texto)  # voltou íntegro ao decodificar

    @skipUnless(NODE, "Node não instalado")
    def test_javascript_das_tres_paginas_tem_sintaxe_valida(self):
        self.popular()
        r = adj.gerar(self.pasta, self.tmp / "s")
        for arq in (a for a in r["arquivos"] if a.endswith(".html")):
            script = re.search(r"<script>(.*)</script>", Path(arq).read_text(encoding="utf-8"), re.S).group(1)
            js = self.tmp / (Path(arq).stem + ".js")
            js.write_text(script, encoding="utf-8")
            res = subprocess.run([NODE, "--check", str(js)], capture_output=True, text=True, timeout=30)
            self.assertEqual(res.returncode, 0, res.stderr)

    def test_chave_nao_vai_dentro_de_nenhum_html(self):
        self.popular()
        r = adj.gerar(self.pasta, self.tmp / "s")
        for arq in (a for a in r["arquivos"] if a.endswith("A_cega.html") or a.endswith("B_informada.html")):
            self.assertNotIn("chave-adjudicacao", Path(arq).read_text(encoding="utf-8"))
