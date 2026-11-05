/* Camada progressiva da prova de conceito: geração e aprovação, sem dependências.
 * Montada após a confirmação no frontend React existente. Mantida em public/
 * para funcionar no Vite e na distribuição compilada sem recompilar o React.
 */
(() => {
  "use strict";
  const CHAVE = "aulaia.consulta.v1";
  let idAtual = null;
  let dadosAtuais = null;
  let ocupado = false;
  let erroAtual = "";
  let atualizacaoAgendada = false;

  const escapar = valor => String(valor ?? "").replace(/[&<>"']/g, caractere => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  })[caractere]);
  const texto = valor => escapar(valor);
  const json = valor => escapar(JSON.stringify(valor, null, 2));

  async function api(url, corpo) {
    const resposta = await fetch(url, corpo === undefined ? undefined : {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(corpo)
    });
    if (!resposta.headers.get("content-type")?.includes("application/json")) {
      throw new Error("Servidor Python indisponível. Confira o terminal.");
    }
    const dados = await resposta.json();
    if (!resposta.ok) throw new Error(dados.erro || "Erro ao executar a operação.");
    return dados;
  }

  function painel() { return document.getElementById("geracao-painel"); }

  function montar() {
    const confirmado = document.querySelector(".confirmacao");
    const consultaId = sessionStorage.getItem(CHAVE);
    if (!confirmado || !consultaId) {
      painel()?.remove();
      idAtual = null;
      dadosAtuais = null;
      erroAtual = "";
      return;
    }
    let host = painel();
    if (!host) {
      host = document.createElement("section");
      host.id = "geracao-painel";
      host.className = "geracao-painel";
      host.setAttribute("aria-label", "Geração e aprovação de plano de aula");
      host.addEventListener("click", clicar);
      document.querySelector("main .colunas")?.insertAdjacentElement("afterend", host);
    }
    if (consultaId === idAtual) return;
    idAtual = consultaId;
    dadosAtuais = null;
    erroAtual = "";
    host.innerHTML = '<h2>Geração do plano de aula</h2><p aria-live="polite">Carregando consulta confirmada…</p>';
    api("/api/consultas/" + consultaId).then(resposta => {
      if (idAtual === consultaId) { dadosAtuais = resposta; renderizar(); }
    }).catch(erro => {
      if (idAtual === consultaId && painel()) {
        painel().innerHTML = '<h2>Geração do plano de aula</h2><p role="alert" class="erro">' + texto(erro.message) + '</p>';
      }
    });
  }

  function etapaHtml(e, i) {
    return '<li><span class="geracao-numero">' + (i + 1) + '</span><div><b>' + texto(e.etapa || "Etapa") + '</b>' +
      '<small>' + texto(e.minutos) + ' min</small><p>' + texto(e.atividade) + '</p></div></li>';
  }

  function planoHtml(plano, resultado, geracao) {
    return `<article class="geracao-documento">
      <div class="geracao-cabecalho"><div><span class="geracao-rotulo">Plano candidato · revisão ${geracao.revisao}</span>
      <h3>${texto(plano.titulo)}</h3></div><span class="geracao-status ${geracao.estado === "aprovado" ? "aprovado" : ""}">${geracao.estado === "aprovado" ? "Aprovado pelo professor" : "Aguardando aprovação"}</span></div>
      <div class="geracao-resumo"><span><b>Ano</b> ${texto(plano.ano)}</span><span><b>Duração</b> ${texto(plano.duracao_min)} min</span><span><b>Tipo</b> ${texto(plano.tipo)}</span></div>
      <div class="geracao-habilidade"><b>Habilidade BNCC · ${texto(plano.habilidade_codigo)}</b><p>${texto(plano.habilidade_texto)}</p></div>
      <h4>Objetivos de aprendizagem</h4><ul>${(plano.objetivos || []).map(o => `<li>${texto(o)}</li>`).join("")}</ul>
      <h4>Metodologia</h4><p>${texto(plano.metodologia)}</p>
      <h4>Recursos disponíveis</h4><p>${texto(plano.recursos)}</p>
      <h4>Sequência didática</h4><ol class="geracao-etapas">${(plano.etapas || []).map(etapaHtml).join("")}</ol>
      <h4>Avaliação da aprendizagem</h4><p>${texto(plano.avaliacao)}</p>
      <h4>Possíveis adaptações</h4><ul>${(plano.adaptacoes || []).map(a => `<li>${texto(a)}</li>`).join("")}</ul>
      <details class="geracao-rastreio"><summary>Inspecionar agentes, entradas e saídas (${(resultado.rastreio || []).length})</summary>
      <p>Estas etapas registram o encadeamento do protótipo. No modo demonstrativo são funções baseadas em regras, não chamadas de LLM.</p>
      ${(resultado.rastreio || []).map(a => `<details><summary>${texto(a.agente)}</summary><b>Entrada</b><pre>${json(a.entrada)}</pre><b>Saída</b><pre>${json(a.saida)}</pre></details>`).join("")}
      </details>
      <details><summary>Ver plano completo (JSON)</summary><pre>${json(resultado)}</pre></details>
      </article>`;
  }

  function renderizar() {
    const host = painel();
    if (!host || !dadosAtuais) return;
    const geracao = dadosAtuais.geracao_atual;
    const resultado = geracao?.resultado;
    const aprovado = geracao?.estado === "aprovado";
    window.dispatchEvent(new CustomEvent("aulaia:geracao-atualizada", {
      detail: { consultaId: idAtual, estado: geracao?.estado || "nao_gerado" }
    }));
    const demo = !resultado || resultado.modo === "demonstracao";
    host.innerHTML = `<div class="geracao-intro">
      <div><span class="geracao-rotulo">Novo incremento da prova de conceito</span><h2>Geração do plano de aula</h2>
      <p>Com a habilidade curricular confirmada, o sistema prepara um plano, mostra as etapas de construção e permite a sua aprovação pedagógica.</p></div>
      <span class="geracao-identidade">${resultado?.modo === "ia" ? "Agentes de IA" : "Modo demonstrativo"}</span></div>
      ${erroAtual ? `<p role="alert" class="erro">${texto(erroAtual)}</p>` : ""}
      <div class="geracao-alerta">${demo
        ? "<b>Demonstração por regras:</b> o plano é gerado automaticamente, mas não por um modelo de linguagem. Para executar agentes com IA, configure OPENAI_API_KEY e inicie o servidor com --gerador ia."
        : `<b>Geração com IA:</b> especialistas executados sequencialmente com o modelo ${texto(resultado.modelo)}. A aprovação do professor não substitui a futura revisão pela IA Juiz.`}</div>
      ${resultado ? planoHtml(resultado.plano, resultado, geracao) : `<p class="geracao-vazio">Nenhum plano gerado ainda. A habilidade ${texto(dadosAtuais.entrada_geracao.habilidade.codigo)} está confirmada e pronta para iniciar o processo.</p>`}
      <div class="geracao-botoes">
        ${!aprovado ? `<button type="button" class="primario" data-geracao-acao="gerar" ${ocupado ? "disabled" : ""}>${ocupado ? "Processando agentes…" : resultado ? "Gerar outra versão" : "Gerar plano de aula"}</button>` : ""}
        ${resultado && !aprovado ? `<button type="button" class="primario geracao-aprovar" data-geracao-acao="aprovar" ${ocupado ? "disabled" : ""}>Aprovar este plano</button>` : ""}
        ${resultado ? `<button type="button" class="secundario" data-geracao-acao="imprimir">Imprimir plano</button>` : ""}
      </div>
      <p class="geracao-nota">${aprovado ? "A aprovação foi registrada no banco de dados. Para iniciar outro planejamento, altere o contexto e consulte novamente." : "A decisão final é sua. A verificação automática da IA Juiz será acrescentada no próximo incremento."}</p>`;
  }

  async function clicar(evento) {
    const botao = evento.target.closest("button[data-geracao-acao]");
    if (!botao || ocupado) return;
    const acao = botao.dataset.geracaoAcao;
    if (acao === "imprimir") { window.print(); return; }
    if (!dadosAtuais?.entrada_geracao) return;
    ocupado = true;
    erroAtual = "";
    renderizar();
    const consultaId = idAtual;
    try {
      let dados;
      if (acao === "gerar") dados = await api(`/api/consultas/${consultaId}/gerar`, {});
      else if (acao === "aprovar") {
        const idGeracao = dadosAtuais.geracao_atual?.id;
        if (!idGeracao) throw new Error("Gere um plano antes de aprová-lo.");
        dados = await api(`/api/geracoes/${idGeracao}/aprovar`, {});
      } else return;
      if (idAtual === consultaId) dadosAtuais = dados;
    } catch (erro) { erroAtual = erro.message; }
    finally { ocupado = false; renderizar(); }
  }

  function agendar() {
    if (atualizacaoAgendada) return;
    atualizacaoAgendada = true;
    queueMicrotask(() => { atualizacaoAgendada = false; montar(); });
  }
  new MutationObserver(agendar).observe(document.getElementById("root"), { childList: true, subtree: true });
  agendar();
})();
