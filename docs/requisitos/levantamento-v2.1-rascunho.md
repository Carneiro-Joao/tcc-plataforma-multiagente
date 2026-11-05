# Levantamento e revisão de requisitos — AulaIA

**Versão proposta:** 2.1-draft · 05/11/2026  
**Situação:** para revisão com João e orientador; **não substitui** a Especificação Técnica v2.0 até aprovação.  
**Fontes:** Documento de Visão e Especificação Técnica v2.0 (05/11/2026); implementação da branch `main`; `app.py`, `servico.py`, `geracao.py`, `rag/search.py`, testes e registros `Capitulo_4_Incremento_01` a `03`.  
**Recorte atual testado:** aplicação local, 8º ano da BNCC de Computação, busca lexical/demonstrativa. A busca híbrida é opcional e foi testada no incremento inicial; o modo LLM consta do código, mas não teve validação externa com provedor. **Status do software** não é sinônimo de evidência científica de qualidade pedagógica.

## 1. Convenções

- **I — implementado no recorte:** possui fluxo funcional e alguma evidência de teste local; pode ter escopo limitado.
- **P — parcial:** parte das regras atende ao requisito, mas falta capacidade essencial da redação da v2.0.
- **N — não implementado:** previsto no produto-alvo.
- **P0:** núcleo científico a validar antes da consolidação da pesquisa; **P1:** essencial para o MVP ampliado; **P2:** experiência de produto após o núcleo.
- **Critério de aceite:** condição observável proposta. Nem toda condição foi executada no código atual.

## 2. Requisitos funcionais — baseline v2.0 com diagnóstico atual

