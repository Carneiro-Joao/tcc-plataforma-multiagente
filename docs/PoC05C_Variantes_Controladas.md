# PoC 05C — Variantes controladas para ensaiar a IA Juiz

Rascunho técnico de 17/11/2026, em cima de `feat/poc05b-juiz-groq`. As hipóteses são do pesquisador, não gabarito validado. Nenhuma das quatro variantes foi enviada à API: **os resultados ainda não existem**.

## 1. O que a ferramenta faz

`aula-ia-backend/variantes_juiz.py` transforma uma **especificação** (campo, valor original, valor novo e hipótese) em um caso congelado e um protocolo de pré-registro. Antes de gravar, ela confere que:

- o `valor_original` coincide com o caso-base congelado;
- **só aquele campo** mudou (a entrada confirmada, o modelo gerador e a revisão ficam intactos);
- o plano continua válido pelo contrato mecânico PlanoDeAula 2.0, ou seja, a alteração é semântica;
- os hashes canônicos do plano, da entrada e da hipótese são calculados e registrados.

A criação é atômica: se o caso **ou** o protocolo já existir, nada é gravado. A hipótese vive só na especificação e no protocolo; o teste `test_caso_enviado_ao_juiz_nao_contem_hipotese_nem_identificacao_da_variante` prova que ela, o `id_variante` e a `origem` não chegam à requisição do Juiz.

Prova de fidelidade: com a especificação certa, a ferramenta **reproduz a sua V01 manual byte a byte** e a V02 (exceto a observação, que tem texto próprio e agora é um campo opcional `observacao_origem`).

## 2. As quatro variantes

Todas derivam de `ordenacao_real_994c4cd5.json` (EF08CO03, 50 min, recurso `papel`).

| Variante | Campo alterado | Defeito | Critério / componente esperados | Gravidade provável |
|---|---|---|---|---|
| V03 | `desenvolvimento[0].acao_docente` | Exige projeção e internet, que não foram confirmados | `viabilidade` / `sequencia` | `maior` |
| V04 | `adaptacoes[1].descricao` | Adaptação genérica, aplicável a qualquer plano | `inclusao` / `adaptacao` | `maior` |
| V05 | `desenvolvimento[1].atividade` | Atividade principal (35 de 50 min) trata de outro assunto | `aderencia_curricular` / `sequencia` | `critica` ou `maior` |
| V06 | `objetivo_geral` | **Nenhum**: reescrita neutra, controle de estabilidade | — | — |

O detalhe de cada hipótese (incluindo o que conta como detecção parcial, resultado negativo e falso positivo) está em `experimentos/juiz/Protocolo_V0X_*.md` e nas especificações em `experimentos/juiz/variantes/`.

## 3. O que estes ensaios medem (e o que não medem)

- **V03, V04 e V05 medem se o Juiz aplica a rubrica que recebe.** Os três tipos de defeito já aparecem nos indicadores e nas âncoras da rubrica, que faz parte do prompt. Não medem a descoberta de defeitos imprevistos. Entre os casos atuais, só a V02 (erro conceitual do Bubble Sort) está fora da rubrica.
- **O plano-base já foi usado no desenvolvimento.** Isto não é holdout de plano. Casos de outras habilidades (gerados pelo site) continuam sendo o passo que realmente testa generalização.
- **A V06 não tem defeito.** Mede variabilidade: falhas novas que ela provoca e mudanças de decisão. Para uma linha de base justa, o plano original precisa de três pareceres válidos com `juiz-v1.3` (hoje há um).
- Três pareceres por variante **não medem** estabilidade, sensibilidade nem especificidade; descrevem o comportamento nesses casos.

## 4. Como executar

Na pasta `aula-ia-backend`, no PowerShell. A ordem importa:

1. **Commit antes de chamar a API.** Faça o commit dos casos, protocolos e especificações. O pré-registro só vale se o texto da hipótese estiver no Git antes do primeiro ensaio.
2. **Integridade** (sem rede nem chave): `python variantes_juiz.py verificar --spec ../experimentos/juiz/variantes/<arquivo>.spec.json`.
3. **Validação offline** do caso: `python ensaio_juiz.py avaliar --caso ../experimentos/juiz/casos/<caso>.json --somente-validar`.
4. **Série real**, com `GROQ_API_KEY` definida: o comando exato está na seção 5 de cada protocolo (três pareceres, pausa de 75 s entre chamadas por causa da cota de tokens por minuto).
5. **Backup** de `local/ensaios_juiz/` fora do Git ou commit dos `resultado.json` saneados. Sem o arquivo, o hash não prova nada.
6. Preencher a seção 6 do protocolo **sem alterar as seções 1 a 5**. Falhas HTTP 400 e 429 entram como falhas técnicas, separadas dos pareceres válidos.

Estimativa de uso, a partir dos seus registros (7.224 a 8.212 tokens por julgamento): 4 variantes × 3 pareceres + 2 do controle original = cerca de 14 chamadas, 18 minutos de espera e ~100 mil tokens. Confirme o seu limite diário na Groq.

## 5. Criar uma nova variante

1. Copie uma especificação de `experimentos/juiz/variantes/` e edite: `id_variante` (começa por `numero` e hífen), `campo`, `valor_original` (texto exato do caso-base), `valor_novo`, arquivos de saída, `natureza_do_conjunto` e `hipotese` (obrigatórios: `principal`, `criterio_esperado`, `componente_esperado`).
2. `python variantes_juiz.py criar --spec <spec> --data AAAA-MM-DD`.
3. Faça o commit e só então ensaie.

Para uma variante de **outro plano-base**, aponte `caso_base` para um caso extraído do SQLite com `ensaio_juiz.py` e use um campo daquele plano.
