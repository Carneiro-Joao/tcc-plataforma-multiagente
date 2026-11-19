# Diário de bordo — AulaIA

Canal entre Claude Code (código/Git local), Codex (implementação em branches paralelas) e Claude do chat (revisão, análise, texto).
Quem termina algo escreve uma entrada curta. **Mais novas no topo.** Formato: data/hora (BRT) · autor · branch/commit,
depois o que foi feito, números e pendências. Sem interpretação pedagógica aqui: isso é da adjudicação humana.

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
