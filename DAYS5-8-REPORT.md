# FlyAggression Analyzer 2.1 — Days 5–8 report

20 October 2026 · PRJ 501 · Development validation and local integration build

The selected raw-video-specific classifier improves performance on movie5’s common reliable subset. It is integrated into a separate Version 2.1 application build. The original Version 2.0 app, archive, original frozen classifier and extraction sources remain unchanged. No untouched final-test recordings were evaluated.

## Comparison on the same newly extracted movie5 features

| Model / operating point | Frame precision | Frame recall | Frame F1 | Event precision | Event recall | Event F1 |
|---|---:|---:|---:|---:|---:|---:|
| original | 79.03% | 9.30% | 16.64% | 84.62% | 8.87% | 16.06% |
| day4 | 77.99% | 23.53% | 36.15% | 86.11% | 25.00% | 38.75% |
| selected | 55.67% | 70.78% | 62.32% | 78.95% | 72.58% | 75.63% |

Selected minus Day 4: frame F1 **+26.17 percentage points**; event F1 **+36.88 points**. Selected minus original operating on these new features: frame F1 +45.68 points; event F1 +59.57 points.

Frame metrics use 100,479 identical eligible fly-frames with 527 positive frames. Event metrics use 100,425 fly-frames after conservative whole-bout censoring, with 124 complete mapped expert bouts retained from 303 source bouts. Both models use exactly the same evaluation coverage. IoU threshold is 0.3, with one-to-one maximum-cardinality matching. The original and Day 4 models use their existing 0.5 thresholds and median3/gap1/minimum2 rules; the selected model uses tuned settings. Differences therefore include operating-point and postprocessing changes, not just RF architecture.

## Day 5 — bounded model and threshold experiments

Training used movies1–4 only: 410,956 finite rows, including 2,711 positives. Each candidate’s median imputer was fitted only on those training rows and checked against their exact feature medians. All 36 predictors and their order are explicit; metadata and labels are excluded. No validation data were passed to fit.

Day 4 was reused. Exactly three additional forests were fitted with 128 trees, sqrt feature selection, bootstrap sampling, seed 501 and four workers: balanced class weights with depth20/leaf2; damped class weights with unlimited depth/leaf1; and balanced-subsample weights with depth20/leaf4. Damped positive weight is sqrt(training negatives / training positives), with negative weight 1. Seven fixed thresholds per model were examined: 0.10, 0.15, 0.20, 0.25, 0.30, 0.40 and 0.50. Selection used frame F1, then precision and recall; fixed deterministic tie breaks are saved in the protocol. No feature elimination, extra candidate search, recording changes or test-data tuning followed.

| Candidate | Best tested threshold | Precision | Recall | Frame F1 |
|---|---:|---:|---:|---:|
| deep | 0.15 | 55.67% | 70.78% | 62.32% |
| day4 | 0.15 | 49.88% | 77.61% | 60.73% |
| balanced | 0.30 | 44.64% | 66.41% | 53.39% |
| subsample | 0.30 | 47.44% | 59.77% | 52.90% |

Much of the gain comes from threshold calibration: Day 4 at threshold0.15 already reaches 60.73% frame F1. The deeper forest adds about 1.59 percentage points over that threshold-adjusted control. Average precision changes only from 61.35% to 61.69%. Higher class-weight alternatives performed worse here. The new threshold improves recall but reduces frame precision from Day 4’s 77.99% to 55.67%; it is not a uniform improvement at every operating point.

### Error and feature review
At the selected operating point, frame outcomes are: {'TN': 99655, 'TP': 373, 'FP': 297, 'FN': 154}. All rows, source keys and trajectory diagnostics are saved in validation-frame-outcomes.csv.

Three high-confidence false positives and three low-probability false negatives were examined across 18 decoded stills, with old/reference trajectories in blue and newly extracted tracks in red. No obvious positional fly-to-track mismatch was visible in these six sampled neighborhoods. This limited correspondence review does not establish behavioural ground truth, verify all orientations or validate all excluded intervals. Source labels were not changed. See selected-error-review.png and selected-error-cases.json.

The highest fitted importances are: facing_angle (17.1%), axis_ratio_diff1 (12.6%), axis_ratio_diff2 (8.4%), fg_body_ratio (7.0%), leg_dist (6.8%), mean_wing_length_diff1 (5.9%). These are descriptive impurity importances and can be biased; they do not prove causation. True and false positive frames have overlapping facing-angle, foreground/body-ratio and minimum-foreground-separation medians, so these features alone do not cleanly distinguish the errors.

| Feature | Validation median shift / training IQR |
|---|---:|
| fg_body_ratio | -2.405 |
| max_wing_ang | +0.240 |
| ang_vel | -0.207 |
| vel | -0.198 |
| min_wing_ang | +0.128 |

The foreground/body-ratio shift is substantial and consistent with the earlier distribution audit. These differences may reflect recording, segmentation and behaviour mix; they are not proof of a single failure mechanism. Per-record q01/q25/median/q75/q99 and error-group medians are saved. The original feature normalization was preserved, not fitted to validation data.

## Day 6 — event optimization

Only the Day 5 selected model/threshold was used. The 27 predeclared combinations were median window1/3/5, merge gap0/1/2 and minimum span1/2/3 frames. Expert bout endpoints remained complete and inclusive. Unknown tracking/annotation regions are hard boundaries; source bouts touching them are excluded whole, with conservative cross-stream overlap closure. Source event numbers restart for each reference fly; evaluation uses unique compound IDs while retaining both reference_fly_id and source_event_id. This avoids collisions when reference flies map to the same source track at different times.

