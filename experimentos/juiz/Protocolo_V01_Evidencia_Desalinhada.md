# PoC 05B / RD-002 — Pré-registro da variante V01

**Data do pré-registro:** 17/11/2026. **Situação:** hipótese congelada antes de qualquer chamada do Juiz com esta variante. Este documento é um protocolo de pesquisador, **não deve ser enviado à LLM**.

## 1. Origem e integridade

- **Caso real de referência:** `experimentos/juiz/casos/ordenacao_real_994c4cd5.json`, extraído do SQLite, geração `994c4cd51d944ca6a1344b15366c3971`.
- **Variante controlada:** `experimentos/juiz/casos/ordenacao_variante_evi2_desalinhada_01.json` (`origem.tipo=variante_controlada`). Não confundir com uma geração real nem com fixtures sintéticas.
- **SHA-256 canônico do plano original:** `1b3bfddcee405c918e70d91faf1cd931419b71be84e5556885fe05b4dfec352d`.
- **SHA-256 canônico do plano da variante:** `74a89df558601df64ba9fcb50f402f7f2fe80d3baf972fe94aa6c286287c5249`.
- **SHA-256 canônico da entrada (idêntica à original):** `b57d56ed6d391b9a979699a7af44c9fb90143df021a4a83d8c901b6d9ede5a8c`.
- **Modelo gerador registrado:** `gemini-3.5-flash-lite`, herdado somente para rastrear a origem do plano-base; a modificação experimental foi feita manualmente pelo pesquisador.
- **Juiz a avaliar:** `openai/gpt-oss-120b` via GroqCloud, com prompt `juiz-v1.2`, contrato `parecer-juiz-1.0`, rubrica `rubrica-juiz-0.1` (seis critérios, notas 0–3), política `politica-juiz-prelim-0.1`.

## 2. Manipulação isolada

Uma **única propriedade do plano** foi alterada: `plano.avaliacao_aprendizagem.evidencias[1].evidencia_esperada` (EVI2, vinculada a OBJ2).

- **Valor do caso real:** “O estudante reorganiza os cartões de papel de forma sequencial crescente através de contagem oral e troca manual.”
- **Valor na V01:** “O estudante presta atenção à demonstração do professor e afirma ter gostado da atividade.”

OBJ2 exige que o estudante simule o Bubble Sort comparando e manipulando cartões. A evidência manipulada observa apenas atenção e interesse. O critério da evidência, os instrumentos (inclusive INS2), as etapas, a habilidade EF08CO03, a entrada e os demais campos do plano são preservados. O teste pretende introduzir **desalinhamento pedagógico**, mantendo as invariantes estruturais.

## 3. Hipótese registrada antes do ensaio

- **H-V01 (principal):** o Juiz aponta que EVI2 não demonstra a execução requerida por OBJ2; a descrição ou justificativa deve relacionar a falha a ambos.
- **Critério esperado:** `avaliacao_aprendizagem`.
- **Componente responsável esperado:** `avaliacao_preliminar` (texto da evidência); não `avaliacao_final` nem `objetivos`.
- **Gravidade provável:** `maior`, pois um objetivo específico central deixou de ter evidência direta; classificação ainda sujeita à revisão pedagógica humana. Uma marcação `menor` será registrada como detecção parcial, não como aprovação plena da hipótese.
- **Nota esperada do critério:** no máximo 2 (se houver uma falha conforme o contrato). Com gravidade `maior`, a política atual sugere `em_correcao`; com falha apenas `menor`, pode sugerir `aguardando_decisao`.
- **Resultado negativo:** nota 3 sem falha no critério, ou justificativa que ignore a insuficiência de EVI2 para OBJ2.
- **Falsos positivos:** registrar separadamente falhas apontadas fora da manipulação e verificá-las com o plano, sem presumir que são necessariamente incorretas.

Esta expectativa é uma **hipótese do pesquisador, não um gabarito cientificamente validado**. Não ajustar a hipótese após observar a resposta do modelo.

## 4. Procedimento

1. Validar a V01 localmente, sem rede nem chave, usando `--somente-validar`.
2. Executar o Juiz real com a V01 e os mesmos parâmetros usados no caso-base: temperatura 0, seed 42, reasoning_effort medium, máximo 8192 tokens, `--reparos 1`. A existência de reparo técnico não representa correção pedagógica.
3. Preservar `inicio.json`, `caso.json`, `resultado.json` produzidos em uma pasta nova a cada execução; nunca sobrescrever o caso real.
4. Verificar primeiro HTTP, contrato, invariantes e rastreio. Depois comparar falhas, justificativas, componentes e decisão à hipótese e à linha de base.
5. Encaminhar a pertinência pedagógica a um avaliador humano/orientador; um ensaio isolado não valida a rubrica e não mede estabilidade.

