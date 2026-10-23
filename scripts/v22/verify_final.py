"""Final preservation, retrospective metrics, fresh-run measurement and package audit."""
from pathlib import Path
import sys,json,subprocess,hashlib,zipfile,io
import numpy as np,pandas as pd,joblib
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'reports/v22-days7-10';BASE=ROOT.parent/'flyaggression-v2.1';P=ROOT.parent/'drosophila-aggression';PACKAGE=ROOT.parent/'FlyAggression-Analyzer-v2.2-Release';sys.path.insert(0,str(ROOT/'scripts'));sys.path.insert(0,str(P))
from raw_release import validate_release
from audit_quantification import audit_tables
from sklearn.metrics import confusion_matrix,precision_score,recall_score,f1_score
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 preservation=json.loads((ROOT/'config/v22-preservation.json').read_text())
 for n,h in preservation['v21_files'].items():assert sha(BASE/n)==h,n
 for n,h in preservation['external_files'].items():assert sha(n)==h,n
 assert not subprocess.check_output(['git','-C',str(BASE),'status','--porcelain'],text=True).strip()
 original=json.loads((BASE/'config/preservation.json').read_text())
 for n,h in original['frozen_files'].items():assert sha(P/'models/final-v1'/n)==h,n
 for n,h in original['extractor_sources'].items():assert sha(n)==h,n
 lock=json.loads((ROOT/'config/v22-evaluation-lock.json').read_text());assert lock['tuning_allowed'] is False and not lock['independent_recordings']
 for n,h in lock['model_files'].items():assert sha(n)==h,n
 assert (ROOT/'config/v22-evaluation-lock.json').stat().st_mtime<(OUT/'performance-by-recording.csv').stat().st_mtime
 _,cfg=validate_release();assert cfg['release_version']=='2.2.0'
 rows=pd.read_csv(OUT/'performance-by-recording.csv');coverage=pd.read_csv(OUT/'evaluation-coverage.csv');assert coverage.source_expert_bouts.sum()==1528 and coverage.retained_expert_bouts.sum()==761
 for rec in lock['recordings']:
  grid=pd.concat([pd.read_parquet(ROOT/f'data/v22-revised/{rec}-fly{i}.parquet') for i in [1,2]],ignore_index=True);a=pd.read_parquet(OUT/f'evaluation/{rec}/v21-probabilities.parquet');b=pd.read_parquet(OUT/f'evaluation/{rec}/v22-probabilities.parquet');pd.testing.assert_frame_equal(a,b);mask=grid.eligible.to_numpy();y=grid.loc[mask,'target_lunge'].to_numpy();pred=b.loc[mask,'probability_lunge'].to_numpy()>=.15;row=rows[rows.recording.eq(rec)&rows.model.eq('v22')].iloc[0]
  for k,fn in [('precision',precision_score),('recall',recall_score),('f1',f1_score)]:assert abs(fn(y,pred)-row['frame_'+k])<1e-12
  assert row.scope==lock['recordings'][rec]
  matches=pd.read_csv(OUT/f'evaluation/{rec}/v22-matches.csv');events=pd.read_csv(OUT/f'evaluation/{rec}/v22-predicted-events.csv');truth=pd.read_csv(ROOT/f'reports/v22-days3-6/{rec}/expert-events.csv');tp=len(matches);fp=len(events)-tp;fn=len(truth)-tp;assert [tp,fp,fn]==[row.event_true_positive_events,row.event_false_positive_events,row.event_false_negative_events]
 demo=OUT/'full-movie1';run=demo/'run/experimental-results';proof=json.loads((demo/'verification.json').read_text());integration=json.loads((demo/'run/integration-manifest.json').read_text());assert integration['status']=='complete' and integration['model_release']['model_sha256']==cfg['model_sha256'];assert proof['inference_annotation_files_read'] is False
 audit=audit_tables(pd.read_csv(run/'frame-predictions.csv'),pd.read_csv(run/'lunge-events.csv'),pd.read_csv(run/'summary-by-fly.csv'),pd.read_csv(run/'summary-by-recording.csv'));assert audit==proof['audit']
 for n in ['frame-predictions.csv','lunge-events.csv']:pd.testing.assert_frame_equal(pd.read_csv(run/n),pd.read_csv(demo/'baseline-paired-results'/n))
 assert json.loads((OUT/'upload-smoke/verification.json').read_text())['actual_upload_service_success']
 invalid=json.loads((OUT/'invalid-input-results.json').read_text());assert len(invalid['cases'])==9 and all(x['status']=='PASS' for x in invalid['cases'])
 sums=json.loads((PACKAGE/'SHA256SUMS.json').read_text())
 for n,h in sums.items():assert sha(PACKAGE/n)==h,n
 archive=ROOT.parent/'FlyAggression-Analyzer-v2.2-Release.zip'
 with zipfile.ZipFile(archive) as z:
  assert z.testzip() is None
  for n,h in sums.items():assert hashlib.sha256(z.read(PACKAGE.name+'/'+n)).hexdigest()==h,n
 build=json.loads((OUT/'release-build.json').read_text());assert sha(archive)==build['archive_sha256']
 result={'status':'PASS','preserved_v21_files':len(preservation['v21_files']),'preserved_default_launcher_and_v21_archive':True,'original_frozen_files':len(original['frozen_files']),'retrospective_recordings':5,'independent_recordings':0,'no_new_fitting_or_selection_in_evaluation':True,'paired_scores_exactly_equal':True,'fresh_run_events':audit['total_events'],'full_run_seconds':proof['total_seconds'],'actual_upload_service':True,'invalid_input_cases':9,'package_files_verified':len(sums),'archive_sha256':sha(archive),'coverage_gain':0,'accuracy_gain':0,'version21_worktree_clean':True}
 (OUT/'final-verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
