# PoC 05B — Juiz isolado via GroqCloud

Data: 17/11/2026. Base: `feat/poc05-juiz-contrato`, SHA `eda344fc3f6acd0a88df615b9184809fb7a73cea`.
Branch: `feat/poc05b-juiz-groq`.

**Estado da entrega inicial (antes do ensaio abaixo): integração verificada com mocks; chamada autenticada não executada.**
`GROQ_API_KEY` não estava configurada no ambiente de implementação. Não há parecer pedagógico real
do GPT-OSS nesta entrega. O ensaio sem chave terminou em falha de configuração persistida, com zero
requisições HTTP. O caso original passou na validação local.

## Comportamento implementado

### Primeiro ensaio autenticado e ajuste 0.2

Em 17/11/2026 às 15:23:58 (America/Fortaleza), execução `20261117T182358Z-b3e13161128a`,
a Groq respondeu HTTP 400, código `json_validate_failed`: o modelo usou `conteudos` em
`falhas[0].componente`, fora do enum do contrato. O provedor incluiu a geração rejeitada em
`failed_generation`. Portanto houve chamada real, mas nenhum parecer válido nessa execução.

O adaptador `groq-juiz-0.2` classifica esse erro específico como erro de contrato, preserva
a resposta rejeitada e permite usar o reparo técnico existente com `--reparos 1`.
O padrão continua zero reparos; outros HTTP 400 não são repetidos. Plano, rubrica e prompts
permaneciam iguais nesse ajuste. Verificação: 90 testes do juiz aprovados, incluindo dois novos
para o HTTP 400 de schema com e sem reparo habilitado. Naquele momento, a nova chamada ainda era pendente.

A resposta rejeitada também alegou que uma aula sobre Bubble Sort deveria cobrir outros algoritmos
da habilidade. Essa conclusão requer revisão humana; não é uma falha pedagógica comprovada.
Reparo de schema não valida a pertinência pedagógica do parecer.

### Primeiro parecer real válido e refinamento do prompt v1.2

Em 17/11/2026, às 15:26:52 (America/Fortaleza), o caso real recuperado do SQLite recebeu
HTTP 200 em uma chamada ao `openai/gpt-oss-120b`, sem consumir o reparo opcional:
`status=sucesso`, `parecer-juiz-1.0` válido, 5,39 s no total e 6.162 tokens registrados.
O Juiz atribuiu 2 em aderência curricular e 3 nos demais cinco critérios, classificou
como `maior` a ausência de outros algoritmos além do Bubble Sort e sugeriu `em_correcao`.
Essa interpretação da EF08CO03 não está comprovada; uma aula de 50 minutos pode trabalhar
um algoritmo pertinente sem ter de cobrir toda a lista de exemplos curriculares. A
proposta de alterar a habilidade oficial também não é aceitável. Na avaliação da
aprendizagem, EVI1 verifica comparação de valores, mas não necessariamente os passos
integrais previstos em OBJ1. Para viabilidade, somar 15 + 35 minutos não demonstra que
a execução é realista.

O prompt `juiz-v1.2` foi refinado no arquivo `contratos/juiz_v1.py` para impedir esses
atalhos: exemplos curriculares não são checklist obrigatório por aula, habilidade oficial
não deve ser modificada, OBJ/EVI/INS devem corresponder integralmente e a viabilidade
precisa de justificativa pedagógica. O refinamento é instrução ao modelo, **não garantia
de acerto**. Exige repetição do ensaio com o mesmo caso para observar o efeito; testes
offline apenas verificam invariantes e presença das instruções. Os registros anteriores
devem ser preservados e comparados, não sobrescritos.

- `groq_juiz.py`: `AgenteGroqJuiz`, REST HTTPS para `openai/gpt-oss-120b` na GroqCloud,
  credencial exclusivamente por `GROQ_API_KEY` no uso da CLI. Não requer SDK ou pacote adicional.
- `juiz.criar_agente_groq_juiz()`: fábrica explícita; reutiliza `avaliar_plano()` e sua validação.
  A fábrica Gemini anterior permanece compatível. Os especialistas continuam em
  `gemini-3.5-flash-lite`, sem mudança em seus prompts.
- `casos_juiz.py`: exporta uma geração específica do SQLite aberto com `mode=ro`, recuperando
  plano e entrada confirmada. Rejeita demonstração, falha e contratos antigos. Não reconstrói
  planos a partir de resultados parciais. Confere hashes de casos congelados.
- `ensaio_juiz.py`: comando isolado para exportação, validação local ou avaliação. Não importa
  o serviço do site, não gera planos, não grava estados no SQLite e não aprova aulas.

