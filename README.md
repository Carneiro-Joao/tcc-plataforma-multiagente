# AulaIA

Plataforma web local que gera **planos de aula de Computação do 8º ano**, alinhados à BNCC, com agentes de IA. TCC de João Victor
(Computação).

O professor informa o contexto da aula e confirma uma habilidade da BNCC. Cinco agentes especialistas (Gemini) escrevem o plano em
seis chamadas encadeadas, e um integrador e um validador determinísticos conferem a estrutura. Depois, uma **IA Juiz** (Groq) avalia
o plano por uma rubrica de seis critérios. Se o parecer não for favorável, o plano é gerado de novo uma vez, **informado pelas
críticas do Juiz**. A decisão final é sempre do professor: ele aprova e baixa o PDF, ou gera novamente.

> **Congelado em 26/11/2026** (tag `tcc-congelado-26-11`): código do commit `c1ef4f8`, o mesmo da execução do caso-base de 26/11
> (pedido `3bf9f2c6`). Especificação v2.4.

| Para saber | Leia |
|---|---|
| Requisitos, regras de negócio e casos de uso | [`docs/especificacao/AulaIA_Especificacao_v2.4.md`](docs/especificacao/AulaIA_Especificacao_v2.4.md) |
| Números, versões, limites e como rodar em detalhe | [`docs/Estado_Final_Sistema.md`](docs/Estado_Final_Sistema.md) |
| Diagramas e figuras | [`docs/diagramas/diagramas-finais.md`](docs/diagramas/diagramas-finais.md) |
| Formato do plano (11 seções) | [`docs/Contrato_PlanoDeAula_2_0.md`](docs/Contrato_PlanoDeAula_2_0.md) |
| IA Juiz: rubrica, contrato e integração | [`docs/Rubrica_e_Contrato_IA_Juiz.md`](docs/Rubrica_e_Contrato_IA_Juiz.md), [`docs/PoC08_Juiz_Integrado.md`](docs/PoC08_Juiz_Integrado.md) |
| Regeneração informada e acentuação | [`docs/PoC10_Regeneracao_Informada_e_Acentuacao.md`](docs/PoC10_Regeneracao_Informada_e_Acentuacao.md) |
| Última revisão da documentação × sistema | [`docs/Revisao_Geral_25-11_noite.md`](docs/Revisao_Geral_25-11_noite.md) |
| Registro do trabalho dia a dia | [`docs/diario_de_bordo.md`](docs/diario_de_bordo.md) |

## Estrutura

| Pasta | Conteúdo |
|---|---|
| `aula-ia-backend/` | Servidor, serviço, agentes, Juiz, validador e testes. Python 3.12+ **só com a biblioteca padrão**; banco SQLite |
| `aula-ia-backend/contratos/` | Contratos versionados: PlanoDeAula 2.0, ParecerJuiz 1.0, rubrica e política do Juiz |
| `aula-ia-backend/legado/` | Scripts das sondagens OpenAI/OpenRouter da PoC 03, fora do fluxo |
| `aula-ia-backend/local/` | Bancos, relatórios e resultados brutos (**ignorado pelo Git**) |
| `aula-ia/` | Interface em React + Vite. A versão compilada (`dist/`) está versionada: não precisa de Node para usar |
| `experimentos/` | Casos congelados, variantes, protocolos pré-registrados e dados brutos dos ensaios |
| `docs/` | Especificação, diagramas, registros das PoCs; `docs/historico/` guarda documentos substituídos |

## Chaves de API

O sistema usa duas chaves, lidas **só de variáveis de ambiente** (nunca de arquivo; nunca as envie em mensagens, prints ou commits):

