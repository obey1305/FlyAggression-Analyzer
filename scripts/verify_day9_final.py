"""Fresh regression evidence, export audit and preservation checks for final release."""
from pathlib import Path
import sys,json,subprocess,re,hashlib,importlib.metadata as md
import pandas as pd
from audit_quantification import audit_tables
from raw_release import validate_release
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT.parent;P=OUT/'drosophila-aggression'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 counts={}
 for tag,cwd in [('v21',ROOT),('original',P)]:
  result=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-v'],cwd=cwd,capture_output=True,text=True);(ROOT/f'reports/day9-regression-{tag}.log').write_text(result.stdout+result.stderr);assert result.returncode==0,result.stderr
  counts[tag]=int(re.search(r'Ran (\d+) tests',result.stderr).group(1))
 frozen=json.loads((ROOT/'config/preservation.json').read_text())
 for n,h in frozen['frozen_files'].items():assert sha(P/'models/final-v1'/n)==h
 for n,h in frozen['extractor_sources'].items():assert sha(n)==h
 assert sha(OUT/'FlyAggression-Analyzer-v2.0.zip')==frozen['v2_archive_sha256']
 model,cfg=validate_release();assert sha(model)=='d8193350a2d100f761e84c2d60609b5f9c17cb4bcc651c82bbf2e3dc5f831f5a'
 for n,h in json.loads((ROOT/'config/toolchain.json').read_text())['native_mex_sha256'].items():assert sha(n)==h
 audits=[]
 for folder in [ROOT/'reports/day9/movie1/run/experimental-results',ROOT/'reports/day10/Version-2.0',ROOT/'reports/day10/Version-2.1']:
  audit=audit_tables(*[pd.read_csv(folder/n) for n in ['frame-predictions.csv','lunge-events.csv','summary-by-fly.csv','summary-by-recording.csv']]);audits.append({'folder':str(folder.relative_to(ROOT)),**audit})
 invalid=json.loads((ROOT/'reports/day9/invalid-input-results.json').read_text());assert len(invalid['cases'])==9 and all(c['status']=='PASS' for c in invalid['cases'])
 full=json.loads((ROOT/'reports/day9/movie1/verification.json').read_text());assert full['status']=='PASS' and full['model_sha256']==sha(model)
 evaluation=json.loads((ROOT/'reports/day10/verification.json').read_text());assert evaluation['status']=='PASS' and not evaluation['fitting_performed'] and not evaluation['settings_changed']
 proof={'status':'PASS','v21_test_count':counts['v21'],'original_test_count':counts['original'],'handled_invalid_input_cases':9,'export_audits_including_onset_stop_and_frame_event_membership':audits,'original_frozen_release_unchanged':True,'raw_frozen_release_unchanged':True,'v20_archive_unchanged':True,'adapter_automatic_calibration_and_native_helpers_unchanged':True,'training_or_tuning_performed':False,'raw_model_sha256':sha(model),'versions':{n:md.version(n) for n in ['numpy','pandas','scipy','scikit-learn','streamlit','matplotlib','h5py','joblib']}}
 (ROOT/'reports/day9-final-verification.json').write_text(json.dumps(proof,indent=2));print(json.dumps(proof,indent=2))
if __name__=='__main__':main()
