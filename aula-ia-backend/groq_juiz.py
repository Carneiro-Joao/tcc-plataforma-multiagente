"""GroqCloud REST para a IA Juiz; sem SDK, fallback ou retentativa HTTP."""
from datetime import datetime, timezone
import json
import math
import os
import re
import time
from urllib import error, request

from contratos import juiz_v1 as contrato
from contratos.execucao import ler_json
from erros import ErroContrato, ErroGeracao

MODELO_PADRAO = "openai/gpt-oss-120b"
ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"
VERSAO_ADAPTADOR = "groq-juiz-0.1"
VERSAO_ESQUEMA_API = "parecer-juiz-1.0-groq-strict-v1"
LIMITE_RESPOSTA = 1_000_000


def sanitizar(valor, chave=None):
    """Remove credenciais inclusive se o provedor as ecoar; nunca serializa headers."""
    chave = chave or os.environ.get("GROQ_API_KEY", "").strip()
    if isinstance(valor, str):
        if chave:
            valor = valor.replace(chave, "[CHAVE_REMOVIDA]")
        return re.sub(r"gsk_[A-Za-z0-9_-]+", "[CHAVE_REMOVIDA]", valor)
    if isinstance(valor, list):
        return [sanitizar(v, chave) for v in valor]
    if isinstance(valor, tuple):
        return [sanitizar(v, chave) for v in valor]
    if isinstance(valor, dict):
        return {sanitizar(k, chave): sanitizar(v, chave) for k, v in valor.items()}
    return valor


