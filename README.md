# AulaIA — PoC 02: busca curricular, geração de plano e aprovação docente

Esta entrega **parte da PoC 01** e mantém a seleção de habilidades oficiais da BNCC de Computação do **8º ano**. Após confirmar uma habilidade, o professor pode gerar um **plano candidato**, consultar as saídas das etapas, solicitar uma nova versão ou **aprovar a versão atual**. A confirmação e a aprovação são registradas no SQLite local.

## 1. Abrir no Windows — funciona sem instalar pacotes

1. Extraia **todo** este ZIP em uma pasta nova. Não execute o Python dentro do ZIP.
2. Abra o PowerShell ou Prompt de Comando **na pasta `aula-ia-backend`**.
3. Execute:

```powershell
py app.py --modo lexical --gerador demonstracao
```

Se o comando `py` não funcionar e você tiver `python` configurado, execute:

```powershell
python app.py --modo lexical --gerador demonstracao
```

4. Entre em **http://127.0.0.1:8000**. Não é necessário executar `npm` ou `vite`: a interface compilada está inclusa.

O modo lexical consulta o catálogo, não precisa de bibliotecas extras, modelo na nuvem nem chave de API. O **modo demonstrativo** cria automaticamente planos com um encadeamento de funções por regras; **não usa inteligência artificial generativa**, mesmo que a interface registre os nomes das etapas do futuro pipeline multiagente. Essa distinção é importante para apresentar a PoC de modo academicamente correto.

## 2. Roteiro de demonstração

1. Ano: **8º ano**; tema: **quero ensinar ordenação**; duração: **50 minutos**; tipo: **Computação desplugada**; recursos: **papel e cartões**.
2. Clique em **Consultar habilidades**, selecione **EF08CO03** e clique em **Confirmar habilidade**.
3. Role a página até **Geração do plano de aula** e clique em **Gerar plano de aula**.
4. Confira objetivos, metodologia, sequência didática (com tempos totalizando 50 min), avaliação e propostas de adaptação.
5. Abra **Inspecionar agentes, entradas e saídas** para verificar a rastreabilidade. Clique em **Gerar outra versão** para ver uma alternativa.
6. Clique em **Aprovar este plano** e recarregue a página: o status de aprovado continua registrado. O botão **Imprimir plano** abre a impressão, com opção de **Salvar como PDF** pelo navegador.

**Observação:** a aprovação é do professor, não da futura IA Juiz. O plano demonstrativo é ilustrativo e requer revisão pedagógica antes de uso real.

## 3. Geração com agentes de IA reais (opcional)

A arquitetura implementa seis papéis especializados: **objetivos**, **metodologia e recursos**, **sequência didática**, **avaliação**, **adaptação** e **integração**. No modo `ia`, **cada um faz uma chamada independente** a um modelo de linguagem pela API da OpenAI, respeitando as dependências entre as saídas. Esse modo **não pôde ser testado contra a API externa neste ambiente**; a validação realizada cobre execução demonstrativa, contratos, persistência e HTTP local. Pode haver custo na API da OpenAI, além da assinatura do ChatGPT.

No PowerShell, configure a chave **somente no terminal**, não no frontend e não em arquivos do ZIP:

```powershell
$env:OPENAI_API_KEY="SUA_CHAVE_DA_API"
py app.py --modo lexical --gerador ia --modelo gpt-4o-mini
```

No Prompt de Comando (CMD):

```bat
set OPENAI_API_KEY=SUA_CHAVE_DA_API
py app.py --modo lexical --gerador ia --modelo gpt-4o-mini
```

Não coloque sua chave em prints, commits ou mensagens. Para trocar o modelo, use `--modelo` com um identificador que sua conta da API suporte. Se a API falhar, o backend retorna erro em vez de **fingir** que houve uma resposta gerada por IA. Saídas com duração inconsistente ou código de habilidade alterado são rejeitadas pelos validadores.

## 4. Busca híbrida opcional

