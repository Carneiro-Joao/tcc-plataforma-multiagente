"""Gera as páginas de adjudicação humana das séries do Juiz (V03 a V06 e controle do plano original).

Saída (pasta escolhida, nunca sobrescreve):
  adjudicacao_A_cega.html       dar ao 2º avaliador. Nota própria dos 5 planos + julgamento de cada crítica do Juiz,
                                sem rótulo de variante, com itens e planos em ordem embaralhada e códigos opacos.
  adjudicacao_B_informada.html  depois da A: mostra o defeito inserido e pergunta se cada parecer o detectou.
  adjudicacao_comparar.html     para o João: abre dois .json de avaliadores, mostra concordância/kappa e monta o consenso.
  chave_de_codigos.json         NÃO compartilhar: liga cada código (I01, P3, R02) à execução e à variante reais.

Somente biblioteca padrão. Lê os resultados já gravados (nada de rede ou API).
"""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import random
import sys

from analisar_serie import carregar_execucoes, config_experimental, validos_e_falhas
from contratos.rubrica_juiz import GRAVIDADES, RUBRICA
from erros import ErroGeracao
import adjudicacao_web as web

RAIZ = Path(__file__).resolve().parents[1]
GRUPOS = ("CONTROLE", "V03", "V04", "V05", "V06")
VERSAO_PROMPT = "juiz-v1.3"


