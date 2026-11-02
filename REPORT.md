# Evaluation report: contract clause search

## Summary

I built a search system that finds the clause in a contract that answers a question, and says "not found" when it cannot find one. For each question it works out which contract is meant, gathers likely passages from that contract using both keyword search and meaning-based search, re-scores the best 50 with a model that reads the question and each passage side by side, and declines to answer if even the best passage is not convincing. On the 54 test questions, the first 8 passages it returns contain on average 70% of the expected answer text (recall@8 of 0.703), against 8% for the simple starting version (0.080). It correctly said "not found" for 12 of the 15 test questions that have no answer (80%) and wrongly said it for 2 of the 54 that do (3.7%). I ran the test questions only twice: once with the starting version and once with the final one. Its main weaknesses are speed (an average search takes 2.3 seconds on a laptop, and the slowest 5% take over 3.4 seconds, above the 3-second limit I set) and questions about clauses a contract simply does not contain, where it still gives an answer about half the time.

## How to read the numbers

| Term | Meaning |
|---|---|
| Passage | A piece of a contract of up to 600 characters, roughly a short paragraph |
| Recall@8 | Of the text that makes up the correct answer, how much appears somewhere in the first 8 passages shown (1.0 = all of it) |
| Precision@8 | Of all the text in those 8 passages, how much is the answer itself. Naturally low, because 8 passages hold much more text than one clause |
| Recall@1, precision@1 | The same, for the first passage only |
| Correct abstention | Of the questions with no answer, how often the system rightly says "not found" |
| False abstention | Of the questions that do have an answer, how often the system wrongly says "not found" |
| MRR | How high the first useful passage appears, on average (1.0 = always first, 0.5 = typically second) |
| utility@8 | The single score the improvement loop tried to raise: recall@8 for a question with an answer (0 if wrongly refused), and 1 or 0 for a question without one, depending on whether the system rightly refused |
| 95% range | With this few questions every score is uncertain; the range shows where the true value probably lies |
| Train / test questions | 140 questions used for all development, and 54 kept aside until the end to check the system on questions it was never tuned on |

## System design

### How it works

1. **Split the question.** Benchmark questions name their contract: "Consider the Promotion Agreement between Depomed and King Pharmaceuticals; is there a non-compete clause?" The first part says which contract; the second is the actual question.
2. **Find the contract.** The contract description is compared with the file name and opening text of every contract, where the parties are introduced. Rare words such as company names count far more than common ones like "agreement". The search is then limited to the best-matching contract. If nothing matches well enough, the system says that contract is not in its collection.
3. **Gather candidates.** Inside that contract, passages are ranked by shared keywords (an algorithm called BM25) and by similarity of meaning (a small embedding model). The two rankings are merged into one list of 64 candidates.
4. **Re-rank.** A second model reads the question together with each of the top 50 candidates and scores how well they match. It is slower but much more accurate than the first step.
5. **Answer or decline.** If the best score is below a threshold chosen using the training questions, the system says it found nothing. Otherwise it returns the top passages with their exact positions.

### Key decisions

