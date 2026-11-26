# Diário de bordo — AulaIA

Canal entre Claude Code (código/Git local), Codex (implementação em branches paralelas) e Claude do chat (revisão, análise, texto).
Quem termina algo escreve uma entrada curta. **Mais novas no topo.** Formato: data/hora (BRT) · autor · branch/commit,
depois o que foi feito, números e pendências. Sem interpretação pedagógica aqui: isso é da adjudicação humana.

---

## 2026-11-25 21:45 · Claude do chat · ajustes pedidos pelo João após a revisão geral (`fix/auditoria-25-11-c1-c4-c5-c9`)

Diagrama de estados: `interrompido` = "sem sinal por mais de 15 min (app parado)". Adendo na auditoria (C1–C9 corrigidos) e nota no §8
da PoC 10 (lista aplicada). README enxuto; o antigo em `docs/historico/README_ate_2026-11-25.md`. Retirados os 3 `*-mermaid.png`.
Projeto do claude.ai: `claude/especificacao-v2.3.md` (nova), v2.2 marcada como histórico, `claude/repositorio-estado-25-11-noite.md`.
Plano de ação da revisão em espera (variante de casos de uso e oks do João). 532 testes ok; 3 de interface ok.

## 2026-11-25 22:00 · Claude do chat · achados C1, C4, C5, C9 e figuras novas (`fix/auditoria-25-11-c1-c4-c5-c9`, a partir de `docs/auditoria-25-11`)

A pedido do João: C1 a reescrita de acentuação só é aceita se IDs, números, vínculos e estrutura ficarem iguais (`acentuacao.mesma_estrutura`);
C4 batimento de 60 s renova `atualizado_em` enquanto o pedido roda (`interrompido` passa a significar app parado); C5 com Juiz de demonstração
a regeneração é cega e o histórico registra o motivo; C9 `REPETICOES_503_PADRAO = 2` na classe `AgenteGemini` (app e lote usam a constante;
`teste_gemini.py` passa 0 de propósito). Testes em `tests/test_auditoria_25_11_achados.py`; 11 mutantes, 0 vivos (sem bytecode).
532 testes (1 ignorado), com e sem `-S`; 3 scripts de interface ok. Figuras: casos de uso em SVG UML desenhado à mão, visão geral e
estrutura do plano ilustradas (`docs/diagramas/final/ilustradas/`; HTML e PlantUML mantidos); nó G das atividades cita a reescrita de
acentuação. Sem chamadas de API. Nada na `main`.

## 2026-11-25 20:00 · Claude do chat · auditoria documentação × código (`docs/auditoria-25-11`, a partir de `fed4a81`; código em `main` `4558b4a`)

Relatório: `docs/Auditoria_Documentacao_e_Codigo_25-11.md`. Com aprovação do João: especificação **v2.3** (regeneração informada pelas
críticas da IA Juiz e verificação de acentuação; RN16, RN17; v2.2 vira histórico) e `Correspondencia_IDs_v2.1R2_v2.3.md`; diagrama de
componentes atualizado e PNG/SVG regenerados; SVGs de atividades e sequência regenerados; versões Mermaid (`.mmd`) de casos de uso,
visão geral e estrutura do plano (fontes PlantUML/HTML mantidas); Estado_Final, contrato do plano, README e CLAUDE.md atualizados,
**sem marcar nada como congelado**. Código: C2, C3, C6, C7, C8 (um commit e teste cada, `tests/test_auditoria_25_11.py`).
Testes: 521 (520 ok, 1 ignorado), com e sem `-S`; 3 scripts de interface ok. Sem chamadas de API. Nada na `main`.
Pendente: exemplo da figura `estrutura-plano` (espera nova execução do João); C1, C4, C5, C9 só registrados.

## 2026-11-25 17:30 · Claude Code · PoC 10: verificação real + `main` (`feat/poc10-regeneracao-informada` → `main`)

Com o ok do João: app reiniciado com o código novo (porta 8000, limites padrão) e 1 pedido real pela API (caso 5 da sondagem,
Ordenação desplugada, EF08CO03), 188 s. Versão 1: 3 reescritas de acento aceitas (`objetivos` 3→0, `metodologia` 1→0, `adaptacao`
2→0), Com ressalvas, F1 maior (instrumentos sem rubrica). Versão 2 (informada, 6/6 chamadas com `revisao_pedagogica`, F1 só para
`avaliacao_preliminar`): nenhuma reescrita necessária; a crítica foi resolvida, mas o Juiz levantou F1 maior nova ("só Bubble sort",
crítica recorrente a adjudicar) → 1 grave → 1 grave, entregue a mais recente com aviso. Planos finais sem texto sem acento.
Bruto: `experimentos/geracao/poc10_verificacao_real/`. Uso do dia depois do teste: 6/8 gerações, 3/8 avaliações. n = 1, provisório.
Branch levada à `main` por fast-forward (inclui a PoC 09).

