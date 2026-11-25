"""Intervalo mínimo entre chamadas reais ao Juiz (Groq: 8.000 tokens/min; ~6–7 mil por avaliação). Relógio e sono falsos, sem rede.
Execute a partir de aula-ia-backend."""
from contextlib import closing
from copy import deepcopy
import json
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import threading
from unittest import TestCase

import juiz_servico
from erros import ErroContrato, ErroGeracao
from rag.search import BuscaCurricular
from servico import ServicoCurricular

FIXTURE = json.loads((Path(__file__).parent / "dados/plano_v2/fixture_ordenacao.json").read_text(encoding="utf-8"))
GRAVADO = json.loads(juiz_servico.PARECER_DEMONSTRACAO.read_text(encoding="utf-8"))["parecer"]  # em_correcao (1 falha maior)
FAVORAVEL = deepcopy(GRAVADO)
FAVORAVEL["falhas"] = [f for f in FAVORAVEL["falhas"] if f["gravidade"] == "menor"]
for _a in FAVORAVEL["avaliacoes"]:
    _a["nota"] = 3
DURACAO_CHAMADA = 7


class Relogio:
    """Relógio falso: dormir avança o tempo; a chamada ao Groq leva DURACAO_CHAMADA segundos."""
    def __init__(self):
        self.t, self.sonos, self.juiz = 1000.0, [], None

    def agora(self):
        if self.juiz is not None:  # o instante só é lido com o lock na mão (ThreadingHTTPServer)
            assert self.juiz._trava.locked(), "relógio lido fora do lock"
        return self.t

    def dormir(self, s):
        self.sonos.append(round(s, 6))
        self.t += s


class AgenteFalso:
    """Imita o AgenteGroqJuiz: registra o instante de início de cada chamada HTTP e consome o roteiro."""
    modelo, versao_prompt, versao_esquema_api = "openai/gpt-oss-120b", "juiz-v1.3", "teste"

    def __init__(self, relogio, roteiro):
        self.relogio, self.roteiro, self.inicios = relogio, list(roteiro), []
        self._trava = threading.Lock()

    def executar(self, nome, entrada, estado, revisao, *, registro, reparo=None):
        with self._trava:
            self.inicios.append(self.relogio.t)
            self.relogio.t += DURACAO_CHAMADA
            passo = self.roteiro.pop(0) if self.roteiro else "ok"
        if passo == "contrato":
            raise ErroContrato("Groq rejeitou o parecer gerado por incompatibilidade com o JSON Schema.")
        if isinstance(passo, Exception):
            raise passo
        return deepcopy(FAVORAVEL if passo == "favoravel" else GRAVADO)


def juiz_com(relogio, roteiro=(), verificar_lock=True):
    agente = AgenteFalso(relogio, roteiro)
    juiz = juiz_servico.JuizGroq(agente=agente, dormir=relogio.dormir, relogio=relogio.agora)
    if verificar_lock:
        relogio.juiz = juiz
    return juiz, agente


def avaliar(juiz, avisos=None):
    return juiz.avaliar(FIXTURE["plano_esperado"], FIXTURE["entrada"], modelo_gerador="g", revisao=1, ciclo=0,
                        ao_esperar=None if avisos is None else avisos.append)


