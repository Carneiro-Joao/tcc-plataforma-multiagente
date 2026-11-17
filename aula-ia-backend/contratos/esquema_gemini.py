"""Projeção do contrato 2.0 para uma gramática menor na API Gemini.

Limites, unicidade e formatos continuam obrigatórios na validação local.
Aqui são orientações textuais: não multiplicam estados da geração estruturada.
"""
from copy import deepcopy
from contratos.plano_v2 import esquema

VERSAO_ESQUEMA_API = 'plano-2.0-estrutura-v1'


def projetar(schema):
    """Preserva campos, tipos e obrigatoriedade; não modifica o schema original."""
    saida = {'type': schema['type']}
    regras = []
    for chave, descricao in (
        ('minItems','Quantidade mínima de itens'), ('maxItems','Quantidade máxima de itens'),
        ('minimum','Valor mínimo'), ('maximum','Valor máximo'),
        ('minLength','Comprimento mínimo'), ('maxLength','Comprimento máximo'),
        ('pattern','Formato obrigatório (expressão regular)'),
    ):
        if chave in schema:
            regras.append(f'{descricao}: {schema[chave]}.')
    if schema.get('uniqueItems'):
        regras.append('Não repita itens nesta lista.')
    if 'enum' in schema:
        regras.append('Valores permitidos: '+', '.join(str(v) for v in schema['enum'])+'.')
    if schema.get('description'):
        regras.insert(0,schema['description'])
    if regras:
        saida['description'] = ' '.join(regras)
    if schema['type']=='object':
        saida['properties'] = {nome:projetar(s) for nome,s in schema['properties'].items()}
        saida['required'] = deepcopy(schema['required'])
        saida['additionalProperties'] = schema['additionalProperties']
    elif schema['type']=='array':
        saida['items'] = projetar(schema['items'])
    return saida


def esquema_api(nome):
    return projetar(esquema(nome))
