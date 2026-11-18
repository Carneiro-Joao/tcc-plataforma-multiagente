"""Análise mecânica e provisória de uma série de ensaios do Juiz contra a hipótese pré-registrada.

Lê as pastas de ensaio (resultado.json + caso.json), separa FALHA TÉCNICA de parecer válido, classifica
cada parecer pelas regras de pontuação (experimentos/juiz/pontuacao/*.json), roda auditorias
determinísticas e gera um rascunho para a seção 6 do protocolo.

Limites: a classificação NÃO substitui a leitura humana, não altera a hipótese e não mede estabilidade
nem sensibilidade. Uma falha só é considerada relacionada ao alvo se citar um ID-alvo no texto.
"""
import argparse
from collections import Counter
from pathlib import Path
import re
import statistics
import sys

from contratos.execucao import ler_json
from erros import ErroGeracao

RE_ID = re.compile(r"\b(?:OBJ|EVI|ET|INS|ADP)\d+\b")
RE_SOMA = re.compile(r"\b\d+\s*(?:min(?:utos?)?\.?)?\s*\+\s*\d+\b|\bsoma\w*\b.{0,60}?\b\d+\s*min", re.IGNORECASE | re.DOTALL)
PREFIXO_COMPONENTE = {"OBJ": "objetivos", "EVI": "avaliacao_preliminar", "INS": "avaliacao_final",
                      "ET": "sequencia", "ADP": "adaptacao"}
NIVEIS = ("plena", "parcial", "a_adjudicar", "ausente")
AVISO = ("Classificação MECÂNICA e PROVISÓRIA, derivada do texto pré-registrado das hipóteses. Não substitui a "
         "leitura humana, não altera a hipótese e não mede estabilidade, sensibilidade nem especificidade.")


def ids_citados(texto):
    return set(RE_ID.findall(texto or ""))


def ids_do_plano(plano):
    ids = {o["id"] for o in plano["objetivos_especificos"]} | {e["id"] for e in plano["desenvolvimento"]}
    ids |= {e["id"] for e in plano["avaliacao_aprendizagem"]["evidencias"]}
    ids |= {i["id"] for i in plano["avaliacao_aprendizagem"]["instrumentos"]}
    return ids | {a["id"] for a in plano["adaptacoes"]}


def texto_da_falha(falha):
    return f"{falha['descricao']} {falha['correcao_sugerida']}"


# ------------------------------------------------------------------- auditorias

def auditar_parecer(parecer, plano):
    """Observações determinísticas sobre o comportamento do Juiz. Informativas: nada aqui bloqueia o parecer."""
    existentes, obs = ids_do_plano(plano), []
    textos = [(f"avaliacoes/{a['criterio']}", a["justificativa"]) for a in parecer["avaliacoes"]]
    textos += [(f"falhas/{f['id']}", texto_da_falha(f)) for f in parecer["falhas"]]
    for onde, texto in textos:
        inexistentes = sorted(ids_citados(texto) - existentes)
        if inexistentes:
            obs.append(dict(regra="id_inexistente", onde=onde, detalhe=", ".join(inexistentes)))
        if RE_SOMA.search(texto):
            obs.append(dict(regra="soma_de_minutos_no_texto", onde=onde, detalhe=RE_SOMA.search(texto).group(0).strip()))
    for a in parecer["avaliacoes"]:
        if a["nota"] == 3 and not (ids_citados(a["justificativa"]) & existentes):
            obs.append(dict(regra="nota_3_sem_id_do_plano", onde=f"avaliacoes/{a['criterio']}", detalhe=""))
    vistos = {}
    for a in parecer["avaliacoes"]:
        chave = re.sub(r"\s+", " ", a["justificativa"].strip().lower())
        if chave in vistos:
            obs.append(dict(regra="justificativa_repetida", onde=f"avaliacoes/{a['criterio']}", detalhe=vistos[chave]))
        vistos.setdefault(chave, a["criterio"])
    for f in parecer["falhas"]:
        cit = ids_citados(texto_da_falha(f)) & existentes
        esperados = {PREFIXO_COMPONENTE[re.match(r"[A-Z]+", i).group(0)] for i in cit}
        if esperados and f["componente"] not in esperados:
            obs.append(dict(regra="componente_provavelmente_errado", onde=f"falhas/{f['id']}",
                            detalhe=f"declarado {f['componente']}; ids citados sugerem {', '.join(sorted(esperados))}"))
    return obs


