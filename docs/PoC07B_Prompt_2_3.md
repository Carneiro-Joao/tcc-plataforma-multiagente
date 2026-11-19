# PoC07B — Prompt dos especialistas 2.3 (pré-registro)

**Status:** registrado em 18/11/2026, **antes** de qualquer geração com a 2.3. Decisão do João; pendente de ratificação do orientador.
Este protocolo não é editado depois de ver resultados; mudou a hipótese → nova versão.

## Motivo (evidência da 2.2)
Revisão de 5 planos reais gerados em 18/11 (`gemini-3.5-flash-lite`, `especialistas-plano-2.2`):
- **Recurso não confirmado:** 2 de 5 planos citam "cartões" sem cartões nos recursos (Ordenação/aula prática/quadro e pincel: 12 ocorrências;
  Ordenação/aula teórica/projetor, computadores: 1, em ADP1). Causa no código: `ORIENTACAO_RECURSOS` (2.2) dizia "sem acrescentar recursos"
  mas oferecia "manipulação de cartões já preparados" como alternativa.
- **Sem acentos:** 1 de 5 planos (Ordenação, 90 min) com 3 campos da avaliação sem acentuação ("observacao", "utilizara"). Causa desconhecida.

## Mudança
`geracao_v2.py`: `ORIENTACAO_RECURSOS_2_3` proíbe citar materiais, objetos ou dispositivos fora de `contexto.recursos`, não sugere nenhum
material, proíbe dizer que algo "já está preparado" e pede português com acentuação correta. Instruções por especialista inalteradas.
A 2.2 continua no código (`VERSOES_PROMPT`) e pode ser usada com `AgenteGeminiCompleto(versao_prompt="especialistas-plano-2.2")`.

## Hipóteses
- **H1:** com a 2.3, menos planos citam material ausente dos recursos (2.2: 2/5).
- **H2:** com a 2.3, menos planos têm campo longo sem acentos (2.2: 1/5). Fraca: a causa não é conhecida e a base é 1 caso.
- **Efeito colateral a observar:** a soma de minutos, a cobertura de IDs e a validade no contrato não pioram (2.2: 5/5 válidos).

## Protocolo
Mesmo modelo (`gemini-3.5-flash-lite`), mesmo app (`--gerador ia --ipv4`, reparos padrão), **mesma habilidade confirmada** e mesmo contexto:

| # | Tema | Tipo | Duração | Recursos (marcar exatamente) | Habilidade |
|---|---|---|---|---|---|
| 1 | Ordenação | Aula prática | 50 | quadro e pincel | EF08CO03 |
| 2 | Ordenação | Aula teórica | 90 | projetor, computadores | EF08CO03 |
| 3 | Listas | Aula teórica | 30 | projetor, computadores, internet | EF08CO02 |
| 4 | Estrutura de Dados | Computação desplugada | 60 | quadro e pincel, material impresso | EF08CO04 |
| 5 | Programação | Aula prática | 50 | material impresso | EF08CO01 |

Uma geração por linha (revisão 1). Falha técnica (503, 429, contrato) é registrada à parte e a linha é refeita uma vez; não conta como plano.
Exportar com `python exportar_planos.py`.

## Regra de medição (fixa)
Texto analisado: todos os campos do plano, exceto `recursos`, `referencias` e `habilidade_bncc`; comparação sem acentos e em minúsculas.
- **Material ausente (H1):** o plano conta como violação se contiver um destes radicais sem que o radical apareça em `contexto.recursos`:
  `cartao/cartoes`, `papel`, `baralho`, `ficha`, `projetor`, `data show`, `computador`, `internet`, `celular`, `quadro/pincel`, `impress`,
  `alto-relevo/tatil`. Exceção: `papel` não conta quando `impress` está nos recursos.
- **Sem acentos (H2):** o plano conta se algum campo de texto com mais de 60 caracteres não tiver nenhum de `áàâãéêíóôõúç` **e** contiver ao
  menos uma palavra da lista `observacao, avaliacao, explicacao, participacao, utilizara, apos, ordenacao, comparacao, verificacao, nao`.
  (A palavra-guia evita o falso positivo de frase que naturalmente não tem acento.)
- Resultado **descritivo** (contagens x/5). n = 5 não permite teste estatístico nem afirmar que a 2.3 "resolve"; a qualidade pedagógica
  continua dependendo da revisão humana.

## Fora do escopo
- O gerador de **demonstração** (regras locais, sem IA) também usa "cartões numerados já preparada" em Ordenação, mesmo sem cartões nos
  recursos (`geracao_v2.py`, `AgenteDemonstrativoCompleto`). Pendência separada.
- Incompatibilidade habilidade × recursos (EF08CO01 exige linguagem de programação; plano 5 só tem material impresso): será um alerta
  determinístico, não mudança de prompt.
