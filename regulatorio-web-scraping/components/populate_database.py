import argparse
import os
import shutil
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.schema.document import Document
from get_embedding_function import get_embedding_function
from langchain_chroma import Chroma

# Caminhos definidos de forma relativa ao sistema operacional
CHROMA_PATH = os.path.join(os.getcwd(), "chroma")
DATA_PATH = os.path.join(os.getcwd(), "data")


def main():
    # Verifica se o banco de dados deve ser reiniciado (--reset flag).
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="Reset the database.")
    args = parser.parse_args()
    if args.reset:
        print("✨ Clearing Database")
        clear_database()

    # Cria ou atualiza a base de dados.
    documents = load_documents()
    chunks = split_documents(documents)
    add_to_chroma(chunks)


def load_documents():
    if not os.path.exists(DATA_PATH):
        print(f"❌ O diretório de dados não foi encontrado: {DATA_PATH}")
        return []
    document_loader = PyPDFDirectoryLoader(DATA_PATH)
    return document_loader.load()


def split_documents(documents: list[Document]):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=80,
        length_function=len,
        is_separator_regex=False,
    )
    return text_splitter.split_documents(documents)


def add_to_chroma(chunks: list[Document]):
    # Carrega a base de dados existente.
    db = Chroma(
        persist_directory=CHROMA_PATH, embedding_function=get_embedding_function()
    )

    # Calcula os IDs das páginas.
    chunks_with_ids = calculate_chunk_ids(chunks)

    # Adiciona ou atualiza os documentos.
    existing_items = db.get(include=[])  # IDs são incluídos por padrão
    existing_ids = set(existing_items["ids"])
    print(f"Number of existing documents in DB: {len(existing_ids)}")

    # Apenas adiciona documentos que ainda não existem na base de dados.
    new_chunks = []
    for chunk in chunks_with_ids:
        if chunk.metadata["id"] not in existing_ids:
            new_chunks.append(chunk)

    if len(new_chunks):
        print(f"👉 Adding new documents: {len(new_chunks)}")
        new_chunk_ids = [chunk.metadata["id"] for chunk in new_chunks]
        db.add_documents(new_chunks, ids=new_chunk_ids)
    else:
        print("✅ No new documents to add")


def calculate_chunk_ids(chunks):
    # Isso criará IDs como "data/monopoly.pdf:6:2"
    # Fonte da página : Número da página : Índice do fragmento

    last_page_id = None
    current_chunk_index = 0

    for chunk in chunks:
        source = chunk.metadata.get("source")
        page = chunk.metadata.get("page")
        current_page_id = f"{source}:{page}"

        # Se o ID da página for o mesmo que o anterior, incrementa o índice.
        if current_page_id == last_page_id:
            current_chunk_index += 1
        else:
            current_chunk_index = 0

        # Calcula o ID do fragmento.
        chunk_id = f"{current_page_id}:{current_chunk_index}"
        last_page_id = current_page_id

        # Adiciona ao metadado da página.
        chunk.metadata["id"] = chunk_id

    return chunks


def clear_database():
    if os.path.exists(CHROMA_PATH):
        shutil.rmtree(CHROMA_PATH)
        print(f"✨ Database cleared: {CHROMA_PATH}")
    else:
        print(f"✅ Database path does not exist: {CHROMA_PATH}")


if __name__ == "__main__":
    main()
