"""Sondagem descartável do AgenteOpenAI da PoC 03, sem alterar os módulos do projeto.

Coloque este arquivo em aula-ia-backend e execute com OPENAI_API_KEY definida.
Registra respostas e erros em local/teste_api/. Uma rodada completa faz seis
chamadas cobradas; uma falha pode interromper o fluxo antes disso.
"""
import argparse
import io
import json
import os
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
from urllib import error
from uuid import uuid4

BASE = Path(__file__).resolve().parent
CHAMADAS = []
ATUAL = {"agente": None}
CHAVE = ""

ESPERADO = {
    "objetivos": {"objetivos"},
    "metodologia": {"metodologia", "recursos"},
    "sequencia": {"etapas"},
    "avaliacao": {"avaliacao"},
    "adaptacao": {"adaptacoes"},
    "integrador": {"titulo", "habilidade_codigo", "habilidade_texto", "ano", "tema",
                   "duracao_min", "tipo", "objetivos", "metodologia", "recursos",
                   "etapas", "avaliacao", "adaptacoes"},
}


def proteger(valor):
    """Evita gravar a chave se ela aparecer em texto de erro ou de resposta."""
    if isinstance(valor, str):
        return valor.replace(CHAVE, "[CHAVE REMOVIDA]") if CHAVE else valor
    if isinstance(valor, list):
        return [proteger(v) for v in valor]
    if isinstance(valor, dict):
        return {k: proteger(v) for k, v in valor.items()}
    return valor


def positivo(valor):
    try:
        numero = int(valor)
        if numero > 0:
            return numero
    except ValueError:
        pass
    raise argparse.ArgumentTypeError("informe um número inteiro maior que zero")


def carregar_projeto():
    try:
        import geracao
        return geracao
    except ImportError as exc:
        raise RuntimeError("Não foi possível importar geracao.py. Coloque este arquivo na pasta "
                           "aula-ia-backend, ao lado de geracao.py. Detalhe: " + str(exc)) from exc


def montar_entrada(duracao):
    caminho = BASE / "data" / "bncc_8ano.json"
    try:
        dados = json.loads(caminho.read_text(encoding="utf-8"))
        lista = dados if isinstance(dados, list) else dados["habilidades"]
        hab = next(h for h in lista if h.get("codigo") == "EF08CO03")
        campos = ("codigo", "habilidade", "eixo", "objeto_conhecimento", "explicacao", "exemplos")
        habilidade = {k: hab[k] for k in campos}
    except (OSError, ValueError, KeyError, TypeError, StopIteration) as exc:
        raise RuntimeError(f"Não foi possível ler a habilidade EF08CO03 em {caminho}: {exc}") from exc
    return {"contexto": {"ano": "8º ano", "tema": "Quero ensinar ordenação",
                          "duracao_min": duracao, "recursos": "papel e cartões",
                          "tipo": "Computação desplugada"}, "habilidade": habilidade}


def registrar_urlopen(original):
    def urlopen_registrado(pedido, timeout=None):
        inicio = time.perf_counter()
        reg = {"agente": ATUAL["agente"]}
        try:
            with original(pedido, timeout=timeout) as resp:
                corpo = resp.read()
                reg["http_status"] = getattr(resp, "status", None)
                headers = getattr(resp, "headers", {})
                reg["request_id"] = headers.get("x-request-id") if headers else None
            # O próprio geracao.py limita sua leitura a 500.000 bytes. Devolvemos
            # os mesmos bytes para que ele mantenha o comportamento original.
            texto = corpo.decode("utf-8", "replace")
            reg["resposta_http_bruta"] = proteger(texto)
            try:
                bruto = json.loads(corpo)
                if isinstance(bruto, dict):
                    choices = bruto.get("choices")
                    escolha = choices[0] if isinstance(choices, list) and choices else {}
                    escolha = escolha if isinstance(escolha, dict) else {}
                    mensagem = escolha.get("message")
                    mensagem = mensagem if isinstance(mensagem, dict) else {}
                    reg.update(modelo_respondeu=bruto.get("model"), usage=bruto.get("usage"),
                               finish_reason=escolha.get("finish_reason"),
                               conteudo_bruto=proteger(mensagem.get("content")),
                               recusa=proteger(mensagem.get("refusal")))
            except (ValueError, UnicodeDecodeError):
                pass
            return io.BytesIO(corpo)
        except error.HTTPError as exc:
            reg.update(erro=f"HTTP {exc.code}", http_status=exc.code)
            try:
                reg["erro_corpo"] = proteger(exc.read().decode("utf-8", "replace"))
            except Exception as leitura:
                reg["erro_leitura"] = proteger(f"{type(leitura).__name__}: {leitura}")
            raise
        except Exception as exc:
            reg["erro"] = proteger(f"{type(exc).__name__}: {exc}")
            raise
        finally:
            reg["latencia_s"] = round(time.perf_counter() - inicio, 3)
            CHAMADAS.append(proteger(reg))
    return urlopen_registrado


