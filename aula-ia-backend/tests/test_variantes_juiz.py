"""Testes da ferramenta de variantes controladas e das variantes V03 a V06 (PoC 05C).

Offline: sem rede e sem chave. Provam integridade, isolamento da manipulação e sigilo da hipótese;
não provam que o Juiz detecta os defeitos (isso depende dos ensaios reais).
"""
from copy import deepcopy
import json
from pathlib import Path
import re
import shutil
import tempfile
from unittest import TestCase

from casos_juiz import carregar_caso, hash_json
from contratos import juiz_v1 as contrato
from contratos.plano_v2 import ETAPAS
import variantes_juiz as v
from ensaio_juiz import executar_ensaio
from groq_juiz import MODELO_PADRAO

RAIZ = Path(__file__).resolve().parents[2]
BASE_REL = "experimentos/juiz/casos/ordenacao_real_994c4cd5.json"
SPECS = sorted((RAIZ / "experimentos" / "juiz" / "variantes").glob("*.spec.json"),
               key=lambda p: json.loads(p.read_text(encoding="utf-8"))["numero"])
PARECER_OK = json.loads((Path(__file__).parent / "dados" / "juiz_v1" / "pareceres.json").read_text(encoding="utf-8"))["favoravel"]
V01_SPEC = dict(
    id_variante="V01-EVI2-DESALINHADA", numero="V01", caso_base=BASE_REL,
    campo="plano.avaliacao_aprendizagem.evidencias[1].evidencia_esperada",
    valor_original="O estudante reorganiza os cartões de papel de forma sequencial crescente através de contagem oral e troca manual.",
    valor_novo="O estudante presta atenção à demonstração do professor e afirma ter gostado da atividade.",
    arquivo_caso="x.json", arquivo_protocolo="x.md", titulo="t", tipo_defeito="t", descricao_manipulacao="d",
    hipotese=dict(principal="p", criterio_esperado="c", componente_esperado="k"))


def spec(caminho):
    return json.loads(Path(caminho).read_text(encoding="utf-8"))


def spec_minima(**mudancas):
    base = deepcopy(V01_SPEC)
    base.update(mudancas)
    return base


class TestCaminhos(TestCase):
    def test_passos_validos(self):
        self.assertEqual(v.passos("plano.desenvolvimento[0].acao_docente"), ["plano", "desenvolvimento", 0, "acao_docente"])
        self.assertEqual(v.passos("plano.objetivo_geral"), ["plano", "objetivo_geral"])
        self.assertEqual(v.passos("plano.a[10][2].b"), ["plano", "a", 10, 2, "b"])

    def test_passos_invalidos(self):
        for ruim in ("", "plano", "entrada.contexto.tema", "plano..x", "plano.x[a]", "plano.x[]", "plano.x.", "plano.1x", None, 5):
            with self.subTest(campo=ruim), self.assertRaises(ValueError):
                v.passos(ruim)

    def test_ler_e_definir_nao_criam_campos(self):
        caso = carregar_caso(RAIZ / BASE_REL)
        self.assertEqual(v.ler_campo(caso, "plano.objetivo_geral"), caso["plano"]["objetivo_geral"])
        for inexistente in ("plano.nao_existe", "plano.desenvolvimento[9].titulo", "plano.objetivo_geral.x"):
            with self.subTest(campo=inexistente):
                with self.assertRaises(ValueError):
                    v.ler_campo(caso, inexistente)
                with self.assertRaises(ValueError):
                    v.definir_campo(caso, inexistente, "x")
        self.assertNotIn("nao_existe", caso["plano"])

    def test_diferencas(self):
        a = {"x": [1, {"y": "a"}], "z": 1}
        self.assertEqual(v.diferencas(a, deepcopy(a)), [])
        self.assertEqual(v.diferencas(a, {"x": [1, {"y": "b"}], "z": 1}), ["x[1].y"])
        self.assertEqual(v.diferencas(a, {"x": [1], "z": 1}), ["x"])
        self.assertEqual(v.diferencas({"z": 1}, {"z": True}), ["z"])  # 1 e True são diferentes
        self.assertEqual(v.diferencas({"z": 1}, {"z": 1, "w": 2}), ["w"])
        self.assertEqual(v.diferencas({"a": 1, "b": 2}, {"a": 9, "b": 8}), ["a", "b"])


