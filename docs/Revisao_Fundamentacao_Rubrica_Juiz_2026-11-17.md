# Revisão fundamentada da rubrica da IA Juiz — 17/11/2026

> **Registro de pesquisa RD-002 / PoC 05 — diagnóstico e protocolo preliminar.**
> Estado: **revisão documental concluída; alterações operacionais propostas, NÃO implementadas nem validadas**.
> Base examinada: branch `feat/poc05-juiz-contrato`, especialmente `contratos/rubrica_juiz.py`, `contratos/juiz_v1.py`, `juiz.py`, `docs/Rubrica_e_Contrato_IA_Juiz.md` e `tests/test_juiz.py`.
> Este arquivo registra análise e hipóteses para orientar testes. Não substitui a fonte operacional da rubrica.

## 1. Decisão de preservação e situação real

**Preservar** a versão operacional `rubrica-juiz-0.1`, com **seis critérios, 24 indicadores, notas inteiras de 0 a 3 e âncoras por critério**, a interface `parecer-juiz-1.0`, a política `politica-juiz-prelim-0.1` (nota mínima 2, falhas maior/crítica como motivos de correção, limite de dois ciclos e encaminhamento humano de casos críticos) e o grafo de invalidação existente. Não criar rubrica concorrente, sétimo critério ou nova escala sem evidência.

A verificação **estrutural/mecânica** permanece em Python; a IA Juiz é responsável por julgamentos **semânticos/pedagógicos**. O parecer do juiz **não aprova** planos: a decisão final é docente. As 54 verificações do juiz registradas na branch são **offline, com pareceres sintéticos**; não demonstram detecção real de defeitos nem confiabilidade pedagógica.

**Provedor escolhido nesta conversa (decisão mais recente):** geradores `gemini-3.5-flash-lite`, Google; juiz proposto `openai/gpt-oss-120b` via **GroqCloud**. O adaptador real ainda não foi implementado. Registros anteriores com DeepSeek no README e nos documentos são históricos e serão atualizados **junto com a implementação**, não nesta revisão. GroqCloud não é Grok da xAI.

## 2. Fundamentação das dimensões existentes

As obras abaixo **fundamentam aspectos do desenho**; nenhuma delas valida empiricamente esta rubrica particular ou seus limiares:

| Dimensão da rubrica atual | Fundamento e interpretação operacional |
|---|---|
| `aderencia_curricular` | O complemento à BNCC para Computação fornece o referencial curricular; verificar a ação exigida pela habilidade e sua concretização, não somente palavras-chave. |
| `alinhamento_objetivos` | Anderson e Krathwohl (2001) oferecem categorias úteis para qualificar processos cognitivos; observar o que o estudante efetivamente fará, sem exigir verbos de uma lista como critério único. |
| `coerencia_metodologica` | Biggs (1996) fundamenta alinhamento entre resultados pretendidos, atividades e avaliação; no domínio Computação, verificar também a **correção conceitual/procedimental** da estratégia proposta. |
| `viabilidade` | Exequibilidade é uma exigência de projeto desta PoC: distinguir soma exata dos minutos (código) de realismo do tempo, materiais e contexto (juiz). Não imputar recursos não informados por mero detalhe textual. |
| `avaliacao_aprendizagem` | Biggs (1996) fundamenta o alinhamento das evidências com os objetivos; Brookhart (2013) destaca critérios referentes à aprendizagem e níveis de qualidade claramente descritos. A aplicação a *planos de aula* é **adaptação metodológica**, não uma validação já estabelecida pelo livro. |
| `inclusao` | CAST (2024) propõe múltiplas possibilidades de engajamento, representação, ação e expressão. As adaptações precisam ampliar participação sem presumir diagnósticos nem eliminar a habilidade pretendida. |

A estrutura **analítica**, com critérios e âncoras diferentes por dimensão, é adequada para produzir um diagnóstico interpretável. Manter a escala 0–3 atual como **hipótese de instrumento**, sem afirmar que quatro níveis são superiores a outras escalas ou que a nota mínima 2 foi cientificamente calibrada.

## 3. Pontos fortes já encontrados no código

1. Seis critérios provenientes da especificação v2.1-R2; cada um contém pergunta, seções, quatro indicadores e quatro âncoras.
2. `juiz_v1.instrucoes()` constrói o prompt diretamente da fonte `rubrica_juiz.py`, reduzindo divergências entre código e prompt; `juiz-v1.1` já transmite os 24 indicadores.
3. `juiz_v1.diagnosticar()` verifica coerência entre notas e falhas; o esquema fecha campos e identifica responsáveis e gravidades.
4. `decidir()` toma decisões de fluxo **em Python**, registra a política e preserva aprovação humana.
5. `juiz.avaliar_plano()` recebe o plano integrado e validado; não reexecuta especialistas nem substitui a versão original.
6. Há testes offline para contrato e decisões. São uma base para testes de regressão, **não** resultados da qualidade de um LLM.

