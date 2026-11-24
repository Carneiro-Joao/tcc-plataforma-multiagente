# AulaIA — Especificação v2.2 (final, conforme implementado)

**Data:** 23/11/2026 · **Situação:** versão final, **aprovada pelo João em 23/11/2026**; pendente de ratificação do orientador.
**Base:** Especificação v2.1-R2 (10/11/2026, branch `docs/diagramas-rascunho`, commit `33e8025`), revisada contra o sistema congelado na
`main` (`694c07c`, 19/11/2026). Revisão item a item: projeto do TCC, `claude/revisao-documentacao.md`.
**Regra desta versão:** descreve **o que foi implementado**. O que estava na R2 e não foi feito está em §12 (trabalhos futuros).
Os identificadores foram **renumerados**; a correspondência com a R2 está em
[`Correspondencia_IDs_v2.1R2_v2.2.md`](Correspondencia_IDs_v2.1R2_v2.2.md). Diagramas: [`../diagramas/diagramas-finais.md`](../diagramas/diagramas-finais.md).

## 1. Objeto, problema e objetivos

**Objeto:** concepção, implementação incremental e verificação técnica de uma plataforma web de apoio ao planejamento de aulas de
Computação, com recuperação curricular da BNCC, agentes especialistas baseados em LLM, validação determinística e uma IA Juiz.

**Problema técnico:** como estruturar e integrar recuperação curricular, geração especializada, validação e avaliação automatizada para
obter planos de aula com estrutura consistente, referência curricular preservada e execução rastreável?

**Objetivo geral:** desenvolver e verificar tecnicamente uma plataforma web que integre recuperação curricular, agentes especialistas,
orquestração, validação determinística e IA Juiz para apoiar a elaboração de planos de aula de Computação.

**Objetivos específicos:**
1. Estruturar e rastrear o catálogo curricular do 8º ano, com códigos e descrições oficiais.
2. Implementar interface e API para contexto pedagógico, recuperação e confirmação de habilidade.
3. Estabelecer o modelo documental do plano de aula e contratos de entrada e saída por especialista.
4. Implementar a integração de especialistas com LLM real, preservando invariantes curriculares e temporais.
5. Implementar a IA Juiz com parecer estruturado e **regeneração automática** com limite de tentativas.
6. Persistir pedidos, versões, pareceres, falhas e trilhas técnicas da execução.
7. Demonstrar fluxos positivos e negativos por testes automatizados e cenários documentados, apresentando limitações.

**Não são objetivos deste TCC:** recrutamento de professores ou estudantes, entrevistas, questionários, aplicação em escola, avaliação
pedagógica humana em campo, mensuração de aprendizagem ou demonstração de superioridade pedagógica (decisão de 23/11: não haverá
capítulo de experimento com participantes).

## 2. Metodologia e evidências

Desenvolvimento incremental com provas de conceito (PoC 01 a PoC 08), cada uma registrada em `docs/` e no `docs/diario_de_bordo.md`.
PoC é instrumento de engenharia, não estudo experimental com participantes. Evidências: histórico Git, testes automatizados (493 Python,
1 ignorado, também com `python -S`; 3 scripts de interface), teste de mutação manual, execuções reais registradas com versão e hash,
protocolos pré-registrados para os ensaios da IA Juiz (V01–V06) e da geração (PoC07B).

**Verificação técnica ≠ validação pedagógica.** O parecer da IA Juiz sinaliza conformidade automatizada com uma rubrica; não prova
qualidade educacional. A aprovação é uma ação do usuário do protótipo, não uma avaliação de docentes participantes de pesquisa.

## 3. Modelo do plano de aula (PlanoDeAula 2.0)

Adaptação do AulaIA fundamentada em Pozzobon et al. (2025), Moreira, Lago e Figueiredo (2025), Silva, Silva e Oliveira (2025) e nas
Diretrizes Curriculares de Içara (2025). Contrato `plano-aula-2.0` (`contratos/plano_v2.py`, `plano_v2.schema.json`,
`docs/Contrato_PlanoDeAula_2_0.md`), 11 seções:

1. Identificação (componente, ano, tema, tipo, duração) · 2. Habilidade BNCC (código e descrição idênticos ao catálogo, eixo, objeto,
fonte, páginas, versão) · 3. Conteúdos (1–8) · 4. Objetivo geral · 5. Objetivos específicos (2–4, `OBJ`) · 6. Metodologia ·
7. Recursos (cópia exata dos recursos informados) · 8. Desenvolvimento (etapas `ET` com minutos, ação docente, ação discente, atividade
e vínculos) · 9. Avaliação da aprendizagem (evidências `EVI` e instrumentos `INS`) · 10. Adaptações (2, `ADP`) · 11. Referências.

**Invariantes verificadas pelo validador:** soma dos minutos = duração (inteiros positivos); todo objetivo ligado a etapa, evidência e
instrumento; código e texto da habilidade idênticos ao catálogo; IDs únicos e referências válidas.

## 4. Contexto informado pelo professor

Ano escolar (8º ano), tema (texto livre de até 800 caracteres, do qual o sistema extrai o tema curto), duração (1–1440 min), tipo de aula
(Computação desplugada, Aula prática, Aula teórica, Projeto) e recursos disponíveis (lista de marcar, ao menos um; "Outro" com texto).
Campos opcionais da R2 (conhecimentos prévios, características da turma, observações) **não foram implementados** (§12).

## 5. Arquitetura implementada

| Componente | Responsabilidade | Arquivo |
|---|---|---|
| Interface web | Formulário, busca, confirmação, progresso, plano, parecer, aprovação, PDF | `aula-ia/src/App.jsx`, `aula-ia/public/geracao-ui.js` |
| Servidor HTTP | Rotas `/api/...` e fonte BNCC; só biblioteca padrão | `aula-ia-backend/app.py` |
| Serviço de aplicação | Consulta, confirmação, pedido (geração + Juiz), aprovação, limites, SQLite | `servico.py` |
| Extração de tema | Tema curto por regras (catálogo → marcador → texto curto) | `tema.py` |
| Busca curricular | Lexical (padrão) ou híbrida opcional sobre o catálogo do 8º ano | `rag/search.py`, `rag/termos.py` |
| Orquestrador da geração | 5 especialistas em 6 chamadas encadeadas, validação a cada etapa, integrador | `geracao_v2.py` |
| Adaptador Gemini | Chamada ao `gemini-3.5-flash-lite`, reparo de formato, novas tentativas em 503 | `gemini.py`, `rede.py` |
| Integrador | Composição determinística das 11 seções (sem LLM) | `geracao_v2.py` |
| Validador | Contrato e invariantes | `contratos/plano_v2.py`, `contratos/validacao.py` |
| IA Juiz | Parecer por rubrica (6 critérios, nota 0–3), falhas com componente e gravidade | `juiz.py`, `contratos/juiz_v1.py`, `contratos/rubrica_juiz.py` |
| Adaptador Groq | Chamada ao `openai/gpt-oss-120b`; pausas por cota | `groq_juiz.py`, `juiz_servico.py` |
| Política de decisão | Próximo estado a partir do parecer (determinística) | `contratos/juiz_v1.py` (`decidir`) |
| Persistência | SQLite: `consultas`, `pedidos`, `geracoes`, `pareceres` | `servico.py` |

**Especialistas (5, em 6 chamadas):** Objetivos → Avaliação (passagem preliminar: evidências) → Metodologia e Recursos → Sequência
Didática → Avaliação (passagem final: instrumentos) → Adaptação. Integrador e validador são componentes determinísticos, não agentes.

**Versões congeladas:** prompt `especialistas-plano-2.3`; Juiz `juiz-v1.3`, `rubrica-juiz-0.1`, `politica-juiz-prelim-0.1`,
contrato `parecer-juiz-1.0`; catálogo `bncc-8ano-v1`. Parâmetros: `docs/Estado_Final_Sistema.md` §4.