class TestCriacao(TestCase):
    def test_reproduz_a_v01_manual_byte_a_byte(self):
        gerado = v.serializar_caso(v.criar_variante(V01_SPEC, RAIZ))
        real = (RAIZ / "experimentos/juiz/casos/ordenacao_variante_evi2_desalinhada_01.json").read_bytes().decode("utf-8")
        self.assertEqual(gerado, real.replace("\r\n", "\n"))

    def test_reproduz_a_v02_manual_usando_o_texto_do_arquivo(self):
        arquivo = RAIZ / "experimentos/juiz/casos/ordenacao_variante_bubble_sort_comparacao_invertida_02.json"
        real = json.loads(arquivo.read_text(encoding="utf-8"))
        campo = real["origem"]["campo_alterado"]
        base = carregar_caso(RAIZ / BASE_REL)
        s = spec_minima(id_variante=real["origem"]["id_variante"], numero=real["origem"]["id_variante"][:3], campo=campo,
                        valor_original=v.ler_campo(base, campo), valor_novo=v.ler_campo(real, campo),
                        observacao_origem=real["origem"]["observacao"])
        self.assertEqual(v.serializar_caso(v.criar_variante(s, RAIZ)), arquivo.read_text(encoding="utf-8").replace("\r\n", "\n"))

    def test_recusas_da_especificacao(self):
        casos = {
            "valor_original_errado": spec_minima(valor_original="outro texto"),
            "valor_novo_igual": spec_minima(valor_novo=V01_SPEC["valor_original"]),
            "valor_novo_vazio": spec_minima(valor_novo="   "),
            "valor_novo_nao_texto": spec_minima(valor_novo=5),
            "campo_fora_do_plano": spec_minima(campo="entrada.contexto.tema"),
            "campo_inexistente": spec_minima(campo="plano.nao_existe"),
            "numero_invalido": spec_minima(numero="V1"),
            "id_sem_numero": spec_minima(id_variante="OUTRO-NOME"),
            "hipotese_sem_criterio": spec_minima(hipotese=dict(principal="p", componente_esperado="k")),
            "campo_ausente": {k: x for k, x in V01_SPEC.items() if k != "titulo"},
            "observacao_vazia": spec_minima(observacao_origem="  "),
        }
        for nome, s in casos.items():
            with self.subTest(caso=nome), self.assertRaises(ValueError):
                v.criar_variante(s, RAIZ)

    def test_alteracao_que_quebra_vinculos_e_recusada_pelo_contrato_mecanico(self):
        # Trocar o id de ET1 deixa evidências e instrumentos apontando para uma etapa que não existe.
        s = spec_minima(campo="plano.desenvolvimento[0].id", valor_original="ET1", valor_novo="ET9")
        with self.assertRaises(Exception):
            v.criar_variante(s, RAIZ)

    def test_defesa_em_profundidade_recusa_se_um_segundo_campo_mudar(self):
        original = v.definir_campo

        def definir_e_alterar_outro(caso, campo, valor):
            original(caso, campo, valor)
            caso["plano"]["objetivo_geral"] += " (alterado por engano)"

        v.definir_campo = definir_e_alterar_outro
        try:
            with self.assertRaisesRegex(ValueError, "somente"):
                v.criar_variante(V01_SPEC, RAIZ)
        finally:
            v.definir_campo = original

    def test_criar_nao_altera_o_caso_base_nem_grava_arquivos(self):
        antes = (RAIZ / BASE_REL).read_bytes()
        v.criar_variante(V01_SPEC, RAIZ)
        self.assertEqual((RAIZ / BASE_REL).read_bytes(), antes)


