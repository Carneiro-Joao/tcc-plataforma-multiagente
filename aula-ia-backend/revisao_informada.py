"""Regeneração informada pelas críticas da IA Juiz (PoC 10; opção C testada na sondagem PoC 09).

Quando o Juiz não dá parecer favorável, o plano inteiro é gerado de novo, mas cada especialista recebe, nos DADOS da chamada
(campo `revisao_pedagogica`), a sua versão anterior, as falhas que o Juiz atribuiu a ele (descrição, gravidade, critério e correção
sugerida) e as demais falhas só como contexto. O prompt de sistema e as instruções dos especialistas (`especialistas-plano-2.3`)
não mudam; a 1ª geração continua idêntica. O texto da instrução é o mesmo da sondagem (`revisao-informada-sondagem-0.1`).
"""
from copy import deepcopy

from contratos import plano_v2

VERSAO = "revisao-informada-1.0"
INSTRUCAO = (
    "A versão anterior deste componente foi avaliada por uma IA Juiz. Em revisao_pedagogica estão a sua versão anterior "
    "(versao_anterior), as falhas atribuídas a este componente (falhas_deste_componente, com descrição, gravidade, critério e "
    "correção sugerida) e as falhas de outros componentes (outras_falhas, só como contexto). Produza uma nova versão que corrija as "
    "falhas deste componente, priorizando as de gravidade maior ou crítica. Siga as correções sugeridas apenas quando forem "
    "compatíveis com o contexto confirmado (recursos, tipo de aula, duração e habilidade): nunca acrescente recursos, materiais ou "
    "dispositivos fora de contexto.recursos. Mantenha o contrato e a coerência com as saídas anteriores recebidas nesta chamada."
)


def saidas_do_rastreio(rastreio):
    """Última saída validada de cada especialista (a corrigida, se houve reparo)."""
    saidas = {}
    for registro in rastreio or []:
        if registro.get("estado") == "validado" and registro.get("agente") in plano_v2.ETAPAS:
            saidas[registro["agente"]] = deepcopy(registro.get("saida"))
    return saidas


def revisao_pedagogica(nome, anteriores, parecer):
    """O que o especialista `nome` recebe na regeneração informada."""
    falhas = [dict(id=f["id"], componente=f["componente"], gravidade=f["gravidade"], criterio=f["criterio"],
                   descricao=f["descricao"], correcao_sugerida=f.get("correcao_sugerida", "")) for f in parecer["falhas"]]
    return {"versao": VERSAO, "instrucao": INSTRUCAO, "versao_anterior": deepcopy(anteriores.get(nome)),
            "falhas_deste_componente": [f for f in falhas if f["componente"] == nome],
            "outras_falhas": [f for f in falhas if f["componente"] != nome]}


def montar_revisoes(rastreio_anterior, parecer):
    """{especialista: revisao_pedagogica} para todos os especialistas do PlanoDeAula 2.0."""
    anteriores = saidas_do_rastreio(rastreio_anterior)
    return {nome: revisao_pedagogica(nome, anteriores, parecer) for nome in plano_v2.ETAPAS}
