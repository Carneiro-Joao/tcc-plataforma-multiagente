/* Ponte visual para o React já compilado da PoC 02.
   O código-fonte em src/App.jsx contém a versão nativa desta interface.
   Não altera nem substitui componentes controlados pelo React. */
(() => {
  "use strict";
  const root = document.getElementById("root");
  if (!root) return;
  const icon = (name) => {
    const shapes = {
      layers: '<path d="m12 2 9 5-9 5-9-5 9-5Z"/><path d="m3 12 9 5 9-5M3 17l9 5 9-5"/>',
      home: '<path d="m3 10 9-7 9 7v10a1 1 0 0 1-1 1h-5v-7H9v7H4a1 1 0 0 1-1-1V10Z"/>',
      book: '<path d="M12 6c-3-2-6-2-9-1v14c3-1 6-1 9 1 3-2 6-2 9-1V5c-3-1-6-1-9 1Zm0 0v14"/>',
      document: '<path d="M7 3h7l5 5v13H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2Z"/><path d="M14 3v5h5M9 12h6M9 16h6"/>',
      clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>'
    };
    return `<svg width="21" height="21" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.85" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${shapes[name]}</svg>`;
  };
  let inicializado = false;
  let ultimaConfirmacao = null;
  let linkPlano;

  function atualizarEstado() {
    if (!inicializado) return;
    root.querySelector("main")?.setAttribute("id", "planejamento");
    root.querySelector(".curricular")?.setAttribute("id", "curriculo");
    const confirmado = Boolean(root.querySelector(".confirmacao"));
    if (confirmado === ultimaConfirmacao) return;
    ultimaConfirmacao = confirmado;
    if (linkPlano) {
      linkPlano.classList.toggle("indisponivel", !confirmado);
      if (confirmado) {
        linkPlano.setAttribute("href", "#geracao-painel");
        linkPlano.removeAttribute("aria-disabled");
        linkPlano.removeAttribute("title");
      } else {
        linkPlano.removeAttribute("href");
        linkPlano.setAttribute("aria-disabled", "true");
        linkPlano.setAttribute("title", "Disponível após confirmar uma habilidade");
      }
    }
    if (!confirmado) document.body.classList.remove("aulaia-plano-aprovado");
  }

  function montar() {
    // Se o frontend nativo (novo JSX) estiver compilado, ele já possui sidebar.
    if (inicializado || !root.querySelector(".app > .barra") || root.querySelector(".lateral")) return;
    inicializado = true;
    document.body.classList.add("aulaia-visual-compat");
    const sidebar = document.createElement("aside");
    sidebar.className = "lateral";
    sidebar.setAttribute("aria-label", "Menu lateral");
    sidebar.innerHTML = `<div class="marca"><span class="marca-icone">${icon("layers")}</span><div class="marca-texto"><b>AulaIA</b><span>Planejamento inteligente</span></div></div>
      <nav class="menu" aria-label="Navegação principal">
        <a class="menu-item selecionado" href="#planejamento" aria-current="page">${icon("home")}Planejar aula</a>
        <a class="menu-item" href="#curriculo">${icon("book")}Base curricular</a>
        <a class="menu-item indisponivel" id="menu-plano" aria-disabled="true" title="Disponível após confirmar uma habilidade">${icon("document")}Plano atual</a>
        <span class="menu-item indisponivel" aria-disabled="true" title="Funcionalidade prevista para um próximo incremento">${icon("clock")}Histórico <small>Em breve</small></span>
      </nav><div class="lateral-rodape"><span class="rodape-ponto"></span>Prova de conceito <small>BNCC de Computação · 8º ano</small></div>`;
    document.body.insertBefore(sidebar, root);
    linkPlano = sidebar.querySelector("#menu-plano");
    const topo = document.createElement("header");
    topo.className = "topo";
    topo.innerHTML = `<div class="trilha">${icon("home")}<span aria-hidden="true">›</span><span>Planejamento</span><span aria-hidden="true">›</span><strong>Computação</strong></div><span class="topo-etiqueta">Versão de demonstração</span>`;
    document.body.insertBefore(topo, root);
    atualizarEstado();
  }

  window.addEventListener("aulaia:geracao-atualizada", evento => {
    if (evento.detail?.consultaId === sessionStorage.getItem("aulaia.consulta.v1")) {
      document.body.classList.toggle("aulaia-plano-aprovado", evento.detail.estado === "aprovado");
    }
  });
  const observador = new MutationObserver(() => { montar(); atualizarEstado(); });
  observador.observe(root, { childList: true, subtree: true });
  montar();
})();