---

## 2026-11-25 · Claude Code · PoC 10: regeneração informada + acentuação (`feat/poc10-regeneracao-informada`)

Pedido do João depois da sondagem: implementar a opção C, corrigir a perda de acentuação e registrar tudo para ajustar o texto.
**Regeneração informada (padrão):** parecer não favorável → plano inteiro gerado de novo; cada especialista recebe `revisao_pedagogica`
(versão anterior, falhas próprias com correção sugerida, demais falhas como contexto, instrução que proíbe recursos fora do contexto).
Prompt de sistema, 1ª geração, Juiz, política, ciclos, limites, estados e entrega inalterados. Histórico do pedido ganha o evento
`regenerando` (modo, versão, críticas usadas); `--regeneracao cega` mantém a PoC 08. **Acentuação:** saída sem acento (campo > 60 car.,
nenhum acento, palavra-guia) → 1 reescrita; aceita só se validar e melhorar; senão fica a original. Causa: gatilho no Gemini + cascata.
Testes: 513 (512 OK, 1 ignorado), também com `-S`; front 3/3; mutação 22 mutantes, 1 sobrevivente na 1ª rodada (saída descartada no
rastreio) → 2 testes novos → 0 vivos. **Sem chamadas reais.** Especificação e diagramas não editados: lista de ajustes em
`docs/PoC10_Regeneracao_Informada_e_Acentuacao.md` §8. `Estado_Final_Sistema.md`, nota na PoC 08 e `CLAUDE.md` atualizados.
Pendente: ok do João para 1–2 pedidos reais de verificação, levar à `main`, reiniciar o app.

---

## 2026-11-25 17:00 · Claude Code · Sondagem PoC 09: regeneração cega × informada (`feat/poc09-sondagem-regeneracao-informada`)

Pedido do João: testar a opção C (regenerar o plano inteiro passando a cada especialista a sua versão anterior e as críticas do Juiz)
antes de implementar. Pré-registro + script + testes commitados ANTES das chamadas (`1e1c096`; 6 testes, 9 mutantes, 0 vivos; 499 OK).
Rodada real 16:20–16:55: 11 gerações, 11 avaliações; 5 primeiras versões reais não favoráveis (9 graves) → **cego: 8 graves, 1/5 favorável,
4 repetidas; informado: 5 graves, 2/5 favoráveis, 2 repetidas**; contrato 5/5 nos dois; o único H1 do informado é o falso positivo de
negação. Os graves restantes do informado vêm de conflitos de entrada (Listas teórica; Programação só com material impresso).
**Achado à parte:** Gemini sem acentuação desde 23/11 (plano do app de 25/11: 16/19 campos longos sem acento), nos dois braços.
Exploratório (n = 5; Juiz circular). Detalhes: `docs/PoC09_Resultado_Sondagem.md`. App e `main` não alterados.

---

## 2026-11-23 22:45 · Claude do chat · Figuras para leigos (`main`)

**Feito:** seleção das figuras do Cap. 4 por pergunta do leitor (visão geral, casos de uso, sequência + prints, componentes, atividades,
estrutura do plano; ER e estados no apêndice; sem diagrama de classes). Criadas `final/visao-geral` e `final/estrutura-plano` (fonte HTML
+ PNG; exemplo real do plano `ordenacao_r1_917c3ba9`). Sequência corrigida: quem chama a IA Juiz é o serviço, não o orquestrador.

---

## 2026-11-23 22:30 · Claude do chat · Documentação final (`docs/especificacao-final`)

**Feito (só documentação; código congelado não mudou)**
- Revisão de requisitos, regras e diagramas da R2 contra o sistema congelado (projeto do TCC: `claude/revisao-documentacao.md`).
- Decisões do João (23/11): RF25 vira "aprovar ou gerar novamente" (sem rejeição); "depois de aprovar, nova consulta" é o comportamento
  final; renumerar IDs a partir de RF01, com tabela de correspondência; Cap. 5 com participantes não entra; levar a documentação final à `main`.
