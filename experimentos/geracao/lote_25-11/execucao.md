# Lote de 25/11/2026 — registro de execução

Pré-registro: `protocolo.md` (commit `637a0db`, antes de qualquer chamada). Executado por Claude Code com autorização do João.

## Preparação
- `git fetch`; base `fix/auditoria-25-11-c1-c4-c5-c9` @ `0f5b8df`; branch `data/lote-25-11`.
- Testes: 532 (1 ignorado), OK. Chaves do Gemini e da Groq: as duas variáveis de ambiente presentes (só verificado `bool`; valores nunca lidos).
- Porta 8000 já estava livre (nenhuma instância do app aberta). Nenhum pedido em andamento no banco.
- Uso antes (21:55 local): 7 gerações, 4 avaliações do Juiz → limites desta execução 17 e 14.
- App: `python app.py --modo lexical --gerador ia --juiz groq --ipv4 --ciclos-juiz 1 --regeneracao informada --limite-diario 17
  --limite-diario-juiz 14` (saída em `aula-ia-backend/local/lote_25-11/servidor.log`, fora do Git; sem chaves).

## Habilidade (regra do protocolo)
Antes das gerações, as candidatas foram conferidas com um banco **temporário** (a busca é lexical, sem API; o banco real não foi
tocado). A 1ª candidata tinha relação com o tema nos 5 cenários e foi a confirmada na interface:
#1 e #2 "Ordenação" → EF08CO03; #3 "Busca binária" → EF08CO03; #4 "Listas" → EF08CO02; #5 → EF08CO10.
Observação: no #5 o tema extraído de "segurança e privacidade na internet" foi **"Segurança e privacidade e internet"** (extração por
regras; a habilidade escolhida está correta). No #4 a interface mostrou o alerta RF08 ("EF08CO02 pede … linguagem de programação, mas
'computadores' não está nos recursos marcados") e permitiu gerar, como previsto.

## Execução (interface real, Playwright + Chrome instalado, script fora do repositório)
| # | Início | Fim | Pedido | Resultado |
|---|---|---|---|---|
| 1 | 21:58:25 | 22:01:05 | `607295ef` | pronto, regenerou |
| 2 | 22:01:27 | 22:02:18 | `837c2e7e` | pronto, favorável na 1ª |
| 3 | 22:02:32 | 22:04:49 | `b67c685a` | pronto, regenerou |
| 4 | 22:04:59 | 22:07:21 | `f388bdd8` | pronto, regenerou |
| 5 | 22:07:40 | 22:09:49 | `5145086d` | pronto, regenerou |

- Nenhuma falha técnica (Gemini ou Groq), nenhuma repetição de cenário, nenhum 429. Um reparo de formato do Juiz (#1, versão 2:
  2 tentativas, a 2ª validou) — previsto no fluxo, não é falha.
- Nenhum plano aprovado; "Gerar novamente" não foi usado. PDFs feitos pela impressão da página (mídia print, A4) **sem aprovar**; o CSS de
  impressão não depende da aprovação, então não foi preciso o PDF em modo de tela. O PDF não tem marca "rascunho" — só o nome do arquivo.
- Uso depois (22:10): 16 gerações, 13 avaliações (9 versões e 9 pareceres deste lote). Não cruzou a meia-noite.

## Desvios do protocolo
- Nenhum desvio de método. Detalhe operacional: o cenário 4 foi disparado em processo desacoplado e acompanhado por um vigia do log
  (sem efeito no pedido). Os nomes das telas seguem o protocolo, com `3b_progresso_regeneracao.png` a mais quando houve regeneração.