class TestCliEmPastaTemporaria(TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        (self.tmp / "experimentos/juiz/casos").mkdir(parents=True)
        shutil.copy(RAIZ / BASE_REL, self.tmp / BASE_REL)
        self.spec = spec_minima(arquivo_caso="experimentos/juiz/casos/v.json", arquivo_protocolo="experimentos/juiz/P.md")
        self.spec_path = self.tmp / "v.spec.json"
        self.spec_path.write_text(json.dumps(self.spec, ensure_ascii=False), encoding="utf-8")

    def cli(self, *args):
        return v.main(["--raiz", str(self.tmp), *args])

    def criar(self):
        return self.cli("criar", "--spec", str(self.spec_path), "--data", "2026-11-17")

    def test_criar_e_verificar(self):
        self.assertEqual(self.criar(), 0)
        self.assertEqual(self.cli("verificar", "--spec", str(self.spec_path)), 0)
        protocolo = (self.tmp / "experimentos/juiz/P.md").read_text(encoding="utf-8")
        self.assertIn("17/11/2026", protocolo)
        self.assertIn(hash_json(self.spec["hipotese"]), protocolo)

    def test_nao_sobrescreve_caso_nem_protocolo(self):
        self.assertEqual(self.criar(), 0)
        antes = (self.tmp / "experimentos/juiz/casos/v.json").read_bytes()
        self.assertEqual(self.criar(), 2)
        self.assertEqual((self.tmp / "experimentos/juiz/casos/v.json").read_bytes(), antes)

    def test_protocolo_existente_impede_a_criacao_sem_deixar_caso_pela_metade(self):
        protocolo = self.tmp / "experimentos/juiz/P.md"
        protocolo.write_text("pré-registro anterior", encoding="utf-8")
        self.assertEqual(self.criar(), 2)
        self.assertEqual(protocolo.read_text(encoding="utf-8"), "pré-registro anterior")
        self.assertFalse((self.tmp / "experimentos/juiz/casos/v.json").exists())

    def test_caso_existente_impede_a_criacao_e_nao_gera_protocolo(self):
        caso = self.tmp / "experimentos/juiz/casos/v.json"
        caso.write_text("{}", encoding="utf-8")
        self.assertEqual(self.criar(), 2)
        self.assertEqual(caso.read_text(encoding="utf-8"), "{}")
        self.assertFalse((self.tmp / "experimentos/juiz/P.md").exists())

    def test_verificar_detecta_caso_editado_depois_do_pre_registro(self):
        self.criar()
        arquivo = self.tmp / "experimentos/juiz/casos/v.json"
        arquivo.write_text(arquivo.read_text(encoding="utf-8").replace("atenção", "atencao"), encoding="utf-8")
        self.assertEqual(self.cli("verificar", "--spec", str(self.spec_path)), 1)

    def test_verificar_detecta_hipotese_alterada_depois_do_pre_registro(self):
        self.criar()
        alterada = deepcopy(self.spec)
        alterada["hipotese"]["principal"] = "hipótese reescrita depois de ver o resultado"
        self.spec_path.write_text(json.dumps(alterada, ensure_ascii=False), encoding="utf-8")
        self.assertEqual(self.cli("verificar", "--spec", str(self.spec_path)), 1)

    def test_verificar_sem_protocolo_falha(self):
        self.criar()
        (self.tmp / "experimentos/juiz/P.md").unlink()
        self.assertEqual(self.cli("verificar", "--spec", str(self.spec_path)), 1)

    def test_valor_original_errado_nao_grava_nada(self):
        errada = deepcopy(self.spec)
        errada["valor_original"] = "x"
        self.spec_path.write_text(json.dumps(errada, ensure_ascii=False), encoding="utf-8")
        self.assertEqual(self.criar(), 2)
        self.assertFalse((self.tmp / "experimentos/juiz/casos/v.json").exists())
        self.assertFalse((self.tmp / "experimentos/juiz/P.md").exists())


class TestVariantesV03aV06(TestCase):
    def test_existem_as_quatro_especificacoes(self):
        self.assertEqual([spec(p)["numero"] for p in SPECS], ["V03", "V04", "V05", "V06"])

    def test_cada_variante_esta_integra(self):
        for caminho in SPECS:
            with self.subTest(spec=caminho.name):
                self.assertEqual(v.main(["verificar", "--spec", str(caminho)]), 0)

    def test_um_unico_campo_mudou_e_a_entrada_e_identica(self):
        base = carregar_caso(RAIZ / BASE_REL)
        campos = set()
        for caminho in SPECS:
            s = spec(caminho)
            var = carregar_caso(RAIZ / s["arquivo_caso"])
            with self.subTest(variante=s["numero"]):
                self.assertEqual(v.diferencas({k: base[k] for k in v.CAMPOS_COMPARADOS},
                                              {k: var[k] for k in v.CAMPOS_COMPARADOS}), [s["campo"]])
                self.assertEqual(var["entrada"], base["entrada"])
                self.assertEqual(var["origem"]["plano_base_sha256"], hash_json(base["plano"]))
                self.assertEqual(var["origem"]["plano_sha256"], hash_json(var["plano"]))
                self.assertEqual(var["origem"]["tipo"], "variante_controlada")
                self.assertEqual(set(var), {"plano", "entrada", "modelo_gerador", "revisao", "origem"})
            campos.add(s["campo"])
        self.assertEqual(len(campos), 4)

    def test_planos_distintos_entre_si_e_das_variantes_anteriores(self):
        hashes = [spec(p)["numero"] and carregar_caso(RAIZ / spec(p)["arquivo_caso"])["origem"]["plano_sha256"] for p in SPECS]
        anteriores = {"1b3bfddcee405c918e70d91faf1cd931419b71be84e5556885fe05b4dfec352d",   # original
                      "74a89df558601df64ba9fcb50f402f7f2fe80d3baf972fe94aa6c286287c5249",   # V01
                      "f98719c00248d16f95b26bfc138780ed0bf17c2eab5c3531a62c3a6b3de87c43"}   # V02
        self.assertEqual(len(set(hashes)), 4)
        self.assertFalse(set(hashes) & anteriores)

    def test_hipoteses_apontam_para_criterios_e_componentes_reais(self):
        for caminho in SPECS:
            s = spec(caminho)
            hip = s["hipotese"]
            with self.subTest(variante=s["numero"]):
                ids = lambda texto: set(re.findall(r"`([a-z_]+)`", texto))
                if s["numero"] == "V06":
                    self.assertTrue(hip["criterio_esperado"].startswith("Nenhum"))
                    continue
                self.assertTrue(ids(hip["criterio_esperado"]) <= set(contrato.CRITERIOS) and ids(hip["criterio_esperado"]))
                self.assertTrue(ids(hip["componente_esperado"]) <= set(ETAPAS) and ids(hip["componente_esperado"]))
                for ressalva in ids(hip.get("aceito_com_ressalva", "")):
                    self.assertIn(ressalva, set(contrato.CRITERIOS) | set(ETAPAS))

    def test_natureza_do_conjunto_nao_alega_holdout_de_plano(self):
        for caminho in SPECS:
            s = spec(caminho)
            with self.subTest(variante=s["numero"]):
                self.assertIn("não é holdout de plano", s["natureza_do_conjunto"]) if s["numero"] != "V06" else None
                self.assertNotIn("holdout de tipo", s["natureza_do_conjunto"])

    def test_protocolos_tem_hashes_valores_e_aviso_de_sigilo(self):
        for caminho in SPECS:
            s = spec(caminho)
            caso = carregar_caso(RAIZ / s["arquivo_caso"])
            texto = (RAIZ / s["arquivo_protocolo"]).read_text(encoding="utf-8")
            with self.subTest(variante=s["numero"]):
                for esperado in (caso["origem"]["plano_sha256"], caso["origem"]["plano_base_sha256"], hash_json(s["hipotese"]),
                                 s["valor_original"], s["valor_novo"], s["campo"], "não deve ser enviado à LLM",
                                 "Start-Sleep -Seconds 75", "--somente-validar", "A preencher depois das execuções"):
                    self.assertIn(esperado, texto)

    def test_caso_enviado_ao_juiz_nao_contem_hipotese_nem_identificacao_da_variante(self):
        """O Juiz só recebe plano e entrada; o gabarito e o rótulo da variante ficam fora da requisição."""
        recebido = []

        class Espiao:
            modelo = MODELO_PADRAO
            versao_esquema_api = "espiao"

            def executar(self, nome, entrada, estado, revisao, *, registro, reparo=None):
                recebido.append(json.dumps(dict(entrada=entrada, estado=estado, revisao=revisao), ensure_ascii=False))
                return deepcopy(PARECER_OK)

        for caminho in SPECS:
            s = spec(caminho)
            destino = Path(tempfile.mkdtemp())
            self.addCleanup(shutil.rmtree, destino, True)
            recebido.clear()
            executar_ensaio(RAIZ / s["arquivo_caso"], destino, fabrica=lambda **kw: Espiao())
            with self.subTest(variante=s["numero"]):
                self.assertEqual(len(recebido), 1)
                for segredo in (s["id_variante"], "variante_controlada", s["hipotese"]["principal"],
                                s["hipotese"]["criterio_esperado"], "hipotese", "pré-registro", "origem"):
                    self.assertNotIn(segredo, recebido[0])
                self.assertIn(s["valor_novo"], recebido[0])  # a manipulação, sim, chega ao Juiz
