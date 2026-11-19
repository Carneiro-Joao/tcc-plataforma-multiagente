"""Extrai o TEMA curto do que o professor digitou ("Olá, bom dia, quero ensinar sobre ordenação" -> "Ordenação").

Sem IA e sem rede. Três camadas, da mais firme para a mais fraca:
  1. catálogo   trechos do texto que casam com o vocabulário curricular da BNCC (termos e objetos de conhecimento);
  2. marcador   o que vem depois de "o tema é", "quero ensinar sobre", "aula sobre"... até a pontuação ou uma palavra de corte;
  3. texto      o próprio texto sem saudação, só se for curto (até 80 caracteres).
Se nenhuma funcionar, levanta TemaNaoIdentificado com uma mensagem para o professor reescrever em poucas palavras.
O trecho devolvido é sempre um pedaço do texto original (nada é inventado) e mantém a grafia digitada.
"""
import re
import unicodedata

LIMITE = 80
MAX_TERMOS = 3
PALAVRAS_DE_CORTE = (r"\s+(?:para|pra|com|usando|utilizando|em|no|na|nos|nas|durante|que|pois|porque|mas|amanha|hoje|"
                     r"semana\s+que\s+vem|e\s+(?:nao|vou|quero|preciso|gostaria|tambem))\b")
CORTE = re.compile(r"[.,;:!?\n]|\s-\s|" + PALAVRAS_DE_CORTE)
MARCADORES = (
    re.compile(r"(?:tema|assunto|conteudo|topico)(?:\s+da\s+aula)?(?:\s+de\s+hoje)?\s*(?:vai\s+ser|sera|e|:|=)\s+"
               r"(?:(?:ensinar|trabalhar|explicar|abordar)\s+)?(?:sobre\s+)?"),
    re.compile(r"(?:ensinar|trabalhar|explicar|abordar|apresentar|falar|(?:aulas?|planos?|atividades?|oficinas?)(?:\s+\w+){0,2}?)\s+"
               r"(?:sobre|de|a\s+respeito\s+de|acerca\s+de)\s+(?!hoje\b)"),
    re.compile(r"o\s+que\s+(?:e|sao|significa|significam)\s+"),
    re.compile(r"(?:quero|gostaria\s+de|preciso|pretendo|vou)\s+(?:ensinar|trabalhar|explicar|abordar)\s+(?!(?:sobre|para|pra|aos?|as?|os)\b)"),
)
PALAVRAS_DE_PEDIDO = frozenset("""a o de uma um aula aulas plano planos atividade atividades oficina oficinas sobre para pra
    os as aos meus meu minha turma alunos""".split())  # palavras que descrevem o pedido, não o assunto
COM_INTENCAO = re.compile(r"\b(?:quero|gostaria|preciso|pretendo|vou|ensinar|explicar|abordar|trabalhar)\b")
ARTIGO = re.compile(r"^(?:o|a|os|as|um|uma)\s+")
SAUDACAO = re.compile(r"^(?:ola|oi|bom\s+dia|boa\s+tarde|boa\s+noite|prezad[oa]s?|e\s+ai|tudo\s+(?:bem|certo))[\s,.!?:;-]*")


class TemaNaoIdentificado(ValueError):
    pass


def normalizar_com_mapa(texto):
    """Minúsculas sem acento, com o mapa posição normalizada -> posição no texto original."""
    saida, mapa = [], []
    for i, ch in enumerate(texto):
        for c in unicodedata.normalize("NFD", ch.lower()):
            if not unicodedata.combining(c):
                saida.append(c)
                mapa.append(i)
    return "".join(saida), mapa


def _original(texto, mapa, ini, fim):
    return texto[mapa[ini]:mapa[fim - 1] + 1].strip()


def _capitalizar(t):
    for i, ch in enumerate(t):
        if ch.isalpha():
            return t[:i] + ch.upper() + t[i + 1:]
    return t


