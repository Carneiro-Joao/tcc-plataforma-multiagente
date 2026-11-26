# Estado do sistema AulaIA (congelado em 26/11/2026, código `c1ef4f8`)

Inventário técnico para a escrita do TCC. Só fatos verificáveis; cada número indica de onde vem. Referência: **`main` com a tag `tcc-congelado-26-11`**, cujo código é o do commit `c1ef4f8` (branch `fix/acento-misto-e-textos-interface`),
usado na execução do caso-base de 26/11 (pedido `3bf9f2c6`, `experimentos/geracao/caso_base_26-11/`). Congelamento decidido pelo João
em 26/11; o de 19/11 tinha sido reaberto em 25/11 para as PoCs 10 e 11.
**25/11/2026 (PoC 10, autorizada pelo João):** a regeneração passou a usar as críticas do Juiz e a geração ganhou verificação de
acentuação. O que mudou e a lista de ajustes no texto: `docs/PoC10_Regeneracao_Informada_e_Acentuacao.md`.
**25/11/2026 (PoC 11):** acento verificado também em campos
curtos (títulos) e recomendação ao professor junto do plano quando a habilidade pede programação sem computador ou em aula teórica.
Lista de ajustes no texto: `docs/PoC11_Acento_Curto_e_Recomendacao.md` §6.
**26/11/2026 (ajuste antes do congelamento, `c1ef4f8`):** `deteccao-acentuacao-1.2` (campo misto: palavra inequívoca sem acento num campo
que tem outros acentos), texto "Nª versão sem parecer favorável" no lugar de "não aprovada pelo Juiz", selo "Versão de demonstração"
removido do cabeçalho.
Requisitos, regras e diagramas finais: `docs/especificacao/AulaIA_Especificacao_v2.4.md` (v2.3 e v2.2 são histórico) e `docs/diagramas/diagramas-finais.md`.
Auditoria de 25/11 (documentação × código): `docs/Auditoria_Documentacao_e_Codigo_25-11.md`.

## 1. Instalar e rodar (Windows)
Requisitos: Python 3.12 ou superior (testado em 3.14.0) — o backend usa **somente a biblioteca padrão** (`aula-ia-backend/requirements.txt`
não tem dependências; `python -S` passa nos testes). Node.js só é necessário para **reconstruir** a interface (testado em 24.21.0);
o `aula-ia/dist/` já vem compilado no repositório. Busca híbrida (opcional): `aula-ia-backend/requirements-hibrido.txt`
(torch 2.15.0, sentence-transformers 6.2.0, transformers 5.22.1, numpy 2.3.5).

Chaves (nunca em arquivo): variáveis de ambiente `GEMINI_API_KEY` (geração) e `GROQ_API_KEY` (IA Juiz).

```
cd aula-ia-backend
python app.py --modo lexical --gerador ia --ipv4 --abrir          :: sistema completo (Gemini + IA Juiz via Groq)
python app.py --modo lexical --gerador demonstracao --juiz demonstracao --porta 8001 --temporario   :: sem rede (plano B)
python relatorio_testes.py                                         :: testes + relatório HTML (--sem-abrir)
node ..\aula-ia\tests\test-plano-render.mjs                        :: testes de interface (também test-formulario e test-juiz-render)
cd ..\aula-ia && npm ci && npm run build                           :: só se mudar a interface
```
Atalho: `INICIAR_AULAIA.cmd` (raiz) chama `aula-ia-backend/iniciar_prototipo.py`, que sobe `--modo lexical --gerador ia --ipv4 --abrir`.
Endereço: `http://127.0.0.1:8000` (JSON técnico: acrescente `?depuracao=1`). Uma porta ocupada por um `app.py` antigo mostra código velho.

Opções do app (`aula-ia-backend/app.py`): `--gerador demonstracao|ia`, `--modelo`, `--reparos 0|1` (padrão 1), `--repeticoes-503 0..2`
(padrão 2), `--limite-diario` (padrão 8 gerações com IA/dia, contando falhas), `--juiz groq|demonstracao|desligado` (padrão groq se
`GROQ_API_KEY` existir), `--ciclos-juiz` (padrão 1), `--regeneracao informada|cega` (padrão `informada`; `cega` = PoC 08),
`--limite-diario-juiz` (padrão 8 avaliações/dia, contando falhas), `--banco`, `--temporario`.

