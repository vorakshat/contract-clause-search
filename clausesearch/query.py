"""Turn a user question into the texts used for retrieval.

Two optional rules (both config switches):
  query.strip_contract_prefix  match on the question only, not on the contract
                               description, once routing has used the description
  query.expand_categories      append synonyms for the CUAD clause type the question
                               is about, so keyword search can match clauses worded
                               differently from the question
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from .routing import parse_query

EXPANSIONS: list[tuple[str, str]] = [
    (r"\bassign", "assign assignment transfer consent successor"),
    (r"change (?:of|in) control", "change control merger acquisition consolidation"),
    (r"convenience|without cause", "terminate convenience without cause notice"),
    (r"renew", "renew renewal term extend automatically"),
    (r"governing law|govern", "governed laws state jurisdiction construed"),
    (r"exclusiv", "exclusive exclusivity sole only"),
    (r"compet", "compete competing competitor competitive restrict"),
    (r"solicit", "solicit hire employ employees customers"),
    (r"most favou?red", "favored favorable terms pricing no less"),
    (r"liabilit|\bcap\b|capped|uncapped", "liability liable damages exceed aggregate limitation"),
    (r"liquidated", "liquidated damages penalty"),
    (r"warrant", "warranty warrants defects period"),
    (r"insurance", "insurance insured coverage policy"),
    (r"audit", "audit inspect books records"),
    (r"intellectual property|\bip\b|owner", "intellectual property own owned ownership rights title"),
    (r"sublicens", "sublicense sublicensable third party"),
    (r"licen[cs]", "license licensed grant rights"),
    (r"source code|escrow", "source code escrow"),
    (r"beneficiar", "third party beneficiary beneficiaries"),
    (r"minimum|commitment", "minimum purchase commitment volume"),
    (r"revenue|profit|royalt", "revenue share royalty royalties percent"),
    (r"price|pricing", "price pricing increase"),
    (r"notice period|notice", "notice days prior written"),
    (r"effective date|agreement date|dated|signed", "effective date dated entered"),
    (r"expir|duration|initial term", "term expire expiration years"),
    (r"\bsue\b|covenant not", "sue challenge contest validity"),
    (r"disparag", "disparage disparaging"),
    (r"first refusal|first offer|first negotiat|rofr|rofo", "right first refusal offer negotiate"),
    (r"post-?termination|after termination", "after termination survive transition"),
    (r"part(?:y|ies)", "parties party between"),
]


@dataclass
class ProcessedQuery:
    raw: str
    contract: str | None   # contract description, if the question names one
    question: str          # the question without the description
    lexical: str           # text for keyword search
    semantic: str          # text for embedding search and reranking


def expansion_terms(question: str) -> str:
    lowered = question.lower()
    extra = [terms for pattern, terms in EXPANSIONS if re.search(pattern, lowered)]
    return " ".join(extra)


def process_query(raw: str, cfg: dict) -> ProcessedQuery:
    contract, question = parse_query(raw)
    base = question if (cfg["query"]["strip_contract_prefix"] and contract) else raw.strip()
    lexical = base
    if cfg["query"]["expand_categories"]:
        extra = expansion_terms(question)
        if extra:
            lexical = f"{base} {extra}"
    return ProcessedQuery(raw=raw, contract=contract, question=question, lexical=lexical, semantic=base)
