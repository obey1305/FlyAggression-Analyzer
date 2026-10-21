"""Rerun frozen inference only on movie5; no fitting or selection permitted."""
from pathlib import Path
import sys,json,subprocess,hashlib
import numpy as np,pandas as pd
from optimize_days5_7 import event_reference,event_eval,measure_frames
from audit_quantification import audit_tables
from raw_release import validate_release
ROOT=Path(__file__).resolve().parents[1];OLD=ROOT.parent/'drosophila-aggression/models/final-v1';DEST=ROOT/'reports/day10'
def main():
 DEST.mkdir(exist_ok=True);model,cfg=validate_release();g=pd.concat([pd.read_parquet(ROOT/f'data/movie5/full-grid-fly{i}.parquet') for i in [1,2]],ignore_index=True);valid,truth=event_reference(g,pd.read_csv(ROOT/'data/movie5/aligned-lunge-bouts.csv'));truth.to_csv(DEST/'expert-events.csv',index=False);rows=[];cms={}
 for tag,path,threshold,rules in [('Version 2.0',OLD/'lunge-detector.joblib',.5,{'median_window':3,'max_gap_frames':1,'min_event_frames':2}),('Version 2.1',model,cfg['threshold'],cfg['event_rules'])]:
  output=DEST/tag.replace(' ','-');subprocess.run([sys.executable,str(OLD/'runtime/analyze.py'),'--input',str(ROOT/'data/movie5/features36.mat'),'--output-dir',str(output),'--model',str(path),'--fps','30','--recording-id','movie5'],check=True,capture_output=True,text=True)
  scores=pd.read_csv(output/'frame-predictions.csv');np.testing.assert_array_equal(scores[['fly_id','frame']],g[['fly_id','frame']]);p=scores.probability_lunge.to_numpy();m=g.eligible.to_numpy(bool);fm=measure_frames(g.loc[m,'target_lunge'],p[m],threshold);em,pred,processed,matches,po,go=event_eval(g,p,valid,truth,rules,threshold)
  audit_tables(scores,pd.read_csv(output/'lunge-events.csv'),pd.read_csv(output/'summary-by-fly.csv'),pd.read_csv(output/'summary-by-recording.csv'))
  previous=pd.read_parquet(ROOT/f"reports/days5-7/movie5/{'original' if tag=='Version 2.0' else 'selected'}-full-grid-probabilities.parquet");np.testing.assert_allclose(p,previous.probability_lunge,rtol=0,atol=1e-14)
  for name,df in [('evaluation-events',pred),('evaluation-matches',matches),('prediction-outcomes',po),('expert-outcomes',go)]:df.to_csv(output/(name+'.csv'),index=False)
  manifest=json.loads((output/'run-manifest.json').read_text());assert not manifest['annotation_files_read'];assert manifest['model_sha256']==hashlib.sha256(path.read_bytes()).hexdigest()
  rows.append({'model':tag,'recording':'movie5','scope':'tuned development validation, not independent final test','frame_rows':int(m.sum()),'positive_frames':int(g.loc[m,'target_lunge'].sum()),'event_scorable_rows':int(valid.sum()),'threshold':threshold,**{'frame_'+k:fm[k] for k in ['precision','recall','f1','average_precision']},**{'event_'+k:em[k] for k in em},'model_sha256':manifest['model_sha256']});cms[tag]=fm['confusion_matrix']
 pd.DataFrame(rows).to_csv(DEST/'final-performance.csv',index=False);(DEST/'frame-confusion-matrices.json').write_text(json.dumps(cms,indent=2));(DEST/'verification.json').write_text(json.dumps({'status':'PASS','fresh_frozen_inference_runs':2,'fitting_performed':False,'settings_changed':False,'identical_features_and_coverage':True,'probabilities_reproduce_frozen_development_artifacts':True,'full_grid_rows_per_model':108000,'frame_scorable_rows':int(m.sum()),'event_scorable_rows':int(valid.sum()),'whole_expert_events':len(truth),'independent_final_test':False},indent=2));print(pd.DataFrame(rows).to_string(index=False))
if __name__=='__main__':main()
