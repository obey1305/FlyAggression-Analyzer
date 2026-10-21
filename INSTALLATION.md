# FlyAggression Analyzer 2.1 — installation and use

## Existing workspace

Double-click **FlyAggression Analyzer.command** on the Desktop. It uses the existing pinned environment and opens Version 2.1 at http://127.0.0.1:8502. The original Version 2.0 launcher remains separately available. The workspace keeps the original app and frozen models intact.

## Extracted release package

The ZIP contains sibling `flyaggression-v2.1`, `drosophila-aggression` and `raw-video-integration` folders, plus examples, evidence and this guide. Keep those folders together. The portable package launcher uses port **8503** to avoid the workspace server.

### Requirements

- macOS on Apple Silicon for the included `.mexmaca64` helpers.
- Licensed MATLAB R2026a at `/Applications/MATLAB_R2026a.app/bin/matlab` with Image Processing Toolbox, Statistics and Machine Learning Toolbox, and Parallel Computing Toolbox for the tested four-worker setup.
- Python **3.12**. The tested version is 3.12.14.
- The exact Python dependencies in `requirements-lock.txt`; this includes scikit-learn 1.9.1, NumPy 2.5.4, pandas 3.0.6 and Streamlit 1.66.0.

MATLAB, its toolboxes, a Python environment and platform installers are not bundled. The included tracker source, upstream notices and native helpers are preserved; other platforms require compatible helper compilation and separate validation. Do not use a different scikit-learn version to deserialize the models without compatibility review.

### Setup

From a Terminal opened in the extracted release folder:

```sh
python3.12 -m venv drosophila-aggression/.venv
source drosophila-aggression/.venv/bin/activate
python -m pip install -r requirements-lock.txt
python verify_package.py
```

Then double-click `Launch_Analyzer.command`, or run:

```sh
zsh Launch_Analyzer.command
```

If port 8503 is occupied, stop the conflicting local server or choose another port with the direct Streamlit command. A verified existing environment can be selected for this launch only:

```sh
FLYAGGRESSION_PYTHON=/absolute/path/to/python zsh Launch_Analyzer.command
```

The relocated package was tested using the existing pinned environment. A clean dependency download/install on a separate machine was not performed. Use the integrity check before launching; missing or changed files require restoring the release.

## Analyze a raw video

1. Select **Experimental raw video** and upload an overhead, single-arena, two-fly MP4 at verified 30 fps.
2. Enter the real measured circular-arena diameter in millimetres. Select **Detect arena automatically**, inspect the red boundary and confirm it. Alternatively upload matching FlyTracker calibration.
3. Confirm experimental predictions, then click **Analyse video**.
4. Review per-fly counts, durations, frequencies and timelines; download CSV, PNG and ZIP. Expand **Analysis details** for the actual model version, threshold, event rules and model hash.

Physical millimetres cannot be inferred from pixels. The supplied benchmark movie uses a published nominal 16 mm arena, not a new individual measurement. Do not reuse16 mm for other recordings without evidence. Full movie1 calibrates automatically; its first ten seconds alone failed the two-fly reliability guard. Use the supplied matching calibration for the short excerpt demonstration. Some nominal 30 fps re-encodings can fail the inherited strict MATLAB frame-rate tolerance. Other frame rates, crowded or clipped arenas, camera motion and unverified feature definitions are unsupported.

## Analyze original MATLAB features

Select **MATLAB features**, then upload a compatible original paired-fly `feat.names`/`feat.data` MAT file, or use **Load development example**. The original 1.0.0 detector and its own imputer/settings remain selected; the known movie5 example gives 325 predicted events. MATLAB v7.3 feature uploads remain unsupported by this inference loader; export compatible v7/v7.2 features.

Known raw-adapter files carrying `feat.integration_status` are rejected in original mode. Matching36 names alone does not prove numerical compatibility, especially if provenance markers were removed.

## Results and limitations

Source frames are1-based inclusive. Event duration is `(end - start + 1)/30`. Total lunge time sums both flies; simultaneous events can overlap. Counts and labels are predictions, not confirmed biological measurements. Source IDs can switch. The reported62.32% frame F1 and75.63% event F1 are tuned movie5 development results on selected reliable intervals, not independent full-video accuracy.

The measured full movie1 run took244.8 seconds on this machine, including22.8 seconds calibration. Runtime varies with hardware, recording length and content. Failed inputs show an error; preserve logs when investigating failures. No additional classifier is trained during upload analysis.

## Provenance and licenses

`SHA256SUMS.json` records package file hashes. Both original and raw-specific models, their settings and feature ordering are included. `evidence/` contains final evaluation tables, figures and testing records. Tracker revision and helper hashes are recorded in `flyaggression-v2.1/config/toolchain.json`; Caltech FlyTracker notices and third-party licenses remain under `raw-video-integration/FlyTracker/`.

Benchmark source: https://data.caltech.edu/records/zrznw-w7386. The included movie1 and movie5 feature example are development/training data, not an untouched test set. Published nominal arena source is cited in the development reports. The release is a research prototype and must retain these provenance and limitation statements when demonstrated.
