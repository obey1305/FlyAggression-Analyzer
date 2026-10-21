"""Verify ZIP extraction away from workspace, then run packaged model routes."""
from pathlib import Path
import sys,subprocess,json,zipfile,tempfile,hashlib
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT.parent
CODE=r'''
from pathlib import Path
import sys,json,subprocess,tempfile
import pandas as pd
from streamlit.testing.v1 import AppTest
base=Path(sys.argv[1]);p=base/'drosophila-aggression';v=base/'flyaggression-v2.1';sys.path.insert(0,str(p));sys.path.insert(0,str(v/'scripts'))
from raw_release import validate_release
from feature_service_v21 import analyze_upload
model,cfg=validate_release();assert str(model).startswith(str(base))
original=analyze_upload((p/'datasets/features/movie5_feat.mat').read_bytes(),'movie5_feat.mat');assert len(original['events'])==325
assert original['manifest']['model_sha256']=='508f49002159bb6da8be4c42f38c76ba43215b692e96aa73276e287cedb86a42'
try:analyze_upload((base/'examples/movie1-raw-features.mat').read_bytes(),'adapter.mat')
except ValueError as e:assert 'raw-video-derived' in str(e)
else:raise AssertionError('Raw features accepted in original mode')
with tempfile.TemporaryDirectory() as t:
 subprocess.run([sys.executable,str(p/'models/final-v1/runtime/analyze.py'),'--input',str(base/'examples/movie1-raw-features.mat'),'--output-dir',t,'--model',str(model),'--fps','30','--recording-id','movie1'],capture_output=True,text=True,check=True)
 manifest=json.loads((Path(t)/'run-manifest.json').read_text());events=pd.read_csv(Path(t)/'lunge-events.csv');assert manifest['model_sha256']==cfg['model_sha256'] and manifest['threshold']==.15 and manifest['event_rules']==cfg['event_rules'] and len(events)==68
app=AppTest.from_file(str(v/'app.py')).run(timeout=30);assert not app.exception
app.button[1].click().run(timeout=30);assert not app.exception and app.metric[0].value=='325'
app.radio[0].set_value('Experimental raw video').run(timeout=30);assert not app.exception and any('2.1' in w.value for w in app.warning)
print('RELOCATED PACKAGE PASS')
'''
def main():
 archive=OUT/'FlyAggression-Analyzer-v2.1-Release.zip';checks={}
 with tempfile.TemporaryDirectory(prefix='relocated-release-',dir=ROOT/'data') as t:
  with zipfile.ZipFile(archive) as z:assert z.testzip() is None;z.extractall(t)
  package=Path(t)/'FlyAggression-Analyzer-v2.1-Release';r=subprocess.run([sys.executable,str(package/'verify_package.py')],capture_output=True,text=True);assert r.returncode==0,r.stderr;checks['zip_crc_and_all_packaged_hashes']=True
  p=package/'DEMONSTRATION.md';before=p.read_bytes();p.write_bytes(before+b'\nchanged')
  tamper=subprocess.run([sys.executable,str(package/'verify_package.py')],capture_output=True,text=True);assert tamper.returncode!=0;p.write_bytes(before);checks['modified_package_file_rejected']=True
  smoke=subprocess.run([sys.executable,'-c',CODE,str(package)],capture_output=True,text=True,timeout=180);(ROOT/'reports/day10/package-smoke.log').write_text(smoke.stdout+smoke.stderr);assert smoke.returncode==0,smoke.stdout+smoke.stderr
  checks.update(relocated_original_model_route=True,relocated_raw_model_route=True,raw_adapter_mat_rejected_by_original_mode=True,app_original_example_and_raw_mode=True)
 result={'status':'PASS','checks':checks,'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'environment':'existing pinned Python environment; no clean dependency installation performed','raw_tracking_in_relocated_package':False,'raw_tracking_note':'Full tracking tested in workspace; relocated check verifies packaged source hashes and executes frozen inference and GUI routing.'};(ROOT/'reports/day10/package-verification.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if __name__=='__main__':main()
