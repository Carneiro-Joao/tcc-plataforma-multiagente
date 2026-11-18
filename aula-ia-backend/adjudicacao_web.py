"""Código das páginas HTML da adjudicação humana (CSS e JavaScript embutidos, sem internet, sem bibliotecas).

Fica separado de adjudicacao.py só para manter cada arquivo legível. Três páginas de arquivo único:
  A  avaliação CEGA: nota própria dos planos e julgamento de cada crítica do Juiz, sem saber qual variante é qual;
  B  avaliação INFORMADA: mostra o defeito inserido e pergunta se cada parecer o detectou (fazer depois da A);
  C  comparação entre dois avaliadores: concordância, kappa e consenso.
"""

CSS = r"""
:root{--bg:#f6f7f9;--fg:#1c2330;--mut:#5b6678;--card:#fff;--bd:#d5dbe5;--ac:#1f5fbf;--ok:#1a7f37;--warn:#b45309;--ruim:#c62828;--sel:#e8f0fd}
@media(prefers-color-scheme:dark){:root{--bg:#0f141b;--fg:#e6eaf1;--mut:#9aa6b8;--card:#171e29;--bd:#2a3444;--ac:#6ea8ff;--ok:#3fb950;--warn:#f0a35a;--ruim:#ff6b6b;--sel:#1d2b45}}
*{box-sizing:border-box}body{margin:0;font:15px/1.5 system-ui,Segoe UI,Roboto,sans-serif;background:var(--bg);color:var(--fg)}
header{position:sticky;top:0;z-index:5;background:var(--card);border-bottom:1px solid var(--bd);padding:8px 16px;display:flex;flex-wrap:wrap;gap:8px;align-items:center}
header h1{font-size:1.05rem;margin:0 8px 0 0}.mut{color:var(--mut)}small{color:var(--mut)}
button,input,select,textarea{font:inherit;color:var(--fg);background:var(--card);border:1px solid var(--bd);border-radius:8px;padding:6px 12px}
button{cursor:pointer}button.pri{background:var(--ac);border-color:var(--ac);color:#fff}button:disabled{opacity:.45;cursor:not-allowed}
:focus-visible{outline:3px solid var(--ac);outline-offset:2px}
.barra{flex:1;min-width:140px;height:10px;background:var(--bd);border-radius:6px;overflow:hidden}.barra i{display:block;height:100%;background:var(--ok)}
main{max-width:1280px;margin:0 auto;padding:14px 16px 60px}
.abas{display:flex;gap:8px;margin:6px 0 12px;flex-wrap:wrap}.abas button[aria-selected=true]{border-color:var(--ac);color:var(--ac);font-weight:700}
.cols{display:grid;grid-template-columns:minmax(0,1.15fr) minmax(0,1fr);gap:16px;align-items:start}
@media(max-width:900px){.cols{grid-template-columns:1fr}}
.painel{background:var(--card);border:1px solid var(--bd);border-radius:12px;padding:12px 16px}
.plano{max-height:78vh;overflow:auto}.plano h4{margin:14px 0 4px;font-size:.85rem;text-transform:uppercase;letter-spacing:.04em;color:var(--mut)}
.plano h4:first-child{margin-top:0}.plano ul{margin:4px 0;padding-left:20px}.plano dl{margin:4px 0}.plano dt{font-weight:600;font-size:.85rem;color:var(--mut)}.plano dd{margin:0 0 4px 0}
.etapa{border-left:4px solid var(--ac);padding:4px 10px;margin:8px 0;background:var(--sel);border-radius:0 8px 8px 0}
.tag{display:inline-block;font-size:.75rem;border:1px solid var(--bd);border-radius:99px;padding:0 8px;margin-right:4px;color:var(--mut)}
.q{margin:14px 0}.q b{display:block;margin-bottom:4px}.op{display:flex;flex-wrap:wrap;gap:6px}
.op label{border:1px solid var(--bd);border-radius:8px;padding:5px 10px;cursor:pointer;display:flex;gap:6px;align-items:center}
.op label:has(input:checked){background:var(--sel);border-color:var(--ac);font-weight:600}
.op input{accent-color:var(--ac)}textarea{width:100%;min-height:64px}
.lista{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:10px}.lista button{padding:3px 10px;font-size:.85rem}
.lista button[aria-current=true]{border-color:var(--ac);color:var(--ac);font-weight:700}.lista button.feito{background:var(--sel)}
.critica{border-left:4px solid var(--warn);padding:6px 12px;background:var(--sel);border-radius:0 8px 8px 0;margin:8px 0}
.aviso{border:1px solid var(--warn);color:var(--warn);border-radius:8px;padding:8px 12px;margin:10px 0}
table{border-collapse:collapse;width:100%;font-size:.88rem}th,td{border:1px solid var(--bd);padding:5px 8px;text-align:left;vertical-align:top}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:10px;margin:10px 0}.cards .painel b{font-size:1.4rem;display:block}
details summary{cursor:pointer;font-weight:600}.nav{display:flex;justify-content:space-between;gap:8px;margin-top:14px}
.dif .a{background:#f8d7da33}pre{white-space:pre-wrap;word-break:break-word}
"""

