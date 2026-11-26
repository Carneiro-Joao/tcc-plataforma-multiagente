# Auditoria de documentação, diagramas e código — 25/11/2026

> **Etapa 1 (só leitura).** Nenhum código, documento de especificação ou diagrama foi alterado; este relatório é o único arquivo novo.
> **Referência:** código da `main` em `4558b4a` (PoC 10). Diagramas: branch `docs/figuras-cap4-exemplo-unico` (`fed4a81`), base desta
> branch `docs/auditoria-25-11`. **O sistema não está congelado** (o congelamento vem depois dos testes finais do João).
> **Testes conferidos agora:** 513 Python (512 passam, 1 ignorado), também com `python -S`; 3 scripts do front OK.
>
> Legenda: ✅ de acordo · ⚠️ desatualizado · ❌ errado ou contraditório · ➕ faltando.
>
> **Adendo (25/11, noite): o que foi feito depois deste relatório.** Etapa 2 aprovada pelo João e aplicada na branch
> `docs/auditoria-25-11`: especificação v2.3, nova correspondência, diagramas e documentos atualizados; correções C2 (`fe85fa7`),
> C3 (`85d592b`), C6 (`90b95ea`), C7 (`3606936`) e C8 (`5f02230`). Depois, a pedido do João, os achados que este relatório marcava como
> "só documentar" também foram corrigidos na branch `fix/auditoria-25-11-c1-c4-c5-c9`: **C1** reescrita de acento só é aceita com
> IDs, números, vínculos e estrutura iguais (`f3b9989`); **C4** batimento de 60 s renova o pedido em andamento (`3b7bbc4`); **C5** Juiz
> de demonstração → regeneração cega (`3b7bbc4`); **C9** `REPETICOES_503_PADRAO = 2` na classe (`6f8feed`); testes em `b943870`
> (11 mutantes, 0 vivos). Total: 532 testes. Revisão seguinte: `docs/Revisao_Geral_25-11_noite.md`. O texto abaixo fica como estava.
> Impacto: **pontual** (muda só o próprio arquivo) ou **cascata** (obriga a mudar outros documentos ou figuras).

## Resumo

| Grupo | ✅ | ⚠️ | ❌ | ➕ |
|---|---|---|---|---|
| Especificação v2.2 (itens: 22 RF, 10 RNF, 15 RN e as seções) | 45 | 17 | 0 | 4 |
| Correspondência de IDs | 1 | 3 | 0 | 1 |
| Outros documentos (Estado_Final, README, CLAUDE.md, Contrato, PoCs, diagramas-finais) | 4 | 4 | 2 | 1 |
| Diagramas (8 figuras: fonte, PNG, SVG, cópia) | 4 | 4 | 0 | 4 |
| Achados de código | — | — | — | 9 (0 alta, 1 média, 8 baixa) |

Nada está "errado" no código em relação ao que ele promete fazer. Os dois ❌ são documentos que descrevem o sistema de antes da PoC 08
(README) e uma lista de pendências já resolvidas (CLAUDE.md).

---

## 1A. Documentação

### 1A.1 `docs/especificacao/AulaIA_Especificacao_v2.2_final.md`

