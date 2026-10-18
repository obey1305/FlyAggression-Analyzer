"""Days2–3: conservative reference-to-new-track labels, complete-grid audit and fixed splits."""
from pathlib import Path
import json,hashlib
import numpy as np,pandas as pd,h5py
from scipy.io import loadmat
from scipy.ndimage import binary_dilation
ROOT=Path(__file__).resolve().parents[1]
SOURCE=Path('/Users/adityasinghchauhan/Documents/Codex/2026-10-16/files-mentioned-by-the-user-codex/outputs/day3-videos/external-benchmark/Aggression')
def ranges(mask):
 d=np.diff(np.r_[False,mask,False].astype(int));return list(zip(np.flatnonzero(d==1),np.flatnonzero(d==-1)))
def load_track(path):
 if h5py.is_hdf5(path):
  with h5py.File(path) as f:
   g=f['trk'];names=[''.join(chr(int(c)) for c in np.asarray(f[z]).ravel()) for z in np.asarray(g['names']).ravel()]
   data=np.asarray(g['data']).transpose(2,1,0);flags=np.asarray(g['flags']).T if 'flags' in g else np.empty((0,6));old_flags=np.asarray(g['flag_frames']).ravel() if 'flag_frames' in g else np.zeros(data.shape[1])
 else:
  g=loadmat(path,simplify_cells=True)['trk'];names=list(g['names']);data=g['data'];flags=np.asarray(g.get('flags',np.empty((0,6))));old_flags=np.asarray(g.get('flag_frames',np.zeros(data.shape[1]))).ravel()
 assert len(names)==len(set(names)) and data.shape[0]==2
 xy=data[:,:,[names.index('pos x'),names.index('pos y')]]
 warning=old_flags.astype(bool)
 if flags.size:
  flags=flags.reshape(-1,6)
  for row in flags:
   a,b=int(row[2]),int(row[3]);warning[max(0,a-1):min(len(warning),b)]=True
 return xy,warning,data,names

def align_positions(old,new,old_warning,new_warning,cfg):
 if old.shape!=new.shape or old.ndim!=3 or old.shape[0]!=2 or old.shape[2]!=2:raise ValueError('Reference/new tracks must match two-fly frame grids')
 direct=np.linalg.norm(old-new,axis=2);swapped=np.linalg.norm(old-new[::-1],axis=2)
 directcost=direct.sum(axis=0);swapcost=swapped.sum(axis=0)
 mapping=(swapcost<directcost).astype('int8') # new fly1 corresponds to original fly2 when 1
 err=np.where(mapping[None,:]==0,direct,swapped);margin=np.abs(directcost-swapcost)
 separation=np.minimum(np.linalg.norm(old[0]-old[1],axis=1),np.linalg.norm(new[0]-new[1],axis=1))
 finite=np.isfinite(old).all(axis=(0,2))&np.isfinite(new).all(axis=(0,2))
 geometric=finite&(err.max(axis=0)<=cfg['maximum_position_error_pixels'])&(margin>=cfg['minimum_assignment_margin_pixels'])&(separation>=cfg['minimum_reference_separation_pixels'])
 reliable=geometric&~np.asarray(old_warning,bool)&~np.asarray(new_warning,bool)
 stable=np.zeros(len(reliable),bool)
 for state in [0,1]:
  for a,b in ranges(reliable&(mapping==state)):
   if b-a>=cfg['minimum_stable_mapping_frames']:stable[a:b]=True
 boundary=cfg['boundary_exclusion_frames'];bad=~stable
 bad[1:] |= mapping[1:]!=mapping[:-1]
 if boundary:bad=binary_dilation(bad,iterations=boundary)
 good=stable&~bad
 # Do not infer temporal context beyond first/last complete source window.
 good[:boundary]=False;good[-boundary:]=False
 return mapping,good,dict(position_error_pixels=err.max(axis=0),assignment_margin_pixels=margin,separation_pixels=separation,geometrically_reliable=geometric)

