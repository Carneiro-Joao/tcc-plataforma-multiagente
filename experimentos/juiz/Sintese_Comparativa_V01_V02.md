# PoC 05B / RD-002 — Síntese comparativa preliminar V01 × V02

**Data da consolidação:** 17/11/2026, depois de encerrar as séries de teste.
**Escopo:** seis pareceres válidos de dois **casos distintos**, três repetições
por caso; uma tentativa adicional falhou tecnicamente na série V01.
Não é validação estatística do agente, nem estudo de casos independentes
ou avaliação com docentes.

## Desenho e rastreabilidade

O plano-base foi **gerado originalmente pelo Gemini** e extraído do SQLite,
com habilidade `EF08CO03` e atividade desplugada de Bubble Sort para 8º ano
em 50 minutos. As variantes V01 e V02 derivam **separadamente desse mesmo
plano-base real** e foram editadas manualmente pelo pesquisador, alterando
**um campo por variante**. Os dois casos passaram pela validação estrutural
offline e tiveram hipóteses registradas antes de chamar o Juiz.

**Avaliador comum:** GroqCloud `openai/gpt-oss-120b`, prompt `juiz-v1.2`,
rubrica `rubrica-juiz-0.1` (6 critérios e notas inteiras 0–3),
contrato `parecer-juiz-1.0`, temperatura 0, seed 42 e
`reasoning_effort=medium`. Mesmo prompt e mesmo contrato em todas
as avaliações comparadas; alterações entre commits foram documentais.

- **V01 — Evidência desalinhada:** campo
  `plano.avaliacao_aprendizagem.evidencias[1].evidencia_esperada`.
  EVI2 passa a observar atenção/interesse, sem demonstrar o OBJ2.
  Plano SHA-256 `74a89df558601df64ba9fcb50f402f7f2fe80d3baf972fe94aa6c286287c5249`.
  Ver [protocolo V01](Protocolo_V01_Evidencia_Desalinhada.md).
- **V02 — Erro de algoritmo:** campo `plano.desenvolvimento[1].acao_discente`.
  ET2 manda trocar elementos quando esquerda é **menor** que direita
  para obter ordenação **crescente**, invertendo a regra do Bubble Sort.
  Plano SHA-256 `f98719c00248d16f95b26bfc138780ed0bf17c2eab5c3531a62c3a6b3de87c43`.
  Ver [protocolo V02](Protocolo_V02_Bubble_Sort_Comparacao_Invertida.md).

## Resultados observados

| Propriedade | V01 — evidência | V02 — algoritmo |
|---|---|---|
| Pareceres formalmente válidos | 3 | 3 |
| **Detecção do defeito introduzido** | **3/3** | **0/3** |
| Nota total dos três pareceres | 15/18, 16/18, 16/18 | 18/18, 18/18, 17/18 |
| Gravidade do defeito injetado | 1 crítica, 2 maiores | Sem gravidade atribuída |
| Decisões dos pareceres | 1 `revisao_necessaria`, 2 `em_correcao` | 3 `aguardando_decisao` |
| Diagnóstico não associado diretamente à manipulação | 1 alegação curricular questionável | 1 falha menor sobre EVI1/EVI2, pertinência não adjudicada |
| Problema técnico observado | 1 execução: HTTP 400 e reparo HTTP 429 | Nenhum nas três avaliações válidas |

**Interpretação:** o juiz respondeu mais adequadamente à alteração
de **evidência de aprendizagem** que à inversão da **lógica algorítmica**
nestas duas variantes. No caso V02, três pareceres formalmente válidos
omitiram a contradição `esquerda < direita` versus ordenação crescente.
A política de decisão transformou os pareceres em estados sem erro
operacional aparente; a decisão repetidamente permissiva decorre do
**diagnóstico insuficiente**, não de falha de cálculo da política.

A V02 também mostrou que **apontar qualquer falha não é o mesmo que
detectar a falha-alvo**: no terceiro ensaio, a observação menor de
rubricas genéricas não pode contar como detecção do erro de Bubble Sort.

## Limitações e consequências para o desenvolvimento

- Amostra deliberadamente pequena: **2 variantes experimentais** do mesmo
  plano-base, com três repetições cada. Nenhum intervalo de confiança,
  precisão, revocação ou sensibilidade generalizável deve ser inferido.
- A hipótese/gabarito é do pesquisador e carece de revisão pedagógica
  humana; a regra do Bubble Sort, por sua vez, é verificável logicamente.
- Temperatura 0 e seed 42 não garantiram identidade de parecer, e os
  `system_fingerprint` registrados mudaram nas repetições.
- Viabilidade foi frequentemente justificada pela soma dos minutos já
  validada por código, contrariando o prompt.
- Parecer válido pelo JSON Schema **não implica** conteúdo pedagógico
  correto. Não permitir aprovação docente implícita nem correções
  automatizadas sem avaliação humana.
- O protocolo registrado é reprodutível por configuração e hashes,
  porém cópias integrais dos `resultado.json` permaneceram nas pastas
  locais `aula-ia-backend/local/ensaios_juiz/`; o GitHub guarda
  protocolos, resumo de achados e hashes de registros. Manter backup
  dessas pastas ao preparar a escrita do TCC.

**Próximo incremento proposto (não executado aqui):** desenvolver e
pré-registrar uma versão **diferente** do prompt/avaliação (por exemplo,
`juiz-v1.3`) com verificação explícita de **correção conceitual**,
exemplos verificáveis do algoritmo e contraste sistemático
ET2–objetivos–evidências. Comparar a versão nova à linha de base
`juiz-v1.2` no **mesmo conjunto congelado**, identificando separadamente
ganhos na V02 e possíveis regressões na V01. Avaliar também se cabe uma
verificação determinística por domínio em vez de confiar apenas em LLM.

## Pistas de redação para o TCC

Na seção de **metodologia**, relatar o desenho com alteração controlada,
pré-registro, três repetições por caso, esquema, hashes e separação entre
falha de API e falso negativo pedagógico. Na seção de **resultados**,
apresentar a tabela acima e os exemplos de omissões/sugestões
inadequadas. Na seção de **limitações**, destacar o tamanho do corpus,
ausência de adjudicação docente e não determinismo operacional.
