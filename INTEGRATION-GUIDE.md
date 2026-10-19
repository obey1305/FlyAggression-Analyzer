# FlyAggression Analyzer 2.1 integration guide

This local integration build adds the selected raw-video-specific Random Forest while preserving the original Version 2.0 app, archive, classifier and extraction sources. Run `launchers/launch-v2.1.command` to open the Version 2.1 app at http://127.0.0.1:8502. The desktop shortcut points to this build after verification. The saved original launcher remains in `launchers/original-v2.0.command` and opens Version 2.0 on port 8501.

## Requirements

Use the existing sibling `drosophila-aggression/.venv` Python environment, installed MATLAB R2026a, required Image Processing/Statistics toolboxes and the pinned sibling `raw-video-integration/FlyTracker` installation. This is a local integration build with sibling dependencies, not a standalone redistributable package. Keep the three output folders in their current relative positions. Dependency versions are recorded in the original requirements and `config/toolchain.json`.

## Raw MP4 workflow

1. Launch Version 2.1 and choose **Experimental raw video**.
2. Upload a compatible overhead two-fly MP4 with one visible circular arena at 30 fps.
3. Enter the actual measured arena diameter; detect the arena and inspect the highlighted boundary. Alternatively upload matching FlyTracker calibration.
4. Confirm the experimental-prediction acknowledgement and select **Analyse video**.
5. Review counts, durations, frequencies and timelines; download CSV, PNG or ZIP reports. Analysis details show the actual model version, hash, threshold and postprocessing rules.

The software does not infer physical millimetres from pixels. The benchmark's nominal 16 mm is not a measurement for arbitrary videos. Automatic calibration rejects videos where reliable two-fly detection is unavailable. Very short or nearly stationary clips can fail that safeguard even when the full source recording calibrates successfully. The current MATLAB decoder/legacy calibration requires a tightly matched 30 fps value; nominally 30 fps encodings with small decoder rounding differences can be rejected. Use a compatible acquisition/export or a verified source calibration; do not override warnings blindly.

## Original MATLAB workflow

Choose **MATLAB features**, upload a compatible original `feat.names`/`feat.data` file, or load the development example. This path still uses the original frozen 1.0.0 classifier and its own imputer, threshold and event rules. Original numerical feature definitions are required; matching names alone do not prove compatibility. Do not upload raw-derived features in this mode to bypass the Version 2.1 route.

## Frozen routing

Raw videos go through the unchanged calibration/feature adapter and pinned tracker into `models/raw-v2.1/lunge-detector.joblib`. Before tracking starts, hashes and schema/configuration consistency are checked. Model, imputer, feature order, threshold and event rules form one bundle. No fitting, annotation loading or adaptation happens during inference. The original mode uses its separate immutable release.

## Scientific scope

Version 2.1 was selected on movie5 after training on movies1–4. The reported metrics cover selected reliable mapped intervals, not all raw-video behaviour. No fresh untouched test recording is available; movies6–10 were previously examined and excluded from this selection. Full-recording output is experimental and includes tracking identities that can switch. Require fresh independent validation before making a new generalization claim.

## Reproduction

From the workspace root:

```sh
outputs/drosophila-aggression/.venv/bin/python outputs/flyaggression-v2.1/scripts/optimize_days5_7.py --resume
outputs/drosophila-aggression/.venv/bin/python outputs/flyaggression-v2.1/scripts/verify_days5_7.py
outputs/drosophila-aggression/.venv/bin/python -m unittest discover -s outputs/flyaggression-v2.1/tests -v
```

`--resume` reuses only candidate bundles whose saved protocol and input hashes match. Without it, the three additional forests are refitted with the fixed seed. These commands overwrite development outputs, so preserve an existing frozen build before rerunning. Neither command evaluates movies6–10.
