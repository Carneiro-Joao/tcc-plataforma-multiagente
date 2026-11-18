"""Variantes controladas para ensaiar a IA Juiz: um campo alterado por variante, com pré-registro.

A partir de um caso congelado (casos_juiz) e de uma especificação, confere que o valor original
confere com o caso, altera UM campo de texto, prova que nada mais mudou, valida o plano 2.0 pelo
contrato mecânico, calcula os hashes canônicos e grava o caso e o protocolo de pré-registro.

A hipótese (o que o Juiz deveria apontar) vive só na especificação e no protocolo: nunca entra no
caso nem na requisição ao Juiz. Os arquivos nunca são sobrescritos.
"""
import argparse
from copy import deepcopy
from datetime import date
import json
from pathlib import Path
import re
import sys

from casos_juiz import carregar_caso, hash_json, salvar_novo, validar_caso
from contratos import juiz_v1 as contrato
from contratos.execucao import ler_json

RAIZ = Path(__file__).resolve().parents[1]
CAMPOS_COMPARADOS = ("plano", "entrada", "modelo_gerador", "revisao")
OBRIGATORIOS = ("id_variante", "numero", "caso_base", "campo", "valor_original", "valor_novo",
                "arquivo_caso", "arquivo_protocolo", "titulo", "tipo_defeito", "descricao_manipulacao", "hipotese")
HIPOTESE_OBRIGATORIA = ("principal", "criterio_esperado", "componente_esperado")
ROTULOS_HIPOTESE = (
    ("principal", "Hipótese principal"),
    ("criterio_esperado", "Critério esperado"),
    ("aceito_com_ressalva", "Aceito como detecção parcial"),
    ("componente_esperado", "Componente responsável esperado"),
    ("gravidade_provavel", "Gravidade provável"),
    ("nota_esperada", "Nota esperada"),
    ("resultado_negativo", "Resultado negativo"),
    ("falsos_positivos", "Falsos positivos"),
    ("observacao_de_desenho", "Observação de desenho"),
)
NATUREZA_PADRAO = ("Não classificada na especificação. Declare se o tipo de defeito já aparece na rubrica ou no prompt "
                   "(nesse caso o ensaio mede a aplicação da rubrica, não a descoberta de defeitos imprevistos) e se o "
                   "plano-base já foi usado no desenvolvimento.")
OBSERVACAO_ORIGEM = ("Variante editada para experimento; nao foi gerada pelo Gemini. "
                     "Modelo_gerador refere-se somente ao plano original.")
_PASSO = re.compile(r"\.?([A-Za-z_][A-Za-z0-9_]*)|\[(\d+)\]")


# ----------------------------------------------------------------- caminhos de campo

def passos(campo):
    """'plano.desenvolvimento[0].acao_docente' -> ['plano', 'desenvolvimento', 0, 'acao_docente']."""
    if not isinstance(campo, str):
        raise ValueError("O campo deve ser texto, como plano.desenvolvimento[0].acao_docente.")
    achados, pos = [], 0
    while pos < len(campo):
        m = _PASSO.match(campo, pos)
        if not m:
            raise ValueError(f"Caminho de campo inválido: {campo!r}")
        achados.append(m.group(1) if m.group(1) is not None else int(m.group(2)))
        pos = m.end()
    if len(achados) < 2 or achados[0] != "plano":
        raise ValueError("O campo deve começar por 'plano.' e apontar para um item interno do plano.")
    return achados


def ler_campo(caso, campo):
    no = caso
    for passo in passos(campo):
        try:
            no = no[passo]
        except (KeyError, IndexError, TypeError):
            raise ValueError(f"Campo inexistente no caso-base: {campo}") from None
    return no


def definir_campo(caso, campo, valor):
    ler_campo(caso, campo)  # nunca cria campos novos
    sequencia = passos(campo)
    pai = caso
    for passo in sequencia[:-1]:
        pai = pai[passo]
    pai[sequencia[-1]] = valor


