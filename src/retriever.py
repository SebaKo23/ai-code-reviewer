import re
from typing import List, Dict, Any
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

from src.config import CHROMA_DIR, EMBEDDING_MODEL_NAME


def parse_git_diff(diff_text: str) -> str:
    """
    Cleans the raw git diff file, removing git metadata and deleted lines (-).
    Returns a clean string of added/changed code (+).
    """
    added_lines = []
    for line in diff_text.splitlines():
        # Ignoring diff file headers (e.g. +++ b/src/user_processor.py)
        if line.startswith("+++") or line.startswith("---") or line.startswith("@@"):
            continue
        # Extracting only added lines (+)
        if line.startswith("+"):
            added_lines.append(line[1:].strip()) # Removing the '+' sign at the beginning

    clean_code = "\n".join(added_lines)
    return clean_code


class ContextRetriever:
    def __init__(self):
        # Loading the same local embedding model
        self.embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
        # Connecting to the ChromaDB database existing on disk
        self.vector_store = Chroma(
            persist_directory=str(CHROMA_DIR),
            embedding_function=self.embeddings
        )

    def get_relevant_context(self, diff_text: str, k_code: int = 2, k_style: int = 2) -> Dict[str, List[Document]]:
        """
        Retrieves relevant code and styleguide rules from the ChromaDB database based on the diff.
        """
        clean_query = parse_git_diff(diff_text)
        
        if not clean_query.strip():
            print("Diff does not contain any added lines of code.")
            return {"code_context": [], "styleguide_context": []}

        print(f"Querying the vector database (cleaned diff):\n'{clean_query[:100]}...'")

        # 1. Searching for relevant code (with filter on source_type = 'code')
        code_docs = self.vector_store.similarity_search(
            query=clean_query,
            k=k_code,
            filter={"source_type": "code"}
        )

        # 2. Searching for styleguide rules (with filter on source_type = 'styleguide')
        styleguide_docs = self.vector_store.similarity_search(
            query=clean_query,
            k=k_style,
            filter={"source_type": "styleguide"}
        )

        return {
            "code_context": code_docs,
            "styleguide_context": styleguide_docs
        }


# Section for testing (runs directly)
if __name__ == "__main__":
    from pathlib import Path
    
    sample_diff_path = Path("sample.diff")
    if not sample_diff_path.exists():
        print("No sample.diff file found! Create it before running.")
    else:
        diff_content = sample_diff_path.read_text(encoding="utf-8")
        
        retriever = ContextRetriever()
        context = retriever.get_relevant_context(diff_content)

        print("\n--- RETRIEVED STYLEGUIDE RULES ---")
        for i, doc in enumerate(context["styleguide_context"], 1):
            print(f"[{i}] {doc.page_content}\n")

        print("--- RETRIEVED CODE CONTEXT ---")
        for i, doc in enumerate(context["code_context"], 1):
            print(f"[{i}] Plik: {doc.metadata.get('source', 'Unknown')}\n{doc.page_content}\n")