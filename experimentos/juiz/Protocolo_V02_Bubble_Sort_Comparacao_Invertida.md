# PoC 05B / RD-002 — Pré-registro da variante V02: comparação invertida no Bubble Sort

**Data de pré-registro:** 17/11/2026. **Estado:** variante e hipótese congeladas **antes da primeira avaliação real pelo Juiz**. Este documento é o gabarito provisório do pesquisador: **não incluir na entrada nem no prompt da LLM**. Ainda não há resultados de V02; adicioná-los em seção separada após cada ensaio.

## 1. Objetivo e desenho

Testar se o agente Juiz detecta **erro conceitual no algoritmo Bubble Sort**, diferente do erro de evidência EVI2 × OBJ2 da V01. O experimento usa a mesma geração real extraída do SQLite, editada em **um campo textual** do plano. Preservar o prompt `juiz-v1.2`, a rubrica `rubrica-juiz-0.1`, o contrato `parecer-juiz-1.0`, a política `politica-juiz-prelim-0.1` e os parâmetros operacionais da V01 para comparação.

- **Caso-base imutável:** `experimentos/juiz/casos/ordenacao_real_994c4cd5.json`, geração SQLite `994c4cd51d944ca6a1344b15366c3971`.
- **Variante V02:** `experimentos/juiz/casos/ordenacao_variante_bubble_sort_comparacao_invertida_02.json`, identificador `V02-BUBBLE-COMPARACAO-INVERTIDA`.
- **Origem:** `variante_controlada`. A modificação foi manual; `modelo_gerador=gemini-3.5-flash-lite` referencia apenas a geração original.
- **SHA-256 canônico do plano-base:** `1b3bfddcee405c918e70d91faf1cd931419b71be84e5556885fe05b4dfec352d`.
- **SHA-256 canônico do plano V02:** `f98719c00248d16f95b26bfc138780ed0bf17c2eab5c3531a62c3a6b3de87c43`.
- **SHA-256 canônico da entrada, idêntica à original:** `b57d56ed6d391b9a979699a7af44c9fb90143df021a4a83d8c901b6d9ede5a8c`.
- **Campo único manipulado:** `plano.desenvolvimento[1].acao_discente` (`ET2`).
- **Contexto preservado:** 8º ano, 50 minutos, Computação desplugada, papel, EF08CO03, ordenação crescente.

## 2. Manipulação isolada — hipótese de erro conceitual

**Antes (caso-base, `ET2.acao_discente`):**

> Manipular os cartões de papel comparando pares adjacentes, trocando-os de posição quando fora de ordem e reorganizando-os em sequência crescente.

**Depois (V02, `ET2.acao_discente`):**

> Manipular os cartões de papel comparando pares adjacentes e trocando-os de posição quando o número da esquerda for menor que o número da direita, repetindo o procedimento para obter uma sequência crescente.

No Bubble Sort em **ordem crescente**, deve-se trocar dois elementos adjacentes se o número da **esquerda for maior** que o da direita. A V02 instrui trocar quando a esquerda é **menor**, regra que favorece ordem **decrescente** e contradiz a intenção explícita de obter sequência crescente. Exemplo de controle humano: o par `[2, 5]` seria invertido indevidamente em `[5, 2]`; o par `[5, 2]` permaneceria sem troca. **Esse exemplo explicativo é do protocolo, não foi acrescentado ao plano enviado ao Juiz.**

O restante do desenvolvimento, `ET2.atividade`, `ET2.acao_docente`, objetivos, metodologia, instrumentos, evidências, adaptações e contexto da BNCC permanecem literalmente iguais ao caso-base. A V02 **não** parte da V01: a evidência `EVI2` nesta variante é a do plano real, sem alteração.

## 3. Hipótese registrada antes da chamada

