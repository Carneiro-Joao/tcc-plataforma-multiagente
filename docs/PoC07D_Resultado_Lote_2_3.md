# PoC07D — Resultado do lote com o prompt 2.3 (comparação descritiva com a 2.2)

**Status:** evidência provisória (n = 5 por versão, um modelo, uma geração por entrada). Leitura pedagógica = opinião do Claude Code,
**a adjudicar**. O protocolo `docs/PoC07B_Prompt_2_3.md` e o prompt **não** foram editados depois dos resultados.

## Execução
- **Quando:** 18/11/2026, 23:29–23:35 (BRT), autorizado pelo João para esta tarefa. Branch `feat/poc07d-lote-2-3`; ferramentas commitadas
  **antes** das chamadas (`e5fa6d4`).
- **Como:** `python gerar_lote.py --entradas ../experimentos/geracao/poc07b_entradas.json --limite-diario 12` → mesmo caminho do app
  (`consultar → confirmar → gerar`), `gemini-3.5-flash-lite`, `especialistas-plano-2.3`, IPv4, reparos 1, até 2 repetições de 503 por chamada,
  banco `local/consultas.sqlite3`. As 5 habilidades vieram na busca por tema (nenhuma precisou do catálogo). Exportação: `python exportar_planos.py`.
- **Resultado:** 5/5 planos gerados (revisão 1), todos `rascunho`. Tempo por plano: 17–48 s.
- **Falhas técnicas (à parte, não contam como plano):** 1 — linha 3 (Listas), `Gemini HTTP 503: modelo sobrecarregado` após 3 tentativas
  internas; refeita uma vez com consulta nova, 60 s depois, e gerou. Nenhum 429.
- **Limite diário:** 12/12 usados em 18/11 (6 antes do lote + 6 do lote: 5 planos + 1 falha). Uma das 6 anteriores (`49f9631d`, 23:01,
  Ordenação / Computação desplugada / quadro e pincel, prompt 2.3) **não** é linha do protocolo e ficou fora da medição.

## Medição pré-registrada (`python medir_planos.py --entradas ../experimentos/geracao/poc07b_entradas.json`)

| Prompt | n | H1 material ausente | H2 sem acentos | Minutos somam a duração | Válido no contrato |
|---|---|---|---|---|---|
| especialistas-plano-2.2 (18/11, 22:04–22:10) | 5 | 2/5 | 1/5 | 5/5 | 5/5 |
| especialistas-plano-2.3 (18/11, 23:29–23:35) | 5 | 2/5 | 0/5 | 5/5 | 5/5 |

A implementação da regra reproduz a linha de base declarada no protocolo para a 2.2 (H1 2/5, H2 1/5) antes de ver a 2.3.
Planos de 17/11 e o `49f9631d` não entram (filtro pelas 5 entradas exatas).

### H1 por plano (radicais que dispararam a regra)
| Linha | 2.2 | 2.3 |
|---|---|---|
| 1 Ordenação / prática / quadro e pincel | cartao/cartoes (12 menções a "cartões já preparados") | — |
| 2 Ordenação / teórica / projetor, computadores | cartao/cartoes (1, em ADP1) | — |
| 3 Listas / teórica / projetor, computadores, internet | — | — |
| 4 Estrutura de Dados / desplugada / quadro e pincel, material impresso | — | computador: "Resolução colaborativa de problemas **sem uso de computador**" |
| 5 Programação / prática / material impresso | — | alto-relevo/tatil: "apoio visual e **tátil com o material impresso**" |

**Contagem oficial: 2/5 nas duas versões.** Leitura (a adjudicar): as duas ocorrências da 2.3 parecem **falsos positivos da regra**
(uma negação; e "tátil" referindo-se ao próprio material impresso), enquanto as da 2.2 citam um material que não estava nos recursos.
Se a adjudicação confirmar, a 2.3 teria 0/5 citações reais de material ausente contra 2/5 da 2.2 — ainda assim n = 5, sem teste estatístico.
A regra não foi alterada; um refinamento (ignorar negação etc.) seria uma nova versão, pré-registrada antes de outra rodada.

