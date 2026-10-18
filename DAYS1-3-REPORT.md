# Version 2.1 — Days 1–3 completion report

Reporting date: 19 October 2026. This delivery prepares a first reproducible development dataset; no aggression classifier or dataset-wide preprocessor is fitted and no accuracy improvement is claimed.

## Day 1 — Data generation and preservation

A separate Git repository and `v2.1` branch were created because the shared parent workspace was not a Git repository. The Version2.0 release archive and exact extractor sources were snapshotted; all nine frozen inference file hashes and the original release ZIP remain unchanged.

All ten available Caltech Aggression recordings were inventoried with video, expert-annotation, reference-track and original-feature hashes. The initial selected cohort is movies1–5: it reuses the complete verified current-generator movie1 run and generates movies2–5 fresh. Earlier manually calibrated movie6/movie8 features are not mixed into this cohort. Native tracking/features, 36-feature conversions, calibration, previews and processing metadata are retained per recording.

The author's experimental-setup figure describes the Aggression assay as 16 mm, 30 FPS and approximately 8 pixels/mm: [primary source, Figure 3.2](https://thesis.caltech.edu/10281/7/eyjolfsdottir_eyrun_2017.pdf). This supplies published nominal cohort provenance; no per-recording physical measurement certificate was found. The dimension is not assumed valid for unrelated videos. Each selected video uses automatic geometry/body/contrast calibration, preserving this uncertainty in metadata.

| recording | center | radius_px | nominal_mm | pixels_per_mm | fps | generation_seconds | reuse |
| --- | --- | --- | --- | --- | --- | --- | --- |
| movie1 | [71, 70] | 65 | 16 | 8.125 | 30 | 0.8 | True |
| movie2 | [73, 71] | 66 | 16 | 8.25 | 30 | 467.86 | False |
| movie3 | [74, 72] | 66 | 16 | 8.25 | 30 | 437.17 | False |
| movie4 | [72, 69] | 66 | 16 | 8.25 | 30 | 291.14 | False |
| movie5 | [72, 76] | 65 | 16 | 8.125 | 30 | 625.12 | False |

Movie1's generation time above is copying/checking a reused completed run, not fresh tracking time; its verified producer run took 237.17 seconds. Other timings include automatic calibration, tracking and conversion. These are observed host-load-dependent times, not controlled speed benchmarks.

## Day 2 — Identity and annotation alignment

Both reference and new trajectories have matching complete 54,000-frame streams per source fly at 30 FPS. Field names, not column positions, select coordinates. ±3-frame position-offset diagnostics are retained; labels are not silently shifted. If zero offset is materially worse, the recording is excluded for review.

Framewise reference-to-new assignment is retained only for finite pairs with each position error ≤3 pixels, pair assignment advantage ≥4 pixels, separation ≥8 pixels in both tracks, no source/new tracking warnings, and a stable assignment run of at least 15 frames. Five-frame buffers exclude uncertain intervals and every assignment change. Tracks and feature arrays are never reordered or edited; only label correspondence is mapped where evidence permits.

Full-grid audit files retain ambiguity, flags, mapping, source labels and missing values. Unknown and nonzero-flag annotations are excluded. Negatives are inferred from the provider's exhaustive-annotation description, not explicit expert-negative intervals. `aligned-lunge-bouts.csv` preserves original complete bout IDs/bounds and marks whole-bout eligibility rather than splitting uncertainty into artificial events. Overlap closure excludes any complete source bout intersecting an ineligible bout; source IDs remain distinct, while frame labels use interval unions.

Original reference trajectories anchor expert annotation IDs but are not independently certified biological identity truth. Conservative geometry can exclude difficult close-contact/lunge frames and introduce selection bias; the coverage losses below must accompany downstream scores. Per-recording selected source-lunge sequences are decoded for manual correspondence/timing spot checks; this is not a new independent expert behavior annotation or exhaustive video audit. See visual-review.md and selected-lunge-review PNGs.

| recording | source_bouts | whole_bouts_eligible | bouts_with_uncertain_mapping |
| --- | --- | --- | --- |
| movie1 | 71 | 60 | 11 |
| movie2 | 550 | 199 | 348 |
| movie3 | 426 | 265 | 145 |
| movie4 | 178 | 113 | 62 |
| movie5 | 303 | 125 | 176 |

## Day 3 — Model-ready dataset

Exact predictor ordering and transformations are documented in config/feature-columns.json and feature-definitions.md. Full consecutive features are calculated before masking. Data contain the same 12 transformed bases and 24 interleaved temporal responses as the current raw-video extractor. Temporal filtering and source-stream median normalization remain unchanged; identity changes can still affect whole-stream normalization. This is an extraction property, not corrected biological tracking.

Nonfinite feature rows are excluded from finite model-ready subsets; original rows and masks remain in full-grid Parquet files. No imputer/scaler is fitted. The predictor list explicitly excludes target labels, source IDs and audit metadata. Both source flies and every interval of a recording remain in one split: movies1–4 train, movie5 validation. There is no frame-level random split.

