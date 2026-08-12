import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
CHROMA_DIR = BASE_DIR / ".chroma"
STYLEGUIDE_PATH = BASE_DIR / "STYLEGUIDE.md"
SRC_DIR = BASE_DIR / "src"

EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")