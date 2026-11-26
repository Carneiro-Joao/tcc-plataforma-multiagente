# PoC 10 — Regeneração informada pelas críticas do Juiz + correção de acentuação

**Data:** 25/11/2026 · **Branch:** `feat/poc10-regeneracao-informada` (a partir de `feat/poc09-sondagem-regeneracao-informada`)
**Autorização:** pedido do João em 25/11 ("vamos fazer essa implementação"), depois da sondagem PoC 09. É mudança de código depois do
congelamento de 19/11, autorizada por ele. Decisão **pendente de ratificação** pelo orientador (reversível: `--regeneracao cega`).
**Base da decisão:** `docs/PoC09_Resultado_Sondagem.md` (exploratória, n = 5).

---

## 1. Resumo para quem vai ajustar o texto

| | Antes (PoC 08 — é o que o texto descreve hoje) | Agora (PoC 10) |
|---|---|---|
| Parecer não favorável | Gera o **plano inteiro** de novo, **sem** usar as críticas ("regeneração cega") | Gera o **plano inteiro** de novo, e **cada especialista recebe a sua versão anterior e as críticas do Juiz** ("regeneração informada") |
| O que a nova geração recebe | O mesmo que a 1ª | O mesmo que a 1ª **+** um campo `revisao_pedagogica` nos dados da chamada |
| Número de chamadas, ciclos, limites, estados, critério de entrega | — | **Sem mudança** |
| Saída sem acentuação | Ia para o plano como veio | Detectada logo após cada especialista; **uma** reescrita pedida; nunca derruba a geração |
| Comportamento antigo | — | Continua disponível: `python app.py ... --regeneracao cega` |

**O que NÃO mudou (importante para não exagerar no texto):** continua sendo regeneração do **plano inteiro** — todos os 6 especialistas
rodam de novo, inclusive os que não receberam crítica. **Não** é a "correção dirigida só dos componentes criticados, com grafo de
invalidação" prevista na R2; isso continua como trabalho futuro. O Juiz, a rubrica, a política e a 1ª geração são exatamente os mesmos.

---

## 2. Regeneração informada (opção C)

### 2.1 Como funciona
1. 1ª geração: idêntica à de antes (nenhum especialista recebe críticas).
2. A IA Juiz avalia. Se o parecer é favorável, entrega (igual a antes).
3. Se não é favorável e ainda há ciclo (`--ciclos-juiz`, padrão 1), o serviço monta, para **cada um dos 6 especialistas**, um campo
   `revisao_pedagogica` com:
   - `versao_anterior`: a saída que esse especialista produziu na versão avaliada (a que entrou no plano — se houve reparo ou reescrita
     de acento aceita, é a corrigida; se a reescrita foi descartada, é a original);
   - `falhas_deste_componente`: as falhas que o Juiz atribuiu a esse componente (id, gravidade, critério, descrição, correção sugerida);
   - `outras_falhas`: as falhas dos outros componentes, só como contexto;
   - `instrucao`: corrigir as próprias falhas, priorizando maior/crítica; seguir as sugestões **só** se compatíveis com o contexto
     confirmado; **nunca acrescentar recursos fora de `contexto.recursos`**; manter contrato e coerência com as saídas anteriores;
   - `versao`: `revisao-informada-1.0`.
4. O plano inteiro é gerado de novo com esse campo, passando pelo mesmo validador, e o Juiz avalia a nova versão do zero.
5. Entrega: a favorável; sem favorável, a com menos falhas graves (empate: a mais recente), com aviso — igual a antes.

Detalhes:
- Com mais de um ciclo, a base é sempre a **última versão avaliada** (não necessariamente a melhor).
- Se a avaliação da 1ª versão falha (Juiz indisponível), não há regeneração — igual a antes.
- Todo parecer não favorável traz ao menos uma falha maior ou crítica (o contrato do parecer exige isso para nota 0 ou 1), então a
  regeneração informada sempre tem críticas para usar.
- O prompt de sistema e as instruções dos especialistas (`especialistas-plano-2.3`) **não mudaram**; o campo vai nos dados da chamada.
- O texto da instrução é **o mesmo** testado na sondagem (`revisao-informada-sondagem-0.1`); há teste que garante a igualdade.

### 2.2 O que fica registrado
- `pedidos.historico` ganha o evento `regenerando` antes de cada nova versão: `modo` (`informada` ou `cega`), `versao_revisao`
  (`revisao-informada-1.0`) e `criticas_usadas` (ids das falhas, ex.: `["F1", "F2"]`).
