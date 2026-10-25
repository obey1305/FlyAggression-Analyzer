"""Day7: fixed predictions scored against the pre-inference locked eligibility protocol."""
from pathlib import Path
import json,sys
import numpy as np,pandas as pd
from sklearn.metrics import confusion_matrix,precision_score,recall_score,f1_score
from evaluation_core import whole_prediction,match_time
from prepare_evaluation import ROOT,R,D,sha,save_json
from run_frozen import verify_inputs

def frame_metrics(y,p):
 y=np.asarray(y,int);p=np.asarray(p,bool)
 return {'rows':len(y),'positive_labels':int(y.sum()),'positive_predictions':int(p.sum()),'confusion_matrix_TN_FP_FN_TP':confusion_matrix(y,p,labels=[0,1]).tolist(),'precision':float(precision_score(y,p,zero_division=0)),'recall':float(recall_score(y,p,zero_division=0)),'f1':float(f1_score(y,p,zero_division=0)),'scientific_status':'conditional on exhaustive supplied lunge labels, not confirmed expert negatives'}
def evaluate(tag,grid,truth,operational,scores,lock):
 one=grid[grid.fly_id.eq(1)].sort_values('frame');mask=one.eligible.to_numpy(bool);mapping=one.mapping_state.to_numpy();pred=operational.copy();keep=[];reasons=[]
 for row in pred.itertuples():
  ok,why=whole_prediction(row.start_frame,row.end_frame,mask,mapping);keep.append(ok);reasons.append(why)
 pred['scorable']=keep;pred['exclusion_reason']=reasons;pred.to_csv(R/f'{tag}-all-operational-event-eligibility.csv',index=False);scorable=pred[pred.scorable].copy()
 metrics,matches,po,go=match_time(scorable,truth,lock['event_iou'])
 for suffix,df in [('matches',matches),('predicted-outcomes',po),('expert-outcomes',go)]:df.to_csv(R/f'{tag}-{suffix}.csv',index=False)
 # Secondary sensitivity preserves source endpoints projected to selected analysis samples.
 projected=truth.copy();projected['start_seconds']=(projected.analysis_start_frame-1)/30;projected['stop_seconds_exclusive']=projected.analysis_end_frame/30
 sensitivity,*_=match_time(scorable,projected,lock['event_iou'])
 q=grid.merge(scores[['recording','fly_id','frame','probability_lunge']],on=['recording','fly_id','frame'],validate='one_to_one');valid=q.eligible.to_numpy(bool);fm=frame_metrics(q.loc[valid,'target_lunge'],q.loc[valid,'probability_lunge']>=lock['threshold'])
 q['threshold_prediction']=q.probability_lunge.ge(lock['threshold']);q['frame_outcome']=np.where(~valid,'excluded',np.where(q.target_lunge.eq(1),np.where(q.threshold_prediction,'TP','FN'),np.where(q.threshold_prediction,'FP','TN')));q.to_parquet(D/f'{tag}-frame-outcomes.parquet',index=False)
 per_fly=[]
 for fly in (1,2):
  em,*_=match_time(scorable[scorable.fly_id.eq(fly)],truth[truth.fly_id.eq(fly)],lock['event_iou']);fg=q[q.fly_id.eq(fly)&q.eligible];per_fly.append({'fly_id':fly,'events':em,'frames':frame_metrics(fg.target_lunge,fg.threshold_prediction)})
 timing={key:{'median':float(matches[key].median()),'median_absolute':float(matches[key].abs().median()),'min':float(matches[key].min()),'max':float(matches[key].max())} for key in ['onset_error_seconds','offset_error_seconds','duration_error_seconds']} if len(matches) else None
 fragmented=0;merged=0
 for row in truth.itertuples():
  pp=scorable[scorable.fly_id.eq(row.fly_id)];fragmented+=int(((pp.start_seconds<row.stop_seconds_exclusive)&(pp.stop_seconds_exclusive>row.start_seconds)).sum()>1)
 for row in scorable.itertuples():
  gt=truth[truth.fly_id.eq(row.fly_id)];merged+=int(((gt.start_seconds<row.stop_seconds_exclusive)&(gt.stop_seconds_exclusive>row.start_seconds)).sum()>1)
 all_source=pd.read_csv(R/f'{tag.split("-common")[0]}-all-source-bouts.csv');assert metrics['true_positive_events']+metrics['false_negative_events']==len(truth);assert metrics['true_positive_events']+metrics['false_positive_events']==len(scorable);assert len(scorable)+int((~pred.scorable).sum())==len(operational)
 return {'annotator':tag,'source_bouts':len(all_source),'retained_bouts':len(truth),'excluded_bouts':len(all_source)-len(truth),'expert_bout_coverage':len(truth)/len(all_source),'operational_predictions':len(operational),'excluded_operational_predictions':int((~pred.scorable).sum()),'scorable_analysis_frames':int(mask.sum()),'scorable_fly_frame_rows':int(valid.sum()),'native_time_event_metrics':metrics,'projected_grid_sensitivity':sensitivity,'conditional_frame_metrics':fm,'per_fly':per_fly,'timing_errors_seconds':timing,'fragmented_expert_intervals':fragmented,'predictions_overlapping_multiple_expert_intervals':merged}
