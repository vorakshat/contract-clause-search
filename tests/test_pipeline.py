import pytest

from clausesearch import evaluate as ev
from clausesearch import prepare
from clausesearch.config import load_config
from clausesearch.data import load_corpus, load_queries
from clausesearch.pipeline import Pipeline

from .fakes import FakeCrossEncoder, FakeEncoder


@pytest.fixture
def setup(tiny_project):
    assert prepare.main(["--config", tiny_project["config_path"]]) == 0
    return tiny_project


def _cfg(setup, *overrides):
    return load_config(setup["config_path"], list(overrides))


def _assert_offsets(pipeline, result):
    for p in result.candidates:
        assert pipeline.corpus[p.doc_id][p.start:p.end] == p.text


def test_bm25_baseline_finds_most_clauses(setup):
    cfg = _cfg(setup)
    summary, records, _ = ev.evaluate(cfg, "all", write=False, progress=False)
    assert summary["n_answerable"] == 9 and summary["n_unanswerable"] == 3
    assert summary["forced"]["span_hit@4"] >= 0.75
    assert summary["false_abstention_rate"] == 0 and summary["correct_abstention_rate"] == 0


def test_every_returned_span_matches_the_document(setup):
    for strategy in ("fixed", "recursive", "clause"):
        cfg = _cfg(setup, f"chunking.strategy={strategy}", "postprocess.trim_spans=true")
        pipeline = Pipeline.from_config(cfg)
        for q in load_queries(cfg):
            _assert_offsets(pipeline, pipeline.search(q.text))


def test_routing_restricts_to_named_contract_and_abstains_on_unknown(setup):
    cfg = _cfg(setup, "routing.enabled=true", "abstention.enabled=true", "abstention.score=bm25",
               "abstention.threshold=-1")
    pipeline = Pipeline.from_config(cfg)
    res = pipeline.search("Consider the Content License Agreement between Gamma Media Ltd. and Omega Streaming "
                          "Private Limited; Can the licensee sublicense to a third-party platform?")
    assert not res.abstained and {p.doc_id for p in res.candidates} == {res.routed[0][0]}
    unknown = pipeline.search("Consider the Joint Venture Agreement between Kappa Films Inc. and Sigma Studios "
                              "Ltd.; Who owns the IP in derivative works?")
    assert unknown.abstained and unknown.reason == "contract_not_found"


def test_dense_hybrid_and_rerank_paths_with_fake_models(setup):
    encoder, cross = FakeEncoder(), FakeCrossEncoder()
    cfg = _cfg(setup, "retrieval.method=hybrid", "rerank.enabled=true", "rerank.top_n=10",
               "abstention.enabled=true", "abstention.score=rerank", "abstention.threshold=1.5",
               "query.strip_contract_prefix=true", "routing.enabled=true")
    pipeline = Pipeline(cfg, load_corpus(cfg), encoder=encoder, cross_encoder=cross)
    summary, _, _ = ev.evaluate(cfg, "all", pipeline=pipeline, write=False, progress=False)
    assert summary["forced"]["span_hit@2"] >= 0.75
    assert summary["correct_abstention_rate"] >= 2 / 3
    scored = cross.pairs_scored
    ev.evaluate(cfg, "all", pipeline=pipeline, write=False, progress=False)
    assert cross.pairs_scored == scored  # second run served entirely from the score cache


def test_dense_embeddings_are_cached(setup):
    cfg = _cfg(setup, "retrieval.method=dense")
    corpus = load_corpus(cfg)
    first = FakeEncoder()
    Pipeline(cfg, corpus, encoder=first)
    second = FakeEncoder()
    Pipeline(cfg, corpus, encoder=second)
    assert first.calls == 1 and second.calls == 0


def test_rerank_gate_requires_reranker(setup):
    with pytest.raises(ValueError):
        Pipeline.from_config(_cfg(setup, "abstention.enabled=true", "abstention.score=rerank"))


def test_evaluate_writes_run_and_guards_test_split(setup, tmp_path):
    cfg = _cfg(setup)
    summary, records, run_dir = ev.evaluate(cfg, "all", out_dir=tmp_path, progress=False)
    for name in ("config.yaml", "metrics.json", "per_query.jsonl", "summary.md"):
        assert (run_dir / name).exists()
    assert len(records) == 12
    assert ev.main(["--config", setup["config_path"], "--split", "test", "--out", str(tmp_path)]) == 2
