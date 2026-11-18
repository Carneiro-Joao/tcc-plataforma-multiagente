# PoC 05C / RD-002 — Pré-registro da variante V06: perturbação semanticamente neutra (controle de estabilidade)

**Data do pré-registro:** 17/11/2026. **Situação:** hipótese congelada antes de qualquer chamada do Juiz com esta variante. Este documento é um protocolo de pesquisador, **não deve ser enviado à LLM**. **Faça o commit deste arquivo e do caso antes da primeira chamada real.**

## 1. Origem e integridade

- **Caso real de referência:** `experimentos/juiz/casos/ordenacao_real_994c4cd5.json`, geração `994c4cd51d944ca6a1344b15366c3971`.
- **Variante controlada:** `experimentos/juiz/casos/ordenacao_variante_perturbacao_neutra_06.json` (`origem.tipo=variante_controlada`, `id_variante=V06-PERTURBACAO-NEUTRA`).
- **SHA-256 canônico do plano original:** `1b3bfddcee405c918e70d91faf1cd931419b71be84e5556885fe05b4dfec352d`.
- **SHA-256 canônico do plano da variante:** `26045feac4b23d2acb6ae86fa815fc3ba953aef4b65b8c4a34b139c0119c4f86`.
- **SHA-256 canônico da entrada (idêntica à original):** `b57d56ed6d391b9a979699a7af44c9fb90143df021a4a83d8c901b6d9ede5a8c`.
- **SHA-256 da hipótese (JSON canônico da seção 3):** `eb88156b1f17c3e3b58b3116b8cb6663fb1804915948248a7f94df9ce38e8b4a`.
- **Modelo gerador registrado:** `gemini-3.5-flash-lite`, herdado somente para rastrear a origem do plano-base; a modificação foi feita pela ferramenta `variantes_juiz.py`, a partir de uma especificação versionada.
- **Juiz a avaliar:** `openai/gpt-oss-120b` via GroqCloud, prompt `juiz-v1.3`, contrato `parecer-juiz-1.0`, rubrica `rubrica-juiz-0.1`, política `politica-juiz-prelim-0.1`.
- **Natureza do conjunto:** Controle de estabilidade: **não há defeito a detectar**. Mede a variabilidade do Juiz diante de uma mudança sem consequência pedagógica. O plano-base já foi usado no desenvolvimento do prompt.

## 2. Manipulação isolada

Uma **única propriedade** foi alterada: `plano.objetivo_geral`.

**Valor do caso real:**

> Compreender e simular algoritmos clássicos de ordenação usando cartões de papel em uma atividade desplugada.

**Valor na V06:**

> Compreender e simular, em uma atividade desplugada com cartões de papel, algoritmos clássicos de ordenação.

O objetivo geral é reescrito com as mesmas palavras em outra ordem; o sentido não muda. Não há defeito a detectar. A variante serve para medir se uma mudança neutra, sem consequência pedagógica, altera os diagnósticos do Juiz (estabilidade) e quantas falhas novas ele inventa (falso positivo).

A ferramenta verificou que o valor original coincide com o caso congelado, que nenhum outro campo (inclusive a entrada confirmada) mudou e que o plano continua válido pelo contrato mecânico PlanoDeAula 2.0. A alteração é **semântica**: o validador Python não a detecta.

## 3. Hipótese registrada antes do ensaio

- **Hipótese principal:** Perturbação neutra. O Juiz não deve apontar falha nova atribuível à reformulação e deve reproduzir, no essencial, o conjunto de falhas (critério e componente) do controle original com o mesmo prompt.
- **Critério esperado:** Nenhum específico (controle de estabilidade).
- **Componente responsável esperado:** Nenhum.
- **Gravidade provável:** Não se aplica.
- **Nota esperada:** Sem queda sistemática em relação ao controle original.
- **Resultado negativo:** Instabilidade: falha `critica` ou `maior` nova, ligada ao objetivo geral e ausente no controle original; ou mudança de decisão causada por falha nova.
- **Falsos positivos:** Toda falha cuja descrição cite a reformulação do objetivo geral é falso positivo. Diferenças de conjunto de falhas em relação ao controle original sem citar a reformulação são registradas como variabilidade do Juiz ou do provedor, não como falso positivo.
- **Observação de desenho:** O controle original tem hoje um único parecer válido com `juiz-v1.3`. Para uma comparação justa, execute o plano original com o mesmo prompt até ter três pareceres válidos.

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
python ensaio_juiz.py avaliar --caso ../experimentos/juiz/casos/ordenacao_variante_perturbacao_neutra_06.json --somente-validar
```

Série real (somente após a validação e o commit; precisa de `GROQ_API_KEY` no terminal):

```powershell
1..3 | ForEach-Object { python ensaio_juiz.py avaliar --caso ../experimentos/juiz/casos/ordenacao_variante_perturbacao_neutra_06.json --versao-prompt juiz-v1.3 --reparos 1; Start-Sleep -Seconds 75 }
```

Integridade (detecta edição do caso depois do pré-registro):

```powershell
python variantes_juiz.py verificar --spec ../experimentos/juiz/variantes/ordenacao_variante_perturbacao_neutra_06.spec.json
```

## 6. Resultados observados

*A preencher depois das execuções. Não alterar as seções 1 a 5.*