Preservados sem alteração: seis critérios, 24 indicadores, escala inteira 0–3,
`rubrica-juiz-0.1`, `parecer-juiz-1.0`, prompt `juiz-v1.2`, política
`politica-juiz-prelim-0.1`, grafo de invalidação e aprovação docente. A decisão é calculada
pelo Python existente e registrada como sugestão; `em_correcao` não inicia nenhum ciclo.

O contrato JSON original é enviado em `response_format.type=json_schema`, com `strict=true`.
O parecer continua sujeito aos invariantes locais (seis critérios únicos e coerência nota/falha).
Não há fallback para outro modelo, para outro provedor ou para outro formato de resposta.
Versões acrescentadas: `groq-juiz-0.1`, `parecer-juiz-1.0-groq-strict-v1`, `ensaio-juiz-0.1`.

## Caso 01 recuperado

Arquivo: [`ordenacao_real_994c4cd5.json`](../experimentos/juiz/casos/ordenacao_real_994c4cd5.json).
O plano foi extraído sem edição do SQLite local e comparado ao rastreio original e às três páginas
de `primeiro-plano-plataforma.pdf`. O PDF não contém ID de geração; a associação é por conteúdo
(objetivos, etapas, evidências, instrumentos e adaptações), não por um identificador impresso.

| Evidência | Valor |
|---|---|
| Geração do caso da revisão | `994c4cd51d944ca6a1344b15366c3971` |
| Consulta | `782973cee6554811bc195228b55e1586` |
| Criação original | 17/11/2026, 11:58:22 em America/Fortaleza (`14:58:22` UTC) |
| Estado / revisão | `rascunho` / 1; aprovação humana pendente |
| Gerador / prompt | `gemini-3.5-flash-lite` / `especialistas-plano-2.2` |
| Contexto | 8º ano; EF08CO03; ordenação; desplugada; papel; 50 min |
| Sequência | ET1=15 min, ET2=35 min |
| EVI1 | Explicar oralmente qual cartão possui o maior número |
| SHA-256 do plano canônico | `1b3bfddcee405c918e70d91faf1cd931419b71be84e5556885fe05b4dfec352d` |
| SHA-256 da entrada canônica | `b57d56ed6d391b9a979699a7af44c9fb90143df021a4a83d8c901b6d9ede5a8c` |
| SHA-256 do texto da coluna resultado | `d411920d9612ba16c05f355720a431d0442773f871c0920245ab3ae62eec8efc` |
| SHA-256 do PDF conferido | `01683b57dc788eaa564b6f3d28585ca6f17f492d4597d6c3fb8c1191b41475fa` |

JSON canônico: UTF-8, chaves ordenadas, `ensure_ascii=False`, separadores `,` e `:`, sem NaN.
O envelope inclui o hash da consulta original e metadados do gerador. O banco, o PDF e as respostas
brutas dos geradores não foram publicados. O JSON contém somente o plano, sua entrada e proveniência.

**Distinção necessária:** `d37f8d158fdc4781b0936e8422761bd6`, descrita em
`Prototipo_Local_2026-11-16.md`, é uma geração válida anterior, com outro texto. O “primeiro plano”
da revisão científica/PDF corresponde a `994c4cd5...`, não ao primeiro registro válido cronológico.
Os anexos `20261116-102219-31fe4e02.json` e `20261116-104248-7f7fbf52.json` registram falhas.
`tests/dados/plano_v2/fixture_ordenacao.json` continua sendo uma fixture sintética separada.

Para repetir a extração na pasta `aula-ia-backend`, usando o banco local original:

```powershell
python ensaio_juiz.py exportar --banco local/consultas.sqlite3 --geracao-id 994c4cd51d944ca6a1344b15366c3971 --saida local/caso_01_exportado.json
```

O comando não sobrescreve arquivos. O objeto `plano` exportado é igual ao objeto persistido;
a formatação externa do JSON não é uma cópia literal da coluna do banco. O hash dessa coluna
preserva a referência aos bytes originais.

## Roteiro da primeira chamada real

Com a nova branch no computador, abra PowerShell na pasta `aula-ia-backend`.
Primeiro confira o caso, sem chave e sem rede:

```powershell
python ensaio_juiz.py avaliar --caso ../experimentos/juiz/casos/ordenacao_real_994c4cd5.json --somente-validar
```

Informe a chave de modo oculto no próprio terminal (não no chat, código ou histórico):

```powershell
$chaveGroq = Read-Host "GROQ_API_KEY" -AsSecureString
$env:GROQ_API_KEY = [System.Net.NetworkCredential]::new('', $chaveGroq).Password
try {
    python ensaio_juiz.py avaliar --caso ../experimentos/juiz/casos/ordenacao_real_994c4cd5.json
} finally {
    Remove-Item Env:GROQ_API_KEY
    $chaveGroq.Dispose()
    Remove-Variable chaveGroq
}
```

