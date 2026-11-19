"""IA Juiz: uma chamada de avaliação sobre o plano integrado, com um reparo técnico opcional.

Este módulo NÃO altera o plano, NÃO executa correções e NÃO persiste nada.
Ele devolve o parecer validado, a decisão calculada por código e o rastreio.
A ligação ao pipeline (ciclos de correção, estados no banco) é a etapa seguinte.
"""
from copy import deepcopy
from contratos import juiz_v1 as contrato
from contratos import plano_v2
from contratos.esquema_gemini import projetar
from erros import ErroContrato, ErroGeracao
from gemini import AgenteGemini, MODELO_PADRAO


VERSAO_ESQUEMA_API = "parecer-juiz-1.0-estrutura-v1"


def esquema_api(nome="juiz"):
    """Reutiliza a projeção Gemini; o contrato completo continua obrigatório localmente."""
    return projetar(contrato.esquema(nome))


class AgenteGeminiJuiz(AgenteGemini):
    versao_esquema_api = VERSAO_ESQUEMA_API

    def __init__(self, modelo=MODELO_PADRAO, **kwargs):
        super().__init__(modelo, esquema_saida=esquema_api,
                         instrucoes={"juiz": contrato.instrucoes()},
                         versao_contrato=contrato.VERSAO, versao_prompt=contrato.VERSAO_PROMPT, **kwargs)

    def executar(self, nome, entrada, estado, revisao, *, registro, reparo=None):
        registro.update(versao_esquema_api=self.versao_esquema_api, versao_rubrica=contrato.rubrica.VERSAO)
        return super().executar(nome, entrada, estado, revisao, registro=registro, reparo=reparo)


def criar_agente_juiz(modelo=MODELO_PADRAO, **kwargs):
    """Agente Gemini configurado com o esquema projetado e a instrução do Juiz.
    Aceita os mesmos kwargs do AgenteGemini (chave, transporte, timeout, repeticoes_503).
    Use, de preferência, um modelo diferente do que gerou o plano (viés de autopreferência)."""
    return AgenteGeminiJuiz(modelo, **kwargs)


def criar_agente_groq_juiz(**kwargs):
    """Provedor da PoC 05B; a fábrica Gemini anterior permanece compatível."""
    from groq_juiz import AgenteGroqJuiz
    return AgenteGroqJuiz(**kwargs)


def avaliar_plano(plano, entrada, agente, *, modelo_gerador, modelo_juiz, revisao=0,
                  reparos=1, ciclos_usados=0, politica=None, antes_do_reparo=None):
    """`antes_do_reparo`: chamado logo antes da tentativa de reparo (ex.: esperar a cota por minuto do provedor).
    Padrão None = comportamento dos experimentos (reparo imediato)."""
    if type(reparos) is not int or reparos not in (0, 1):
        raise ValueError("Limite de reparos inválido.")
    politica_usada = contrato.resolver_politica(politica, ciclos_usados=ciclos_usados)
    if type(revisao) is not int or revisao < 0:
        raise ValueError("Revisão deve ser um inteiro não negativo.")
    for modelo in (modelo_gerador, modelo_juiz):
        if not isinstance(modelo, str) or not modelo.strip():
            raise ValueError("Informe os identificadores dos modelos gerador e juiz.")
    if getattr(agente, "modelo", modelo_juiz) != modelo_juiz:
        raise ValueError("Modelo do Juiz informado difere do configurado no agente.")
    plano_v2.validar_entrada(entrada)
    plano_v2.validar("plano", plano, entrada)
    estado, rastreio, reparo, saida = {"plano": deepcopy(plano)}, [], None, None
    for tentativa in range(1, reparos + 2):
        if tentativa > 1 and antes_do_reparo is not None:
            antes_do_reparo()
        reg = {"agente": "juiz", "tentativa": tentativa, "estado": "processando",
               "revisao": revisao, "ciclos_usados": ciclos_usados,
               "versao_rubrica": contrato.rubrica.VERSAO, "politica": deepcopy(politica_usada),
               "entrada": {"contexto": deepcopy(entrada["contexto"]),
                           "habilidade": deepcopy(entrada["habilidade"]),
                           "saidas_anteriores": deepcopy(estado)}}
        if reparo:
            reg["reparo"] = deepcopy(reparo)
        rastreio.append(reg)
        try:
            saida = agente.executar("juiz", deepcopy(entrada), deepcopy(estado), revisao,
                                    registro=reg, reparo=deepcopy(reparo))
            reg["saida"] = deepcopy(saida)
            contrato.validar(saida)
        except ErroContrato as erro:
            reg.update(estado="rejeitado", erro=str(erro), tipo_erro=erro.tipo,
                       diagnosticos=deepcopy(getattr(erro, "diagnosticos", [])))
            if tentativa > reparos:
                erro.rastreio = deepcopy(rastreio)
                raise
            reparo = {"erro": str(erro), "diagnosticos": reg["diagnosticos"],
                      "resposta_anterior": reg.get("conteudo_bruto", reg.get("saida")),
                      "instrucao": "Corrija exclusivamente o contrato do parecer, mantendo o mesmo plano avaliado."}
            continue
        except ErroGeracao as erro:
            reg.update(estado="falha", erro=str(erro), tipo_erro=erro.tipo)
            erro.rastreio = deepcopy(rastreio)
            raise
        reg["estado"] = "validado"
        break
    return {"contrato": contrato.VERSAO, "versao_rubrica": contrato.rubrica.VERSAO,
            "revisao": revisao, "parecer": saida,
            "decisao": contrato.decidir(saida, ciclos_usados, politica_usada),
            "modelo_juiz": modelo_juiz, "modelo_gerador": modelo_gerador,
            "modelo_distinto_do_gerador": modelo_juiz != modelo_gerador,
            "versao_esquema_api": getattr(agente, "versao_esquema_api", None),
            "politica": politica_usada, "rastreio": rastreio}
