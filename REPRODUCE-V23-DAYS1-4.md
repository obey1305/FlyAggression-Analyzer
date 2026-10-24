# Version2.3 Days1–4 reproducibility

This separate `v2.3` worktree contains offline import/tracking tools. Existing Streamlit routing, frozen model bundles, circular calibration and MATLAB feature workflow are inherited unchanged. No new UI release or classifier evaluation is claimed in this phase.

Use the sibling `drosophila-aggression/.venv/bin/python` environment, FFmpeg at `/opt/homebrew/bin/ffmpeg`, and MATLABR2026a. Versions are recorded in `reports/v23-days1-4/environment.json`. The original video and extracted provider MATs live in sibling `new-training-data/BoyMeetsBoy`; they are read-only inputs, not copied into Git. The published provider MD5s and local SHA256s are in its `download-verification.json`.

Run from this worktree:

```sh
../drosophila-aggression/.venv/bin/python -m unittest discover -s tests/v23 -v
../drosophila-aggression/.venv/bin/python scripts/v23/inspect_dataset.py
../drosophila-aggression/.venv/bin/python scripts/v23/convert_video.py
/Applications/MATLAB_R2026a.app/bin/matlab -batch "run('scripts/v23/check_reader.m')"
/Applications/MATLAB_R2026a.app/bin/matlab -batch "run('scripts/v23/run_tracking.m')"
../drosophila-aggression/.venv/bin/python scripts/v23/audit_features.py
../drosophila-aggression/.venv/bin/python scripts/v23/verify_preservation.py
```

The converter refuses to overwrite an existing analysis MP4, and calibration refuses an existing calibration MAT. Preserve completed artifacts: use a fresh copy of the worktree/new output destinations for a new generation run. Do not delete the source AVI, provider archive, or frozen release to force a rerun. Existing generated data are ignored by Git; their hashes and paths are retained in the report receipts.

`convert_video.py` samples the integer source indices in `frame-time-map.csv`. It uses H264CRF0 at the original640×480 resolution with no image interpolation and verifies every output YUV frame against the selected source stream. The original completed conversion command predates a subsequently tested guard against an extra tail frame on other clip lengths. `tail-selection-regression.json` confirms both expressions produce exactly the same38390 indices for this recording; the completed MP4 is preserved.

`run_tracking.m` uses manual bounds[20,10,620,479],12pixels padding and the published nominal12pixels/mm. The scale is not independently measured. The resulting tracking region is[8,1,632,480]; it does not certify physical wall positions or unclipped fly bodies. Calibration uses pinned upstream parameter inference/refinement; none of these tools fits a classifier.

For a fresh native probe, run `../drosophila-aggression/.venv/bin/python scripts/v23/prepare_native_probe.py` before MATLAB. The native200FPS diagnostic is `native_with_full_background.m`. It requires the full30FPS background/calibration first and tracks a400-frame native clip at640seconds using those spatial/body parameters and200FPS temporal parameters. The failed independent short-clip calibration is retained in logs. This diagnostic is not full-record native200FPS tracking or a model evaluation.

The raw13-feature output is converted using the existing pinned36-feature adapter. Do not pass the provider's already augmented200FPS36-feature MAT through it, and do not directly feed that MAT to the frozen30FPS classifier. Its sample-based derivative windows have different physical durations. Identity correspondence and scientific feature compatibility require the audit receipts and later locked evaluation, even when names/order agree.
