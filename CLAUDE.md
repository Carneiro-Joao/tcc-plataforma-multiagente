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
  - `revisao_informada.py` (regeneração com as críticas do Juiz) e `acentuacao.py` (reescrita de saída sem acento), PoC 10.
  - `legado/` scripts quebrados das sondagens OpenAI/OpenRouter da PoC 03 (fora do fluxo).
  - `local/` é **ignorado pelo Git** (bancos, relatórios, resultados brutos).
- `experimentos/juiz/` — casos congelados, variantes, protocolos pré-registrados (V03–V06) e regras de pontuação.
- `docs/` — documentação e diagramas.

## Comandos (rodar dentro de `aula-ia-backend`; no Windows `python` ou `py`)
- Testes com relatório visual: `python relatorio_testes.py` (abre HTML; `--sem-abrir`, `--filtro juiz`).
- Testes simples: `python -m unittest discover -s tests -v`.
- App: `python app.py --modo lexical --gerador ia --ipv4 --abrir` (demo sem API: `--gerador demonstracao --juiz demonstracao`).
  Juiz: `--juiz groq|demonstracao|desligado` (padrão groq se houver `GROQ_API_KEY`), `--ciclos-juiz 1`,
  `--regeneracao informada|cega` (padrão informada), `--limite-diario-juiz 8`. Não misture `--gerador ia` com `--juiz demonstracao`
  fora de teste: a regeneração recebe críticas do parecer gravado de outro plano.
- Planos reais (Gemini): `python app.py --modo lexical --gerador ia --ipv4 --pedir-chave --abrir` e depois `python exportar_planos.py`
  (exporta os planos reais do SQLite para `local/planos_ia/`; guia em `docs/PoC07_Gerar_e_Exportar_Planos.md`).
  Limite padrão: 8 gerações com IA por dia (decisão do João, 18/11), contando falhas (`--limite-diario N`). **Não aumente nem desligue sem o João pedir.**
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
   Rode os mutantes **sem bytecode** (`python -B` e `PYTHONDONTWRITEBYTECODE=1`): mutante do mesmo tamanho restaurado no mesmo segundo
   deixa `.pyc` velho e produz resultado falso (aconteceu em 18/11).
7. Uma branch por incremento (`feat/pocNN-...`), mensagens `feat|fix|docs|test|data(escopo): ...`, nunca `push --force`,
   nunca mexer em `main` sem o João pedir. Mostrar `git status` antes de `git add`; listar arquivos explicitamente.
8. Resultado de LLM é evidência provisória: a classificação mecânica não substitui adjudicação humana. Não afirmar "estável",
   "validado" ou "o Juiz acerta" sem evidência (n pequeno, um plano, temperatura 0 não é determinístico).

## Estado em 25/11/2026 (noite) — auditoria documentação × código (`docs/auditoria-25-11`, NÃO congelado)
- Relatório: `docs/Auditoria_Documentacao_e_Codigo_25-11.md`. **O sistema não está congelado**: o congelamento de 19/11 foi reaberto
  em 25/11 para a PoC 10; novo congelamento só depois dos testes finais, quando o João pedir.
- Especificação vigente: `docs/especificacao/AulaIA_Especificacao_v2.3.md` (+ RN16, RN17) e `Correspondencia_IDs_v2.1R2_v2.3.md`;
  a v2.2 virou histórico. Nome oficial: "regeneração informada pelas críticas da IA Juiz" (não "correção dirigida", que segue futuro).
  "Gerar novamente" do professor = novo pedido do zero, sem as críticas anteriores (documentado; código não mudou).
- Diagramas: `componentes` com revisão informada e acentuação; versões Mermaid de casos de uso, visão geral e estrutura do plano.
  `estrutura-plano` (exemplo de 23/11) espera a nova execução do João.
- Código (aprovado item a item): C2 recursos não disparam reescrita de acento; C3 mensagem de limite (18 chamadas/54 requisições);
  C6 chaves falsas montadas em tempo de execução; C7 scripts OpenAI/OpenRouter → `legado/`; C8 docstring da herança em `geracao.py`.
  Só registrados: C1, C4, C5, C9. 521 testes (1 ignorado). Nada levado à `main`.

## Estado em 25/11/2026 — PoC 09 e PoC 10 (mudança de código autorizada pelo João depois do congelamento)
- **PoC 09** (`feat/poc09-sondagem-regeneracao-informada`): sondagem pré-registrada cega × informada, n = 5 → informada 5 graves e 2/5
  favoráveis contra cega 8 e 1/5 (exploratório; o próprio Juiz mede). `docs/PoC09_Resultado_Sondagem.md`.
