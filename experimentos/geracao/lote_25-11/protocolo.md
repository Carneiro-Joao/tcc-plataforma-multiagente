# Lote de 25/11/2026 — 5 pedidos reais com a IA Juiz (pré-registro)

**Escrito e commitado antes de qualquer chamada de API.** Não será editado depois de ver resultados; desvios vão para
`execucao.md` e para o `resumo.md`.

## Objetivo
Lote **exploratório de demonstração**, não teste de hipótese: rodar a plataforma como o professor rodaria (geração com o Gemini → IA
Juiz automática na Groq → regeneração informada quando o parecer não for favorável) em até 5 pedidos novos, e guardar os artefatos
(planos, pareceres, rastreios, telas, PDFs de rascunho, métricas) para o texto e as figuras do TCC. n = 5, uma execução por cenário:
nada aqui permite afirmar que "o Juiz acerta", que o sistema é "estável" ou que algo foi "validado".

## Versão e configuração
- Código: branch `fix/auditoria-25-11-c1-c4-c5-c9`, commit `0f5b8dfabcc43241822149d652161fc9fd1de354` (correções C1–C9); dados nesta
  branch `data/lote-25-11`. Testes antes do lote: 532 (1 ignorado), OK.
- Geração: `gemini-3.5-flash-lite`, prompt `especialistas-plano-2.3`, reparos 1, HTTP 503 com 2 repetições, timeout 90 s; reescrita
  de acentuação ligada (modo IA; aceita só com IDs/números/vínculos/estrutura iguais — C1).
- Juiz: `openai/gpt-oss-120b` (Groq), `juiz-v1.3`, `rubrica-juiz-0.1`, `politica-juiz-prelim-0.1`, temperature 0, seed 42, reparos 1,
  intervalo de 75 s entre avaliações (120 s depois de HTTP 413), 60 s antes do reparo.
- Fluxo: `--ciclos-juiz 1`, `--regeneracao informada` (`revisao-informada-1.0`).
- Comando: `python app.py --modo lexical --gerador ia --juiz groq --ipv4 --ciclos-juiz 1 --regeneracao informada
  --limite-diario 17 --limite-diario-juiz 14` (porta 8000, banco real `aula-ia-backend/local/consultas.sqlite3`).
- Limites: uso de hoje antes do lote (25/11, 21:55 local) = **7 gerações** e **4 avaliações do Juiz**; limites só desta execução
  = 7 + 10 = **17** e 4 + 10 = **14** (autorização do João; padrão 8 no código não muda). Se cruzar a meia-noite, a contagem recomeça.

## Cenários (nesta ordem; 8º ano; recursos marcados no checklist do formulário)
| # | Tema (frase do professor) | Tipo | Duração | Recursos |
|---|---|---|---|---|
| 1 | quero ensinar ordenação | Aula prática | 50 | projetor, computadores |
| 2 | quero ensinar ordenação | Computação desplugada | 50 | quadro e pincel |
| 3 | busca binária | Computação desplugada | 50 | quadro e pincel, material impresso |
| 4 | listas | Aula teórica | 50 | quadro e pincel, projetor |
| 5 | segurança e privacidade na internet | Projeto | 100 | computadores, internet |

**Regra da habilidade:** confirmar a 1ª candidata da busca por tema. Se ela claramente não tiver relação com o tema, confirmar a 1ª
que tiver e registrar o motivo em `execucao.md`. Tema não reconhecido (HTTP 422) → registrar e passar ao próximo; não inventar tema.

## Execução
- Pela interface real (Playwright + Chrome/Edge instalado, pasta fora do repositório): formulário → Consultar habilidades → confirmar
  → Gerar plano de aula → esperar o fim (sem limite curto; até ~15 min por pedido). Um pedido por vez, sem espera extra.
- Telas: habilidades encontradas, resumo da confirmação, progresso do pedido, parecer da IA Juiz, plano completo. PDF do plano
  entregue **sem aprovar**, pela impressão da página (mídia print, A4), nome terminado em `_rascunho.pdf`.
- Não clicar em "Aprovar plano" nem em "Gerar novamente".
- Falha técnica (Gemini 503/timeout, Groq 400/413/429) = falha técnica, **nunca** parecer. Repetir o mesmo cenário no máximo 1 vez, e
  só se sobrar limite e houver < 5 pedidos válidos. 429 de cota diária → parar e resumir.

## O que será medido (por pedido e por versão, em `metricas.json`, por script, lendo o SQLite só com SELECT)
Tempo; chamadas HTTP; tokens conhecidos; reparos; reescritas de acentuação (aceitas e descartadas, com o motivo, inclusive C1);
campos ainda sem acento (`acentuacao.campos_sem_acentuacao`); entidades HTML no texto (ex.: `&#231;`); soma dos minutos × duração;
recursos do plano × confirmados; decisão da política; notas por critério; falhas por gravidade e componente; modo da regeneração e
críticas usadas; versão entregue e aviso. No resumo: comparação seção a seção entre versões (só fatos) e observações qualitativas
marcadas como "opinião provisória" (fidelidade ao tipo de aula, avaliação só oral, só Bubble sort, aderência à habilidade).
