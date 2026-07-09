import json

import numpy as np
from sentence_transformers import SentenceTransformer

from ingest.constants import CHUNKS_PATH, EMBED_MODEL, EMBEDDINGS_PATH


def chunk_texts() -> list[str]:
    lines = CHUNKS_PATH.read_text(encoding="utf-8").splitlines()
    return [json.loads(line)["text"] for line in lines if line.strip()]


def main() -> None:
    texts = chunk_texts()
    model = SentenceTransformer(EMBED_MODEL)
    vectors = model.encode(
        texts, batch_size=64, normalize_embeddings=True, show_progress_bar=True
    )
    np.save(EMBEDDINGS_PATH, vectors.astype("float32"))
    print(f"embedded {len(texts)} chunks -> {EMBEDDINGS_PATH} shape {vectors.shape}")


if __name__ == "__main__":
    main()