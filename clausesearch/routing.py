"""Work out which indexed contract a question is about.

CUAD questions name their contract: "Consider the <type> between <party A> and
<party B>; <question>". The router compares the informative words of that
description with each contract's profile (its file name plus its opening text, where
the parties are introduced) and scores coverage: the IDF-weighted share of
description words found in the profile. Rare words such as party names dominate;
words found in every contract ("inc", "corporation") count for little, and words
found in no contract at all count fully against every candidate, which is what
makes questions about contracts that are not indexed score low.
"""
from __future__ import annotations

import math
import re
from collections import Counter

from .chunking import doc_title
from .text import tokenize

PREFIX_RE = re.compile(r"^\s*consider\s+(?:the\s+)?(?P<contract>[^;]+?)\s*;\s*(?P<question>.+)$",
                       re.IGNORECASE | re.DOTALL)


def parse_query(query: str) -> tuple[str | None, str]:
    """Split "Consider the X between A and B; question" into (contract description, question)."""
    match = PREFIX_RE.match(query)
    if not match:
        return None, query.strip()
    return match.group("contract").strip(), match.group("question").strip()


class DocumentRouter:
    def __init__(self, corpus: dict[str, str], header_chars: int = 4000):
        self.doc_ids = list(corpus)
        self.profiles = [
            set(tokenize(doc_title(d) + "\n" + corpus[d][:header_chars], stopwords=True, stem_tokens=True))
            for d in self.doc_ids
        ]
        n = max(len(self.doc_ids), 1)
        df = Counter(t for profile in self.profiles for t in profile)
        self._idf = {t: math.log(1 + n / c) for t, c in df.items()}
        self._unseen_idf = math.log(1 + n / 0.5)

    def idf(self, term: str) -> float:
        return self._idf.get(term, self._unseen_idf)

    def route(self, description: str) -> list[tuple[str, float]]:
        """All contracts ranked by coverage of the description (1.0 = every word found)."""
        terms = set(tokenize(description, stopwords=True, stem_tokens=True))
        if not terms:
            return []
        total = sum(self.idf(t) for t in terms)
        scored = [(doc, sum(self.idf(t) for t in terms if t in profile) / total)
                  for doc, profile in zip(self.doc_ids, self.profiles)]
        return sorted(scored, key=lambda item: -item[1])
