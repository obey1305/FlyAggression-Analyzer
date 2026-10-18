# FlyAggression Analyzer 2.1 — Days 1–3 data preparation

Separate Git repository/branch `v2.1`; the surrounding workspace was not a Git repository. This work prepares data only. No new aggression classifier is fitted, and the Version 2.0 app, tracker, original frozen model and release archive are preserved.

## Cohort

Initial selected cohort: movies1–5 from the available Caltech Aggression recordings. Movies1–4 are training; movie5 is validation. Both flies and every interval from a recording remain together. Movies6–10 are inventoried but not included in these prepared splits: their earlier original-model test results were already consumed. There is no genuinely independent new final test set in this preparation.

All selected recordings use the current automatic-calibration/feature-extraction workflow. Movie1 reuses the verified completed current-generator run with input/calibration hashes checked; movies2–5 run fresh. The same 36-feature ordering and upstream log/median/temporal definitions are retained. The dataset-specific nominal 16 mm arena is supported by the author's experimental-setup figure: https://thesis.caltech.edu/10281/7/eyjolfsdottir_eyrun_2017.pdf (Figure 3.2). This is cohort-level nominal provenance, not individual physical metrology. No such dimension is inferred for unrelated videos.

## Conservative alignment contract

New tracks are not renamed, reordered or edited. Labels are mapped per frame from original reference tracks to the new source fly. Reliable assignments require finite coordinates, each best-pair error ≤3 pixels, pair-cost advantage ≥4 pixels, separation ≥8 pixels in both tracks, no native/reference tracking warnings, and a stable assignment run ≥15 frames. A five-frame buffer excludes unreliable regions and every assignment change; first/last five frames are also excluded. These geometric settings are predeclared in config/preparation.json and are not optimized against classifier scores.

The original reference identity is a correspondence anchor for the provided annotations, not independently certified biological identity. Close contacts and ambiguous mappings are excluded, not forced into a label. Whole-recording feature normalization is computed before exclusions so discontinuous subsets never become artificial temporal neighbors. Any derivative context crossing a swap/uncertain frame is buffered; full-grid features retain the existing pipeline's per-stream normalization even where source identities switch. This remaining measurement property must be considered when training later.

Lunge source bouts become positive labels with inclusive endpoints. Absent bouts become inferred background only under the provider's exhaustive-annotation assumption. Unknown intervals and any nonzero annotation flag are excluded. There are no explicit expert negative intervals. Nonfinite-feature rows are excluded from model-ready subsets; original full-grid rows, values and masks remain available. No imputer is fitted here. Future imputation/scaling must be learned exclusively on the training split.

## Files and reproduction

- config/: selected cohort, fixed splits, schema, calibration evidence, source inventory and preservation hashes.
- scripts/generate_features.py: calibration, tracking and feature generation (current local MATLAB installation required).
- scripts/prepare_aligned.py: reference/new mapping, label expansion, complete-grid audit and fixed recording splits.
- tests/: synthetic swap/ambiguity/boundary and annotation precedence checks.
- data/movie*/: native tracks/features, calibration, generation provenance, mapping audits, full grids and eligible rows.
- data/train.parquet, validation.parquet: finite, eligible 36-feature data plus source keys and provenance columns.
- reports/: quality/coverage/distribution summaries and selected-event visual review.
- source-snapshot/: preserved Version2.0 archive and exact extractor source copies (large artifacts are git-ignored).

Use the existing pinned interpreter `../drosophila-aggression/.venv/bin/python`. From this directory:

```sh
../drosophila-aggression/.venv/bin/python scripts/generate_features.py
../drosophila-aggression/.venv/bin/python scripts/prepare_aligned.py
../drosophila-aggression/.venv/bin/python -m unittest discover -s tests
```

Generation is resumable at completed recording boundaries. Existing intermediates/results are retained. Do not mix earlier manually calibrated movie6/movie8 feature files into this automatically calibrated cohort. No accuracy improvement or generalization claim follows from preparing this dataset.

## Final verification and reporting

After generation/preparation, independently compare augmentation with the official MATLAB function and run the remaining audit/report steps:

```sh
/Applications/MATLAB_R2026a.app/bin/matlab -batch "run(fullfile(pwd,'scripts','verify_augmentation.m'))"
../drosophila-aggression/.venv/bin/python scripts/check_augmentation.py
../drosophila-aggression/.venv/bin/python scripts/review_examples.py
../drosophila-aggression/.venv/bin/python scripts/prepare_aligned.py
../drosophila-aggression/.venv/bin/python scripts/audit_dataset.py
../drosophila-aggression/.venv/bin/python scripts/build_report.py
```

Visual-review image/clip generation additionally uses the installed `/opt/homebrew/bin/ffmpeg`; this is an inspection dependency, not a new tracking algorithm. Review the resulting frames manually before accepting the visual-review note. The stored note records the current review, not a claim that future regenerated images were inspected automatically.

Current outcome: 410,956 finite training rows (2,711 positives), 100,479 finite validation rows (527 positives), six preparation tests and independent dataset/official-MATLAB checks pass. Only about 54% of annotation-reliable positive frames remain after conservative filters. This is an important selection bias, not evidence of improved detection. No new aggression classifier or fitted dataset-wide preprocessor was produced.
