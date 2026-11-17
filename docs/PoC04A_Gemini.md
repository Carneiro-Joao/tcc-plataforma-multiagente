# PoC 04A — Gemini e contrato completo

Revisão: 16/11/2026. Base executável: `3939dfd`; contratos originais: `70cfff2`; referência documental R2: `33e8025`; integração Gemini anterior: `f6b7913`.

O incremento implementa o contrato `plano-aula-2.0`, com 11 seções e avaliação preliminar/final. Isso fecha a definição mecânica do plano; não conclui Juiz, correção pedagógica ou os estados completos da PoC. Consulte o [contrato](Contrato_PlanoDeAula_2_0.md) e a [matriz R2](Alinhamento_PoC04A.md).

## Problema observado e decisões

Na sondagem OpenRouter, seis chamadas terminaram com `stop`, mas o plano foi rejeitado: metodologia, antes string, voltou como objeto no integrador. A rodada usou modelos diferentes, consumiu 21.441 tokens conhecidos e levou 174,976 segundos. Esses dados descrevem aquela rodada, não uma comparação entre provedores.

A geração agora usa Gemini nativo por REST, sem SDK nem fallback. Cinco especialidades compartilham o modelo configurado, inicialmente `gemini-3.5-flash-lite`. A avaliação possui duas chamadas: fixa critérios/evidências antes das atividades e instrumentos/procedimentos depois. O integrador é Python, com mapeamento explícito. Contexto e metadados BNCC são imutáveis; versão/hash identificam o catálogo JSON utilizado.

Cada saída é validada antes dos dependentes. IDs, cobertura, duração e fontes são verificados localmente. O Gemini recebe `generationConfig.responseFormat.text`, `mimeType: APPLICATION_JSON` e uma projeção estrutural do schema da etapa. Os limites e formatos ficam como descrições e continuam obrigatórios localmente. A documentação oficial de `generateContent` e do modelo foi conferida em 16/11/2026; isso não substitui executar uma requisição com chave do projeto.

A documentação também informa que certas restrições, como `uniqueItems` e `minLength`, não são impostas pela geração estruturada do servidor. O validador local mantém essas regras. Tipos incompatíveis, extras e valores vazios são recusados sem coerção. Não se transforma objeto em texto para aparentar sucesso.

## Dependências e retentativas

A ordem é objetivos → avaliação preliminar → metodologia → sequência → avaliação final → adaptação. Cada chamada recebe as dependências declaradas em `contratos/plano_v2.py`. O integrador reúne as saídas validadas; código e texto oficiais vêm do catálogo confirmado, nunca de uma resposta LLM.

São seis chamadas normais e até 12 tentativas estruturais se cada uma precisar do único reparo técnico permitido. `--reparos 0` desabilita reparos. No site, somente HTTP 503 permite duas novas tentativas na mesma etapa, com espera crescente e variação aleatória; `--repeticoes-503 0` desativa essa recuperação. São no máximo 18 requisições sem reparos ou 36 com reparos. O teste de terminal mantém erros HTTP sem repetição. Outros erros HTTP, timeout, bloqueio e término diferente de `STOP` encerram a execução. O reparo conserva entrada/dependências e registra a tentativa anterior. Nova geração manual cria outra revisão e recalcula o fluxo completo; invalidação seletiva e orçamento pedagógico ficam para o Juiz.

## Observabilidade e compatibilidade

`teste_gemini.py` usa por padrão o mesmo contrato do site. O JSON registra entrada, envelope da API, conteúdo bruto, modelo respondido, `usageMetadata`, `finishReason`, status HTTP, latência, versões de contrato/prompt e tentativas. Ausência de uso não é interpretada como ausência de consumo. Cabeçalhos e credenciais não são gravados; a chave é enviada em `x-goog-api-key` e removida se for ecoada.

Quando há recuperação de HTTP 503 no site, `chamadas_http` informa a quantidade real de requisições daquela tentativa estrutural. `falhas_http_transitorias` conserva cada 503 intermediário, seu corpo redigido, latência e espera; a resposta final fica nos campos usuais da etapa.

`inspecionar_gemini.py` revalida registros já salvos, inclusive v0.1, sem novas chamadas. Informa o modo declarado e consumo conhecido e compara o plano com a recomposição das saídas. Não autentica a origem de arquivos editáveis.

Os cinco arquivos originais do contrato v0.1 permanecem idênticos; o contrato completo está em novos módulos. Planos antigos continuam legíveis, sem migração destrutiva. Consultas antigas sem metadados do catálogo exigem nova consulta antes de gerar 2.0. O serviço mantém SQLite local para versões, aprovações e falhas; não implementa contas ou histórico privado. A branch documental e seu PR continuam separados.

## Evidências e limites

- 115 testes Python: 114 aprovados e um teste híbrido opcional ignorado, também com `python -S`.
- Os 27 casos estruturais anteriores continuam exercitados.
- Transporte Gemini simulado: seis chamadas, reparo, falhas parciais e limite de 12 chamadas.
- HTTP local: confirmação, geração 2.0, rascunho e aprovação humana; falha não pode ser aprovada.
- Renderização JavaScript: 11 seções, leitura do legado e escape de HTML; `public` e `dist` iguais.
- CLI simulado com 45 minutos; inspeção do registro sem chave e sem rede.
- A execução parcial inicial apresentou três etapas válidas e falha por complexidade. Posteriormente, uma geração completa no protótipo concluiu as seis etapas e a integração em 38,281 s, com 8 requisições, duas recuperações de 503 e 7.831 tokens conhecidos. O plano persistido foi revalidado offline e permanece rascunho.

O [registro inicial](Execucao_Gemini_2026-11-16.md) documenta a execução parcial. O [estado atual do protótipo](Prototipo_Local_2026-11-16.md) registra a geração completa e diferencia o prompt 2.1 observado da versão consolidada 2.2, validada offline. A qualidade pedagógica e a estabilidade por múltiplas rodadas ainda precisam ser avaliadas. Cotas, disponibilidade e gratuidade dependem do projeto; o script não consulta faturamento e não troca de modelo.

IA Juiz independente, rubrica, correção dirigida, rejeição explícita e experimento comparativo continuam pendentes. A validação mecânica não aprova pedagogicamente um plano. Não foi realizado estudo com participantes.

Referências oficiais: [modelo](https://ai.google.dev/gemini-api/docs/models/gemini-3.5-flash-lite), [generateContent](https://ai.google.dev/api/generate-content), [saída estruturada](https://ai.google.dev/gemini-api/docs/structured-output), [preços](https://ai.google.dev/gemini-api/docs/pricing) e [limites](https://ai.google.dev/gemini-api/docs/rate-limits).