def inspecionar(reg, entrada):
    achados = []
    conteudo = reg.get("conteudo_bruto")
    if not isinstance(conteudo, str):
        return ["O conteúdo da mensagem não é texto JSON; consulte recusa e resposta_http_bruta."]
    try:
        saida = json.loads(conteudo)
    except ValueError:
        return ["Conteúdo não é JSON válido."]
    if not isinstance(saida, dict):
        return [f"Conteúdo é {type(saida).__name__}, não objeto."]
    esperado = ESPERADO.get(reg.get("agente"))
    if esperado is not None:
        faltam, extras = esperado - saida.keys(), saida.keys() - esperado
        if faltam:
            achados.append(f"FALTAM chaves: {sorted(faltam)}")
        if extras:
            achados.append(f"Chaves EXTRAS: {sorted(extras)}")
        if not faltam and not extras:
            achados.append("Chaves de primeiro nível correspondem ao esperado.")
    achados.append("Tipos: " + str({k: type(v).__name__ for k, v in saida.items()}))
    etapas = saida.get("etapas")
    if isinstance(etapas, list):
        minutos = [e.get("minutos") if isinstance(e, dict) else None for e in etapas]
        achados.append(f"Minutos por etapa: {minutos}; tipos: {[type(m).__name__ for m in minutos]}")
        if all(type(m) is int for m in minutos):
            achados.append(f"Soma: {sum(minutos)}; duração pedida: {entrada['contexto']['duracao_min']}")
        else:
            achados.append("Soma não calculada: há duração que não é inteiro.")
    if reg.get("agente") == "integrador":
        hab = entrada["habilidade"]
        achados.append(f"Código igual ao catálogo: {saida.get('habilidade_codigo') == hab['codigo']}")
        achados.append(f"Texto igual ao catálogo: {saida.get('habilidade_texto') == hab['habilidade']}")
    return achados


def resultado_chamadas(entrada):
    return [dict(c, inspecao=inspecionar(c, entrada) if "resposta_http_bruta" in c else [])
            for c in CHAMADAS]


def executar_rodada(geracao, modelo, entrada, numero):
    CHAMADAS.clear()
    class AgenteRegistrador(geracao.AgenteOpenAI):
        def executar(self, nome, entrada, estado, revisao):
            ATUAL["agente"] = nome
            return super().executar(nome, entrada, estado, revisao)
    resultado = {"rodada": numero, "status": "em_andamento", "modelo_pedido": modelo,
                 "entrada": entrada, "inicio": datetime.now().astimezone().isoformat(timespec="seconds")}
    inicio = time.perf_counter()
    try:
        gerador = geracao.GeradorDePlano("ia", modelo, agente=AgenteRegistrador(modelo))
        saida = gerador.gerar(entrada, 0)
        resultado.update(status="ok", plano=saida["plano"])
    except KeyboardInterrupt:
        resultado.update(status="interrompida", erro="Interrompida pelo usuário.")
    except Exception as exc:
        resultado.update(status="falha", erro=proteger(f"{type(exc).__name__}: {exc}"),
                         causa=proteger(f"{type(exc.__cause__).__name__}: {exc.__cause__}") if exc.__cause__ else None,
                         detalhes=proteger(traceback.format_exc()))
    resultado["tempo_total_s"] = round(time.perf_counter() - inicio, 3)
    resultado["chamadas"] = resultado_chamadas(entrada)
    return resultado