def hash_curto(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()[:12]


def carregar_specs(pasta):
    specs = {}
    for arq in sorted(Path(pasta).glob("*.spec.json")):
        s = json.loads(arq.read_text(encoding="utf-8-sig"))
        specs[s["numero"]] = s
    return specs


def coletar(pasta_ensaios, versao_prompt=VERSAO_PROMPT, grupos=GRUPOS):
    """Pareceres VÁLIDOS da configuração pedida, agrupados (CONTROLE, V03...). Devolve (grupos, avisos)."""
    execs, avisos = carregar_execucoes(pasta_ensaios)
    validos, _ = validos_e_falhas(execs)
    plano_base = {(e["registro"].get("origem") or {}).get("plano_base_sha256") for e in validos} - {None}
    sel = defaultdict(list)
    for e in validos:
        r, o = e["registro"], e["registro"].get("origem") or {}
        if r.get("versao_prompt") != versao_prompt or r.get("modo") != "api_real" or not e.get("caso"):
            continue
        if o.get("id_variante"):
            g = o["id_variante"].split("-")[0]
        elif o.get("tipo") == "sqlite_real" and (not plano_base or r.get("plano_sha256") in plano_base):
            g = "CONTROLE"
        else:
            continue
        if g in grupos:
            sel[g].append(e)
    for g in sel:
        sel[g].sort(key=lambda e: e["pasta"])
    configs = {json.dumps(config_experimental(e["registro"]), sort_keys=True) for g in sel.values() for e in g}
    if len(configs) > 1:
        avisos.append(f"Os pareceres selecionados misturam {len(configs)} configurações experimentais.")
    faltando = [g for g in grupos if not sel.get(g)]
    if faltando:
        avisos.append("Sem pareceres válidos para: " + ", ".join(faltando))
    return dict(sel), avisos


def _rubrica():
    return {c: dict(rotulo=v["rotulo"], pergunta=v["pergunta"], indicadores=list(v["indicadores"]),
                    ancoras={str(k): t for k, t in v["ancoras"].items()}) for c, v in RUBRICA.items()}


def montar(sel, specs, seed=42):
    """Devolve (dados_A, dados_B, chave). Os códigos (P1, I01, R01) não dizem nada sobre variante nem ordem de execução."""
    rng = random.Random(seed)
    planos_por_hash = {}
    for g in sorted(sel):
        for e in sel[g]:
            h = e["registro"]["plano_sha256"]
            planos_por_hash.setdefault(h, dict(plano=e["caso"]["plano"], entrada=e["caso"].get("entrada"), grupos=set()))["grupos"].add(g)
    ordem = sorted(planos_por_hash)
    rng.shuffle(ordem)
    cod_plano = {h: f"P{i}" for i, h in enumerate(ordem, 1)}
    planos = [dict(codigo=cod_plano[h], plano=planos_por_hash[h]["plano"], entrada=planos_por_hash[h]["entrada"]) for h in ordem]

    brutos = []
    for g in sorted(sel):
        for e in sel[g]:
            p = e["registro"]["resultado"]["parecer"]
            for f in p["falhas"]:
                brutos.append(dict(pasta=e["pasta"], grupo=g, falha=f, plano_hash=e["registro"]["plano_sha256"]))
    brutos.sort(key=lambda b: (b["pasta"], b["falha"]["id"]))
    rng.shuffle(brutos)
    brutos.sort(key=lambda b: cod_plano[b["plano_hash"]])  # estável: agrupado por plano, embaralhado dentro de cada um
    itens, chave_itens = [], {}
    for i, b in enumerate(brutos, 1):
        f, cod = b["falha"], f"I{i:02d}"
        itens.append(dict(codigo=cod, plano=cod_plano[b["plano_hash"]], criterio=f["criterio"], componente=f["componente"],
                          gravidade=f["gravidade"], descricao=f["descricao"], correcao=f["correcao_sugerida"]))
        chave_itens[cod] = dict(pasta=b["pasta"], falha_id=f["id"], grupo=b["grupo"], plano=cod_plano[b["plano_hash"]])

    A = dict(fase="A", planos=planos, itens=itens, rubrica=_rubrica(), gravidades=GRAVIDADES)
    A["dataset_id"] = hash_curto(A)

    grupos_b, pareceres, chave_pareceres = {}, [], {}
    for g in (x for x in sorted(sel) if x != "CONTROLE"):
        spec = specs.get(g)
        if spec is None:
            raise ErroGeracao(f"Falta a especificação da variante {g} em experimentos/juiz/variantes.")
        primeiro = sel[g][0]
        neutra = g == "V06"
        grupos_b[g] = dict(numero=g, titulo=spec["titulo"], tipo="controle" if neutra else "defeito",
                           descricao=spec["descricao_manipulacao"], campo=spec["campo"], valor_original=spec["valor_original"],
                           valor_novo=spec["valor_novo"], plano=primeiro["caso"]["plano"], entrada=primeiro["caso"].get("entrada"))
        for e in sel[g]:
            p = e["registro"]["resultado"]["parecer"]
            cod = f"R{len(pareceres) + 1:02d}"
            pareceres.append(dict(codigo=cod, grupo=g, falhas=[dict(id=f["id"], criterio=f["criterio"], componente=f["componente"],
                                                                   gravidade=f["gravidade"], descricao=f["descricao"]) for f in p["falhas"]]))
            chave_pareceres[cod] = dict(pasta=e["pasta"], grupo=g)
    B = dict(fase="B", grupos=grupos_b, pareceres=pareceres, rubrica=_rubrica())
    B["dataset_id"] = hash_curto(B)

    chave = dict(versao="chave-adjudicacao-1.0", dataset_A=A["dataset_id"], dataset_B=B["dataset_id"], seed=seed,
                 aviso="NÃO compartilhar com o avaliador da Fase A: revela qual crítica pertence a qual variante.",
                 planos={cod_plano[h]: dict(plano_sha256=h, grupos=sorted(planos_por_hash[h]["grupos"])) for h in ordem},
                 itens=chave_itens, pareceres=chave_pareceres)
    return A, B, chave


def _json_html(obj):
    return json.dumps(obj, ensure_ascii=False).replace("</", "<\\/").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")


def pagina(titulo, dados, js, abas=""):
    return (web.PAGINA_HTML_AB.replace("__TITULO__", titulo).replace("__CSS__", web.CSS).replace("__ABAS__", abas)
            .replace("__COMUM__", web.COMUM).replace("__JS__", js).replace("__DATA__", _json_html(dados)))


def pagina_comparar(A, B):
    return (web.PAGINA_HTML_C.replace("__CSS__", web.CSS).replace("__COMUM__", web.COMUM).replace("__JS__", web.PAGINA_C)
            .replace("__DATA__", _json_html(dict(A=A, B=B))))


def gravar_novo(caminho, texto):
    with Path(caminho).open("x", encoding="utf-8", newline="\n") as f:  # "x": nunca sobrescreve
        f.write(texto)


def gerar(pasta_ensaios, pasta_saida, pasta_specs=None, seed=42):
    sel, avisos = coletar(pasta_ensaios)
    if not sel.get("V03") and not sel.get("CONTROLE"):
        raise ErroGeracao("Nenhum parecer válido encontrado na pasta de ensaios.")
    A, B, chave = montar(sel, carregar_specs(pasta_specs or RAIZ / "experimentos" / "juiz" / "variantes"), seed)
    saida = Path(pasta_saida)
    saida.mkdir(parents=True, exist_ok=True)
    arquivos = {
        "adjudicacao_A_cega.html": pagina("Adjudicação — Fase A (cega)", A, web.PAGINA_A, web.ABAS_A),
        "adjudicacao_B_informada.html": pagina("Adjudicação — Fase B (informada)", B, web.PAGINA_B),
        "adjudicacao_comparar.html": pagina_comparar(A, B),
        "chave_de_codigos.json": json.dumps(chave, ensure_ascii=False, indent=1),
    }
    for nome, texto in arquivos.items():
        if (saida / nome).exists():
            raise ErroGeracao(f"{saida / nome} já existe; escolha outra pasta ou apague com cuidado (não sobrescrevo).")
    for nome, texto in arquivos.items():
        gravar_novo(saida / nome, texto)
    return dict(arquivos=[str(saida / n) for n in arquivos], planos=len(A["planos"]), itens=len(A["itens"]),
                pareceres_b=len(B["pareceres"]), avisos=avisos)


def main(argv=None):
    p = argparse.ArgumentParser(description="Gera as páginas de adjudicação humana (V03–V06 + controle).")
    p.add_argument("--ensaios", type=Path, default=Path("local/ensaios_juiz"))
    p.add_argument("--saida", type=Path, default=Path("local/adjudicacao"))
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args(argv)
    try:
        r = gerar(args.ensaios, args.saida, seed=args.seed)
    except (ErroGeracao, OSError, ValueError, KeyError) as erro:
        print(f"Erro: {type(erro).__name__}: {erro}", file=sys.stderr)
        return 2
    print(f"Planos: {r['planos']} · críticas a julgar (Fase A): {r['itens']} · pareceres (Fase B): {r['pareceres_b']}")
    for a in r["avisos"]:
        print("Aviso:", a)
    print("Arquivos:\n  " + "\n  ".join(r["arquivos"]))
    print("Dê ao 2º avaliador SOMENTE adjudicacao_A_cega.html. Guarde chave_de_codigos.json só com você.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
