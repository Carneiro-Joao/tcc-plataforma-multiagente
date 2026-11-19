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

from contratos import juiz_v1 as contrato
from juiz import avaliar_plano, criar_agente_groq_juiz

RAIZ = Path(__file__).resolve().parent.parent
PARECER_DEMONSTRACAO = RAIZ / "experimentos" / "juiz" / "demonstracao" / "parecer_controle_v13.json"
REPAROS = 1
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

    def __init__(self, agente=None, **kwargs):
        self.agente = agente or criar_agente_groq_juiz(**{**PARAMETROS_EXPERIMENTOS, **kwargs})
        self.modelo = self.agente.modelo
        self.versao_prompt = getattr(self.agente, "versao_prompt", contrato.VERSAO_PROMPT)

    def avaliar(self, plano, entrada, *, modelo_gerador, revisao, ciclo):
        resultado = avaliar_plano(plano, entrada, self.agente, modelo_gerador=modelo_gerador, modelo_juiz=self.modelo,
                                  revisao=revisao, reparos=REPAROS, ciclos_usados=ciclo)
        resultado.update(modo=self.modo, versao_prompt=self.versao_prompt, demonstracao=False)
        return resultado


class JuizDemonstracao:
    modo = "demonstracao"

    def __init__(self, arquivo=PARECER_DEMONSTRACAO):
        self.gravado = json.loads(Path(arquivo).read_text(encoding="utf-8"))
        contrato.validar(self.gravado["parecer"])
        self.modelo = self.gravado["modelo_juiz"]
        self.versao_prompt = self.gravado["versao_prompt"]

    def avaliar(self, plano, entrada, *, modelo_gerador, revisao, ciclo):
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
