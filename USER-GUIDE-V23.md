# Version2.3 user guide

## Original feature analysis

Choose **MATLAB features**, upload a compatible paired-fly36-feature MAT throughv7.2, then analyse. The original frozen1.0model remains responsible. Known raw-adapter feature MATs are rejected in this mode. **Load development example** remains a known development recording, not an independent test.

## Circular raw video

Choose **Experimental raw video → Circular (30FPS MP4)**. Use the existing automatic circular calibration with a real measured diameter and boundary confirmation, or upload a matching FlyTracker calibration. Confirm experimental predictions and analyse. The frozen2.2raw-video classifier and existing reports are preserved.

## Rectangular raw video

1. Choose **Experimental raw video → Rectangular (30/200FPS)**.
2. Upload a supported AVI/MP4 up to200MB, or choose **Local file** and enter a readable path for a larger recording.
3. Click **Inspect rectangular video**. Review dimensions, nativeFPS, frame count and source image. Analysis is normalized to30FPS with an exported nearest-source frame map.
4. Enter inclusive left/top/right/bottom pixel bounds and padding. Bounds/padding define a tracking mask, not physical wall measurements. Leave outside pixels around the mask; full-image masks produce invalid wall distances and are refused.
5. Supply a positive pixels-per-millimetre value and scale evidence. The video cannot measure physical dimensions. The supplied Boy Meets Boy starter uses nominal12px/mm and manual bounds[20,10,620,479] with12px padding; those values are not universal. Select **published-nominal**, not **user-measured**, for this documented example.
6. Confirm the reviewed boundary/scale and experimental status, then analyse. The app reports processing stages and elapsed time; the indicator is not an overall completion percentage.
7. Review source/analysisFPS, scale provenance, tracking warnings, missingness, per-fly counts, durations and frequency. Identity continuity and biological accuracy are not certified. Download CSVs, graphical PNG and ZIP; rectangular exports include native-frame mapping and import/quality provenance.

Source videos are preserved. Fresh rectangular runs use a lossless30FPS analysis stream with all selected decoded pixel hashes checked. Timestamp sampling is not equivalent to preserving all short-event detail. Very short/static/poorly lit recordings may fail two-fly body/background calibration; a successful metadata inspection does not guarantee tracking success.

## Completed demonstration and external study

**Load completed starter demonstration** reads saved completed results; it does not analyse the selected input. The **Locked Boy Meets Boy external evaluation** panel concerns the original locked study only: primary9/42expert bouts and secondary32/48 retained. It is not an accuracy claim for the current video. All three primary FN counts reflect operational responses excluded at scoring boundaries.

Counts use native FlyTracker output IDs and may be affected by identity switches. Total lunge time sums fly-seconds and can include simultaneous events. Frequency uses fly-minutes. Remaining track time is not a confirmed non-aggression label. Error messages retain a run directory for inspection; failed runs are not silently replaced with a different model or reused as completed results.
