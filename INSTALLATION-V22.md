# Version 2.2 research prototype — installation and use

This release preserves the original feature classifier and adds a separately frozen Version 2.2 raw-video model. Version 2.2 reproduces Version 2.1 predictions on the evaluated grids. No biological accuracy or identity improvement has been established.

## Existing workspace

Use the separate Desktop `FlyAggression Analyzer v2.2.command` launcher. It opens the Version 2.2 worktree on localhost port 8504. The existing default Version 2.1 Desktop launcher remains unchanged.

## Extracted research package

Requires macOS, a licensed compatible MATLAB installation (tested R2026a), Python 3.12, and the pinned Python dependencies. MATLAB and a Python environment are not bundled. The included FlyTracker native extensions were tested on this Mac; other platforms/architectures may need recompilation and revalidation. No automatic installation or license bypass is provided.

From the extracted package root, create `drosophila-aggression/.venv`, install the root `requirements-lock.txt`, then run `verify_package.py` with that environment. Set `FLYAGGRESSION_PYTHON` to another compatible environment if necessary and use `Launch_Analyzer.command`. Package launch uses localhost port 8505. The tracker currently expects `/Applications/MATLAB_R2026a.app/bin/matlab`; adapting that path requires revalidation.

```sh
python3.12 -m venv drosophila-aggression/.venv
drosophila-aggression/.venv/bin/python -m pip install -r requirements-lock.txt
drosophila-aggression/.venv/bin/python verify_package.py
./Launch_Analyzer.command
```

## Original MATLAB feature workflow

Choose MATLAB features, upload a compatible original two-fly × consecutive-frame × 36-feature MAT (through v7.2), then Analyse uploaded file. Known adapter-produced MAT files are rejected in this mode. The frozen original model and preprocessing remain responsible for this workflow. The development example is movie5, not independent test data.

## Raw MP4 workflow

Choose Experimental raw video. Supply a compatible 30 FPS, two-fly MP4 and either a matching FlyTracker calibration MAT or a physically measured circular-arena diameter for automatic geometry detection. Automatic detection cannot measure millimetres from pixels. Confirm the boundary preview and experimental-results acknowledgement, then Analyse video.

The packaged benchmark demo uses a published nominal 16 mm value with explicit uncertainty, not a new physical measurement. For your own recordings, obtain the real experimental diameter; do not transfer this nominal value blindly. The first300-frame example can be analysed using the packaged full-movie calibration; this is a matching geometry demo, not a claim that short clips always support automatic calibration.

The UI reports stage/elapsed-time progress, not a reliable completion percentage. Download CSV tables, graphical PNG and all-results ZIP. Counts refer to native source fly IDs, which can switch. Sum of fly durations is fly-seconds and may exceed simultaneous wall-clock time. The report frequency denominator is fly-minutes.

## Limitations

One circular arena, two flies, 30 FPS and readable MP4 are the tested conditions; uploads have a 200 MB UI limit and processing a 30-minute timeout. Arena quality, lighting, overlap, orientation and identity ambiguity can degrade results. No new independent expert-labelled recordings were available. Retrospective accuracy concerns a restricted reliably aligned subset, not complete-video biological accuracy.