COMUM = r"""
const $=(s,r=document)=>r.querySelector(s),$$=(s,r=document)=>[...r.querySelectorAll(s)];
const esc=s=>String(s==null?"":s).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const ROT_COMP={objetivos:"Objetivos",avaliacao_preliminar:"Avaliação preliminar (evidências)",metodologia:"Metodologia",sequencia:"Sequência (desenvolvimento)",avaliacao_final:"Avaliação final (instrumentos)",adaptacao:"Adaptações"};
const ROT_GRAV={critica:"crítica",maior:"maior",menor:"menor"};
function guardar(k,v){try{localStorage.setItem(k,JSON.stringify(v));return true}catch(e){return false}}
function ler(k){try{const t=localStorage.getItem(k);return t?JSON.parse(t):null}catch(e){return null}}
function baixar(nome,texto,mime){const a=document.createElement("a");a.href=URL.createObjectURL(new Blob([texto],{type:mime}));a.download=nome;document.body.appendChild(a);a.click();setTimeout(()=>{URL.revokeObjectURL(a.href);a.remove()},500)}
function csvCel(v){v=String(v==null?"":v).replace(/"/g,'""');return /[;"\n\r]/.test(v)?'"'+v+'"':v}
function csv(linhas){return "﻿"+linhas.map(l=>l.map(csvCel).join(";")).join("\r\n")}
function agora(){const d=new Date();return d.toLocaleTimeString("pt-BR",{hour:"2-digit",minute:"2-digit"})}
// <KAPPA>
function kappaNominal(a,b){const n=a.length;if(!n)return null;const cats=[...new Set([...a,...b])];let po=0;a.forEach((x,i)=>{if(x===b[i])po++});po/=n;
 let pe=0;cats.forEach(c=>{pe+=(a.filter(x=>x===c).length/n)*(b.filter(x=>x===c).length/n)});return 1-pe<1e-12?null:(po-pe)/(1-pe)}
function kappaPonderado(a,b,k){const n=a.length;if(!n)return null;const w=(i,j)=>1-Math.pow((i-j)/(k-1),2);let po=0;for(let t=0;t<n;t++)po+=w(a[t],b[t]);po/=n;
 let pe=0;for(let i=0;i<k;i++)for(let j=0;j<k;j++){pe+=w(i,j)*(a.filter(x=>x===i).length/n)*(b.filter(x=>x===j).length/n)}return 1-pe<1e-12?null:(po-pe)/(1-pe)}
// </KAPPA>
function val(v){if(v==null)return "";if(Array.isArray(v))return "<ul>"+v.map(x=>"<li>"+val(x)+"</li>").join("")+"</ul>";
 if(typeof v==="object")return "<dl>"+Object.entries(v).map(([k,x])=>"<dt>"+esc(k)+"</dt><dd>"+val(x)+"</dd>").join("")+"</dl>";return esc(v)}
function ids(a){return (a||[]).map(i=>'<span class="tag">'+esc(i)+"</span>").join("")}
function renderPlano(p,ent){
 const id=p.identificacao||{},hb=p.habilidade_bncc||{},c=(ent&&ent.contexto)||{},h=[];
 const sec=(t,b)=>h.push("<h4>"+esc(t)+"</h4>"+b);
 sec("Dados informados pelo professor (confirmados)","Ano: <b>"+esc(c.ano||id.ano)+"</b> · tema: <b>"+esc(c.tema||id.tema)+"</b> · duração: <b>"+esc(c.duracao_min||id.duracao_min)+" min</b> · tipo: <b>"+esc(c.tipo||id.tipo)+"</b><br>Recursos disponíveis: <b>"+val(c.recursos!=null?c.recursos:p.recursos)+"</b>");
 sec("Habilidade (BNCC)","<b>"+esc(hb.codigo)+"</b> — "+esc(hb.descricao)+"<br><small>"+esc(hb.eixo)+" · "+esc(hb.objeto_conhecimento)+"</small>");
 if(ent&&ent.habilidade){sec("Explicação e exemplos oficiais da habilidade",esc(ent.habilidade.explicacao)+val(ent.habilidade.exemplos))}
 sec("Plano — "+(id.titulo||""),"Conteúdos:"+val(p.conteudos));
 sec("Objetivo geral",esc(p.objetivo_geral));
 sec("Objetivos específicos","<ul>"+(p.objetivos_especificos||[]).map(o=>"<li><span class='tag'>"+esc(o.id)+"</span>"+esc(o.descricao)+"</li>").join("")+"</ul>");
 sec("Metodologia",esc(p.metodologia));
 sec("Recursos do plano",val(p.recursos));
 const dev=p.desenvolvimento||[];let tot=0;dev.forEach(e=>tot+=Number(e.minutos)||0);
 sec("Desenvolvimento (soma das etapas: "+tot+" min)",dev.map(e=>"<div class='etapa'><b>"+esc(e.id)+" — "+esc(e.titulo)+"</b> · "+esc(e.minutos)+" min<br><b>Ação docente:</b> "+esc(e.acao_docente)+"<br><b>Ação discente:</b> "+esc(e.acao_discente)+"<br><b>Atividade:</b> "+esc(e.atividade)+"<br>Objetivos: "+ids(e.objetivos_ids)+" Evidências: "+ids(e.evidencias_ids)+"</div>").join(""));
 const av=p.avaliacao_aprendizagem||{};
 sec("Avaliação — evidências",(av.evidencias||[]).map(e=>"<div class='etapa'><b>"+esc(e.id)+"</b> (objetivo "+esc(e.objetivo_id)+")<br><b>Critério:</b> "+esc(e.criterio)+"<br><b>Evidência esperada:</b> "+esc(e.evidencia_esperada)+"</div>").join(""));
 sec("Avaliação — instrumentos",(av.instrumentos||[]).map(e=>"<div class='etapa'><b>"+esc(e.id)+"</b> — "+esc(e.descricao)+"<br>Etapas: "+ids(e.etapas_ids)+" Evidências: "+ids(e.evidencias_ids)+"<br><b>Procedimento:</b> "+esc(e.procedimento)+"</div>").join(""));
 sec("Como os resultados serão usados",esc(av.uso_resultados));
 sec("Adaptações (inclusão)",(p.adaptacoes||[]).map(e=>"<div class='etapa'><b>"+esc(e.id)+"</b> — "+esc(e.descricao)+"<br>Objetivos: "+ids(e.objetivos_ids)+" Etapas: "+ids(e.etapas_ids)+"</div>").join(""));
 return h.join("")}
function radios(nome,opcoes,atual,attrs){return '<div class="op" role="radiogroup">'+opcoes.map(([v,l])=>'<label><input type="radio" name="'+nome+'" value="'+esc(v)+'" '+attrs+(atual===v?" checked":"")+"> "+esc(l)+"</label>").join("")+"</div>"}
"""

