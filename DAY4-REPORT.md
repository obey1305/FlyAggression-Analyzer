# FlyAggression Analyzer 2.1 — Day 4 training report

A separate raw-video-specific Random Forest candidate was trained on movies 1–4 and evaluated on movie5. The original frozen classifier and application remain unchanged.

| Model | Precision | Recall | Frame F1 |
|---|---:|---:|---:|
| previous | 79.03% | 9.30% | 16.64% |
| candidate | 77.99% | 23.53% | 36.15% |

Candidate minus previous frame F1: +19.51 percentage points. Training took 49.2 seconds.

## Method
Training: 410,956 rows, 2,711 lunging frames; validation: 100,479 rows, 527 lunging frames. All 36 predictor names and ordering are explicit; fly IDs, frame numbers, split and labels are excluded from predictors. Median imputation was fitted only on training rows and verified against training medians. RF: 128 trees, maximum depth 20, minimum leaf 2, sqrt feature selection, seed 501, four workers. Positive class weight is sqrt(training negatives / training positives), 12.271444; negative weight 1. Fixed threshold 0.5, one candidate, no parameter or threshold search.

Both models score the same 108,000-row newly extracted movie5 grid. Frame metrics use exactly the same 100,479 eligible aligned validation rows. Confusion matrices in metrics.json use true classes as rows and predicted classes as columns, ordered [0,1]. These are unsmoothed frame metrics; event detection optimization and event-level validation remain future work. Original event rules are copied as defaults only.

## Limits
Only 527 of 1,186 annotation-reliable movie5 positive frames (44.44%) survived alignment and feature quality exclusions. Training retained 2,711 of 4,812 positives (56.34%). Scores describe this selected reliable subset, not full-recording biological accuracy. Absent annotated bouts are inferred negatives under an exhaustive-annotation assumption. Track identities and nominal 16 mm arena calibration have documented uncertainty. Whole-recording feature normalization remains part of the existing extractor; the newly fitted imputer uses training rows only. Movie5 was already used for previous model development and is not independent validation. Movies6–10 were previously examined and were not used here; fresh independent recordings are required for a new generalization claim. Previous raw-video frame F1 38.05% and event F1 39.84% came from different recordings/calibration and must not be treated as the baseline for this table.

## Saved artifacts
- models/day4-raw-random-forest.joblib: separate candidate and trained imputer.
- config/day4-training.json: fixed protocol, feature order, weights, versions and input hashes.
- reports/day4/metrics.json: paired metrics and verification.
- reports/day4/movie5-full-grid-probabilities.parquet: both models, full grid.
- reports/day4/movie5-eligible-probabilities.csv: common scored validation subset.
- reports/day4/feature-importances.csv: descriptive fitted importances.

Verification: all source dataset manifest hashes matched; recording splits disjoint; complete finite binary training/validation subsets; imputer statistics equal training medians; serialized model predictions agree within 1e-14; all nine original frozen file hashes unchanged. Candidate has not replaced the application model.

Independent post-training verification also passed: manually reconstructed confusion matrices and metrics, both models’ full-grid probability reproduction, training medians, input hashes, nine frozen file hashes and Version 2.0 archive hash. Nine preparation/training unit tests passed.

Reproduce from the workspace root:
```sh
outputs/drosophila-aggression/.venv/bin/python outputs/flyaggression-v2.1/scripts/train_day4.py
outputs/drosophila-aggression/.venv/bin/python outputs/flyaggression-v2.1/scripts/verify_day4.py
```
The training command overwrites Day 4 candidate artifacts using the fixed protocol.
