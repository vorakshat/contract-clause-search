import math

import pytest
import yaml

from clausesearch import loop, prepare
from clausesearch.calibrate import calibrate_threshold, simulate_gate
from clausesearch.data import load_corpus, read_jsonl
from clausesearch.pipeline import Pipeline

from .fakes import FakeCrossEncoder, FakeEncoder

RECORDS = [
    {"answerable": True, "forced": {"recall@8": 1.0}, "top_scores": {"rerank": 5.0}},
    {"answerable": True, "forced": {"recall@8": 0.5}, "top_scores": {"rerank": 3.0}},
    {"answerable": False, "top_scores": {"rerank": 1.0}},
    {"answerable": False, "top_scores": {"rerank": 2.0}},
]


def test_calibration_picks_the_best_threshold_under_the_ceiling():
    cal = calibrate_threshold(RECORDS, "rerank", k=8, max_false_abstention=0.0)
    assert cal["threshold"] == pytest.approx(2.5)
    assert cal["utility"] == pytest.approx(0.875) and cal["false_abstention_rate"] == 0


def test_routing_coverage_also_abstains_in_simulation():
    records = RECORDS + [{"answerable": False, "top_scores": {"rerank": 9.0}, "routed": [["x", 0.2]]}]
    assert simulate_gate(records, "rerank", -math.inf, 8, min_coverage=0.5)["correct_abstention_rate"] == pytest.approx(1 / 3)


def test_identical_candidate_is_rejected():
    recs = [{"qid": f"q{i}", "answerable": True, "abstained": False,
             "e2e": {"recall@8": 0.5, "precision@8": 0.1}} for i in range(6)]
    summary = {"false_abstention_rate": 0.0, "correct_abstention_rate": 0.0, "latency_ms": {"p95": 10}}
    objective = yaml.safe_load(open("configs/objective.yaml"))
    accepted, reasons, _ = loop.decide(recs, summary, recs, summary, objective)
    assert not accepted and any("below" in r for r in reasons)


def test_loop_end_to_end(tiny_project, tmp_path, monkeypatch):
    assert prepare.main(["--config", tiny_project["config_path"]]) == 0
    monkeypatch.setattr(loop, "make_pipeline", lambda cfg: Pipeline(
        cfg, load_corpus(cfg), encoder=FakeEncoder(), cross_encoder=FakeCrossEncoder()))
    objective = yaml.safe_load(open("configs/objective.yaml"))
    objective.update({"min_improvement": 0.0, "bootstrap_p": 0.0})
    obj_path = tmp_path / "objective.yaml"
    obj_path.write_text(yaml.safe_dump(objective))
    common = ["--objective", str(obj_path), "--out", str(tmp_path / "exp"), "--configs-dir", str(tmp_path / "cfg")]

    assert loop.main(["--start", tiny_project["config_path"], "--iterations", "3", *common]) == 0
    entries = read_jsonl(tmp_path / "exp" / "log.jsonl")
    assert [e["iteration"] for e in entries] == [0, 1, 2, 3] and entries[0]["decision"] == "baseline"
    assert all(e["decision"] in ("accepted", "rejected") for e in entries[1:])
    assert (tmp_path / "exp" / "LOG.md").exists() and (tmp_path / "exp" / "latest_diagnosis.md").exists()
    assert len(list((tmp_path / "cfg" / "iterations").glob("iter*.yaml"))) == 3

    assert loop.main(["--propose", "chunking.chunk_size=400", "--proposer", "claude",
                      "--rationale", "test", *common]) == 0
    assert read_jsonl(tmp_path / "exp" / "log.jsonl")[-1]["proposer"] == "claude"

    assert loop.main(["--finalize", *common]) == 0
    assert yaml.safe_load(open(tmp_path / "cfg" / "final.yaml"))["name"] == "final"