- **H-V02 (principal):** o Juiz identifica que a regra de troca em `ET2.acao_discente` está invertida para ordenação crescente, indicando explicitamente o sentido correto da comparação ou a tendência a ordenar em ordem decrescente. Não basta apontar deficiência genérica sem identificar a inversão.
- **Localização obrigatória da falha:** `componente="sequencia"` (pois o texto incorreto está em `desenvolvimento`). Para esta variante, sugerir corrigir BNCC, objetivo ou evidência como *componente primário* não resolve o defeito isolado.
- **Critério esperado:** `coerencia_metodologica` (contradição entre método/objetivo e ação executada) ou `aderencia_curricular` (algoritmo aplicado incorretamente). Registrar qual critério foi escolhido e se a justificativa é pertinente, sem mudar as regras após observar o resultado.
- **Gravidade pedagogicamente provável:** `critica`, pois há erro conceitual central na execução do algoritmo; o contrato prevê revisão humana nesse caso. `maior` é possível se o avaliador entender que a etapa pode ser corrigida localmente, mas ficará registrada como divergência de gravidade e exigirá revisão do orientador.
- **Nota e decisão esperadas:** no critério da falha, nota máxima 1 se `critica`, ou até 2 se `maior`. Com `critica`, a política sugere `revisao_necessaria`; com `maior`, `em_correcao`.
- **Resultado negativo:** o Juiz não aponta erro na regra de comparação, concede notas máximas sem ressalvas à ação ET2 ou identifica apenas problemas não relacionados à inversão.
- **Falsos positivos a monitorar:** exigência de vários algoritmos em aula única EF08CO03; sugestão de alterar habilidade oficial; supostos defeitos não suportados no plano.
- **Verificações adicionais:** julgamento sobre viabilidade não deve se basear apenas na soma de minutos; verificar se o modelo propõe correção direcionada à sequência, sem alterar o catálogo BNCC.

**Importante:** estas são expectativas do pesquisador, ainda sem validação de especialista. Documentar também divergências e erros técnicos. Não reenquadrar resultados a posteriori para obter sucesso artificial.

## 4. Procedimento e preservação das evidências

1. Fazer `git pull --ff-only origin feat/poc05b-juiz-groq` na pasta `aula-ia-backend`.
2. Executar regressões offline `python -S -m unittest discover -s tests -p 'test_variante*juiz.py' -q`. Elas comparam todos os campos, validam os hashes e usam `carregar_caso` para acionar o contrato, sem consumir tokens.
3. Executar `python ensaio_juiz.py avaliar --caso ../experimentos/juiz/casos/ordenacao_variante_bubble_sort_comparacao_invertida_02.json --somente-validar`.
4. Após validação local, executar a **primeira avaliação real**: `python ensaio_juiz.py avaliar --caso ../experimentos/juiz/casos/ordenacao_variante_bubble_sort_comparacao_invertida_02.json --reparos 1`. Não enviar este protocolo nem o gabarito à API.
5. Guardar o diretório gerado `local/ensaios_juiz/<UTC-id>/` com `inicio.json`, `caso.json` e `resultado.json`; não sobrescrever, não alterar plano e não armazenar chaves de API.
6. Avaliar a primeira chamada pelo contrato, depois pelos campos `falhas[].criterio`, `componente`, `gravidade`, `descricao` e `decisao`. Registrar acertos, omissões, falsos positivos e falhas técnicas em seção posterior, usando os nomes reais dos arquivos de ensaio.
7. Para replicações, usar exatamente a mesma versão de código, prompt, rubrica, parâmetros e SHA-256 do caso; diferenciar contagem de tentativas de HTTP, pareceres válidos e casos independentes. Uma série de repetições não estima validade geral; prever revisão pedagógica humana.

## 5. Cuidado metodológico

A V01 mostrou detecção de falha de evidência em 3/3 pareceres válidos, mas instabilidade em gravidade e um falso positivo curricular; ocorreu também uma chamada de reparo bloqueada por HTTP 429. **V02 é caso distinto**, voltado à correção de algoritmo. Como o plano conserva sua BNCC e os demais componentes, o critério central de acerto é a identificação do sinal invertido na comparação, não apenas alterar a decisão para `em_correcao` ou `revisao_necessaria`.

Nenhum resultado real V02 foi obtido ou alegado neste pré-registro.

## 6. Primeiro ensaio real da V02 — análise posterior ao pré-registro

**Momento do ensaio (UTC):** 2026-11-17T19:01:59.053845+00:00. Esta seção é um resultado **posterior** à hipótese congelada nas seções 1–5 acima, não uma alteração retroativa dessa hipótese.

