# AulaIA — Gemini, PlanoDeAula 2.0 e IA Juiz via Groq

Plataforma local para planejar aulas de Computação do **8º ano**, com seleção explícita da habilidade BNCC, cinco especialistas, integração em Python, **IA Juiz automática** e aprovação docente.

> **Estado em 25/11/2026 (`main` `4558b4a`, depois da PoC 10).** Fluxo atual: o professor informa o contexto → o sistema extrai o
> tema e busca a habilidade → o professor confirma → 5 especialistas (Gemini, 6 chamadas) geram o plano, com uma reescrita de saída
> escrita sem acentuação → integrador e validador → a IA Juiz (Groq) avalia → parecer não favorável regenera o plano inteiro uma vez,
> **informado pelas críticas do Juiz** → o professor recebe o plano com o parecer, aprova e baixa o PDF ou gera novamente (do zero).
> Requisitos e regras: [`docs/especificacao/AulaIA_Especificacao_v2.3.md`](docs/especificacao/AulaIA_Especificacao_v2.3.md);
> números, versões e como rodar: [`docs/Estado_Final_Sistema.md`](docs/Estado_Final_Sistema.md); diagramas:
> [`docs/diagramas/diagramas-finais.md`](docs/diagramas/diagramas-finais.md). As seções abaixo que citam datas de 16–17/11 são
> registro histórico dos incrementos. O modo de IA agora usa a **API nativa do Gemini**. Os testes descartáveis anteriores com OpenAI/OpenRouter deixam de ser o caminho de execução.

Esta entrega incorpora o **PlanoDeAula 2.0 com 11 seções**, avaliação em duas passagens e vínculos entre objetivos, etapas e evidências. Uma execução real no protótipo concluiu as seis etapas e a integração, com recuperação de dois HTTP 503. Consulte a [evidência da geração real](docs/Prototipo_Local_2026-11-16.md), o [contrato](docs/Contrato_PlanoDeAula_2_0.md) e o [alinhamento com a R2](docs/Alinhamento_PoC04A.md). A branch `feat/poc05-juiz-contrato` acrescenta a base da **IA Juiz**, verificada offline: rubrica, parecer estruturado e política de decisão. A conexão ao site e a execução dos ciclos de correção ainda estão pendentes; veja a [revisão de compatibilidade de 17/11/2026](docs/Revisao_PoC05_2026-11-17.md).

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

O teste usa o contrato 2.0 e faz **6 chamadas normais**: objetivos → avaliação preliminar → metodologia → sequência → avaliação final → adaptação. Pode fazer **até 12 chamadas** se todos precisarem do único reparo estrutural permitido. Use `--reparos 0` para sondar a primeira resposta de cada etapa, sem reparo. HTTP 429, erros de autenticação, rede, bloqueio e resposta interrompida encerram a execução sem repetição automática.

```bat
python teste_gemini.py --rodadas 3 --duracao 45 --reparos 0
```

Resultados em `aula-ia-backend/local/teste_gemini/`, ignorados pelo Git. O terminal mostra estado, tipos, tempo, modelo e tokens conhecidos. O JSON registra entrada, resposta da API, conteúdo recebido, uso, erros, tentativas e integração. Ausência de `usageMetadata` não é tratada como consumo zero. Uma falha interrompe as rodadas seguintes. Interrupção por Ctrl+C também salva o registro; encerramento forçado do processo pode deixar a última etapa como `processando`.

O parâmetro `--modelo` permite escolher outro identificador Gemini, mas você deve conferir antes suporte a JSON estruturado, disponibilidade e preço. Não existe fallback automático.

Se houver `ConnectionResetError` / `WinError 10054` em uma rede com IPv6 instável, teste a conexão por IPv4:

```powershell
python teste_gemini.py --ipv4 --rodadas 1 --duracao 50 --reparos 0
```

`--ipv4` vale somente para essa execução, mantém HTTPS com validação de certificado e não altera a rede do Windows. O JSON registra a opção em `rede`. A chave continua sendo lida de `GEMINI_API_KEY`; falhas da API encerram a rodada sem repetição automática.

