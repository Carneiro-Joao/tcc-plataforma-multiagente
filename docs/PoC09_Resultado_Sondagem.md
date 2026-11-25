# PoC 09 — Resultado da sondagem: regeneração cega × informada pelas críticas do Juiz

**Protocolo (pré-registrado antes das chamadas, commit `1e1c096`):** `docs/PoC09_Sondagem_Regeneracao_Informada.md` — não editado.
**Execução:** 25/11/2026, 16:20–16:55 (BRT), autorizada pelo João. `gemini-3.5-flash-lite` (`especialistas-plano-2.3`), Juiz `juiz-v1.3`
na configuração dos experimentos. 11 gerações e 11 avaliações (teto 14/14). Brutos: `experimentos/geracao/poc09_sondagem_c/`
(cópia de `aula-ia-backend/local/sondagem_c/20261125T192047Z/`; busca de chaves sem achados).
**Natureza:** exploratória (n = 5, uma geração por braço, o próprio Juiz mede). Serve para decidir se vale implementar a opção C.

## Medidas fixas (contagens)
| Braço | Planos avaliados | Falhas graves (soma) | Favoráveis | Graves repetidas da 1ª versão | H1 material ausente | H2 sem acento | Contrato ok | Falhas técnicas |
|---|---|---|---|---|---|---|---|---|
| 1ª versão (referência) | 5 | 9 | 0/5 | — | — | — | 5/5 | — |
| Cego (como o app faz hoje) | 5/5 | 8 | 1/5 | 4 | 0/5 | 5/5 | 5/5 | 1 (Gemini 503, refeita) |
| Informado (opção C) | 5/5 | 5 | 2/5 | 2 | 1/5* | 4/5 | 5/5 | 1 (Groq 413, refeita) |

\* O único H1 do braço informado é o falso positivo de negação já conhecido ("Resolução colaborativa de problemas **sem uso de**
computador", mesmo texto da 1ª versão; ver PoC07D). Pela regra fixa conta; na leitura, nenhum plano informado citou material fora dos recursos.

**S1** (menos graves no informado): 5 × 8 — a favor, sem teste estatístico. **S2** (menos graves repetidas): 2 × 4 — a favor.
**Efeito colateral:** H1 sem piora real; contrato 5/5 nos dois braços.

## Por plano (falhas graves: 1ª → cego / informado)
| # | Plano | 1ª | Cego | Informado | Leitura (a adjudicar) |
|---|---|---|---|---|---|
| 1 | Estrutura de Dados · desplugada | 1 | 3 (em_correcao) | **0 (favorável)** | A crítica da 1ª (instrumentos sem rubrica) foi resolvida no informado; o cego a repetiu e ganhou 2 novas. |
| 2 | Listas · teórica | 1 | 2 (revisão recomendada; 1 crítica) | 3 (em_correcao) | Nenhum braço resolve: a habilidade pede criar soluções com listas e a aula é marcada como **teórica**. Conflito de entrada. |
| 3 | Ordenação · teórica · 90 | 1 | **0 (favorável)** | 1 (em_correcao) | O informado acatou a crítica (incluiu inserção, remoção e busca), mas o Juiz achou a ET2 longa demais para 4 algoritmos (viabilidade). O cego saiu favorável "por sorteio". |
| 4 | Programação · prática · só material impresso | 3 | 2 (revisão recomendada; 1 crítica) | 1 (em_correcao) | O informado corrigiu "aula prática sem prática" e o critério vago; sobra só a falha que nenhuma regeneração resolve (EF08CO01 pede linguagem de programação e não há computador). |
| 5 | Ordenação · desplugada · quadro e pincel | 3 | 1 (em_correcao) | **0 (favorável)** | As 3 críticas (ET2 só observação; OBJ2 sem prática; instrumentos sem critério) foram resolvidas no informado. |

As falhas graves que restaram no braço informado concentram-se em **conflitos da própria entrada** (habilidade × tipo de aula em #2;
habilidade × recursos em #4) e num efeito colateral (#3: acatar a crítica tornou a etapa longa). Isso reforça o alerta determinístico
habilidade × recursos/tipo, que a regeneração não substitui.

## Achado à parte: Gemini sem acentuação (independente da opção C)
Nos dois braços, 9 de 10 planos tiveram campos longos sem nenhum acento ("sera", "explicacao", "ordenacao"). Nos planos reais do app:
até 19/11, de 0 a 3 campos longos sem acento por plano; em 23/11, 2–5; no plano de 25/11 16:01, **16 de 19**. Prompt e código são os
mesmos (a 2.3 pede acentuação correta) — indica mudança de comportamento do provedor/modelo. O Juiz não penaliza acentuação (as notas não
mudam por isso). Afeta a apresentação dos planos gerados a partir de 23/11.

## Limites
n = 5, uma amostra por braço; variação do modelo pode explicar parte da diferença (o cego teve um favorável "por sorteio"); quem mede é
o próprio Juiz e as críticas vêm dele (circularidade); no braço informado o especialista recebe também a sua versão anterior, então o
efeito é de "críticas + versão anterior", não só das críticas. Para afirmar ganho no TCC seriam necessárias mais repetições por plano
e leitura humana de amostra.

## Leitura para a decisão
Sinal provisório **a favor da opção C**: menos falhas graves (5 × 8), mais favoráveis (2 × 1), menos críticas repetidas (2 × 4), sem
material fora dos recursos e sem quebrar o contrato, com o mesmo número de chamadas. Os casos que não melhoraram são conflitos de entrada,
que pedem alerta ao professor, não mais regeneração.