## 2. Arquitetura (arquivos de cada parte)
| Parte | Arquivos |
|---|---|
| Servidor HTTP local e rotas `/api/...` | `aula-ia-backend/app.py` |
| Consulta, confirmação, pedido (geração + Juiz), aprovação, SQLite | `aula-ia-backend/servico.py` |
| Extração do tema curto (sem IA) | `aula-ia-backend/tema.py` |
| Busca curricular (lexical; híbrida opcional) e vocabulário | `aula-ia-backend/rag/search.py`, `rag/termos.py`, `rag/ingest.py` |
| Catálogo BNCC do 8º ano e PDF-fonte | `aula-ia-backend/data/bncc_8ano.json`, `data/BNCCComputacao.pdf` |
| Geração: 5 especialistas + integrador em Python | `aula-ia-backend/geracao_v2.py`, `geracao.py`, `gemini.py`, `rede.py` |
| Verificação de acentuação (uma reescrita por especialista) | `aula-ia-backend/acentuacao.py` (chamada em `geracao.py`) |
| Regeneração informada (versão anterior + críticas do Juiz para cada especialista) | `aula-ia-backend/revisao_informada.py` (chamada em `servico.py`) |
| Contrato do plano (PlanoDeAula 2.0, 11 seções) e validador | `aula-ia-backend/contratos/plano_v2.py`, `plano_v2.schema.json`, `validacao.py`, `execucao.py`, `esquema_gemini.py` |
| IA Juiz: contrato do parecer, rubrica, política, prompt | `aula-ia-backend/contratos/juiz_v1.py`, `juiz_v1.schema.json`, `rubrica_juiz.py` |
| IA Juiz: avaliação, adaptador Groq, integração ao pedido | `aula-ia-backend/juiz.py`, `groq_juiz.py`, `juiz_servico.py` |
| Experimentos do Juiz (casos, variantes, séries, adjudicação) | `ensaio_juiz.py`, `casos_juiz.py`, `variantes_juiz.py`, `analisar_serie.py`, `adjudicacao.py`, `adjudicacao_web.py`, `concordancia.py` |
| Lote de geração e medição (PoC07) | `gerar_lote.py`, `medir_planos.py`, `exportar_planos.py` |
| Interface React (formulário, busca, confirmação) | `aula-ia/src/App.jsx`, `src/formulario.js`, `src/App.css` |
| Interface do pedido (progresso, painel do Juiz, aprovar, PDF) | `aula-ia/public/geracao-ui.js`, `public/geracao-ui.css` (copiados para `dist/` no build) |

**Banco SQLite** (`aula-ia-backend/local/consultas.sqlite3`, fora do Git): `consultas`, `geracoes` (com `pedido_id`, `ciclo`, `entregue`),
`pedidos`, `pareceres` (criadas/migradas em `ServicoCurricular.__init__`).

## 3. Fluxo com a IA Juiz
1. Professor informa contexto (ano, tema — pode ser frase inteira —, duração, tipo, recursos em checklist).
2. `tema.py` extrai o tema curto; a busca devolve habilidades do 8º ano; o professor **confirma** uma habilidade.
3. "Gerar plano": cria um **pedido**. Os 5 especialistas (objetivos, avaliação preliminar, metodologia, sequência, avaliação final;
   adaptação) geram em 6 chamadas ao Gemini; o integrador compõe as 11 seções; o validador confere o contrato. Saída de especialista
   sem acentuação recebe **uma** reescrita antes da etapa seguinte (falhou ou não melhorou → fica a original).
4. A IA Juiz avalia o plano (6 critérios, nota 0–3; falhas com gravidade e componente) e a política calcula o próximo estado.
5. Favorável → entrega. Não favorável → gera o plano inteiro de novo (até `--ciclos-juiz`), e cada especialista recebe a sua versão
   anterior e as críticas do Juiz (`revisao-informada-1.0`); a nova versão é avaliada do zero. Sem favorável, entrega a versão com menos
   falhas graves, com aviso. Falha técnica do Juiz → entrega com "avaliação indisponível".
6. Professor vê o parecer ("Avaliação automática e provisória; a decisão final é do professor."), aprova e baixa o PDF, ou gera novamente
   (novo pedido, do zero, sem as críticas do pedido anterior).
Detalhes e testes: `docs/PoC08_Juiz_Integrado.md`.

