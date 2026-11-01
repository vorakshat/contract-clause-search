"""Choose the abstention threshold from train results.

Every evaluation record stores the scores of its top candidate, so the effect of any
threshold can be simulated exactly without re-running retrieval. The threshold kept
is the one with the highest per-query utility among those that satisfy every
guardrail that depends on the threshold:

    false abstention on benchmark questions   <= max_false_abstention
    correct abstention on unanswerable ones   >= min_correct_abstention (if given)
    end-to-end precision@k                    >= min_precision (if given)

    utility(benchmark query)    = recall@k of the answer in the top k (0 if abstained)
    utility(unanswerable query) = 1 if the system abstained, else 0

If no threshold meets the floors, the best one under the false-abstention ceiling is
returned (flagged constrained=False) and the acceptance step will reject the
candidate on the guardrail it misses.
"""
from __future__ import annotations

import math

import numpy as np

EPS = 1e-9


def _would_abstain(rec: dict, score_name: str, threshold: float, min_coverage: float | None) -> bool:
    if min_coverage is not None and rec.get("routed") and rec["routed"][0][1] < min_coverage:
        return True  # routing says the named contract is not indexed
    score = (rec.get("top_scores") or {}).get(score_name)
    return score is None or score < threshold


def simulate_gate(records: list[dict], score_name: str, threshold: float, k: int = 8,
                  min_coverage: float | None = None) -> dict[str, float]:
    utilities, false_abst, correct_abst, precision = [], [], [], []
    for rec in records:
        abstain = _would_abstain(rec, score_name, threshold, min_coverage)
        if rec["answerable"]:
            utilities.append(0.0 if abstain else rec["forced"][f"recall@{k}"])
            precision.append(0.0 if abstain else rec["forced"].get(f"precision@{k}", 0.0))
            false_abst.append(abstain)
        else:
            utilities.append(float(abstain))
            correct_abst.append(abstain)
    return {
        "utility": float(np.mean(utilities)) if utilities else 0.0,
        "false_abstention_rate": float(np.mean(false_abst)) if false_abst else 0.0,
        "correct_abstention_rate": float(np.mean(correct_abst)) if correct_abst else 0.0,
        "precision": float(np.mean(precision)) if precision else 0.0,
    }


def calibrate_threshold(records: list[dict], score_name: str, k: int = 8, max_false_abstention: float = 0.10,
                        min_coverage: float | None = None, min_correct_abstention: float | None = None,
                        min_precision: float | None = None) -> dict:
    """Best threshold under the guardrails (ties go to the lower threshold).

    Candidate thresholds sit halfway between consecutive train scores, so none lies
    exactly on a train example.
    """
    scores = sorted({s for r in records if (s := (r.get("top_scores") or {}).get(score_name)) is not None
                     and math.isfinite(s)})
    thresholds = [-math.inf] + [(tau + scores[i - 1]) / 2 if i else tau for i, tau in enumerate(scores)]
    options = [(t, simulate_gate(records, score_name, t, k, min_coverage)) for t in thresholds]

    within_ceiling = [o for o in options if o[1]["false_abstention_rate"] <= max_false_abstention + EPS]
    feasible = [o for o in within_ceiling
                if (min_correct_abstention is None or o[1]["correct_abstention_rate"] >= min_correct_abstention - EPS)
                and (min_precision is None or o[1]["precision"] >= min_precision - EPS)]
    pool = feasible or within_ceiling or options[:1]
    threshold, result = max(pool, key=lambda o: (o[1]["utility"], -o[0]))
    return {"threshold": threshold, **result, "constrained": bool(feasible),
            "floors": {"max_false_abstention": max_false_abstention,
                       "min_correct_abstention": min_correct_abstention, "min_precision": min_precision}}