| Decision | What I chose | What else I tried | What the evidence showed (training questions) |
|---|---|---|---|
| Finding the right contract | Match the named contract first, then search only inside it | Search all 29 contracts at once (starting version) | Without this, the top passage came from a contract's first 1,500 characters, where the parties are named, for 129 of 140 questions. Matching picks the right contract for all 140, and recall@8 rose from 0.08 to 0.40 |
| Cutting contracts into passages | Follow the contract's own clause headings, up to 600 characters | Fixed 500-character pieces (start); fixed 750-character pieces; adding the contract title and heading to each piece | Clause-based pieces gave the biggest late gain (+0.051 utility, precision@8 from 0.069 to 0.090). Bigger fixed pieces found more answer text but hurt precision by 18% and made "not found" much less reliable |
| Gathering candidates | Keywords plus meaning, merged | Keywords only; adding synonyms of clause types to the query; reducing words to their stems | Combining both helped a little (+0.022). Synonyms and stemming never helped once the re-ranker was in place, and were rejected twice each |
| Re-ranking | A small cross-encoder (`ms-marco-MiniLM-L-6-v2`) on the top 50 | No re-ranking; a larger re-ranker (planned last, never reached, as it is slow on a CPU) | The largest single gain: recall@8 from 0.40 to 0.61. Its score is also the best signal for "not found" |
| Saying "not found" | Two checks: no matching contract, or best re-ranker score below a threshold set on training questions | Never refusing (start); a threshold on the keyword score | Correct abstention went from 0% to 23% with the contract check alone, and to 77% with the re-ranker score |
| Length of returned passages | Whole passages | Trimming each passage to its best-matching sentences | Trimming made results more precise (+15%) but cut off parts of answers (recall −0.09); rejected |
| Building blocks | My own code, with standard libraries (scipy, sentence-transformers) | LangChain or LlamaIndex | Every step stays visible and easy to explain, and exact character positions are kept throughout |

### Messy contracts

- **Contracts not in the collection** are handled well. The contract-matching check caught every such question: 7 of 7 in training and 6 of 6 in test.
- **Inconsistent formatting** is handled partly. Passages follow numbered clauses, "Section" and "Article" headings and headings in capitals, and fall back to paragraph and sentence breaks when no heading is found.
- **Cross-references and definitions** ("as defined in Section 4.2") are not handled. When the meaning of a clause depends on a definition elsewhere, the system can miss it; the error analysis shows an example.
- **Questions that do not name a contract** are searched across all contracts, but this case was not evaluated, because every benchmark question names its contract.

## LLM use

