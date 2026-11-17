"""IA Juiz: uma chamada de avaliação sobre o plano integrado, com um reparo técnico opcional.

Este módulo NÃO altera o plano, NÃO executa correções e NÃO persiste nada.
Ele devolve o parecer validado, a decisão calculada por código e o rastreio.
A ligação ao pipeline (ciclos de correção, estados no banco) é a etapa seguinte.
"""
from copy import deepcopy
from contratos import juiz_v1 as contrato
from erros import ErroContrato, ErroGeracao
from gemini import AgenteGemini, MODELO_PADRAO


def criar_agente_juiz(modelo=MODELO_PADRAO, **kwargs):
    """Agente Gemini configurado com o esquema e a instrução do Juiz.
    Use, de preferência, um modelo diferente do que gerou o plano (viés de autopreferência)."""
    return AgenteGemini(modelo, esquema_saida=contrato.esquema, instrucoes={"juiz": contrato.instrucoes()},
                        versao_contrato=contrato.VERSAO, versao_prompt=contrato.VERSAO_PROMPT, **kwargs)


def avaliar_plano(plano, entrada, agente, *, modelo_gerador, modelo_juiz, revisao=0,
                  reparos=1, ciclos_usados=0, politica=None):
    if type(reparos) is not int or reparos not in (0, 1):
        raise ValueError("Limite de reparos inválido.")
    estado, rastreio, reparo, saida = {"plano": deepcopy(plano)}, [], None, None
    for tentativa in range(1, reparos + 2):
        reg = {"agente": "juiz", "tentativa": tentativa, "estado": "processando"}
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
    politica_usada = dict(contrato.POLITICA_PRELIMINAR, **(politica or {}))
    return {"contrato": contrato.VERSAO, "parecer": saida,
            "decisao": contrato.decidir(saida, ciclos_usados, politica),
            "modelo_juiz": modelo_juiz, "modelo_gerador": modelo_gerador,
            "modelo_distinto_do_gerador": modelo_juiz != modelo_gerador,
            "politica": politica_usada, "rastreio": rastreio}
