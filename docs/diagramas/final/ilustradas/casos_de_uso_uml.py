"""Diagrama de casos de uso do AulaIA em SVG desenhado à mão (notação UML: bonecos, elipses, «include»/«extend» tracejados).

Mesmo conteúdo de ../casos-de-uso.puml, com layout fixo (sem posicionamento automático). Só biblioteca padrão.
Uso: python casos_de_uso_uml.py  → escreve casos-de-uso-uml.svg nesta pasta (o PNG sai pelo render.js, escala 2).
"""
from math import hypot, sqrt
from pathlib import Path

W, H = 1720, 1000
TINTA, CINZA, AZUL, AZUL_BG, LARANJA, LARANJA_BG, CLARO = "#16242b", "#5a6a72", "#0f6b84", "#e3f1f5", "#a2561b", "#fbeee2", "#f2f5f6"

# id: (x, y, rx, ry, linhas, estilo)
UCS = {
    "UC01": (830, 500, 160, 66, ["UC01", "Gerar plano de aula"], "principal"),
    "UC02": (515, 230, 150, 50, ["UC02", "Visualizar plano e parecer"], "uc"),
    "UC03": (520, 370, 120, 46, ["UC03", "Aprovar plano"], "uc"),
    "UC04": (520, 650, 135, 50, ["UC04", "Baixar plano em PDF"], "uc"),
    "CTX": (830, 260, 125, 46, ["Informar contexto", "da aula"], "aux"),
    "CONF": (1130, 300, 125, 46, ["Confirmar", "habilidade BNCC"], "aux"),
    "CAT": (620, 815, 130, 46, ["Escolher habilidade", "no catálogo"], "aux"),
    "FONTE": (890, 845, 140, 46, ["Abrir documento-fonte", "da BNCC"], "aux"),
    "NOVA": (1150, 790, 110, 40, ["Gerar novamente"], "aux"),
}
ATORES = {"P": (150, 500, ["Professor"]), "GEM": (1560, 360, ["Serviço Gemini", "(geração)"]),
          "GROQ": (1560, 640, ["Serviço Groq", "(IA Juiz)"])}
ASSOC = [("P", "UC01"), ("P", "UC02"), ("P", "UC03"), ("P", "UC04"), ("UC01", "GEM"), ("UC01", "GROQ")]
INCLUDE = [("UC01", "CTX"), ("UC01", "CONF")]
EXTEND = [("CAT", "UC01"), ("FONTE", "UC01"), ("NOVA", "UC01")]


def borda_elipse(id_, alvo):
    x, y, rx, ry, *_ = UCS[id_]
    dx, dy = alvo[0] - x, alvo[1] - y
    k = 1 / sqrt((dx / rx) ** 2 + (dy / ry) ** 2)
    return x + dx * k, y + dy * k


def ponto(id_):
    if id_ in UCS:
        return UCS[id_][:2]
    x, y, _ = ATORES[id_]
    return x, y - 10


def ponta(id_, outro):
    """Onde a linha encosta: na borda da elipse ou ao lado do boneco."""
    if id_ in UCS:
        return borda_elipse(id_, ponto(outro))
    x, y, _ = ATORES[id_]
    lado = 1 if ponto(outro)[0] > x else -1
    return x + 34 * lado, y - 10


def texto(x, y, linhas, tam, peso=600, cor=TINTA, estilo=""):
    alt = tam * 1.25
    y0 = y - alt * (len(linhas) - 1) / 2
    spans = "".join(f'<tspan x="{x:.1f}" y="{y0 + i * alt + tam * 0.35:.1f}">{l}</tspan>' for i, l in enumerate(linhas))
    return f'<text text-anchor="middle" font-size="{tam}" font-weight="{peso}" fill="{cor}" {estilo}>{spans}</text>'