**Registro original preservado localmente:** `aula-ia-backend/local/ensaios_juiz/20261117T190159Z-004f470ecc98/resultado.json`.
**SHA-256 do arquivo bruto recebido para análise:** `9ff3c4e7cc51d43a35c519fd9a9fac0621bfdc8c001bf814ad2f7709ebc1e0c6`.
**SHA-256 do arquivo do caso:** `05b836174ea2595c9db1140e6fe43dc44695b34b7bc284baf0a127316ff7cf31`.
**SHA-256 canônico do plano:** `f98719c00248d16f95b26bfc138780ed0bf17c2eab5c3531a62c3a6b3de87c43`.
**Código:** commit `cffae67459cdf22bc86a146d4f08f50c1a7aaff8`, árvore não modificada.
**Modelo:** `openai/gpt-oss-120b`; prompt `juiz-v1.2`, rubrica `rubrica-juiz-0.1`, contrato `parecer-juiz-1.0`, seed 42, temperatura 0 e demais parâmetros conforme §4.
**Resposta do serviço:** HTTP 200, uma chamada, sem reparo, `finish_reason=stop`, esquema aceito, `status=sucesso`.
**Métricas:** 4.665647 s de ensaio total; 4.551826 s de latência da chamada; 4.464 tokens de prompt, 1.743 tokens de completion (6.207 no total); `system_fingerprint=fp_fe269835c7`. `ciclos_pedagogicos_executados=0`, `aprovacao_docente=nao_alterada`.

### 6.1. Parecer observado

| Critério | Nota (0–3) |
|---|---:|
| `aderencia_curricular` | 3 |
| `alinhamento_objetivos` | 3 |
| `coerencia_metodologica` | 3 |
| `viabilidade` | 3 |
| `avaliacao_aprendizagem` | 3 |
| `inclusao` | 3 |
| **Total** | **18/18** |

- `falhas=[]`: **nenhuma falha foi apontada**.
- `decisao.proximo_estado="aguardando_decisao"`, `componentes_a_corrigir=[]`, `componentes_invalidados=[]`.
- A justificativa de coerência metodológica afirma haver ações discentes coerentes em ET1/ET2, **sem citar a regra errada em `ET2.acao_discente`**.
- A justificativa de avaliação da aprendizagem dá nota 3, apoiada nos vínculos EVI/INS, sem perceber que o procedimento de troca definido em ET2 produziria ordenação decrescente, embora se exija crescente.
- A viabilidade volta a citar a **soma de minutos**, previamente verificada por código, e pressupõe um "número pequeno de cartões", que não foi especificado.

### 6.2. Confronto com a hipótese pré-registrada

**Resultado:** **falso negativo / não detecção da falha injetada** nesta primeira avaliação da V02.

A regra incorreta é explícita: para ordenação **crescente**, ET2 manda trocar cartões quando a **esquerda é menor** que a direita. A regra resultante é oposta à ordenação crescente. Como o Juiz não apontou inversão da comparação, nem defeito de sequência, nem qualquer outra falha, **H-V02 não foi confirmada neste ensaio**.

A decisão `aguardando_decisao` é uma consequência determinística do parecer emitido sem falhas; o mecanismo de decisão não detecta esse erro independentemente. **Não interpretar** essa decisão como aprovação pedagógica nem alterar o gabarito do pesquisador para conciliar a saída.

### 6.3. Limites e ações previstas

Uma única avaliação permite afirmar **não detecção neste caso**; não permite estimar taxa de erro, precisão geral ou confiabilidade estatística. Conservar a configuração congelada e repetir V02 como teste de estabilidade, registrando também HTTP 400/429 separadamente se ocorrerem. Não modificar o prompt até fechar uma série predefinida de repetições e submeter o gabarito à validação humana. A correção automática de planos por IA continua desabilitada, sem alteração na aprovação docente.

**Resumo arquivado em formato estruturado:** [V02_20261117T190159Z_analise.json](resultados/V02_20261117T190159Z_analise.json). A evidência bruta completa de 91.294 bytes e seu SHA-256 acima continuam no arquivo local citado; este commit preserva **resumo verificável**, não uma cópia integral do registro.

## 7. Segundo ensaio real da V02 — 17/11/2026

**Esta seção foi redigida depois da segunda resposta real.** Hipótese e gabarito da V02 (seções 1–5) permanecem pré-registrados e inalterados. O primeiro ensaio (§6) foi preservado integralmente.

**Registro bruto local:** `aula-ia-backend/local/ensaios_juiz/20261117T190500Z-67f19a8598e0/resultado.json`.  
**SHA-256 do arquivo bruto carregado para análise:** `64a045979b3f6bb7d42c6d13de8f90f68d2459d15be8aa17475ac05023e2462e` (`90585` bytes).  
**Arquivo do caso:** SHA-256 `05b836174ea2595c9db1140e6fe43dc44695b34b7bc284baf0a127316ff7cf31` (mesmo da primeira avaliação).  
**Plano canônico:** SHA-256 `f98719c00248d16f95b26bfc138780ed0bf17c2eab5c3531a62c3a6b3de87c43` (mesmo da primeira avaliação).  
**Commit local:** `ad2631bf44184e3b59dbea4703a7127795d3a135` (atualização apenas documental desde o primeiro ensaio); `arvore_modificada=false`. Os hashes de código dos módulos executáveis registrados no ensaio não mudaram.  
**Parâmetros congelados:** Groq `openai/gpt-oss-120b`, prompt `juiz-v1.2`, rubrica `rubrica-juiz-0.1`, contrato `parecer-juiz-1.0`, temperatura 0, seed 42, `reasoning_effort=medium`, `max_completion_tokens=8192`, `--reparos 1`.

