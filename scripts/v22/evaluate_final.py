"""Locked retrospective comparison. No fitting or parameter selection."""
from pathlib import Path
import sys,json,hashlib
import numpy as np,pandas as pd,joblib
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT.parent/'flyaggression-v2.1';OUT=ROOT/'reports/v22-days7-10';sys.path.insert(0,str(ROOT/'scripts'))
from optimize_days5_7 import measure_frames,event_eval
from raw_release import validate_release
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 lock=json.loads((ROOT/'config/v22-evaluation-lock.json').read_text());assert lock['tuning_allowed'] is False
 for p,h in lock['model_files'].items():assert sha(p)==h,p
 path,cfg=validate_release();models={'v21':joblib.load(BASE/'models/raw-v2.1/lunge-detector.joblib'),'v22':joblib.load(path)};names=lock['features'];rows=[];conf={};coverage=[]
 for rec,scope in lock['recordings'].items():
  print('Retrospective',rec,scope,flush=True);g=pd.concat([pd.read_parquet(ROOT/f'data/v22-revised/{rec}-fly{i}.parquet') for i in [1,2]],ignore_index=True);v=pd.read_parquet(ROOT/f'reports/v22-days3-6/{rec}/evaluation-coverage.parquet').valid_for_events.to_numpy();truth=pd.read_csv(ROOT/f'reports/v22-days3-6/{rec}/expert-events.csv');mask=g.eligible.to_numpy();source=pd.read_csv(BASE/f'data/{rec}/aligned-lunge-bouts.csv');folder=OUT/'evaluation'/rec;folder.mkdir(parents=True,exist_ok=True)
  coverage.append({'recording':rec,'scope':scope,'total_fly_frame_rows':len(g),'eligible_frame_rows':int(mask.sum()),'event_scorable_rows':int(v.sum()),'source_expert_bouts':len(source),'retained_expert_bouts':len(truth),'excluded_expert_bouts':len(source)-len(truth),'bout_coverage_fraction':len(truth)/len(source)})
  common=None
  for tag,b in models.items():
   assert b['source_feature_names']==names and b['threshold']==lock['threshold'] and b['event_rules']==lock['event_rules'];p=b['pipeline'].predict_proba(g[names])[:,1]
   if common is None:common=p
   else:np.testing.assert_array_equal(common,p)
   fm=measure_frames(g.loc[mask,'target_lunge'],p[mask],b['threshold']);em,events,processed,matches,po,go=event_eval(g,p,v,truth,b['event_rules'],b['threshold']);rows.append({'recording':rec,'scope':scope,'model':tag,**{'frame_'+k:fm[k] for k in ['frames','positive_frames','precision','recall','f1']},**{'event_'+k:value for k,value in em.items()}});conf[rec+'-'+tag]=fm['confusion_matrix']
   for suffix,df in [('predicted-events',events),('matches',matches),('prediction-outcomes',po),('expert-outcomes',go)]:df.to_csv(folder/f'{tag}-{suffix}.csv',index=False)
   scores=g[['recording','fly_id','frame']].copy();scores['probability_lunge']=p;scores['eligible_frame']=mask;scores['valid_for_events']=v;scores.to_parquet(folder/f'{tag}-probabilities.parquet',index=False)
 pd.DataFrame(rows).to_csv(OUT/'performance-by-recording.csv',index=False);pd.DataFrame(coverage).to_csv(OUT/'evaluation-coverage.csv',index=False);(OUT/'frame-confusion-matrices.json').write_text(json.dumps(conf,indent=2)+'\n')
 for p,h in lock['model_files'].items():assert sha(p)==h,p
 (OUT/'evaluation-verification.json').write_text(json.dumps({'status':'PASS','protocol_sha256':sha(ROOT/'config/v22-evaluation-lock.json'),'paired_probabilities_exactly_equal':True,'model_files_unchanged':True,'model_fits':0,'independent_recordings':0,'recording_roles_explicit':True,'retrospective_movies':list(lock['recordings'])},indent=2)+'\n')
if __name__=='__main__':main()
