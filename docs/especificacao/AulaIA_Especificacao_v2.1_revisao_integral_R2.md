# AulaIA — Especificação Técnica v2.1 (revisão integral R2)

**Data:** 10/11/2026  
**Situação:** baseline v2.1-R2 **aprovada pelo autor em 10/11/2026**, quanto ao escopo, RF25/UC10 e integração determinística; em revisão acadêmica pelo orientador; **não mesclada à `main`**.  
**Origem:** Documento de Visão v2.0 (05/11), PoCs 01–03, revisão v2.1 inicial, decisão de **não realizar validação em campo com professores**.  
**Regra:** documentação de arquitetura-alvo não implica que esteja implementada. Não houve mudança de código nesta revisão.

**Registro de decisão 10/11/2026:** (a) aprovado o MVP de núcleo científico/técnico sem estudo de campo com professores; (b) aprovados RF25 e UC10 para aceite/rejeição explícitos, sem confundir com a IA Juiz; (c) aprovada a integração determinística em Python com cinco especialistas gerativos e um sexto componente lógico integrador. **Aprovação de escopo não é afirmação de implementação.**

## 1. Objeto, problema e delimitação

**Objeto:** concepção, implementação incremental e verificação técnica de uma plataforma web de apoio ao planejamento de aulas de Computação, com recuperação curricular da BNCC, especialistas baseados em LLM e mecanismos de verificação/correção automatizada.

**Problema técnico:** como estruturar e integrar componentes de recuperação curricular, geração especializada, validação e correção para obter planos de aula com esquema consistente, referência curricular preservada e execução rastreável?

**Pergunta orientadora:** Como projetar e implementar uma plataforma multiagente integrada à BNCC de Computação capaz de gerar planos de aula estruturados e submetê-los a verificação e correção automatizada?

**Objetivo geral:** desenvolver e verificar tecnicamente uma plataforma web que integre recuperação curricular, agentes especialistas, orquestração, validação determinística e IA Juiz para apoiar a elaboração de planos de aula de Computação.

**Objetivos específicos:**
1. Estruturar e rastrear catálogo curricular do 8º ano, com códigos e descrições oficiais.
2. Implementar interface/API para contexto pedagógico, recuperação e confirmação de habilidade.
3. Estabelecer modelo documental de plano de aula e contratos de entrada/saída por especialista.
4. Implementar integração de especialistas com LLM real e preservar invariantes curriculares/temporais.
5. Implementar IA Juiz com parecer estruturado, correções dirigidas e limite de tentativas.
6. Persistir planos, versões, falhas e trilhas técnicas da execução.
7. Demonstrar fluxos positivos e negativos por testes automatizados e cenários sintéticos/documentados, apresentando limitações.

**Não são objetivos deste TCC:** recrutamento de professores ou estudantes, entrevistas, questionários, aplicação em escola, avaliação pedagógica humana em campo, mensuração de aprendizagem, demonstração de superioridade pedagógica ou comparação estatística com validação humana. Esses assuntos são possibilidades de trabalhos futuros.

## 2. Metodologia e evidências

Estratégia de desenvolvimento incremental e verificação técnica, com PoCs como instrumentos de engenharia para descobrir lacunas, exercitar contratos e documentar evolução; **PoC não é equivalente a estudo experimental com participantes**. A classificação acadêmica formal da metodologia deve ser alinhada ao orientador.

**Evidências requeridas:** histórico Git, artefatos de requisitos e diagramas versionados, cenário sintético com entrada/saída estruturadas, testes de validação e falhas, registros de execução, demonstração em interface, indicadores técnicos (latência e consumo de tokens quando disponíveis).

**Verificação técnica ≠ validação pedagógica:** parecer da IA Juiz sinaliza conformidade automatizada com critérios, não prova qualidade educacional. A aceitação/rejeição de demonstração é uma interação funcional do usuário do protótipo, não uma avaliação de docentes participantes da pesquisa.