- Em `geracoes.resultado.rastreio`, cada chamada da regeneração guarda o `revisao_pedagogica` que recebeu.
- **Sem mudança de tabelas** no SQLite (os campos novos estão dentro dos JSON que já existiam).

### 2.3 O que o professor vê
- Progresso: a etapa "Ajustando: gerando nova versão…" passa a ser **"Ajustando: gerando nova versão com as críticas do Juiz…"**.
- Painel do Juiz: nova linha "A 2ª versão foi gerada a partir das críticas do Juiz à versão anterior (F1, F2), mantendo o contexto
  confirmado." Com `--regeneracao cega`, os textos antigos continuam.
- **Prints antigos** da etapa "Ajustando" e do painel de um pedido regenerado ficam diferentes da tela atual.

### 2.4 Por que (evidência)
Sondagem PoC 09 (pré-registrada, 5 primeiras versões reais não favoráveis, uma regeneração por braço):

| Braço | Falhas graves (soma) | Favoráveis | Graves repetidas da 1ª versão | Contrato ok |
|---|---|---|---|---|
| 1ª versão | 9 | 0/5 | — | 5/5 |
| Cego (PoC 08) | 8 | 1/5 | 4 | 5/5 |
| Informado (PoC 10) | 5 | 2/5 | 2 | 5/5 |

Sinal provisório a favor, **não** prova: n = 5, uma amostra por braço, e quem mede é o próprio Juiz (ver §4).

---

## 3. Acentuação

### 3.1 O problema
Planos gerados sem acentos ("avaliacao", "sera", "nao"). Na sondagem, 9 de 10 planos regenerados tinham campos longos sem nenhum acento;
no plano real do app de 25/11 16:01, 16 de 19 campos longos. Até 19/11, de 0 a 3 por plano. O Juiz não penaliza isso (as notas não mudam),
mas o plano chega ao professor com aparência de erro.

### 3.2 A causa (diagnóstico com os dados)
- **Gatilho:** em algumas chamadas o Gemini responde sem acentos, apesar de o prompt 2.3 pedir acentuação correta. A `modelVersion`
  informada pela API é a mesma em todas as datas; por que ficou mais frequente desde 23/11 **não se sabe** (comportamento do provedor).
- **Propagação (cascata):** os especialistas são encadeados — cada um recebe as saídas anteriores. Quando um responde sem acento, os
  seguintes recebem esse texto e imitam o estilo. Nos planos afetados, `objetivos` vinha acentuado e, a partir de
  `avaliacao_preliminar`, o texto bruto do Gemini já vinha sem acento.

### 3.3 O conserto (`aula-ia-backend/acentuacao.py` + `geracao.py`)
1. Depois que a saída de cada especialista é validada, um detector **determinístico** procura campos de texto com mais de 60
   caracteres, **sem nenhum** caractere acentuado (`áàâãéêíóôõúç`) e com ao menos uma palavra que em português leva acento
   ("avaliacao", "nao", "sera", "pratica", "sequencia"…). A palavra-guia evita acusar frases que naturalmente não têm acento.
2. Se achar, pede **uma** reescrita ao mesmo especialista pelo mecanismo de reparo já existente, com a instrução: reescrever o mesmo
   conteúdo com acentuação e cedilha corretas, sem mudar sentido, IDs, minutos, vínculos nem estrutura.
3. A reescrita só é aceita se passar no validador **e** reduzir o número de campos sem acento. Senão (ou se a chamada falhar: 503,
   timeout, contrato), fica a saída original. **Nunca derruba a geração.**
4. Como acontece antes do próximo especialista, interrompe a cascata.

- Só no modo IA (o gerador de demonstração é por regras e não roda isso).
- Custo: +1 chamada ao Gemini por especialista afetado (0 a 6 por versão). **Não conta no limite diário**, que conta versões geradas.
  Aumenta o tempo da geração quando dispara.
- Rastreio: um registro com `tentativa: "acentuacao"`, estado `validado` ou `descartado`, e os campos sem acento antes e depois.
- **Limites:** é heurística. Não pega texto curto, texto sem palavra-guia, nem texto com um único acento solto; pode reescrever um
  pseudocódigo sem acento (ex.: "se ... entao troca"). Verificado em **um** pedido real (§7.1): 3 reescritas, todas aceitas, plano final sem
  texto sem acento.

---

