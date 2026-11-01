"""Build the unanswerable query set with a fixed, seeded procedure.

    python scripts/build_unanswerable.py --out data/unanswerable.jsonl

Run once, review the output by hand, then commit it and never edit it again. Every
query uses the benchmark's own format ("Consider the <contract>; <question>"), so the
system cannot recognise unanswerable questions by their wording.

absent_clause   An indexed contract's own description plus a benchmark question type
                that is (a) never asked about that contract anywhere in the full CUAD
                benchmark and (b) has zero matches for a strict list of synonyms of the
                clause in that contract's text. At most one per contract.
not_in_corpus   Real benchmark questions about CUAD contracts that are not among the
                indexed ones, skipping contracts from the same company as an indexed
                one and descriptions whose party names occur in any indexed contract.
out_of_scope    An indexed contract's description plus a question about facts no
                contract records (share price, credit rating, revenue, ...), kept only
                if the topic's key terms have zero matches in that contract.

Benchmark annotations are used here only to label evaluation queries, never by the
pipeline.
"""
from __future__ import annotations

import argparse
import json
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from clausesearch.config import load_config  # noqa: E402
from clausesearch.data import load_benchmark, load_corpus, load_queries  # noqa: E402
from clausesearch.routing import parse_query  # noqa: E402

# Benchmark question -> regex of words that would indicate the clause is present.
# Deliberately broad: any match disqualifies the (contract, question) pair.
ABSENCE_CHECKS = {
    "What is the governing law for this contract?": r"govern|laws of|construed|jurisdiction",
    "Is there a cap on liability under this contract?": r"liab|consequential|in no event|limitation of",
    "Is there uncapped liability under this contract?": r"liab|indemnif|in no event",
    "What are the audit rights under this contract?": r"audit|inspect|books and records|examin",
    "What is the renewal term for this contract?": r"renew|extend|extension|successive",
    "What is the notice period required to terminate the renewal?": r"renew|extend|extension|successive",
    "Can this contract be terminated for convenience, and under what conditions?":
        r"convenience|without cause|for any reason|at any time",
    "Does this contract include an exclusivity agreement?": r"exclusiv",
    "Are there any services to be provided after the termination of this contract?":
        r"after (the )?(termination|expiration)|following (the )?(termination|expiration)|transition|surviv|wind.?down",
    "Does this contract include any revenue or profit-sharing arrangements?":
        r"revenue|profit|royalt|commission|percent|%",
    "What are the insurance requirements under this contract?": r"insur",
    "Is there a minimum commitment required under this contract?": r"minimum|at least|commit",
    "How is intellectual property ownership assigned in this contract?":
        r"intellectual property|patent|copyright|trademark|work product|invention|ownership|title to",
    "Does this contract provide for joint intellectual property ownership?":
        r"joint|co-own|intellectual property|patent|invention",
    "Is there a non-compete clause in this contract?": r"compet|exclusiv|restrict",
    "Are there any exceptions to competitive restrictions in this contract?": r"compet|exclusiv|restrict",
    "What happens in the event of a change of control of one of the parties in this contract?":
        r"change (of|in) control|merger|acquisition|acquire|consolidat|controlling interest|reorganiz",
    "Is there a covenant not to sue included in this contract?": r"\bsue\b|challenge|contest|bring (any )?(action|claim|suit)",
    "Does this contract include any right of first refusal, right of first offer, or right of first negotiation?":
        r"first refusal|first offer|first negotiat|right of first|\bmatch",
    "What is the duration of any warranties provided in this contract?": r"warrant|guarant|defect",
    "Is there a clause preventing the solicitation of employees in this contract?":
        r"solicit|hire|employ|recruit|personnel",
    "Is there a clause preventing the solicitation of customers in this contract?":
        r"solicit|customer|client|divert|interfer",
    "Are there any third-party beneficiaries designated in this contract?": r"beneficiar|third part",
    "Is there a most favored nation clause in this contract?":
        r"favou?red|most favou?rable|no less favou?rable|best price|lowest price|comparable terms",
    "Is there a non-disparagement clause in this contract?": r"disparag|derogator|negative statement|defam|reputation",
    "Are there any price restrictions or controls specified in this contract?": r"price|pricing|discount",
    "What licenses are granted under this contract?": r"licen",
    "Are the licenses granted under this contract non-transferable?": r"licen",
    "Are any of the licenses granted under this contract irrevocable or perpetual?": r"licen|irrevocab|perpetu",
    "Does the licensee's affiliates have any licensing rights under this contract?": r"licen",
    "Does the licensor's affiliates have any licensing rights under this contract?": r"licen",
    "Does this contract include an unlimited or all-you-can-eat license?": r"licen|unlimited",
}

# Questions about facts that contracts do not record, with the words whose presence
# would make the label doubtful for a given contract.
OUT_OF_SCOPE = [
    ("What was the share price of each party on the date this contract was signed?",
     r"share price|stock price|per share|trading price|closing price"),
    ("What credit rating did each party hold when this contract was signed?",
     r"credit rating|rating agenc|moody|standard & poor|s&p|fitch"),
    ("What market share does each party hold in its industry?", r"market share"),
    ("Who founded each of the parties to this contract?", r"founde[dr]"),
    ("What was each party's total annual revenue in the year this contract was signed?",
     r"revenue|annual sales|turnover"),
    ("What was each party's net profit in the year after this contract was signed?",
     r"profit|net income|earnings"),
    ("Which of the parties had the larger market capitalisation when this contract was signed?",
     r"market capitali[sz]ation|market cap\b"),
    ("Did the shareholders of either party vote to approve this contract, and by what margin?",
     r"shareholder|stockholder|\bvote"),
]


