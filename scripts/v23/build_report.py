"""Build standalone engineering audit figures and the Days1–4 technical report."""
from pathlib import Path
import json,shutil,re
import numpy as np,pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[2];R=ROOT/'reports/v23-days1-4'
def main():
 inspection=json.loads((R/'inspection-summary.json').read_text());conversion=json.loads((R/'conversion-verification.json').read_text());features=json.loads((R/'feature-compatibility.json').read_text());preserve=json.loads((R/'preservation-verification.json').read_text());reader=json.loads((R/'representative-reader-check.json').read_text());native=json.loads((R/'native-probe-result.json').read_text())
 a=pd.read_csv(R/'trajectory-comparison.csv');b=pd.read_csv(R/'lunge-time-projection.csv');dist=pd.read_csv(R/'feature-distribution-comparison.csv')
 plt.rcParams.update({'font.size':11,'axes.spines.top':False,'axes.spines.right':False})
 fig,axes=plt.subplots(2,1,figsize=(11,7),layout='constrained')
 for offset,(name,g) in zip([-.2,.2],b.groupby('annotator')):
  counts=g.sample_count.value_counts().sort_index();axes[0].bar(counts.index+offset,counts.values,width=.38,label=f'{name}: {len(g)} source bouts')
 axes[0].set(xlabel='Selected 30 FPS samples within source lunge interval',ylabel='Expert-labelled bouts',title='Temporal resolution of the two separate annotation sets');axes[0].legend();axes[0].set_ylim(bottom=0);axes[0].set_xticks(range(1,int(b.sample_count.max())+1))
 finite=a.position_error_pixels.replace([np.inf,-np.inf],np.nan);axes[1].plot((a.analysis_frame-1)/30,finite,lw=.5,color='#276978');axes[1].axhline(3,color='#b65c32',ls='--',label='Existing 3-pixel correspondence threshold');axes[1].set(xlabel='Time (seconds)',ylabel='Best-assignment maximum\nper-fly position error (pixels)',title='New 30 FPS trajectories versus sampled provider reference');axes[1].fill_between((a.analysis_frame-1)/30,0,1,where=~np.isfinite(finite),transform=axes[1].get_xaxis_transform(),color='#888888',alpha=.2,label='Missing paired positions');axes[1].set_yscale('symlog',linthresh=1);axes[1].set_ylabel('Maximum per-fly position error\n(pixels; symlog scale)');axes[1].legend();axes[1].set_ylim(bottom=0)
 fig.savefig(R/'timing-and-tracking.png',dpi=170);plt.close(fig)
 ranking=dist.groupby('feature').median_shift_training_iqr.apply(lambda s:s.abs().max()).nlargest(12).index
 fig,ax=plt.subplots(figsize=(10,6),layout='constrained');y=np.arange(len(ranking))
 for fly,offset,color in [(1,-.18,'#276978'),(2,.18,'#b65c32')]:
  vals=dist[dist.fly_id.eq(fly)].set_index('feature').reindex(ranking).median_shift_training_iqr;ax.barh(y+offset,vals,height=.34,label=f'New tracker fly {fly}',color=color)
 ax.set_yticks(y,ranking);ax.invert_yaxis();ax.axvline(0,color='#777',lw=.8);ax.set(xlabel='Median difference / frozen training-feature IQR',title='Largest descriptive feature shifts versus V2.2 training recordings');ax.legend();fig.savefig(R/'feature-shifts.png',dpi=170);plt.close(fig)
 shutil.copy2(ROOT/'data/v23-input/movie5-rectangular-calibration.mat.png',R/'rectangular-mask-preview.png');shutil.copy2(ROOT/'data/v23-input/movie5-rectangular-calibration.mat.json',R/'calibration.json')
 top=dist.assign(abs_shift=dist.median_shift_training_iqr.abs()).nlargest(5,'abs_shift');toplines='\n'.join(f"| {x.feature} | {x.fly_id} | {x.median_shift_training_iqr:.2f} | {100*x.fraction_outside_training_q01_q99:.1f}% |" for x in top.itertuples())
 missing='\n'.join(f"| {x['fly']} | {x['missing_position_frames']} | {x['longest_missing_position_gap_frames']} | {x['nonfinite_36feature_rows']} |" for x in features['missingness'])
 text=f'''# FlyAggression Analyzer2.3 — Days1–4

Completed on2026-10-24 in the separate `v2.3` worktree, based on frozen2.2 commit5f3deaf. This delivery covers dataset inspection, video/time import, rectangular calibration, full-recording tracking and36-feature extraction. It does **not** report classifier accuracy: no aggression-model inference, fitting, threshold changes or event scoring was performed.

## Day1 — Dataset verified and documented

Provider: [Caltech Fly-vs-Fly dataset](https://data.caltech.edu/records/zrznw-w7386), DOI10.22002/D1.1893, provider CC0 record. The downloaded BoyMeetsBoy archive contains annotations, reference tracks and already augmented features for six recordings; only movie5's raw video is downloaded. Movie5 was selected after inspecting lunge counts, not through random independent cohort selection. It has not influenced model training or prediction selection. Its namespace is `flyvsfly_boymeetsboy_movie5`, distinct from Aggression/movie5 used for development.

The original MJPEG AVI is640×480,200FPS,255929frames,1279.645seconds. Provider MD5s and local SHA256s match the downloaded files; extracted archive contents were verified against ZIP bytes/CRC. `dataset-inventory.json` records every available MAT's keys, shapes and hashes. Reference tracks have2×255929×17 measurements; current FlyTracker emits35 tracking measurements with a different column order. Coordinates are compared by names, not positional assumptions.

Primary expert annotations contain42lunges (fly1:1, fly2:41); the second annotator contains48 (fly1:2, fly2:46). They remain separate, not90distinct ground-truth events or a consensus. Provider viewer start:end indexing confirms1-based inclusive source-frame bounds. Biological onset/offset criteria, extra annotation-column semantics, exhaustive negatives and biological fly-identity continuity remain unverified. Extra columns are retained verbatim. No missing video files are represented as available.

## Day2 — Full import and timestamp mapping

The complete original AVI decoded all255929frames with error-abort enabled and no reported errors. All38390actual decoded analysis timestamps are strictly increasing and match the30FPS grid within0.34microseconds in FFprobe printed precision (`full-video-verification.json`). The complete deterministic30FPS stream contains38390frames at the original resolution. All38390decoded YUV frame hashes match the selected source frames. No spatial resize, frame interpolation or lossy quantization was introduced. MATLAB's actual RGB reader differed by at most{max(x['max_rgb_difference'] for x in reader)}intensity level on nine paired frames spanning the recording; exact YUV parity therefore does not imply identical RGB arrays across decoder paths.

`frame-time-map.csv` retains every source index and both timestamps. Analysis frame k, zero-based, selects `min(round(k*200/30),255928)` with integer half-up rounding. Maximum sample-time jitter is{1000*conversion['maximum_sample_time_error_seconds']:.3f}ms, with no accumulated drift. The final analysis-grid duration is21.667ms longer than source duration, less than one30FPS period; the last selected native frame is255928. Event endpoints are quantized separately: maximum observed absolute onset/stop shift is30ms, **not**1.67ms.

All42primary and48secondary lunges retain at least one sample under the predetermined phase. However18/42primary and33/48secondary bouts retain only one or two samples. The frozen event detector requires at least3frames after its unchanged smoothing/merging rules, so event loss remains a material risk; retaining one sample is not successful event detection. No threshold or sampling phase was tuned to annotations.

A native200FPS400-frame clip at640seconds completed tracking and13-feature extraction using the full-recording background/body calibration. Standalone2-second automatic calibration failed its two-fly reliability check and is documented in retained logs; full native200FPS tracking was not run. The native velocity kernel has9samples versus3at30FPS. Provider200FPS36-feature MATs cannot be assumed interchangeable with30FPS model inputs: five-sample derivative endpoints span20ms versus133.33ms. We regenerate features from30FPS trajectories instead.

An additional FFmpeg fixture exposed an extra clipped-tail frame for some shorter source lengths. The selector now rejects rounded output indices beyond the intended count; regression fixtures7,8,13,31,40frames pass. Both old and guarded selectors select exactly the same38390indices for this full recording, whose verified conversion remains preserved. An initial FFmpeg rate-mode configuration error and dependency-path error were also corrected; failed attempts remain in logs.

## Day3 — Rectangular calibration

Configurable inclusive bounds[20,10,620,479], padded12pixels and clipped to[8,1,632,480], replace circular assumptions for this offline import. The calibrated ROI uses correct row/column dimensions480×640. The pinned FlyTracker body/contrast refinement passed on the full recording; parameters are in `calibration.json`. The existing circular code was not edited.

The [published assay description](https://projet.liris.cnrs.fr/imagine/pub/proceedings/ECCV-2014/papers/8690/86900772.pdf) supplies nominal4×5cm and12pixels/mm. No per-record measurement certificate was available. The padded mask is a tracking region, not a measured physical wall. All{inspection['reference_centroids_inside_padded_mask']:,}finite reference centroids lie inside it;{inspection['reference_centroids_nonfinite']:,}reference fly/frame positions are nonfinite. Centroid containment does not prove entire fly bodies are retained: bodies near image boundaries may be clipped. Raw wall distance is excluded from the36-feature schema.

![Padded manual rectangular tracking mask](reports/v23-days1-4/rectangular-mask-preview.png)

## Day4 — Full tracking, extraction and compatibility audit

Full30FPS tracking completed for both output streams across38390frames, with missing positions and features retained rather than silently removed. Raw feature shape is2×38390×13; converted shape is2×38390×36 with the frozen bundle's exact names/order. New `features36.mat` carries the adapter provenance marker; a regression test confirms original-feature mode rejects it before classifier invocation. The original workflow and models remain unchanged.

| New fly | Missing XY frames | Longest XY gap (frames) | Nonfinite36-feature rows |
|---|---:|---:|---:|
{missing}

The longest new fly2position gap covers0–87.7seconds; the sampled reference also lacks one fly position throughout that same interval. It is not valid two-fly tracking evidence, and its presence in both outputs does not establish a newly introduced tracking failure. Elsewhere43new fly1missing frames and147new fly2missing frames occur when both reference positions are finite. `missing-data-intervals.csv` records every gap. The zero-offset trajectory comparison has the lowest median pair error among offsets−3through+3; no automatic frame shift was applied.

The pinned extractor interpolates internal tracking gaps before feature computation. Finite features can therefore conceal invalid original tracking; missingness and flags must remain part of future eligibility rules. No imputer/scaler was fitted on this dataset. Whole-recording per-fly median normalization and the original log/five-sample transforms were retained, including their offline dependence on the complete recording.

The conservative existing geometric rules find{features['conservative_geometric_mapping_reliable_frames']:,}/{features['converted_shape'][1]:,}frames ({100*features['conservative_geometric_mapping_reliable_fraction']:.2f}%) with stable correspondence to sampled reference positions. They use3pixels maximum error,4pixels assignment margin,8pixels separation,15stable frames and5frame boundary exclusion. This is relative geometric correspondence, not expert-certified biological identity. The diagnostic marks{features['new_tracking_warning_frames']:,}new tracking-warning frames and{features['reference_warning_time_bins']}reference-warning time bins. No identities were forcibly reassigned. Best-assignment changes are diagnostic, not a certified count of identity swaps. The full timeline and intervals remain inspectable in CSVs.

![Timing and reference trajectory diagnostics](reports/v23-days1-4/timing-and-tracking.png)

Training-reference comparison uses only the frozen2.2 training-recording features. It reports descriptive per-fly quantiles, median differences scaled by training IQR and fractions outside training1st–99th percentiles. It does not fit a classifier or claim distribution equivalence. Largest observed shifts:

| Feature | New fly | Median shift / training IQR | Outside training1st–99th percentiles |
|---|---:|---:|---:|
{toplines}

![Descriptive feature shifts](reports/v23-days1-4/feature-shifts.png)

Names, ordering and units are technically compatible; physical scale uncertainty, tracking/identity reliability, short-event sampling, decoder rounding and cross-dataset feature shifts remain scientific compatibility issues. Current evidence supports producing and auditing inputs; it does not establish generalization or expert-equivalent aggression measurement. Future evaluation needs locked annotation/identity/coverage rules before model predictions are examined.

## Preservation and verification

{preserve['v22_tracked_regular_files_verified']}frozen2.2tracked files,3external release/launcher artifacts,9original frozen-bundle files,6original extractor sources and{preserve['pinned_dependency_files_verified']}pinned dependency files passed hash checks. The2.2worktree remains clean. All2.3changes are additive; inherited app/model/event-rule files are unchanged. Ten new unit/integration tests, six inherited alignment tests, six MATLAB invalid-geometry cases and the saved positive mask/ROI checks passed. Read-only review identified the MAT provenance issue; it was fixed and tested. Logs preserve corrected import failures instead of treating them as successful runs.

## Reproduce and inspect

See [REPRODUCE-V23-DAYS1-4.md](REPRODUCE-V23-DAYS1-4.md), `config/v23-import.json`, `config/v23-dependencies.json` and the `reports/v23-days1-4/` receipts. Large video/tracking/feature files remain in ignored local `data/` with recorded hashes. This is an offline Days1–4 delivery, not a new Streamlit release, final model evaluation or accuracy improvement.
'''
 text=text.replace('commit5f3deaf','commit `5f3deaf`')
 parts=re.split(r'(`[^`]*`|!?\[[^\]]*\]\([^)]*\))',text)
 for i in range(0,len(parts),2):
  parts[i]=re.sub(r'(?<=[A-Za-z])(?=\d)|(?<=\d)(?=[A-Za-z])',' ',parts[i])
 text=''.join(parts).replace('V 2.2','Version 2.2').replace('D 1.1893','D1.1893').replace('MD 5 s','MD5s').replace('SHA 256 s','SHA256s').replace('CC 0','CC0')
 (ROOT/'DAYS1-4-REPORT-V23.md').write_text(text)
if __name__=='__main__':main()
