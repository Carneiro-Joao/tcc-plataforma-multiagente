import { useEffect, useRef, useState } from "react";
import "./App.css";

const INICIAL = { ano: "8º ano", duracao_min: "50", tema: "", recursos: "", tipo: "Computação desplugada" };
const CHAVE = "aulaia.consulta.v1";
const PDF = "/fonte/BNCCComputacao.pdf";

async function api(caminho, body, signal) {
  const resposta = await fetch(caminho, body ? {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body), signal,
  } : { signal });
  if (!resposta.headers.get("content-type")?.includes("application/json")) {
    throw new Error("A API está indisponível. Verifique se o servidor Python está em execução.");
  }
  const dados = await resposta.json();
  if (!resposta.ok) throw new Error(dados.erro || "Falha ao processar o pedido.");
  return dados;
}

function Icon({ nome, tamanho = 21, className = "" }) {
  const props = { width: tamanho, height: tamanho, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: 1.85, strokeLinecap: "round", strokeLinejoin: "round", className, "aria-hidden": true };
  switch (nome) {
    case "layers": return <svg {...props}><path d="m12 2 9 5-9 5-9-5 9-5Z"/><path d="m3 12 9 5 9-5M3 17l9 5 9-5"/></svg>;
    case "home": return <svg {...props}><path d="m3 10 9-7 9 7v10a1 1 0 0 1-1 1h-5v-7H9v7H4a1 1 0 0 1-1-1V10Z"/></svg>;
    case "book": return <svg {...props}><path d="M12 6c-3-2-6-2-9-1v14c3-1 6-1 9 1 3-2 6-2 9-1V5c-3-1-6-1-9 1Zm0 0v14"/></svg>;
    case "document": return <svg {...props}><path d="M7 3h7l5 5v13H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2Z"/><path d="M14 3v5h5M9 12h6M9 16h6"/></svg>;
    case "clock": return <svg {...props}><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>;
    case "settings": return <svg {...props}><path d="M4 6h16M4 12h16M4 18h16"/><circle cx="9" cy="6" r="2" fill="currentColor" stroke="none"/><circle cx="16" cy="12" r="2" fill="currentColor" stroke="none"/><circle cx="11" cy="18" r="2" fill="currentColor" stroke="none"/></svg>;
    case "check": return <svg {...props}><path d="m5 12 4 4L19 6"/></svg>;
    case "arrow": return <svg {...props}><path d="M4 12h16m-6-6 6 6-6 6"/></svg>;
    case "search": return <svg {...props}><circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 5 5"/></svg>;
    case "clipboard": return <svg {...props}><rect x="5" y="4" width="14" height="18" rx="2"/><rect x="9" y="2" width="6" height="4" rx="1"/><path d="M9 11h6M9 15h6"/></svg>;
    case "code": return <svg {...props}><path d="m8 8-4 4 4 4m8-8 4 4-4 4m-2-12-4 16"/></svg>;
    default: return null;
  }
}

function Referencia({ valor }) {
  return <div className="ref">
    <span>{valor.documento}</span>
    <a href={PDF + "#page=" + valor.pagina_habilidade} target="_blank" rel="noreferrer">Habilidade · p. {valor.pagina_habilidade}</a>
    <a href={PDF + "#page=" + valor.pagina_exemplos} target="_blank" rel="noreferrer">Exemplos · p. {valor.pagina_exemplos}</a>
  </div>;
}

function Fonte() {
  return <div className="fonte">
    <div className="capa"><img src="/capa-bncc.jpg" alt="Capa do complemento de Computação à BNCC" /></div>
    <div className="ficha">
      <span className="rotulo">Documento curricular</span>
      <h3>BNCC de Computação</h3>
      <p>O catálogo reúne as 11 habilidades do 8º ano. Consulte pelo tema da aula ou escolha diretamente no catálogo.</p>
      <a href={PDF + "#page=52"} target="_blank" rel="noreferrer">Abrir documento-fonte <span aria-hidden="true">↗</span></a>
    </div>
  </div>;
}

