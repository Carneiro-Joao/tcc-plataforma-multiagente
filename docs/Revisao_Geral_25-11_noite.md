# Revisão geral da documentação × sistema (25/11/2026, noite)

**Referência conferida:** branch `fix/auditoria-25-11-c1-c4-c5-c9` (`fb7228e`), que contém a `origin/main` (`4558b4a`, PoC 10) +
`docs/figuras-cap4-exemplo-unico` + `docs/auditoria-25-11` + correções C1/C4/C5/C9. Só leitura: nada foi alterado nesta revisão
além deste arquivo. Sem chamadas de API.

**Como foi feita:** suíte completa (com e sem `python -S`), 3 scripts de interface, busca de termos desatualizados nos documentos
vigentes, constantes do código × números da especificação, arquivos de teste citados na especificação, `public` × `dist`, varredura
de chaves, fontes × figuras, e leitura da cópia do Cap. 4 que está no Projeto do claude.ai (`claude/cap4-texto.md`, 24/11).

## 1. Placar

| Área | ✅ ok | ⚠️ ajustar | ❌ errado | ➕ falta | ➖ retirar |
|---|---|---|---|---|---|
| Código e testes | 6 | 0 | 0 | 0 | 0 |
| Especificação v2.3 e correspondência | 4 | 2 | 0 | 0 | 0 |
| Outros documentos do repositório | 5 | 3 | 0 | 0 | 0 |
| Diagramas e figuras | 6 | 3 | 0 | 0 | 1 |
| Fora do repositório (Projeto e texto do TCC) | 0 | 2 | 1 | 0 | 0 |

## 2. O que está bom (✅)

**Código e testes**
- 532 testes Python (531 passam, 1 ignorado), também com `python -S -B`. 3 scripts de interface ok.
- Teste de mutação das correções C1, C4, C5 e C9: 11 mutantes, 0 vivos (sem bytecode).
- `aula-ia/public/geracao-ui.*` idêntico a `aula-ia/dist/`.
- Nenhuma credencial real em arquivo versionado.
- Constantes iguais às da especificação: timeout 90 s; 503 com 2 repetições (agora também na classe); Juiz com 75 s entre avaliações,
  120 s depois de 413, 60 s antes do reparo; temperatura 0 e seed 42; 8 gerações e 8 avaliações por dia; 15 min para `interrompido`;
  batimento de 60 s.
- Interface coerente: só mostra "com as críticas do Juiz" quando a regeneração foi de fato informada. No Juiz de demonstração (C5)
  aparece o texto genérico de nova versão.

**Especificação v2.3**
- Todos os arquivos de teste citados nos RFs existem.
- RF09, RF12, RF18, RNF03, RNF04, RNF08, RN11, RN16, RN17 batem com o código.
- §6 (fluxo) e §12 (limitações) já descrevem C1 e C4.
- Correspondência v2.1-R2 → v2.3 completa (RN16 e RN17 incluídas).

**Outros documentos:** `Estado_Final_Sistema.md`, `Contrato_PlanoDeAula_2_0.md`, `CLAUDE.md`, diário de bordo e a seção atual
do `README.md` (quadro de estado, opções do Juiz, ferramentas) estão em dia com o código.

**Figuras:** componentes, atividades (com a reescrita de acentuação), sequência, ER, visão geral (HTML e ilustrada) e as duas variantes
SVG de casos de uso estão coerentes com o sistema. As cópias Mermaid dentro de `diagramas-finais.md` são iguais às fontes.

## 3. O que precisa de ajuste (⚠️), está errado (❌) ou pode sair (➖)