| Onde (linha) | Situação | Texto atual | O que o código faz | Proposta | Impacto |
|---|---|---|---|---|---|
| Cabeçalho (l. 3–4) | ⚠️ | "versão final… aprovada em 23/11"; "revisada contra o sistema congelado na `main` (`694c07c`)" | Código em `4558b4a`, não congelado | Na v2.3: "versão de trabalho de 25/11/2026, conferida contra a `main` `4558b4a`; o congelamento vem depois dos testes finais" | pontual |
| §1 objetivo 5 (l. 26) | ⚠️ | "regeneração automática com limite de tentativas" | Regeneração informada pelas críticas | "…e **regeneração automática informada pelas críticas do parecer**, com limite de tentativas" | cascata leve (texto do TCC) |
| §1 demais objetivos, problema, não-objetivos | ✅ | — | — | — | — |
| §2 (l. 36–39) | ⚠️ | "PoC 01 a PoC 08"; "493 Python"; pré-registros "(V01–V06) e da geração (PoC07B)" | 10 PoCs; 513 testes; PoC 09 pré-registrada | "PoC 01 a PoC 10"; "513 Python, 1 ignorado"; "…(PoC07B) e da sondagem de regeneração (PoC 09)" | pontual |
| §3 Modelo do plano | ✅ | — | Contrato `plano-aula-2.0` inalterado | — | — |
| §4 Contexto | ✅ | — | 800 caracteres, 1–1440 min (`servico.py` l. 59–64) | — | — |
| §5 tabela, Orquestrador (l. 73) | ⚠️ | "5 especialistas em 6 chamadas encadeadas, validação a cada etapa, integrador" | Também verifica acentuação e pede 1 reescrita | Acrescentar "; verificação de acentuação com uma reescrita" | pontual |
| §5 tabela (novas linhas) | ➕ | — | `revisao_informada.py`, `acentuacao.py` | "Revisão informada \| monta, para cada especialista, a versão anterior e as críticas do Juiz \| `revisao_informada.py`" e "Verificação de acentuação \| detecta campos sem acento e pede reescrita \| `acentuacao.py`" | cascata (diagrama de componentes) |
| §5 versões (l. 85) | ⚠️ | "**Versões congeladas:**…" | + `revisao-informada-1.0` | "**Versões vigentes:**…; regeneração `revisao-informada-1.0`" | pontual |
| §5 especialistas | ✅ | "5 em 6 chamadas" | Igual | — | — |
| §6 passo 2 (l. 91) | ⚠️ | "Os especialistas geram o plano; o integrador compõe e o validador confere." | Reescrita de acentuação entre etapas | Acrescentar "Saída de especialista sem acentuação recebe uma reescrita antes da etapa seguinte; se falhar ou não melhorar, fica a original." | cascata leve (atividades, opcional) |
| §6 passo 4 (l. 94) | ⚠️ | "o plano inteiro é gerado de novo… e avaliado de novo" | Cada especialista recebe `revisao_pedagogica` | Texto da PoC 10 §8.1 (versão anterior + críticas; sem acrescentar recursos; avaliada do zero) | cascata (atividades, sequência, visão geral — já feitos na branch de figuras) |
| §6 passo 6 (l. 97) | ➕ | "…ou **gera novamente** (novo pedido, mesmo fluxo)" | Novo pedido gera do zero, **sem** as críticas do pedido anterior (decisão do João: manter) | Acrescentar "…; a nova geração começa do zero, sem as críticas do pedido anterior" | pontual |
| §6 estados | ✅ | — | Nenhum estado novo (`servico.py`) | — | — |
| §7 Casos de uso | ✅ | — | — | — | — |
| §8 frase de abertura (l. 123) | ⚠️ | "Todos estão implementados **na versão congelada**" | Não congelado | "…na versão de 25/11" | pontual |
| §8 RF01–RF08, RF10, RF11, RF13–RF16, RF19–RF22 | ✅ | — | Conferidos; testes citados existem e cobrem | — | — |
| §8 RF09 (l. 135) | ⚠️ | "…validando cada etapa" | + reescrita de acentuação | "…validando cada etapa e pedindo uma reescrita quando a saída vem sem acentuação"; teste `test_poc10.py` | pontual |
| §8 RF12 (l. 138) | ⚠️ | "Regenerar automaticamente o plano inteiro…" | Informada | Texto da PoC 10 §8.1; testes `test_juiz_integrado.py`, `test_poc10.py` | cascata (correspondência) |
| §8 RF14 | ✅ | — | Progresso diz "com as críticas do Juiz"; `test-juiz-render.mjs` cobre | — | — |
| §8 RF17/RF18 (l. 143–144) | ⚠️ | "quem não aprovar pode gerar novamente" | Gerar novamente = do zero, sem críticas | RF18: acrescentar "; a nova versão pedida pelo professor é gerada do zero, sem as críticas do pedido anterior" | pontual |
| §9 RNF01, RNF02, RNF05, RNF06, RNF07, RNF09, RNF10 | ✅ | — | Conferidos (75/120/60 s, 90 s, 2× 503 no app) | — | — |
| §9 RNF03 (l. 156) | ⚠️ | — | Histórico registra `modo`, `versao_revisao`, `criticas_usadas`; rastreio registra reescritas de acento | Acrescentar essas duas frases | pontual |
| §9 RNF04 (l. 157) | ⚠️ | — | Reescrita de acentuação nunca derruba a geração | Acrescentar | pontual |
| §9 RNF08 (l. 161) | ⚠️ | "limite diário de 8 gerações e 8 avaliações" | Reescritas de acento: até 6 chamadas extras por versão, **fora** do limite diário | Acrescentar | pontual |
| §10 RN01–RN10, RN12–RN15 | ✅ | — | — | — | — |
| §10 RN11 (l. 179) | ⚠️ | "até N regenerações completas (padrão 1)" | Informadas; 1ª geração sem críticas | Texto da PoC 10 §8.1 | cascata (correspondência) |
| §10 (novas) | ➕ | — | (a) A regeneração não autoriza acrescentar recursos: instrução + validador exige `recursos` idêntico; (b) a reavaliação do Juiz não recebe críticas nem versão anterior (`juiz.avaliar_plano` recebe só contexto, habilidade, revisão e plano) | RN16 "As críticas do Juiz não alteram o contexto confirmado: a regeneração não pode acrescentar recursos" · RN17 "Cada avaliação do Juiz é independente: não recebe críticas, parecer nem versão anterior" | cascata (correspondência) |
| §11 Dados | ✅ | — | Sem mudança de tabelas; evento `regenerando` dentro de `pedidos.historico` (JSON) | Opcional: uma frase sobre o evento | — |
| §12 Limitações (l. 194) | ⚠️ | "regeneração não usa as críticas do Juiz" | Usa | Texto da PoC 10 §8.1 (refaz tudo; ganho só em sondagem n = 5, medido pelo próprio Juiz; acentuação é heurística) | cascata (texto do TCC) |
| §12 Trabalhos futuros (l. 199) | ⚠️ | correção dirigida… | — | Manter, com a nuance "a regeneração já usa as críticas, mas refaz todos os componentes"; acrescentar "verificação humana cega do ganho" e "Gerar novamente com as críticas do pedido anterior" | pontual |
| §13 Histórico | ➕ | — | — | "v2.3 \| 25/11/2026 \| Regeneração informada pelas críticas do Juiz (PoC 10) e verificação de acentuação" | pontual |

