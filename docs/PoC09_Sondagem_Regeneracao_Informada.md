# PoC 09 — Sondagem: regeneração informada pelas críticas do Juiz (opção C) — pré-registro

**Status:** registrado em 25/11/2026, **antes** de qualquer chamada desta sondagem. Pedido do João ("testar antes de implementar").
É uma **sondagem exploratória**: decide se vale implementar a opção C; não é avaliação para afirmar ganho no TCC. Não altera o app.
Este protocolo não é editado depois de ver resultados; mudou a hipótese → nova versão.

## Pergunta
Quando a IA Juiz não dá parecer favorável, gerar o plano inteiro de novo **passando a cada especialista a sua versão anterior e as
críticas do Juiz** (opção C) produz versões com menos falhas graves do que gerar de novo **sem** as críticas (comportamento atual)?

## Material (já existente, nada é gerado para a 1ª versão)
As 5 primeiras versões reais não favoráveis disponíveis, com o parecer real do Juiz (juiz-v1.3) que receberam:

| # | Plano (prompt 2.3, gemini-3.5-flash-lite) | Geração de origem | Parecer de origem | Falhas graves |
|---|---|---|---|---|
| 1 | Estrutura de Dados · desplugada · 60 | `a3b450f3` | `local/ensaios_juiz/20261119T144542Z-22e0c849d313` | 1 |
| 2 | Listas · teórica · 30 | `f98d522e` | `local/ensaios_juiz/20261119T144703Z-04b72cd5f7c1` | 1 |
| 3 | Ordenação · teórica · 90 | `f67ad3b5` | `local/ensaios_juiz/20261119T144944Z-af30e69d7832` | 1 |
| 4 | Programação · prática · 50 | `d08006bf` | `local/ensaios_juiz/20261119T145105Z-aea4ed435c8c` | 3 |
| 5 | Ordenação · desplugada · quadro e pincel | `a1ddae3e` | tabela `pareceres` do app, 19/11 12:54:56 | 3 |

## Braços (mesma entrada confirmada, mesmo gerador `especialistas-plano-2.3`, mesmo modelo, `--ipv4`, reparos 1, revisão 2)
- **Cego (controle):** gerar o plano inteiro de novo, exatamente como o app faz hoje.
- **Informado (C):** idem, mas a entrada de cada especialista ganha o campo `revisao_pedagogica` (versão
  `revisao-informada-sondagem-0.1`), com: a versão anterior daquele componente, as falhas do Juiz atribuídas a ele (descrição,
  gravidade, critério, correção sugerida), as demais falhas só como contexto e a instrução de corrigir **sem** violar o contexto confirmado
  (recursos, tipo, duração, habilidade). O prompt de sistema e as instruções dos especialistas **não mudam**; o campo vai nos dados.
- Cada versão nova é avaliada uma vez pela IA Juiz na configuração dos experimentos (juiz-v1.3, rubrica 0.1, política prelim 0.1,
  reparos 1, temperature 0, seed 42), com 75 s entre inícios de chamadas.

## Medidas (fixas)
Para cada braço e plano: (a) número de falhas graves (maior/crítica) — comparado com a 1ª versão; (b) decisão da política
(favorável = `aguardando_decisao`); (c) **graves repetidas**: pares (componente, critério) graves da 1ª versão que reaparecem graves;
(d) H1 "material ausente" e H2 "sem acentos" pela regra fixa da PoC07B (`medir_planos.py`); (e) validade no contrato e soma de minutos.
Resultado **descritivo** (contagens x/5). Falha técnica (Gemini 503/timeout, Groq 4xx) é registrada à parte, 1 nova tentativa após 60 s,
e não conta como resultado.

## Hipóteses (exploratórias)
- **S1:** o braço informado tem menos falhas graves somadas que o braço cego.
- **S2:** o braço informado repete menos pares graves da 1ª versão que o braço cego.
- **Efeito colateral a observar:** o braço informado não piora H1 (sugestões do Juiz levando a material fora dos recursos) nem o contrato.

## Limites (declarados antes)
n = 5, uma geração por braço; quem mede é o próprio Juiz (circular: as críticas vêm do mesmo avaliador); o plano 4 (EF08CO01 só com
material impresso) tem conflito habilidade × recursos que nenhuma regeneração resolve. Sem teste estatístico; leitura pedagógica, se
houver, fica "a adjudicar". Teto de chamadas: 14 gerações e 14 avaliações (10 + até 4 novas tentativas cada).

## Execução
`python sondagem_regeneracao_informada.py` (pasta `aula-ia-backend`); resultados brutos em `local/sondagem_c/` (busca de chaves antes de
qualquer `git add -f`). `--somente-validar` roda o fluxo sem rede (gerador e Juiz de demonstração).
