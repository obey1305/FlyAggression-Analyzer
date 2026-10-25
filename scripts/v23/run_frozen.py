"""Day6: single frozen full-grid prediction run, independent of annotation values."""
from pathlib import Path
from datetime import datetime,timezone
import json,sys,time
import numpy as np,pandas as pd,joblib
from prepare_evaluation import sha,save_json,ROOT,R

def verify_inputs(lock):
 for name,h in lock['input_hashes'].items():
  if not Path(name).is_file() or sha(name)!=h:raise ValueError('Locked input changed: '+name)
def claim_output(path):
 if path.exists():raise ValueError('Existing prediction run must be preserved')
 path.mkdir(parents=True)
def main():
 lockpath=ROOT/'config/v23-evaluation-lock.json';lock=json.loads(lockpath.read_text());verify_inputs(lock);assert lock['model_tuning_allowed'] is False
 dest=ROOT/'data/v23-predictions';claim_output(dest);started=time.monotonic();cfg=json.loads((ROOT/'models/raw-v2.2/configuration.json').read_text());assert cfg['threshold']==lock['threshold'] and cfg['event_rules']==lock['event_rules']
 runtime=ROOT.parent/'drosophila-aggression/models/final-v1/runtime';sys.path.insert(0,str(runtime));from scripts.lunge_pipeline import score_feature_file;from scripts.event_detection import detect_events
 bundle=joblib.load(ROOT/'models/raw-v2.2/lunge-detector.joblib');assert bundle['threshold']==lock['threshold'] and bundle['event_rules']==lock['event_rules'] and bundle['source_feature_names']==lock['feature_names'];assert bundle['feature_names']==lock['feature_names'];assert bundle['feature_engineering_version']==0
 imputer=bundle['pipeline'].named_steps['imputer'];before=imputer.statistics_.copy()
 scores,info=score_feature_file(ROOT/'data/v23-derived/features36.mat',bundle,lock['recording']);assert len(scores)==76780 and np.isfinite(scores.probability_lunge).all()
 # Exactly the frozen full-grid detector; annotation-dependent masks are not supplied.
 events,processed=detect_events(scores,fps=30,threshold=lock['threshold'],**lock['event_rules']);tech=pd.read_csv(R/'technical-coverage.csv');bits=tech.technical_eligible.to_numpy(bool);mapping=tech.mapping_state.to_numpy();scores=scores.merge(tech[['frame','technical_eligible','mapping_state','new_tracking_warning']],on='frame',validate='many_to_one')
 scores.to_parquet(dest/'probabilities.parquet',index=False);processed.to_parquet(dest/'processed-full-grid.parquet',index=False)
 events['contains_missing_features']=False;events['technical_fully_eligible']=False;events['relative_identity_stable']=False;events['reference_fly_id']=0
 for i,row in events.iterrows():
  a,b=int(row.start_frame)-1,int(row.end_frame);stream=scores[scores.fly_id.eq(row.fly_id)].reset_index(drop=True);stable=len(np.unique(mapping[a:b]))==1
  events.loc[i,'contains_missing_features']=bool(stream.had_missing_source_features.iloc[a:b].any());events.loc[i,'technical_fully_eligible']=bool(bits[a:b].all());events.loc[i,'relative_identity_stable']=stable
  if stable and bits[a:b].all():events.loc[i,'reference_fly_id']=int(row.fly_id if mapping[a]==0 else 3-row.fly_id)
 events.to_csv(R/'operational-predicted-events.csv',index=False);np.testing.assert_array_equal(before,imputer.statistics_);verify_inputs(lock)
 receipt={'status':'PASS','started_after_protocol_lock':True,'locked_protocol_sha256':sha(lockpath),'completed_utc':datetime.now(timezone.utc).isoformat(),'elapsed_seconds':time.monotonic()-started,'model_sha256':sha(ROOT/'models/raw-v2.2/lunge-detector.joblib'),'threshold':lock['threshold'],'event_rules':lock['event_rules'],'full_probability_rows':len(scores),'operational_events':len(events),'input_feature_information':info,'missing_feature_rows_scored_by_frozen_imputer':int(scores.had_missing_source_features.sum()),'preprocessing_statistics_unchanged':True,'classifier_fit_called':False,'annotations_used_for_prediction':False,'outputs':{str(p):sha(p) for p in [dest/'probabilities.parquet',dest/'processed-full-grid.parquet',R/'operational-predicted-events.csv']},'inference_code_sha256':sha(Path(__file__))}
 save_json(R/'inference.json',receipt);print(json.dumps(receipt,indent=2))
if __name__=='__main__':main()
