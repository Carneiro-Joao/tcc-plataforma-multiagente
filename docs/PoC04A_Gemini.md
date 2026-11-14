# PoC 04A — migração para Gemini e aplicação dos contratos

Data de revisão: 14/11/2026. Base de código: `3939dfd9aad00b3850f9e1c025af705cf812f644`; contratos: `70cfff23333e728f31e6b34d283c0e2f7be790a4`. Referência documental: `33e8025c7bbdae8ab27c37332f2c3b9d3cc11903`.

**Alcance:** integração parcial dos contratos v0.1 e adaptador Gemini. Não equivale à conclusão da PoC 04A prevista na R2. Veja [o confronto com o planejamento](Alinhamento_PoC04A.md).

## Problema observado

Na sondagem OpenRouter, seis chamadas terminaram com `stop`, mas o plano foi rejeitado: a metodologia, anteriormente string, voltou como objeto no integrador. A rodada usou cinco modelos diferentes, consumiu 21.441 tokens conhecidos e levou 174,976 segundos. Esses dados descrevem uma rodada, não uma comparação de desempenho entre provedores.

Também apareceram campos extras na metodologia, alterações no contexto e formatos de adaptação incompatíveis. A avaliação apresentava resultados como se a aula já tivesse ocorrido. O último problema é semântico: JSON válido não o resolve.

## Decisões implementadas

- Gemini nativo por REST, no backend. Cinco especialistas compartilham o identificador fixo `gemini-3.5-flash-lite` e usam prompts distintos. Não há SDK OpenAI, OpenRouter ou escolha aleatória de modelo neste fluxo.
- Integração em Python com mapeamento explícito. Código e texto BNCC, ano, tema, tipo, duração e recursos provêm da entrada confirmada. O título é `Plano de aula — {tema}`.
- Validador `contratos/validacao.py`, seus testes e os dois arquivos de dados incorporados integralmente de `feat/poc04a-contratos`; diagnósticos adaptados ao pipeline em `contratos/execucao.py`. Sem biblioteca externa para validar. Contratos v0.1 aplicados ao código de produção. Tipos estritos: `true`, `5.0` e `"5"` não são minutos inteiros. Rejeição de extras e de textos vazios; não há coerção.
- O Gemini recebe `generationConfig.responseFormat.text` com `mimeType: APPLICATION_JSON` e o schema do especialista. A validação local continua obrigatória, inclusive soma de minutos e igualdade dos recursos.
- Estado de falha registrado, sem fabricar plano nem apagar a tentativa. Aprovação humana somente da revisão atual em rascunho. Falha HTTP não inicia novas tentativas automaticamente.
- Site sem login, cadastro ou histórico privado. SQLite persistente local preserva versões e falhas conforme RF14/RF21; `--temporario` oferece demonstração descartável optativa.

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

- 63 testes aprovados e um teste opcional de ranking híbrido ignorado.
- Os 27 casos da revisão são exercitados como subtestes contra o validador de produção.
- Fixture sintética integrada exatamente ao plano esperado, sem LLM.
- Transporte Gemini simulado: cinco chamadas, reparo localizado, falhas, JSON duplicado, credenciais, bloqueio, truncamento e concorrência.
- HTTP local exercitado: confirmação, geração, aprovação, bloqueio de aprovação de falha e nova revisão após falha.
- CLI executado em simulação com 45 minutos; resultado gravado com sucesso. Sintaxe dos scripts JavaScript conferida.
- Navegador automatizado indisponível por restrição de processos/sockets do ambiente. Revisão visual local pendente.
- Chamada Gemini real, qualidade pedagógica, latência real e consumo real: **pendentes**.

Próxima verificação: executar uma rodada real com chave do projeto Free Tier; examinar o JSON completo, inclusive respostas rejeitadas; depois repetir com as mesmas entradas/modelo para observar estabilidade. Os números da rodada OpenRouter não devem ser comparados diretamente ao pipeline de cinco chamadas sem separar o efeito da retirada do integrador LLM.

A IA Juiz independente, rubrica, correção pedagógica dirigida e experimento comparativo continuam fora deste incremento. Não há nota automática de qualidade nem aprovação automática. A interface mantém a revisão e aprovação do professor.

## Contrato operacional e arquitetura-alvo

O contrato `poc04a-0.1` não implementa ainda as 11 seções de `PlanoDeAula 2.0`. A geração atual mantém cinco chamadas normais, incluindo uma avaliação final. A arquitetura-alvo mantém cinco especialistas gerativos, mas prevê duas chamadas do especialista de avaliação (preliminar e final). Portanto a migração de provedor, isoladamente, não satisfaz integralmente RF09/RF10/RF11/RF12/RF25.

A incorporação da branch de contratos preserva seus cinco arquivos sem alteração e inclui o commit original na ancestralidade da branch Gemini. A branch documental e seu PR permanecem separados; os documentos R2 não foram reescritos nem mesclados por esta integração.
