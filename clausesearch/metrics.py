"""Character-level retrieval metrics (LegalBench-RAG style), abstention rates,
failure diagnosis and a paired bootstrap.

A span is (file_path, start, end) with ``end`` exclusive, matching Python slicing.
Retrieved spans are merged before scoring, so overlapping chunks never count the
same characters twice (with non-overlapping chunks this equals summing per chunk).

    precision@k = |retrieved ∩ gold| / |retrieved|   over the top-k passages
    recall@k    = |retrieved ∩ gold| / |gold|
"""
from __future__ import annotations

from collections import defaultdict
from typing import Iterable, Sequence

import numpy as np

Span = tuple[str, int, int]
Intervals = dict[str, list[tuple[int, int]]]

FULL_RECALL = 0.95  # recall at or above this counts as "full" in the diagnosis buckets


def merge_spans(spans: Iterable[Span]) -> Intervals:
    """Group spans by file and merge overlapping or touching intervals."""
    by_file: dict[str, list[tuple[int, int]]] = defaultdict(list)
    for file_path, start, end in spans:
        if end > start:
            by_file[file_path].append((start, end))
    merged: Intervals = {}
    for file_path, intervals in by_file.items():
        intervals.sort()
        out = [list(intervals[0])]
        for start, end in intervals[1:]:
            if start <= out[-1][1]:
                out[-1][1] = max(out[-1][1], end)
            else:
                out.append([start, end])
        merged[file_path] = [(s, e) for s, e in out]
    return merged


def total_length(merged: Intervals) -> int:
    return sum(e - s for intervals in merged.values() for s, e in intervals)


def intersection_length(a: Intervals, b: Intervals) -> int:
    """Characters covered by both interval sets (two-pointer sweep per file)."""
    total = 0
    for file_path, ivs_a in a.items():
        ivs_b = b.get(file_path)
        if not ivs_b:
            continue
        i = j = 0
        while i < len(ivs_a) and j < len(ivs_b):
            start = max(ivs_a[i][0], ivs_b[j][0])
            end = min(ivs_a[i][1], ivs_b[j][1])
            if end > start:
                total += end - start
            if ivs_a[i][1] < ivs_b[j][1]:
                i += 1
            else:
                j += 1
    return total


def precision_recall(retrieved: Sequence[Span], gold: Sequence[Span]) -> tuple[float, float]:
    r, g = merge_spans(retrieved), merge_spans(gold)
    overlap = intersection_length(r, g)
    r_len, g_len = total_length(r), total_length(g)
    return (overlap / r_len if r_len else 0.0, overlap / g_len if g_len else 0.0)


def overlaps(span: Span, gold: Sequence[Span]) -> bool:
    f, s, e = span
    return any(f == gf and min(e, ge) > max(s, gs) for gf, gs, ge in gold)


def first_hit_rank(ranked: Sequence[Span], gold: Sequence[Span]) -> int | None:
    """1-based rank of the first passage that overlaps the gold answer."""
    for rank, span in enumerate(ranked, 1):
        if overlaps(span, gold):
            return rank
    return None


def gap_to_gold(ranked: Sequence[Span], gold: Sequence[Span]) -> int | None:
    """Smallest character distance between a retrieved passage and the gold answer,
    looking only at passages from a gold file (0 = overlapping); None if none."""
    best = None
    for f, s, e in ranked:
        for gf, gs, ge in gold:
            if f != gf:
                continue
            gap = max(0, max(s, gs) - min(e, ge))
            best = gap if best is None else min(best, gap)
    return best


def per_query_metrics(ranked: Sequence[Span], gold: Sequence[Span], ks: Iterable[int]) -> dict[str, float]:
    gold_files = {f for f, _, _ in gold}
    out: dict[str, float] = {}
    for k in ks:
        top = list(ranked[:k])
        p, r = precision_recall(top, gold)
        out[f"precision@{k}"] = p
        out[f"recall@{k}"] = r
        out[f"doc_hit@{k}"] = float(any(f in gold_files for f, _, _ in top))
        out[f"span_hit@{k}"] = float(any(overlaps(s, gold) for s in top))
    rank = first_hit_rank(ranked, gold)
    out["mrr"] = 1.0 / rank if rank else 0.0
    return out


def diagnose_answerable(ranked: Sequence[Span], gold: Sequence[Span], abstained: bool,
                        k: int, near_miss_chars: int) -> str:
    """Bucket one benchmark query by what went wrong in its top-k passages."""
    if abstained:
        return "false_abstention"
    top = list(ranked[:k])
    gold_files = {f for f, _, _ in gold}
    if not any(f in gold_files for f, _, _ in top):
        return "wrong_document"
    _, recall = precision_recall(top, gold)
    if recall >= FULL_RECALL:
        return "full"
    if recall > 0:
        return "partial"
    gap = gap_to_gold(top, gold)
    return "near_miss" if gap is not None and gap <= near_miss_chars else "wrong_section"


def diagnose_unanswerable(abstained: bool) -> str:
    return "correct_abstention" if abstained else "false_answer"


def mean_metrics(rows: Sequence[dict[str, float]]) -> dict[str, float]:
    if not rows:
        return {}
    keys = rows[0].keys()
    return {k: float(np.mean([row[k] for row in rows])) for k in keys}


def abstention_rates(records: Sequence[dict]) -> dict[str, float]:
    answerable = [r for r in records if r["answerable"]]
    unanswerable = [r for r in records if not r["answerable"]]
    out = {"n_answerable": len(answerable), "n_unanswerable": len(unanswerable)}
    out["false_abstention_rate"] = (
        float(np.mean([r["abstained"] for r in answerable])) if answerable else float("nan"))
    out["correct_abstention_rate"] = (
        float(np.mean([r["abstained"] for r in unanswerable])) if unanswerable else float("nan"))
    return out


def paired_bootstrap(new: Sequence[float], old: Sequence[float], n_boot: int = 2000,
                     seed: int = 0) -> dict[str, float]:
    """Resample queries with replacement to see how reliably ``new`` beats ``old``.

    Returns the mean difference, a 95% interval for it, and the share of resamples
    in which the new configuration came out ahead.
    """
    new_arr, old_arr = np.asarray(new, dtype=float), np.asarray(old, dtype=float)
    if new_arr.shape != old_arr.shape or new_arr.size == 0:
        raise ValueError("paired_bootstrap needs two equal-length, non-empty sequences")
    diff = new_arr - old_arr
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, diff.size, size=(n_boot, diff.size))
    boot = diff[idx].mean(axis=1)
    return {
        "mean_diff": float(diff.mean()),
        "ci_low": float(np.percentile(boot, 2.5)),
        "ci_high": float(np.percentile(boot, 97.5)),
        "p_improve": float((boot > 0).mean()),
    }
