# PoC06 — Tema curto extraído automaticamente

**Origem:** feedback externo de 18/11/2026 ("no plano de aula está indo o input completo, e não somente o tema").
**Decisão de João:** a extração é automática, sem tela de confirmação. **Status: pendente de ratificação do orientador** (reversível).

## O que mudou
`aula-ia-backend/tema.py` extrai o tema do que o professor digitou, sem IA e sem rede, em três camadas:

1. **Catálogo** — trechos do texto que casam, como palavra inteira, com o vocabulário curricular (`rag/termos.py` + `objeto_conhecimento`
   da BNCC). Termos ligados só por "de/e/vírgula" viram um trecho único, na grafia digitada. Até 3 trechos separados.
2. **Marcador** — o que vem depois de "o tema é…", "quero ensinar sobre…", "aula/plano/atividade sobre…", "o que é…", cortado na pontuação
   ou em palavras como *para, com, usando, que, amanhã*. Cobre temas fora do catálogo ("IA generativa"). Se a frase do marcador contém o
   termo do catálogo e é mais completa, ela vence ("algoritmos de ordenação").
3. **Texto curto** — o próprio texto sem saudação, só se tiver até 80 caracteres e nenhum verbo de intenção ("quero", "preciso"…).

Se nada funciona, a consulta falha com **422** e a mensagem *"Não consegui identificar o tema. Escreva-o em poucas palavras, por exemplo: ordenação."*
Nada é gravado no banco nesse caso. O resultado é sempre um trecho do que o professor escreveu (nada inventado), com a primeira letra maiúscula.

## Onde entra
`ServicoCurricular.consultar`: `contexto.tema` passa a ser o tema curto e **a busca curricular também usa o tema curto**, não a frase.
Motivo medido em 18/11: com a frase "Olá, eu quero ensinar sobre IA generativa…" a busca devolvia 2 habilidades por palavras de ruído
("quero", "ensinar"…); com o tema "IA generativa" devolve vazio, que é o correto (a BNCC do 8º ano não tem IA). Título do plano, tela e a
validação `plano.tema == contexto.tema` também usam só o tema.
O texto original fica em `consulta.pedido_original` e a camada usada em `consulta.origem_tema` (`catalogo`/`marcador`/`texto`), fora do
`contexto`, que mantém o esquema fechado.

## Evidência e limites (provisória)
- `tests/test_tema.py`: 28 testes (20 frases com tema esperado e 13 frases que devem ser recusadas). Mutação manual do extrator e do
  serviço em duas rodadas (mais de 35 mutantes; 1 equivalente removido): **0 sobreviventes ao final**; os sobreviventes da 1ª rodada
  eram testes fracos e foram corrigidos.
- As 15 frases da sondagem de 18/11 foram usadas para corrigir bugs; **não são mais avaliação independente**. Placar antes das correções:
  8 aceitáveis e 7 com defeito; depois: 14 aceitáveis (uma recusa correta incluída) e 1 fraca ("Lista").
  Isto é regressão, não medida de acurácia. Para o TCC falta um conjunto de frases reais coletado de professores, não escrito por mim.
- Falso positivo conhecido: "atividade com lista de compras" → **"Lista"** (o termo `lista` do catálogo casa com o sentido não curricular).
- O gerador só recebe o tema curto: detalhes ditos na frase ("com cartões", "para turma com dislexia") não chegam ao plano, ficam só em
  `pedido_original`. Se isso incomodar, é uma decisão futura (campo de observações), não desta PoC.
- Fixtures `tests/dados/**/fixture_ordenacao.json` e `casos_estruturais.json` agora usam o tema curto "Ordenação" (antes "Quero ensinar ordenação",
  o defeito apontado). O caso `resposta_real_integrador` (resposta real gravada) foi mantido.

## Fora desta PoC (interface; vai para o Claude Code)
Esconder o JSON do professor (só com `?depuracao=1`), trocar o placeholder do tema para "Ex.: ordenação" com limite ~80 caracteres e
checklist de recursos.
