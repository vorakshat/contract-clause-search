"""Evaluate a configuration on a split.

    python -m clausesearch.evaluate --config configs/baseline.yaml --split train
    python -m clausesearch.evaluate --config configs/final.yaml --split test --confirm-test

Writes experiments/runs/<timestamp>_<name>_<split>/ containing the fully resolved
config, metrics.json, per_query.jsonl and summary.md.

Two views of retrieval quality are reported for benchmark (answerable) queries:
  forced  the ranked candidates with the confidence gate ignored (pure retrieval)
  e2e     what a user actually gets: an abstained query scores P = R = 0
Abstention is reported in both directions: correct abstention on the unanswerable
set and false abstention on benchmark queries.

Test-set runs are refused unless --confirm-test is given, and every one is appended
to experiments/test_runs.jsonl so the report can state how often test was used.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter
from datetime import datetime
from pathlib import Path

import numpy as np
from tqdm import tqdm

from .config import config_hash, dump_config, load_config
from .data import Query, load_queries
from .metrics import (abstention_rates, diagnose_answerable, diagnose_unanswerable, first_hit_rank,
                      gap_to_gold, mean_metrics, per_query_metrics)
from .pipeline import Pipeline


def run_queries(pipeline: Pipeline, queries: list[Query], progress: bool = True) -> list[dict]:
    cfg = pipeline.cfg
    ks, dk, near = cfg["eval"]["ks"], cfg["eval"]["diagnosis_k"], cfg["eval"]["near_miss_chars"]
    records = []
    for q in tqdm(queries, desc=f"{cfg['name']}", disable=not progress, leave=False):
        t0 = time.perf_counter()
        res = pipeline.search(q.text)
        ms = (time.perf_counter() - t0) * 1000
        ranked = [p.span for p in res.candidates]
        rec = {
            "qid": q.qid, "split": q.split, "answerable": q.answerable,
            "type": q.meta.get("type", "benchmark"), "query": q.text,
            "abstained": res.abstained, "reason": res.reason, "gate_score": res.gate_score,
            "top_scores": res.candidates[0].scores if res.candidates else {},
            "routed": [[d, round(s, 4)] for d, s in res.routed],
            "top": [[p.doc_id, p.start, p.end, round(p.score, 4)] for p in res.candidates[:10]],
            "latency_ms": round(ms, 1),
        }
        if q.answerable:
            gold = q.gold_spans
            rec["gold"] = [list(g) for g in gold]
            rec["forced"] = per_query_metrics(ranked, gold, ks)
            rec["e2e"] = per_query_metrics([] if res.abstained else ranked, gold, ks)
            rec["first_hit_rank"] = first_hit_rank(ranked, gold)
            rec["gap_chars"] = gap_to_gold(ranked[:dk], gold)
            rec["bucket"] = diagnose_answerable(ranked, gold, res.abstained, dk, near)
        else:
            rec["bucket"] = diagnose_unanswerable(res.abstained)
        records.append(rec)
    return records


def summarize(records: list[dict], cfg: dict, split: str) -> dict:
    answerable = [r for r in records if r["answerable"]]
    by_type: dict[str, dict] = {}
    for kind in sorted({r["type"] for r in records if not r["answerable"]}):
        rows = [r for r in records if not r["answerable"] and r["type"] == kind]
        by_type[kind] = {"n": len(rows), "correct_abstention_rate": float(np.mean([r["abstained"] for r in rows]))}
    latencies = [r["latency_ms"] for r in records] or [0.0]
    return {
        "config": cfg["name"], "config_hash": config_hash(cfg), "split": split,
        "n_queries": len(records), **abstention_rates(records),
        "forced": mean_metrics([r["forced"] for r in answerable]),
        "e2e": mean_metrics([r["e2e"] for r in answerable]),
        "buckets": dict(Counter(r["bucket"] for r in records)),
        "abstain_reasons": dict(Counter(r["reason"] for r in records if r["abstained"])),
        "unanswerable_by_type": by_type,
        "latency_ms": {"mean": float(np.mean(latencies)), "p95": float(np.percentile(latencies, 95))},
    }


def format_summary(summary: dict, ks: list[int]) -> str:
    f, e = summary["forced"], summary["e2e"]
    lines = [
        f"## {summary['config']} on {summary['split']} "
        f"(answerable n={summary['n_answerable']}, unanswerable n={summary['n_unanswerable']})",
        "",
        "| k | P forced | R forced | P e2e | R e2e | doc hit | span hit |",
        "|---|---|---|---|---|---|---|",
    ]
    if f:
        for k in ks:
            lines.append(f"| {k} | {f[f'precision@{k}']:.3f} | {f[f'recall@{k}']:.3f} | "
                         f"{e[f'precision@{k}']:.3f} | {e[f'recall@{k}']:.3f} | "
                         f"{f[f'doc_hit@{k}']:.3f} | {f[f'span_hit@{k}']:.3f} |")
        lines += ["", f"MRR (forced): {f['mrr']:.3f}"]
    lines += [
        f"Correct abstention (unanswerable): {summary['correct_abstention_rate']:.3f} "
        f"(n={summary['n_unanswerable']})",
        f"False abstention (benchmark): {summary['false_abstention_rate']:.3f} (n={summary['n_answerable']})",
        f"Buckets: {json.dumps(summary['buckets'])}",
        f"Unanswerable by type: {json.dumps(summary['unanswerable_by_type'])}",
        f"Latency ms: mean {summary['latency_ms']['mean']:.0f}, p95 {summary['latency_ms']['p95']:.0f}",
    ]
    return "\n".join(lines)


def write_run(summary: dict, records: list[dict], cfg: dict, out_dir: str | Path = "experiments") -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir = Path(out_dir) / "runs" / f"{stamp}_{cfg['name']}_{summary['split']}"
    run_dir.mkdir(parents=True, exist_ok=True)
    dump_config(cfg, run_dir / "config.yaml")
    (run_dir / "metrics.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    with open(run_dir / "per_query.jsonl", "w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    (run_dir / "summary.md").write_text(format_summary(summary, cfg["eval"]["ks"]) + "\n", encoding="utf-8")
    return run_dir


def evaluate(cfg: dict, split: str, queries: list[Query] | None = None, pipeline: Pipeline | None = None,
             write: bool = True, out_dir: str | Path = "experiments", progress: bool = True,
             limit: int | None = None) -> tuple[dict, list[dict], Path | None]:
    if queries is None:
        queries = load_queries(cfg, None if split == "all" else split)
    if limit:
        answerable = [q for q in queries if q.answerable][:limit]
        unanswerable = [q for q in queries if not q.answerable][: max(1, limit // 3)]
        queries = answerable + unanswerable
    pipeline = pipeline or Pipeline.from_config(cfg)
    records = run_queries(pipeline, queries, progress=progress)
    summary = summarize(records, cfg, split)
    run_dir = write_run(summary, records, cfg, out_dir) if write else None
    return summary, records, run_dir


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", default="configs/baseline.yaml")
    ap.add_argument("--split", choices=["train", "test", "all"], default="train")
    ap.add_argument("--set", action="append", default=[], metavar="KEY=VALUE",
                    help="override a config value, e.g. --set chunking.chunk_size=300")
    ap.add_argument("--limit", type=int, help="smoke test on the first N benchmark queries")
    ap.add_argument("--confirm-test", action="store_true", help="required to evaluate on the test split")
    ap.add_argument("--no-write", action="store_true")
    ap.add_argument("--out", default="experiments")
    args = ap.parse_args(argv)

    if args.split in ("test", "all") and not args.confirm_test:
        print("Refusing to touch the test split without --confirm-test (it is for final reporting only).")
        return 2

    cfg = load_config(args.config, args.set)
    summary, _, run_dir = evaluate(cfg, args.split, write=not args.no_write, out_dir=args.out, limit=args.limit)
    print(format_summary(summary, cfg["eval"]["ks"]))
    if run_dir:
        print(f"\nSaved to {run_dir}")
    if args.split in ("test", "all") and not args.limit:
        log = Path(args.out) / "test_runs.jsonl"
        log.parent.mkdir(parents=True, exist_ok=True)
        with open(log, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"time": datetime.now().isoformat(timespec="seconds"), "config": cfg["name"],
                                 "config_hash": summary["config_hash"], "split": args.split,
                                 "run_dir": str(run_dir) if run_dir else None}) + "\n")
        n_runs = sum(1 for _ in open(log, encoding="utf-8"))
        print(f"Test-split evaluations so far: {n_runs} (logged in {log})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