**In the improvement loop: yes, in a limited way.** Two of the thirteen iterations (7 and 11) were suggested by Claude (Anthropic's assistant, through claude.ai). I shared the loop's failure summary with it, and its suggestion went through exactly the same accept-or-reject rule as every other change. Iteration 7 (adding titles and headings to passages) was rejected. Iteration 11 was accepted: Claude noticed that iteration 8, the best idea so far, had been rejected because of a flaw in how the threshold was tuned. The suggestions are written in the experiment log, so the results can be reproduced without calling any model, and there is no cost per search. What I shared was the questions, file names and character positions, not contract text. With real JioStar agreements, failure summaries that include clause text would need to be redacted first, or handled by a model running in-house.

**In the search itself: no.** The re-ranking model already does the job of reading each passage against the question, and it runs on my own machine. A hosted model would send confidential contract text to an outside company. A local model on a laptop would add several seconds per search, when searches already take 2.3 seconds on average. I also chose to spend the limited time on the core requirements. If I add one later, the most useful place is a final check of whether the top passages really answer the question. That is where the system is weakest: questions about clauses that do not exist. Its outputs would be cached, and it would be kept only if the loop's rule accepts it.

## Evaluation setup

- **Questions with answers.** The 194 CUAD questions of LegalBench-RAG-mini, about 29 contracts (1.2 million characters in total). The fixed split gives 140 training and 54 test questions. 52 questions have their answer in more than one place (272 answer snippets in all). Before building anything, I checked that every expected answer appears at its stated position in its contract.
- **Questions with no answer.** I wrote 45, split the same way into 30 training and 15 test questions, in three kinds:
  - a clause the named contract does not contain (20: 13 train, 7 test);
  - a real CUAD contract that is not in the collection (13: 7 train, 6 test);
  - a fact contracts do not record, such as a party's credit rating (12: 10 train, 2 test).

  All use the benchmark's own question format, so the system cannot spot them by their wording. They were generated by a script with a fixed seed. For the first and third kinds, each label was checked by searching the named contract for every word that would suggest the clause or fact is there. The full set was committed before the improvement loop started (commit "Freeze unanswerable query set (45 queries)") and never edited.
- **Scoring answers.** Character-level precision and recall, as defined in the LegalBench-RAG paper, after showing the first 1, 2, 4, 8, 16, 32 and 64 passages, averaged over questions. Overlapping passages are counted once. I report two views: "end-to-end", where a wrongly refused question scores 0, and "forced", which ignores refusals and shows search quality alone. I also report MRR.
- **Scoring refusals.** Correct abstention (on questions with no answer) and false abstention (on questions with one).
- **Uncertainty.** Each 95% range comes from re-sampling the questions 2,000 times.
- **Use of the test questions.** All development and every loop iteration used only the training questions. The test questions were run twice: once for the starting version and once for the final version, both recorded in `experiments/test_runs.jsonl`. Nothing in the system changed afterwards. The two later fixes concerned only the web app on Windows and wording, and they do not affect any result.

## Results

**Precision (P) and recall (R) on questions that have answers**, end-to-end, for different numbers of passages shown:

| Version | Questions | n | P@1 | R@1 | P@2 | R@2 | P@4 | R@4 | P@8 | R@8 | P@16 | R@16 | P@32 | R@32 | P@64 | R@64 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| starting | train | 140 | 0.000 | 0.000 | 0.000 | 0.000 | 0.003 | 0.013 | 0.009 | 0.080 | 0.011 | 0.163 | 0.009 | 0.253 | 0.007 | 0.392 |
| final | train | 140 | 0.400 | 0.431 | 0.253 | 0.522 | 0.161 | 0.645 | 0.090 | 0.709 | 0.051 | 0.764 | 0.030 | 0.818 | 0.020 | 0.874 |
| starting | test | 54 | 0.000 | 0.000 | 0.000 | 0.000 | 0.005 | 0.045 | 0.009 | 0.080 | 0.012 | 0.178 | 0.008 | 0.221 | 0.007 | 0.332 |
| final | test | 54 | 0.309 | 0.362 | 0.220 | 0.521 | 0.136 | 0.588 | 0.093 | 0.703 | 0.054 | 0.763 | 0.029 | 0.803 | 0.017 | 0.854 |

**Refusals and overall score**, with 95% ranges:

| Version | Questions | utility@8 (n) | R@8 | P@8 | Correct abstention (n) | False abstention (n) | MRR |
|---|---|---|---|---|---|---|---|
| starting | train | 0.066 [0.036–0.100] (170) | 0.080 [0.043–0.121] | 0.009 | 0% (30) | 0% (140) | 0.052 |
| final | train | 0.707 [0.638–0.768] (170) | 0.709 [0.638–0.780] | 0.090 [0.077–0.104] | 70.0% [53–87] (30) | 7.9% [4–13] (140) | 0.633 |
| starting | test | 0.063 [0.016–0.115] (69) | 0.080 [0.025–0.149] | 0.009 | 0% (15) | 0% (54) | 0.053 |
| final | test | 0.724 [0.629–0.819] (69) | 0.703 [0.589–0.814] | 0.093 [0.067–0.124] | 80.0% [60–100] (15) | 3.7% [0–9] (54) | 0.575 |

**Correct abstention by kind of unanswerable question** (final version):

| Questions | Clause not in the contract | Contract not in the collection | Fact contracts do not record |
|---|---|---|---|
| train | 46% (6 of 13) | 100% (7 of 7) | 80% (8 of 10) |
| test | 71% (5 of 7) | 100% (6 of 6) | 50% (1 of 2) |

What these numbers say:

- **The final system is a large improvement.** In the first 8 passages it finds about 70% of the answer text, against 8% at the start. On test, the first passage alone holds about a third answer text (P@1 0.31), and the first useful passage is usually first or second (MRR 0.58).
- **Precision looks low, but that is expected.** An answer is usually a sentence or two inside a 600-character passage, and P@8 counts all 8 passages. Even a perfect first result leaves the other 7 counting against precision. P@1 is the fairer measure of how clean the results are.
- **Refusing costs little.** The system wrongly refused 11 of 140 training questions, but those were mostly questions it was getting wrong anyway: recall@8 is 0.723 if refusals are ignored and 0.709 with them. On test, the two wrong refusals made no visible difference (0.703 either way).
- **Contracts not in the collection are always caught. Missing clauses are the hard case.** When the contract exists but the clause does not, some neighbouring clause often looks partly relevant (see the error analysis).
- **Speed is over my own limit.** On the final test run, an average search took 2.3 seconds and the slowest 5% took more than 3.4 seconds, above the 3-second limit I set. The loop should have caught this, but it measured speed on runs that reused re-ranker scores saved moments earlier by the same iteration, so the re-ranker's cost never showed up (the training run's 60 ms is misleading for that reason). I did not change the system after seeing the test results. The fixes are listed under next steps.