PAGINA_A = r"""
const D=DATA,CHAVE="adjud-A-"+D.dataset_id,CRIT=Object.keys(D.rubrica);
let S=ler(CHAVE)||{avaliador:"",notas:{},itens:{},etapa:1,plano:D.planos[0].codigo,item:0};
const planoPor=c=>D.planos.find(p=>p.codigo===c);
const notaFeita=(p,c)=>Number.isInteger((S.notas[p]||{})[c]);
const planoFeito=p=>CRIT.every(c=>notaFeita(p,c));
const etapa1Feita=()=>D.planos.every(p=>planoFeito(p.codigo));
const itemFeito=i=>!!(S.itens[i.codigo]||{}).procedencia;
function totais(){const t=D.planos.length*CRIT.length+D.itens.length;let f=0;D.planos.forEach(p=>CRIT.forEach(c=>{if(notaFeita(p.codigo,c))f++}));D.itens.forEach(i=>{if(itemFeito(i))f++});return[f,t]}
function salvar(){const ok=guardar(CHAVE,S);$("#salvo").textContent=ok?"Salvo neste navegador às "+agora():"Não foi possível salvar no navegador: baixe o arquivo."}
function exportar(){const[f,t]=totais();return{versao:"adjudicacao-1.0",fase:"A",dataset_id:D.dataset_id,avaliador:S.avaliador,exportado_em:new Date().toISOString(),completo:f===t,notas_proprias:S.notas,itens:S.itens}}
function slug(){return (S.avaliador||"avaliador").normalize("NFD").replace(/[^\w]+/g,"_").replace(/^_|_$/g,"").toLowerCase()||"avaliador"}
function cabecalho(){const[f,t]=totais();$("#prog").style.width=(100*f/t)+"%";$("#progtxt").textContent=f+" de "+t+" respostas";}
function render(){cabecalho();$$("[data-aba]").forEach(b=>b.setAttribute("aria-selected",String(+b.dataset.aba===S.etapa)));
 $("#aba2").disabled=!etapa1Feita();$("#aba2").title=etapa1Feita()?"":"Termine a Etapa 1 (as 30 notas) para liberar a Etapa 2";
 if(S.etapa===2&&!etapa1Feita())S.etapa=1;S.etapa===1?etapa1():etapa2()}
function etapa1(){const P=planoPor(S.plano);
 const lista=D.planos.map(p=>'<button data-plano="'+p.codigo+'" class="'+(planoFeito(p.codigo)?"feito":"")+'" '+(p.codigo===S.plano?'aria-current="true"':"")+">Plano "+p.codigo+(planoFeito(p.codigo)?" ✓":"")+"</button>").join("");
 const n=S.notas[P.codigo]||{};
 const cards=CRIT.map(c=>{const r=D.rubrica[c];return '<div class="q"><b>'+esc(r.rotulo)+"</b><small>"+esc(r.pergunta)+"</small>"+
  '<details><summary>Indicadores e âncoras da nota</summary><ul>'+r.indicadores.map(i=>"<li>"+esc(i)+"</li>").join("")+"</ul><ul>"+Object.entries(r.ancoras).sort((a,b)=>b[0]-a[0]).map(([k,v])=>"<li><b>"+k+"</b> — "+esc(v)+"</li>").join("")+"</ul></details>"+
  radios("n_"+c,[[0,"0 inadequado"],[1,"1 insuficiente"],[2,"2 com ressalvas"],[3,"3 adequado"]].map(([v,l])=>[String(v),l]),notaFeita(P.codigo,c)?String(n[c]):null,'data-nota="'+c+'"')+"</div>"}).join("");
 $("#conteudo").innerHTML='<div class="aviso"><b>Etapa 1 — sua leitura, antes de ver qualquer crítica.</b> Leia o plano e dê <b>a sua nota</b> (0 a 3) para cada critério, como se fosse o professor responsável. Não existe resposta certa; discorde do que achar errado. Esta etapa é a base para comparar você com o Juiz.</div><div class="lista">'+lista+'</div><div class="cols"><div class="painel plano" tabindex="0" aria-label="Plano de aula">'+renderPlano(P.plano,P.entrada)+'</div><div class="painel"><h3 style="margin-top:0">Plano '+P.codigo+'</h3>'+cards+'<div class="q"><b>Problemas que você apontaria neste plano (opcional)</b><textarea data-ncom="1" placeholder="Ex.: ET2 não repete as passagens; recurso X não está na lista...">'+esc(n.comentario||"")+"</textarea></div></div></div>";
 if(etapa1Feita())$("#conteudo").insertAdjacentHTML("beforeend",'<div class="nav"><span></span><button class="pri" data-aba="2" id="vai2">Etapa 1 completa — ir para a Etapa 2 →</button></div>')}
function etapa2(){const I=D.itens[S.item],P=planoPor(I.plano),r=D.rubrica[I.criterio]||{rotulo:I.criterio},a=S.itens[I.codigo]||{};
 const lista=D.itens.map((i,k)=>'<button data-item="'+k+'" class="'+(itemFeito(i)?"feito":"")+'" '+(k===S.item?'aria-current="true"':"")+">"+(k+1)+(itemFeito(i)?" ✓":"")+"</button>").join("");
 $("#conteudo").innerHTML='<div class="aviso"><b>Etapa 2 — julgue cada crítica do Juiz.</b> O Juiz é uma IA; ela pode errar. Marque se a crítica <b>procede com base no plano</b>, e não se você gostaria que o plano fosse diferente. Atalhos: teclas 1 a 4 respondem a primeira pergunta; ← → navegam.</div><div class="lista">'+lista+'</div><div class="cols"><div class="painel plano" tabindex="0" aria-label="Plano de aula"><b>Plano '+P.codigo+"</b>"+renderPlano(P.plano,P.entrada)+'</div><div class="painel"><h3 style="margin-top:0">Crítica '+(S.item+1)+" de "+D.itens.length+' <small>(Plano '+I.plano+")</small></h3>"+
  '<div><span class="tag">critério: '+esc(r.rotulo)+'</span><span class="tag">componente: '+esc(ROT_COMP[I.componente]||I.componente)+'</span><span class="tag">gravidade: '+esc(ROT_GRAV[I.gravidade]||I.gravidade)+'</span></div><div class="critica"><b>O Juiz escreveu:</b><br>'+esc(I.descricao)+'<br><br><b>Correção sugerida:</b><br>'+esc(I.correcao)+"</div>"+
  '<div class="q"><b>1. Esta crítica procede?</b>'+radios("procedencia",[["procedente","1 Procede"],["parcial","2 Procede em parte"],["improcedente","3 Não procede"],["nao_sei","4 Não sei avaliar"]],a.procedencia,'data-campo="procedencia"')+"</div>"+
  '<div class="q"><b>2. A gravidade ('+esc(ROT_GRAV[I.gravidade]||I.gravidade)+') está adequada?</b>'+radios("gravidade",[["adequada","Adequada"],["exagerada","Exagerada"],["subestimada","Subestimada"],["nao_sei","Não sei"]],a.gravidade,'data-campo="gravidade"')+"<small>crítica = plano inadequado sem revisão humana · maior = compromete o critério, corrigível refazendo o componente · menor = melhoria desejável</small></div>"+
  '<div class="q"><b>3. O componente apontado ('+esc(ROT_COMP[I.componente]||I.componente)+') é o responsável pelo problema?</b>'+radios("componente",[["sim","Sim"],["nao","Não"],["nao_aplica","Não procede / não se aplica"]],a.componente_correto,'data-campo="componente_correto"')+"</div>"+
  '<div class="q"><b>Comentário (opcional)</b><textarea data-icom="1">'+esc(a.comentario||"")+'</textarea></div><div class="nav"><button id="ant" '+(S.item===0?"disabled":"")+'>← Anterior</button><button id="prox" class="pri" '+(S.item===D.itens.length-1?"disabled":"")+">Próxima →</button></div></div></div>"}
document.addEventListener("change",e=>{const t=e.target;if(!(t instanceof HTMLInputElement)||t.type!=="radio")return;
 if(t.dataset.nota){(S.notas[S.plano]=S.notas[S.plano]||{})[t.dataset.nota]=+t.value}
 else if(t.dataset.campo){const I=D.itens[S.item];(S.itens[I.codigo]=S.itens[I.codigo]||{})[t.dataset.campo]=t.value}
 salvar();render();const novo=$('input[name="'+t.name+'"]:checked');if(novo)novo.focus()});
document.addEventListener("input",e=>{const t=e.target;if(t.dataset&&t.dataset.ncom){(S.notas[S.plano]=S.notas[S.plano]||{}).comentario=t.value;salvar()}
 if(t.dataset&&t.dataset.icom){const I=D.itens[S.item];(S.itens[I.codigo]=S.itens[I.codigo]||{}).comentario=t.value;salvar()}
 if(t.id==="nome"){S.avaliador=t.value;salvar()}});
document.addEventListener("click",e=>{const b=e.target.closest("button");if(!b)return;
 if(b.dataset.aba){S.etapa=+b.dataset.aba;salvar();render();window.scrollTo(0,0)}
 else if(b.dataset.plano){S.plano=b.dataset.plano;salvar();render();window.scrollTo(0,0)}
 else if(b.dataset.item){S.item=+b.dataset.item;salvar();render();window.scrollTo(0,0)}
 else if(b.id==="ant"&&S.item>0){S.item--;salvar();render();window.scrollTo(0,0)}
 else if(b.id==="prox"&&S.item<D.itens.length-1){S.item++;salvar();render();window.scrollTo(0,0)}
 else if(b.id==="baixar"){baixar("adjudicacao_A_"+slug()+".json",JSON.stringify(exportar(),null,1),"application/json")}
 else if(b.id==="csv"){const L=[["tipo","codigo","campo","valor"]];D.planos.forEach(p=>{const n=S.notas[p.codigo]||{};CRIT.forEach(c=>L.push(["nota_propria",p.codigo,c,n[c]==null?"":n[c]]));L.push(["nota_propria",p.codigo,"comentario",n.comentario||""])});
  D.itens.forEach(i=>{const a=S.itens[i.codigo]||{};["procedencia","gravidade","componente_correto","comentario"].forEach(c=>L.push(["item",i.codigo,c,a[c]||""]))});baixar("adjudicacao_A_"+slug()+".csv",csv(L),"text/csv")}
 else if(b.id==="limpar"){if(confirm("Apagar TODAS as respostas deste navegador? (O arquivo que você baixou não é afetado.)")){S={avaliador:"",notas:{},itens:{},etapa:1,plano:D.planos[0].codigo,item:0};try{localStorage.removeItem(CHAVE)}catch(x){}$("#nome").value="";render()}}});
$("#abrir").addEventListener("change",e=>{const f=e.target.files[0];if(!f)return;const r=new FileReader();r.onload=()=>{try{const j=JSON.parse(r.result);if(j.dataset_id!==D.dataset_id||j.fase!=="A")throw new Error("Este arquivo é de outra versão da adjudicação.");
 S.avaliador=j.avaliador||"";S.notas=j.notas_proprias||{};S.itens=j.itens||{};$("#nome").value=S.avaliador;salvar();render()}catch(x){alert("Não consegui carregar: "+x.message)}};r.readAsText(f)});
document.addEventListener("keydown",e=>{if(S.etapa!==2||/INPUT|TEXTAREA|SELECT/.test((document.activeElement||{}).tagName)&&document.activeElement.type!=="radio")return;
 const m={"1":"procedente","2":"parcial","3":"improcedente","4":"nao_sei"};
 if(m[e.key]){const I=D.itens[S.item];(S.itens[I.codigo]=S.itens[I.codigo]||{}).procedencia=m[e.key];salvar();render()}
 else if(e.key==="ArrowRight"&&S.item<D.itens.length-1){S.item++;salvar();render()}else if(e.key==="ArrowLeft"&&S.item>0){S.item--;salvar();render()}});
$("#nome").value=S.avaliador;render();
"""

