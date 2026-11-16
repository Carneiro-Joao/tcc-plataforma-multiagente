"""PlanoDeAula 2.0: esquema fechado, vínculos e integração sem coerção.

Valida somente o subconjunto usado no schema versionado do projeto; não é um
interpretador geral de JSON Schema. Sem biblioteca externa ou chamada de API.
"""
from copy import deepcopy
import json
from pathlib import Path
import re
from contratos.execucao import exigir_sem_erros

VERSAO = 'plano-aula-2.0'
SCHEMA = json.loads((Path(__file__).parent / 'plano_v2.schema.json').read_text(encoding='utf-8'))
ETAPAS = ('objetivos', 'avaliacao_preliminar', 'metodologia', 'sequencia', 'avaliacao_final', 'adaptacao')
DEPENDENCIAS = {
    'objetivos': (),
    'avaliacao_preliminar': ('objetivos',),
    'metodologia': ('objetivos', 'avaliacao_preliminar'),
    'sequencia': ('objetivos', 'avaliacao_preliminar', 'metodologia'),
    'avaliacao_final': ('objetivos', 'avaliacao_preliminar', 'metodologia', 'sequencia'),
    'adaptacao': ('objetivos', 'avaliacao_preliminar', 'metodologia', 'sequencia', 'avaliacao_final'),
}


def esquema(nome):
    return deepcopy(SCHEMA['$defs'][nome])


def _erro(erros, caminho, regra, **detalhe):
    erros.append(dict(caminho=caminho or '$', regra=regra, **detalhe))


def _estrutura(valor, s, caminho, erros):
    tipo = s['type']
    correto = {'object': isinstance(valor, dict), 'array': isinstance(valor, list),
               'string': isinstance(valor, str), 'integer': type(valor) is int}[tipo]
    if not correto:
        _erro(erros, caminho, 'tipo_invalido', esperado=tipo, recebido=type(valor).__name__)
        return
    if tipo == 'object':
        for k in s['required']:
            if k not in valor: _erro(erros, f'{caminho}/{k}', 'campo_ausente')
        for k, v in valor.items():
            if k not in s['properties']: _erro(erros, f'{caminho}/{k}', 'campo_extra')
            else: _estrutura(v, s['properties'][k], f'{caminho}/{k}', erros)
    elif tipo == 'array':
        if not s.get('minItems', 0) <= len(valor) <= s.get('maxItems', float('inf')):
            _erro(erros, caminho, 'quantidade_invalida')
        if s.get('uniqueItems') and any(v in valor[:i] for i, v in enumerate(valor)):
            _erro(erros, caminho, 'item_duplicado')
        for i, v in enumerate(valor): _estrutura(v, s['items'], f'{caminho}/{i}', erros)
    elif tipo == 'string':
        if not valor.strip(): _erro(erros, caminho, 'texto_vazio')
        elif 'pattern' in s and not re.search(s['pattern'], valor): _erro(erros, caminho, 'formato_invalido')
        if len(valor) < s.get('minLength', 0): _erro(erros, caminho, 'comprimento_invalido')
    elif tipo == 'integer' and not s.get('minimum', float('-inf')) <= valor <= s.get('maximum', float('inf')):
        _erro(erros, caminho, 'limite_invalido')
    if 'enum' in s and valor not in s['enum']: _erro(erros, caminho, 'valor_invalido')


def validar_entrada(entrada):
    erros = []
    if not isinstance(entrada, dict):
        exigir_sem_erros([{'caminho':'$', 'regra':'entrada_invalida'}], 'Entrada inválida')
    c, h = entrada.get('contexto'), entrada.get('habilidade')
    if not isinstance(c, dict) or not isinstance(h, dict):
        exigir_sem_erros([{'caminho':'$', 'regra':'contexto_ou_habilidade_ausente'}], 'Entrada inválida')
    for k in ('ano','tema','tipo','recursos'):
        if not isinstance(c.get(k), str) or not c[k].strip(): _erro(erros, 'contexto/'+k, 'texto_vazio')
    if type(c.get('duracao_min')) is not int or not 1 <= c['duracao_min'] <= 1440:
        _erro(erros, 'contexto/duracao_min', 'duracao_invalida')
    for k in ('codigo','habilidade','eixo','objeto_conhecimento'):
        if not isinstance(h.get(k), str) or not h[k].strip(): _erro(erros, 'habilidade/'+k, 'texto_vazio')
    _estrutura(h.get('referencia'), SCHEMA['$defs']['plano']['properties']['habilidade_bncc']['properties']['referencia'], 'habilidade/referencia', erros)
    exigir_sem_erros(erros, 'Entrada confirmada incompatível com PlanoDeAula 2.0; faça uma nova consulta curricular')


