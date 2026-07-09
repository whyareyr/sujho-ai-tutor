import json
from functools import lru_cache

import numpy as np
from sentence_transformers import SentenceTransformer

from ingest.constants import CHUNKS_PATH, EMBED_MODEL, EMBEDDINGS_PATH
from ingest.types import Chunk


class Index:
    """The NCERT search index: chunk metadata + a matrix of normalized embeddings."""

    def __init__(self) -> None:
        lines = CHUNKS_PATH.read_text(encoding="utf-8").splitlines()
        self.chunks = [Chunk.model_validate_json(line) for line in lines if line.strip()]
        self.vectors = np.load(EMBEDDINGS_PATH)
        self.model = SentenceTransformer(EMBED_MODEL)

    def search(self, query: str, k: int) -> list[tuple[Chunk, float]]:
        vector = self.model.encode([query], normalize_embeddings=True)[0]
        scores = self.vectors @ vector
        best = np.argsort(-scores)[:k]
        return [(self.chunks[i], float(scores[i])) for i in best]


@lru_cache(maxsize=1)
def index() -> Index:
    """Load the index once and reuse it across requests."""
    return Index()