- `docs/especificacao/AulaIA_Especificacao_v2.2_final.md` (22 RF, 10 RNF, 15 RN, 4 UC, todos implementados; RF06 sem teste automatizado),
  `Correspondencia_IDs_v2.1R2_v2.2.md`, `docs/diagramas/diagramas-finais.md` + `final/` (componentes, casos de uso UML, sequência,
  atividades, estados, ER, com fontes e imagens). `PoC04A_Gemini_atual.md` marcado como histórico; testes atualizados para 493.

---

## 2026-11-19 14:50 · Claude Code · Correção: intervalo mínimo entre chamadas do Juiz (`feat/poc08c-intervalo-juiz`, autorizada pelo João)

**Estado antes (pedido do João):** geração usada hoje = 16, Juiz = 3 (pela mesma consulta do app); nenhum pedido preso em andamento.
O app aberto às 14:16 (PID 6556, aberto à mão) roda com os limites PADRÃO (8/8, ciclos 1): com 16 usadas, novas gerações são recusadas
pelo limite diário até reiniciar com `--limite-diario` maior. As duas falhas depois das 13:44 foram do Gemini (timeout e 503).
**Premissa conferida:** já havia 75 s entre avaliações em `servico._avaliar` (contados do FIM da anterior), mas sem lock, sem aviso na tela
e sem contar o reparo. **Correção:** o intervalo passou para `juiz_servico.JuizGroq` (um lugar só): 75 s entre INÍCIOS de chamadas reais,
120 s depois de 413, sob `threading.Lock`; o reparo segue com 60 s e vira a "última chamada"; durante a espera o pedido fica
`aguardando_juiz` e a tela mostra "Aguardando a cota da IA Juiz…". A pausa antiga do `servico` foi removida (sem espera dupla).
Prompt, modelo, rubrica, política e reparos inalterados; `ensaio_juiz.py` não muda.
**Testes:** 10 novos (`tests/test_intervalo_juiz.py`, relógio e sono falsos; inclui duas threads ao mesmo tempo e relógio só lido com o lock)
+ front (`test-juiz-render.mjs`); 17 mutantes sem bytecode, 0 vivos; 493 OK (também `-S`); E2E Playwright OK. `dist/` rebuildado.

---

## 2026-11-19 13:40 · Claude Code · Correção: pausa antes do reparo do Juiz (`feat/poc08b-pausa-reparo-juiz`, autorizada pelo João)

**Problema (uso real do João):** Groq rejeitou o formato do parecer (400) e o reparo imediato estourou 8.000 tokens/min → 429 →
"avaliação indisponível". **Correção:** espera de 60 s antes do reparo, só no app; configuração do Juiz e experimentos inalterados.
7 testes, 7 mutantes, 0 vivos; 484 OK (também `-S`). Detalhes em `docs/PoC08_Juiz_Integrado.md`. Levada à `main` (fast-forward).

---

## 2026-11-19 12:40 · Claude Code · PoC 08 — IA Juiz integrada (`feat/poc08-juiz-integrado`)

**Feito (um commit por fase, todos no GitHub)**
- F1 `533a6c5` backend: pedido = gerar → Juiz (juiz-v1.3, rubrica 0.1, política prelim 0.1, reparos 1) → regenera o plano inteiro se não
  favorável (`--ciclos-juiz`, padrão 1) → entrega a favorável ou a com menos falhas graves (empate: a mais recente), com aviso. Tabelas
  `pedidos`/`pareceres`, migração sem perda; limites de geração e do Juiz; `--juiz groq|demonstracao|desligado`.
- F2 `a2536ec` interface: progresso, painel "Avaliação da IA Juiz", Aprovar / Gerar novamente / Baixar PDF (parecer resumido na impressão).
- F3 `c40ada6` testes: 46 mutantes sem bytecode, 0 vivos; E2E Playwright em modo demonstração OK.
- F4 `fb59b32` real: Juiz nos 5 planos da 2.3 → 5 válidos (1 favorável, 4 em_correcao), 0 falhas; pedidos pela interface: Ordenação
  favorável em 49 s; Programação: timeout do Gemini 2× (falha técnica). Uso de 19/11: geração 8/8, Juiz 1/8 no app + 5 no ensaio.
- F5 `90d1a4c` acertos: demonstração sem cartões fora dos recursos; erro do tema com código; `tem_credencial` no `ensaio_juiz exportar`;
  alerta EF08CO01/02 sem computadores. 11 mutantes, 0 vivos. Suíte 477 OK (também `-S`); 3 testes de front OK.
