"""Sondagem do mesmo pipeline do site: Gemini real ou --simular (sem rede).

Exemplos na pasta aula-ia-backend:
    python teste_gemini.py --simular
    python teste_gemini.py --rodadas 1 --duracao 50
Registros técnicos em local/teste_gemini/; não incluem headers ou chaves.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import time
from uuid import uuid4
from geracao import GeradorDePlano, ErroGeracao
from gemini import MODELO_PADRAO
from rag.search import BuscaCurricular
from servico import habilidade_publica

BASE = Path(__file__).resolve().parent


def inteiro_positivo(valor):
    numero = int(valor)
    if numero < 1:
        raise argparse.ArgumentTypeError("Use um inteiro positivo.")
    return numero


def salvar(destino, documento):
    temporario = destino.with_suffix(".tmp")
    temporario.write_text(json.dumps(documento, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
    temporario.replace(destino)


def resumir(rodada):
    print(f"\n=== Rodada {rodada['rodada']}: {rodada['status'].upper()} ===")
    if rodada.get("erro"):
        print("Erro:", rodada["erro"])
    chamadas = [r for r in rodada.get("rastreio", []) if r.get("provedor") == "gemini"]
    tokens, com_uso = 0, 0
    for reg in rodada.get("rastreio", []):
        uso = reg.get("usage") or {}
        total = uso.get("totalTokenCount") if isinstance(uso, dict) else None
        if type(total) is int:
            tokens += total
            com_uso += 1
        print(f"[{reg['agente']}] {reg['estado']} | tentativa {reg.get('tentativa', '-')} | "
              f"{reg.get('latencia_s', '-')} s | tokens {total if total is not None else '?'} | "
              f"finish {reg.get('finish_reason', '-')} | modelo {reg.get('modelo_respondeu', '-')}")
        if "saida" in reg and isinstance(reg["saida"], dict):
            print("  tipos:", {k: type(v).__name__ for k, v in reg["saida"].items()})
        if reg.get("erro"):
            print("  erro:", reg["erro"])
    print(f"Chamadas: {len(chamadas)}; tokens conhecidos: {tokens} ({com_uso} com uso); "
          f"tempo: {rodada['tempo_total_s']} s")
    print("OK indica estrutura válida; aprovação pedagógica continua pendente.")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--simular", action="store_true", help="Executa regras locais; não usa Gemini nem comprova sua qualidade.")
    parser.add_argument("--modelo", default=MODELO_PADRAO)
    parser.add_argument("--rodadas", type=inteiro_positivo, default=1)
    parser.add_argument("--duracao", type=inteiro_positivo, default=50)
    parser.add_argument("--reparos", type=int, choices=(0, 1), default=1)
    args = parser.parse_args(argv)
    if args.duracao > 1440:
        parser.error("Duração máxima: 1440 minutos.")
    try:
        gerador = GeradorDePlano("demonstracao" if args.simular else "ia", args.modelo, reparos=args.reparos)
    except ErroGeracao as e:
        parser.exit(1, f"{e}\n")
    hab = next(h for h in BuscaCurricular().documentos if h["codigo"] == "EF08CO03")
    entrada = {"contexto": {"ano": "8º ano", "tema": "Quero ensinar ordenação", "duracao_min": args.duracao,
                            "recursos": "papel e cartões", "tipo": "Computação desplugada"},
               "habilidade": habilidade_publica(hab)}
    pasta = BASE / "local" / "teste_gemini"
    pasta.mkdir(parents=True, exist_ok=True)
    destino = pasta / f"{datetime.now():%Y%m%d-%H%M%S}-{uuid4().hex[:8]}.json"
    documento = {"versao": "poc04a-0.1", "criado_em": datetime.now(timezone.utc).isoformat(),
                 "modo": gerador.modo, "modelo_pedido": gerador.modelo,
                 "entrada": entrada, "rodadas": []}
    salvar(destino, documento)
    print("SIMULAÇÃO sem API." if args.simular else f"Gemini real: {args.modelo}. Cinco chamadas normais; até {5*(1+args.reparos)} por rodada com reparos.", flush=True)
    if not args.simular:
        print("Use um projeto Free Tier no AI Studio. O script não consegue verificar seu faturamento e não troca de modelo automaticamente.", flush=True)
    print(f"Resultados: {destino}", flush=True)
    codigo = 0
    for n in range(1, args.rodadas + 1):
        rodada = {"rodada": n, "status": "processando", "rastreio": []}
        documento["rodadas"].append(rodada)
        inicio = time.perf_counter()
        def progresso(reg):
            rodada["rastreio"].append(reg)
            salvar(destino, documento)
            print(f"  Chamando {reg['agente']} (tentativa {reg['tentativa']})...", flush=True)
        try:
            resultado = gerador.gerar(entrada, n - 1, progresso=progresso)
            rodada.update(status="ok", **resultado)
        except ErroGeracao as erro:
            rodada.update(status="falha", erro=str(erro), tipo_erro=erro.tipo, rastreio=erro.rastreio)
            codigo = 1
        except KeyboardInterrupt as erro:
            rodada.update(status="interrompido", erro="Interrompido pelo usuário.", rastreio=getattr(erro, "rastreio", rodada["rastreio"]))
            codigo = 130
        finally:
            rodada["tempo_total_s"] = round(time.perf_counter() - inicio, 3)
            salvar(destino, documento)
        resumir(rodada)
        if codigo:
            print("Teste encerrado após falha/interrupção, sem iniciar outra rodada.")
            break
    print(f"\nRegistro salvo em: {destino}")
    return codigo


if __name__ == "__main__":
    raise SystemExit(main())