## 6. Fluxo do pedido e estados

1. O professor confirma a habilidade e pede o plano; o sistema cria um **pedido**.
2. Os especialistas geram o plano; o integrador compõe e o validador confere. Falha técnica → pedido em `falha`, sem plano fictício.
3. A IA Juiz avalia automaticamente; a política calcula o próximo estado: `aguardando_decisao` (favorável), `em_correcao` ou
   `revisao_necessaria` (não favoráveis).
4. Não favorável → o plano inteiro é gerado de novo (até `--ciclos-juiz`, padrão 1) e avaliado de novo.
5. Entrega: a versão favorável; sem favorável, a versão com menos falhas graves (empate: a mais recente), com aviso.
   Falha técnica do Juiz → entrega sem parecer ("avaliação indisponível").
6. O professor **aprova** o plano e baixa o PDF, ou **gera novamente** (novo pedido, mesmo fluxo).

| Entidade | Estados |
|---|---|
| Pedido | `gerando`, `avaliando`, `aguardando_juiz` (espera da cota do Groq), `regenerando`, `pronto`, `falha`; `interrompido` quando um pedido em andamento fica parado mais de 15 min |
| Geração (versão do plano) | `processando`, `rascunho`, `aprovado`, `falha` |
| Parecer | `ok` ou `falha`; com `proximo_estado` da política |

## 7. Casos de uso

**Ator primário:** Professor (usuário planejador; não é participante de pesquisa). **Atores secundários:** serviço Gemini (geração) e
serviço Groq (IA Juiz).

| UC | Nome | Requisitos |
|---|---|---|
| UC01 | Gerar plano de aula (inclui informar contexto, consultar e confirmar habilidade, avaliação automática) | RF01–RF15, RF18, RF20, RF21 |
| UC02 | Visualizar plano e parecer | RF13, RF16 |
| UC03 | Aprovar plano | RF17 |
| UC04 | Baixar plano em PDF | RF19 |

Extensões de UC01: escolher a habilidade no catálogo (RF05), abrir o documento-fonte (RF06), gerar novamente (RF18).
Inspecionar especialistas (RF22) é recurso de depuração, não caso de uso do professor.

## 8. Requisitos funcionais

Prioridade: **P0** indispensável para demonstrar o núcleo técnico; **P1** necessário para uma entrega apresentável.
Todos estão **implementados** na versão congelada; RF06 é o único sem teste automatizado.

