# PoC 08 — IA Juiz integrada ao fluxo de geração

**Status:** implementado em 19/11/2026 (último dia de desenvolvimento, decisão do João após a reunião com o orientador; pendente de
ratificação). Branch `feat/poc08-juiz-integrado`. Resultados com LLM são **exploratórios** (n pequeno, um modelo por papel):
não permitem concluir que "o Juiz acerta". A decisão final é sempre do professor.

> **Atualização 25/11/2026 (PoC 10):** este documento descreve a regeneração **cega** da PoC 08 (o plano inteiro gerado de novo sem as
> críticas). Desde a PoC 10 o padrão é a regeneração **informada**: o plano inteiro continua sendo gerado de novo, mas cada especialista
> recebe a sua versão anterior e as críticas do Juiz. O comportamento abaixo continua disponível com `--regeneracao cega`. Detalhes:
> `docs/PoC10_Regeneracao_Informada_e_Acentuacao.md`. O corpo deste documento ficou como registro histórico.

## O que foi integrado
O Juiz deixou de ser só um experimento (`ensaio_juiz.py`) e virou uma **etapa automática** de cada pedido de plano:

```
Gerar (5 especialistas, Gemini) → IA Juiz avalia (Groq) → decisão pela política
   favorável ("aguardando_decisao")            → entrega o plano com o parecer
   "em_correcao" ou "revisao_necessaria"       → gera o plano INTEIRO de novo (nova revisão) → Juiz avalia de novo
                                                  (até --ciclos-juiz, padrão 1; 0 = não regenera)
   continua não favorável                      → entrega a versão com MENOS falhas graves (maior/crítica; empate = a mais recente), com aviso
   falha técnica do Juiz (400/413/429/recusa)  → entrega o plano com "avaliação indisponível" (nunca conta como parecer)
Professor: Aprovar plano → Baixar PDF   |   ou Gerar novamente (repete o fluxo inteiro, com Juiz)
```

| Parte | Arquivo |
|---|---|
| Orquestração, tabelas `pedidos` e `pareceres`, limites, escolha da versão entregue | `aula-ia-backend/servico.py` (`gerar`, `_gerar_uma`, `_avaliar`, `escolher_entrega`) |
| Adaptadores do Juiz (Groq real e demonstração) e rótulos | `aula-ia-backend/juiz_servico.py` |
| Opções `--juiz`, `--ciclos-juiz`, `--limite-diario-juiz` e mensagens ao iniciar | `aula-ia-backend/app.py` |
| Parecer real gravado usado no modo demonstração | `experimentos/juiz/demonstracao/parecer_controle_v13.json` (fonte: `aula-ia-backend/local/ensaios_juiz/20261117T193100Z-60bc40e3bbad/resultado.json`) |
| Tela: progresso do pedido, painel "Avaliação da IA Juiz", Aprovar / Gerar novamente / Baixar PDF | `aula-ia/public/geracao-ui.js`, `aula-ia/public/geracao-ui.css` |
| Testes | `aula-ia-backend/tests/test_juiz_integrado.py`, `aula-ia/tests/test-juiz-render.mjs` |

**Configuração do Juiz** (igual à dos experimentos V03–V06): `openai/gpt-oss-120b` na Groq, prompt `juiz-v1.3`, `rubrica-juiz-0.1`,
`politica-juiz-prelim-0.1`, `--reparos 1`, temperature 0, max_completion_tokens 8192, reasoning_effort medium, seed 42, timeout 90 s
(`juiz_servico.PARAMETROS_EXPERIMENTOS`, conferido por teste).

**Rastreabilidade:** todas as gerações e todos os pareceres de um pedido ficam no SQLite (`geracoes` com `pedido_id`, `ciclo`, `entregue`;
`pareceres` com `estado` ok/falha, `proximo_estado`, versões e o JSON completo). A geração entregue é marcada (`entregue = 1`).
Bancos antigos são migrados ao abrir (colunas novas, sem perder dados).

**Limites diários** (proteção de gasto): geração continua com `--limite-diario` (padrão 8; regenerações contam); Juiz com
`--limite-diario-juiz` (padrão 8, contando falhas). Limite atingido no meio do pedido → entrega o que tiver, com aviso, sem nova chamada.
Intervalo de 75 s entre os inícios de chamadas reais ao Groq (120 s depois de HTTP 413), em `JuizGroq`, com lock.