def annotation_labels(src,nframes):
 behaviors=list(src['behs']);bouts=src['bouts'];y=np.zeros((2,nframes),dtype='int8');unknown=np.zeros_like(y,bool)
 for fly in [0,1]:
  for j,name in enumerate(behaviors):
   cell=np.asarray(bouts[fly,j]);rows=cell.reshape(-1,3) if cell.size else np.empty((0,3))
   for start,end,flag in rows:
    if not np.isfinite([start,end,flag]).all() or start!=int(start) or end!=int(end) or not 1<=start<=end<=nframes:raise ValueError('Invalid annotation frame interval')
    if name=='lunge':y[fly,int(start)-1:int(end)]=1
    if name=='unknown' or flag!=0:unknown[fly,int(start)-1:int(end)]=True
 y[unknown]=-1;return y

def close_bout_exclusions(bouts):
 d=bouts.copy();d['excluded_by_overlap_closure']=False
 while True:
  changed=False
  for i,row in d[d.whole_bout_eligible].iterrows():
   bad=d[(~d.whole_bout_eligible)&d.reference_fly_id.eq(row.reference_fly_id)]
   if ((bad.start_frame<=row.end_frame)&(bad.end_frame>=row.start_frame)).any():
    d.loc[i,'whole_bout_eligible']=False;d.loc[i,'excluded_by_overlap_closure']=True;changed=True
  if not changed:break
 return d