- F6: `docs/Estado_Final_Sistema.md` (instalar, arquitetura, fluxo, versões congeladas, números, caminhos, limites).

**Achados / limites (sem interpretação pedagógica)**
- Regeneração com chamadas reais NÃO foi observada (limite de geração do dia acabou); coberta por testes e pelo modo demonstração.
- 4 de 8 gerações de 19/11 em timeout do Gemini (90 s), em etapas diferentes. PA-2 não reproduzida no Chrome headless (preventivo).

**Pendências**
- Fase 7: merge na `main` aguarda o "ok" do João. Depois: CLAUDE.md dizendo que a `main` é a versão congelada.
- Para o texto (trabalho futuro): correção dirigida por críticas, prompt 2.4, adjudicação humana, deploy.

---

## 2026-11-19 11:30 · Claude Code · Feedback do orientador e início da PoC 08 (`feat/poc08-juiz-integrado`)

**Feedback do orientador (reunião de 19/11):** o sistema já prova o conceito; é TCC, não produto. Na semana seguinte o João foca 100% na
escrita; **hoje é o último dia de desenvolvimento**: integrar a IA Juiz ao fluxo e congelar.
**Decisão do João (pendente de ratificação):** Juiz como etapa automática da geração; o professor recebe o plano já avaliado e decide.
**Reunião:** 1 geração real às 10:12 (61 s, ok); 2 timeouts do Gemini às 10:33 e 10:34 (falha técnica, contaram no limite); às 10:40, 58 s, ok.

---

## 2026-11-18 23:50 · Claude Code · Passagem para 19/11 (João segue primeiro com o Claude do chat)

**Onde parar/retomar:** branch `feat/poc07d-lote-2-3` @ `54d2711`, tudo commitado e no GitHub. `main` não tocada.
**Cota:** limite de IA de 18/11 esgotado (12/12). Em 19/11 o contador zera; qualquer chamada real continua exigindo pedido do João.
**Para o Claude do chat (sugestão de pauta):**
1. Adjudicar `docs/PoC07D_Resultado_Lote_2_3.md` (2 H1 da 2.3 e leitura por plano).
2. Decidir o que pré-registrar a seguir: regra de medição v2, prompt 2.4 e/ou alerta habilidade × recursos (texto do pré-registro é com o chat;
   implementação e testes podem voltar para o Claude Code).
3. Se houver decisão nova, registrar aqui e no `CLAUDE.md` (pendências já atualizadas).
**Para o Claude Code ao voltar:** ler este diário do topo, conferir `git status` e `git fetch`, e partir da branch que o chat indicar.

---

## 2026-11-18 23:45 · Claude Code · `feat/poc07d-lote-2-3` (base: `poc07c-limite-diario`)

**Feito**
- `e5fa6d4` (antes de qualquer chamada): `gerar_lote.py` (mesmo caminho e mesmo limite diário do app; pausa 30 s; falha técnica → 60 s e
  1 nova tentativa com consulta nova, revisão 1; 2 cotas seguidas ou limite → para; `--somente-validar` com banco temporário),
  `medir_planos.py` (regra fixa do PoC07B + minutos + contrato) e `experimentos/geracao/poc07b_entradas.json` (5 linhas do protocolo;
  teste compara com a tabela do documento). 35 testes; mutação sem bytecode: 37 mutantes, 3 vivos na 1ª rodada → testes novos, 0 ao final.
  Suíte 435 OK, também com `-S`.
- Lote real (autorizado pelo João, 23:29–23:35): 5/5 planos com `especialistas-plano-2.3`; 1 falha técnica (503, Listas), refeita uma vez.
  Limite de 18/11: 12/12. `49f9631d` (23:01, fora do protocolo) não entra na medição.
- Medição pré-registrada (n = 5 cada): H1 2.2 = 2/5, 2.3 = 2/5; H2 1/5 → 0/5; minutos 5/5 e contrato 5/5 nas duas.
  Os 2 H1 da 2.3 ("sem uso de computador"; "tátil com o material impresso") parecem falsos positivos da regra — **a adjudicar**.
- Casos da 2.3 em `experimentos/geracao/poc07b_planos_2_3/` (busca de chaves: nada). Relatório: `docs/PoC07D_Resultado_Lote_2_3.md`.