| ID | Requisito | Prior. | Evidência (testes em `aula-ia-backend/tests/`) |
|---|---|---|---|
| RF01 | Coletar ano, tema em texto livre, duração, tipo de aula e recursos em lista de marcar (ao menos um) | P0 | `test_http.py`, `test_fluxo.py`, `aula-ia/tests/test-formulario.mjs` |
| RF02 | Extrair automaticamente o tema curto da frase do professor, sem etapa de confirmação | P0 | `test_tema.py` |
| RF03 | Validar as entradas antes da busca e da geração | P0 | `test_fluxo.py`, `test_http.py` |
| RF04 | Recuperar e ordenar as habilidades da BNCC pelo tema, mostrando a fonte | P0 | `test_fluxo.py`, `test_tema.py` |
| RF05 | Permitir escolher a habilidade no catálogo completo | P0 | `test_fluxo.py` |
| RF06 | Abrir o documento-fonte da BNCC na página da habilidade | P0 | **Sem teste automatizado**; verificado na interface |
| RF07 | Exigir a confirmação da habilidade antes de gerar | P0 | `test_fluxo.py` |
| RF08 | Alertar, sem bloquear, quando a habilidade exige computador e ele não está nos recursos | P1 | `test_acertos_finais.py` |
| RF09 | Orquestrar os especialistas com contratos e dependências, validando cada etapa | P0 | `test_plano_v2.py`, `test_integracao_contratos.py`, `test_gemini.py` |
| RF10 | Produzir o plano no formato PlanoDeAula 2.0 (11 seções) | P0 | `test_plano_v2.py`, `test_contratos.py` |
| RF11 | Validar o plano deterministicamente e submetê-lo automaticamente à IA Juiz | P0 | `test_juiz.py`, `test_juiz_integrado.py` |
| RF12 | Regenerar automaticamente o plano inteiro quando o parecer não for favorável, com limite configurável (padrão 1), entregando a versão com menos falhas graves e um aviso | P0 | `test_juiz_integrado.py` |
| RF13 | Exibir ao professor o parecer da IA Juiz (decisão, notas, críticas) com aviso de que é provisório | P0 | `aula-ia/tests/test-juiz-render.mjs` |
| RF14 | Mostrar o progresso do planejamento e do pedido | P1 | `aula-ia/tests/test-juiz-render.mjs` |
| RF15 | Registrar e informar falha, interrupção e avisos, sem apresentar plano fictício | P0 | `test_geracao.py`, `test_http.py`, `test_juiz_integrado.py` |
| RF16 | Visualizar o plano da consulta atual e sua referência curricular | P1 | `aula-ia/tests/test-plano-render.mjs` |
| RF17 | Aprovar o plano explicitamente; quem não aprovar pode gerar novamente | P0 | `test_geracao.py`, `test_http.py`, `test_juiz_integrado.py` |
| RF18 | Gerar nova versão antes da aprovação, preservando as anteriores; após aprovar, iniciar nova consulta | P1 | `test_geracao.py`, `test_http.py` |
| RF19 | Baixar o plano em PDF (impressão do navegador, com parecer resumido) | P1 | `aula-ia/tests/test-juiz-render.mjs` |
| RF20 | Persistir consultas, pedidos, versões, pareceres e decisão | P0 | `test_geracao.py`, `test_juiz_integrado.py` |
| RF21 | Registrar por chamada: agente, modelo, versão do prompt, latência, tokens e erros | P0 | `test_gemini.py`, `test_groq_juiz.py` |
| RF22 | Inspecionar entradas e saídas dos especialistas em modo de depuração (`?depuracao=1`) | P1 | `aula-ia/tests/test-plano-render.mjs` |

## 9. Requisitos não funcionais

| ID | Categoria | Requisito e como é atendido |
|---|---|---|
| RNF01 | Segurança e privacidade | Execução local; chaves só em variáveis de ambiente, nunca em arquivo; nenhum dado de estudante; exportação de planos recusa arquivo com credencial |
| RNF02 | Rastreabilidade curricular | Código, descrição, páginas, versão e hash do catálogo ligados a cada plano |
| RNF03 | Observabilidade | Modelo, versão do prompt, estado, latência, tokens e erros por chamada; pareceres com versões de prompt, rubrica e política |
| RNF04 | Resiliência | Timeout de 90 s; até 2 novas tentativas em HTTP 503; 1 reparo de formato por chamada; intervalo de 75 s entre avaliações do Juiz e 60 s antes do reparo (cota do Groq); falha registrada, nunca convertida em plano ou parecer |
| RNF05 | Integridade | Gravações transacionais; versões imutáveis; invariantes curriculares e soma exata dos minutos |
| RNF06 | Portabilidade e manutenibilidade | Backend só com a biblioteca padrão do Python; adaptadores de LLM substituíveis; contratos JSON versionados; modos de demonstração para geração e Juiz |
| RNF07 | Usabilidade | Progresso visível, mensagens claras, layout responsivo testado a 390 px. Acessibilidade **não foi auditada** formalmente |
| RNF08 | Desempenho e custo | Latência e tokens medidos por chamada; limite diário de 8 gerações e 8 avaliações, contando falhas; sem metas de tempo |
| RNF09 | Transparência | Distingue demonstração, LLM, validação determinística, parecer do Juiz e aprovação humana; JSON técnico só em depuração |
| RNF10 | Testabilidade | Testes offline com transporte simulado, regressão, mutação manual e cenários reproduzíveis |