### H2
0/5 na 2.3 contra 1/5 na 2.2. A hipótese já era fraca (base de 1 caso, causa desconhecida); a diferença de 1 plano não permite concluir.

## Contagens exploratórias (NÃO pré-registradas; só para orientar a leitura)

| Linha | Algoritmos citados 2.2 → 2.3 | Linguagem de programação nomeada | Evidências esperadas orais | "o computador exibe" | Erro de digitação visto |
|---|---|---|---|---|---|
| 1 Ordenação prática | Bubble → Bubble | não → não | 2/2 → 1/2 | não → não | — |
| 2 Ordenação teórica | Bubble → Bubble + Quicksort | não → não | 0/2 → 1/2 | **sim** → não | — |
| 3 Listas teórica | — → — | não → não ("sintaxe", "códigos", sem nomear) | 1/2 → 1/2 | não → não | 2.3: "Ouir" (ET1) |
| 4 Estrutura de Dados | — → — | — | 1/2 → 1/2 | não → não | 2.3: "Material Impreso" (título ET2) |
| 5 Programação | — → — | não → não | 2/2 → 2/2 | não → não | — |

"Oral" = a evidência esperada é resposta/explicação oral, verbal ou "em voz alta". Contagem automática por palavra; conferida na leitura.

## Leitura dos 5 planos novos (opinião, a adjudicar)

### 1. Ordenação · Aula prática · 50 min · quadro e pincel (`ordenacao_r1_917c3ba9`)
1. **Em relação à 2.2:** não cita cartões; tudo acontece no quadro (o professor escreve a sequência e faz as trocas).
2. **Igual ou pior:** só Bubble Sort, como na 2.2. Para uma **aula prática**, os alunos ficam mais passivos que na 2.2: só respondem oralmente
   "quais elementos trocar"; quem executa as trocas é o professor (a 2.2 punha os alunos para manipular — os cartões ausentes). Remover o
   material inventado tirou a manipulação e nada a substituiu. A própria metodologia diz "nenhum registro escrito pelos alunos é necessário".
3. **Bom:** fiel aos recursos; adaptações concretas e viáveis (cores e setas no quadro); minutos e IDs coerentes.
4. Ver "Divergências".

### 2. Ordenação · Aula teórica · 90 min · projetor, computadores (`ordenacao_r1_f67ad3b5`)
1. **Em relação à 2.2:** cita Quicksort além do Bubble Sort (o único plano de ordenação, nas duas rodadas, que sai do Bubble Sort);
   não usa mais "o computador exibe a lista ordenada" como evidência; sem cartões na adaptação.
2. **Igual ou pior:** 50 de 90 min são "simulações práticas nos computadores" sem dizer **qual** simulador, site ou programa — numa aula
   marcada como teórica. A evidência EVI2 ("demonstram, através da interação prática nos computadores, a ordenação") continua vaga sobre o
   que o aluno produz. Sem conteúdo concreto (lista de exemplo, passos de Quicksort, pivô).
3. **Bom:** objetivos ligados aos recursos; perguntas orais durante a exposição fazem sentido numa aula teórica.

### 3. Listas · Aula teórica · 30 min · projetor, computadores, internet (`listas_r1_f98d522e`)
1. **Em relação à 2.2:** mais coerente com "teórica": o professor demonstra código projetado e os alunos analisam (na 2.2 os alunos
   manipulavam o ambiente de programação nos computadores).
2. **Igual ou pior:** fala de "sintaxe", "trechos de código" e "linguagem de programação" sem nomear a linguagem nem mostrar um exemplo
   de lista; "coleções de dados da internet" é genérico. As duas evidências são orais. Erro de digitação: "Ouir" (ET1, ação discente).
3. **Bom:** 30 min bem divididos (15 + 15); adaptações usam o projetor para destacar sintaxe — viável com os recursos.

