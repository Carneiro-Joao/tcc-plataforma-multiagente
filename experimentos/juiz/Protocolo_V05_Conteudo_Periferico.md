# PoC 05C / RD-002 — Pré-registro da variante V05: conteúdo periférico na etapa principal

**Data do pré-registro:** 17/11/2026. **Situação:** hipótese congelada antes de qualquer chamada do Juiz com esta variante. Este documento é um protocolo de pesquisador, **não deve ser enviado à LLM**. **Faça o commit deste arquivo e do caso antes da primeira chamada real.**

## 1. Origem e integridade

- **Caso real de referência:** `experimentos/juiz/casos/ordenacao_real_994c4cd5.json`, geração `994c4cd51d944ca6a1344b15366c3971`.
- **Variante controlada:** `experimentos/juiz/casos/ordenacao_variante_conteudo_periferico_05.json` (`origem.tipo=variante_controlada`, `id_variante=V05-CONTEUDO-PERIFERICO`).
- **SHA-256 canônico do plano original:** `1b3bfddcee405c918e70d91faf1cd931419b71be84e5556885fe05b4dfec352d`.
- **SHA-256 canônico do plano da variante:** `388bd9f875498e892b420de3d51bb317c48618c2e920842d68d6e44fb359c007`.
- **SHA-256 canônico da entrada (idêntica à original):** `b57d56ed6d391b9a979699a7af44c9fb90143df021a4a83d8c901b6d9ede5a8c`.
- **SHA-256 da hipótese (JSON canônico da seção 3):** `7e91aa5692c013f5d31da8ef4b62e34441b7af8dbab66df0b50498b7b80268f3`.
- **Modelo gerador registrado:** `gemini-3.5-flash-lite`, herdado somente para rastrear a origem do plano-base; a modificação foi feita pela ferramenta `variantes_juiz.py`, a partir de uma especificação versionada.
- **Juiz a avaliar:** `openai/gpt-oss-120b` via GroqCloud, prompt `juiz-v1.3`, contrato `parecer-juiz-1.0`, rubrica `rubrica-juiz-0.1`, política `politica-juiz-prelim-0.1`.
- **Natureza do conjunto:** O tipo de defeito **já é descrito pela rubrica** (indicadores e âncoras de `aderencia_curricular`: nenhum assunto periférico ocupa a maior parte do tempo; atividades principais que tratam de outro assunto). O ensaio mede se o Juiz **aplica a rubrica que recebe** a um caso concreto; não mede a descoberta de defeitos imprevistos. O plano-base já foi usado no desenvolvimento do prompt: não é holdout de plano.

## 2. Manipulação isolada

Uma **única propriedade** foi alterada: `plano.desenvolvimento[1].atividade`.

**Valor do caso real:**

> Atividade prática desplugada de simulação do Bubble sort utilizando cartões de papel com números.

**Valor na V05:**

> Pesquisa e debate em grupos sobre a história dos computadores e a evolução dos dispositivos de armazenamento, com registro das conclusões em papel.

A atividade de ET2, que ocupa 35 dos 50 minutos, passa a tratar da história dos computadores e do armazenamento, assunto alheio à habilidade EF08CO03 e ao OBJ2. Os IDs, os vínculos e a soma de minutos permanecem válidos. Como apenas um campo mudou, `acao_docente` e `acao_discente` de ET2 continuam falando em Bubble sort e cartões.

A ferramenta verificou que o valor original coincide com o caso congelado, que nenhum outro campo (inclusive a entrada confirmada) mudou e que o plano continua válido pelo contrato mecânico PlanoDeAula 2.0. A alteração é **semântica**: o validador Python não a detecta.

## 3. Hipótese registrada antes do ensaio

- **Hipótese principal:** O Juiz aponta que a atividade central de ET2 (35 dos 50 minutos) trata da história dos computadores e do armazenamento, assunto que não desenvolve a habilidade EF08CO03 nem o OBJ2.
- **Critério esperado:** `aderencia_curricular`.
- **Aceito como detecção parcial:** O mesmo problema sob `coerencia_metodologica` (incoerência entre a atividade e as ações de ET2), desde que a descrição diga que o assunto é alheio à habilidade ou aos objetivos. Apontar somente a incoerência interna, sem mencionar o assunto alheio, conta como detecção parcial.
- **Componente responsável esperado:** `sequencia` (texto de ET2).
- **Gravidade provável:** `critica` ou `maior` (a atividade principal trata de outro assunto). Será registrada a gravidade atribuída, sem se exigir uma delas.
- **Nota esperada:** `aderencia_curricular` no máximo 1.
- **Resultado negativo:** Nota 2 ou 3 em `aderencia_curricular` sem falha sobre a atividade de ET2, ou parecer que não relacione o assunto da atividade à habilidade e aos objetivos.
- **Falsos positivos:** Falhas fora de `desenvolvimento[1]` são registradas separadamente e comparadas ao controle original; não contam como detecção.
- **Observação de desenho:** A V02 também altera um campo de ET2 (`acao_discente`), com outra natureza de defeito (erro conceitual do algoritmo).

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
python ensaio_juiz.py avaliar --caso ../experimentos/juiz/casos/ordenacao_variante_conteudo_periferico_05.json --somente-validar
```

Série real (somente após a validação e o commit; precisa de `GROQ_API_KEY` no terminal):

```powershell
1..3 | ForEach-Object { python ensaio_juiz.py avaliar --caso ../experimentos/juiz/casos/ordenacao_variante_conteudo_periferico_05.json --versao-prompt juiz-v1.3 --reparos 1; Start-Sleep -Seconds 75 }
```

Integridade (detecta edição do caso depois do pré-registro):

```powershell
python variantes_juiz.py verificar --spec ../experimentos/juiz/variantes/ordenacao_variante_conteudo_periferico_05.spec.json
```

## 6. Resultados observados

*A preencher depois das execuções. Não alterar as seções 1 a 5.*