## 4. Há viés na reavaliação do Juiz? O que dá e o que não dá para afirmar

**Dá para afirmar (verificado no código e nos dados):**
1. **Sem memória e sem vazamento direto.** Cada avaliação é uma chamada independente. O Juiz recebe só `contexto`, `habilidade`,
   `revisao` (número da versão) e o plano (`juiz.py`, `avaliar_plano`). **Não** recebe as críticas anteriores, a versão anterior, o
   parecer anterior nem o aviso de que é uma regeneração. O `revisao_pedagogica` vai só para os especialistas do Gemini.
2. **Mesma configuração** em todas as avaliações: `juiz-v1.3`, rubrica 0.1, política preliminar, temperatura 0, seed 42.
3. **Outra família de modelo:** quem gera é o Gemini, quem avalia é o `openai/gpt-oss-120b` (Groq).
4. **Os planos não citam o Juiz:** nos 10 planos regenerados da sondagem (`experimentos/geracao/poc09_sondagem_c/`) não aparece
   "juiz", "parecer", "correção sugerida", "versão anterior" nem id de falha (F1, F2…). A única ocorrência de "crítica" (caso 2,
   informado) é "análise crítica de código", atividade pedagógica — o plano não "conversa" com o avaliador.

**Não dá para afirmar que não há viés:**
1. **"Ensinar para a prova".** Na regeneração informada os especialistas otimizam para os critérios e até para as palavras do próprio
   Juiz. A nota pode subir porque o plano ficou mais parecido com o que **esse** Juiz pede, o que não é necessariamente um plano melhor
   para o professor. Exemplo real: no plano #3 da sondagem, acatar a crítica deixou a ET2 longa demais e o Juiz apontou um novo problema.
2. **Medida circular.** Quem critica e quem mede é o mesmo Juiz: "5 graves contra 8" significa "menos falhas segundo o Juiz".
3. **Variância.** Temperatura 0 não garante repetição; n = 5, uma amostra por braço; o braço cego teve um favorável "por sorteio".
4. **Pequena diferença no pedido ao Juiz:** a nova versão vai com `revisao` maior. Efeito esperado desprezível, mas não medido.

**Como medir (trabalho futuro):** leitura humana **cega** (professor compara 1ª versão e regenerada sem saber qual é qual — a ferramenta
`adjudicacao.py` já existe) ou um segundo avaliador independente (outro modelo ou outra rubrica).

**Frase sugerida para o texto:** "A reavaliação é feita por uma chamada independente, sem acesso às críticas anteriores nem à versão
anterior do plano, o que elimina vazamento direto de informação. Isso não elimina a circularidade: o mesmo Juiz que critica também
mede, e a melhora observada é melhora segundo esse Juiz, o que exige verificação humana para ser confirmada."

---

## 5. Arquivos alterados

| Arquivo | O que mudou |
|---|---|
| `aula-ia-backend/revisao_informada.py` (**novo**) | Monta o `revisao_pedagogica` de cada especialista a partir do rastreio e do parecer da versão avaliada (`VERSAO`, `INSTRUCAO`, `saidas_do_rastreio`, `montar_revisoes`) |
| `aula-ia-backend/acentuacao.py` (**novo**) | Detector de campos sem acentuação e instrução de reescrita |
| `aula-ia-backend/geracao.py` | `gerar(..., revisoes=None)` repassa o campo a cada especialista; `_reescrever_sem_acento` após cada etapa validada (`corrigir_acentuacao`, só modo IA) |
| `aula-ia-backend/geracao_v2.py` | Repassa `revisoes` e `corrigir_acentuacao`; agentes aceitam `revisao_pedagogica` |
| `aula-ia-backend/gemini.py` | Inclui `revisao_pedagogica` nos dados da chamada quando houver |
| `aula-ia-backend/servico.py` | `regeneracao="informada"` (ou `"cega"`); guarda (resultado, parecer) da versão avaliada; monta as revisões na regeneração; evento `regenerando` no histórico |
| `aula-ia-backend/app.py` | Opção `--regeneracao informada|cega` (padrão `informada`) e mensagem ao iniciar |
| `aula-ia/public/geracao-ui.js` (+ `dist/`) | Texto do progresso e linha no painel do Juiz |
| `aula-ia-backend/tests/test_poc10.py` (**novo**) | 14 testes (acentuação, regeneração informada, serviço, app) |
| `tests/test_juiz_integrado.py`, `tests/test_intervalo_juiz.py`, `aula-ia/tests/test-juiz-render.mjs` | Ajustados ao evento `regenerando` e aos textos novos |

