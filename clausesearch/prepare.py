"""Prepare the evaluation data: select the mini subset, assign splits, validate
offsets and write the corpus manifest.

    python -m clausesearch.prepare --config configs/baseline.yaml
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

from .config import load_config
from .data import (build_queries, corpus_files, load_benchmark, load_unanswerable,
                   processed_paths, read_document, select_mini, validate_offsets, write_jsonl)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", default="configs/baseline.yaml")
    ap.add_argument("--allow-mismatch", action="store_true", help="write outputs even if offsets fail")
    args = ap.parse_args(argv)

    cfg = load_config(args.config)
    tests = load_benchmark(cfg["data"]["benchmark_path"])
    mini = select_mini(tests, cfg["data"]["mini_size"])
    queries = build_queries(mini)
    problems = validate_offsets(queries, cfg["data"]["corpus_dir"])
    files = corpus_files(queries)

    corpus_dir = Path(cfg["data"]["corpus_dir"])
    sizes = {fp: len(read_document(corpus_dir / fp)) for fp in files if (corpus_dir / fp).exists()}
    splits = Counter(q.split for q in queries)
    n_snippets = sum(len(q.snippets) for q in queries)
    multi = sum(1 for q in queries if len(q.snippets) > 1)
    multi_file = sum(1 for q in queries if len({s.file_path for s in q.snippets}) > 1)

    summary = {
        "benchmark_tests": len(tests),
        "mini_queries": len(queries),
        "train": splits.get("train", 0),
        "test": splits.get("test", 0),
        "contracts": len(files),
        "corpus_chars": sum(sizes.values()),
        "gold_snippets": n_snippets,
        "multi_snippet_queries": multi,
        "multi_file_queries": multi_file,
        "offset_problems": len(problems),
    }

    upath = Path(cfg["data"]["unanswerable_path"])
    if upath.exists():
        unans = load_unanswerable(upath)
        usplits = Counter(q.split for q in unans)
        summary.update({"unanswerable": len(unans), "unanswerable_train": usplits.get("train", 0),
                        "unanswerable_test": usplits.get("test", 0)})

    print("\n".join(f"{k:>24}: {v}" for k, v in summary.items()))
    if problems:
        print(f"\nOffset problems (first 5 of {len(problems)}):")
        for p in problems[:5]:
            print("  ", json.dumps(p, ensure_ascii=False))
        if not args.allow_mismatch:
            print("\nNot writing outputs. Fix the reading mode or pass --allow-mismatch.")
            return 1
    else:
        print("\nOffsets OK: document[start:end] == answer for every snippet.")

    paths = processed_paths(cfg)
    write_jsonl(paths["queries"], [q.to_dict() for q in queries])
    paths["manifest"].write_text(json.dumps({"files": files, "chars": sizes}, indent=2), encoding="utf-8")
    paths["summary"].write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Wrote {paths['queries']} and {paths['manifest']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
