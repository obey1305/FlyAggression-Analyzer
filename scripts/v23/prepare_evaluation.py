"""Day5: lock annotation/time/identity eligibility before aggression-model inference."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,sys
import numpy as np,pandas as pd
from scipy.io import loadmat
from scipy.ndimage import binary_dilation
from evaluation_core import native_bins,close_coverage
from tracking_io import load_track
ROOT=Path(__file__).resolve().parents[2];R=ROOT/'reports/v23-days5-8';D=ROOT/'data/v23-evaluation';SRC=ROOT.parent/'new-training-data/BoyMeetsBoy/extracted/Boy_meets_boy light/movie5';REC='flyvsfly_boymeetsboy_movie5'
def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def save_json(p,x):p.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def main():
 lockfile=ROOT/'config/v23-evaluation-lock.json'
 if lockfile.exists() or (R/'inference.json').exists():raise ValueError('Locked evaluation already exists; preserve it')
 R.mkdir(exist_ok=True);D.mkdir(exist_ok=True)
 data=loadmat(ROOT/'data/v23-derived/features36.mat',simplify_cells=True)['feat']['data'];n=data.shape[1];assert data.shape==(2,38390,36)
 times=pd.read_csv(ROOT/'reports/v23-days1-4/frame-time-map.csv');idx=times.source_frame.to_numpy()-1;diag=pd.read_csv(ROOT/'reports/v23-days1-4/trajectory-comparison.csv');mapping=diag.new_fly1_reference_id.to_numpy()-1
 old,ow,_,_=load_track(SRC/'movie5_track.mat');new,nw,_,_=load_track(ROOT/'data/v23-tracking/movie5-analysis30/movie5-analysis30-track.mat')
 native_bad=~np.isfinite(old).all(axis=(0,2))|ow;native_bin=np.minimum(np.arange(old.shape[1])*30//200,n-1);badbin=np.zeros(n,bool);np.logical_or.at(badbin,native_bin,native_bad)
 base=diag.conservative_geometric_mapping_reliable.to_numpy(bool)&np.isfinite(data).all(axis=(0,2))&np.isfinite(new).all(axis=(0,2))&~nw&~badbin
 base=~binary_dilation(~base,iterations=2);base[:2]=False;base[-2:]=False
 pd.DataFrame({'frame':np.arange(1,n+1),'technical_eligible':base,'native_reference_bad_in_bin':badbin,'new_tracking_warning':nw,'mapping_state':mapping}).to_csv(R/'technical-coverage.csv',index=False)
 coverage=[];allbeh=[];locked=[]
 for annotator,suffix in [('primary','actions'),('secondary','second_actions')]:
  source=SRC/f'movie5_{suffix}.mat';g=loadmat(source,simplify_cells=True);beh=list(g['behs']);unknown=np.zeros(n,bool);native_unknown=np.zeros(old.shape[1],bool);positives=np.zeros((2,old.shape[1]),np.int8);boutrows=[]
  for ref in range(2):
   for j,name in enumerate(beh):
    x=np.asarray(g['bouts'][ref,j]);rows=np.atleast_2d(x) if x.size else []
    for count,row in enumerate(rows,1):
     s,e=map(int,row[:2]);assert 1<=s<=e<=old.shape[1];a,b=native_bins(s,e);extras=row[2:];extra_uncertain=bool(not np.isfinite(extras).all() or np.any(extras!=0))
     uncertain=name=='unknown' or extra_uncertain
     if uncertain:unknown[a:b]=True;native_unknown[s-1:e]=True
     allbeh.append(dict(annotator=annotator,reference_fly_id=ref+1,behavior=str(name),start_frame=s,end_frame=e,start_seconds=(s-1)/200,stop_seconds_exclusive=e/200,extra_columns=json.dumps(extras.tolist()),uncertain=uncertain))
     if name=='lunge':
      positives[ref,s-1:e]=1;boutrows.append(dict(recording=REC,annotator=annotator,event_id=(ref+1)*1000000+count,source_event_id=count,reference_fly_id=ref+1,source_start_frame=s,source_end_frame=e,start_seconds=(s-1)/200,stop_seconds_exclusive=e/200,source_duration_seconds=(e-s+1)/200,cover_start=a,cover_stop=b,extra_columns=json.dumps(extras.tolist()),extra_uncertain=extra_uncertain))
  initial=base&~unknown;keep=[];bounds=[]
  for row in boutrows:
   a,b=row['cover_start'],row['cover_stop'];s,e=row['source_start_frame'],row['source_end_frame'];states=mapping[a:b];samples=np.flatnonzero((idx>=s-1)&(idx<=e-1));reasons=[]
   if not len(samples):reasons.append('no_selected_analysis_sample')
   if not np.isfinite(old[:,s-1:e]).all():reasons.append('native_reference_missing')
   if ow[s-1:e].any():reasons.append('native_reference_warning')
   if native_unknown[s-1:e].any() or row['extra_uncertain']:reasons.append('annotation_unknown_or_extra_uncertain')
   if not initial[a:b].all():reasons.append('technical_or_unknown_coverage')
   if len(np.unique(states))!=1:reasons.append('identity_mapping_switch')
   row.update(sample_count=len(samples),analysis_start_frame=int(samples[0]+1) if len(samples) else None,analysis_end_frame=int(samples[-1]+1) if len(samples) else None,fly_id=int(row['reference_fly_id'] if states[0]==0 else 3-row['reference_fly_id']) if len(np.unique(states))==1 else 0,initially_eligible=not reasons,exclusion_reasons=';'.join(reasons));keep.append(not reasons);bounds.append((a,b))
  valid,retained=close_coverage(initial,bounds,keep)
  for row,k in zip(boutrows,retained):
   row['retained']=bool(k)
   if row['initially_eligible'] and not k:row['exclusion_reasons']='overlap_closure'
  bouts=pd.DataFrame(boutrows);bouts.to_csv(R/f'{annotator}-all-source-bouts.csv',index=False);truth=bouts[bouts.retained].copy();truth.to_csv(R/f'{annotator}-expert-events.csv',index=False)
  grids=[]
  for fly in (1,2):
   refs=np.where(mapping==0,fly,3-fly);y=positives[refs-1,idx];grids.append(pd.DataFrame({'recording':REC,'fly_id':fly,'frame':np.arange(1,n+1),'source_frame':idx+1,'reference_fly_id':refs,'target_lunge':np.where(valid,y,-1),'eligible':valid,'technical_eligible':base,'annotation_unknown':unknown,'source_label_positive':y,'mapping_state':mapping}))
  grid=pd.concat(grids,ignore_index=True);grid.to_parquet(D/f'{annotator}-grid.parquet',index=False)
  for fly in (1,2):
   q=bouts[bouts.reference_fly_id.eq(fly)];coverage.append({'annotator':annotator,'reference_fly_id':fly,'source_bouts':len(q),'retained_bouts':int(q.retained.sum()),'excluded_bouts':int((~q.retained).sum()),'coverage_fraction':float(q.retained.mean()) if len(q) else None,'joint_scorable_analysis_frames':int(valid.sum()),'joint_total_analysis_frames':n,'annotation_unknown_bins':int(unknown.sum()),'technical_eligible_bins_before_unknown':int(base.sum())})
  locked.extend([source,D/f'{annotator}-grid.parquet',R/f'{annotator}-all-source-bouts.csv',R/f'{annotator}-expert-events.csv'])
 pd.DataFrame(coverage).to_csv(R/'expert-coverage.csv',index=False);pd.DataFrame(allbeh).to_csv(R/'all-source-behaviors.csv',index=False)
 files=[ROOT/'data/v23-derived/features36.mat',ROOT/'data/v23-tracking/movie5-analysis30/movie5-analysis30-track.mat',SRC/'movie5_track.mat',ROOT/'reports/v23-days1-4/frame-time-map.csv',ROOT/'reports/v23-days1-4/trajectory-comparison.csv',ROOT/'models/raw-v2.2/lunge-detector.joblib',ROOT/'models/raw-v2.2/configuration.json',ROOT/'models/raw-v2.2/freeze-manifest.json',ROOT/'scripts/v23/evaluation_core.py',ROOT/'scripts/v23/prepare_evaluation.py',ROOT.parent/'drosophila-aggression/models/final-v1/runtime/scripts/event_detection.py',ROOT.parent/'drosophila-aggression/models/final-v1/runtime/scripts/lunge_pipeline.py',*locked,R/'technical-coverage.csv',R/'all-source-behaviors.csv',R/'expert-coverage.csv']
 cfg=json.loads((ROOT/'models/raw-v2.2/configuration.json').read_text());protocol={'locked_utc':datetime.now(timezone.utc).isoformat(),'scope':'one externally collected lunge-count-selected recording; no blind representative cohort claim','recording':REC,'source_fps':200,'analysis_fps':30,'threshold':cfg['threshold'],'event_rules':cfg['event_rules'],'feature_names':cfg['source_feature_names'],'event_matching':'max cardinality then IoU, one-to-one within recording/native output fly ID','event_iou':.3,'intervals':'main native200FPS half-open expert times vs30FPS prediction times; projected-grid sensitivity separate','prediction_policy':'frozen full-grid imputation and event detection independent of annotations; whole operational predictions excluded at evaluation boundaries, never clipped or re-smoothed','coverage':'existing geometric mapping; native reference finite/unflagged throughout source bouts and analysis bins; joint finite features/new XY; technical invalidity dilated2frames; explicit unknown/nonzero extras; whole-bout overlap closure censors both streams','frame_metrics':'conditional on exhaustive supplied lunge labels in scorable intervals; no confirmed negative annotations','model_tuning_allowed':False,'prediction_inspection_before_lock':False,'input_hashes':{str(p.resolve()):sha(p) for p in files}}
 save_json(lockfile,protocol);print(pd.DataFrame(coverage).to_string(index=False));print('LOCKED',sha(lockfile))
if __name__=='__main__':main()
