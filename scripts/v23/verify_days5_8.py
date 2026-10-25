"""Independent final accounting, chronology, preservation and score-integrity checks."""
from pathlib import Path
import json,subprocess
import numpy as np,pandas as pd
from prepare_evaluation import ROOT,R,D,sha,save_json
from run_frozen import verify_inputs

def main():
 lockpath=ROOT/'config/v23-evaluation-lock.json';lock=json.loads(lockpath.read_text());verify_inputs(lock);inf=json.loads((R/'inference.json').read_text());assert inf['locked_protocol_sha256']==sha(lockpath) and inf['status']=='PASS';assert inf['classifier_fit_called'] is False and inf['annotations_used_for_prediction'] is False
 for p,h in inf['outputs'].items():assert sha(p)==h,p
 assert sha(ROOT/'scripts/v23/run_frozen.py')==inf['inference_code_sha256']
 config=json.loads((ROOT/'models/raw-v2.2/configuration.json').read_text());assert config['threshold']==.15 and config['event_rules']=={'median_window':3,'max_gap_frames':1,'min_event_frames':3}
 scores=pd.read_parquet(ROOT/'data/v23-predictions/probabilities.parquet');ops=pd.read_csv(R/'operational-predicted-events.csv');assert len(scores)==76780 and len(ops)==64;assert scores.probability_lunge.between(0,1).all();assert not scores.duplicated(['recording','fly_id','frame']).any()
 for _,g in scores.groupby('fly_id'):np.testing.assert_array_equal(g.frame,np.arange(1,38391))
 result=json.loads((R/'evaluation.json').read_text());checks=[]
 for tag,m in result['metrics'].items():
  base=tag.split('-common')[0];source=pd.read_csv(R/f'{base}-all-source-bouts.csv');expert=pd.read_csv(R/f'{tag}-expert-outcomes.csv');pred=pd.read_csv(R/f'{tag}-predicted-outcomes.csv');elig=pd.read_csv(R/f'{tag}-all-operational-event-eligibility.csv');matches=pd.read_csv(R/f'{tag}-matches.csv');e=m['native_time_event_metrics']
  assert len(source)==m['source_bouts'];assert len(expert)==m['retained_bouts'];assert len(expert)+m['excluded_bouts']==len(source);assert len(elig)==len(ops);assert int(elig.scorable.sum())==len(pred);assert int((~elig.scorable).sum())==m['excluded_operational_predictions'];tp=len(matches);assert tp==e['true_positive_events']==int(pred.outcome.eq('TP').sum())==int(expert.outcome.eq('matched').sum());assert len(pred)-tp==e['false_positive_events'];assert len(expert)-tp==e['false_negative_events'];assert not matches.duplicated(['recording','fly_id','pred_event_id']).any();assert not matches.duplicated(['recording','fly_id','expert_event_id']).any()
  f1=2*tp/(len(pred)+len(expert)) if len(pred)+len(expert) else 0;assert abs(f1-e['f1'])<1e-14
  checks.append({'scope':tag,'source_expert_events':len(source),'retained':len(expert),'scored_predictions':len(pred),'matches':tp,'whole_event_accounting':'PASS'})
 # Verify exact600Hz integer IoU threshold decisions match floating-time matching for these actual pairs.
 differences=0
 for tag in ['primary','secondary']:
  p=pd.read_csv(R/f'{tag}-predicted-outcomes.csv');g=pd.read_csv(R/f'{tag}-expert-outcomes.csv')
  for pr in p.itertuples():
   for gt in g[g.fly_id.eq(pr.fly_id)].itertuples():
    a,b,c,d=map(lambda t:int(round(t*600)),[pr.start_seconds,pr.stop_seconds_exclusive,gt.start_seconds,gt.stop_seconds_exclusive]);inter=max(0,min(b,d)-max(a,c));integer_allowed=10*inter>=3*(b-a+d-c-inter);overlap=max(0,min(pr.stop_seconds_exclusive,gt.stop_seconds_exclusive)-max(pr.start_seconds,gt.start_seconds));float_allowed=overlap/((pr.stop_seconds_exclusive-pr.start_seconds)+(gt.stop_seconds_exclusive-gt.start_seconds)-overlap)>=.3;differences+=int(integer_allowed!=float_allowed)
 assert differences==0
 frozen=json.loads((ROOT/'config/v23-preservation.json').read_text());v22=Path(frozen['v22_root'])
 for p,h in frozen['files'].items():assert sha(v22/p)==h
 for p,h in frozen['external'].items():assert sha(p)==h
 old=json.loads((ROOT/'config/preservation.json').read_text())
 for p,h in old['extractor_sources'].items():assert sha(p)==h
 for p,h in old['frozen_files'].items():assert sha(ROOT.parent/'drosophila-aggression/models/final-v1'/p)==h
 inherited=set(subprocess.check_output(['git','ls-tree','-r','--name-only','816f6d5'],cwd=ROOT,text=True).splitlines());changes=subprocess.check_output(['git','diff','816f6d5','--name-only'],cwd=ROOT,text=True).splitlines();assert not inherited.intersection(changes),'Inherited Days1–4 files changed'
 locked_version=json.loads(subprocess.check_output(['git','show','4025d01:config/v23-evaluation-lock.json'],cwd=ROOT,text=True));assert locked_version==lock
 assert (ROOT/'REPRODUCE-V23-DAYS5-8.md').is_file() and (ROOT/'DAYS5-8-REPORT-V23.md').is_file()
 status={'status':'PASS','protocol_lock_matches_preinference_commit':'4025d01','all_locked_inputs_and_prediction_hashes_match':True,'new_probability_rows':len(scores),'operational_events':len(ops),'accounting':checks,'integer_lattice_threshold_classification_differences':differences,'v22_tracked_files_preserved':len(frozen['files']),'original_frozen_files_preserved':len(old['frozen_files']),'inherited_v23_days1_4_files_modified':0,'model_or_threshold_tuned':False,'no_additional_model_inference_in_verifier':True};save_json(R/'final-verification.json',status);print(json.dumps(status,indent=2))
if __name__=='__main__':main()