| # | Onde | Situação | O que fazer | Esforço |
|---|---|---|---|---|
| A1 | `AulaIA_Especificacao_v2.3.md` cabeçalho e `diagramas-finais.md` cabeçalho | ⚠️ Dizem "conferida contra a `main` `4558b4a`", mas o código vigente agora inclui C1/C4/C5/C9, que ainda não estão na `main` | Trocar por "conferida contra `fix/auditoria-25-11-c1-c4-c5-c9` (base `main` `4558b4a`)"; depois do merge, pelo hash novo da `main` | 2 min |
| A2 | Especificação §7 (l. 118–119) | ⚠️ "Atores secundários: serviço Gemini (geração) e serviço Groq (IA Juiz)": o rótulo "(IA Juiz)" sugere que o Juiz é externo | Depende da escolha do diagrama: (a) três atores → "serviços de LLM de geração (API Gemini) e de avaliação (API Groq); os agentes e a IA Juiz são internos"; (b) um ator → "Ator: Professor; as APIs de LLM são dependências externas (§5)" | 5 min |
| A3 | `casos-de-uso.puml`, `casos-de-uso.mmd`, `casos-de-uso.png` | ⚠️ Mesmo rótulo antigo "Serviço Groq (IA Juiz)"; hoje existem 4 versões do mesmo diagrama (PlantUML, Mermaid, SVG 3 atores, SVG 1 ator) | Depois da escolha: alinhar rótulos do `.puml`/`.mmd` com a variante escolhida e deixar no `diagramas-finais.md` **uma** figura oficial + fontes | 15 min |
| A4 | `estados.mmd` / `estados.png` | ⚠️ "interrompido: parado mais de 15 min" continua certo, mas desde C4 o sentido é "sem sinal de vida" (app parado) | Rótulo → "sem sinal por mais de 15 min (app parado)"; regenerar PNG/SVG | 5 min |
| A5 | `estrutura-plano` (HTML, Mermaid e ilustrada) | ⚠️ Exemplo de 23/11 (antes da PoC 10), sem o plano bruto no repositório | Já combinado: esperar a nova execução do João; trocar os trechos e regenerar as três | 20 min, depois da execução |
| A6 | `docs/Auditoria_Documentacao_e_Codigo_25-11.md` | ⚠️ Ainda diz que C1, C4, C5 e C9 são "só documentar" | Acrescentar um adendo com o que foi corrigido e os commits (sem reescrever o relatório) | 5 min |
| A7 | `docs/PoC10_Regeneracao_Informada_e_Acentuacao.md` §8 | ⚠️ Lista de ajustes para a v2.2; quem ler pode achar que está pendente | Nota no topo do §8: "aplicada na v2.3 em 25/11; ver auditoria"; os números (513 testes) ficam como registro da PoC | 2 min |
| A8 | `README.md` §1–§3 e partes de §5/§7 | ⚠️ Texto de 16–17/11 (OpenRouter, PoC 05B, "168 testes") mantido como histórico; o quadro do topo avisa, mas o arquivo é longo e confunde | Mover o histórico para `docs/historico/README_2026-11-17.md` e deixar o README só com: o que é, como rodar, fluxo, opções, testes, links | 30 min |
| A9 | Figuras de conferência `*-mermaid.png` (3 arquivos) | ➖ Foram úteis para testar as versões Mermaid; com as SVG ilustradas, não entram no texto | Retirar do repositório (as fontes `.mmd` ficam) | 2 min |
| A10 | Projeto do claude.ai: `claude/especificacao-v2.2-final.md` | ⚠️ O chat que escreve o TCC lê a v2.2 | Subir a v2.3 no Projeto (é documentação, não texto do TCC) e marcar a v2.2 como histórico; com o seu ok | 2 min |
| A11 | Texto do TCC, Cap. 4 (cópia `claude/cap4-texto.md` de 24/11) | ❌ Diverge do sistema atual (lista abaixo). Não mexo no texto: é para levar ao chat de escrita | Entregar a lista da §4 ao chat de escrita | — |
| A12 | Projeto: `claude/continuidade-tcc.md` e `claude/revisao-final-documentacao.md` | ⚠️ Escritos antes da PoC 10 | Atualizar ou marcar como histórico quando você for retomar a escrita | 10 min |

## 4. Divergências do Cap. 4 (para o chat de escrita)

Conferido na cópia do Projeto de 24/11. Se a versão mais nova do texto já corrigiu algum item, ignore.