def resumir(resultado):
    print(f"\n=== Rodada {resultado['rodada']}: {resultado['status'].upper()} ===")
    if resultado.get("erro"):
        print("Erro:", resultado["erro"])
    if resultado.get("causa"):
        print("Causa técnica:", resultado["causa"])
    total, conhecidos = 0, 0
    for chamada in resultado["chamadas"]:
        uso = chamada.get("usage") or {}
        tokens = uso.get("total_tokens") if isinstance(uso, dict) else None
        if type(tokens) is int:
            total += tokens
            conhecidos += 1
        print(f"\n[{chamada.get('agente')}] {chamada.get('latencia_s')} s | "
              f"tokens: {tokens if tokens is not None else '?'} | "
              f"finish: {chamada.get('finish_reason')} | modelo: {chamada.get('modelo_respondeu')}")
        if chamada.get("erro"):
            print("  ERRO:", chamada["erro"], chamada.get("erro_corpo", ""))
        for linha in chamada.get("inspecao", []):
            print("  -", linha)
    print(f"\nChamadas registradas: {len(resultado['chamadas'])}; "
          f"tokens conhecidos: {total} ({conhecidos} chamada(s) com usage); "
          f"tempo total: {resultado['tempo_total_s']} s")
    print("Observação: OK indica apenas que a validação mecânica atual passou; não é aprovação pedagógica.")


def main():
    global CHAVE
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--modelo", default="gpt-4o-mini", help="modelo usado pelo gerador (padrão: gpt-4o-mini)")
    parser.add_argument("--rodadas", type=positivo, default=1)
    parser.add_argument("--duracao", type=positivo, default=50, help="duração da aula, em minutos")
    args = parser.parse_args()
    CHAVE = os.environ.get("OPENAI_API_KEY", "").strip()
    if not CHAVE:
        parser.exit(1, "Defina OPENAI_API_KEY no terminal antes de executar o teste.\n")
    try:
        geracao = carregar_projeto()
        entrada = montar_entrada(args.duracao)
        geracao.AgenteOpenAI(args.modelo)
        destino = BASE / "local" / "teste_api"
        destino.mkdir(parents=True, exist_ok=True)
    except Exception as exc:
        parser.exit(1, proteger(f"Preparação falhou: {exc}\n"))
    arquivo = destino / f"{datetime.now():%Y%m%d-%H%M%S}-{uuid4().hex[:8]}.json"
    registro = {"descricao": "Teste exploratório do gerador existente; não é aprovação pedagógica.",
                "modelo_pedido": args.modelo, "rodadas_solicitadas": args.rodadas, "rodadas": []}
    def salvar():
        arquivo.write_text(json.dumps(proteger(registro), ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        salvar()
    except OSError as exc:
        parser.exit(1, f"Não foi possível criar o arquivo de resultados: {exc}\n")
    original = geracao.request.urlopen
    geracao.request.urlopen = registrar_urlopen(original)
    print(f"API real: {args.rodadas} rodada(s), até 6 chamadas por rodada, modelo {args.modelo}.")
    print("As chamadas podem gerar cobrança. Resultados:", arquivo, flush=True)
    codigo = 0
    try:
        for numero in range(1, args.rodadas + 1):
            print(f"\nIniciando rodada {numero}...", flush=True)
            resultado = executar_rodada(geracao, args.modelo, entrada, numero)
            registro["rodadas"].append(resultado)
            salvar()
            resumir(resultado)
            if resultado["status"] != "ok":
                codigo = 1
                print("\nTeste encerrado após a falha/interrupção para evitar chamadas adicionais.")
                break
    except OSError as exc:
        print(f"Erro ao salvar resultados: {exc}", file=sys.stderr)
        codigo = 1
    except KeyboardInterrupt:
        print("\nTeste interrompido. As rodadas já concluídas foram salvas.")
        codigo = 130
    finally:
        geracao.request.urlopen = original
    print(f"\nRegistro completo salvo em: {arquivo}")
    return codigo


if __name__ == "__main__":
    sys.exit(main())
