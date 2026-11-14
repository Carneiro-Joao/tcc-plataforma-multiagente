# AulaIA — integração Gemini sobre os contratos PoC 04A v0.1

Plataforma local para planejar aulas de Computação do **8º ano**, com seleção explícita da habilidade BNCC, cinco especialistas, integração em Python e aprovação docente. O modo de IA agora usa a **API nativa do Gemini**. Os testes descartáveis anteriores com OpenAI/OpenRouter deixam de ser o caminho de execução.

Esta entrega aplica os contratos já existentes em `feat/poc04a-contratos`. É uma etapa parcial da PoC 04A com o adaptador Gemini antecipado da 04B: não conclui o PlanoDeAula 2.0 de 11 seções. Consulte [o alinhamento com a especificação R2](docs/Alinhamento_PoC04A.md).

A geração mantém a habilidade, o tema, o ano, o tipo, os recursos e a duração confirmados. Cada especialista é validado antes do próximo. A integração não usa LLM: isso evita a conversão de `metodologia` de texto para objeto observada no teste anterior.

## 1. Preparar no Windows

É necessário Python 3.12 ou superior. O modo lexical, os contratos e o adaptador Gemini usam somente a biblioteca padrão; `requirements.txt` é um arquivo informativo sem dependências. Abra o terminal na pasta **`aula-ia-backend`**:

```bat
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python teste_gemini.py --simular
```

Se seu computador usa `py`, substitua `python` por `py`. A simulação usa regras locais, não chama a API e não demonstra a qualidade pedagógica do Gemini.

## 2. Criar a chave e conferir a faixa gratuita

