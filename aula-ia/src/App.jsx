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
      {ocupado ? "Confirmando…" : "Confirmar habilidade"}
    </button>}
  </>;
}

function Confirmacao({ entrada }) {
  const { contexto: c, habilidade: h } = entrada;
  return <div className="confirmacao">
    <div className="selo"><span aria-hidden="true">✓</span> Habilidade confirmada</div>
    <h3>{h.codigo}</h3><p className="destaque">{h.habilidade}</p>
    <Referencia valor={h.referencia}/>
    <h4>Contexto para a geração</h4>
    <dl>{[["Tema", c.tema], ["Turma", c.ano], ["Duração", c.duracao_min + " minutos"], ["Tipo de aula", c.tipo], ["Recursos", c.recursos]].map(([k,v]) =>
      <div key={k}><dt>{k}</dt><dd>{v}</dd></div>
    )}</dl>
    <details><summary>Ver entrada da geração (JSON)</summary><pre>{JSON.stringify(entrada, null, 2)}</pre></details>
  </div>;
}

export default function App() {
  const [form, setForm] = useState(INICIAL);
  const [consulta, setConsulta] = useState(null);
  const [codigo, setCodigo] = useState("");
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
    }).catch(e => {
      if (controller.signal.aborted) return;
      setErro(e.message);
    }).finally(() => {
      if (!controller.signal.aborted) setOcupacao("");
    });
    return () => controller.abort();
  }, []);

  function limparConsulta() {
    sessionStorage.removeItem(CHAVE);
    setConsulta(null);
    setCodigo("");
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
    <header className="barra"><div className="barra-interior">
      <div className="marca"><svg width="29" height="30" viewBox="0 0 29 30" fill="none" aria-hidden="true"><path d="M2 5c4-1 8 0 12 3v18c-4-3-8-4-12-3V5ZM27 5c-4-1-8 0-12 3v18c4-3 8-4 12-3V5Z" stroke="currentColor" strokeWidth="2.3" strokeLinejoin="round"/></svg>AulaIA</div>
      <span>Planejamento docente</span>
    </div></header>
    <main>
      <ol className="progresso" aria-label="Etapas do planejamento">
        {["Contexto", "Habilidade", "Confirmação"].map((s, i) => <li key={s} aria-current={i === etapa ? "step" : undefined} className={i <= etapa ? "ativa" : ""}>{s}</li>)}
      </ol>
      <h1>Planejar aula de Computação</h1>
      <p className="intro">Defina o contexto da turma e confirme a habilidade que vai orientar o plano.</p>
      {erro && <p role="alert" className="erro">{erro}</p>}
      <div className="colunas">
        <section className="painel"><h2>Contexto da aula</h2>
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
              <button className="primario" type="submit" value="tema">{ocupacao === "consulta" ? "Consultando…" : "Consultar habilidades"} <span aria-hidden="true">→</span></button>
              <button className="secundario" type="submit" value="catalogo">Escolher no catálogo</button>
            </div>
          </fieldset></form>
        </section>
        <section className="painel curricular" aria-busy={ocupado}>
          <h2 ref={painel} tabIndex="-1">{entrada ? "Resumo da confirmação" : consulta ? "Habilidades encontradas" : "Base curricular"}</h2>
          {entrada ? <Confirmacao entrada={entrada}/> : consulta
            ? <Resultados consulta={consulta} codigo={codigo} escolher={setCodigo} confirmar={confirmar} ocupado={ocupado}/>
            : <Fonte/>}
        </section>
      </div>
    </main>
  </div>;
}
