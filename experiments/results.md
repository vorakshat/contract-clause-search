End-to-end character-level precision (P) and recall (R) on benchmark queries:

| run | split | n bench | P@1 | R@1 | P@2 | R@2 | P@4 | R@4 | P@8 | R@8 | P@16 | R@16 | P@32 | R@32 | P@64 | R@64 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline | train | 140 | 0.000 | 0.000 | 0.000 | 0.000 | 0.003 | 0.013 | 0.009 | 0.080 | 0.011 | 0.163 | 0.009 | 0.253 | 0.007 | 0.392 |
| final | train | 140 | 0.400 | 0.431 | 0.253 | 0.522 | 0.161 | 0.645 | 0.090 | 0.709 | 0.051 | 0.764 | 0.030 | 0.818 | 0.020 | 0.874 |
| baseline | test | 54 | 0.000 | 0.000 | 0.000 | 0.000 | 0.005 | 0.045 | 0.009 | 0.080 | 0.012 | 0.178 | 0.008 | 0.221 | 0.007 | 0.332 |
| final | test | 54 | 0.309 | 0.362 | 0.220 | 0.521 | 0.136 | 0.588 | 0.093 | 0.703 | 0.054 | 0.763 | 0.029 | 0.803 | 0.017 | 0.854 |

Abstention, utility and latency:

| run | split | utility@8 (n all) | correct abstention (n unanswerable) | false abstention (n bench) | forced R@8 | MRR | p95 ms |
|---|---|---|---|---|---|---|---|
| baseline | train | 0.066 (170) | 0.0% (30) | 0.0% (140) | 0.080 | 0.052 | 1 |
| final | train | 0.707 (170) | 70.0% (30) | 7.9% (140) | 0.723 | 0.633 | 60 |
| baseline | test | 0.063 (69) | 0.0% (15) | 0.0% (54) | 0.080 | 0.053 | 1 |
| final | test | 0.724 (69) | 80.0% (15) | 3.7% (54) | 0.703 | 0.575 | 3379 |

Means with 95% bootstrap intervals (2,000 resamples of each run's queries):

| run | split | utility@8 | R@8 e2e | P@8 e2e | correct abstention | false abstention |
|---|---|---|---|---|---|---|
| baseline | train | 0.066 [0.036, 0.100] | 0.080 [0.043, 0.121] | 0.0089 [0.0050, 0.0136] | 0.0% [0%, 0%] | 0.0% [0%, 0%] |
| final | train | 0.707 [0.638, 0.768] | 0.709 [0.638, 0.780] | 0.0899 [0.0768, 0.1040] | 70.0% [53%, 87%] | 7.9% [4%, 13%] |
| baseline | test | 0.063 [0.016, 0.115] | 0.080 [0.025, 0.149] | 0.0090 [0.0032, 0.0165] | 0.0% [0%, 0%] | 0.0% [0%, 0%] |
| final | test | 0.724 [0.629, 0.819] | 0.703 [0.589, 0.814] | 0.0934 [0.0673, 0.1244] | 80.0% [60%, 100%] | 3.7% [0%, 9%] |

Correct abstention by kind of unanswerable question:

| run | split | absent_clause | not_in_corpus | out_of_scope |
|---|---|---|---|---|
| baseline | train | 0% (n=13) | 0% (n=7) | 0% (n=10) |
| final | train | 46% (n=13) | 100% (n=7) | 80% (n=10) |
| baseline | test | 0% (n=7) | 0% (n=6) | 0% (n=2) |
| final | test | 71% (n=7) | 100% (n=6) | 50% (n=2) |
