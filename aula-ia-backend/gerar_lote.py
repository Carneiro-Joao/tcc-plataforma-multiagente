"""Gera em lote os planos de um protocolo pelo MESMO caminho do app: consultar -> confirmar -> gerar.

Uso:
  python gerar_lote.py --entradas ../experimentos/geracao/poc07b_entradas.json --limite-diario 12
  python gerar_lote.py --entradas ... --somente-validar      (gerador de demonstração, banco temporário, sem rede)

- Banco: o mesmo do app (local/consultas.sqlite3) e o MESMO limite diário de gerações com IA (ServicoCurricular).
- Gerador: GeradorDePlanoCompleto("ia") com AgenteGeminiCompleto (prompt padrão do código), IPv4 e 503 repetido como no app.
- Habilidade: confirma exatamente a indicada; se a busca pelo tema não a trouxer, refaz a consulta no modo "catalogo".
- Pausa entre planos. Falha técnica (HTTP, contrato, resposta): registrada pelo próprio serviço; espera e refaz a linha UMA vez,
  com consulta nova (o plano continua sendo revisão 1). Falhou de novo: segue. Duas falhas seguidas de cota (HTTP 429) ou o limite
  diário atingido: PARA tudo. Nunca apaga nem sobrescreve; só insere pelo serviço.
- A chave fica na variável de ambiente GEMINI_API_KEY; nunca é impressa nem gravada.
"""
import argparse
import json
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import time

from erros import ErroGeracao
from gemini import MODELO_PADRAO, REPETICOES_503_PADRAO
from geracao_v2 import AgenteGeminiCompleto, GeradorDePlanoCompleto
from rag.search import BASE, BuscaCurricular
from rede import transporte_ipv4
from servico import ErroConsulta, ServicoCurricular

CAMPOS = ("tema", "tipo", "duracao_min", "recursos", "habilidade")
PAUSA_ENTRE_PLANOS = 30
PAUSA_APOS_FALHA = 60


def ler_entradas(caminho):
    """Lista de dicts com exatamente os campos do protocolo (+ "ano" opcional). Erro claro se algo faltar ou sobrar."""
    dados = json.loads(Path(caminho).read_text(encoding="utf-8"))
    linhas = dados.get("entradas") if isinstance(dados, dict) else dados
    if not isinstance(linhas, list) or not linhas:
        raise ValueError("O arquivo de entradas deve ter uma lista não vazia (ou {\"entradas\": [...]}).")
    for i, e in enumerate(linhas, 1):
        if not isinstance(e, dict):
            raise ValueError(f"Entrada {i}: deve ser um objeto.")
        faltando = [c for c in CAMPOS if c not in e]
        sobrando = sorted(set(e) - set(CAMPOS) - {"ano"})
        if faltando or sobrando:
            raise ValueError(f"Entrada {i}: faltando {faltando}, sobrando {sobrando}.")
        if type(e["duracao_min"]) is not int or e["duracao_min"] <= 0:
            raise ValueError(f"Entrada {i}: duracao_min deve ser inteiro positivo.")
        for c in ("tema", "tipo", "recursos", "habilidade"):
            if not isinstance(e[c], str) or not e[c].strip():
                raise ValueError(f"Entrada {i}: {c} deve ser texto não vazio.")
    return linhas


def eh_cota(mensagem):
    return "HTTP 429" in mensagem or "cota" in mensagem.lower()


def _consultar_e_confirmar(servico, entrada):
    contexto = dict(ano=entrada.get("ano", "8º ano"), tema=entrada["tema"], duracao_min=entrada["duracao_min"],
                    tipo=entrada["tipo"], recursos=entrada["recursos"])
    modo = "tema"
    consulta = servico.consultar({"contexto": contexto, "consulta": modo})
    if entrada["habilidade"] not in [r["habilidade"]["codigo"] for r in consulta["resultados"]]:
        modo = "catalogo"
        consulta = servico.consultar({"contexto": contexto, "consulta": modo})
    servico.confirmar(consulta["id"], entrada["habilidade"])
    return consulta["id"], modo