## 4. Versões vigentes
| Item | Valor | Fonte |
|---|---|---|
| Modelo gerador | `gemini-3.5-flash-lite` | `aula-ia-backend/gemini.py` (`MODELO_PADRAO`) |
| Prompt dos especialistas | `especialistas-plano-2.3` (2.2 preservada) | `geracao_v2.py` (`VERSAO_PROMPT`, `VERSOES_PROMPT`) |
| Contrato do plano | `plano-aula-2.0` (11 seções; etapas: objetivos, avaliacao_preliminar, metodologia, sequencia, avaliacao_final, adaptacao) | `contratos/plano_v2.py` |
| Modelo do Juiz | `openai/gpt-oss-120b` (Groq), adaptador `groq-juiz-0.2` | `groq_juiz.py` |
| Prompt do Juiz | `juiz-v1.3` (v1.2 preservada) | `contratos/juiz_v1.py` (`VERSAO_PROMPT`) |
| Contrato do parecer | `parecer-juiz-1.0` | `contratos/juiz_v1.py` (`VERSAO`) |
| Rubrica | `rubrica-juiz-0.1` (6 critérios: aderência curricular, alinhamento dos objetivos, coerência metodológica, viabilidade, avaliação da aprendizagem, inclusão) | `contratos/rubrica_juiz.py` |
| Política | `politica-juiz-prelim-0.1` (nota mínima 2; maior/crítica exigem correção; crítica → revisão humana) — preliminar, não validada | `contratos/juiz_v1.py` (`POLITICA_PRELIMINAR`) |
| Parâmetros do Juiz | temperature 0, max_completion_tokens 8192, reasoning_effort medium, seed 42, timeout 90 s, reparos 1 | `juiz_servico.py` (`PARAMETROS_EXPERIMENTOS`, `REPAROS`) |
| Catálogo | `bncc-8ano-v1` | `servico.py` (`VERSAO_CATALOGO`) |
| Regeneração | `revisao-informada-1.0` (padrão; texto idêntico ao da sondagem PoC 09) | `revisao_informada.py` (`VERSAO`, `INSTRUCAO`) |
| Acentuação | `deteccao-acentuacao-1.2` (26/11): campo sem nenhum acento e com palavra-guia (> 60 caracteres: qualquer; curto: só inequívoca) ou campo misto com palavra inequívoca sem acento → 1 reescrita (só modo IA) | `acentuacao.py` (`VERSAO`) |

## 5. Números atuais (25/11/2026)
| Número | Valor | Como conferir |
|---|---|---|
| Testes Python | **545 (544 passam, 1 ignorado: `test_fluxo.TestRankingOriginal.test_modelo_e_embeddings_anexados`, só com `TESTAR_HIBRIDO=1`) no código congelado `c1ef4f8`**, também com `python -S`. Antes: 539 na `feat/poc11-acento-curto-e-recomendacao`; 532 (531 passam, 1 ignorado), também com `python -S` — conferido em 25/11 na `fix/auditoria-25-11-c1-c4-c5-c9` (513 na `main` `4558b4a`, +19 da auditoria; eram 493 em 23/11) | `python relatorio_testes.py --sem-abrir`; arquivos em `aula-ia-backend/tests/` (38 `.py`) |
| Testes de interface | 3 scripts | `aula-ia/tests/test-plano-render.mjs`, `test-formulario.mjs`, `test-juiz-render.mjs` |
| Habilidades no catálogo | 11 (EF08CO01–EF08CO11) | `aula-ia-backend/data/bncc_8ano.json` |
| Especialistas | 5 (6 chamadas; a avaliação tem duas passagens) + integrador em Python | `geracao_v2.py`, `contratos/plano_v2.py` (`ETAPAS`) |
| Seções do plano | 11 | `contratos/plano_v2.py`, `docs/Contrato_PlanoDeAula_2_0.md` |
| Mutação manual (PoC 08) | 46 + 11 mutantes, 0 sobreviventes | `docs/diario_de_bordo.md` (entrada de 19/11) |
| Mutação manual (PoC 10) | 22 mutantes, 0 sobreviventes (1 sobrevivente na 1ª rodada, morto com 2 testes novos) | `docs/PoC10_Regeneracao_Informada_e_Acentuacao.md` §7 |
| Mutação manual (PoC 11) | 17 mutantes (12 backend, 5 front), 0 sobreviventes | `docs/PoC11_Acento_Curto_e_Recomendacao.md` §5 |
| Mutação manual (código congelado `c1ef4f8`) | 15 mutantes no backend (os 12 da PoC 11 + 3 do campo misto) e 6 no front (os 5 da PoC 11 + 1 do texto "sem parecer favorável"), 0 sobreviventes | `docs/diario_de_bordo.md` (entrada de 26/11) |