> **Correção (25/11, 21h40).** O documento de continuidade do Projeto (`claude/continuidade-tcc.md`, 25/11 18h55) diz que a versão
> principal do Cap. 4 está no Google Docs e que `claude/cap4-texto.md` está desatualizado. Pelo registro de lá, já foram aplicados no
> Docs: RF12, RN11, a 4.3.3 com a regeneração informada (item 6), o Orquestrador com a acentuação (parte do item 8) e a 4.2.4 ("sem as
> críticas do pedido anterior"). Continuam pendentes, segundo o próprio registro: exemplo e prints novos (item 9), contagem de testes
> (item 2) e ratificação. A lista abaixo serve só para conferência; o chat de escrita decide.

1. **Introdução e 4.3:** "sistema congelado em 19 de novembro" → o desenvolvimento foi reaberto em 25/11 (PoC 10). Novo congelamento
   depois dos testes finais.
2. **4.1:** "versão 2.2, de 23 de novembro" → v2.3, de 25/11. "493 testes" → 532.
3. **Quadro 1:** RF09 ganhou "pedindo uma reescrita da saída escrita sem acentuação". RF12 ganhou "informando a cada especialista a
   sua versão anterior e as críticas do Juiz". RF18 ganhou "novo pedido, do zero, sem as críticas do pedido anterior".
4. **Quadro 2:** RNF03, RNF04 e RNF08 têm complementos (ver especificação v2.3 §9).
5. **Quadro 3:** RN11 informada; faltam **RN16** (as críticas não alteram o contexto confirmado) e **RN17** (cada avaliação do Juiz é
   independente).
6. **4.1, comentário do RF12** e **4.3.3, penúltimo parágrafo:** "a regeneração automática refaz o plano inteiro e **não utiliza as
   críticas** do parecer" está **errado** desde a PoC 10. Agora refaz o plano inteiro **usando** as críticas. Continua futuro: refazer
   só os componentes criticados.
7. **4.3.1:** depende da escolha do diagrama de casos de uso (três atores ou um).
8. **4.3.2:** faltam os componentes **Revisão informada** e **Verificação de acentuação**. O Orquestrador agora também pede uma
   reescrita de saída sem acento, aceita só se mantiver IDs, números e vínculos.
9. **4.3.4:** o texto descreve um exemplo com "único recurso quadro e pincel", "Bubble Sort", "ET1 de 15 minutos", mas a figura atual
   usa a execução de 23/11 (projetor e computadores, ET1 de 20 min). Alinhar texto e figura; isso se resolve junto com a nova execução.
10. **Apêndice A, estados:** "parado por mais de 15 minutos" → "sem sinal de vida por mais de 15 minutos (o sistema renova o pedido
    a cada minuto enquanto ele roda)".

## 5. Plano de ação

> **Atualização (25/11, 21h50).** A2 e A3 resolvidos: o João escolheu só o professor como ator; justificativa na especificação §7 e em
> `diagramas-finais.md` §2; APIs de LLM no diagrama de componentes como serviços externos. A4, A6, A7, A8, A9, A10 e A12 feitos a pedido
> do João. Em espera: A1 (cabeçalhos), A5 (execução nova), merge e congelamento.

Ordem sugerida. Itens marcados **(João)** dependem de decisão ou ação sua; os outros eu faço com o seu ok.

| Etapa | Ação | Itens | Depende de |
|---|---|---|---|
| 1 | **Escolher a variante do diagrama de casos de uso** (três atores ou um) | A2, A3 | **(João)** |
| 2 | Ajustes pequenos de documentação: cabeçalhos, adendo da auditoria, nota no §8 da PoC 10, rótulo de `estados`, retirar `*-mermaid.png`, aplicar a escolha da etapa 1 | A1, A2, A3, A4, A6, A7, A9 | etapa 1 |
| 3 | Limpar o README (histórico para `docs/historico/`) | A8 | seu ok |
| 4 | **Nova execução real** (1 pedido pelo app, com as duas chaves): confere C1 e C4 em uso real e gera o exemplo novo | A5 | **(João)**: autorizar a chamada de API ou rodar você mesmo |
| 5 | Trocar o exemplo nas três versões de `estrutura-plano` e regenerar | A5 | etapa 4 |
| 6 | Levar `fix/auditoria-25-11-c1-c4-c5-c9` à `main`. É fast-forward: a branch contém `origin/main` + 26 commits (figuras do Cap. 4, auditoria, correções). Atualizar os hashes citados (A1) | — | **(João)** pedir |
| 7 | Subir a especificação v2.3 no Projeto e marcar os documentos antigos como histórico | A10, A12 | seu ok |
| 8 | Levar a lista da §4 ao chat de escrita do TCC | A11 | **(João)** |
| 9 | **Novo congelamento** depois dos testes finais (marcar a `main` e registrar no `CLAUDE.md`) | — | **(João)** pedir |

## 6. Próximos passos imediatos

1. Você escolhe a variante do diagrama de casos de uso.
2. Eu faço a etapa 2 (uns 30 min, só documentação) e, se quiser, a 3.
3. Você decide quando fazer a nova execução real (etapa 4). É o que destrava a figura `estrutura-plano`, as telas do Cap. 4 e a
   conferência de C1/C4 em uso real.
4. Merge na `main` e novo congelamento quando você pedir.
