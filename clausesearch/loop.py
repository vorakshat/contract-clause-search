"""The self-improvement loop.

    python -m clausesearch.loop --iterations 3     # run 3 iterations, resuming from saved state
    python -m clausesearch.loop --dry-run          # show the diagnosis and queued proposals only
    python -m clausesearch.loop --propose rerank.top_n=30 --proposer claude --rationale "why"
    python -m clausesearch.loop --finalize         # copy the current best config to configs/final.yaml

Each iteration:
  1. loads the current configuration's train results
  2. diagnoses failures into buckets (wrong document, wrong section, near miss,
     partial span, false abstention, false answer) and writes a failure summary
  3. picks the first untried proposal: rules keyed to the diagnosis, then a small grid
     (or a single proposal given on the command line by a human or an LLM)
  4. evaluates the candidate on train; if it uses the confidence gate, the threshold
     is first re-calibrated on the candidate's own train results
  5. accepts it only if the criterion in configs/objective.yaml holds
  6. logs the outcome to experiments/log.jsonl and rewrites experiments/LOG.md

Only the train split is ever loaded. Gold spans are used to score runs, never as
pipeline input.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import yaml

from .calibrate import calibrate_threshold
from .chunking import doc_title
from .config import config_hash, diff_configs, dump_config, load_config, set_path, validate
from .data import read_jsonl
from .evaluate import evaluate
from .metrics import paired_bootstrap
from .pipeline import Pipeline

NEVER = -1e9  # threshold that never abstains on score


@dataclass
class Proposal:
    changes: dict[str, Any]
    rationale: str
    proposer: str = "rules"
    tags: list[str] = field(default_factory=list)


def make_pipeline(cfg: dict) -> Pipeline:
    """Build the pipeline for a configuration (tests replace this with fake models)."""
    return Pipeline.from_config(cfg)


def body_hash(cfg: dict) -> str:
    return config_hash({k: v for k, v in cfg.items() if k not in ("name", "description")})


def fold_of(qid: str) -> int:
    return int(hashlib.sha256(qid.encode("utf-8")).hexdigest(), 16) % 2


def query_utility(rec: dict, k: int) -> float:
    if rec["answerable"]:
        return rec["e2e"][f"recall@{k}"]
    return float(rec["abstained"])


def preferred_gate_score(cfg: dict) -> str:
    if cfg["rerank"]["enabled"]:
        return "rerank"
    return "dense" if cfg["retrieval"]["method"] in ("dense", "hybrid") else "bm25"


# --------------------------------------------------------------------------- diagnosis

def key_metrics(records: list[dict], summary: dict, k: int) -> dict[str, float]:
    answerable = [r for r in records if r["answerable"]]
    return {
        "utility": float(np.mean([query_utility(r, k) for r in records])),
        "recall": float(np.mean([r["e2e"][f"recall@{k}"] for r in answerable])) if answerable else 0.0,
        "precision": float(np.mean([r["e2e"][f"precision@{k}"] for r in answerable])) if answerable else 0.0,
        "false_abstention": summary["false_abstention_rate"],
        "correct_abstention": summary["correct_abstention_rate"],
        "latency_p95_ms": summary["latency_ms"]["p95"],
    }


def diagnose(records: list[dict], k: int) -> dict:
    answerable = [r for r in records if r["answerable"]]
    unanswerable = [r for r in records if not r["answerable"]]
    n = max(len(answerable), 1)
    buckets = Counter(r["bucket"] for r in answerable)
    ranks = [r.get("first_hit_rank") for r in answerable]
    return {
        "n_answerable": len(answerable),
        "n_unanswerable": len(unanswerable),
        "buckets": dict(buckets),
        "share": {b: c / n for b, c in buckets.items()},
        "ranked_below_k": sum(1 for x in ranks if x and x > k) / n,
        "missed_in_candidates": sum(1 for x in ranks if not x) / n,
        "false_answers_by_type": dict(Counter(r["type"] for r in unanswerable if not r["abstained"])),
    }


def failure_summary(records: list[dict], diag: dict, cfg: dict, k: int, examples: int = 3) -> str:
    """Readable failure report: counts plus a few examples per bucket (for humans or an LLM)."""
    lines = [f"# Failure summary for `{cfg['name']}` (train)", "",
             f"Benchmark queries: {diag['n_answerable']}; unanswerable: {diag['n_unanswerable']}", "",
             f"Buckets at k={k}: {json.dumps(diag['buckets'])}",
             f"Relevant passage exists but ranked below {k}: {diag['ranked_below_k']:.1%}",
             f"Relevant passage absent from all candidates: {diag['missed_in_candidates']:.1%}",
             f"False answers on unanswerable queries by type: {json.dumps(diag['false_answers_by_type'])}", ""]
    for bucket in ("wrong_document", "wrong_section", "near_miss", "partial", "false_abstention", "false_answer"):
        rows = [r for r in records if r["bucket"] == bucket][:examples]
        if not rows:
            continue
        lines.append(f"## {bucket}")
        for r in rows:
            top = r["top"][0] if r["top"] else None
            lines.append(f"- `{r['qid']}` {r['query'][:200]}")
            if r["answerable"]:
                g = r["gold"][0]
                lines.append(f"  - gold: {doc_title(g[0])} chars {g[1]}-{g[2]}; first hit rank: "
                             f"{r.get('first_hit_rank')}; gap to gold in top {k}: {r.get('gap_chars')}")
            if top:
                lines.append(f"  - top passage: {doc_title(top[0])} chars {top[1]}-{top[2]} (score {top[3]})")
            if r.get("reason"):
                lines.append(f"  - abstained: {r['reason']}")
        lines.append("")
    return "\n".join(lines)


# --------------------------------------------------------------------------- proposals

def propose(diag: dict, cfg: dict) -> list[Proposal]:
    """Candidate changes, most promising first, each with the evidence behind it."""
    share = diag["share"]
    wrong_doc = share.get("wrong_document", 0.0)
    section = share.get("wrong_section", 0.0) + share.get("near_miss", 0.0)
    partial = share.get("partial", 0.0)
    rc, ch, rr, gate = cfg["retrieval"], cfg["chunking"], cfg["rerank"], cfg["abstention"]
    out: list[Proposal] = []

    if not cfg["routing"]["enabled"]:
        out.append(Proposal({"routing.enabled": True, "query.strip_contract_prefix": True},
                            f"{wrong_doc:.0%} of benchmark queries have no passage from the right contract in the "
                            f"top {cfg['eval']['diagnosis_k']}, and passages from other contracts dilute precision. "
                            "Questions name their contract, so route to it and match on the question alone; this "
                            "also lets the gate refuse questions about contracts that are not indexed."))
    elif wrong_doc > 0.03:
        out.append(Proposal({"routing.top_docs": 2},
                            f"{wrong_doc:.0%} still retrieve from the wrong contract: keep the top 2 routed contracts."))
        out.append(Proposal({"routing.header_chars": 8000},
                            f"{wrong_doc:.0%} still retrieve from the wrong contract: let the router read more of each "
                            "contract's opening text."))

    if not gate["enabled"] and diag["n_unanswerable"]:
        out.append(Proposal({"abstention.enabled": True},
                            f"The system never abstains, so all {diag['n_unanswerable']} unanswerable train queries get "
                            "an answer. Enable the confidence gate with a threshold calibrated on train."))

    if not rr["enabled"] and (diag["ranked_below_k"] > 0.05 or section > 0.10):
        out.append(Proposal({"rerank.enabled": True},
                            f"{diag['ranked_below_k']:.0%} have a relevant passage ranked below the cut-off and "
                            f"{section:.0%} land in the wrong section: a cross-encoder can reorder candidates."))

    if rc["method"] == "bm25" and diag["missed_in_candidates"] > 0.03:
        out.append(Proposal({"retrieval.method": "hybrid"},
                            f"{diag['missed_in_candidates']:.0%} have no relevant passage among all candidates: add "
                            "embedding-based retrieval to catch paraphrased clauses."))

    if not cfg["query"]["expand_categories"]:
        out.append(Proposal({"query.expand_categories": True},
                            f"{section:.0%} hit the right contract but the wrong section: add clause-type synonyms "
                            "so keyword search matches differently worded clauses."))

    if not rc["bm25"]["stem"]:
        out.append(Proposal({"retrieval.bm25.stem": True, "retrieval.bm25.stopwords": True},
                            "Word-form mismatches (assign/assignment, terminate/termination) cost keyword matches."))

    if partial > 0.10:
        if ch["strategy"] != "clause":
            out.append(Proposal({"chunking.strategy": "clause", "chunking.chunk_size": max(ch["chunk_size"], 600)},
                                f"{partial:.0%} only partly cover the answer: cut chunks at clause boundaries."))
        out.append(Proposal({"chunking.chunk_size": int(ch["chunk_size"] * 1.5)},
                            f"{partial:.0%} only partly cover the answer: try larger chunks."))

    if not cfg["postprocess"]["trim_spans"]:
        out.append(Proposal({"postprocess.trim_spans": True},
                            "Character precision is low because whole chunks are returned: trim each passage to "
                            "its best-matching sentences."))

    grid: list[tuple[dict, str]] = []
    if rc["method"] != "hybrid":
        grid.append(({"retrieval.method": "hybrid"}, "hybrid retrieval"))
    for size in (300, 800):
        if ch["chunk_size"] != size:
            grid.append(({"chunking.chunk_size": size}, f"chunk size {size}"))
    for strategy in ("recursive", "clause"):
        if ch["strategy"] != strategy:
            grid.append(({"chunking.strategy": strategy}, f"{strategy} chunking"))
    if not ch["overlap"] and ch["strategy"] != "clause":
        grid.append(({"chunking.overlap": ch["chunk_size"] // 4}, "overlapping chunks"))
    if not ch["contextual_header"]:
        grid.append(({"chunking.contextual_header": True}, "contract title + heading prepended to indexed text"))
    if rr["enabled"] and rr["top_n"] != 30:
        grid.append(({"rerank.top_n": 30}, "rerank fewer candidates"))
    if cfg["routing"]["enabled"] and cfg["routing"]["top_docs"] == 1:
        grid.append(({"routing.top_docs": 2}, "route to the top 2 contracts"))
    if rr["enabled"] and rr["model"] != "BAAI/bge-reranker-base":
        grid.append(({"rerank.model": "BAAI/bge-reranker-base"}, "larger reranker (slow on CPU, so tried last)"))
    out += [Proposal(changes, f"Parameter search: {why}.", proposer="grid") for changes, why in grid]
    return out


# --------------------------------------------------------------------------- acceptance

def decide(cur_records: list[dict], cur_summary: dict, cand_records: list[dict], cand_summary: dict,
           objective: dict) -> tuple[bool, list[str], dict]:
    k, guard = objective["k"], objective["guardrails"]
    cur_u = {r["qid"]: query_utility(r, k) for r in cur_records}
    cand_u = {r["qid"]: query_utility(r, k) for r in cand_records}
    qids = sorted(set(cur_u) & set(cand_u))
    new, old = np.array([cand_u[q] for q in qids]), np.array([cur_u[q] for q in qids])
    boot = paired_bootstrap(new, old)
    folds = {}
    for f in (0, 1):
        mask = np.array([fold_of(q) == f for q in qids])
        folds[f"fold{f}"] = float(new[mask].mean() - old[mask].mean()) if mask.any() else 0.0
    cur, cand = key_metrics(cur_records, cur_summary, k), key_metrics(cand_records, cand_summary, k)
    gain = cand["utility"] - cur["utility"]

    reasons = []
    if gain < objective["min_improvement"]:
        reasons.append(f"utility gain {gain:+.4f} is below {objective['min_improvement']}")
    if boot["p_improve"] < objective["bootstrap_p"]:
        reasons.append(f"wins in only {boot['p_improve']:.0%} of bootstrap resamples")
    if min(folds.values()) < -objective["fold_tolerance"]:
        reasons.append(f"worse on one half of train ({json.dumps({k2: round(v, 4) for k2, v in folds.items()})})")
    if cur["precision"] > 0 and (cur["precision"] - cand["precision"]) / cur["precision"] > guard["e2e_precision_relative_drop"]:
        reasons.append(f"guardrail: precision@{k} {cur['precision']:.4f} -> {cand['precision']:.4f}")
    if cand["false_abstention"] > guard["max_false_abstention"]:
        reasons.append(f"guardrail: false abstention {cand['false_abstention']:.1%} above "
                       f"{guard['max_false_abstention']:.0%}")
    if cur["correct_abstention"] - cand["correct_abstention"] > guard["correct_abstention_drop"]:
        reasons.append(f"guardrail: correct abstention {cur['correct_abstention']:.1%} -> {cand['correct_abstention']:.1%}")
    if cand["latency_p95_ms"] > guard["max_latency_p95_ms"]:
        reasons.append(f"guardrail: p95 latency {cand['latency_p95_ms']:.0f} ms")
    return not reasons, reasons, {"gain": gain, "bootstrap": boot, "folds": folds, "current": cur, "candidate": cand}


# --------------------------------------------------------------------------- running

def run_candidate(cfg: dict, objective: dict, out_dir: Path) -> tuple[dict, dict, list[dict], Path, dict | None]:
    """Evaluate a candidate on train, re-calibrating the gate threshold first if it is enabled."""
    calibration = None
    if cfg["abstention"]["enabled"]:
        score_name = preferred_gate_score(cfg)
        cfg = set_path(set_path(cfg, "abstention.score", score_name), "abstention.threshold", NEVER)
        pipeline = make_pipeline(cfg)
        probe = set_path(cfg, "abstention.enabled", False)
        pipeline.cfg = probe
        _, probe_records, _ = evaluate(probe, "train", pipeline=pipeline, write=False, progress=False)
        min_cov = cfg["routing"]["min_coverage"] if cfg["routing"]["enabled"] else None
        calibration = calibrate_threshold(probe_records, score_name, objective["k"],
                                          objective["guardrails"]["max_false_abstention"], min_cov)
        threshold = calibration["threshold"] if math.isfinite(calibration["threshold"]) else NEVER
        cfg = set_path(cfg, "abstention.threshold", round(float(threshold), 6))
        pipeline.cfg = cfg
    else:
        pipeline = make_pipeline(cfg)
    summary, records, run_dir = evaluate(cfg, "train", pipeline=pipeline, out_dir=out_dir, progress=True)
    return cfg, summary, records, run_dir, calibration


def unanswerable_commit(path: str) -> str | None:
    """Commit hash that last touched the unanswerable file, or None if untracked or modified."""
    try:
        if subprocess.run(["git", "diff", "--quiet", "HEAD", "--", path], capture_output=True).returncode != 0:
            return None
        out = subprocess.run(["git", "log", "-1", "--format=%h", "--", path], capture_output=True, text=True)
        return out.stdout.strip() or None
    except OSError:
        return None


class LoopState:
    def __init__(self, out_dir: Path):
        self.path = out_dir / "loop_state.json"
        self.data = json.loads(self.path.read_text(encoding="utf-8")) if self.path.exists() else {}

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.data, indent=2), encoding="utf-8")


def append_log(out_dir: Path, entry: dict) -> None:
    with open(out_dir / "log.jsonl", "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    write_log_markdown(out_dir)


def write_log_markdown(out_dir: Path) -> None:
    entries = read_jsonl(out_dir / "log.jsonl") if (out_dir / "log.jsonl").exists() else []
    lines = ["# Experiment log", "",
             "Objective, guardrails and acceptance rule: `configs/objective.yaml`. Every entry is a train-split run.",
             "utility@8 = per-query score (recall@8 for benchmark questions, 1 for a correct abstention on an "
             "unanswerable one). R and P are end-to-end character recall and precision at 8. FAR = false "
             "abstention rate, CAR = correct abstention rate.", "",
             "| iter | change | proposer | utility@8 | Δ vs current | R@8 | P@8 | FAR | CAR | P(win) | decision |",
             "|---|---|---|---|---|---|---|---|---|---|---|"]
    for e in entries:
        m = e["metrics"]
        change = "; ".join(f"`{k}={v}`" for k, v in e["changes"].items()) or "(baseline)"
        p_win = f"{e['bootstrap']['p_improve']:.0%}" if e.get("bootstrap") else "–"
        delta = f"{e['gain']:+.4f}" if e.get("gain") is not None else "–"
        lines.append(f"| {e['iteration']} | {change} | {e['proposer']} | {m['utility']:.4f} | {delta} | "
                     f"{m['recall']:.4f} | {m['precision']:.4f} | {m['false_abstention']:.1%} | "
                     f"{m['correct_abstention']:.1%} | {p_win} | {e['decision']} |")
    lines += ["", "## Details", ""]
    for e in entries:
        lines += [f"### Iteration {e['iteration']}: {e['decision']} ({e['config_name']})", "",
                  f"- Proposed by: {e['proposer']}", f"- Why: {e['rationale']}",
                  f"- Changes: {json.dumps(e['changes'])}"]
        if e.get("calibration"):
            c = e["calibration"]
            rule = (f"{e['gate_score']} >= {c['threshold']:.4f}" if math.isfinite(c["threshold"])
                    else "no score threshold helps; abstains only when routing finds no matching contract")
            lines.append(f"- Gate calibrated on train: {rule} (simulated utility {c['utility']:.4f}, "
                         f"FAR {c['false_abstention_rate']:.1%}, CAR {c['correct_abstention_rate']:.1%})")
        if e.get("reasons"):
            lines.append(f"- Rejected because: {'; '.join(e['reasons'])}")
        if e.get("folds"):
            lines.append(f"- Δ utility on train halves: {json.dumps({k: round(v, 4) for k, v in e['folds'].items()})}")
        lines += [f"- Run: `{e['run_dir']}`", ""]
    (out_dir / "LOG.md").write_text("\n".join(lines), encoding="utf-8")


def entry_for(iteration: int, cfg: dict, proposal: Proposal | None, summary: dict, records: list[dict],
              run_dir: Path, objective: dict, decision: str, extra: dict | None = None) -> dict:
    extra = extra or {}
    return {
        "iteration": iteration, "time": datetime.now().isoformat(timespec="seconds"),
        "config_name": cfg["name"], "config_hash": body_hash(cfg),
        "changes": proposal.changes if proposal else {}, "proposer": proposal.proposer if proposal else "baseline",
        "rationale": proposal.rationale if proposal else "Simplest end-to-end pipeline; reference point.",
        "metrics": key_metrics(records, summary, objective["k"]), "decision": decision,
        "gate_score": cfg["abstention"]["score"] if cfg["abstention"]["enabled"] else None,
        "run_dir": str(run_dir), **extra,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--start", default="configs/baseline.yaml", help="starting config when there is no state yet")
    ap.add_argument("--objective", default="configs/objective.yaml")
    ap.add_argument("--iterations", type=int, default=1)
    ap.add_argument("--propose", action="append", default=[], metavar="KEY=VALUE",
                    help="evaluate this specific change instead of the next queued proposal")
    ap.add_argument("--rationale", default="Manual proposal.")
    ap.add_argument("--proposer", default="human", help="who proposed a --propose change (human, claude, ...)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--finalize", action="store_true")
    ap.add_argument("--out", default="experiments")
    ap.add_argument("--configs-dir", default="configs")
    args = ap.parse_args(argv)

    out_dir, configs_dir = Path(args.out), Path(args.configs_dir)
    objective = yaml.safe_load(Path(args.objective).read_text(encoding="utf-8"))
    k = objective["k"]
    state = LoopState(out_dir)

    if not state.data:
        cfg = load_config(args.start)
        upath = cfg["data"]["unanswerable_path"]
        if not Path(upath).exists():
            print(f"{upath} is missing. Write and commit the unanswerable set before starting the loop.")
            return 1
        commit = unanswerable_commit(upath)
        if commit is None:
            print(f"Warning: {upath} is not committed (or has uncommitted edits). Commit it before iterating.")
        print(f"Evaluating starting config {cfg['name']} on train...")
        summary, records, run_dir = evaluate(cfg, "train", pipeline=make_pipeline(cfg), out_dir=out_dir)
        state.data = {"iteration": 0, "current_config": args.start, "current_run": str(run_dir),
                      "tried": [body_hash(cfg)], "unanswerable_commit": commit}
        state.save()
        append_log(out_dir, entry_for(0, cfg, None, summary, records, run_dir, objective, "baseline"))

    if args.finalize:
        cfg = load_config(state.data["current_config"])
        cfg["name"], cfg["description"] = "final", f"Best configuration found by the loop ({state.data['current_config']})."
        dump_config(cfg, configs_dir / "final.yaml")
        print(f"Wrote {configs_dir / 'final.yaml'} from {state.data['current_config']}")
        return 0

    for _ in range(args.iterations):
        cur_cfg = load_config(state.data["current_config"])
        cur_run = Path(state.data["current_run"])
        cur_records = read_jsonl(cur_run / "per_query.jsonl")
        cur_summary = json.loads((cur_run / "metrics.json").read_text(encoding="utf-8"))
        diag = diagnose(cur_records, k)
        (out_dir / "latest_diagnosis.md").write_text(failure_summary(cur_records, diag, cur_cfg, k), encoding="utf-8")

        if args.propose:
            changes = {}
            for item in args.propose:
                key, value = item.split("=", 1)
                changes[key.strip()] = yaml.safe_load(value)
            queue = [Proposal(changes, args.rationale, proposer=args.proposer)]
        else:
            queue = propose(diag, cur_cfg)

        iteration = state.data["iteration"] + 1
        name = f"iter{iteration:02d}"
        chosen, cand_cfg = None, None
        for proposal in queue:
            try:
                candidate = copy.deepcopy(cur_cfg)
                for key, value in proposal.changes.items():
                    candidate = set_path(candidate, key, value)
                candidate["name"], candidate["description"] = name, proposal.rationale
                validate(candidate)
            except (KeyError, ValueError) as err:
                print(f"Skipping invalid proposal {proposal.changes}: {err}")
                continue
            if body_hash(candidate) in state.data["tried"] and not args.propose:
                continue
            chosen, cand_cfg = proposal, candidate
            break

        if args.dry_run:
            print(failure_summary(cur_records, diag, cur_cfg, k))
            print("\nQueued proposals:")
            for p in queue:
                print(f"  [{p.proposer}] {p.changes}  <- {p.rationale}")
            return 0
        if chosen is None:
            print("No untried proposals left. Use --propose to try a specific change.")
            return 0

        print(f"\n=== Iteration {iteration}: {chosen.changes} ({chosen.proposer})\n    {chosen.rationale}")
        proposed_hash = body_hash(cand_cfg)
        cand_cfg, summary, records, run_dir, calibration = run_candidate(cand_cfg, objective, out_dir)
        accepted, reasons, stats = decide(cur_records, cur_summary, records, summary, objective)
        dump_config(cand_cfg, configs_dir / "iterations" / f"{name}.yaml")
        state.data["tried"] += [proposed_hash, body_hash(cand_cfg)]
        state.data["iteration"] = iteration
        if accepted:
            state.data["current_config"] = str(configs_dir / "iterations" / f"{name}.yaml")
            state.data["current_run"] = str(run_dir)
        state.save()
        entry = entry_for(iteration, cand_cfg, chosen, summary, records, run_dir, objective,
                          "accepted" if accepted else "rejected",
                          {"reasons": reasons, "gain": stats["gain"], "bootstrap": stats["bootstrap"],
                           "folds": stats["folds"], "calibration": calibration,
                           "diagnosis_before": {"buckets": diag["buckets"],
                                                "ranked_below_k": diag["ranked_below_k"],
                                                "missed_in_candidates": diag["missed_in_candidates"]},
                           "config_diff": {k2: list(v) for k2, v in diff_configs(cur_cfg, cand_cfg).items()}})
        append_log(out_dir, entry)
        verdict = "ACCEPTED" if accepted else "rejected: " + "; ".join(reasons)
        print(f"    utility@{k} {stats['current']['utility']:.4f} -> {stats['candidate']['utility']:.4f} "
              f"(P(win) {stats['bootstrap']['p_improve']:.0%}) {verdict}")
        if args.propose:
            break

    print(f"\nCurrent best: {state.data['current_config']}. Log: {out_dir / 'LOG.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
