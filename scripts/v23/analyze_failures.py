"""Day8 descriptive failure evidence. Does not modify model, masks or matching rules."""
from pathlib import Path
import json
import numpy as np,pandas as pd
from scipy.io import loadmat
from prepare_evaluation import ROOT,R,D,save_json

def attainable_iou(start,end,min_frames=3):
 # Exact integer600Hz lattice: native200FPS ticks3; analysis30FPS ticks20.
 a=(int(start)-1)*3;b=int(end)*3;lo=max(0,a//20-min_frames);hi=(b+19)//20;best=0.
 for k in range(lo,hi+1):
  for j in range(k+min_frames,max(k+min_frames,hi+min_frames)+1):
   overlap=max(0,min(b,j*20)-max(a,k*20));best=max(best,overlap/(b-a+(j-k)*20-overlap))
 return best

def main():
 results=json.loads((R/'evaluation.json').read_text());p=pd.read_parquet(ROOT/'data/v23-predictions/probabilities.parquet');processed=pd.read_parquet(ROOT/'data/v23-predictions/processed-full-grid.parquet');ops=pd.read_csv(R/'operational-predicted-events.csv');beh=pd.read_csv(R/'all-source-behaviors.csv');tracking=pd.read_csv(ROOT/'reports/v23-days1-4/trajectory-comparison.csv');feat=loadmat(ROOT/'data/v23-derived/features36.mat',simplify_cells=True)['feat'];names=list(feat['names']);data=feat['data'];missed=[];false=[];temporal=[];reasons=[];feature_errors=[]
 for tag in ['primary','secondary']:
  source=pd.read_csv(R/f'{tag}-all-source-bouts.csv');other=pd.read_csv(R/(('secondary' if tag=='primary' else 'primary')+'-all-source-bouts.csv'));gt=pd.read_csv(R/f'{tag}-expert-outcomes.csv');po=pd.read_csv(R/f'{tag}-predicted-outcomes.csv')
  for row in source.itertuples():
   temporal.append({'annotator':tag,'event_id':row.event_id,'retained':row.retained,'sample_count':row.sample_count,'source_duration_seconds':row.source_duration_seconds,'maximum_possible_native_iou_given30fps_min3':attainable_iou(row.source_start_frame,row.source_end_frame)})
  counts={}
  for text in source.loc[~source.retained,'exclusion_reasons']:
   for reason in str(text).split(';'):counts[reason]=counts.get(reason,0)+1
  reasons.extend({'annotator':tag,'reason':k,'excluded_source_bouts':v,'counts_overlap':True} for k,v in counts.items())
  for row in gt[gt.outcome.eq('FN')].itertuples():
   a,b=int(row.cover_start),int(row.cover_stop);stream=p[p.fly_id.eq(row.fly_id)].reset_index(drop=True);pr=processed[processed.fly_id.eq(row.fly_id)].reset_index(drop=True);near=ops[ops.fly_id.eq(row.fly_id)].copy();overlap=np.maximum(0,np.minimum(near.stop_seconds_exclusive,row.stop_seconds_exclusive)-np.maximum(near.start_seconds,row.start_seconds));union=(near.stop_seconds_exclusive-near.start_seconds)+(row.stop_seconds_exclusive-row.start_seconds)-overlap;best=float((overlap/union).max()) if len(near) else 0.;raw_support=int(stream.probability_lunge.iloc[a:b].ge(.15).sum());event_support=int(pr.event_positive.iloc[a:b].sum())
   if best>0:diagnosis='operational prediction overlaps, but insufficient IoU or one-to-one conflict; inspect exported intervals'
   elif raw_support and not event_support:diagnosis='above-threshold sample(s) present, no final event in touched bins; temporal filtering/minimum duration implicated'
   else:diagnosis='no overlapping operational event; inspect probability and temporal context, no causal attribution'
   missed.append({'annotator':tag,'event_id':row.event_id,'fly_id':row.fly_id,'reference_fly_id':row.reference_fly_id,'start_seconds':row.start_seconds,'stop_seconds_exclusive':row.stop_seconds_exclusive,'sample_count':row.sample_count,'source_duration_seconds':row.source_duration_seconds,'max_probability_in_touched_bins':float(stream.probability_lunge.iloc[a:b].max()),'raw_threshold_positive_touched_bins':raw_support,'final_event_positive_touched_bins':event_support,'best_operational_native_iou':best,'maximum_attainable_native_iou':attainable_iou(row.source_start_frame,row.source_end_frame),'max_reference_position_error_in_bins':float(tracking.position_error_pixels.iloc[a:b].max()),'diagnostic_evidence':diagnosis})
  for row in po[po.outcome.eq('FP')].itertuples():
   op=ops[(ops.fly_id==row.fly_id)&(ops.event_id==row.event_id)].iloc[0];ref=int(op.reference_fly_id);otherover=other[(other.reference_fly_id==ref)&(other.start_seconds<row.stop_seconds_exclusive)&(other.stop_seconds_exclusive>row.start_seconds)];labels=beh[(beh.annotator==tag)&(beh.reference_fly_id==ref)&(beh.behavior!='lunge')&(beh.start_seconds<row.stop_seconds_exclusive)&(beh.stop_seconds_exclusive>row.start_seconds)]
   false.append({'annotator':tag,'operational_event_id':row.event_id,'fly_id':row.fly_id,'reference_fly_id':ref,'start_seconds':row.start_seconds,'stop_seconds_exclusive':row.stop_seconds_exclusive,'duration_seconds':row.duration_seconds,'overlaps_other_annotator_lunge':bool(len(otherover)),'overlapping_other_behaviors':';'.join(sorted(labels.behavior.unique())),'interpretation':'unmatched provided lunge annotation; other behaviours/absence of labels do not independently certify a biological false positive'})
  outcomes=pd.read_parquet(D/f'{tag}-frame-outcomes.parquet')
  for fly in (1,2):
   f=outcomes[outcomes.fly_id.eq(fly)].reset_index(drop=True)
   for outcome in ['TP','FP','FN','TN']:
    chosen=f.frame_outcome.eq(outcome).to_numpy();x=data[fly-1,chosen]
    if len(x):
     med=np.nanmedian(x,axis=0)
     feature_errors.extend({'annotator':tag,'fly_id':fly,'frame_outcome':outcome,'feature':name,'rows':len(x),'median':float(med[j]) if np.isfinite(med[j]) else None} for j,name in enumerate(names))
 pd.DataFrame(missed).to_csv(R/'missed-event-diagnostics.csv',index=False);pd.DataFrame(false).to_csv(R/'unmatched-prediction-diagnostics.csv',index=False);pd.DataFrame(temporal).to_csv(R/'temporal-resolution-limits.csv',index=False);pd.DataFrame(reasons).to_csv(R/'exclusion-reason-counts.csv',index=False);pd.DataFrame(feature_errors).to_csv(R/'feature-error-medians.csv',index=False)
 summary={'operational_events':len(ops),'operational_events_touching_imputed_features':int(ops.contains_missing_features.sum()),'operational_events_not_fully_technical_eligible':int((~ops.technical_fully_eligible).sum()),'per_annotator':{}}
 for tag in ['primary','secondary']:
  t=pd.DataFrame(temporal).query('annotator==@tag');fn=pd.DataFrame(missed).query('annotator==@tag');fp=pd.DataFrame(false).query('annotator==@tag');summary['per_annotator'][tag]={'source_events_with_at_most2selected_samples':int(t.sample_count.le(2).sum()),'source_events_unmatchable_at_native_iou03_even_with_optimal30fps_min3':int(t.maximum_possible_native_iou_given30fps_min3.lt(.3).sum()),'retained_events_unmatchable_at_native_iou03':int((t.retained&t.maximum_possible_native_iou_given30fps_min3.lt(.3)).sum()),'missed_retained_events':len(fn),'missed_retained_events_with_at_most2selected_samples':int(fn.sample_count.le(2).sum()),'unmatched_predictions':len(fp),'unmatched_overlapping_other_annotator_lunge':int(fp.overlaps_other_annotator_lunge.sum()),'unmatched_overlapping_nonlunge_behaviour_label':int(fp.overlapping_other_behaviors.fillna('').ne('').sum())}
 summary['evidence_supported']='Coverage is restricted; native-to30FPS temporal quantization changes matching; common-mask annotator metrics can separate coverage effects; descriptive feature shifts exist. None isolates a causal effect of tracking vs feature differences vs classifier.';summary['primary_limitation']='Scientific interpretation is constrained first by annotation/identity/coverage. Within retained intervals, short event timing and extra predicted support reduce frame precision. Cross-dataset classifier/feature shift remains a plausible contributor, not causally established.';summary['prohibited_claims']=['whole-recording75%F1','expert-equivalent measurements','proof of causal failure mode','model improvement from test-data tuning'];save_json(R/'failure-analysis.json',summary);print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
