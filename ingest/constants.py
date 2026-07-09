from pathlib import Path
from typing import Final

MAX_CHAPTERS: Final[int] = 20
NCERT_PDF_BASE: Final[str] = "https://ncert.nic.in/textbook/pdf"
MANIFEST_PATH: Final[Path] = Path("data/manifest.json")
RAW_DIR: Final[Path] = Path("data/raw")

# Insert a space when the gap between two glyphs exceeds this fraction of the font
# size. NCERT PDFs often omit space glyphs; tune on real pages (lower = more splits).
CHAR_GAP_RATIO: Final[float] = 0.10

GENERATED_DIR: Final[Path] = Path("data/generated")
CHUNKS_PATH: Final[Path] = GENERATED_DIR / "chunks.jsonl"
CHUNK_CHARS: Final[int] = 1200
CHUNK_OVERLAP: Final[int] = 200

EMBED_MODEL: Final[str] = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDINGS_PATH: Final[Path] = GENERATED_DIR / "embeddings.npy"