def prepare(rec):
 cfg=json.loads((ROOT/'config/preparation.json').read_text());d=ROOT/'data'/rec
 names=json.loads((ROOT/'config/feature-columns.json').read_text());feat=loadmat(d/'features36.mat',simplify_cells=True)['feat'];data=feat['data']
 assert list(feat['names'])==names and data.shape==(2,54000,36)
 old,ow,_,_=load_track(SOURCE/rec/(rec+'_track.mat'));new,nw,_,_=load_track(d/'tracks.mat');mapping,good,diag=align_positions(old,new,ow,nw,cfg['alignment']);n=data.shape[1]
 offsets=[]
 for shift in cfg['frame_offset_diagnostic']['new_frame_offsets']:
  lo=max(0,-shift);hi=min(n,n-shift);a=old[:,lo:hi];b=new[:,lo+shift:hi+shift]
  direct=np.linalg.norm(a-b,axis=2).sum(axis=0);swap=np.linalg.norm(a-b[::-1],axis=2).sum(axis=0)
  offsets.append({'recording':rec,'new_frame_offset':shift,'median_best_pair_error_pixels':float(np.nanmedian(np.minimum(direct,swap)))})
 zero=offsets[3]['median_best_pair_error_pixels'];best=min(x['median_best_pair_error_pixels'] for x in offsets)
 if zero>best+cfg['frame_offset_diagnostic']['maximum_zero_offset_excess_median_pair_error_pixels']:good[:]=False
 pd.DataFrame(offsets).to_csv(d/'frame-offset-diagnostic.csv',index=False)
 src=loadmat(SOURCE/rec/(rec+'_actions.mat'),simplify_cells=True);y=annotation_labels(src,n)
 audit=pd.DataFrame({'frame':np.arange(1,n+1),'new_fly1_maps_to_reference':mapping+1,'alignment_reliable':good,'reference_tracking_warning':ow,'new_tracking_warning':nw,**diag})
 audit.to_parquet(d/'alignment-audit.parquet',index=False)
 intervals=[]
 for state in [0,1]:
  for a,b in ranges(good&(mapping==state)):intervals.append({'recording':rec,'start_frame':a+1,'end_frame':b,'new_fly1_reference_id':state+1,'evidence':'stable separated-body geometric match; reference identity not independently certified'})
 pd.DataFrame(intervals).to_csv(d/'reliable-mapping-intervals.csv',index=False)
 parts=[];features=[];counts=[]
 for fly in [0,1]:
  reference_id=np.where(mapping==0,fly,1-fly);source_y=y[reference_id,np.arange(n)]
  finite=np.isfinite(data[fly]).all(axis=1);usable=good&(source_y>=0)&finite
  target=np.where(usable,source_y,-1).astype('int8')
  df=pd.DataFrame(data[fly],columns=names)
  for k,v in {'recording':rec,'split':cfg['splits'][rec],'fly_id':fly+1,'frame':np.arange(1,n+1),'reference_fly_id':reference_id+1,'alignment_reliable':good,'annotation_reliable':source_y>=0,'features_finite':finite,'source_lunge_label':source_y,'target_lunge':target,'eligible':usable,'explicit_confirmed_negative':False}.items():df[k]=v
  df.to_parquet(d/f'full-grid-fly{fly+1}.parquet',index=False);parts.append(df.loc[usable,names+['recording','split','fly_id','frame','reference_fly_id','target_lunge']].copy())
  counts.append({'recording':rec,'fly_id':fly+1,'split':cfg['splits'][rec],'total_frames':n,'identity_reliable_frames':int(good.sum()),'annotation_uncertain_frames':int((source_y<0).sum()),'nonfinite_feature_rows':int((~finite).sum()),'eligible_frames':int(usable.sum()),'lunge_frames':int((target==1).sum()),'inferred_nonlunge_frames':int((target==0).sum()),'positive_frames_before_alignment_filter':int((source_y==1).sum()),'positive_frames_excluded':int(((source_y==1)&~usable).sum()),'reference_id_reassignment_frames':int((reference_id!=fly).sum())})
  for j,name in enumerate(names):
   v=data[fly,:,j];clean=v[np.isfinite(v)]
   features.append({'recording':rec,'fly_id':fly+1,'feature':name,'nan':int(np.isnan(v).sum()),'inf':int(np.isinf(v).sum()),'min':float(clean.min()),'q01':float(np.quantile(clean,.01)),'median':float(np.median(clean)),'q99':float(np.quantile(clean,.99)),'max':float(clean.max())})
 # Preserve complete source bout identity and mark eligibility without fragmenting events.
 boutrows=[]
 lunge_index=list(src['behs']).index('lunge')
 for ref in [0,1]:
  cell=np.asarray(src['bouts'][ref,lunge_index]);bouts=cell.reshape(-1,3) if cell.size else np.empty((0,3))
  for event_id,(start,end,flag) in enumerate(bouts,1):
   a,b=int(start)-1,int(end);mapped=np.where(mapping[a:b]==0,ref,1-ref)
   one_stream=np.unique(mapped).size==1;newfly=int(mapped[0]) if one_stream else -1
   identity_ok=bool(good[a:b].all()) and one_stream
   annotation_ok=bool((y[ref,a:b]>=0).all()) and flag==0
   features_ok=bool(np.isfinite(data[newfly,a:b]).all()) if one_stream else False
   boutrows.append(dict(recording=rec,source_event_id=event_id,reference_fly_id=ref+1,new_fly_id=newfly+1,start_frame=int(start),end_frame=int(end),source_flag=float(flag),identity_reliable=identity_ok,annotation_reliable=annotation_ok,features_finite=features_ok,whole_bout_eligible=identity_ok and annotation_ok and features_ok))
 close_bout_exclusions(pd.DataFrame(boutrows)).to_csv(d/'aligned-lunge-bouts.csv',index=False)
 eligible=pd.concat(parts,ignore_index=True);eligible.to_parquet(d/'eligible.parquet',index=False)
 pd.DataFrame(counts).to_csv(d/'coverage.csv',index=False);pd.DataFrame(features).to_csv(d/'feature-distributions.csv',index=False)
 return counts,features

def main():
 cfg=json.loads((ROOT/'config/preparation.json').read_text());coverage=[];profiles=[];splits={'train':[],'validation':[]}
 for rec in cfg['selected_recordings']:
  c,p=prepare(rec);coverage+=c;profiles+=p;df=pd.read_parquet(ROOT/'data'/rec/'eligible.parquet');splits[cfg['splits'][rec]].append(df)
 for split,parts in splits.items():
  data=pd.concat(parts,ignore_index=True);assert set(data.recording)=={r for r,s in cfg['splits'].items() if s==split};assert not data.duplicated(['recording','fly_id','frame']).any();assert data.target_lunge.isin([0,1]).all()
  data.to_parquet(ROOT/'data'/f'{split}.parquet',index=False)
 pd.DataFrame(coverage).to_csv(ROOT/'reports/coverage.csv',index=False);pd.DataFrame(profiles).to_csv(ROOT/'reports/feature-distributions.csv',index=False)
 result={split:{'recordings':sorted(pd.concat(parts).recording.unique()),'rows':sum(len(x) for x in parts),'lunge_frames':int(sum(x.target_lunge.sum() for x in parts))} for split,parts in splits.items()}
 (ROOT/'reports/dataset-summary.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if __name__=='__main__':main()
