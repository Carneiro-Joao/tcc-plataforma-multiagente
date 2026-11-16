# Execução real Gemini — 16/11/2026

Registro analisado: `20261116-104248-7f7fbf52.json`, fornecido pelo usuário. Data/hora declarada: 16/11/2026, 10:42:48 em America/Fortaleza. SHA-256 do arquivo: `ec5273d142bee64536ba7e37cac20003fc2ff7f1f617189d85c0e6f04d634d64`. O arquivo bruto não é publicado no repositório.

Entrada: 8º ano, ordenação, 50 minutos, papel e cartões, Computação desplugada, habilidade EF08CO03. Modelo pedido/respondido nas chamadas bem-sucedidas: `gemini-3.5-flash-lite`. Contrato `plano-aula-2.0`; prompt `especialistas-plano-2.0`. O arquivo declara `rede: ipv4`, ajuste local que não estava no GitHub conferido nesta revisão.

## Resultado observado

| Chamada | HTTP | Tempo | Tokens informados | Resultado |
|---|---|---:|---:|---|
| objetivos | 200 | 2,004 s | 714 | JSON e contrato válidos; 3 objetivos |
| avaliacao_preliminar | 200 | 1,887 s | 956 | JSON, IDs e cobertura válidos; 3 evidências |
| metodologia | 200 | 5,399 s | 1.126 | Texto válido e recursos preservados |
| sequencia | 400 | 1,382 s | Não informados | Requisição recusada por complexidade do schema |

Tempo total registrado: **10,679 s**. Total conhecido: **2.796 tokens**, sendo 2.074 de entrada e 722 de saída nas três chamadas com uso informado. Não se atribui consumo zero à chamada sem metadados. O uso não permite inferir gratuidade ou faturamento da conta.

As três respostas recebidas foram revalidadas offline com os contratos publicados. Não houve saída da sequência, avaliação final, adaptações nem plano integrado. A rodada terminou em `falha`, sem novas tentativas após HTTP 400. Portanto existe evidência de acesso ao modelo e de três etapas aderentes ao contrato, mas a execução completa permanece pendente.

O erro foi `INVALID_ARGUMENT`, com mensagem de que o schema produzia estados demais para a API. A causa específica não era chave inválida. Limites de listas aninhadas, limites numéricos e padrões dos IDs estavam sendo enviados como restrições da gramática.

## Ajuste implementado

`contratos/esquema_gemini.py` projeta o contrato em um schema estrutural para o Gemini: conserva nomes, tipos, campos obrigatórios e proibição de extras. Limites de quantidade/valor/comprimento, unicidade, enumerações e padrões passam a descrições orientadoras. O schema completo e a validação local permanecem intactos, incluindo soma de duração e vínculos. Essa estratégia segue a [orientação oficial de simplificação](https://ai.google.dev/gemini-api/docs/structured-output#simplifying-complex-schemas).

A versão enviada é registrada como `versao_esquema_api: plano-2.0-estrutura-v1`. A interface de transporte continua inalterada; esta correção não altera `gemini.py`, `teste_gemini.py` ou o tratamento de rede. Não há fallback nem repetição automática do HTTP 400. Erros de complexidade e `API_KEY_INVALID` recebem mensagens específicas no gerador completo.

## Achado pedagógico

OBJ3 pede registro de comparações e trocas; EVI3 exige preenchimento de tabela em papel; a metodologia repete registros escritos. Não há instrumento de escrita explicitamente confirmado. O campo `recursos` correto não garante que a prosa respeite os recursos. O prompt `especialistas-plano-2.0.1` reforça a orientação: sem instrumento ou dispositivo de escrita confirmado, propor contagem/explicação oral ou manipulação dos cartões. O efeito desse reforço precisa ser observado em nova chamada; não é validação semântica implementada.

## Verificação e próximo teste

Suíte offline: **94 testes aprovados e 1 opcional ignorado** (`python -S -m unittest discover -s tests -q`). A regressão confirma as seis requisições com gramática simplificada, mantém rejeição local de limites/IDs/duração inválidos e reproduz a parada no HTTP 400 após três sucessos. A suíte não reproduz o compilador privado da API e não comprova que a correção já foi aceita pelo servidor.

Atualizar `feat/poc04a-gemini` e executar novamente, na pasta `aula-ia-backend` e com a chave já definida no terminal:

```bat
python teste_gemini.py --contrato 2.0 --rodadas 1 --duracao 50 --reparos 0
```

Analisar o novo JSON. Não afirmar execução completa, qualidade pedagógica ou melhoria de latência antes dessa evidência. Os tempos desta rodada incompleta não devem ser comparados diretamente com o plano completo do OpenRouter.
