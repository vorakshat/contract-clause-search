import json
from collections import Counter

import pytest

from clausesearch import prepare
from clausesearch.config import load_config
from clausesearch.data import (assign_split, build_queries, load_corpus, load_queries,
                               load_unanswerable, read_document, select_mini, validate_offsets)


def _fake_tests(n_queries=400, n_docs=50):
    return [{"query": f"question {i}",
             "snippets": [{"file_path": f"cuad/doc{i % n_docs}.txt", "span": [0, 1], "answer": "x"}]}
            for i in range(n_queries)]


def test_select_mini_returns_everything_when_small():
    tests = _fake_tests(10)
    assert select_mini(tests, 194) == tests


def test_select_mini_is_deterministic_and_keeps_contracts_together():
    tests = _fake_tests()
    first, second = select_mini(tests, 194), select_mini(tests, 194)
    assert first == second and len(first) == 194
    full = Counter(t["snippets"][0]["file_path"] for t in tests)
    chosen = Counter(t["snippets"][0]["file_path"] for t in first)
    partial = [f for f in chosen if chosen[f] != full[f]]
    assert len(partial) <= 1  # only the last contract can be cut


def test_assign_split_ignores_surrounding_whitespace_and_is_about_30_percent():
    assert assign_split("What is the term?") == assign_split("  What is the term?\n")
    share = sum(assign_split(f"query number {i}") == "test" for i in range(3000)) / 3000
    assert 0.25 < share < 0.35


def test_read_document_uses_universal_newlines(tmp_path):
    path = tmp_path / "doc.txt"
    path.write_bytes(b"line one\r\nline two\r\n")
    assert read_document(path) == "line one\nline two\n"


def test_validate_offsets_reports_mismatches(tmp_path):
    (tmp_path / "cuad").mkdir()
    (tmp_path / "cuad" / "a.txt").write_text("hello world", encoding="utf-8")
    tests = [
        {"query": "ok", "snippets": [{"file_path": "cuad/a.txt", "span": [6, 11], "answer": "world"}]},
        {"query": "bad", "snippets": [{"file_path": "cuad/a.txt", "span": [0, 5], "answer": "world"}]},
        {"query": "gone", "snippets": [{"file_path": "cuad/missing.txt", "span": [0, 1], "answer": "x"}]},
    ]
    problems = validate_offsets(build_queries(tests), tmp_path)
    assert [p["reason"] for p in problems] == ["text_mismatch", "missing_file"]


def test_load_unanswerable_validates_and_computes_split(tmp_path):
    path = tmp_path / "u.jsonl"
    path.write_text(json.dumps({"id": "u1", "query": "Q?", "type": "absent_clause"}) + "\n", encoding="utf-8")
    [q] = load_unanswerable(path)
    assert not q.answerable and q.split == assign_split("Q?") and q.meta["type"] == "absent_clause"

    path.write_text(json.dumps({"id": "u1", "query": "Q?", "type": "made_up"}) + "\n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_unanswerable(path)

    row = json.dumps({"id": "u1", "query": "Q?", "type": "out_of_scope"})
    path.write_text(row + "\n" + row + "\n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_unanswerable(path)


def test_prepare_end_to_end(tiny_project):
    assert prepare.main(["--config", tiny_project["config_path"]]) == 0
    cfg = load_config(tiny_project["config_path"])
    queries = load_queries(cfg)
    assert sum(q.answerable for q in queries) == 9 and sum(not q.answerable for q in queries) == 3
    corpus = load_corpus(cfg)
    assert len(corpus) == 3
    for q in queries:
        for s in q.snippets:
            assert corpus[s.file_path][s.start:s.end] == s.answer
