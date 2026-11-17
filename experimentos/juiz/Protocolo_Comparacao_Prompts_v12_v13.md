# Protocolo prospectivo — Comparação do prompt `juiz-v1.2` com `juiz-v1.3`

**Data:** 17/11/2026. **Situação:** desenho e critérios registrados antes da primeira
chamada real da **v1.3**. As respostas anteriores da v1.2 são conhecidas
e foram usadas para decidir a melhoria. Não usar este documento como
entrada da IA Juiz; contém expectativas do pesquisador.

## 1. Hipótese e controle de viés

A v1.2 detectou o desalinhamento de evidência na V01 (3/3), mas
ignorou a comparação invertida do algoritmo da V02 (0/3). A mudança
da v1.3 é **somente** uma instrução adicional de auditoria conceitual
genérica: examinar operações e condições explícitas nas etapas,
confrontar resultado com objetivo e evidência, tentar mentalmente um
caso mínimo e localizar contradições verificáveis.

**H-13 (desenvolvimento):** com a nova instrução, o Juiz identifica
a operação conceitualmente incorreta no caso V02, aponta sua
consequência e atribui `componente=sequencia` no caso de uma falha
em ET2; sem perder a capacidade de detectar EVI2 desalinhada na V01.
`critica` é uma expectativa plausível para erro conceitual central,
mas gravidade deverá ser confirmada por avaliador humano.

**Não considerar V02 validação independente:** esse caso motivou
o desenho da v1.3. Um resultado favorável será evidência exploratória
de melhoria em conjunto de desenvolvimento, sujeita a superajuste.

## 2. Invariantes e casos congelados

**Invariantes mantidas:**
- Mesma LLM `openai/gpt-oss-120b` via GroqCloud e o mesmo
  `parecer-juiz-1.0`, `rubrica-juiz-0.1`, seis critérios, política
  `politica-juiz-prelim-0.1`, sequência de agentes e estado docente.
- Temperatura 0, seed 42, `reasoning_effort=medium`,
  `max_completion_tokens=8192`, `--reparos 1`.
- Histórico de v1.2 preservado; SHA-256 **da string exata do prompt v1.2**
  `f93058ca002d0718955d7ff391c77d3343030cd41005c8cf6732dd7f251280b5`.
  A opção `--versao-prompt` seleciona versões sem alterar os planos.

**Conjunto inicial (exploratório / regressão, NÃO holdout):**
1. Caso real original `experimentos/juiz/casos/ordenacao_real_994c4cd5.json`,
   hash canônico `1b3bfddcee405c918e70d91faf1cd931419b71be84e5556885fe05b4dfec352d`.
2. V01 `experimentos/juiz/casos/ordenacao_variante_evi2_desalinhada_01.json`,
   hash `74a89df558601df64ba9fcb50f402f7f2fe80d3baf972fe94aa6c286287c5249`.
3. V02 `experimentos/juiz/casos/ordenacao_variante_bubble_sort_comparacao_invertida_02.json`,
   hash `f98719c00248d16f95b26bfc138780ed0bf17c2eab5c3531a62c3a6b3de87c43`.

## 3. Métricas e condições de êxito

- **Detecção-alvo na V02:** o parecer identifica explicitamente a
  incompatibilidade entre uma regra de comparação na etapa ET2 e a
  ordenação crescente, e aponta `sequencia`. Não basta identificar
  qualquer problema periférico ou reduzir genericamente a nota.
- **Não regressão V01:** identificar que EVI2 não prova a execução
  requerida por OBJ2 e apontar `avaliacao_preliminar`.
- **Controle original:** não inventar falha curricular por exigir todos
  os algoritmos listados na BNCC; registrar separadamente quaisquer
  críticas concretas que mereçam avaliação humana. Não impor 18/18
  como nota obrigatória ao plano real.
- **Pertinência:** gravidade, componente, descrição e recomendação
  devem ser coerentes com cada falha; a revisão do orientador decide
  o que é adequadamente pedagógico.
- **Robustez:** contar três pareceres válidos para cada caso somente
  depois de um primeiro ensaio válido e registrar todas as tentativas;
  HTTP 400/429 e recusas são falhas técnicas, nunca falsas detecções.
  Relatar variações de `system_fingerprint`.
