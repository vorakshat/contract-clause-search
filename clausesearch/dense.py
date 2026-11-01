"""Dense retrieval with a sentence-transformers bi-encoder.

Each chunk is embedded once into a unit-length vector; a question is embedded the
same way and scored against every chunk by dot product (cosine similarity). Chunk
embeddings are cached on disk, keyed by the model, the prefix and the exact chunk
texts, so re-running an evaluation never re-embeds unchanged chunks.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np


def load_encoder(model_name: str):
    from sentence_transformers import SentenceTransformer  # heavy import, only when needed
    return SentenceTransformer(model_name, device="cpu")


class DenseIndex:
    def __init__(self, texts: list[str], model_name: str, cache_dir: str | Path,
                 passage_prefix: str = "", query_prefix: str = "", batch_size: int = 32, encoder=None):
        self.encoder = encoder if encoder is not None else load_encoder(model_name)
        self.query_prefix = query_prefix
        digest = hashlib.sha256()
        for part in [model_name, passage_prefix, *texts]:
            digest.update(part.encode("utf-8"))
            digest.update(b"\x00")
        path = Path(cache_dir) / "dense" / f"{digest.hexdigest()[:20]}.npy"
        if path.exists():
            self.embeddings = np.load(path)
        else:
            self.embeddings = np.asarray(self.encoder.encode(
                [passage_prefix + t for t in texts], batch_size=batch_size, normalize_embeddings=True,
                show_progress_bar=len(texts) > 500, convert_to_numpy=True), dtype=np.float32)
            path.parent.mkdir(parents=True, exist_ok=True)
            np.save(path, self.embeddings)

    def scores(self, query: str) -> np.ndarray:
        q = np.asarray(self.encoder.encode([self.query_prefix + query], normalize_embeddings=True,
                                           convert_to_numpy=True), dtype=np.float32)[0]
        return self.embeddings @ q
