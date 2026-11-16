"""Revalida um JSON de teste_gemini.py sem rede, chave ou nova chamada à API.

Uso: python inspecionar_gemini.py local/teste_gemini/ARQUIVO.json
A análise verifica o arquivo recebido; não autentica a origem de um log editável.
"""
import argparse
from copy import deepcopy
import json
from pathlib import Path
from contratos import plano_v2
from contratos.execucao import ler_json, integrar as integrar_legado, VERSAO as VERSAO_LEGADO
from contratos.validacao import validar as diagnosticar_legado
from erros import ErroGeracao
from geracao import GeradorDePlano


def inspecionar(documento):
    versao = documento.get('versao')
    if versao not in (plano_v2.VERSAO, VERSAO_LEGADO):
        raise ValueError('Versão de contrato desconhecida: '+str(versao))
    completo = versao == plano_v2.VERSAO
    ordem = plano_v2.ETAPAS if completo else GeradorDePlano.ESPECIALISTAS
    entrada = documento['entrada']
    if completo: plano_v2.validar_entrada(entrada)
    resumo = {'contrato':versao,'modo_declarado':documento.get('modo'),
              'observacao':'Análise local do registro; não autentica sua origem nem avalia qualidade pedagógica.',
              'rodadas':[]}
    for rodada in documento['rodadas']:
        estado, avaliacoes, uso = {}, [], []
        chamadas = [r for r in rodada.get('rastreio',[]) if r.get('provedor')=='gemini']
        for reg in rodada.get('rastreio',[]):
            nome = reg['agente']
            if nome not in ordem: continue
            diagnosticos = []
            saida = None
            if 'conteudo_bruto' in reg:
                try: saida = ler_json(reg['conteudo_bruto'])
                except ErroGeracao as erro:
                    diagnosticos = getattr(erro,'diagnosticos',[]) or [{'caminho':'$','regra':'json_invalido'}]
                if saida is not None and 'saida' in reg and saida != reg['saida']:
                    diagnosticos.append({'caminho':'saida','regra':'saida_difere_do_conteudo_bruto'})
            elif documento.get('modo')=='demonstracao':
                saida = reg.get('saida')
            if saida is None and not diagnosticos:
                diagnosticos.append({'caminho':'$','regra':'sem_conteudo_para_validar'})
            if saida is not None:
                diagnosticos += (plano_v2.diagnosticar(nome,saida,entrada,estado) if completo
                                  else diagnosticar_legado(nome,saida,entrada))
            metadados = reg.get('usage') or {}
            tokens = metadados.get('totalTokenCount') if isinstance(metadados,dict) else None
            if reg.get('provedor')=='gemini' and type(tokens) is int: uso.append(tokens)
            # Uma tentativa rejeitada nunca libera dependentes, mesmo se o arquivo for inconsistente.
            if reg.get('estado')=='validado' and not diagnosticos:
                estado[nome] = deepcopy(saida)
            avaliacoes.append({'agente':nome,'tentativa':reg.get('tentativa'),'estado_registrado':reg.get('estado'),
                'http_status':reg.get('http_status'),'modelo':reg.get('modelo_respondeu'),
                'latencia_s':reg.get('latencia_s'),'tokens':tokens,'finish_reason':reg.get('finish_reason'),
                'diagnosticos':diagnosticos})
        validacao_final = 'não há plano completo validado'
        if set(estado)==set(ordem) and isinstance(rodada.get('plano'),dict):
            try:
                recomposto = (plano_v2.integrar if completo else integrar_legado)(entrada,estado)
                validacao_final = ('válido e igual à integração das etapas' if recomposto==rodada['plano']
                                   else 'INVÁLIDO: plano difere da integração das etapas')
            except ErroGeracao:
                validacao_final = 'INVÁLIDO: integração reprovada'
        resumo['rodadas'].append({'rodada':rodada.get('rodada'),'status_registrado':rodada.get('status'),
            'chamadas_gemini_registradas':len(chamadas),'chamadas_com_usage':len(uso),
            'tokens_conhecidos':sum(uso),'tempo_total_s':rodada.get('tempo_total_s'),
            'validacao_final':validacao_final,'etapas':avaliacoes})
    return resumo


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('arquivo',type=Path)
    args = parser.parse_args(argv)
    try:
        documento = ler_json(args.arquivo.read_text(encoding='utf-8'))
        resumo = inspecionar(documento)
    except (OSError, ValueError, TypeError, KeyError, ErroGeracao) as erro:
        parser.exit(1,f'Não foi possível inspecionar o registro: {erro}\n')
    print(json.dumps(resumo,ensure_ascii=False,indent=2))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