## 4. Lacunas e propostas de melhoria — sem alterar código nesta etapa

| Prioridade | Achado | Ação candidata | Teste que deve anteceder alteração |
|---|---|---|---|
| Alta | Correção de conteúdo/algoritmo aparece na descrição de falha crítica, mas **não está explícita entre os 24 indicadores**. | Especificar, em `coerencia_metodologica` ou `aderencia_curricular`, a exatidão dos procedimentos de Computação; **preservar 6 critérios e, preferencialmente, 24 indicadores** ao substituir uma formulação redundante. | Injetar passos incorretos de algoritmos e verificar detecção e gravidade. |
| Alta | Existência de vínculo `OBJ ↔ EVI` validado por código não assegura que a evidência mede o objetivo. | Reforçar a distinção `vínculo válido` versus `evidência suficiente`, já presente na rubrica. | Fazer uma evidência mencionar um OBJ correto mas medir apenas uma habilidade preliminar. |
| Média | Justificativa exige IDs, mas pode citar IDs existentes sem indicar a passagem relevante ou sua interpretação. | Testar instrução de fundamentar cada nota em elementos verificáveis; não pressupor que citar um ID prova a conclusão. | Conferir manualmente as justificativas contra o JSON do plano. |
| Média | As fronteiras `menor/maior/critica` e notas 1/2 podem ter interpretações variáveis. | Construir exemplos-âncora específicos antes de ajustar a política. | Repetir julgamentos de exemplos limítrofes; verificar consistência. |
| Média | A escala/política de decisão ainda não foi validada. | Manter `nota_minima=2` e `limite_ciclos=2` como parâmetros iniciais, com versões explícitas em cada experimento. | Comparar decisões da política com a gravidade adjudicada na análise humana. |
| Baixa | Fechamento/síntese não aparece como etapa independente em todo plano. | Avaliar se há oportunidade de síntese/verificação **no conjunto da aula**, sem exigir uma etapa formal nem uma duração fixa. | Usar um plano bom sem etapa chamada “fechamento” como controle de falso positivo. |

**Não mudar silenciosamente pesos, notas mínimas, contratos ou estados.** Se os testes motivarem alteração de indicador, âncora ou prompt, atualizar `rubrica_juiz.py`, sua documentação espelhada, a versão da rubrica/prompt e os testes de regressão no **mesmo incremento**.

## 5. Caso 01 — primeiro plano real da AulaIA (17/11/2026)

**Origem da evidência:** `primeiro-plano-plataforma.pdf`, fornecido pelo responsável no chat em 17/11/2026, **não é uma fixture JSON versionada aqui**. Plano: 8º ano, EF08CO03, ordenação/Bubble Sort desplugado, 50 minutos, ET1=15 e ET2=35 minutos, OBJ1/OBJ2, EVI1/EVI2, INS1/INS2, ADP1/ADP2, estado aguardando aprovação.

**Forças observadas:** documento organizado, habilidade plausível para o tema, tempos somados corretamente, encadeamento explícito entre objetivos/etapas/evidências/instrumentos, instrumentos de observação, adaptações e aprovação docente pendente.

**Hipóteses de falha a testar, NÃO diagnóstico emitido por LLM:**

- **H01 — `avaliacao_aprendizagem` / `avaliacao_preliminar`**: EVI1 (comparar números/indicar o maior cartão) é uma evidência parcial, insuficiente para demonstrar o OBJ1 (identificar passos da ordenação). A gravidade depende do conjunto de instrumentos e atividades.
- **H02 — `coerencia_metodologica` / `sequencia`**: instruções mencionam comparações e trocas adjacentes, mas não explicitam suficientemente as **passadas sucessivas e a condição de parada do Bubble Sort**. Evitar afirmar que todo plano precisaria descrever pseudocódigo completo; avaliar se o procedimento é realizável e conceitualmente correto.
- **H03 — `avaliacao_aprendizagem` / `avaliacao_final`**: observação oral e manipulação são pertinentes, mas os critérios podem ser mais discriminativos quanto à execução do algoritmo.
- **H04 — `viabilidade` / `metodologia` ou `sequencia`**: materiais e preparação dos cartões podem ser mais explícitos; “papel” não significa automaticamente ausência de cartões de papel. Não criar falha sem examinar o contexto confirmado.
- **H05 — `coerencia_metodologica`**: a aula poderia oferecer uma síntese final mais visível. **Melhoria opcional**, nunca reprovação automática pela ausência de ET3.
- **H06 — `inclusao` / `adaptacao`**: adaptações existentes são relevantes; investigar alternativas concretas de participação sem exigir recursos extra ou diagnóstico individual.