Padrões explícitos: `temperature=0`, `seed=42`, `reasoning_effort=medium`,
`max_completion_tokens=8192`, timeout 90 s, sem streaming, `include_reasoning=false`.
Seed e temperatura não garantem repetibilidade; preserve `system_fingerprint` quando informado.
O orçamento de conclusão pode incluir tokens de raciocínio: `finish_reason=length` é falha,
nunca parecer aceito. Um novo ensaio pode ajustar `--max-completion-tokens`, com registro separado.

Por padrão há **uma única chamada**, sem retentativa HTTP nem reparo de contrato.
`--reparos 1` habilita somente o reparo técnico já existente (no máximo duas avaliações do mesmo
plano). Ele não corrige conteúdo pedagógico e não é necessário no primeiro ensaio.
HTTP 429/503 interrompe a execução e registra a falha; uma nova tentativa é uma nova execução.
O código de saída é 0 para sucesso/validação local e 1 para falha.

## Registros para o TCC

Cada execução cria `local/ensaios_juiz/<data-UTC>-<id>/`, ignorada pelo Git:

- `inicio.json`: configuração, política, versões, SHA do código, indicação de árvore modificada
  e hashes dos arquivos operacionais. É gravado antes da chamada.
- `caso.json`: cópia do caso validado, plano e entrada intactos.
- `resultado.json`: sucesso ou falha, origem e hashes, parecer, justificativas, diagnósticos,
  falhas pedagógicas, decisão calculada, rastreio, requisição sem cabeçalhos de autenticação,
  resposta bruta, modelo pedido/respondido, ID da resposta, fingerprint, latência local,
  uso/tokens/tempos de fila e de inferência quando fornecidos, cabeçalhos selecionados de cotas.

Ausência de `usage` ou de uma métrica fica `null`, não zero. Totais são apenas os valores conhecidos;
não comprovam consumo ou faturamento. Custo fica `null`, pois esta implementação não tem fonte de
preço/faturamento. O raciocínio interno não é solicitado; as justificativas do parecer são preservadas.
Credenciais são removidas dos registros; eco de credencial causa rejeição. Redirecionamentos HTTP
são recusados. Falha ao criar o registro inicial impede a chamada. Interrupção do processo pode
deixar somente `inicio.json`; não classificar esse diretório como sucesso.

Para analisar um ensaio real, confira primeiro `status`, `modelo_respondeu`, `finish_reason`, contrato
e rastreio; depois compare cada justificativa/ID com o caso original. Não confunda um parecer
estruturalmente válido com qualidade pedagógica. Nunca use os mocks como resultado do GPT-OSS.

## Verificações executadas

Windows, Python 3.14.0, 17/11/2026:

| Verificação | Resultado |
|---|---|
| `python -S -m unittest discover -s tests -p '*juiz*.py' -q` | 88 testes aprovados: 54 anteriores + 34 novos |
| Regressão excluindo apenas `test_http` | 199 executados, 198 aprovados, 1 híbrido opcional ignorado |
| Validação do caso original pela CLI | `validado_localmente`, zero chamadas |
| CLI sem `GROQ_API_KEY` | Falha de configuração persistida, zero chamadas |
| Conferência contra SQLite e rastreio | Plano, contexto e habilidade iguais aos originais |
| Renderização JavaScript e sintaxe | Aprovadas: 11 seções, escape HTML, legado e igualdade public/dist |

Os testes novos cobrem requisição, esquema/prompt existentes, política favorável/correção/crítica,
preservação do plano, segredos, parâmetros, falta de chave, HTTP 400/401/403/404/429/500/503,
timeout, redirecionamento, envelopes inválidos, recusa, truncamento, JSON duplicado, invariantes
nota/falha, reparo técnico limitado, persistência, exportação somente leitura e hashes.

A suíte integral foi tentada na linha de base: os quatro testes HTTP local foram bloqueados com
`WinError 10013` pelas permissões de sockets deste ambiente. Não foram alterados nem marcados como
aprovados. Para repetir a seleção offline no PowerShell, dentro de `aula-ia-backend`:

```powershell
@'
import unittest
suite = unittest.defaultTestLoader.discover('tests')
def casos(s):
    for t in s:
        if isinstance(t, unittest.TestSuite):
            yield from casos(t)
        else:
            yield t
suite = unittest.TestSuite(t for t in casos(suite) if not t.id().startswith('test_http.'))
resultado = unittest.TextTestRunner().run(suite)
raise SystemExit(not resultado.wasSuccessful())
'@ | python -S -
```

Em ambiente com sockets locais permitidos, executar a suíte completa:
`python -S -m unittest discover -s tests -q`.

## Limitações e próximo incremento

1. Repetir o ensaio com o mesmo caso real e o prompt `juiz-v1.2`, comparando parecer, notas,
   falhas e justificativas com a execução v1.1. Não presumir que um teste prove estabilidade.
