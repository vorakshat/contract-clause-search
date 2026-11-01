"""A tiny synthetic project (three contracts, a benchmark file, an unanswerable set)
so the pipeline can be tested end to end without downloading anything."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

CONTRACTS = {
    "cuad/AcmeCorp_20190301_EX-10.1_Distribution Agreement.txt": """DISTRIBUTION AGREEMENT

This Distribution Agreement (the "Agreement") is entered into as of March 1, 2019 by and between Acme Corp., a Delaware corporation ("Acme"), and Beta Retail Inc., a New York corporation ("Distributor").

1. DEFINITIONS
1.1 "Products" means the consumer electronics listed in Exhibit A.
1.2 "Territory" means India and Sri Lanka.

2. APPOINTMENT
2.1 Acme appoints Distributor as its exclusive distributor of the Products in the Territory during the Term.

3. TERM AND TERMINATION
3.1 This Agreement shall commence on the Effective Date and continue for three (3) years.
3.2 Either party may terminate this Agreement for convenience upon sixty (60) days prior written notice to the other party.

4. ASSIGNMENT
4.1 Neither party may assign or transfer this Agreement or any rights hereunder without the prior written consent of the other party, except to a successor in a merger or acquisition.

5. GOVERNING LAW
5.1 This Agreement shall be governed by and construed in accordance with the laws of the State of New York.

6. LIMITATION OF LIABILITY
6.1 In no event shall either party's aggregate liability under this Agreement exceed the fees paid by Distributor in the twelve (12) months preceding the claim.
""",
    "cuad/GammaMediaLtd_20200115_EX-10.2_Content License Agreement.txt": """CONTENT LICENSE AGREEMENT

This Content License Agreement is made on January 15, 2020 between Gamma Media Ltd. ("Licensor") and Omega Streaming Private Limited ("Licensee").

ARTICLE 1 GRANT OF LICENSE
1.1 Licensor grants Licensee a non-exclusive, non-transferable license to stream the Programs in the Territory.
1.2 Licensee may not sublicense any of its rights under this Agreement to any third party platform without Licensor's prior written approval.

ARTICLE 2 EXCLUSIVITY
2.1 During the first eighteen (18) months after launch, Licensor shall not license the Programs to any other streaming service in the Territory.

ARTICLE 3 INTELLECTUAL PROPERTY
3.1 All intellectual property in derivative works created by Licensee, including clips and trailers, shall be owned exclusively by Licensor.

ARTICLE 4 AUDIT
4.1 Licensor may audit Licensee's books and records relating to subscriber counts once per calendar year upon thirty (30) days notice.

ARTICLE 5 INSURANCE
5.1 Licensee shall maintain general liability insurance of not less than USD 2,000,000 per occurrence.
""",
    "cuad/DeltaSportsLLC_20180610_EX-10.3_Sponsorship Agreement.txt": """SPONSORSHIP AGREEMENT

This Sponsorship Agreement is entered into on June 10, 2018 by Delta Sports LLC ("Team") and Zeta Beverages Inc. ("Sponsor").

Section 1. Sponsorship Rights. Team grants Sponsor the right to display its marks on the team jersey during the 2018 and 2019 seasons.

Section 2. Non-Competition. During the Term, Team shall not enter into any sponsorship agreement with a competing beverage company.

Section 3. Confidentiality. Each party shall keep the financial terms of this Agreement confidential.

Section 4. Indemnification. Sponsor shall indemnify Team against all claims arising from Sponsor's products.

