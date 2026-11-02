# Experiment log

Objective, guardrails and acceptance rule: `configs/objective.yaml`. Every entry is a train-split run.
utility@8 = per-query score (recall@8 for benchmark questions, 1 for a correct abstention on an unanswerable one). R and P are end-to-end character recall and precision at 8. FAR = false abstention rate, CAR = correct abstention rate.

| iter | change | proposer | utility@8 | Δ vs current | R@8 | P@8 | FAR | CAR | P(win) | decision |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | (baseline) | baseline | 0.0661 | – | 0.0803 | 0.0089 | 0.0% | 0.0% | – | baseline |
| 1 | `routing.enabled=True`; `query.strip_contract_prefix=True` | rules | 0.3276 | +0.2615 | 0.3978 | 0.0456 | 0.0% | 0.0% | 100% | accepted |
| 2 | `abstention.enabled=True` | rules | 0.3688 | +0.0412 | 0.3978 | 0.0456 | 0.0% | 23.3% | 100% | accepted |
| 3 | `rerank.enabled=True` | rules | 0.6347 | +0.2659 | 0.6064 | 0.0632 | 10.0% | 76.7% | 100% | accepted |
| 4 | `retrieval.method=hybrid` | rules | 0.6564 | +0.0216 | 0.6399 | 0.0693 | 9.3% | 73.3% | 90% | accepted |
| 5 | `query.expand_categories=True` | rules | 0.6613 | +0.0049 | 0.6459 | 0.0704 | 9.3% | 73.3% | 92% | rejected |
| 6 | `retrieval.bm25.stem=True`; `retrieval.bm25.stopwords=True` | rules | 0.6592 | +0.0028 | 0.6433 | 0.0696 | 9.3% | 73.3% | 62% | rejected |
| 7 | `chunking.contextual_header=True` | claude | 0.6559 | -0.0005 | 0.6536 | 0.0736 | 5.7% | 66.7% | 51% | rejected |
| 8 | `chunking.strategy=clause`; `chunking.chunk_size=600` | rules | 0.7071 | +0.0508 | 0.7158 | 0.0903 | 5.0% | 66.7% | 99% | rejected |
| 9 | `chunking.chunk_size=750` | rules | 0.6856 | +0.0293 | 0.7397 | 0.0565 | 2.9% | 43.3% | 84% | rejected |
| 10 | `postprocess.trim_spans=True` | rules | 0.5858 | -0.0705 | 0.5542 | 0.0794 | 9.3% | 73.3% | 0% | rejected |
| 11 | `chunking.strategy=clause`; `chunking.chunk_size=600` | claude | 0.7071 | +0.0508 | 0.7086 | 0.0899 | 7.9% | 70.0% | 100% | accepted |
| 12 | `query.expand_categories=True` | rules | 0.7023 | -0.0048 | 0.7099 | 0.0894 | 5.0% | 66.7% | 29% | rejected |
| 13 | `retrieval.bm25.stem=True`; `retrieval.bm25.stopwords=True` | rules | 0.7087 | +0.0016 | 0.7106 | 0.0895 | 5.0% | 70.0% | 57% | rejected |

## Details

### Iteration 0: baseline (baseline)

- Proposed by: baseline
- Why: Simplest end-to-end pipeline; reference point.
- Changes: {}
- Run: `experiments\runs\20261102-001300_baseline_train`

### Iteration 1: accepted (iter01)

- Proposed by: rules
- Why: 0% of benchmark queries have no passage from the right contract in the top 8, and passages from other contracts dilute precision. Questions name their contract, so route to it and match on the question alone; this also lets the gate refuse questions about contracts that are not indexed.
- Changes: {"routing.enabled": true, "query.strip_contract_prefix": true}
- Δ utility on train halves: {"fold0": 0.2212, "fold1": 0.3048}
- Run: `experiments\runs\20261102-001301_iter01_train`

### Iteration 2: accepted (iter02)