No contrato 2.0, o esquema enviado ao Gemini preserva campos obrigatórios, tipos e objetos fechados. Limites de listas/números, padrões de texto e unicidade são descritos para o modelo e continuam sendo exigidos pelo validador Python. Isso reduz a complexidade da gramática da API, evitando a rejeição HTTP 400 `too many states` causada por limites de listas aninhadas. A versão consolidada registra `versao_prompt: especialistas-plano-2.2` e `versao_esquema_api: plano-2.0-estrutura-v1`; o contrato local permanece `plano-aula-2.0`. A execução completa documentada usou o prompt 2.1, anterior à consolidação. Consulte as [orientações oficiais sobre simplificação de esquemas](https://ai.google.dev/gemini-api/docs/structured-output#simplifying-complex-schemas).

## 4. Abrir o site

No Windows, dê duplo clique em **`INICIAR_AULAIA.cmd`** na pasta do projeto. Se a chave ainda não estiver no ambiente, uma janela permite usar **Colar chave** e **Iniciar protótipo**. A entrada aparece como asteriscos; a chave não é gravada em arquivo. O iniciador usa Gemini real por IPv4 e abre o navegador. Mantenha a janela do servidor aberta.

No mesmo terminal com a chave definida:

```bat
python app.py --modo lexical --gerador ia --ipv4 --abrir
```

Abra **http://127.0.0.1:8000**. Não precisa executar Node, npm ou Vite: o frontend compilado está versionado.

Se estiver em um novo terminal, sem `GEMINI_API_KEY`, use a entrada oculta da chave:

```powershell
python app.py --modo lexical --gerador ia --ipv4 --pedir-chave --abrir
```

A chave fica somente na memória desse processo. Mantenha o terminal aberto enquanto usa o protótipo; pressione `Ctrl+C` nele para encerrar. `--abrir` inicia o navegador e `--ipv4` aplica ao site o mesmo transporte usado no teste de terminal.

No site, HTTP **503** recebe até **duas novas tentativas na mesma etapa**, com esperas de 2–3 e 4–5 segundos. As etapas anteriores não são refeitas. Se o serviço continuar indisponível, a geração termina em falha. O rastreio mantém `chamadas_http` e `falhas_http_transitorias`, incluindo erros e esperas. Por versão do plano são 6 chamadas normais e até 18 com reparos e reescritas de acentuação; com as repetições em 503, até 54 requisições (a mensagem de partida do `app.py` mostra os valores da configuração em uso). `--repeticoes-503 0` desativa esse comportamento; `teste_gemini.py` continua sem repetir erros HTTP. Cota (429), autenticação, rede e outros erros não são repetidos automaticamente. A estratégia segue a [orientação do Google para falhas transitórias](https://ai.google.dev/gemini-api/docs/troubleshooting#retry-strategy).

### IA Juiz e regeneração

Com `GROQ_API_KEY` definida no mesmo terminal, a IA Juiz entra automaticamente depois de cada geração (sem a chave, fica desligada):

```bat
python app.py --modo lexical --gerador ia --ipv4 --abrir
python app.py --modo lexical --gerador ia --ipv4 --juiz groq --ciclos-juiz 1 --regeneracao informada --abrir
```

| Opção | Padrão | Efeito |
|---|---|---|
| `--juiz groq\|demonstracao\|desligado` | `groq` se houver `GROQ_API_KEY`, senão `desligado` | `demonstracao` usa um parecer real **gravado de outro plano**, sem rede; por isso a regeneração fica cega |
| `--ciclos-juiz N` | 1 | Regenerações automáticas quando o parecer não é favorável (0 = não regenera) |
| `--regeneracao informada\|cega` | `informada` | `informada`: cada especialista recebe a sua versão anterior e as críticas do Juiz (`revisao-informada-1.0`); `cega`: gera de novo sem as críticas (PoC 08) |
| `--limite-diario N` | 8 | Gerações com IA por dia, contando falhas |
| `--limite-diario-juiz N` | 8 | Avaliações reais do Juiz por dia, contando falhas |

Sem versão favorável, o professor recebe a versão com menos falhas graves, com aviso. Falha técnica do Juiz entrega o plano com
"avaliação indisponível" e nunca conta como parecer. O Juiz não vê as críticas nem a versão anterior. O parecer é consultivo: só o
professor aprova. Detalhes: [`docs/PoC08_Juiz_Integrado.md`](docs/PoC08_Juiz_Integrado.md) e
[`docs/PoC10_Regeneracao_Informada_e_Acentuacao.md`](docs/PoC10_Regeneracao_Informada_e_Acentuacao.md).

Para demonstrar sem chave e sem rede:

```bat
python app.py --modo lexical --gerador demonstracao --juiz demonstracao
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
| Objetivos | Conteúdos, objetivo geral e 2–4 objetivos específicos com IDs |
| Avaliação preliminar | Critérios e evidências esperadas por objetivo |
| Metodologia | Texto e recursos exatamente iguais aos confirmados |
| Sequência | Etapas com duração, ações docente/discente, atividade e IDs de objetivos/evidências |
| Avaliação final | Instrumentos, procedimentos, vínculos e uso futuro dos resultados |
| Adaptação | Duas adaptações com vínculos a objetivos e etapas |
| Integração | Composição local das 11 seções e metadados oficiais do catálogo |

Campos extras, tipos diferentes, textos em branco, chaves duplicadas e números `NaN`/`Infinity` são rejeitados. Não há conversão silenciosa de objetos em texto ou descarte de campos extras. O schema enviado ao Gemini mantém estrutura/tipos e usa descrições para limites e formatos, evitando multiplicar estados na API. O contrato completo continua obrigatório na validação local.

Há no máximo um reparo por especialista na mesma execução, mantendo as dependências já validadas. Não é um ciclo de correção pedagógica. Se o reparo também falhar, os dependentes não executam. A tentativa fica em estado `falha`, com rastreio, e não pode ser aprovada. Uma nova solicitação do professor cria outra revisão e recalcula todos os especialistas.

O contrato operacional é `plano-aula-2.0`. Todos os objetivos, etapas, evidências e instrumentos têm identificadores; o validador verifica cobertura e referências. A fonte curricular inclui versão e hash do catálogo JSON, não do PDF. Planos antigos continuam legíveis sem conversão; para reproduzir a sondagem antiga, use `--contrato v0.1`. Consultas antigas sem metadados de versão exigem nova consulta antes de gerar 2.0.

A **IA Juiz** (`juiz.py`, `juiz_servico.py`, `groq_juiz.py`) usa a [rubrica preliminar e o contrato ParecerJuiz 1.0](docs/Rubrica_e_Contrato_IA_Juiz.md). Antes de chamar o agente, valida o plano 2.0, o contexto confirmado e a política. O parecer indica `aguardando_decisao`, `em_correcao` ou `revisao_necessaria`; ele nunca aprova o plano. Desde a PoC 08 o Juiz é uma etapa automática do pedido, com pareceres gravados na tabela `pareceres` do SQLite e exibidos na interface (ver "IA Juiz e regeneração" acima). Os testes offline não demonstram qualidade pedagógica nem eficácia de um Juiz real.

### Histórico: Juiz isolado e ensaios (PoC 05)

Para testar somente a base do Juiz, sem chave nem chamadas de API, execute na pasta `aula-ia-backend`:

```bat
python -m unittest discover -s tests -p test_juiz.py -v
```

A **PoC 05B implementa o adaptador GroqCloud** para `openai/gpt-oss-120b`, com `GROQ_API_KEY`, mantendo `gemini-3.5-flash-lite` nos especialistas. A fábrica `criar_agente_groq_juiz` seleciona o novo adaptador; `criar_agente_juiz` continua compatível com Gemini. O contrato, a rubrica de seis critérios/escala 0–3 e a política permanecem iguais. **A chamada autenticada à Groq ainda precisa ser validada:** a chave não estava disponível no ambiente desta entrega.

A execução isolada registra pareceres, falhas, justificativas, modelos, versões, hashes, latência e uso conhecido em `local/ensaios_juiz/`, sem acionar correções ou aprovação. O JSON original do caso da revisão foi recuperado do SQLite e conferido contra o PDF; está separado das fixtures sintéticas.

```powershell
# Na pasta aula-ia-backend, sem chave nem rede:
python ensaio_juiz.py avaliar --caso ../experimentos/juiz/casos/ordenacao_real_994c4cd5.json --somente-validar
# Com GROQ_API_KEY configurada no mesmo terminal:
python ensaio_juiz.py avaliar --caso ../experimentos/juiz/casos/ordenacao_real_994c4cd5.json
# Testes com mocks:
python -S -m unittest discover -s tests -p '*juiz*.py' -q
```

Resultado: **88 testes do juiz/ensaio aprovados**, sendo 34 novos. Regressão sem os quatro testes HTTP local: **198 aprovados e 1 opcional ignorado**. Os testes HTTP local foram bloqueados pelas permissões de sockets deste ambiente. Veja o [roteiro completo, proveniência e limitações da PoC 05B](docs/PoC05B_Groq.md), incluindo configuração oculta da chave. A integração dos ciclos de correção com o site continua para o próximo incremento.

Um registro já salvo pode ser inspecionado sem chave e sem novas chamadas:

```bat
python inspecionar_gemini.py "local/teste_gemini/NOME_DO_ARQUIVO.json"
```

Para conferir a execução real, compartilhe o JSON desse diretório. Não compartilhe a chave. O inspetor informa o modo declarado e não autentica a origem de arquivos editáveis.

## 6. Ferramentas de pesquisa e scripts históricos

Fora do fluxo do site, na pasta `aula-ia-backend` (nenhum faz chamada real sem a chave e sem o pedido explícito do João):

| Script | Para quê |
|---|---|
| `ensaio_juiz.py`, `variantes_juiz.py`, `casos_juiz.py`, `analisar_serie.py` | Ensaios pré-registrados do Juiz (V01–V06) sobre casos congelados (`--somente-validar` testa sem rede) |
| `adjudicacao.py`, `adjudicacao_web.py`, `concordancia.py` | Adjudicação humana dos pareceres e concordância entre avaliadores |
| `gerar_lote.py`, `medir_planos.py` | Lote e medição pré-registrados da geração (PoC07B; `--somente-validar`) |
| `sondagem_regeneracao_informada.py` | Sondagem cega × informada da PoC 09 (registro exploratório, n = 5) |
| `exportar_planos.py` | Exporta os planos reais do SQLite para `local/planos_ia/` (recusa arquivo com credencial) |
| `teste_gemini.py`, `inspecionar_gemini.py` | Sondagem do Gemini pelo terminal e inspeção de registros salvos |
| `relatorio_testes.py` | Roda os testes e gera relatório HTML (`--sem-abrir`, `--filtro`) |
| `legado/` | Scripts das sondagens OpenAI/OpenRouter da PoC 03, já quebrados e fora do fluxo ([`legado/README.md`](aula-ia-backend/legado/README.md)) |

## 7. Arquivos e validação

| Arquivo | Responsabilidade |
|---|---|
| `INICIAR_AULAIA.cmd` | Inicialização por duplo clique no Windows |
| `aula-ia-backend/iniciar_prototipo.py` | Janela para colar a chave, mantida somente em memória |
| `aula-ia-backend/rede.py` | Transporte IPv4 opcional com HTTPS e validação de certificado |
| `aula-ia-backend/gemini.py` | API nativa, schema, limites de leitura, erros e metadados |
| `aula-ia-backend/geracao_v2.py` | Prompts completos e fluxo com seis chamadas |
| `aula-ia-backend/geracao.py` | Orquestrador compartilhado e compatibilidade v0.1 |
| `aula-ia-backend/contratos/plano_v2.py` | Validação estrutural, vínculos e integração 2.0 |
| `aula-ia-backend/contratos/plano_v2.schema.json` | Esquemas completos versionados |
| `aula-ia-backend/contratos/esquema_gemini.py` | Projeção estrutural do esquema para a API |
| `aula-ia-backend/servico.py` | Consulta, pedido (geração + Juiz + regeneração), aprovação, limites e SQLite |
| `aula-ia-backend/revisao_informada.py` | Versão anterior + críticas do Juiz para cada especialista na regeneração (`revisao-informada-1.0`) |
| `aula-ia-backend/acentuacao.py` | Detecção de saída sem acentuação e instrução da reescrita |
| `aula-ia-backend/juiz.py` | Avaliação do plano 2.0 pelo Juiz e rastreio |
| `aula-ia-backend/juiz_servico.py`, `groq_juiz.py` | Juiz no pedido (modos groq/demonstração), pausas de cota e adaptador Groq |
| `aula-ia-backend/contratos/juiz_v1.py` | Validação do parecer, configuração da política e decisão determinística |
| `aula-ia-backend/contratos/juiz_v1.schema.json` | Contrato fechado ParecerJuiz 1.0 |
| `aula-ia-backend/contratos/rubrica_juiz.py` | Seis critérios, indicadores e âncoras preliminares usados no prompt |
| `aula-ia-backend/contratos/validacao.py` | Validador e parser em Python puro, preservados da branch de contratos |
| `aula-ia-backend/contratos/execucao.py` | Parser compartilhado e integração legada v0.1 |
| `aula-ia-backend/contratos/contratos.schema.json` | Contratos PoC 04A v0.1 |
| `aula-ia-backend/teste_gemini.py` | Sondagem real ou simulação com registro JSON |
| `aula-ia-backend/tests/dados/poc04a/` | Fixture sintética e 27 casos da revisão anterior |
| `aula-ia-backend/tests/` | Contratos, transporte simulado, fluxo, concorrência e HTTP |
| `aula-ia/public/geracao-ui.js` | Exibição do plano, falha e aprovação; espelhado em `dist/` |
| `docs/PoC04A_Gemini.md` | Decisões, achados, evidências e limites deste incremento |

Validação atual (25/11/2026): **532 testes Python (531 passam, 1 ignorado)**, também com `python -S`, e os 3 scripts de interface (`aula-ia/tests/`). O parágrafo a seguir é o registro de 17/11.

Validação em 17/11/2026: **168 testes aprovados e 1 teste opcional ignorado**, também com `python -S`, incluindo os 27 casos estruturais como subtestes, HTTP local, inicializadores, IPv4, recuperação limitada de HTTP 503 e 54 testes do Juiz. O teste de renderização JavaScript confere 11 seções, escape de HTML, planos legados e igualdade entre `public` e `dist`; funciona com quebras de linha Windows ou Unix. Uma geração real anterior, registrada no SQLite local, concluiu o contrato 2.0 em **38,281 s**, com **8 requisições HTTP**, duas recuperações de 503 e **7.831 tokens conhecidos** em seis respostas com uso informado. Essa execução não incluiu IA Juiz. O plano permanece rascunho; a validação mecânica não equivale à aprovação pedagógica. Consulte a [evidência e seus limites](docs/Prototipo_Local_2026-11-16.md).

Os módulos legados `AgenteOpenAI` e os probes que fazem monkeypatch de `geracao.request.urlopen` não integram mais o fluxo atual. Use `teste_gemini.py`. O modo de busca híbrida permanece opcional: instale também `requirements-hibrido.txt`, prepare os arquivos/modelos necessários e execute `--modo hibrido`. A alteração do provedor de geração não muda o catálogo ou o método da busca curricular.

## Referências oficiais consultadas

- [Modelo Gemini 3.5 Flash-Lite](https://ai.google.dev/gemini-api/docs/models/gemini-3.5-flash-lite)
- [Preços e Free Tier](https://ai.google.dev/gemini-api/docs/pricing)
- [Limites por projeto](https://ai.google.dev/gemini-api/docs/rate-limits)
- [Criação e uso de chaves](https://ai.google.dev/gemini-api/docs/api-key)
- [Referência generateContent](https://ai.google.dev/api/generate-content)