- **Operação:** preservar uso total de tokens, tempo, headers de limite,
  versão do prompt, hash do prompt e commit. Separar sucesso de API
  e aceitação por contrato de qualidade pedagógica.

**O que NÃO constitui resultado de sucesso:** obter JSON válido,
nota alta ou decisão `aguardando_decisao`, apontar uma falha não
relacionada ao defeito alvo ou ajustar o protocolo após a resposta.

## 4. Sequência de execução planejada

1. Atualizar a branch e executar testes offline de compatibilidade.
2. Validar os três casos sem rede com `--somente-validar --versao-prompt juiz-v1.3`.
3. Realizar primeiro ensaio real na V02, sem introduzir exemplo-alvo
   no prompt, para verificar a hipótese H-13.
4. Testar a V01 e o plano original com a mesma versão e parâmetros.
5. Se operacionalmente viável, ampliar para três repetições válidas
   por caso; resultados técnicos inválidos são mantidos separadamente.
6. Fechar a comparação descritiva com v1.2 e submeter achados a
   especialista/docente. Não alegar significância estatística,
   precisão populacional nem causalidade exclusiva do prompt,
   pois `system_fingerprint` pode variar.
7. **Criar pelo menos um caso realmente novo e não usado no refinamento**
   antes de reivindicar qualquer validação externa da melhoria.
   Registrar hipótese desse caso antes de avaliá-lo.

**Para uma comparação posterior mais forte**, considerar avaliação
intercalada v1.2/v1.3 com controle de janela/TPM e plano idêntico;
a série histórica da v1.2 permanece disponível como referência
observacional, não como ensaio pareado contemporâneo.

## 5. Comandos da CLI (PowerShell em `aula-ia-backend`)

Atualizar:
```powershell
git pull --ff-only origin feat/poc05b-juiz-groq
```

Testes offline:
```powershell
python -S -m unittest discover -s tests -p '*juiz*.py' -q
```

Validar V02 sem rede:
```powershell
python ensaio_juiz.py avaliar --caso ../experimentos/juiz/casos/ordenacao_variante_bubble_sort_comparacao_invertida_02.json --versao-prompt juiz-v1.3 --somente-validar
```

Primeira chamada real, **apenas depois dos testes**:
```powershell
python ensaio_juiz.py avaliar --caso ../experimentos/juiz/casos/ordenacao_variante_bubble_sort_comparacao_invertida_02.json --versao-prompt juiz-v1.3 --reparos 1
```

Reprodução de prompt antigo (não uma nova chamada obrigatória):
```powershell
python ensaio_juiz.py avaliar --caso ../experimentos/juiz/casos/ordenacao_variante_bubble_sort_comparacao_invertida_02.json --versao-prompt juiz-v1.2 --somente-validar
```

**Nenhum ensaio real v1.3 foi executado durante a criação deste protocolo.**

## 6. Tentativa real v1.3 bloqueada por limite da API (registro posterior)

Em **17/11/2026 às 19:21:24 UTC**, após a validação local da V02 com
`status=validado_localmente`, a primeira tentativa real de avaliar
V02 pela `juiz-v1.3` **não produziu parecer**:
`status=falha`, **HTTP 429** (`rate_limit_exceeded`, `type=tokens`).
Foi uma única chamada HTTP, sem reparo e sem resposta com métricas de uso.
Não contar como acerto, falso negativo ou parecer válido da v1.3.

- Registro bruto local: `aula-ia-backend/local/ensaios_juiz/20261117T192124Z-1620642ff976/resultado.json`.
- SHA-256 do arquivo bruto enviado para análise:
  `980474589f42a605ec067c92e0ae7f4dfd9a3d5d63ccc18075d0d8df4a1c43b6`
  (39.295 bytes). O bruto **não** foi incorporado ao Git.
- Commit em execução: `1ba402f22d80c4322e8f4329f99dba5a1e40952c`,
  `arvore_modificada=false`.
- Caso V02 SHA-256 do arquivo:
  `05b836174ea2595c9db1140e6fe43dc44695b34b7bc284baf0a127316ff7cf31`.
  Plano canônico: `f98719c00248d16f95b26bfc138780ed0bf17c2eab5c3531a62c3a6b3de87c43`.
