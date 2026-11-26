"""Figura ilustrada "Visão geral do AulaIA" em SVG (ilustração vetorial feita à mão). Só biblioteca padrão.

Mesmo conteúdo de ../visao-geral.html (que continua guardada), em estilo de infográfico: cinco estações ligadas por um caminho,
com desenhos simples em cada uma. Uso: python visao_geral_ilustrada.py → ../visao-geral-ilustrada.svg (PNG pelo render.js).
"""
from pathlib import Path

W, H = 1800, 1000
TINTA, MUTED = "#16242b", "#4f5f67"
COR = {"hum": ("#a2561b", "#fbeee2", "#f6d9bf"), "regra": ("#5a6a72", "#f2f5f6", "#dde5e8"), "ia": ("#0f6b84", "#e3f1f5", "#bfe0ea")}


def t(x, y, s, tam=18, peso=500, cor=TINTA, anc="middle", extra=""):
    return f'<text x="{x}" y="{y}" font-size="{tam}" font-weight="{peso}" fill="{cor}" text-anchor="{anc}" {extra}>{s}</text>'


def linhas(x, y, ls, tam=17, peso=500, cor="#2c3b42", alt=1.42, anc="middle"):
    return "".join(t(x, y + i * tam * alt, l, tam, peso, cor, anc) for i, l in enumerate(ls))


# ---------- desenhos (centrados em 0,0; cabem num círculo de raio ~80) ----------
def professor_fala():
    c, bg, _ = COR["hum"]
    return (f'<g stroke="{c}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">'
            f'<circle cx="-18" cy="-6" r="22" fill="#fff"/>'
            f'<path d="M-58 62 C-56 28 -40 18 -18 18 C4 18 20 28 22 62 Z" fill="#fff"/>'
            f'<path d="M6 -62 h62 a12 12 0 0 1 12 12 v26 a12 12 0 0 1 -12 12 h-36 l-14 14 v-14 h-12 a12 12 0 0 1 -12 -12 v-26 a12 12 0 0 1 12 -12z" fill="#fff"/>'
            f'</g>'
            f'<g fill="{c}"><circle cx="24" cy="-37" r="4.5"/><circle cx="37" cy="-37" r="4.5"/><circle cx="50" cy="-37" r="4.5"/></g>')


def bncc():
    c = COR["regra"][0]
    return (f'<g stroke="{c}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" fill="#fff">'
            f'<path d="M-62 -40 C-40 -52 -18 -50 -2 -36 C14 -50 36 -52 58 -40 V40 C36 28 14 30 -2 44 C-18 30 -40 28 -62 40 Z"/>'
            f'<path d="M-2 -36 V44" fill="none"/>'
            f'<path d="M-48 -22 h30 M-48 -8 h30 M-48 6 h22 M14 -22 h30 M14 -8 h30" fill="none" stroke-width="3" opacity=".7"/>'
            f'<circle cx="34" cy="26" r="22"/><path d="M50 42 L70 62" stroke-width="7"/></g>'
            f'<path d="M24 26 l7 7 l13 -14" fill="none" stroke="#1f7a4d" stroke-width="4.5" stroke-linecap="round" stroke-linejoin="round"/>')


def robo(x, y, s=1.0, c=COR["ia"][0]):
    return (f'<g transform="translate({x} {y}) scale({s})" stroke="{c}" stroke-width="3.4" stroke-linecap="round" stroke-linejoin="round">'
            f'<line x1="0" y1="-24" x2="0" y2="-15"/><circle cx="0" cy="-27" r="3.6" fill="{c}"/>'
            f'<rect x="-17" y="-15" width="34" height="27" rx="8" fill="#fff"/>'
            f'<circle cx="-7" cy="-2" r="3.2" fill="{c}" stroke="none"/><circle cx="7" cy="-2" r="3.2" fill="{c}" stroke="none"/>'
            f'<path d="M-6 6 h12" /></g>')


def especialistas():
    c = COR["ia"][0]
    doc = (f'<g stroke="{c}" stroke-width="4" stroke-linejoin="round" fill="#fff"><path d="M-26 -34 h36 l16 16 v52 h-52 z"/>'
           f'<path d="M10 -34 v16 h16" fill="none"/></g>'
           f'<g stroke="{c}" stroke-width="3" stroke-linecap="round" opacity=".75"><path d="M-16 -10 h28 M-16 2 h32 M-16 14 h24"/></g>')
    pos = [(0, -78), (74, -26), (48, 62), (-48, 62), (-74, -26)]
    return doc + "".join(robo(x, y, 0.95) for x, y in pos)


