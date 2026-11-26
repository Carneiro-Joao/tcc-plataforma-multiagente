"""Figura ilustrada "Estrutura do plano de aula gerado" em SVG (ilustração vetorial feita à mão). Só biblioteca padrão.

Mesmo conteúdo de ../estrutura-plano.html (que continua guardada): o plano como uma folha com as 11 seções e, ao lado, a corrente
OBJ → ET → EVI → INS. Exemplo: execução de 23/11/2026 (Ordenação, 8º ano, aula prática, 50 min); trocar os trechos de EXEMPLO
quando houver a nova execução. Uso: python estrutura_plano_ilustrada.py → ../estrutura-plano-ilustrada.svg (PNG pelo render.js).
"""
from pathlib import Path

W, H = 1800, 1100
TINTA, MUTED = "#16242b", "#4f5f67"
IA, IA_BG, IA_BG2 = "#0f6b84", "#e3f1f5", "#bfe0ea"
REGRA, REGRA_BG, REGRA_BG2 = "#5a6a72", "#f2f5f6", "#dde5e8"
ELO, ELO_BG, ELO_BG2 = "#1f7a4d", "#e6f4ec", "#9fcfb3"

EXEMPLO = {
    "subtitulo": "Modelo PlanoDeAula 2.0 · exemplo real: Ordenação, 8º ano, aula prática de 50 min, com projetor e computadores",
    "cabecalho": "Plano de aula · Ordenação · 8º ano · 50 min",
    "habilidade": "EF08CO03, copiada do documento oficial",
    "elos": [
        ("OBJ1", "objetivo", "O que o aluno vai aprender", ["“Explicar o funcionamento do", "algoritmo Bubblesort.”"]),
        ("ET1", "etapa · 20 min", "Quando isso acontece na aula", ["Introdução ao Bubblesort: explicação", "oral com o projetor, trocas sucessivas."]),
        ("EVI1", "evidência", "Como saber que aprendeu", ["“O aluno explica oralmente como os", "elementos adjacentes são comparados e trocados.”"]),
        ("INS1", "instrumento", "Como o professor observa", ["“Arguição oral sobre a lógica de", "trocas sucessivas do Bubblesort.”"]),
    ],
    "fonte": "Exemplo: plano gerado pelo AulaIA em 23/11/2026 (prompt 2.3) e aprovado pelo professor.",
}

GRUPOS = [
    ("Identificação e currículo", [(1, "Identificação", "Tema, ano, tipo de aula e duração", "Sistema", "regra"),
                                   (2, "Habilidade da BNCC", EXEMPLO["habilidade"], "Sistema", "regra")]),
    ("O que ensinar e como", [(3, "Conteúdos", "Conceitos que a aula aborda", "Objetivos", "ia"),
                              (4, "Objetivo geral", "A meta da aula", "Objetivos", "ia"),
                              (5, "Objetivos específicos", "De 2 a 4, observáveis (OBJ1, OBJ2…)", "Objetivos", "ia"),
                              (6, "Metodologia", "A estratégia da aula", "Metodologia", "ia"),
                              (7, "Recursos", "Exatamente os que o professor marcou", "Cópia exata", "regra"),
                              (8, "Desenvolvimento", "Etapas com minutos e ações (ET1, ET2…)", "Sequência", "ia")]),
    ("Avaliar e incluir", [(9, "Avaliação da aprendizagem", "Evidências (EVI) e instrumentos (INS)", "Avaliação", "ia"),
                           (10, "Adaptações", "Duas estratégias de inclusão, sem supor diagnósticos", "Adaptação", "ia")]),
    ("Fonte", [(11, "Referências", "Só a fonte oficial, com páginas e versão", "Sistema", "regra")]),
]


def t(x, y, s, tam=18, peso=500, cor=TINTA, anc="middle", extra=""):
    return f'<text x="{x}" y="{y}" font-size="{tam}" font-weight="{peso}" fill="{cor}" text-anchor="{anc}" {extra}>{s}</text>'


