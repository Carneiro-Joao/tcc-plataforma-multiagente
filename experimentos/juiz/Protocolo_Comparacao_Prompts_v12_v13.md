# Protocolo prospectivo — Comparação do prompt `juiz-v1.2` com `juiz-v1.3`

**Data:** 17/11/2026. **Situação:** desenho e critérios registrados antes da primeira
chamada real da **v1.3**. As respostas anteriores da v1.2 são conhecidas
e foram usadas para decidir a melhoria. Não usar este documento como
entrada da IA Juiz; contém expectativas do pesquisador.

## 1. Hipótese e controle de viés

A v1.2 detectou o desalinhamento de evidência na V01 (3/3), mas
ignorou a comparação invertida do algoritmo da V02 (0/3). A mudança
da v1.3 é **somente** uma instrução adicional de auditoria conceitual
genérica: examinar operações e condições explícitas nas etapas,
confrontar resultado com objetivo e evidência, tentar mentalmente um
caso mínimo e localizar contradições verificáveis.

**H-13 (desenvolvimento):** com a nova instrução, o Juiz identifica
a operação conceitualmente incorreta no caso V02, aponta sua
consequência e atribui `componente=sequencia` no caso de uma falha
em ET2; sem perder a capacidade de detectar EVI2 desalinhada na V01.
`critica` é uma expectativa plausível para erro conceitual central,
mas gravidade deverá ser confirmada por avaliador humano.

**Não considerar V02 validação independente:** esse caso motivou
o desenho da v1.3. Um resultado favorável será evidência exploratória
de melhoria em conjunto de desenvolvimento, sujeita a superajuste.

## 2. Invariantes e casos congelados

**Invariantes mantidas:**
- Mesma LLM `openai/gpt-oss-120b` via GroqCloud e o mesmo
  `parecer-juiz-1.0`, `rubrica-juiz-0.1`, seis critérios, política
  `politica-juiz-prelim-0.1`, sequência de agentes e estado docente.
- Temperatura 0, seed 42, `reasoning_effort=medium`,
  `max_completion_tokens=8192`, `--reparos 1`.
- Histórico de v1.2 preservado; SHA-256 **da string exata do prompt v1.2**
  `f93058ca002d0718955d7ff391c77d3343030cd41005c8cf6732dd7f251280b5`.
  A opção `--versao-prompt` seleciona versões sem alterar os planos.

**Conjunto inicial (exploratório / regressão, NÃO holdout):**
1. Caso real original `experimentos/juiz/casos/ordenacao_real_994c4cd5.json`,
   hash canônico `1b3bfddcee405c918e70d91faf1cd931419b71be84e5556885fe05b4dfec352d`.
2. V01 `experimentos/juiz/casos/ordenacao_variante_evi2_desalinhada_01.json`,
   hash `74a89df558601df64ba9fcb50f402f7f2fe80d3baf972fe94aa6c286287c5249`.
3. V02 `experimentos/juiz/casos/ordenacao_variante_bubble_sort_comparacao_invertida_02.json`,
   hash `f98719c00248d16f95b26bfc138780ed0bf17c2eab5c3531a62c3a6b3de87c43`.

## 3. Métricas e condições de êxito

- **Detecção-alvo na V02:** o parecer identifica explicitamente a
  incompatibilidade entre uma regra de comparação na etapa ET2 e a
  ordenação crescente, e aponta `sequencia`. Não basta identificar
  qualquer problema periférico ou reduzir genericamente a nota.
- **Não regressão V01:** identificar que EVI2 não prova a execução
  requerida por OBJ2 e apontar `avaliacao_preliminar`.
- **Controle original:** não inventar falha curricular por exigir todos
  os algoritmos listados na BNCC; registrar separadamente quaisquer
  críticas concretas que mereçam avaliação humana. Não impor 18/18
  como nota obrigatória ao plano real.
- **Pertinência:** gravidade, componente, descrição e recomendação
  devem ser coerentes com cada falha; a revisão do orientador decide
  o que é adequadamente pedagógico.
- **Robustez:** contar três pareceres válidos para cada caso somente
  depois de um primeiro ensaio válido e registrar todas as tentativas;
  HTTP 400/429 e recusas são falhas técnicas, nunca falsas detecções.
  Relatar variações de `system_fingerprint`.
- **Operação:** preservar uso total de tokens, tempo, headers de limite,
  versão do prompt, hash do prompt e commit. Separar sucesso de API
  e aceitação por contrato de qualidade pedagógica.

**O que NÃO constitui resultado de sucesso:** obter JSON válido,
nota alta ou decisão `aguardando_decisao`, apontar uma falha não
relacionada ao defeito alvo ou ajustar o protocolo após a resposta.

## 4. Sequência de execução planejada

1. Atualizar a branch e executar testes offline de compatibilidade.
2. Validar os três casos sem rede com `--somente-validar --versao-prompt juiz-v1.3`.
3. Realizar primeiro ensaio real na V02, sem introduzir exemplo-alvo
   no prompt, para verificar a hipótese H-13.
4. Testar a V01 e o plano original com a mesma versão e parâmetros.
5. Se operacionalmente viável, ampliar para três repetições válidas
   por caso; resultados técnicos inválidos são mantidos separadamente.
6. Fechar a comparação descritiva com v1.2 e submeter achados a
   especialista/docente. Não alegar significância estatística,
   precisão populacional nem causalidade exclusiva do prompt,
   pois `system_fingerprint` pode variar.
7. **Criar pelo menos um caso realmente novo e não usado no refinamento**
   antes de reivindicar qualquer validação externa da melhoria.
   Registrar hipótese desse caso antes de avaliá-lo.

**Para uma comparação posterior mais forte**, considerar avaliação
intercalada v1.2/v1.3 com controle de janela/TPM e plano idêntico;
a série histórica da v1.2 permanece disponível como referência
observacional, não como ensaio pareado contemporâneo.

## 5. Comandos da CLI (PowerShell em `aula-ia-backend`)

Atualizar:
```powershell
git pull --ff-only origin feat/poc05b-juiz-groq
```

Testes offline:
```powershell
python -S -m unittest discover -s tests -p '*juiz*.py' -q
```

Validar V02 sem rede:
```powershell
python ensaio_juiz.py avaliar --caso ../experimentos/juiz/casos/ordenacao_variante_bubble_sort_comparacao_invertida_02.json --versao-prompt juiz-v1.3 --somente-validar
```

Primeira chamada real, **apenas depois dos testes**:
```powershell
python ensaio_juiz.py avaliar --caso ../experimentos/juiz/casos/ordenacao_variante_bubble_sort_comparacao_invertida_02.json --versao-prompt juiz-v1.3 --reparos 1
```

Reprodução de prompt antigo (não uma nova chamada obrigatória):
```powershell
python ensaio_juiz.py avaliar --caso ../experimentos/juiz/casos/ordenacao_variante_bubble_sort_comparacao_invertida_02.json --versao-prompt juiz-v1.2 --somente-validar
```

**Nenhum ensaio real v1.3 foi executado durante a criação deste protocolo.**
