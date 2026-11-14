"""Validação dos contratos candidatos da PoC 04A (versão poc04a-0.1), em Python puro.

Não usa biblioteca externa nem chama API. Cada função devolve uma LISTA DE
DIAGNÓSTICOS (vazia = válido); nunca corrige, converte nem descarta dados.

Cada diagnóstico é um dict com `caminho` e `regra` e, quando útil, `esperado`
e `recebido`. Regras: tipo_invalido, campo_ausente, campo_extra, texto_vazio,
quantidade_invalida, minimo, soma_duracao, recursos_confirmados,
entrada_preservada e, na decodificação, json_invalido, chave_duplicada,
constante_nao_finita e raiz_nao_objeto.

Escopo: estrutura, tipos e consistência mecânica. Não avalia qualidade
pedagógica (isso é papel da IA Juiz e do professor).
"""
import json

VERSAO_CONTRATO = "poc04a-0.1"
CONTRATOS = ("objetivos", "metodologia", "sequencia", "avaliacao", "adaptacao", "plano")

_CAMPOS_PLANO = ("titulo", "habilidade_codigo", "habilidade_texto", "ano", "tema", "duracao_min",
                 "tipo", "objetivos", "metodologia", "recursos", "etapas", "avaliacao", "adaptacoes")
_CAMPOS_ETAPA = ("etapa", "minutos", "atividade")


# ---------------------------------------------------------------- utilitários

def _d(caminho, regra, esperado=None, recebido=None):
    diag = {"caminho": caminho, "regra": regra}
    if esperado is not None:
        diag["esperado"] = esperado
    if recebido is not None:
        diag["recebido"] = recebido
    return diag


def _tipo(valor):
    """Nome do tipo JSON. bool é separado de integer (True nunca vale como número)."""
    if valor is None:
        return "null"
    if isinstance(valor, bool):
        return "boolean"
    if isinstance(valor, int):
        return "integer"
    if isinstance(valor, float):
        return "number"
    if isinstance(valor, str):
        return "string"
    if isinstance(valor, list):
        return "array"
    if isinstance(valor, dict):
        return "object"
    return type(valor).__name__


def _junta(base, parte):
    return f"{base}/{parte}" if base else str(parte)


# --------------------------------------------------------------- decodificação

class _ErroDecodificacao(Exception):
    def __init__(self, regra, detalhe):
        super().__init__(regra, detalhe)
        self.regra, self.detalhe = regra, detalhe


def _sem_chaves_duplicadas(pares):
    objeto = {}
    for chave, valor in pares:
        if chave in objeto:
            raise _ErroDecodificacao("chave_duplicada", chave)
        objeto[chave] = valor
    return objeto


def _recusa_constante(nome):
    raise _ErroDecodificacao("constante_nao_finita", nome)


def _float_finito(texto):
    valor = float(texto)
    if valor in (float("inf"), float("-inf")):
        raise _ErroDecodificacao("constante_nao_finita", texto)
    return valor


def decodificar(texto):
    """Interpreta a resposta bruta do modelo. Devolve (objeto, diagnosticos).

    Recusa texto fora do JSON (inclusive cercas Markdown), JSON truncado, chaves
    duplicadas, NaN/Infinity e raiz que não seja objeto. Em caso de erro o
    objeto devolvido é None; guarde sempre o texto original como evidência.
    """
    if not isinstance(texto, str):
        return None, [_d("$", "tipo_invalido", "string", _tipo(texto))]
    try:
        dados = json.loads(texto, object_pairs_hook=_sem_chaves_duplicadas,
                           parse_constant=_recusa_constante, parse_float=_float_finito)
    except _ErroDecodificacao as erro:
        return None, [_d("$", erro.regra, recebido=erro.detalhe)]
    except ValueError as erro:  # JSONDecodeError: truncado, texto extra, cerca Markdown, vazio
        return None, [_d("$", "json_invalido", recebido=str(erro))]
    if not isinstance(dados, dict):
        return None, [_d("$", "raiz_nao_objeto", "object", _tipo(dados))]
    return dados, []


# ---------------------------------------------------------- validação estrutural

def _objeto_fechado(dados, campos, caminho, erros):
    """Exige objeto com exatamente os campos declarados. Devolve False se não for objeto."""
    if not isinstance(dados, dict):
        erros.append(_d(caminho or "$", "tipo_invalido", "object", _tipo(dados)))
        return False
    for campo in campos:
        if campo not in dados:
            erros.append(_d(_junta(caminho, campo), "campo_ausente"))
    for campo in dados:
        if campo not in campos:
            erros.append(_d(_junta(caminho, campo), "campo_extra"))
    return True


def _texto(valor, caminho, erros):
    if not isinstance(valor, str):
        erros.append(_d(caminho, "tipo_invalido", "string", _tipo(valor)))
    elif not valor.strip():
        erros.append(_d(caminho, "texto_vazio"))