**Comparação A/B/C/D:** fica **fora dos critérios obrigatórios de conclusão**. Poderá ser executada como benchmark técnico exploratório se houver tempo e recursos, evitando conclusões causais ou de superioridade sem desenho controlado. Se executada, A=LLM único, B=especialistas, C=especialistas+Juiz/correção e D=LLM único+Juiz/correção, com mesmo contexto, esquema de saída e registro de versões, custos e repetições.

**Questões éticas:** sem coleta planejada de dados de participantes; usar dados sintéticos e evitar dados pessoais de estudantes nos prompts. Caso pesquisa com humanos seja retomada, definir protocolo/recrutamento e obter orientação institucional prévia sobre aprovação ética.

## 3. Fundamentação do plano de aula

**Núcleo pedagógico aprovado:** Pozzobon et al. (2025, publicação online 2026) para decisões e momentos do plano; Moreira, Lago e Figueiredo (2025) para importância e flexibilidade do planejamento; Silva, Silva e Oliveira (2025) para dificuldades relatadas; Diretrizes Curriculares de Içara (2025) para estrutura documental. O modelo abaixo é uma **adaptação do AulaIA**, não formulário nacional obrigatório nem formato diretamente extraído de uma única fonte.

**Contrato conceitual de plano — PlanoDeAula 2.0, 11 seções:**
1. Identificação: componente, ano, tema, tipo e duração.
2. Habilidade BNCC: código e descrição **idênticos** ao catálogo, eixo, objeto de conhecimento, fonte/páginas/versão.
3. Conteúdos: conceitos pertinentes.
4. Objetivo geral.
5. Objetivos específicos: observáveis e identificados por ID.
6. Metodologia.
7. Recursos didáticos: compatíveis com contexto.
8. Desenvolvimento: etapas com título, duração, ação docente, ação discente, atividade e referências aos objetivos/evidências.
9. Avaliação da aprendizagem: instrumentos, critérios e evidências relacionadas aos objetivos.
10. Estratégias inclusivas/adaptações, sem presumir diagnósticos de estudantes.
11. Referências: fonte oficial e fontes adicionais **somente quando efetivamente consultadas e verificáveis**.

**Invariantes:** duração total = soma exata de minutos inteiros e positivos; nenhum objetivo fica sem vínculo com atividade e evidência; código/texto da habilidade não podem ser modificados pelo LLM; recursos inexistentes não podem ser exigidos sem alternativa viável. Conformidade estrutural não equivale a qualidade pedagógica comprovada.

## 4. Contexto do usuário

Obrigatórios: ano escolar, tema, duração, modalidade/tipo e recursos disponíveis.  
Opcionais: conhecimentos prévios, características pedagógicas gerais da turma, restrições de infraestrutura e observações/instruções adicionais. Os opcionais são texto **não confiável**, limitado e não podem substituir instruções de sistema, fonte curricular ou regras de validação. Não solicitar nomes ou dados sensíveis de estudantes.

**Recorte técnico inicial:** somente 8º ano (11 habilidades). Preparar contratos para outros anos no futuro; não prometer cobertura curricular ampla na entrega atual.

## 5. Arquitetura de referência

- **Frontend:** React/Vite, com etapas Configurar aula → Escolher habilidade → Gerar e revisar; hoje a distribuição utiliza extensões JS/compatibilidade por limitação do build (dívida técnica registrada).
- **API Python:** validações HTTP e operações de consulta, confirmação, geração e decisão humana.
- **Recuperação curricular:** catálogo estruturado oficial, busca lexical e busca híbrida opcional por embeddings; não afirmar superioridade do RAG com 11 habilidades sem avaliação.
- **Orquestrador:** estados, dependências, retries limitados, rastreamento, grafo de invalidação e encaminhamento de correções.
- **Especialistas lógicos:** Objetivos; Avaliação (duas passagens: evidências preliminares e instrumentos finais); Metodologia e Recursos; Sequência Didática; Adaptação; Integração. A integração **será preferencialmente composição determinística**, não exigindo chamada LLM, preservando seis responsabilidades lógicas.
- **Validador determinístico:** esquema, campos, duração, identidade da habilidade, vínculos entre objetivos/etapas/evidências e restrições verificáveis.
- **IA Juiz (planejada):** parecer por critérios, defeitos, responsáveis e direcionamento de correção; não altera diretamente o documento final.
- **Persistência:** SQLite local inicialmente para consultas, gerações, versões, rastreios, pareceres e falhas. Sem suporte multiusuário na entrega do TCC.

