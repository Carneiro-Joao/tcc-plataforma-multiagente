"""PlanoDeAula 2.0: cinco especialidades, seis chamadas e integrador Python."""
from contratos import plano_v2 as contrato
from contratos.esquema_gemini import esquema_api, VERSAO_ESQUEMA_API
from erros import ErroGeracao
import json
from geracao import GeradorDePlano, distribuicao_tempo
from gemini import AgenteGemini, MODELO_PADRAO

INSTRUCOES = {
    'objetivos': 'Defina conteudos (lista de textos), objetivo_geral (texto) e objetivos_especificos (2 a 4 objetos id OBJ1, OBJ2... e descricao observável). Atenda à habilidade confirmada e à duração.',
    'avaliacao_preliminar': 'Defina evidencias: objetos id EVI1..., objetivo_id existente, criterio e evidencia_esperada. Cubra TODOS os objetivos com pelo menos uma evidência observável. São evidências esperadas, nunca resultados já observados. Não altere os objetivos.',
    'metodologia': 'Defina metodologia como texto e recursos como cópia EXATA de contexto.recursos. Considere os objetivos e as evidências preliminares. Explique a estratégia; não distribua minutos aqui. Use somente os recursos confirmados.',
    'sequencia': 'Defina etapas com id ET1..., titulo, minutos inteiros positivos, acao_docente, acao_discente, atividade, objetivos_ids e evidencias_ids. Some EXATAMENTE contexto.duracao_min. Cubra todos os objetivos e evidências recebidos. Em cada etapa, objetivos_ids deve ser exatamente o conjunto dos objetivos das suas evidencias_ids. Use apenas IDs existentes e recursos confirmados.',
    'avaliacao_final': 'Defina instrumentos (id INS1..., descricao, etapas_ids, evidencias_ids, procedimento) e uso_resultados como texto. Cubra TODAS as evidências preliminares sem reescrevê-las. Cada evidência do instrumento deve ocorrer em pelo menos uma das etapas vinculadas; cada etapa vinculada deve conter evidência desse instrumento. Explique como o professor coletará e usará as evidências futuras. Não invente notas, resultados observados ou percentuais de sucesso.',
    'adaptacao': 'Defina exatamente duas adaptacoes com id ADP1 e ADP2, descricao, objetivos_ids e etapas_ids. Use somente IDs existentes. Os objetivos citados devem ocorrer nas etapas vinculadas. Preserve objetivos, recursos e duração; não presuma diagnósticos nem materiais adicionais.',
}


# 2.2 (preservada para reprodutibilidade): ao oferecer "cartões já preparados" como alternativa, induzia o modelo a citar
# cartões mesmo quando o professor não os marcou (achado em 18/11/2026: 2 de 5 planos reais, ver docs/PoC07B_Prompt_2_3.md).
ORIENTACAO_RECURSOS_2_2 = (
    ' Só exija registros escritos se os recursos confirmados incluírem explicitamente '
    'um instrumento ou dispositivo que permita escrever. Sem isso, use explicação e '
    'contagem oral ou manipulação de cartões já preparados, sem acrescentar recursos.'
)
# 2.3: proíbe materiais fora de contexto.recursos sem sugerir nenhum material, e pede acentuação (1 de 5 planos veio sem acentos).
ORIENTACAO_RECURSOS_2_3 = (
    ' Use somente os recursos listados em contexto.recursos. Não cite materiais, objetos ou dispositivos que não estejam '
    'nessa lista, nem diga que algum material "já está preparado". Só exija registros escritos se os recursos confirmados '
    'incluírem explicitamente algo que permita escrever. Sem isso, use explicação oral, perguntas e respostas e '
    'demonstração com os recursos confirmados. Escreva em português do Brasil com acentuação correta.'
)
VERSOES_PROMPT = {
    'especialistas-plano-2.2': {nome: texto + ORIENTACAO_RECURSOS_2_2 for nome, texto in INSTRUCOES.items()},
    'especialistas-plano-2.3': {nome: texto + ORIENTACAO_RECURSOS_2_3 for nome, texto in INSTRUCOES.items()},
}
VERSAO_PROMPT = 'especialistas-plano-2.3'
INSTRUCOES = VERSOES_PROMPT[VERSAO_PROMPT]


