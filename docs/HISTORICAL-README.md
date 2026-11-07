# FlyAggression Analyzer Version2.2 research release

See [final report](FINAL-REPORT-V22.md), [installation/user guide](INSTALLATION-V22.md) and [demonstration](DEMONSTRATION-V22.md). Both workflows are integrated and tested. Retrospective evaluation found no accuracy, identity or annotation-coverage improvement over2.1; no independent annotated test recording was available. Historical reports below describe earlier development stages.

# Version 2.2 development — Days 3–6

See [Days 3–6 report](DAYS3-6-REPORT.md) for calibration audit, rebuilt data, separate fresh candidate and temporal search. No accuracy or coverage improvement was measured. Nominal physical scale remains unverified per recording; candidate is offline and not integrated.

# Version 2.2 development — Days 1–2

Offline exclusion audit and conservative reference-assisted identity alignment. See [Days 1–2 report](DAYS1-2-REPORT.md). No new classifier or runtime integration is included; Version 2.1 remains the working application.

The following inherited documentation describes the preserved Version 2.1 baseline.

# FlyAggression Analyzer 2.1

Completed local research prototype through Days9–10. See **FINAL-REPORT.pdf** for the measured results and limitations, **INSTALLATION.md** for setup, and **DEMONSTRATION.md** for the PRJ501 walkthrough.

- Workspace app: `app.py`, opened by the Desktop **FlyAggression Analyzer.command**, port8502.
- Original MATLAB workflow: original frozen1.0.0 classifier, preserved unchanged.
- Raw MP4 workflow: unchanged automatic calibration and tracker/36-feature adapter, separate frozen2.1.0 Random Forest.
- Raw model: `models/raw-v2.1/` (threshold0.15, median3, gap1, minimum3 frames).
- Training: movies1–4; development selection: movie5. No untouched final-test recording available.
- Final development results on filtered movie5 coverage: frame F1 **62.32%**, event F1 **75.63%**. Event evaluation retains124/303 source bouts; these are not independent full-video accuracy estimates.
- Fresh full30-minute movie1 functional test: **244.8 seconds**, **68 predicted events**, **11.2 summed fly-seconds**. Training-source test, not accuracy validation.
- Final checks: **26 Version2.1 tests**, **55 original-workflow tests**, nine handled invalid-input cases, independent export/metric audits and relocated package verification.

The release ZIP and folder are siblings of this repository: `../FlyAggression-Analyzer-v2.1-Release.zip` and `../FlyAggression-Analyzer-v2.1-Release/`. The extracted launcher uses port8503 and requires a separately installed compatible Python environment and licensed MATLAB. The relocated package was tested with the existing pinned environment, not a clean dependency installation on another machine.

Detailed evidence is under `reports/day9/`, `reports/day10/` and `reports/day9-final-verification.json`. Earlier reports preserve the Days1–3 preparation, Day4 baseline and Days5–8 development history. Training data and source release snapshots remain outside Git under `data/` and `source-snapshot/`; their hashes are recorded. No training or parameter tuning occurred during Days9–10.
