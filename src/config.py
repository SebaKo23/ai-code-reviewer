from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CHROMA_DIR = BASE_DIR / ".chroma"
STYLEGUIDE_PATH = BASE_DIR / "STYLEGUIDE.md"
SRC_DIR = BASE_DIR / "src"

EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"