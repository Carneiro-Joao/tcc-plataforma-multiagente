# AulaIA — Diagramas finais (conforme implementado)

**Data:** 23/11/2026 · **Situação:** versão final, aprovada pelo João; refletem o sistema congelado na `main` (`694c07c`).
Especificação correspondente: [`../especificacao/AulaIA_Especificacao_v2.2_final.md`](../especificacao/AulaIA_Especificacao_v2.2_final.md).
Substituem os diagramas v2.1-R2 (D1–D6, branch `docs/diagramas-rascunho`, commit `33e8025`), que descreviam a arquitetura-**alvo**.

**Arquivos:** fontes e imagens em [`final/`](final/) (`.mmd` Mermaid, `.puml` PlantUML, `.png` para o texto, `.svg` para ampliar).
Para regenerar: `mmdc -i final/<nome>.mmd -o final/<nome>.png -s 2 -b white` (Mermaid CLI) e
`java -jar plantuml.jar -tpng final/casos-de-uso.puml` (PlantUML + Graphviz). As figuras 1 e 6 têm fonte em HTML
(`final/visao-geral.html`, `final/estrutura-plano.html`): abrir no Chromium a 1800 px e capturar o elemento `.fig` com escala 2 (Playwright).

**Seleção para o texto (decisão de 23/11):** seis figuras, cada uma respondendo a uma pergunta do leitor, na ordem de leitura do Cap. 4.

| Ordem | Figura | Pergunta que responde | Onde entra no TCC | Arquivo |
|---|---|---|---|---|
| 1 | Visão geral (ilustrativa, sem UML) | O que é e por que importa? | Abertura do Cap. 4 | `final/visao-geral.png` |
| 2 | Casos de uso (UML) | O que o professor pode fazer? | 4.3 (ou abrindo a 4.2) | `final/casos-de-uso.png` |
| 3 | Sequência + prints das telas | Como é usar, passo a passo? | 4.2 (o único de sequência) | `final/sequencia.png` |
| 4 | Componentes + um parágrafo por agente | Do que o sistema é feito? | 4.3 (principal) | `final/componentes.png` |
| 5 | Atividades de "Gerar plano" | O que acontece quando algo não sai bem? | 4.3 | `final/atividades.png` |
| 6 | Estrutura do plano | O que exatamente o sistema entrega? | 4.3 | `final/estrutura-plano.png` |
| — | Entidade-relacionamento | Como os dados são guardados? | Apêndice (opcional) | `final/er.png` |
| — | Estados do pedido | Quais estados um pedido percorre? | Apêndice (opcional) | `final/estados.png` |
| — | Classes | — | Não usar: o plano é um documento JSON validado por contrato, não um modelo de objetos | — |

## 1. Componentes

![Componentes](final/componentes.png)

```mermaid
flowchart TB
    P(["Professor"]) --> UI["Interface web<br/>(React + Vite)"]
    UI -->|"HTTP/JSON"| API["Servidor HTTP<br/>app.py"]
    API --> SV["Serviço de aplicação<br/>servico.py"]
    SV --> TEMA["Extração de tema<br/>tema.py (regras)"]
    SV --> RAG["Busca curricular<br/>rag/search.py"]
    RAG --> CAT[("Catálogo BNCC 8º ano<br/>+ PDF oficial")]
    SV --> ORQ["Orquestrador da geração<br/>geracao_v2.py"]
    subgraph ESP["Agentes especialistas (LLM) — 6 chamadas encadeadas"]
        direction LR
        A1["Objetivos"] --> A2["Avaliação<br/>(preliminar)"] --> A3["Metodologia<br/>e Recursos"] --> A4["Sequência<br/>Didática"] --> A5["Avaliação<br/>(final)"] --> A6["Adaptação"]
    end
    ORQ --> ESP
    ESP -.-> GEM["Adaptador Gemini<br/>gemini.py"]
    GEM -.-> GAPI(("API Gemini<br/>gemini-3.5-flash-lite"))
    ORQ --> INT["Integrador<br/>(Python, sem LLM)"]
    INT --> VAL["Validador<br/>contrato plano-aula-2.0"]
    SV --> JUIZ["IA Juiz<br/>juiz_servico.py / juiz.py"]
    JUIZ -.-> GROQ["Adaptador Groq<br/>groq_juiz.py"]
    GROQ -.-> GRAPI(("API Groq<br/>gpt-oss-120b"))
    JUIZ --> POL["Política de decisão<br/>(determinística)"]
    SV <--> DB[("SQLite<br/>consultas · pedidos<br/>geracoes · pareceres")]
```