### 1A.2 `docs/especificacao/Correspondencia_IDs_v2.1R2_v2.2.md`

| Linha | Situação | Proposta |
|---|---|---|
| Título e referência à v2.2 | ⚠️ | Criar `Correspondencia_IDs_v2.1R2_v2.3.md` (ou manter o arquivo e acrescentar uma coluna/nota "v2.3: IDs iguais") |
| 25 (RF12) | ⚠️ | "…regeneração do plano inteiro informada pelas críticas do Juiz (padrão 1); correção dirigida → futuro" |
| 54 (RN11) | ⚠️ | "…até N regenerações completas, informadas pelas críticas (padrão 1)" |
| Novas RN16, RN17 (se aprovadas) | ➕ | Duas linhas "— (novo, PoC 10)" |
| Demais linhas | ✅ | — |

### 1A.3 Outros documentos

| Documento | Situação | O que está escrito × o que o código faz | Proposta | Impacto |
|---|---|---|---|---|
| `docs/Estado_Final_Sistema.md` | ⚠️ | Conteúdo técnico **certo** (atualizado na PoC 10: opções, arquitetura, fluxo, versões, 513 testes). Mas: título "congelado em 19/11", l. 3 "versão congelada", §4 "Versões congeladas", §8 "fora do escopo congelado", l. 6 aponta para a v2.2, l. 86 "conferido na `feat/poc10…`" | Trocar por "versão de 25/11 (congelamento após os testes finais)"; apontar para a v2.3; "conferido na `main` `4558b4a`" | pontual |
| `README.md` | ❌ | Não muda desde 17/11. Diz que a "IA Juiz existe como **módulo isolado**… sem acionar correções ou aprovação" (l. 128); não cita Juiz integrado, extração de tema, limites diários, regeneração informada, acentuação; "até 12 chamadas"; roteiro de demonstração com recursos em texto livre; usa o teste de terminal da PoC 04 como caminho principal | Reescrever §4–§5: como rodar (`app.py` com `--juiz`, `--ciclos-juiz`, `--regeneracao`, limites), fluxo atual em 6 passos, link para a especificação e para o `Estado_Final_Sistema.md`; nova seção curta "Ferramentas de pesquisa e scripts históricos" | pontual (grande) |
| `CLAUDE.md` | ❌/⚠️ | ⚠️ Seção "Estado em 19/11 — CONGELAMENTO" diz "`main` = VERSÃO CONGELADA" e "desenvolvimento encerrado", contraditório com a PoC 10. ❌ "Pendências (18/11)": itens 5 (Juiz → pipeline), 6 (impressão, cartões, `tem_credencial`, `erroEhDoTema`) e 7 (merge na `main`) já foram feitos; o item 2 cita alerta habilidade × recursos, já feito. ⚠️ l. 58 "Especificação v2.2 e diagramas não foram editados" muda após a Etapa 2. Comandos sem `--regeneracao` | Nota no topo da seção de 19/11 ("congelamento reaberto em 25/11; novo congelamento após os testes finais"); pendências atualizadas; comando do app com `--regeneracao` | pontual |
| `docs/Contrato_PlanoDeAula_2_0.md` | ⚠️ | l. 67 "até 12 tentativas estruturais" | Reescrita de acentuação soma até 6 chamadas; `revisao_pedagogica` nos dados da regeneração | Acrescentar uma frase com as duas coisas | pontual |
| `docs/diagramas/diagramas-finais.md` | ⚠️ | Cabeçalho (l. 3): "versão final… sistema congelado na `main` (`694c07c`)"; cópias Mermaid **idênticas** às fontes ✅ | "versão de 25/11, conferida contra a `main` `4558b4a`" | pontual |
| `docs/PoC08_Juiz_Integrado.md` | ✅ | Já tem nota de que a PoC 10 substituiu a regeneração cega | — | — |
| `docs/PoC09_*`, `docs/PoC10_*` | ✅ | Números conferem (513 testes, 22 mutantes, verificação de 25/11 17:18) | — | — |
| `docs/diario_de_bordo.md` | ✅ | Registro; não precisa de mudança além da entrada desta tarefa | — | — |
| Documentos de PoC antigas (PoC04A–PoC07D, Incrementos) | ✅ | Históricos; `PoC04A_Gemini_atual.md` já marcado como histórico | Opcional: nota "superado" no `Capitulo_4_Incremento_03.md` | — |
| Ferramentas sem documentação de uso | ➕ | `sondagem_regeneracao_informada.py` não aparece no README nem no `Estado_Final` (só no doc da PoC 09) | Citar na lista de ferramentas do README | pontual |