## Como rodar (Windows, pasta `aula-ia-backend`)
```
python app.py --modo lexical --gerador ia --ipv4 --abrir                  (Gemini + Juiz Groq se GROQ_API_KEY estiver definida)
python app.py --modo lexical --gerador ia --ipv4 --ciclos-juiz 0          (Juiz avalia, mas não regenera)
python app.py --modo lexical --gerador demonstracao --juiz demonstracao --porta 8001 --temporario   (plano B, sem rede)
```
Sem `GROQ_API_KEY` o Juiz fica desligado e o terminal avisa; os planos saem com "avaliação não realizada".
JSON técnico do plano e do parecer na tela: acrescente `?depuracao=1` ao endereço.

## Verificação sem rede
- 34 testes novos do fluxo (favorável na 1ª; não favorável → regenera → favorável; não favorável duas vezes → a melhor com aviso; empate;
  crítica; falha técnica do Juiz; limite do Juiz; limite de geração no meio; `--ciclos-juiz 0`; Juiz desligado; migração; app.py).
  Suíte: 469 testes OK, também com `python -S` (`python relatorio_testes.py`: RESULTADO: OK).
- Mutação manual sem bytecode: 46 mutantes em `servico.py`, `juiz_servico.py`, `app.py` e `geracao-ui.js`, **0 sobreviventes**.
- Playwright de ponta a ponta com `--gerador demonstracao --juiz demonstracao`: progresso → plano avaliado → aprovar → Baixar PDF, sem erro
  no console; impressão com o parecer resumido (decisão + notas). Capturas em `aula-ia-backend/local/capturas_poc08/` (fora do Git).
- Impressão (PA-2, "página em branco no fim"): **não reproduzida** no Chrome headless com 3 planos reais (texto extraído por página com
  pdf.js: nenhuma página vazia, antes e depois). Correção preventiva: sem altura mínima de tela e sem margem final na impressão.

## Execução real (19/11/2026, autorizada pelo João para esta etapa)

### a) Juiz sobre os 5 planos da 2.3 (`ensaio_juiz.py avaliar --versao-prompt juiz-v1.3 --reparos 1`, pausa de 75 s)
5 chamadas, **5 pareceres válidos, 0 falhas técnicas**. Código no commit `c40ada6`, árvore limpa. Tempo por avaliação: 5,3–8,2 s;
6.804–7.637 tokens. Notas: AC aderência curricular, AO alinhamento dos objetivos, CM coerência metodológica, VI viabilidade,
AA avaliação da aprendizagem, IN inclusão.

| Plano (2.3) | Decisão (política) | Notas | Críticas maior/crítica (resumo do texto do Juiz) | Resultado bruto |
|---|---|---|---|---|
| Ordenação · prática · 50 · quadro e pincel | **aguardando_decisao** (favorável) | AC3 AO3 CM3 VI3 AA2 IN3 | nenhuma (1 menor: critérios sem indicadores claros) | `20261119T144824Z-cb005eb2b2a7` |
| Ordenação · teórica · 90 · projetor, computadores | em_correcao | AC2 AO3 CM3 VI3 AA2 IN3 | objetivos: foca só em ordenação, sem outras manipulações de lista da EF08CO03 | `20261119T144944Z-af30e69d7832` |
| Listas · teórica · 30 · projetor, computadores, internet | em_correcao | AC1 AO2 CM3 VI3 AA2 IN3 | objetivos: a habilidade pede criar soluções com listas; o plano fica na explicação e em respostas orais | `20261119T144703Z-04b72cd5f7c1` |
| Estrutura de Dados · desplugada · 60 · quadro, material impresso | em_correcao | AC3 AO3 CM3 VI3 AA2 IN3 | avaliação: instrumentos sem rubrica ou critérios de desempenho | `20261119T144542Z-22e0c849d313` |
| Programação · prática · 50 · material impresso | em_correcao | AC1 AO3 CM2 VI3 AA2 IN3 | objetivos: sem construção recursiva nem linguagem (EF08CO01); metodologia: "aula prática" só com leitura; critério de OBJ2 vago | `20261119T145105Z-aea4ed435c8c` |

Pastas em `aula-ia-backend/local/ensaios_juiz/` (commitadas com `git add -f` depois da busca de chaves; só o falso positivo conhecido
`20261118T023623Z-e8304f3019e7`). Leitura (exploratória, a adjudicar): as críticas graves coincidem com achados da revisão humana da
PoC07D (Programação sem programação; "aula prática" sem prática; plano de ordenação restrito), mas isso não mede acerto — n = 5, sem
gabarito independente. A aderência curricular baixa (AC1) em Listas e Programação também pode refletir o recorte de recursos marcado
pelo professor, não só o plano.