## Iteration history

### Target and limits

I wrote these down in `configs/objective.yaml` before the first iteration, and did not change them.

| | What | Rule |
|---|---|---|
| Main score | utility@8 on all 170 training questions | raise it |
| Limit | Precision@8 | may not fall by more than 10% of its current value |
| Limit | False abstention | at most 10% |
| Limit | Correct abstention | may not fall by more than 5 points |
| Limit | Slowest 5% of searches | at most 3 seconds |
| Keeping a change | Improvement in the main score | at least 0.005, holding in at least 90% of 2,000 re-samples of the questions, and not worse (by more than 0.002) on either fixed half of the training questions |

Why these choices:

- **One main score.** It rewards finding the clause and rewards saying "not found" only when that is right, so the loop can't improve one by quietly breaking the other.
- **8 passages,** because that is about as much as a person reviewing results will read.
- **Built around recall.** For a legal user, a missed clause costs more than reading one extra passage.
- **Precision and both refusal rates as limits,** so recall cannot be bought with junk results or careless refusals.
- **The re-sampling and two-halves checks** because with about 170 questions, a one-point change can easily be luck.

### How the loop works

One command, `python -m clausesearch.loop`, does the following each iteration:

1. Scores the current settings on the training questions.
2. Sorts every failure into a category: wrong contract, right contract but wrong part, answer just outside the results, answer only partly covered, wrongly refused, or wrongly answered. It writes a summary to `experiments/latest_diagnosis.md`.
3. Picks the next change. Rules aimed at the biggest failure categories come first, then a short list of settings to try. A person or an LLM can also suggest a change.
4. Re-tunes the "not found" threshold for that change, using only training questions, staying within the limits.
5. Keeps or rejects the change using the rule above.
6. Writes the result to `experiments/LOG.md`.

It never loads the test questions, and the expected answers are used only for scoring, never as input to the system.

### What was tried

All on training questions (140 with answers, 30 without). The change in score is measured against the settings in use at the time. More detail is in `experiments/LOG.md`.

