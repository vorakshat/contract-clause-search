"""Okapi BM25 over chunk texts, stored as a sparse matrix so scoring a query is one
sparse matrix-vector product.

    score(chunk, query) = sum over query terms t of
        idf(t) * tf * (k1 + 1) / (tf + k1 * (1 - b + b * len(chunk) / avg_len))
    idf(t) = ln(1 + (N - df + 0.5) / (df + 0.5))       (always positive)

tf is how often t occurs in the chunk, df how many chunks contain t, N the number
of chunks. k1 controls how quickly repeated terms stop adding score; b controls how
strongly long chunks are penalised.
"""
from __future__ import annotations

from collections import Counter

import numpy as np
from scipy import sparse


class BM25Index:
    def __init__(self, tokenized: list[list[str]], k1: float = 1.5, b: float = 0.75):
        self.vocab: dict[str, int] = {}
        rows, cols, tfs = [], [], []
        lengths = np.zeros(len(tokenized))
        for i, tokens in enumerate(tokenized):
            lengths[i] = len(tokens)
            for term, tf in Counter(tokens).items():
                rows.append(i)
                cols.append(self.vocab.setdefault(term, len(self.vocab)))
                tfs.append(tf)
        self.n_docs = len(tokenized)
        rows_a, cols_a, tf_a = np.array(rows, int), np.array(cols, int), np.array(tfs, float)
        avg_len = max(lengths.mean(), 1e-9) if self.n_docs else 1.0
        df = np.bincount(cols_a, minlength=len(self.vocab))
        self.idf = np.log1p((self.n_docs - df + 0.5) / (df + 0.5))
        norm = k1 * (1 - b + b * lengths[rows_a] / avg_len)
        weights = self.idf[cols_a] * tf_a * (k1 + 1) / (tf_a + norm)
        self.matrix = sparse.csc_matrix((weights, (rows_a, cols_a)), shape=(self.n_docs, len(self.vocab)))

    def term_idf(self, term: str) -> float:
        j = self.vocab.get(term)
        return float(self.idf[j]) if j is not None else 0.0

    def scores(self, query_tokens: list[str]) -> np.ndarray:
        counts = Counter(t for t in query_tokens if t in self.vocab)
        if not counts:
            return np.zeros(self.n_docs)
        terms = list(counts)
        cols = [self.vocab[t] for t in terms]
        weights = np.array([counts[t] for t in terms], dtype=float)
        return np.asarray(self.matrix[:, cols] @ weights).ravel()