# ------------------------------------------------------------------- pontuação

def _casa(falha, conjunto):
    return (falha["criterio"] in conjunto.get("criterios", ()) and falha["componente"] in conjunto.get("componentes", ())
            and falha["gravidade"] in conjunto.get("gravidades", ()))


def pontuar_deteccao(parecer, regra):
    alvo = set(regra["ids_alvo"])
    do_alvo = [f for f in parecer["falhas"] if ids_citados(texto_da_falha(f)) & alvo]
    fora = [f for f in parecer["falhas"] if f not in do_alvo]
    nivel, motivo = "ausente", None
    if any(_casa(f, regra["pleno"]) for f in do_alvo):
        nivel = "plena"
    elif any(_casa(f, p) for f in do_alvo for p in regra.get("parcial", ())):
        nivel = "parcial"
    elif any(f["criterio"] in regra["pleno"]["criterios"] and f["componente"] in regra["pleno"]["componentes"] for f in do_alvo):
        nivel, motivo = "a_adjudicar", "critério e componente esperados, gravidade fora das listadas no protocolo"
    notas = {a["criterio"]: a["nota"] for a in parecer["avaliacoes"]}
    acima = {c: notas[c] for c, maxima in regra.get("nota_maxima", {}).items() if notas[c] > maxima}
    return dict(nivel=nivel, motivo=motivo, falhas_do_alvo=[f["id"] for f in do_alvo],
                trechos_do_alvo={f["id"]: texto_da_falha(f)[:300] for f in do_alvo}, semantica_confirmada=False,
                gravidades=sorted({f["gravidade"] for f in do_alvo}), falhas_fora_do_alvo=[f["id"] for f in fora],
                notas_acima_do_esperado=acima, resultado_negativo_provavel=not do_alvo and bool(acima))


def pares(parecer):
    return {(f["criterio"], f["componente"]) for f in parecer["falhas"]}


def pontuar_controle(parecer, regra, baselines):
    termos = [re.compile(t, re.IGNORECASE) for t in regra["termos_da_reformulacao"]]
    citam = [f["id"] for f in parecer["falhas"] if any(t.search(texto_da_falha(f)) for t in termos)]
    base_pares = set().union(*[pares(b) for b in baselines]) if baselines else None
    novos = sorted(pares(parecer) - base_pares) if base_pares is not None else None
    decisoes = {b["_decisao"] for b in baselines}
    return dict(falhas_que_citam_a_reformulacao=citam, pares_novos_vs_baseline=novos,
                decisao_igual_ao_baseline=(None if not baselines else parecer["_decisao"] in decisoes),
                critica_ou_maior_nova=None if novos is None else any(
                    f["gravidade"] in ("critica", "maior") and (f["criterio"], f["componente"]) in set(novos)
                    for f in parecer["falhas"]))


# --------------------------------------------------------------------- execuções

def carregar_execucoes(pasta):
    execs, avisos = [], []
    for sub in sorted(Path(pasta).glob("*/resultado.json")):
        try:
            reg = ler_json(sub.read_text(encoding="utf-8-sig"))
            caso = ler_json((sub.parent / "caso.json").read_text(encoding="utf-8-sig")) if (sub.parent / "caso.json").exists() else None
            execs.append(dict(pasta=sub.parent.name, registro=reg, caso=caso))
        except (OSError, ValueError, RecursionError, ErroGeracao) as erro:  # ErroContrato: JSON inválido
            avisos.append(f"{sub.parent.name}: não lido ({type(erro).__name__})")
    return execs, avisos


