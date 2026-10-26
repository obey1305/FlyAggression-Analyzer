# FlyAggression Analyzer2.3 — installation

This is a local research prototype, tested on this macOS machine with Python3.12, MATLABR2026a, FFmpeg8.1.2 and the recorded Python dependency versions. MATLAB, a Python environment, FFmpeg and the large source videos are not bundled. FlyTracker native extensions are architecture-specific; other systems need recompilation and validation.

## Existing workspace

Use the new Desktop `FlyAggression Analyzer v2.3.command` launcher on localhost port8506. The default and Version2.2 launchers remain unchanged. The2.3software continues using the frozen2.2raw-video model and the original1.0MATLAB-feature model.

## Extracted package

From the extracted package root:

```sh
python3.12 -m venv drosophila-aggression/.venv
drosophila-aggression/.venv/bin/python -m pip install -r requirements-lock.txt
drosophila-aggression/.venv/bin/python verify_package.py
./Launch_Analyzer.command
```

Use `FLYAGGRESSION_PYTHON` for an existing compatible Python environment. New rectangular import accepts `FLYAGGRESSION_MATLAB`, `FLYAGGRESSION_FFMPEG` and `FLYAGGRESSION_FFPROBE` executable overrides; defaults are `/Applications/MATLAB_R2026a.app/bin/matlab`, `/opt/homebrew/bin/ffmpeg`, and `/opt/homebrew/bin/ffprobe`. The preserved legacy circular workflow expects its original MATLAB path. A licensed MATLAB installation with required image/statistics/parallel functionality is necessary for tracking. Automatic installation or licensing is not provided.

The installed application supports existing compatible MAT features and30FPS circular MP4 uploads. The new rectangular path supports tested8-bit YUV420 AVI/MP4 at constant30or200FPS. Variable/fractional rates,10-bit pixels and unsupported metadata are rejected. Uploaded videos remain limited to200MB; use a local path for large videos. Source dimensions/timestamps are validated before processing. Local input must remain available for the run.

The Boy Meets Boy source video is7.3GB and is not bundled. Provider DOI10.22002/D1.1893, [Caltech dataset record](https://data.caltech.edu/records/zrznw-w7386). Original movie5AVI MD5 is `745e2fc0094850b93ba57ebfb5ede2dc`; local source SHA256 and annotation hashes are in the research receipts. The completed demonstration exports and locked evaluation tables are included for a fast walkthrough.

Allow disk space for the source, a lossless normalized video, tracking intermediates and exports. Persistent local run folders retain logs and provenance. Archive needed outputs before manually removing your own completed run folders; never remove the original dataset or frozen release to force a rerun. The evaluation scripts' historical absolute paths identify the original research run; they require its exact data and are separate from the relocatable application.
