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
  let timerProgresso = null;
  let inicioPedido = 0;
  let acaoAtual = "";

  const escapar = valor => String(valor ?? "").replace(/[&<>"']/g, caractere => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  })[caractere]);
  const texto = valor => escapar(valor);
  // Só na exibição: inicial maiúscula no que o professor digitou (ex.: "papel" -> "Papel").
  // O dado salvo não muda, pois o contrato exige recursos idênticos à entrada.
  const inicialMaiuscula = valor => String(valor ?? "").trim().replace(/^\p{Ll}/u, letra => letra.toLocaleUpperCase("pt-BR"));
  const textoDigitado = valor => escapar(inicialMaiuscula(valor));
  // Título: o modelo de demonstração repete o tema digitado após o travessão ("Plano de aula — quero…").
  const tituloExibido = valor => escapar(inicialMaiuscula(valor).replace(/(—\s*)(\p{Ll})/u, (_, sep, letra) => sep + letra.toLocaleUpperCase("pt-BR")));
  const json = valor => escapar(JSON.stringify(valor, null, 2));
  // JSON e rastreio técnico ficam fora da vista do professor; aparecem só com ?depuracao=1 na URL.
  const depuracao = () => new URLSearchParams(globalThis.location?.search || "").get("depuracao") === "1";
  const soDepuracao = html => depuracao() ? html : "";

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
      if (idAtual === consultaId) {
        dadosAtuais = resposta;
        if (resposta.pedido_atual?.em_andamento) iniciarAcompanhamento(consultaId);
        renderizar();
      }
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
      <h3>${tituloExibido(i.titulo)}</h3></div><span class="geracao-status ${geracao.estado === "aprovado" ? "aprovado" : ""}">${geracao.estado === "aprovado" ? "Aprovado pelo professor" : "Aguardando aprovação"}</span></div>
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
      ${soDepuracao(`<details class="geracao-rastreio"><summary>Inspecionar a construção do plano</summary>
      <p>Cinco especialidades em seis chamadas normais: a avaliação define evidências antes das atividades e instrumentos depois. Reparos e novas tentativas após indisponibilidade ficam registrados em cada etapa. O integrador compõe as 11 seções em Python. Na demonstração, todas as etapas usam regras locais.</p>
      ${(resultado.rastreio || []).map(a => `<details><summary>${texto(a.agente)} · ${texto(a.estado)} · tentativa ${texto(a.tentativa || "—")}</summary><pre>${json(a)}</pre></details>`).join("")}</details>
      <details><summary>Ver plano completo (JSON)</summary><pre>${json(resultado)}</pre></details>`)}
    </article>`;
  }

  function planoHtml(plano, resultado, geracao) {
    if (resultado.contrato === "plano-aula-2.0") return planoCompletoHtml(plano, resultado, geracao);
    return `<article class="geracao-documento">
      <div class="geracao-cabecalho"><div><span class="geracao-rotulo">Plano candidato · revisão ${geracao.revisao}</span>
      <h3>${tituloExibido(plano.titulo)}</h3></div><span class="geracao-status ${geracao.estado === "aprovado" ? "aprovado" : ""}">${geracao.estado === "aprovado" ? "Aprovado pelo professor" : "Aguardando aprovação"}</span></div>
      <div class="geracao-resumo"><span><b>Ano</b> ${texto(plano.ano)}</span><span><b>Duração</b> ${texto(plano.duracao_min)} min</span><span><b>Tipo</b> ${texto(plano.tipo)}</span></div>
      <div class="geracao-habilidade"><b>Habilidade BNCC · ${texto(plano.habilidade_codigo)}</b><p>${texto(plano.habilidade_texto)}</p></div>
      <h4>Objetivos de aprendizagem</h4><ul>${(plano.objetivos || []).map(o => `<li>${texto(o)}</li>`).join("")}</ul>
      <h4>Metodologia</h4><p>${texto(plano.metodologia)}</p>
      <h4>Recursos disponíveis</h4><p>${textoDigitado(plano.recursos)}</p>
      <h4>Sequência didática</h4><ol class="geracao-etapas">${(plano.etapas || []).map(etapaHtml).join("")}</ol>
      <h4>Avaliação da aprendizagem</h4><p>${texto(plano.avaliacao)}</p>
      <h4>Possíveis adaptações</h4><ul>${(plano.adaptacoes || []).map(a => `<li>${texto(a)}</li>`).join("")}</ul>
      ${soDepuracao(`<details class="geracao-rastreio"><summary>Inspecionar agentes, entradas e saídas (${(resultado.rastreio || []).length})</summary>
      <p>Os cinco especialistas são validados separadamente. O integrador monta o plano em Python. No modo demonstrativo, todas as etapas usam regras locais.</p>
      ${(resultado.rastreio || []).map(a => `<details><summary>${texto(a.agente)}</summary><b>Entrada</b><pre>${json(a.entrada)}</pre><b>Saída</b><pre>${json(a.saida)}</pre></details>`).join("")}
      </details>
      <details><summary>Ver plano completo (JSON)</summary><pre>${json(resultado)}</pre></details>`)}
      </article>`;
  }

  // ---- IA Juiz: painel da avaliação e progresso do pedido (PoC 08) ----
  const AVISO_JUIZ = "Avaliação automática e provisória; a decisão final é do professor.";
  const CRITERIOS = { aderencia_curricular: "Aderência curricular", alinhamento_objetivos: "Alinhamento dos objetivos",
    coerencia_metodologica: "Coerência metodológica", viabilidade: "Viabilidade",
    avaliacao_aprendizagem: "Avaliação da aprendizagem", inclusao: "Inclusão" };
  const COMPONENTES = { objetivos: "Objetivos", avaliacao_preliminar: "Evidências de avaliação", metodologia: "Metodologia",
    sequencia: "Sequência didática", avaliacao_final: "Instrumentos de avaliação", adaptacao: "Adaptações" };
  const GRAVIDADES = { critica: "Crítica", maior: "Maior", menor: "Menor" };
  const CLASSES = { aguardando_decisao: "favoravel", em_correcao: "ressalvas", revisao_necessaria: "revisao" };

  function avaliacaoHtml(avaliacao, pedido, geracaoId) {
    if (!avaliacao) return "";
    const parecer = avaliacao.parecer;
    const classe = CLASSES[avaliacao.status] || "indisponivel";
    const notas = parecer ? `<table class="juiz-notas"><thead><tr><th>Critério</th><th>Nota (0–3)</th></tr></thead><tbody>${
      parecer.avaliacoes.map(a => `<tr><td>${texto(CRITERIOS[a.criterio] || a.criterio)}</td><td><b>${texto(a.nota)}</b></td></tr>`).join("")
    }</tbody></table>` : "";
    const criticas = !parecer ? "" : parecer.falhas.length
      ? `<h5>Críticas do Juiz</h5><ul class="juiz-criticas">${parecer.falhas.map(f => `<li class="juiz-grav-${texto(f.gravidade)}">
          <span class="juiz-gravidade">${texto(GRAVIDADES[f.gravidade] || f.gravidade)}</span>
          <b>${texto(COMPONENTES[f.componente] || f.componente)}</b> · ${texto(CRITERIOS[f.criterio] || f.criterio)}
          <p>${texto(f.descricao)}</p>${f.correcao_sugerida ? `<p class="juiz-sugestao"><b>Sugestão:</b> ${texto(f.correcao_sugerida)}</p>` : ""}</li>`).join("")}</ul>`
      : "<p>Nenhuma crítica registrada.</p>";
    const anteriores = (pedido?.historico || []).filter(h => h.evento === "avaliado" && h.geracao_id !== geracaoId);
    const informadas = (pedido?.historico || []).filter(h => h.evento === "regenerando" && h.modo === "informada");
    const regeneracao = informadas.map(h => `<p class="juiz-historico">A ${texto(h.ciclo + 1)}ª versão foi gerada a partir das
      críticas do Juiz à versão anterior (${texto((h.criticas_usadas || []).join(", "))}), mantendo o contexto confirmado.</p>`).join("");
    const historico = anteriores.map(h => `<p class="juiz-historico">${texto(h.ciclo + 1)}ª versão não aprovada pelo Juiz
      (${texto(h.rotulo)}): ${texto((h.criticas && h.criticas.length ? h.criticas : h.motivos || []).join(" · "))}</p>`).join("");
    const semParecer = avaliacao.status === "indisponivel"
      ? "<p>A IA Juiz não conseguiu avaliar este plano (falha técnica). Isso não é um parecer.</p>"
      : avaliacao.status === "nao_realizada" ? "<p>A avaliação automática não foi realizada para este plano.</p>" : "";
    return `<section class="juiz-painel juiz-${classe}" aria-label="Avaliação da IA Juiz">
      <div class="juiz-cabecalho"><h4>Avaliação da IA Juiz</h4><span class="juiz-decisao">${texto(avaliacao.rotulo)}</span></div>
      ${avaliacao.demonstracao ? `<p class="juiz-demo"><b>Demonstração:</b> ${texto(avaliacao.aviso_demonstracao || "parecer gravado")}</p>` : ""}
      ${pedido?.aviso ? `<p class="juiz-aviso-pedido">${texto(pedido.aviso)}</p>` : ""}
      ${historico}${regeneracao}${parecer?.resumo ? `<p class="juiz-resumo">${texto(parecer.resumo)}</p>` : ""}${semParecer}${notas}${criticas}
      <p class="juiz-aviso">${AVISO_JUIZ}</p>
      ${parecer ? soDepuracao(`<details><summary>Ver parecer completo (JSON)</summary><pre>${json(avaliacao)}</pre></details>`) : ""}
    </section>`;
  }

  function duracao(segundos) {
    const m = Math.floor(segundos / 60), s = segundos % 60;
    return m ? `${m} min ${String(s).padStart(2, "0")} s` : `${s} s`;
  }

  function progressoHtml(pedido, decorridoS) {
    const estado = pedido?.estado || "gerando";
    const ciclo = pedido?.ciclo || 0;
    const passos = [["gerando", 0, "Gerando plano…"], ["avaliando", 0, "IA Juiz avaliando…"]];
    const informada = c => (pedido?.historico || []).some(h => h.evento === "regenerando" && h.ciclo === c && h.modo === "informada");
    for (let c = 1; c <= ciclo; c++) passos.push(["regenerando", c, informada(c) ? "Ajustando: gerando nova versão com as críticas do Juiz…"
      : "Ajustando: gerando nova versão…"], ["avaliando", c, "IA Juiz avaliando a nova versão…"]);
    // Esperando a cota do Groq: mesma etapa de avaliação, com o texto da espera.
    const aguardando = estado === "aguardando_juiz";
    const atual = Math.max(0, passos.findIndex(([e, c]) => e === (aguardando ? "avaliando" : estado) && c === ciclo));
    return `<div class="pedido-progresso" role="status" aria-live="polite"><ol>${
      passos.map(([, , rotulo], i) => `<li class="${i < atual ? "feito" : i === atual ? "atual" : ""}">${
        texto(aguardando && i === atual ? "Aguardando a cota da IA Juiz…" : rotulo)}</li>`).join("")
    }</ol><p>Isso pode levar até 4 minutos. Você não precisa fazer nada: o plano chega já avaliado pela IA Juiz.${
      decorridoS ? ` Tempo decorrido: ${duracao(decorridoS)}.` : ""}</p></div>`;
  }

  function iniciarAcompanhamento(consultaId) {
    pararAcompanhamento();
    if (!inicioPedido) inicioPedido = Date.now();
    timerProgresso = setInterval(async () => {
      try {
        const consulta = await api("/api/consultas/" + consultaId);
        if (idAtual !== consultaId) return;
        if (ocupado) dadosAtuais = { ...dadosAtuais, pedido_atual: consulta.pedido_atual };
        else {
          dadosAtuais = consulta;
          if (!consulta.pedido_atual?.em_andamento) { pararAcompanhamento(); inicioPedido = 0; }
        }
        renderizar();
      } catch (_) { /* tenta de novo no próximo intervalo */ }
    }, 2000);
  }

  function pararAcompanhamento() {
    if (timerProgresso) clearInterval(timerProgresso);
    timerProgresso = null;
  }

  function renderizar() {
    const host = painel();
    if (!host || !dadosAtuais) return;
    const geracao = dadosAtuais.geracao_atual;
    const pedido = dadosAtuais.pedido_atual;
    const emAndamento = (ocupado && acaoAtual === "gerar") || Boolean(pedido?.em_andamento);
    const resultado = geracao?.resultado?.plano ? geracao.resultado : null;
    const falha = geracao?.estado === "falha" ? geracao.resultado : null;
    const aprovado = geracao?.estado === "aprovado";
    window.dispatchEvent(new CustomEvent("aulaia:geracao-atualizada", {
      detail: { consultaId: idAtual, estado: geracao?.estado || "nao_gerado" }
    }));
    const demo = resultado?.modo === "demonstracao";
    const decorrido = inicioPedido ? Math.round((Date.now() - inicioPedido) / 1000) : 0;
    host.innerHTML = `<div class="geracao-intro">
      <div><span class="geracao-rotulo">Planejamento com avaliação automática</span><h2>Geração do plano de aula</h2>
      <p>Com a habilidade curricular confirmada, cinco especialistas geram o plano e a IA Juiz o avalia automaticamente antes da entrega. Você revisa, aprova e baixa.</p></div>
      <span class="geracao-identidade">${resultado?.modo === "ia" ? "Gemini + IA Juiz" : demo ? "Modo demonstrativo" : "Planejamento"}</span></div>
      ${erroAtual || (falha && !emAndamento) ? `<p role="alert" class="erro">${texto(erroAtual || falha.erro)}</p>` : ""}
      ${emAndamento ? progressoHtml(pedido, decorrido) : `<div class="geracao-alerta">${demo
        ? "<b>Demonstração por regras:</b> o plano é gerado automaticamente, mas não por um modelo de linguagem. Revise a adequação pedagógica antes de aprovar."
        : resultado ? `<b>Geração com IA:</b> cinco especialistas usam ${texto(resultado.modelo)}. O plano passou pelo validador de contrato e pela IA Juiz e deve ser revisado pedagogicamente.` : "O plano será gerado, avaliado pela IA Juiz e apresentado para sua revisão. Isso pode levar até 4 minutos."}</div>`}
      ${falha && !emAndamento ? soDepuracao(`<details><summary>Detalhes da tentativa que falhou</summary><pre>${json(falha)}</pre></details>`) : ""}
      ${emAndamento ? "" : resultado ? avaliacaoHtml(geracao.avaliacao, pedido, geracao.id) + planoHtml(resultado.plano, resultado, geracao)
        : `<p class="geracao-vazio">Nenhum plano gerado ainda. A habilidade ${texto(dadosAtuais.entrada_geracao.habilidade.codigo)} está confirmada e pronta para iniciar o processo.</p>`}
      <div class="geracao-botoes">
        ${emAndamento ? `<button type="button" class="primario" disabled>Gerando e avaliando…</button>` : ""}
        ${!emAndamento && resultado && !aprovado ? `<button type="button" class="primario geracao-aprovar" data-geracao-acao="aprovar" ${ocupado ? "disabled" : ""}>Aprovar plano</button>` : ""}
        ${!emAndamento && !aprovado ? `<button type="button" class="${resultado ? "secundario" : "primario"}" data-geracao-acao="gerar" ${ocupado ? "disabled" : ""}>${resultado ? "Gerar novamente" : "Gerar plano de aula"}</button>` : ""}
        ${aprovado ? `<button type="button" class="primario" data-geracao-acao="imprimir">Baixar PDF</button>` : ""}
      </div>
      <p class="geracao-nota">${aprovado ? "A aprovação foi registrada. Use “Baixar PDF” para salvar ou imprimir o plano com o parecer resumido da IA Juiz." : "A decisão final é sua: o parecer da IA Juiz é consultivo. “Gerar novamente” repete a geração e a avaliação."}</p>`;
  }

  async function clicar(evento) {
    const botao = evento.target.closest("button[data-geracao-acao]");
    if (!botao || ocupado) return;
    const acao = botao.dataset.geracaoAcao;
    if (acao === "imprimir") { window.print(); return; }
    if (!dadosAtuais?.entrada_geracao) return;
    ocupado = true;
    acaoAtual = acao;
    erroAtual = "";
    const consultaId = idAtual;
    if (acao === "gerar") {
      inicioPedido = Date.now();
      dadosAtuais = { ...dadosAtuais, pedido_atual: { estado: "gerando", ciclo: 0, em_andamento: true, historico: [] } };
      iniciarAcompanhamento(consultaId);
    }
    renderizar();
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
    finally {
      ocupado = false;
      acaoAtual = "";
      if (!dadosAtuais?.pedido_atual?.em_andamento) { pararAcompanhamento(); inicioPedido = 0; }
      renderizar();
    }
  }

  function agendar() {
    if (atualizacaoAgendada) return;
    atualizacaoAgendada = true;
    queueMicrotask(() => { atualizacaoAgendada = false; montar(); });
  }
  new MutationObserver(agendar).observe(document.getElementById("root"), { childList: true, subtree: true });
  agendar();
})();
