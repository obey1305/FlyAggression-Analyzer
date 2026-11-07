# FlyAggression Analyzer

PRJ 501 research prototype for automated Drosophila lunge detection and quantification.

**Current software: Version 2.3.** The raw-video workflow uses the unchanged frozen Version 2.2 Random Forest. The original MATLAB feature-file classifier remains available.

## Start here

- [Download the packaged application](https://github.com/obey1305/FlyAggression-Analyzer/releases/tag/v2.3.0)
- [Installation](INSTALLATION-V23.md) · [User guide](USER-GUIDE-V23.md)
- [Final report](FINAL-REPORT-V23.md) · [PRJ 501 demonstration](DEMONSTRATION-V23.md)
- [Dataset and compatibility inspection](DAYS1-4-REPORT-V23.md)
- [Cross-dataset evaluation and failure analysis](DAYS5-8-REPORT-V23.md)

The packaged release includes the companion runtime files needed by the application. A source checkout preserves the research history; several research scripts reference the original local data layout. Use the release package and installation guide for the tested runnable distribution. Python dependencies, licensed MATLAB and FFmpeg must be installed separately. This is a macOS-tested research prototype, not a validated clinical or production system.

## Supported workflows

- Compatible original MATLAB feature files with the frozen original classifier.
- Circular-arena 30 FPS MP4 recordings with the preserved calibration and tracking workflow.
- Tested rectangular-arena constant 30/200 FPS AVI/MP4 recordings, timestamp mapping, FlyTracker and 36-feature extraction.
- Lunge counts, durations, timelines and CSV, PNG and ZIP exports.

## Scientific results and limits

The frozen model was evaluated on one externally collected Boy Meets Boy recording under a locked protocol. Primary annotations retained **9/42 expert events (21.43%)**, with conditional event F1 **0.750**; secondary annotations retained **32/48 (66.67%)**, with event F1 **0.718**. These are restricted-coverage results, not full-recording accuracy estimates. Frame-level scoring assumes the supplied labels are exhaustive in eligible intervals. Arena scale is published nominal scale, not a verified per-recording measurement. Fly identity and tracking uncertainty remain documented limitations.

The fresh full-video functional run reproduced **64 operational predicted events**. Operational counts differ from the subset of predictions eligible for expert comparison. No classifier retraining or threshold tuning occurred during Version 2.3 evaluation. See the final report before interpreting any metric.

## Repository organization

| Location | Contents |
| --- | --- |
| `app.py`, `scripts/` | Interface, import, tracking integration and analysis tools |
| `models/`, `config/` | Frozen models, preprocessing, provenance and evaluation locks |
| `tests/` | Regression and integration tests |
| `reports/` | Recorded development and validation evidence |
| `examples/` | Completed demonstration exports |
| `docs/` | Implementation plans and historical documentation |

Large raw videos, Python environments and temporary processing folders are excluded. The source dataset is attributed in the installation guide: [Boy Meets Boy, Caltech Data](https://data.caltech.edu/records/zrznw-w7386), DOI 10.22002/D1.1893. Obtain data from its provider under the provider's terms. Third-party components retain their original notices; this repository does not grant new rights over them.

## Preserved versions

`main` contains the GitHub handoff documentation above Version 2.3. Branches `v2.1`, `v2.2` and `v2.3` preserve their original commits. Release tags identify the corresponding frozen snapshots. Do not overwrite frozen model files or reuse evaluation recordings as untouched test data after tuning.

The original development narrative is preserved in [historical README](docs/HISTORICAL-README.md).