def juiz():
    c = COR["ia"][0]
    barras = "".join(f'<rect x="{-42 + i * 14}" y="{20 - h}" width="9" height="{h}" rx="2" fill="{c}" opacity="{0.45 + i * 0.1}"/>'
                     for i, h in enumerate([18, 32, 24, 38]))
    return (f'<g stroke="{c}" stroke-width="4" stroke-linejoin="round" stroke-linecap="round">'
            f'<rect x="-52" y="-50" width="66" height="92" rx="8" fill="#fff"/>'
            f'<rect x="-34" y="-60" width="30" height="18" rx="5" fill="{COR["ia"][2]}"/></g>'
            + barras +
            f'<path d="M-42 32 h46" stroke="{c}" stroke-width="3"/>'
            f'<g transform="translate(46 -10) rotate(-38)" stroke="{TINTA}" stroke-width="4" stroke-linejoin="round" stroke-linecap="round">'
            f'<rect x="-22" y="-16" width="44" height="22" rx="6" fill="#f3c87a"/><line x1="0" y1="6" x2="0" y2="56"/></g>'
            f'<rect x="34" y="50" width="46" height="10" rx="4" fill="{TINTA}"/>')


def aprova_pdf():
    c = COR["hum"][0]
    return (f'<g stroke="{c}" stroke-width="4" stroke-linejoin="round" stroke-linecap="round">'
            f'<path d="M-46 -58 h56 l22 22 v84 h-78 z" fill="#fff"/><path d="M10 -58 v22 h22" fill="none"/>'
            f'<path d="M-32 -26 h40 M-32 -12 h48 M-32 2 h34" stroke-width="3" opacity=".7"/></g>'
            f'<rect x="-40" y="16" width="38" height="20" rx="4" fill="#c0392b"/>{t(-21, 31, "PDF", 13, 800, "#fff")}'
            f'<circle cx="38" cy="34" r="27" fill="#1f7a4d"/>'
            f'<path d="M25 34 l9 9 l17 -19" fill="none" stroke="#fff" stroke-width="5.5" stroke-linecap="round" stroke-linejoin="round"/>')


ESTACOES = [
    dict(x=180, cat="hum", tag="PROFESSOR", titulo="Diz o que quer ensinar", desenho=professor_fala,
         texto=["“Bom dia, quero ensinar", "ordenação”, mais a duração,", "o tipo de aula e os recursos", "que tem na sala."]),
    dict(x=530, cat="regra", tag="REGRAS FIXAS", titulo="Acha a habilidade da BNCC", desenho=bncc,
         texto=["Extrai o tema (“Ordenação”),", "busca no catálogo oficial", "e o professor confirma", "a habilidade (EF08CO03)."]),
    dict(x=900, cat="ia", tag="IA · GEMINI", titulo="5 especialistas escrevem", desenho=especialistas, grande=True,
         texto=["Objetivos, avaliação, metodologia,", "sequência e adaptações: cada um", "usa o que os anteriores fizeram;", "o sistema confere cada passo."]),
    dict(x=1270, cat="ia", tag="IA · JUIZ (GROQ)", titulo="A IA Juiz revisa", desenho=juiz,
         texto=["Nota de 0 a 3 em 6 critérios", "(currículo, objetivos, método,", "viabilidade, avaliação, inclusão)", "e aponta os problemas."]),
    dict(x=1620, cat="hum", tag="PROFESSOR", titulo="Aprova e baixa o PDF", desenho=aprova_pdf,
         texto=["Lê o plano e o parecer.", "Aprova e baixa, ou pede", "para gerar de novo.", "A decisão final é dele."]),
]
CY = 470


def estacao(i, e):
    c, bg, bg2 = COR[e["cat"]]
    r = 118 if e.get("grande") else 100
    x = e["x"]
    s = [f'<circle cx="{x}" cy="{CY}" r="{r + 14}" fill="{bg}" opacity=".9"/>',
         f'<circle cx="{x}" cy="{CY}" r="{r}" fill="url(#g-{e["cat"]})" stroke="{c}" stroke-width="4" filter="url(#sombra)"/>',
         f'<g transform="translate({x} {CY + 4})">{e["desenho"]()}</g>',
         f'<circle cx="{x - r * 0.72}" cy="{CY - r * 0.72}" r="25" fill="{TINTA}" stroke="#fff" stroke-width="4"/>',
         t(x - r * 0.72, CY - r * 0.72 + 8, str(i + 1), 23, 800, "#fff")]
    # cartão
    cw, ch, cy0 = 306, 236, CY + 118 + 40
    s += [f'<rect x="{x - cw / 2}" y="{cy0}" width="{cw}" height="{ch}" rx="18" fill="#fff" stroke="{bg2}" stroke-width="2.5" filter="url(#sombra)"/>',
          f'<rect x="{x - cw / 2}" y="{cy0}" width="{cw}" height="8" rx="4" fill="{c}"/>',
          f'<rect x="{x - 78}" y="{cy0 + 24}" width="156" height="28" rx="14" fill="{bg}"/>',
          t(x, cy0 + 43, e["tag"], 13.5, 700, c, extra='letter-spacing="1.2"'),
          t(x, cy0 + 86, e["titulo"], 22, 700),
          linhas(x, cy0 + 122, e["texto"], 16.5)]
    return "".join(s)