Selected postprocessing: **threshold0.15, median3, gap1, minimum3 frames**, at 30 fps. Minimum span is 0.10 seconds. Median filtering is centered/offline, with nearest-edge handling within each valid segment. Gap merging cannot cross invalid or absent frames. With minimum2 instead of3, event F1 was 74.72%; minimum3 improved precision while reducing recall, yielding 75.63%.

Selected model: **114 predicted vs124 retained expert events**, with **90 matches, 24 false-positive events and 34 missed events**. Count difference is −10, but that small net difference hides both types of error. No expert event was overlapped by multiple retained predictions under the reported fragmentation definition; this does not prove an absence of all timing errors. Saved match tables provide IoU, onset and duration errors.

## Day 7 — per-record comparison and freezing

| Recording | Scope | Original frame/event F1 | Day 4 frame/event F1 | Selected frame/event F1 | Retained expert / selected predicted |
|---|---|---:|---:|---:|---:|
| movie1 | training-resubstitution | 78.66% / 88.89% | 99.19% / 95.65% | 96.08% / 95.65% | 60 / 55 |
| movie2 | training-resubstitution | 68.50% / 70.99% | 92.81% / 92.06% | 85.84% / 89.09% | 199 / 241 |
| movie3 | training-resubstitution | 70.28% / 76.89% | 96.95% / 96.83% | 91.01% / 94.37% | 265 / 286 |
| movie4 | training-resubstitution | 77.01% / 80.95% | 94.01% / 90.13% | 87.25% / 88.61% | 113 / 124 |
| movie5 | development-validation | 16.64% / 16.06% | 36.15% / 38.75% | 62.32% / 75.63% | 124 / 114 |

Movies1–4 are training resubstitution diagnostics, not held-out performance, and were not used to select this search result. The strong training scores versus lower movie5 frame F1 show an important generalization gap. Only movie5 is excluded from the new model’s fitting, and it is repeatedly used for development selection. Movies6–10 were previously examined and remain excluded from these experiments. No fresh independent final test is available.

Frozen artifacts: models/raw-v2.1/lunge-detector.joblib, configuration.json and freeze-manifest.json. The selected model is deep. Model SHA-256: `d8193350a2d100f761e84c2d60609b5f9c17cb4bcc651c82bbf2e3dc5f831f5a`. The bundle contains the fitted imputer, predictor order, threshold and event rules.

## Day 8 — integration and functional verification

Version 2.1 is a separate local build at app.py, preserving the original Version 2.0 files. Raw MP4 inference explicitly selects the hash-checked raw-v2.1 bundle. Original compatible MATLAB files continue through the original frozen runtime and its own model. Automatic calibration, tracking and the 36-feature adapter are reused. The app displays actual model version, hash, threshold and rules; result downloads include provenance, counts, durations, frequencies, timelines and graphical reports. Missing, changed or mixed model/configuration/adapter files fail before tracking starts.

All 19 preparation, training, optimization, routing and app tests passed. Independent verification reconstructed coverage and frame metrics, checked source event endpoints, used a separate maximum-bipartite-matching calculation to verify event match cardinality, reproduced selected probabilities after reload, checked input hashes and confirmed the original nine frozen files, Version 2.0 archive and extraction sources are unchanged. Code review reported no material findings.

Functional smoke passed in 37.1 seconds: fresh automatic calibration on full source movie1, fresh tracking/extraction/inference on a 300-frame (10-second) stream-copied excerpt using that calibration, correct Version 2.1 model hash/settings, and CSV/PNG/ZIP exports. Original MATLAB analysis still used the original model and produced 325 movie5 development-example events. This was a training-source functional check, not accuracy validation.

The first ten seconds alone failed the existing two-fly calibration reliability check; the guard was retained. An H.264 re-encoding was also rejected because MATLAB reported 30.0000019 fps, outside the existing strict tolerance, while the source stream copy retained compatible timing. These input compatibility limits are documented rather than bypassed. See INTEGRATION-GUIDE.md.

## Limits and next work

Only 44.44% of annotation-reliable movie5 positive frames survived preparation, and event evaluation retains 124/303 source bouts (40.92%). High total-frame coverage therefore does not establish representative positive-event coverage. Absent annotated bouts are inferred negatives under the provider’s exhaustive-annotation assumption. Actual physical arena measurements are unavailable; the benchmark uses published nominal 16 mm, which cannot be generalized to arbitrary uploads. Tracking identities, orientation, segmentation and excluded intervals still warrant expert review. Original whole-recording stream normalization is unchanged. Production outputs do not have expert labels available to reproduce the evaluation censoring mask and can include tracking failures; therefore the reported filtered development F1 must not be advertised as full-video biological accuracy.

No independent-performance claim is made from reaching 75.63% event F1 here. Obtain new recordings and measured calibration metadata, freeze this build before one-time independent testing, and review uncertain tracking/annotation alignment before increasing model complexity further. Days9–10 reliability testing and final packaging remain outside this Days5–8 deliverable.

## Inspectable evidence

- config/days5-7-protocol.json: fixed search, split and coverage policy.
- reports/days5-7/frame-search.csv and event-search.csv: every evaluated configuration.
- reports/days5-7/comparison-by-recording.csv: per-record metrics and counts.
- reports/days5-7/movie1…movie5/: common coverage, probabilities, events, matches and outcomes.
- reports/days5-7/feature-profiles.csv and feature-error-diagnostics.csv: distributions and error summaries.
- reports/days5-7/independent-verification.json: independent audit.
- reports/days5-8-tests.log: 19-test output.
- reports/day8/: actual functional-run manifests and export artifacts.
- INTEGRATION-GUIDE.md: launch, inputs, limitations and reproduction commands.