def main():
 lockpath=ROOT/'config/v23-evaluation-lock.json';lock=json.loads(lockpath.read_text());verify_inputs(lock);receipt=json.loads((R/'inference.json').read_text());assert receipt['status']=='PASS' and receipt['locked_protocol_sha256']==sha(lockpath)
 for p,h in receipt['outputs'].items():assert sha(p)==h
 scores=pd.read_parquet(ROOT/'data/v23-predictions/probabilities.parquet');operational=pd.read_csv(R/'operational-predicted-events.csv');out={};grids={};truths={}
 for tag in ['primary','secondary']:
  grids[tag]=pd.read_parquet(D/f'{tag}-grid.parquet');truths[tag]=pd.read_csv(R/f'{tag}-expert-events.csv');out[tag]=evaluate(tag,grids[tag],truths[tag],operational,scores,lock)
 common=grids['primary'].eligible.to_numpy()&grids['secondary'].eligible.to_numpy();base=common[:38390];mapping=grids['primary'].mapping_state.to_numpy()[:38390]
 # Remove complete truth intervals that touch the common-mask boundary, then close across both annotators.
 from evaluation_core import close_coverage
 joined=pd.concat([truths['primary'].assign(annotation='primary'),truths['secondary'].assign(annotation='secondary')],ignore_index=True);bounds=joined[['cover_start','cover_stop']].to_numpy(int);base,kept=close_coverage(base,bounds,np.ones(len(joined),bool))
 for tag in ['primary','secondary']:
  grid=grids[tag].copy();grid['eligible']=np.tile(base,2);grid.loc[~grid.eligible,'target_lunge']=-1;truth=joined[(joined.annotation==tag)&kept].drop(columns='annotation');out[tag+'-common']=evaluate(tag+'-common',grid,truth,operational,scores,lock)
 # Annotator disagreement is descriptive and keeps original reference IDs, with native timing.
 aa=pd.read_csv(R/'primary-all-source-bouts.csv');bb=pd.read_csv(R/'secondary-all-source-bouts.csv')
 for df in (aa,bb):df['fly_id']=df.reference_fly_id
 agreement,am,ap,ag=match_time(aa,bb,lock['event_iou']);am.to_csv(R/'annotator-agreement-matches.csv',index=False);ap.to_csv(R/'primary-vs-secondary-outcomes.csv',index=False);ag.to_csv(R/'secondary-vs-primary-outcomes.csv',index=False)
 result={'scope':lock['scope'],'protocol_sha256':sha(lockpath),'model_tuned':False,'metrics':out,'annotation_agreement_asymmetric_primary_predictions_secondary_reference':agreement,'annotation_agreement_warning':'Agreement describes two annotation sets, not an adjudicated ground truth or expert accuracy.'};save_json(R/'evaluation.json',result);verify_inputs(lock)
 print(json.dumps({k:{'coverage':v['expert_bout_coverage'],'event':v['native_time_event_metrics'],'frame':v['conditional_frame_metrics']} for k,v in out.items()},indent=2))
if __name__=='__main__':main()
