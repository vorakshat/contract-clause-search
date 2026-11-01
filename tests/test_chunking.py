import pytest

from clausesearch.chunking import chunk_document, clause_spans, doc_title, fixed_spans, recursive_spans

from .conftest import CONTRACTS

TEXT = next(iter(CONTRACTS.values()))


def _cfg(**over):
    cfg = {"strategy": "fixed", "chunk_size": 200, "overlap": 0, "min_chunk_size": 80, "contextual_header": False}
    cfg.update(over)
    return cfg


@pytest.mark.parametrize("strategy", ["fixed", "recursive", "clause"])
def test_chunks_keep_exact_offsets_and_respect_size(strategy):
    chunks = chunk_document("cuad/x.txt", TEXT, _cfg(strategy=strategy))
    assert chunks
    for c in chunks:
        assert TEXT[c.start:c.end] == c.text and c.text == c.text.strip()
        assert len(c.text) <= 200


def test_fixed_spans_cover_text_with_overlap():
    spans = fixed_spans(1000, 300, 100)
    assert spans[0] == (0, 300) and spans[1] == (200, 500) and spans[-1][1] == 1000


def test_recursive_and_clause_spans_cover_the_whole_text():
    for spans in (recursive_spans(TEXT, 200), clause_spans(TEXT, 200, 80)):
        assert spans[0][0] == 0 and spans[-1][1] == len(TEXT)
        assert all(a[1] == b[0] for a, b in zip(spans, spans[1:]))  # contiguous, no gaps


def test_clause_chunking_starts_chunks_at_headings():
    chunks = chunk_document("cuad/x.txt", TEXT, _cfg(strategy="clause", chunk_size=400, min_chunk_size=60))
    assert any(c.text.startswith("4. ASSIGNMENT") for c in chunks)


def test_contextual_header_changes_indexed_text_not_offsets():
    plain = chunk_document("cuad/Acme_Distribution Agreement.txt", TEXT, _cfg())
    ctx = chunk_document("cuad/Acme_Distribution Agreement.txt", TEXT, _cfg(contextual_header=True))
    assert [c.span for c in plain] == [c.span for c in ctx]
    assert ctx[3].index_text.startswith("Acme Distribution Agreement |")


def test_doc_title():
    assert doc_title("cuad/BirchFirstGlobal_2018_Marketing Agreement.txt") == "Birch First Global 2018 Marketing Agreement"