**Pendências**
- Adjudicar os 2 H1 da 2.3 e a leitura por plano do relatório (Claude do chat + João).
- Possíveis próximos passos (não feitos, exigem pré-registro): regra de medição v2 (negação), prompt 2.4 (fidelidade ao tipo de aula,
  exemplo concreto, evidência não só oral), alerta habilidade × recursos.

---

## 2026-11-18 23:20 · Claude do chat · `feat/poc07c-limite-diario` (base: `poc07b-prompt-2-3`)

**Feito**
- Chaves Gemini e Groq salvas pelo João como variáveis de ambiente do usuário no Windows (decisão dele, com limite de gasto na conta Google).
- **Limite diário no app:** `ServicoCurricular(limite_diario_ia=...)` + `app.py --limite-diario` (padrão 8, decisão do João; 0 desliga). Conta gerações com IA
  do dia (data local), incluindo falhas e regenerações; bloqueia com HTTP 429 **antes** de chamar a API. Demonstração não conta.
  O terminal mostra o uso do dia ao iniciar.
- 11 testes novos (`test_limite_diario.py`); mutação sem bytecode: 11 mutantes, 1 sobrevivente → teste novo, 0 ao final.

**Pendências**
- Rodada da 2.3 (5 planos) pelo João. Script de lote para o Claude Code: respeitará o mesmo limite.

---

## 2026-11-18 22:40 · Claude do chat · `feat/poc07b-prompt-2-3` (base: `poc07-exportar-planos`)

**Feito**
- Revisão de 5 planos reais (prompt 2.2) + PDFs impressos pela interface. Achados: "cartões" sem estar nos recursos em 2/5 (causa: o próprio
  prompt sugeria "cartões já preparados"); 1/5 com campos sem acento; plano "Programação" sem programação (EF08CO01 × só material impresso);
  evidências fracas ("registra oralmente/mentalmente"; "o computador exibe a lista ordenada"); falta de conteúdo concreto; 4/4 planos de
  ordenação só com Bubble Sort (fato; se é defeito fica para a adjudicação).
- **Prompt `especialistas-plano-2.3`** (`geracao_v2.py`), com a 2.2 preservada em `VERSOES_PROMPT`. Pré-registro com hipóteses, as 5 entradas
  exatas e a regra de medição em `docs/PoC07B_Prompt_2_3.md`, **commitado antes de qualquer chamada**. 5 testes novos; mutação: 8 mutantes, 0 vivos.
- **Erro de método corrigido:** meus testes de mutação deixavam `.pyc` velho (mutante do mesmo tamanho restaurado no mesmo segundo), o que
  fez a 2.2 parecer quebrada na suíte e mascarou um sobrevivente no exportador (`gsk_` redundante com o `sanitizar`). Refeitos sem bytecode
  (tema 12, exportador 14, prompt 8 mutantes): 0 vivos depois de um teste novo no exportador. Regra adicionada ao `CLAUDE.md`.

**Pendências**
- João regenera as 5 entradas com a 2.3 e exporta; comparação descritiva pela regra pré-registrada.
- Interface (Claude Code): página em branco no fim da impressão do plano de Programação (PA-2, 4ª página); impressão sem texto pesquisável
  quando o usuário escolhe "Microsoft Print to PDF" (limitação do Windows, não do app).
- Alerta determinístico de material fora dos recursos, campo sem acento e habilidade × recursos. Gerador de demonstração também usa cartões.

---

## 2026-11-18 23:00 · Claude do chat · `feat/poc07-exportar-planos` (base: `poc06b-ui-tema-recursos`)

**Feito**
- `exportar_planos.py`: exporta de uma vez os planos reais (IA) do SQLite local para `local/planos_ia/*.json` (formato de caso congelado), em leitura
  e sem sobrescrever; pula com motivo demonstração, falha, plano fora do contrato e credencial. Guia: `docs/PoC07_Gerar_e_Exportar_Planos.md`.
- Achado: `groq_juiz.sanitizar` só mascara chaves do Groq (`gsk_…`); o exportador ganhou checagem própria para `AIza…`/`gsk_…`/`sk-…`.
  (O `ensaio_juiz.py exportar` continua só com o `sanitizar` — pendência pequena: reaproveitar `tem_credencial` ali.)
- 12 testes novos (381 no total, também com `-S`); mutação manual: 14 mutantes na 1ª rodada, 3 sobreviventes (testes que faltavam), 0 ao final.

