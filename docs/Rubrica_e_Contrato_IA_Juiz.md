# Rubrica e contrato da IA Juiz (`rubrica-juiz-0.1` / `parecer-juiz-1.0`)

Rascunho técnico iniciado em 16/11/2026 sobre `feat/poc04a-gemini` (`3e9e034`), incorporado em `8aa3546` à base consolidada do protótipo (`3fb69cd`). Revisão de compatibilidade em 17/11/2026 na branch `feat/poc05-juiz-contrato`. **Proposta preliminar para ratificação do orientador.** Não foi executada contra nenhum LLM real; o que existe é contrato, lógica de decisão e testes offline. Nada aqui comprova qualidade pedagógica nem que um modelo real avalia bem.

## 1. Papel e limites

Três coisas distintas, como pedem a RN07 e a RN09 da especificação v2.1-R2:

| Camada | Quem decide | O que afirma |
|---|---|---|
| Verificação mecânica | Código (`plano_v2.py`) | Estrutura, tipos, soma de minutos, IDs, vínculos |
| Parecer da IA Juiz | LLM, validado por código | Coerência, viabilidade, observabilidade e pertinência, segundo a rubrica |
| Decisão humana | Usuário da aplicação | Aceitar ou rejeitar (RF25/UC10) |

O Juiz **avalia e aponta**: não reescreve o plano, não executa correções e não escolhe o próximo estado. O próximo estado é calculado por código (`decidir`) a partir do parecer validado e de uma política explícita. Um parecer favorável leva a `aguardando_decisao`, que **não é aprovação**: nenhum caminho do código produz estado de aprovação.

O Juiz **não reverifica** o que o código já garantiu (soma de minutos, quantidades, IDs, vínculos). Gastar a avaliação do LLM nisso seria redundante e arriscaria contradizer a verificação mecânica.

## 2. Escala

Nota inteira de 0 a 3 por critério:

- **0** — inadequado
- **1** — insuficiente
- **2** — adequado com ressalvas
- **3** — adequado

Quatro níveis evitam o ponto médio neutro. A escala e as âncoras são uma proposta inicial, a ajustar após testes (decisão D4).

## 3. Critérios

Os seis critérios vêm da especificação v2.1 (§5). Cada nota tem uma âncora descritiva; para dar 3, o Juiz precisa apontar no plano o trecho que demonstra o critério.

O prompt `juiz-v1.2` inclui perguntas, seções, os 24 indicadores e todas as âncoras de `rubrica_juiz.py`. A revisão anterior enviava as perguntas e âncoras, mas omitia os indicadores. A rubrica continua na versão `rubrica-juiz-0.1`: os indicadores foram transmitidos integralmente desde o prompt v1.1. O v1.2 acrescenta orientações de escopo por aula, imutabilidade da habilidade BNCC, correspondência entre OBJ/EVI/INS e viabilidade efetiva, sem alterar âncoras, critérios, contrato ou política.

### Aderência curricular (`aderencia_curricular`)

**Pergunta:** O plano desenvolve a habilidade oficial confirmada, e não um tema vizinho?

**Seções do plano consultadas:** `habilidade_bncc`, `conteudos`, `objetivo_geral`, `objetivos_especificos`, `desenvolvimento`

**Indicadores:**

- Conteúdos e objetivos correspondem ao objeto de conhecimento e à ação pedida pela habilidade.
- As atividades exercitam o que a habilidade exige, não apenas falam sobre o tema.
- Nenhum assunto periférico ocupa a maior parte do tempo.
- O plano não reinterpreta nem amplia a habilidade oficial.

| Nota | Âncora |
|---|---|
| 3 | Conteúdos, objetivos e atividades exercitam diretamente a habilidade; sem divergência relevante. |
| 2 | A habilidade é atendida, mas parte do tempo vai a conteúdo periférico ou um aspecto dela fica pouco trabalhado. |
| 1 | A habilidade é só parcialmente contemplada; as atividades principais tratam de outro assunto. |
| 0 | O plano não desenvolve a habilidade ou a contradiz. |

### Alinhamento dos objetivos (`alinhamento_objetivos`)

**Pergunta:** Os objetivos específicos são claros, observáveis e coerentes com o objetivo geral e a habilidade?

**Seções do plano consultadas:** `objetivo_geral`, `objetivos_especificos`, `habilidade_bncc`

**Indicadores:**

- Cada objetivo descreve algo que o estudante faz e que o professor consegue observar.
- Os objetivos são distintos entre si e desdobram o objetivo geral.
- O conjunto é atingível na duração informada.
- Verbos vagos (compreender, conhecer) vêm acompanhados da ação que os torna observáveis.