1. Acesse [Google AI Studio — API keys](https://aistudio.google.com/apikey) com sua conta Google.
2. Crie ou selecione um projeto **Free Tier** e crie sua chave. Alguns projetos precisam de verificação.
3. Confira os [limites ativos do projeto](https://aistudio.google.com/rate-limit?timeRange=last-28-days).
4. Para esta PoC sem investimento, mantenha o projeto no Free Tier. O programa não ativa faturamento e não consegue consultar nem garantir o regime de cobrança da sua conta.

Modelo fixo inicial: **`gemini-3.5-flash-lite`**, com geração estruturada e entrada/saída gratuitas no Free Tier, conforme documentação consultada em **13/11/2026**. As cotas são por projeto, variam por modelo e conta e podem mudar. Não se promete uma quantidade fixa de tokens ou planos por dia. Quando a cota falha, a execução para; não há troca automática para outro modelo ou provedor.

No Free Tier, o conteúdo pode ser usado pelo Google para melhorar produtos. Use contexto fictício nos testes, sem dados pessoais de alunos. A referência de preços da API é independente da experiência do aplicativo Gemini.

## 3. Testar a API real

No **Prompt de Comando (CMD)** — terminal com caminho como `C:\...>`:

```bat
set "GEMINI_API_KEY=SUA_CHAVE_DO_AI_STUDIO"
python teste_gemini.py --rodadas 1 --duracao 50
```

No **PowerShell** — terminal normalmente iniciado por `PS C:\...>`:

```powershell
$env:GEMINI_API_KEY = "SUA_CHAVE_DO_AI_STUDIO"
python teste_gemini.py --rodadas 1 --duracao 50
```

A chave fica somente na variável de ambiente do terminal. Não envie a chave em mensagens, prints, código ou commits. A chave OpenAI exposta anteriormente deve ser revogada no provedor antigo.

O teste faz **5 chamadas normais**: objetivos → metodologia → sequência → avaliação → adaptação. Pode fazer **até 10 chamadas** se todos precisarem do único reparo estrutural permitido. Use `--reparos 0` para sondar a primeira resposta de cada etapa, sem reparo. HTTP 429, erros de autenticação, rede, bloqueio e resposta interrompida encerram a execução sem repetição automática.

```bat
python teste_gemini.py --rodadas 3 --duracao 45 --reparos 0
```

Resultados em `aula-ia-backend/local/teste_gemini/`, ignorados pelo Git. O terminal mostra estado, tipos, tempo, modelo e tokens conhecidos. O JSON registra entrada, resposta da API, conteúdo recebido, uso, erros, tentativas e integração. Ausência de `usageMetadata` não é tratada como consumo zero. Uma falha interrompe as rodadas seguintes. Interrupção por Ctrl+C também salva o registro; encerramento forçado do processo pode deixar a última etapa como `processando`.

O parâmetro `--modelo` permite escolher outro identificador Gemini, mas você deve conferir antes suporte a JSON estruturado, disponibilidade e preço. Não existe fallback automático.

## 4. Abrir o site

No mesmo terminal com a chave definida:

```bat
python app.py --modo lexical --gerador ia
```

Abra **http://127.0.0.1:8000**. Não precisa executar Node, npm ou Vite: o frontend compilado está versionado.

Para demonstrar sem chave e sem rede:

```bat
python app.py --modo lexical --gerador demonstracao
```

Roteiro: informe **quero ensinar ordenação**, **50 minutos**, **papel e cartões**, **Computação desplugada**; consulte e confirme **EF08CO03**; gere o plano; confira cada seção e o rastreio. Uma saída válida estruturalmente continua sendo um **rascunho**. A aprovação é feita pelo professor. O botão de impressão permite salvar PDF pelo navegador.

Não há login ou cadastro. Consultas, versões, aprovações e falhas mantêm o **SQLite local** em `local/consultas.sqlite3`, preservando a rastreabilidade técnica prevista na especificação R2. Isso não implementa histórico privado ou contas de usuário, e não exige instalar um servidor de banco. Os JSONs do teste de terminal também permanecem para análise técnica.

Para uma demonstração explicitamente descartável, use:

```bat
python app.py --gerador demonstracao --temporario
```

Nesse modo, os dados são temporários e removidos ao encerrar normalmente; um encerramento forçado pode deixar arquivo temporário no sistema. Para escolher outro banco persistente, use `--banco caminho/arquivo.sqlite3`.

## 5. Contratos e fluxo

| Etapa | Saída aceita |
|---|---|
| Objetivos | `objetivos`: lista de 2 a 4 textos não vazios |
| Metodologia | `metodologia`: texto; `recursos`: cópia exata dos recursos confirmados |
| Sequência | `etapas`: lista de `{etapa, minutos, atividade}`, minutos inteiros positivos, soma exata |
| Avaliação | `avaliacao`: texto; prompt exige critérios e evidências futuras |
| Adaptação | `adaptacoes`: exatamente dois textos |
| Integração | Composição determinística dos 13 campos do plano |

Campos extras, tipos diferentes, textos em branco, chaves duplicadas e números `NaN`/`Infinity` são rejeitados. Não há conversão silenciosa de objetos em texto ou descarte de campos extras. O schema enviado ao Gemini reduz desvios, mas a validação local permanece obrigatória.

Há no máximo um reparo por especialista na mesma execução, mantendo as dependências já validadas. Não é um ciclo de correção pedagógica. Se o reparo também falhar, os dependentes não executam. A tentativa fica em estado `falha`, com rastreio, e não pode ser aprovada. Uma nova solicitação do professor cria outra revisão e recalcula todos os especialistas.

O contrato operacional é `poc04a-0.1`, com 13 campos. Ainda faltam o PlanoDeAula 2.0 completo, IDs e vínculos objetivo–etapa–evidência, avaliação preliminar/final em chamadas separadas e rejeição explícita pelo usuário. A **IA Juiz ainda não está implementada**. As verificações estruturais não comprovam alinhamento pedagógico, viabilidade dos materiais citados na prosa nem ausência de resultados inventados. Esses pontos são orientados nos prompts e precisam de revisão docente e avaliação posterior.

## 6. Arquivos e validação

| Arquivo | Responsabilidade |
|---|---|
| `aula-ia-backend/gemini.py` | API nativa, schema, limites de leitura, erros e metadados |
| `aula-ia-backend/geracao.py` | Dependências, validação por etapa e reparo limitado |
| `aula-ia-backend/contratos/validacao.py` | Validador e parser em Python puro, preservados da branch de contratos |
| `aula-ia-backend/contratos/execucao.py` | Adaptação dos diagnósticos, schema para Gemini e integração determinística |
| `aula-ia-backend/contratos/contratos.schema.json` | Contratos PoC 04A v0.1 |
| `aula-ia-backend/teste_gemini.py` | Sondagem real ou simulação com registro JSON |
| `aula-ia-backend/tests/dados/poc04a/` | Fixture sintética e 27 casos da revisão anterior |
| `aula-ia-backend/tests/` | Contratos, transporte simulado, fluxo, concorrência e HTTP |
| `aula-ia/public/geracao-ui.js` | Exibição do plano, falha e aprovação; espelhado em `dist/` |
| `docs/PoC04A_Gemini.md` | Decisões, achados, evidências e limites deste incremento |

Validação desta entrega: **63 testes aprovados e 1 teste opcional ignorado**, incluindo os 27 casos estruturais como subtestes; execução do CLI em simulação com duração de 45 minutos; sintaxe JavaScript conferida. O fluxo HTTP usa respostas Gemini simuladas. A execução do navegador automatizado foi bloqueada pelo ambiente, portanto a interface visual precisa ser conferida localmente. **A API real Gemini ainda não foi chamada com uma chave do projeto.**

Os módulos legados `AgenteOpenAI` e os probes que fazem monkeypatch de `geracao.request.urlopen` não integram mais o fluxo atual. Use `teste_gemini.py`. O modo de busca híbrida permanece opcional: instale também `requirements-hibrido.txt`, prepare os arquivos/modelos necessários e execute `--modo hibrido`. A alteração do provedor de geração não muda o catálogo ou o método da busca curricular.

## Referências oficiais consultadas

- [Modelo Gemini 3.5 Flash-Lite](https://ai.google.dev/gemini-api/docs/models/gemini-3.5-flash-lite)
- [Preços e Free Tier](https://ai.google.dev/gemini-api/docs/pricing)
- [Limites por projeto](https://ai.google.dev/gemini-api/docs/rate-limits)
- [Criação e uso de chaves](https://ai.google.dev/gemini-api/docs/api-key)
- [Referência generateContent](https://ai.google.dev/api/generate-content)