def _ids(itens, caminho, erros):
    mapa = {}
    for i, item in enumerate(itens):
        if item['id'] in mapa: _erro(erros, f'{caminho}/{i}/id', 'id_duplicado')
        mapa[item['id']] = item
    return mapa


def _referencias(ids, disponiveis, caminho, erros):
    for i, id_ in enumerate(ids):
        if id_ not in disponiveis: _erro(erros, f'{caminho}/{i}', 'referencia_inexistente', recebido=id_)


def _cobertura(necessarios, usados, caminho, erros):
    for id_ in sorted(set(necessarios) - set(usados)):
        _erro(erros, caminho, 'cobertura_incompleta', recebido=id_)


def _evidencias(itens, objetivos, erros):
    ev = _ids(itens, 'evidencias', erros)
    for i, e in enumerate(itens):
        _referencias([e['objetivo_id']], objetivos, f'evidencias/{i}/objetivo_id', erros)
    _cobertura(objetivos, [e['objetivo_id'] for e in itens], 'evidencias', erros)
    return ev


def _sequencia(etapas, objetivos, evidencias, duracao, erros):
    mapa = _ids(etapas, 'etapas', erros)
    if sum(e['minutos'] for e in etapas) != duracao:
        _erro(erros, 'etapas', 'soma_duracao', esperado=duracao, recebido=sum(e['minutos'] for e in etapas))
    for i, e in enumerate(etapas):
        _referencias(e['objetivos_ids'], objetivos, f'etapas/{i}/objetivos_ids', erros)
        _referencias(e['evidencias_ids'], evidencias, f'etapas/{i}/evidencias_ids', erros)
        vinculados = {evidencias[id_]['objetivo_id'] for id_ in e['evidencias_ids'] if id_ in evidencias}
        if set(e['objetivos_ids']) != vinculados:
            _erro(erros, f'etapas/{i}', 'vinculo_objetivo_evidencia_incoerente')
    _cobertura(objetivos, [o for e in etapas for o in e['objetivos_ids']], 'etapas/objetivos_ids', erros)
    _cobertura(evidencias, [v for e in etapas for v in e['evidencias_ids']], 'etapas/evidencias_ids', erros)
    return mapa


def _instrumentos(itens, etapas, evidencias, erros):
    _ids(itens, 'instrumentos', erros)
    for i, item in enumerate(itens):
        _referencias(item['etapas_ids'], etapas, f'instrumentos/{i}/etapas_ids', erros)
        _referencias(item['evidencias_ids'], evidencias, f'instrumentos/{i}/evidencias_ids', erros)
        ligados = {v for id_ in item['etapas_ids'] if id_ in etapas for v in etapas[id_]['evidencias_ids']}
        if not set(item['evidencias_ids']) <= ligados:
            _erro(erros, f'instrumentos/{i}', 'evidencia_fora_das_etapas')
        for id_ in item['etapas_ids']:
            if id_ in etapas and not set(etapas[id_]['evidencias_ids']) & set(item['evidencias_ids']):
                _erro(erros, f'instrumentos/{i}/etapas_ids', 'etapa_sem_evidencia_do_instrumento', recebido=id_)
    _cobertura(evidencias, [v for i in itens for v in i['evidencias_ids']], 'instrumentos', erros)


def _adaptacoes(itens, objetivos, etapas, erros):
    _ids(itens, 'adaptacoes', erros)
    for i, a in enumerate(itens):
        _referencias(a['objetivos_ids'], objetivos, f'adaptacoes/{i}/objetivos_ids', erros)
        _referencias(a['etapas_ids'], etapas, f'adaptacoes/{i}/etapas_ids', erros)
        ligados = {v for id_ in a['etapas_ids'] if id_ in etapas for v in etapas[id_]['objetivos_ids']}
        if not set(a['objetivos_ids']) <= ligados:
            _erro(erros, f'adaptacoes/{i}', 'objetivo_fora_das_etapas')


def identificacao(entrada):
    c = entrada['contexto']
    return dict(titulo=f"Plano de aula — {c['tema']}", componente='Computação',
                **{k:c[k] for k in ('ano','tema','tipo','duracao_min')})


