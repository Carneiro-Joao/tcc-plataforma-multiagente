# PoC 11 — Acento em campos curtos + recomendação ao professor

**Data:** 25/11/2026 · **Branch:** `feat/poc11-acento-curto-e-recomendacao` (a partir de `fix/auditoria-25-11-c1-c4-c5-c9` @ `0f5b8df`)
**Autorização:** pedido do João depois do lote de 25/11 ("implementar 1 e 2 numa branch nova"). Origem: problemas 1 e 2 do
`experimentos/geracao/lote_25-11/resumo.md`. Fora desta PoC, por decisão do João: "só Bubble sort" (fica de molho, como observação
para a adjudicação) e o tema "Segurança e privacidade e internet" (não será corrigido).
**Sem chamadas reais de API.** Nada levado à `main`.

---

## 1. Resumo para quem vai ajustar o texto

| | Antes | Agora (PoC 11) |
|---|---|---|
| Acento em campo curto (título de etapa, item de conteúdo) | Não era verificado (só campos com mais de 60 caracteres) — no lote, o cenário 3 saiu com "Introducao ao Conceito…", "Execucao Completa…" | Verificado com palavras **inequívocas**; se faltar acento, entra na mesma reescrita única da PoC 10 |
| Habilidade de programação sem computador | Alerta **só antes** de gerar (resumo da confirmação) | Alerta antes de gerar **e** "Recomendação ao professor" junto do plano entregue |
| Habilidade de programação em aula teórica | Nenhum aviso | Novo alerta + recomendação (mesmo com computador marcado) |
| Bloqueio | — | **Nenhum.** O plano é gerado do jeito que o professor pediu |

---

## 2. Acento em campos curtos (`deteccao-acentuacao-1.1`)

### 2.1 O problema
No lote de 25/11, cenário 3 (busca binária), os títulos das etapas saíram sem acento nas duas versões, embora o resto do plano estivesse
acentuado: o detector da PoC 10 só olhava campos com mais de 60 caracteres (regra pensada para frases; títulos são curtos).

### 2.2 A regra nova (`aula-ia-backend/acentuacao.py`)
Um campo conta como "sem acentuação" quando **não tem nenhum** caractere acentuado (`áàâãéêíóôõúç`) **e**:
- **campo longo (> 60 caracteres):** tem qualquer palavra-guia — regra da PoC 10, sem mudança ("avaliacao", "nao", "sera", "pratica",
  "logica", "sequencia"…);
- **campo curto (novo):** tem uma palavra **inequívoca**, que nunca se escreve sem acento: terminações -cao/-coes/-sao/-soes
  ("introducao", "execucao", "revisao"), "nao", "sera", "serao", "tambem", "voce(s)", "entao", "estao".

Ficam de fora dos campos curtos as palavras que existem sem acento como verbo ou nome ("o aluno **pratica**", "que ele **analise**",
"**especifica**", "sequencia", "ate", "sao", "ja"), para não pedir reescrita de um título correto. Continua valendo:
- o campo `recursos` (cópia do que o professor digitou) é ignorado (auditoria C2);
- **uma** reescrita por especialista; aceita só se o contrato validar, IDs/números/vínculos/estrutura ficarem iguais (C1) e o número de
  campos sem acento cair; senão fica a original; nunca derruba a geração;
- só no modo IA.

Novidade no rastreio: o registro da reescrita leva `"regra": "deteccao-acentuacao-1.1"`.

### 2.3 Custo e limites
- Pode disparar a reescrita em especialistas que antes passavam (por causa de um título curto). Continua no máximo 1 chamada extra por
  especialista (0 a 6 por versão), fora do limite diário.
- Continua heurística: título curto sem palavra inequívoca escapa (ex.: "Logica de comparacao" — "comparacao" pega; "Pratica guiada" não).

---

## 3. Recomendação ao professor (conflito da própria entrada)