function Resultados({ consulta, codigo, escolher, confirmar, ocupado }) {
  const hibrido = consulta.metodo === "hibrido";
  const manual = consulta.metodo === "catalogo";
  return <>
    <p className="metodo">{manual ? "Catálogo completo" : hibrido ? "Busca híbrida · similaridade semântica e bônus curricular" : "Busca lexical · termos e bônus curricular"}</p>
    {consulta.resultados.length === 0
      ? <p className="aviso">Nenhuma correspondência para este tema. Use “Escolher no catálogo” para ver as habilidades do 8º ano.</p>
      : <fieldset disabled={ocupado} className="resultados">
        <legend>Selecione uma habilidade</legend>
        {consulta.resultados.map(({ habilidade: h, pontuacao }) =>
          <div key={h.codigo} className={"resultado" + (codigo === h.codigo ? " escolhido" : "")}>
            <label className="opcao">
              <input type="radio" name="codigo" checked={codigo === h.codigo} onChange={() => escolher(h.codigo)} value={h.codigo}/>
              <span><b className="codigo">{h.codigo}</b><span className="descricao">{h.habilidade}</span></span>
            </label>
            <div className="fatos"><span>{h.objeto_conhecimento}</span><Referencia valor={h.referencia}/>
              <details><summary>Ver detalhes curriculares</summary>
                <p><strong>{h.eixo}</strong></p><p>{h.explicacao}</p>
                <ul>{h.exemplos.map(ex => <li key={ex}>{ex}</li>)}</ul>
                {pontuacao && <p className="scores">
                  {hibrido && <>Semântico {pontuacao.score_semantico.toFixed(4)} · </>}
                  Bônus {pontuacao.bonus.toFixed(4)} · Total {pontuacao.score_final.toFixed(4)}
                </p>}
              </details>
            </div>
          </div>
        )}
      </fieldset>}
    {consulta.resultados.length > 0 && <button type="button" className="primario confirmar" disabled={!codigo || ocupado} onClick={confirmar}>
      {ocupado ? "Confirmando…" : "Confirmar habilidade"} <Icon nome="check" tamanho={18}/>
    </button>}
  </>;
}

function Confirmacao({ entrada }) {
  const { contexto: c, habilidade: h } = entrada;
  return <div className="confirmacao">
    <div className="selo"><Icon nome="check" tamanho={18}/> Habilidade confirmada</div>
    <h3>{h.codigo}</h3><p className="destaque">{h.habilidade}</p>
    <Referencia valor={h.referencia}/>
    <h4><Icon nome="layers" tamanho={20}/> Contexto para a geração</h4>
    <dl>{[["Tema", c.tema], ["Turma", c.ano], ["Duração", c.duracao_min + " minutos"], ["Tipo de aula", c.tipo], ["Recursos", c.recursos]].map(([k,v]) =>
      <div key={k}><dt>{k}</dt><dd>{v}</dd></div>
    )}</dl>
    <details className="json-entrada"><summary>Ver entrada da geração (JSON)</summary><pre>{JSON.stringify(entrada, null, 2)}</pre></details>
  </div>;
}

const ETAPAS = ["Configurar aula", "Escolher habilidade", "Gerar e aprovar"];
function IndicadorDeProgresso({ etapa, aprovado }) {
  return <ol className="etapas" aria-label="Etapas do planejamento">
    {ETAPAS.map((nome, i) => {
      const concluida = i < etapa || (i === 2 && aprovado);
      const atual = i === etapa && !concluida;
      return <li key={nome} className={["etapa", concluida ? "concluida" : "", atual ? "atual" : ""].join(" ")} aria-current={atual ? "step" : undefined}>
        <span className="etapa-indice">{concluida ? <Icon nome="check" tamanho={18}/> : i + 1}</span>
        <span>{nome}</span>
      </li>;
    })}
  </ol>;
}