### 7.1. Observado

- `status=sucesso`, `modo=api_real`, **HTTP 200**, uma chamada, uma resposta aceita; `finish_reason=stop`, nenhuma tentativa de reparo.
- **Seis notas 3/3 (total 18/18)**, `falhas=[]`.
- `decisao.proximo_estado=aguardando_decisao`, `componentes_a_corrigir=[]`, `componentes_invalidados=[]`.
- **Resultado da hipótese H-V02: não confirmada.** O parecer não localiza a inversão do operador de comparação em `ET2.acao_discente`. A saída considera ET2 coerente, apesar de a regra de troca com `esquerda < direita` produzir ordem decrescente, contradizendo a exigência de ordem crescente. É o **segundo falso negativo**.
- Persistem as justificativas problemáticas: viabilidade fundamentada parcialmente na soma dos minutos e invocação de número reduzido de cartões sem contexto informado; descrição de uma sequência que inclui "síntese" sem etapa explicitamente prevista. O parecer também enfatiza vínculos estruturais EVI/INS sem verificar a consistência da lógica algorítmica de ET2.
- **Dados operacionais:** `tempo_total_s=5.345594`; latência da chamada `5.227486` s; `prompt_tokens=4464`, `completion_tokens=2054`, total `6518`; `system_fingerprint=fp_dee443f41b` (diferente do primeiro: `fp_fe269835c7`).
- `aprovacao_docente=nao_alterada`, `ciclos_pedagogicos_executados=0`.

### 7.2. Comparação provisória da V02

| Resultado observado | Ensaio 1 (19:01:59 UTC) | Ensaio 2 (19:05:00 UTC) |
|---|---|---|
| Status técnico | Sucesso / HTTP 200 | Sucesso / HTTP 200 |
| Plano enviado | SHA-256 `f98719c...` | Mesmo SHA-256 |
| Nota total | 18/18 | 18/18 |
| Falhas | 0 | 0 |
| Identificou inversão da regra? | **Não** | **Não** |
| Decisão | `aguardando_decisao` | `aguardando_decisao` |
| Classificação do pesquisador | Falso negativo | Falso negativo |
| `system_fingerprint` | `fp_fe269835c7` | `fp_dee443f41b` |

**Síntese 2/2:** erro injetado foi **omitido em ambas as respostas válidas**. Isso mede apenas duas repetições do mesmo caso, **não** uma taxa populacional de falso negativo ou validação geral do Juiz. A estabilidade da decisão neste caso **não** equivale à confiabilidade pedagógica: ambas as decisões podem repetir a mesma omissão.

**Encaminhamento:** manter o prompt e a rubrica congelados até completar uma terceira avaliação válida da V02; preservar o resultado bruto no diretório de ensaio e documentar futuros erros técnicos separadamente. A aceitação estrutural do parecer **não** certifica correção do algoritmo e não deve autorizar correção ou aprovação docente automáticas.

**Resumo estruturado:** [V02_20261117T190500Z_analise.json](resultados/V02_20261117T190500Z_analise.json). O arquivo de análise é derivado do registro bruto, que permanece apenas local e não foi adicionado ao Git.

## 8. Terceiro ensaio real da V02 — 17/11/2026

**Análise posterior à execução; hipótese §3 inalterada.** Registro bruto:
`aula-ia-backend/local/ensaios_juiz/20261117T190802Z-f5fb77c4a5b4/resultado.json`,
SHA-256 **`2db2169efe20afcbebcb18effcc9b7d0c32b8b96055827326e0bb5e966cc7395`**, **95996 bytes**, verificado diretamente no arquivo bruto anexado pelo pesquisador.
A entrada e o plano mantiveram os mesmos SHA-256 das duas execuções anteriores:
`05b836174ea2595c9db1140e6fe43dc44695b34b7bc284baf0a127316ff7cf31` (arquivo de caso)
e `f98719c00248d16f95b26bfc138780ed0bf17c2eab5c3531a62c3a6b3de87c43` (plano canônico).