**Pendências**
- João gera ~4 planos reais, roda `python exportar_planos.py` e envia; Claude do chat revisa. Chamada real de API só quando o João roda.

---

## 2026-11-18 22:30 · Claude do chat · `feat/poc06b-ui-tema-recursos` (revisão da PoC 06b)

**Revisão:** testes OK (372 Python, `test-formulario.mjs`, `test-plano-render.mjs`); fluxo conferido no Chromium. Um defeito achado, de um prompt meu:
o campo de tema tinha `maxLength=80` e **cortava a frase antes da extração** (frase de 104 caracteres entrava como "…vai ser IA gen").
**Correção:** `LIMITE_TEMA` 80 → 300 (backend aceita 800) + teste que exige que a frase do feedback caiba no campo; `dist/` rebuildado
(build reprodutível: só o JS mudou). Conferido com 4 frases longas: tema correto em todas, JSON invisível sem `?depuracao=1`.
**EF08CO11 em 2º para "Ordenação":** não é bug. O exemplo da BNCC dessa habilidade cita "critérios de ordenação e relevância" e a busca lexical
dá bônus por palavra de exemplo (0,30 contra 0,35 da EF08CO03). Mantido.
**Observações (sem ação agora):** (1) no botão "Escolher no catálogo" o backend ainda exige tema identificável (o tema é usado no título do plano);
(2) `erroEhDoTema` usa a regex /tema/ na mensagem, frágil se o texto do backend mudar.

---

## 2026-11-18 21:40 · Claude Code · `feat/poc06b-ui-tema-recursos` @ `ce8397b`

**Base** (decisão do João): criada de `feat/poc06-tema-curto` + merge de `feat/ui-jsx-nativo` (`beb43fc`; conflito só neste diário).
Originais intactas; `main` não tocada. `tema.py` e `servico.py` não foram alterados. Nenhuma chamada real de API.

**Feito** (`aula-ia/src/App.jsx`, `src/formulario.js`, `src/App.css`, `public/geracao-ui.js`; `dist/` reconstruído)
1. JSON e rastreio técnico (confirmação, plano 2.0, plano legado, tentativa com falha) só aparecem com `?depuracao=1`; código mantido.
2. Tema: placeholder "Ex.: ordenação", `maxLength` 80. 422 cuja mensagem fala de tema aparece junto ao campo (`aria-invalid`),
   o texto digitado é preservado; outros erros continuam no topo. Consulta restaurada mostra `pedido_original` no campo.
3. "Tema identificado: …" (`consulta.contexto.tema`) acima dos resultados; sem botão nem etapa extra.
4. Lista vazia: "Não encontramos habilidade da BNCC de Computação para este tema. Tente outro termo." (+ dica do catálogo).
5. Recursos: checklist (quadro e pincel, projetor, computadores, celulares, internet, material impresso, outro) + "Quais?" opcional
   quando "Outro" está marcado. Obrigatório: sem nada marcado, a consulta nem é enviada. Valor enviado = string
   ("quadro e pincel, projetor, cartões numerados"). Aula teórica pré-marca "quadro e pincel" sem desmarcar os outros.

**Verificação**
- `tests/test-formulario.mjs` (novo) e `tests/test-plano-render.mjs` (depuração no plano 2.0 e legado). 12 mutações manuais
  (recursos, aula teórica, depuração, 422, App.jsx, geracao-ui.js): 0 sobreviventes. Backend `python -S`: 372 testes OK.
- Playwright (Chrome do sistema, `playwright-core` fora do repo) no servidor de demonstração: fluxo completo até aprovar em 1440 px,
  422 com "quero preparar uma aula bem legal", lista vazia com "IA generativa", `?depuracao=1`, restauração do checklist e
  formulário em 360 px. Sem erro de JS no console (só o log de rede do 422 esperado). Capturas ficaram fora do repositório.

**Observações (sem interpretação pedagógica)**
- Com o tema "Ordenação" a busca lexical também traz EF08CO11 (mídias digitais) em 2º lugar. É comportamento do backend, não mudado aqui.
- Um servidor de demonstração antigo (outra branch) ainda ocupava a porta 8765 e respondia sem extrair o tema; foi encerrado.
  Ao testar localmente, conferir que só há um `app.py` na porta.

**Pendências**
- Merge da cadeia para `main`.

---

## 2026-11-18 18:00 · Claude do chat · `feat/poc06-tema-curto`