- **PoC 10** (`feat/poc10-regeneracao-informada`): (1) **regeneração informada** é o padrão: parecer não favorável → plano inteiro gerado
  de novo, cada especialista recebe `revisao_pedagogica` (versão anterior + críticas do Juiz) nos dados da chamada; prompt de sistema e
  1ª geração inalterados; `revisao-informada-1.0` (`revisao_informada.py`); `--regeneracao cega` = PoC 08. (2) **Acentuação**: saída de
  especialista sem acento → 1 reescrita pelo `reparo_estrutural` (`acentuacao.py`; só modo IA; nunca derruba a geração). Causa: gatilho
  no Gemini + cascata entre especialistas encadeados. 513 testes; 22 mutantes, 0 vivos. Verificação real (1 pedido, 25/11 17:18):
  3 reescritas de acento aceitas, plano sem texto sem acento; regeneração informada resolveu a crítica, mas o Juiz levantou outra
  ("só Bubble sort") → 1 grave → 1 grave. Bruto em `experimentos/geracao/poc10_verificacao_real/`. Levada à `main` (fast-forward, 25/11).
- Lista de ajustes na escrita (especificação, correspondência, diagramas, capítulos): `docs/PoC10_Regeneracao_Informada_e_Acentuacao.md` §8.
  Especificação e diagramas foram atualizados depois, na auditoria (v2.3, branch `docs/auditoria-25-11`); o texto do TCC é do João.
- Viés: o Juiz não vê críticas nem versão anterior (sem vazamento), mas a medida é circular e há risco de "ensinar para a prova".

## Estado em 19/11/2026 — CONGELAMENTO
> Reaberto em 25/11 para a PoC 10 (decisão do João). As linhas abaixo são o registro de 19/11; novo congelamento após os testes finais.
- **`main` = VERSÃO CONGELADA** (19/11/2026, fast-forward de `feat/poc08-juiz-integrado`, autorizado pelo João). Toda a cadeia
  poc04a → poc08 está nela. Desenvolvimento encerrado: daqui em diante só escrita do TCC; qualquer mudança de código precisa do João.
  Fora da `main` (de propósito): `origin/docs/diagramas-rascunho` (rascunhos históricos de requisitos/diagramas).
- Para rodar e para os números do texto: `docs/Estado_Final_Sistema.md`; Juiz integrado: `docs/PoC08_Juiz_Integrado.md`.
- **Documentação final (23/11, aprovada pelo João):** `docs/especificacao/AulaIA_Especificacao_v2.2_final.md` (RF01–RF22, RNF01–RNF10,
  RN01–RN15, UC01–UC04, renumerados), correspondência com a R2 em `docs/especificacao/Correspondencia_IDs_v2.1R2_v2.2.md`, diagramas em
  `docs/diagramas/diagramas-finais.md` (fontes e imagens em `docs/diagramas/final/`). A R2 e os diagramas v2.1 são históricos.
- **Feedback do orientador (reunião de 19/11):** o sistema já prova o conceito; é TCC, não produto, não precisa ser perfeito. A partir da
  semana seguinte o João foca 100% na escrita. **19/11 é o último dia de desenvolvimento:** fechar o sistema com a IA Juiz integrada e congelar.
- **Decisão do João (pendente de ratificação):** o Juiz é uma ETAPA AUTOMÁTICA da geração (PoC 08, `feat/poc08-juiz-integrado`):
  gerar → Juiz avalia → favorável entrega; não favorável regenera o plano inteiro (até `--ciclos-juiz`, padrão 1) e entrega a melhor versão
  com aviso; falha técnica do Juiz entrega com "avaliação indisponível" (nunca conta como parecer). O Juiz é consultivo; o professor aprova.
- **Versões congeladas:** geração `especialistas-plano-2.3` (`gemini-3.5-flash-lite`); Juiz `juiz-v1.3` + `rubrica-juiz-0.1` +
  `politica-juiz-prelim-0.1` (`openai/gpt-oss-120b` na Groq), mesma configuração dos experimentos.
- **Fora do escopo (trabalho futuro no texto):** refazer só os componentes criticados (correção dirigida com grafo de invalidação; desde a
  PoC 10 a regeneração usa as críticas, mas refaz o plano inteiro), prompt 2.4, deploy na internet.