Para reproduzir a busca semântica da PoC 01, é necessário preparar o ambiente descrito nos requisitos do projeto:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-hibrido.txt
.\.venv\Scripts\python.exe app.py --modo hibrido --gerador demonstracao
```

O modelo público `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` pode precisar de download na primeira execução. A busca híbrida independe do modo de geração: é possível usar `--modo hibrido --gerador ia` após configurar ambas as dependências.

## 5. Onde editar

| Arquivo | Responsabilidade |
|---|---|
| `aula-ia-backend/app.py` | Rotas HTTP e parâmetros de inicialização |
| `aula-ia-backend/servico.py` | Confirmação, revisões, aprovação e SQLite |
| `aula-ia-backend/geracao.py` | Orquestração de agentes, integração e validações |
| `aula-ia/src/App.jsx` | Interface React original para seleção curricular |
| `aula-ia/public/geracao-ui.js` | Extensão de interface de geração e aprovação após a confirmação |
| `aula-ia/public/geracao-ui.css` | Estilos da extensão e impressão |
| `aula-ia/dist/` | Site pronto para ser servido pelo Python, sem precisar de Node |
| `aula-ia-backend/tests/` | Testes de regressão e do incremento 02 |
| `docs/Capitulo_4_Incremento_01.md` | Registro da busca curricular |
| `docs/Capitulo_4_Incremento_02.md` | Registro da geração de plano e aprovação |

**Observação de arquitetura frontend:** a extensão foi adicionada como JavaScript progressivo, separado do React existente, para disponibilizar **um site imediatamente executável** mesmo sem recompilar a aplicação. No desenvolvimento definitivo, recomenda-se migrar essa extensão para um componente React e executar `npm ci && npm run build`. O build original React está presente no ZIP e a extensão é carregada pelo HTML do desenvolvimento e pelo HTML compilado.

## 6. API local

- `POST /api/consultas` — consulta a BNCC pelo tema ou catálogo.
- `POST /api/consultas/{id}/confirmar` — confirma o código curricular.
- `GET /api/consultas/{id}` — devolve consulta, entrada confirmada e `geracao_atual`.
- `GET /api/consultas/{id}/entrada-geracao` — contrato curricular confirmado.
- `POST /api/consultas/{id}/gerar` — gera uma nova revisão (JSON `{}`).
- `POST /api/geracoes/{id}/aprovar` — registra aprovação humana da última revisão (JSON `{}`).

Rejeita-se a geração sem habilidade confirmada, a aprovação prematura, a aprovação de revisão obsoleta e a regeneração após aprovação. Antes da aprovação, uma nova geração não modifica o registro da habilidade.

## 7. Testes

Dentro de `aula-ia-backend`, rode:

```powershell
py -m unittest discover -s tests -v
```

São **15 testes locais executados com sucesso e 1 teste opcional de ranking híbrido ignorado** sem `TESTAR_HIBRIDO=1`. A versão distribuída foi também verificada por execução local de endpoints HTTP. A interface foi exercitada também com Chromium em um ambiente de teste de página isolada, com ponte HTTP controlada: consulta, confirmação, geração, nova versão e aprovação. O endereço local diretamente no navegador de teste era bloqueado, mas os fluxos foram verificados pela ponte. Repita o roteiro acima no seu computador.

## 8. Próximos incrementos

Integrar e testar o modo de IA com credenciais reais, melhorar contratos por agente, incorporar a **IA Juiz** com política de validação e correção dirigida e manter histórico de execuções. A autenticação, a exportação de PDF gerada no servidor e a avaliação com usuários pertencem a incrementos posteriores. A impressão em PDF pelo navegador é apenas um atalho demonstrativo.

## Incremento 03 — Interface azul e progresso visual

A interface foi atualizada para **azul-marinho, azul-claro e cinza quase branco**, com títulos em Nunito, textos em Inter (com fontes de reserva), menu lateral e indicador de **Configurar aula → Escolher habilidade → Gerar e aprovar**. A estrutura funcional da PoC 02 permanece a mesma.

O comando de execução **não mudou**:

```powershell
cd aula-ia-backend
py app.py --modo lexical --gerador demonstracao
```

A distribuição em `aula-ia/dist/` já inclui `tema-compat.js` e `tema-compat.css`: essa camada aplica a nova interface à versão compilada da PoC 02 sem exigir Node.js no computador do professor. Os arquivos `src/App.jsx` e `src/App.css` também contêm a versão React nativa; para recompilá-la, dentro de `aula-ia/`, execute `npm ci` e `npm run build`. Consulte `docs/Capitulo_4_Incremento_03.md` para detalhes, testes e limites da distribuição.
