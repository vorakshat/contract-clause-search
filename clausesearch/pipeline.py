"""The search pipeline: route -> retrieve -> rerank -> confidence gate -> trim.

Pipeline.search() is the single entry point used by the CLI, the web app and the
evaluation, so all three always run exactly the same code. Ground-truth spans are
never visible here: the pipeline sees only the question and the contracts.
"""
from __future__ import annotations

import re
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field

import numpy as np

from .bm25 import BM25Index
from .chunking import chunk_corpus, doc_title
from .data import load_corpus
from .query import ProcessedQuery, process_query
from .routing import DocumentRouter
from .text import tokenize

ABSTAIN_MESSAGES = {
    "contract_not_found": "The contract named in the question is not in the indexed corpus.",
    "low_confidence": "No passage scored above the confidence threshold for this question.",
    "no_candidates": "No passages matched the question.",
}


@dataclass
class Passage:
    doc_id: str
    start: int
    end: int
    text: str
    score: float
    scores: dict[str, float] = field(default_factory=dict)
    heading: str = ""

    @property
    def span(self) -> tuple[str, int, int]:
        return (self.doc_id, self.start, self.end)


@dataclass
class SearchResult:
    query: str
    passages: list[Passage]          # what a user is shown; empty when abstained
    candidates: list[Passage]        # full ranked list before the gate (for "forced" evaluation)
    abstained: bool
    reason: str | None = None
    routed: list[tuple[str, float]] = field(default_factory=list)
    gate_score: float | None = None
    processed: ProcessedQuery | None = None
    timings_ms: dict[str, float] = field(default_factory=dict)

    @property
    def message(self) -> str:
        return ABSTAIN_MESSAGES.get(self.reason or "", "") if self.abstained else ""


def top_indices(scores: np.ndarray, n: int, allowed: np.ndarray | None = None) -> np.ndarray:
    """Indices of the n highest scores (descending), optionally restricted to a mask."""
    s = np.asarray(scores, dtype=float).copy()
    if allowed is not None:
        s[~allowed] = -np.inf
    n = min(n, int(np.isfinite(s).sum()))
    if n <= 0:
        return np.array([], dtype=int)
    idx = np.argpartition(-s, n - 1)[:n]
    return idx[np.argsort(-s[idx], kind="stable")]


def rrf_fuse(rankings: list[np.ndarray], k: int = 60) -> dict[int, float]:
    """Reciprocal rank fusion: each list adds 1 / (k + rank) to every item it ranks."""
    fused: dict[int, float] = defaultdict(float)
    for ranking in rankings:
        for rank, idx in enumerate(ranking, 1):
            fused[int(idx)] += 1.0 / (k + rank)
    return fused


def sentence_spans(text: str) -> list[tuple[int, int]]:
    spans, start = [], 0
    for m in re.finditer(r"(?<=[.;:])\s+|\n\s*", text):
        if m.start() > start:
            spans.append((start, m.start()))
        start = m.end()
    if start < len(text):
        spans.append((start, len(text)))
    return spans


