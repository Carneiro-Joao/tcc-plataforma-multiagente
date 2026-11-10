# AulaIA — Plano de implementação da PoC 04A (pré-implementação)

**Data:** 10/11/2026  
**Base aprovada:** [Especificação v2.1-R2](../especificacao/AulaIA_Especificacao_v2.1_revisao_integral_R2.md) e [Diagramas v2.1-R2](../diagramas/diagramas-v2.1-R2.md).  
**Estado:** planejamento técnico para implementação posterior; **nenhum código alterado**.

## 1. Resultado verificável do incremento

Ter um contrato estruturado **PlanoDeAula 2.0**, contratos individuais para os cinco especialistas gerativos, um **integrador Python determinístico**, regras de integridade e rastreabilidade persistente para sucesso/falha, com testes automatizados offline. Ainda não pressupõe funcionamento de IA Juiz nem validação de LLM contra API real (PoC 04B).

## 2. Interfaces e contratos a formalizar

| Artefato | Entrada | Saída | Invariantes |
|---|---|---|---|
| ContextoAula 2.0 | ano, tema, duração, tipo, recursos, opcionais | objeto validado | limitações de tamanho, duração inteira e sem dados pessoais |
| HabilidadeConfirmada 1.0 | catálogo oficial e escolha do usuário | código/texto/eixo/objeto/fonte/hash | somente fonte oficial, nunca reescrita por LLM |
| Objetivos 2.0 | contexto + habilidade | conteúdos, objetivo geral, lista de objetivos específicos com IDs | objetivos não vazios e IDs distintos |
| AvaliacaoPreliminar 1.0 | objetivos + contexto/habilidade | evidências pretendidas e critérios por objetivo | cada objetivo recebe evidência verificável |
| MetodologiaRecursos 2.0 | objetivos/evidências + contexto | metodologia, recursos e estratégias | recursos compatíveis com contexto |
| SequenciaDidatica 2.0 | objetivos, critérios, metodologia/recursos | etapas com ID, ações docentes/discentes, tempos, objetivos relacionados | etapas válidas; duração total igual ao contexto |
| AvaliacaoFinal 2.0 | evidências, objetivos e sequência | instrumentos, critérios e evidências vinculados | rastreabilidade objetivo → etapa → evidência |
| Adaptacao 2.0 | contexto e proposta didática | alternativas inclusivas sem diagnósticos presumidos | viáveis e não contraditórias |
| PlanoDeAula 2.0 | saídas aceitas de especialistas + fonte oficial | plano com 11 seções | integrador apenas compõe; sem criar texto oficial |
| TrilhaExecucao 1.0 | eventos e retornos | IDs, estados, modelo, prompt/contrato, tempos, tokens disponíveis, erros | falha persiste; não se apresenta como sucesso |

**Nota:** um único especialista de avaliação produz dois contratos (`AvaliacaoPreliminar`, `AvaliacaoFinal`) em chamadas distintas. O sexto papel, Integrador, é determinístico em Python.

## 3. Ordem de implementação proposta

1. **Fixture e JSON Schema/Pydantic:** iniciar pelo contrato final `PlanoDeAula 2.0` e os contratos de todas as etapas. Produzir um objeto válido de referência e casos inválidos.
2. **Integrador determinístico:** compor plano a partir das saídas validadas e reinjetar a habilidade official do catálogo; não aceitar descrição vinda do LLM como fonte de verdade.
3. **Validadores por etapa:** validar tipos, campos requeridos, IDs e vínculos imediatamente após cada especialista; distinguir reparo de tipo/estrutura de correção pedagógica.
4. **Tratamento de duração:** calcular e verificar soma exata; aceitar somente políticas de ajuste determinístico que preservem passos/objetivos, com trilha do ajuste. Não modificar texto pedagógico sem rastreio.
5. **Persistência de execução/erro:** alterar a política atual que apaga gerações que falharam; registrar causa, etapa, status e tempos.
6. **Testes offline do provedor:** mockar resposta JSON válida, JSON inválido, texto BNCC alterado, minutos como string, soma inconsistente, timeout e erro HTTP. Falhas não passam como sucesso.
7. **Verificação transversal:** atualizar os RF09–14, RF21 e RF25 se algum contrato mudar; refletir mudanças em RN, UC04/UC10, componentes, atividades, sequência, classes/dados, testes e Capítulo 4.
8. **Revisão da PoC 04A:** demonstrar uma execução de ponta a ponta em modo demo obedecendo ao contrato novo e regressão automática passando, sem prometer que IA real foi testada.

## 4. Critérios mínimos de aceite

- O plano contém as 11 seções e todas as referências necessárias são verificáveis.
- O código **e a descrição oficial** são imutáveis e obtidos exclusivamente do catálogo.
- Cada objetivo tem ligação explícita com etapa e evidência de avaliação.
- A soma dos minutos é igual à duração solicitada; inteiros positivos.
- Todas as etapas têm saídas validadas independentemente antes de avançar.
- Falha intermediária tem registro rastreável e não aparece como plano aprovado.
- Nenhum fluxo do modo demonstração é identificado como geração real por IA.
- Testes de contratos, erros, validações, persistência e regressão passam offline.
- Requisitos, regras, casos de uso, diagramas e capítulo técnico são confrontados e atualizados no mesmo incremento.

## 5. Decisões secundárias a documentar durante a implementação

- Limites de tamanho dos textos opcionais e mensagens de validação.
- Enumeração exata de estados de execução e de decisão do usuário (inclui rejeição).
- Política de ajuste de tempos e reparos de JSON/limites de tentativas, com logs.
- Forma de serializar referências/fontes e estratégias inclusivas.
- Mapeamento de arquivos e módulos da refatoração sem quebrar a UI atual.
- Momento de migrar para React nativo (preferência após o núcleo técnico).

## 6. Fora do incremento

Não implementar ainda a IA Juiz (PoC 05), avaliação pedagógica com professores, benchmark A/B/C/D, login/multiusuário, histórico privado ou reescrita integral do frontend. Teste LLM real fica no Inc. 04B.

## 7. Política de atualização documental contínua

Para cada alteração funcional, verificar **sempre**: requisitos RF/RNF → regras RN → casos de uso UC → componentes/atividades/sequência/dados → contratos → testes → Capítulo 4 → histórico Git. Marcar claramente 'implementado', 'parcial' ou 'planejado' com evidências; não elevar status só por ter sido documentado.
