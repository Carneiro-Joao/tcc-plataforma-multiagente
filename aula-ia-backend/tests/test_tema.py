"""Extração do tema curto (tema.py) e sua integração em ServicoCurricular.consultar. Execute a partir de aula-ia-backend."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from rag.search import BuscaCurricular
from rag.termos import TERMOS
from servico import ErroConsulta, ServicoCurricular
from tema import TemaNaoIdentificado, extrair_tema, normalizar_com_mapa

BUSCA = BuscaCurricular()
VOCAB = [t for v in TERMOS.values() for t in v] + [d["objeto_conhecimento"] for d in BUSCA.documentos]

# (o que o professor digitou, tema esperado). Frases no estilo de quem escreve rápido num formulário.
CASOS = [
    ("Olá, bom dia, quero ensinar sobre ordenação", "Ordenação"),
    ("Olá, eu quero ensinar sobre IA generativa. O tema da aula de hoje vai ser IA generativa. E não sei o que, não sei o que.",
     "IA generativa"),
    ("o tema da aula de hoje vai ser ensinar sobre ordenação", "Ordenação"),
    ("gostaria de uma aula sobre bubble sort e merge sort com cartões, 50 minutos", "Bubble sort e merge sort"),
    ("quero ensinar sobre privacidade de dados pessoais", "Privacidade de dados pessoais"),
    ("ordenação", "Ordenação"),
    ("Ordenação.", "Ordenação"),
    ("na aula de hoje vamos falar de redes sociais", "Redes sociais"),
    ("quero ensinar sobre o funcionamento da internet para o 8º ano", "Funcionamento da internet"),
    ("tema: recursão", "Recursão"),
    ("Boa tarde! Hoje o assunto é inteligência artificial generativa, mas não sei como começar", "Inteligência artificial generativa"),
    ("quero trabalhar fake news com os alunos", "Fake news"),
    ("quero ensinar algoritmos de ordenação usando baralho", "Algoritmos de ordenação"),
    # achados na sondagem com frases novas (18/11/2026)
    ("oi, tudo bem? vou dar uma aula de segurança digital amanhã", "Segurança digital"),
    ("Quero uma aula prática sobre como funciona o ChatGPT", "Como funciona o ChatGPT"),
    ("Preciso de um plano sobre pensamento computacional para o 8 ano", "Pensamento computacional"),
    ("Hoje eu quero ensinar para os meus alunos o que são algoritmos", "Algoritmos"),
    ("Ensinar listas e pilhas", "Listas e pilhas"),
    ("aula de lógica de programação com scratch", "Lógica de programação"),
    ("tema da aula: cyberbullying", "Cyberbullying"),
]


class TestExtrairTema(TestCase):
    def tema(self, texto):
        return extrair_tema(texto, VOCAB)["tema"]

    def test_tabela_de_frases_reais(self):
        for texto, esperado in CASOS:
            with self.subTest(texto=texto[:50]):
                self.assertEqual(self.tema(texto), esperado)

    def test_origem_registrada(self):
        self.assertEqual(extrair_tema("quero ensinar sobre ordenação", VOCAB)["origem"], "catalogo")
        self.assertEqual(extrair_tema("o tema é IA generativa", VOCAB)["origem"], "marcador")
        self.assertEqual(extrair_tema("Computação quântica", VOCAB)["origem"], "texto")

    def test_mantem_acento_e_sigla_digitados(self):
        self.assertEqual(self.tema("quero ensinar sobre ordenação"), "Ordenação")
        self.assertEqual(self.tema("tema: IA generativa"), "IA generativa")

    def test_palavra_inteira_nao_casa_no_meio_de_outra(self):
        # "rede" (termo do catálogo) não pode aparecer dentro de "credenciais" nem "parede".
        self.assertNotIn("rede", self.tema("credenciais").lower().replace("credenciais", ""))
        self.assertEqual(extrair_tema("quero ensinar sobre parede", ["rede"])["origem"], "marcador")
        self.assertEqual(self.tema("parede"), "Parede")

    def test_termo_mais_longo_vence_o_contido_nele(self):
        self.assertEqual(extrair_tema("aula sobre merge sort", ["sort", "merge sort"])["tema"], "Merge sort")

    def test_no_maximo_tres_trechos_separados(self):
        t = extrair_tema("ordenação é difícil; depois recursão; mais tarde listas; por fim pilha",
                         ["ordenacao", "recursao", "listas", "pilha"])["tema"]
        self.assertEqual(t, "Ordenação, recursão e listas")

    def test_termos_vizinhos_saem_como_um_trecho_so(self):
        t = extrair_tema("ordenação, recursão, listas e pilha", ["ordenacao", "recursao", "listas", "pilha"])["tema"]
        self.assertEqual(t, "Ordenação, recursão, listas e pilha")

    def test_trecho_repetido_aparece_uma_vez(self):
        self.assertEqual(extrair_tema("ordenação é legal. Mais tarde volto a ordenação", ["ordenacao"])["tema"], "Ordenação")

    def test_sem_assunto_pede_reescrita(self):
        for texto in ("Olá, bom dia", "quero ensinar", "Olá, quero ensinar sobre", "   ", "oi!", "preciso de uma aula",
                      "oi, tudo bem? quero um plano de aula", "quero ensinar para os alunos",
                      "plano de aula", "uma aula", "uma oficina", "atividade para a turma",
                      "quero ensinar para os alunos do 8º ano coisas legais"):
            with self.subTest(texto=texto), self.assertRaises(TemaNaoIdentificado):
                extrair_tema(texto, VOCAB)

    def test_texto_nao_textual_e_recusado(self):
        for valor in (None, 5, ["ordenação"]):
            with self.assertRaises(TemaNaoIdentificado):
                extrair_tema(valor, VOCAB)

    def test_texto_longo_sem_pista_e_recusado(self):
        with self.assertRaises(TemaNaoIdentificado):
            extrair_tema("palavra " * 30, VOCAB)

    def test_nunca_passa_de_80_caracteres(self):
        with self.assertRaises(TemaNaoIdentificado):
            extrair_tema("o tema é " + "x" * 81, VOCAB)
        self.assertEqual(len(self.tema("o tema é " + "x" * 80)), 80)
        # trecho longo vindo do catálogo também é recusado
        with self.assertRaises(TemaNaoIdentificado):
            extrair_tema("ordenação, recursão, listas, pilha, ordenação, recursão, listas, pilha, ordenação, recursão",
                         ["ordenacao", "recursao", "listas", "pilha"])

    def test_palavra_inteira_tambem_no_fim(self):
        self.assertEqual(extrair_tema("redes", ["rede"])["tema"], "Redes")
        self.assertEqual(extrair_tema("ordenarmos", ["ordenar"])["origem"], "texto")

    def test_termo_mais_longo_vence_sem_ajuda_do_marcador(self):
        self.assertEqual(extrair_tema("merge sort", ["sort", "merge sort"])["tema"], "Merge sort")

    def test_traco_separado_corta_o_tema_fora_do_catalogo(self):
        self.assertEqual(self.tema("o tema é computação quântica - 50 minutos"), "Computação quântica")

    def test_saudacao_com_interrogacao_e_removida_do_texto_curto(self):
        self.assertEqual(self.tema("tudo bem? computação quântica"), "Computação quântica")

    def test_assunto_de_uma_letra_nao_vira_tema(self):
        self.assertNotEqual(self.tema("o tema é x"), "X")

    def test_nada_e_inventado_so_palavras_do_texto_digitado(self):
        for texto, _ in CASOS:
            palavras = set(normalizar_com_mapa(texto)[0].replace(",", " ").replace(".", " ").split())
            for p in normalizar_com_mapa(self.tema(texto))[0].replace(",", " ").split():
                self.assertIn(p, palavras | {"e"}, (texto, p))

    def test_termos_ligados_por_de_mantem_a_grafia_do_professor(self):
        self.assertEqual(extrair_tema("aula sobre privacidade de dados pessoais", ["privacidade", "dados pessoais"])["tema"],
                         "Privacidade de dados pessoais")

    def test_termos_separados_sao_unidos_com_e(self):
        t = extrair_tema("ordenação é difícil; depois falo de recursão", ["ordenacao", "recursao"])["tema"]
        self.assertEqual(t, "Ordenação e recursão")


class TestIntegracaoServico(TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.servico = ServicoCurricular(BuscaCurricular(), Path(temp.name) / "t.sqlite3")

    def consultar(self, tema, modo="tema"):
        ctx = dict(ano="8º ano", tema=tema, duracao_min=50, recursos="papel e cartões", tipo="Computação desplugada")
        return self.servico.consultar({"contexto": ctx, "consulta": modo})

    def test_contexto_guarda_so_o_tema_e_o_original_fica_a_parte(self):
        frase = "Olá, bom dia, quero ensinar sobre ordenação"
        c = self.consultar(frase)
        self.assertEqual(c["contexto"]["tema"], "Ordenação")
        self.assertEqual(c["pedido_original"], frase)
        self.assertEqual(c["origem_tema"], "catalogo")
        self.assertEqual(set(c["contexto"]), {"ano", "tema", "duracao_min", "recursos", "tipo"})

    def test_frase_com_termo_traz_a_habilidade_certa(self):
        c = self.consultar("gostaria de uma aula sobre bubble sort com cartões")
        self.assertEqual(c["resultados"][0]["habilidade"]["codigo"], "EF08CO03")

    def test_busca_recebe_o_tema_curto_e_nao_a_frase_inteira(self):
        with patch.object(self.servico.busca, "buscar", wraps=self.servico.busca.buscar) as busca:
            self.consultar("Olá, bom dia, quero ensinar sobre ordenação")
        busca.assert_called_once_with("Ordenação")

    def test_frase_com_ruido_nao_traz_habilidade_errada(self):
        # Fora do catálogo (a BNCC do 8º ano não tem IA generativa): resultado vazio, e não habilidades por acaso.
        frase = "Olá, eu quero ensinar sobre IA generativa. O tema da aula de hoje vai ser IA generativa. E não sei o que"
        self.assertEqual(BUSCA.buscar(frase) != [], True)  # a frase inteira, como era antes, trazia falsos positivos
        c = self.consultar(frase)
        self.assertEqual(c["contexto"]["tema"], "IA generativa")
        self.assertEqual(c["resultados"], [])

    def test_objeto_de_conhecimento_da_bncc_entra_no_vocabulario(self):
        objeto = BUSCA.documentos[0]["objeto_conhecimento"]
        c = self.consultar(f"quero que a aula seja assim: {objeto}, 50 minutos")
        self.assertEqual(c["contexto"]["tema"], objeto)
        self.assertEqual(c["origem_tema"], "catalogo")

    def test_tema_sem_assunto_vira_erro_422_com_mensagem_util(self):
        with self.assertRaises(ErroConsulta) as e:
            self.consultar("Olá, bom dia")
        self.assertEqual(e.exception.status, 422)
        self.assertIn("poucas palavras", str(e.exception))

    def test_nada_e_gravado_quando_o_tema_e_recusado(self):
        with self.assertRaises(ErroConsulta):
            self.consultar("Olá, bom dia")
        import sqlite3
        with sqlite3.connect(self.servico.banco) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM consultas").fetchone()[0], 0)

    def test_modo_catalogo_tambem_normaliza_o_tema(self):
        c = self.consultar("o tema da aula de hoje vai ser ensinar sobre ordenação", modo="catalogo")
        self.assertEqual(c["contexto"]["tema"], "Ordenação")

    def test_titulo_do_plano_usa_o_tema_curto(self):
        c = self.consultar("Olá, quero ensinar sobre ordenação")
        cod = c["resultados"][0]["habilidade"]["codigo"]
        self.servico.confirmar(c["id"], cod) if hasattr(self.servico, "confirmar") else None
        self.assertEqual(self.servico.obter(c["id"])["contexto"]["tema"], "Ordenação")
