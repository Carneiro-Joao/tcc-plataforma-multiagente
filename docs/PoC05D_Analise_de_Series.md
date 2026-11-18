# PoC 05D — Análise mecânica de séries de ensaios do Juiz

Rascunho técnico de 18/11/2026, em cima de `feat/poc05c-variantes`. Ferramenta de apoio: **não produz resultado científico por si só**.

## 1. Para que serve

Depois de rodar a série de uma variante (três pareceres válidos), é preciso ler cada parecer e compará-lo com a hipótese pré-registrada. `aula-ia-backend/analisar_serie.py` faz a parte **mecânica** dessa leitura e gera um rascunho para a seção 6 do protocolo. A leitura humana continua necessária.

O que ele faz, para cada execução da variante:

- **Separa falha técnica de parecer válido.** HTTP 400, 429 e recusas ficam em tabela própria e nunca entram como detecção nem como falso negativo.
- **Classifica o parecer** pelas regras de `experimentos/juiz/pontuacao/V0X.json`: `plena`, `parcial`, `a_adjudicar` (critério e componente certos, gravidade fora das listadas no protocolo) ou `ausente`. Falhas que não citam o ID-alvo vão para "fora do alvo" e ficam para adjudicação humana; **não** são declaradas falso positivo.
- **Controle (V06):** compara com a linha de base do plano original (pares critério/componente novos, falha crítica ou maior nova, mudança de decisão, falhas que citam a reformulação).
- **Audita o comportamento do Juiz** (informativo, nada é bloqueado): ID que não existe no plano, soma de minutos na justificativa (o prompt manda não fazer), nota 3 sem citar nenhum ID do plano, justificativas idênticas entre critérios e componente incompatível com os IDs citados.
- Resume tokens e tempo **somente quando informados** e conta as decisões.

## 2. Como usar

Na pasta `aula-ia-backend`, depois da série (os ensaios ficam em `local/ensaios_juiz/`):

```powershell
python analisar_serie.py --pasta local/ensaios_juiz --regra ../experimentos/juiz/pontuacao/V03.json --saida ../experimentos/juiz/resultados/V03_rascunho.md
```

Para a V06, informe também a pasta do caso original como linha de base:

```powershell
python analisar_serie.py --pasta local/ensaios_juiz --regra ../experimentos/juiz/pontuacao/V06.json --baseline-pasta local/ensaios_juiz --saida ../experimentos/juiz/resultados/V06_rascunho.md
```

O relatório não sobrescreve arquivos existentes. Cole o que for útil na seção 6 do protocolo **sem alterar as seções 1 a 5**.

## 3. Regra de integridade

Os arquivos em `experimentos/juiz/pontuacao/` são derivados do texto já pré-registrado e trazem o hash da hipótese (`fonte.sha256_hipotese`). Um teste confere que cada regra bate com os critérios e componentes do texto da hipótese. **Faça o commit deles antes de rodar a série e não os edite depois de ver resultados.** Se uma regra estiver errada, crie uma nova versão e preserve a antiga.

## 4. Limites

- A classificação é provisória. Uma falha só é relacionada ao alvo se **citar o ID-alvo** (por exemplo, `ET1`); uma falha correta que não cite ID aparece como "fora do alvo".
- V05 trata `coerencia_metodologica` como detecção **parcial** porque a diferença para a plena depende de ler se a descrição diz que o assunto é alheio, o que o código não faz.
- Três pareceres por variante descrevem o comportamento nesses casos; não medem estabilidade, sensibilidade nem especificidade.
- A auditoria de soma de minutos usa uma expressão regular; pode haver falso positivo (por exemplo, uma soma legítima de itens) e falso negativo (uma soma escrita por extenso).
- Os testes usam pareceres **sintéticos** gerados pelo próprio `executar_ensaio` com agentes falsos. Eles provam a lógica do analisador, não o comportamento de um LLM.

## Correção de 17/11 (noite): controle só vale na mesma configuração

Problema achado na revisão: o analisador escolhia os controles do plano original só por `origem.tipo = sqlite_real`.
No repositório existem 3 pareceres válidos desse plano, mas de **prompts diferentes** (v1.1, v1.2, v1.3), então havia
apenas **1** controle válido para a configuração v1.3, e não 3.

Agora um controle só entra na linha de base se tiver o **mesmo `plano_sha256`** (hash do plano original, lido de
`origem.plano_base_sha256` da variante) e a **mesma configuração experimental** da série analisada: modo, versão e hash do
prompt, rubrica, adaptador, esquema da API, modelo do Juiz, parâmetros e política de decisão. O relatório lista cada
controle descartado e o motivo. Série com configurações misturadas não recebe baseline.

Antes de existir qualquer parecer da variante, `--versao-prompt juiz-v1.3` conta quantos controles daquela versão existem.

Limite que continua valendo na detecção (V03 a V05): "plena" = ID-alvo citado + critério + componente + gravidade
esperados. Isso **não** confirma que o texto descreve o defeito inserido; o relatório mostra o trecho (`trechos_do_alvo`)
e `semantica_confirmada` é sempre `False` até a adjudicação humana.
