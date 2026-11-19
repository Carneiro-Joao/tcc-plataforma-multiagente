"""IA Juiz como etapa automática da geração (PoC 08): adaptadores usados por ServicoCurricular.gerar.

- JuizGroq: avaliação real (Groq, openai/gpt-oss-120b), MESMA configuração dos experimentos: prompt juiz-v1.3, rubrica 0.1,
  politica-juiz-prelim-0.1, reparos 1, temperature 0, max_completion_tokens 8192, reasoning_effort medium, seed 42.
- JuizDemonstracao: sem rede; devolve um parecer REAL já gravado (controle do plano original, juiz-v1.3), marcado como
  demonstração. Serve de plano B e para testes. Não avalia o plano exibido.
O Juiz é consultivo: nunca aprova o plano; a decisão final é do professor.
"""
from copy import deepcopy
import json
from pathlib import Path
import threading
import time

from contratos import juiz_v1 as contrato
from juiz import avaliar_plano, criar_agente_groq_juiz

RAIZ = Path(__file__).resolve().parent.parent
PARECER_DEMONSTRACAO = RAIZ / "experimentos" / "juiz" / "demonstracao" / "parecer_controle_v13.json"
REPAROS = 1
# Groq (plano gratuito): 8.000 tokens por minuto e ~6–7 mil por avaliação. O reparo logo após a 1ª chamada estourava a cota
# (HTTP 429 em 19/11/2026, 13:18). No app, espera-se antes do reparo; prompt, modelo, rubrica e reparos não mudam.
PAUSA_ANTES_DO_REPARO_S = 60
# Intervalo mínimo entre o INÍCIO de duas chamadas reais ao Groq neste processo (pedidos seguidos ou a avaliação da
# regeneração, ~40 s depois da 1ª); depois de HTTP 413, intervalo maior. Mesmos valores da regra 2 do CLAUDE.md.
INTERVALO_MINIMO_S = 75
INTERVALO_APOS_413_S = 120
PARAMETROS_EXPERIMENTOS = dict(timeout=90, temperature=0, max_completion_tokens=8192, reasoning_effort="medium", seed=42,
                               versao_prompt="juiz-v1.3")

# Texto para o professor, a partir do próximo estado calculado pela política (nunca é aprovação).
ROTULOS = {"aguardando_decisao": "Favorável", "em_correcao": "Com ressalvas", "revisao_necessaria": "Revisão recomendada"}
NAO_FAVORAVEL = ("em_correcao", "revisao_necessaria")


def falhas_graves(parecer):
    """Quantidade de falhas 'maior' ou 'critica' (critério de 'melhor versão' quando nenhuma é favorável)."""
    return sum(1 for f in parecer["falhas"] if f["gravidade"] in ("maior", "critica"))


class JuizGroq:
    modo = "groq"

    def __init__(self, agente=None, *, pausa_reparo_s=PAUSA_ANTES_DO_REPARO_S, intervalo_s=INTERVALO_MINIMO_S,
                 intervalo_413_s=INTERVALO_APOS_413_S, dormir=time.sleep, relogio=time.monotonic, **kwargs):
        self.pausa_reparo_s, self.dormir, self.relogio = pausa_reparo_s, dormir, relogio
        self.intervalo_s, self.intervalo_413_s = intervalo_s, intervalo_413_s
        # O ThreadingHTTPServer atende pedidos em paralelo: a reserva da próxima chamada é feita sob lock.
        self._trava = threading.Lock()
        self._ultima = None  # (instante de início da última chamada real, terminou em HTTP 413)
        self.agente = agente or criar_agente_groq_juiz(**{**PARAMETROS_EXPERIMENTOS, **kwargs})
        self.modelo = self.agente.modelo
        self.versao_prompt = getattr(self.agente, "versao_prompt", contrato.VERSAO_PROMPT)

    def _reservar_chamada(self, ao_esperar=None):
        """Espera o que faltar do intervalo mínimo desde o início da chamada anterior e reserva o início desta."""
        with self._trava:
            if self._ultima is not None:
                inicio, foi_413 = self._ultima
                falta = (self.intervalo_413_s if foi_413 else self.intervalo_s) - (self.relogio() - inicio)
                if falta > 0:
                    if ao_esperar:
                        ao_esperar(falta)
                    self.dormir(falta)
                    if ao_esperar:
                        ao_esperar(0)
            self._ultima = (self.relogio(), False)
            return self._ultima[0]

    def _antes_do_reparo(self):
        self.dormir(self.pausa_reparo_s)  # reparo: 60 s (cota por minuto); a chamada de reparo vira a "última"
        with self._trava:
            self._ultima = (self.relogio(), False)

    def avaliar(self, plano, entrada, *, modelo_gerador, revisao, ciclo, ao_esperar=None):
        self._reservar_chamada(ao_esperar)
        try:
            resultado = avaliar_plano(plano, entrada, self.agente, modelo_gerador=modelo_gerador, modelo_juiz=self.modelo,
                                      revisao=revisao, reparos=REPAROS, ciclos_usados=ciclo,
                                      antes_do_reparo=self._antes_do_reparo)
        except Exception as erro:
            if "413" in str(erro):
                with self._trava:
                    if self._ultima is not None:
                        self._ultima = (self._ultima[0], True)
            raise
        resultado.update(modo=self.modo, versao_prompt=self.versao_prompt, demonstracao=False)
        return resultado


class JuizDemonstracao:
    modo = "demonstracao"

    def __init__(self, arquivo=PARECER_DEMONSTRACAO):
        self.gravado = json.loads(Path(arquivo).read_text(encoding="utf-8"))
        contrato.validar(self.gravado["parecer"])
        self.modelo = self.gravado["modelo_juiz"]
        self.versao_prompt = self.gravado["versao_prompt"]

    def avaliar(self, plano, entrada, *, modelo_gerador, revisao, ciclo, ao_esperar=None):  # sem rede: nunca espera
        parecer = deepcopy(self.gravado["parecer"])
        return {"contrato": contrato.VERSAO, "versao_rubrica": contrato.rubrica.VERSAO, "revisao": revisao,
                "parecer": parecer, "decisao": contrato.decidir(parecer, ciclo),
                "modelo_juiz": self.modelo, "modelo_gerador": modelo_gerador,
                "politica": contrato.resolver_politica(ciclos_usados=ciclo), "rastreio": [],
                "modo": self.modo, "versao_prompt": self.versao_prompt, "demonstracao": True,
                "aviso_demonstracao": "Parecer real GRAVADO de outro plano (controle, " + self.gravado["fonte"] + "); "
                                      "não avalia este plano."}


def criar_juiz(modo, **kwargs):
    """'groq' | 'demonstracao' | 'desligado' (None)."""
    if modo == "groq":
        return JuizGroq(**kwargs)
    if modo == "demonstracao":
        return JuizDemonstracao()
    if modo == "desligado":
        return None
    raise ValueError(f"Modo do Juiz desconhecido: {modo!r}")
