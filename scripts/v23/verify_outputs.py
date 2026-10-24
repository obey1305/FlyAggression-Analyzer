"""Final artifact integrity, shape, provenance and source checks; no model execution."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from scipy.io import loadmat
ROOT=Path(__file__).resolve().parents[2];R=ROOT/'reports/v23-days1-4';B=ROOT.parent/'new-training-data/BoyMeetsBoy'
def hashes(path):
 a=hashlib.sha256();b=hashlib.md5()
 with path.open('rb') as f:
  for x in iter(lambda:f.read(1048576),b''):a.update(x);b.update(x)
 return a.hexdigest(),b.hexdigest()
def main():
 expected=json.loads((B/'download-verification.json').read_text());sources=[]
 for name,v in expected['files'].items():
  p=B/'downloads'/name;sha,md5=hashes(p);assert sha==v['sha256'] and md5==v['md5'] and p.stat().st_size==v['bytes'];sources.append(name)
 audit=json.loads((R/'feature-compatibility.json').read_text())
 for name,digest in audit['files'].items():assert hashes(ROOT/name)[0]==digest
 g=loadmat(ROOT/'data/v23-derived/features36.mat',simplify_cells=True)['feat'];assert g['data'].shape==(2,38390,36);assert list(g['names'])==json.loads((ROOT/'config/feature-columns.json').read_text());assert 'integration_status' in g
 for i,row in enumerate(audit['missingness']):assert int((~np.isfinite(g['data'][i]).all(axis=1)).sum())==row['nonfinite_36feature_rows']
 video=json.loads((R/'full-video-verification.json').read_text());assert video['status']=='PASS'
 assert json.loads((R/'calibration-tests.json').read_text())['status']=='PASS'
 model=ROOT/'models/raw-v2.2';manifest=json.loads((model/'freeze-manifest.json').read_text())
 # The frozen bundle is inspected as bytes/configuration only, never deserialized.
 assert hashes(model/'lunge-detector.joblib')[0]==json.loads((model/'configuration.json').read_text())['model_sha256']
 result={'status':'PASS','provider_downloads_reverified':sources,'full_feature_shape':list(g['data'].shape),'mat_provenance_marker_present':True,'generated_tracking_and_features_hashes_verified':len(audit['files']),'missingness_matches_report':True,'full_video_receipt_verified':True,'frozen_classifier_hash_verified':True,'classifier_deserialized_or_invoked':False}
 (R/'final-verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