## 6. Versões

| Item | Valor |
|---|---|
| Revisão informada | `revisao-informada-1.0` (texto idêntico ao da sondagem `revisao-informada-sondagem-0.1`) |
| Regeneração padrão do app | `informada` (`--regeneracao cega` = PoC 08) |
| Verificação de acentuação | ligada no modo IA; limiar 60 caracteres; 1 reescrita |
| Inalterados | `especialistas-plano-2.3`, `gemini-3.5-flash-lite`, `plano-aula-2.0`, `juiz-v1.3`, `rubrica-juiz-0.1`, `politica-juiz-prelim-0.1`, `parecer-juiz-1.0`, parâmetros do Juiz, limites diários |

## 7. Testes, mutação e verificação

- Python: **513 testes** (512 passam, 1 ignorado), também com `python -S` (eram 499 depois da PoC 09; +14 de `test_poc10.py`).
- Interface: 3 scripts OK (`test-plano-render`, `test-formulario`, `test-juiz-render`).
- Mutação manual sem bytecode (`python -B`, `PYTHONDONTWRITEBYTECODE=1`): **22 mutantes**, 21 mortos na 1ª rodada. O sobrevivente
  ("`saidas_do_rastreio` pega saída rejeitada/descartada") revelou um caso real sem teste: reescrita de acento descartada fica por último
  no rastreio, e a regeneração tem de usar a versão que entrou no plano. Dois testes acrescentados → morto. **0 sobreviventes.**
### 7.1 Verificação com chamadas reais (25/11/2026, 17:18, autorizada pelo João)
Um pedido no app reiniciado com o commit `7a04bd7` (limites padrão), pela API local, com o caso 5 da sondagem (Ordenação · 8º ano ·
50 min · desplugada · "quadro e pincel" · EF08CO03). Bruto: `experimentos/geracao/poc10_verificacao_real/pedido_54aca4c2.json`
(busca de chaves sem achados). Tempo total do pedido: 188 s.

| | Versão 1 (geração normal) | Versão 2 (regeneração informada) |
|---|---|---|
| Chamadas ao Gemini | 9 (6 + 3 reescritas de acento) | 6 (todas com `revisao_pedagogica`) |
| Reescritas de acento | 3, todas aceitas: `objetivos` (3 campos → 0), `metodologia` (1 → 0), `adaptacao` (2 → 0) | nenhuma necessária |
| Campos de texto sem acento no plano final | 0 (os únicos campos longos sem acento são os hashes `sha256_catalogo`) | 0 |
| Parecer | Com ressalvas · 1 grave: F1 [maior] `avaliacao_preliminar` — instrumentos sem rubrica/critérios de desempenho | Com ressalvas · 1 grave: F1 [maior] `objetivos` — "só trabalha Bubble sort" (+ 2 menores) |
| Entregue | não | sim (empate em graves → a mais recente), com aviso |

Exemplo de reescrita (objetivo geral): "Compreender e simular algoritmos classicos de ordenacao de listas utilizando computacao
desplugada." → "Compreender e simular algoritmos clássicos de ordenação de listas utilizando computação desplugada."

**Leitura (provisória, n = 1):**
- Acentuação: o gatilho apareceu já no 1º especialista (`objetivos`) e em mais dois; depois da reescrita de `objetivos`, os especialistas
  seguintes vieram acentuados — compatível com a cascata interrompida. O plano entregue não tem texto sem acento.
- Regeneração informada: o histórico registrou `regenerando` com `modo: informada`, `revisao-informada-1.0` e `criticas_usadas: ["F1"]`;
  a falha F1 foi entregue só ao especialista `avaliacao_preliminar` (os outros 5 a receberam como contexto). A crítica da 1ª versão
  **foi resolvida** (a 2ª versão tem rubrica; a nova falha menor F3 já comenta "a rubrica avalia…"), mas o Juiz levantou uma falha maior
  **nova**: "só Bubble sort" — a mesma crítica recorrente já listada como possível falso positivo curricular a adjudicar (`CLAUDE.md`).
  Resultado: 1 grave → 1 grave, sem parecer favorável. Ilustra o limite do §4: o Juiz reavalia do zero e a variância dele pesa tanto
  quanto a correção.

---

## 8. Adaptações na escrita (lista detalhada)