export default function App() {
  const [form, setForm] = useState(INICIAL);
  const [consulta, setConsulta] = useState(null);
  const [codigo, setCodigo] = useState("");
  const [aprovado, setAprovado] = useState(false);
  const [ocupacao, setOcupacao] = useState(() => sessionStorage.getItem(CHAVE) ? "restaurar" : "");
  const [erro, setErro] = useState("");
  const painel = useRef(null);
  const entrada = consulta?.entrada_geracao;
  const ocupado = Boolean(ocupacao);

  useEffect(() => {
    const id = sessionStorage.getItem(CHAVE);
    if (!id) return;
    const controller = new AbortController();
    api("/api/consultas/" + id, null, controller.signal).then(dados => {
      setConsulta(dados);
      setForm(dados.contexto);
      setCodigo(dados.entrada_geracao?.habilidade.codigo || "");
      setAprovado(dados.geracao_atual?.estado === "aprovado");
    }).catch(e => {
      if (controller.signal.aborted) return;
      setErro(e.message);
    }).finally(() => {
      if (!controller.signal.aborted) setOcupacao("");
    });
    return () => controller.abort();
  }, []);

  // A tela de geração é uma extensão progressiva; sincronizamos seu estado
  // para atualizar o indicador sem alterar os contratos da API existente.
  useEffect(() => {
    function aoAtualizar(e) {
      if (e.detail?.consultaId === sessionStorage.getItem(CHAVE)) {
        setAprovado(e.detail.estado === "aprovado");
      }
    }
    window.addEventListener("aulaia:geracao-atualizada", aoAtualizar);
    return () => window.removeEventListener("aulaia:geracao-atualizada", aoAtualizar);
  }, []);

  function limparConsulta() {
    sessionStorage.removeItem(CHAVE);
    setConsulta(null);
    setCodigo("");
    setAprovado(false);
    setErro("");
  }

  function alterar(e) {
    limparConsulta();
    setForm({ ...form, [e.target.name]: e.target.value });
  }

  async function consultar(e) {
    e.preventDefault();
    if (ocupado) return;
    const modo = e.nativeEvent.submitter?.value === "catalogo" ? "catalogo" : "tema";
    limparConsulta();
    setOcupacao("consulta");
    try {
      const dados = await api("/api/consultas", { consulta: modo, contexto: { ...form, duracao_min: Number(form.duracao_min) } });
      setConsulta(dados);
      sessionStorage.setItem(CHAVE, dados.id);
      painel.current?.focus();
    } catch (e) {
      setErro(e.message);
    } finally {
      setOcupacao("");
    }
  }

  async function confirmar() {
    if (ocupado || !codigo) return;
    setOcupacao("confirmar");
    setErro("");
    try {
      const dados = await api("/api/consultas/" + consulta.id + "/confirmar", { codigo });
      setConsulta(dados);
      painel.current?.focus();
    } catch (e) {
      setErro(e.message);
    } finally {
      setOcupacao("");
    }
  }

  const etapa = entrada ? 2 : consulta ? 1 : 0;
  return <div className="app">
    <aside className="lateral" aria-label="Menu lateral">
      <div className="marca"><span className="marca-icone"><Icon nome="layers" tamanho={30}/></span><div className="marca-texto"><b>AulaIA</b><span>Planejamento inteligente</span></div></div>
      <nav className="menu" aria-label="Navegação principal">
        <a className="menu-item selecionado" href="#planejamento" aria-current="page"><Icon nome="home"/>Planejar aula</a>
        <a className="menu-item" href="#curriculo"><Icon nome="book"/>Base curricular</a>
        {entrada ? <a className="menu-item" href="#geracao-painel"><Icon nome="document"/>Plano atual</a> : <span className="menu-item indisponivel" aria-disabled="true" title="Disponível após a confirmação da habilidade"><Icon nome="document"/>Plano atual</span>}
        <span className="menu-item indisponivel" aria-disabled="true" title="Funcionalidade prevista para um próximo incremento"><Icon nome="clock"/>Histórico <small>Em breve</small></span>
      </nav>
      <div className="lateral-rodape"><span className="rodape-ponto"/>Prova de conceito <small>BNCC de Computação · 8º ano</small></div>
    </aside>
    <div className="area-principal">
      <header className="topo">
        <div className="trilha"><Icon nome="home" tamanho={18}/><span aria-hidden="true">›</span><span>Planejamento</span><span aria-hidden="true">›</span><strong>Computação</strong></div>
        <span className="topo-etiqueta">Versão de demonstração</span>
      </header>
      <main id="planejamento">
        <div className="cabecalho"><span className="cabecalho-icone"><Icon nome="code" tamanho={35}/></span><div>
          <h1>Planejar aula de Computação</h1>
          <p className="intro">Defina o contexto da turma e confirme a habilidade que vai orientar o plano.</p>
        </div></div>
        <IndicadorDeProgresso etapa={etapa} aprovado={aprovado}/>
        {erro && <p role="alert" className="erro">{erro}</p>}
        <div className="colunas">
          <section className="painel" aria-labelledby="titulo-contexto"><h2 id="titulo-contexto"><span className="titulo-icone"><Icon nome="settings" tamanho={23}/></span>Contexto da aula</h2>
            <form onSubmit={consultar}><fieldset disabled={ocupado}>
              <div className="dupla">
                <label>Ano escolar<select name="ano" value={form.ano} onChange={alterar}><option>8º ano</option></select></label>
                <label>Duração (min)<input name="duracao_min" type="number" min="1" max="1440" step="1" required value={form.duracao_min} onChange={alterar}/></label>
              </div>
              <label>Tema da aula<textarea name="tema" required maxLength={800} rows="2" placeholder="Ex.: quero ensinar ordenação" value={form.tema} onChange={alterar}/></label>
              <label>Tipo de aula<select name="tipo" value={form.tipo} onChange={alterar}>
                {["Computação desplugada", "Aula prática", "Aula teórica", "Projeto"].map(t => <option key={t}>{t}</option>)}
              </select></label>
              <label>Recursos disponíveis<input name="recursos" required maxLength={800} placeholder="Ex.: papel e cartões" value={form.recursos} onChange={alterar}/></label>
              <div className="acoes">
                <button className="primario" type="submit" value="tema"><Icon nome="search" tamanho={18}/>{ocupacao === "consulta" ? "Consultando…" : "Consultar habilidades"}<Icon nome="arrow" tamanho={18}/></button>
                <button className="secundario" type="submit" value="catalogo"><Icon nome="book" tamanho={17}/> Escolher no catálogo</button>
              </div>
            </fieldset></form>
          </section>
          <section className="painel curricular" id="curriculo" aria-busy={ocupado}>
            <h2 ref={painel} tabIndex="-1"><span className="titulo-icone"><Icon nome="clipboard" tamanho={23}/></span>{entrada ? "Resumo da confirmação" : consulta ? "Habilidades encontradas" : "Base curricular"}</h2>
            {entrada ? <Confirmacao entrada={entrada}/> : consulta
              ? <Resultados consulta={consulta} codigo={codigo} escolher={setCodigo} confirmar={confirmar} ocupado={ocupado}/>
              : <Fonte/>}
          </section>
        </div>
      </main>
    </div>
  </div>;
}
