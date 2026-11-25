"""Correções da auditoria de 25/11/2026 (C2, C3, C6, C7, C8). Sem rede. Execute a partir de aula-ia-backend."""
from contextlib import ExitStack
from copy import deepcopy
import io
import os
import json
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

import acentuacao
import app
from geracao_v2 import AgenteGeminiCompleto, GeradorDePlanoCompleto
from test_gemini import CHAVE, Transporte, envelope
from contratos import plano_v2

FIXTURE = json.loads((Path(__file__).parent / "dados/plano_v2/fixture_ordenacao.json").read_text(encoding="utf-8"))
RECURSOS_SEM_ACENTO = "quadro e pincel, material didatico impresso e fichas com a sequencia numerica para pratica em duplas"


class TestC2RecursosNaoDisparamReescrita(TestCase):
    """C2: `recursos` é cópia exata do que o professor digitou; reescrevê-lo seria sempre descartado pelo validador."""

    def test_detector_ignora_recursos_e_continua_vendo_os_outros_campos(self):
        saida = {"metodologia": "A explicacao do professor ocorre durante a atividade de comparacao dos grupos.",
                 "recursos": RECURSOS_SEM_ACENTO}
        self.assertEqual(acentuacao.campos_sem_acentuacao(saida), ["metodologia"])
        self.assertEqual(acentuacao.campos_sem_acentuacao({"recursos": RECURSOS_SEM_ACENTO}), [])
        # só a chave exata "recursos" é ignorada; outro campo com o mesmo texto continua detectado
        self.assertEqual(acentuacao.campos_sem_acentuacao({"recursos_extras": RECURSOS_SEM_ACENTO}), ["recursos_extras"])
        self.assertEqual(acentuacao.campos_sem_acentuacao({"outros_recursos": RECURSOS_SEM_ACENTO}), ["outros_recursos"])

    def test_gerador_nao_faz_chamada_extra_por_recursos_digitados_sem_acento(self):
        entrada = deepcopy(FIXTURE["entrada"])
        entrada["contexto"]["recursos"] = RECURSOS_SEM_ACENTO
        saidas = deepcopy(FIXTURE["saidas"])
        saidas["metodologia"]["recursos"] = RECURSOS_SEM_ACENTO
        transporte = Transporte([envelope(saidas[n]) for n in plano_v2.ETAPAS])
        agente = AgenteGeminiCompleto(chave=CHAVE, transporte=transporte, repeticoes_503=0)
        resultado = GeradorDePlanoCompleto("ia", agente=agente, reparos=1).gerar(entrada, 1)
        self.assertEqual(len(transporte.pedidos), 6)
        self.assertEqual(resultado["plano"]["recursos"], RECURSOS_SEM_ACENTO)
        self.assertFalse([r for r in resultado["rastreio"] if r.get("tentativa") == "acentuacao"])


class TestC3MensagemDoLimiteDeRequisicoes(TestCase):
    """C3: o teto mostrado ao iniciar tem de contar a reescrita de acentuação (1 chamada por especialista, com as mesmas repetições)."""

    def test_conta_reparo_e_reescrita_por_especialista(self):
        self.assertEqual(app.limites_de_requisicoes(reparos=1, repeticoes_503=2), (18, 54))
        self.assertEqual(app.limites_de_requisicoes(reparos=0, repeticoes_503=0), (12, 12))
        self.assertEqual(app.limites_de_requisicoes(reparos=1, repeticoes_503=0), (18, 18))
        self.assertEqual(app.limites_de_requisicoes(reparos=0, repeticoes_503=2), (12, 36))

    def _iniciar(self, argv):
        with ExitStack() as ctx:
            ctx.enter_context(patch.dict(os.environ, {"GEMINI_API_KEY": "chave-ficticia-do-teste"}, clear=True))
            saida = ctx.enter_context(patch("sys.stdout", new_callable=io.StringIO))
            servico = ctx.enter_context(patch("app.ServicoCurricular"))
            servico.return_value.uso_hoje.return_value = (0, 8)
            servidor = ctx.enter_context(patch("app.ThreadingHTTPServer")).return_value
            servidor.server_port = 8000
            servidor.serve_forever.side_effect = KeyboardInterrupt()
            app.main(argv)
            return saida.getvalue()

    def test_mensagem_ao_iniciar_usa_o_teto_com_acentuacao(self):
        texto = self._iniciar(["--gerador", "ia"])
        self.assertIn("até 18 com reparos e reescritas de acentuação", texto)
        self.assertIn("54 requisições", texto)
        texto = self._iniciar(["--gerador", "ia", "--reparos", "0", "--repeticoes-503", "0"])
        self.assertIn("até 12 com reparos e reescritas de acentuação", texto)
        self.assertIn("12 requisições", texto)


class TestC6SemPadraoDeChaveNosArquivos(TestCase):
    """C6: nenhum arquivo de teste contém o padrão literal de uma chave (as falsas são montadas em tempo de execução)."""

    def test_testes_sem_padrao_literal_de_chave(self):
        import re
        padrao = re.compile("AI" + r"za[0-9A-Za-z_-]{20,}|" + "gs" + r"k_[0-9A-Za-z_-]{10,}")
        raiz = Path(__file__).resolve().parents[2]
        achados = [str(f.relative_to(raiz)) for pasta in ("aula-ia-backend/tests", "aula-ia/tests") for f in (raiz / pasta).rglob("*")
                   if f.suffix in (".py", ".mjs", ".js", ".json") and padrao.search(f.read_text(encoding="utf-8", errors="ignore"))]
        self.assertEqual(achados, [])