class AgenteGeminiCompleto(AgenteGemini):
    def __init__(self, modelo=MODELO_PADRAO, versao_prompt=VERSAO_PROMPT, **kwargs):
        if versao_prompt not in VERSOES_PROMPT:
            raise ValueError(f"Versão de prompt desconhecida: {versao_prompt}")
        super().__init__(modelo, esquema_saida=esquema_api, instrucoes=VERSOES_PROMPT[versao_prompt],
                         versao_contrato=contrato.VERSAO, versao_prompt=versao_prompt, **kwargs)


    def executar(self, nome, entrada, estado, revisao, *, registro, reparo=None, revisao_pedagogica=None):
        registro['versao_esquema_api'] = VERSAO_ESQUEMA_API
        try:
            return super().executar(nome, entrada, estado, revisao, registro=registro, reparo=reparo,
                                    revisao_pedagogica=revisao_pedagogica)
        except ErroGeracao:
            # O corpo já foi sanitizado pelo transporte. Não repete HTTP 400.
            if registro.get('http_status') == 400:
                try:
                    detalhe = json.loads(registro.get('erro_corpo', '{}')).get('error', {})
                    mensagem = detalhe.get('message', '')
                    razoes = {d.get('reason') for d in detalhe.get('details', []) if isinstance(d, dict)}
                except (ValueError, TypeError, AttributeError):
                    mensagem, razoes = '', set()
                if isinstance(mensagem, str) and 'too many states' in mensagem.lower():
                    raise ErroGeracao('Gemini HTTP 400: o esquema enviado excedeu o limite de complexidade da API. Atualize o adaptador de esquema; esse erro não será repetido automaticamente.', tipo='esquema_api') from None
                if 'API_KEY_INVALID' in razoes:
                    raise ErroGeracao('Gemini HTTP 400: chave inválida. Confira GEMINI_API_KEY e copie a chave completa do Google AI Studio.', tipo='autenticacao') from None
            raise