PAGINA_B = r"""
const D=DATA,CHAVE="adjud-B-"+D.dataset_id;
let S=ler(CHAVE)||{avaliador:"",itens:{},item:0};
const campos=p=>D.grupos[p.grupo].tipo==="defeito"?["deteccao","componente_correto","falha_correspondente"]:["reagiu","falha_correspondente"];
const feito=p=>{const a=S.itens[p.codigo]||{};return D.grupos[p.grupo].tipo==="defeito"?!!a.deteccao:!!a.reagiu};
function totais(){let f=0;D.pareceres.forEach(p=>{if(feito(p))f++});return[f,D.pareceres.length]}
function salvar(){const ok=guardar(CHAVE,S);$("#salvo").textContent=ok?"Salvo neste navegador às "+agora():"Não foi possível salvar no navegador: baixe o arquivo."}
function exportar(){const[f,t]=totais();return{versao:"adjudicacao-1.0",fase:"B",dataset_id:D.dataset_id,avaliador:S.avaliador,exportado_em:new Date().toISOString(),completo:f===t,itens:S.itens}}
function slug(){return (S.avaliador||"avaliador").normalize("NFD").replace(/[^\w]+/g,"_").replace(/^_|_$/g,"").toLowerCase()||"avaliador"}
function render(){const[f,t]=totais();$("#prog").style.width=(100*f/t)+"%";$("#progtxt").textContent=f+" de "+t+" pareceres";
 const p=D.pareceres[S.item],g=D.grupos[p.grupo],a=S.itens[p.codigo]||{};
 const lista=D.pareceres.map((x,k)=>'<button data-item="'+k+'" class="'+(feito(x)?"feito":"")+'" '+(k===S.item?'aria-current="true"':"")+">"+x.codigo+(feito(x)?" ✓":"")+"</button>").join("");
 const falhas=p.falhas.map(x=>'<div class="critica"><b>'+esc(x.id)+"</b> · "+esc((D.rubrica[x.criterio]||{rotulo:x.criterio}).rotulo)+" · "+esc(ROT_COMP[x.componente]||x.componente)+" · gravidade "+esc(ROT_GRAV[x.gravidade]||x.gravidade)+"<br>"+esc(x.descricao)+"</div>").join("")||"<i>O parecer não apontou nenhuma falha.</i>";
 const opFalha=[["nenhuma","Nenhuma"]].concat(p.falhas.map(x=>[x.id,x.id]));
 let perguntas;
 if(g.tipo==="defeito")perguntas='<div class="q"><b>1. O parecer identificou o defeito inserido?</b>'+radios("deteccao",[["plena","Sim, claramente"],["parcial","Em parte"],["nao","Não identificou"]],a.deteccao,'data-campo="deteccao"')+'</div><div class="q"><b>2. Qual falha corresponde ao defeito?</b>'+radios("falha",opFalha,a.falha_correspondente,'data-campo="falha_correspondente"')+'</div><div class="q"><b>3. O componente apontado nessa falha é o responsável pelo defeito?</b>'+radios("comp",[["sim","Sim"],["nao","Não"],["nao_aplica","Não identificou o defeito"]],a.componente_correto,'data-campo="componente_correto"')+"</div>";
 else perguntas='<div class="q"><b>1. O parecer criticou a reformulação do objetivo geral como se ela fosse um problema?</b>'+radios("reagiu",[["sim","Sim"],["nao","Não"],["em_parte","Em parte"]],a.reagiu,'data-campo="reagiu"')+'</div><div class="q"><b>2. Se sim, qual falha?</b>'+radios("falha",opFalha,a.falha_correspondente,'data-campo="falha_correspondente"')+"</div>";
 $("#conteudo").innerHTML='<div class="aviso"><b>Fase B — informada.</b> Agora você sabe o que foi alterado no plano. Só faça depois de terminar a Fase A (ela é cega). Responda pelo <b>sentido</b> do texto do Juiz, não só pelo código do item citado.</div><div class="lista">'+lista+'</div><div class="cols"><div class="painel"><h3 style="margin-top:0">Parecer '+p.codigo+" — "+esc(g.numero)+" · "+esc(g.titulo)+"</h3><p>"+esc(g.descricao)+"</p><p><small>Campo alterado: <code>"+esc(g.campo)+"</code></small></p><details open><summary>Antes → depois</summary><p><b>Original:</b> "+esc(g.valor_original)+"</p><p><b>Variante:</b> "+esc(g.valor_novo)+"</p></details><h4>Falhas apontadas pelo Juiz neste parecer</h4>"+falhas+'<details><summary>Ver o plano completo desta variante</summary><div class="plano">'+renderPlano(g.plano,g.entrada)+'</div></details></div><div class="painel">'+perguntas+'<div class="q"><b>Comentário (opcional)</b><textarea data-icom="1">'+esc(a.comentario||"")+'</textarea></div><div class="nav"><button id="ant" '+(S.item===0?"disabled":"")+'>← Anterior</button><button id="prox" class="pri" '+(S.item===D.pareceres.length-1?"disabled":"")+">Próximo →</button></div></div></div>"}
document.addEventListener("change",e=>{const t=e.target;if(!(t instanceof HTMLInputElement)||t.type!=="radio"||!t.dataset.campo)return;const p=D.pareceres[S.item];(S.itens[p.codigo]=S.itens[p.codigo]||{})[t.dataset.campo]=t.value;salvar();render();const n=$('input[name="'+t.name+'"]:checked');if(n)n.focus()});
document.addEventListener("input",e=>{const t=e.target;if(t.dataset&&t.dataset.icom){const p=D.pareceres[S.item];(S.itens[p.codigo]=S.itens[p.codigo]||{}).comentario=t.value;salvar()}if(t.id==="nome"){S.avaliador=t.value;salvar()}});
document.addEventListener("click",e=>{const b=e.target.closest("button");if(!b)return;
 if(b.dataset.item){S.item=+b.dataset.item;salvar();render();window.scrollTo(0,0)}else if(b.id==="ant"&&S.item>0){S.item--;salvar();render();window.scrollTo(0,0)}else if(b.id==="prox"&&S.item<D.pareceres.length-1){S.item++;salvar();render();window.scrollTo(0,0)}
 else if(b.id==="baixar")baixar("adjudicacao_B_"+slug()+".json",JSON.stringify(exportar(),null,1),"application/json");
 else if(b.id==="csv"){const L=[["tipo","codigo","campo","valor"]];D.pareceres.forEach(p=>{const a=S.itens[p.codigo]||{};["deteccao","reagiu","falha_correspondente","componente_correto","comentario"].forEach(c=>L.push(["parecer",p.codigo,c,a[c]||""]))});baixar("adjudicacao_B_"+slug()+".csv",csv(L),"text/csv")}
 else if(b.id==="limpar"&&confirm("Apagar TODAS as respostas deste navegador?")){S={avaliador:"",itens:{},item:0};try{localStorage.removeItem(CHAVE)}catch(x){}$("#nome").value="";render()}});
$("#abrir").addEventListener("change",e=>{const f=e.target.files[0];if(!f)return;const r=new FileReader();r.onload=()=>{try{const j=JSON.parse(r.result);if(j.dataset_id!==D.dataset_id||j.fase!=="B")throw new Error("Este arquivo é de outra versão da adjudicação.");S.avaliador=j.avaliador||"";S.itens=j.itens||{};$("#nome").value=S.avaliador;salvar();render()}catch(x){alert("Não consegui carregar: "+x.message)}};r.readAsText(f)});
$("#nome").value=S.avaliador;render();
"""