Section 5. Termination. Team may terminate this Agreement immediately if Sponsor fails to pay any sponsorship fee within fifteen (15) days of its due date.
""",
}

# (contract, question, exact answer text)
QUESTIONS = [
    ("AcmeCorp", "Consider the Distribution Agreement between Acme Corp. and Beta Retail Inc.; Is consent required to assign the agreement?",
     "4.1 Neither party may assign or transfer this Agreement or any rights hereunder without the prior written consent of the other party, except to a successor in a merger or acquisition."),
    ("AcmeCorp", "Consider the Distribution Agreement between Acme Corp. and Beta Retail Inc.; Which state's law governs the contract?",
     "5.1 This Agreement shall be governed by and construed in accordance with the laws of the State of New York."),
    ("AcmeCorp", "Consider the Distribution Agreement between Acme Corp. and Beta Retail Inc.; Can a party terminate for convenience?",
     "3.2 Either party may terminate this Agreement for convenience upon sixty (60) days prior written notice to the other party."),
    ("AcmeCorp", "Consider the Distribution Agreement between Acme Corp. and Beta Retail Inc.; Is there a cap on liability?",
     "6.1 In no event shall either party's aggregate liability under this Agreement exceed the fees paid by Distributor in the twelve (12) months preceding the claim."),
    ("GammaMedia", "Consider the Content License Agreement between Gamma Media Ltd. and Omega Streaming Private Limited; Can the licensee sublicense to a third-party platform?",
     "1.2 Licensee may not sublicense any of its rights under this Agreement to any third party platform without Licensor's prior written approval."),
    ("GammaMedia", "Consider the Content License Agreement between Gamma Media Ltd. and Omega Streaming Private Limited; When does the exclusivity period end?",
     "2.1 During the first eighteen (18) months after launch, Licensor shall not license the Programs to any other streaming service in the Territory."),
    ("GammaMedia", "Consider the Content License Agreement between Gamma Media Ltd. and Omega Streaming Private Limited; Who owns the IP in derivative works?",
     "3.1 All intellectual property in derivative works created by Licensee, including clips and trailers, shall be owned exclusively by Licensor."),
    ("DeltaSports", "Consider the Sponsorship Agreement between Delta Sports LLC and Zeta Beverages Inc.; Is there a non-compete restriction?",
     "Section 2. Non-Competition. During the Term, Team shall not enter into any sponsorship agreement with a competing beverage company."),
    ("DeltaSports", "Consider the Sponsorship Agreement between Delta Sports LLC and Zeta Beverages Inc.; Does the sponsor indemnify the team?",
     "Section 4. Indemnification. Sponsor shall indemnify Team against all claims arising from Sponsor's products."),
]

UNANSWERABLE = [
    {"id": "u001", "query": "Consider the Distribution Agreement between Acme Corp. and Beta Retail Inc.; Is there a most favored nation clause?",
     "type": "absent_clause", "rationale": "No pricing parity clause in the contract."},
    {"id": "u002", "query": "Consider the Joint Venture Agreement between Kappa Films Inc. and Sigma Studios Ltd.; Who owns the IP in derivative works?",
     "type": "not_in_corpus", "rationale": "No such contract is indexed."},
    {"id": "u003", "query": "Consider the Sponsorship Agreement between Delta Sports LLC and Zeta Beverages Inc.; What was the sponsor's revenue in 2017?",
     "type": "out_of_scope", "rationale": "Company financials are not in the contract."},
]


@pytest.fixture
def tiny_project(tmp_path: Path) -> dict:
    corpus = tmp_path / "corpus"
    for rel, text in CONTRACTS.items():
        path = corpus / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        # The license contract uses Windows line endings: offsets must still line up
        # because documents are read with universal newlines.
        payload = text.replace("\n", "\r\n") if "Gamma" in rel else text
        path.write_bytes(payload.encode("utf-8"))

    by_key = {rel.split("/")[1].split("_")[0][:10]: rel for rel in CONTRACTS}
    tests = []
    for key, question, answer in QUESTIONS:
        rel = next(r for k, r in by_key.items() if k.startswith(key[:8]))
        start = CONTRACTS[rel].index(answer)
        tests.append({"query": question, "snippets": [
            {"file_path": rel, "span": [start, start + len(answer)], "answer": answer}]})
    bench = tmp_path / "benchmarks" / "cuad.json"
    bench.parent.mkdir(parents=True)
    bench.write_text(json.dumps({"tests": tests}), encoding="utf-8")

    unans = tmp_path / "unanswerable.jsonl"
    unans.write_text("\n".join(json.dumps(u) for u in UNANSWERABLE) + "\n", encoding="utf-8")

    cfg_path = tmp_path / "config.yaml"
    cfg = {
        "name": "tiny",
        "data": {"benchmark_path": str(bench), "corpus_dir": str(corpus),
                 "processed_dir": str(tmp_path / "processed"), "unanswerable_path": str(unans)},
        "cache_dir": str(tmp_path / "cache"),
        "chunking": {"chunk_size": 300},
    }
    cfg_path.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    return {"root": tmp_path, "config_path": str(cfg_path), "tests": tests}
