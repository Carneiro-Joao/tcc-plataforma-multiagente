"""Rubrica operacional PRELIMINAR da IA Juiz (rubrica-juiz-0.1).

Fonte única: o prompt do Juiz (contratos/juiz_v1.py) e a documentação
(docs/Rubrica_e_Contrato_IA_Juiz.md) derivam daqui. Os seis critérios vêm da
especificação v2.1 (§5). Os níveis e âncoras são uma proposta inicial a ser
ajustada após testes; não são limiares cientificamente validados.

O Juiz avalia SOMENTE o que o validador mecânico não consegue verificar:
coerência, viabilidade, observabilidade e pertinência pedagógica. Contagem de
itens, soma de minutos, IDs e vínculos já foram verificados por código.
"""

VERSAO = "rubrica-juiz-0.1"
NOTAS = {0: "inadequado", 1: "insuficiente", 2: "adequado com ressalvas", 3: "adequado"}

CRITERIOS = (
    "aderencia_curricular",
    "alinhamento_objetivos",
    "coerencia_metodologica",
    "viabilidade",
    "avaliacao_aprendizagem",
    "inclusao",
)

RUBRICA = {
    "aderencia_curricular": {
        "rotulo": "Aderência curricular",
        "pergunta": "O plano desenvolve a habilidade oficial confirmada, e não um tema vizinho?",
        "secoes": ("habilidade_bncc", "conteudos", "objetivo_geral", "objetivos_especificos", "desenvolvimento"),
        "indicadores": (
            "Conteúdos e objetivos correspondem ao objeto de conhecimento e à ação pedida pela habilidade.",
            "As atividades exercitam o que a habilidade exige, não apenas falam sobre o tema.",
            "Nenhum assunto periférico ocupa a maior parte do tempo.",
            "O plano não reinterpreta nem amplia a habilidade oficial.",
        ),
        "ancoras": {
            3: "Conteúdos, objetivos e atividades exercitam diretamente a habilidade; sem divergência relevante.",
            2: "A habilidade é atendida, mas parte do tempo vai a conteúdo periférico ou um aspecto dela fica pouco trabalhado.",
            1: "A habilidade é só parcialmente contemplada; as atividades principais tratam de outro assunto.",
            0: "O plano não desenvolve a habilidade ou a contradiz.",
        },
    },
    "alinhamento_objetivos": {
        "rotulo": "Alinhamento dos objetivos",
        "pergunta": "Os objetivos específicos são claros, observáveis e coerentes com o objetivo geral e a habilidade?",
        "secoes": ("objetivo_geral", "objetivos_especificos", "habilidade_bncc"),
        "indicadores": (
            "Cada objetivo descreve algo que o estudante faz e que o professor consegue observar.",
            "Os objetivos são distintos entre si e desdobram o objetivo geral.",
            "O conjunto é atingível na duração informada.",
            "Verbos vagos (compreender, conhecer) vêm acompanhados da ação que os torna observáveis.",
        ),
        "ancoras": {
            3: "Objetivos observáveis, distintos, atingíveis na duração e coerentes com o objetivo geral.",
            2: "Objetivos adequados, mas algum é vago, redundante ou ambicioso para a duração.",
            1: "Vários objetivos não observáveis, redundantes ou inviáveis na duração.",
            0: "Objetivos incoerentes com o objetivo geral ou com a habilidade, ou impossíveis de observar.",
        },
    },
    "coerencia_metodologica": {
        "rotulo": "Coerência metodológica",
        "pergunta": "A metodologia e as ações docente e discente sustentam os objetivos e o tipo de aula informado?",
        "secoes": ("metodologia", "desenvolvimento", "objetivos_especificos", "identificacao"),
        "indicadores": (
            "A estratégia descrita na metodologia aparece de fato nas atividades do desenvolvimento.",
            "As ações do docente e as do estudante são distintas e compatíveis com cada etapa.",
            "O tipo de aula informado (por exemplo, desplugada) é respeitado.",
            "A sequência tem progressão lógica, da abertura à prática e à síntese.",
        ),
        "ancoras": {
            3: "Metodologia, atividades e ações se reforçam; progressão clara; tipo de aula respeitado.",
            2: "Coerente no geral, mas com uma etapa desconectada da estratégia ou progressão pouco clara.",
            1: "A metodologia declarada não se reflete nas atividades, ou o tipo de aula é desrespeitado em parte.",
            0: "Metodologia e atividades se contradizem, ou a estratégia não leva aos objetivos.",
        },
    },
    "viabilidade": {
        "rotulo": "Viabilidade",
        "pergunta": "O plano cabe no tempo e nos recursos informados e é executável por um professor real?",
        "secoes": ("desenvolvimento", "recursos", "identificacao"),
        "indicadores": (
            "As atividades usam somente os recursos confirmados (nada de projetor, internet ou dispositivos não informados).",
            "O tempo de cada etapa é realista para a atividade descrita, não apenas somado corretamente.",
            "Não exige preparo, materiais ou espaço que o contexto não indica.",
            "Não presume tamanho ou perfil da turma além do informado.",
        ),
        "ancoras": {
            3: "Recursos e tempos realistas; executável com o contexto informado.",
            2: "Executável, mas com tempo apertado numa etapa ou pequeno material implícito não informado.",
            1: "Depende de recurso não informado ou tem etapas claramente curtas ou longas demais para o que descrevem.",
            0: "Inexequível com os recursos ou a duração informados.",
        },
    },
    "avaliacao_aprendizagem": {
        "rotulo": "Avaliação da aprendizagem",
        "pergunta": "As evidências e os instrumentos permitem verificar cada objetivo?",
        "secoes": ("avaliacao_aprendizagem", "objetivos_especificos", "desenvolvimento"),
        "indicadores": (
            "Cada evidência é observável e corresponde ao objetivo ao qual está ligada.",
            "O instrumento coleta de fato a evidência durante as etapas vinculadas.",
            "Os critérios permitem distinguir desempenho adequado de inadequado.",
            "O uso dos resultados é plausível e descrito como ação futura; nenhum resultado é dado como já ocorrido.",
        ),
        "ancoras": {
            3: "Evidências observáveis e ligadas aos objetivos; instrumentos coletam a evidência; critérios discriminam.",
            2: "Verificável, mas algum critério é vago ou um instrumento coleta a evidência de forma indireta.",
            1: "Evidências genéricas ou instrumentos que não captam o objetivo; critérios não discriminam.",
            0: "Não permite verificar os objetivos, ou afirma resultados que não existem.",
        },
    },
    "inclusao": {
        "rotulo": "Inclusão",
        "pergunta": "As adaptações ampliam participação e demonstração de aprendizagem sem diluir os objetivos?",
        "secoes": ("adaptacoes", "desenvolvimento", "objetivos_especificos"),
        "indicadores": (
            "Oferecem alternativas reais de participação, representação ou expressão.",
            "Mantêm os objetivos e são viáveis com os mesmos recursos e tempo.",
            "Não presumem diagnósticos individuais.",
            "São específicas deste plano, não frases genéricas aplicáveis a qualquer aula.",
        ),
        "ancoras": {
            3: "Alternativas concretas, específicas e viáveis, que preservam os objetivos.",
            2: "Pertinentes, mas pouco específicas ou ligadas de forma frágil às etapas.",
            1: "Genéricas ou dependentes de recurso não informado; pouco alteram a participação.",
            0: "Ausentes na prática, inadequadas, ou que presumem diagnósticos ou reduzem os objetivos.",
        },
    },
}

# Para onde apontar cada falha, conforme a seção do plano em que ela aparece.
RESPONSAVEL_POR_SECAO = {
    "conteudos / objetivo_geral / objetivos_especificos": "objetivos",
    "evidências e critérios (avaliacao_aprendizagem.evidencias)": "avaliacao_preliminar",
    "metodologia / recursos": "metodologia",
    "desenvolvimento (etapas, tempos, ações, atividades)": "sequencia",
    "instrumentos, procedimentos e uso_resultados": "avaliacao_final",
    "adaptacoes": "adaptacao",
}

GRAVIDADES = {
    "critica": "Torna o plano inadequado para uso sem revisão humana (contradiz a habilidade, conceito errado, atividade insegura ou imprópria).",
    "maior": "Compromete o critério, mas pode ser corrigida refazendo o componente responsável.",
    "menor": "Melhoria desejável; não exige correção automática.",
}