def diferencas(a, b, caminho=""):
    """Caminhos de todas as folhas que diferem entre dois valores JSON."""
    if isinstance(a, dict) and isinstance(b, dict):
        achadas = []
        for chave in list(a) + [k for k in b if k not in a]:
            filho = f"{caminho}.{chave}" if caminho else str(chave)
            if chave not in a or chave not in b:
                achadas.append(filho)
            else:
                achadas += diferencas(a[chave], b[chave], filho)
        return achadas
    if isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        achadas = []
        for i, (x, y) in enumerate(zip(a, b)):
            achadas += diferencas(x, y, f"{caminho}[{i}]")
        return achadas
    return [] if type(a) is type(b) and a == b else [caminho or "$"]


# ------------------------------------------------------------------------ criação

def validar_especificacao(spec):
    if not isinstance(spec, dict):
        raise ValueError("A especificação deve ser um objeto JSON.")
    faltam = [k for k in OBRIGATORIOS if k not in spec]
    if faltam:
        raise ValueError(f"Especificação sem: {', '.join(faltam)}.")
    if not re.fullmatch(r"V\d{2}", str(spec["numero"])):
        raise ValueError("numero deve ter o formato V03.")
    if not str(spec["id_variante"]).startswith(spec["numero"] + "-"):
        raise ValueError("id_variante deve começar por numero seguido de hífen.")
    for chave in ("valor_original", "valor_novo"):
        if not isinstance(spec[chave], str) or not spec[chave].strip():
            raise ValueError(f"{chave} deve ser um texto não vazio (esta ferramenta altera campos de texto).")
    if spec["valor_original"] == spec["valor_novo"]:
        raise ValueError("valor_novo é igual ao valor_original.")
    if not isinstance(spec["hipotese"], dict) or any(not spec["hipotese"].get(k) for k in HIPOTESE_OBRIGATORIA):
        raise ValueError(f"A hipótese exige: {', '.join(HIPOTESE_OBRIGATORIA)}.")
    if "observacao_origem" in spec and not (isinstance(spec["observacao_origem"], str) and spec["observacao_origem"].strip()):
        raise ValueError("observacao_origem, quando informada, deve ser um texto não vazio.")
    passos(spec["campo"])


def criar_variante(spec, raiz=RAIZ):
    """Devolve o caso da variante (dict). Não grava nada."""
    validar_especificacao(spec)
    base = carregar_caso(Path(raiz) / spec["caso_base"])
    atual = ler_campo(base, spec["campo"])
    if atual != spec["valor_original"]:
        raise ValueError("valor_original difere do caso-base congelado; confira o campo e o texto exato.")
    novo = {chave: deepcopy(base[chave]) for chave in CAMPOS_COMPARADOS}
    definir_campo(novo, spec["campo"], spec["valor_novo"])
    alterados = diferencas({k: base[k] for k in CAMPOS_COMPARADOS}, novo)
    if alterados != [spec["campo"]]:
        raise ValueError(f"A variante deve alterar somente {spec['campo']}; alterou: {alterados}")
    novo["origem"] = dict(
        tipo="variante_controlada", id_variante=spec["id_variante"], caso_base=spec["caso_base"],
        geracao_id_base=base["origem"].get("geracao_id"), plano_base_sha256=hash_json(base["plano"]),
        entrada_base_sha256=hash_json(base["entrada"]), campo_alterado=spec["campo"],
        plano_sha256=hash_json(novo["plano"]), entrada_sha256=hash_json(novo["entrada"]),
        observacao=spec.get("observacao_origem") or OBSERVACAO_ORIGEM)
    return validar_caso(novo)


# --------------------------------------------------------------------- protocolo

def _bloco(texto):
    return "> " + str(texto).replace("\n", "\n> ")


