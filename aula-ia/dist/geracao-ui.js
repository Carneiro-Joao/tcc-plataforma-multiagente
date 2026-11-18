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
  // Só na exibição: inicial maiúscula no que o professor digitou (ex.: "papel" -> "Papel").
  // O dado salvo não muda, pois o contrato exige recursos idênticos à entrada.
  const inicialMaiuscula = valor => String(valor ?? "").trim().replace(/^\p{Ll}/u, letra => letra.toLocaleUpperCase("pt-BR"));
  const textoDigitado = valor => escapar(inicialMaiuscula(valor));
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

  function planoCompletoHtml(p, resultado, geracao) {
    const i = p.identificacao;
    const h = p.habilidade_bncc;
    const ids = valores => valores.map(texto).join(", ");
    return `<article class="geracao-documento">
      <div class="geracao-cabecalho"><div><span class="geracao-rotulo">Plano candidato · revisão ${texto(geracao.revisao)}</span>
      <h3>${texto(i.titulo)}</h3></div><span class="geracao-status ${geracao.estado === "aprovado" ? "aprovado" : ""}">${geracao.estado === "aprovado" ? "Aprovado pelo professor" : "Aguardando aprovação"}</span></div>
      <h4>1. Identificação</h4>
      <div class="geracao-resumo"><span><b>Componente</b> ${texto(i.componente)}</span><span><b>Ano</b> ${texto(i.ano)}</span><span><b>Duração</b> ${texto(i.duracao_min)} min</span><span><b>Tipo</b> ${texto(i.tipo)}</span></div>
      <p><b>Tema:</b> ${textoDigitado(i.tema)}</p>
      <h4>2. Habilidade BNCC</h4><div class="geracao-habilidade"><b>${texto(h.codigo)}</b><p>${texto(h.descricao)}</p>
      <p><b>Eixo:</b> ${texto(h.eixo)}<br><b>Objeto de conhecimento:</b> ${texto(h.objeto_conhecimento)}</p>
      <p>${texto(h.referencia.documento)} · habilidade na página ${texto(h.referencia.pagina_habilidade)}, exemplos na página ${texto(h.referencia.pagina_exemplos)}.</p></div>
      <h4>3. Conteúdos</h4><ul>${p.conteudos.map(v => `<li>${texto(v)}</li>`).join("")}</ul>
      <h4>4. Objetivo geral</h4><p>${texto(p.objetivo_geral)}</p>
      <h4>5. Objetivos específicos</h4><ul>${p.objetivos_especificos.map(o => `<li><b>${texto(o.id)}</b> — ${texto(o.descricao)}</li>`).join("")}</ul>
      <h4>6. Metodologia</h4><p>${texto(p.metodologia)}</p>
      <h4>7. Recursos disponíveis</h4><p>${textoDigitado(p.recursos)}</p>
      <h4>8. Desenvolvimento</h4><ol class="geracao-etapas">${p.desenvolvimento.map(e => `<li><span class="geracao-numero">${texto(e.id)}</span><div><b>${texto(e.titulo)}</b><small>${texto(e.minutos)} min</small>
      <p><b>Atividade:</b> ${texto(e.atividade)}</p><p><b>Professor:</b> ${texto(e.acao_docente)}</p><p><b>Estudantes:</b> ${texto(e.acao_discente)}</p>
      <p>Objetivos: ${ids(e.objetivos_ids)} · Evidências: ${ids(e.evidencias_ids)}</p></div></li>`).join("")}</ol>
      <h4>9. Avaliação da aprendizagem</h4><p>Critérios e evidências esperadas para a aula:</p>
      <ul>${p.avaliacao_aprendizagem.evidencias.map(e => `<li><b>${texto(e.id)} · ${texto(e.objetivo_id)}</b><p><b>Critério:</b> ${texto(e.criterio)}</p><p><b>Evidência esperada:</b> ${texto(e.evidencia_esperada)}</p></li>`).join("")}</ul>
      <p><b>Instrumentos e procedimentos</b></p><ul>${p.avaliacao_aprendizagem.instrumentos.map(v => `<li><b>${texto(v.id)} — ${texto(v.descricao)}</b><p>${texto(v.procedimento)}</p><p>Etapas: ${ids(v.etapas_ids)} · Evidências: ${ids(v.evidencias_ids)}</p></li>`).join("")}</ul>
      <p><b>Uso dos resultados futuros:</b> ${texto(p.avaliacao_aprendizagem.uso_resultados)}</p>
      <h4>10. Adaptações inclusivas</h4><ul>${p.adaptacoes.map(a => `<li><b>${texto(a.id)}</b> — ${texto(a.descricao)}<p>Objetivos: ${ids(a.objetivos_ids)} · Etapas: ${ids(a.etapas_ids)}</p></li>`).join("")}</ul>
      <h4>11. Referências</h4><ul>${p.referencias.map(r => `<li>${texto(r.titulo)}. ${texto(r.arquivo)}. Páginas: ${ids(r.paginas)}. Catálogo: ${texto(r.versao_catalogo)}.</li>`).join("")}</ul>
      <details class="geracao-rastreio"><summary>Inspecionar a construção do plano</summary>
      <p>Cinco especialidades em seis chamadas normais: a avaliação define evidências antes das atividades e instrumentos depois. Reparos e novas tentativas após indisponibilidade ficam registrados em cada etapa. O integrador compõe as 11 seções em Python. Na demonstração, todas as etapas usam regras locais.</p>
      ${(resultado.rastreio || []).map(a => `<details><summary>${texto(a.agente)} · ${texto(a.estado)} · tentativa ${texto(a.tentativa || "—")}</summary><pre>${json(a)}</pre></details>`).join("")}</details>
      <details><summary>Ver plano completo (JSON)</summary><pre>${json(resultado)}</pre></details>
    </article>`;
  }

  function planoHtml(plano, resultado, geracao) {
    if (resultado.contrato === "plano-aula-2.0") return planoCompletoHtml(plano, resultado, geracao);
    return `<article class="geracao-documento">
      <div class="geracao-cabecalho"><div><span class="geracao-rotulo">Plano candidato · revisão ${geracao.revisao}</span>
      <h3>${texto(plano.titulo)}</h3></div><span class="geracao-status ${geracao.estado === "aprovado" ? "aprovado" : ""}">${geracao.estado === "aprovado" ? "Aprovado pelo professor" : "Aguardando aprovação"}</span></div>
      <div class="geracao-resumo"><span><b>Ano</b> ${texto(plano.ano)}</span><span><b>Duração</b> ${texto(plano.duracao_min)} min</span><span><b>Tipo</b> ${texto(plano.tipo)}</span></div>
      <div class="geracao-habilidade"><b>Habilidade BNCC · ${texto(plano.habilidade_codigo)}</b><p>${texto(plano.habilidade_texto)}</p></div>
      <h4>Objetivos de aprendizagem</h4><ul>${(plano.objetivos || []).map(o => `<li>${texto(o)}</li>`).join("")}</ul>
      <h4>Metodologia</h4><p>${texto(plano.metodologia)}</p>
      <h4>Recursos disponíveis</h4><p>${textoDigitado(plano.recursos)}</p>
      <h4>Sequência didática</h4><ol class="geracao-etapas">${(plano.etapas || []).map(etapaHtml).join("")}</ol>
      <h4>Avaliação da aprendizagem</h4><p>${texto(plano.avaliacao)}</p>
      <h4>Possíveis adaptações</h4><ul>${(plano.adaptacoes || []).map(a => `<li>${texto(a)}</li>`).join("")}</ul>
      <details class="geracao-rastreio"><summary>Inspecionar agentes, entradas e saídas (${(resultado.rastreio || []).length})</summary>
      <p>Os cinco especialistas são validados separadamente. O integrador monta o plano em Python. No modo demonstrativo, todas as etapas usam regras locais.</p>
      ${(resultado.rastreio || []).map(a => `<details><summary>${texto(a.agente)}</summary><b>Entrada</b><pre>${json(a.entrada)}</pre><b>Saída</b><pre>${json(a.saida)}</pre></details>`).join("")}
      </details>
      <details><summary>Ver plano completo (JSON)</summary><pre>${json(resultado)}</pre></details>
      </article>`;
  }

  function renderizar() {
    const host = painel();
    if (!host || !dadosAtuais) return;
    const geracao = dadosAtuais.geracao_atual;
    const resultado = geracao?.resultado?.plano ? geracao.resultado : null;
    const falha = geracao?.estado === "falha" ? geracao.resultado : null;
    const aprovado = geracao?.estado === "aprovado";
    window.dispatchEvent(new CustomEvent("aulaia:geracao-atualizada", {
      detail: { consultaId: idAtual, estado: geracao?.estado || "nao_gerado" }
    }));
    const demo = resultado?.modo === "demonstracao";
    host.innerHTML = `<div class="geracao-intro">
      <div><span class="geracao-rotulo">Novo incremento da prova de conceito</span><h2>Geração do plano de aula</h2>
      <p>Com a habilidade curricular confirmada, o sistema prepara um plano, mostra as etapas de construção e permite a sua aprovação pedagógica.</p></div>
      <span class="geracao-identidade">${resultado?.modo === "ia" ? "Gemini" : demo ? "Modo demonstrativo" : "Planejamento"}</span></div>
      ${erroAtual || falha ? `<p role="alert" class="erro">${texto(erroAtual || falha.erro)}</p>` : ""}
      <div class="geracao-alerta">${demo
        ? "<b>Demonstração por regras:</b> o plano é gerado automaticamente, mas não por um modelo de linguagem. Revise a adequação pedagógica antes de aprovar."
        : resultado ? `<b>Geração com IA:</b> cinco especialistas usam ${texto(resultado.modelo)}. O plano passou pela verificação automática e deve ser revisado pedagogicamente.` : "O plano será apresentado para sua revisão. A geração pode levar alguns minutos."}</div>
      ${falha ? `<details><summary>Detalhes da tentativa que falhou</summary><pre>${json(falha)}</pre></details>` : ""}
      ${resultado ? planoHtml(resultado.plano, resultado, geracao) : `<p class="geracao-vazio">Nenhum plano gerado ainda. A habilidade ${texto(dadosAtuais.entrada_geracao.habilidade.codigo)} está confirmada e pronta para iniciar o processo.</p>`}
      <div class="geracao-botoes">
        ${!aprovado ? `<button type="button" class="primario" data-geracao-acao="gerar" ${ocupado ? "disabled" : ""}>${ocupado ? "Processando agentes…" : resultado ? "Gerar outra versão" : "Gerar plano de aula"}</button>` : ""}
        ${resultado && !aprovado ? `<button type="button" class="primario geracao-aprovar" data-geracao-acao="aprovar" ${ocupado ? "disabled" : ""}>Aprovar este plano</button>` : ""}
        ${resultado ? `<button type="button" class="secundario" data-geracao-acao="imprimir">Imprimir plano</button>` : ""}
      </div>
      <p class="geracao-nota">${aprovado ? "A aprovação foi registrada. Para iniciar outro planejamento, altere o contexto e consulte novamente." : "A decisão final é sua. A verificação automática da IA Juiz será acrescentada no próximo incremento."}</p>`;
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
    } catch (erro) {
      erroAtual = erro.message;
      try {
        const consulta = await api(`/api/consultas/${consultaId}`);
        if (idAtual === consultaId) dadosAtuais = consulta;
      } catch (_) { /* preserva a mensagem da ação original */ }
    }
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
