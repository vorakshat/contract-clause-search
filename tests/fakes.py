"""Light stand-ins for the sentence-transformers models, so tests run offline and fast."""
import zlib

import numpy as np

from clausesearch.text import tokenize


class FakeEncoder:
    """Hashed bag-of-words embedder with the same encode() signature as SentenceTransformer."""

    def __init__(self, dim: int = 512):
        self.dim = dim
        self.calls = 0

    def encode(self, texts, normalize_embeddings=True, convert_to_numpy=True, **kwargs):
        self.calls += 1
        out = np.zeros((len(texts), self.dim), dtype=np.float32)
        for i, text in enumerate(texts):
            for tok in tokenize(text, stopwords=True, stem_tokens=True):
                out[i, zlib.crc32(tok.encode()) % self.dim] += 1.0
        norms = np.linalg.norm(out, axis=1, keepdims=True)
        return out / np.maximum(norms, 1e-9)


class FakeCrossEncoder:
    """Scores a (question, passage) pair by shared content words, like CrossEncoder.predict()."""

    def __init__(self):
        self.pairs_scored = 0

    def predict(self, pairs, batch_size=16, show_progress_bar=False):
        self.pairs_scored += len(pairs)
        return np.array([len(set(tokenize(q, True, True)) & set(tokenize(p, True, True))) for q, p in pairs],
                        dtype=float)
