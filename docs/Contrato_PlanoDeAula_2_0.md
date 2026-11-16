# Contrato PlanoDeAula 2.0

Versão operacional: `plano-aula-2.0`. Revisão: 16/11/2026. Fecha a estrutura e os vínculos mecânicos das 11 seções previstas na especificação v2.1-R2. A aceitação empírica das respostas reais Gemini e a validação pedagógica permanecem pendentes.

O schema executável está em [plano_v2.schema.json](../aula-ia-backend/contratos/plano_v2.schema.json), com definições de cada chamada e do plano. O validador [plano_v2.py](../aula-ia-backend/contratos/plano_v2.py) implementa seu subconjunto e acrescenta invariantes entre seções. Não é um interpretador geral de JSON Schema. A [fixture sintética](../aula-ia-backend/tests/dados/plano_v2/fixture_ordenacao.json) contém entrada, seis saídas e plano esperado; não veio da API.

## Envelope e compatibilidade

O resultado contém `contrato`, `plano`, `rastreio`, `modo`, `provedor`, `modelo`, `revisao`, `tempo_total_s`, `avaliacao_pedagogica` e `criterios_mecanicos`. `contrato` vale `plano-aula-2.0`; fica fora de `plano` para manter exatamente 11 seções. Aprovação e estado da geração pertencem ao registro do serviço, não ao conteúdo pedagógico.

Novas gerações do site e do CLI usam 2.0. Os contratos v0.1, seus 27 casos e a fixture anterior permanecem íntegros. Registros antigos são lidos e renderizados sem conversão automática; `teste_gemini.py --contrato v0.1` reproduz o pipeline anterior para comparação. Uma consulta antiga sem versão/hash do catálogo exige nova consulta curricular antes de gerar 2.0; seus planos já salvos continuam acessíveis.

## As 11 seções

Todos os campos são obrigatórios. Objetos são fechados; não aceitam chaves extras. Textos devem conter caracteres não brancos. Não há coerção, preenchimento silencioso ou descarte de campos inválidos.

| Seção | Campos e tipos | Origem e restrições |
|---|---|---|
| `identificacao` | `titulo`, `componente`, `ano`, `tema`, `tipo`: textos; `duracao_min`: inteiro 1–1440 | Composição local. Componente Computação, título derivado do tema e demais valores iguais ao contexto confirmado |
| `habilidade_bncc` | `codigo`, `descricao`, `eixo`, `objeto_conhecimento`: textos; `referencia`: objeto | Cópia exata do catálogo confirmado; nunca gerada pelo modelo |
| `conteudos` | Lista de 1–8 textos distintos | Especialista objetivos |
| `objetivo_geral` | Texto | Especialista objetivos |
| `objetivos_especificos` | Lista de 2–4 objetos `{id, descricao}` | IDs `OBJ1`, `OBJ2` etc., únicos |
| `metodologia` | Texto | Estratégia alinhada aos objetivos e evidências preliminares |
| `recursos` | Texto | Cópia exata de `contexto.recursos`; não acrescenta recursos |
| `desenvolvimento` | Lista de 1–12 etapas | Cada etapa tem ID, duração, atividade, ações e vínculos, conforme abaixo |
| `avaliacao_aprendizagem` | Objeto `{evidencias, instrumentos, uso_resultados}` | Combina as duas passagens de avaliação; `uso_resultados` é texto sobre uso futuro |
| `adaptacoes` | Exatamente 2 objetos | IDs `ADP1`, `ADP2` etc., descrição e vínculos a objetivos e etapas |
| `referencias` | Lista com a referência curricular utilizada | Somente a fonte BNCC do catálogo; sem referências bibliográficas inventadas pelo modelo |

### Etapas e avaliação

Uma etapa contém `id` (`ET1` etc.), `titulo`, `minutos`, `acao_docente`, `acao_discente`, `atividade`, `objetivos_ids` e `evidencias_ids`. Os campos de ação/atividade são textos. `minutos` é inteiro positivo: `true`, `5.0` e `"5"` são rejeitados. A soma deve ser exatamente a duração confirmada. Cada lista de vínculos é não vazia e sem duplicatas.

Uma evidência contém `id` (`EVI1` etc.), `objetivo_id`, `criterio` e `evidencia_esperada`. Cada objetivo precisa de pelo menos uma evidência. São 2–12 evidências, definidas antes da sequência. Os critérios são textos; não há nota ou resultado observado.

Um instrumento contém `id` (`INS1` etc.), `descricao`, `etapas_ids`, `evidencias_ids` e `procedimento`. São 1–12 instrumentos. As duas listas de vínculos são não vazias e sem duplicatas. Todas as evidências devem estar cobertas pelos instrumentos.