## 6. Experimentos e resultados (onde estão)
| O quê | Onde |
|---|---|
| Casos congelados e variantes do Juiz (V01–V06) | `experimentos/juiz/casos/`, `experimentos/juiz/variantes/` |
| Protocolos pré-registrados e regras de pontuação | `experimentos/juiz/Protocolo_*.md`, `experimentos/juiz/pontuacao/V03–V06.json` |
| Resultados brutos do Juiz (todas as chamadas) | `aula-ia-backend/local/ensaios_juiz/` (commitado com `git add -f`) |
| Análises das séries | `experimentos/juiz/resultados/` |
| Protocolo e lote da geração 2.3; planos 2.3 | `docs/PoC07B_Prompt_2_3.md`, `experimentos/geracao/poc07b_entradas.json`, `experimentos/geracao/poc07b_planos_2_3/` |
| Comparação 2.2 × 2.3 | `docs/PoC07D_Resultado_Lote_2_3.md` |
| Juiz integrado: pareceres dos 5 planos 2.3 e pedidos reais | `docs/PoC08_Juiz_Integrado.md` |
| Sondagem regeneração cega × informada (pré-registrada) | `docs/PoC09_Sondagem_Regeneracao_Informada.md`, `docs/PoC09_Resultado_Sondagem.md`, `experimentos/geracao/poc09_sondagem_c/` |
| Parecer usado no modo demonstração | `experimentos/juiz/demonstracao/parecer_controle_v13.json` |
| Ferramenta de adjudicação humana | `aula-ia-backend/adjudicacao.py`, `docs/Guia_Adjudicacao_Humana.md` (fases ainda não realizadas) |
| Histórico de decisões e trabalho | `docs/diario_de_bordo.md`, `CLAUDE.md` |

## 7. Limites conhecidos
- Evidência com LLM é provisória: amostras pequenas (n = 5 por versão de prompt), um modelo por papel, temperatura 0 não garante
  repetição. Nenhum resultado mostra que "o Juiz acerta"; a adjudicação humana das séries V03–V06 não foi feita.
- A política do Juiz é preliminar. A regeneração usa as críticas do Juiz, mas refaz o plano inteiro (também os componentes sem
  crítica); o ganho foi visto só numa sondagem exploratória (n = 5) medida pelo próprio Juiz (circularidade).
- A verificação de acentuação é heurística (sem palavra-guia escapa; desde a PoC 11, campos curtos contam só com palavra inequívoca);
  a regra 1.2 rodou com chamadas reais no caso-base de 26/11 (3 reescritas aceitas, registradas com `deteccao-acentuacao-1.2`); a
  recomendação ao professor foi conferida na interface só em modo demonstração (não conferida em execução real); PoC 10 verificada com chamadas reais em um único
  pedido (25/11: 3 reescritas aceitas; regeneração informada resolveu a crítica, mas o Juiz levantou outra — 1 grave → 1 grave).
- Timeout de 90 s por chamada ao Gemini: em 19/11, 4 de 8 gerações terminaram em timeout (`docs/PoC08_Juiz_Integrado.md`).
- Só o 8º ano; busca lexical por padrão; tema por regras (falso positivo conhecido: "lista de compras" → "Lista", `docs/PoC06_Tema_Curto.md`).
- Gerador de demonstração é por regras e não representa a qualidade do Gemini. Com `--juiz demonstracao` (parecer gravado de outro
  plano), a regeneração é sempre cega e o histórico registra o motivo (auditoria C5).
- A reescrita de acentuação é heurística na detecção; só é aceita se o contrato continuar válido, IDs, números, vínculos e estrutura
  ficarem iguais aos da original e o número de campos sem acento cair (auditoria C1).
- Enquanto o pedido roda, o serviço renova `atualizado_em` a cada 60 s; sem sinal por mais de 15 min, o pedido aparece como
  `interrompido` (app fechado no meio da geração). Antes, uma geração só lenta podia aparecer assim (auditoria C4).
- HTTP 503: a classe `AgenteGemini` e o site repetem até 2 vezes por padrão (`REPETICOES_503_PADRAO`); só a sondagem de terminal
  (`teste_gemini.py`) desliga de propósito (auditoria C9).
- Execução local (sem deploy); sem contas de usuário; impressão "página em branco no fim" (PA-2) não reproduzida, correção preventiva.

## 8. Trabalho futuro
Correção dirigida só dos componentes criticados pelo Juiz, com grafo de invalidação (hoje a regeneração usa as críticas, mas refaz
todos os componentes); verificação humana cega do ganho da regeneração informada; "Gerar novamente" com as críticas do pedido anterior; prompt 2.4 (fidelidade ao tipo de aula, exemplo
concreto, evidência não só oral); regra de medição v2 (negação/recurso confirmado); adjudicação humana e calibração da política; mais
anos escolares; deploy na internet com autenticação.