| Variável | Para quê | Onde criar |
|---|---|---|
| `GEMINI_API_KEY` | Geração (`gemini-3.5-flash-lite`) | [Google AI Studio](https://aistudio.google.com/apikey) |
| `GROQ_API_KEY` | IA Juiz (`openai/gpt-oss-120b`) | [GroqCloud](https://console.groq.com/keys) |

```bat
:: CMD, só para este terminal
set "GEMINI_API_KEY=SUA_CHAVE"
set "GROQ_API_KEY=SUA_CHAVE"
```

```powershell
# PowerShell, só para este terminal
$env:GEMINI_API_KEY = "SUA_CHAVE"
$env:GROQ_API_KEY = "SUA_CHAVE"
```

Os dois serviços foram usados na faixa gratuita. As cotas variam por conta e podem mudar; o sistema não troca de modelo nem de
provedor sozinho. Na faixa gratuita do Gemini o conteúdo pode ser usado pelo Google: use contextos fictícios, sem dados de alunos.

## Como rodar

Na pasta `aula-ia-backend` (no Windows, `python` ou `py`):

```bat
:: demonstração sem chave e sem rede (gerador por regras e parecer gravado)
python app.py --modo lexical --gerador demonstracao --juiz demonstracao

:: uso real: Gemini na geração; IA Juiz automática se GROQ_API_KEY estiver definida
python app.py --modo lexical --gerador ia --ipv4 --abrir

:: sem GEMINI_API_KEY no ambiente: pede a chave com entrada oculta e a mantém só na memória
python app.py --modo lexical --gerador ia --ipv4 --pedir-chave --abrir
```

Abra **http://127.0.0.1:8000**. No Windows também dá para dar duplo clique em `INICIAR_AULAIA.cmd`, que pede a chave do Gemini numa
janela e inicia o app por IPv4. A IA Juiz entra se `GROQ_API_KEY` já estiver no ambiente.

| Opção | Padrão | Efeito |
|---|---|---|
| `--gerador demonstracao\|ia` | `demonstracao` | `ia` usa o Gemini |
| `--juiz groq\|demonstracao\|desligado` | `groq` se houver `GROQ_API_KEY`, senão `desligado` | `demonstracao` usa um parecer real **gravado de outro plano**, sem rede; por isso a regeneração fica cega |
| `--ciclos-juiz N` | 1 | Regenerações automáticas quando o parecer não é favorável (0 = não regenera) |
| `--regeneracao informada\|cega` | `informada` | `informada`: cada especialista recebe a sua versão anterior e as críticas do Juiz; `cega`: gera de novo sem elas |
| `--limite-diario N` | 8 | Gerações com IA por dia, contando falhas |
| `--limite-diario-juiz N` | 8 | Avaliações reais do Juiz por dia, contando falhas |
| `--reparos 0\|1` | 1 | Reparo de formato por chamada de especialista |
| `--repeticoes-503 0..2` | 2 | Novas tentativas por chamada em HTTP 503 |
| `--banco caminho` / `--temporario` | `local/consultas.sqlite3` | Outro banco, ou banco descartável |
| `--modo lexical\|hibrido` | `lexical` | `hibrido` exige `requirements-hibrido.txt` e modelo de embeddings |

Por versão do plano são 6 chamadas normais e até 18 com reparos e reescritas de acentuação; com as repetições em 503, até 54
requisições. A IA Juiz espera 75 s entre avaliações (120 s depois de HTTP 413) por causa da cota do Groq. Falha técnica do Juiz
entrega o plano com "avaliação indisponível" e nunca conta como parecer. Mais detalhes em `docs/Estado_Final_Sistema.md`.

## Fluxo da geração

| Etapa | Quem | Saída aceita |
|---|---|---|
| Objetivos | Gemini | Conteúdos, objetivo geral e 2–4 objetivos específicos (OBJ) |
| Avaliação preliminar | Gemini | Critérios e evidências esperadas por objetivo (EVI) |
| Metodologia | Gemini | Texto da metodologia; recursos iguais aos confirmados |
| Sequência | Gemini | Etapas (ET) com minutos, ações docente e discente, vínculos a OBJ e EVI |
| Avaliação final | Gemini | Instrumentos (INS), procedimentos, vínculos e uso dos resultados |
| Adaptação | Gemini | Duas adaptações (ADP) ligadas a objetivos e etapas |
| Integração e validação | Python | As 11 seções; habilidade, duração e recursos copiados da entrada; soma dos minutos = duração |
| IA Juiz | Groq | Parecer com notas de 0 a 3 em 6 critérios e falhas; a política (Python) decide o próximo estado |

Cada saída é validada antes da etapa seguinte. Saída escrita sem acentuação recebe uma reescrita, aceita só se continuar válida,
mantiver IDs, números e vínculos e melhorar. O plano é sempre um rascunho até o professor aprovar.

## Testes

```bat
cd aula-ia-backend
python relatorio_testes.py            :: roda tudo e abre um relatório HTML (--sem-abrir, --filtro juiz)
python -m unittest discover -s tests  :: só os testes, no terminal
python -S -m unittest discover -s tests
cd ..
node aula-ia/tests/test-plano-render.mjs
node aula-ia/tests/test-formulario.mjs
node aula-ia/tests/test-juiz-render.mjs
```

No código congelado (26/11/2026): 545 testes Python (544 passam, 1 ignorado: busca híbrida opcional, só com `TESTAR_HIBRIDO=1`), também com `python -S`, e os 3 roteiros da interface. Os testes não usam
rede. Mudou o front? `cd aula-ia && npm run build` e versione `dist/`.

## Ferramentas de pesquisa

Fora do fluxo do site, na pasta `aula-ia-backend`. Nenhuma faz chamada real sem a chave; `--somente-validar` testa sem rede.

| Script | Para quê |
|---|---|
| `ensaio_juiz.py`, `variantes_juiz.py`, `casos_juiz.py`, `analisar_serie.py` | Ensaios pré-registrados do Juiz (V01–V06) sobre casos congelados |
| `adjudicacao.py`, `adjudicacao_web.py`, `concordancia.py` | Adjudicação humana dos pareceres e concordância entre avaliadores |
| `gerar_lote.py`, `medir_planos.py` | Lote e medição pré-registrados da geração (PoC 07B) |
| `sondagem_regeneracao_informada.py` | Sondagem cega × informada da PoC 09 (exploratória, n = 5) |
| `exportar_planos.py` | Exporta os planos reais do SQLite para `local/planos_ia/` |
| `teste_gemini.py`, `inspecionar_gemini.py` | Sondagem do Gemini pelo terminal (sem repetição em 503) e inspeção de registros |

## Histórico

O README anterior, com o registro dos incrementos de 13 a 17/11 (primeira execução real com Gemini, simplificação do esquema para a
API, adaptador Groq), está em [`docs/historico/README_ate_2026-11-25.md`](docs/historico/README_ate_2026-11-25.md). Cada PoC tem o seu
registro em `docs/PoC*.md`.

## Referências oficiais consultadas

- [Modelo Gemini 3.5 Flash-Lite](https://ai.google.dev/gemini-api/docs/models/gemini-3.5-flash-lite)
- [Preços e Free Tier do Gemini](https://ai.google.dev/gemini-api/docs/pricing)
- [Limites por projeto](https://ai.google.dev/gemini-api/docs/rate-limits)
- [Estratégia de nova tentativa em falhas transitórias](https://ai.google.dev/gemini-api/docs/troubleshooting#retry-strategy)
- [Simplificação de esquemas na saída estruturada](https://ai.google.dev/gemini-api/docs/structured-output#simplifying-complex-schemas)
