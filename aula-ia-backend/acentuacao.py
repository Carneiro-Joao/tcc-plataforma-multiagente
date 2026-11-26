"""Detecção de texto gerado sem acentuação (achado de 25/11/2026).

Causa observada: quando um especialista responde sem acentos, os seguintes recebem essa saída como entrada e imitam o estilo
(efeito cascata; no plano de 25/11 16:01, 16 de 19 campos longos ficaram sem acento). O gerador detecta o problema logo na saída
de cada especialista e pede UMA reescrita com acentuação correta antes de passar ao próximo, interrompendo a cascata.

Critério (determinístico, `deteccao-acentuacao-1.2`):
- Campo SEM nenhum caractere acentuado, com mais de 60 caracteres: qualquer palavra que em português leva acento (ex.: "avaliacao",
  "nao", "sera", "pratica").
- Campo SEM nenhum caractere acentuado, curto (PoC 11, achado do lote de 25/11): só palavras inequívocas (-cao/-coes/-sao/-soes,
  "nao", "sera", "tambem"…), porque um título curto pode não ter acento nenhum e "pratica"/"analise" existem sem acento como verbo.
- Campo MISTO, de qualquer tamanho (1.2, execução real de 26/11: "metodologia" com "sera"/"demonstracao" sem acento e
  "ordenação"/"computação" com acento): palavra inequívoca sem acento, mesmo havendo outros acentos. A lista ampla não vale aqui.
A palavra-guia evita acusar frases que naturalmente não têm acento.
"""
import re
import unicodedata

VERSAO = "deteccao-acentuacao-1.2"  # 1.0 (PoC 10): só campos > 60; 1.1 (PoC 11): campos curtos; 1.2: campos mistos
ACENTOS = set("áàâãéêíóôõúç")
MINIMO_CARACTERES = 60
PALAVRA_QUE_LEVA_ACENTO = re.compile(
    r"\b(?:[a-z]+(?:cao|coes|sao|soes)|nao|sera|serao|ate|apos|tambem|voce|voces|entao|estao|sao|ja|numero|numeros|"
    r"pratica|praticas|teorica|teoricas|logica|codigo|codigos|conteudo|conteudos|sequencia|metodo|didatica|analise|"
    r"basico|basica|especifico|especificos|especifica|especificas)\b")
# Campos curtos (títulos de etapa, itens de conteúdo — achado do lote de 25/11, cenário 3: "Introducao ao Conceito…"): só palavras
# que NUNCA se escrevem sem acento. Ficam de fora as que existem sem acento como verbo ou nome ("pratica", "analise", "especifica",
# "sequencia", "ate", "sao", "ja"), para não pedir reescrita de título correto.
PALAVRA_INEQUIVOCA = re.compile(r"\b(?:[a-z]+(?:cao|coes|sao|soes)|nao|sera|serao|tambem|voce|voces|entao|estao)\b")


def _textos(valor, caminho=""):
    if isinstance(valor, str):
        yield caminho, valor
    elif isinstance(valor, dict):
        for k, v in valor.items():
            yield from _textos(v, f"{caminho}.{k}" if caminho else k)
    elif isinstance(valor, list):
        for i, v in enumerate(valor):
            yield from _textos(v, f"{caminho}[{i}]")


# Campos que são cópia exata do que o professor digitou: o validador exige igualdade, então reescrevê-los seria sempre descartado
# (auditoria de 25/11, C2).
CAMPOS_COPIADOS_DO_CONTEXTO = frozenset({"recursos"})


def campos_sem_acentuacao(saida):
    """Caminhos dos campos que parecem escritos sem acentuação (ignora os copiados do contexto).

    Campo longo (> 60 caracteres): nenhum acento + qualquer palavra-guia. Campo curto: nenhum acento + palavra inequívoca.
    Campo misto (qualquer tamanho, com algum acento): palavra inequívoca sem acento."""
    achados = []
    for caminho, texto in _textos(saida):
        if caminho in CAMPOS_COPIADOS_DO_CONTEXTO:
            continue
        minusculo = texto.lower()
        if set(minusculo) & ACENTOS:
            # 1.2: campo misto (tem acento em alguma palavra, mas "sera"/"demonstracao" sem) — só palavra inequívoca
            if PALAVRA_INEQUIVOCA.search(minusculo):
                achados.append(caminho)
            continue
        guia = PALAVRA_QUE_LEVA_ACENTO if len(texto) > MINIMO_CARACTERES else PALAVRA_INEQUIVOCA
        if guia.search(minusculo):
            achados.append(caminho)
    return achados


INSTRUCAO_REESCRITA = (
    "Os textos desta resposta foram escritos sem acentuação. Reescreva exatamente o mesmo conteúdo em português do Brasil com "
    "acentuação e cedilha corretas (por exemplo: avaliação, explicação, será, não, prática, sequência). Não mude o sentido, "
    "os IDs, os minutos, os vínculos nem a estrutura."
)


def _sem_acento(texto):
    return unicodedata.normalize("NFD", texto).encode("ascii", "ignore").decode("ascii")


def esqueleto(valor):
    """A saída sem os textos corridos: chaves, tamanhos de listas, IDs, números e valores curtos (sem acento).

    Auditoria 25/11, C1: a reescrita de acentuação só pode mexer nos textos. Strings com espaço são texto corrido e viram um marcador;
    strings sem espaço (IDs como "OBJ1", rótulos curtos) entram sem acentos, para que "Introducao" → "Introdução" não conte como mudança.
    """
    if isinstance(valor, dict):
        return {k: esqueleto(v) for k, v in valor.items()}
    if isinstance(valor, list):
        return [esqueleto(v) for v in valor]
    if isinstance(valor, str):
        return "<texto>" if any(c.isspace() for c in valor.strip()) else _sem_acento(valor)
    return valor


def mesma_estrutura(original, reescrita):
    """True se a reescrita só mudou textos corridos (ou acentos), mantendo IDs, minutos, vínculos e estrutura."""
    return esqueleto(original) == esqueleto(reescrita)
