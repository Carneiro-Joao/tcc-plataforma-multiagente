// Painel "Avaliação da IA Juiz" e progresso do pedido (PoC 08), sem DOM: rótulos, notas, críticas, histórico, avisos e escape.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
const ler = path => readFileSync(new URL(path, import.meta.url), 'utf8');
const source = ler('../public/geracao-ui.js');
assert.equal(source, ler('../dist/geracao-ui.js'));
const context = {document:{getElementById:()=>null}, MutationObserver:class {observe(){}}, queueMicrotask:()=>{}, URLSearchParams};
vm.createContext(context);
vm.runInContext(source.replace(/\r\n/g, '\n').replace('  agendar();\n})();',
  '  globalThis.renderAvaliacao = avaliacaoHtml; globalThis.renderProgresso = progressoHtml;\n})();'), context);
const gravado = JSON.parse(ler('../../experimentos/juiz/demonstracao/parecer_controle_v13.json'));
const parecer = gravado.parecer;
const AVISO = 'Avaliação automática e provisória; a decisão final é do professor.';
const av = (status, rotulo, extra = {}) => ({status, rotulo, parecer, demonstracao: false, ...extra});

// Favorável / com ressalvas / revisão recomendada: rótulo, classe, 6 notas com o nome do critério, críticas com gravidade e componente
for (const [status, rotulo, classe] of [['aguardando_decisao', 'Favorável', 'juiz-favoravel'], ['em_correcao', 'Com ressalvas', 'juiz-ressalvas'],
                                        ['revisao_necessaria', 'Revisão recomendada', 'juiz-revisao']]) {
  const html = context.renderAvaliacao(av(status, rotulo), null, 'g1');
  assert.ok(html.includes(`juiz-painel ${classe}`), classe);
  assert.ok(html.includes(`<span class="juiz-decisao">${rotulo}</span>`), rotulo);
  assert.ok(html.includes(AVISO));
}
let html = context.renderAvaliacao(av('em_correcao', 'Com ressalvas'), null, 'g1');
for (const nome of ['Aderência curricular', 'Alinhamento dos objetivos', 'Coerência metodológica', 'Viabilidade', 'Avaliação da aprendizagem', 'Inclusão'])
  assert.ok(html.includes(`<td>${nome}</td>`), nome);
assert.equal((html.match(/<tr><td>/g) || []).length, 6);
assert.ok(html.includes('<td><b>1</b></td>'));  // nota real da avaliação da aprendizagem no parecer gravado
assert.ok(html.includes('Evidências de avaliação'));  // componente avaliacao_preliminar em linguagem simples
assert.ok(html.includes('<span class="juiz-gravidade">Maior</span>') && html.includes('<span class="juiz-gravidade">Menor</span>'));
assert.ok(html.includes(parecer.falhas[0].descricao.slice(0, 40).replace(/&/g, '&amp;').replace(/</g, '&lt;')));
assert.ok(!html.includes('Ver parecer completo (JSON)'), 'JSON do parecer só com ?depuracao=1');
context.location = {search: '?depuracao=1'};
assert.ok(context.renderAvaliacao(av('em_correcao', 'Com ressalvas'), null, 'g1').includes('Ver parecer completo (JSON)'));
delete context.location;

// Indisponível (falha técnica) e não realizada: sem notas, sem críticas, mensagem clara
html = context.renderAvaliacao({status: 'indisponivel', rotulo: 'Indisponível', erro: 'Groq HTTP 413'}, null, 'g1');
assert.ok(html.includes('juiz-indisponivel') && html.includes('Isso não é um parecer.') && !html.includes('juiz-notas'));
assert.ok(html.includes(AVISO));
html = context.renderAvaliacao({status: 'nao_realizada', rotulo: 'Avaliação não realizada'}, null, 'g1');
assert.ok(html.includes('não foi realizada') && !html.includes('Críticas do Juiz'));
assert.equal(context.renderAvaliacao(null, null, 'g1'), '');

// Histórico: versão anterior não aprovada aparece com o motivo; a própria versão entregue não
const pedido = {aviso: 'A IA Juiz não deu parecer favorável a nenhuma das 2 versões.', historico: [
  {ciclo: 0, geracao_id: 'g1', evento: 'avaliado', rotulo: 'Com ressalvas', criticas: ['ET2 simula <uma> passagem só'], motivos: ['x']},
  {ciclo: 1, geracao_id: 'g2', evento: 'avaliado', rotulo: 'Favorável', criticas: [], motivos: ['nenhuma']}]};
html = context.renderAvaliacao(av('aguardando_decisao', 'Favorável'), pedido, 'g2');
assert.ok(html.includes('1ª versão não aprovada pelo Juiz') && html.includes('ET2 simula &lt;uma&gt; passagem só'));
assert.ok(!html.includes('2ª versão não aprovada'));
assert.ok(html.includes('<p class="juiz-aviso-pedido">A IA Juiz não deu parecer favorável a nenhuma das 2 versões.</p>'));

// Demonstração: marcada como tal
html = context.renderAvaliacao(av('em_correcao', 'Com ressalvas', {demonstracao: true, aviso_demonstracao: 'Parecer real GRAVADO de outro plano'}), null, 'g1');
assert.ok(html.includes('<b>Demonstração:</b> Parecer real GRAVADO de outro plano'));

// Escape: texto do parecer nunca vira HTML
const malicioso = JSON.parse(JSON.stringify(parecer));
malicioso.falhas[0].descricao = '<img src=x onerror=alert(1)>';
html = context.renderAvaliacao(av('em_correcao', 'Com ressalvas', {parecer: malicioso}), null, 'g1');
assert.ok(!html.includes('<img') && html.includes('&lt;img'));

// Progresso: etapas visíveis e a atual marcada; regeneração aparece; aviso de até 4 minutos
html = context.renderProgresso({estado: 'gerando', ciclo: 0}, 0);
assert.ok(html.includes('<li class="atual">Gerando plano…</li>') && html.includes('<li class="">IA Juiz avaliando…</li>'));
assert.ok(html.includes('até 4 minutos') && !html.includes('Ajustando'));
html = context.renderProgresso({estado: 'avaliando', ciclo: 0}, 65);
assert.ok(html.includes('<li class="feito">Gerando plano…</li>') && html.includes('<li class="atual">IA Juiz avaliando…</li>'));
assert.ok(html.includes('Tempo decorrido: 1 min 05 s.'));
html = context.renderProgresso({estado: 'regenerando', ciclo: 1}, 0);
assert.ok(html.includes('<li class="feito">IA Juiz avaliando…</li>') && html.includes('<li class="atual">Ajustando: gerando nova versão…</li>'));
html = context.renderProgresso({estado: 'avaliando', ciclo: 1}, 0);
assert.ok(html.includes('<li class="feito">Ajustando: gerando nova versão…</li>') && html.includes('<li class="atual">IA Juiz avaliando a nova versão…</li>'));
assert.ok(context.renderProgresso(null, 0).includes('<li class="atual">Gerando plano…</li>'));
console.log('Juiz OK: rótulos, 6 notas, críticas, histórico, indisponível, demonstração, escape, progresso e public/dist iguais.');
