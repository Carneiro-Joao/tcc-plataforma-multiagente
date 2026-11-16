# Alinhamento da integração Gemini com as branches do projeto

Conferência: 16/11/2026. Continuação da branch Gemini a partir de `f6b7913`.

## Fontes conferidas

| Fonte | Commit | Tratamento nesta integração |
|---|---|---|
| `main` | `3939dfd` | Base executável das PoCs 01–03 |
| `feat/poc04a-contratos` | `70cfff2` | Incorporada ao histórico da branch Gemini, preservando seus cinco arquivos |
| `docs/diagramas-rascunho` | `33e8025` | Referência de escopo; permanece em PR separado |

Referências fixadas para esta conferência:
- [Especificação v2.1-R2](https://github.com/Carneiro-Joao/tcc-plataforma-multiagente/blob/33e8025c7bbdae8ab27c37332f2c3b9d3cc11903/docs/especificacao/AulaIA_Especificacao_v2.1_revisao_integral_R2.md)
- [Plano de implementação 04A](https://github.com/Carneiro-Joao/tcc-plataforma-multiagente/blob/33e8025c7bbdae8ab27c37332f2c3b9d3cc11903/docs/planejamento/PoC_04A_contratos_validadores_persistencia.md)
- [Diagramas R2](https://github.com/Carneiro-Joao/tcc-plataforma-multiagente/blob/33e8025c7bbdae8ab27c37332f2c3b9d3cc11903/docs/diagramas/diagramas-v2.1-R2.md)

## Aproveitamento do trabalho existente

`contratos/validacao.py` permanece a fonte da validação v0.1 e do parser estrito compartilhado. `contratos/plano_v2.py` acrescenta a validação completa das 11 seções e seus vínculos, com schema próprio versionado. Seus diagnósticos (caminho, regra, esperado e recebido quando aplicável) são aproveitados na mensagem de erro, rastreio e reparo estrutural. `contratos/execucao.py` adapta a interface para exceções do pipeline e compõe o plano em Python. O schema JSON fica como instrução enviada ao provedor, sem impor dependência de `jsonschema` ao usuário.

Preservados integralmente:
- `aula-ia-backend/contratos/__init__.py`
- `aula-ia-backend/contratos/validacao.py`
- `aula-ia-backend/tests/test_contratos.py`
- `aula-ia-backend/tests/dados/poc04a/casos_estruturais.json`
- `aula-ia-backend/tests/dados/poc04a/fixture_ordenacao.json`

A integração elimina o módulo concorrente `contratos.py` e a segunda cópia de fixtures. Isso evita colisão de imports ao reunir as branches. Não há substituição dos testes existentes pelos testes do provedor.

## Confronto com a especificação

| Requisito/decisão R2 | Evidência desta integração | Situação |
|---|---|---|
| RF09: contratos e dependências | Seis chamadas, avaliação preliminar/final, dependências validadas e reparo limitado | Implementado no fluxo; verificação real Gemini pendente |
| RF10: PlanoDeAula 2.0 | 11 seções, IDs, cobertura e vínculos objetivo–etapa–evidência | Contrato mecânico implementado; qualidade pedagógica pendente |
| RN01/RN04/RN12: fonte curricular e duração | Integrador usa catálogo/contexto confirmados; soma exata de inteiros positivos | Implementado em 2.0, com versão e hash do catálogo JSON |
| RF11/RF12/RN06/RN14: Juiz e correções dirigidas | Reparos técnicos separados; nova revisão recalcula todos os especialistas | Juiz, orçamento pedagógico e invalidação seletiva pendentes |
| RF13: falhas rastreáveis | Estado `falha`, tentativas registradas, sem plano fictício | Implementado nos caminhos tratados |
| RF14/RF21: persistência e rastreio | SQLite local; respostas, metadados, versão de contrato/prompt e erros por tentativa | Parcial: faltam modelo de execução completo e demais artefatos-alvo |
| RF25/UC10/RN13: aceitar/rejeitar | Aprovação humana explícita da revisão atual | Parcial: rejeição explícita ainda pendente |
| RN03/RN11: versões | Nova tentativa não sobrescreve anterior | Parcial: regeneração após aprovação continua bloqueada |
| Estados R2 | `processando`, `rascunho`, `aprovado`, `falha` | Parcial: enumeração de nove estados depende dos incrementos seguintes |
| Sem estudo com participantes | Fixtures, mocks, testes de serviço/HTTP | Mantido; uso funcional pelo professor não é validação em campo |
| Sem login/cadastro/histórico privado | Execução local com SQLite técnico | Mantido; persistência técnica não equivale a contas/histórico privado |

A árvore documental R2 descreve arquitetura-alvo. A implementação Gemini é **04A parcial + adaptador da 04B**, não conclusão automática da 04A nem do TCC. Os diagramas propostos e o capítulo final devem refletir a versão efetivamente demonstrada quando esses incrementos forem concluídos.

## Verificação da integração conjunta

89 testes aprovados e um teste híbrido opcional ignorado; os 27 casos estruturais anteriores continuam presentes. A suíte inclui as 11 seções, referências/IDs/cobertura, protocolo Gemini simulado com seis chamadas, reparo limitado, falhas e HTTP até aprovação docente. O JavaScript foi verificado para renderização completa, escape de HTML e leitura do legado. Nenhuma chamada real à API foi feita nesta conferência.

Próximos trabalhos: inspecionar o JSON da execução real do projeto; avaliar estabilidade e qualidade; implementar IA Juiz e correção dirigida; aceite/rejeição e estados completos. As 11 seções e as duas passagens de avaliação já fazem parte do código, com documentação atualizada nesta branch.

## Documentação da implementação atual

O [diagrama dos componentes implementados](diagramas/PoC04A_Gemini_atual.md) registra o fluxo 2.0 e suas limitações. O [registro técnico do incremento](Capitulo_4_Incremento_04A_parcial.md) fornece a evidência para o Capítulo 4. Esses documentos complementam os diagramas-alvo R2, preservados no PR documental.
