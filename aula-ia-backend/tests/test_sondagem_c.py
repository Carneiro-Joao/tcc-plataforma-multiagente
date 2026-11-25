"""Sondagem PoC 09 (sondagem_regeneracao_informada.py): injeção das críticas só no braço informado, métricas e teto. Sem rede."""
import json
from pathlib import Path
from unittest import TestCase

import juiz_servico
import sondagem_regeneracao_informada as s
from erros import ErroGeracao
from geracao_v2 import GeradorDePlanoCompleto
from test_gemini import CHAVE, Transporte, envelope

FIXTURE = json.loads((Path(__file__).parent / "dados/plano_v2/fixture_ordenacao.json").read_text(encoding="utf-8"))
PARECER = json.loads(juiz_servico.PARECER_DEMONSTRACAO.read_text(encoding="utf-8"))["parecer"]  # F1 maior em avaliacao_preliminar
ANTERIORES = {n: FIXTURE["saidas"][n] for n in s.plano_v2.ETAPAS}


def gerar(revisoes):
    base = Transporte([envelope(FIXTURE["saidas"][n]) for n in s.plano_v2.ETAPAS])
    agente = s.AgenteInformado(revisoes, chave=CHAVE, transporte=base)
    agente.transporte = s.transporte_informado(agente, base)
    resultado = GeradorDePlanoCompleto("ia", agente=agente, reparos=0).gerar(FIXTURE["entrada"], s.REVISAO)
    return base.pedidos, resultado


def dados_do_usuario(pedido):
    return json.loads(json.loads(pedido.data.decode("utf-8"))["contents"][0]["parts"][0]["text"])


def sistema(pedido):
    return json.loads(pedido.data.decode("utf-8"))["systemInstruction"]


class TestRevisaoPedagogica(TestCase):
    def test_cada_especialista_recebe_a_propria_versao_e_as_proprias_falhas(self):
        r = s.revisao_pedagogica("avaliacao_preliminar", ANTERIORES, PARECER)
        self.assertEqual(r["versao"], "revisao-informada-sondagem-0.1")
        self.assertEqual(r["versao_anterior"], FIXTURE["saidas"]["avaliacao_preliminar"])
        self.assertEqual([f["id"] for f in r["falhas_deste_componente"]], ["F1"])
        self.assertEqual(r["falhas_deste_componente"][0]["correcao_sugerida"], PARECER["falhas"][0]["correcao_sugerida"])
        self.assertEqual({f["id"] for f in r["outras_falhas"]}, {"F2", "F3"})
        self.assertIn("contexto.recursos", r["instrucao"])
        vazio = s.revisao_pedagogica("adaptacao", ANTERIORES, PARECER)
        self.assertEqual((vazio["falhas_deste_componente"], len(vazio["outras_falhas"])), ([], 3))


class TestInjecao(TestCase):
    def test_braco_cego_nao_recebe_revisao_e_informado_recebe_so_nos_dados(self):
        revisoes = {n: s.revisao_pedagogica(n, ANTERIORES, PARECER) for n in s.plano_v2.ETAPAS}
        cegos, r_cego = gerar({})
        informados, r_inf = gerar(revisoes)
        self.assertEqual(len(cegos), 6)
        self.assertEqual(len(informados), 6)
        for nome, cego, inf in zip(s.plano_v2.ETAPAS, cegos, informados):
            with self.subTest(nome=nome):
                self.assertNotIn("revisao_pedagogica", dados_do_usuario(cego))
                self.assertEqual(dados_do_usuario(inf)["revisao_pedagogica"], revisoes[nome])
                self.assertEqual(sistema(cego), sistema(inf))  # prompt de sistema e instruções inalterados
                d_c, d_i = dados_do_usuario(cego), dados_do_usuario(inf)
                d_i.pop("revisao_pedagogica")
                self.assertEqual(d_c, d_i)  # o resto dos dados é idêntico
                self.assertEqual({k.lower(): v for k, v in cego.header_items()}, {k.lower(): v for k, v in inf.header_items()})
                self.assertEqual((cego.full_url, cego.get_method()), (inf.full_url, inf.get_method()))
        self.assertEqual(r_cego["plano"], r_inf["plano"])
        registrados = [r for r in r_inf["rastreio"] if r.get("revisao_pedagogica")]
        self.assertEqual(len(registrados), 6)

    def test_especialista_sem_revisao_definida_nao_recebe_nada(self):
        pedidos, _ = gerar({"sequencia": s.revisao_pedagogica("sequencia", ANTERIORES, PARECER)})
        com = [n for n, p in zip(s.plano_v2.ETAPAS, pedidos) if "revisao_pedagogica" in dados_do_usuario(p)]
        self.assertEqual(com, ["sequencia"])


class TestMedidasETeto(TestCase):
    def test_graves_repetidas_e_medidas(self):
        plano, entrada = FIXTURE["plano_esperado"], FIXTURE["entrada"]
        m = s.medir(plano, PARECER, entrada, PARECER)
        self.assertEqual((m["graves"], m["graves_repetidas"], m["decisao"], m["contrato_ok"], m["minutos_ok"]),
                         (1, 1, "em_correcao", True, True))
        outro = json.loads(json.dumps(PARECER))
        outro["falhas"][0]["componente"] = "sequencia"
        self.assertEqual(s.medir(plano, outro, entrada, PARECER)["graves_repetidas"], 0)
        self.assertEqual(s.pares_graves(PARECER), {("avaliacao_preliminar", "avaliacao_aprendizagem")})

    def test_nova_tentativa_unica_com_pausa_e_teto(self):
        pausas, eventos, chamadas = [], [], []
        c = s.Contador()

        def falha():
            chamadas.append(1)
            raise ErroGeracao("Gemini HTTP 503", tipo="http")
        r, erros = s.com_nova_tentativa("x", falha, c, "geracoes", 14, pausas.append, eventos.append)
        self.assertEqual((r, len(erros), len(chamadas), pausas, c.geracoes), (None, 2, 2, [60], 2))
        respostas = iter([ErroGeracao("timeout", tipo="transporte"), "ok"])

        def falha_depois_ok():
            v = next(respostas)
            if isinstance(v, Exception):
                raise v
            return v
        r, _ = s.com_nova_tentativa("x", falha_depois_ok, c, "geracoes", 14, pausas.append, eventos.append)
        self.assertEqual((r, c.geracoes), ("ok", 4))
        c.geracoes = 14
        r, erros = s.com_nova_tentativa("x", lambda: "nunca", c, "geracoes", 14, pausas.append, eventos.append)
        self.assertEqual((r, c.geracoes), (None, 14))
        self.assertIn("teto", erros[0])

    def test_casos_sao_os_cinco_do_protocolo(self):
        protocolo = (Path(s.BASE).parent / "docs" / "PoC09_Sondagem_Regeneracao_Informada.md").read_text(encoding="utf-8")
        for caso in s.CASOS:
            self.assertIn(f"`{caso['geracao'][:8]}`", protocolo)
        self.assertEqual((s.TETO_GERACOES, s.TETO_AVALIACOES), (14, 14))
