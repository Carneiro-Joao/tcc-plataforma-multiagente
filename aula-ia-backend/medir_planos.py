"""Mede planos exportados pela "Regra de medição (fixa)" de docs/PoC07B_Prompt_2_3.md, mais soma de minutos e contrato.

Uso:  python medir_planos.py [--pasta local/planos_ia] [--entradas ../experimentos/geracao/poc07b_entradas.json] [--saida rel.md]

- Texto analisado: todos os campos do plano, exceto `recursos`, `referencias` e `habilidade_bncc`; sem acentos e em minúsculas.
- H1 (material ausente): o plano viola se contiver um radical da lista sem que o radical apareça em `contexto.recursos`.
  Radicais escritos com "/" no protocolo são o mesmo grupo (ex.: quadro/pincel). Exceção: `papel` não conta com `impress` nos recursos.
- H2 (sem acentos): algum campo de texto com mais de 60 caracteres sem nenhum de áàâãéêíóôõúç E com ao menos uma palavra-guia.
- Minutos: soma de `desenvolvimento[].minutos` == `contexto.duracao_min`. Contrato: `plano_v2.diagnosticar` sem erros.
- Agrupa por `origem.prompts_gerador`. Com --entradas, só entram casos cujo contexto+habilidade batem com uma linha do protocolo.
Resultado descritivo (contagens x/n). Não é teste estatístico nem avaliação pedagógica.
"""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import re
import sys
import unicodedata

from contratos import plano_v2

BASE = Path(__file__).resolve().parent
EXCLUIDOS = ("recursos", "referencias", "habilidade_bncc")
# Grupos de radicais, exatamente como no protocolo. A barra "/" do protocolo vira um grupo.
RADICAIS = (
    ("cartao/cartoes", ("cartao", "cartoes")),
    ("papel", ("papel",)),
    ("baralho", ("baralho",)),
    ("ficha", ("ficha",)),
    ("projetor", ("projetor",)),
    ("data show", ("data show",)),
    ("computador", ("computador",)),
    ("internet", ("internet",)),
    ("celular", ("celular",)),
    ("quadro/pincel", ("quadro", "pincel")),
    ("impress", ("impress",)),
    ("alto-relevo/tatil", ("alto-relevo", "tatil")),
)
ACENTOS = set("áàâãéêíóôõúç")
PALAVRAS_GUIA = ("observacao", "avaliacao", "explicacao", "participacao", "utilizara", "apos", "ordenacao",
                 "comparacao", "verificacao", "nao")
GUIA = re.compile(r"\b(?:" + "|".join(PALAVRAS_GUIA) + r")\b")
MINIMO_CARACTERES = 60


def normalizar(texto):
    return "".join(c for c in unicodedata.normalize("NFD", str(texto).lower()) if not unicodedata.combining(c))


def campos_de_texto(plano):
    """[(caminho, texto)] de todas as strings do plano, exceto os campos excluídos pela regra."""
    saida = []

    def visitar(valor, caminho):
        if isinstance(valor, str):
            saida.append((caminho, valor))
        elif isinstance(valor, dict):
            for k, v in valor.items():
                visitar(v, f"{caminho}.{k}" if caminho else k)
        elif isinstance(valor, list):
            for i, v in enumerate(valor):
                visitar(v, f"{caminho}[{i}]")

    for chave, valor in plano.items():
        if chave not in EXCLUIDOS:
            visitar(valor, chave)
    return saida


def material_ausente(plano, recursos):
    """Grupos de radicais citados no texto e ausentes de contexto.recursos (H1)."""
    texto = normalizar(" ".join(t for _, t in campos_de_texto(plano)))
    rec = normalizar(recursos)
    violacoes = []
    for nome, radicais in RADICAIS:
        if not any(r in texto for r in radicais):
            continue
        if any(r in rec for r in radicais):
            continue
        if nome == "papel" and "impress" in rec:
            continue
        violacoes.append(nome)
    return violacoes


def campos_sem_acento(plano):
    """Caminhos dos campos com mais de 60 caracteres, sem nenhum acento e com palavra-guia (H2)."""
    achados = []
    for caminho, texto in campos_de_texto(plano):
        if len(texto) > MINIMO_CARACTERES and not (set(texto.lower()) & ACENTOS) and GUIA.search(normalizar(texto)):
            achados.append(caminho)
    return achados


