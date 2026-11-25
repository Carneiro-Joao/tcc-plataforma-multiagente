"""Sondagem PoC 09 (pré-registro: docs/PoC09_Sondagem_Regeneracao_Informada.md): regeneração CEGA × INFORMADA pelas críticas do Juiz.

Uso (pasta aula-ia-backend):
  python sondagem_regeneracao_informada.py                 (chamadas reais: Gemini + Groq; teto de 14 gerações e 14 avaliações)
  python sondagem_regeneracao_informada.py --somente-validar  (sem rede: gerador e Juiz de demonstração)

Não altera o app nem o banco (só leitura). Usa as MESMAS classes do app (GeradorDePlanoCompleto + AgenteGeminiCompleto 2.3 e JuizGroq);
no braço informado, um transporte embrulhado acrescenta `revisao_pedagogica` aos DADOS da chamada de cada especialista — o prompt de
sistema e as instruções não mudam. Resultados em local/sondagem_c/<UTC>/ (nunca sobrescreve). A chave nunca é impressa nem gravada.
"""
import argparse
from contextlib import closing
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import time
from urllib import request

from casos_juiz import exportar_sqlite
from contratos import juiz_v1, plano_v2
from erros import ErroGeracao
from exportar_planos import tem_credencial
from gemini import MODELO_PADRAO
from geracao_v2 import AgenteGeminiCompleto, GeradorDePlanoCompleto
from groq_juiz import sanitizar
from juiz_servico import JuizDemonstracao, JuizGroq, falhas_graves
from medir_planos import campos_sem_acento, material_ausente
from rede import transporte_ipv4

BASE = Path(__file__).resolve().parent
VERSAO_REVISAO = "revisao-informada-sondagem-0.1"
INSTRUCAO = (
    "A versão anterior deste componente foi avaliada por uma IA Juiz. Em revisao_pedagogica estão a sua versão anterior "
    "(versao_anterior), as falhas atribuídas a este componente (falhas_deste_componente, com descrição, gravidade, critério e "
    "correção sugerida) e as falhas de outros componentes (outras_falhas, só como contexto). Produza uma nova versão que corrija as "
    "falhas deste componente, priorizando as de gravidade maior ou crítica. Siga as correções sugeridas apenas quando forem "
    "compatíveis com o contexto confirmado (recursos, tipo de aula, duração e habilidade): nunca acrescente recursos, materiais ou "
    "dispositivos fora de contexto.recursos. Mantenha o contrato e a coerência com as saídas anteriores recebidas nesta chamada."
)
CASOS = (  # pré-registrados (tabela do protocolo)
    dict(n=1, geracao="a3b450f3bf734faeadaee29db75c4245", parecer="local/ensaios_juiz/20261119T144542Z-22e0c849d313/resultado.json"),
    dict(n=2, geracao="f98d522efb83489a889da0c9a5e4a901", parecer="local/ensaios_juiz/20261119T144703Z-04b72cd5f7c1/resultado.json"),
    dict(n=3, geracao="f67ad3b5ac704238b89d5556c9afec6b", parecer="local/ensaios_juiz/20261119T144944Z-af30e69d7832/resultado.json"),
    dict(n=4, geracao="d08006bf5b5f4c2296931eb12b518b4e", parecer="local/ensaios_juiz/20261119T145105Z-aea4ed435c8c/resultado.json"),
    dict(n=5, geracao="a1ddae3ec8cf4887a743fc2455c128f1", parecer=None),  # parecer na tabela `pareceres` do app
)
TETO_GERACOES, TETO_AVALIACOES, PAUSA_FALHA_S, REVISAO = 14, 14, 60, 2


