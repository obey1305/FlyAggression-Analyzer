"""Independent output reconciliation and immutable-input verification."""
from pathlib import Path
import hashlib,json,sys,subprocess
import numpy as np,pandas as pd
ROOT=Path(__file__).resolve().parents[2]; BASE=ROOT.parent/'flyaggression-v2.1'; OUT=ROOT/'reports/v22-days1-2'
sys.path.insert(0,str(BASE/'scripts'))
from prepare_aligned import load_track
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 cfg=json.loads((ROOT/'config/v22-preservation.json').read_text());checked=0
 for name,h in cfg['v21_files'].items():
  assert sha(BASE/name)==h,name;checked+=1
 for name,h in cfg['external_files'].items():assert sha(name)==h,name
 assert subprocess.check_output(['git','-C',str(BASE),'rev-parse','--short','HEAD'],text=True).strip()==cfg['v21_commit']
 assert not subprocess.check_output(['git','-C',str(BASE),'status','--porcelain'],text=True).strip()
 b=pd.read_csv(OUT/'bout-exclusion-audit.csv');c=pd.read_csv(OUT/'coverage-by-recording-fly.csv');s=pd.read_csv(OUT/'identity-candidate-summary.csv');ca=pd.read_csv(OUT/'causes-by-recording.csv')
 assert len(b)==1528 and b.baseline_retained.sum()==761
 assert not b.duplicated(['recording','reference_fly_id','source_event_id']).any()
 assert (b.baseline_retained==b.candidate_retained).all()
 assert not b.primary_exclusion.eq('UNEXPLAINED').any()
 assert ca.primary_excluded_bouts.sum()==(~b.baseline_retained).sum()==767
 assert c.source_bouts.sum()==len(b) and c.v21_retained_bouts.sum()==761
 assert s.supported_bridge_frames.sum()==0 and s.mapping_corrections_on_bridged_frames.sum()==0
 legacy=b[~b.legacy_features_finite_flag & ~b.actual_nonfinite_mapped_features]
 assert len(legacy)==12 and legacy.reason_frames_assignment_changes_within_bout.gt(0).all()
 manifest={};rows=0
 for rec in s.recording:
  _,_,raw,names=load_track(BASE/'data'/rec/'tracks.mat');corr=pd.read_parquet(OUT/rec/'identity-correspondence.parquet');good=corr.candidate_identity_reliable.to_numpy();mapping=corr.candidate_new_fly1_reference.to_numpy()-1;n=raw.shape[1]
  np.testing.assert_array_equal(good,corr.v21_identity_reliable)
  np.testing.assert_array_equal(mapping+1,corr.v21_new_fly1_reference)
  for ref in [0,1]:
   path=ROOT/'data/v22-derived'/rec/f'reference-fly{ref+1}.parquet';v=pd.read_parquet(path);chosen=np.where(mapping==0,ref,1-ref)
   np.testing.assert_array_equal(v.frame,np.arange(1,n+1));np.testing.assert_array_equal(v.source_fly_id,np.where(good,chosen+1,0));np.testing.assert_array_equal(v.identity_reliable,good)
   np.testing.assert_array_equal(v.loc[good,names].to_numpy(),raw[chosen,np.arange(n)][good])
   assert v.loc[~good,names].isna().all().all()
   manifest[str(path.relative_to(ROOT))]=sha(path);rows+=len(v)
 (OUT/'derived-data-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 result={'status':'PASS','preserved_v21_files':checked,'preserved_external_files':len(cfg['external_files']),'source_bouts':len(b),'retained_bouts':761,'excluded_bouts':767,'derived_rows_verified':rows,'legacy_nonfinite_flags_explained_by_assignment_changes':len(legacy),'additional_supported_corrections':0}
 (OUT/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
