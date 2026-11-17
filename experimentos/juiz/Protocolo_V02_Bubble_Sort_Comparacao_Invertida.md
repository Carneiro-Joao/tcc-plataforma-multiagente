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
