"""Concordância entre dois avaliadores humanos (adjudicação do Juiz). Somente biblioteca padrão.

Lê os dois arquivos JSON exportados pela página de adjudicação e calcula concordância simples, kappa de Cohen
(categorias) e kappa ponderado quadrático (notas 0 a 3). A mesma conta existe em JavaScript dentro da página de
comparação; os testes conferem as duas implementações contra os mesmos vetores.

Limites: com poucos itens o kappa é instável; se quase todas as respostas caem numa categoria, o kappa fica baixo mesmo
com muita concordância (paradoxo da prevalência). Por isso o relatório mostra também a concordância simples e as contagens.
"""
import argparse
import json
from pathlib import Path
import sys

CRITERIOS = ("aderencia_curricular", "alinhamento_objetivos", "coerencia_metodologica", "viabilidade",
             "avaliacao_aprendizagem", "inclusao")
CAMPOS_ITEM = ("procedencia", "gravidade", "componente_correto")
EPS = 1e-12


def kappa_nominal(a, b):
    """Kappa de Cohen. None quando indefinido (sem pares, ou os dois só usaram a mesma categoria)."""
    if len(a) != len(b):
        raise ValueError("listas de tamanhos diferentes")
    n = len(a)
    if n == 0:
        return None
    po = sum(x == y for x, y in zip(a, b)) / n
    pe = sum((a.count(c) / n) * (b.count(c) / n) for c in set(a) | set(b))
    return None if 1 - pe < EPS else (po - pe) / (1 - pe)


def kappa_ponderado(a, b, k=4):
    """Kappa ponderado com pesos quadráticos para notas inteiras 0..k-1."""
    if len(a) != len(b):
        raise ValueError("listas de tamanhos diferentes")
    n = len(a)
    if n == 0:
        return None

    def w(i, j):
        return 1 - ((i - j) / (k - 1)) ** 2
    po = sum(w(x, y) for x, y in zip(a, b)) / n
    pe = sum(w(i, j) * (a.count(i) / n) * (b.count(j) / n) for i in range(k) for j in range(k))
    return None if 1 - pe < EPS else (po - pe) / (1 - pe)


def concordancia_simples(a, b):
    return sum(x == y for x, y in zip(a, b)) / len(a) if a else None


def _pares_itens(e1, e2, campo):
    a, b, ids = [], [], []
    for codigo in sorted(set(e1.get("itens", {})) & set(e2.get("itens", {}))):
        x, y = e1["itens"][codigo].get(campo), e2["itens"][codigo].get(campo)
        if x is not None and y is not None:
            a.append(x)
            b.append(y)
            ids.append(codigo)
    return a, b, ids


def comparar(e1, e2):
    """Compara duas exportações da MESMA página (mesmo dataset_id e fase)."""
    for chave in ("dataset_id", "fase"):
        if e1.get(chave) != e2.get(chave):
            raise ValueError(f"As exportações não são do mesmo arquivo de adjudicação ({chave} diferente).")
    saida = dict(fase=e1["fase"], avaliadores=[e1.get("avaliador"), e2.get("avaliador")], campos={}, divergencias=[])
    campos = CAMPOS_ITEM if e1["fase"] == "A" else tuple(sorted({c for it in e1.get("itens", {}).values() for c in it
                                                                   if c != "comentario"}))
    for campo in campos:
        a, b, ids = _pares_itens(e1, e2, campo)
        saida["campos"][campo] = dict(n=len(a), concordancia=concordancia_simples(a, b), kappa=kappa_nominal(a, b))
        saida["divergencias"] += [dict(tipo="item", codigo=i, campo=campo, avaliador1=x, avaliador2=y)
                                  for i, x, y in zip(ids, a, b) if x != y]
    if e1["fase"] == "A":
        a, b, onde = [], [], []
        for plano in sorted(set(e1.get("notas_proprias", {})) & set(e2.get("notas_proprias", {}))):
            for crit in CRITERIOS:
                x, y = e1["notas_proprias"][plano].get(crit), e2["notas_proprias"][plano].get(crit)
                if isinstance(x, int) and isinstance(y, int):
                    a.append(x)
                    b.append(y)
                    onde.append((plano, crit))
        saida["notas_proprias"] = dict(
            n=len(a), concordancia=concordancia_simples(a, b), dentro_de_1=(sum(abs(x - y) <= 1 for x, y in zip(a, b)) / len(a) if a else None),
            kappa_ponderado=kappa_ponderado(a, b))
        saida["divergencias"] += [dict(tipo="nota", codigo=p, campo=c, avaliador1=x, avaliador2=y)
                                  for (p, c), x, y in zip(onde, a, b) if abs(x - y) >= 2]
    return saida


def _fmt(v):
    return "n/d" if v is None else f"{v:.2f}"


def relatorio(c):
    linhas = [f"Fase {c['fase']} — avaliadores: {c['avaliadores'][0]} × {c['avaliadores'][1]}", ""]
    for campo, d in c["campos"].items():
        linhas.append(f"- {campo}: n={d['n']} · concordância {_fmt(d['concordancia'])} · kappa {_fmt(d['kappa'])}")
    if "notas_proprias" in c:
        d = c["notas_proprias"]
        linhas.append(f"- notas próprias (0–3): n={d['n']} · exatas {_fmt(d['concordancia'])} · dentro de ±1 {_fmt(d['dentro_de_1'])}"
                      f" · kappa ponderado {_fmt(d['kappa_ponderado'])}")
    linhas += ["", f"Divergências para consenso: {len(c['divergencias'])} (notas só contam com diferença ≥ 2)",
               "Aviso: n pequeno; kappa baixo com concordância alta pode ser paradoxo da prevalência."]
    return "\n".join(linhas)


def main(argv=None):
    p = argparse.ArgumentParser(description="Concordância entre dois avaliadores (exportações da adjudicação).")
    p.add_argument("avaliador1", type=Path)
    p.add_argument("avaliador2", type=Path)
    args = p.parse_args(argv)
    try:
        e1, e2 = (json.loads(a.read_text(encoding="utf-8-sig")) for a in (args.avaliador1, args.avaliador2))
        print(relatorio(comparar(e1, e2)))
    except (OSError, ValueError, KeyError, AttributeError) as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
