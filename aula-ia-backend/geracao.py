"""Cinco especialistas, contratos por etapa e integração determinística."""
from copy import deepcopy
import time
import re
from contratos import VERSAO, validar, integrar
from erros import ErroGeracao, ErroContrato
from gemini import AgenteGemini, MODELO_PADRAO


def validar_saida(plano, entrada):
    validar("plano", plano, entrada)


def distribuicao_tempo(total):
    """Divide o tempo em etapas positivas, somando exatamente o tempo informado."""
    n = min(4, total)
    pesos = [15, 20, 45, 20] if n == 4 else [1] * n
    livre = total - n
    unidades = [livre * peso / sum(pesos) for peso in pesos]
    inteiros = [int(v) for v in unidades]
    resto = livre - sum(inteiros)
    for i in sorted(range(n), key=lambda j: (unidades[j] - inteiros[j], -j), reverse=True)[:resto]:
        inteiros[i] += 1
    return [n + 1 for n in inteiros]


class AgenteDemonstrativo:
    """Estratégias por regras, para conferir o fluxo sem rede nem chave de IA."""
    def executar(self, nome, entrada, estado, revisao, *, registro=None, reparo=None):
        c, h = entrada["contexto"], entrada["habilidade"]
        tema = re.sub(r"^(?:quero ensinar|gostaria de ensinar|quero uma aula sobre)\s+", "", c["tema"].strip(), flags=re.IGNORECASE).rstrip(". ")
        descricao = h["habilidade"].rstrip(". ")
        ordenacao = h["codigo"] == "EF08CO03" and bool(re.search(r"ordena|lista", tema, re.IGNORECASE))
        recursos = c["recursos"]
        diferentes = revisao % 3
        if nome == "objetivos":
            if ordenacao:
                return {"objetivos": [
                    "Ordenar uma lista curta de números usando um procedimento explícito.",
                    "Representar as etapas de um algoritmo de ordenação por seleção ou trocas sucessivas.",
                    "Comparar soluções e justificar como verificar se a lista está em ordem crescente.",
                ]}
            return {"objetivos": [
                f"Relacionar a habilidade {h['codigo']} ao tema {tema}.",
                f"Aplicar, em situação orientada, a ação curricular: {descricao.lower()}.",
                "Explicar o procedimento utilizado e revisar os resultados com a turma.",
            ]}
        if nome == "metodologia":
            estrategias = ["resolução colaborativa de problemas", "investigação guiada em pequenos grupos", "desafio prático com discussão entre pares"]
            return {"metodologia": f"{c['tipo']}; {estrategias[diferentes]}. A atividade deve usar os recursos realmente disponíveis.",
                    "recursos": recursos}
        if nome == "sequencia":
            roteiro = [
                [("Abertura", f"Apresentar o tema {tema} e recuperar conhecimentos prévios."),
                 ("Exploração", f"Ler a habilidade {h['codigo']} com exemplos do cotidiano."),
                 ("Prática", f"Em grupos, resolver um desafio de {tema}, registrando as decisões com {recursos}."),
                 ("Síntese", "Comparar as soluções, explicar decisões e registrar dúvidas.")],
                [("Problema inicial", f"Propor uma situação-problema relacionada a {tema}."),
                 ("Hipóteses", "Reunir as hipóteses dos estudantes e planejar como testá-las."),
                 ("Desafio", f"Usar {recursos} para testar soluções ligadas à habilidade {h['codigo']}."),
                 ("Socialização", "Debater os resultados e identificar pontos de melhoria.")],
                [("Diagnóstico", f"Perguntar o que os estudantes já sabem sobre {tema}."),
                 ("Demonstração", f"Modelar uma aplicação simples da habilidade {h['codigo']}."),
                 ("Aplicação", f"Organizar duplas para executar e comparar procedimentos usando {recursos}."),
                 ("Fechamento", "Solicitar uma explicação individual da estratégia adotada.")],
            ][diferentes]
            if ordenacao:
                roteiro = [
                    [("Desafio inicial", "Apresentar cartões com números fora de ordem e pedir uma solução rápida em duplas."),
                     ("Modelagem", "Demonstrar como encontrar o menor elemento e colocá-lo na posição correta da lista."),
                     ("Prática desplugada", f"Com {recursos}, ordenar uma sequência de cartões; anotar cada troca e conferir o resultado."),
                     ("Reflexão", "Comparar os passos das equipes e explicar como verificar se a ordenação terminou.")],
                    [("Problema inicial", "Apresentar cinco cartões embaralhados e perguntar como organizar a lista com um método reproduzível."),
                     ("Hipóteses", "Em grupos, registrar duas possíveis estratégias para encontrar números fora de ordem."),
                     ("Investigação", f"Usando {recursos}, testar as duas estratégias, anotar passos e comparar as soluções."),
                     ("Socialização", "Identificar diferenças entre estratégias e justificar uma sequência correta de ordenação.")],
                    [("Diagnóstico", "Pedir que cada dupla organize uma lista numérica pequena e explique o caminho escolhido."),
                     ("Demonstração", "Representar passo a passo um algoritmo de seleção do menor valor em uma lista."),
                     ("Aplicação", f"Com {recursos}, executar a ordenação, registrar cada passo e testar outra lista."),
                     ("Fechamento", "Produzir instruções claras para que outra dupla reproduza o algoritmo.")],
                ][diferentes]
            duracoes = distribuicao_tempo(c["duracao_min"])
            return {"etapas": [{"etapa": titulo, "minutos": minuto, "atividade": atividade}
                               for (titulo, atividade), minuto in zip(roteiro, duracoes)]}
        if nome == "avaliacao":
            if ordenacao:
                return {"avaliacao": "Avaliação formativa: propor uma lista nova de cinco números, observar a sequência de passos registrada por cada dupla e verificar se todos conseguem explicar por que o resultado ficou em ordem crescente."}
            return {"avaliacao": "Acompanhamento formativo: observar a participação, verificar os registros da prática e solicitar que cada estudante explique como a solução atende à habilidade confirmada."}
        if nome == "adaptacao":
            return {"adaptacoes": [
                "Oferecer instruções divididas em passos e exemplos adicionais quando necessário.",
                "Permitir registro escrito, diagramado ou oral, conforme a atividade e as possibilidades da turma.",
            ]}
        raise ErroGeracao(f"Agente demonstrativo inexistente: {nome}")