class AgenteDemonstrativoCompleto:
    """Saída sintética por regras; não representa avaliação pedagógica nem LLM."""
    def executar(self, nome, entrada, estado, revisao, *, registro=None, reparo=None, revisao_pedagogica=None):
        # Regras locais: ignora reparos e revisões pedagógicas (não há modelo para receber as críticas).
        if registro is not None:
            registro.update(provedor='regras', versao_contrato=contrato.VERSAO, versao_prompt='demonstracao-plano-2.0')
        c, h = entrada['contexto'], entrada['habilidade']
        ordenacao = h['codigo'] == 'EF08CO03' and 'ordena' in c['tema'].lower()
        # Só cita cartões se o professor marcou cartões nos recursos (achado PoC07B: material fora dos recursos).
        cartoes = 'cart' in c['recursos'].lower().replace('õ', 'o').replace('ã', 'a')
        if nome == 'objetivos':
            if ordenacao:
                return dict(conteudos=['Listas numéricas', 'Comparação de vizinhos e ordenação por bolha'],
                            objetivo_geral='Compreender e executar um procedimento de ordenação sobre listas.',
                            objetivos_especificos=[
                                dict(id='OBJ1', descricao='Ordenar cartões numerados aplicando comparações e trocas entre vizinhos.'
                                     if cartoes else 'Ordenar uma lista de números aplicando comparações e trocas entre vizinhos.'),
                                dict(id='OBJ2', descricao='Explicar quando realizar uma troca e como reconhecer que a lista está ordenada.')])
            return dict(conteudos=[h['objeto_conhecimento'], c['tema']],
                        objetivo_geral=f"Explorar {c['tema']} em atividades relacionadas à habilidade {h['codigo']}.",
                        objetivos_especificos=[dict(id='OBJ1', descricao=f"Aplicar, em situação orientada, a habilidade: {h['habilidade']}"),
                                               dict(id='OBJ2', descricao='Explicar e justificar oralmente as decisões tomadas na atividade.')])
        if nome == 'avaliacao_preliminar':
            return {'evidencias': [dict(id=f'EVI{i}', objetivo_id=o['id'],
                         criterio=f"Realizar a ação descrita no objetivo: {o['descricao']}",
                         evidencia_esperada='Demonstração do procedimento e explicação oral das decisões pelo estudante.')
                         for i, o in enumerate(estado['objetivos']['objetivos_especificos'], 1)]}
        if nome == 'metodologia':
            return dict(metodologia=f"{c['tipo']}, com demonstração orientada, prática em duplas e discussão oral. O professor usa as evidências previstas para observar as decisões dos estudantes. As atividades utilizam os recursos confirmados, sem exigir escrita ou dispositivos adicionais.", recursos=c['recursos'])
        objs = [o['id'] for o in estado['objetivos']['objetivos_especificos']]
        ev = [e['id'] for e in estado['avaliacao_preliminar']['evidencias']]
        if nome == 'sequencia':
            duracoes = distribuicao_tempo(c['duracao_min'])
            titulos = ['Problema inicial', 'Demonstração', 'Prática em duplas', 'Síntese']
            if revisao % 2: titulos = ['Desafio inicial', 'Investigação guiada', 'Teste em duplas', 'Socialização']
            atividades = ([
                'Comparar oralmente os valores de uma lista de cartões numerados já preparada.' if cartoes else
                'Comparar oralmente os valores de uma lista de números apresentada com os recursos confirmados.',
                'Comparar vizinhos, trocar os que estão fora de ordem e repetir passagens até não haver trocas.',
                'Ordenar uma nova disposição de cartões pelo procedimento de bolha, alternando quem compara e quem movimenta.' if cartoes else
                'Ordenar uma nova lista de números pelo procedimento de bolha, alternando quem compara e quem indica a troca.',
                'Explicar uma troca e uma não troca e justificar o término do algoritmo.'
            ] if ordenacao else [f"Explorar oralmente {c['tema']} e levantar ideias prévias.",
                                f"Acompanhar uma demonstração da habilidade {h['codigo']} com os recursos confirmados.",
                                'Executar um desafio orientado e justificar as decisões em duplas.',
                                'Compartilhar oralmente o procedimento, dúvidas e conclusões.'])
            return {'etapas': [dict(id=f'ET{i+1}', titulo=titulos[i], minutos=m,
                    acao_docente='Orientar a tarefa, demonstrar quando necessário e observar as evidências previstas.',
                    acao_discente='Participar da tarefa e explicar oralmente suas decisões.',
                    atividade=atividades[i], objetivos_ids=list(objs), evidencias_ids=list(ev)) for i, m in enumerate(duracoes)]}
        etapas = [e['id'] for e in estado['sequencia']['etapas']]
        if nome == 'avaliacao_final':
            return dict(instrumentos=[dict(id='INS1', descricao='Observação orientada e perguntas orais.',
                etapas_ids=etapas, evidencias_ids=ev,
                procedimento='Observar a execução, solicitar justificativas individuais e comparar as ações com os critérios de cada evidência.')],
                uso_resultados='Se as evidências esperadas não aparecerem, retomar a demonstração e oferecer uma tarefa menor; nenhuma aprendizagem é presumida antes da aula.')
        if nome == 'adaptacao':
            return {'adaptacoes': [dict(id='ADP1', descricao='Dividir as instruções em passos, demonstrar novamente e começar por uma tarefa menor usando os mesmos materiais.', objetivos_ids=objs, etapas_ids=etapas),
                                   dict(id='ADP2', descricao='Alternar funções nas duplas e permitir resposta oral ou indicação dos materiais, com apoio do professor sem presumir diagnósticos.', objetivos_ids=objs, etapas_ids=etapas)]}
        raise ValueError('Etapa inexistente: '+nome)


class GeradorDePlanoCompleto(GeradorDePlano):
    VERSAO_CONTRATO = contrato.VERSAO
    ESPECIALISTAS = contrato.ETAPAS
    ORDEM = contrato.ETAPAS + ('integrador',)
    DEPENDENCIAS = contrato.DEPENDENCIAS
    integrar = staticmethod(contrato.integrar)
    validar_etapa = staticmethod(contrato.validar)

    def __init__(self, modo='demonstracao', modelo=MODELO_PADRAO, agente=None, reparos=1, corrigir_acentuacao=True):
        if agente is None:
            agente = AgenteGeminiCompleto(modelo) if modo == 'ia' else AgenteDemonstrativoCompleto()
        super().__init__(modo, modelo, agente, reparos, corrigir_acentuacao)

    def gerar(self, entrada, revisao, progresso=None, revisoes=None):
        contrato.validar_entrada(entrada)
        return super().gerar(entrada, revisao, progresso, revisoes=revisoes)
