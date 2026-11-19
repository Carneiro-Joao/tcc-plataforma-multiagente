"""CLI da PoC 05B: exportar um caso real ou avaliar um plano, sem executar correções."""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
import math
from pathlib import Path
import platform
import sqlite3
import subprocess
import time
from uuid import uuid4

from casos_juiz import exportar_sqlite, hash_json, salvar_novo, validar_caso
from contratos import juiz_v1 as contrato, plano_v2
from contratos.execucao import ler_json
from erros import ErroGeracao
from groq_juiz import MODELO_PADRAO, VERSAO_ADAPTADOR, VERSAO_ESQUEMA_API, sanitizar
from juiz import avaliar_plano, criar_agente_groq_juiz
from exportar_planos import tem_credencial

BASE = Path(__file__).resolve().parent
VERSAO_ENSAIO = "ensaio-juiz-0.1"


def versao_codigo():
    arquivos = ["ensaio_juiz.py", "casos_juiz.py", "groq_juiz.py", "juiz.py", "erros.py",
                "contratos/juiz_v1.py", "contratos/juiz_v1.schema.json", "contratos/rubrica_juiz.py",
                "contratos/plano_v2.py", "contratos/plano_v2.schema.json",
                "contratos/execucao.py", "contratos/validacao.py"]
    dados = {"sha": None, "arvore_modificada": None,
             "arquivos_sha256": {a: sha256((BASE / a).read_bytes()).hexdigest() for a in arquivos}}
    try:
        def git(*args):
            return subprocess.run(["git", *args], cwd=BASE, capture_output=True, text=True,
                                  check=True, timeout=5).stdout.strip()
        dados.update(sha=git("rev-parse", "HEAD"), arvore_modificada=bool(git("status", "--porcelain")))
    except (OSError, subprocess.SubprocessError):
        pass
    return dados


def metricas(rastreio):
    """Soma somente métricas informadas; ausência de uso nunca significa custo zero."""
    saida = {"tentativas_avaliacao": len(rastreio),
             "chamadas_http": sum(r.get("chamadas_http", 0) for r in rastreio),
             "respostas_com_usage": sum(isinstance(r.get("usage"), dict) for r in rastreio),
             "custo_informado": None}
    for campo in ("prompt_tokens", "completion_tokens", "total_tokens", "queue_time",
                  "prompt_time", "completion_time", "total_time"):
        valores = [(r.get("usage") or {}).get(campo) for r in rastreio if isinstance(r.get("usage"), dict)]
        valores = [v for v in valores if type(v) in (int, float) and math.isfinite(v) and v >= 0]
        saida[campo + "_conhecido"] = sum(valores) if valores else None
    return saida


