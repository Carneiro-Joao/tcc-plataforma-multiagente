# Protótipo local — consolidação de 16/11/2026

Branch de trabalho: `feat/poc04a-prototipo-local`. Esta etapa reúne o protótipo Windows, as correções locais e o commit remoto `723181a`, preservando o contrato `plano-aula-2.0`.

## Funcionalidades consolidadas

- Inicialização por `INICIAR_AULAIA.cmd`, com janela **Colar chave** / **Iniciar protótipo**, chave apenas em memória e abertura do navegador.
- Site e teste de terminal com opção IPv4, mantendo HTTPS e validação de certificado. O diagnóstico local encontrou resets intermitentes no IPv6.
- Projeção do esquema em `contratos/esquema_gemini.py`: estrutura e tipos na API; limites, formatos e relações continuam obrigatórios no Python.
- Mensagens específicas para chave inválida, esquema complexo, alta demanda e falhas de conexão, com remoção da chave dos registros.
- No site, até duas novas tentativas somente para HTTP 503, com espera de 2–3 e 4–5 segundos, preservando etapas anteriores. O teste de terminal mantém essa repetição desativada.
- Rastreio das requisições extras em `chamadas_http` e `falhas_http_transitorias`; falhas persistem no SQLite local.
- Catálogo BNCC com quebras LF definidas por `.gitattributes`, preservando seu hash entre Windows e Linux.
- Scripts exploratórios antigos de OpenAI e OpenRouter preservados como histórico. Eles dependem da integração antiga; o fluxo atual usa `teste_gemini.py` ou o site.

## Execução completa observada

Fonte: geração `d37f8d158fdc4781b0936e8422761bd6` em `aula-ia-backend/local/consultas.sqlite3`, revisão 1, estado `rascunho`. Data de criação: **16/11/2026 às 21:38:52 em America/Fortaleza** (`2026-11-17 00:38:52` UTC no banco).

Modelo pedido/respondido: `gemini-3.5-flash-lite`. Modo: `ia`. Contrato: `plano-aula-2.0`. Prompt registrado: `especialistas-plano-2.1`.

| Etapa | Requisições HTTP | HTTP final | Estado |
|---|---:|---:|---|
| Objetivos | 2 | 200 | Validado após um 503 |
| Avaliação preliminar | 1 | 200 | Validado |
| Metodologia | 1 | 200 | Validado |
| Sequência | 1 | 200 | Validado |
| Avaliação final | 2 | 200 | Validado após um 503 |
| Adaptação | 1 | 200 | Validado |
| Integrador Python | 0 | — | Validado |

Tempo total registrado: **38,281 s**. Total: **8 requisições HTTP**, com seis respostas concluídas e dois 503 intermediários. Foram informados **7.831 tokens** nas seis respostas com metadados de uso; a ausência de uso nos erros não significa consumo zero. O plano persistido foi revalidado offline pelo contrato completo.

SHA-256 do texto UTF-8 da coluna `resultado`: `43afd5d4d75a68f086d09a7f9d916b92ae7258d09121f615d32ff473a0a1a1cc`.

O banco, os registros brutos e as chaves não são publicados. Estes números descrevem uma execução local observada, sem autenticação externa do arquivo, comprovação de faturamento ou avaliação pedagógica. A [falha parcial anterior](Execucao_Gemini_2026-11-16.md) fica preservada como histórico.

## Integração e verificação

A consolidação utiliza a projeção compartilhada do commit remoto e preserva sua orientação sobre recursos de escrita. O prompt resultante é `especialistas-plano-2.2`, com `versao_esquema_api: plano-2.0-estrutura-v1`. A execução real acima ocorreu antes dessa consolidação e não deve ser atribuída retroativamente ao prompt 2.2.

Verificações da versão integrada: **115 testes Python, 114 aprovados e 1 híbrido opcional ignorado**, tanto na execução normal quanto com `python -S`; sintaxe JavaScript validada e arquivos `public/geracao-ui.js` e `dist/geracao-ui.js` idênticos. Os testes cobrem os dois lados da integração, preservação dos contratos, recursos de inicialização, rede, sigilo da chave, limite de repetição e fluxo HTTP.

A validação pedagógica, IA Juiz, rubrica, correção dirigida, estudo com participantes e demonstração de estabilidade por múltiplas execuções continuam pendentes. O próximo passo pode acrescentar os novos arquivos e evidências nesta mesma branch.
