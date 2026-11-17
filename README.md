# Contract clause search

This project answers questions about contracts by pointing to the exact passage that answers them. You ask about one of the contracts, for example whether a service agreement stops one side from hiring away the other's employees, and the system shows the passages from that contract most likely to contain the answer, each with the file name and the exact character positions where it starts and ends. If it cannot find a convincing answer, it says so plainly instead of guessing.

It was built and tested on 194 real contract questions from a public legal benchmark (the CUAD part of LegalBench-RAG-mini), covering 29 commercial contracts, plus 45 extra questions I wrote that have no answer in those contracts. You can use it through a small web page or from the command line. The design was chosen step by step by an improvement loop that tried changes, measured them, and kept only the ones that helped.

How well it works, and how I know: [REPORT.md](REPORT.md). Every experiment, kept or rejected: [experiments/LOG.md](experiments/LOG.md).

## Setup

You need Python 3.10 or newer. I developed and tested it on Windows with Python 3.12.5. The tests and the starting version were also run on Linux. No API keys and no paid services are needed.

**1. Create a virtual environment and install the libraries**

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

On macOS or Linux, activate with `source .venv/bin/activate` instead. On Linux, install the smaller CPU-only version of PyTorch first, otherwise pip downloads several gigabytes of graphics-card libraries you do not need:

```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

**2. Download the data and prepare it**

```bat
python scripts/download_data.py
python -m clausesearch.prepare
```

The first command downloads the benchmark questions and the contract files from the dataset's public Hugging Face page into `data/raw/`. The second picks out the 194 questions used here, splits them into training and test questions, checks that every expected answer really appears at the stated position in its contract (it stops if even one does not), and writes the list of the 29 contracts to search.

**3. Models**

Two small open models are downloaded automatically the first time they are needed (about 220 MB in total) and then run on your own computer:

- `BAAI/bge-small-en-v1.5` turns text into numbers that capture meaning, so passages can be found even when they use different words from the question.
- `cross-encoder/ms-marco-MiniLM-L-6-v2` reads the question and each candidate passage together and scores how well they match.

No contract text is sent anywhere.

**Windows notes.** You may see a warning about "symlinks" while models download; it is harmless (`set HF_HUB_DISABLE_SYMLINKS_WARNING=1` hides it). The first time Streamlit starts it asks for an email address; just press Enter. Before saving report output to a file with `>`, run `set PYTHONUTF8=1`, otherwise special characters in contract text can cause an error.

## How to run

**Web app**

```bat
streamlit run app.py
```

This opens a page at http://localhost:8501. Type a question, or pick an example from the list, and press Search. The first search takes 20 to 30 seconds while the models load; later searches take a second or two. Each result shows the passage highlighted inside the surrounding contract text, with its file name and character positions. The sidebar lets you switch between the baseline and final settings and choose how many passages to show.

**Command line**

```bat
python -m clausesearch.cli "Consider the Service Agreement between Theravance Biopharma UK Limited and Brett Haumann; Is there a clause preventing the solicitation of employees in this contract?"
python -m clausesearch.cli --interactive
python -m clausesearch.cli "<question>" --json -k 5
```

Questions work best in the benchmark's format: "Consider the <agreement> between <party A> and <party B>; <question>". The command line uses the final settings (`configs/final.yaml`) unless you pass `--config`. `--interactive` keeps asking for questions until you type `quit`; `--json` prints machine-readable output; `-k` sets how many passages to show.

**Evaluation**

```bat
python -m clausesearch.evaluate --config configs/final.yaml --split train
python -m clausesearch.evaluate --config configs/final.yaml --split train --set rerank.top_n=30
```

This runs every training question through the system and scores the results. Each run is saved in its own folder under `experiments/runs/` with the exact settings used, the scores, and the result for every question. `--set` changes one setting for a single run without editing any file.

The test questions are kept for final reporting only, so the program refuses to run them unless you add `--confirm-test`. Every test run is recorded in `experiments/test_runs.jsonl`:

```bat
python -m clausesearch.evaluate --config configs/final.yaml --split test --confirm-test
```

**Improvement loop**

```bat
python -m clausesearch.loop --iterations 3
python -m clausesearch.loop --dry-run
python -m clausesearch.loop --propose rerank.top_n=30 --proposer human --rationale "why I want to try this"
python -m clausesearch.loop --finalize
```

Each iteration scores the current settings on the training questions, works out what is going wrong, tries one change, and keeps it only if it clearly helps. `--dry-run` shows the diagnosis and the queue of planned changes without running anything. `--propose` tries a change you choose. `--finalize` copies the best settings so far to `configs/final.yaml`. The loop continues the history saved in `experiments/`; to experiment without touching it, add `--out some_other_folder --configs-dir some_other_configs`.

**Report tables and failure examples**

```bat
python -m clausesearch.report compare RUN_FOLDER [RUN_FOLDER ...]
python -m clausesearch.report errors RUN_FOLDER
```

`compare` prints side-by-side tables for any saved runs, with the number of questions behind every figure and a likely range for each. `errors` lists concrete failures, showing the expected answer next to what the system returned.

**Tests**

```bat
pytest -q
```

The 50 tests run in a few seconds without downloading anything. They use three small made-up contracts and lightweight stand-ins for the two models.

## Architecture

The work happens in two stages.

**Once, before any questions.** Each contract is cut into passages of up to 600 characters, following the contract's own clause headings where possible ("4.2", "Section 7", "ARTICLE III", headings in capitals). Every passage remembers exactly where it starts and ends in the original file, so anything the system returns can be checked against the source. Two search indexes are built over these passages: a keyword index and a meaning-based index.

**For every question:**

1. **Split the question.** "Consider the Distribution Agreement between Acme and Beta; is consent needed to assign it?" becomes the contract description ("Distribution Agreement between Acme and Beta") and the actual question.
2. **Find the contract.** The description is compared with the name and opening text of every contract, where the parties are introduced. Rare words such as company names count much more than common ones such as "agreement". The search is then limited to the best match. If no contract matches well enough, the system says the contract is not in its collection.
3. **Collect candidates.** Inside that contract, passages are ranked twice: by shared keywords (an algorithm called BM25) and by similarity of meaning (the embedding model). The two rankings are merged into one list of 64 candidates.
4. **Re-rank.** The top 50 candidates are scored again by the second model, which reads the question and each passage side by side. This is slower but much more accurate.
5. **Answer or decline.** If even the best passage scores below a threshold set using the training questions, the system says it found nothing. Otherwise it returns the top passages with their file names and positions.

One function, `Pipeline.search()` in `clausesearch/pipeline.py`, does all of this. The web app, the command line and the evaluation all call that same function, so what is measured is exactly what users see.

```
question ──► split question ──► find contract ──► collect 64 candidates ──► re-rank top 50 ──► answer or decline
             (query.py)         (routing.py)      (bm25.py + dense.py)      (rerank.py)        (pipeline.py)
