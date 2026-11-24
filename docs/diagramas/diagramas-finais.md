# AulaIA — Diagramas finais (conforme implementado)

**Data:** 23/11/2026 · **Situação:** versão final, aprovada pelo João; refletem o sistema congelado na `main` (`694c07c`).
Especificação correspondente: [`../especificacao/AulaIA_Especificacao_v2.2_final.md`](../especificacao/AulaIA_Especificacao_v2.2_final.md).
Substituem os diagramas v2.1-R2 (D1–D6, branch `docs/diagramas-rascunho`, commit `33e8025`), que descreviam a arquitetura-**alvo**.

**Arquivos:** fontes e imagens em [`final/`](final/) (`.mmd` Mermaid, `.puml` PlantUML, `.png` para o texto, `.svg` para ampliar).
Para regenerar: `mmdc -i final/<nome>.mmd -o final/<nome>.png -s 2 -b white` (Mermaid CLI) e
`java -jar plantuml.jar -tpng final/casos-de-uso.puml` (PlantUML + Graphviz).

| Diagrama | Onde entra no TCC | Arquivo |
|---|---|---|
| Sequência | 4.2 Navegação (o único de sequência) | `final/sequencia.png` |
| Componentes | 4.3 Modelagem (principal: estrutura dos agentes) | `final/componentes.png` |
| Casos de uso (UML) | 4.3 Modelagem | `final/casos-de-uso.png` |
| Entidade-relacionamento | 4.3 Modelagem | `final/er.png` |
| Atividades | Opcional (4.2 ou 4.3) | `final/atividades.png` |
| Estados do pedido | Opcional (4.3) | `final/estados.png` |

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
    participant API as Servidor
    participant BUS as Tema e busca BNCC
    participant ORQ as Orquestrador
    participant ESP as Especialistas (Gemini)
    participant VAL as Integrador e validador
    participant J as IA Juiz (Groq)
    participant DB as SQLite
    P->>UI: Informar contexto da aula
    UI->>API: POST /api/consultas
    API->>BUS: Extrair tema curto e buscar habilidades
    BUS-->>API: Habilidades candidatas e fonte
    API->>DB: Registrar consulta
    API-->>UI: Tema identificado e candidatas
    P->>UI: Confirmar habilidade
    UI->>API: POST /api/consultas/{id}/confirmar
    API->>DB: Gravar confirmação
    P->>UI: Gerar plano de aula
    UI->>API: POST /api/consultas/{id}/gerar
    API->>ORQ: Criar pedido
    loop 6 chamadas encadeadas
        ORQ->>ESP: Próxima etapa com as saídas anteriores
        ESP-->>ORQ: Saída JSON validada
    end
    ORQ->>VAL: Integrar 11 seções e validar contrato
    VAL-->>ORQ: Plano válido (rascunho)
    ORQ->>J: Avaliar plano (rubrica de 6 critérios)
    J-->>ORQ: Parecer e decisão da política
    opt Parecer não favorável (até 1 vez)
        ORQ->>ESP: Gerar o plano inteiro de novo
        ORQ->>J: Avaliar a nova versão
    end
    ORQ->>DB: Gravar versões, pareceres e versão entregue
    API-->>UI: Plano e parecer
    P->>UI: Aprovar plano
    UI->>API: POST /api/geracoes/{id}/aprovar
    API->>DB: Estado "aprovado"
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
    CI -->|"Sim"| RG["Gerar o plano inteiro de novo"]
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

## Manutenção

Mudou contrato, dependência, estado ou responsabilidade no código? Atualizar a fonte em `final/`, regenerar a imagem e citar o commit.
