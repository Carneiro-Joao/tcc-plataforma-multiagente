"""Adapta os diagnósticos do contrato existente ao pipeline e ao Gemini.

A validação é de contratos.validacao; este módulo não redefine suas regras.
"""
from copy import deepcopy
import json
from pathlib import Path
from contratos.validacao import VERSAO_CONTRATO, decodificar, validar as diagnosticar
from erros import ErroContrato

VERSAO = VERSAO_CONTRATO
SCHEMA = json.loads((Path(__file__).parent / "contratos.schema.json").read_text(encoding="utf-8"))


def esquema(nome):
    return deepcopy(SCHEMA["$defs"][nome])


def exigir_sem_erros(diagnosticos, mensagem):
    if diagnosticos:
        detalhes = [f"{d['caminho']}: {d['regra']}" for d in diagnosticos[:8]]
        erro = ErroContrato(mensagem + ": " + "; ".join(detalhes))
        erro.diagnosticos = deepcopy(diagnosticos)
        raise erro


def ler_json(texto):
    try:
        dados, diagnosticos = decodificar(texto)
    except RecursionError:
        raise ErroContrato("JSON excede a profundidade suportada.") from None
    exigir_sem_erros(diagnosticos, "JSON inválido")
    return dados


def validar(nome, saida, entrada):
    exigir_sem_erros(diagnosticar(nome, saida, entrada), f"Contrato {nome} inválido")


def integrar(entrada, estado):
    """Composição explícita: nenhuma chamada de IA, nenhum dict.update de saída."""
    for nome in ("objetivos", "metodologia", "sequencia", "avaliacao", "adaptacao"):
        validar(nome, estado[nome], entrada)
    c, h = entrada["contexto"], entrada["habilidade"]
    plano = {
        "titulo": f"Plano de aula — {c['tema']}",
        "habilidade_codigo": h["codigo"], "habilidade_texto": h["habilidade"],
        "ano": c["ano"], "tema": c["tema"], "duracao_min": c["duracao_min"], "tipo": c["tipo"],
        "objetivos": deepcopy(estado["objetivos"]["objetivos"]),
        "metodologia": estado["metodologia"]["metodologia"], "recursos": c["recursos"],
        "etapas": deepcopy(estado["sequencia"]["etapas"]),
        "avaliacao": estado["avaliacao"]["avaliacao"],
        "adaptacoes": deepcopy(estado["adaptacao"]["adaptacoes"]),
    }
    validar("plano", plano, entrada)
    return plano