**Ordem pretendida:** contexto e confirmação curricular → objetivos → avaliação preliminar (evidências) → metodologia/recursos → sequência → avaliação final (instrumentos) → adaptações → integração determinística → validações mecânicas → Juiz → correções dirigidas, se necessárias → disponibilização ao usuário.

**Grafo de invalidação:** se objetivos mudarem, invalidar evidências, metodologia dependente, sequência, avaliação final e adaptações afetadas; se recursos mudarem, invalidar sequência e avaliação afetadas. Corrigir somente componente isolado quando suas dependências permanecerem válidas. A política concreta deve ser coberta por testes.

**Dois tipos de retentativa, com contadores independentes:** reparo técnico de JSON/formato (limitado, sem usar orçamento de correção pedagógica) e correção pedagógica dirigida pelo Juiz (até 2 ciclos por execução, valor inicial ajustável).

## 6. Política de estados e decisão humana

Estados candidatos: `processando`, `validacao_estrutural`, `em_avaliacao`, `em_correcao`, `aguardando_decisao`, `revisao_necessaria`, `aprovado_pelo_usuario`, `rejeitado_pelo_usuario`, `falha`.

- **Parecer técnico favorável:** leva a `aguardando_decisao`, não a `aprovado_pelo_usuario`.
- **Juiz excede limite/caso crítico:** leva a `revisao_necessaria` (resultado pode ser inspecionado, jamais rotulado como aprovado).
- **Erro de API, contrato ou indisponibilidade:** `falha` com causa e rastreio preservados; jamais eliminar o registro para aparentar sucesso.
- **Aprovação/rejeição:** decisão explícita pelo usuário da aplicação; funcionalidade do produto, **não coleta de dados de pesquisa com professores**.
- **Regeneração:** plano gerado é imutável; nova tentativa cria versão/execução, sem sobrescrever anteriores. A consulta atual permite revisões pré-aprovação; reexecução após aprovação deverá ser implementada sem perda do histórico.
- **Impressão:** salvar como PDF via navegador já disponível; exportação PDF dedicada é P1 e não condição para demonstrar os agentes.

## 7. Casos de uso — versão alvo desta entrega

**Ator:** Usuário planejador (papel docente no produto; não implica participação em pesquisa). **Sistema externo opcional:** Provedor de LLM. Especialistas/RAG/Juiz são componentes internos.

| UC | Nome | Entrega |
|---|---|---|
| UC04 | Gerar plano de aula (contexto, recomendação, confirmação, geração, validação, correção) | Núcleo do MVP |
| UC06 | Visualizar plano/versão e referência curricular | MVP |
| UC07 | Imprimir/obter plano em PDF | Impressão disponível; exportação dedicada P1 |
| UC10 **novo** | Aceitar ou rejeitar plano candidato | Aprovar existente; rejeitar pendente |

**Subfunções de UC04, e não atores ou novos UCs obrigatórios:** consultar catálogo, confirmar habilidade, inspecionar rastreio e solicitar nova geração. Relações UML `include`/`extend` serão usadas somente se semanticamente corretas, não para representar ordem temporal.

**Backlog futuro FORA do escopo do TCC:** UC01 cadastro, UC02 login, UC03 logout, UC05 histórico privado, UC08 feedback docente estruturado, UC09 excluir plano próprio, integrações escolares, edição manual e estudos com participantes. Seus IDs são preservados para rastreabilidade histórica, mas **não aparecem como recursos exigidos no MVP**.

## 8. Requisitos funcionais — versão do TCC