| Nota | Âncora |
|---|---|
| 3 | Objetivos observáveis, distintos, atingíveis na duração e coerentes com o objetivo geral. |
| 2 | Objetivos adequados, mas algum é vago, redundante ou ambicioso para a duração. |
| 1 | Vários objetivos não observáveis, redundantes ou inviáveis na duração. |
| 0 | Objetivos incoerentes com o objetivo geral ou com a habilidade, ou impossíveis de observar. |

### Coerência metodológica (`coerencia_metodologica`)

**Pergunta:** A metodologia e as ações docente e discente sustentam os objetivos e o tipo de aula informado?

**Seções do plano consultadas:** `metodologia`, `desenvolvimento`, `objetivos_especificos`, `identificacao`

**Indicadores:**

- A estratégia descrita na metodologia aparece de fato nas atividades do desenvolvimento.
- As ações do docente e as do estudante são distintas e compatíveis com cada etapa.
- O tipo de aula informado (por exemplo, desplugada) é respeitado.
- A sequência tem progressão lógica, da abertura à prática e à síntese.

| Nota | Âncora |
|---|---|
| 3 | Metodologia, atividades e ações se reforçam; progressão clara; tipo de aula respeitado. |
| 2 | Coerente no geral, mas com uma etapa desconectada da estratégia ou progressão pouco clara. |
| 1 | A metodologia declarada não se reflete nas atividades, ou o tipo de aula é desrespeitado em parte. |
| 0 | Metodologia e atividades se contradizem, ou a estratégia não leva aos objetivos. |

### Viabilidade (`viabilidade`)

**Pergunta:** O plano cabe no tempo e nos recursos informados e é executável por um professor real?

**Seções do plano consultadas:** `desenvolvimento`, `recursos`, `identificacao`

**Indicadores:**

- As atividades usam somente os recursos confirmados (nada de projetor, internet ou dispositivos não informados).
- O tempo de cada etapa é realista para a atividade descrita, não apenas somado corretamente.
- Não exige preparo, materiais ou espaço que o contexto não indica.
- Não presume tamanho ou perfil da turma além do informado.

| Nota | Âncora |
|---|---|
| 3 | Recursos e tempos realistas; executável com o contexto informado. |
| 2 | Executável, mas com tempo apertado numa etapa ou pequeno material implícito não informado. |
| 1 | Depende de recurso não informado ou tem etapas claramente curtas ou longas demais para o que descrevem. |
| 0 | Inexequível com os recursos ou a duração informados. |

### Avaliação da aprendizagem (`avaliacao_aprendizagem`)

**Pergunta:** As evidências e os instrumentos permitem verificar cada objetivo?

**Seções do plano consultadas:** `avaliacao_aprendizagem`, `objetivos_especificos`, `desenvolvimento`

**Indicadores:**

- Cada evidência é observável e corresponde ao objetivo ao qual está ligada.
- O instrumento coleta de fato a evidência durante as etapas vinculadas.
- Os critérios permitem distinguir desempenho adequado de inadequado.
- O uso dos resultados é plausível e descrito como ação futura; nenhum resultado é dado como já ocorrido.

| Nota | Âncora |
|---|---|
| 3 | Evidências observáveis e ligadas aos objetivos; instrumentos coletam a evidência; critérios discriminam. |
| 2 | Verificável, mas algum critério é vago ou um instrumento coleta a evidência de forma indireta. |
| 1 | Evidências genéricas ou instrumentos que não captam o objetivo; critérios não discriminam. |
| 0 | Não permite verificar os objetivos, ou afirma resultados que não existem. |

### Inclusão (`inclusao`)

**Pergunta:** As adaptações ampliam participação e demonstração de aprendizagem sem diluir os objetivos?

**Seções do plano consultadas:** `adaptacoes`, `desenvolvimento`, `objetivos_especificos`

**Indicadores:**

- Oferecem alternativas reais de participação, representação ou expressão.
- Mantêm os objetivos e são viáveis com os mesmos recursos e tempo.
- Não presumem diagnósticos individuais.
- São específicas deste plano, não frases genéricas aplicáveis a qualquer aula.

| Nota | Âncora |
|---|---|
| 3 | Alternativas concretas, específicas e viáveis, que preservam os objetivos. |
| 2 | Pertinentes, mas pouco específicas ou ligadas de forma frágil às etapas. |
| 1 | Genéricas ou dependentes de recurso não informado; pouco alteram a participação. |
| 0 | Ausentes na prática, inadequadas, ou que presumem diagnósticos ou reduzem os objetivos. |

## 4. Falhas, gravidades e responsáveis

Cada falha aponta o critério, o **componente responsável** e uma orientação de correção dirigida ao especialista (não texto pronto).