### 4. Estrutura de Dados · Computação desplugada · 60 min · quadro e pincel, material impresso (`estrutura-de-dados_r1_a3b450f3`)
1. **Em relação à 2.2:** estrutura muito parecida (explicação → análise do material em grupos → apresentação no quadro).
2. **Igual ou pior:** **menos concreto** que a 2.2: a 2.2 nomeava "vetores e listas"; a 2.3 fala só em "a estrutura de dados mais adequada"
   sem dizer quais estruturas nem quais problemas o material impresso traz. O conteúdo "sem uso de computador" disparou a regra H1
   (falso positivo, ver acima). Erro de digitação no título da ET2 ("Material Impreso").
3. **Bom:** fiel ao tipo desplugado e aos recursos; trabalho em grupo com apresentação; ADP2 (colega registra no quadro sob orientação verbal
   do estudante) é uma adaptação plausível.

### 5. Programação · Aula prática · 50 min · material impresso · EF08CO01 (`programacao_r1_d08006bf`)
1. **Em relação à 2.2:** praticamente o mesmo plano (recursão: caso base e passo recursivo em material impresso, explicação oral).
2. **Igual ou pior:** continua "Programação sem programação": a EF08CO01 pede "automatizar tais soluções usando uma linguagem de programação",
   e com só material impresso o plano não escreve nem executa código (incompatibilidade habilidade × recursos, já prevista como alerta
   determinístico no protocolo, fora do escopo do prompt). A evidência EVI1 é "**apontar com o dedo** o trecho" — fraca para "construir
   soluções". Ficou **menos concreto** que a 2.2, que trazia os exemplos da própria BNCC (árvore genealógica, tamanho de lista).
   "Aula prática" vira leitura dirigida + discussão.
3. **Bom:** foco correto em recursão (parte da habilidade); sequência caso base → passo recursivo → redução progressiva é didaticamente ordenada.

### Divergências entre planos
- **"Prática" × "teórica" invertidas em Ordenação:** o plano **teórico** (linha 2) tem 50 min de alunos nos computadores; o plano **prático**
  (linha 1) tem alunos só respondendo oralmente enquanto o professor faz as trocas.
- **"Teórica" interpretada de dois jeitos:** Listas (linha 3) mantém os alunos sem computador; Ordenação teórica (linha 2) põe os alunos nos
  computadores. Os recursos marcados (computadores) parecem pesar mais que o tipo de aula.
- **Concretude caiu onde o material é genérico:** linhas 4 e 5 ("material impresso") perderam os exemplos nomeados que a 2.2 tinha.
- **Evidências orais seguem dominantes:** 6 de 10 evidências esperadas na 2.3 são orais (2.2: 6 de 10, pela mesma contagem).

## Limites
- n = 5 por versão, uma amostra de cada; temperatura e sorteio do modelo variam entre execuções; as duas rodadas foram com 1h25 de diferença.
- A regra de H1 é por radical e não entende negação nem sentido; as contagens exploratórias também são por palavra.
- A leitura pedagógica acima não substitui a adjudicação humana; termos como "concreto", "fraco" e "fiel ao tipo" são juízo do revisor.

## Sugestões (não executadas)
1. **Adjudicar** os dois H1 da 2.3 (falso positivo ou não) e registrar.
2. **Nova versão da regra de medição** (pré-registrada antes de nova rodada): ignorar radical em negação ("sem uso de …") e quando qualifica
   um recurso confirmado ("tátil com o material impresso").
3. **Prompt 2.4 (pré-registrar antes):** fidelidade ao tipo de aula (prática = alunos executam; teórica = exposição e análise), exigir ao menos
   um exemplo concreto (lista de valores, nome da linguagem ou da estrutura) e evitar evidência só oral/"apontar". Manter a regra 2.3 de recursos.
4. **Alerta determinístico** habilidade × recursos (EF08CO01 sem computador) e verificação ortográfica simples ("Ouir", "Impreso").
5. Mais de uma geração por entrada antes de comparar versões (variabilidade do modelo).

## Arquivos
- Casos da 2.3 (para teste futuro, após busca de chaves sem achados): `experimentos/geracao/poc07b_planos_2_3/*.json` (5).
- Ferramentas: `aula-ia-backend/gerar_lote.py`, `aula-ia-backend/medir_planos.py`, `experimentos/geracao/poc07b_entradas.json`.