### 3.1 O problema
Cenário 4 do lote: EF08CO02 ("criar soluções … automatizá-las usando uma linguagem de programação") em **aula teórica**, só com quadro e
projetor. O alerta de computador aparecia antes de gerar, mas sumia depois; e o tipo de aula não era considerado. A regeneração informada
não resolve isso (a 2ª versão passou a prometer "implementar" um algoritmo numa aula sem computador, e o Juiz apontou).

### 3.2 As regras (`aula-ia-backend/servico.py`, `alertas_recursos`) — determinísticas, sem IA
Só para as habilidades que pedem programação (`HABILIDADES_COM_COMPUTADOR` = EF08CO01, EF08CO02):

| Código | Quando | Recomendação (texto mostrado junto do plano) |
|---|---|---|
| `habilidade_sem_computador` (já existia) | "computador" não está nos recursos | "Para trabalhar a EF08CO0X por inteiro, os estudantes precisam programar: marque “computadores” nos recursos e gere de novo, ou confirme outra habilidade." |
| `habilidade_aula_teorica` (**novo**) | tipo = "Aula teórica" (mesmo com computador) | "Para trabalhar a EF08CO0X por inteiro, considere uma aula prática com computadores e gere de novo, ou confirme outra habilidade." |

Cada alerta tem `mensagem` (o aviso, mostrado no resumo da confirmação, antes de gerar) e `recomendacao` (o que fazer). O cenário 4
dispara os dois.

### 3.3 O que o professor vê (`aula-ia/public/geracao-ui.js` + `.css`, copiados para `dist/`)
- **Antes de gerar:** o(s) aviso(s) no resumo da confirmação (como antes; agora pode haver dois).
- **Depois de gerar:** um quadro **"Recomendação ao professor"** acima do parecer da IA Juiz, com aviso + recomendação.
  Não aparece na impressão/PDF (é sobre o pedido, não conteúdo do plano).
- Nada bloqueia: os botões "Aprovar plano" e "Gerar novamente" continuam iguais.
- Verificado na interface em modo demonstração (sem API), com o contexto do cenário 4.

---

## 4. Arquivos alterados

| Arquivo | O que mudou |
|---|---|
| `aula-ia-backend/acentuacao.py` | `VERSAO = "deteccao-acentuacao-1.1"`, `PALAVRA_INEQUIVOCA`, regra por tamanho em `campos_sem_acentuacao` |
| `aula-ia-backend/geracao.py` | Registro da reescrita leva `regra` (versão da detecção) |
| `aula-ia-backend/servico.py` | `alertas_recursos`: regra da aula teórica e campo `recomendacao` |
| `aula-ia/public/geracao-ui.js`, `geracao-ui.css` (+ `dist/`) | `recomendacoesHtml` no painel do plano entregue; estilo; oculto na impressão |
| `aula-ia-backend/tests/test_poc11.py` (**novo**) | 7 testes |
| `aula-ia-backend/tests/test_poc10.py` | Caso "frase curta com 'avaliacao sera'" passou de `[]` para acusado (mudança intencional da 1.1) |
| `aula-ia/tests/test-juiz-render.mjs` | Recomendação: renderização, escape, filtro, presença no painel, CSS de impressão, `public` = `dist` |

## 5. Testes e mutação
- Python: **539** testes (538 passam, 1 ignorado), também com `python -S` (eram 532; +7 de `test_poc11.py`).
- Interface: 3 scripts OK.
- Mutação manual sem bytecode: **17 mutantes** (12 no backend, 5 no front, alterando `public/` e `dist/` juntos), **0 sobreviventes**.
  Uma primeira rodada do backend deu "erro de carga" (caminho de importação do script de mutação, não do código) e foi descartada.

---

## 6. Adaptações na escrita (lista detalhada)

> **Aplicada (26/11).** Esta lista foi aplicada na especificação v2.4 (`docs/especificacao/AulaIA_Especificacao_v2.4.md`),
> junto com o ajuste de 26/11 (`deteccao-acentuacao-1.2`, "sem parecer favorável", selo removido). A v2.3 citada abaixo é histórico.