Uma adaptação contém `id`, `descricao`, `objetivos_ids` e `etapas_ids`. Os objetivos citados precisam ocorrer nas etapas vinculadas. A adequação da descrição à inclusão e aos recursos exige revisão pedagógica; não é demonstrada por esses IDs.

### Relações verificadas

- IDs são únicos dentro de cada coleção; referências a IDs inexistentes são recusadas.
- Todos os objetivos e evidências aparecem em pelo menos uma etapa.
- Em cada etapa, os objetivos referidos correspondem exatamente aos objetivos de suas evidências.
- Cada evidência de um instrumento aparece em pelo menos uma etapa vinculada a ele; cada etapa vinculada tem pelo menos uma evidência desse instrumento.
- A avaliação final não pode reescrever as evidências preliminares: sua saída só contém instrumentos e uso futuro dos resultados.
- A integração copia apenas campos autorizados das seis saídas e revalida o plano inteiro.

### Proveniência curricular

`habilidade_bncc.referencia` contém `documento`, `arquivo`, `pagina_habilidade`, `pagina_exemplos`, `versao_catalogo` e `sha256_catalogo`. Os valores vêm de `habilidade_publica`, não do modelo. A versão atual do catálogo é `bncc-8ano-v1`; o SHA-256 é calculado sobre os bytes de `data/bncc_8ano.json`.

**Esse hash identifica o catálogo JSON, não o PDF.** As páginas são as registradas no catálogo do projeto. A referência bibliográfica contém `id: BNCC`, `titulo`, `arquivo`, `paginas` sem duplicatas, `versao_catalogo` e `sha256_catalogo`. O pipeline consulta o catálogo local; não abre o PDF a cada geração nem faz busca bibliográfica externa.

## Chamadas, dependências e falhas

| Chamada | Dados anteriores disponíveis |
|---|---|
| `objetivos` | Contexto e habilidade confirmados |
| `avaliacao_preliminar` | Objetivos e conteúdos |
| `metodologia` | Objetivos e avaliação preliminar |
| `sequencia` | Objetivos, avaliação preliminar e metodologia |
| `avaliacao_final` | Objetivos, avaliação preliminar, metodologia e sequência |
| `adaptacao` | Todas as saídas anteriores |

São cinco especialidades, **seis chamadas normais**, pois avaliação tem duas passagens. O integrador é Python e não chama a API. Cada chamada pode receber um reparo técnico, resultando em até 12 chamadas. `--reparos 0` limita às seis tentativas originais, interrompendo na primeira falha. Dependências já validadas são copiadas e preservadas durante o reparo.

Erros HTTP, timeout, bloqueio ou término diferente de `STOP` interrompem a execução sem repetição automática. Não há fallback. JSON inválido, schema ou invariante violada permite o reparo técnico limitado. A tentativa inválida e seus diagnósticos ficam registrados. Isso não implementa o ciclo de correção pedagógica do Juiz.

## Conferência da execução real

Na pasta `aula-ia-backend`, com `GEMINI_API_KEY` definida no próprio terminal:

```bat
python teste_gemini.py --contrato 2.0 --rodadas 1 --duracao 50 --reparos 0
```

O comando registra as primeiras respostas sem pedir correção. Uma segunda rodada com `--reparos 1` permite avaliar a recuperação. A cota e o regime gratuito dependem do projeto no AI Studio; o script não consulta faturamento.

Para revalidar um arquivo já produzido, sem chamar a API novamente:

```bat
python inspecionar_gemini.py "local/teste_gemini/NOME_DO_ARQUIVO.json"
```

O inspetor diferencia simulação pelo modo declarado, informa chamadas/consumo conhecido, revalida conteúdos e compara o plano com a recomposição das etapas. Falta de `usageMetadata` não é zero consumo. O arquivo é editável: inspeção não autentica sua origem. Versão desconhecida é recusada.

Em 16/11/2026, os registros acessíveis eram simulações. Não havia credencial Gemini no ambiente nem JSON de chamada real disponível. Não foram inferidos tempo, tokens ou qualidade real a partir dos testes com transporte simulado.

## Evidências e limites

Verificação: 90 testes Python, **89 aprovados e 1 opcional ignorado**, executados com `python -S`; renderização JavaScript das 11 seções, escape de HTML, leitura do formato antigo e igualdade `public`/`dist`; CLI simulado com 45 minutos. HTTP local exercita o contrato completo até aprovação docente. A inspeção visual em navegador permanece pendente.

A estrutura completa não prova qualidade pedagógica, viabilidade dos materiais citados no texto ou ausência de resultados inventados na prosa. Continuam pendentes o teste real Gemini, IA Juiz independente, rubrica, correção pedagógica dirigida, rejeição explícita e enumeração completa de estados R2. A PoC inteira ainda não está encerrada.
