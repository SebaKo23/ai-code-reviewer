import sys
from pathlib import Path
from langchain_community.document_loaders import TextLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter, Language
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

from src.config import CHROMA_DIR, STYLEGUIDE_PATH, SRC_DIR, EMBEDDING_MODEL_NAME

def run_ingestion():
    """
    Launches the ingestion process.
    It takes the STYLEGUIDE.md file and code from the src/ folder and saves them in the ChromaDB vector database.
    """
    print("Starting the ingestion process...")

    documents = []

    # 1. Loading the STYLEGUIDE.md file
    if STYLEGUIDE_PATH.exists():
        print(f"Loading style guidelines: {STYLEGUIDE_PATH.name}")
        styleguide_loader = TextLoader(str(STYLEGUIDE_PATH), encoding="utf-8")
        styleguide_docs = styleguide_loader.load()
        
        # Marking the document type in the metadata (crucial for later filtering)
        for doc in styleguide_docs:
            doc.metadata["source_type"] = "styleguide"
        
        # Splitting the styleguide into chunks
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=30)
        styleguide_chunks = text_splitter.split_documents(styleguide_docs)
        documents.extend(styleguide_chunks)
        print(f"Created {len(styleguide_chunks)} chunks from the guidelines.")
    else:
        print("No STYLEGUIDE.md file found! Skipping this step.")

    # 2. Loading the source code from the src/ folder
    if SRC_DIR.exists():
        print(f"Loading source code from: {SRC_DIR.name}/")
        code_loader = DirectoryLoader(
            str(SRC_DIR),
            glob="**/*.py",
            loader_cls=TextLoader,
            loader_kwargs={"encoding": "utf-8"}
        )
        code_docs = code_loader.load()

        for doc in code_docs:
            doc.metadata["source_type"] = "code"

        # Splitting the Python code into chunks using a language-aware splitter
        python_splitter = RecursiveCharacterTextSplitter.from_language(
            language=Language.PYTHON,
            chunk_size=400,
            chunk_overlap=40
        )
        code_chunks = python_splitter.split_documents(code_docs)
        documents.extend(code_chunks)
        print(f"Created {len(code_chunks)} chunks of Python code.")
    else:
        print("No src/ directory found!")

    if not documents:
        print("No documents to index.")
        return

    # 3. Initializing the free local embedding model
    print(f"Loading embedding model: {EMBEDDING_MODEL_NAME}...")
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)

    # 4. Creating/updating the ChromaDB vector database
    print(f"Saving vectors to ChromaDB database at: {CHROMA_DIR}...")
    
    # Chroma.from_documents automatically generates embeddings and saves them to disk
    vector_store = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        persist_directory=str(CHROMA_DIR)
    )

    print("Indexing completed successfully!")


if __name__ == "__main__":
    run_ingestion()