def _juntar(partes):
    return partes[0] if len(partes) == 1 else ", ".join(partes[:-1]) + " e " + partes[-1]


LIGACAO = re.compile(r"^(?:\s*,)?\s*(?:(?:e|de|da|do|das|dos|ou)\s+)?$")


def _do_catalogo(texto, n, mapa, termos):
    termos = {normalizar_com_mapa(t)[0].strip() for t in termos if t.strip()}
    achados = []
    for t in termos:
        for m in re.finditer(r"(?<![a-z0-9])" + re.escape(t) + r"s?(?![a-z0-9])", n):
            achados.append((m.start(), m.end()))
    escolhidos = []
    for ini, fim in sorted(achados, key=lambda a: (-(a[1] - a[0]), a[0])):  # mais longos primeiro
        if all(fim <= i or ini >= f for i, f in escolhidos):
            escolhidos.append((ini, fim))
    grupos = []  # termos ligados só por "de", "e", vírgula... viram um trecho único, na grafia do professor
    for ini, fim in sorted(escolhidos):
        if grupos and LIGACAO.match(n[grupos[-1][1]:ini]):
            grupos[-1] = (grupos[-1][0], fim)
        else:
            grupos.append((ini, fim))
    partes, vistos = [], set()
    for ini, fim in grupos:
        if n[ini:fim] not in vistos:
            vistos.add(n[ini:fim])
            partes.append(_original(texto, mapa, ini, fim))
    return _juntar(partes[:MAX_TERMOS]) if partes else None


def _por_marcador(texto, n, mapa):
    candidatos = []
    for padrao in MARCADORES:
        for m in padrao.finditer(n):
            candidatos.append(m.end())
    for inicio in sorted(candidatos):
        corte = CORTE.search(n, inicio)
        fim = corte.start() if corte else len(n)
        recorte = n[inicio:fim]
        artigo = ARTIGO.match(recorte)
        if artigo:
            inicio += artigo.end()
        if set(re.findall(r"[a-z0-9]+", n[inicio:fim])) <= PALAVRAS_DE_PEDIDO:
            continue  # "plano de aula", "uma aula": é o pedido, não o assunto
        if fim - inicio >= 2 and fim - inicio <= LIMITE:
            return _original(texto, mapa, inicio, fim)
    return None


def _sem_saudacao(texto):
    n, mapa = normalizar_com_mapa(texto)
    pos = 0
    while True:
        m = SAUDACAO.match(n[pos:])
        if not m or m.end() == 0:
            break
        pos += m.end()
    return texto[mapa[pos]:].strip() if pos < len(n) else ""


def extrair_tema(texto, termos=()):
    """Devolve dict(tema, origem). `termos`: vocabulário do catálogo (termos e objetos de conhecimento)."""
    if not isinstance(texto, str) or not texto.strip():
        raise TemaNaoIdentificado("Informe o tema da aula.")
    n, mapa = normalizar_com_mapa(texto)
    achado = _do_catalogo(texto, n, mapa, termos)
    origem = "catalogo"
    frase = _por_marcador(texto, n, mapa)
    if frase and (not achado or (len(frase) > len(achado) and
                                 normalizar_com_mapa(achado)[0] in normalizar_com_mapa(frase)[0])):
        achado, origem = frase, "marcador"  # a frase do professor é mais completa e contém o termo do catálogo
    if not achado:
        limpo = _sem_saudacao(texto).strip(" .,;:!?-")
        nl = normalizar_com_mapa(limpo)[0]
        so_intencao = set(re.findall(r"[a-z0-9]+", nl)) <= PALAVRAS_DE_PEDIDO
        achado, origem = (limpo if 0 < len(limpo) <= LIMITE and not so_intencao and not COM_INTENCAO.search(nl)
                          else None), "texto"
    if not achado or len(achado) > LIMITE:
        raise TemaNaoIdentificado("Não consegui identificar o tema. Escreva-o em poucas palavras, por exemplo: ordenação.")
    return dict(tema=_capitalizar(achado), origem=origem)
