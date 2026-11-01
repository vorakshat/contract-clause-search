import threading

from clausesearch import prepare
from clausesearch.config import load_config
from clausesearch.data import load_corpus
from clausesearch.pipeline import Pipeline
from clausesearch.rerank import ScoreCache

from .fakes import FakeCrossEncoder, FakeEncoder


def _in_thread(fn):
    """Run fn on a new thread (as Streamlit does for each interaction); re-raise its errors."""
    box = {}

    def target():
        try:
            box["value"] = fn()
        except Exception as err:  # noqa: BLE001
            box["error"] = err

    t = threading.Thread(target=target)
    t.start()
    t.join()
    if "error" in box:
        raise box["error"]
    return box["value"]


def test_score_cache_can_be_used_from_another_thread(tmp_path):
    cache = ScoreCache(tmp_path / "scores.sqlite")
    cache.put_many({"a": 1.5})
    assert _in_thread(lambda: cache.get_many(["a", "b"])) == {"a": 1.5}
    _in_thread(lambda: cache.put_many({"b": -2.0}))
    assert cache.get_many(["a", "b"]) == {"a": 1.5, "b": -2.0}


def test_pipeline_with_reranker_searches_from_another_thread(tiny_project):
    assert prepare.main(["--config", tiny_project["config_path"]]) == 0
    cfg = load_config(tiny_project["config_path"], ["rerank.enabled=true", "retrieval.method=hybrid"])
    pipeline = Pipeline(cfg, load_corpus(cfg), encoder=FakeEncoder(), cross_encoder=FakeCrossEncoder())
    question = ("Consider the Content License Agreement between Gamma Media Ltd. and Omega Streaming Private "
                "Limited; Can the licensee sublicense to a third-party platform?")
    first = _in_thread(lambda: pipeline.search(question))
    second = _in_thread(lambda: pipeline.search(question))  # served from the cache on another thread
    assert first.passages and [p.span for p in first.passages] == [p.span for p in second.passages]
