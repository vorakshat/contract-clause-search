"""Choose the abstention threshold from train results.

Every evaluation record stores the scores of its top candidate, so the effect of any
threshold can be simulated exactly without re-running retrieval. The threshold
kept is the one that maximises per-query utility while keeping false abstention on
benchmark questions at or below a ceiling:

    utility(benchmark query)    = recall@k of the answer in the top k (0 if abstained)
    utility(unanswerable query) = 1 if the system abstained, else 0
"""
from __future__ import annotations

import math

import numpy as np


def _would_abstain(rec: dict, score_name: str, threshold: float, min_coverage: float | None) -> bool:
    if min_coverage is not None and rec.get("routed") and rec["routed"][0][1] < min_coverage:
        return True  # routing says the named contract is not indexed
    score = (rec.get("top_scores") or {}).get(score_name)
    return score is None or score < threshold


def simulate_gate(records: list[dict], score_name: str, threshold: float, k: int = 8,
                  min_coverage: float | None = None) -> dict[str, float]:
    utilities, false_abst, correct_abst = [], [], []
    for rec in records:
        abstain = _would_abstain(rec, score_name, threshold, min_coverage)
        if rec["answerable"]:
            utilities.append(0.0 if abstain else rec["forced"][f"recall@{k}"])
            false_abst.append(abstain)
        else:
            utilities.append(float(abstain))
            correct_abst.append(abstain)
    return {
        "utility": float(np.mean(utilities)) if utilities else 0.0,
        "false_abstention_rate": float(np.mean(false_abst)) if false_abst else 0.0,
        "correct_abstention_rate": float(np.mean(correct_abst)) if correct_abst else 0.0,
    }


def calibrate_threshold(records: list[dict], score_name: str, k: int = 8, max_false_abstention: float = 0.10,
                        min_coverage: float | None = None) -> dict[str, float]:
    """Best threshold under the false-abstention ceiling (ties go to the lower threshold).

    The returned threshold sits halfway between the chosen train score and the next
    lower one, so it does not lie exactly on a train example.
    """
    scores = sorted({s for r in records if (s := (r.get("top_scores") or {}).get(score_name)) is not None
                     and math.isfinite(s)})
    best = {"threshold": -math.inf, **simulate_gate(records, score_name, -math.inf, k, min_coverage)}
    for i, tau in enumerate(scores):
        result = simulate_gate(records, score_name, tau, k, min_coverage)
        if result["false_abstention_rate"] > max_false_abstention:
            continue
        if result["utility"] > best["utility"] + 1e-12:
            midpoint = (tau + scores[i - 1]) / 2 if i > 0 else tau
            best = {"threshold": midpoint, **simulate_gate(records, score_name, midpoint, k, min_coverage)}
    return best
