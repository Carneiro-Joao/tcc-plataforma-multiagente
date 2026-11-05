# Incremento 03 — Identidade visual e orientação do fluxo

**Data:** 05/11/2026. **Escopo:** refinamento da interface, sem alterar os contratos HTTP nem a lógica curricular, geração e aprovação do incremento anterior.

## Objetivo

Reformular a apresentação da PoC 02 respeitando o formulário de contexto à esquerda e o painel de recuperação/confirmação da habilidade à direita. A linguagem visual foi definida em parceria com o autor do TCC, com uma proposta intermediária entre um sistema institucional formal e uma interface gamificada: **azul-marinho, azul-claro, fundo cinza quase branco, tipografia arredondada para títulos e detalhes de progresso discretos**.

## Mudanças realizadas

- Navegação lateral com ações existentes: **Planejar aula**, **Base curricular** e **Plano atual** (este último disponível após a confirmação). O **Histórico** é mostrado como funcionalidade ainda indisponível, sem simular navegação inexistente.
- Três etapas de progresso: **Configurar aula → Escolher habilidade → Gerar e aprovar**. O estado é derivado de consulta, habilidade confirmada e aprovação do professor; a última etapa é concluída apenas quando a aprovação foi registrada.
- Componentes e botões com estilos consistentes; melhor contraste, estados de foco, responsividade para celular e visual adaptado para impressão.
- Tipografia preferencial **Nunito** para títulos e **Inter** para texto; fontes substitutas de sistema disponíveis se a fonte web estiver inacessível.
- Preservação do acesso à fonte da BNCC, métodos de recuperação, contratos JSON e sinalização expressa de geração por regras vs. geração por agentes com LLM.

## Estratégia de distribuição

O ambiente de empacotamento deste incremento não conseguiu instalar os pacotes do Vite (registry.npmjs.org inacessível). Para que o comando `python app.py --modo lexical --gerador demonstracao` continue mostrando a interface atualizada, foi adicionada uma **camada visual de compatibilidade** (`tema-compat.js` e `tema-compat.css`) sobre o React da PoC 02 compilado em `dist/`. Ela cria navegação e aplica a nova identidade sem mover ou substituir os elementos controlados pelo React. O código-fonte React (`src/App.jsx` e `src/App.css`) também foi atualizado com a mesma estrutura de interface, podendo substituir a compatibilidade após um novo build em ambiente com as dependências instaladas.

Para gerar o `dist/` a partir do novo JSX em um ambiente com Node instalado, execute `npm ci && npm run build` dentro de `aula-ia/`. O script de compatibilidade só se ativa quando encontra a barra da interface anterior; se o novo JSX for compilado, a sidebar é nativa e a camada não cria elementos adicionais. Um próximo refinamento poderá remover esses arquivos de compatibilidade depois do build definitivo.

## Evidências

- **15 testes automatizados aprovados e 1 ignorado**, relativo ao encoder do modo híbrido.
- **Sintaxe JSX validada** por transpile TypeScript (`react-jsx`), sem diagnósticos.
- **Chromium** em simulação DOM sobre o bundle compilado: consulta de ordenação, seleção de EF08CO03, confirmação, geração demonstrativa e aprovação; nenhum erro JavaScript. Teste responsivo com viewport de 390 px sem estouro horizontal.
- Screenshots locais em `docs/captura_03_confirmacao.webp`, `docs/captura_03_aprovacao.webp` e `docs/captura_03_mobile.webp`.

**Limitação:** as capturas do teste isolado foram feitas com fontes substitutas do sistema, pois a resolução de fontes web estava bloqueada no navegador de teste. A tipografia Nunito/Inter será carregada no navegador do usuário quando houver acesso à infraestrutura do Google Fonts.

O incremento é uma evolução de **interface e usabilidade**, não uma nova implementação científica do mecanismo RAG ou da IA Juiz.