- Proposed by: rules
- Why: The system never abstains, so all 30 unanswerable train queries get an answer. Enable the confidence gate with a threshold calibrated on train.
- Changes: {"abstention.enabled": true}
- Gate calibrated on train: no score threshold helps; abstains only when routing finds no matching contract (simulated utility 0.3688, FAR 0.0%, CAR 23.3%)
- Δ utility on train halves: {"fold0": 0.0341, "fold1": 0.0488}
- Run: `experiments\runs\20261102-001302_iter02_train`

### Iteration 3: accepted (iter03)

- Proposed by: rules
- Why: 39% have a relevant passage ranked below the cut-off and 42% land in the wrong section: a cross-encoder can reorder candidates.
- Changes: {"rerank.enabled": true}
- Gate calibrated on train: rerank >= -6.1072 (simulated utility 0.6347, FAR 10.0%, CAR 76.7%)
- Δ utility on train halves: {"fold0": 0.3335, "fold1": 0.1934}
- Run: `experiments\runs\20261102-001648_iter03_train`

### Iteration 4: accepted (iter04)

- Proposed by: rules
- Why: 4% have no relevant passage among all candidates: add embedding-based retrieval to catch paraphrased clauses.
- Changes: {"retrieval.method": "hybrid"}
- Gate calibrated on train: rerank >= -6.1072 (simulated utility 0.6564, FAR 9.3%, CAR 73.3%)
- Δ utility on train halves: {"fold0": 0.0094, "fold1": 0.0348}
- Run: `experiments\runs\20261102-002029_iter04_train`

### Iteration 5: rejected (iter05)

- Proposed by: rules
- Why: 14% hit the right contract but the wrong section: add clause-type synonyms so keyword search matches differently worded clauses.
- Changes: {"query.expand_categories": true}
- Gate calibrated on train: rerank >= -6.1072 (simulated utility 0.6613, FAR 9.3%, CAR 73.3%)
- Rejected because: utility gain +0.0049 is below 0.005
- Δ utility on train halves: {"fold0": 0.0098, "fold1": -0.0002}
- Run: `experiments\runs\20261102-002049_iter05_train`

### Iteration 6: rejected (iter06)

- Proposed by: rules
- Why: Word-form mismatches (assign/assignment, terminate/termination) cost keyword matches.
- Changes: {"retrieval.bm25.stem": true, "retrieval.bm25.stopwords": true}
- Gate calibrated on train: rerank >= -6.1072 (simulated utility 0.6592, FAR 9.3%, CAR 73.3%)
- Rejected because: utility gain +0.0028 is below 0.005; wins in only 62% of bootstrap resamples; worse on one half of train ({"fold0": -0.0057, "fold1": 0.012})
- Δ utility on train halves: {"fold0": -0.0057, "fold1": 0.012}
- Run: `experiments\runs\20261102-002121_iter06_train`

### Iteration 7: rejected (iter07)

- Proposed by: claude
- Why: 18.6 percent of benchmark questions have a relevant passage ranked below 8, and wrong-section cases rank passages from other clauses first (q035, q061). Fixed 500-character chunks start mid-clause, so the retrievers and reranker cannot see which section a chunk belongs to. Prepend the contract title and nearest clause heading to the indexed and reranked text; offsets unchanged.
- Changes: {"chunking.contextual_header": true}
- Gate calibrated on train: rerank >= -7.6516 (simulated utility 0.6559, FAR 5.7%, CAR 66.7%)
- Rejected because: utility gain -0.0005 is below 0.005; wins in only 51% of bootstrap resamples; worse on one half of train ({"fold0": -0.0023, "fold1": 0.0014}); guardrail: correct abstention 73.3% -> 66.7%
- Δ utility on train halves: {"fold0": -0.0023, "fold1": 0.0014}
- Run: `experiments\runs\20261102-003718_iter07_train`

### Iteration 8: rejected (iter08)

- Proposed by: rules
- Why: 28% only partly cover the answer: cut chunks at clause boundaries.
- Changes: {"chunking.strategy": "clause", "chunking.chunk_size": 600}
- Gate calibrated on train: rerank >= -6.8202 (simulated utility 0.7071, FAR 5.0%, CAR 66.7%)
- Rejected because: guardrail: correct abstention 73.3% -> 66.7%
- Δ utility on train halves: {"fold0": 0.0682, "fold1": 0.032}
- Run: `experiments\runs\20261102-004250_iter08_train`