def habilidade_bncc(entrada):
    h = entrada['habilidade']
    return dict(codigo=h['codigo'], descricao=h['habilidade'], eixo=h['eixo'],
                objeto_conhecimento=h['objeto_conhecimento'], referencia=deepcopy(h['referencia']))


def referencias(entrada):
    r = entrada['habilidade']['referencia']
    return [dict(id='BNCC', titulo=r['documento'], arquivo=r['arquivo'],
                 paginas=list(dict.fromkeys([r['pagina_habilidade'], r['pagina_exemplos']])),
                 versao_catalogo=r['versao_catalogo'], sha256_catalogo=r['sha256_catalogo'])]


def diagnosticar(nome, saida, entrada, estado=None):
    if nome not in SCHEMA['$defs']: raise ValueError('Contrato desconhecido: '+nome)
    erros = []
    _estrutura(saida, SCHEMA['$defs'][nome], '', erros)
    if erros: return erros
    c = entrada['contexto']
    estado = estado or {}
    if nome == 'plano':
        fontes = dict(identificacao=identificacao(entrada), habilidade_bncc=habilidade_bncc(entrada),
                      referencias=referencias(entrada), recursos=c['recursos'])
        for k, v in fontes.items():
            if saida[k] != v: _erro(erros, k, 'entrada_preservada')
        objs = _ids(saida['objetivos_especificos'], 'objetivos_especificos', erros)
        ev = _evidencias(saida['avaliacao_aprendizagem']['evidencias'], objs, erros)
        etapas = _sequencia(saida['desenvolvimento'], objs, ev, c['duracao_min'], erros)
        _instrumentos(saida['avaliacao_aprendizagem']['instrumentos'], etapas, ev, erros)
        _adaptacoes(saida['adaptacoes'], objs, etapas, erros)
        return erros
    if nome == 'objetivos':
        _ids(saida['objetivos_especificos'], 'objetivos_especificos', erros)
        return erros
    # Dependências devem existir e já ter sido validadas; nunca presumir saída ausente.
    for dep in DEPENDENCIAS[nome]:
        if dep not in estado: _erro(erros, 'dependencias/'+dep, 'dependencia_ausente')
    if erros: return erros
    objs = {o['id']:o for o in estado['objetivos']['objetivos_especificos']}
    if nome == 'avaliacao_preliminar': _evidencias(saida['evidencias'], objs, erros)
    elif nome == 'metodologia':
        if saida['recursos'] != c['recursos']: _erro(erros, 'recursos', 'recursos_confirmados')
    else:
        ev = {e['id']:e for e in estado['avaliacao_preliminar']['evidencias']}
        if nome == 'sequencia': _sequencia(saida['etapas'], objs, ev, c['duracao_min'], erros)
        else:
            etapas = {e['id']:e for e in estado['sequencia']['etapas']}
            if nome == 'avaliacao_final': _instrumentos(saida['instrumentos'], etapas, ev, erros)
            elif nome == 'adaptacao': _adaptacoes(saida['adaptacoes'], objs, etapas, erros)
    return erros


def validar(nome, saida, entrada, estado=None):
    exigir_sem_erros(diagnosticar(nome, saida, entrada, estado), f'Contrato 2.0 {nome} inválido')


def integrar(entrada, estado):
    validar_entrada(entrada)
    for nome in ETAPAS:
        if nome not in estado:
            exigir_sem_erros([{'caminho':nome,'regra':'dependencia_ausente'}], 'Integração incompleta')
        validar(nome, estado[nome], entrada, estado)
    plano = dict(
        identificacao=identificacao(entrada), habilidade_bncc=habilidade_bncc(entrada),
        conteudos=deepcopy(estado['objetivos']['conteudos']), objetivo_geral=estado['objetivos']['objetivo_geral'],
        objetivos_especificos=deepcopy(estado['objetivos']['objetivos_especificos']),
        metodologia=estado['metodologia']['metodologia'], recursos=entrada['contexto']['recursos'],
        desenvolvimento=deepcopy(estado['sequencia']['etapas']),
        avaliacao_aprendizagem=dict(evidencias=deepcopy(estado['avaliacao_preliminar']['evidencias']),
                                   instrumentos=deepcopy(estado['avaliacao_final']['instrumentos']),
                                   uso_resultados=estado['avaliacao_final']['uso_resultados']),
        adaptacoes=deepcopy(estado['adaptacao']['adaptacoes']), referencias=referencias(entrada))
    validar('plano', plano, entrada)
    return plano