def folha():
    x0, y0, w = 60, 150, 860
    linha_h, gap_grupo = 54, 34
    n = sum(len(s) for _, s in GRUPOS)
    h = 120 + n * linha_h + len(GRUPOS) * gap_grupo + 10
    p = [f'<g filter="url(#sombra)"><path d="M{x0} {y0} h{w - 60} l60 60 v{h - 60} h-{w} z" fill="#ffffff" stroke="#cfd9de" stroke-width="2"/></g>',
         f'<path d="M{x0 + w - 60} {y0} v60 h60" fill="#eef3f5" stroke="#cfd9de" stroke-width="2" stroke-linejoin="round"/>',
         f'<rect x="{x0 + 34}" y="{y0 + 34}" width="44" height="54" rx="6" fill="{IA_BG}" stroke="{IA}" stroke-width="2.5"/>',
         f'<path d="M{x0 + 44} {y0 + 52} h24 M{x0 + 44} {y0 + 62} h24 M{x0 + 44} {y0 + 72} h16" stroke="{IA}" stroke-width="2.5" stroke-linecap="round"/>',
         t(x0 + 98, y0 + 58, EXEMPLO["cabecalho"], 22, 700, anc="start"),
         t(x0 + 98, y0 + 84, "11 seções · contrato plano-aula-2.0 · conferido pelo validador", 15.5, 500, MUTED, anc="start")]
    y = y0 + 120
    for nome, secoes in GRUPOS:
        p.append(t(x0 + 34, y + 20, nome.upper(), 13.5, 700, MUTED, anc="start", extra='letter-spacing="1.3"'))
        y += gap_grupo
        for num, titulo, dica, quem, cat in secoes:
            cor, bg, bg2 = (IA, IA_BG, IA_BG2) if cat == "ia" else (REGRA, REGRA_BG, REGRA_BG2)
            p += [f'<rect x="{x0 + 30}" y="{y - 4}" width="{w - 60}" height="{linha_h - 10}" rx="12" fill="{bg}" stroke="{bg2}" stroke-width="1.5"/>',
                  f'<rect x="{x0 + 30}" y="{y - 4}" width="7" height="{linha_h - 10}" rx="3.5" fill="{cor}"/>',
                  f'<circle cx="{x0 + 72}" cy="{y + 18}" r="15" fill="{TINTA}"/>', t(x0 + 72, y + 23.5, str(num), 14, 800, "#fff"),
                  t(x0 + 102, y + 14, titulo, 17, 700, anc="start"), t(x0 + 102, y + 33, dica, 14, 500, "#3d4c53", anc="start")]
            cw = 9.2 * len(quem) + 46
            cx = x0 + w - 44 - cw
            icone = (f'<circle cx="{cx + 17}" cy="{y + 18}" r="6" fill="none" stroke="{cor}" stroke-width="2.4"/>'
                     f'<path d="M{cx + 13.5} {y + 18} l2.5 2.5 l4.5 -5" stroke="{cor}" stroke-width="2" fill="none" stroke-linecap="round"/>'
                     if cat == "regra" else
                     f'<rect x="{cx + 10}" y="{y + 11}" width="14" height="12" rx="3.5" fill="none" stroke="{cor}" stroke-width="2.2"/>'
                     f'<circle cx="{cx + 14.5}" cy="{y + 17}" r="1.6" fill="{cor}"/><circle cx="{cx + 19.5}" cy="{y + 17}" r="1.6" fill="{cor}"/>')
            p += [f'<rect x="{cx}" y="{y + 3}" width="{cw}" height="30" rx="15" fill="#fff" stroke="{bg2}" stroke-width="1.5"/>', icone,
                  t(cx + 32, y + 23, quem, 14, 650, cor, anc="start")]
            y += linha_h
    return "".join(p), y0 + h


def elo_corrente(cx, y):
    """Dois elos de corrente entrelaçados, na vertical."""
    return (f'<g fill="none" stroke="{ELO}" stroke-width="5" stroke-linecap="round">'
            f'<rect x="{cx - 13}" y="{y - 26}" width="26" height="34" rx="13"/>'
            f'<rect x="{cx - 13}" y="{y - 8}" width="26" height="34" rx="13" stroke="#58a77c"/></g>')