PAGINA_C = r"""
const D=DATA;const E=[null,null];const CRIT=Object.keys(D.A.rubrica);
function lerArq(i,f){const r=new FileReader();r.onload=()=>{try{E[i]=JSON.parse(r.result)}catch(x){E[i]=null;alert("Arquivo "+(i+1)+" não é JSON válido.")}$("#nome"+i).textContent=E[i]?(E[i].avaliador||"(sem nome)")+" — fase "+E[i].fase+(E[i].completo?"":" — INCOMPLETO"):"";calcular()};r.readAsText(f)}
$("#f0").addEventListener("change",e=>e.target.files[0]&&lerArq(0,e.target.files[0]));$("#f1").addEventListener("change",e=>e.target.files[0]&&lerArq(1,e.target.files[0]));
const fmt=v=>v==null?"n/d":v.toFixed(2);const pct=v=>v==null?"n/d":Math.round(100*v)+"%";
function comparar(e1,e2){const out={campos:{},div:[],notas:null};
 const campos=e1.fase==="A"?["procedencia","gravidade","componente_correto"]:[...new Set(Object.values(e1.itens||{}).flatMap(o=>Object.keys(o)).filter(c=>c!=="comentario"))];
 campos.forEach(c=>{const a=[],b=[],ids=[];Object.keys(e1.itens||{}).filter(k=>(e2.itens||{})[k]).sort().forEach(k=>{const x=e1.itens[k][c],y=e2.itens[k][c];if(x!=null&&y!=null){a.push(x);b.push(y);ids.push(k)}});
  out.campos[c]={n:a.length,conc:a.length?a.filter((x,i)=>x===b[i]).length/a.length:null,kappa:kappaNominal(a,b)};ids.forEach((k,i)=>{if(a[i]!==b[i])out.div.push({tipo:"item",codigo:k,campo:c,v1:a[i],v2:b[i]})})});
 if(e1.fase==="A"){const a=[],b=[],onde=[];Object.keys(e1.notas_proprias||{}).filter(p=>(e2.notas_proprias||{})[p]).sort().forEach(p=>CRIT.forEach(c=>{const x=e1.notas_proprias[p][c],y=e2.notas_proprias[p][c];if(Number.isInteger(x)&&Number.isInteger(y)){a.push(x);b.push(y);onde.push([p,c])}}));
  out.notas={n:a.length,conc:a.length?a.filter((x,i)=>x===b[i]).length/a.length:null,d1:a.length?a.filter((x,i)=>Math.abs(x-b[i])<=1).length/a.length:null,k:kappaPonderado(a,b,4),dif1:[]};
  onde.forEach(([p,c],i)=>{const d=Math.abs(a[i]-b[i]);if(d>=2)out.div.push({tipo:"nota",codigo:p,campo:c,v1:a[i],v2:b[i]});else if(d===1)out.notas.dif1.push({codigo:p,campo:c,v1:a[i],v2:b[i]})})}
 return out}
let RES=null,CONS={};
function textoItem(d){if(d.tipo==="nota")return"Plano "+d.codigo+" — "+((D.A.rubrica[d.campo]||{}).rotulo||d.campo);
 if(E[0].fase==="A"){const I=D.A.itens.find(i=>i.codigo===d.codigo);return I?"Crítica "+d.codigo+" (Plano "+I.plano+"): "+I.descricao:d.codigo}
 const p=D.B.pareceres.find(x=>x.codigo===d.codigo);return p?"Parecer "+d.codigo+" — "+D.B.grupos[p.grupo].numero:d.codigo}
function comentarios(d){if(d.tipo!=="item")return"";const c=[0,1].map(i=>((E[i].itens||{})[d.codigo]||{}).comentario).map((t,i)=>t?"<small><b>"+esc(E[i].avaliador||"Av."+(i+1))+":</b> "+esc(t)+"</small>":"").filter(Boolean);return c.join("<br>")}
function calcular(){const sai=$("#saida");if(!E[0]||!E[1]){sai.innerHTML="";return}
 if(E[0].dataset_id!==E[1].dataset_id||E[0].fase!==E[1].fase){sai.innerHTML='<div class="aviso">Os dois arquivos não são da mesma fase/versão da adjudicação. Compare apenas arquivos gerados pela mesma página.</div>';return}
 const ok=(E[0].fase==="A"?D.A:D.B).dataset_id===E[0].dataset_id;if(!ok){sai.innerHTML='<div class="aviso">Estes arquivos vêm de outra versão da adjudicação (dataset diferente do embutido nesta página).</div>';return}
 RES=comparar(E[0],E[1]);const inc=[0,1].filter(i=>!E[i].completo).map(i=>E[i].avaliador||"Avaliador "+(i+1));
 let h=inc.length?'<div class="aviso">Atenção: arquivo(s) incompleto(s): '+inc.map(esc).join(", ")+". Os números abaixo usam só os itens respondidos pelos dois.</div>":"";
 h+='<div class="cards">'+Object.entries(RES.campos).map(([c,d])=>'<div class="painel"><small>'+esc(c)+'</small><b>'+pct(d.conc)+'</b>concordância ('+d.n+' itens)<br>kappa: <b style="display:inline;font-size:1rem">'+fmt(d.kappa)+"</b></div>").join("");
 if(RES.notas)h+='<div class="painel"><small>notas próprias (0–3)</small><b>'+pct(RES.notas.conc)+'</b>exatas ('+RES.notas.n+' notas)<br>dentro de ±1: '+pct(RES.notas.d1)+'<br>kappa ponderado: <b style="display:inline;font-size:1rem">'+fmt(RES.notas.k)+"</b></div>";
 h+='</div><p class="mut"><small>n pequeno: o kappa varia muito com poucos itens. Se quase tudo cai numa categoria, o kappa fica baixo mesmo com concordância alta (paradoxo da prevalência) — use as duas medidas e leia os desacordos. Notas que diferem por 1 ponto não entram no consenso: '+(RES.notas?RES.notas.dif1.length:0)+" caso(s).</small></p>";
 h+="<h2>Divergências para consenso ("+RES.div.length+")</h2>";
 if(!RES.div.length)h+="<p>Nenhuma divergência.</p>";else h+='<table><thead><tr><th>Item</th><th>Campo</th><th>'+esc(E[0].avaliador||"Av.1")+"</th><th>"+esc(E[1].avaliador||"Av.2")+'</th><th>Consenso</th><th>Justificativa</th></tr></thead><tbody>'+RES.div.map((d,i)=>{const o=[...new Set([String(d.v1),String(d.v2)])];return'<tr><td>'+esc(textoItem(d))+"<br>"+comentarios(d)+"</td><td>"+esc(d.campo)+"</td><td>"+esc(d.v1)+"</td><td>"+esc(d.v2)+'</td><td><select data-c="'+i+'"><option value="">—</option>'+o.map(v=>"<option>"+esc(v)+"</option>").join("")+'<option value="sem_consenso">sem consenso (3ª opinião)</option></select></td><td><input data-j="'+i+'" style="width:100%"></td></tr>'}).join("")+"</tbody></table>";
 h+='<p><button class="pri" id="exp">Baixar consenso (JSON)</button> <button id="expcsv">Baixar divergências (CSV)</button></p>';sai.innerHTML=h;CONS={}}
document.addEventListener("change",e=>{if(e.target.dataset&&e.target.dataset.c!=null){(CONS[e.target.dataset.c]=CONS[e.target.dataset.c]||{}).valor=e.target.value}});
document.addEventListener("input",e=>{if(e.target.dataset&&e.target.dataset.j!=null){(CONS[e.target.dataset.j]=CONS[e.target.dataset.j]||{}).just=e.target.value}});
document.addEventListener("click",e=>{const b=e.target.closest("button");if(!b||!RES)return;
 if(b.id==="exp"){const itens={},notas={};
  Object.keys(E[0].itens||{}).forEach(k=>{if(!(E[1].itens||{})[k])return;itens[k]={};Object.keys(E[0].itens[k]).filter(c=>c!=="comentario").forEach(c=>{const x=E[0].itens[k][c],y=E[1].itens[k][c];if(x===y)itens[k][c]={valor:x,origem:"acordo"}})});
  RES.div.forEach((d,i)=>{const c=CONS[i]||{};const dest=d.tipo==="item"?(itens[d.codigo]=itens[d.codigo]||{}):(notas[d.codigo]=notas[d.codigo]||{});dest[d.campo]={valor:c.valor||null,origem:c.valor?(c.valor==="sem_consenso"?"sem_consenso":"consenso"):"pendente",justificativa:c.just||"",avaliador1:d.v1,avaliador2:d.v2}});
  baixar("adjudicacao_"+E[0].fase+"_consenso.json",JSON.stringify({versao:"adjudicacao-1.0",fase:E[0].fase,dataset_id:E[0].dataset_id,avaliadores:[E[0].avaliador,E[1].avaliador],gerado_em:new Date().toISOString(),concordancia:RES.campos,notas_proprias:RES.notas,itens,notas_divergentes:notas},null,1),"application/json")}
 else if(b.id==="expcsv"){baixar("divergencias_"+E[0].fase+".csv",csv([["tipo","codigo","campo","avaliador1","avaliador2","consenso","justificativa"]].concat(RES.div.map((d,i)=>[d.tipo,d.codigo,d.campo,d.v1,d.v2,(CONS[i]||{}).valor||"",(CONS[i]||{}).just||""]))),"text/csv")}});
"""

