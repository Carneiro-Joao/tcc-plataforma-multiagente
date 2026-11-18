# Diário de bordo — AulaIA

Canal entre Claude Code (código/Git local), Codex (implementação em branches paralelas) e Claude do chat (revisão, análise, texto).
Quem termina algo escreve uma entrada curta. **Mais novas no topo.** Formato: data/hora (BRT) · autor · branch/commit,
depois o que foi feito, números e pendências. Sem interpretação pedagógica aqui: isso é da adjudicação humana.

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
