# PoC 04A — migração para Gemini e aplicação dos contratos

Data de revisão: 13/11/2026. Base: `3939dfd9aad00b3850f9e1c025af705cf812f644`.

## Problema observado

Na sondagem OpenRouter, seis chamadas terminaram com `stop`, mas o plano foi rejeitado: a metodologia, anteriormente string, voltou como objeto no integrador. A rodada usou cinco modelos diferentes, consumiu 21.441 tokens conhecidos e levou 174,976 segundos. Esses dados descrevem uma rodada, não uma comparação de desempenho entre provedores.

Também apareceram campos extras na metodologia, alterações no contexto e formatos de adaptação incompatíveis. A avaliação apresentava resultados como se a aula já tivesse ocorrido. O último problema é semântico: JSON válido não o resolve.

## Decisões implementadas

- Gemini nativo por REST, no backend. Cinco especialistas compartilham o identificador fixo `gemini-3.5-flash-lite` e usam prompts distintos. Não há SDK OpenAI, OpenRouter ou escolha aleatória de modelo neste fluxo.
- Integração em Python com mapeamento explícito. Código e texto BNCC, ano, tema, tipo, duração e recursos provêm da entrada confirmada. O título é `Plano de aula — {tema}`.
- Contratos v0.1 da revisão anterior aplicados ao código de produção. Tipos estritos: `true`, `5.0` e `"5"` não são minutos inteiros. Rejeição de extras e de textos vazios; não há coerção.
- O Gemini recebe `generationConfig.responseFormat.text` com `mimeType: APPLICATION_JSON` e o schema do especialista. A validação local continua obrigatória, inclusive soma de minutos e igualdade dos recursos.
- Estado de falha registrado, sem fabricar plano nem apagar a tentativa. Aprovação humana somente da revisão atual em rascunho. Falha HTTP não inicia novas tentativas automaticamente.
- Site sem login, cadastro ou histórico durável por padrão. O armazenamento SQLite existente passa a ser temporário por execução; `--banco` mantém persistência opcional.

## Dependências e retentativas

| Especialista | Saídas anteriores recebidas |
|---|---|
| objetivos | nenhuma |
| metodologia | objetivos |
| sequencia | objetivos, metodologia |
| avaliacao | objetivos, metodologia, sequencia |
| adaptacao | objetivos, metodologia, sequencia |

Cada entrada e saída é copiada para evitar mutações compartilhadas e mistura de rastreios entre requisições concorrentes. O integrador recebe as cinco saídas validadas e não faz chamadas externas.

Um erro de JSON/schema/invariante permite no máximo um reparo naquele especialista, preservando a mesma entrada e as mesmas dependências. A resposta inválida e o reparo ficam registrados separadamente. A próxima etapa só executa após sucesso. Cinco chamadas normais, limite de dez com reparos; `--reparos 0` elimina chamadas de reparo.

Erros HTTP, timeout, bloqueio ou término diferente de `STOP` param a execução. Não há fallback de modelo/provedor, nem substituição por demonstração. Uma nova geração solicitada manualmente incrementa a revisão e executa novamente todo o pipeline. A invalidação seletiva e o contador separado de correção pedagógica ficam para a IA Juiz, não são reivindicados nesta entrega.

## Observabilidade e dados

`teste_gemini.py` usa o mesmo gerador do site. Registra JSON local com entradas, conteúdo da API, modelo informado pela resposta, `usageMetadata`, `finishReason`, latência, estados e tentativas. O envelope é mantido para comparação futura. Erros HTTP guardam até 5.000 bytes do corpo, com remoção da chave se ela for ecoada. Headers e URL com credencial não são registrados: a chave vai no header `x-goog-api-key`.

A cota não é inferida pelo script. A conta precisa estar em Free Tier no AI Studio. O schema não garante gratuidade: um projeto com faturamento pode cobrar pelo mesmo identificador. O modelo não é alterado automaticamente. O uso de cada tentativa, inclusive rejeitada, entra no total conhecido; ausência de uso não prova ausência de consumo.

## Evidências e próximos passos

- 32 testes aprovados e um teste opcional de ranking híbrido ignorado.
- Os 27 casos da revisão são exercitados como subtestes contra o validador de produção.
- Fixture sintética integrada exatamente ao plano esperado, sem LLM.
- Transporte Gemini simulado: cinco chamadas, reparo localizado, falhas, JSON duplicado, credenciais, bloqueio, truncamento e concorrência.
- HTTP local exercitado: confirmação, geração, aprovação, bloqueio de aprovação de falha e nova revisão após falha.
- CLI executado em simulação com 45 minutos; resultado gravado com sucesso. Sintaxe dos scripts JavaScript conferida.
- Navegador automatizado indisponível por restrição de processos/sockets do ambiente. Revisão visual local pendente.
- Chamada Gemini real, qualidade pedagógica, latência real e consumo real: **pendentes**.

Próxima verificação: executar uma rodada real com chave do projeto Free Tier; examinar o JSON completo, inclusive respostas rejeitadas; depois repetir com as mesmas entradas/modelo para observar estabilidade. Os números da rodada OpenRouter não devem ser comparados diretamente ao pipeline de cinco chamadas sem separar o efeito da retirada do integrador LLM.

A IA Juiz independente, rubrica, correção pedagógica dirigida e experimento comparativo continuam fora deste incremento. Não há nota automática de qualidade nem aprovação automática. A interface mantém a revisão e aprovação do professor.