CABECALHO_AB = (
    '<header><h1>__TITULO__</h1><input id="nome" placeholder="Seu nome" aria-label="Seu nome" size="16">'
    '<div class="barra" aria-hidden="true"><i id="prog" style="width:0"></i></div><span id="progtxt" class="mut"></span>'
    '<span id="salvo" class="mut" role="status"></span>'
    '<button id="baixar" class="pri">Baixar meu arquivo (JSON)</button><button id="csv">CSV</button>'
    '<label class="mut" style="cursor:pointer">Carregar arquivo salvo <input id="abrir" type="file" accept=".json" hidden></label>'
    '<button id="limpar" title="Apaga o progresso salvo neste navegador">Recomeçar</button></header>'
)

PAGINA_HTML_AB = (
    '<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
    '<title>__TITULO__</title><style>__CSS__</style></head><body>' + CABECALHO_AB +
    '<main>__ABAS__<div id="conteudo"></div></main><script>const DATA=__DATA__;\n__COMUM__\n__JS__</script></body></html>'
)

PAGINA_HTML_C = (
    '<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
    '<title>Adjudicação — comparar avaliadores</title><style>__CSS__</style></head><body>'
    '<header><h1>Comparar avaliadores</h1><span class="mut">Abra aqui os dois arquivos .json exportados (mesma fase)</span></header>'
    '<main><div class="cards"><div class="painel"><b>Avaliador 1</b><input id="f0" type="file" accept=".json" aria-label="Arquivo do avaliador 1"><br><small id="nome0"></small></div>'
    '<div class="painel"><b>Avaliador 2</b><input id="f1" type="file" accept=".json" aria-label="Arquivo do avaliador 2"><br><small id="nome1"></small></div></div>'
    '<div id="saida"></div></main><script>const DATA=__DATA__;\n__COMUM__\n__JS__</script></body></html>'
)

