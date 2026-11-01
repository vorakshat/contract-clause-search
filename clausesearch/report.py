"""Tables and failure examples for REPORT.md.

    python -m clausesearch.report compare RUN_DIR [RUN_DIR ...]
    python -m clausesearch.report errors RUN_DIR --per-bucket 4 > experiments/error_examples.md

`compare` prints end-to-end precision/recall at each k plus abstention and utility
for several runs (for example baseline and final, on train and test), with the
number of queries behind every figure. `errors` prints concrete failures grouped by
bucket, with the gold text next to what the system returned, as raw material for
the error analysis.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import numpy as np

from .chunking import doc_title
from .config import load_config
from .data import load_corpus, read_jsonl


def _utility(records: list[dict], k: int = 8) -> float:
    return float(np.mean([r["e2e"][f"recall@{k}"] if r["answerable"] else float(r["abstained"]) for r in records]))


def compare(run_dirs: list[str], ks: tuple[int, ...] = (1, 2, 4, 8, 16, 32, 64)) -> str:
    rows = []
    for rd in map(Path, run_dirs):
        summary = json.loads((rd / "metrics.json").read_text(encoding="utf-8"))
        records = read_jsonl(rd / "per_query.jsonl")
        rows.append((summary, records))
    head = "| run | split | n bench | " + " | ".join(f"P@{k} | R@{k}" for k in ks) + " |"
    lines = ["End-to-end character-level precision (P) and recall (R) on benchmark queries:", "", head,
             "|" + "---|" * (3 + 2 * len(ks))]
    for s, _ in rows:
        e = s["e2e"]
        cells = " | ".join(f"{e[f'precision@{k}']:.3f} | {e[f'recall@{k}']:.3f}" for k in ks)
        lines.append(f"| {s['config']} | {s['split']} | {s['n_answerable']} | {cells} |")
    lines += ["", "Abstention, utility and latency:", "",
              "| run | split | utility@8 (n all) | correct abstention (n unanswerable) | false abstention (n bench) | "
              "forced R@8 | MRR | p95 ms |", "|---|---|---|---|---|---|---|---|"]
    for s, recs in rows:
        lines.append(f"| {s['config']} | {s['split']} | {_utility(recs):.3f} ({s['n_queries']}) | "
                     f"{s['correct_abstention_rate']:.1%} ({s['n_unanswerable']}) | "
                     f"{s['false_abstention_rate']:.1%} ({s['n_answerable']}) | "
                     f"{s['forced']['recall@8']:.3f} | {s['forced']['mrr']:.3f} | {s['latency_ms']['p95']:.0f} |")
    return "\n".join(lines)


def _clip(text: str, n: int = 300) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return text if len(text) <= n else text[:n] + " ..."


def errors(run_dir: str, per_bucket: int = 4) -> str:
    rd = Path(run_dir)
    cfg = load_config(rd / "config.yaml")
    corpus = load_corpus(cfg)
    records = read_jsonl(rd / "per_query.jsonl")
    lines = [f"# Failure examples from `{rd.name}`", ""]
    for bucket in ("wrong_document", "wrong_section", "near_miss", "partial", "false_abstention", "false_answer"):
        rows = [r for r in records if r["bucket"] == bucket]
        if not rows:
            continue
        lines += [f"## {bucket} ({len(rows)} queries)", ""]
        for r in rows[:per_bucket]:
            lines.append(f"### `{r['qid']}` ({r['type']})")
            lines.append(f"- Question: {r['query']}")
            if r["answerable"]:
                g = r["gold"][0]
                lines.append(f"- Gold ({doc_title(g[0])}, chars {g[1]}-{g[2]}): {_clip(corpus[g[0]][g[1]:g[2]])}")
                lines.append(f"- First relevant rank: {r.get('first_hit_rank')}; gap to gold in top k: {r.get('gap_chars')}")
            if r.get("routed"):
                lines.append(f"- Routed to: {doc_title(r['routed'][0][0])} (coverage {r['routed'][0][1]})")
            if r["top"]:
                t = r["top"][0]
                lines.append(f"- Top passage ({doc_title(t[0])}, chars {t[1]}-{t[2]}, score {t[3]}): "
                             f"{_clip(corpus[t[0]][t[1]:t[2]])}")
            if r["abstained"]:
                lines.append(f"- Abstained: {r['reason']} (gate score {r.get('gate_score')})")
            lines += ["- Diagnosis: TODO", ""]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("compare")
    c.add_argument("runs", nargs="+")
    e = sub.add_parser("errors")
    e.add_argument("run")
    e.add_argument("--per-bucket", type=int, default=4)
    args = ap.parse_args(argv)
    print(compare(args.runs) if args.cmd == "compare" else errors(args.run, args.per_bucket))
    return 0


if __name__ == "__main__":
    sys.exit(main())