| ID | Requisito revisado | Situação | Prioridade | Critério de aceite proposto |
|---|---|---|---|---|
| RF01 | Cadastrar professor com identificador persistente e único. | N | P2 | Dois cadastros distintos não compartilham identidade; não permite duplicação do identificador. |
| RF02 | Autenticar professor e encerrar sessão. | N | P2 | Login válido cria sessão; logout invalida acesso autenticado; credenciais inválidas não entram. |
| RF03 | Proteger planos e ações pela identidade do professor. | N | P2 | Acesso cruzado aos planos e execuções de outro usuário retorna erro de autorização. |
| RF04 | Coletar ano/série, tema, duração, tipo de aula e recursos. | I | P0 | Campos presentes; enviados à API preservando valores informados. Observações são extensão prevista. |
| RF05 | Validar entradas obrigatórias antes da busca e geração. | I | P0 | Ano incompatível, tema vazio, recursos vazios, duração não inteira/inválida e tipo desconhecido retornam erro. |
| RF06 | Recuperar e ordenar habilidades da BNCC a partir do tema. | I no 8º ano | P0 | Recupera códigos válidos do catálogo com texto e referência; lexical disponível, híbrida opcional. |
| RF07 | Consultar catálogo e selecionar habilidade manualmente. | I no 8º ano | P0 | Professor pode visualizar as 11 habilidades do catálogo e selecionar uma. |
| RF08 | Exigir confirmação explícita de habilidade antes de gerar. | I | P0 | Geração sem confirmação retorna conflito; código escolhido deve constar dos candidatos. |
| RF09 | Orquestrar especialistas de acordo com dependências e contratos. | P | P0 | Cada etapa com entrada/saída JSON validada e rastreável; executar chamadas reais ao LLM em teste de integração. Regras atuais são somente demonstração. |
| RF10 | Integrar saídas em plano estruturado com objetivos, metodologia, recursos, sequência temporizada, avaliação e adaptações. | I em demonstração | P0 | Plano resultante possui campos requeridos; soma de tempos igual à duração; habilidade preservada. Qualidade por LLM pendente. |
| RF11 | Aplicar validadores determinísticos e submeter candidato à IA Juiz. | P | P0 | Estrutura, tempos e habilidade validados; parecer do Juiz devolve critérios, justificativas, falhas e decisão verificável. Hoje só existem validadores determinísticos. |
| RF12 | Encaminhar falhas corrigíveis aos agentes responsáveis, com limite de iterações. | N | P0 | Reexecução direcionada, contabilização de tentativas e encerramento ao exceder limite. Política de até 2 correções é provisória. |
| RF13 | Comunicar erro, reprovação ou limite sem classificar indevidamente plano como aprovado. | P | P0 | Erros visíveis e estados persistentes diferenciando falha, reprovação técnica, pendência humana e aprovação docente. Atualmente falha remove execução em processamento. |
| RF14 | Persistir planos concluídos e seus vínculos com contexto, habilidade, execução e proprietário. | P | P1 | Registro com identificador, conteúdo e vínculos; professor proprietário definido. Atualmente há SQLite para consultas/gerações, mas sem usuários. |
| RF15 | Listar histórico privado do professor. | N | P2 | Lista apenas planos do professor, com filtros básicos por data/estado. Não confundir com reabertura da consulta atual. |
| RF16 | Abrir um plano salvo com conteúdo e referência curricular. | P | P1 | Plano persistido recuperável por ID com origem BNCC. O fluxo atual reexibe a geração vinculada à consulta, não oferece biblioteca pessoal. |
| RF17 | Exportar em PDF legível o próprio plano persistido. | P | P1 | PDF gerado/obtido por ação explícita reproduz integralmente versão salva. Hoje existe impressão/salvar como PDF do navegador, não exportação dedicada. |
| RF18 | Registrar avaliação simples do professor sobre o plano. | N | P2 | Nota/escala e comentário opcional vinculados à geração/plano, separados do parecer da IA Juiz. |
| RF19 | Excluir plano próprio com confirmação. | N | P2 | Exclusão exige confirmação, verifica propriedade e respeita política de rastreio de pesquisa. |
| RF20 | Iniciar nova geração a partir de parâmetros recuperados, sem modificar resultado anterior. | P | P1 | Permite nova execução com parâmetros pré-preenchidos, inclusive após aprovação, conservando o plano anterior. Hoje há revisões na mesma consulta só antes da aprovação. |
| RF21 | Registrar dados técnicos por execução/agente e parecer para pesquisa. | P | P0 | Persistir ID, agente, modelo, versão do prompt, timestamps, duração, tokens/custo quando disponíveis, resultados, erros, decisões do Juiz e iteração. Atualmente há trilha JSON por etapa sem métricas completas nem Juiz. |

**Contagem da baseline (21 RF):** 6 implementados no recorte, 8 parciais e 7 não implementados. Cuidado: 'implementado' não implica pesquisa experimental concluída.

## 3. Requisitos funcionais adicionais para avaliação (NÃO aprovados ainda)

| ID proposto | Requisito | Situação atual | Por quê |
|---|---|---|---|
| RF22 | Exibir as etapas do planejamento com indicação de concluída, ativa ou pendente. | Implementado como UI | Tornar testável o indicador `Configurar aula → Escolher habilidade → Gerar e aprovar`. |
| RF23 | Permitir visualizar entradas e saídas dos especialistas associados à geração. | Implementado no fluxo atual | Complementa RF21: RF21 obriga registro técnico; RF23 dá visibilidade ao usuário/pesquisador. |
| RF24 | Permitir abrir a fonte curricular correspondente à habilidade exibida. | Implementado no fluxo atual | Dá evidência explícita à origem/explicação, sem depender apenas de RNF02. |

**Escopo opcional:** coletar observações adicionais de contexto no RF04 e incluí-las no contrato JSON; ainda não está no formulário atual. Não incluir edição manual de plano: está expressamente fora do escopo da v2.0. Não criar caso de uso distinto para “Gerar novamente”: manter como variação do UC04.

## 4. Requisitos não funcionais — revisão e medidas de verificação