| ID | Requisito revisado | Prioridade | Estado diante das PoCs 01–03 |
|---|---|---|---|
| RF04 | Coletar contexto obrigatório e opcionais previstos | P0 | Parcial (obrigatórios implementados) |
| RF05 | Validar entradas e impedir chamadas inválidas | P0 | Implementado no recorte, novos campos pendentes |
| RF06 | Recuperar habilidades oficiais por tema e mostrar fonte | P0 | Implementado no 8º ano; híbrido opcional |
| RF07 | Permitir seleção manual da habilidade | P0 | Implementado |
| RF08 | Exigir confirmação antes da geração | P0 | Implementado |
| RF09 | Orquestrar especialistas com contratos e dependências | P0 | Parcial (demonstração testada; LLM externo não validado) |
| RF10 | Produzir PlanoDeAula 2.0 completo | P0 | Parcial (campos do modelo novo ausentes) |
| RF11 | Executar verificações mecânicas e IA Juiz | P0 | Parcial (somente mecânicas) |
| RF12 | Correções dirigidas com grafo de dependências e limite | P0 | Não implementado |
| RF13 | Registrar e informar estados de falha/revisão | P0 | Parcial (falha hoje é removida do banco) |
| RF14 | Persistir execução, plano, habilidade e versões | **P0** | Parcial (SQLite atual sem trilha completa) |
| RF16 | Visualizar versão gerada e fonte da BNCC | P1 | Parcial (consulta atual recuperável) |
| RF17 | Obter plano imprimível/PDF | P1 | Parcial (impressão via navegador) |
| RF20 | Regerar preservando versões, inclusive após aprovação | P1 | Parcial (apenas antes da aprovação) |
| RF21 | Registrar execução por agente, falhas, modelo, prompts e métricas | **P0** | Parcial |
| RF22 **novo na v2.1** | Mostrar progresso do planejamento | P1 | Implementado na PoC 03 |
| RF23 **novo na v2.1** | Inspecionar entradas e saídas dos especialistas | P1 | Implementado no recorte |
| RF24 **novo na v2.1** | Abrir documento de origem da habilidade | P0 | Implementado |
| RF25 **novo na revisão R2** | Permitir aceitar/rejeitar plano explicitamente e registrar decisão | P0 | Parcial (aceitar sim, rejeitar não) |

**Preservados somente como backlog futuro fora do escopo:** RF01 cadastro, RF02 login/logout, RF03 privacidade entre contas, RF15 histórico privado, RF18 feedback de docente, RF19 exclusão privada. Não tratar esses IDs como pendência de entrega do TCC.

**P0:** indispensável para demonstrar núcleo técnico. **P1:** necessário para usabilidade/entrega apresentável, mas pode ter solução simplificada. **Futuro:** fora da avaliação de conclusão.

## 9. Requisitos não funcionais — versão do TCC

| ID | RNF e critério de verificação |
|---|---|
| RNF01 | Segurança/privacidade: servidor local, segredo fora do código, sem dados de estudantes, validação e tratamento de instruções do usuário como dados não confiáveis |
| RNF02 | Rastreabilidade curricular: documento, versão/hash, código, descrição e páginas ligados à execução |
| RNF03 | Observabilidade: modelo, versão de prompt, status, duração, tokens e erros por chamada quando disponíveis |
| RNF04 | Resiliência: timeout, reparo de formato limitado, falhas explícitas, sem geração fictícia após erro |
| RNF05 | Integridade: gravações transacionais, versões imutáveis, invariantes curriculares, tempo exato e estados coerentes |
| RNF06 | Portabilidade: interface de provedor substituível, contrato JSON versionado, demo/LLM separados |
| RNF07 | Usabilidade/acessibilidade: progresso, mensagens claras, operação por teclado, layout responsivo e teste de contraste/foco |
| RNF08 | Desempenho/custo: coletar latência e uso/custo por execução, sem declarar metas arbitrárias como validadas |
| RNF09 **novo** | Transparência: diferenciar modo demo, LLM, validação determinística, Juiz e decisão humana |
| RNF10 **novo** | Testabilidade: fixtures, testes offline de provedor, regressão, cenários sintéticos reproduzíveis |

## 10. Regras de negócio — revisadas