def selecionar(execs, id_variante=None, tipo=None):
    saida = []
    for e in execs:
        origem = e["registro"].get("origem") or {}
        if (id_variante and origem.get("id_variante") == id_variante) or (tipo and origem.get("tipo") == tipo):
            saida.append(e)
    return saida


CAMPOS_CONFIG = ("modo", "versao_prompt", "prompt_sha256", "versao_rubrica", "versao_adaptador", "versao_esquema_api",
                 "modelo_juiz", "parametros")


def config_experimental(registro):
    """Tudo o que, se mudar, torna dois pareceres NÃO comparáveis (além do plano avaliado)."""
    c = {k: registro.get(k) for k in CAMPOS_CONFIG}
    c["politica"] = (registro.get("politica") or {}).get("nome")
    return c


def configs_distintas(execs):
    vistas = []
    for e in execs:
        c = config_experimental(e["registro"])
        if c not in vistas:
            vistas.append(c)
    return vistas


def baseline_compativel(execs, plano_sha256, config):
    """Controles do plano ORIGINAL com o mesmo hash de plano e a mesma configuração da série analisada.
    Devolve (execuções, descartadas) onde descartadas conta o motivo de cada exclusão."""
    aceitos, descartados = [], Counter()
    for e in selecionar(execs, tipo="sqlite_real"):
        r = e["registro"]
        if r.get("plano_sha256") != plano_sha256:
            descartados["outro plano (hash diferente)"] += 1
        elif config_experimental(r) != config:
            diferentes = sorted(k for k, v in config_experimental(r).items() if v != config.get(k))
            descartados["configuração diferente: " + ", ".join(diferentes)] += 1
        else:
            aceitos.append(e)
    return aceitos, descartados


def validos_e_falhas(execs):
    validos, falhas = [], []
    for e in execs:
        status = e["registro"].get("status")
        if status == "sucesso" and isinstance((e["registro"].get("resultado") or {}).get("parecer"), dict):
            validos.append(e)
        elif status == "falha":
            r = e["registro"]
            falhas.append(dict(pasta=e["pasta"], tipo=r.get("tipo_erro"), erro=str(r.get("erro", ""))[:160]))
    return validos, falhas


def parecer_de(e):
    r = e["registro"]["resultado"]
    return dict(r["parecer"], _decisao=r["decisao"]["proximo_estado"])


def analisar(pasta, regra, pasta_baseline=None, versao_prompt=None):
    execs, avisos = carregar_execucoes(pasta)
    do_caso = selecionar(execs, id_variante=regra["id_variante"])
    validos, falhas = validos_e_falhas(do_caso)
    baselines, descartados = [], Counter()
    configs = configs_distintas(validos)
    if len(configs) > 1:
        avisos.append(f"A série mistura {len(configs)} configurações experimentais (prompt/modelo/parâmetros): "
                      "não é uma série homogênea e nenhum baseline foi selecionado.")
    if pasta_baseline is not None:
        base_execs, av2 = carregar_execucoes(pasta_baseline)
        avisos += av2
        hashes = {(e["registro"].get("origem") or {}).get("plano_base_sha256") for e in validos} - {None}
        if not validos and versao_prompt:  # antes da série: a configuração vem do prompt pedido, o plano do próprio controle
            candidatos = [e for e in validos_e_falhas(selecionar(base_execs, tipo="sqlite_real"))[0]
                          if e["registro"].get("versao_prompt") == versao_prompt]
            configs = configs_distintas(candidatos)
            hashes = {e["registro"].get("plano_sha256") for e in candidatos}
            avisos.append(f"Série ainda sem pareceres: baseline calculado pelo prompt informado ({versao_prompt}); "
                          "confirme que a série futura usará exatamente esta configuração.")
        if len(configs) != 1 or len(hashes) != 1:
            if len(configs) == 1 or not validos:
                avisos.append("Sem pareceres válidos da variante (ou sem plano_base_sha256): não há como saber qual "
                              "configuração e qual plano o baseline deve ter. Nenhum baseline selecionado.")
        else:
            aceitos, descartados = baseline_compativel(validos_e_falhas(base_execs)[0], next(iter(hashes)), configs[0])
            baselines = [parecer_de(e) for e in aceitos]
    linhas = []
    for e in validos:
        p = parecer_de(e)
        plano = (e["caso"] or {}).get("plano")
        r = e["registro"]
        linha = dict(pasta=e["pasta"], decisao=p["_decisao"], notas={a["criterio"]: a["nota"] for a in p["avaliacoes"]},
                     falhas=[(f["id"], f["criterio"], f["componente"], f["gravidade"]) for f in p["falhas"]],
                     tokens=(r.get("metricas") or {}).get("total_tokens_conhecido"), tempo_s=r.get("tempo_total_s"),
                     auditoria=auditar_parecer(p, plano) if plano else None)
        if regra["tipo"] == "deteccao":
            linha["pontuacao"] = pontuar_deteccao(p, regra)
        else:
            linha["pontuacao"] = pontuar_controle(p, regra, baselines)
        linhas.append(linha)
    return dict(regra=regra, linhas=linhas, falhas_tecnicas=falhas, avisos=avisos, n_baseline=len(baselines),
                baseline_descartados=dict(descartados), configuracao=configs[0] if len(configs) == 1 else None,
                n_execucoes=len(do_caso))