def revisao_pedagogica(nome, anteriores, parecer):
    """O que o especialista `nome` recebe no braço informado."""
    falhas = [dict(id=f["id"], componente=f["componente"], gravidade=f["gravidade"], criterio=f["criterio"],
                   descricao=f["descricao"], correcao_sugerida=f.get("correcao_sugerida", "")) for f in parecer["falhas"]]
    return {"versao": VERSAO_REVISAO, "instrucao": INSTRUCAO, "versao_anterior": deepcopy(anteriores.get(nome)),
            "falhas_deste_componente": [f for f in falhas if f["componente"] == nome],
            "outras_falhas": [f for f in falhas if f["componente"] != nome]}


class AgenteInformado(AgenteGeminiCompleto):
    """AgenteGeminiCompleto 2.3 que sabe qual especialista está chamando (para o transporte injetar a revisão certa)."""

    def __init__(self, revisoes, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.revisoes, self.nome_atual = revisoes, None

    def executar(self, nome, entrada, estado, revisao, *, registro, reparo=None):
        self.nome_atual = nome
        if self.revisoes.get(nome) is not None:
            registro["revisao_pedagogica"] = deepcopy(self.revisoes[nome])
        return super().executar(nome, entrada, estado, revisao, registro=registro, reparo=reparo)


def transporte_informado(agente, base):
    """Embrulha o transporte HTTP: acrescenta `revisao_pedagogica` aos dados do usuário; o resto da requisição fica igual."""
    def enviar(pedido, timeout):
        revisao = agente.revisoes.get(agente.nome_atual)
        if revisao is not None:
            corpo = json.loads(pedido.data.decode("utf-8"))
            parte = corpo["contents"][0]["parts"][0]
            dados = json.loads(parte["text"])
            dados["revisao_pedagogica"] = revisao
            parte["text"] = json.dumps(dados, ensure_ascii=False)
            pedido = request.Request(pedido.full_url, data=json.dumps(corpo, ensure_ascii=False).encode("utf-8"),
                                     headers=dict(pedido.header_items()), method=pedido.get_method())
        return base(pedido, timeout=timeout)
    return enviar


def carregar(banco, item):
    """Plano e entrada da 1ª versão, saídas de cada especialista (rastreio) e o parecer real que ela recebeu."""
    caso = exportar_sqlite(banco, item["geracao"])
    uri = Path(banco).resolve().as_uri() + "?mode=ro"
    with closing(sqlite3.connect(uri, uri=True)) as db:
        resultado = json.loads(db.execute("SELECT resultado FROM geracoes WHERE id = ?", (item["geracao"],)).fetchone()[0])
        if item["parecer"] is None:
            linha = db.execute("SELECT resultado FROM pareceres WHERE geracao_id = ? AND estado = 'ok' ORDER BY criado_em LIMIT 1",
                               (item["geracao"],)).fetchone()
            parecer = json.loads(linha[0])["parecer"]
        else:
            parecer = json.loads((BASE / item["parecer"]).read_text(encoding="utf-8"))["resultado"]["parecer"]
    anteriores = {r["agente"]: r["saida"] for r in resultado["rastreio"]
                  if r.get("estado") == "validado" and r.get("agente") in plano_v2.ETAPAS}
    juiz_v1.validar(parecer)
    return dict(caso=caso, anteriores=anteriores, parecer=parecer)


def pares_graves(parecer):
    return {(f["componente"], f["criterio"]) for f in parecer["falhas"] if f["gravidade"] in ("maior", "critica")}


def medir(plano, parecer, entrada, parecer_original):
    contexto = entrada["contexto"]
    return dict(graves=falhas_graves(parecer), decisao=juiz_v1.decidir(parecer)["proximo_estado"],
                graves_repetidas=len(pares_graves(parecer_original) & pares_graves(parecer)),
                h1_material_ausente=material_ausente(plano, contexto["recursos"]), h2_sem_acentos=campos_sem_acento(plano),
                contrato_ok=not plano_v2.diagnosticar("plano", plano, entrada),
                minutos_ok=sum(e["minutos"] for e in plano["desenvolvimento"]) == contexto["duracao_min"],
                notas={a["criterio"]: a["nota"] for a in parecer["avaliacoes"]})


class Contador:
    def __init__(self):
        self.geracoes = self.avaliacoes = 0


def com_nova_tentativa(rotulo, funcao, contador, campo, teto, dormir, eventos):
    """Executa; falha técnica → espera 60 s e tenta 1 vez. Respeita o teto de chamadas. Devolve (resultado|None, erros)."""
    erros = []
    for tentativa in (1, 2):
        if getattr(contador, campo) >= teto:
            erros.append(f"teto de {teto} {campo} atingido")
            break
        if tentativa == 2:
            eventos(f"    {rotulo}: falha técnica; nova tentativa em {PAUSA_FALHA_S} s")
            dormir(PAUSA_FALHA_S)
        setattr(contador, campo, getattr(contador, campo) + 1)
        try:
            return funcao(), erros
        except (ErroGeracao, ValueError) as erro:
            erros.append(sanitizar(str(erro))[:300])
    return None, erros


def rodar(banco, destino, *, somente_validar=False, dormir=time.sleep, eventos=print, fabrica_agente=None, juiz=None):
    destino = Path(destino) / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    destino.mkdir(parents=True, exist_ok=False)
    contador, linhas = Contador(), []
    juiz = juiz or (JuizDemonstracao() if somente_validar else JuizGroq())
    for item in CASOS:
        dados = carregar(banco, item)
        entrada, parecer0 = dados["caso"]["entrada"], dados["parecer"]
        x = entrada["contexto"]
        eventos(f"#{item['n']} {x['tema']} · {x['tipo']} · {x['duracao_min']} min — 1ª versão: {falhas_graves(parecer0)} grave(s)")
        registro = dict(n=item["n"], geracao_origem=item["geracao"], contexto=x, habilidade=entrada["habilidade"]["codigo"],
                        primeira=dict(graves=falhas_graves(parecer0), decisao=juiz_v1.decidir(parecer0)["proximo_estado"],
                                      pares_graves=sorted(pares_graves(parecer0))), bracos={})
        for braco in ("cego", "informado"):
            revisoes = ({n: revisao_pedagogica(n, dados["anteriores"], parecer0) for n in plano_v2.ETAPAS}
                        if braco == "informado" else {})
            if somente_validar:
                gerador = GeradorDePlanoCompleto("demonstracao")
            elif fabrica_agente is not None:
                gerador = GeradorDePlanoCompleto("ia", agente=fabrica_agente(revisoes), reparos=1)
            else:
                agente = AgenteInformado(revisoes, MODELO_PADRAO, transporte=transporte_ipv4(), repeticoes_503=2)
                agente.transporte = transporte_informado(agente, agente.transporte)
                gerador = GeradorDePlanoCompleto("ia", MODELO_PADRAO, agente=agente, reparos=1)
            inicio = time.time()
            gerado, erros_g = com_nova_tentativa(f"{braco}/geração", lambda: gerador.gerar(entrada, REVISAO), contador,
                                                 "geracoes", TETO_GERACOES, dormir, eventos)
            linha = dict(caso=item["n"], braco=braco, erros_geracao=erros_g, segundos_geracao=round(time.time() - inicio, 1))
            if gerado is not None:
                avaliado, erros_j = com_nova_tentativa(
                    f"{braco}/Juiz", lambda: juiz.avaliar(gerado["plano"], entrada, modelo_gerador=gerado.get("modelo") or MODELO_PADRAO,
                                                          revisao=REVISAO, ciclo=0, ao_esperar=lambda s: s and eventos(f"    aguardando a cota do Juiz ({s:.0f} s)")),
                    contador, "avaliacoes", TETO_AVALIACOES, dormir, eventos)
                linha.update(erros_juiz=erros_j)
                if avaliado is not None:
                    linha.update(medir(gerado["plano"], avaliado["parecer"], entrada, parecer0))
                registro["bracos"][braco] = dict(plano=gerado["plano"], rastreio=gerado.get("rastreio", []),
                                                 parecer=avaliado and avaliado["parecer"], linha=linha)
            else:
                registro["bracos"][braco] = dict(linha=linha)
            eventos("   " + resumo_linha(linha))
            linhas.append(linha)
        salvar(destino / f"caso_{item['n']}.json", registro)
    resumo = dict(protocolo="docs/PoC09_Sondagem_Regeneracao_Informada.md", versao_revisao=VERSAO_REVISAO, somente_validar=somente_validar,
                  modelo_gerador=MODELO_PADRAO, juiz=dict(modo=juiz.modo, modelo=juiz.modelo, versao_prompt=juiz.versao_prompt),
                  geracoes=contador.geracoes, avaliacoes=contador.avaliacoes, codigo=versao_git(), linhas=linhas)
    salvar(destino / "resumo.json", resumo)
    texto = tabela(linhas)
    (destino / "resumo.md").write_text(texto + "\n", encoding="utf-8")
    eventos(texto)
    eventos(f"Chamadas: {contador.geracoes} gerações, {contador.avaliacoes} avaliações. Resultados: {destino}")
    return resumo, destino


def resumo_linha(l):
    if "graves" not in l:
        return f"{l['braco']}: FALHA TÉCNICA {l.get('erros_geracao') or l.get('erros_juiz')}"
    return (f"{l['braco']}: {l['graves']} grave(s), {l['decisao']}, repetidas {l['graves_repetidas']}, "
            f"H1 {l['h1_material_ausente'] or '—'}, contrato {'ok' if l['contrato_ok'] else 'FALHA'}")


def tabela(linhas):
    saida = ["| Braço | Planos avaliados | Falhas graves (soma) | Favoráveis | Graves repetidas (soma) | H1 material ausente | H2 sem acento | Contrato ok | Falhas técnicas |",
             "|---|---|---|---|---|---|---|---|---|"]
    for braco in ("cego", "informado"):
        ls = [l for l in linhas if l["braco"] == braco]
        ok = [l for l in ls if "graves" in l]
        saida.append(f"| {braco} | {len(ok)}/{len(ls)} | {sum(l['graves'] for l in ok)} | "
                     f"{sum(l['decisao'] == 'aguardando_decisao' for l in ok)}/{len(ok)} | {sum(l['graves_repetidas'] for l in ok)} | "
                     f"{sum(bool(l['h1_material_ausente']) for l in ok)}/{len(ok)} | {sum(bool(l['h2_sem_acentos']) for l in ok)}/{len(ok)} | "
                     f"{sum(l['contrato_ok'] for l in ok)}/{len(ok)} | {sum(len(l.get('erros_geracao', [])) + len(l.get('erros_juiz', [])) for l in ls)} |")
    return "\n".join(saida)


def salvar(caminho, dados):
    dados = sanitizar(dados)
    if tem_credencial(dados):
        raise ValueError(f"Recusado: {caminho.name} conteria credencial.")
    caminho.write_text(json.dumps(dados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def versao_git():
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=BASE, capture_output=True, text=True, timeout=5).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None


def main(argv=None):
    p = argparse.ArgumentParser(description="Sondagem PoC 09: regeneração cega × informada pelas críticas do Juiz.")
    p.add_argument("--banco", type=Path, default=BASE / "local" / "consultas.sqlite3")
    p.add_argument("--destino", type=Path, default=BASE / "local" / "sondagem_c")
    p.add_argument("--somente-validar", action="store_true", help="Sem rede: gerador e Juiz de demonstração.")
    args = p.parse_args(argv)
    rodar(args.banco, args.destino, somente_validar=args.somente_validar,
          dormir=(lambda s: None) if args.somente_validar else time.sleep)
    return 0


if __name__ == "__main__":
    sys.exit(main())