class _SemRedirecionamento(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Authorization nunca deve acompanhar um redirecionamento.
        return None


class AgenteGroqJuiz:
    versao_esquema_api = VERSAO_ESQUEMA_API

    def __init__(self, modelo=MODELO_PADRAO, *, chave=None, transporte=None,
                 timeout=90, temperature=0, max_completion_tokens=8192,
                 reasoning_effort="medium", seed=42):
        self.chave = (chave if chave is not None else os.environ.get("GROQ_API_KEY", "")).strip()
        if not self.chave or any(c.isspace() for c in self.chave):
            raise ErroGeracao("Defina GROQ_API_KEY no terminal do ensaio.", tipo="configuracao")
        if modelo != MODELO_PADRAO:
            raise ErroGeracao("Esta PoC usa openai/gpt-oss-120b, sem fallback.", tipo="configuracao")
        if (type(timeout) not in (int, float) or not math.isfinite(timeout) or not 0 < timeout <= 300
                or type(temperature) not in (int, float) or not math.isfinite(temperature)
                or not 0 <= temperature <= 2
                or type(max_completion_tokens) is not int or not 1 <= max_completion_tokens <= 65536
                or reasoning_effort not in ("low", "medium", "high")
                or type(seed) is not int or not 0 <= seed <= 2147483647):
            raise ErroGeracao("Parâmetros Groq inválidos.", tipo="configuracao")
        self.modelo, self.timeout = modelo, timeout
        self.parametros = dict(temperature=temperature, max_completion_tokens=max_completion_tokens,
                               reasoning_effort=reasoning_effort, seed=seed,
                               include_reasoning=False, stream=False)
        self.transporte = transporte or request.build_opener(_SemRedirecionamento()).open

    def executar(self, nome, entrada, estado, revisao, *, registro, reparo=None):
        if nome != "juiz":
            raise ErroGeracao("O adaptador Groq só executa a IA Juiz.", tipo="configuracao")
        dados = dict(contexto=entrada["contexto"], habilidade=entrada["habilidade"],
                     revisao=revisao, saidas_anteriores=estado)
        if reparo:
            dados["reparo_estrutural"] = reparo
        corpo = dict(model=self.modelo, **self.parametros, messages=[
            {"role": "system", "content": contrato.instrucoes()},
            {"role": "user", "content": json.dumps(dados, ensure_ascii=False, allow_nan=False)},
        ], response_format={"type": "json_schema", "json_schema": {
            "name": "parecer_juiz", "strict": True, "schema": contrato.esquema()}})
        seguro = lambda valor: sanitizar(valor, self.chave)
        if seguro(corpo) != corpo:
            raise ErroGeracao("Entrada recusada por conter credencial.", tipo="configuracao")
        registro.update(provedor="groq", modelo_pedido=self.modelo,
                        versao_adaptador=VERSAO_ADAPTADOR, versao_contrato=contrato.VERSAO,
                        versao_prompt=contrato.VERSAO_PROMPT, versao_rubrica=contrato.rubrica.VERSAO,
                        versao_esquema_api=self.versao_esquema_api, requisicao=corpo,
                        iniciado_em=datetime.now(timezone.utc).isoformat(), timeout_s=self.timeout,
                        chamadas_http=0)
        pedido = request.Request(ENDPOINT, data=json.dumps(corpo, ensure_ascii=False).encode("utf-8"),
                                 headers={"Content-Type": "application/json", "Authorization": "Bearer " + self.chave,
                                          "User-Agent": "AulaIA-PoC05B/0.1"}, method="POST")
        inicio = time.perf_counter()
        try:
            try:
                registro["chamadas_http"] = 1
                with self.transporte(pedido, timeout=self.timeout) as resposta:
                    registro["http_status"] = resposta.status
                    self._headers(resposta.headers, registro)
                    bruto = resposta.read(LIMITE_RESPOSTA + 1)
            except error.HTTPError as exc:
                registro["http_status"] = exc.code
                self._headers(exc.headers, registro)
                try:
                    registro["erro_corpo"] = seguro(exc.read(10000).decode("utf-8", "replace"))
                except OSError:
                    registro["erro_corpo"] = "Corpo de erro indisponível."
                finally:
                    exc.close()
                orientacao = {400: "Confira esquema e parâmetros.", 401: "Confira GROQ_API_KEY.",
                              403: "Confira permissões da conta/modelo.", 404: "Confira a disponibilidade do modelo.",
                              429: "Limite atingido; consulte Retry-After e cotas da conta."}.get(
                                  exc.code, "Provedor indisponível ou redirecionamento recusado.")
                raise ErroGeracao(f"Groq HTTP {exc.code}: {orientacao} Sem repetição automática.", tipo="http") from None
            except (error.URLError, TimeoutError, OSError) as exc:
                registro["erro_transporte"] = seguro(str(exc))
                raise ErroGeracao("Falha de conexão ou timeout ao chamar Groq; sem repetição automática.",
                                  tipo="transporte") from None
            if registro["http_status"] != 200:
                raise ErroGeracao("Status HTTP inesperado da Groq.", tipo="http")
            if len(bruto) > LIMITE_RESPOSTA:
                raise ErroGeracao("Resposta Groq excedeu o limite de leitura.", tipo="resposta_api")
            try:
                raw = ler_json(bruto.decode("utf-8"))
                if not isinstance(raw, dict):
                    raise ValueError()
            except (ErroContrato, ValueError, UnicodeError):
                raise ErroGeracao("Groq retornou envelope inválido.", tipo="resposta_api") from None
            registro.update(resposta_api=seguro(raw), usage=seguro(raw.get("usage")),
                            modelo_respondeu=seguro(raw.get("model")), response_id=seguro(raw.get("id")),
                            system_fingerprint=seguro(raw.get("system_fingerprint")))
            if raw.get("model") != self.modelo:
                raise ErroGeracao("Modelo retornado pela Groq difere do solicitado.", tipo="resposta_api")
            choices = raw.get("choices")
            if not isinstance(choices, list) or len(choices) != 1 or not isinstance(choices[0], dict):
                raise ErroGeracao("Groq não retornou uma escolha única.", tipo="resposta_api")
            choice = choices[0]
            registro["finish_reason"] = seguro(choice.get("finish_reason"))
            message = choice.get("message")
            if not isinstance(message, dict):
                raise ErroGeracao("Groq retornou mensagem inválida.", tipo="resposta_api")
            if message.get("refusal") or choice.get("finish_reason") == "content_filter":
                raise ErroGeracao("Groq recusou a avaliação.", tipo="bloqueio")
            texto = message.get("content")
            registro["conteudo_bruto"] = seguro(texto)
            if choice.get("finish_reason") != "stop":
                raise ErroGeracao("Groq não concluiu o parecer. Consulte finish_reason.", tipo="resposta_incompleta")
            if not isinstance(texto, str) or not texto.strip():
                raise ErroGeracao("Groq retornou conteúdo vazio ou inválido.", tipo="resposta_api")
            if seguro(raw) != raw:
                raise ErroGeracao("Resposta recusada por conter credencial.", tipo="resposta_api")
            # O contrato e os invariantes completos são aplicados por avaliar_plano.
            return ler_json(texto)
        finally:
            registro["latencia_s"] = round(time.perf_counter() - inicio, 6)

    def _headers(self, headers, registro):
        permitidos = ("x-request-id", "retry-after", "x-ratelimit-limit-requests", "x-ratelimit-limit-tokens",
                      "x-ratelimit-remaining-requests", "x-ratelimit-remaining-tokens",
                      "x-ratelimit-reset-requests", "x-ratelimit-reset-tokens")
        registro["headers_metricas"] = {k: sanitizar(headers.get(k), self.chave) for k in permitidos
                                       if headers and headers.get(k) is not None}