def company_prefix(file_path: str) -> str:
    return Path(file_path).name.split("_")[0].lower()


def party_names(description: str) -> list[str]:
    """Rough party names from '<type> between A and B ...' (used only to filter)."""
    match = re.search(r"\bbetween\b(.+)", description, re.IGNORECASE)
    if not match:
        return []
    names = []
    for part in re.split(r"\band\b", match.group(1)):
        name = part.split(",")[0].strip(" .;")
        name = re.sub(r"\b(inc|corp|corporation|llc|ltd|limited|co|company|l\.?p)\.?$", "", name,
                      flags=re.IGNORECASE).strip(" .,")
        if len(name) >= 4:
            names.append(name.lower())
    return names


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", default="configs/baseline.yaml")
    ap.add_argument("--out", default="data/unanswerable.jsonl")
    ap.add_argument("--seed", type=int, default=20261101)
    ap.add_argument("--absent", type=int, default=20)
    ap.add_argument("--not-indexed", type=int, default=13)
    ap.add_argument("--out-of-scope", type=int, default=12)
    args = ap.parse_args()

    cfg = load_config(args.config)
    tests = load_benchmark(cfg["data"]["benchmark_path"])
    corpus = load_corpus(cfg)
    lowered = {fp: text.lower() for fp, text in corpus.items()}
    mini = load_queries(cfg, include_unanswerable=False)
    rng = random.Random(args.seed)

    asked: dict[str, set[str]] = defaultdict(set)
    for t in tests:
        question = parse_query(t["query"])[1]
        for s in t["snippets"]:
            asked[s["file_path"]].add(question)

    descriptions: dict[str, str] = {}
    by_file: dict[str, Counter] = defaultdict(Counter)
    for q in mini:
        contract = parse_query(q.text)[0]
        if contract:
            by_file[q.snippets[0].file_path][contract] += 1
    for fp, counts in by_file.items():
        descriptions[fp] = counts.most_common(1)[0][0]

    rows: list[dict] = []
    contracts = sorted(corpus)
    rng.shuffle(contracts)

    # 1. absent_clause: one per contract, spreading clause types as evenly as possible.
    used_types: Counter = Counter()
    for fp in contracts:
        if sum(r["type"] == "absent_clause" for r in rows) >= args.absent or fp not in descriptions:
            continue
        clean = [q for q, pattern in ABSENCE_CHECKS.items()
                 if q not in asked[fp] and not re.search(pattern, lowered[fp])]
        if not clean:
            continue
        rng.shuffle(clean)
        question = min(clean, key=lambda q: used_types[q])
        used_types[question] += 1
        rows.append({"type": "absent_clause", "query": f"Consider the {descriptions[fp]}; {question}",
                     "contract": fp,
                     "rationale": "Clause type never asked about this contract in the full benchmark.",
                     "verified": f"0 matches in the contract for /{ABSENCE_CHECKS[question]}/"})

    # 2. not_in_corpus: real benchmark questions about contracts that are not indexed.
    indexed_prefixes = {company_prefix(fp) for fp in corpus}
    pool: dict[str, list[str]] = defaultdict(list)
    for t in tests:
        files = {s["file_path"] for s in t["snippets"]}
        if len(files) != 1:
            continue
        fp = next(iter(files))
        if fp in corpus or company_prefix(fp) in indexed_prefixes:
            continue
        contract = parse_query(t["query"])[0]
        if not contract or any(name in text for name in party_names(contract) for text in lowered.values()):
            continue
        pool[fp].append(t["query"])
    candidates = sorted(pool)
    rng.shuffle(candidates)
    used_types = Counter()
    for fp in candidates[:args.not_indexed]:
        queries = sorted(pool[fp])
        rng.shuffle(queries)
        query = min(queries, key=lambda q: used_types[parse_query(q)[1]])
        used_types[parse_query(query)[1]] += 1
        rows.append({"type": "not_in_corpus", "query": query, "contract": fp,
                     "rationale": "Real benchmark question about a CUAD contract that is not indexed.",
                     "verified": "Contract file not in the indexed set; no indexed contract from the same "
                                 "company; party names not found in any indexed contract"})

    # 3. out_of_scope: facts that contracts do not record.
    order = [fp for fp in contracts if fp in descriptions]
    rng.shuffle(order)
    used = Counter()
    for fp in order:
        if sum(r["type"] == "out_of_scope" for r in rows) >= args.out_of_scope:
            break
        clean = [(q, p) for q, p in OUT_OF_SCOPE if not re.search(p, lowered[fp])]
        if not clean:
            continue
        question, pattern = min(clean, key=lambda qp: (used[qp[0]], OUT_OF_SCOPE.index(qp)))
        used[question] += 1
        rows.append({"type": "out_of_scope", "query": f"Consider the {descriptions[fp]}; {question}",
                     "contract": fp, "rationale": "Asks for a fact that contracts do not record.",
                     "verified": f"0 matches in the contract for /{pattern}/"})

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        for i, row in enumerate(rows, 1):
            rest = {k: v for k, v in row.items() if k not in ("query", "type")}
            ordered = {"id": f"u{i:03d}", "query": row["query"], "type": row["type"], **rest}
            fh.write(json.dumps(ordered, ensure_ascii=False) + "\n")
    counts = Counter(r["type"] for r in rows)
    print(f"Wrote {len(rows)} queries to {args.out}: {dict(counts)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
