"""Exporta de uma vez os planos reais (gerador IA) do SQLite local para arquivos de caso congelado.

Uso:  python exportar_planos.py [--banco local/consultas.sqlite3] [--saida local/planos_ia]

Abre o banco SOMENTE para leitura. Cada arquivo sai no formato de `ensaio_juiz.py exportar` (plano + entrada + origem com hashes),
então serve para mostrar os planos a quem for revisar e depois como caso de teste do Juiz. Nunca sobrescreve arquivo existente.
Gerações de demonstração, com falha, em andamento ou sem plano válido são puladas e listadas com o motivo.
Recusa exportar qualquer caso que contenha credencial.
"""
import argparse
from contextlib import closing
import json
from pathlib import Path
import re
import sqlite3
import sys
import unicodedata

from casos_juiz import exportar_sqlite, salvar_novo
from erros import ErroContrato
from groq_juiz import sanitizar

BASE = Path(__file__).resolve().parent
# Padrões de chave de API (Gemini "AIza…", Groq "gsk_…", estilo "sk-…"). O sanitizar() do Juiz só conhece as do Groq.
CREDENCIAL = re.compile(r"AIza[0-9A-Za-z_-]{20,}|gsk_[0-9A-Za-z_-]{10,}|\bsk-[0-9A-Za-z_-]{20,}")


def tem_credencial(caso):
    return bool(CREDENCIAL.search(json.dumps(caso, ensure_ascii=False)))


def _slug(texto, limite=40):
    sem_acento = unicodedata.normalize("NFD", str(texto).lower()).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", sem_acento).strip("-")[:limite] or "plano"


def listar_geracoes(banco):
    """[(geracao_id, consulta_id, revisao, estado, criado_em, tema)] em ordem de criação. Somente leitura."""
    uri = Path(banco).resolve().as_uri() + "?mode=ro"
    with closing(sqlite3.connect(uri, uri=True)) as db:
        linhas = db.execute("""SELECT g.id, g.consulta_id, g.revisao, g.estado, g.criado_em, c.dados
                               FROM geracoes g JOIN consultas c ON c.id = g.consulta_id
                               ORDER BY g.criado_em, g.revisao""").fetchall()
    saida = []
    for gid, cid, revisao, estado, criado, dados in linhas:
        try:
            tema = json.loads(dados)["contexto"]["tema"]
        except (ValueError, KeyError, TypeError):
            tema = "?"
        saida.append((gid, cid, revisao, estado, criado, tema))
    return saida


def exportar_todos(banco, pasta):
    """Devolve (exportados, pulados): listas de (arquivo|geracao_id, tema, detalhe)."""
    pasta = Path(pasta)
    exportados, pulados = [], []
    for gid, _, revisao, estado, _, tema in listar_geracoes(banco):
        try:
            caso = exportar_sqlite(banco, gid)
            if sanitizar(caso) != caso or tem_credencial(caso):
                raise ValueError("contém credencial; não exportado")
            destino = pasta / f"{_slug(tema)}_r{revisao}_{gid[:8]}.json"
            salvar_novo(destino, caso)
            exportados.append((destino, tema, estado))
        except FileExistsError:
            pulados.append((gid, tema, "arquivo já existe; não sobrescrito"))
        except (ValueError, ErroContrato) as erro:
            pulados.append((gid, tema, str(erro)))
    return exportados, pulados


def main(argv=None):
    p = argparse.ArgumentParser(description="Exporta os planos reais (IA) do SQLite local para casos congelados.")
    p.add_argument("--banco", type=Path, default=BASE / "local" / "consultas.sqlite3")
    p.add_argument("--saida", type=Path, default=BASE / "local" / "planos_ia")
    args = p.parse_args(argv)
    if not args.banco.is_file():
        print(f"Erro: banco não encontrado: {args.banco}", file=sys.stderr)
        return 2
    try:
        exportados, pulados = exportar_todos(args.banco, args.saida)
    except sqlite3.Error as erro:
        print(f"Erro ao ler o banco: {erro}", file=sys.stderr)
        return 2
    print(f"Exportados: {len(exportados)} · pulados: {len(pulados)}")
    for arq, tema, estado in exportados:
        print(f"  ok   {tema!r} ({estado}) -> {arq}")
    for gid, tema, motivo in pulados:
        print(f"  pulo {tema!r} [{gid[:8]}]: {motivo}")
    return 0 if exportados else 1


if __name__ == "__main__":
    sys.exit(main())
