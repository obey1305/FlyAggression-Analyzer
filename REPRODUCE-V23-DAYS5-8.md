# Reproduce Version 2.3 Days 5–8

Run from this isolated `flyaggression-v2.3` worktree using sibling `../drosophila-aggression/.venv/bin/python`. Use the preserved Day 1–4 feature/tracking artifacts and original Boy Meets Boy MAT files at the absolute paths recorded in `config/v23-evaluation-lock.json`. No new download, tracking, fitting or threshold search is required. The original feature MAT workflow and released application are unchanged.

## Inspect the completed evaluation

- `DAYS5-8-REPORT-V23.md`: complete interpretation and limitations.
- `reports/v23-days5-8/performance-table.csv`: aggregate metrics, coverage and temporal sensitivity.
- `reports/v23-days5-8/per-fly-performance.csv`: per-native-output-fly metrics.
- `reports/v23-days5-8/{primary,secondary}-all-source-bouts.csv`: every source lunge, native interval, projected bins, retained/excluded status and reasons.
- `reports/v23-days5-8/{primary,secondary}-all-operational-event-eligibility.csv`: every one of 64 fixed operational events, including exclusions.
- `reports/v23-days5-8/*-matches.csv`, `*-expert-outcomes.csv`, `*-predicted-outcomes.csv`: individual outcomes and native-time onset/offset/duration errors.
- `data/v23-evaluation/{primary,secondary}-grid.parquet`: complete per-fly frame/identity/target/eligibility grid. Outcomes and features retain missingness; no frame rows were dropped.
- `data/v23-predictions/probabilities.parquet` and `processed-full-grid.parquet`: all 76,780 frozen probabilities and unchanged operational temporal output.
- `config/v23-evaluation-lock.json`: pre-inference input hashes and protocol. Commit `4025d01` precedes the one successful prediction run. `reports/v23-days5-8/inference.json` records the same protocol hash and every prediction artifact hash.

Large local data are ignored by Git; preserve them along with original downloaded data. Git contains code, protocol, small receipts, CSV outcomes and figures. A checkout alone does not reproduce the large input artifacts; follow Day 1–4 reproduction first or restore the exact hashed files.

## Validation without model inference

```sh
../drosophila-aggression/.venv/bin/python -m unittest discover -s tests/v23 -v
../drosophila-aggression/.venv/bin/python -m unittest discover -s tests -p test_preparation.py -v
../drosophila-aggression/.venv/bin/python scripts/v23/verify_days5_8.py
```

## Fresh execution order

In a fresh copy with the preserved Day 1–4 data available and **new output destinations**, run these scripts in order:

```sh
../drosophila-aggression/.venv/bin/python scripts/v23/prepare_evaluation.py
# Commit the new protocol and eligibility artifacts BEFORE model prediction.
../drosophila-aggression/.venv/bin/python scripts/v23/run_frozen.py
../drosophila-aggression/.venv/bin/python scripts/v23/evaluate_frozen.py
../drosophila-aggression/.venv/bin/python scripts/v23/analyze_failures.py
../drosophila-aggression/.venv/bin/python scripts/v23/report_days5_8.py
../drosophila-aggression/.venv/bin/python scripts/v23/verify_days5_8.py
```

The supplied worktree already contains a lock and successful predictions. `prepare_evaluation.py` refuses to replace a lock, and `run_frozen.py` refuses an existing prediction directory. Preserve this evidence; do not remove a lock or change hashed code/data to force an unrecorded rerun. For a fresh reproduction copy, adjust destinations, commit the new protocol, update the verifier's lock-commit identity to that new commit, and explicitly record the new run; do not describe it as a fresh untouched test after results have been examined. Evaluation/report regeneration reads the existing frozen predictions and cannot fit a model.

## Fixed interpretation

Native expert intervals use `[(start-1)/200,end/200)`, predictions use `[(start-1)/30,end/30)`. Main IoU threshold is 0.30 with cardinality-first one-to-one matching. Prediction smoothing runs once on the full grid with the saved fitted imputer, threshold0.15, median3/gap1/min3. Evaluation excludes whole predictions crossing locked boundaries; it never clips or re-smooths them against annotation labels. This differs from prior development scoring and creates boundary-excluded responses among primary FN counts. Projected-grid sensitivity is separate and was not used for parameter selection.

Frame metrics assume exhaustive lunge labels outside explicit uncertainty, and remain conditional because unlabelled frames are not confirmed expert negatives. Nonzero unverified extra annotation values are conservatively uncertain. Relative geometric correspondence is not biological identity certification. Coverage is 9/42 primary and32/48 secondary expert events; neither result represents whole-recording accuracy.