- Prompt: `juiz-v1.3`, SHA-256
  `bdb7f05ee34f5aa59c4ea410282fa267bcbb057d370e0f8be223ad33367f2bd8`.
  Mesma rubrica, contrato, modelo `openai/gpt-oss-120b` e parâmetros
  congelados do protocolo.
- Janela de tokens informada pelo provedor: limite **8.000 TPM**;
  **5.474 usados** e **5.066 solicitados**; apenas **2.526 restantes**
  naquele instante. Header `Retry-After: 20`, reset de tokens
  `41.055s`. Tempos relativos são referentes àquela tentativa,
  não garantias de disponibilidade futura.

**Encaminhamento:** só repetir a **mesma** solicitação depois de a
janela de limite estar liberada; não modificar prompt, caso, parâmetros,
política ou gabarito para contornar esse bloqueio. O status da v1.3
permanece **zero pareceres reais válidos**.

## 7. Primeiro parecer real válido da v1.3 — 17/11/2026, V02

**Seção acrescentada APÓS a execução real.** As hipóteses e critérios das
seções 1–5 não foram modificados. A tentativa HTTP 429 da seção 6 permanece
como **falha técnica sem parecer**, não entra nos resultados pedagógicos.

- **Horário da avaliação:** `2026-11-17T19:24:57.666005+00:00`.
- **Registro bruto local:** `aula-ia-backend/local/ensaios_juiz/20261117T192457Z-dc6c34345f59/resultado.json`.
- **SHA-256 do arquivo bruto anexado:** `cbc43497c61335b14d5800c99e7203e411d555c31de51912df9e87fff6ec7b33` (**99.720 bytes**).
  O registro bruto não foi adicionado ao GitHub. Este arquivo e o resumo
  estruturado abaixo permitem relacionar o resultado à evidência original.
- **Commit de execução:** `f965f814c953c69fc91b8af796e2fb8255433170`;
  `arvore_modificada=false`. A alteração desde a tentativa de 429 foi
  exclusivamente documental.
- **Caso V02:** SHA-256 de arquivo `05b836174ea2595c9db1140e6fe43dc44695b34b7bc284baf0a127316ff7cf31`,
  plano canônico `f98719c00248d16f95b26bfc138780ed0bf17c2eab5c3531a62c3a6b3de87c43`.
- **Prompt:** `juiz-v1.3`, SHA-256 `bdb7f05ee34f5aa59c4ea410282fa267bcbb057d370e0f8be223ad33367f2bd8`.
  Permaneceram `rubrica-juiz-0.1`, `parecer-juiz-1.0`,
  `politica-juiz-prelim-0.1`, modelo `openai/gpt-oss-120b`,
  temperatura 0, seed 42, `reasoning_effort=medium`,
  `max_completion_tokens=8192` e `--reparos 1`.

### 7.1 Resultado bruto e leitura do pesquisador

**Status técnico:** `sucesso`; **HTTP 200**; um único envio; parecer
estrutural e semanticamente válido pelo contrato; `finish_reason=stop`;
**nenhum reparo usado**.

| Critério | Nota (0–3) |
|---|---:|
| `aderencia_curricular` | 1 |
| `alinhamento_objetivos` | 3 |
| `coerencia_metodologica` | 1 |
| `viabilidade` | 3 |
| `avaliacao_aprendizagem` | 3 |
| `inclusao` | 3 |
| **Total** | **14/18** |

**Duas falhas apontadas para o mesmo defeito central**, ambas
`componente=sequencia`, `gravidade=critica`:

1. `F1`, `criterio=aderencia_curricular`: ET2 manda trocar pares
   adjacentes se o número da esquerda for **menor** que o da direita;
   a regra de troca esperada para ordenação **crescente** é trocar
   quando a esquerda for **maior**.
2. `F2`, `criterio=coerencia_metodologica`: a regra de ET2
   contradiz a metodologia e a execução pretendida do Bubble Sort;
   sugere corrigir a etapa ET2.

O parecer inclui correção causalmente adequada da comparação e localiza
a falha no componente correto. **A hipótese-alvo H-13 teve detecção
positiva nesta primeira execução válida.** As duas falhas representam
**duas leituras do mesmo defeito experimental**, não dois defeitos
independentes.

