"""Roda a suíte de testes do AulaIA e gera um relatório HTML (arquivo único, sem internet, sem dependências).

Uso, dentro da pasta aula-ia-backend:
    python relatorio_testes.py                  # roda tudo e abre o relatório no navegador
    python relatorio_testes.py --sem-abrir      # só grava o arquivo
    python relatorio_testes.py --filtro juiz    # só testes cujo identificador contém "juiz"

Os testes são offline: não usam chave de API nem rede. O relatório fica em local/relatorio_testes/
(pasta ignorada pelo Git) e nunca sobrescreve um relatório anterior.
"""
import argparse
from datetime import datetime
import html
from pathlib import Path
import platform
import subprocess
import sys
import time
import unittest
import webbrowser

AQUI = Path(__file__).resolve().parent
ROTULOS = {"ok": "Passou", "falha": "Falhou", "erro": "Erro", "ignorado": "Ignorado",
           "falha_esperada": "Falha esperada", "sucesso_inesperado": "Sucesso inesperado"}
ICONES = {"ok": "✓", "falha": "✗", "erro": "!", "ignorado": "–", "falha_esperada": "≈", "sucesso_inesperado": "?"}
RUINS = ("falha", "erro", "sucesso_inesperado")


class Resultado(unittest.TestResult):
    """Coleta um registro por teste (status, tempo, detalhe), inclusive falhas dentro de subTest."""

    def __init__(self):
        super().__init__()
        self.buffer = True
        self.registros, self._atual, self._inicio = [], None, 0.0

    def startTest(self, teste):
        super().startTest(teste)
        partes = teste.id().split(".")
        if teste.id().startswith("unittest.loader._FailedTest."):  # módulo que nem foi importado
            modulo, classe, metodo = partes[-1], "Falha ao importar", partes[-1]
        else:
            modulo, classe, metodo = partes[0], partes[-2] if len(partes) > 2 else "", partes[-1]
        self._atual = dict(id=teste.id(), modulo=modulo, classe=classe, metodo=metodo, status="ok", tempo_ms=0.0,
                           detalhe="", descricao=(teste.shortDescription() or "").strip(), subtestes=[])
        self._inicio = time.perf_counter()

    def stopTest(self, teste):
        self._atual["tempo_ms"] = (time.perf_counter() - self._inicio) * 1000
        self.registros.append(self._atual)
        super().stopTest(teste)

    def _marcar(self, status, detalhe=""):
        if self._atual["status"] == "ok" or status == "erro":
            self._atual["status"] = status
        if detalhe:
            self._atual["detalhe"] += ("\n" if self._atual["detalhe"] else "") + detalhe

    def addFailure(self, teste, err):
        super().addFailure(teste, err)
        self._marcar("falha", self._exc_info_to_string(err, teste))

    def addError(self, teste, err):
        super().addError(teste, err)
        self._marcar("erro", self._exc_info_to_string(err, teste))

    def addSkip(self, teste, motivo):
        super().addSkip(teste, motivo)
        self._marcar("ignorado", str(motivo))

    def addExpectedFailure(self, teste, err):
        super().addExpectedFailure(teste, err)
        self._marcar("falha_esperada", self._exc_info_to_string(err, teste))

    def addUnexpectedSuccess(self, teste):
        super().addUnexpectedSuccess(teste)
        self._marcar("sucesso_inesperado", "O teste estava marcado como falha esperada, mas passou.")

    def addSubTest(self, teste, subteste, err):
        super().addSubTest(teste, subteste, err)
        if err is not None:
            texto = self._exc_info_to_string(err, teste)
            self._atual["subtestes"].append(str(subteste))
            self._marcar("falha" if issubclass(err[0], teste.failureException) else "erro", f"[{subteste}]\n{texto}")