def _lista_de_textos(valor, caminho, erros, minimo, maximo):
    if not isinstance(valor, list):
        erros.append(_d(caminho, "tipo_invalido", "array", _tipo(valor)))
        return
    if not minimo <= len(valor) <= maximo:
        esperado = str(minimo) if minimo == maximo else f"{minimo} a {maximo}"
        erros.append(_d(caminho, "quantidade_invalida", esperado, len(valor)))
    for i, item in enumerate(valor):
        _texto(item, _junta(caminho, i), erros)


def _inteiro_positivo(valor, caminho, erros):
    # type(...) is int recusa bool, 5.0 e "5": sem coerção silenciosa.
    if type(valor) is not int:
        erros.append(_d(caminho, "tipo_invalido", "integer", _tipo(valor)))
    elif valor < 1:
        erros.append(_d(caminho, "minimo", 1, valor))


def _etapas(valor, caminho, erros):
    if not isinstance(valor, list):
        erros.append(_d(caminho, "tipo_invalido", "array", _tipo(valor)))
        return
    if not valor:
        erros.append(_d(caminho, "quantidade_invalida", "pelo menos 1", 0))
    for i, etapa in enumerate(valor):
        base = _junta(caminho, i)
        if _objeto_fechado(etapa, _CAMPOS_ETAPA, base, erros):
            if "etapa" in etapa:
                _texto(etapa["etapa"], _junta(base, "etapa"), erros)
            if "minutos" in etapa:
                _inteiro_positivo(etapa["minutos"], _junta(base, "minutos"), erros)
            if "atividade" in etapa:
                _texto(etapa["atividade"], _junta(base, "atividade"), erros)


def _estrutura(contrato, dados):
    erros = []
    if contrato == "objetivos":
        if _objeto_fechado(dados, ("objetivos",), "", erros) and "objetivos" in dados:
            _lista_de_textos(dados["objetivos"], "objetivos", erros, 2, 4)
    elif contrato == "metodologia":
        if _objeto_fechado(dados, ("metodologia", "recursos"), "", erros):
            for campo in ("metodologia", "recursos"):
                if campo in dados:
                    _texto(dados[campo], campo, erros)
    elif contrato == "sequencia":
        if _objeto_fechado(dados, ("etapas",), "", erros) and "etapas" in dados:
            _etapas(dados["etapas"], "etapas", erros)
    elif contrato == "avaliacao":
        if _objeto_fechado(dados, ("avaliacao",), "", erros) and "avaliacao" in dados:
            _texto(dados["avaliacao"], "avaliacao", erros)
    elif contrato == "adaptacao":
        if _objeto_fechado(dados, ("adaptacoes",), "", erros) and "adaptacoes" in dados:
            _lista_de_textos(dados["adaptacoes"], "adaptacoes", erros, 2, 2)
    else:  # plano
        if _objeto_fechado(dados, _CAMPOS_PLANO, "", erros):
            for campo in ("titulo", "habilidade_codigo", "habilidade_texto", "ano", "tema", "tipo",
                          "metodologia", "recursos", "avaliacao"):
                if campo in dados:
                    _texto(dados[campo], campo, erros)
            if "duracao_min" in dados:
                _inteiro_positivo(dados["duracao_min"], "duracao_min", erros)
            if "objetivos" in dados:
                _lista_de_textos(dados["objetivos"], "objetivos", erros, 2, 4)
            if "etapas" in dados:
                _etapas(dados["etapas"], "etapas", erros)
            if "adaptacoes" in dados:
                _lista_de_textos(dados["adaptacoes"], "adaptacoes", erros, 2, 2)
    return erros


# -------------------------------------------------------- consistência mecânica

def _consistencia(contrato, dados, entrada):
    erros = []
    contexto, habilidade = entrada["contexto"], entrada["habilidade"]
    if contrato in ("sequencia", "plano"):
        soma = sum(etapa["minutos"] for etapa in dados["etapas"])
        if soma != contexto["duracao_min"]:
            erros.append(_d("etapas", "soma_duracao", contexto["duracao_min"], soma))
    if contrato in ("metodologia", "plano") and dados["recursos"] != contexto["recursos"]:
        erros.append(_d("recursos", "recursos_confirmados", contexto["recursos"], dados["recursos"]))
    if contrato == "plano":
        esperado = {"ano": contexto["ano"], "tema": contexto["tema"],
                    "duracao_min": contexto["duracao_min"], "tipo": contexto["tipo"],
                    "habilidade_codigo": habilidade["codigo"], "habilidade_texto": habilidade["habilidade"]}
        for campo, valor in esperado.items():
            if type(dados[campo]) is not type(valor) or dados[campo] != valor:
                erros.append(_d(campo, "entrada_preservada", valor, dados[campo]))
    return erros


def validar(contrato, dados, entrada):
    """Valida `dados` contra o contrato. `entrada` = {"contexto": ..., "habilidade": ...}
    confirmados pelo professor. Devolve lista de diagnósticos (vazia = válido).
    Só aplica as regras de consistência se a estrutura estiver correta.
    """
    if contrato not in CONTRATOS:
        raise ValueError(f"Contrato desconhecido: {contrato!r}")
    erros = _estrutura(contrato, dados)
    return erros if erros else _consistencia(contrato, dados, entrada)