### 1A.4 Números e versões (todos conferidos no código)

| Item | Documentos | Código | Situação |
|---|---|---|---|
| Testes | Estado_Final 513; spec 493 | 513 (512 + 1 ignorado) | ⚠️ só na spec |
| Limites diários | 8 gerações, 8 avaliações | `app.py` l. 119, 129 | ✅ |
| Ciclos do Juiz | padrão 1 | `app.py` l. 124 | ✅ |
| Intervalos do Groq | 75 s, 120 s após 413, 60 s antes do reparo | `juiz_servico.py` l. 23–27 | ✅ |
| Timeout | 90 s | `gemini.py` l. 30; `juiz_servico.py` l. 28 | ✅ |
| HTTP 503 | até 2 novas tentativas | `app.py` l. 117 (padrão 2; a classe `AgenteGemini` tem padrão 0, usado só por scripts) | ✅ |
| Tema / duração | 800 caracteres / 1–1440 min | `servico.py` l. 59–64 | ✅ |
| Versões | `especialistas-plano-2.3`, `juiz-v1.3`, `rubrica-juiz-0.1`, `politica-juiz-prelim-0.1`, `parecer-juiz-1.0`, `plano-aula-2.0`, `revisao-informada-1.0` | conferidas | ✅ (spec sem `revisao-informada-1.0`) |
| Chamadas por versão | 6 (até 12 com reparos) | 6 + até 6 reescritas de acento; com reparos, até 18 | ⚠️ Contrato e README |