| ID | Regra |
|---|---|
| RN01 | Somente habilidade escolhida/confirmada pode fundamentar a geração |
| RN02 | Cada plano tem uma habilidade principal e uma execução identificável; proprietário é requisito futuro |
| RN03 | Plano gerado imutável; nova execução/versionamento preserva o anterior |
| RN04 | Soma dos minutos = duração total, com inteiros positivos |
| RN05 | Recursos e atividades devem ser compatíveis ou conter alternativas |
| RN06 | Juiz produz parecer e permite até duas correções pedagógicas dirigidas inicialmente |
| RN07 | Avaliação mecânica, parecer do Juiz e aceite humano são independentes; sem rótulo indevido |
| RN08 | Avaliação da aprendizagem no plano ≠ parecer automático ≠ aceitação/feedback de uso |
| RN09 | Juiz automático não comprova eficácia/qualidade pedagógica em escola |
| RN10 | Regra de titularidade entre contas **futura**, não aplicável ao ambiente local sem login |
| RN11 **novo** | Cada nova geração mantém versão imutável e trilha técnica |
| RN12 **novo** | Fontes curriculares oficiais não podem ser reescritas; bibliografia adicional apenas se verificável |
| RN13 **novo** | Rejeição/aceitação pelo usuário são ações explícitas com estados distintos |
| RN14 **novo** | Alterar objetivo invalida saídas dependentes; correção segue grafo de dependências |
| RN15 **novo** | Instruções de usuário não podem sobrescrever invariantes de segurança, BNCC e contratos |

## 11. Dados conceituais

**Núcleo a implementar:** `ContextoAula` → `ConsultaCurricular` → `HabilidadeBNCC`/ `DocumentoBNCC` → `ExecucaoGeracao` → `PlanoDeAula` (versões) + `ExecucaoAgente` + `ParecerJuiz` + `DecisaoUsuario`. Cada execução de agente armazena tipo, modelo, prompt/contrato, entrada/saída saneadas, duração, tokens e erro quando existentes.

**Não necessários agora:** `Professor` com credenciais, `AvaliacaoProfessor` baseada em estudo com participantes, `CenarioExperimental`, `ConfiguracaoExperimental`, `AvaliacaoExperimental` cega e instrumentos de recrutamento. Não modelar tabelas que não correspondam ao escopo atual.

## 12. Plano de verificação técnica (sem participantes externos)

| Cenário | Resultado exigido |
|---|---|
| Consulta lexical de ordenação | Recuperar candidato oficial pertinente com referência |
| Consulta sem resultados | Oferecer catálogo manual; não escolher habilidade silenciosamente |
| Busca híbrida opcional | Não afirmar qualidade por pontuação isolada; quando testada, comparar com gabarito sintético |
| Tentativa de gerar sem confirmação | Bloqueio |
| Geração demo | Plano completo na estrutura correspondente à versão do contrato |
| Geração por LLM real | Pelo menos um fluxo de ponta a ponta ou registro honesto de falha |
| LLM retorna JSON inválido | Reparação limitada ou falha rastreável |
| Mudança de código/texto da BNCC pelo LLM | Rejeitar e/ou reconstruir exclusivamente da fonte oficial |
| Tempos incompatíveis | Reparação determinística controlada ou falha; sem aprovar dado inválido |
| Falha do provedor | Erro persistido sem criar plano fictício |
| Parecer Juiz desfavorável | Correção dirigida e revalidação com orçamento de 2 ciclos |
| Alteração de objetivos | Regenerar dependentes coerentemente |
| Resultado tecnicamente aceito | Exibir para decisão do usuário, sem aprovação humana automática |
| Aceite/rejeição explícitos | Estados e registros distintos e imutáveis |
| Impressão/PDF | Documento legível correspondente à versão exibida |

Os cenários devem ser descritos com entrada, resultado esperado, teste executado e evidência; não há entrevistas, questionários ou aplicação em escola.

## 13. Sequência de incrementos (sem data artificial)

