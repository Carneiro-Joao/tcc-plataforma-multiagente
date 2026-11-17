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