def renderizar_protocolo(spec, caso, base, data_iso):
    d, hip = caso["origem"], spec["hipotese"]
    dd = "/".join(reversed(data_iso.split("-")))
    arquivo_caso = spec["arquivo_caso"]
    caminho_caso = "../" + arquivo_caso
    linhas = [
        f"# PoC 05C / RD-002 — Pré-registro da variante {spec['numero']}: {spec['titulo']}", "",
        f"**Data do pré-registro:** {dd}. **Situação:** hipótese congelada antes de qualquer chamada do Juiz com esta "
        "variante. Este documento é um protocolo de pesquisador, **não deve ser enviado à LLM**. "
        "**Faça o commit deste arquivo e do caso antes da primeira chamada real.**", "",
        "## 1. Origem e integridade", "",
        f"- **Caso real de referência:** `{spec['caso_base']}`, geração `{d['geracao_id_base']}`.",
        f"- **Variante controlada:** `{arquivo_caso}` (`origem.tipo=variante_controlada`, `id_variante={d['id_variante']}`).",
        f"- **SHA-256 canônico do plano original:** `{d['plano_base_sha256']}`.",
        f"- **SHA-256 canônico do plano da variante:** `{d['plano_sha256']}`.",
        f"- **SHA-256 canônico da entrada (idêntica à original):** `{d['entrada_sha256']}`.",
        f"- **SHA-256 da hipótese (JSON canônico da seção 3):** `{hash_json(hip)}`.",
        f"- **Modelo gerador registrado:** `{caso['modelo_gerador']}`, herdado somente para rastrear a origem do plano-base; "
        "a modificação foi feita pela ferramenta `variantes_juiz.py`, a partir de uma especificação versionada.",
        f"- **Juiz a avaliar:** `openai/gpt-oss-120b` via GroqCloud, prompt `{contrato.VERSAO_PROMPT}`, contrato "
        f"`{contrato.VERSAO}`, rubrica `{contrato.rubrica.VERSAO}`, política `{contrato.POLITICA_PRELIMINAR['nome']}`.",
        f"- **Natureza do conjunto:** {spec.get('natureza_do_conjunto') or NATUREZA_PADRAO}", "",
        "## 2. Manipulação isolada", "",
        f"Uma **única propriedade** foi alterada: `{spec['campo']}`.", "",
        "**Valor do caso real:**", "", _bloco(spec["valor_original"]), "",
        f"**Valor na {spec['numero']}:**", "", _bloco(spec["valor_novo"]), "",
        spec["descricao_manipulacao"], "",
        "A ferramenta verificou que o valor original coincide com o caso congelado, que nenhum outro campo "
        "(inclusive a entrada confirmada) mudou e que o plano continua válido pelo contrato mecânico "
        "PlanoDeAula 2.0. A alteração é **semântica**: o validador Python não a detecta.", "",
        "## 3. Hipótese registrada antes do ensaio", ""]
    for chave, rotulo in ROTULOS_HIPOTESE:
        if hip.get(chave):
            linhas.append(f"- **{rotulo}:** {hip[chave]}")
    linhas += [
        "", "Esta expectativa é uma **hipótese do pesquisador, não um gabarito cientificamente validado**. "
        "Não ajustar a hipótese após observar a resposta do modelo; se for preciso corrigi-la, registre a "
        "correção como nova versão e preserve esta.", "",
        "## 4. Procedimento", "",
        "1. Validar localmente, sem rede nem chave (`--somente-validar`).",
        f"2. Executar o Juiz real com os mesmos parâmetros do controle original: prompt `{contrato.VERSAO_PROMPT}`, "
        "temperatura 0, seed 42, `reasoning_effort=medium`, máximo 8192 tokens, `--reparos 1`.",
        "3. Obter **três pareceres válidos**, esperando pelo menos 75 segundos entre chamadas (cota de ~8.000 tokens "
        "por minuto; cada julgamento consome ~7.000 a 8.200). Registrar **todas** as tentativas; HTTP 400, 429 e "
        "recusas são falhas técnicas, nunca detecção nem falso negativo.",
        "4. Preservar `inicio.json`, `caso.json` e `resultado.json` de cada execução; guardar cópia de segurança "
        "fora de `local/`.",
        "5. Verificar primeiro HTTP, contrato, invariantes e rastreio; depois comparar falhas, justificativas, "
        "componentes e decisão à hipótese. **Apontar qualquer falha não é detectar a falha-alvo.**",
        "6. Encaminhar a pertinência pedagógica e a gravidade a um avaliador humano; uma série pequena não mede "
        "estabilidade, sensibilidade nem especificidade.", "",
        "## 5. Comandos (PowerShell, na pasta `aula-ia-backend`)", "", "Validação offline:", "",
        "```powershell",
        f"python ensaio_juiz.py avaliar --caso {caminho_caso} --somente-validar", "```", "",
        "Série real (somente após a validação e o commit; precisa de `GROQ_API_KEY` no terminal):", "",
        "```powershell",
        f"1..3 | ForEach-Object {{ python ensaio_juiz.py avaliar --caso {caminho_caso} "
        f"--versao-prompt {contrato.VERSAO_PROMPT} --reparos 1; Start-Sleep -Seconds 75 }}", "```", "",
        "Integridade (detecta edição do caso depois do pré-registro):", "",
        "```powershell",
        f"python variantes_juiz.py verificar --spec ../experimentos/juiz/variantes/{Path(spec['arquivo_caso']).stem}.spec.json",
        "```", "",
        "## 6. Resultados observados", "",
        "*A preencher depois das execuções. Não alterar as seções 1 a 5.*", ""]
    return "\n".join(linhas)