| # | Change | Suggested by | utility@8 | Change in score | R@8 | P@8 | False abst. | Correct abst. | Holds in | Decision |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | Starting version: fixed 500-character pieces, keyword search, never refuses | — | 0.066 | — | 0.080 | 0.009 | 0.0% | 0.0% | — | start |
| 1 | Find the named contract first; search with the question only | rules | 0.328 | +0.2615 | 0.398 | 0.046 | 0.0% | 0.0% | 100% | kept |
| 2 | Turn on "not found" | rules | 0.369 | +0.0412 | 0.398 | 0.046 | 0.0% | 23.3% | 100% | kept |
| 3 | Re-ranking model | rules | 0.635 | +0.2659 | 0.606 | 0.063 | 10.0% | 76.7% | 100% | kept |
| 4 | Keyword plus meaning-based search | rules | 0.656 | +0.0216 | 0.640 | 0.069 | 9.3% | 73.3% | 90% | kept |
| 5 | Add clause-type synonyms to the query | rules | 0.661 | +0.0049 | 0.646 | 0.070 | 9.3% | 73.3% | 92% | rejected |
| 6 | Reduce words to their stems; drop common words | rules | 0.659 | +0.0028 | 0.643 | 0.070 | 9.3% | 73.3% | 62% | rejected |
| 7 | Add the contract title and heading to each passage | Claude | 0.656 | −0.0005 | 0.654 | 0.074 | 5.7% | 66.7% | 51% | rejected |
| 8 | Passages that follow clause headings, up to 600 characters | rules | 0.707 | +0.0508 | 0.716 | 0.090 | 5.0% | 66.7% | 99% | rejected |
| 9 | Fixed 750-character pieces | rules | 0.686 | +0.0293 | 0.740 | 0.057 | 2.9% | 43.3% | 84% | rejected |
| 10 | Trim passages to their best sentences | rules | 0.586 | −0.0705 | 0.554 | 0.079 | 9.3% | 73.3% | 0% | rejected |
| 11 | Same as 8, after fixing threshold tuning | Claude | 0.707 | +0.0508 | 0.709 | 0.090 | 7.9% | 70.0% | 100% | **kept (final)** |
| 12 | Clause-type synonyms again, on the new settings | rules | 0.702 | −0.0048 | 0.710 | 0.089 | 5.0% | 66.7% | 29% | rejected |
| 13 | Stems and common words again, on the new settings | rules | 0.709 | +0.0016 | 0.711 | 0.090 | 5.0% | 70.0% | 57% | rejected |

Thirteen iterations beyond the start: 5 kept, 8 rejected. Eleven were suggested by the loop's rules and two by Claude.

### What the iterations taught me

- **Iteration 1 was the turning point.** The starting version kept returning the opening paragraph of the right contract, because keyword search matched the company names in "Consider the X between A and B". Finding the contract first, then searching with only the question, fixed that.
- **Iterations 2 and 3 made "not found" work.** The contract check alone refused every question about a contract the system does not have. The re-ranker then gave the biggest single improvement in finding clauses, and a much better signal for refusing. But tuning pushed false abstention right up to the 10% limit, because refusing a question the system answers badly costs very little in the main score.
- **Iteration 4 was a small, borderline win.** Combining keyword and meaning-based search passed the 90% bar exactly.
- **Iterations 5, 6, 12 and 13 show that once a good re-ranker reorders the candidates, keyword tweaks stop mattering.** Each was tried twice, and each was rejected twice.
- **Iteration 7 traded one kind of refusal for another.** It found more answer text and made fewer wrong refusals, but more wrong answers on questions without one. Overall, no change.
- **Iterations 9 and 10 show the precision–recall trade-off.** Bigger pieces of text find more of the answer, but bring in more noise and blur the "not found" signal. Trimming does the reverse.
- **Iterations 8 and 11 were my most useful lesson.** Iteration 8 was the best idea so far (+0.051, holding in 99% of re-samples), yet it was rejected because correct abstention fell 6.7 points, beyond the 5-point limit. The cause was a flaw in the loop: when it tuned the "not found" threshold for a new idea, it respected the false-abstention limit but ignored the other two limits that also depend on the threshold. When two thresholds scored the same, it also picked the more lenient one. I fixed the tuning in a separate commit, without changing the target or the limits. The same idea was then accepted with a threshold inside every limit. Without that fix the loop would have thrown away its best result.

### Training versus test results

- **No sign of over-tuning at 8 passages.** Recall@8 is 0.709 on training and 0.703 on test, and precision@8 is 0.090 against 0.093. The 95% ranges overlap almost completely. The starting version scores the same on both, so the split itself is not lopsided.
- **The very top of the list is a little weaker on test.** Recall@1 falls from 0.43 to 0.36 and MRR from 0.63 to 0.58. With 54 test questions this may well be chance. It is also the direction you would expect, since the loop optimised for "the answer somewhere in the top 8", not "the answer first".
- **Refusals look better on test, but I would not read much into it.** There are only 15 unanswerable test questions, just 2 of them about facts contracts do not record, so one question moves the rate by almost 7 points. The fair conclusion is "no worse than on training". Also, the training range for false abstention (4% to 13%) crosses the 10% limit, so the threshold meets that limit on average, not with confidence.
- **What the test checks.** Every test question is about a contract that also appears in the training questions: 21 of the 29 contracts have questions in both. So the test measures new questions on familiar contracts, not unfamiliar contracts.
- **The results reproduce.** Re-running the final settings on the training questions gave exactly the same numbers as iteration 11, and the starting version gave exactly the same numbers on a second machine running Linux.

