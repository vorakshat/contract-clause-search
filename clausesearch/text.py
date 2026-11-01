"""Tokenisation shared by BM25, document routing and span trimming."""
from __future__ import annotations

import re
from functools import lru_cache

import snowballstemmer

TOKEN_RE = re.compile(r"[a-z0-9]+")

STOPWORDS = frozenset("""
a about above after all also an and any are as at be been being between both but by can could
consider did do does doing during each either for from further had has have having he her here
hers him his how i if in into is it its itself me more most my no nor not of off on once only or
other our out over own same she should so some such than that the their them then there these
they this those through to too under until up very was we were what when where which while who
whom why will with would you your agreement document contract clause
""".split())

_STEMMER = snowballstemmer.stemmer("english")


@lru_cache(maxsize=200_000)
def stem(token: str) -> str:
    return _STEMMER.stemWord(token)


def tokenize(text: str, stopwords: bool = False, stem_tokens: bool = False) -> list[str]:
    tokens = TOKEN_RE.findall(text.lower())
    if stopwords:
        tokens = [t for t in tokens if t not in STOPWORDS]
    if stem_tokens:
        tokens = [stem(t) for t in tokens]
    return tokens