---

## 1B. Diagramas (`docs/diagramas/final/`)

Método: renderizei de novo cada fonte (`mmdc`, Playwright) e comparei os pixels com o PNG versionado; procurei no SVG o texto atual
da fonte; comparei as cópias do `diagramas-finais.md` com as fontes.

| Diagrama | Fonte | PNG | SVG | Cópia no `.md` | Conteúdo × código | Proposta |
|---|---|---|---|---|---|---|
| `atividades` | ✅ nó "Gerar de novo o plano com as críticas do Juiz" | ✅ igual à fonte (só suavização de pixels) | ⚠️ **desatualizado** (texto de 23/11) | ✅ | ✅ | Regenerar SVG. Opcional: nó G "(…validação e verificação de acentuação a cada etapa)" |
| `sequencia` | ✅ "Gerar de novo com a versão anterior e as críticas do Juiz" | ✅ idêntico | ⚠️ **desatualizado** | ✅ | ✅ | Regenerar SVG |
| `componentes` | ⚠️ sem revisão informada nem acentuação | ✅ | ✅ | ✅ | ⚠️ | ➕ caixas "Revisão informada (`revisao_informada.py`)" entre Serviço e Orquestrador e "Verificação de acentuação (`acentuacao.py`)" no Orquestrador; regenerar PNG e SVG |
| `estados` | ✅ nenhum estado novo | ✅ idêntico | ✅ | ✅ | ✅ | — |
| `er` | ✅ nenhuma tabela nova | ✅ idêntico | ✅ | ✅ | ✅ | — |
| `casos-de-uso` (`.puml`) | ✅ | ✅ | ✅ | (imagem) | ✅ | ➕ versão Mermaid `casos-de-uso.mmd` (pedido da Etapa 2) |
| `visao-geral` (`.html`) | ✅ "usando as críticas do Juiz" e "se nenhuma versão tiver parecer favorável…" | ✅ idêntico ao HTML (1800 e 1900 px dão o mesmo, pois `.fig` tem largura fixa) | — | ✅ | ✅ | ➕ versão `visao-geral.mmd` |
| `estrutura-plano` (`.html`) | ⚠️ exemplo da execução de 23/11 **sem fonte versionada** (o plano está num PDF fora do Git), então as citações literais não podem ser conferidas no repositório | ✅ idêntico ao HTML | — | ✅ | ✅ estrutura | Manter até a nova execução (decisão do João); ao refazer, versionar o JSON exportado do plano. ➕ versão `estrutura-plano.mmd` |

**Precisa de imagem nova:** `atividades.svg`, `sequencia.svg`; `componentes.png` e `.svg` (se a caixa nova for aprovada);
`casos-de-uso.mmd`, `visao-geral.mmd` e `estrutura-plano.mmd` (fontes novas, com PNG opcional).
**Não precisa:** `estados`, `er`, `casos-de-uso.png`, `visao-geral.png`, `estrutura-plano.png`, `atividades.png`, `sequencia.png`.

---

## 1C. Código (nada foi alterado)