**Feito**
- Feedback externo (tema = input completo no plano): `aula-ia-backend/tema.py` extrai o **tema curto automaticamente, sem confirmação**
  (catálogo → marcador → texto curto; recusa com 422 se não achar). Integrado em `servico.consultar`; a busca também usa o tema curto (a frase
  inteira trazia habilidades erradas por palavras de ruído); a frase fica em `consulta.pedido_original`. Detalhes e limites em `docs/PoC06_Tema_Curto.md`.
- Fixtures de ordenação atualizadas para o tema curto ("Ordenação"); caso real gravado `resposta_real_integrador` mantido.
- 373 testes OK (com e sem `-S`); mutação manual (>35 mutantes, 2 rodadas), 0 sobreviventes ao final. Frases usadas na sondagem viraram regressão, não avaliação.

**Pendências**
- UI (Claude Code): esconder JSON (`?depuracao=1`), placeholder/limite do tema, checklist de recursos. Recursos obrigatório mantido (decisão de João).
- Decisão **pendente de ratificação do orientador**. Falso positivo conhecido: "lista de compras" → "Lista".

---

## 2026-11-18 15:30 · Claude do chat · `feat/poc05h-adjudicacao`

**Feito**
- Ferramenta de adjudicação humana das séries V03–V06 + controle (v1.3): `adjudicacao.py`, `adjudicacao_web.py`, `concordancia.py`
  e `docs/Guia_Adjudicacao_Humana.md`. Gera 3 páginas HTML offline (Fase A cega, Fase B informada, comparação com kappa e consenso)
  e `chave_de_codigos.json` (não compartilhar antes do fim da Fase A).
- Escopo: 5 planos, 39 críticas, 12 pareceres (só válidos de `juiz-v1.3`).
- Testes novos: `test_adjudicacao.py` (23) e `test_concordancia.py` (12), com mutação manual; interface testada em Chromium.

**Pendências**
- João escolhe o 2º avaliador, gera as páginas (`python adjudicacao.py`) e conduz as fases; o resultado volta em `experimentos/juiz/adjudicacao/`.

---

## 2026-11-18 02:00 · Claude Code · `feat/ui-jsx-nativo` (a partir de `feat/ui-identidade-cores` @ `a734cca`)

**Feito** (decisão do João: usar a versão nova do JSX)
- `a734cca` (em `ui-identidade-cores`): título do plano com inicial maiúscula na exibição, inclusive após o travessão
  ("Plano de aula — Quero ensinar…"). Teste + mutação manual.
- `npm ci` + `npm run build`: `dist/` agora vem de `src/App.jsx` (antes: React da PoC 02 compilado + camada `tema-compat`).
  Mesma API, mesma chave de sessão `aulaia.consulta.v1`, mesmos campos. Ganhos: menu lateral, trilha e etapas nativos no React,
  ícones SVG, indicador de progresso que escuta `aulaia:geracao-atualizada` (aprovação marca a etapa 3).
- Removidos `public/tema-compat.css/js` (e cópias em `dist/`), sem uso com o JSX novo.
- `geracao-ui.css`: `.primario.geracao-aprovar` (mais específica), porque no build novo o CSS do app carrega depois e deixaria o botão
  Aprovar marinho em vez de verde.
- Verificação: fluxo real na UI via CDP (preencher → consultar → escolher → confirmar → gerar → aprovar) em 1440 e 360 px:
  sem erro no console, sem estouro horizontal, Aprovar verde, 3 etapas concluídas após aprovar. Front test OK; backend 309 OK.

**Pendências**
- `npm audit`: 0 vulnerabilidades nas dependências de produção; avisos só nas de desenvolvimento (não afetam o `dist/`).
- Merge da cadeia para `main` continua pendente.

---

## 2026-11-18 01:10 · Claude Code · `feat/ui-identidade-cores` @ `bb94f16`, `9ff2b29`

**Feito** (branch criada a partir de `feat/poc05g-completar-series`; pedido do João, só visual)
- `bb94f16` identidade visual: marinho `#0b1f3a` (dominante), gelo `#e6f4f6` (secundária), turquesa `#14b8b0` (destaque; texto
  marinho sobre ele). Fonte Sora (títulos/menu/botões) + Inter (texto). Variáveis `--marinho`, `--gelo`, `--turquesa`.
  Primeira tentativa (marinho/creme `#FBE8CF`/laranja `#FDAC2F`) foi descartada pelo João: o creme dominou.