| ID | Diretriz | Situação atual | Critério de verificação proposto |
|---|---|---|---|
| RNF01 | Segurança, privacidade e minimização | P | Chaves só no ambiente do servidor; credenciais não commitadas; autenticação segura quando houver usuários; autorização em rotas; sem dados pessoais sensíveis enviados a LLM sem necessidade; testes de acesso cruzado. |
| RNF02 | Rastreabilidade curricular | P | Para cada execução, registrar código e descrição oficiais, documento, versão/hash e referência aos trechos/páginas usados; não basta manter o PDF fixo no código. |
| RNF03 | Observabilidade e reprodutibilidade | P | Eventos com ID de correlação; por agente: modelo, versão do prompt, entrada/saída conforme política de privacidade, status, latência, tokens, custo e erro; exportável para experimentos. |
| RNF04 | Resiliência e tratamento de falhas | P | Timeout em chamadas; política de retry/backoff e máximo de tentativas; falha externa não é convertida em plano fictício; estado de falha recuperável. |
| RNF05 | Consistência e integridade | P | Persistência transacional; habilidade imutável após confirmação; etapas somam duração; rejeitar aprovação de revisão antiga e gravação de planos incompletos; manter trilha de falhas. |
| RNF06 | Portabilidade e independência de provedor | P | Contratos JSON versionados; serviço de LLM trocável por configuração/adaptador sem alterar orquestração; `--modo demonstracao` separado e explícito. |
| RNF07 | Usabilidade, acessibilidade e responsividade | P | Fluxo com estado de progresso e erro claro; tabulação e foco visível; labels acessíveis; contraste mínimo WCAG AA nos principais componentes; testes a 390px e desktop, sem rolagem horizontal. Acessibilidade completa ainda não auditada. |
| RNF08 | Desempenho e controle de custos | N (medição formal) | Medir latência por etapa e total, chamadas, tokens e custo por plano; definir limites/percentis após piloto em vez de inventar SLA. |

**Propostas adicionais (não aprovadas):**
- **RNF09 — Transparência:** indicar se a geração é por regras ou por LLM e distinguir validação estrutural, parecer da IA Juiz e aprovação humana; testar que o modo demonstrativo não é apresentado como IA generativa.
- **RNF10 — Testabilidade:** cenários e fixtures reproduzíveis; testes de regressão para contratos, erros, invariantes e fluxo HTTP; resultados registráveis no relatório experimental.

## 5. Regras de negócio a manter e conciliar

| RN | Texto da v2.0 e ajuste necessário |
|---|---|
| RN01 | Professor confirma a habilidade principal. **Mantida.** |
| RN02 | Plano concluído pertence a professor e habilidade principal. **Ainda sem identificação do usuário.** |
| RN03 | Planos são imutáveis. Nova geração é nova execução. **Ajustar modelo de revisões:** hoje revisões sequenciais existem apenas antes da aprovação; após aprovar é preciso iniciar outra consulta. |
| RN04 | A soma de etapas não pode ultrapassar duração. **Decisão necessária:** implementação atual exige soma **exatamente igual** à duração, regra mais rigorosa. Recomendo alinhá-las. |
| RN05 | Recursos propostos precisam ser disponíveis ou ter alternativa. **Apenas presença de texto validada:** falta checagem de adequação dos recursos. |
| RN06 | Parecer do Juiz e correção dirigida com limite. **Planejada.** |
| RN07 | Nenhum resultado não aprovado deve ser rotulado como aprovado. **Diferenciar aprovação técnica e aceitação pelo professor.** |
| RN08 | Avaliação da aprendizagem (conteúdo do plano) ≠ avaliação humana do plano. **Mantida.** |
| RN09 | Parecer da IA não constitui comprovação científica de qualidade. **Mantida.** |
| RN10 | Somente titular consulta/exporta/avalia/exclui. **Pendente de autenticação e autorização.** |

## 6. Casos de uso de referência (v2.0)