| # | Arquivo e linha | Problema | Grav. | Correção proposta | Risco da correção | Recomendação |
|---|---|---|---|---|---|---|
| C1 | `geracao.py` l. 125–152 (`_reescrever_sem_acento`) | A reescrita de acentuação é aceita se passa no validador e tem menos campos sem acento, mas **não se confere que IDs, minutos, vínculos e estrutura ficaram iguais** aos da saída original. O modelo pode, por exemplo, redistribuir os minutos ou mudar um texto de sentido; o contrato aceita | média | Comparar a nova saída com a original ignorando só os textos (mesmas chaves, listas do mesmo tamanho, mesmos IDs e números); se diferir, descartar | médio (descarta mais reescritas) | Depois do congelamento; documentar como limitação |
| C2 | `acentuacao.py` l. 32–39; `geracao.py` l. 195 | O detector olha também campos copiados do contexto (ex.: `recursos` da metodologia). Recursos digitados sem acento e com mais de 60 caracteres disparam uma reescrita que sempre será descartada (o validador exige `recursos` idêntico): chamada desperdiçada | baixa | Ignorar o caminho `recursos` (e outros copiados do contexto) | baixo | Depois; documentar |
| C3 | `app.py` l. 177–178 | Ao iniciar, o app mostra "Limite total com reparos e repetições: 36 requisições", que **não conta** as reescritas de acentuação (até 6 chamadas extras, cada uma com até 3 tentativas). A mensagem subestima o teto | baixa | Somar o termo das reescritas na conta | baixo (só texto) | Corrigir agora, se aprovado, ou documentar |
| C4 | `servico.py` l. 35, 219–226, 297 | Um pedido em andamento é mostrado como "interrompido" depois de 15 min sem atualização, e `atualizado_em` só muda nas transições de estado. Uma geração muito lenta (timeouts + reparos + reescritas) pode passar de 15 min ainda rodando e liberar um 2º pedido em paralelo. Pré-existente; a PoC 10 aumentou o teto de chamadas | baixa | Atualizar `atualizado_em` a cada chamada (progresso) ou subir o limiar | médio | Só documentar |
| C5 | `servico.py` l. 337–339 | Com `--gerador ia --juiz demonstracao`, a regeneração informada manda ao Gemini as críticas de um parecer gravado de **outro** plano | baixa | No Juiz de demonstração, usar regeneração cega | baixo | Só documentar (combinação de teste, não de uso) |
| C6 | `tests/test_exportar_planos.py` | Chave **falsa** no formato `AIza…` como dado de teste: pode disparar scanners de segredo (GitHub, `findstr` da regra 5) | baixa | Montar a string em tempo de execução (`"AIza" + "…"`) | baixo | Depois |
| C7 | `aula-ia-backend/teste_api_rapido.py`, `teste_openrouter.py` (PoC 03, OpenAI/OpenRouter), `iniciar_prototipo.py`, `inspecionar_gemini.py`, `teste_gemini.py` (PoC 04) | Scripts históricos soltos na pasta principal, ao lado do app; os dois primeiros usam provedores que o sistema não usa mais | baixa | Listar no README como históricos; mover para `legado/` | baixo (documentar) / médio (mover: imports) | Documentar agora; mover depois |
| C8 | `geracao.py` (contrato 1.0) | O gerador 2.0 herda do gerador 1.0 (`GeradorDePlano`, `AgenteDemonstrativo`, `contratos.execucao`), que só é usado diretamente por scripts históricos. Não é código morto, mas o nome confunde | baixa | Comentário no topo de `geracao.py` explicando a herança | baixo | Depois |
| C9 | `gemini.py` l. 32 | Padrão `repeticoes_503=0` na classe, enquanto o app usa 2. Correto (documentado no contrato), mas quem instancia a classe diretamente não tem repetição | baixa | Nenhuma | — | Só registrar |

Verificações sem achado: nenhuma credencial real em arquivos versionados (inclusive os dados brutos das PoC 09 e 10); `dist/` igual a
`public/`; o Juiz não recebe críticas nem versão anterior (`juiz.avaliar_plano`); a reescrita de acento descartada não entra na
`versao_anterior` da regeneração (teste da PoC 10); o "Gerar novamente" abre pedido novo e começa sem `revisoes`.

---

## Lista de mudanças propostas para a Etapa 2

1. **Especificação v2.3** (nova; v2.2 vira histórico): todos os ⚠️ e ➕ da §1A.1, incluindo RN16 e RN17 se aprovadas.
2. **Correspondência de IDs**: RF12, RN11 e, se aprovadas, RN16/RN17.
3. **Diagramas**: regenerar `atividades.svg` e `sequencia.svg`; `componentes` com as duas caixas novas (se aprovado); versões Mermaid de
   `casos-de-uso`, `visao-geral` e `estrutura-plano`; cabeçalho do `diagramas-finais.md`.
4. **Estado_Final_Sistema.md**, **CLAUDE.md**, **Contrato_PlanoDeAula_2_0.md**: ajustes da §1A.3, sem marcar congelamento.
5. **README.md**: reescrita das seções 4 e 5 e lista de ferramentas/scripts históricos.
6. **Código**: só os itens que o João aprovar (candidato de risco baixo: C3; o resto recomendado para depois ou só documentar).