Linhas tracejadas: chamadas a serviços externos, sempre por um adaptador. Integrador, validador, extração de tema e política são
determinísticos (sem LLM). Os seis blocos dos especialistas são **cinco agentes em seis chamadas** (a Avaliação tem duas passagens).

## 2. Casos de uso

![Casos de uso](final/casos-de-uso.png)

Fonte PlantUML: [`final/casos-de-uso.puml`](final/casos-de-uso.puml). `<<include>>`: partes obrigatórias de UC01. `<<extend>>`:
comportamentos opcionais (catálogo, documento-fonte, gerar novamente). Inspecionar especialistas é depuração, não caso de uso.

## 3. Sequência

![Sequência](final/sequencia.png)

```mermaid
sequenceDiagram
    actor P as Professor
    participant UI as Interface
    participant SV as Servidor e serviço
    participant BUS as Tema e busca BNCC
    participant ORQ as Orquestrador da geração
    participant ESP as Especialistas (Gemini)
    participant J as IA Juiz (Groq)
    participant DB as SQLite
    P->>UI: Informar contexto da aula
    UI->>SV: POST /api/consultas
    SV->>BUS: Extrair tema curto e buscar habilidades
    BUS-->>SV: Habilidades candidatas e fonte
    SV->>DB: Registrar consulta
    SV-->>UI: Tema identificado e candidatas
    P->>UI: Confirmar habilidade
    UI->>SV: POST /api/consultas/{id}/confirmar
    SV->>DB: Gravar confirmação
    P->>UI: Gerar plano de aula
    UI->>SV: POST /api/consultas/{id}/gerar
    SV->>DB: Criar pedido
    SV->>ORQ: Gerar plano
    loop 6 chamadas encadeadas
        ORQ->>ESP: Próxima etapa com as saídas anteriores
        ESP-->>ORQ: Saída JSON validada
    end
    ORQ->>ORQ: Integrar 11 seções e validar contrato
    ORQ-->>SV: Plano válido (rascunho)
    SV->>J: Avaliar plano (rubrica de 6 critérios)
    J-->>SV: Parecer e decisão da política
    opt Parecer não favorável (até 1 vez)
        SV->>ORQ: Gerar de novo com a versão anterior e as críticas do Juiz
        ORQ-->>SV: Nova versão
        SV->>J: Avaliar a nova versão
        J-->>SV: Novo parecer
    end
    SV->>DB: Gravar versões, pareceres e versão entregue
    SV-->>UI: Plano e parecer
    P->>UI: Aprovar plano
    UI->>SV: POST /api/geracoes/{id}/aprovar
    SV->>DB: Estado "aprovado"
    P->>UI: Baixar PDF
```

## 4. Atividades

![Atividades](final/atividades.png)

```mermaid
flowchart TD
    I(["Início"]) --> C["Informar contexto da aula"]
    C --> V{"Contexto válido?"}
    V -->|"Não"| C
    V -->|"Sim"| T["Extrair tema e buscar habilidades"]
    T --> H["Escolher habilidade<br/>(candidatas ou catálogo)"]
    H --> CF["Confirmar habilidade"]
    CF --> G["Especialistas geram o plano<br/>(6 chamadas, validação a cada etapa)"]
    G --> OK{"Geração concluída?"}
    OK -->|"Não"| FG["Registrar falha e avisar"]
    OK -->|"Sim"| J["IA Juiz avalia"]
    J --> FJ{"Avaliação concluída?"}
    FJ -->|"Não"| SP["Entregar sem parecer<br/>(avaliação indisponível)"]
    FJ -->|"Sim"| FAV{"Parecer favorável?"}
    FAV -->|"Sim"| EN["Entregar plano com parecer"]
    FAV -->|"Não"| CI{"Ainda há ciclo<br/>de regeneração?"}
    CI -->|"Sim"| RG["Gerar de novo o plano<br/>com as críticas do Juiz"]
    RG --> RV{"Nova versão válida?"}
    RV -->|"Sim"| J
    RV -->|"Não"| MV
    CI -->|"Não"| MV["Entregar a versão com menos<br/>falhas graves, com aviso"]
    EN --> D{"Professor aprova?"}
    SP --> D
    MV --> D
    D -->|"Sim"| AP["Registrar aprovação e baixar PDF"]
    D -->|"Não"| NV["Gerar novamente"]
    NV --> G
    FG --> F(["Fim"])
    AP --> F
```