> **Aplicada (25/11, noite).** Esta lista foi aplicada na especificação v2.3 (`docs/especificacao/AulaIA_Especificacao_v2.3.md`), na
> correspondência v2.3, nos diagramas e nos documentos de estado (auditoria de 25/11, branch `docs/auditoria-25-11`). Fica como
> registro do que mudou; não é mais lista de pendências. Os números desta PoC (513 testes) são os da época; o total atual está em
> `docs/Estado_Final_Sistema.md`.

Linhas conferidas em 25/11 na `main`/branch atual. "Sugestão" é texto pronto para colar; ajuste o estilo à vontade.

### 8.1 `docs/especificacao/AulaIA_Especificacao_v2.2_final.md`
| Onde | Hoje | Sugestão |
|---|---|---|
| §1, objetivo 5 (l. 26) | "Implementar a IA Juiz com parecer estruturado e **regeneração automática** com limite de tentativas." | "Implementar a IA Juiz com parecer estruturado e **regeneração automática informada pelas críticas do parecer**, com limite de tentativas." |
| §2 (l. 36–39) | "PoC 01 a PoC 08"; "493 Python, 1 ignorado"; pré-registro "(V01–V06) e da geração (PoC07B)" | "PoC 01 a PoC 10"; "513 Python, 1 ignorado"; acrescentar "e da sondagem de regeneração (PoC 09)" |
| §5, tabela | Orquestrador: "5 especialistas em 6 chamadas encadeadas, validação a cada etapa, integrador" | Acrescentar "; verificação de acentuação com uma reescrita". Nova linha: "Revisão informada \| Monta, para cada especialista, a versão anterior e as críticas do Juiz \| `revisao_informada.py`". Opcional: "Verificação de acentuação \| `acentuacao.py`" |
| §5, versões (l. 85) | — | Acrescentar `revisao-informada-1.0` |
| §6, passo 4 (l. 94) | "Não favorável → o plano inteiro é gerado de novo (até `--ciclos-juiz`, padrão 1) e avaliado de novo." | "Não favorável → o plano inteiro é gerado de novo (até `--ciclos-juiz`, padrão 1); cada especialista recebe a sua versão anterior e as críticas do Juiz (descrição, gravidade, critério e correção sugerida), sem poder acrescentar recursos não informados. A nova versão é avaliada do zero." |
| §6, passo 2 (opcional) | "Os especialistas geram o plano; o integrador compõe e o validador confere." | Acrescentar: "Saída de especialista sem acentuação recebe uma reescrita antes da etapa seguinte." |
| §6, tabela de estados | — | **Sem mudança** (nenhum estado novo) |
| §8, RF09 (opcional) | "Orquestrar os especialistas com contratos e dependências, validando cada etapa" | Acrescentar "e pedindo uma reescrita quando a saída vem sem acentuação"; teste: `test_poc10.py` |
| §8, RF12 (l. 138) | "Regenerar automaticamente o plano inteiro quando o parecer não for favorável, com limite configurável (padrão 1), entregando a versão com menos falhas graves e um aviso" | "Regenerar automaticamente o plano inteiro quando o parecer não for favorável, **fornecendo a cada especialista a sua versão anterior e as críticas do Juiz**, com limite configurável (padrão 1), entregando a versão com menos falhas graves e um aviso"; testes: `test_juiz_integrado.py`, `test_poc10.py` |
| §8, RF14 | — | Sem mudança de texto (o progresso agora diz "com as críticas do Juiz"; teste já cobre) |
| §9, RNF03 | — | Acrescentar: "histórico do pedido registra o modo da regeneração e as críticas usadas; rastreio registra as reescritas de acentuação" |
| §9, RNF04 | — | Acrescentar: "reescrita de acentuação nunca derruba a geração (falha → mantém a saída original)" |
| §9, RNF08 | — | Acrescentar: "reescrita de acentuação: até 1 chamada extra por especialista, fora do limite diário (que conta versões)" |
| §10, RN11 (l. 179) | "Parecer não favorável dispara até N regenerações completas (padrão 1)" | "Parecer não favorável dispara até N regenerações completas (padrão 1), informadas pelas críticas do parecer; a 1ª geração não recebe críticas" |
| §11, Dados | — | Sem mudança de tabelas; opcional: "o histórico do pedido inclui o evento de regeneração com as críticas usadas" |
| §12, Limitações (l. 195) | "regeneração não usa as críticas do Juiz" | Trocar por: "a regeneração refaz o plano inteiro, mesmo os componentes sem crítica; o ganho da regeneração informada foi observado só em sondagem exploratória (n = 5) e medido pelo próprio Juiz (circularidade); a verificação de acentuação é heurística" |
| §12, Trabalhos futuros | "correção dirigida só dos componentes criticados, com grafo de invalidação (...)" | Manter, com a nuance: "a regeneração já usa as críticas, mas refaz todos os componentes". Acrescentar: "verificação humana cega do ganho da regeneração informada" |
| §13, Histórico | — | Nova linha: "v2.3 \| 25/11/2026 \| Regeneração informada pelas críticas do Juiz (PoC 10) e verificação de acentuação" |

