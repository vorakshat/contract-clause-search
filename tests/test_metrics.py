import pytest

from clausesearch.metrics import (abstention_rates, diagnose_answerable, diagnose_unanswerable,
                                  first_hit_rank, merge_spans, paired_bootstrap, per_query_metrics,
                                  precision_recall)

GOLD = [("a.txt", 1000, 1200)]


def test_worked_example_from_the_explanation():
    assert precision_recall([("a.txt", 900, 1400)], GOLD) == pytest.approx((0.4, 1.0))
    assert precision_recall([("a.txt", 900, 1400), ("a.txt", 5000, 5500)], GOLD) == pytest.approx((0.2, 1.0))
    assert precision_recall([("a.txt", 1100, 1600)], GOLD) == pytest.approx((0.2, 0.5))


def test_overlapping_retrieved_spans_are_not_double_counted():
    merged = merge_spans([("a", 0, 100), ("a", 50, 150), ("a", 150, 160), ("b", 5, 6)])
    assert merged == {"a": [(0, 160)], "b": [(5, 6)]}
    assert precision_recall([("a", 0, 100), ("a", 50, 100)], [("a", 0, 100)]) == (1.0, 1.0)


def test_wrong_file_and_empty_retrieval_score_zero():
    assert precision_recall([("b.txt", 1000, 1200)], GOLD) == (0.0, 0.0)
    assert precision_recall([], GOLD) == (0.0, 0.0)


def test_multiple_gold_snippets():
    gold = [("a", 0, 100), ("a", 200, 300)]
    assert precision_recall([("a", 0, 100)], gold) == (1.0, 0.5)


def test_per_query_metrics_hits_and_mrr():
    ranked = [("b.txt", 0, 500), ("a.txt", 0, 500), ("a.txt", 900, 1400)]
    m = per_query_metrics(ranked, GOLD, [1, 2, 3])
    assert m["doc_hit@1"] == 0 and m["doc_hit@2"] == 1
    assert m["span_hit@2"] == 0 and m["span_hit@3"] == 1
    assert m["recall@3"] == 1.0 and m["mrr"] == pytest.approx(1 / 3)
    assert first_hit_rank(ranked, GOLD) == 3


def test_diagnosis_buckets():
    k, near = 2, 1500
    assert diagnose_answerable([], GOLD, True, k, near) == "false_abstention"
    assert diagnose_answerable([("b.txt", 0, 500)], GOLD, False, k, near) == "wrong_document"
    assert diagnose_answerable([("a.txt", 9000, 9500)], GOLD, False, k, near) == "wrong_section"
    assert diagnose_answerable([("a.txt", 2000, 2500)], GOLD, False, k, near) == "near_miss"
    assert diagnose_answerable([("a.txt", 1100, 1600)], GOLD, False, k, near) == "partial"
    assert diagnose_answerable([("a.txt", 900, 1400)], GOLD, False, k, near) == "full"
    assert diagnose_unanswerable(True) == "correct_abstention"
    assert diagnose_unanswerable(False) == "false_answer"


def test_abstention_rates():
    records = [{"answerable": True, "abstained": False}, {"answerable": True, "abstained": True},
               {"answerable": False, "abstained": True}, {"answerable": False, "abstained": True}]
    rates = abstention_rates(records)
    assert rates["false_abstention_rate"] == 0.5 and rates["correct_abstention_rate"] == 1.0


def test_paired_bootstrap():
    better = paired_bootstrap([0.6, 0.7, 0.8, 0.9], [0.5, 0.6, 0.7, 0.8])
    assert better["mean_diff"] == pytest.approx(0.1) and better["p_improve"] == 1.0 and better["ci_low"] > 0
    same = paired_bootstrap([0.5, 0.5], [0.5, 0.5])
    assert same["mean_diff"] == 0 and same["p_improve"] == 0
