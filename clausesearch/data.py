"""Benchmark loading, the LegalBench-RAG-mini subset, the fixed train/test split,
the unanswerable set and offset validation.

Benchmark offsets index into each contract read in Python's default text mode with
UTF-8 (universal newlines, so "\\r\\n" becomes "\\n"). Every read in this project goes
through read_document() so offsets stay consistent everywhere.
"""
from __future__ import annotations

import hashlib
import json
import random
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

MINI_SIZE = 194
UNANSWERABLE_TYPES = {"absent_clause", "not_in_corpus", "out_of_scope"}


# --------------------------------------------------------------------------- selection

def select_mini(tests: list[dict], n: int = MINI_SIZE) -> list[dict]:
    """Deterministic LegalBench-RAG-mini selection (the benchmark authors' procedure).

    Each test gets a pseudo-random key seeded with the file path of its first
    snippet; the n smallest keys are kept. Queries about the same contract share a
    key, so the subset keeps contracts together (except possibly the last one).
    """
    if len(tests) <= n:
        return list(tests)

    def sort_key(test: dict) -> float:
        random.seed(test["snippets"][0]["file_path"])
        return random.random()

    return sorted(tests, key=sort_key)[:n]


def assign_split(query: str) -> str:
    """Fixed train/test assignment from a hash of the query text (~30% test)."""
    digest = hashlib.sha256(query.strip().encode("utf-8")).hexdigest()
    return "test" if int(digest, 16) % 10 < 3 else "train"


# --------------------------------------------------------------------------- records

@dataclass
class Snippet:
    file_path: str
    start: int
    end: int
    answer: str = ""

    @property
    def span(self) -> tuple[str, int, int]:
        return (self.file_path, self.start, self.end)


@dataclass
class Query:
    qid: str
    text: str
    split: str
    answerable: bool
    snippets: list[Snippet] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)

    @property
    def gold_spans(self) -> list[tuple[str, int, int]]:
        return [s.span for s in self.snippets]

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Query":
        return cls(
            qid=d["qid"],
            text=d["text"],
            split=d["split"],
            answerable=d["answerable"],
            snippets=[Snippet(**s) for s in d.get("snippets", [])],
            meta=d.get("meta", {}),
        )


# --------------------------------------------------------------------------- io

def read_document(path: str | Path) -> str:
    """Read a contract exactly as the benchmark offsets assume."""
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def load_benchmark(path: str | Path) -> list[dict]:
    raw = Path(path).read_text(encoding="utf-8")
    return json.loads(raw)["tests"]


def build_queries(tests: list[dict]) -> list[Query]:
    queries = []
    for i, test in enumerate(tests):
        snippets = [
            Snippet(
                file_path=s["file_path"],
                start=int(s["span"][0]),
                end=int(s["span"][1]),
                answer=s.get("answer", ""),
            )
            for s in test["snippets"]
        ]
        queries.append(
            Query(qid=f"q{i:03d}", text=test["query"], split=assign_split(test["query"]),
                  answerable=True, snippets=snippets)
        )
    return queries


def corpus_files(queries: list[Query]) -> list[str]:
    return sorted({s.file_path for q in queries for s in q.snippets})


def validate_offsets(queries: list[Query], corpus_dir: str | Path) -> list[dict]:
    """Check document[start:end] == answer for every snippet; return the mismatches."""
    corpus_dir = Path(corpus_dir)
    cache: dict[str, str | None] = {}
    problems = []
    for q in queries:
        for s in q.snippets:
            if s.file_path not in cache:
                path = corpus_dir / s.file_path
                cache[s.file_path] = read_document(path) if path.exists() else None
            doc = cache[s.file_path]
            if doc is None:
                problems.append({"qid": q.qid, "file_path": s.file_path, "reason": "missing_file"})
                continue
            got = doc[s.start:s.end]
            if got != s.answer:
                problems.append({
                    "qid": q.qid, "file_path": s.file_path, "reason": "text_mismatch",
                    "span": [s.start, s.end], "expected": s.answer[:80], "got": got[:80],
                })
    return problems


def write_jsonl(path: str | Path, rows: list[dict]) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def read_jsonl(path: str | Path) -> list[dict]:
    rows = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                rows.append(json.loads(line))
    return rows


# --------------------------------------------------------------------------- unanswerable

def load_unanswerable(path: str | Path) -> list[Query]:
    """Load the hand-written unanswerable set. The split is computed, never stored,
    so the frozen file never needs editing."""
    queries, seen_ids, seen_text = [], set(), set()
    with open(path, encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, 1):
            if not line.strip():
                continue
            obj = json.loads(line)
            missing = {"id", "query", "type"} - set(obj)
            if missing:
                raise ValueError(f"{path}:{line_no} missing fields {sorted(missing)}")
            if obj["type"] not in UNANSWERABLE_TYPES:
                raise ValueError(f"{path}:{line_no} type must be one of {sorted(UNANSWERABLE_TYPES)}")
            if obj["id"] in seen_ids or obj["query"].strip() in seen_text:
                raise ValueError(f"{path}:{line_no} duplicate id or query")
            seen_ids.add(obj["id"])
            seen_text.add(obj["query"].strip())
            meta = {k: v for k, v in obj.items() if k not in ("id", "query")}
            queries.append(Query(qid=obj["id"], text=obj["query"], split=assign_split(obj["query"]),
                                 answerable=False, meta=meta))
    return queries


# --------------------------------------------------------------------------- processed data

def processed_paths(cfg: dict) -> dict[str, Path]:
    base = Path(cfg["data"]["processed_dir"])
    return {
        "queries": base / "queries.jsonl",
        "manifest": base / "corpus_manifest.json",
        "summary": base / "prepare_summary.json",
    }


def load_queries(cfg: dict, split: str | None = None, include_unanswerable: bool = True,
                 strict: bool = False) -> list[Query]:
    """Benchmark queries (from the prepared file) plus the unanswerable set, filtered by split."""
    paths = processed_paths(cfg)
    if not paths["queries"].exists():
        raise FileNotFoundError(f"{paths['queries']} not found; run `python -m clausesearch.prepare` first")
    queries = [Query.from_dict(d) for d in read_jsonl(paths["queries"])]
    if include_unanswerable:
        upath = Path(cfg["data"]["unanswerable_path"])
        if upath.exists():
            queries += load_unanswerable(upath)
        elif strict:
            raise FileNotFoundError(f"{upath} not found")
    if split is not None:
        queries = [q for q in queries if q.split == split]
    return queries


def load_corpus(cfg: dict) -> dict[str, str]:
    """The indexed contracts: only those referenced by the mini queries."""
    manifest_path = processed_paths(cfg)["manifest"]
    if not manifest_path.exists():
        raise FileNotFoundError(f"{manifest_path} not found; run `python -m clausesearch.prepare` first")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    corpus_dir = Path(cfg["data"]["corpus_dir"])
    return {fp: read_document(corpus_dir / fp) for fp in manifest["files"]}
