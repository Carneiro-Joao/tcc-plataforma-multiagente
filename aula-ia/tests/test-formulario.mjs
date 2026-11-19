// Regras do formulário (src/formulario.js): checklist de recursos, aula teórica, depuração e erro 422 do tema.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { LIMITE_TEMA, RECURSOS, RECURSO_OUTRO, MENSAGEM_SEM_RESULTADOS, modoDepuracao, montarRecursos, lerRecursos,
  aplicarTipo, erroEhDoTema } from '../src/formulario.js';

// Depuração só com ?depuracao=1
assert.equal(modoDepuracao(''), false);
assert.equal(modoDepuracao('?depuracao=0'), false);
assert.equal(modoDepuracao('?outra=1'), false);
assert.equal(modoDepuracao('?depuracao=1'), true);
assert.equal(modoDepuracao('?x=2&depuracao=1'), true);

// Recursos: obrigatório (string vazia quando nada informado), ordem fixa da lista, "Outro" só com texto
assert.deepEqual(RECURSOS, ['quadro e pincel', 'projetor', 'computadores', 'celulares', 'internet', 'material impresso']);
assert.equal(montarRecursos([], ''), '');
assert.equal(montarRecursos([RECURSO_OUTRO], '   '), '');
assert.equal(montarRecursos(['projetor', 'quadro e pincel'], ''), 'quadro e pincel, projetor');
assert.equal(montarRecursos(['internet', RECURSO_OUTRO], ' cartões numerados '), 'internet, cartões numerados');
assert.equal(montarRecursos(['celulares'], 'texto ignorado sem marcar Outro'), 'celulares');
assert.equal(typeof montarRecursos(['projetor'], ''), 'string');

// Restaurar consulta salva: ida e volta preserva a string
for (const texto of ['quadro e pincel, projetor', 'computadores, internet, cartões numerados', 'papel e cartões']) {
  const { marcados, outro } = lerRecursos(texto);
  assert.equal(montarRecursos(marcados, outro), texto, texto);
}
assert.deepEqual(lerRecursos('Projetor, papel'), { marcados: ['projetor', RECURSO_OUTRO], outro: 'papel' });
assert.deepEqual(lerRecursos(''), { marcados: [], outro: '' });

// Aula teórica pré-marca "quadro e pincel" sem desmarcar o resto; outros tipos não mexem
assert.deepEqual(aplicarTipo('Aula teórica', []), ['quadro e pincel']);
assert.deepEqual(aplicarTipo('Aula teórica', ['projetor']), ['quadro e pincel', 'projetor']);
assert.deepEqual(aplicarTipo('Aula teórica', ['quadro e pincel']), ['quadro e pincel']);
assert.deepEqual(aplicarTipo('Aula prática', ['projetor']), ['projetor']);
assert.deepEqual(aplicarTipo('Computação desplugada', []), []);

// 422 do tema vai para junto do campo; outros erros não
const erro = (status, message) => Object.assign(new Error(message), { status });
assert.equal(erroEhDoTema(erro(422, 'Não consegui identificar o tema. Escreva-o em poucas palavras, por exemplo: ordenação.')), true);
assert.equal(erroEhDoTema(erro(422, 'Informe o tema da aula.')), true);
assert.equal(erroEhDoTema(erro(422, 'Selecione um tipo de aula válido.')), false);
assert.equal(erroEhDoTema(erro(500, 'Falha no tema')), false);
assert.equal(erroEhDoTema(new Error('sem status')), false);

assert.equal(LIMITE_TEMA, 300);
// a frase longa do feedback (104 caracteres) precisa caber inteira no campo
assert.ok("Olá, eu quero ensinar sobre IA generativa. O tema da aula de hoje vai ser IA generativa. E não sei o que".length <= LIMITE_TEMA);
assert.ok(MENSAGEM_SEM_RESULTADOS.startsWith('Não encontramos habilidade da BNCC de Computação para este tema.'));

// App.jsx usa estas regras (evita regressão silenciosa para o campo antigo)
const app = readFileSync(new URL('../src/App.jsx', import.meta.url), 'utf8');
assert.ok(app.includes('placeholder="Ex.: ordenação"'));
assert.ok(app.includes('maxLength={LIMITE_TEMA}'));
assert.ok(!app.includes('name="recursos" required'), 'campo de texto livre de recursos voltou');
assert.ok(/\{DEPURACAO && <details className="json-entrada">/.test(app), 'JSON da confirmação precisa ficar atrás de DEPURACAO');
console.log('Formulário OK: depuração, recursos obrigatórios, aula teórica, erro 422 do tema.');