### b) Pedidos de ponta a ponta pela interface (Gemini + Groq)
| Pedido | Resultado | Tempo total | Etapas vistas na tela | Regeneração |
|---|---|---|---|---|
| Ordenação · prática · 50 · quadro e pincel · EF08CO03 | plano entregue, **Favorável** (6 notas 3, 0 críticas) | **49 s** (geração 43,3 s + Juiz) | Gerando plano… → IA Juiz avaliando… | não foi necessária |
| Programação · prática · 50 · material impresso · EF08CO01 | **falha técnica** do Gemini (timeout de leitura), 2 tentativas (11:53 e 11:56) | 90 s e 139 s até a falha | Gerando plano… | não chegou ao Juiz |

**Falhas técnicas à parte:** nas duas tentativas do 2º pedido o Gemini estourou o tempo de leitura (90 s por chamada) em etapas diferentes
(`objetivos`; depois `avaliacao_final`). No mesmo dia houve outros 2 timeouts às 10:33 e 10:34 (`objetivos`, `adaptacao`): **4 de 8 gerações
de 19/11 terminaram em timeout**, um problema de latência do provedor, não de contrato. A falha é registrada, conta no limite diário
e não vira plano nem parecer; a tela mostra a mensagem e mantém o pedido. O limite de geração do dia (8/8) acabou, então **o caminho de
regeneração com chamadas reais não foi observado**; ele está coberto pelos testes sem rede e pelo modo demonstração (que, com o parecer
gravado `em_correcao`, regenera uma vez e entrega a versão com menos falhas graves).

## Correção após uso real (19/11/2026, tarde) — `feat/poc08b-pausa-reparo-juiz`
Uso do João com `--limite-diario 38 --limite-diario-juiz 31`: num pedido (Listas · teórica · projetor, computadores) o Groq rejeitou o
parecer por formato (HTTP 400 `json_validate_failed`: `componente` fora da lista permitida) e o **reparo** foi enviado na mesma hora;
como cada avaliação usa ~6 mil tokens e o plano gratuito do Groq permite 8.000 tokens/minuto, o reparo levou **HTTP 429** ("Used 4399,
Requested 5918") e o plano saiu com "avaliação indisponível". **Correção:** no app, espera de 60 s antes do reparo
(`juiz_servico.PAUSA_ANTES_DO_REPARO_S`, via `avaliar_plano(..., antes_do_reparo=...)`). Prompt, modelo, rubrica, política e `reparos 1`
não mudaram; o `ensaio_juiz.py` (experimentos) continua com reparo imediato. 7 testes novos (`tests/test_pausa_reparo.py`), 7 mutantes,
0 sobreviventes; suíte 484 OK (também `-S`).
No mesmo uso, outro pedido (Ordenação · desplugada) teve a 1ª versão "Com ressalvas" (3 falhas graves) e a regeneração falhou por
**Gemini 503**; o app entregou a 1ª versão com o aviso "A nova versão falhou tecnicamente" (o Juiz avaliou uma vez só).
Geração em 19/11 até 13:22: 12, das quais 6 com falha técnica do Gemini (4 timeouts, 2× 503).

## Correção: intervalo mínimo entre chamadas (19/11/2026) — `feat/poc08c-intervalo-juiz`
O intervalo entre avaliações reais ficou em `juiz_servico.JuizGroq`: **75 s entre os inícios** de chamadas ao Groq no mesmo processo
(120 s depois de HTTP 413), protegido por lock (o `ThreadingHTTPServer` atende pedidos em paralelo); o reparo mantém 60 s e conta como
última chamada. Durante a espera o pedido fica `aguardando_juiz` e a tela mostra "Aguardando a cota da IA Juiz…". Substitui a pausa que
estava em `servico._avaliar` (contada do fim da chamada, sem lock). Configuração do Juiz inalterada. Testes: `tests/test_intervalo_juiz.py`.

## Limites conhecidos
- O Juiz avalia o plano inteiro e o fluxo regenera o plano inteiro: as críticas do Juiz **não** são usadas para corrigir componentes
  (trabalho futuro, exige prompt novo e pré-registro).
- A política `politica-juiz-prelim-0.1` não foi validada empiricamente; a adjudicação humana das séries V03–V06 segue pendente.
- Timeout de 90 s por chamada ao Gemini não foi alterado (versões e parâmetros congelados); em horários de alta demanda o pedido pode falhar.
- O pedido roda dentro da requisição HTTP (até ~4 min); fechar o app no meio deixa o pedido "interrompido" (tratado após 15 min).