**Decisão determinada por código:** `revisao_necessaria`;
`componentes_a_corrigir=["sequencia"]`;
`componentes_invalidados=["sequencia","avaliacao_final","adaptacao"]`;
`falhas_que_motivam=["F1","F2"]`. Nenhuma correção pedagógica nem
aprovação docente foi executada.

**Métricas informadas pela API:** 4.778 tokens de entrada,
2.446 de saída, **7.224 no total**. O ensaio durou **6,580651 s**
(latência de chamada **6,458269 s**); `system_fingerprint=fp_fe269835c7`.
O custo financeiro não foi informado; não estimar custo zero.

**Limitação que permanece:** a justificativa de `viabilidade=3`
invocou diretamente `15 min + 35 min = 50 min`, apesar da instrução
explícita de que a soma já foi verificada em Python e não deve ser
tomada como evidência de viabilidade pedagógica. Isso é um
**descumprimento de instrução**, não um defeito V02 adicional.

### 7.2 Comparação provisória com a v1.2

| Variável no mesmo caso V02 | `juiz-v1.2` (histórico) | `juiz-v1.3` |
|---|---|---|
| Pareceres válidos | 3 | **1** |
| Detecção da comparação invertida | **0/3** | **1/1** |
| Notas totais | 18/18, 18/18, 17/18 | 14/18 |
| Decisões | 3 × `aguardando_decisao` | `revisao_necessaria` |
| Erro técnico separado | 0 na série válida | 1 tentativa HTTP 429 anterior à resposta válida |

**Interpretação restrita:** o resultado é **promissor**, mas uma única
detecção no caso que motivou o novo prompt **não demonstra generalização,
estabilidade, sensibilidade populacional ou causalidade isolada do texto do prompt**.
O caso não é holdout; o `system_fingerprint` também pode variar.
Não tratar 1/1 como taxa robusta nem anunciar a v1.3 como validada.

**Próximo controle:** testar V01 com v1.3 para detectar possível regressão
e o plano original sem edição para examinar falsos positivos. Manter
o prompt v1.3 congelado, registrar cada chamada/resultado, e depois
verificar repetibilidade da V02 em mais respostas válidas com pausas
operacionais suficientes para evitar HTTP 429. Guardar o gabarito
fora da requisição da LLM. Realizar avaliação com casos novos
não usados para refinar o prompt antes de reivindicar qualidade externa.

**Resumo estruturado:** [V02_prompt_v13_20261117T192457Z_analise.json](resultados/V02_prompt_v13_20261117T192457Z_analise.json).

## 8. Primeiro controle de regressão V01 — `juiz-v1.3`, 17/11/2026

**Registro pós-execução, preservando intacta a hipótese da seção 1 e o protocolo prospectivo.**
A avaliação real de V01 pelo novo prompt é um controle exploratório de
não regressão no caso usado previamente para desenvolver `juiz-v1.2`;
**não é validação cega ou independente**.

- **Início (UTC):** `2026-11-17T19:27:51.136419+00:00`.
- **Registro bruto local:** `aula-ia-backend/local/ensaios_juiz/20261117T192751Z-26db5472e016/resultado.json`.
- **SHA-256 do bruto efetivamente inspecionado:** `ed95fce497f2a03ba9d704f12cf2cc9d58e0b1d41213c1917f1ec8f3be032e4c`;
  **100.285 bytes**. O arquivo completo não foi incorporado ao Git.
- **Commit local executado:** `559c6b4e640d6803daa55d92aa805aaec1bf51f6`,
  `arvore_modificada=false`. Módulos de execução iguais aos do teste
  V02-v1.3 anterior; apenas atualizações documentais entre commits.
- **Variante V01:** caso SHA-256 `6d1d376c812963648620c6e2462e1a9ef22975f1bc1d1e6a339408492e66dcd5`,
  plano canônico SHA-256 `74a89df558601df64ba9fcb50f402f7f2fe80d3baf972fe94aa6c286287c5249`,
  alteração única em `plano.avaliacao_aprendizagem.evidencias[1].evidencia_esperada`.
- **Versão avaliada:** `juiz-v1.3`, prompt SHA-256
  `bdb7f05ee34f5aa59c4ea410282fa267bcbb057d370e0f8be223ad33367f2bd8`,
  `rubrica-juiz-0.1`, `parecer-juiz-1.0`, Groq
  `openai/gpt-oss-120b`; temperatura 0, seed 42,
  `reasoning_effort=medium`, `max_completion_tokens=8192`, `--reparos 1`.