| recording | split | total | eligible | lunging | negative | excluded_positive | retained_percent |
| --- | --- | --- | --- | --- | --- | --- | --- |
| movie1 | train | 108000 | 106851 | 245 | 106606 | 42 | 98.94 |
| movie2 | train | 108000 | 96199 | 858 | 95341 | 1315 | 89.07 |
| movie3 | train | 108000 | 103081 | 1129 | 101952 | 526 | 95.45 |
| movie4 | train | 108000 | 104825 | 479 | 104346 | 218 | 97.06 |
| movie5 | validation | 108000 | 100479 | 527 | 99952 | 659 | 93.04 |

Split totals:

| split | recordings | rows | positive | negative | positive_percent |
| --- | --- | --- | --- | --- | --- |
| train | movie1, movie2, movie3, movie4 | 410956 | 2711 | 408245 | 0.6597 |
| validation | movie5 | 100479 | 527 | 99952 | 0.5245 |

Feature missingness and per-recording/source-fly min, 1st percentile, median, 99th percentile and max are in reports/feature-distributions.csv. The companion plot displays the 12 base-feature distributions; all 36 fields are checked in the table. Class imbalance is reported rather than hidden by aggregate frame accuracy. No class balancing or target-based row sampling is applied at preparation time.


## Positive-frame retention and distribution findings

The positive-frame baseline below excludes source-annotation uncertainty first, before identity/finite-feature filters. Only about 54% of these positives survive across the selected cohort. This is a substantial selection bias even though most total frames survive. A model trained on this subset cannot be assumed accurate on the excluded difficult contacts.

| split | annotation_reliable_positive_frames_before_filters | retained_positive_frames | excluded_positive_frames | positive_retention_percent |
| --- | --- | --- | --- | --- |
| train | 4812 | 2711 | 2101 | 56.34 |
| validation | 1186 | 527 | 659 | 44.44 |

Validation feature distributions differ from training: transformed fg_body_ratio medians are 0.261–0.283 versus training-stream medians 0.429–0.515; validation fly1 contrast has a 99th percentile of 2.743; validation fly1 max_wing_ang median is -0.431 versus training-stream medians -1.003 to -0.757. Per-stream normalization makes the medians of mean_wing_length, axis_ratio and contrast exactly 1, as expected. These are descriptive differences, not proof of a specific tracking failure or a reason to fit normalization on validation data. Behavior mix, appearance and measurement settings are possible explanations requiring further investigation. Numerical consistency does not certify equivalent biological measurements.

All five 36-feature arrays independently match the official pinned MATLAB feat_augment_data output within absolute tolerance 1e-12, including identical NaN locations. Maximum observed finite difference is below 9e-16. See augmentation-verification.json.

## Verification and limits

Independent auditing reconstructs source labels directly from annotation intervals, verifies every eligible label against its mapped reference ID/frame, checks geometric assignment criteria and five-frame warning/transition context, compares stored feature values with their source arrays, verifies finite model-ready rows, complete audit grids, unique keys, recording separation, both classes, source hashes and release/model preservation. Synthetic tests cover swapped identities, ambiguity, swap buffers and inclusive unknown-label precedence. Detailed PASS evidence is in reports/verification.json and tests.log.

Movies6–10 were previously examined in original-model evaluation; they are not a fresh independent final test set. No genuinely new independent annotated recordings were found in this preparation. They remain outside the current train/validation files, and a fresh final generalization claim requires new independent recordings. Movie5 has also been reused for development and must not be described as independent final evaluation.

This is an initial five-recording development cohort, not extraction of all ten inventoried recordings. Native/reference identity warnings and uncertain mappings remain excluded. Published nominal arena dimensions are not individual metrology. Manual checks are limited samples. Functional data preparation does not guarantee achieving the later 0.75 event-F1 target.

## Delivered artifacts and reproduction

- data/train.parquet and data/validation.parquet: 36 finite predictors, source keys and binary lunge target.
- data/movie*/: full-grid audit Parquets, eligible data, aligned bout tables, reference/new mapping intervals, offset diagnostics, native features/tracks, calibration and provenance.
- config/: fixed preparation policy, inventory/hashes, feature definitions and preservation manifest.
- reports/: coverage, distributions, calibration/bout tables, visual review and independent verification.
- scripts/ and tests/: reproducible generation, alignment, audit and review code.
- source-snapshot/: Version2.0 archive and extractor source copies, retained outside Git large-file tracking.

See README.md for commands. Version2.0 remains operational; no app replacement or model training is performed in Days1–3. The next step is a separately fitted raw-video classifier using only this declared training split, with any tuning restricted to development validation and independent testing explicitly qualified.

Six preparation unit tests pass. The final manual review covers 70 decoded stills across ten source-labelled lunge sequences (two per selected recording); short source clips are retained for additional human review. This verifies sampled correspondence/timing, not independent expert-equivalent biological annotation. No new aggression classifier is fitted.