### Iteration 9: rejected (iter09)

- Proposed by: rules
- Why: 28% only partly cover the answer: try larger chunks.
- Changes: {"chunking.chunk_size": 750}
- Gate calibrated on train: rerank >= -8.4929 (simulated utility 0.6856, FAR 2.9%, CAR 43.3%)
- Rejected because: wins in only 84% of bootstrap resamples; worse on one half of train ({"fold0": -0.0033, "fold1": 0.0643}); guardrail: precision@8 0.0693 -> 0.0565; guardrail: correct abstention 73.3% -> 43.3%
- Δ utility on train halves: {"fold0": -0.0033, "fold1": 0.0643}
- Run: `experiments\runs\20261102-004721_iter09_train`

### Iteration 10: rejected (iter10)

- Proposed by: rules
- Why: Character precision is low because whole chunks are returned: trim each passage to its best-matching sentences.
- Changes: {"postprocess.trim_spans": true}
- Gate calibrated on train: rerank >= -6.1072 (simulated utility 0.5858, FAR 9.3%, CAR 73.3%)
- Rejected because: utility gain -0.0705 is below 0.005; wins in only 0% of bootstrap resamples; worse on one half of train ({"fold0": -0.0692, "fold1": -0.0719})
- Δ utility on train halves: {"fold0": -0.0692, "fold1": -0.0719}
- Run: `experiments\runs\20261102-004732_iter10_train`

### Iteration 11: accepted (iter11)

- Proposed by: claude
- Why: Iteration 8 raised utility by 0.051 (P(win) 99 percent) but was rejected only on the correct-abstention guardrail, because threshold calibration ignored that guardrail. Calibration now picks the best threshold that satisfies every threshold-dependent guardrail; re-evaluate the same change.
- Changes: {"chunking.strategy": "clause", "chunking.chunk_size": 600}
- Gate calibrated on train: rerank >= -5.7731 (simulated utility 0.7071, FAR 7.9%, CAR 70.0%)
- Threshold chosen within guardrails (CAR >= 68.3%, P@8 >= 0.0624, FAR <= 10%): met
- Δ utility on train halves: {"fold0": 0.0682, "fold1": 0.032}
- Run: `experiments\runs\20261102-005611_iter11_train`

### Iteration 12: rejected (iter12)

- Proposed by: rules
- Why: 14% hit the right contract but the wrong section: add clause-type synonyms so keyword search matches differently worded clauses.
- Changes: {"query.expand_categories": true}
- Gate calibrated on train: rerank >= -6.8202 (simulated utility 0.7023, FAR 5.0%, CAR 66.7%)
- Threshold chosen within guardrails (CAR >= 65.0%, P@8 >= 0.0809, FAR <= 10%): met
- Rejected because: utility gain -0.0048 is below 0.005; wins in only 29% of bootstrap resamples; worse on one half of train ({"fold0": -0.0093, "fold1": 0.0})
- Δ utility on train halves: {"fold0": -0.0093, "fold1": 0.0}
- Run: `experiments\runs\20261102-005721_iter12_train`

### Iteration 13: rejected (iter13)

- Proposed by: rules
- Why: Word-form mismatches (assign/assignment, terminate/termination) cost keyword matches.
- Changes: {"retrieval.bm25.stem": true, "retrieval.bm25.stopwords": true}
- Gate calibrated on train: rerank >= -6.7664 (simulated utility 0.7087, FAR 5.0%, CAR 70.0%)
- Threshold chosen within guardrails (CAR >= 65.0%, P@8 >= 0.0809, FAR <= 10%): met
- Rejected because: utility gain +0.0016 is below 0.005; wins in only 57% of bootstrap resamples
- Δ utility on train halves: {"fold0": 0.002, "fold1": 0.0011}
- Run: `experiments\runs\20261102-005805_iter13_train`