## 10. Regras de negócio

| ID | Regra |
|---|---|
| RN01 | Somente a habilidade confirmada pelo professor fundamenta a geração |
| RN02 | Cada plano tem uma habilidade principal e um pedido identificável |
| RN03 | Plano gerado é imutável; nova geração cria nova versão com sua trilha técnica |
| RN04 | A soma dos minutos das etapas é igual à duração da aula, em inteiros positivos |
| RN05 | Os recursos do plano são cópia exata dos informados; o prompt proíbe citar outros materiais; habilidade que exige computador sem computador nos recursos gera alerta |
| RN06 | A fonte curricular oficial não pode ser reescrita; referências adicionais só se verificáveis |
| RN07 | Instruções do usuário não sobrescrevem as invariantes de BNCC, estrutura e contrato |
| RN08 | Validação determinística, parecer da IA Juiz e aprovação são independentes; só o professor aprova |
| RN09 | Avaliação da aprendizagem (conteúdo do plano) ≠ parecer automático ≠ aprovação do professor |
| RN10 | O parecer da IA Juiz não comprova qualidade ou eficácia pedagógica |
| RN11 | Parecer não favorável dispara até N regenerações completas (padrão 1) |
| RN12 | Sem parecer favorável, entrega-se a versão com menos falhas graves (empate: a mais recente), com aviso |
| RN13 | Falha técnica (HTTP 400/413/429/503, timeout, contrato após reparo) nunca conta como parecer nem como plano |
| RN14 | O tema exibido e usado na busca e no plano é o extraído; a frase original fica guardada |
| RN15 | O uso de IA é limitado por dia; tentativas com falha contam no limite |

## 11. Dados

Tabelas SQLite reais (`aula-ia-backend/local/consultas.sqlite3`): `consultas` (contexto, candidatas e habilidade confirmada, em JSON),
`pedidos` (estado, ciclo, versão entregue, aviso, histórico), `geracoes` (versão do plano: revisão, estado, resultado com plano e
rastreio em JSON, pedido, ciclo, entregue) e `pareceres` (estado, próximo estado, versões de prompt, modelo, rubrica e política, parecer
em JSON). O plano é guardado como JSON, não normalizado. Diagrama ER em `docs/diagramas/diagramas-finais.md`.

## 12. Limitações e trabalhos futuros

**Limitações:** só o 8º ano; execução local, sem contas e sem deploy; evidências com LLM provisórias (n pequeno, um modelo por papel,
temperatura 0 não garante repetição); política do Juiz preliminar e sem adjudicação humana; regeneração não usa as críticas do Juiz;
dependência de APIs externas no plano gratuito (em 19/11, 6 de 12 gerações com falha técnica do Gemini); extração de tema por regras
(falso positivo conhecido: "lista de compras" → "Lista"); acessibilidade não auditada.

**Trabalhos futuros (previstos na R2 e não implementados):** correção dirigida só dos componentes criticados, com grafo de
invalidação (a função `invalidados` existe no contrato do Juiz, mas o fluxo não a usa); estado explícito de rejeição; regerar após a
aprovação na mesma consulta; campos opcionais de contexto; cadastro, login e privacidade entre contas; histórico de planos (o menu mostra
"Em breve"); feedback do professor; exclusão de planos; mais anos escolares; prompt 2.4 e regra de medição v2; adjudicação humana e
calibração da política; estudo com professores ou estudantes.

## 13. Histórico de versões

| Versão | Data | Mudança |
|---|---|---|
| v2.0 | 05/11/2026 | Documento de Visão e Especificação Técnica |
| v2.1-R2 | 10/11/2026 | Sem validação em campo; RF25/UC10; integrador determinístico |
| **v2.2 final** | 23/11/2026 | Conforme implementado: Juiz automático com regeneração, extração de tema, alerta de recursos, limites de uso; IDs renumerados |
