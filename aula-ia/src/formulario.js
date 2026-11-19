// Regras do formulário de contexto, sem React, para poderem ser testadas em Node (tests/test-formulario.mjs).

export const LIMITE_TEMA = 80; // o backend aceita até 800 e extrai o tema curto; o campo orienta o professor a ser breve
export const RECURSOS = ["quadro e pincel", "projetor", "computadores", "celulares", "internet", "material impresso"];
export const RECURSO_OUTRO = "outro";
export const RECURSO_PADRAO_TEORICA = "quadro e pincel";
export const MENSAGEM_SEM_RECURSOS = "Marque pelo menos um recurso disponível (ou descreva em “Outro”).";
export const MENSAGEM_SEM_RESULTADOS = "Não encontramos habilidade da BNCC de Computação para este tema. Tente outro termo.";

/** JSON e detalhes técnicos só aparecem com ?depuracao=1 na URL. */
export function modoDepuracao(search) {
  return new URLSearchParams(search || "").get("depuracao") === "1";
}

/** Recursos marcados (+ texto de "Outro") -> a string que o backend recebe. Vazia quando nada foi informado. */
export function montarRecursos(marcados, outro) {
  const itens = RECURSOS.filter(r => marcados.includes(r));
  const extra = marcados.includes(RECURSO_OUTRO) ? (outro || "").trim() : "";
  if (extra) itens.push(extra);
  return itens.join(", ");
}

/** String salva (consulta restaurada) -> {marcados, outro}. O que não é item da lista vai para "Outro". */
export function lerRecursos(texto) {
  const partes = String(texto || "").split(",").map(p => p.trim()).filter(Boolean);
  const marcados = [], extras = [];
  for (const parte of partes) {
    const item = RECURSOS.find(r => r === parte.toLocaleLowerCase("pt-BR"));
    if (item) { if (!marcados.includes(item)) marcados.push(item); } else extras.push(parte);
  }
  if (extras.length) marcados.push(RECURSO_OUTRO);
  return { marcados, outro: extras.join(", ") };
}

/** Ao escolher "Aula teórica", "quadro e pincel" fica marcado (sem desmarcar o resto). Outros tipos não mudam nada. */
export function aplicarTipo(tipo, marcados) {
  if (tipo === "Aula teórica" && !marcados.includes(RECURSO_PADRAO_TEORICA)) return [RECURSO_PADRAO_TEORICA, ...marcados];
  return marcados;
}

/** Erro 422 da consulta é sobre o tema (não identificado/inválido): mostrar junto ao campo, não no topo. */
export function erroEhDoTema(erro) {
  return erro?.status === 422 && /tema/i.test(erro.message || "");
}
