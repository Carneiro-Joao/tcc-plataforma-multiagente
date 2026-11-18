# Guia da adjudicação humana (séries V03–V06 do Juiz)

A classificação mecânica (`analisar_serie.py`) é provisória: ela olha IDs, critério, componente e gravidade, mas **não lê o sentido**
do texto. A adjudicação humana diz (1) se as críticas do Juiz procedem e (2) se ele detectou o defeito inserido. Sem ela, nenhuma
conclusão sobre o Juiz deve ir ao TCC como resultado.

## O que é avaliado (5 planos, 39 críticas, 12 pareceres)
- **Fase A (cega)** — 2 avaliadores, independentes, sem saber qual plano é de qual variante:
  - *Etapa 1:* cada um dá **a própria nota 0–3** nos 6 critérios da rubrica para cada plano (30 notas), antes de ver o Juiz.
  - *Etapa 2:* cada um julga as **39 críticas** do Juiz: procede / em parte / não procede / não sei; gravidade adequada?; componente certo?
- **Fase B (informada)** — depois da A, mostra o defeito inserido e pergunta se cada um dos 12 pareceres o detectou
  (V03–V05) ou se reagiu à reformulação neutra (V06). Pode ser feita só pelo João, e depois por quem quiser.
- **Comparação** — abre os dois arquivos, mostra concordância e kappa, e organiza o **consenso** nas divergências.

## Passo a passo do João
1. Na pasta `aula-ia-backend` (com os ensaios em `local/ensaios_juiz`):
   `python adjudicacao.py` → cria `local/adjudicacao/` com 3 páginas e a `chave_de_codigos.json`. Não sobrescreve nada.
2. Dê ao 2º avaliador **somente** `adjudicacao_A_cega.html` (por e-mail, pendrive etc.; abre em qualquer navegador, offline).
   **Não envie** a chave nem a Fase B.
3. Você faz a Fase A **no mesmo arquivo**, sem combinar nada com ele. Cada um baixa o seu `.json` no fim.
4. Só depois de ambos terminarem a A: você faz a Fase B (`adjudicacao_B_informada.html`).
5. Abra `adjudicacao_comparar.html`, carregue os dois `.json` da Fase A; veja concordância e resolva as divergências
   (consenso + justificativa). Baixe `adjudicacao_A_consenso.json`. Divergência sem acordo = "sem consenso (3ª opinião)".
6. Guarde em `experimentos/juiz/adjudicacao/`: os `.json` dos avaliadores, o consenso e a `chave_de_codigos.json`
   (a chave só **depois** de os dois terminarem a Fase A; antes disso ela revela as variantes).
7. Análise: `python concordancia.py avaliador1.json avaliador2.json` imprime o resumo no terminal.

## Como julgar "a crítica procede?"
- Julgue **contra o plano e o contexto confirmado** (recursos, tempo, habilidade), não contra o seu gosto.
- *Procede* = o problema existe como descrito. *Em parte* = existe, mas exagerado, impreciso ou mal localizado.
  *Não procede* = o plano não tem o problema (ou o Juiz exigiu algo que a habilidade não pede). *Não sei* = fora da sua competência.
- *Gravidade:* **crítica** = plano inadequado sem revisão humana; **maior** = compromete o critério, corrigível refazendo o componente;
  **menor** = melhoria desejável.
- *Componente:* é o trecho do plano onde o problema está (objetivos, avaliação preliminar, metodologia, sequência, avaliação final, adaptações).
- Ao dar a **sua** nota na Etapa 1, use a âncora de cada critério (0 inadequado · 1 insuficiente · 2 com ressalvas · 3 adequado).

## Quem pode ser o 2º avaliador
Alguém que **entenda de ensino e de Computação** (professor/licenciando de Computação ou Pedagogia com noção de algoritmos). Não precisa
conhecer o projeto. Idealmente alguém que **não tenha visto os resultados do Juiz** e que não escreva o prompt do Juiz.
Se o orientador (ou outro docente) puder, ele entra como **3º avaliador** só nas divergências sem consenso.

## Limites (escrever no TCC)
- 2 avaliadores e 39 críticas: o kappa é instável; relate a concordância simples e o kappa juntos, com as contagens.
- João conhece o experimento; a cegueira real é a do 2º avaliador. Ainda assim, a Fase A embaralha e usa códigos opacos.
- Todos os planos derivam do **mesmo plano-base** e de uma habilidade (EF08CO03): não generaliza para outras habilidades.
- Se quase todas as críticas caírem numa mesma resposta, o kappa fica baixo mesmo com concordância alta (paradoxo da prevalência).
- A Fase B não é cega por construção (o avaliador sabe o defeito): serve para classificar detecção, não para medir qualidade pedagógica.
- Os pareceres usados são só os **válidos** de `juiz-v1.3`; falhas técnicas (413, 429, chave ausente) ficam fora.

## Arquivos
`adjudicacao.py` (gera) · `adjudicacao_web.py` (páginas) · `concordancia.py` (kappa em Python; a página tem a mesma conta em JavaScript,
e os testes comparam as duas).