# --------------------------------------------------------------------------- CLI

def carregar_especificacao(caminho):
    spec = ler_json(Path(caminho).read_text(encoding="utf-8-sig"))
    validar_especificacao(spec)
    return spec


def serializar_caso(caso):
    return json.dumps(caso, ensure_ascii=False, indent=2, allow_nan=False) + "\n"


def comando_criar(args):
    spec = carregar_especificacao(args.spec)
    caso = criar_variante(spec, args.raiz)
    base = carregar_caso(args.raiz / spec["caso_base"])
    protocolo = renderizar_protocolo(spec, caso, base, args.data)
    destino_caso, destino = args.raiz / spec["arquivo_caso"], args.raiz / spec["arquivo_protocolo"]
    for existente in (destino_caso, destino):  # atômico: confere os dois antes de gravar qualquer um
        if existente.exists():
            raise FileExistsError(f"Já existe e não será sobrescrito: {existente}")
    salvar_novo(destino_caso, caso)
    destino.parent.mkdir(parents=True, exist_ok=True)
    with destino.open("x", encoding="utf-8", newline="\n") as arquivo:
        arquivo.write(protocolo if protocolo.endswith("\n") else protocolo + "\n")
    print(f"Caso:      {spec['arquivo_caso']}\nProtocolo: {spec['arquivo_protocolo']}")
    print(f"SHA-256 do plano da variante: {caso['origem']['plano_sha256']}")
    print(f"SHA-256 da hipótese:          {hash_json(spec['hipotese'])}")
    print("Faça o commit do caso e do protocolo ANTES da primeira chamada real ao Juiz.")
    return 0


def comando_verificar(args):
    spec = carregar_especificacao(args.spec)
    esperado = serializar_caso(criar_variante(spec, args.raiz))
    arquivo = args.raiz / spec["arquivo_caso"]
    atual = arquivo.read_text(encoding="utf-8").replace("\r\n", "\n")
    protocolo = args.raiz / spec["arquivo_protocolo"]
    problemas = []
    if atual != esperado:
        problemas.append(f"O caso {spec['arquivo_caso']} difere do que a especificação gera.")
    if not protocolo.exists():
        problemas.append(f"Protocolo ausente: {spec['arquivo_protocolo']}.")
    elif hash_json(spec["hipotese"]) not in protocolo.read_text(encoding="utf-8"):
        problemas.append("O hash da hipótese no protocolo não confere com a especificação.")
    for problema in problemas:
        print("FALHA:", problema, file=sys.stderr)
    if not problemas:
        print(f"OK: {spec['id_variante']} íntegra (caso, hash do plano e hipótese conferem).")
    return 1 if problemas else 0


def main(argv=None):
    parser = argparse.ArgumentParser(description="Variantes controladas para ensaiar a IA Juiz.")
    parser.add_argument("--raiz", type=Path, default=RAIZ, help="Raiz do repositório.")
    sub = parser.add_subparsers(dest="comando", required=True)
    criar = sub.add_parser("criar", help="Gera caso e protocolo a partir de uma especificação.")
    criar.add_argument("--spec", required=True, type=Path)
    criar.add_argument("--data", default=date.today().isoformat(), help="AAAA-MM-DD do pré-registro.")
    criar.set_defaults(funcao=comando_criar)
    verificar = sub.add_parser("verificar", help="Confere caso e protocolo contra a especificação.")
    verificar.add_argument("--spec", required=True, type=Path)
    verificar.set_defaults(funcao=comando_verificar)
    args = parser.parse_args(argv)
    try:
        return args.funcao(args)
    except (ValueError, FileExistsError, FileNotFoundError, OSError) as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