class GeradorDePlano:
    ESPECIALISTAS = ("objetivos", "metodologia", "sequencia", "avaliacao", "adaptacao")
    ORDEM = ESPECIALISTAS + ("integrador",)
    DEPENDENCIAS = {
        "objetivos": (), "metodologia": ("objetivos",),
        "sequencia": ("objetivos", "metodologia"),
        "avaliacao": ("objetivos", "metodologia", "sequencia"),
        "adaptacao": ("objetivos", "metodologia", "sequencia"),
    }

    def __init__(self, modo="demonstracao", modelo=MODELO_PADRAO, agente=None, reparos=1):
        if modo not in ("demonstracao", "ia") or type(reparos) is not int or reparos not in (0, 1):
            raise ValueError("Modo ou limite de reparos inválido.")
        self.modo = modo
        self.modelo = modelo if modo == "ia" else None
        self.reparos = reparos if modo == "ia" else 0
        self.agente = agente or (AgenteGemini(modelo) if modo == "ia" else AgenteDemonstrativo())

    def gerar(self, entrada, revisao, progresso=None):
        estado, rastreio = {}, []
        inicio = time.perf_counter()
        try:
            for nome in self.ESPECIALISTAS:
                dependencias = {k: deepcopy(estado[k]) for k in self.DEPENDENCIAS[nome]}
                reparo = None
                for tentativa in range(1, self.reparos + 2):
                    reg = {"agente": nome, "tentativa": tentativa,
                           "entrada": {"contexto": deepcopy(entrada["contexto"]),
                                       "habilidade": deepcopy(entrada["habilidade"]),
                                       "saidas_anteriores": deepcopy(dependencias)},
                           "estado": "processando"}
                    if reparo:
                        reg["reparo"] = deepcopy(reparo)
                    rastreio.append(reg)
                    if progresso:
                        progresso(reg)
                    try:
                        saida = self.agente.executar(nome, deepcopy(entrada), deepcopy(dependencias),
                                                     revisao, registro=reg, reparo=deepcopy(reparo))
                        reg["saida"] = deepcopy(saida)
                        validar(nome, saida, entrada)
                    except ErroContrato as erro:
                        reg.update(estado="rejeitado", erro=str(erro), tipo_erro=erro.tipo)
                        if tentativa > self.reparos:
                            raise
                        reparo = {"erro": str(erro), "resposta_anterior": reg.get("conteudo_bruto", reg.get("saida")),
                                  "instrucao": "Corrija exclusivamente o contrato do especialista, mantendo a mesma entrada confirmada."}
                        continue
                    except ErroGeracao as erro:
                        reg.update(estado="falha", erro=str(erro), tipo_erro=erro.tipo)
                        raise
                    reg["estado"] = "validado"
                    estado[nome] = deepcopy(saida)
                    break
            plano = integrar(entrada, estado)
            rastreio.append({"agente": "integrador", "tipo": "deterministico", "estado": "validado",
                            "entrada": {"contexto": deepcopy(entrada["contexto"]),
                                        "habilidade": deepcopy(entrada["habilidade"]),
                                        "saidas_anteriores": deepcopy(estado)}, "saida": deepcopy(plano)})
        except (ErroGeracao, KeyboardInterrupt) as erro:
            if rastreio and rastreio[-1]["estado"] == "processando":
                rastreio[-1]["estado"] = "interrompido"
            erro.rastreio = deepcopy(rastreio)
            raise
        except Exception:
            if rastreio and rastreio[-1]["estado"] == "processando":
                rastreio[-1].update(estado="falha", erro="Falha interna na geração.", tipo_erro="interno")
            erro = ErroGeracao("Falha interna na geração. Consulte os testes e o registro técnico.", tipo="interno")
            erro.rastreio = deepcopy(rastreio)
            raise erro from None
        return {"plano": plano, "rastreio": rastreio, "modo": self.modo,
                "provedor": "gemini" if self.modo == "ia" else "regras",
                "modelo": self.modelo, "revisao": revisao, "contrato": VERSAO,
                "tempo_total_s": round(time.perf_counter() - inicio, 3),
                "avaliacao_pedagogica": "pendente", "criterios_mecanicos": {
                    "habilidade_confirmada_preservada": True,
                    "duracao_total_confere": True, "contratos_por_etapa_validos": True,
                }}
