"""Independent checks, timing diagnostics and scientific figures for Days3–6."""
from pathlib import Path
import sys,json,hashlib
import numpy as np,pandas as pd,joblib,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.io import loadmat
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT.parent/'flyaggression-v2.1';OUT=ROOT/'reports/v22-days3-6';sys.path.insert(0,str(ROOT/'scripts/v22'))
from days3_6 import boundary_labels,annotation_labels,SOURCE,sha,validate_dataset,event_eval

def main():
 names=json.loads((BASE/'config/feature-columns.json').read_text());cal=pd.read_csv(OUT/'calibration-audit.csv');profiles=pd.read_csv(OUT/'feature-distributions.csv');sens=pd.read_csv(OUT/'scale-sensitivity.csv');a=pd.read_csv(OUT/'alignment-summary.csv');r=json.loads((OUT/'results.json').read_text());protocol=json.loads((ROOT/'config/v22-days3-6.json').read_text());source_manifest={}
 for item in json.loads((BASE/'config/source-inventory.json').read_text()):
  if item['recording'] not in protocol['training_recordings']+protocol['selection_recordings']:continue
  for suffix,info in item['files'].items():assert sha(info['path'])==info['sha256'];source_manifest[info['path']]=info['sha256']
 for rec in a.recording:
  src=loadmat(SOURCE/rec/(rec+'_actions.mat'),simplify_cells=True);actual=annotation_labels(src,54000)
  for ref in [0,1]:
   lunge=np.asarray(src['bouts'][ref,list(src['behs']).index('lunge')]).reshape(-1,3);independent=boundary_labels(54000,lunge)
   for j,behavior in enumerate(src['behs']):
    for start,end,flag in np.asarray(src['bouts'][ref,j]).reshape(-1,3):
     if behavior=='unknown' or flag!=0:independent[int(start)-1:int(end)]=-1
   np.testing.assert_array_equal(independent,actual[ref])
  for fly in [1,2]:
   fresh=pd.read_parquet(ROOT/f'data/v22-revised/{rec}-fly{fly}.parquet');old=pd.read_parquet(BASE/f'data/{rec}/full-grid-fly{fly}.parquet');pd.testing.assert_frame_equal(fresh,old)
  oldcov=pd.read_parquet(BASE/f'reports/days5-7/{rec}/evaluation-coverage.parquet');newcov=pd.read_parquet(OUT/rec/'evaluation-coverage.parquet');np.testing.assert_array_equal(oldcov.valid_for_events,newcov.valid_for_events)
  oldtruth=pd.read_csv(BASE/f'reports/days5-7/{rec}/expert-events.csv');newtruth=pd.read_csv(OUT/rec/'expert-events.csv');pd.testing.assert_frame_equal(oldtruth,newtruth)
 train=pd.read_parquet(ROOT/'data/v22-revised/train.parquet');val=pd.read_parquet(ROOT/'data/v22-revised/validation.parquet');validate_dataset(train,val,names)
 for name,h in json.loads((OUT/'dataset-manifest.json').read_text()).items():assert sha(ROOT/name)==h
 modeldir=ROOT/'models/raw-v2.2-candidate'
 for name,h in json.loads((modeldir/'freeze-manifest.json').read_text())['files'].items():assert sha(modeldir/name)==h
 model=joblib.load(modeldir/'lunge-detector.joblib');baseline=joblib.load(BASE/'models/raw-v2.1/lunge-detector.joblib');assert model['pipeline'] is not baseline['pipeline'];np.testing.assert_array_equal(model['pipeline'].named_steps['imputer'].statistics_,np.median(train[names],axis=0))
 params=model['pipeline'].named_steps['classifier'].get_params();(OUT/'estimator-parameters.json').write_text(json.dumps(params,indent=2)+'\n')
 g=pd.concat([pd.read_parquet(ROOT/f'data/v22-revised/movie5-fly{i}.parquet') for i in [1,2]],ignore_index=True);scores=pd.read_parquet(OUT/'movie5-probabilities.parquet');p=model['pipeline'].predict_proba(g[names])[:,1];np.testing.assert_allclose(p,scores.candidate_probability,atol=1e-14,rtol=0)
 coverage=pd.read_parquet(OUT/'movie5/evaluation-coverage.parquet');truth=pd.read_csv(OUT/'movie5/expert-events.csv');em,pred,processed,matches,po,go=event_eval(g,p,coverage.valid_for_events.to_numpy(),truth,model['event_rules'],model['threshold']);saved=pd.read_csv(OUT/'comparison.csv').set_index('model').loc['candidate']
 for key in ['precision','recall','f1']:assert abs(em[key]-saved['event_'+key])<1e-12
 # Add explicit matched offsets and overlap topology. Errors: prediction minus expert, in frames.
 timing=matches.copy();timing['offset_error_frames']=timing.onset_error_frames+timing.duration_error_frames;timing.to_csv(OUT/'matched-timing-errors.csv',index=False)
 diag={'matched_events':len(timing),'median_onset_error_frames':float(timing.onset_error_frames.median()),'median_absolute_onset_error_frames':float(timing.onset_error_frames.abs().median()),'median_offset_error_frames':float(timing.offset_error_frames.median()),'median_absolute_offset_error_frames':float(timing.offset_error_frames.abs().median()),'predicted_duration_quantiles_frames':{str(q):float(pred.duration_frames.quantile(q)) for q in [0,.25,.5,.75,1]},'predictions_overlapping_multiple_expert_bouts':sum(int(((truth.fly_id==x.fly_id)&(truth.start_frame<=x.end_frame)&(truth.end_frame>=x.start_frame)).sum()>1) for x in pred.itertuples()),'expert_bouts_overlapping_multiple_predictions':em['fragmented_expert_events'],'false_positive_events':em['false_positive_events'],'missed_expert_events':em['false_negative_events'],'caution':'overlap topology does not establish biological fragmentation or merging; coverage is restricted'}
 fp=po[po.outcome.eq('FP')].copy();fn=go[go.outcome.eq('FN')].copy();fn['duration_frames']=fn.end_frame-fn.start_frame+1
 fp.to_csv(OUT/'false-positive-review.csv',index=False);fn.to_csv(OUT/'missed-event-review.csv',index=False)
 diag['false_positive_duration_counts']=fp.duration_frames.value_counts().sort_index().to_dict();diag['missed_expert_duration_counts']=fn.duration_frames.value_counts().sort_index().to_dict();diag['false_positives_overlapping_retained_expert']=int(fp.overlaps_any_expert.sum());diag['missed_experts_overlapping_prediction']=int(fn.overlaps_any_prediction.sum())
 (OUT/'temporal-diagnostics.json').write_text(json.dumps(diag,indent=2)+'\n')
 # Across-record median shifts use pooled within-record IQR as descriptive denominator.
 shift=profiles.copy();shift['iqr']=shift.q75-shift.q25;centers=shift.groupby('feature')['median'].median();scales=shift.groupby('feature').iqr.median();shift['median_shift_record_iqr']=[(row['median']-centers[row['feature']])/max(scales[row['feature']],1e-12) for _,row in shift.iterrows()];shift.to_csv(OUT/'feature-shift-summary.csv',index=False)
 plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
 fig,ax=plt.subplots(figsize=(9,11));matrix=shift.pivot(index='feature',columns='recording',values='median_shift_record_iqr').reindex(names);im=ax.imshow(matrix,aspect='auto',cmap='RdBu_r',vmin=-2,vmax=2);ax.set_yticks(range(36),names);ax.set_xticks(range(5),matrix.columns);ax.set_title('Feature medians across recordings\nRelative to median recording; within-record IQR denominator');fig.colorbar(im,ax=ax,label='Descriptive shift (clipped colour at ±2)');fig.tight_layout();fig.savefig(OUT/'feature-consistency.png',dpi=170);plt.close(fig)
 ss=sens.groupby('feature').median_absolute_change_over_baseline_iqr.max().reindex(names);ss=ss[ss>1e-10].sort_values();fig,ax=plt.subplots(figsize=(9,6));ax.barh(ss.index,ss);ax.set_xlabel('Maximum median absolute change / baseline IQR');ax.set_title('Hypothetical diameter ±10% · fixed tracks\nScale sensitivity, not measured calibration correction');fig.tight_layout();fig.savefig(OUT/'scale-sensitivity.png',dpi=170);plt.close(fig)
 fig,axes=plt.subplots(2,1,figsize=(12,5),sharex=True)
 for fly,ax in zip([1,2],axes):
  for x in truth[truth.fly_id.eq(fly)].itertuples():ax.broken_barh([((x.start_frame-1)/30,(x.end_frame-x.start_frame+1)/30)],(.6,.25),facecolors='#3466a0')
  for x in pred[pred.fly_id.eq(fly)].itertuples():ax.broken_barh([((x.start_frame-1)/30,x.duration_frames/30)],(.1,.25),facecolors='#bd7918')
  ax.set_yticks([.22,.72],['Candidate','Expert']);ax.set_title(f'Movie5 source fly {fly} · restricted scorable intervals');ax.set_xlim(0,1800)
 axes[-1].set_xlabel('Seconds from recording start');fig.tight_layout();fig.savefig(OUT/'development-event-timeline.png',dpi=170);plt.close(fig)
 result={'status':'PASS','source_files_verified':len(source_manifest),'annotation_boundary_rows_verified':540000,'revised_full_grid_identical_to_v21':True,'frame_and_event_coverage_identical_to_v21':True,'source_bouts':int(a.source_bouts.sum()),'retained_bouts':int(a.retained_expert_bouts.sum()),'recovered_bouts':int(a.recovered_bouts.sum()),'training_only_imputer_verified':True,'serialized_candidate_probabilities_verified':True,'event_metrics_recomputed':True,'physical_diameter_independently_verified':False}
 (OUT/'source-manifest.json').write_text(json.dumps(source_manifest,indent=2)+'\n');(OUT/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
