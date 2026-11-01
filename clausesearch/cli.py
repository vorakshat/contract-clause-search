"""Command-line clause search.

    python -m clausesearch.cli "Consider the ... between A and B; Can the licensee sublicense?"
    python -m clausesearch.cli --config configs/final.yaml --interactive
    python -m clausesearch.cli "..." --json
"""
from __future__ import annotations

import argparse
import json
import re
import sys

from .chunking import doc_title
from .config import load_config
from .pipeline import Pipeline, SearchResult


def render(result: SearchResult, width: int = 320) -> str:
    if result.abstained:
        return f"No answer: {result.message} (reason: {result.reason})"
    lines = []
    for rank, p in enumerate(result.passages, 1):
        preview = re.sub(r"\s+", " ", p.text).strip()
        if len(preview) > width:
            preview = preview[:width].rstrip() + " ..."
        lines.append(f"[{rank}] {doc_title(p.doc_id)}\n    file: {p.doc_id}\n"
                     f"    chars {p.start}-{p.end}   score {p.score:.3f}\n    {preview}")
    return "\n\n".join(lines)


def as_json(result: SearchResult) -> str:
    return json.dumps({
        "query": result.query, "abstained": result.abstained, "reason": result.reason,
        "message": result.message,
        "passages": [{"rank": i, "file_path": p.doc_id, "start": p.start, "end": p.end, "score": p.score,
                      "scores": p.scores, "text": p.text} for i, p in enumerate(result.passages, 1)],
    }, indent=2, ensure_ascii=False)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("question", nargs="?")
    ap.add_argument("--config", default="configs/baseline.yaml")
    ap.add_argument("--set", action="append", default=[], metavar="KEY=VALUE")
    ap.add_argument("-k", "--top-k", type=int, default=5)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--interactive", action="store_true")
    args = ap.parse_args(argv)
    if not args.question and not args.interactive:
        ap.error("give a question or use --interactive")

    try:
        pipeline = Pipeline.from_config(load_config(args.config, args.set))
    except FileNotFoundError as err:
        print(err)
        return 1

    def answer(q: str) -> None:
        res = pipeline.search(q, top_k=args.top_k)
        print(as_json(res) if args.json else render(res))

    if args.question:
        answer(args.question)
    if args.interactive:
        while True:
            try:
                q = input("\nquestion> ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if q in ("", "quit", "exit"):
                break
            answer(q)
    return 0


if __name__ == "__main__":
    sys.exit(main())
