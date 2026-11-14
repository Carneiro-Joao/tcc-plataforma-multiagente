"""Contratos mecânicos PoC 04A. Não avaliam adequação pedagógica."""
from copy import deepcopy
import json
from pathlib import Path
from jsonschema import Draft202012Validator, validators
from erros import ErroContrato

SCHEMA = json.loads((Path(__file__).parent / "contratos" / "contratos.schema.json").read_text(encoding="utf-8"))
VERSAO = "poc04a-0.1"
# JSON Schema considera 5.0 inteiro; o contrato Python exige int, sem bool/coerção.
Validador = validators.extend(Draft202012Validator, type_checker=Draft202012Validator.TYPE_CHECKER.redefine(
    "integer", lambda _, valor: type(valor) is int))
VALIDADORES = {nome: Validador(s) for nome, s in SCHEMA["$defs"].items()}


def esquema(nome):
    return deepcopy(SCHEMA["$defs"][nome])


def ler_json(texto):
    def pares(itens):
        saida = {}
        for chave, valor in itens:
            if chave in saida:
                raise ValueError("chave duplicada")
            saida[chave] = valor
        return saida

    def constante(_):
        raise ValueError("constante não JSON")

    try:
        return json.loads(texto, object_pairs_hook=pares, parse_constant=constante)
    except (ValueError, TypeError, RecursionError):
        raise ErroContrato("JSON inválido: envie somente JSON, sem cercas Markdown, chaves duplicadas ou NaN/Infinity.") from None


def validar(nome, saida, entrada):
    falhas = list(VALIDADORES[nome].iter_errors(saida))
    if falhas:
        # Não ecoar valores gerados ou dados sensíveis na mensagem pública.
        detalhes = [f"{'/'.join(map(str, e.absolute_path)) or '$'}: regra {e.validator}" for e in falhas[:8]]
        raise ErroContrato(f"Contrato {nome} inválido: " + "; ".join(detalhes))
    c, h = entrada["contexto"], entrada["habilidade"]
    if nome in ("sequencia", "plano") and sum(e["minutos"] for e in saida["etapas"]) != c["duracao_min"]:
        raise ErroContrato(f"Contrato {nome}: a soma dos minutos deve ser {c['duracao_min']}.")
    if nome in ("metodologia", "plano") and saida["recursos"] != c["recursos"]:
        raise ErroContrato(f"Contrato {nome}: recursos deve reproduzir exatamente contexto.recursos.")
    if nome == "plano":
        imutaveis = {k: c[k] for k in ("ano", "tema", "duracao_min", "tipo")}
        imutaveis.update(habilidade_codigo=h["codigo"], habilidade_texto=h["habilidade"],
                         titulo=f"Plano de aula — {c['tema']}")
        for k, valor in imutaveis.items():
            if type(saida[k]) is not type(valor) or saida[k] != valor:
                raise ErroContrato(f"Contrato plano: {k} diverge da entrada confirmada.")


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