def executar_lote(entradas, servico, dormir=time.sleep, saida=print,
                  pausa=PAUSA_ENTRE_PLANOS, pausa_falha=PAUSA_APOS_FALHA):
    """Devolve (linhas, parou_por). Cada linha: dict(n, tema, tipo, situacao, tentativas, geracao_id, modo_consulta, erros)."""
    linhas, parou_por, cotas_seguidas = [], None, 0
    for n, entrada in enumerate(entradas, 1):
        if n > 1:
            dormir(pausa)
        linha = dict(n=n, tema=entrada["tema"], tipo=entrada["tipo"], situacao="falha", tentativas=0,
                     geracao_id=None, modo_consulta=None, erros=[])
        linhas.append(linha)
        for tentativa in (1, 2):
            if tentativa == 2:
                saida(f"  #{n} falha técnica; nova tentativa em {pausa_falha} s.")
                dormir(pausa_falha)
            try:
                id_consulta, linha["modo_consulta"] = _consultar_e_confirmar(servico, entrada)
            except ErroConsulta as erro:  # entrada recusada pelo app (ex.: tema não identificado): não é falha técnica
                linha.update(situacao="entrada recusada", erros=linha["erros"] + [f"{erro.status}: {erro}"])
                break
            linha["tentativas"] = tentativa
            try:
                resultado = servico.gerar(id_consulta)
            except ErroConsulta as erro:
                mensagem = str(erro)
                linha["erros"].append(f"{erro.status}: {mensagem}")
                if erro.status == 429:  # limite diário do app: nenhuma chamada foi feita
                    linha["situacao"] = "limite diário"
                    parou_por = "limite diário atingido"
                    break
                cotas_seguidas = cotas_seguidas + 1 if eh_cota(mensagem) else 0
                if cotas_seguidas >= 2:
                    parou_por = "duas falhas seguidas de cota (HTTP 429)"
                    break
                continue
            cotas_seguidas = 0
            geracao = resultado["geracao_atual"]
            linha.update(situacao="ok", geracao_id=geracao["id"], revisao=geracao["revisao"])
            break
        saida(resumo(linha))
        if parou_por:
            saida(f"PARADO: {parou_por}. Linhas seguintes não foram tentadas.")
            break
    return linhas, parou_por


def resumo(linha):
    base = f"#{linha['n']} {linha['tema']} | {linha['tipo']} | {linha['situacao']} | tentativas: {linha['tentativas']}"
    if linha["geracao_id"]:
        base += f" | geração {linha['geracao_id'][:8]} (revisão {linha['revisao']}, consulta por {linha['modo_consulta']})"
    if linha["erros"]:
        base += " | erros: " + " || ".join(e[:160] for e in linha["erros"])
    return base


def montar_gerador(somente_validar, modelo, ipv4, repeticoes_503, reparos):
    if somente_validar:
        return GeradorDePlanoCompleto("demonstracao", modelo, reparos=reparos)
    agente = AgenteGeminiCompleto(modelo, chave=os.environ.get("GEMINI_API_KEY", "").strip(),
                                  transporte=transporte_ipv4() if ipv4 else None, repeticoes_503=repeticoes_503)
    return GeradorDePlanoCompleto("ia", modelo, agente=agente, reparos=reparos)


def main(argv=None, dormir=time.sleep):
    p = argparse.ArgumentParser(description="Gera em lote os planos de um protocolo pelo mesmo caminho do app.")
    p.add_argument("--entradas", type=Path, required=True)
    p.add_argument("--banco", type=Path, default=BASE / "local" / "consultas.sqlite3")
    p.add_argument("--limite-diario", type=int, default=8, help="Mesmo limite do app (padrão 8). Não há opção para desligar.")
    p.add_argument("--modelo", default=MODELO_PADRAO)
    p.add_argument("--sem-ipv4", action="store_true", help="Não força IPv4 (o app do protocolo usa --ipv4).")
    p.add_argument("--repeticoes-503", type=int, choices=(0, 1, 2), default=REPETICOES_503_PADRAO)
    p.add_argument("--reparos", type=int, choices=(0, 1), default=1)
    p.add_argument("--somente-validar", action="store_true",
                   help="Gerador de demonstração, banco temporário, sem rede e sem pausas.")
    args = p.parse_args(argv)
    if args.limite_diario <= 0:
        p.error("--limite-diario deve ser positivo (o lote não roda sem limite).")
    try:
        entradas = ler_entradas(args.entradas)
    except (OSError, ValueError) as erro:
        p.exit(2, f"Entradas inválidas: {erro}\n")
    try:
        gerador = montar_gerador(args.somente_validar, args.modelo, not args.sem_ipv4, args.repeticoes_503, args.reparos)
    except ErroGeracao as erro:
        p.exit(2, f"Não foi possível iniciar a geração: {erro}\n")

    temporario = TemporaryDirectory(prefix="aulaia-lote-") if args.somente_validar else None
    try:
        banco = Path(temporario.name) / "lote.sqlite3" if temporario else args.banco
        limite = None if args.somente_validar else args.limite_diario
        servico = ServicoCurricular(BuscaCurricular("lexical"), banco, gerador, limite_diario_ia=limite)
        if args.somente_validar:
            print(f"SOMENTE VALIDAR: gerador de demonstração, banco temporário, sem rede. {len(entradas)} entradas.")
        else:
            usados, _ = servico.uso_hoje()
            print(f"Lote real: {len(entradas)} entradas · modelo {args.modelo} · banco {banco}")
            print(f"Limite: {limite} planos com IA por dia; usados hoje: {usados}; cabem: {max(0, limite - usados)}.")
        linhas, parou_por = executar_lote(entradas, servico, dormir=(lambda s: None) if args.somente_validar else dormir)
    finally:
        if temporario:
            temporario.cleanup()
    ok = sum(1 for l in linhas if l["situacao"] == "ok")
    print(f"Resumo: {ok}/{len(entradas)} planos gerados" + (f"; parado: {parou_por}" if parou_por else "") + ".")
    return 0 if ok == len(entradas) else (3 if parou_por else 1)


if __name__ == "__main__":
    sys.exit(main())
