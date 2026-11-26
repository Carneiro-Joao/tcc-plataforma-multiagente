# Caso-base do texto — execução manual de 26/11/2026

**Escolhido pelo João:** pedido `3bf9f2c6` (arquivo `pedido_3bf9f2c6_CASO_BASE.json`), consulta `a61ac7d1`. Contexto:
Ordenação · 8º ano · 50 min · **Aula teórica** · quadro e pincel · habilidade EF08CO03. Executado das 01:49:56 às 01:51:52 (BRT).
Todos os números abaixo foram tirados do banco local (`aula-ia-backend/local/consultas.sqlite3`), só com SELECT. Os 9 pedidos do dia
estão exportados nesta pasta (`pedido_<id8>.json`: consulta, pedido, histórico, todas as versões com plano, rastreio e pareceres).

## 1. Versão × revisão × geração (por que o PDF diz "Revisão 6" e a tela diz "2ª versão")
- **Geração** = uma linha na tabela `geracoes`: cada vez que os especialistas rodam, inclusive as que falham. É o que conta no limite diário.
- **Versão** (na tela: "1ª versão", "2ª versão") = posição **dentro do pedido**: a 1ª é a geração normal; a 2ª é a regeneração
  informada (campo `ciclo` 0 e 1).
- **Revisão** (no plano e no PDF: "Revisão N") = número sequencial da geração **dentro da consulta**, somando todos os pedidos
  daquela consulta (campo `geracoes.revisao`).
- **Pedido** = um clique em "Gerar plano de aula" ou em "Gerar novamente" (tabela `pedidos`).

Consulta `a61ac7d1` (a do caso-base): **3 pedidos, 6 gerações**, revisões 1 a 6:

| Pedido | Horário | Revisão (versão) | O que aconteceu |
|---|---|---|---|
| `0f0df4b1` | 01:42–01:45 | 1 (1ª) | Com ressalvas, 3 graves |
| | | 2 (2ª) | **falha técnica:** timeout de leitura do Gemini na regeneração → entregue a revisão 1, com aviso |
| `77f62f03` | 01:45–01:47 | 3 (1ª) | Com ressalvas, 3 graves |
| | | 4 (2ª) | gerada, mas **a avaliação da IA Juiz falhou** (Groq HTTP 413) → entregue sem parecer ("avaliação indisponível") |
| **`3bf9f2c6`** | **01:49–01:51** | **5 (1ª)** | Com ressalvas, 1 grave (F1), notas 17/18 |
| | | **6 (2ª)** | **Favorável**, 0 falhas, notas 18/18 — **aprovada pelo professor** |

Antes disso, para o mesmo contexto (Ordenação · teórica · 50 · quadro e pincel), a consulta `daa7cda3` teve 2 pedidos (01:37 e 01:38),
os dois encerrados por **Gemini HTTP 503** ("modelo sobrecarregado por alta demanda"), sem plano.
Ou seja: **5 pedidos para o mesmo contexto; o 5º foi o escolhido** (o único com as duas versões avaliadas).

## 2. Todas as execuções do dia (n honesto)
**9 pedidos, 14 gerações, 9 avaliações do Juiz (8 com parecer + 1 falha técnica).**

| Horário | Pedido | Contexto | Resultado |
|---|---|---|---|
| 00:52 | `04585130` | Ordenação · prática · 50 · material impresso | **interrompido**: a janela do app foi fechada no meio da 1ª geração (fica `gerando` no banco; a interface mostra "interrompido") |
| 00:56–00:58 | `56a7d342` | Ordenação · prática · 50 · material impresso | Com ressalvas (2 graves) → regeneração informada → Com ressalvas (2 graves); entregue a revisão 2, **aprovada** |
| 01:04–01:08 | `b18f2914` | Listas · teórica · 70 · projetor, computadores, internet | Com ressalvas (3 graves) → **regeneração falhou: Gemini HTTP 503** → entregue a 1ª versão, com aviso |
| 01:10–01:11 | `54ebeeb3` | Ordenação · teórica · 70 · quadro e pincel | **Favorável** na 1ª versão; **aprovada** |
| 01:37 | `37d79f86` | Ordenação · teórica · 50 · quadro e pincel | **falha: Gemini HTTP 503** (5º especialista), sem plano |
| 01:38 | `528f5197` | idem | **falha: Gemini HTTP 503** (1º especialista), sem plano |
| 01:42–01:45 | `0f0df4b1` | idem | ressalvas → **regeneração falhou: timeout do Gemini** → entregue a 1ª versão |
| 01:45–01:47 | `77f62f03` | idem | ressalvas → nova versão gerada → **avaliação falhou: Groq HTTP 413** → entregue sem parecer |
| 01:49–01:51 | **`3bf9f2c6`** | idem | **caso-base:** ressalvas (1 grave) → regeneração informada → **Favorável**; aprovada |

