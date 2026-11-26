# Lote de 25/11/2026 — resumo (5 pedidos reais com a IA Juiz)

**Natureza:** lote exploratório de demonstração (pré-registro `protocolo.md`, commit `637a0db`), n = 5, uma execução por cenário.
Nada aqui mostra que "o Juiz acerta", que o sistema é "estável" ou que algo foi "validado" (regra 8 do `CLAUDE.md`).
**Código:** `fix/auditoria-25-11-c1-c4-c5-c9` @ `0f5b8df` · Gemini `gemini-3.5-flash-lite` (`especialistas-plano-2.3`) · Juiz
`openai/gpt-oss-120b` (`juiz-v1.3`, `rubrica-juiz-0.1`, `politica-juiz-prelim-0.1`) · `--ciclos-juiz 1 --regeneracao informada`.
**Execução:** 25/11, 21:58–22:10, pela interface real (Playwright + Chrome). Detalhes e desvios: `execucao.md`.

## 1. Por pedido
Rótulos: Favorável = `aguardando_decisao`; Com ressalvas = `em_correcao`; Revisão recomendada = `revisao_necessaria`. "Graves" = maior + crítica.

| # | Cenário | Habilidade | Versões | Juiz na v1 | Juiz na v2 | Entregue | Aviso | Reescritas de acento (v1 / v2) | Tempo | Falhas técnicas |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Ordenação · prática · 50 · projetor, computadores | EF08CO03 | 2 | Com ressalvas · 3 graves | Com ressalvas · 2 graves (+1 menor) | v2 | sim (nenhuma favorável) | 2 / 2 | 157 s | 0 |
| 2 | Ordenação · desplugada · 50 · quadro e pincel | EF08CO03 | 1 | **Favorável** · 0 | — | v1 | — | 3 / — | 49 s | 0 |
| 3 | Busca binária · desplugada · 50 · quadro e pincel, material impresso | EF08CO03 | 2 | Com ressalvas · 2 graves (+1 menor) | **Favorável** · 0 | v2 | — | 3 / 1 | 135 s | 0 |
| 4 | Listas · teórica · 50 · quadro e pincel, projetor | EF08CO02 | 2 | Revisão recomendada · 3 graves (1 crítica) | Com ressalvas · 1 grave | v2 | sim (nenhuma favorável) | 1 / 1 | 141 s | 0 |
| 5 | Segurança e privacidade · projeto · 100 · computadores, internet | EF08CO10 | 2 | Com ressalvas · 1 grave (+1 menor) | **Favorável** · 0 | v2 | — | 2 / 1 | 127 s | 0 |

Tempo = da tela "Gerar plano de aula" até o fim do pedido (inclui as esperas de 75 s da cota do Juiz).

**Críticas principais (texto curto do parecer):**
- #1 v1: F1 conteúdos/objetivos só BubbleSort (outros algoritmos da EF08CO03 omitidos); F2 objetivo geral × específicos desalinhados;
  F3 critérios de avaliação vagos. v2: F1 "só BubbleSort" de novo; F2 critério de EVI2 ("em até cinco passos lógicos") impreciso; F3 (menor) INS2 sem rubrica.
- #2 v1: nenhuma falha.
- #3 v1: F1 não contempla a execução completa da busca binária; F2 objetivos cobrem só as partes iniciais; F3 (menor) sem fechamento. v2: nenhuma falha.
- #4 v1: F1 (crítica) nenhuma atividade cria/programa solução com listas, como pede a EF08CO02; F2 objetivos sem criação de solução;
  F3 critérios genéricos. v2: F1 objetivos usam "Desenvolver"/"Implementar" (sugerem algoritmo codificado), sem correspondência na aula.
- #5 v1: F1 critérios genéricos, sem níveis de desempenho; F2 (menor) 50 min para explorar as configurações pode ser pouco. v2: nenhuma falha.