def setas():
    s = []
    xs = [(e["x"], 118 if e.get("grande") else 100) for e in ESTACOES]
    for (x1, r1), (x2, r2) in zip(xs, xs[1:]):
        a, b = x1 + r1 + 22, x2 - r2 - 26
        s.append(f'<path d="M{a} {CY} C{a + 30} {CY - 26} {b - 30} {CY - 26} {b} {CY}" fill="none" stroke="{TINTA}" stroke-width="4" '
                 f'stroke-linecap="round" marker-end="url(#ponta)"/>')
    # laço da regeneração informada: do Juiz (4) de volta aos especialistas (3), por cima
    x3, x4 = ESTACOES[2]["x"], ESTACOES[3]["x"]
    c = COR["ia"][0]
    s.append(f'<path d="M{x4} {CY - 118} C{x4} {CY - 250} {x3 + 40} {CY - 270} {x3 + 30} {CY - 146}" fill="none" stroke="{c}" '
             f'stroke-width="4" stroke-dasharray="11 9" stroke-linecap="round" marker-end="url(#ponta-ia)"/>')
    bx, by = (x3 + x4) / 2 + 12, CY - 270
    s.append(f'<rect x="{bx - 250}" y="{by - 40}" width="500" height="78" rx="16" fill="#fff" stroke="{c}" stroke-width="2.5"/>')
    s.append(t(bx, by - 10, "Parecer não favorável?", 18, 700, c))
    s.append(t(bx, by + 18, "o plano é escrito de novo uma vez, usando as críticas do Juiz", 16, 500, "#2c3b42"))
    return "".join(s)


def svg():
    defs = ['<defs>',
            '<filter id="sombra" x="-20%" y="-20%" width="140%" height="140%"><feDropShadow dx="0" dy="6" stdDeviation="9" flood-color="#16242b" flood-opacity=".12"/></filter>',
            f'<marker id="ponta" viewBox="0 0 12 12" refX="8" refY="6" markerWidth="5" markerHeight="5" orient="auto"><path d="M1 1 L10 6 L1 11" fill="none" stroke="{TINTA}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></marker>',
            f'<marker id="ponta-ia" viewBox="0 0 12 12" refX="8" refY="6" markerWidth="5" markerHeight="5" orient="auto"><path d="M1 1 L10 6 L1 11" fill="none" stroke="{COR["ia"][0]}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></marker>',
            '<linearGradient id="fundo" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#f7fafb"/><stop offset="1" stop-color="#ffffff"/></linearGradient>']
    for k, (c, bg, bg2) in COR.items():
        defs.append(f'<radialGradient id="g-{k}" cx=".35" cy=".3" r=".9"><stop offset="0" stop-color="#ffffff"/><stop offset="1" stop-color="{bg2}"/></radialGradient>')
    defs.append('</defs>')
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="Inter, \'DejaVu Sans\', sans-serif">',
         *defs, f'<rect width="{W}" height="{H}" fill="url(#fundo)"/>',
         t(60, 74, "AulaIA: do pedido do professor ao plano de aula pronto", 36, 800, anc="start", extra='letter-spacing="-0.5"'),
         t(60, 112, "Planos de aula de Computação do 8º ano, alinhados à BNCC, escritos por agentes de IA e revisados por uma IA Juiz",
           19, 500, MUTED, anc="start"),
         setas(), *[estacao(i, e) for i, e in enumerate(ESTACOES)]]
    # rodapé: legenda e nota
    y = H - 64
    p.append(f'<line x1="60" y1="{y - 30}" x2="{W - 60}" y2="{y - 30}" stroke="#d6e0e4" stroke-width="1.5"/>')
    leg = [("hum", "Pessoa: o professor decide"), ("regra", "Regras fixas, sem IA"), ("ia", "Inteligência artificial (modelos de linguagem)")]
    x = 60
    for k, rot in leg:
        c, bg, _ = COR[k]
        p.append(f'<circle cx="{x + 12}" cy="{y}" r="11" fill="{bg}" stroke="{c}" stroke-width="3"/>')
        p.append(t(x + 32, y + 6, rot, 16.5, 500, MUTED, anc="start"))
        x += 32 + 9.0 * len(rot) + 40
    p.append(t(W - 60, y + 6, "Sem versão favorável, o professor recebe a que tem menos falhas graves, com um aviso.", 16.5, 500, MUTED, anc="end"))
    p.append("</svg>")
    return "\n".join(p)


if __name__ == "__main__":
    destino = Path(__file__).resolve().parent.parent / "visao-geral-ilustrada.svg"
    destino.write_text(svg(), encoding="utf-8")
    print(destino)