class Pipeline:
    def __init__(self, cfg: dict, corpus: dict[str, str], encoder=None, cross_encoder=None):
        self.cfg = cfg
        self.corpus = corpus
        self.chunks = chunk_corpus(corpus, cfg["chunking"])
        if not self.chunks:
            raise ValueError("Chunking produced no passages; is the corpus empty?")
        self.doc_ids = list(corpus)
        position = {d: i for i, d in enumerate(self.doc_ids)}
        self.chunk_doc = np.array([position[c.doc_id] for c in self.chunks])
        texts = [c.index_text for c in self.chunks]

        rcfg, gate = cfg["retrieval"], cfg["abstention"]
        if gate["enabled"] and gate["score"] == "rerank" and not cfg["rerank"]["enabled"]:
            raise ValueError("abstention.score=rerank needs rerank.enabled=true")

        self.bm25 = BM25Index([self._bm25_tokens(t) for t in texts], rcfg["bm25"]["k1"], rcfg["bm25"]["b"])

        self.dense = None
        if rcfg["method"] in ("dense", "hybrid") or (gate["enabled"] and gate["score"] == "dense"):
            from .dense import DenseIndex
            d = rcfg["dense"]
            self.dense = DenseIndex(texts, d["model"], cfg["cache_dir"], d["passage_prefix"],
                                    d["query_prefix"], d["batch_size"], encoder=encoder)

        self.router = (DocumentRouter(corpus, cfg["routing"]["header_chars"])
                       if cfg["routing"]["enabled"] else None)

        self.reranker = None
        if cfg["rerank"]["enabled"]:
            from .rerank import Reranker
            r = cfg["rerank"]
            self.reranker = Reranker(r["model"], cfg["cache_dir"], r["batch_size"], r["max_length"],
                                     model=cross_encoder)
        self._trim_idf: dict[str, float] | None = None

    @classmethod
    def from_config(cls, cfg: dict, **kwargs) -> "Pipeline":
        return cls(cfg, load_corpus(cfg), **kwargs)

    # ------------------------------------------------------------------ helpers

    def _bm25_tokens(self, text: str) -> list[str]:
        b = self.cfg["retrieval"]["bm25"]
        return tokenize(text, stopwords=b["stopwords"], stem_tokens=b["stem"])

    def _rerank_text(self, p: Passage) -> str:
        if self.cfg["chunking"]["contextual_header"]:
            return f"{doc_title(p.doc_id)} | {p.heading}\n{p.text}"
        return p.text

    def _trim(self, p: Passage, query_terms: set[str]) -> Passage:
        """Shrink a passage to the sentences that best match the question."""
        pp = self.cfg["postprocess"]
        if self._trim_idf is None:
            df = Counter(t for c in self.chunks for t in set(tokenize(c.text, True, True)))
            n = len(self.chunks)
            self._trim_idf = {t: float(np.log1p(n / c)) for t, c in df.items()}
        sents = sentence_spans(p.text)
        if len(sents) <= 1:
            return p
        weights = [sum(self._trim_idf.get(t, 0.0) for t in set(tokenize(p.text[s:e], True, True)) & query_terms)
                   for s, e in sents]
        best = max(weights)
        if best <= 0:
            return p
        keep = [i for i, w in enumerate(weights) if w >= pp["trim_keep_ratio"] * best]
        s, e = sents[keep[0]][0], sents[keep[-1]][1]
        while e - s < pp["trim_min_chars"] and (s > 0 or e < len(p.text)):
            s, e = max(0, s - 25), min(len(p.text), e + 25)
        while s < e and p.text[s].isspace():
            s += 1
        while e > s and p.text[e - 1].isspace():
            e -= 1
        return Passage(p.doc_id, p.start + s, p.start + e, p.text[s:e], p.score, dict(p.scores), p.heading)

    # ------------------------------------------------------------------ search

    def search(self, query: str, top_k: int | None = None) -> SearchResult:
        cfg, timings = self.cfg, {}
        clock = time.perf_counter()

        def lap(name: str) -> None:
            nonlocal clock
            now = time.perf_counter()
            timings[name] = round((now - clock) * 1000, 2)
            clock = now

        pq = process_query(query, cfg)
        reason, allowed, routed = None, None, []

        # 1. Routing: restrict to the contract the question names, if any.
        if self.router is not None and pq.contract:
            ranked_docs = self.router.route(pq.contract)
            routed = ranked_docs[:3]
            keep = {doc for doc, _ in ranked_docs[: cfg["routing"]["top_docs"]]}
            allowed = np.isin(self.chunk_doc, [i for i, d in enumerate(self.doc_ids) if d in keep])
            if ranked_docs and ranked_docs[0][1] < cfg["routing"]["min_coverage"]:
                reason = "contract_not_found"
        lap("route")

        # 2. First-stage retrieval.
        method, n = cfg["retrieval"]["method"], cfg["retrieval"]["candidates"]
        bm25_scores = self.bm25.scores(self._bm25_tokens(pq.lexical))
        dense_scores = self.dense.scores(pq.semantic) if self.dense is not None else None
        fused = None
        if method == "bm25":
            order = top_indices(bm25_scores, n, allowed)
        elif method == "dense":
            order = top_indices(dense_scores, n, allowed)
        else:
            depth = max(n, 100)
            fused = rrf_fuse([top_indices(bm25_scores, depth, allowed),
                              top_indices(dense_scores, depth, allowed)], cfg["retrieval"]["rrf_k"])
            order = np.array(sorted(fused, key=lambda i: (-fused[i], i))[:n], dtype=int)
        lap("retrieve")

        candidates = []
        for i in order:
            scores = {"bm25": float(bm25_scores[i])}
            if dense_scores is not None:
                scores["dense"] = float(dense_scores[i])
            if fused is not None:
                scores["rrf"] = fused[int(i)]
            c = self.chunks[int(i)]
            primary = scores["rrf"] if method == "hybrid" else scores[method]
            candidates.append(Passage(c.doc_id, c.start, c.end, c.text, primary, scores, c.heading))

        # 3. Reranking of the first top_n candidates.
        if self.reranker is not None and candidates:
            top_n = cfg["rerank"]["top_n"]
            head = candidates[:top_n]
            rr = self.reranker.score(pq.semantic, [self._rerank_text(p) for p in head])
            for p, s in zip(head, rr):
                p.scores["rerank"] = float(s)
                p.score = float(s)
            candidates = [head[j] for j in np.argsort(-rr, kind="stable")] + candidates[top_n:]
        lap("rerank")

        # 4. Confidence gate.
        gate = cfg["abstention"]
        gate_score = candidates[0].scores.get(gate["score"]) if candidates else None
        if not gate["enabled"]:
            reason = None
        elif reason is None and gate_score is not None and gate_score < gate["threshold"]:
            reason = "low_confidence"
        if not candidates:
            reason = "no_candidates"

        # 5. Optional span trimming.
        if cfg["postprocess"]["trim_spans"] and candidates:
            terms = set(tokenize(pq.question, stopwords=True, stem_tokens=True))
            candidates = [self._trim(p, terms) for p in candidates]
        lap("gate_trim")

        abstained = reason is not None
        k = top_k or cfg["output"]["top_k"]
        return SearchResult(query=query, passages=[] if abstained else candidates[:k], candidates=candidates,
                            abstained=abstained, reason=reason, routed=routed, gate_score=gate_score,
                            processed=pq, timings_ms=timings)
