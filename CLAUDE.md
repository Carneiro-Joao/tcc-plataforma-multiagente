# AulaIA — contexto para o Claude Code

TCC de João Victor (Computação). Plataforma web que gera planos de aula de Computação (BNCC) com especialistas LLM em
múltiplos agentes, RAG da BNCC, validador determinístico e uma "IA Juiz" que avalia o plano. Idioma de trabalho: português do Brasil.
Quem decide o escopo é o João; o orientador está viajando, então toda decisão grande fica registrada como
"pendente de ratificação" (reversível).

## Estrutura
- `aula-ia-backend/` — Python, **somente biblioteca padrão** (`python -S` precisa passar), SQLite, `unittest`.
  - `contratos/` PlanoDeAula 2.0 (11 seções, IDs OBJ/EVI/ET/INS/ADP), ParecerJuiz 1.0, rubrica 0.1 do Juiz.
  - `geracao_v2.py` + `gemini.py` geradores (Gemini); `juiz.py` + `groq_juiz.py` Juiz (Groq, `openai/gpt-oss-120b`).
  - `ensaio_juiz.py` roda o Juiz sobre casos congelados; `variantes_juiz.py` cria variantes controladas;
    `analisar_serie.py` pontua séries; `relatorio_testes.py` roda os testes e gera HTML.
  - `local/` é **ignorado pelo Git** (bancos, relatórios, resultados brutos).
- `experimentos/juiz/` — casos congelados, variantes, protocolos pré-registrados (V03–V06) e regras de pontuação.
- `docs/` — documentação e diagramas.

## Comandos (rodar dentro de `aula-ia-backend`; no Windows `python` ou `py`)
- Testes com relatório visual: `python relatorio_testes.py` (abre HTML; `--sem-abrir`, `--filtro juiz`).
- Testes simples: `python -m unittest discover -s tests -v`.
- App: `python app.py --modo lexical --gerador ia --ipv4 --abrir` (demo sem API: `--gerador demonstracao`).
- Juiz: `python ensaio_juiz.py avaliar --caso ../experimentos/juiz/casos/<caso>.json --versao-prompt juiz-v1.3 --reparos 1`
  (use `--somente-validar` para testar sem rede nem chave).
- Adjudicação humana: `python adjudicacao.py` (gera páginas em `local/adjudicacao/`); guia em `docs/Guia_Adjudicacao_Humana.md`; `python concordancia.py a.json b.json`.
- Análise: `python analisar_serie.py --pasta local/ensaios_juiz --regra ../experimentos/juiz/pontuacao/V0X.json --baseline-pasta local/ensaios_juiz`.

## Regras que não podem ser quebradas
1. **Nunca ler, imprimir, escrever em arquivo ou commitar chaves de API** (`GROQ_API_KEY`, `GEMINI_API_KEY`). Só variável de ambiente.
2. **Não rodar chamadas reais de API sem o João pedir** naquele momento. Groq tem limite de ~8.000 tokens/min: pausa de 75 s entre
   chamadas (120 s se vier HTTP 413). Falha técnica (400/413/429, recusa) é registrada e **nunca** conta como parecer, detecção ou falso negativo.
3. **Pré-registro:** protocolos e regras em `experimentos/juiz/` (V03–V06) não são editados depois de ver resultados.
   Mudou a hipótese? É uma nova versão, commitada antes de qualquer chamada.
4. Não misturar configurações: controle só vale com mesmo hash de plano e mesma configuração (prompt, modelo, rubrica, parâmetros).
5. `local/` não vai para o Git. Única exceção: `git add -f aula-ia-backend/local/ensaios_juiz`, **depois** de procurar chaves
   (`findstr /s /i /m "AIza gsk_ api_key" aula-ia-backend\local\ensaios_juiz\*`).
6. Código novo vem com testes que falham quando o código é quebrado de propósito (teste de mutação manual). `python -S` tem que passar.
7. Uma branch por incremento (`feat/pocNN-...`), mensagens `feat|fix|docs|test|data(escopo): ...`, nunca `push --force`,
   nunca mexer em `main` sem o João pedir. Mostrar `git status` antes de `git add`; listar arquivos explicitamente.
8. Resultado de LLM é evidência provisória: a classificação mecânica não substitui adjudicação humana. Não afirmar "estável",
   "validado" ou "o Juiz acerta" sem evidência (n pequeno, um plano, temperatura 0 não é determinístico).

## Estado em 18/11/2026
- Cadeia de branches: `feat/poc04a-contratos` → `poc04a-gemini` → `poc04a-prototipo-local` → `poc05-juiz-contrato` → `poc05b-juiz-groq`
  → `poc05c-variantes` → `poc05d-analise-serie` → `poc05e-relatorio-testes` → `poc05f-filtro-baseline` → `claude-md-contexto`
  → `poc05g-completar-series` → `ui-identidade-cores` (paleta marinho/gelo/turquesa, fonte Sora + Inter) → `ui-jsx-nativo`.
  `main` está defasada (`3939dfd`).
- Front: o app serve `aula-ia/dist/`, gerado por `npm run build` a partir de `src/App.jsx` + `src/App.css` (camada `tema-compat` removida
  em `ui-jsx-nativo`). `public/geracao-ui.*` (painel de geração) é copiado para `dist/` pelo build. Mudou o front? `cd aula-ia && npm run build`
  e commitar `dist/`. Teste: `node aula-ia/tests/test-plano-render.mjs`.
- Registro entre Claude Code, Codex e Claude do chat: `docs/diario_de_bordo.md` (mais novas no topo; escrever uma entrada ao terminar algo).
- Juiz: prompt `juiz-v1.3`, rubrica 0.1, política preliminar. **Não está integrado** ao pipeline, à UI nem ao SQLite.
- Séries com v1.3 **completas** (3 válidos cada; falhas técnicas à parte): controle do plano original = 3; V03 = 3; V04 = 3 (+2 falhas 413);
  V05 = 3 (+1 falha 413); V06 = 3. Níveis mecânicos: V03 parcial 2/ausente 1; V04 parcial 1/ausente 2; V05 plena 3;
  V06 sem pares novos e decisão igual à base 3/3. Tudo provisório, aguardando adjudicação humana.
- A busca de chaves com `findstr` dá falso positivo conhecido em `20261118T023623Z-e8304f3019e7/resultado.json`
  (mensagem de erro cita "GROQ_API_KEY"; sem chave real). Qualquer outro match: parar e avisar o João.
- Achados a adjudicar: o Juiz repete "plano só trabalha Bubble sort" (possível falso positivo curricular) e "ET2 simula uma passagem só";
  na V03 ele acha o defeito mas atribui ao componente `metodologia` em vez de `sequencia`.

## Pendências (ordem sugerida)
1. ~~Completar V04 e V05~~ (feito em `f35ff84`, 18/11). Próximo: adjudicação humana das séries V03–V06.
2. Adjudicação humana: ferramenta pronta (`feat/poc05h-adjudicacao`); falta escolher o 2º avaliador e rodar as Fases A e B.
3. Registro de decisões + e-mail ao orientador (pendente de ratificação). Perguntar a data final do TCC.
4. Juiz → pipeline (estados, tabela de pareceres no SQLite, UI); ciclo de correção entre agentes.
5. Plano de merge para `main`; limpar menções residuais a DeepSeek na documentação.