**Reprodutibilidade operacional:** código no commit `065ef032098976a64fa9e57b7edec2f3881e7b2e`
(árvore limpa, hashes dos módulos executáveis iguais aos ensaios anteriores).
Configuração conservada: `openai/gpt-oss-120b`, `juiz-v1.2`, `rubrica-juiz-0.1`, `parecer-juiz-1.0`,
`temperature=0`, `seed=42`, `reasoning_effort=medium`, `max_completion_tokens=8192`, `--reparos 1`.

**Verificação técnica:** HTTP 200, uma chamada, parecer aceito sem reparo; `finish_reason=stop`.
Tempo total do ensaio: **6,247232 s**; latência da chamada **6,088801 s**;
4.464 tokens de entrada, 2.466 de saída (total **6.930**);
`system_fingerprint=fp_96d96a151c`.
Nenhum ciclo de correção pedagógica foi executado; aprovação docente não alterada.

### 8.1. Parecer e desfecho da hipótese

- Notas `aderencia_curricular=3`, `alinhamento_objetivos=3`, `coerencia_metodologica=3`,
  `viabilidade=3`, `avaliacao_aprendizagem=2`, `inclusao=3`: **total 17/18**.
- Uma falha **F1**, `gravidade=menor`, `criterio=avaliacao_aprendizagem`,
  `componente=avaliacao_preliminar`: critérios EVI1/EVI2 descritos como genéricos, sem níveis
  explícitos de desempenho. A pertinência dessa observação não foi adjudicada pelo orientador;
  **não corresponde ao erro de comparação invertida** e não deve contar como detecção da V02.
- `decisao.proximo_estado=aguardando_decisao`,
  `componentes_a_corrigir=[]`, `componentes_invalidados=[]`.
  A falha menor não provoca correção automática pela política.
- **H-V02 não confirmada novamente:** o parecer considerou ET2 metodologicamente coerente,
  sem perceber que a instrução troca cartões quando `esquerda < direita`, produzindo ordem
  decrescente em vez da crescente exigida. Trata-se de **falso negativo quanto ao defeito
  injetado**, apesar de ter encontrado uma ressalva diferente.
- A justificativa de viabilidade voltou a citar a soma 15 + 35 = 50 como argumento,
  apesar da instrução expressa em `juiz-v1.2` para não fazê-lo. A metodologia segue
  alegando uma síntese sem etapa explícita correspondente.

### 8.2. Fechamento da primeira série V02 — três pareceres válidos

| Ensaio UTC | Nota total | Falha da comparação invertida? | Outras falhas | Decisão |
|---|---:|---|---|---|
| `20261117T190159Z-004f470ecc98` | 18/18 | **Não** | Nenhuma | `aguardando_decisao` |
| `20261117T190500Z-67f19a8598e0` | 18/18 | **Não** | Nenhuma | `aguardando_decisao` |
| `20261117T190802Z-f5fb77c4a5b4` | 17/18 | **Não** | Uma `menor`, relacionada a EVI1/EVI2 | `aguardando_decisao` |

**Desfecho descritivo:** detecção da inversão = **0/3**; omissão = **3/3**
nas três respostas aceitas do **mesmo caso**, com variação em justificativas,
notas e falhas secundárias. Não são três casos independentes.
A estabilidade de `aguardando_decisao` não significa qualidade pedagógica:
a política determinística aplicou corretamente as regras a diagnósticos que
omitiram o erro central.

**Comparação com V01:** V01 detectou a falha de evidência injetada em 3/3
pareceres válidos, embora com variação de gravidade e um falso positivo curricular
aparente. A diferença V01/V02 sugere maior dificuldade do Juiz para verificar
a lógica do algoritmo do que vínculos entre objetivo e evidência **neste
pequeno conjunto**, sem permitir estimar capacidade geral por categoria.

**Encerramento da série congelada:** não repetir V02 indefinidamente para
obter um parecer favorável; não mudar o gabarito a posteriori.
A revisão do prompt (eventual `juiz-v1.3`) deve ser tratada como
**nova configuração experimental**, preservando resultados e hashes de `juiz-v1.2`.
Exigir revisão humana de classificações, gravidades e falsos positivos;
manter o fluxo de correção e aprovação docente separados e sem automação.

**Resumo estruturado:** [V02_20261117T190802Z_analise.json](resultados/V02_20261117T190802Z_analise.json).