def medir_caso(caso):
    plano, entrada = caso["plano"], caso["entrada"]
    contexto = entrada["contexto"]
    soma = sum(e.get("minutos", 0) for e in plano.get("desenvolvimento", []))
    try:
        erros_contrato = plano_v2.diagnosticar("plano", plano, entrada)
    except Exception as erro:  # estrutura quebrada também é "fora do contrato"
        erros_contrato = [str(erro)]
    ausentes = material_ausente(plano, contexto["recursos"])
    sem_acento = campos_sem_acento(plano)
    return dict(h1=bool(ausentes), material_ausente=ausentes, h2=bool(sem_acento), campos_sem_acento=sem_acento,
                minutos=soma, minutos_ok=soma == contexto["duracao_min"], contrato_ok=not erros_contrato,
                erros_contrato=len(erros_contrato))


def chave_entrada(contexto, habilidade):
    return (contexto["tema"], contexto["tipo"], contexto["duracao_min"], contexto["recursos"], habilidade)


def carregar(pasta, entradas=None):
    """Casos medidos por grupo de prompt: {prompts: [(arquivo, n_linha|None, caso, medida)]}; e casos ignorados."""
    filtro = None
    if entradas is not None:
        filtro = {chave_entrada(e, e["habilidade"]): i for i, e in enumerate(entradas, 1)}
    grupos, ignorados = defaultdict(list), []
    for arq in sorted(Path(pasta).glob("*.json")):
        caso = json.loads(arq.read_text(encoding="utf-8"))
        n = None
        if filtro is not None:
            n = filtro.get(chave_entrada(caso["entrada"]["contexto"], caso["entrada"]["habilidade"]["codigo"]))
            if n is None:
                ignorados.append(arq.name)
                continue
        prompts = " + ".join(caso.get("origem", {}).get("prompts_gerador") or ["?"])
        grupos[prompts].append((arq.name, n, caso, medir_caso(caso)))
    for lista in grupos.values():
        lista.sort(key=lambda item: (item[1] or 0, item[0]))
    return dict(grupos), ignorados


def tabela(grupos):
    linhas = ["| Prompt | n | H1 material ausente | H2 sem acentos | Minutos somam a duração | Válido no contrato |",
              "|---|---|---|---|---|---|"]
    for prompts in sorted(grupos):
        medidas = [m for *_, m in grupos[prompts]]
        n = len(medidas)
        conta = lambda chave: sum(1 for m in medidas if m[chave])
        linhas.append(f"| {prompts} | {n} | {conta('h1')}/{n} | {conta('h2')}/{n} | {conta('minutos_ok')}/{n} | {conta('contrato_ok')}/{n} |")
    return "\n".join(linhas)


def detalhe(grupos):
    linhas = []
    for prompts in sorted(grupos):
        linhas.append(f"\n### {prompts}\n")
        linhas.append("| Linha | Arquivo | Tema / tipo / min | H1 (radicais) | H2 (campos) | Minutos | Contrato |")
        linhas.append("|---|---|---|---|---|---|---|")
        for arq, n, caso, m in grupos[prompts]:
            c = caso["entrada"]["contexto"]
            linhas.append(f"| {n or '-'} | `{arq}` | {c['tema']} / {c['tipo']} / {c['duracao_min']} | "
                          f"{', '.join(m['material_ausente']) or '—'} | {', '.join(m['campos_sem_acento']) or '—'} | "
                          f"{m['minutos']}/{c['duracao_min']} | {'ok' if m['contrato_ok'] else str(m['erros_contrato']) + ' erro(s)'} |")
    return "\n".join(linhas)


def main(argv=None):
    p = argparse.ArgumentParser(description="Medição fixa da PoC07B (H1, H2, minutos, contrato) sobre casos exportados.")
    p.add_argument("--pasta", type=Path, default=BASE / "local" / "planos_ia")
    p.add_argument("--entradas", type=Path, help="Só casos que batem com estas entradas do protocolo.")
    p.add_argument("--saida", type=Path, help="Grava o relatório em Markdown (não sobrescreve).")
    args = p.parse_args(argv)
    entradas = None
    if args.entradas:
        from gerar_lote import ler_entradas
        entradas = ler_entradas(args.entradas)
    grupos, ignorados = carregar(args.pasta, entradas)
    texto = "## Contagens\n\n" + tabela(grupos) + "\n\n## Por plano\n" + detalhe(grupos)
    if ignorados:
        texto += "\n\nIgnorados (fora das entradas do protocolo): " + ", ".join(f"`{a}`" for a in ignorados)
    print(texto)
    if args.saida:
        if args.saida.exists():
            print(f"Erro: {args.saida} já existe; não sobrescrito.", file=sys.stderr)
            return 2
        args.saida.write_text(texto + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