class TestIntervaloEntreChamadas(TestCase):
    def test_constantes(self):
        self.assertEqual((juiz_servico.INTERVALO_MINIMO_S, juiz_servico.INTERVALO_APOS_413_S, juiz_servico.PAUSA_ANTES_DO_REPARO_S),
                         (75, 120, 60))
        self.assertEqual((juiz_servico.REPAROS, juiz_servico.PARAMETROS_EXPERIMENTOS["versao_prompt"]), (1, "juiz-v1.3"))

    def test_primeira_chamada_nunca_espera(self):
        r = Relogio()
        juiz, agente = juiz_com(r)
        avisos = []
        avaliar(juiz, avisos)
        self.assertEqual((r.sonos, avisos, agente.inicios), ([], [], [1000.0]))

    def test_duas_avaliacoes_seguidas_esperam_o_que_falta_desde_o_inicio_da_anterior(self):
        r = Relogio()
        juiz, agente = juiz_com(r)
        avaliar(juiz)
        r.t += 40  # a regeneração do plano leva ~40 s
        avisos = []
        avaliar(juiz, avisos)
        self.assertEqual(r.sonos, [28])  # 75 - (7 da chamada + 40 da regeneração)
        self.assertEqual(avisos, [28, 0])  # avisa a tela antes de esperar e quando a espera termina
        self.assertEqual(agente.inicios, [1000.0, 1075.0])

    def test_depois_de_75_s_do_inicio_nao_espera(self):
        r = Relogio()
        juiz, agente = juiz_com(r)
        avaliar(juiz)
        r.t = 1075.0
        avisos = []
        avaliar(juiz, avisos)
        self.assertEqual((r.sonos, avisos), ([], []))

    def test_reparo_continua_esperando_60_s_e_conta_como_ultima_chamada(self):
        r = Relogio()
        juiz, agente = juiz_com(r, ["contrato", "ok"])
        avaliar(juiz)
        self.assertEqual(r.sonos, [60])
        self.assertEqual(agente.inicios, [1000.0, 1067.0])  # 7 s da 1ª chamada + 60 s de pausa
        avaliar(juiz)  # logo depois: espera 75 s contados do início do REPARO
        self.assertEqual(r.sonos, [60, 68])
        self.assertEqual(agente.inicios[-1], 1142.0)

    def test_depois_de_413_espera_120_s(self):
        r = Relogio()
        juiz, agente = juiz_com(r, [ErroGeracao("Groq HTTP 413: Payload Too Large", tipo="http")])
        with self.assertRaises(ErroGeracao):
            avaliar(juiz)
        avaliar(juiz)
        self.assertEqual(r.sonos, [113])  # 120 - 7
        avaliar(juiz)
        self.assertEqual(r.sonos[-1], 75 - DURACAO_CHAMADA)  # sem novo 413, volta a 75

    def test_outra_falha_mantem_75_s(self):
        r = Relogio()
        juiz, _ = juiz_com(r, [ErroGeracao("Groq HTTP 429: limite", tipo="http")])
        with self.assertRaises(ErroGeracao):
            avaliar(juiz)
        avaliar(juiz)
        self.assertEqual(r.sonos, [68])

    def test_duas_threads_ao_mesmo_tempo_ficam_separadas_por_75_s(self):
        r = Relogio()
        juiz, agente = juiz_com(r, verificar_lock=False)
        barreira = threading.Barrier(2)

        def tarefa():
            barreira.wait()
            avaliar(juiz)
        threads = [threading.Thread(target=tarefa) for _ in range(2)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(10)
        a, b = sorted(agente.inicios)
        self.assertGreaterEqual(b - a, 75)

    def test_demonstracao_nunca_espera_nem_avisa(self):
        avisos = []
        juiz = juiz_servico.JuizDemonstracao()
        for _ in range(2):
            juiz.avaliar(FIXTURE["plano_esperado"], FIXTURE["entrada"], modelo_gerador="g", revisao=1, ciclo=0,
                         ao_esperar=avisos.append)
        self.assertEqual(avisos, [])


class GeradorFalso:
    modo, modelo, VERSAO_CONTRATO = "ia", "gemini-falso", "plano-aula-2.0"

    def __init__(self, relogio):
        self.relogio = relogio

    def gerar(self, entrada, revisao, revisoes=None):
        self.relogio.t += 40
        return dict(plano=deepcopy(FIXTURE["plano_esperado"]), modo="ia", modelo=self.modelo, contrato="plano-aula-2.0", rastreio=[])


class TestTelaDuranteAEspera(TestCase):
    def test_pedido_fica_aguardando_juiz_durante_a_espera_e_termina_pronto(self):
        with TemporaryDirectory() as d:
            banco = Path(d) / "t.sqlite3"
            r = Relogio()
            agente = AgenteFalso(r, ["ok", "favoravel"])  # 1ª versão em_correcao → regenera → favorável
            vistos = []
            servico = {}

            def dormir(s):
                vistos.append(servico["s"].obter(servico["cid"])["pedido_atual"])
                r.dormir(s)
            juiz = juiz_servico.JuizGroq(agente=agente, dormir=dormir, relogio=lambda: r.t)
            s = ServicoCurricular(BuscaCurricular(), banco, GeradorFalso(r), juiz=juiz, ciclos_juiz=1)
            c = s.consultar({"contexto": dict(FIXTURE["entrada"]["contexto"]), "consulta": "tema"})
            s.confirmar(c["id"], FIXTURE["entrada"]["habilidade"]["codigo"])
            servico.update(s=s, cid=c["id"])
            final = s.gerar(c["id"])
            self.assertEqual(r.sonos, [28])  # 2ª avaliação veio 47 s depois do início da 1ª
            self.assertEqual([(v["estado"], v["ciclo"], v["em_andamento"]) for v in vistos], [("aguardando_juiz", 1, True)])
            self.assertEqual((final["pedido_atual"]["estado"], final["geracao_atual"]["avaliacao"]["rotulo"]), ("pronto", "Favorável"))
            with closing(sqlite3.connect(banco)) as db:
                self.assertEqual(db.execute("SELECT COUNT(*) FROM pareceres WHERE estado = 'ok'").fetchone()[0], 2)