2. Submeter as justificativas dos pareceres ao responsável/orientador; a validade do
   contrato não comprova pertinência pedagógica.
3. Seguir o protocolo RD-002: congelar expectativas antes das chamadas; criar cópias identificadas como
   `variante_controlada`, alterando uma condição por vez (evidência desalinhada, erro de algoritmo,
   recurso indisponível, adaptação genérica, conteúdo periférico) e um controle de síntese sem ET3 formal.
   Registrar novo hash, origem do caso-base e hipótese em documento separado; não enviar expectativas ao juiz.
4. Comparar detecção, omissões, falsos positivos e estabilidade. As hipóteses H01–H06 da revisão
   são expectativas humanas preliminares, não gabarito validado nem falhas já detectadas pelo modelo.
5. Integrar estados, persistência do parecer no serviço e correções dirigidas ao site em outro incremento.

## Fontes técnicas consultadas

- Groq, [Structured Outputs](https://console.groq.com/docs/structured-outputs): suporte de GPT-OSS 120B
  ao modo estrito e exigência de propriedades fechadas/obrigatórias.
- Groq, [Chat Completions API](https://console.groq.com/docs/api-reference): endpoint, parâmetros e metadados.
- [Revisão científica e protocolo RD-002](Revisao_Fundamentacao_Rubrica_Juiz_2026-11-17.md).

Os registros antigos que mencionam DeepSeek são históricos. A decisão implementada nesta PoC é GroqCloud.

## V02 — Comparação invertida no Bubble Sort (pré-registro)

A variante controlada V02 foi derivada do mesmo plano real SQLite, alterando somente
`plano.desenvolvimento[1].acao_discente` (ET2) para inverter o sentido da troca
em ordenação crescente. É um experimento de **erro conceitual**, distinto do
desalinhamento EVI2/OBJ2 estudado na V01. Não confundir a edição manual com
uma nova geração do Gemini. A hipótese, os hashes e o protocolo foram
congelados **antes de qualquer avaliação GroqCloud da V02**; não existem
resultados V02 registrados nesta revisão. Ver
[protocolo V02](../experimentos/juiz/Protocolo_V02_Bubble_Sort_Comparacao_Invertida.md).


### V02 — primeiro resultado real (17/11/2026)

Com o caso de comparação invertida de Bubble Sort (ET2), a chamada GroqCloud
retornou HTTP 200 e um parecer formalmente válido, mas atribuiu **18/18** e
`falhas=[]`, gerando `aguardando_decisao`. A regra incorreta de troca
`esquerda < direita` para ordenação crescente não foi identificada.
**Falso negativo nesta execução**, não prova de taxa geral de erro.
Ver [protocolo V02 atualizado](../experimentos/juiz/Protocolo_V02_Bubble_Sort_Comparacao_Invertida.md)
e [resumo rastreável do resultado](../experimentos/juiz/resultados/V02_20261117T190159Z_analise.json).

### V02 — segunda execução real (17/11/2026)

A segunda execução da mesma variante, com os mesmos parâmetros e hash do
plano, repetiu **18/18**, `falhas=[]` e `aguardando_decisao`, sem identificar
a comparação invertida. **Dois falsos negativos em dois pareceres válidos do
mesmo caso** — observação descritiva, não estimativa de taxa geral.
A estabilidade da decisão não comprova correção pedagógica. Ver o
[protocolo V02 (§7)](../experimentos/juiz/Protocolo_V02_Bubble_Sort_Comparacao_Invertida.md)
e o [segundo resumo estruturado](../experimentos/juiz/resultados/V02_20261117T190500Z_analise.json).

### V02 — terceira execução e encerramento da série (17/11/2026)

A terceira resposta real, com o mesmo caso de comparação invertida,
não detectou o erro de Bubble Sort. Apontou uma falha **menor** relacionada
à especificidade dos critérios EVI1/EVI2, nota total **17/18** e manteve
`aguardando_decisao`. A série V02 terminou com **0/3 detecções do
defeito-alvo em três pareceres tecnicamente válidos**, contra 3/3 na V01
(evidência desalinhada). Esses seis pareceres são repetições de apenas
**dois casos** — não caracterizam acurácia global do Juiz.

Os casos, resultados e limites foram consolidados em
[síntese comparativa V01 × V02](../experimentos/juiz/Sintese_Comparativa_V01_V02.md);
[protocolo V02 (§8)](../experimentos/juiz/Protocolo_V02_Bubble_Sort_Comparacao_Invertida.md)
e [resumo da terceira avaliação](../experimentos/juiz/resultados/V02_20261117T190802Z_analise.json).

**Marco de controle:** nenhuma correção automática ativada; antes de novas
chamadas, registrar proposta `juiz-v1.3` como configuração experimental
separada, mantendo intactas as evidências da v1.2.
