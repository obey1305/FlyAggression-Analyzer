"""Fail-closed model routing for the raw-video-only Version 2.1 release."""
from pathlib import Path
import json,hashlib
import joblib
ROOT=Path(__file__).resolve().parents[1]
RELEASE=ROOT/'models/raw-v2.1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def validate_release(release=RELEASE):
 release=Path(release)
 try:
  manifest=json.loads((release/'freeze-manifest.json').read_text())
  required={'configuration.json','lunge-detector.joblib'}
  if set(manifest['files'])!=required:raise ValueError('Raw release integrity manifest has invalid files')
  for n,h in manifest['files'].items():
   if sha(release/n)!=h:raise ValueError('Raw release integrity check failed: '+n)
  cfg=json.loads((release/'configuration.json').read_text());model=release/'lunge-detector.joblib'
  if cfg['mode']!='raw-video-only' or cfg['release_version']!='2.1.0' or sha(model)!=cfg['model_sha256']:raise ValueError('Raw release model routing mismatch')
  adapter=ROOT.parent/'raw-video-integration/day5/adapter.py'
  if sha(adapter)!=cfg['adapter_sha256']:raise ValueError('Raw release feature adapter has changed')
  names=json.loads((ROOT/'config/feature-columns.json').read_text())
  if cfg['source_feature_names']!=names or cfg['feature_engineering_version']!=0:raise ValueError('Raw release feature schema mismatch')
  bundle=joblib.load(model)
  for key in ['threshold','event_rules','source_feature_names','feature_engineering_version','release_version']:
   if bundle[key]!=cfg[key]:raise ValueError('Raw release preprocessing or event configuration mismatch: '+key)
  if bundle['feature_names']!=names or bundle['pipeline'].feature_names_in_.tolist()!=names:raise ValueError('Raw release predictor order mismatch')
  return model,cfg
 except (OSError,KeyError,json.JSONDecodeError) as exc:raise ValueError('Version 2.1 raw release is missing or invalid; restore its frozen files.') from exc
