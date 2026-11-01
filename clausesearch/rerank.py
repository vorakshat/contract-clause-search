"""Cross-encoder reranking.

A cross-encoder reads the question and a passage together and outputs one relevance
score, which is slower but more accurate than comparing separate embeddings. It is
applied only to the first-stage candidates. Scores are cached in SQLite, keyed by
model, question and passage text, so repeated evaluations are fast and reproducible.
"""
from __future__ import annotations

import hashlib
import sqlite3
from contextlib import closing
from pathlib import Path

import numpy as np


def load_cross_encoder(model_name: str, max_length: int):
    from sentence_transformers import CrossEncoder  # heavy import, only when needed
    return CrossEncoder(model_name, max_length=max_length, device="cpu")


class ScoreCache:
    """Key -> score store in SQLite.

    A short-lived connection is opened for every call, so the cache can be used from
    any thread (Streamlit runs each interaction on a new thread, and SQLite refuses a
    connection created on a different thread).
    """

    def __init__(self, path: str | Path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.path = str(path)
        with self._connect() as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS scores (key TEXT PRIMARY KEY, score REAL)")
            conn.commit()

    def _connect(self):
        return closing(sqlite3.connect(self.path, timeout=30))

    def get_many(self, keys: list[str]) -> dict[str, float]:
        found: dict[str, float] = {}
        with self._connect() as conn:
            for i in range(0, len(keys), 500):
                batch = keys[i:i + 500]
                marks = ",".join("?" * len(batch))
                found.update(conn.execute(f"SELECT key, score FROM scores WHERE key IN ({marks})", batch))
        return found

    def put_many(self, items: dict[str, float]) -> None:
        with self._connect() as conn:
            conn.executemany("INSERT OR REPLACE INTO scores VALUES (?, ?)", list(items.items()))
            conn.commit()


class Reranker:
    def __init__(self, model_name: str, cache_dir: str | Path, batch_size: int = 16,
                 max_length: int = 512, model=None):
        self.model_name = model_name
        self.model = model if model is not None else load_cross_encoder(model_name, max_length)
        self.batch_size = batch_size
        self.cache = ScoreCache(Path(cache_dir) / "rerank_scores.sqlite")

    def _key(self, query: str, text: str) -> str:
        return hashlib.sha1(f"{self.model_name}\x00{query}\x00{text}".encode("utf-8")).hexdigest()

    def score(self, query: str, texts: list[str]) -> np.ndarray:
        keys = [self._key(query, t) for t in texts]
        cached = self.cache.get_many(keys)
        missing = [i for i, k in enumerate(keys) if k not in cached]
        if missing:
            preds = self.model.predict([(query, texts[i]) for i in missing], batch_size=self.batch_size,
                                       show_progress_bar=False)
            new = {keys[i]: float(p) for i, p in zip(missing, np.asarray(preds).ravel())}
            self.cache.put_many(new)
            cached.update(new)
        return np.array([cached[k] for k in keys], dtype=float)