**Regra de proveniência:** a IA Juiz recebe **JSON `PlanoDeAula 2.0` + entrada confirmada**, não um PDF. Antes do ensaio real, recuperar o **JSON original** associado ao PDF no SQLite/rastreio ou exportá-lo fielmente. A fixture `tests/dados/plano_v2/fixture_ordenacao.json` é **sintética** e não deve ser apresentada como o plano realmente gerado sem conferência.

## 6. Protocolo mínimo de avaliação (ainda não executado)

1. **Congelar uma linha de base**: SHA da branch, versão do contrato, rubrica, prompt, política, modelo gerador e modelo juiz, parâmetros da API, data e hash do JSON do plano; registrar erros, latência e tokens conhecidos.
2. **Obter o caso real** em JSON válido `PlanoDeAula 2.0` e preservá-lo sem edição. Associar PDF/JSON por identificador de execução, respeitando privacidade.
3. **Preparar variantes controladas** que preservem os invariantes estruturais e alterem **uma condição pedagógica por vez**: evidência que não mede objetivo; erro algorítmico de comparação/troca; uso de projetor sem recurso confirmado; adaptação genérica; conteúdo periférico; e ausência legítima de etapa formal de síntese como controle.
4. **Definir expectativas antes da chamada ao LLM**: critério esperado, gravidade provável, seção responsável e justificativa. Essas expectativas são hipóteses de pesquisadores; idealmente revisar com professor/orientador.
5. **Executar o Juiz isolado** sem mudar prompts geradores nem reparar automaticamente planos. Registrar parecer bruto, erros de contrato, `avaliacoes`, `falhas`, `decisao` e custo/latência conhecidos.
6. **Conferir qualidade**, separando contrato válido de pertinência pedagógica: detecção dos defeitos injetados, falhas não detectadas, falsos positivos nos controles, coerência das justificativas, encaminhamento do componente correto e estabilidade em repetições possíveis.
7. **Analisar divergências** e só então propor alterações versionadas na rubrica. Após estabilização, integrar os ciclos de correção e estudar os efeitos de mudanças nos prompts dos geradores.

**Cuidados metodológicos:** os pareceres sintéticos existentes exercitam o código, não o desempenho do juiz. Uma inspeção humana inicial não é um *gold standard* pedagógico validado. A literatura sobre LLM-as-a-Judge alerta para vieses e limitações; empregar outra família de LLM reduz dependência do gerador, mas não elimina erros nem substitui avaliação humana.

## 7. Decisões deste registro

- **D-R01 (manter):** `rubrica-juiz-0.1` + seis critérios + escala 0–3 + `parecer-juiz-1.0` + política atual.
- **D-R02 (estudar):** explicitação de correção conceitual/procedimental em indicador existente, condicionada a ensaios reais.
- **D-R03 (manter):** separação de validação Python, parecer LLM e decisão docente.
- **D-R04 (não fazer agora):** mudança de README/DeepSeek e implementação do provedor; executar na etapa da API GroqCloud.
- **D-R05 (próximo marco):** criar ensaio reproduzível do Juiz para o caso real e mutações pedagógicas, antes de melhorar geradores.
- **D-R06 (não alegar):** rubrica “validada”, IA Juiz “precisa” ou eficácia estatística sem evidências empíricas suficientes.

## 8. Referências verificadas

1. BIGGS, John. **Enhancing teaching through constructive alignment**. *Higher Education*, v. 32, p. 347–364, 1996. DOI: https://doi.org/10.1007/BF00138871.
2. BROOKHART, Susan M. **How to Create and Use Rubrics for Formative Assessment and Grading**. Alexandria: ASCD, 2013. https://www.ascd.org/books/how-to-create-and-use-rubrics-for-formative-assessment-and-grading?chapter=what-are-rubrics-and-why-are-they-important.
3. ANDERSON, Lorin W.; KRATHWOHL, David R. (eds.). **A Taxonomy for Learning, Teaching, and Assessing: A Revision of Bloom's Taxonomy of Educational Objectives**. New York: Longman, 2001. Registro bibliográfico: https://www.loc.gov/item/00063423/.
4. BRASIL. Conselho Nacional de Educação. **Resolução CNE/CEB nº 1, de 4 de outubro de 2022**. Normas sobre Computação na Educação Básica — Complemento à BNCC. https://portal.mec.gov.br/docman/outubro-2022-pdf/241671-rceb001-22/file.
5. CAST. **Universal Design for Learning Guidelines, version 3.0**. 2024. https://udlguidelines.cast.org/.
6. ZHENG, Lianmin et al. **Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena**. *Advances in Neural Information Processing Systems* (NeurIPS), 2023. https://papers.nips.cc/paper_files/paper/2023/hash/91f18a1287b398d378ef22505bf41832-Abstract-Datasets_and_Benchmarks.html.

**Limites da revisão bibliográfica:** obras de avaliação educacional fundamentam o desenho proposto; não constituem por si só validação empírica da rubrica da AulaIA. A seleção e a operacionalização dos critérios também decorrem de decisões documentadas na especificação do projeto.