def executar_ensaio(caminho, destino, *, reparos=0, somente_validar=False,
                     timeout=90, temperature=0, max_completion_tokens=8192,
                     reasoning_effort="medium", seed=42, versao_prompt=None, fabrica=criar_agente_groq_juiz):
    """Grava início antes da chamada; sucesso e falha preservam o mesmo identificador."""
    versao_prompt = contrato.resolver_versao_prompt(versao_prompt)
    prompt_sha256 = sha256(contrato.instrucoes(versao_prompt).encode("utf-8")).hexdigest()
    pasta = Path(destino) / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:12])
    pasta.mkdir(parents=True, exist_ok=False)
    inicio = time.perf_counter()
    registro = dict(versao_ensaio=VERSAO_ENSAIO, iniciado_em=datetime.now(timezone.utc).isoformat(),
                    status="iniciado", modo="validacao_local" if somente_validar else "api_real",
                    codigo=versao_codigo(), python=platform.python_version(),
                    contrato_plano=plano_v2.VERSAO, contrato_parecer=contrato.VERSAO,
                    versao_rubrica=contrato.rubrica.VERSAO, versao_prompt=versao_prompt,
                    prompt_sha256=prompt_sha256,
                    versao_adaptador=VERSAO_ADAPTADOR, versao_esquema_api=VERSAO_ESQUEMA_API,
                    politica=deepcopy(contrato.POLITICA_PRELIMINAR),
                    modelo_juiz=MODELO_PADRAO, reparos_contrato_permitidos=reparos,
                    ciclos_pedagogicos_executados=0, aprovacao_docente="nao_alterada",
                    parametros=dict(timeout_s=timeout, temperature=temperature,
                                    max_completion_tokens=max_completion_tokens,
                                    reasoning_effort=reasoning_effort, seed=seed), rastreio=[])
    salvar_novo(pasta / "inicio.json", sanitizar(registro))
    try:
        raw = Path(caminho).read_bytes()
        registro["arquivo_caso_sha256"] = sha256(raw).hexdigest()
        caso = validar_caso(ler_json(raw.decode("utf-8-sig")))
        if sanitizar(caso) != caso:
            raise ValueError("Caso recusado por conter credencial.")
        registro.update(origem=deepcopy(caso["origem"]), plano_sha256=hash_json(caso["plano"]),
                        entrada_sha256=hash_json(caso["entrada"]), modelo_gerador=caso["modelo_gerador"])
        # Plano e entrada originais preservados; nenhum dado sintético é promovido a real.
        salvar_novo(pasta / "caso.json", caso)
        if somente_validar:
            registro["status"] = "validado_localmente"
        else:
            agente = fabrica(timeout=timeout, temperature=temperature,
                              max_completion_tokens=max_completion_tokens, reasoning_effort=reasoning_effort, seed=seed,
                               versao_prompt=versao_prompt)
            resultado = avaliar_plano(caso["plano"], caso["entrada"], agente,
                                      modelo_gerador=caso["modelo_gerador"], modelo_juiz=MODELO_PADRAO,
                                      revisao=caso.get("revisao", 0), reparos=reparos, ciclos_usados=0)
            registro.update(status="sucesso", resultado=resultado, rastreio=resultado["rastreio"])
    except (ErroGeracao, ValueError, OSError, RecursionError) as exc:
        registro.update(status="falha", erro=str(exc), tipo_erro=getattr(exc, "tipo", "entrada_ou_arquivo"),
                        diagnosticos=getattr(exc, "diagnosticos", []), rastreio=getattr(exc, "rastreio", []))
    registro.update(finalizado_em=datetime.now(timezone.utc).isoformat(),
                    tempo_total_s=round(time.perf_counter() - inicio, 6), metricas=metricas(registro["rastreio"]))
    salvar_novo(pasta / "resultado.json", sanitizar(registro))
    return sanitizar(registro), pasta / "resultado.json"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="acao", required=True)
    exportar = sub.add_parser("exportar", help="Extrair geração específica do SQLite, sem modificá-lo")
    exportar.add_argument("--banco", required=True, type=Path)
    exportar.add_argument("--geracao-id", required=True)
    exportar.add_argument("--saida", required=True, type=Path)
    avaliar = sub.add_parser("avaliar", help="Avaliar caso congelado; não chama especialistas")
    avaliar.add_argument("--caso", required=True, type=Path)
    avaliar.add_argument("--destino", type=Path, default=BASE / "local" / "ensaios_juiz")
    avaliar.add_argument("--somente-validar", action="store_true", help="Sem rede nem chave")
    avaliar.add_argument("--reparos", type=int, choices=(0, 1), default=0,
                         help="Reparo de contrato do parecer; padrão 0. Nunca corrige o plano.")
    avaliar.add_argument("--timeout", type=float, default=90)
    avaliar.add_argument("--temperature", type=float, default=0)
    avaliar.add_argument("--max-completion-tokens", type=int, default=8192)
    avaliar.add_argument("--reasoning-effort", choices=("low", "medium", "high"), default="medium")
    avaliar.add_argument("--seed", type=int, default=42)
    avaliar.add_argument("--versao-prompt", choices=contrato.VERSOES_PROMPT,
                          default=contrato.VERSAO_PROMPT,
                          help="Prompt do Juiz; default v1.3, v1.2 preservado para comparação.")
    args = parser.parse_args(argv)
    try:
        if args.acao == "exportar":
            caso = exportar_sqlite(args.banco, args.geracao_id)
            if sanitizar(caso) != caso or tem_credencial(caso):
                raise ValueError("Exportação recusada por conter credencial.")
            salvar_novo(args.saida, caso)
            print("Caso exportado e validado:", args.saida)
            return 0
        resultado, arquivo = executar_ensaio(args.caso, args.destino, reparos=args.reparos,
                                             somente_validar=args.somente_validar, timeout=args.timeout,
                                             temperature=args.temperature, max_completion_tokens=args.max_completion_tokens,
                                             reasoning_effort=args.reasoning_effort, seed=args.seed,
                                             versao_prompt=args.versao_prompt)
        print("Status:", resultado["status"])
        print("Registro:", arquivo)
        if resultado["status"] == "falha":
            print("Erro:", resultado["erro"])
            return 1
        if resultado.get("resultado"):
            print("Decisão sugerida:", resultado["resultado"]["decisao"]["proximo_estado"])
        return 0
    except (OSError, ValueError, ErroGeracao, sqlite3.Error) as exc:
        print("Falha:", sanitizar(str(exc)))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