- **Inc. 04A — Contratos, dados e segurança:** PlanoDeAula 2.0, esquema por especialista, invariantes, integrador determinístico, rastreio de falhas, testes offline.
- **Inc. 04B — LLM real:** provider adapter, execução sequencial com duas passagens de avaliação, métricas, testes de integração.
- **Inc. 05 — IA Juiz:** rubrica operacional, parecer, correção dirigida, invalidação, limite, estados e testes negativos.
- **Inc. 06 — Consolidação:** UI de estados/aceite e rejeição, apresentação de planos, impressão/PDF, screenshots e evidências para Capítulo 4, diagrama atualizado e demonstração final.
- **Futuro:** login, multiusuário, histórico privado, edição manual, estudo com professores, avaliação em campo e estudos comparativos rigorosos.

## 14. Critério de conclusão e limitações

O TCC atinge seu objetivo técnico quando apresenta **fluxo integrado funcional** (contexto → habilidade confirmada → especialistas de IA → integração validada → parecer do Juiz → correção, quando exigida → resultado e decisão do usuário), demonstrado por testes e documentação da arquitetura. Se algum componente não for concluído, reportar alcance e limitações com precisão, sem classificá-lo como implementado.

**Limitações expressas:** recorte curricular 8º ano, cenário local controlado, ausência de validação docente/impacto em aprendizagem, qualidade do Juiz não aferida por especialistas humanos, ausência de garantia de acerto pedagógico.

## 15. Referências e trabalhos relacionados (ponto de partida)

**Núcleo aprovado do modelo pedagógico:**
- POZZOBON, M. C. C. et al. A fase de planeamento num estudo de aula: a tarefa e o plano de aula. *Educación Matemática*, v.37, n.3, p.99–126, 2025 (online 2026). DOI: 10.24844/em3703.04.
- MOREIRA, G. G. F.; LAGO, N. A. do; FIGUEIREDO, F. J. Q. de. Bridging theory and **pratice**: insights on lesson planning from English teachers. *SOLETRAS*, n.53, 2025. DOI: 10.12957/soletras.2025.93184. **Nota:** “pratice” aparece no título editorial do artigo; manter como publicado em citações, sem corrigir silenciosamente.
- SILVA, D. N. da; SILVA, Y. M. da; OLIVEIRA, L. D. de. Percepções de professores acerca do planejamento de ensino: dificuldades encontradas e soluções propostas para a prática docente. *Revista Interacções*, v.21, n.70, p.1–28, 2025. DOI: 10.25755/int.33415.
- IÇARA (SC). Secretaria Municipal de Educação, Ciência e Tecnologia. *Diretrizes Curriculares do Ensino Fundamental do Município de Içara/SC*. Içara, 2025.

**Fundamentação técnica ainda a redigir e referenciar no TCC:** recuperação aumentada por geração e busca híbrida, arquitetura multiagente baseada em LLM, saídas estruturadas, IA Juiz e limites/vieses, verificação de software e rastreabilidade. Não tomar exemplos de ferramentas como comprovação científica.

**Status final:** decisões de escopo e arquitetura-base aprovadas por João em 10/11/2026. Detalhes de contratos, tratamento de revisões e políticas de estados são refinamentos técnicos ainda pendentes. Revisão acadêmica pelo orientador ainda necessária. Nenhum componente do software foi alterado por este documento.

## 16. Pontos de projeto a detalhar na PoC 04A (sem reabrir decisões aprovadas)

1. Definir esquema JSON exato e versionado do plano e de cada agente, incluindo tipos, IDs de objetivos/evidências e regras de validação.
2. Decidir a política de exibição e eventual aceite explícito de um plano com estado `revisao_necessaria`, sem rótulo de aprovação técnica; documentar transições válidas.
3. Definir como registrar artefatos de correção, erros, custos, tempos e prompts de maneira compatível com privacidade e reprodutibilidade.
4. Precisar a política de reparo determinístico dos minutos e seu limite; sem alterar silenciosamente o sentido pedagógico.
5. Separar testagem do modo demonstração e execução real LLM; definir os cenários mínimos de aceite da PoC 04A.