- `9ff2b29` Tema e Recursos aparecem com inicial maiúscula **só na exibição** do plano (`geracao-ui.js`). O dado salvo não muda,
  porque o contrato exige `recursos` idêntico à entrada. Teste em `aula-ia/tests/test-plano-render.mjs` (mutação manual: tirar a
  maiúscula ou o escape faz o teste falhar). Backend: 309 testes OK.

**Atenção para quem mexer no front**
- O app serve `aula-ia/dist/` = React **antigo** compilado + `tema-compat.css` + `geracao-ui.css/js` por cima. Editar em `public/` e
  copiar para `dist/`. **Não rodar `npm run build`** sem decisão do João: troca o app pela versão nova de `src/App.jsx`.
- `src/App.css` e o início de `public/tema-compat.css` são cópias; manter iguais.

**Pendências**
- ~~Overflow no celular~~: era artefato da captura (`--window-size` do Chrome headless tem largura mínima). Medido com emulação
  real (CDP) em 360/390/430/768 px, inclusive confirmação e plano gerado: nenhum elemento passa da largura da tela.
- ~~Tema/Recursos minúsculos na confirmação~~: resolvido só com CSS (`::first-letter` nas linhas 1 e 5 do `dl`), ver commit seguinte.
- O título do plano de demonstração repete o tema como digitado ("Plano de aula — quero ensinar…"); não alterado.
- Branch não mesclada; `main` não tocada.

---

## 2026-11-18 00:35 · Claude Code · `feat/poc05g-completar-series` @ `f35ff84`

**Feito**
- Branch criada a partir de `feat/claude-md-contexto` (`64105cf`, que contém `poc05f` + CLAUDE.md).
- Testes antes das chamadas: 309, 308 ok, 1 ignorado, RESULTADO: OK.
- 3 chamadas reais ao Juiz (autorizadas pelo João), `--versao-prompt juiz-v1.3 --reparos 1`, demais parâmetros padrão
  (temperature 0, max_completion_tokens 8192, reasoning_effort medium, seed 42), pausa de 120 s entre chamadas:
  - V04 `20261118T032851Z-956593e418cf` → sucesso
  - V05 `20261118T033107Z-c2a9153155ce` → sucesso
  - V04 `20261118T033323Z-e88deb38c9ed` → sucesso
  - Nenhum HTTP 413/429 nesta sessão.
- `analisar_serie.py` rodado para V03–V06 (V06 com `--baseline-pasta`). Rascunhos em `aula-ia-backend/local/V0X_rascunho_0033.md`
  (fora do Git).
- Commit só de `aula-ia-backend/local/ensaios_juiz` (3 pastas novas) após busca de chaves.

**Números (prompt juiz-v1.3, classificação mecânica provisória)**

| Variante | Válidos | Falhas técnicas | Nível mecânico |
|---|---|---|---|
| V03 | 3 | 0 | plena 0 · parcial 2 · ausente 1 |
| V04 | 3 | 2 (HTTP 413, sessão anterior) | plena 0 · parcial 1 · ausente 2 |
| V05 | 3 | 1 (HTTP 413, sessão anterior) | plena 3 |
| V06 (controle) | 3 | 0 | 0/3 citam a reformulação · 0 pares novos · decisão igual à base 3/3 (base: 3 controles v1.3) |
| Controle original | 3 | 1 (configuração: chave ausente, sessão anterior) | — |

**Observações**
- A busca `findstr ... "AIza gsk_ api_key"` dá **falso positivo previsível** em
  `20261118T023623Z-e8304f3019e7/resultado.json` (já commitado em `eac86a6`) (falha de configuração cuja mensagem cita "GROQ_API_KEY").
  Verificado: 0 ocorrências com formato de chave Google/Groq. João confirmou falso positivo. Sugestão (não aplicada): usar padrão mais
  específico (ex.: regex `gsk_[0-9A-Za-z]{40,}` / `AIza[0-9A-Za-z_-]{35}`).
- Auditorias informativas que chamam atenção para a adjudicação: `nota_3_sem_id_do_plano` 3/3 em V03, V04 e V06;
  `componente_provavelmente_errado` 3/3 em V03 e 2/3 em V05; `soma_de_minutos_no_texto` 3/3 em V04 e V06.

**Pendências**
- Adjudicação humana das séries V03–V06 (Claude do chat + João/adjudicador). Os níveis acima não são veredito.
- Planilha de adjudicação; registro de decisões; merge da cadeia para `main` (não tocada).