### 8.2 `docs/especificacao/Correspondencia_IDs_v2.1R2_v2.2.md`
| Linha | Hoje | Sugestão |
|---|---|---|
| 25 (RF12) | "**Reescrito:** regeneração do plano inteiro (padrão 1); correção dirigida → futuro" | "**Reescrito:** regeneração do plano inteiro informada pelas críticas do Juiz (padrão 1); correção dirigida → futuro" |
| 54 (RN11) | "**Reescrita:** até N regenerações completas (padrão 1)" | "**Reescrita:** até N regenerações completas, informadas pelas críticas (padrão 1)" |
| 60 (RN14 grafo) | Trabalho futuro | Sem mudança |

### 8.3 Diagramas (`docs/diagramas/final/` e cópias em `docs/diagramas/diagramas-finais.md`)
Depois de editar a fonte, regenerar a imagem (`mmdc -i final/<nome>.mmd -o final/<nome>.png -s 2 -b white`) e citar o commit.

| Diagrama | Onde | Sugestão |
|---|---|---|
| `atividades.mmd` (l. 17; cópia l. 135) | `RG["Gerar o plano inteiro de novo"]` | `RG["Gerar o plano inteiro de novo<br/>com as críticas do Juiz"]` |
| `atividades.mmd` (opcional) | `G["Especialistas geram o plano<br/>(6 chamadas, validação a cada etapa)"]` | acrescentar "e verificação de acentuação" |
| `sequencia.mmd` (l. 32; cópia l. 101) | `SV->>ORQ: Gerar o plano inteiro de novo` | `SV->>ORQ: Gerar de novo com a versão anterior e as críticas do Juiz` |
| `componentes.mmd` (opcional) | — | caixa "Revisão informada `revisao_informada.py`" ligando Serviço → Orquestrador |
| `visao-geral.html` (l. 77) + PNG | "Se o parecer não for favorável, o plano é escrito de novo uma vez" | "Se o parecer não for favorável, o plano é escrito de novo uma vez, usando as críticas do Juiz" |
| `estados.mmd`, `er.mmd`, `casos-de-uso.puml`, `estrutura-plano` | — | **Sem mudança** |

### 8.4 Outros documentos do repositório
- `docs/Estado_Final_Sistema.md`: **já atualizado** neste commit (opções, arquitetura, fluxo, versões, números, limites).
- `docs/PoC08_Juiz_Integrado.md`: recebeu uma nota no topo dizendo que descreve a regeneração cega (PoC 08) e que a PoC 10 a substituiu
  como padrão; o corpo ficou como registro histórico.
- `CLAUDE.md` e `docs/diario_de_bordo.md`: atualizados.

### 8.5 Texto do TCC (capítulos)
- **Metodologia / incrementos:** acrescentar a PoC 09 (sondagem pré-registrada cego × informado) e a PoC 10 (implementação). Mostra o
  ciclo "medir antes de implementar".
- **Desenvolvimento / fluxo da IA Juiz:** onde diz que a regeneração refaz o plano "sem usar as críticas", trocar pela descrição do §2.1.
  Deixar explícito que continua sendo o plano inteiro.
- **Resultados:** tabela da sondagem (§2.4) com as ressalvas (n = 5, circularidade). Achado da acentuação (§3) como problema real
  encontrado no uso e corrigido.
- **Discussão / limitações:** a frase do §4 sobre circularidade e "ensinar para a prova".
- **Trabalhos futuros:** correção dirigida com grafo de invalidação; verificação humana cega do ganho; alerta habilidade × tipo de aula
  (os casos que não melhoraram na sondagem eram conflitos da própria entrada).
- **Figuras/prints:** prints da etapa "Ajustando" e do painel de um pedido regenerado devem ser refeitos se forem usados.