**Falhas técnicas do dia: 6** (nenhuma contou como parecer nem como plano, conforme RN13):
- 3 × Gemini HTTP 503 em que as 3 tentativas falharam (01:06, 01:37, 01:38);
- 1 × timeout de leitura do Gemini (01:42–01:45);
- 1 × Groq HTTP 413 na avaliação (01:47);
- 1 × interrupção por fechamento do app (00:52; não é falha de provedor).

Comportamento observado (RNF04): na regeneração, a falha técnica não derrubou o pedido. Foi entregue a melhor versão anterior, com o
aviso "A nova versão falhou tecnicamente; entregue a melhor versão anterior." Quando a falha foi do Juiz, a entrega veio com "Avaliação
indisponível (falha técnica da IA Juiz); o plano foi entregue sem parecer." **Repetições automáticas de HTTP 503 que deram certo:**
14 dos 84 registros de especialista do dia precisaram de 2 ou 3 requisições (no caso-base, 5 delas).

## 3. Pareceres do caso-base
**Revisão 5 (1ª versão) — Com ressalvas** (`em_correcao`). Política: "falhas que exigem correção: F1".
Notas (0–3): aderência curricular 3 · alinhamento dos objetivos 3 · coerência metodológica 3 · viabilidade 3 ·
**avaliação da aprendizagem 2** · inclusão 3 → **17 de 18 pontos**.
- **F1 · gravidade MAIOR** · componente `avaliacao_preliminar` (Evidências de avaliação) · critério avaliação da aprendizagem:
  "Os critérios de avaliação (participação oral e demonstração prática) são genéricos e não permitem diferenciar desempenho adequado
  de inadequado para os objetivos OBJ1 e OBJ2."
  Sugestão: "Elaborar rubricas com níveis de desempenho (ex.: participação mínima, explicação correta das trocas, uso adequado da
  terminologia) e incluir observação da execução correta das comparações e trocas durante a simulação."

**Revisão 6 (2ª versão, regeneração informada com a crítica F1) — Favorável** (`aguardando_decisao`). Notas 3 em todos os critérios
→ **18 de 18**; nenhuma falha. Política: "nenhuma falha exige correção pela política vigente". Os 6 especialistas receberam
`revisao_pedagogica`; a F1 foi entregue como "falha deste componente" só ao `avaliacao_preliminar`.
Na revisão 6, os instrumentos passaram a descrever desempenho "adequado" × "inadequado" (ver `7_plano_aprovado.png`).

Reescritas de acentuação no caso-base: 2 na revisão 5 (`avaliacao_preliminar`, `adaptacao`) e 1 na revisão 6 (`sequencia`), todas
aceitas, com a regra `deteccao-acentuacao-1.2` registrada no rastreio.

## 4. Versão do sistema nesta execução
- **Branch `fix/acento-misto-e-textos-interface`, commit `c1ef4f8`** (sobre `feat/poc11-acento-curto-e-recomendacao` `f95ee8a`, que
  sobre `fix/auditoria-25-11-c1-c4-c5-c9` `0f5b8df`, que sobre `main` `4558b4a`). Prova no próprio rastreio: as reescritas registram
  `deteccao-acentuacao-1.2`, que só existe nesse commit.
- Configuração: Gemini `gemini-3.5-flash-lite`, prompt `especialistas-plano-2.3`; Juiz `openai/gpt-oss-120b` (Groq), `juiz-v1.3`,
  `rubrica-juiz-0.1`, `politica-juiz-prelim-0.1`; `--ciclos-juiz 1 --regeneracao informada`. A partir das 01:42, limites desta execução
  14 gerações/10 avaliações (pedido do João; padrão 8/8 no código não mudou).
- Testes desse commit: **545 testes Python** (544 passam, 1 ignorado), também com `python -S`; **3/3 testes de interface**;
  mutação manual **15 mutantes no backend + 6 no front, 0 sobreviventes**.
- Execuções das 00:52 às 01:11: app aberto a partir de `feat/poc11-acento-curto-e-recomendacao` (`f95ee8a`, regra de acento 1.1, texto
  "não aprovada pelo Juiz" e selo de demonstração ainda presentes).

## 5. Telas
- `6_plano_antes_de_aprovar_RECONSTITUIDO.png` (+ `_botoes.png`): plano entregue com "Aprovar plano" e "Gerar novamente" e o status
  "Aguardando aprovação". **Reconstituída:** o pedido já estava aprovado, então a tela foi refeita a partir de uma **cópia** do banco em que
  só essa versão voltou a "rascunho", num app separado (porta 8001, sem chamar API). O conteúdo (plano, parecer, histórico) é o real.
- `7_plano_aprovado.png` (+ `_botoes.png`): a mesma consulta no app real, depois da aprovação: "Aprovado pelo professor" e "Baixar PDF".
