# PoC 05C / RD-002 — Pré-registro da variante V03: recurso não confirmado (projeção e internet)

**Data do pré-registro:** 17/11/2026. **Situação:** hipótese congelada antes de qualquer chamada do Juiz com esta variante. Este documento é um protocolo de pesquisador, **não deve ser enviado à LLM**. **Faça o commit deste arquivo e do caso antes da primeira chamada real.**

## 1. Origem e integridade

- **Caso real de referência:** `experimentos/juiz/casos/ordenacao_real_994c4cd5.json`, geração `994c4cd51d944ca6a1344b15366c3971`.
- **Variante controlada:** `experimentos/juiz/casos/ordenacao_variante_projetor_nao_confirmado_03.json` (`origem.tipo=variante_controlada`, `id_variante=V03-RECURSO-NAO-CONFIRMADO`).
- **SHA-256 canônico do plano original:** `1b3bfddcee405c918e70d91faf1cd931419b71be84e5556885fe05b4dfec352d`.
- **SHA-256 canônico do plano da variante:** `16745a8550b34740cd9f9e3658efb5c9003dd73ce0002d8b3253c3caa3c54afb`.
- **SHA-256 canônico da entrada (idêntica à original):** `b57d56ed6d391b9a979699a7af44c9fb90143df021a4a83d8c901b6d9ede5a8c`.
- **SHA-256 da hipótese (JSON canônico da seção 3):** `c851dd8ee36f59d30945ba174ed90e7984b9358fc9867fe7b76c927056d6bca5`.
- **Modelo gerador registrado:** `gemini-3.5-flash-lite`, herdado somente para rastrear a origem do plano-base; a modificação foi feita pela ferramenta `variantes_juiz.py`, a partir de uma especificação versionada.
- **Juiz a avaliar:** `openai/gpt-oss-120b` via GroqCloud, prompt `juiz-v1.3`, contrato `parecer-juiz-1.0`, rubrica `rubrica-juiz-0.1`, política `politica-juiz-prelim-0.1`.
- **Natureza do conjunto:** O tipo de defeito **já é descrito pela rubrica** (indicador de `viabilidade`: usar somente os recursos confirmados, sem projetor, internet ou dispositivos não informados). O ensaio mede se o Juiz **aplica a rubrica que recebe** a um caso concreto; não mede a descoberta de defeitos imprevistos. O plano-base já foi usado no desenvolvimento do prompt: não é holdout de plano.

## 2. Manipulação isolada

Uma **única propriedade** foi alterada: `plano.desenvolvimento[0].acao_docente`.

**Valor do caso real:**

> Apresentar o conceito de algoritmos clássicos de manipulação de listas e demonstrar com cartões de papel a lógica de comparação de elementos adjacentes.

**Valor na V03:**

> Apresentar o conceito de algoritmos clássicos de manipulação de listas e demonstrar a lógica de comparação de elementos adjacentes projetando no quadro uma animação online do Bubble sort, avançando passo a passo na tela.

A ação docente de ET1 passa a exigir projeção em tela e acesso à internet. O contexto confirmado declara apenas `papel` como recurso. O campo `recursos` do plano permanece `papel`, de modo que a verificação mecânica de recursos não detecta a mudança: ela só aparece na prosa da etapa. Como apenas um campo foi alterado, `atividade` e `acao_discente` de ET1 continuam falando em cartões.

A ferramenta verificou que o valor original coincide com o caso congelado, que nenhum outro campo (inclusive a entrada confirmada) mudou e que o plano continua válido pelo contrato mecânico PlanoDeAula 2.0. A alteração é **semântica**: o validador Python não a detecta.

## 3. Hipótese registrada antes do ensaio

- **Hipótese principal:** O Juiz aponta que a ação docente de ET1 depende de projeção em tela e de acesso à internet, recursos que não constam entre os recursos confirmados (apenas papel).
- **Critério esperado:** `viabilidade`.
- **Aceito como detecção parcial:** O mesmo problema sob `coerencia_metodologica` (ET1 passa a contradizer a demonstração com cartões descrita na metodologia e em ET1). Conta como detecção parcial, não plena.
- **Componente responsável esperado:** `sequencia` (texto de ET1).
- **Gravidade provável:** `maior`: a etapa de abertura não pode ser executada como descrita com os recursos confirmados. `menor` conta como detecção parcial; `critica` será registrada como gravidade excessiva a adjudicar.
- **Nota esperada:** `viabilidade` no máximo 2.
- **Resultado negativo:** Nota 3 em `viabilidade` sem falha sobre ET1, ou justificativa que aceite a projeção sem mencionar a ausência do recurso.
- **Falsos positivos:** Falhas fora de `desenvolvimento[0].acao_docente` (por exemplo sobre EVI1, OBJ1/OBJ2 ou aderência curricular) são registradas separadamente e comparadas ao controle original; não contam como detecção.
- **Observação de desenho:** Apontar a incongruência entre a ação docente e a atividade de ET1 (que ainda cita cartões) é leitura legítima do mesmo defeito.

Esta expectativa é uma **hipótese do pesquisador, não um gabarito cientificamente validado**. Não ajustar a hipótese após observar a resposta do modelo; se for preciso corrigi-la, registre a correção como nova versão e preserve esta.

## 4. Procedimento

1. Validar localmente, sem rede nem chave (`--somente-validar`).
2. Executar o Juiz real com os mesmos parâmetros do controle original: prompt `juiz-v1.3`, temperatura 0, seed 42, `reasoning_effort=medium`, máximo 8192 tokens, `--reparos 1`.
3. Obter **três pareceres válidos**, esperando pelo menos 75 segundos entre chamadas (cota de ~8.000 tokens por minuto; cada julgamento consome ~7.000 a 8.200). Registrar **todas** as tentativas; HTTP 400, 429 e recusas são falhas técnicas, nunca detecção nem falso negativo.
4. Preservar `inicio.json`, `caso.json` e `resultado.json` de cada execução; guardar cópia de segurança fora de `local/`.
5. Verificar primeiro HTTP, contrato, invariantes e rastreio; depois comparar falhas, justificativas, componentes e decisão à hipótese. **Apontar qualquer falha não é detectar a falha-alvo.**
6. Encaminhar a pertinência pedagógica e a gravidade a um avaliador humano; uma série pequena não mede estabilidade, sensibilidade nem especificidade.

## 5. Comandos (PowerShell, na pasta `aula-ia-backend`)

Validação offline:

```powershell
python ensaio_juiz.py avaliar --caso ../experimentos/juiz/casos/ordenacao_variante_projetor_nao_confirmado_03.json --somente-validar
```

Série real (somente após a validação e o commit; precisa de `GROQ_API_KEY` no terminal):

```powershell
1..3 | ForEach-Object { python ensaio_juiz.py avaliar --caso ../experimentos/juiz/casos/ordenacao_variante_projetor_nao_confirmado_03.json --versao-prompt juiz-v1.3 --reparos 1; Start-Sleep -Seconds 75 }
```

Integridade (detecta edição do caso depois do pré-registro):

```powershell
python variantes_juiz.py verificar --spec ../experimentos/juiz/variantes/ordenacao_variante_projetor_nao_confirmado_03.spec.json
```

## 6. Resultados observados

*A preencher depois das execuções. Não alterar as seções 1 a 5.*
