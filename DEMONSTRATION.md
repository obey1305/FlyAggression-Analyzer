# PRJ 501 — five-minute Version 2.1 demonstration

## Before the presentation

Open the desktop workspace launcher, or run the extracted package launcher after installation. Keep FINAL-REPORT.pdf and the supplied completed movie1 report available. Live tracking is optional: the measured full30-minute movie1 run took about4 minutes5 seconds on this machine. Present a precomputed report while it runs.

## 0:00–0:45 — Explain the two workflows

Show the input-mode switch. Original MATLAB features retain the original frozen 1.0.0 classifier. Raw videos use automatic calibration, the existing FlyTracker and36-feature extractor, then the separately trained frozen2.1 classifier. Model-specific imputation and event rules stay with their respective bundles.

## 0:45–1:30 — Show automatic calibration

Choose Experimental raw video and upload `examples/movie1.mp4`. For this supplied benchmark only, use the documented nominal 16 mm arena. Detect the arena, inspect the boundary and confirm it. Explain that physical diameter must be measured for new experiments and cannot be inferred from pixels. For a short demonstration, `examples/movie1-first300.mp4` can use `examples/movie1-calibration.mat`; its short prefix alone is not a reliable automatic-calibration example.

## 1:30–2:30 — Show the analysis and exports

Start analysis and show the elapsed-stage messages, or open the supplied completed movie1 report. The full fresh run produced 68 predicted lunge events and 11.2 summed fly-seconds in predicted lunges. Show per-fly counts, event frequency, timelines, CSV and graphical downloads. Expand Analysis details: model 2.1.0, threshold 0.15, median 3, gap 1, minimum 3 frames. Explain inclusive frame durations.

## 2:30–3:15 — Confirm preservation of original mode

Switch to MATLAB features and load the development example. It still produces325 movie5 events with the original model. Explain that these are a different recording and feature condition;325 must not be compared directly with movie1’s 68. Known adapter-derived feature MAT files are rejected in original mode.

## 3:15–4:15 — Present the fair comparison

Show the final movie5 confusion matrices and event-onset timelines. On identical newly extracted features and common reliable coverage, Version 2.0 has frame/event F1 of16.64%/16.06%, versus Version 2.1 at62.32%/75.63%. The event comparison has124 retained expert bouts; Version 2.1 predicts114, of which90 match,24 are false positives and34 expert bouts are missed. Mention that threshold calibration contributes much of the improvement.

## 4:15–5:00 — State the scientific limits and next experiment

These are tuned development results, not independent final-test accuracy. Only124 of303 source bouts were retained, and only44.44% of annotation-reliable positive frames survived preparation. Full production reports cannot recreate expert-label censoring. The fresh full-run audit had573 uncertain reference-mapping frames; source IDs are not certified biological identities. New measured recordings and independent expert annotations are the next validation step.

Report the software evidence separately:26 Version 2.1 tests,55 original-workflow tests, nine handled invalid-input cases, frozen-file checks, and a real full-video run with audited CSV/PNG/ZIP exports. Relocated-package testing uses the existing pinned environment and is not a clean installation on another machine.