INSTRUCOES_A = (
    '<details class="painel" style="margin-bottom:12px"><summary>Leia antes de começar (1 minuto)</summary>'
    '<ul><li>Você vai avaliar <b>5 planos de aula</b> de Computação (8º ano, ordenação com cartões) e <b>as críticas que uma IA ("Juiz") fez a eles</b>. '
    'Leva de 60 a 90 minutos e você pode parar e voltar: o progresso fica salvo neste navegador.</li>'
    '<li><b>Etapa 1:</b> leia cada plano e dê a <b>sua</b> nota de 0 a 3 em 6 critérios. Ainda sem ver nenhuma crítica.</li>'
    '<li><b>Etapa 2:</b> para cada crítica da IA, diga se ela procede, se a gravidade está certa e se o componente apontado é o responsável.</li>'
    '<li>Não existe resposta certa; queremos a <b>sua opinião independente</b>. Não converse com o outro avaliador até os dois terminarem.</li>'
    '<li>No final clique em <b>"Baixar meu arquivo (JSON)"</b> e envie o arquivo para quem organizou. Use o mesmo navegador e o mesmo computador até terminar.</li></ul></details>')
ABAS_A = INSTRUCOES_A + ('<div class="abas" role="tablist"><button role="tab" data-aba="1" aria-selected="true">Etapa 1 — Sua leitura dos planos</button>'
          '<button role="tab" data-aba="2" id="aba2" aria-selected="false">Etapa 2 — Críticas do Juiz</button></div>')