## Error analysis

These failures come from the final version, on both training and test questions. They are grouped by cause, and the character positions refer to the original contract files.

### 1. Shared words win over meaning

The re-ranker sometimes prefers a passage that repeats the question's words over the passage that actually answers it.

- **Depomed–King promotion agreement: "Is there a non-compete clause?"** (test). The top result is a sentence saying the parties *will discuss* non-compete obligations in some future agreement. It contains the exact words "non-compete", but it is not a restriction. The real clause (from character 28,888) says King "shall not promote, market or distribute any product containing metformin hydrochloride" during the term. It never uses the word "non-compete", and it was not even among the 64 candidates.
- **Same agreement: "Is there a covenant not to sue?"** (test). The top result literally contains "covenant not to sue", but in a list of licensing terms. The answer (from character 64,934) is King's promise not to do anything that would "impair the rights of Depomed" in its trademarks, which effectively is a promise not to challenge them. It appeared only at rank 30.
- **ISA–Rubicon strategic alliance: "Is there a covenant not to sue?"** (test). The top result is a warranties section that "represents, covenants and warrants". The one-line answer, "Rubicon shall not contest ownership by ISA of any of the foregoing", was at rank 11.
- **Dynamex transportation agreement, a question with no answer: "Are there any third-party beneficiaries?"** (training). The system answered with a confidentiality clause because it mentions "third Parties", instead of saying "not found".

*Diagnosis:* the re-ranker was trained on general web search, where repeating the question's words is a strong sign of relevance. In contracts, the same words often appear in passing in clauses about something else.

### 2. The answer uses different words from the question

- **Dynamex transportation agreement: "Does this contract include an exclusivity agreement?"** (test). The answer (characters 7,970 to 8,101) is "Dynamex agrees not to provide sameday delivery services for any other provider". That is exclusivity, but neither "exclusive" nor "exclusivity" appears. The top result was a nearby clause saying the opposite (that nothing prevents the parties from continuing their services).
- **Union Dental affiliate agreement: "What are the audit rights?"** (test). The answer requires each party to make "records, books, agreements, policies and procedures" available within ten days of a request. That is an audit right without the word "audit". The re-ranker found nothing convincing, so the system wrongly said "not found".
- **Premier Biomedical IP agreement: "Does this contract include any revenue or profit-sharing arrangements?"** (training). The answer is a 5% royalty (from character 11,296). The model does not treat "royalty" as revenue sharing, ranked the clause 19th, and the system wrongly said "not found".
- **Papa John's endorsement agreement: "Does this contract include any volume restrictions?"** (test). The answer is "at least eight (8) Service Days", up to four of them production days. The re-ranker found it only at rank 52, and the system said "not found".

*Diagnosis:* legal categories such as audit rights, exclusivity and revenue sharing are often expressed through what parties must or must not do, not by name. Both models match wording more than legal function. This is also the main cause of wrong refusals.

### 3. The answer is long or in several places

- **Dynamex transportation agreement: "What are the insurance requirements?"** (test). The answer is a single clause of about 1,100 characters (characters 19,106 to 20,201), almost twice the maximum passage length. It is split across passages, and only part of it made the top results (first part at rank 2).
- **ISA–Rubicon strategic alliance: "Is there uncapped liability?"** (test). The first passage returned starts exactly where the expected answer starts and covers all of that part. But this question's answer has more than one snippet, and the others were not found, so recall is incomplete.

