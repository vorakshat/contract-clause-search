"""Help write the unanswerable query set.

    python -m clausesearch.unanswerable_helper

For each indexed contract, lists the CUAD question types that are asked about other
contracts in the full benchmark but never about this one. CUAD annotators labelled
every clause type for every contract, so a type that is never asked usually means
the clause is absent. That is a lead, not proof: the report shows how often the
question's key words occur in the contract, and every candidate must be confirmed
by reading or searching the contract before it goes into data/unanswerable.jsonl.

Writes:
  data/unanswerable_candidates.md    candidates per contract, fewest keyword hits first
  data/unanswerable_draft.jsonl      draft "absent_clause" queries to verify and edit

The helper reads ground-truth annotations to *label* candidate queries. That is
evaluation-set construction, not inference: nothing here is used by the pipeline.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

from .chunking import doc_title
from .config import load_config
from .data import load_benchmark, load_corpus, load_queries
from .routing import parse_query
from .text import tokenize


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", default="configs/baseline.yaml")
    ap.add_argument("--per-contract", type=int, default=12, help="candidates listed per contract")
    ap.add_argument("--draft-per-contract", type=int, default=2, help="draft queries per contract")
    ap.add_argument("--out-dir", default="data")
    args = ap.parse_args(argv)

    cfg = load_config(args.config)
    tests = load_benchmark(cfg["data"]["benchmark_path"])
    mini = load_queries(cfg, include_unanswerable=False)
    corpus = load_corpus(cfg)

    asked: dict[str, set[str]] = defaultdict(set)
    templates: Counter[str] = Counter()
    for test in tests:
        _, question = parse_query(test["query"])
        for snippet in test["snippets"]:
            asked[snippet["file_path"]].add(question)
        templates[question] += 1

    descriptions: dict[str, str] = {}
    for q in mini:
        contract, _ = parse_query(q.text)
        if contract:
            descriptions.setdefault(q.snippets[0].file_path, contract)

    lines = ["# Unanswerable-query candidates", "",
             f"{len(templates)} distinct question wordings across {len(tests)} benchmark queries.", ""]
    if len(templates) > 150:
        lines += ["> Question wording varies a lot between contracts, so 'never asked' is a weak signal here. "
                  "Lean on the keyword-hit column and read the contract.", ""]

    drafts = []
    for fp, text in corpus.items():
        counts = Counter(tokenize(text, stopwords=True, stem_tokens=True))
        rows = []
        for question in templates:
            if question in asked[fp]:
                continue
            terms = sorted({t for t in tokenize(question, stopwords=True, stem_tokens=True) if len(t) > 3})
            rows.append((sum(counts[t] for t in terms), question, terms))
        rows.sort(key=lambda r: (r[0], r[1]))
        desc = descriptions.get(fp)
        lines += [f"## {doc_title(fp)}", f"`{fp}`", "",
                  f"Description used in its queries: {desc or '(none found)'}",
                  f"Question types asked about it: {len(asked[fp])}; never asked: {len(rows)}", "",
                  "| keyword hits | question never asked about this contract | key words |", "|---|---|---|"]
        lines += [f"| {hits} | {question} | {', '.join(terms[:8])} |"
                  for hits, question, terms in rows[: args.per_contract]]
        lines.append("")
        if desc:
            for hits, question, _ in rows[: args.draft_per_contract]:
                drafts.append({"query": f"Consider the {desc}; {question}", "type": "absent_clause",
                               "rationale": f"Clause type never annotated for {fp} in CUAD; "
                                            f"keyword hits in contract: {hits}",
                               "verified": "TODO: confirm by reading the contract"})

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "unanswerable_candidates.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    with open(out_dir / "unanswerable_draft.jsonl", "w", encoding="utf-8") as fh:
        for i, row in enumerate(drafts, 1):
            fh.write(json.dumps({"id": f"draft{i:03d}", **row}, ensure_ascii=False) + "\n")
    print(f"Wrote {out_dir / 'unanswerable_candidates.md'} ({len(corpus)} contracts) and "
          f"{out_dir / 'unanswerable_draft.jsonl'} ({len(drafts)} draft queries)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
