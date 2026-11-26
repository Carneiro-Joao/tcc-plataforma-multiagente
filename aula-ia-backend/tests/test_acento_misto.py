"""deteccao-acentuacao-1.2: campo misto (algumas palavras com acento, outras inequívocas sem). Achado da execução real de 26/11:
o campo "metodologia" (especialista `metodologia`) veio com "sera"/"demonstracao" sem acento e "ordenação"/"computação" com acento,
e a 1.1 não detectava porque ignorava todo campo com qualquer acento. Sem rede."""
from copy import deepcopy
from unittest import TestCase

import acentuacao
from test_gemini import envelope
from test_poc10 import SAIDAS, dados, gerar, normais

TRECHO_REAL = ("A aula sera desenvolvida por meio de exposicao oral dialogada e demonstracao pratica no quadro. "
               "Inicialmente, o professor apresentará o conceito de ordenação…")
TRECHO_CORRETO = ("A aula será desenvolvida por meio de exposição oral dialogada e demonstração prática no quadro. "
                  "Inicialmente, o professor não apresentará só o conceito de ordenação.")

METODOLOGIA_MISTA = deepcopy(SAIDAS["metodologia"])
METODOLOGIA_MISTA["metodologia"] = METODOLOGIA_MISTA["metodologia"].replace("com demonstração orientada", "com demonstracao orientada")


class TestCampoMisto(TestCase):
    def test_trecho_da_execucao_real_e_detectado(self):
        self.assertEqual(acentuacao.campos_sem_acentuacao({"metodologia": TRECHO_REAL}), ["metodologia"])

    def test_texto_correto_nao_e_detectado(self):
        self.assertEqual(acentuacao.campos_sem_acentuacao({"metodologia": TRECHO_CORRETO}), [])
        self.assertEqual(acentuacao.campos_sem_acentuacao(SAIDAS["metodologia"]), [])

    def test_misto_so_com_palavra_ambigua_nao_conta(self):
        # "pratica", "analise", "ate", "sao", "ja" ficam fora da regra do campo misto (falso positivo)
        self.assertEqual(acentuacao.campos_sem_acentuacao(
            {"t": "O aluno pratica a análise até o fim; sao exemplos já vistos."}), [])

    def test_misto_curto_tambem_conta(self):
        self.assertEqual(acentuacao.campos_sem_acentuacao({"t": "Revisão da explicacao"}), ["t"])

    def test_recursos_continua_ignorado(self):
        self.assertEqual(acentuacao.campos_sem_acentuacao({"recursos": "projeção e explicacao"}), [])
        self.assertEqual(acentuacao.VERSAO, "deteccao-acentuacao-1.2")

    def test_reescrita_de_campo_misto_e_aceita_no_gerador(self):
        # "acento melhorou" = menos campos acusados; não depende de o original não ter acento nenhum
        depois = [envelope(SAIDAS[n]) for n in ("sequencia", "avaliacao_final", "adaptacao")]
        resultado, t = gerar(normais("metodologia") + [envelope(METODOLOGIA_MISTA), envelope(SAIDAS["metodologia"])] + depois)
        self.assertEqual(len(t.pedidos), 7)
        self.assertEqual(dados(t.pedidos[3])["reparo_estrutural"]["diagnosticos"], [{"caminho": "metodologia", "regra": "sem_acentuacao"}])
        self.assertEqual(resultado["plano"]["metodologia"], SAIDAS["metodologia"]["metodologia"])
        reg = [r for r in resultado["rastreio"] if r.get("tentativa") == "acentuacao"]
        self.assertEqual([(r["agente"], r["estado"], r["campos_sem_acentuacao_antes"], r["campos_sem_acentuacao_depois"]) for r in reg],
                         [("metodologia", "validado", ["metodologia"], [])])