*Diagnosis:* passages are capped at 600 characters to keep results focused, so long clauses get split. Answers spread across the contract need several separate hits.

### 4. The meaning sits in a definition

- **Flotek supply agreement: "Does this contract include any volume restrictions?"** (training). The restriction is a definition near the start of the contract (character 958): "'Maximum Quantity' means [***] pounds of Terpene Product per Year". The clauses that apply it use only the defined term "Maximum Quantity". The definition was ranked 26th, and the system said "not found".

*Diagnosis:* this is the cross-reference and definition problem described under System design. Linking defined terms to their definitions when building the index would address it.

### 5. A plausible neighbour is returned for a question with no answer

- **Holiday RV endorsement agreement: "What happens in the event of a change of control?"** (test; the contract has no such clause). The system returned the early-termination clause, which sounds related to "what happens if…" questions.
- **Jaguars–ARC sponsorship agreement: "Who founded each of the parties?"** (test; contracts do not record this). The system returned the signature block, which names the people who signed. It looks like an answer about people, but it is not the answer.
- **On2–Wildform support agreement: "Is there a non-disparagement clause?"** (training; there is none). The system returned "Exceptions to Non-Disclosure Obligations", a different legal term that sounds similar.

*Diagnosis:* these are the most dangerous errors, because the passages look plausible. They come from a single threshold applied to every kind of question, and some kinds of question score unrelated passages higher than others.

### 6. Questionable expected answers

- **BicycleTX service agreement: "Are there any exceptions to competitive restrictions?"** (training). The system's top result, "nothing in this paragraph 14 shall prevent you from having any dealings with any Prospective Customer… which is not competitive", is itself an exception to a restriction. The benchmark only accepts a different exception, about holding up to 3% of a listed company. Here the system is arguably right, but it is scored as wrong.
- **Same agreement: "Does this contract include any right of first refusal, right of first offer, or right of first negotiation?"** (training). The expected answer is a grant of share options. Few readers would call that a right of first refusal, so a miss here says more about the label than about the system.

*Diagnosis:* some expert labels are narrow or debatable. Scores on single questions should be read with that in mind.

**Overall pattern.** Most errors come from the same gap: the models match words, while legal questions are about what a clause *does*. This shows up as wrong passages ranked first (group 1), missed or wrongly refused answers (groups 2 and 4), and plausible but wrong answers to questions with no answer (group 5). Splitting long clauses (group 3) is a separate, smaller issue.

## Limitations and next steps

**What does not work well yet**

- Questions about clauses a contract does not contain: the system still answers about half of them in training (6 of 13 correctly refused).
- Speed: 2.3 seconds on average and over 3.4 seconds for the slowest 5% on a laptop, above my 3-second limit. The loop also measured speed in a way that hid this.
- Cross-references and definitions are not linked.
- The "not found" threshold was set using only 30 unanswerable questions (each one is worth 3.3 points), and the test set has only 15.
- The test covers new questions on familiar contracts only, and only questions that name their contract.

**Next steps**

- Measure speed inside the loop on a run that starts from an empty cache. Re-rank 30 candidates instead of 50, or use a faster version of the model, or a graphics card.
- When building the index, attach each defined term's definition and each referenced clause to the passages that use them.
- Add a final "does this passage really answer the question?" check, using a model that runs in-house, to reduce plausible wrong answers. Cache its outputs, and keep it only if the loop's rule accepts it.
- Write a larger and harder set of unanswerable questions. Test on contracts never seen during tuning.

**Before legal teams rely on it**

- Evaluate on real JioStar agreements, with questions and answers marked by in-house lawyers.
- Always show each passage in context with its location, and phrase "not found" as "the system did not find this", never as "the contract has no such clause".
- Keep everything on company systems, with models running in-house, and log questions and answers for audit.
- Have a person check anything a business decision depends on.
