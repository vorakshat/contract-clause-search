"""Split contracts into passages that keep exact character offsets.

Every chunk records (doc_id, start, end) and its text is always doc[start:end], so
anything the pipeline returns can be scored against the gold spans directly.

Strategies (chunking.strategy):
  fixed      cut every chunk_size characters, with optional overlap
  recursive  split at paragraph breaks, then lines, then sentences, then words, and
             greedily pack the pieces into chunks of at most chunk_size
  clause     split at clause headings ("4.2", "Section 7", "ARTICLE III", all-caps
             heading lines), merge segments shorter than min_chunk_size into the
             next one, and split long clauses recursively
"""
from __future__ import annotations

import bisect
import re
from dataclasses import dataclass
from pathlib import Path

SEPARATORS = ["\n\n", "\n", ". ", "; ", ", ", " "]

HEADING_RE = re.compile(
    r"""^[ \t]*(?:
        (?:ARTICLE|Article|SECTION|Section|CLAUSE|Clause)\s+[0-9IVXLC]+(?:\.\d+)*\b
      | \d{1,2}(?:\.\d{1,2}){0,3}\.?[ \t]+(?=[A-Z("“])
      | [A-Z][A-Z0-9 ,&/'\-]{2,80}$
    )""",
    re.MULTILINE | re.VERBOSE,
)


@dataclass
class Chunk:
    doc_id: str
    start: int
    end: int
    text: str
    heading: str = ""
    index_text: str = ""  # what gets indexed; may carry a contextual header

    @property
    def span(self) -> tuple[str, int, int]:
        return (self.doc_id, self.start, self.end)


def doc_title(doc_id: str) -> str:
    """Readable title from a CUAD file name ("BirchFirst_2018_..._Agreement.txt")."""
    name = Path(doc_id).stem
    name = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", name)
    name = re.sub(r"[_]+", " ", name)
    return re.sub(r"\s+", " ", name).strip()


def _strip(text: str, start: int, end: int) -> tuple[int, int]:
    while start < end and text[start].isspace():
        start += 1
    while end > start and text[end - 1].isspace():
        end -= 1
    return start, end


def fixed_spans(length: int, size: int, overlap: int = 0, offset: int = 0) -> list[tuple[int, int]]:
    step = size - overlap
    spans, start = [], 0
    while start < length:
        end = min(start + size, length)
        spans.append((offset + start, offset + end))
        if end == length:
            break
        start += step
    return spans


def _split_on(text: str, start: int, end: int, sep: str) -> list[tuple[int, int]]:
    """Contiguous pieces of [start, end), each ending just after an occurrence of sep."""
    pieces, cur = [], start
    idx = text.find(sep, start, end)
    while idx != -1:
        cut = idx + len(sep)
        if cut >= end:
            break
        pieces.append((cur, cut))
        cur = cut
        idx = text.find(sep, cut, end)
    pieces.append((cur, end))
    return pieces


def _atomic_pieces(text: str, start: int, end: int, size: int, seps: list[str]) -> list[tuple[int, int]]:
    """Cut [start, end) into contiguous pieces no longer than size, preferring coarse separators."""
    if end - start <= size:
        return [(start, end)]
    for i, sep in enumerate(seps):
        pieces = _split_on(text, start, end, sep)
        if len(pieces) > 1:
            out: list[tuple[int, int]] = []
            for s, e in pieces:
                out.extend([(s, e)] if e - s <= size else _atomic_pieces(text, s, e, size, seps[i + 1:]))
            return out
    return fixed_spans(end - start, size, 0, offset=start)


def _pack(pieces: list[tuple[int, int]], size: int) -> list[tuple[int, int]]:
    """Greedily join consecutive pieces while the result stays within size."""
    chunks: list[tuple[int, int]] = []
    for s, e in pieces:
        if chunks and e - chunks[-1][0] <= size:
            chunks[-1] = (chunks[-1][0], e)
        else:
            chunks.append((s, e))
    return chunks


def recursive_spans(text: str, size: int, overlap: int = 0) -> list[tuple[int, int]]:
    spans = _pack(_atomic_pieces(text, 0, len(text), size, SEPARATORS), size)
    if overlap:
        spans = [(max(0, s - overlap) if i else s, e) for i, (s, e) in enumerate(spans)]
    return spans


def clause_spans(text: str, size: int, min_size: int) -> list[tuple[int, int]]:
    bounds = sorted({0, len(text)} | {m.start() for m in HEADING_RE.finditer(text)})
    pieces: list[tuple[int, int]] = []
    for s, e in zip(bounds, bounds[1:]):
        if e - s > size:
            pieces.extend(_pack(_atomic_pieces(text, s, e, size, SEPARATORS), size))
        elif e > s:
            pieces.append((s, e))
    merged: list[tuple[int, int]] = []
    for s, e in pieces:
        if merged and merged[-1][1] - merged[-1][0] < min_size and e - merged[-1][0] <= size:
            merged[-1] = (merged[-1][0], e)
        else:
            merged.append((s, e))
    return merged


def heading_index(text: str) -> tuple[list[int], list[str]]:
    positions, lines = [], []
    for m in HEADING_RE.finditer(text):
        line_end = text.find("\n", m.start())
        line = text[m.start(): line_end if line_end != -1 else len(text)].strip()
        positions.append(m.start())
        lines.append(line[:100])
    return positions, lines


def chunk_document(doc_id: str, text: str, cfg: dict) -> list[Chunk]:
    strategy, size = cfg["strategy"], cfg["chunk_size"]
    if strategy == "fixed":
        spans = fixed_spans(len(text), size, cfg["overlap"])
    elif strategy == "recursive":
        spans = recursive_spans(text, size, cfg["overlap"])
    elif strategy == "clause":
        spans = clause_spans(text, size, cfg["min_chunk_size"])
    else:
        raise ValueError(f"Unknown chunking strategy {strategy!r}")

    positions, lines = heading_index(text)
    title = doc_title(doc_id)
    chunks = []
    for s, e in spans:
        s, e = _strip(text, s, e)
        if e <= s:
            continue
        i = bisect.bisect_right(positions, s) - 1
        heading = lines[i] if i >= 0 else ""
        body = text[s:e]
        index_text = f"{title} | {heading}\n{body}" if cfg.get("contextual_header") else body
        chunks.append(Chunk(doc_id, s, e, body, heading, index_text))
    return chunks


def chunk_corpus(corpus: dict[str, str], cfg: dict) -> list[Chunk]:
    chunks: list[Chunk] = []
    for doc_id, text in corpus.items():
        chunks.extend(chunk_document(doc_id, text, cfg))
    return chunks
