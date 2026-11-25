"""Detecção de texto gerado sem acentuação (achado de 25/11/2026).

Causa observada: quando um especialista responde sem acentos, os seguintes recebem essa saída como entrada e imitam o estilo
(efeito cascata; no plano de 25/11 16:01, 16 de 19 campos longos ficaram sem acento). O gerador detecta o problema logo na saída
de cada especialista e pede UMA reescrita com acentuação correta antes de passar ao próximo, interrompendo a cascata.

Critério (determinístico): campo de texto com mais de 60 caracteres, SEM nenhum caractere acentuado e com ao menos uma palavra que
em português leva acento (ex.: "avaliacao", "nao", "sera", "pratica"). A palavra-guia evita acusar frases que naturalmente não
têm acento.
"""
import re

ACENTOS = set("áàâãéêíóôõúç")
MINIMO_CARACTERES = 60
PALAVRA_QUE_LEVA_ACENTO = re.compile(
    r"\b(?:[a-z]+(?:cao|coes|sao|soes)|nao|sera|serao|ate|apos|tambem|voce|voces|entao|estao|sao|ja|numero|numeros|"
    r"pratica|praticas|teorica|teoricas|logica|codigo|codigos|conteudo|conteudos|sequencia|metodo|didatica|analise|"
    r"basico|basica|especifico|especificos|especifica|especificas)\b")


def _textos(valor, caminho=""):
    if isinstance(valor, str):
        yield caminho, valor
    elif isinstance(valor, dict):
        for k, v in valor.items():
            yield from _textos(v, f"{caminho}.{k}" if caminho else k)
    elif isinstance(valor, list):
        for i, v in enumerate(valor):
            yield from _textos(v, f"{caminho}[{i}]")


def campos_sem_acentuacao(saida):
    """Caminhos dos campos que parecem escritos sem acentuação."""
    achados = []
    for caminho, texto in _textos(saida):
        minusculo = texto.lower()
        if len(texto) > MINIMO_CARACTERES and not (set(minusculo) & ACENTOS) and PALAVRA_QUE_LEVA_ACENTO.search(minusculo):
            achados.append(caminho)
    return achados


INSTRUCAO_REESCRITA = (
    "Os textos desta resposta foram escritos sem acentuação. Reescreva exatamente o mesmo conteúdo em português do Brasil com "
    "acentuação e cedilha corretas (por exemplo: avaliação, explicação, será, não, prática, sequência). Não mude o sentido, "
    "os IDs, os minutos, os vínculos nem a estrutura."
)