## 5. Estados do pedido

![Estados](final/estados.png)

```mermaid
stateDiagram-v2
    direction LR
    state "Em andamento" as andamento {
        [*] --> gerando
        gerando --> avaliando: plano válido
        avaliando --> aguardando_juiz: espera a cota do Groq
        aguardando_juiz --> avaliando
        avaliando --> regenerando: não favorável e há ciclo
        regenerando --> avaliando: nova versão válida
    }
    [*] --> andamento: professor pede o plano
    andamento --> pronto: plano entregue (com parecer, sem parecer ou melhor versão)
    andamento --> falha: a primeira geração falhou
    andamento --> interrompido: parado mais de 15 min
    pronto --> [*]
    falha --> [*]
    interrompido --> [*]
```

Estados da **geração** (versão do plano): `processando` → `rascunho` → `aprovado`, ou `falha`. "Interrompido" não é gravado: é como o
sistema mostra um pedido em andamento parado há mais de 15 minutos.

## 6. Entidade-relacionamento (tabelas reais do SQLite)

![ER](final/er.png)

```mermaid
erDiagram
    CONSULTAS ||--o{ PEDIDOS : origina
    CONSULTAS ||--o{ GERACOES : possui
    PEDIDOS ||--o{ GERACOES : "agrupa por ciclo"
    GERACOES ||--o{ PARECERES : recebe
    CONSULTAS {
        text id PK
        text dados "contexto, tema e candidatas (JSON)"
        text codigo_confirmado
    }
    PEDIDOS {
        text id PK
        text consulta_id FK
        text estado
        int ciclo
        text geracao_entregue
        text aviso
        text historico "JSON"
        text criado_em
        text atualizado_em
    }
    GERACOES {
        text id PK
        text consulta_id FK
        int revisao
        text estado "processando, rascunho, aprovado, falha"
        text resultado "plano e rastreio (JSON)"
        text criado_em
        text pedido_id FK
        int ciclo
        int entregue
    }
    PARECERES {
        text id PK
        text geracao_id FK
        int ciclo
        text criado_em
        text estado "ok ou falha"
        text proximo_estado
        text versao_prompt
        text modelo
        text versao_rubrica
        text politica
        text resultado "parecer (JSON)"
    }
```

O plano e o rastreio ficam em JSON em `geracoes.resultado`; o parecer, em `pareceres.resultado`. A versão entregue de cada pedido tem
`geracoes.entregue = 1` (e `pedidos.geracao_entregue`).

## 7. Visão geral (figura ilustrativa)

![Visão geral](final/visao-geral.png)

Para leitores sem formação técnica: cinco passos, com a separação entre pessoa, regras fixas e IA. Fonte: [`final/visao-geral.html`](final/visao-geral.html).

## 8. Estrutura do plano de aula

![Estrutura do plano](final/estrutura-plano.png)

As 11 seções do PlanoDeAula 2.0, quem preenche cada uma e a corrente objetivo → etapa → evidência → instrumento, com trechos
**literais** do plano aprovado na execução de 23/11/2026 pela interface (Gemini + Groq; Ordenação, aula prática, 50 min, projetor e
computadores; revisão 1, parecer "Com ressalvas"), a mesma usada nas telas do Cap. 4 do TCC. O texto da etapa ET1 é resumido; os demais
estão entre aspas. Fonte: [`final/estrutura-plano.html`](final/estrutura-plano.html).

## Manutenção

Mudou contrato, dependência, estado ou responsabilidade no código? Atualizar a fonte em `final/`, regenerar a imagem e citar o commit.