def corrente():
    x0, y0, w = 1000, 150, 740
    p = [f'<rect x="{x0}" y="{y0}" width="{w}" height="860" rx="24" fill="{ELO_BG}" stroke="{ELO}" stroke-width="2.5"/>',
         t(x0 + 40, y0 + 56, "A corrente que garante a coerência", 25, 800, ELO, anc="start"),
         t(x0 + 40, y0 + 88, "Cada objetivo precisa aparecer numa etapa, ter uma evidência e um instrumento.", 16, 500, "#2b4a39", anc="start")]
    y, ch, passo = y0 + 120, 126, 160
    for i, (ident, tipo, pergunta, citacao) in enumerate(EXEMPLO["elos"]):
        p += [f'<rect x="{x0 + 40}" y="{y}" width="{w - 80}" height="{ch}" rx="18" fill="#fff" stroke="{ELO_BG2}" stroke-width="2" filter="url(#sombra)"/>',
              f'<rect x="{x0 + 64}" y="{y + 22}" width="{12 + 11 * len(ident)}" height="34" rx="9" fill="{ELO}"/>',
              t(x0 + 70 + 5.5 * len(ident), y + 45, ident, 18, 800, "#fff", extra='font-family="DejaVu Sans Mono, monospace"'),
              t(x0 + 86 + 11 * len(ident), y + 45, tipo, 15, 600, ELO, anc="start", extra='letter-spacing="0.6"'),
              t(x0 + w - 64, y + 45, pergunta, 17, 700, TINTA, anc="end")]
        for k, l in enumerate(citacao):
            p.append(t(x0 + 64, y + 86 + k * 25, l, 17, 500, "#2c3b42", anc="start"))
        if i < 3:
            p.append(elo_corrente(x0 + w - 140, y + ch + 21))
        y += passo
    # selo do validador
    sy = y
    p += [f'<rect x="{x0 + 40}" y="{sy}" width="{w - 80}" height="86" rx="18" fill="#ffffff" stroke="{ELO}" stroke-width="2" stroke-dasharray="8 6"/>',
          f'<path d="M{x0 + 96} {sy + 14} l26 10 v20 c0 16 -11 26 -26 32 c-15 -6 -26 -16 -26 -32 v-20 z" fill="{ELO}"/>',
          f'<path d="M{x0 + 85} {sy + 44} l8 8 l15 -16" fill="none" stroke="#fff" stroke-width="4.5" stroke-linecap="round" stroke-linejoin="round"/>',
          t(x0 + 140, sy + 37, "O validador confere a corrente", 18, 700, ELO, anc="start"),
          t(x0 + 140, sy + 64, "Faltou um elo, ou a soma dos minutos não fecha? O plano é recusado.", 15, 500, "#2b4a39", anc="start")]
    return "".join(p)


def svg():
    corpo, fim_folha = folha()
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="Inter, \'DejaVu Sans\', sans-serif">',
         '<defs><filter id="sombra" x="-10%" y="-10%" width="120%" height="130%"><feDropShadow dx="0" dy="6" stdDeviation="9" flood-color="#16242b" flood-opacity=".10"/></filter>'
         '<linearGradient id="fundo" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#f7fafb"/><stop offset="1" stop-color="#ffffff"/></linearGradient></defs>',
         f'<rect width="{W}" height="{H}" fill="url(#fundo)"/>',
         t(60, 74, "O que o AulaIA entrega: um plano de aula em 11 seções ligadas entre si", 34, 800, anc="start", extra='letter-spacing="-0.5"'),
         t(60, 110, EXEMPLO["subtitulo"], 18.5, 500, MUTED, anc="start"),
         corpo, corrente()]
    # seta pontilhada da seção 5 (objetivos) para a corrente
    p.append(f'<path d="M925 572 C985 572 985 334 1034 334" fill="none" stroke="{ELO}" stroke-width="3" stroke-dasharray="7 6" marker-end="url(#pe)"/>')
    p.insert(2, f'<defs><marker id="pe" viewBox="0 0 12 12" refX="8" refY="6" markerWidth="5" markerHeight="5" orient="auto"><path d="M1 1 L10 6 L1 11" fill="none" stroke="{ELO}" stroke-width="2.2" stroke-linecap="round"/></marker></defs>')
    y = H - 40
    leg = [(REGRA, REGRA_BG, "Preenchido ou copiado pelo sistema (a IA não pode alterar)"), (IA, IA_BG, "Escrito pelo agente especialista indicado")]
    x = 60
    for cor, bg, rot in leg:
        p.append(f'<rect x="{x}" y="{y - 13}" width="24" height="24" rx="6" fill="{bg}" stroke="{cor}" stroke-width="2.5"/>')
        p.append(t(x + 36, y + 5, rot, 16, 500, MUTED, anc="start"))
        x += 36 + 8.6 * len(rot) + 40
    p.append(t(W - 60, y + 5, EXEMPLO["fonte"], 15, 500, MUTED, anc="end"))
    p.append("</svg>")
    return "\n".join(p)


if __name__ == "__main__":
    destino = Path(__file__).resolve().parent.parent / "estrutura-plano-ilustrada.svg"
    destino.write_text(svg(), encoding="utf-8")
    print(destino)
