import json
import os
import pickle

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


# =========================================================
# CONFIGURAÇÕES
# =========================================================

JSON_PATH = "data/bncc_8ano.json"

DATABASE_DIR = "database"

INDEX_PATH = os.path.join(
    DATABASE_DIR,
    "bncc_8ano.index"
)

DOCUMENTS_PATH = os.path.join(
    DATABASE_DIR,
    "bncc_8ano_documentos.pkl"
)

EMBEDDINGS_PATH = os.path.join(
    DATABASE_DIR,
    "bncc_8ano_embeddings.npy"
)

MODELO_EMBEDDING = (
    "sentence-transformers/"
    "paraphrase-multilingual-MiniLM-L12-v2"
)


# =========================================================
# VALIDAR ARQUIVO
# =========================================================

if not os.path.exists(JSON_PATH):

    raise FileNotFoundError(
        f"""
Arquivo não encontrado:

{JSON_PATH}

Coloque o arquivo bncc_8ano.json
dentro da pasta data.
"""
    )


# =========================================================
# CARREGAR JSON
# =========================================================

print("\n========================================")
print("CARREGANDO BASE ESTRUTURADA DA BNCC")
print("========================================")


with open(
    JSON_PATH,
    "r",
    encoding="utf-8"
) as arquivo:

    dados = json.load(
        arquivo
    )


habilidades = dados.get(
    "habilidades",
    []
)


if not habilidades:

    raise ValueError(
        "Nenhuma habilidade encontrada no JSON."
    )


print(
    f"{len(habilidades)} habilidades carregadas."
)


# =========================================================
# PREPARAR DOCUMENTOS
# =========================================================

print("\n========================================")
print("PREPARANDO DOCUMENTOS")
print("========================================")


documentos = []


for habilidade in habilidades:

    codigo = habilidade.get(
        "codigo",
        ""
    )

    eixo = habilidade.get(
        "eixo",
        ""
    )

    objeto = habilidade.get(
        "objeto_conhecimento",
        ""
    )

    descricao = habilidade.get(
        "habilidade",
        ""
    )

    explicacao = habilidade.get(
        "explicacao",
        ""
    )

    exemplos = habilidade.get(
        "exemplos",
        []
    )

    pagina = habilidade.get(
        "pagina_pdf"
    )


    # -----------------------------------------------------
    # Texto que será transformado em embedding
    # -----------------------------------------------------

    texto_embedding = f"""
Ano: 8º ano
Código da habilidade: {codigo}
Eixo: {eixo}
Objeto de conhecimento: {objeto}

Habilidade:
{descricao}

Explicação:
{explicacao}

Exemplos:
{"; ".join(exemplos)}
""".strip()


    documentos.append(
        {
            "ano": "8º ano",

            "codigo": codigo,

            "eixo": eixo,

            "objeto_conhecimento": objeto,

            "habilidade": descricao,

            "explicacao": explicacao,

            "exemplos": exemplos,

            "pagina_pdf": pagina,

            "texto_embedding": texto_embedding
        }
    )


print(
    f"{len(documentos)} documentos preparados."
)


# =========================================================
# MOSTRAR DOCUMENTOS
# =========================================================

for documento in documentos:

    print("\n----------------------------------------")

    print(
        f"Código: "
        f"{documento['codigo']}"
    )

    print(
        f"Eixo: "
        f"{documento['eixo']}"
    )

    print(
        f"Objeto: "
        f"{documento['objeto_conhecimento']}"
    )


# =========================================================
# CARREGAR MODELO
# =========================================================

print("\n========================================")
print("CARREGANDO MODELO DE EMBEDDINGS")
print("========================================")


modelo = SentenceTransformer(
    MODELO_EMBEDDING
)


print(
    "Modelo carregado."
)


# =========================================================
# GERAR EMBEDDINGS
# =========================================================

print("\n========================================")
print("GERANDO EMBEDDINGS")
print("========================================")


textos = [

    documento["texto_embedding"]

    for documento in documentos
]


embeddings = modelo.encode(
    textos,
    show_progress_bar=True,
    convert_to_numpy=True
)


embeddings = np.asarray(
    embeddings,
    dtype="float32"
)


# =========================================================
# NORMALIZAR
# =========================================================

faiss.normalize_L2(
    embeddings
)


print(
    f"{embeddings.shape[0]} embeddings gerados."
)

print(
    f"Dimensão: {embeddings.shape[1]}"
)


# =========================================================
# CRIAR ÍNDICE
# =========================================================

print("\n========================================")
print("CRIANDO ÍNDICE FAISS")
print("========================================")


dimensao = embeddings.shape[1]


index = faiss.IndexFlatIP(
    dimensao
)


index.add(
    embeddings
)


print(
    f"{index.ntotal} documentos indexados."
)


# =========================================================
# SALVAR BANCO
# =========================================================

os.makedirs(
    DATABASE_DIR,
    exist_ok=True
)


faiss.write_index(
    index,
    INDEX_PATH
)


with open(
    DOCUMENTS_PATH,
    "wb"
) as arquivo:

    pickle.dump(
        documentos,
        arquivo
    )


np.save(
    EMBEDDINGS_PATH,
    embeddings
)


# =========================================================
# FINALIZAÇÃO
# =========================================================

print("\n========================================")
print("BASE BNCC 8º ANO CRIADA COM SUCESSO")
print("========================================")


print(
    f"""
Habilidades indexadas: {len(documentos)}

Arquivos gerados:

- {INDEX_PATH}
- {DOCUMENTS_PATH}
- {EMBEDDINGS_PATH}
"""
)