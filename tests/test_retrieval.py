import math

import numpy as np
import pytest

from clausesearch.bm25 import BM25Index
from clausesearch.pipeline import rrf_fuse, top_indices
from clausesearch.query import process_query
from clausesearch.routing import DocumentRouter, parse_query

from .conftest import CONTRACTS


def test_bm25_matches_the_formula_on_a_tiny_corpus():
    docs = [["assign", "consent"], ["law", "state", "law"], ["assign"]]
    index = BM25Index(docs, k1=1.5, b=0.75)
    n, avg = 3, (2 + 3 + 1) / 3
    idf = math.log(1 + (n - 2 + 0.5) / (2 + 0.5))  # "assign" is in 2 of 3 docs
    expected = idf * 1 * 2.5 / (1 + 1.5 * (1 - 0.75 + 0.75 * 2 / avg))
    assert index.scores(["assign"])[0] == pytest.approx(expected)
    assert index.scores(["law"]).argmax() == 1
    assert not index.scores(["unseen"]).any()


def test_top_indices_respects_mask_and_order():
    scores = np.array([0.1, 0.9, 0.5, 0.7])
    assert list(top_indices(scores, 2)) == [1, 3]
    assert list(top_indices(scores, 3, np.array([True, False, True, False]))) == [2, 0]


def test_rrf_rewards_agreement_between_lists():
    fused = rrf_fuse([np.array([5, 7, 9]), np.array([7, 5, 8])], k=60)
    assert max(fused, key=fused.get) in (5, 7) and fused[7] == fused[5] > fused[9]


def test_parse_query():
    contract, question = parse_query("Consider the Distribution Agreement between Acme Corp. and Beta Inc.; Is X allowed?")
    assert contract == "Distribution Agreement between Acme Corp. and Beta Inc." and question == "Is X allowed?"
    assert parse_query("Can we sublicense?") == (None, "Can we sublicense?")


def test_router_finds_named_contract_and_flags_unknown_ones():
    router = DocumentRouter(CONTRACTS)
    ranked = router.route("Content License Agreement between Gamma Media Ltd. and Omega Streaming Private Limited")
    assert "GammaMedia" in ranked[0][0] and ranked[0][1] > 0.8
    unknown = router.route("Joint Venture Agreement between Kappa Films Inc. and Sigma Studios Ltd.")
    assert unknown[0][1] < 0.5


def test_query_processing_switches():
    raw = "Consider the License between A Corp and B Ltd; Can the licensee sublicense?"
    cfg = {"query": {"strip_contract_prefix": True, "expand_categories": True}}
    pq = process_query(raw, cfg)
    assert pq.semantic == "Can the licensee sublicense?" and "sublicensable" in pq.lexical
    cfg = {"query": {"strip_contract_prefix": False, "expand_categories": False}}
    assert process_query(raw, cfg).lexical == raw
