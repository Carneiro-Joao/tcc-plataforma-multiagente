# Alinhamento da integração Gemini com as branches do projeto

Conferência: 14/11/2026.

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

`contratos/validacao.py` permanece a fonte da validação local. Seus diagnósticos (caminho, regra, esperado e recebido quando aplicável) são aproveitados na mensagem de erro, rastreio e reparo estrutural. `contratos/execucao.py` adapta a interface para exceções do pipeline e compõe o plano em Python. O schema JSON fica como instrução enviada ao provedor, sem impor dependência de `jsonschema` ao usuário.

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
| RF09: contratos e dependências | Validação imediata, apenas dependentes validados, um reparo estrutural | Parcial: falta avaliação em duas passagens |
| RF10: PlanoDeAula 2.0 | Contrato operacional v0.1 com 13 campos | Parcial: faltam as 11 seções completas, IDs e vínculos |
| RN01/RN04/RN12: fonte curricular e duração | Integrador usa catálogo/contexto confirmados; soma exata de inteiros positivos | Implementado no contrato v0.1 |
| RF11/RF12/RN06/RN14: Juiz e correções dirigidas | Reparos técnicos separados; nova revisão recalcula todos os especialistas | Juiz, orçamento pedagógico e invalidação seletiva pendentes |
| RF13: falhas rastreáveis | Estado `falha`, tentativas registradas, sem plano fictício | Implementado nos caminhos tratados |
| RF14/RF21: persistência e rastreio | SQLite local por padrão; respostas, metadados e erros por tentativa | Parcial: faltam modelo de execução completo, versão de prompt e demais artefatos-alvo |
| RF25/UC10/RN13: aceitar/rejeitar | Aprovação humana explícita da revisão atual | Parcial: rejeição explícita ainda pendente |
| RN03/RN11: versões | Nova tentativa não sobrescreve anterior | Parcial: regeneração após aprovação continua bloqueada |
| Estados R2 | `processando`, `rascunho`, `aprovado`, `falha` | Parcial: enumeração de nove estados depende dos incrementos seguintes |
| Sem estudo com participantes | Fixtures, mocks, testes de serviço/HTTP | Mantido; uso funcional pelo professor não é validação em campo |
| Sem login/cadastro/histórico privado | Execução local com SQLite técnico | Mantido; persistência técnica não equivale a contas/histórico privado |

A árvore documental R2 descreve arquitetura-alvo. A implementação Gemini é **04A parcial + adaptador da 04B**, não conclusão automática da 04A nem do TCC. Os diagramas propostos e o capítulo final devem refletir a versão efetivamente demonstrada quando esses incrementos forem concluídos.

## Verificação da integração conjunta

63 testes aprovados e um teste híbrido opcional ignorado; os 27 casos estruturais anteriores continuam presentes. Os testes adicionais cobrem integração determinística, adaptação dos diagnósticos, protocolo Gemini simulado, reparo, erros e fluxo HTTP. Nenhuma chamada real à API foi feita nesta conferência.

Próximos trabalhos permanecem explícitos: sondagem real com chave Free Tier; PlanoDeAula 2.0 e avaliação em duas passagens; IA Juiz e correção dirigida; aceite/rejeição e estados completos; consolidação de diagramas e Capítulo 4. Não é necessário substituir o trabalho de contratos para executar a sondagem Gemini v0.1.

## Documentação da implementação atual

O [diagrama dos componentes implementados](diagramas/PoC04A_Gemini_atual.md) registra o fluxo v0.1 e suas limitações. O [registro técnico do incremento](Capitulo_4_Incremento_04A_parcial.md) fornece a evidência para o Capítulo 4. Esses documentos complementam os diagramas-alvo R2, preservados no PR documental.
