# PoC 05C / RD-002 — Pré-registro da variante V04: adaptação genérica

**Data do pré-registro:** 17/11/2026. **Situação:** hipótese congelada antes de qualquer chamada do Juiz com esta variante. Este documento é um protocolo de pesquisador, **não deve ser enviado à LLM**. **Faça o commit deste arquivo e do caso antes da primeira chamada real.**

## 1. Origem e integridade

- **Caso real de referência:** `experimentos/juiz/casos/ordenacao_real_994c4cd5.json`, geração `994c4cd51d944ca6a1344b15366c3971`.
- **Variante controlada:** `experimentos/juiz/casos/ordenacao_variante_adaptacao_generica_04.json` (`origem.tipo=variante_controlada`, `id_variante=V04-ADAPTACAO-GENERICA`).
- **SHA-256 canônico do plano original:** `1b3bfddcee405c918e70d91faf1cd931419b71be84e5556885fe05b4dfec352d`.
- **SHA-256 canônico do plano da variante:** `7ea6c476961ca1de8dd61f93b467650ec65c953ca98b451d0671c2550f904b99`.
- **SHA-256 canônico da entrada (idêntica à original):** `b57d56ed6d391b9a979699a7af44c9fb90143df021a4a83d8c901b6d9ede5a8c`.
- **SHA-256 da hipótese (JSON canônico da seção 3):** `6443389ec3805f0e7d5de67e54623e6e786a1dbed50712853ddccd9cc80f4ff1`.
- **Modelo gerador registrado:** `gemini-3.5-flash-lite`, herdado somente para rastrear a origem do plano-base; a modificação foi feita pela ferramenta `variantes_juiz.py`, a partir de uma especificação versionada.
- **Juiz a avaliar:** `openai/gpt-oss-120b` via GroqCloud, prompt `juiz-v1.3`, contrato `parecer-juiz-1.0`, rubrica `rubrica-juiz-0.1`, política `politica-juiz-prelim-0.1`.
- **Natureza do conjunto:** O tipo de defeito **já é descrito pela rubrica** (indicador e âncora de `inclusao`: adaptações específicas do plano, não frases genéricas). O ensaio mede se o Juiz **aplica a rubrica que recebe** a um caso concreto; não mede a descoberta de defeitos imprevistos. O plano-base já foi usado no desenvolvimento do prompt: não é holdout de plano.

## 2. Manipulação isolada

Uma **única propriedade** foi alterada: `plano.adaptacoes[1].descricao`.

**Valor do caso real:**

> Reduzir a quantidade de cartões de papel utilizados simultaneamente na simulação do Bubble sort, focando em pares menores para facilitar a contagem oral e a manipulação manual.

**Valor na V04:**

> Adaptar as atividades conforme as necessidades individuais de cada estudante, oferecendo apoio adicional sempre que necessário.

A descrição de ADP2 passa a ser uma frase aplicável a qualquer plano de qualquer disciplina: não indica material, alternativa de participação nem como o apoio ocorre. Os vínculos com OBJ1, OBJ2 e ET2 são preservados, então o contrato mecânico continua satisfeito. ADP1 permanece específica.

A ferramenta verificou que o valor original coincide com o caso congelado, que nenhum outro campo (inclusive a entrada confirmada) mudou e que o plano continua válido pelo contrato mecânico PlanoDeAula 2.0. A alteração é **semântica**: o validador Python não a detecta.

## 3. Hipótese registrada antes do ensaio

- **Hipótese principal:** O Juiz aponta que ADP2 é genérica: não oferece alternativa concreta de participação ou de demonstração da aprendizagem e poderia ser copiada para qualquer plano.
- **Critério esperado:** `inclusao`.
- **Componente responsável esperado:** `adaptacao`.
- **Gravidade provável:** `maior` (a rubrica descreve adaptações genéricas como nota 1). `menor` conta como detecção parcial.
- **Nota esperada:** `inclusao` no máximo 2; esperada 1 se a falha for `maior`.
- **Resultado negativo:** Nota 3 em `inclusao` sem falha sobre ADP2, ou elogio de ADP2 como específica ou concreta.
- **Falsos positivos:** Falhas sobre ADP1 ou fora de `adaptacoes` são registradas separadamente e comparadas ao controle original; não contam como detecção.
- **Observação de desenho:** Como ADP1 continua específica, é plausível uma nota 2 com falha sobre ADP2. Isso será lido como detecção, com a nota registrada.

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
python ensaio_juiz.py avaliar --caso ../experimentos/juiz/casos/ordenacao_variante_adaptacao_generica_04.json --somente-validar
```

Série real (somente após a validação e o commit; precisa de `GROQ_API_KEY` no terminal):

```powershell
1..3 | ForEach-Object { python ensaio_juiz.py avaliar --caso ../experimentos/juiz/casos/ordenacao_variante_adaptacao_generica_04.json --versao-prompt juiz-v1.3 --reparos 1; Start-Sleep -Seconds 75 }
```

Integridade (detecta edição do caso depois do pré-registro):

```powershell
python variantes_juiz.py verificar --spec ../experimentos/juiz/variantes/ordenacao_variante_adaptacao_generica_04.spec.json
```

## 6. Resultados observados

*A preencher depois das execuções. Não alterar as seções 1 a 5.*