## Estado em 18/11/2026
- Cadeia de branches: `feat/poc04a-contratos` → `poc04a-gemini` → `poc04a-prototipo-local` → `poc05-juiz-contrato` → `poc05b-juiz-groq`
  → `poc05c-variantes` → `poc05d-analise-serie` → `poc05e-relatorio-testes` → `poc05f-filtro-baseline` → `claude-md-contexto`
  → `poc05g-completar-series` → `poc05h-adjudicacao` → `poc06-tema-curto` → **`poc06b-ui-tema-recursos`** (base oficial da interface,
  decisão do João em 18/11: `poc06-tema-curto` + merge de `ui-jsx-nativo`, que veio de `ui-identidade-cores`). `main` está defasada (`3939dfd`).
- Front: o app serve `aula-ia/dist/`, gerado por `npm run build` a partir de `src/App.jsx` + `src/App.css` (camada `tema-compat` removida
  em `ui-jsx-nativo`). `public/geracao-ui.*` (painel de geração) é copiado para `dist/` pelo build. Mudou o front? `cd aula-ia && npm run build`
  e commitar `dist/`. Testes: `node aula-ia/tests/test-plano-render.mjs` e `node aula-ia/tests/test-formulario.mjs`.
  JSON/rastreio técnico na tela só com `?depuracao=1` na URL. Recursos: checklist obrigatório (string no backend).
- Registro entre Claude Code, Codex e Claude do chat: `docs/diario_de_bordo.md` (mais novas no topo; escrever uma entrada ao terminar algo).
- Geração: prompt `especialistas-plano-2.3` (PoC07B). Lote do protocolo: `python gerar_lote.py --entradas ../experimentos/geracao/poc07b_entradas.json --limite-diario N` (mesmo limite do app; teste sem rede: `--somente-validar`); medição: `python medir_planos.py --entradas ...`. Resultado 2.2 × 2.3 (n=5): `docs/PoC07D_Resultado_Lote_2_3.md` (branch `poc07d-lote-2-3`).
- Juiz: prompt `juiz-v1.3`, rubrica 0.1, política preliminar. **Não está integrado** ao pipeline, à UI nem ao SQLite.
- Séries com v1.3 **completas** (3 válidos cada; falhas técnicas à parte): controle do plano original = 3; V03 = 3; V04 = 3 (+2 falhas 413);
  V05 = 3 (+1 falha 413); V06 = 3. Níveis mecânicos: V03 parcial 2/ausente 1; V04 parcial 1/ausente 2; V05 plena 3;
  V06 sem pares novos e decisão igual à base 3/3. Tudo provisório, aguardando adjudicação humana.
- A busca de chaves com `findstr` dá falso positivo conhecido em `20261118T023623Z-e8304f3019e7/resultado.json`
  (mensagem de erro cita "GROQ_API_KEY"; sem chave real). Qualquer outro match: parar e avisar o João.
- Achados a adjudicar: o Juiz repete "plano só trabalha Bubble sort" (possível falso positivo curricular) e "ET2 simula uma passagem só";
  na V03 ele acha o defeito mas atribui ao componente `metodologia` em vez de `sequencia`.

## Pendências (ordem sugerida, revista em 25/11 na auditoria)
**Sem congelamento vigente** (o de 19/11 foi reaberto em 25/11). Mudança de código só com aprovação do João, item a item.
1. **Adjudicar o lote 2.3** (`docs/PoC07D_Resultado_Lote_2_3.md`): os 2 H1 da 2.3 parecem falsos positivos da regra; a leitura por plano é opinião.
2. **Decidir o próximo ciclo da geração** (cada item exige pré-registro commitado ANTES de chamar API): regra de medição v2 (negação /
   recurso confirmado) e prompt 2.4 (fidelidade ao tipo de aula, exemplo concreto, evidência não só oral). Feitos: alerta
   habilidade × recursos (PoC 08, RF08) e verificação de acentuação (PoC 10; heurística, não é checagem ortográfica geral).
3. Adjudicação humana do Juiz (V03–V06): ferramenta pronta (`poc05h-adjudicacao`); falta o 2º avaliador e as Fases A e B.
4. Registro de decisões + e-mail ao orientador (pendente de ratificação). Perguntar a data final do TCC.
5. Nova execução real do João para trocar o exemplo da figura `estrutura-plano` (e telas do Cap. 4, se ele quiser).
6. Achados registrados na auditoria e não corrigidos: C1 (reescrita de acento não compara IDs/minutos com a original além do
   validador), C4 (`interrompido` após 15 min), C5 (`--gerador ia` + `--juiz demonstracao`), C9 (503 padrão 0 na classe, 2 no app).
7. Levar `docs/auditoria-25-11` à `main` quando o João pedir. Feitos e retirados da lista: Juiz no pipeline (PoC 08), regeneração com
   as críticas (PoC 10), merge da cadeia na `main` (19/11 e 25/11).
