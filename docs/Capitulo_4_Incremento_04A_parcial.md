# Registro técnico — integração parcial da PoC 04A com Gemini

Este incremento conecta a geração ao validador em Python puro da branch `feat/poc04a-contratos` (commit `70cfff2`) e acrescenta um adaptador da API nativa Gemini. O contrato operacional permanece `poc04a-0.1`. A arquitetura-alvo da especificação v2.1-R2 é mais ampla e não é considerada concluída por esta entrega.

O principal problema observado na sondagem anterior foi a alteração do tipo de `metodologia` pelo integrador LLM, além de campos extras e formatos incompatíveis em respostas de especialistas. A implementação passa a validar cada saída antes de executar seus dependentes. O plano final é composto em Python, com dados curriculares e contexto obtidos das fontes confirmadas, reduzindo uma chamada gerativa. As cinco especializações compartilham um modelo Gemini e instruções próprias.

O validador existente, seus testes e arquivos de dados foram preservados integralmente. Uma camada de adaptação aproveita seus diagnósticos no rastreio e no reparo de formato. Cada especialista pode receber no máximo um reparo na mesma execução. Falhas de HTTP, transporte, bloqueio e resposta incompleta interrompem o fluxo sem fallback. O registro da tentativa permanece em SQLite; uma nova solicitação cria outra revisão. A aprovação humana é distinta da validação mecânica.

A verificação conjunta executou 64 testes: 63 aprovados e um teste opcional de busca híbrida ignorado. Os 27 casos estruturais da revisão anterior foram mantidos, incluindo respostas reais da sondagem e entradas sintéticas inválidas. Os testes adicionais exercitam composição, protocolo Gemini simulado, falhas, retentativa, isolamento concorrente e fluxo HTTP. A suíte também passou com pacotes externos desabilitados (`python -S`), confirmando a independência da biblioteca padrão no modo lexical. O teste de terminal em simulação gerou um plano com duração total de 45 minutos e salvou seu registro.

Essas evidências não comprovam funcionamento contra a API real Gemini, qualidade pedagógica ou eficácia em sala de aula. A chamada real com chave do projeto permanece pendente. A implementação também não inclui ainda as 11 seções do PlanoDeAula 2.0, avaliação em duas passagens, IDs e vínculos entre objetivos/etapas/evidências, IA Juiz, correção pedagógica dirigida nem rejeição explícita pelo usuário. Não foi realizado estudo com participantes.

Referências internas: [matriz de alinhamento](Alinhamento_PoC04A.md), [decisões de implementação](PoC04A_Gemini.md) e [componentes implementados](diagramas/PoC04A_Gemini_atual.md).
