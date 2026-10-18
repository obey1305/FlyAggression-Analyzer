"""Independent Day3 checks: source annotations, correspondence geometry, finite rows, splits and preservation."""
from pathlib import Path
import sys,json,hashlib
import numpy as np,pandas as pd
from scipy.io import loadmat
import h5py
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT.parent;P=OUT/'drosophila-aggression'
SOURCE=Path('/Users/adityasinghchauhan/Documents/Codex/2026-10-16/files-mentioned-by-the-user-codex/outputs/day3-videos/external-benchmark/Aggression')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 cfg=json.loads((ROOT/'config/preparation.json').read_text());names=json.loads((ROOT/'config/feature-columns.json').read_text());checks=[]
 for rec in cfg['selected_recordings']:
  folder=ROOT/'data'/rec;generation=json.loads((folder/'generation.json').read_text());assert generation['video_sha256']==sha(SOURCE/rec/(rec+'.mp4'))
  for filename,digest in generation['files'].items():assert sha(folder/filename)==digest
  full=pd.concat([pd.read_parquet(folder/f'full-grid-fly{fly}.parquet') for fly in [1,2]],ignore_index=True);eligible=pd.read_parquet(folder/'eligible.parquet')
  assert len(full)==108000 and not full.duplicated(['recording','fly_id','frame']).any()
  assert np.isfinite(eligible[names]).all().all() and eligible.target_lunge.isin([0,1]).all()
  raw=loadmat(folder/'features36.mat',simplify_cells=True)['feat'];assert list(raw['names'])==names
  for fly in [1,2]:
   d=full[full.fly_id==fly];np.testing.assert_array_equal(d.frame,np.arange(1,54001));np.testing.assert_array_equal(d[names],raw['data'][fly-1])
  # Independently reconstruct source positives and exclusions from intervals.
  src=loadmat(SOURCE/rec/(rec+'_actions.mat'),simplify_cells=True);positive=np.zeros((2,54000),bool);uncertain=np.zeros_like(positive)
  for fly in [0,1]:
   for j,behavior in enumerate(src['behs']):
    a=np.asarray(src['bouts'][fly,j]);a=a.reshape(-1,3) if a.size else []
    for start,end,flag in a:
     ix=np.arange(1,54001);inside=(ix>=start)&(ix<=end)
     if behavior=='lunge':positive[fly]|=inside
     if behavior=='unknown' or flag!=0:uncertain[fly]|=inside
  rid=eligible.reference_fly_id.to_numpy(int)-1;frame=eligible.frame.to_numpy(int)-1
  assert not uncertain[rid,frame].any();np.testing.assert_array_equal(eligible.target_lunge,positive[rid,frame].astype(int))
  audit=pd.read_parquet(folder/'alignment-audit.parquet').set_index('frame')
  assert audit.loc[eligible.frame,'alignment_reliable'].all()
  a=loadmat(SOURCE/rec/(rec+'_track.mat'),simplify_cells=True)['trk'];on=list(a['names']);old=a['data'][:,:,[on.index('pos x'),on.index('pos y')]]
  with h5py.File(folder/'tracks.mat') as f:
   nn=[''.join(chr(int(c)) for c in np.asarray(f[z]).ravel()) for z in np.asarray(f['trk/names']).ravel()];data=np.asarray(f['trk/data']).transpose(2,1,0);new=data[:,:,[nn.index('pos x'),nn.index('pos y')]]
  direct=np.linalg.norm(old-new,axis=2);reverse=np.linalg.norm(old-new[::-1],axis=2);mode=audit.new_fly1_maps_to_reference.to_numpy()-1
  err=np.where(mode[None,:]==0,direct,reverse);good=audit.alignment_reliable.to_numpy()
  assert np.all(err[:,good]<=3) and np.all(np.abs(direct.sum(axis=0)-reverse.sum(axis=0))[good]>=4)
  chosen=np.where(mode==0,direct.sum(axis=0),reverse.sum(axis=0));other=np.where(mode==0,reverse.sum(axis=0),direct.sum(axis=0));assert np.all((other-chosen)[good]>=4)
  assert np.all(np.linalg.norm(old[0]-old[1],axis=1)[good]>=8) and np.all(np.linalg.norm(new[0]-new[1],axis=1)[good]>=8)
  for shift in range(-5,6):
   ids=np.flatnonzero(good)+shift
   assert np.all(mode[ids]==mode[good])
   assert not audit.reference_tracking_warning.to_numpy()[ids].any() and not audit.new_tracking_warning.to_numpy()[ids].any()
  bouts=pd.read_csv(folder/'aligned-lunge-bouts.csv')
  for row in bouts[bouts.whole_bout_eligible].itertuples():
   bad=bouts[(~bouts.whole_bout_eligible)&bouts.reference_fly_id.eq(row.reference_fly_id)]
   assert not ((bad.start_frame<=row.end_frame)&(bad.end_frame>=row.start_frame)).any()
   assert good[row.start_frame-1:row.end_frame].all()
   expected_stream=np.where(mode[row.start_frame-1:row.end_frame]==0,row.reference_fly_id,3-row.reference_fly_id)
   assert np.all(expected_stream==row.new_fly_id)
   assert np.isfinite(raw['data'][row.new_fly_id-1,row.start_frame-1:row.end_frame]).all()
  checks.append({'recording':rec,'status':'PASS','full_grid_rows':len(full),'eligible_rows':len(eligible),'positive_rows':int(eligible.target_lunge.sum()),'excluded_rows':len(full)-len(eligible)})
 train=pd.read_parquet(ROOT/'data/train.parquet');val=pd.read_parquet(ROOT/'data/validation.parquet')
 assert set(train.recording)=={'movie1','movie2','movie3','movie4'} and set(val.recording)=={'movie5'} and not set(train.recording)&set(val.recording)
 assert train.target_lunge.nunique()==2 and val.target_lunge.nunique()==2
 toolchain=json.loads((ROOT/'config/toolchain.json').read_text())
 for filename,digest in toolchain['native_mex_sha256'].items():assert sha(filename)==digest
 preserve=json.loads((ROOT/'config/preservation.json').read_text());assert sha(OUT/'FlyAggression-Analyzer-v2.0.zip')==preserve['v2_archive_sha256']==sha(ROOT/'source-snapshot/Version2.0-release.zip')
 for name,h in preserve['frozen_files'].items():assert sha(P/'models/final-v1'/name)==h
 for name,h in preserve['extractor_sources'].items():assert sha(name)==h
 report={'status':'PASS','checks':checks,'version2_preserved':True,'nine_frozen_files_unchanged':True,'extractor_unchanged':True,'no_classifier_or_preprocessor_fit':True,'independent_test_available':False,'dataset_sha256':{n:sha(ROOT/'data'/n) for n in ['train.parquet','validation.parquet']}}
 (ROOT/'reports/verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':main()