| Gravidade | Significado |
|---|---|
| `critica` | Torna o plano inadequado para uso sem revisão humana (contradiz a habilidade, conceito errado, atividade insegura ou imprópria). |
| `maior` | Compromete o critério, mas pode ser corrigida refazendo o componente responsável. |
| `menor` | Melhoria desejável; não exige correção automática. |

| Seção do plano | Componente responsável |
|---|---|
| conteudos / objetivo_geral / objetivos_especificos | `objetivos` |
| evidências e critérios (avaliacao_aprendizagem.evidencias) | `avaliacao_preliminar` |
| metodologia / recursos | `metodologia` |
| desenvolvimento (etapas, tempos, ações, atividades) | `sequencia` |
| instrumentos, procedimentos e uso_resultados | `avaliacao_final` |
| adaptacoes | `adaptacao` |

## 5. Coerência obrigatória entre notas e falhas

O validador recusa um parecer que se contradiz (o prompt pede o mesmo, mas quem garante é o código):

| Regra | Diagnóstico |
|---|---|
| Falha crítica exige nota 0 ou 1 no critério | `critica_exige_nota_baixa` |
| Nota 0 ou 1 exige ao menos uma falha maior ou crítica no critério | `nota_baixa_sem_falha_grave` |
| Nota 2 exige ao menos uma falha (qualquer gravidade) | `nota_sem_falha` |
| Nota 3 não admite falha maior nem crítica no critério | `nota_alta_com_falha_grave` |
| Seis critérios, sem repetição ou ausência; IDs de falha únicos | `criterio_ausente`, `criterio_repetido`, `id_duplicado` |

## 6. Política de decisão (preliminar)

`decidir(parecer, ciclos_usados)` devolve `proximo_estado`, `componentes_a_corrigir`, `componentes_invalidados`, os motivos e a política usada. Parâmetros de `politica-juiz-prelim-0.1`:

| Parâmetro | Valor inicial | Observação |
|---|---|---|
| `nota_minima` | 2 | Critério abaixo disso exige correção |
| `gravidades_que_exigem_correcao` | `maior`, `critica` | Falha `menor` não exige correção |
| `critica_exige_revisao_humana` | `True` | Spec R2 §6: caso crítico vai a `revisao_necessaria` (decisão D1) |
| `limite_ciclos` | 2 | Spec R2 §5: valor inicial ajustável |

Ordem de avaliação:

1. Há falha crítica e a política manda ao humano → `revisao_necessaria`.
2. Senão, há falha grave (ou critério abaixo do mínimo) e `ciclos_usados` < limite → `em_correcao`.
3. Há o que corrigir, mas o limite foi atingido → `revisao_necessaria`.
4. Nada a corrigir → `aguardando_decisao`.

Os componentes a corrigir vêm das falhas graves. As falhas `menor` do mesmo critério só entram se o critério ficar abaixo da nota mínima **e** não tiver nenhuma falha grave (política mais rigorosa). Isso evita refazer componentes a mais.

`resolver_politica` recusa parâmetros desconhecidos, notas mínimas fora de 0–3, gravidades inválidas ou repetidas, contadores negativos/não inteiros e valores não booleanos para revisão humana. Limite zero é permitido e encaminha diretamente para revisão quando há o que corrigir. A política efetiva é copiada antes da chamada e registrada integralmente no resultado e no rastreio; alterações posteriores no objeto do chamador não mudam a decisão. Ajustes experimentais devem receber um nome de política próprio para comparação entre execuções.

## 7. Invalidação

Corrigir um componente invalida quem depende dele (grafo de `plano_v2.DEPENDENCIAS`). `invalidados(componentes)` calcula o fecho:

| Se corrigir | Refazer também |
|---|---|
| `objetivos` | `avaliacao_preliminar`, `metodologia`, `sequencia`, `avaliacao_final`, `adaptacao` |
| `avaliacao_preliminar` | `metodologia`, `sequencia`, `avaliacao_final`, `adaptacao` |
| `metodologia` | `sequencia`, `avaliacao_final`, `adaptacao` |
| `sequencia` | `avaliacao_final`, `adaptacao` |
| `avaliacao_final` | `adaptacao` |
| `adaptacao` | (nenhum) |

## 8. Entrada, saída e independência

**Entrada:** contexto confirmado, habilidade oficial e o **plano já integrado** (`saidas_anteriores = {plano}`). `avaliar_plano` exige o contrato PlanoDeAula 2.0 e verifica a preservação do contexto/habilidade antes de consumir qualquer chamada. Entradas vazias, planos inválidos ou legados são recusados; planos legados continuam legíveis no site, mas exigem nova geração 2.0 para passar pelo Juiz. O Juiz não vê as saídas intermediárias.