# ---------------------------------------------------------------------- relatório

def _faixa(valores):
    v = [x for x in valores if isinstance(x, (int, float))]
    return f"{min(v):.4g} a {max(v):.4g} (média {statistics.mean(v):.4g})" if v else "n/d"


def renderizar_relatorio(a):
    r, linhas = a["regra"], a["linhas"]
    out = [f"# Rascunho de resultados — {r['id_variante']}", "", f"> {AVISO}", "",
           f"- Execuções encontradas para a variante: **{a['n_execucoes']}** · pareceres válidos: **{len(linhas)}** · "
           f"falhas técnicas: **{len(a['falhas_tecnicas'])}**.",
           f"- Os pareceres válidos são o denominador. Falhas técnicas (HTTP, cota, recusa) **não** entram como "
           "detecção nem como falso negativo."]
    if a.get("configuracao"):
        c = a["configuracao"]
        out.append(f"- Configuração da série: prompt `{c['versao_prompt']}`, modelo `{c['modelo_juiz']}`, "
                   f"rubrica `{c['versao_rubrica']}`, modo `{c['modo']}`.")
    if r["tipo"] == "deteccao":
        out.append("- **Atenção:** \"plena\" significa ID-alvo citado + critério, componente e gravidade esperados. "
                   "Isso NÃO confirma que o texto da falha descreve o defeito inserido; confirme lendo cada trecho "
                   "(`trechos_do_alvo`) na adjudicação humana.")
        cont = Counter(l["pontuacao"]["nivel"] for l in linhas)
        out += [f"- Níveis (mecânicos): " + ", ".join(f"{n}: {cont.get(n, 0)}/{len(linhas)}" for n in NIVEIS) + ".", "",
                "| Execução | Nível | Falhas do alvo (gravidade) | Fora do alvo | Notas acima do esperado | Decisão |",
                "|---|---|---|---|---|---|"]
        for l in linhas:
            p = l["pontuacao"]
            out.append(f"| `{l['pasta']}` | {p['nivel']} | {', '.join(p['falhas_do_alvo']) or '—'} "
                       f"({', '.join(p['gravidades']) or '—'}) | {', '.join(p['falhas_fora_do_alvo']) or '—'} | "
                       f"{p['notas_acima_do_esperado'] or '—'} | {l['decisao']} |")
    else:
        out += [f"- Pareceres do controle original usados como linha de base: **{a['n_baseline']}**"
                + (" (insuficiente: o protocolo pede 3)." if a["n_baseline"] < 3 else "."),
                *[f"- Controle descartado ({n}): {motivo}." for motivo, n in sorted(a.get("baseline_descartados", {}).items())], "",
                "| Execução | Citam a reformulação | Pares (critério, componente) novos | Crítica/maior nova | Decisão igual à base | Decisão |",
                "|---|---|---|---|---|---|"]
        for l in linhas:
            p = l["pontuacao"]
            out.append(f"| `{l['pasta']}` | {', '.join(p['falhas_que_citam_a_reformulacao']) or '—'} | "
                       f"{p['pares_novos_vs_baseline'] if p['pares_novos_vs_baseline'] is not None else 'sem baseline'} | "
                       f"{p['critica_ou_maior_nova']} | {p['decisao_igual_ao_baseline']} | {l['decisao']} |")
    out += ["", "## Auditorias determinísticas (informativas)", ""]
    todas = Counter()
    for l in linhas:
        for o in l["auditoria"] or []:
            todas[o["regra"]] += 1
    if not linhas:
        out.append("Sem pareceres válidos.")
    else:
        for regra_aud in ("id_inexistente", "soma_de_minutos_no_texto", "nota_3_sem_id_do_plano",
                          "justificativa_repetida", "componente_provavelmente_errado"):
            quais = [l["pasta"] for l in linhas if any(o["regra"] == regra_aud for o in (l["auditoria"] or []))]
            out.append(f"- `{regra_aud}`: {len(quais)}/{len(linhas)} pareceres" + (f" ({', '.join(quais)})" if quais else "") + ".")
        sem_caso = [l["pasta"] for l in linhas if l["auditoria"] is None]
        if sem_caso:
            out.append(f"- Sem `caso.json` para auditar: {', '.join(sem_caso)}.")
    out += ["", "## Custo e tempo informados", "",
            f"- Tokens por julgamento (somente respostas com `usage`): {_faixa([l['tokens'] for l in linhas])}.",
            f"- Tempo total por execução em segundos: {_faixa([l['tempo_s'] for l in linhas])}.",
            "- Decisões: " + (", ".join(f"{k}: {v}" for k, v in Counter(l['decisao'] for l in linhas).items()) or "n/d") + "."]
    if a["falhas_tecnicas"]:
        out += ["", "## Falhas técnicas (separadas dos pareceres)", "", "| Execução | Tipo | Erro |", "|---|---|---|"]
        out += [f"| `{f['pasta']}` | {f['tipo']} | {f['erro']} |" for f in a["falhas_tecnicas"]]
    if a["avisos"]:
        out += ["", "## Avisos", ""] + [f"- {x}" for x in a["avisos"]]
    return "\n".join(out) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description="Análise mecânica provisória de uma série de ensaios do Juiz.")
    parser.add_argument("--pasta", required=True, type=Path, help="Pasta com os ensaios (local/ensaios_juiz).")
    parser.add_argument("--regra", required=True, type=Path, help="Arquivo de pontuação da variante.")
    parser.add_argument("--versao-prompt", help="Antes da série existir: conta os controles válidos desta versão (ex.: juiz-v1.3).")
    parser.add_argument("--baseline-pasta", type=Path, help="Pasta com os ensaios do caso original (só para controles).")
    parser.add_argument("--saida", type=Path, help="Grava o relatório (não sobrescreve).")
    args = parser.parse_args(argv)
    try:
        regra = ler_json(args.regra.read_text(encoding="utf-8-sig"))
        relatorio = renderizar_relatorio(analisar(args.pasta, regra, args.baseline_pasta, args.versao_prompt))
        if args.saida:
            with args.saida.open("x", encoding="utf-8", newline="\n") as arquivo:
                arquivo.write(relatorio)
            print(f"Relatório gravado em {args.saida}")
        else:
            print(relatorio)
        return 0
    except (OSError, ValueError, KeyError, ErroGeracao) as erro:
        print(f"Erro: {type(erro).__name__}: {erro}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
