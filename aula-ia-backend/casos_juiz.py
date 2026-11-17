"""Recuperação fiel de planos confirmados. Nunca integra fixtures ou regenera texto."""
from contextlib import closing
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import sqlite3

from contratos import plano_v2
from contratos.execucao import ler_json


def hash_json(valor):
    """SHA-256 de JSON canônico UTF-8 (chaves ordenadas, sem espaços, sem NaN)."""
    return sha256(json.dumps(valor, ensure_ascii=False, sort_keys=True,
                             separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest()


def validar_caso(caso):
    if not isinstance(caso, dict) or not all(k in caso for k in ("plano", "entrada", "modelo_gerador", "origem")):
        raise ValueError("Caso exige plano, entrada confirmada, modelo_gerador e origem.")
    if not isinstance(caso["modelo_gerador"], str) or not caso["modelo_gerador"].strip():
        raise ValueError("Informe o modelo gerador original.")
    origem = caso["origem"]
    if not isinstance(origem, dict) or not origem.get("tipo"):
        raise ValueError("Identifique a origem (real, sintética ou variante controlada).")
    if type(caso.get("revisao", 0)) is not int or caso.get("revisao", 0) < 0:
        raise ValueError("Revisão inválida.")
    if not isinstance(caso["entrada"], dict):
        raise ValueError("Entrada confirmada deve ser objeto.")
    plano_v2.validar_entrada(caso["entrada"])
    plano_v2.validar("plano", caso["plano"], caso["entrada"])
    for campo in ("plano", "entrada"):
        esperado = origem.get(campo + "_sha256")
        if esperado and esperado != hash_json(caso[campo]):
            raise ValueError(f"Hash de {campo} difere da origem; não altere o caso congelado.")
    return caso


def carregar_caso(caminho):
    return validar_caso(ler_json(Path(caminho).read_text(encoding="utf-8-sig")))


def exportar_sqlite(banco, geracao_id):
    """Abre o banco SOMENTE para leitura e exige o ID exato da geração."""
    uri = Path(banco).resolve().as_uri() + "?mode=ro"
    with closing(sqlite3.connect(uri, uri=True)) as db:
        row = db.execute("""SELECT g.consulta_id,g.revisao,g.estado,g.resultado,g.criado_em,
                                   c.dados,c.codigo_confirmado
                            FROM geracoes g JOIN consultas c ON c.id=g.consulta_id
                            WHERE g.id=?""", (geracao_id,)).fetchone()
    if row is None:
        raise ValueError("Geração não encontrada no banco informado.")
    consulta_id, revisao, estado, bruto, criado, dados, codigo = row
    if not bruto or estado == "falha":
        raise ValueError("Geração não contém um plano concluído; não reconstruir de saídas parciais.")
    resultado, consulta = ler_json(bruto), ler_json(dados)
    if resultado.get("modo") != "ia" or resultado.get("contrato") != plano_v2.VERSAO:
        raise ValueError("Geração não é uma execução real de PlanoDeAula 2.0.")
    habilidades = [r["habilidade"] for r in consulta["resultados"] if r["habilidade"]["codigo"] == codigo]
    if len(habilidades) != 1:
        raise ValueError("Habilidade confirmada não é única na consulta original.")
    entrada = dict(versao="1.0", consulta_id=consulta_id, contexto=consulta["contexto"], habilidade=habilidades[0])
    plano = resultado.get("plano")
    rastreio = resultado.get("rastreio", [])
    origem = dict(tipo="sqlite_real", geracao_id=geracao_id, consulta_id=consulta_id,
                  estado_original=estado, criado_em_sqlite_utc=criado,
                  resultado_sqlite_sha256=sha256(bruto.encode("utf-8")).hexdigest(),
                  consulta_sqlite_sha256=sha256(dados.encode("utf-8")).hexdigest(),
                  plano_sha256=hash_json(plano), entrada_sha256=hash_json(entrada),
                  contrato_gerador=resultado.get("contrato"), provedor_gerador=resultado.get("provedor"),
                  prompts_gerador=sorted({r["versao_prompt"] for r in rastreio if r.get("versao_prompt")}),
                  modelos_respondidos=sorted({r["modelo_respondeu"] for r in rastreio if r.get("modelo_respondeu")}),
                  tempo_geracao_s=resultado.get("tempo_total_s"))
    return validar_caso(dict(plano=deepcopy(plano), entrada=deepcopy(entrada),
                             modelo_gerador=resultado.get("modelo"), revisao=revisao, origem=origem))


def salvar_novo(caminho, dados):
    """Não sobrescreve casos congelados nem ensaios anteriores."""
    texto = json.dumps(dados, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with caminho.open("x", encoding="utf-8", newline="\n") as arquivo:
        arquivo.write(texto)