**Contagens (só o que o Juiz mediu):** 4 de 5 primeiras versões não favoráveis (9 graves). Depois da regeneração informada: 2 de 4
favoráveis, 3 graves no total (#1 3→2, #3 2→0, #4 3→1, #5 1→0). Mesma ressalva da PoC 09: quem critica e quem mede é o mesmo Juiz.

## 2. Regeneração informada (4 pedidos)
Todos registraram `regenerando` com `modo: informada`, `revisao-informada-1.0`; nas versões 2, as 6 chamadas de especialista tiveram
`revisao_pedagogica`. Comparação v1 → v2 seção a seção (só fatos; detalhes em `metricas.json` → `diferencas_v1_v2`):

| # | Críticas usadas | Seções que mudaram | IDs | Minutos das etapas |
|---|---|---|---|---|
| 1 | F1, F2, F3 | conteúdos (3º item: "Manipulação de listas em computadores" → "Simulação e execução de algoritmos de ordenação em listas"), objetivo geral, texto dos objetivos, metodologia, títulos/textos das etapas, avaliação | iguais (OBJ1–2, ET1–2, EVI1–2, INS1–2, ADP1–2) | 20/30 → 20/30 |
| 3 | F1, F2, F3 | conteúdos (3 → 4 itens), objetivo geral, objetivos (+OBJ3 "concluir… localizar o alvo ou determinar a ausência"), metodologia, etapas (+ET3 "Execução completa e fechamento"), avaliação (+EVI3, +INS3), texto das adaptações | +OBJ3, +ET3, +EVI3, +INS3 | 25/25 → 15/20/15 |
| 4 | F1, F2, F3 | conteúdos (+"Uso de recursão…"), objetivo geral, texto dos objetivos ("Desenvolver um algoritmo…", "Implementar a solução… recursão"), metodologia, etapas (ET2 "Desenvolvimento do Algoritmo com Listas e Recursão"), avaliação | iguais | 25/25 → 15/35 |
| 5 | F1, F2 | etapas (2 → 4: exploração, aprofundamento, discussão, síntese), avaliação, texto das adaptações; conteúdos, objetivos e metodologia **iguais** | +ET3, +ET4 | 50/50 → 25/25/25/25 |

## 3. Checagens mecânicas (todas as 9 versões)
- **Acentuação:** 16 reescritas, **todas aceitas** (nenhuma descartada; nenhum descarte por C1 — IDs/números/vínculos/estrutura).
  `acentuacao.campos_sem_acentuacao` = 0 em todas as versões. **Mas** sobraram títulos curtos sem acento no #3 (v1: 2; v2: 3 — ex.:
  "Introducao ao Conceito e Elemento Central", "Execucao Completa e Fechamento da Busca Binaria"): o detector só olha campos com mais
  de 60 caracteres, então títulos de etapa escapam. Os demais campos sem acento são o nome do arquivo `BNCCComputacao.pdf` e os hashes.
- **Entidades HTML** (`&#231;` etc.): nenhuma.
- **Soma dos minutos = duração:** 9/9.
- **Recursos do plano = confirmados:** 9/9 (cópia exata). Nenhum plano cita material fora da lista (varredura de cartões, papel, folhas,
  fichas, celular, slides, lápis etc.); o #4 cita "código" 1–2 vezes, sem computador.
- **Chamadas:** Gemini 70 requisições HTTP (54 de especialistas + 16 reescritas; 0 reparos de contrato, 0 repetições de 503), ~118 mil
  tokens; Juiz 9 pareceres em 10 requisições (1 reparo de formato no #1 v2), ~62 mil tokens.

## 4. Observações qualitativas — **opinião provisória** (leitura de Claude Code, sem adjudicação humana)
- **Fidelidade ao tipo de aula:** #1 (prática) usa os computadores na ET2; #2 e #3 (desplugadas) ficam no quadro e no material impresso;
  #5 (projeto) usa computadores e internet nas etapas. O #4 (teórica, sem computadores) é o conflito de entrada já conhecido: a EF08CO02
  pede linguagem de programação; o alerta RF08 apareceu na tela. Ao acatar a crítica, a v2 passou a prometer "desenvolver/implementar"
  um algoritmo, mas a atividade continua oral no quadro/projetor — o próprio Juiz apontou isso. A regeneração não resolve conflito de entrada.
- **Avaliação só oral:** predominante. #2, #3 e #4 avaliam por perguntas e explicações orais; #1 e #5 combinam observação na tela com
  arguição/debate oral. Nenhum instrumento escrito ou produto entregue pelos alunos nas versões entregues.
- **Só Bubble sort:** #1 e #2 trabalham só o BubbleSort. O Juiz criticou isso no #1 (duas versões) e não no #2 (favorável) — mesmo
  tema e habilidade, tipos de aula diferentes; mostra a variação do Juiz diante de uma escolha parecida. Segue como possível falso
  positivo curricular a adjudicar.
- **Aderência à habilidade:** #3 v2 cobre a execução completa da busca binária (início, descarte de metades, alvo ou ausência);
  #5 trabalha configurações de privacidade, riscos e medidas de proteção, coerente com a EF08CO10.

## 5. Uso dos limites
| | Antes (21:55) | Depois (22:10) | Limite desta execução |
|---|---|---|---|
| Gerações com IA (cada versão conta) | 7 | 16 | 17 |
| Avaliações reais do Juiz | 4 | 13 | 14 |
Padrão do código (8/8) não foi alterado; limites subidos só na linha de comando desta execução. Não cruzou a meia-noite.
Desvios do protocolo: nenhum de método (ver `execucao.md`).

## 6. Arquivos (`experimentos/geracao/lote_25-11/`)
- `protocolo.md` (pré-registro), `execucao.md`, `resumo.md`, `metricas.json` (por pedido e por versão).
- `pedido_<id8>.json` × 5: consulta, pedido (estado, histórico, aviso, versão entregue) e todas as versões com plano, rastreio e pareceres completos.
- `pedido_<id8>/` × 5: `1_habilidades.png`, `2_confirmacao.png`, `3_progresso.png`, `3b_progresso_regeneracao.png` (quando regenerou),
  `4_parecer_juiz.png`, `5_plano_completo.png`, `plano_rascunho.pdf` (plano entregue, **não aprovado**), `execucao.json`.
- `planos_ia/` × 9: saída de `exportar_planos.py` só das versões deste lote.
- Fora do Git: `aula-ia-backend/local/lote_25-11/` (bruto, `servidor.log`, exportação completa).
