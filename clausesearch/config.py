"""Pipeline configuration.

A config is a YAML file merged over DEFAULTS, optionally followed by dotted-path
overrides such as ``chunking.chunk_size=300``. Every pipeline choice lives here so
the improvement loop can change behaviour by writing a new config instead of
editing code. Unknown keys raise an error, which catches typos in proposals.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

import yaml

DEFAULTS: dict[str, Any] = {
    "name": "unnamed",
    "description": "",
    "data": {
        "benchmark_path": "data/raw/benchmarks/cuad.json",
        "corpus_dir": "data/raw/corpus",
        "processed_dir": "data/processed",
        "unanswerable_path": "data/unanswerable.jsonl",
        "mini_size": 194,
    },
    "chunking": {
        "strategy": "fixed",          # fixed | recursive | clause
        "chunk_size": 500,            # maximum characters per chunk
        "overlap": 0,                 # characters shared by consecutive chunks
        "min_chunk_size": 100,        # clause strategy: merge segments shorter than this
        "contextual_header": False,   # prepend contract title + section heading to indexed text
    },
    "query": {
        "strip_contract_prefix": False,  # drop "Consider the X between A and B;" before matching
        "expand_categories": False,      # append rule-based synonyms for CUAD clause types
    },
    "routing": {
        "enabled": False,             # restrict retrieval to the contract named in the query
        "top_docs": 1,
        "header_chars": 4000,         # how much of each contract's opening text describes it
        "min_coverage": 0.5,          # below this the named contract is treated as not indexed
    },
    "retrieval": {
        "method": "bm25",             # bm25 | dense | hybrid
        "candidates": 64,             # chunks passed on from first-stage retrieval
        "bm25": {"k1": 1.5, "b": 0.75, "stopwords": False, "stem": False},
        "dense": {
            "model": "BAAI/bge-small-en-v1.5",
            "query_prefix": "Represent this sentence for searching relevant passages: ",
            "passage_prefix": "",
            "batch_size": 32,
        },
        "rrf_k": 60,
    },
    "rerank": {
        "enabled": False,
        "model": "cross-encoder/ms-marco-MiniLM-L-6-v2",
        "top_n": 50,
        "batch_size": 16,
        "max_length": 512,
    },
    "abstention": {
        "enabled": False,
        "score": "rerank",            # score the gate thresholds: rerank | dense | bm25
        "threshold": 0.0,
    },
    "postprocess": {
        "trim_spans": False,          # shrink each passage to its best-matching sentences
        "trim_keep_ratio": 0.5,       # keep sentences scoring >= ratio * best sentence
        "trim_min_chars": 120,
    },
    "output": {"top_k": 8},
    "eval": {"ks": [1, 2, 4, 8, 16, 32, 64], "diagnosis_k": 8, "near_miss_chars": 1500},
    "cache_dir": "cache",
}

CHOICES = {
    "chunking.strategy": {"fixed", "recursive", "clause"},
    "retrieval.method": {"bm25", "dense", "hybrid"},
    "abstention.score": {"rerank", "dense", "bm25"},
}


def deep_merge(base: dict, override: dict, path: str = "") -> dict:
    """Return a copy of ``base`` updated with ``override``; unknown keys are an error."""
    out = copy.deepcopy(base)
    for key, value in (override or {}).items():
        dotted = f"{path}.{key}" if path else key
        if key not in out:
            raise KeyError(f"Unknown config key: {dotted}")
        if isinstance(out[key], dict) and isinstance(value, dict):
            out[key] = deep_merge(out[key], value, dotted)
        else:
            out[key] = copy.deepcopy(value)
    return out


def get_path(cfg: dict, dotted: str) -> Any:
    node: Any = cfg
    for part in dotted.split("."):
        node = node[part]
    return node


def set_path(cfg: dict, dotted: str, value: Any) -> dict:
    """Return a copy of ``cfg`` with one dotted key changed (the key must already exist)."""
    out = copy.deepcopy(cfg)
    parts = dotted.split(".")
    node = out
    for part in parts[:-1]:
        if part not in node or not isinstance(node[part], dict):
            raise KeyError(f"Unknown config key: {dotted}")
        node = node[part]
    if parts[-1] not in node:
        raise KeyError(f"Unknown config key: {dotted}")
    node[parts[-1]] = value
    return out


def parse_override(text: str) -> tuple[str, Any]:
    """Parse ``a.b=value``; the value is read as YAML so numbers and booleans work."""
    if "=" not in text:
        raise ValueError(f"Override must look like key=value, got: {text}")
    key, raw = text.split("=", 1)
    return key.strip(), yaml.safe_load(raw)


def validate(cfg: dict) -> dict:
    for dotted, allowed in CHOICES.items():
        value = get_path(cfg, dotted)
        if value not in allowed:
            raise ValueError(f"{dotted}={value!r}; expected one of {sorted(allowed)}")
    ch = cfg["chunking"]
    if ch["chunk_size"] <= 0 or not 0 <= ch["overlap"] < ch["chunk_size"]:
        raise ValueError("chunking needs chunk_size > 0 and 0 <= overlap < chunk_size")
    if cfg["routing"]["top_docs"] < 1:
        raise ValueError("routing.top_docs must be >= 1")
    return cfg


def load_config(path: str | Path | None = None, overrides: Iterable[str] = ()) -> dict:
    cfg = copy.deepcopy(DEFAULTS)
    if path:
        loaded = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
        cfg = deep_merge(cfg, loaded)
    for item in overrides:
        key, value = parse_override(item)
        cfg = set_path(cfg, key, value)
    return validate(cfg)


def config_hash(cfg: dict, sections: Iterable[str] | None = None) -> str:
    """Short stable hash of the whole config, or of selected sections (used for caches)."""
    part = cfg if sections is None else {s: get_path(cfg, s) for s in sections}
    blob = json.dumps(part, sort_keys=True, default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:12]


def dump_config(cfg: dict, path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")


def diff_configs(old: dict, new: dict, prefix: str = "") -> dict[str, tuple[Any, Any]]:
    """Dotted keys whose values differ between two configs, as {key: (old, new)}."""
    changes: dict[str, tuple[Any, Any]] = {}
    for key in sorted(set(old) | set(new)):
        dotted = f"{prefix}.{key}" if prefix else key
        a, b = old.get(key), new.get(key)
        if isinstance(a, dict) and isinstance(b, dict):
            changes.update(diff_configs(a, b, dotted))
        elif a != b and key not in ("name", "description"):
            changes[dotted] = (a, b)
    return changes
