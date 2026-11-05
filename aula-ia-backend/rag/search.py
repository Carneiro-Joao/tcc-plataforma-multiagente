"""Recuperação da BNCC compartilhada pelo terminal e pela API local."""
import argparse
import json
import os
from pathlib import Path
import pickle
import unicodedata
from threading import Lock

if __package__:
    from .termos import TERMOS
else:
    from termos import TERMOS

BASE = Path(__file__).resolve().parents[1]
ARQUIVO = BASE / "data" / "bncc_8ano.json"
MODELO = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
REVISAO = "e8f8c211226b894fcb81acc59f3b34ba3efd5f42"
FONTE = "Computação na Educação Básica – Complemento à BNCC"


def normalizar_texto(texto):
    simples = unicodedata.normalize("NFD", texto.lower())
    return " ".join("".join(c for c in simples if not unicodedata.combining(c)).split())


def calcular_bonus(pergunta, documento):
    """Mesmos pesos, comparações por substring e limites de contagem do protótipo."""
    consulta = normalizar_texto(pergunta)

    def contar(texto, minimo):
        return sum(len(p) >= minimo and p in consulta for p in normalizar_texto(texto).split())

    codigo = documento["codigo"]
    bonus = 0.50 if codigo.lower() in consulta else 0.0
    bonus += 0.25 * min(contar(documento["objeto_conhecimento"], 4), 2)
    bonus += 0.20 * min(contar(documento["habilidade"], 5), 2)
    if any(contar(exemplo, 5) for exemplo in documento["exemplos"]):
        bonus += 0.30
    return bonus + 0.35 * sum(termo in consulta for termo in TERMOS.get(codigo, ()))


class DocumentosPrimitivos(pickle.Unpickler):
    def find_class(self, module, name):
        raise ValueError("O índice de documentos deve conter apenas dados simples.")


class BuscaCurricular:
    def __init__(self, modo="lexical"):
        dados = json.loads(ARQUIVO.read_text(encoding="utf-8"))
        self.ano = dados["ano"]
        self.documentos = dados["habilidades"]
        self.modo = modo
        if modo == "hibrido":
            self._carregar_modelo()

    def _carregar_modelo(self):
        import numpy as np
        from sentence_transformers import SentenceTransformer

        pasta = BASE / "database"
        with (pasta / "bncc_8ano_documentos.pkl").open("rb") as f:
            ordem = DocumentosPrimitivos(f).load()
        campos = ("codigo", "habilidade", "eixo", "objeto_conhecimento", "explicacao", "exemplos", "pagina_pdf")
        if [tuple(d[k] for k in campos) for d in ordem] != [
            tuple(d[k] for k in campos) for d in self.documentos
        ]:
            raise ValueError("O catálogo diverge dos documentos usados para gerar os embeddings.")
        self.embeddings = np.load(pasta / "bncc_8ano_embeddings.npy", allow_pickle=False)
        if self.embeddings.shape != (len(ordem), 384):
            raise ValueError("Dimensões incompatíveis no arquivo de embeddings do 8º ano.")
        self.trava_modelo = Lock()
        pasta_local = os.environ.get("BNCC_MODELO_DIR")
        self.modelo = SentenceTransformer(
            pasta_local or MODELO, revision=None if pasta_local else REVISAO, device="cpu"
        )

    def buscar(self, pergunta, quantidade=5, eixo=None, codigo=None, objeto=None):
        indices = [i for i, doc in enumerate(self.documentos)
                   if (not eixo or doc["eixo"].casefold() == eixo.casefold())
                   and (not codigo or doc["codigo"].upper() == codigo.upper())
                   and (not objeto or objeto.casefold() in doc["objeto_conhecimento"].casefold())]
        if not indices:
            return []
        semanticos = {}
        if self.modo == "hibrido":
            import numpy as np
            with self.trava_modelo:
                vetor = self.modelo.encode([pergunta], convert_to_numpy=True)[0].astype("float32")
            vetor = vetor / max(np.linalg.norm(vetor), 1e-12)
            semanticos = dict(zip(indices, (self.embeddings[indices] @ vetor).tolist()))
        resultados = []
        for i in indices:
            doc = self.documentos[i]
            bonus = calcular_bonus(pergunta, doc)
            if self.modo == "lexical" and not bonus:
                continue
            resultados.append(dict(doc, ano=self.ano, score_semantico=semanticos.get(i),
                                   bonus=bonus, score_final=semanticos.get(i, 0) + bonus))
        return sorted(resultados, key=lambda r: r["score_final"], reverse=True)[:quantidade]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--modo", choices=("hibrido", "lexical"), default="hibrido")
    parser.add_argument("--consulta", help="Consulta única. Sem esta opção, abre o terminal interativo.")
    args = parser.parse_args()
    busca = BuscaCurricular(args.modo)
    print("BNCC de Computação | 8º ano | modo", args.modo)
    while True:
        pergunta = args.consulta or input("Pergunta (sair para encerrar): ").strip()
        if pergunta.lower() in ("sair", "exit", "quit"):
            break
        if not pergunta:
            continue
        filtros = {} if args.consulta else {
            k: input(f"{k.capitalize()} (opcional): ").strip() for k in ("eixo", "codigo", "objeto")
        }
        resultados = busca.buscar(pergunta, **filtros)
        for i, r in enumerate(resultados, 1):
            score = r["score_semantico"]
            print(f"\n{i}. {r['codigo']} — {r['habilidade']}\n{r['eixo']} | {r['objeto_conhecimento']}")
            print(r["explicacao"], *r["exemplos"], sep="\n")
            print(f"PDF: habilidade p. {r['pagina_habilidade']}, exemplos p. {r['pagina_pdf']}")
            print(f"Semântico: {score:.4f}" if score is not None else "Semântico: desativado")
            print(f"Bônus: {r['bonus']:.4f} | Final: {r['score_final']:.4f}")
        if not resultados:
            print("Nenhuma habilidade encontrada.")
        if args.consulta:
            break


if __name__ == "__main__":
    main()