def boneco(x, y, linhas):
    c = LARANJA
    return (f'<g stroke="{c}" stroke-width="4" stroke-linecap="round" fill="none">'
            f'<circle cx="{x}" cy="{y - 62}" r="20" fill="{LARANJA_BG}"/>'
            f'<line x1="{x}" y1="{y - 42}" x2="{x}" y2="{y + 18}"/>'
            f'<line x1="{x - 32}" y1="{y - 18}" x2="{x + 32}" y2="{y - 18}"/>'
            f'<line x1="{x}" y1="{y + 18}" x2="{x - 26}" y2="{y + 62}"/>'
            f'<line x1="{x}" y1="{y + 18}" x2="{x + 26}" y2="{y + 62}"/></g>'
            + texto(x, y + 96 + 12 * (len(linhas) - 1), linhas, 21, 700))


def seta(a, b, rotulo, cor):
    (x1, y1), (x2, y2) = ponta(a, b), ponta(b, a)
    d = hypot(x2 - x1, y2 - y1)
    ux, uy = (x2 - x1) / d, (y2 - y1) / d
    # ponta aberta (UML): duas linhas curtas
    p1 = (x2 - 16 * ux + 8 * uy, y2 - 16 * uy - 8 * ux)
    p2 = (x2 - 16 * ux - 8 * uy, y2 - 16 * uy + 8 * ux)
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    larg = 9.2 * len(rotulo) + 14
    return (f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{cor}" stroke-width="2.4" stroke-dasharray="9 7"/>'
            f'<polyline points="{p1[0]:.1f},{p1[1]:.1f} {x2:.1f},{y2:.1f} {p2[0]:.1f},{p2[1]:.1f}" fill="none" stroke="{cor}" '
            f'stroke-width="2.6" stroke-linejoin="round" stroke-linecap="round"/>'
            f'<rect x="{mx - larg / 2:.1f}" y="{my - 14:.1f}" width="{larg:.1f}" height="28" rx="14" fill="#ffffff" stroke="{cor}" stroke-width="1.2"/>'
            + texto(mx, my, [rotulo], 16, 600, cor, 'font-style="italic"'))


def elipse(id_):
    x, y, rx, ry, linhas, estilo = UCS[id_]
    fill, stroke, sw, tam, peso = {"principal": (AZUL_BG, AZUL, 3.4, 22, 700), "uc": ("#ffffff", TINTA, 2.6, 19, 650),
                                   "aux": (CLARO, CINZA, 2, 17, 550)}[estilo]
    return (f'<ellipse cx="{x}" cy="{y}" rx="{rx}" ry="{ry}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
            + texto(x, y, linhas, tam, peso))


def svg():
    partes = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
              f'font-family="Inter, \'DejaVu Sans\', sans-serif">',
              f'<rect width="{W}" height="{H}" fill="#ffffff"/>',
              '<rect x="330" y="80" width="1060" height="880" rx="22" fill="#fbfcfd" stroke="#5a6a72" stroke-width="2.4"/>',
              '<rect x="330" y="80" width="1060" height="56" rx="22" fill="#eef3f5"/>'
              '<rect x="330" y="114" width="1060" height="22" fill="#eef3f5"/>',
              '<line x1="330" y1="136" x2="1390" y2="136" stroke="#cfd9de" stroke-width="1.5"/>',
              texto(860, 108, ["Sistema AulaIA"], 24, 700)]
    for a, b in ASSOC:
        (x1, y1), (x2, y2) = ponta(a, b), ponta(b, a)
        partes.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{TINTA}" stroke-width="2.4"/>')
    for a, b in INCLUDE:
        partes.append(seta(a, b, "«include»", AZUL))
    for a, b in EXTEND:
        partes.append(seta(a, b, "«extend»", LARANJA))
    partes += [elipse(i) for i in UCS]
    partes += [boneco(*v) for v in ATORES.values()]
    partes.append(texto(860, 985, ["Caso de uso principal em azul; casos incluídos e extensões em cinza. "
                                   "«include»: sempre acontece dentro do UC01; «extend»: acontece só quando o professor escolhe."],
                        15, 500, CINZA))
    partes.append("</svg>")
    return "\n".join(partes)


if __name__ == "__main__":
    destino = Path(__file__).resolve().parent.parent / "casos-de-uso-uml.svg"
    destino.write_text(svg(), encoding="utf-8")
    print(destino)