### 6.1 `docs/especificacao/AulaIA_Especificacao_v2.3.md`
| Onde | Hoje | Sugestão |
|---|---|---|
| §5, tabela, "Verificação de acentuação" (l. 78) | "Detecta campo longo escrito sem acentos e pede uma reescrita…" | "Detecta campo escrito sem acentos (longo: qualquer palavra-guia; curto, como títulos: palavra que nunca se escreve sem acento) e pede uma reescrita…" |
| §6, passo 2 (l. 97) | "Saída de especialista com texto sem acentuação recebe…" | Sem mudança obrigatória; opcional: "(inclusive títulos curtos)" |
| §8, RF08 (l. 145) | "Alertar, sem bloquear, quando a habilidade exige computador e ele não está nos recursos" | "Alertar, sem bloquear, quando a habilidade exige programação e não há computador nos recursos ou a aula é teórica, e repetir a recomendação ao professor junto do plano entregue"; testes: `test_acertos_finais.py`, `test_poc11.py`, `test-juiz-render.mjs` |
| §8, RF09 (l. 146) | testes: `… test_poc10.py` | acrescentar `test_poc11.py` |
| §8, RF13/RF16 | — | Sem mudança (opcional: o painel mostra a recomendação antes do parecer) |
| §9, RNF03 | "rastreio registra as reescritas…" | acrescentar "com a versão da regra de detecção" |
| §9, RNF09 Transparência | — | opcional: "conflito entre habilidade e contexto informado é mostrado ao professor como recomendação" |
| §10, RN05 (l. 184) | "…habilidade que exige computador sem computador nos recursos gera alerta" | "…habilidade que exige programação sem computador nos recursos, ou em aula teórica, gera alerta e recomendação ao professor; nenhum dos dois bloqueia a geração" |
| §12, Limitações (l. 211) | "a verificação de acentuação é heurística (palavras-guia)…" | Manter, acrescentando: "em campos curtos só palavras inequívocas contam, então um título curto sem elas pode escapar". Opcional: "o alerta habilidade × contexto cobre só EF08CO01 e EF08CO02" |
| §13, Histórico | — | Nova linha: "v2.4 \| 25/11/2026 \| Acento em campos curtos (`deteccao-acentuacao-1.1`); alerta de aula teórica e recomendação ao professor junto do plano (PoC 11)" |

### 6.2 `docs/especificacao/Correspondencia_IDs_v2.1R2_v2.3.md`
Sem mudança de IDs. Se a tabela comentar RF08/RN05, acrescentar "aula teórica + recomendação após a geração (PoC 11)".

### 6.3 Diagramas
- `atividades.mmd` (opcional): depois de "Entregar plano…", nota "Mostrar recomendação se habilidade × recursos/tipo em conflito".
- `componentes.mmd` (opcional): a caixa "Verificação de acentuação" já existe; nada novo de componente (a recomendação é do Serviço + Interface).
- `estados`, `er`, `casos-de-uso`, `sequencia`, `visao-geral`, `estrutura-plano`: **sem mudança**.

### 6.4 Texto do TCC (capítulos)
- **Incrementos:** PoC 11 como ciclo curto "lote real → problemas → correção": dois problemas do lote de 25/11 corrigidos sem IA nova
  (regra determinística de acento; recomendação determinística).
- **Desenvolvimento / interface:** o professor recebe, junto do plano, a recomendação quando a habilidade pede programação e o contexto não
  permite (sem computador ou aula teórica). Reforça a tese de que o sistema **orienta** e o professor **decide**.
- **Discussão:** conflitos de entrada não se resolvem regenerando (a sondagem PoC 09 e o lote de 25/11 mostram isso); a resposta certa é
  avisar o professor.
- **Prints:** o quadro "Recomendação ao professor" é novo; prints do cenário 4 do lote (`pedido_f388bdd8`) **não** o mostram.

### 6.5 Outros documentos do repositório
`docs/Estado_Final_Sistema.md`, `CLAUDE.md` e `docs/diario_de_bordo.md` atualizados neste commit.