**Saída (`parecer-juiz-1.0`):** `avaliacoes` (seis, com nota e justificativa), `falhas` (até 12) e `resumo`. O contrato completo está em `contratos/juiz_v1.schema.json`. O esquema enviado ao Gemini reutiliza a projeção de `contratos/esquema_gemini.py`: campos, tipos e obrigatoriedade permanecem estruturais; limites, formatos e valores permitidos viram descrições. O validador Python continua exigindo todas as regras e invariantes. A projeção é registrada como `parecer-juiz-1.0-estrutura-v1`; a aceitação por um Juiz real ainda precisa ser verificada.

**Independência.** O resultado registra `modelo_distinto_do_gerador`. Isso só diz que os identificadores de modelo diferem; **não garante famílias diferentes**. Vieses a controlar na avaliação do Juiz: autopreferência, verbosidade, posição e leniência. O prompt pede nota 3 apenas com trecho do plano como prova, e diz que quantidade de texto não é qualidade.

O identificador declarado do Juiz deve coincidir com o modelo configurado no agente. O rastreio conserva plano avaliado, contexto/habilidade, revisão, ciclos usados, política e versões, inclusive nas falhas do provedor. HTTP 503 só é repetido quando `repeticoes_503` é configurado no agente (padrão zero; máximo duas repetições); o reparo estrutural tem contador separado e não repete erros HTTP.

O resultado também expõe `versao_esquema_api`, fornecida pelo agente: `parecer-juiz-1.0-estrutura-v1` para o Gemini Juiz, ou `None` para agentes de teste sem essa informação. O campo foi incorporado do patch complementar `poc05-juiz-patch2-esquema-api.patch`, preservando a versão no rastreio de cada tentativa.

## 9. O que está e o que não está verificado

**Verificado offline em 17/11/2026** (`tests/test_juiz.py`, 54 testes aprovados; suíte completa 169 executados, 168 aprovados e 1 ignorado; também com `python -S`):

- contrato, esquema fechado, enums iguais aos do código e aos seis critérios da spec;
- invariantes nota × falha e estados de decisão, com caminho e regra em cada rejeição;
- política, limite de ciclos e invalidação;
- um reparo técnico, falha de provedor sem repetição, plano e entrada não alterados;
- requisição Gemini simulada com esquema, instrução e plano como dado.
- entrada inválida e política malformada recusadas antes da chamada, com preservação da configuração usada;
- geração 2.0 seguida do Juiz em transporte simulado, nos cenários favorável, corrigível e crítico, sem refazer especialistas;
- projeção de esquema com validação local estrita e recuperação opcional de HTTP 503.

O rascunho original relata um teste de mutação com 9 defeitos plantados no validador e na decisão: 8 detectados e 1 equivalente (cópia redundante). Esse experimento não foi reproduzido nesta revisão; os resultados acima correspondem à suíte automatizada versionada.

**Não verificado:** que um LLM real siga o contrato e a rubrica; que as notas sejam calibradas ou estáveis entre execuções; que o Juiz **detecte defeitos reais**; que concorde com avaliadores humanos. Os pareceres das fixtures são sintéticos, escritos à mão.

## 10. Decisões pendentes

| # | Decisão | Proposta atual |
|---|---|---|
| D1 | Caso crítico: revisão humana direta ou ainda corrigível? | Revisão humana direta (literal da spec R2 §6) |
| D2 | Quais gravidades exigem correção, e a nota mínima | `maior` e `crítica`; mínimo 2 |
| D3 | Limite de ciclos | 2 |
| D4 | Escala 0–3 e texto das âncoras | Proposta inicial |
| D5 | Fundamentação da rubrica | A redigir: objetivos observáveis (taxonomia de Bloom revisada, Anderson e Krathwohl, 2001) e alinhamento construtivo (Biggs e Tang). **Confirmar as referências e edições antes de citar** |

## 11. Próximos passos

1. Implementar o adaptador da API DeepSeek, escolhido em 17/11/2026 para a próxima integração do Juiz. A fábrica atual usa Gemini; ainda não há configuração nem chamada DeepSeek no protótipo.
2. Ligar o Juiz ao pipeline: ciclo de correção com `componentes_invalidados`, contador de ciclos e estados no banco, mais o registro do Juiz no rastreio.
3. Conjunto de planos com **defeitos injetados** para medir detecção e falsos positivos do Juiz.
4. CLI de uma rodada real (como `teste_gemini.py`) e inspeção do JSON.
5. Ajustar rubrica e política com base nessas rodadas, registrando cada mudança de versão.