| UC | Nome | RF ligados | Estado |
|---|---|---|---|
| UC01 | Criar conta | RF01 | Não implementado |
| UC02 | Autenticar-se | RF02–03 | Não implementado |
| UC03 | Encerrar sessão | RF02 | Não implementado |
| UC04 | Gerar plano de aula (contexto, BNCC, confirmação, geração, validação e revisão) | RF04–14, RF20–21; propostas RF22–24 | Parcial (demonstração funcional) |
| UC05 | Consultar histórico | RF15 | Não implementado |
| UC06 | Visualizar plano salvo | RF16 | Parcial |
| UC07 | Exportar plano PDF | RF17 | Parcial (impressão do navegador) |
| UC08 | Avaliar plano | RF18 | Não implementado |
| UC09 | Excluir plano | RF19 | Não implementado |

O **Professor** é o ator primário; **Provedor de Modelos de IA** só como ator secundário quando modelada interação com serviço externo. Os especialistas, RAG, integrador e IA Juiz são componentes internos. Não representar “gerar novamente” como UC novo nem agentes internos como atores. Relações `<<include>>`/`<<extend>>` devem refletir comportamentos obrigatórios/opcionais corretos, não dependências cronológicas.

## 7. Inconsistências relevantes e decisões recomendadas

1. **MVP científico versus produto completo:** a especificação inclui autenticação, histórico e PDF; o protótipo executável é local, sem usuário. Evitar descrever o backlog inteiro como já pronto.
2. **Agente curricular:** hoje a recuperação é serviço de busca/catálogo; não uma chamada LLM curricular independente. A busca híbrida via embeddings é opcional. Documento-fonte não é prova automática de RAG generativo no ciclo completo.
3. **Agente de recursos:** especificação separa Metodologia e Recursos; implementação usa etapa conjunta. Decidir se desmembrar é necessidade científica ou apenas organização.
4. **Juiz e aprovação:** validações mecânicas atuais não são IA Juiz; o botão 'Aprovar' é uma decisão humana. Modelar estados e interfaces de modo distinto.
5. **Erros:** hoje, se falha a geração, o registro `processando` é removido, o que limita o estudo de falhas e latência. Para a pesquisa, manter logs sem marcar sucesso.
6. **Nova versão:** revisão do mesmo contexto antes de aprovação é útil, mas não substitui a ação de criar execução nova reutilizando parâmetros após aprovação.
7. **Plano e edição:** não criar funcionalidade de editar manualmente plano sem revisão explícita do escopo.
8. **Critérios quantitativos:** para latência, qualidade e nota mínima do Juiz, não impor valores sem piloto e orientação.

## 8. Priorização por incremento

- **P0 — núcleo científico:** finalizar RF09, RF11–13 e RF21, acrescentar rastreabilidade RNF02–04, testar LLM real, implementar e testar IA Juiz/correção, registrar falhas e custos. Preservar RF04–10 já existentes.
- **P1 — produto utilizável:** completar RF14, RF16–17 e RF20, mantendo histórico coerente de versões e PDF dedicado.
- **P2 — ampliação funcional:** RF01–03, RF15, RF18–19; priorizar autenticação antes de afirmar privacidade de histórico multiusuário.

Para o **MVP da pesquisa**, é defensável estudar inicialmente uso local individual sem contas, desde que conste expressamente da delimitação e não seja apresentado como atendimento a RF01–03/RNF01 completo. A aprovação do conjunto final e da ordem de entrega depende do orientador.

## 9. Próximos passos de modelagem

1. Validar com João quais RF propostas entram na especificação 2.1.
2. Confirmar regra da duração (soma igual ou até total) e diferença entre revisão e nova execução.
3. Fixar estados de execução/avaliação técnica/aprovação humana.
4. Atualizar caso de uso UC04, diagrama de componentes, atividades, sequência e modelo de dados.
5. Atualizar requisitos e diagramas por commit, com versão e links para testes.

**Documento de trabalho:** não afirmar que requisitos planejados passaram a existir no sistema apenas porque estão especificados.