### 8.1. Observações no parecer

**Técnica:** `status=sucesso`, `modo=api_real`, HTTP 200, **uma chamada**,
parecer validado sem reparo, `finish_reason=stop`.
**Notas por critério:** aderência curricular 2, alinhamento de objetivos 3,
coerência metodológica 3, viabilidade 3, avaliação da aprendizagem 2,
inclusão 3; **total 16/18**.

- **F1 — detecção-alvo correta:** `criterio=avaliacao_aprendizagem`,
  `componente=avaliacao_preliminar`, `gravidade=maior`. Identificou que
  `EVI2` apenas relata atenção e gosto pela atividade e não comprova
  a simulação de trocas de cartões solicitada em `OBJ2`.
  Propôs substituir EVI2 por evidência observável da execução.
  **H-13 de não regressão V01 foi atendida neste primeiro parecer válido.**
- **F2 — possível falso positivo curricular:** `criterio=aderencia_curricular`,
  `componente=objetivos`, `gravidade=menor`. O modelo questionou que
  o objetivo geral se refere a “algoritmos clássicos de ordenação” (plural)
  enquanto a aula trabalha somente Bubble Sort, e sugeriu incluir outro
  algoritmo ou restringir a redação do objetivo. A observação sobre a
  precisão do plural é discutível; **exigir mais algoritmos como requisito
  da BNCC em uma única aula de 50 minutos é indevido** e contraria o
  controle explícito de escopo do prompt. Marcar como **possível falso
  positivo** até adjudicação docente; não classificar como
  verdadeira falha curricular sem revisão humana.
- **Viabilidade:** a nota 3 foi fundamentada em parte pela soma
  `15 + 35 = 50`, embora a soma seja verificação determinística já
  realizada e haja proibição expressa do uso dessa justificativa isolada.

**Decisão determinística do contrato:** `em_correcao`, pois F1 é
`maior`; `componentes_a_corrigir=["avaliacao_preliminar"]`,
`falhas_que_motivam=["F1"]`. F2 `menor` não acionou correção.
Os componentes invalidados por dependência foram
`["avaliacao_preliminar","metodologia","sequencia","avaliacao_final","adaptacao"]`.
Nenhum ciclo de correção pedagógica foi executado e a aprovação do
professor permaneceu inalterada.

**Métricas informadas pelo provedor:** 4.762 tokens de prompt,
3.059 tokens de conclusão, **7.821 tokens totais**; tempo total
do ensaio **7,403247 s**, latência de chamada **7,280655 s**;
`system_fingerprint=fp_7a4ab09ae4`; custo monetário não informado.
O consumo ficou próximo da cota de 8.000 tokens/minuto, de modo
que chamadas consecutivas podem ser bloqueadas por HTTP 429.

### 8.2. Resultado parcial de comparação v1.2 × v1.3

| Caso | `juiz-v1.2` histórico | `juiz-v1.3` inicial |
|---|---|---|
| V01 (evidência EVI2 inadequada) | **3/3 detectaram** | **1/1 detectou** |
| V02 (troca invertida no Bubble Sort) | **0/3 detectaram** | **1/1 detectou** |
| Falso positivo de escopo curricular | Apareceu em ao menos 1 parecer V01 | **Reapareceu na V01** |
| Vício de citar soma dos minutos como viabilidade | Observado | **Persistente** |

**Interpretação restrita:** não regressão demonstrada **nesta execução
V01**, mas o prompt v1.3 não resolveu o problema de escopo curricular,
nem o de fundamentar viabilidade em análise além da aritmética.
A diferença de detecção V02 ainda não permite inferir estabilidade ou
eficácia geral: são dois casos conhecidos no desenvolvimento, com
somente um parecer válido novo por caso.

**Próximo controle:** executar o plano original imutável com `juiz-v1.3`
para observar se a nova versão introduz falso positivo no caso sem
defeito injetado. Registrar todas as críticas que apareçam em vez de
pressupor que o original deva receber 18/18. Depois decidir a série
de repetições e preparação de casos novos, mantendo o prompt congelado.

**Resumo estruturado:**
[V01_prompt_v13_20261117T192751Z_analise.json](resultados/V01_prompt_v13_20261117T192751Z_analise.json).
