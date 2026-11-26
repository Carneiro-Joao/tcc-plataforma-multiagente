# Correspondência de identificadores: v2.1-R2 → v2.3

> **Vale também para a [v2.4](AulaIA_Especificacao_v2.4.md)** (26/11/2026, congelamento): nenhum ID foi criado, removido ou
> renumerado. Na v2.4 mudou só o texto de RF08, RF09, RF13, RN05, RNF03 e RNF09 (PoC 11 e ajuste de 26/11).

Decisão do João (23/11/2026): renumerar a partir de RF01 no texto do TCC e guardar aqui a correspondência, para rastrear decisões
antigas, commits e documentos de PoC que citam os IDs da R2. Especificação final:
[`AulaIA_Especificacao_v2.3.md`](AulaIA_Especificacao_v2.3.md) (25/11/2026).

A v2.3 mantém todos os identificadores da v2.2 (23/11/2026) e acrescenta RN16 e RN17 (PoC 10). A correspondência anterior fica como
histórico em [`Correspondencia_IDs_v2.1R2_v2.2.md`](Correspondencia_IDs_v2.1R2_v2.2.md). Na coluna "O que mudou", "v2.3:" marca o que
mudou de 23/11 para 25/11.

## Requisitos funcionais

| v2.1-R2 | v2.3 | O que mudou |
|---|---|---|
| RF01 cadastro | — | Trabalho futuro |
| RF02 login/logout | — | Trabalho futuro |
| RF03 privacidade entre contas | — | Trabalho futuro |
| RF04 coletar contexto | **RF01** | Sem campos opcionais; tema em texto livre; recursos em lista de marcar |
| — (novo, PoC 06) | **RF02** | Extração automática do tema curto |
| RF05 validar entradas | **RF03** | — |
| RF06 recuperar habilidades | **RF04** | Busca usa o tema extraído |
| RF07 seleção no catálogo | **RF05** | — |
| RF24 abrir documento-fonte | **RF06** | — |
| RF08 exigir confirmação | **RF07** | — |
| — (novo, PoC 08) | **RF08** | Alerta habilidade × recursos |
| RF09 orquestrar especialistas | **RF09** | v2.3: uma reescrita da saída escrita sem acentuação |
| RF10 PlanoDeAula 2.0 | **RF10** | — |
| RF11 verificações mecânicas e Juiz | **RF11** | Juiz automático em todo plano gerado |
| RF12 correções dirigidas (grafo, até 2) | **RF12** | **Reescrito:** regeneração do plano inteiro (padrão 1); v2.3: informada pelas críticas do Juiz (versão anterior + críticas para cada especialista); correção dirigida só dos componentes criticados → futuro |
| — (novo, PoC 08) | **RF13** | Exibir parecer da IA Juiz ao professor |
| RF22 progresso | **RF14** | Inclui o progresso do pedido |
| RF13 estados de falha/revisão | **RF15** | Inclui pedido interrompido |
| RF15 histórico privado | — | Trabalho futuro |
| RF16 visualizar plano e fonte | **RF16** | Plano da consulta atual (sem biblioteca) |
| RF25 aceitar ou rejeitar | **RF17** | **Reescrito:** aprovar ou gerar novamente (sem estado de rejeição) |
| RF20 regerar preservando versões | **RF18** | **Reescrito:** só antes da aprovação; depois, nova consulta; v2.3: deixa explícito que "Gerar novamente" começa do zero, sem as críticas do pedido anterior |
| RF17 imprimir/PDF | **RF19** | "Baixar PDF" pela impressão do navegador |
| RF14 persistir | **RF20** | Inclui pedidos e pareceres |
| RF21 registro técnico por agente | **RF21** | — |
| RF23 inspecionar especialistas | **RF22** | Só em modo de depuração (`?depuracao=1`) |
| RF18 feedback docente | — | Trabalho futuro |
| RF19 excluir plano | — | Trabalho futuro |

## Regras de negócio

| v2.1-R2 | v2.3 | O que mudou |
|---|---|---|
| RN01 | RN01 | — |
| RN02 | RN02 | "Execução" passa a ser "pedido" |
| RN03 + RN11 | RN03 | Fundidas (repetidas) |
| RN04 | RN04 | — |
| RN05 | RN05 | **Reescrita:** cópia exata dos recursos, proibição no prompt e alerta |
| RN12 | RN06 | — |
| RN15 | RN07 | — |
| RN07 + RN13 | RN08 | Sem estado de rejeição; só o professor aprova |
| RN08 | RN09 | — |
| RN09 | RN10 | — |
| RN06 | RN11 | **Reescrita:** até N regenerações completas (padrão 1); v2.3: informadas pelas críticas; 1ª geração sem críticas |
| — (novo) | RN12 | Entrega da versão com menos falhas graves |
| — (novo) | RN13 | Falha técnica nunca conta como parecer nem plano |
| — (novo) | RN14 | Tema extraído; frase original guardada |
| — (novo) | RN15 | Limite diário de uso de IA, contando falhas |
| — (novo, PoC 10) | RN16 | v2.3: críticas do Juiz não alteram o contexto confirmado (recursos, tipo, duração, habilidade) |
| — (novo, PoC 10) | RN17 | v2.3: cada avaliação do Juiz é independente (sem críticas, parecer ou versão anterior) |
| RN10 titularidade | — | Trabalho futuro |
| RN14 grafo de invalidação | — | Trabalho futuro |

## Requisitos não funcionais

RNF01–RNF10 mantêm a numeração e a categoria; os textos foram atualizados para o que foi implementado (ver especificação §9). Na v2.3,
RNF03 (histórico da regeneração e rastreio das reescritas de acentuação), RNF04 (reescrita nunca derruba a geração) e RNF08 (reescritas
fora do limite diário) ganharam complementos.

## Casos de uso

| v2.1-R2 | v2.3 |
|---|---|
| UC04 Gerar plano de aula | UC01 Gerar plano de aula |
| UC06 Visualizar plano | UC02 Visualizar plano e parecer |
| UC10 Aceitar ou rejeitar | UC03 Aprovar plano |
| UC07 Imprimir/PDF | UC04 Baixar plano em PDF |
| UC01–03, UC05, UC08, UC09 | Trabalho futuro |
