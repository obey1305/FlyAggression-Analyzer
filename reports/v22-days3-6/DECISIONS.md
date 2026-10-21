# Days 3–6 execution record

Approved scope: calibration/feature consistency, conservative annotation rebuild, separate fresh RF fit, development-only temporal search. Executed inline on existing isolated v2.2 worktree after a43d96f.

- Day 3: No per-record physical measurement available. Keep nominal scale with explicit uncertainty; run fixed-track ±10% scale sensitivity, never select a guessed diameter from F1 or feature agreement.
- Day 4: No accepted Day2 identity bridges. Rebuild labels, retain warnings/unknown/whole-bout rules and compare exact frame and event parity. No recovery is justified.
- Day 5: Data are unchanged. One fresh same-settings estimator fit isolates the data-quality question; do not add unrelated hyperparameter tuning or claim improved data. Fit completed in 49.46s; probability difference 0.0.
- Day 6: Predeclared 27 temporal configurations on movie5 only; no threshold search; same winning settings. No independent final-test claim.
- Review fix: Independent boundary helper originally allowed overlapping later unflagged bouts to override flags. Added failing overlap regression, changed to sticky exclusion mask, then passed all 14 unit tests. Actual rebuilt labels used the unchanged correct annotation_labels throughout; complete-grid parity verified. Independent source labels now compared for all 540000 rows by finish_days3_6.py.
- Initial module-absent test failure and overlap regression failure saved with green suite receipt.