```

| Part | File(s) | What it does |
|---|---|---|
| Settings | `clausesearch/config.py`, `configs/` | Every choice in the pipeline is a setting, so the improvement loop can change behaviour without code changes |
| Data | `clausesearch/data.py`, `clausesearch/prepare.py` | Loads the benchmark, selects the 194 questions, splits them, checks every answer position |
| Passages | `clausesearch/chunking.py`, `clausesearch/text.py` | Cuts contracts into passages with exact positions; splits text into words |
| Search | `clausesearch/bm25.py`, `clausesearch/dense.py`, `clausesearch/rerank.py` | Keyword search, meaning-based search, and re-ranking (results are cached on disk so repeated runs are fast) |
| Contract matching | `clausesearch/routing.py`, `clausesearch/query.py` | Finds the contract named in a question; prepares the question text |
| The system | `clausesearch/pipeline.py` | Runs the steps above for one question |
| Scoring | `clausesearch/metrics.py`, `clausesearch/evaluate.py` | Character-level scores, refusal rates, and a label for each failure |
| Improving | `clausesearch/calibrate.py`, `clausesearch/loop.py` | Sets the "no answer" threshold; runs the improvement loop |
| Reporting | `clausesearch/report.py` | Results tables with likely ranges; failure examples |
| Unanswerable questions | `scripts/build_unanswerable.py`, `data/unanswerable.jsonl` | How the 45 extra questions were made (run once, then frozen) |
| Interfaces | `app.py`, `clausesearch/cli.py` | Web app and command line |

**Where settings live.** `configs/baseline.yaml` is the simple starting point and `configs/final.yaml` is the final system. `configs/iterations/` holds the exact settings of every loop iteration, and `configs/objective.yaml` holds the target and the rules for keeping a change. Anything a settings file leaves out takes its default value from `clausesearch/config.py`.

**Where outputs live.** `experiments/` holds every evaluation run, the experiment log and the record of test runs. Downloaded data (`data/raw/`), prepared data (`data/processed/`) and model caches (`cache/`) are not stored in the repository; the commands above recreate them.

## Reproducing results

After Setup, these commands produce every number in the report. Times are rough estimates from my own runs on a laptop CPU with no graphics card.

| Step | Command | Time |
|---|---|---|
| Prepare data | `python -m clausesearch.prepare` | under a minute |
| Tests | `pytest -q` | seconds |
| Baseline, training questions | `python -m clausesearch.evaluate --config configs/baseline.yaml --split train` | seconds |
| Final, training questions | `python -m clausesearch.evaluate --config configs/final.yaml --split train` | about 7 to 10 minutes the first time (it scores every passage); seconds afterwards |
| Baseline, test questions | `python -m clausesearch.evaluate --config configs/baseline.yaml --split test --confirm-test` | seconds |
| Final, test questions | `python -m clausesearch.evaluate --config configs/final.yaml --split test --confirm-test` | about 2 to 3 minutes |
| Results tables | `python -m clausesearch.report compare <the four new folders in experiments/runs/>` | seconds |

Every loop iteration can also be re-scored from its saved settings, which include its own "no answer" threshold. For example:

```bat
python -m clausesearch.evaluate --config configs/iterations/iter11.yaml --split train
```

Search results are cached in `cache/`. Delete that folder if you want to time a run from scratch.

## Assumptions

Where the brief left something open, this is what I assumed and why.

- **Selecting the 194 questions and splitting them.** I implemented the selection and the train/test split in `clausesearch/data.py` so that they behave exactly like the functions given in the brief, writing them myself instead of copying them, because the brief must not be copied into the repository. Tests check that they behave as intended, and the counts match: 194 questions, 140 for training and 54 for testing.
- **Which contracts to search.** Only the 29 contracts that the 194 questions are about.
- **How answers are scored.** I follow the LegalBench-RAG paper and score by characters: how much of the expected answer text was returned, and how much of what was returned was the answer. If two returned passages overlap, the shared text is counted once. When a question has several expected snippets (52 of the 194 do), they are scored together.
- **Refusals in the scores.** When the system wrongly refuses a question that has an answer, that question scores zero. I also report a second view that ignores refusals, to show search quality on its own.
- **Main target and limits.** The main score and the limits a change must respect were written down in `configs/objective.yaml` before the improvement loop started, and never changed.
- **The 45 unanswerable questions.** These are of three kinds: a clause that the named contract does not contain; a contract that is not in the collection; and a fact that contracts do not record, such as a company's credit rating. They are written in the same format as the benchmark questions, so the system cannot spot them by their wording. Each label was checked by searching the contract's text. The set was committed before the improvement loop began (commit "Freeze unanswerable query set (45 queries)") and has not been edited since.
- **The expected answers are never used by the system.** They are used only for scoring, and to label the unanswerable questions when building them.
- **"Contract not in the collection".** When the contract named in a question matches no contract well enough (a match score below 0.5), the system says it does not have that contract instead of searching a different one.

## AI tool usage

I used Claude (Anthropic's assistant, through claude.ai) throughout this project:

- **Planning and learning.** Claude helped me plan the approach and explained the retrieval methods and scoring used here, since this is the first search system of this kind I have built.
- **Code and tests.** Claude wrote most of the code and tests. I ran everything on my own machine, reviewed the code, and made sure I can explain and change each part.
- **Unanswerable questions.** Claude drafted `scripts/build_unanswerable.py`. I reviewed all 45 questions before freezing them.
- **Improvement loop.** Two iterations (7 and 11, marked "claude" in the log) were suggested by Claude after I shared the loop's failure summary. They went through exactly the same accept-or-reject rule as every other change. After iteration 8, Claude noticed that threshold tuning ignored two of the limits; that fix is a separate commit.
- **Bug fixes.** Claude fixed two Windows-only problems in the web app that I found while testing the demo.
- **Documents.** Claude drafted this README and REPORT.md from my results; I reviewed and edited them.