def achatar(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from achatar(item)
        else:
            yield item


def executar(pasta_testes, filtro=None):
    """Descobre e roda os testes de `pasta_testes`. Devolve um dict com registros e totais."""
    pasta = Path(pasta_testes).resolve()
    antes_modulos, antes_caminho = set(sys.modules), list(sys.path)
    try:
        suite = unittest.TestLoader().discover(str(pasta), pattern="test*.py", top_level_dir=str(pasta))
        testes = [t for t in achatar(suite) if not filtro or filtro.lower() in t.id().lower()]
        resultado = Resultado()
        inicio = time.perf_counter()
        unittest.TestSuite(testes).run(resultado)
        duracao = time.perf_counter() - inicio
    finally:  # higiene: não deixa módulos e caminhos da pasta de testes poluírem quem chamou
        for nome in set(sys.modules) - antes_modulos:
            arquivo = getattr(sys.modules[nome], "__file__", None)
            if arquivo and str(pasta) in str(Path(arquivo).resolve()):
                del sys.modules[nome]
        sys.path[:] = antes_caminho
    contagem = {k: sum(r["status"] == k for r in resultado.registros) for k in ROTULOS}
    return dict(registros=resultado.registros, contagem=contagem, total=len(resultado.registros),
                duracao_s=duracao, filtro=filtro, gerado_em=datetime.now().astimezone(), ambiente=ambiente())


def ambiente():
    def git(*args):
        try:
            return subprocess.run(["git", *args], cwd=AQUI, capture_output=True, text=True, timeout=5).stdout.strip()
        except (OSError, subprocess.SubprocessError):
            return ""
    return dict(python=platform.python_version(), sistema=f"{platform.system()} {platform.release()}",
                branch=git("rev-parse", "--abbrev-ref", "HEAD") or "(sem git)", commit=git("rev-parse", "--short", "HEAD"),
                alteracoes_locais=bool(git("status", "--porcelain")))


def aprovado(dados):
    return not any(dados["contagem"][k] for k in RUINS) and dados["total"] > 0


CSS = """
:root{--bg:#f6f7f9;--fg:#1c2330;--mut:#5b6678;--card:#fff;--bd:#d9dee7;--ok:#1a7f37;--falha:#c62828;--erro:#b45309;
--ign:#5b6678;--esp:#6a4fb3;--ac:#1f5fbf}
@media(prefers-color-scheme:dark){:root{--bg:#0f141b;--fg:#e6eaf1;--mut:#9aa6b8;--card:#171e29;--bd:#2a3444;--ok:#3fb950;
--falha:#ff6b6b;--erro:#f0a35a;--ign:#9aa6b8;--esp:#a78bfa;--ac:#6ea8ff}}
*{box-sizing:border-box}body{margin:0;font:15px/1.5 system-ui,Segoe UI,Roboto,sans-serif;background:var(--bg);color:var(--fg)}
main{max-width:1100px;margin:0 auto;padding:24px 16px 64px}h1{margin:0 0 4px;font-size:1.6rem}
.mut{color:var(--mut)}.banner{margin:16px 0;padding:14px 18px;border-radius:10px;font-weight:700;font-size:1.1rem;border:2px solid}
.banner.ok{color:var(--ok);border-color:var(--ok)}.banner.ruim{color:var(--falha);border-color:var(--falha)}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:10px;margin:14px 0}
.card{background:var(--card);border:1px solid var(--bd);border-radius:10px;padding:10px 14px}
.card b{display:block;font-size:1.6rem}.barra{display:flex;height:12px;border-radius:6px;overflow:hidden;background:var(--bd);margin:6px 0 18px}
.barra span{display:block}.s-ok{background:var(--ok)}.s-falha{background:var(--falha)}.s-erro{background:var(--erro)}
.s-ignorado{background:var(--ign)}.s-falha_esperada,.s-sucesso_inesperado{background:var(--esp)}
.ctl{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:10px 0 18px}
button,input{font:inherit;color:var(--fg);background:var(--card);border:1px solid var(--bd);border-radius:8px;padding:6px 12px}
button{cursor:pointer}button[aria-pressed=true]{border-color:var(--ac);color:var(--ac);font-weight:700}
button:focus-visible,input:focus-visible,summary:focus-visible{outline:3px solid var(--ac);outline-offset:2px}
details{background:var(--card);border:1px solid var(--bd);border-radius:10px;margin:8px 0}
summary{cursor:pointer;padding:10px 14px;font-weight:700;display:flex;gap:10px;align-items:center;flex-wrap:wrap}
.badge{font-weight:400;font-size:.85rem;padding:1px 8px;border-radius:99px;border:1px solid var(--bd);color:var(--mut)}
.badge.ruim{color:var(--falha);border-color:var(--falha)}.classe{padding:2px 14px 10px}.classe h3{margin:10px 0 4px;font-size:.95rem;color:var(--mut)}
.t{display:flex;gap:10px;padding:4px 0;border-top:1px solid var(--bd);align-items:baseline}
.ic{width:1.4em;text-align:center;font-weight:700;flex:none}.ic.ok{color:var(--ok)}.ic.falha{color:var(--falha)}
.ic.erro{color:var(--erro)}.ic.ignorado{color:var(--ign)}.ic.falha_esperada,.ic.sucesso_inesperado{color:var(--esp)}
.nome{flex:1;min-width:0}.id{display:block;font-size:.78rem;color:var(--mut);word-break:break-all}.ms{color:var(--mut);font-size:.85rem;flex:none}
pre{white-space:pre-wrap;word-break:break-word;background:var(--bg);border:1px solid var(--bd);border-radius:8px;padding:10px;font-size:.82rem;margin:6px 0}
.oculto{display:none}footer{margin-top:28px;color:var(--mut);font-size:.85rem}
"""

JS = """
const botoes=[...document.querySelectorAll('[data-filtro]')],caixa=document.getElementById('busca');
let filtro='todos';
function aplicar(){const q=caixa.value.trim().toLowerCase();
 document.querySelectorAll('.t').forEach(t=>{const ok=(filtro==='todos'||t.dataset.status===filtro||(filtro==='ruins'&&['falha','erro','sucesso_inesperado'].includes(t.dataset.status)))
  &&(!q||t.dataset.texto.includes(q));t.classList.toggle('oculto',!ok)});
 document.querySelectorAll('.classe').forEach(c=>c.classList.toggle('oculto',!c.querySelector('.t:not(.oculto)')));
 document.querySelectorAll('details.modulo').forEach(d=>{const v=d.querySelector('.t:not(.oculto)');d.classList.toggle('oculto',!v);if(q||filtro!=='todos'){d.open=!!v}})}
botoes.forEach(b=>b.addEventListener('click',()=>{filtro=b.dataset.filtro;botoes.forEach(x=>x.setAttribute('aria-pressed',x===b));aplicar()}));
caixa.addEventListener('input',aplicar);
document.getElementById('abrir').addEventListener('click',()=>document.querySelectorAll('details.modulo').forEach(d=>d.open=true));
document.getElementById('fechar').addEventListener('click',()=>document.querySelectorAll('details.modulo').forEach(d=>d.open=false));
"""


def esc(x):
    return html.escape(str(x), quote=True)


def humanizar(metodo):
    texto = metodo[5:] if metodo.startswith("test_") else metodo
    texto = texto.replace("_", " ").strip()
    return texto[:1].upper() + texto[1:]


def renderizar_html(dados):
    c, total = dados["contagem"], dados["total"]
    ok = aprovado(dados)
    por_modulo = {}
    for r in dados["registros"]:
        por_modulo.setdefault(r["modulo"], {}).setdefault(r["classe"], []).append(r)
    cartoes = [("Total", total, "")] + [(ROTULOS[k], c[k], k) for k in ("ok", "falha", "erro", "ignorado")]
    for extra in ("falha_esperada", "sucesso_inesperado"):
        if c[extra]:
            cartoes.append((ROTULOS[extra], c[extra], extra))
    barra = "".join(f'<span class="s-{k}" style="width:{100 * v / total:.3f}%" title="{esc(ROTULOS[k])}: {v}"></span>'
                    for k, v in c.items() if v and total)
    partes = ['<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">'
              '<meta name="viewport" content="width=device-width,initial-scale=1">'
              f'<title>AulaIA — Relatório de testes</title><style>{CSS}</style></head><body><main>',
              "<h1>AulaIA — Relatório de testes</h1>",
              f'<div class="mut">{esc(dados["gerado_em"].strftime("%d/%m/%Y %H:%M:%S"))} · testes offline, sem chave de API e sem rede</div>']
    if total == 0:
        veredito = "NENHUM TESTE EXECUTADO" + (f" (filtro: {dados['filtro']})" if dados["filtro"] else "")
    else:
        veredito = "TODOS OS TESTES PASSARAM" if ok else "HÁ TESTES COM PROBLEMA"
        if ok and c["ignorado"]:
            veredito += f" ({c['ignorado']} ignorado{'s' if c['ignorado'] > 1 else ''})"
    partes.append(f'<div class="banner {"ok" if ok else "ruim"}" role="status">{esc(veredito)}</div>')
    partes.append('<div class="cards">' + "".join(
        f'<div class="card"><span class="mut">{esc(rot)}</span><b{" style=color:var(--" + k + ")" if k and v else ""}>{v}</b></div>'
        for rot, v, k in cartoes) + f'<div class="card"><span class="mut">Tempo</span><b>{dados["duracao_s"]:.2f}s</b></div></div>')
    partes.append(f'<div class="barra" aria-hidden="true">{barra}</div>')
    partes.append('<div class="ctl"><button data-filtro="todos" aria-pressed="true">Todos</button>'
                  '<button data-filtro="ruins" aria-pressed="false">Só problemas</button>'
                  '<button data-filtro="ignorado" aria-pressed="false">Só ignorados</button>'
                  '<input id="busca" type="search" placeholder="Buscar teste…" aria-label="Buscar teste">'
                  '<button id="abrir" type="button">Abrir tudo</button><button id="fechar" type="button">Fechar tudo</button></div>')
    for modulo, classes in sorted(por_modulo.items()):
        todos = [r for lista in classes.values() for r in lista]
        ruins = sum(r["status"] in RUINS for r in todos)
        aberto = " open" if ruins else ""
        partes.append(f'<details class="modulo"{aberto}><summary>{esc(modulo)} <span class="badge{" ruim" if ruins else ""}">'
                      f'{len(todos)} teste{"s" if len(todos) != 1 else ""}{f" · {ruins} com problema" if ruins else ""}</span></summary>')
        for classe, lista in sorted(classes.items()):
            partes.append(f'<div class="classe"><h3>{esc(classe)}</h3>')
            for r in lista:
                nome = humanizar(r["metodo"]) if r["classe"] != "Falha ao importar" else f'Não foi possível importar {r["modulo"]}'
                texto = f'{r["id"]} {nome} {r["descricao"]}'.lower()
                extra = f'<span class="mut"> — {esc(r["descricao"])}</span>' if r["descricao"] else ""
                detalhe = ""
                if r["detalhe"]:
                    abre = " open" if r["status"] in RUINS else ""
                    rotulo = "Motivo" if r["status"] == "ignorado" else "Detalhe"
                    detalhe = f'<details{abre}><summary class="mut">{rotulo}</summary><pre>{esc(r["detalhe"])}</pre></details>'
                partes.append(f'<div class="t" data-status="{r["status"]}" data-texto="{esc(texto)}">'
                              f'<span class="ic {r["status"]}" title="{esc(ROTULOS[r["status"]])}">{ICONES[r["status"]]}</span>'
                              f'<span class="nome">{esc(nome)}{extra}<span class="id">{esc(r["id"])}</span>{detalhe}</span>'
                              f'<span class="ms">{r["tempo_ms"]:.1f} ms</span></div>')
            partes.append("</div>")
        partes.append("</details>")
    a = dados["ambiente"]
    sujo = " · alterações locais não commitadas" if a["alteracoes_locais"] else ""
    partes.append(f'<footer>Branch <b>{esc(a["branch"])}</b> · commit <b>{esc(a["commit"] or "?")}</b>{sujo} · Python {esc(a["python"])} · '
                  f'{esc(a["sistema"])}. Os testes provam a lógica e os contratos do projeto; não provam a qualidade pedagógica '
                  f'nem o comportamento de um LLM real.</footer>')
    partes.append(f"<script>{JS}</script></main></body></html>")
    return "".join(partes)


def resumo_console(dados):
    c = dados["contagem"]
    linhas = [f"Testes: {dados['total']} · passaram {c['ok']} · falharam {c['falha']} · erros {c['erro']} · "
              f"ignorados {c['ignorado']} · {dados['duracao_s']:.2f}s"]
    for r in dados["registros"]:
        if r["status"] in RUINS:
            linhas.append(f"  {ICONES[r['status']]} {r['id']}")
    linhas.append("RESULTADO: " + ("OK" if aprovado(dados) else "COM PROBLEMAS"))
    return "\n".join(linhas)


def main(argv=None):
    p = argparse.ArgumentParser(description="Roda os testes e gera um relatório HTML.")
    p.add_argument("--pasta-testes", type=Path, default=AQUI / "tests")
    p.add_argument("--filtro", help="Só testes cujo identificador contém este texto (ex.: juiz).")
    p.add_argument("--saida", type=Path, help="Arquivo HTML de saída (não sobrescreve).")
    p.add_argument("--sem-abrir", action="store_true", help="Não abre o navegador.")
    args = p.parse_args(argv)
    if not args.pasta_testes.is_dir():
        print(f"Pasta de testes não encontrada: {args.pasta_testes}", file=sys.stderr)
        return 2
    dados = executar(args.pasta_testes, args.filtro)
    destino = args.saida or AQUI / "local" / "relatorio_testes" / f"relatorio-{dados['gerado_em']:%Y%m%d-%H%M%S}.html"
    try:
        destino.parent.mkdir(parents=True, exist_ok=True)
        with destino.open("x", encoding="utf-8", newline="\n") as arquivo:
            arquivo.write(renderizar_html(dados))
    except OSError as erro:
        print(f"Não foi possível gravar o relatório: {erro}", file=sys.stderr)
        return 2
    print(resumo_console(dados))
    print(f"Relatório: {destino}")
    if not args.sem_abrir:
        webbrowser.open(destino.resolve().as_uri())
    if dados["total"] == 0:
        return 2
    return 0 if aprovado(dados) else 1


if __name__ == "__main__":
    sys.exit(main())