**Linha de base mais recente:** ensaio real com prompt v1.2 de 17/11/2026, caso original, seis notas 3, nenhuma falha e sugestão `aguardando_decisao`. Os casos não devem ser trocados entre si.

## 5. Comandos (PowerShell, na pasta `aula-ia-backend`)

Validação offline:

```powershell
python ensaio_juiz.py avaliar --caso ../experimentos/juiz/casos/ordenacao_variante_evi2_desalinhada_01.json --somente-validar
```

Ensaio real, **somente após a validação**:

```powershell
python ensaio_juiz.py avaliar --caso ../experimentos/juiz/casos/ordenacao_variante_evi2_desalinhada_01.json --reparos 1
```

## 6. Resultados observados — série V01 (17/11/2026)

**Análise posterior aos ensaios, sem alteração da hipótese pré-registrada (§3).**
As execuções utilizaram o mesmo arquivo de caso (SHA-256 de arquivo
`6d1d376c812963648620c6e2462e1a9ef22975f1bc1d1e6a339408492e66dcd5`),
a mesma revisão de código `794af1a`, prompt `juiz-v1.2`, rubrica
`rubrica-juiz-0.1`, modelo `openai/gpt-oss-120b`, temperatura 0, seed 42,
`reasoning_effort=medium`, `max_completion_tokens=8192` e `--reparos 1`.
Os registros originais de execução estão na pasta local ignorada pelo Git
(`aula-ia-backend/local/ensaios_juiz/`) do responsável; **os arquivos
`resultado.json` não foram incorporados ao Git nesta atualização**.

| Ensaio / pasta UTC | Status | Nota aderência | Nota avaliação da aprendizagem | Falhas emitidas | Decisão |
| --- | --- | ---: | ---: | --- | --- |
| `20261117T184531Z-e40eead530df` | sucesso / parecer válido | 2 | 1 | F1 curricular questionável (`maior`); F2 EVI2 × OBJ2 (`critica`) | `revisao_necessaria` |
| `20261117T184810Z-ec3aac6cfbf5` | sucesso / parecer válido | 3 | 1 | F1 EVI2 × OBJ2 (`maior`) | `em_correcao` |
| `20261117T185010Z-ae34c9511e83` | falha / sem parecer válido | — | — | 1ª chamada HTTP 400: `componente="conteudos"` fora do enum; reparo técnico HTTP 429 (TPM 8.000, `retry-after: 43`) | nenhuma |
| `20261117T185332Z-b68b4a0e4708` | sucesso / parecer válido | 3 | 1 | F1 EVI2 × OBJ2 (`maior`) | `em_correcao` |

**Consolidação descritiva (somente três pareceres aceitos):**

- **Detecção do desalinhamento EVI2 × OBJ2:** 3/3.
- **Critério correto `avaliacao_aprendizagem` e componente correto
  `avaliacao_preliminar`:** 3/3.
- **Gravidade prevista `maior`:** 2/3; uma avaliação indicou `critica`.
  A adequação da gravidade depende de revisão pedagógica humana.
- **Decisão prevista `em_correcao`:** 2/3; uma indicou
  `revisao_necessaria` em razão da classificação `critica`.
- **Falso positivo curricular aparente (exigir outros algoritmos além de
  Bubble Sort na mesma aula):** 1/3 pareceres válidos. No ensaio rejeitado
  com HTTP 400, a geração bruta também repetiu essa alegação, mas **não é
  parecer válido** e não entra nesse denominador.
- **Pontuação total:** 15/18 na primeira avaliação válida; 16/18 nas duas
  seguintes. A nota de `avaliacao_aprendizagem` foi 1/3 nas três.
- **Problema recorrente de justificativa:** nota 3 em `viabilidade` ainda
  se apoia parcialmente na soma de minutos, já validada mecanicamente.
  As avaliações bem-sucedidas também sugeriram ajustar INS2, embora seu
  procedimento já descreva observação das trocas; revisar a necessidade.

**Limites e integridade:** os ensaios são repetições de **um único caso
manualmente manipulado**, não três casos independentes nem validação
estatística. O mesmo `seed` e a temperatura 0 não garantiram respostas
idênticas; houve diferentes `system_fingerprint` registrados. A detecção
demonstrada não garante especificidade, precisão global, calibração da
gravidade ou adequação da política de correção. O HTTP 400 inicial e o 429
do reparo devem ser relatados como falhas técnicas separadas dos pareceres
aceitos. A aprovação docente não foi alterada e nenhum ciclo pedagógico de
correção foi executado.

**Encaminhamento:** manter o prompt, a rubrica e o contrato congelados nesta
série. Submeter a avaliação da gravidade e o falso positivo curricular ao
orientador; pré-registrar a V02 em documento próprio antes de uma nova
chamada real. Evitar integrar correção automática enquanto as decisões e
diagnósticos não forem mais bem avaliados.
