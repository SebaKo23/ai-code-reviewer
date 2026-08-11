import sys
from pathlib import Path
from langchain_community.document_loaders import TextLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter, Language
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

from src.config import CHROMA_DIR, STYLEGUIDE_PATH, SRC_DIR, EMBEDDING_MODEL_NAME


def run_ingestion():
    print("Rozpoczynam proces indeksowania (Ingestion)...")

    documents = []

    # 1. Ładowanie pliku STYLEGUIDE.md
    if STYLEGUIDE_PATH.exists():
        print(f"Wczytuję wytyczne stylu: {STYLEGUIDE_PATH.name}")
        styleguide_loader = TextLoader(str(STYLEGUIDE_PATH), encoding="utf-8")
        styleguide_docs = styleguide_loader.load()
        
        # Oznaczamy w metadanych typ dokumentu (kluczowe dla późniejszego filtrowania)
        for doc in styleguide_docs:
            doc.metadata["source_type"] = "styleguide"
        
        # Dzielimy styleguide zwykłym splitterem tekstowym
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=30)
        styleguide_chunks = text_splitter.split_documents(styleguide_docs)
        documents.extend(styleguide_chunks)
        print(f"Utworzono {len(styleguide_chunks)} fragmentów z wytycznych.")
    else:
        print("Brak pliku STYLEGUIDE.md! Pomiń ten etap.")

    # 2. Ładowanie kodu źródłowego z folderu src/
    if SRC_DIR.exists():
        print(f"Wczytuję kod źródłowy z: {SRC_DIR.name}/")
        code_loader = DirectoryLoader(
            str(SRC_DIR),
            glob="**/*.py",
            loader_cls=TextLoader,
            loader_kwargs={"encoding": "utf-8"}
        )
        code_docs = code_loader.load()

        for doc in code_docs:
            doc.metadata["source_type"] = "code"

        # Dzielimy kod Pythonowy splitterem świadomym składni języka (Language-aware)
        python_splitter = RecursiveCharacterTextSplitter.from_language(
            language=Language.PYTHON,
            chunk_size=400,
            chunk_overlap=40
        )
        code_chunks = python_splitter.split_documents(code_docs)
        documents.extend(code_chunks)
        print(f"Utworzono {len(code_chunks)} fragmentów kodu Python.")
    else:
        print("Brak katalogu src/!")

    if not documents:
        print("Brak dokumentów do zaindeksowania.")
        return

    # 3. Inicjalizacja darmowego modelu embeddingów lokalnych
    print(f"Ładowanie modelu embeddingów: {EMBEDDING_MODEL_NAME}...")
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)

    # 4. Tworzenie/aktualizacja bazy wektorowej ChromaDB
    print(f"Zapisywanie wektorów w bazie ChromaDB pod ścieżką: {CHROMA_DIR}...")
    
    # Chroma.from_documents automatycznie generuje embeddingi i zapisuje je na dysku
    vector_store = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        persist_directory=str(CHROMA_DIR)
    )

    print("Indeksowanie zakończone sukcesem!")


if __name__ == "__main__":
    run_ingestion()