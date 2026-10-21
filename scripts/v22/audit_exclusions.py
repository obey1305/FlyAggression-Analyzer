"""Version2.2 Days1–2: independent exclusion decomposition and conservative identity candidate."""
from pathlib import Path
import sys,json,hashlib
import numpy as np,pandas as pd
from scipy.io import loadmat
from scipy.ndimage import binary_dilation
from identity_alignment import align_identity,runs,axial_error
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT.parent/'flyaggression-v2.1';DEST=ROOT/'reports/v22-days1-2'
sys.path.insert(0,str(BASE/'scripts'))
from prepare_aligned import load_track,annotation_labels,close_bout_exclusions,SOURCE
from optimize_days5_7 import event_reference
REASONS=['missing_track_coordinates','nonfinite_feature_measurements','source_lunge_flag','annotation_unknown','annotation_flagged_overlap','reference_tracking_warning','new_tracking_warning','position_disagreement','assignment_margin','close_contact_separation','assignment_changes_within_bout','short_stable_run','context_buffer','recording_boundary','frame_alignment_gate','same_reference_bout_closure','whole_bout_event_censoring']
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def decompose(old,new,ow,nw,cfg,offset_failed=False):
 n=old.shape[1];direct=np.linalg.norm(old-new,axis=2);swap=np.linalg.norm(old-new[::-1],axis=2);mapping=(swap.sum(axis=0)<direct.sum(axis=0)).astype(int)
 paired=np.where(mapping[None,:]==0,direct,swap);finite=np.isfinite(old).all(axis=(0,2))&np.isfinite(new).all(axis=(0,2));margin=np.abs(direct.sum(axis=0)-swap.sum(axis=0));separation=np.minimum(np.linalg.norm(old[0]-old[1],axis=1),np.linalg.norm(new[0]-new[1],axis=1))
 primitive=finite&(paired.max(axis=0)<=cfg['maximum_position_error_pixels'])&(margin>=cfg['minimum_assignment_margin_pixels'])&(separation>=cfg['minimum_reference_separation_pixels'])&~ow&~nw
 stable=np.zeros(n,bool)
 for state in [0,1]:
  for a,b in runs(primitive&(mapping==state)):
   if b-a>=cfg['minimum_stable_mapping_frames']:stable[a:b]=True
 bad=~stable;bad[1:]|=mapping[1:]!=mapping[:-1];boundary=cfg['boundary_exclusion_frames'];dilated=binary_dilation(bad,iterations=boundary) if boundary else bad.copy();edge=np.zeros(n,bool)
 if boundary:edge[:boundary]=True;edge[-boundary:]=True
 good=stable&~dilated&~edge
 if offset_failed:good[:]=False
 reasons={'missing_track_coordinates':~finite,'position_disagreement':finite&(paired.max(axis=0)>cfg['maximum_position_error_pixels']),'assignment_margin':finite&(margin<cfg['minimum_assignment_margin_pixels']),'close_contact_separation':finite&(separation<cfg['minimum_reference_separation_pixels']),'reference_tracking_warning':ow,'new_tracking_warning':nw,'short_stable_run':primitive&~stable,'context_buffer':stable&dilated,'recording_boundary':edge,'frame_alignment_gate':np.full(n,offset_failed)}
 return mapping,good,reasons,{'position_error_pixels':paired.max(axis=0),'assignment_margin_pixels':margin,'separation_pixels':separation}
def annotation_masks(src,n):
 unknown=np.zeros((2,n),bool);flagged=np.zeros_like(unknown)
 for ref in [0,1]:
  for j,name in enumerate(src['behs']):
   a=np.asarray(src['bouts'][ref,j]);a=a.reshape(-1,3) if a.size else []
   for start,end,flag in a:
    if name=='unknown':unknown[ref,int(start)-1:int(end)]=True
    if flag!=0:flagged[ref,int(start)-1:int(end)]=True
 return unknown,flagged

def coverage(rec,data,mapping,reliable,y,source_bouts):
 n=data.shape[1];parts=[];boutrows=[]
 for fly in [0,1]:
  ref=np.where(mapping==0,fly,1-fly);labels=y[ref,np.arange(n)];finite=np.isfinite(data[fly]).all(axis=1)
  parts.append(pd.DataFrame({'recording':rec,'fly_id':fly+1,'frame':np.arange(1,n+1),'eligible':reliable&(labels>=0)&finite}))
 for row in source_bouts.itertuples():
  a,b=int(row.start_frame)-1,int(row.end_frame);ref=int(row.reference_fly_id)-1;stream=np.where(mapping[a:b]==0,ref,1-ref);one=np.unique(stream).size==1;fly=int(stream[0]) if one else -1
  identity=bool(reliable[a:b].all()) and one;annotation=bool((y[ref,a:b]>=0).all()) and row.source_flag==0;features=bool(np.isfinite(data[fly,a:b]).all()) if one else False
  boutrows.append({'recording':rec,'source_event_id':row.source_event_id,'reference_fly_id':ref+1,'new_fly_id':fly+1,'start_frame':a+1,'end_frame':b,'source_flag':row.source_flag,'identity_reliable':identity,'annotation_reliable':annotation,'features_finite':features,'whole_bout_eligible':identity and annotation and features})
 bouts=close_bout_exclusions(pd.DataFrame(boutrows));grid=pd.concat(parts,ignore_index=True);valid,truth=event_reference(grid,bouts)
 return grid,bouts,valid.reshape(2,n),truth

def main():
 DEST.mkdir(parents=True,exist_ok=True);cfg=json.loads((ROOT/'config/v22-days1-2.json').read_text());basecfg=json.loads((BASE/'config/preparation.json').read_text());all_bouts=[];all_summary=[];all_causes=[];all_windows=[];all_intervals=[];identity_summary=[];all_attempts=[]
 derived=ROOT/'data/v22-derived';derived.mkdir(parents=True,exist_ok=True)
 for rec in cfg['recordings']:
  print('Audit',rec,flush=True);d=BASE/'data'/rec;dest=DEST/rec;dest.mkdir(exist_ok=True);saved=pd.read_parquet(d/'alignment-audit.parquet');feat=loadmat(d/'features36.mat',simplify_cells=True)['feat'];data=feat['data'];n=data.shape[1]
  old,ow,od,on=load_track(SOURCE/rec/(rec+'_track.mat'));new,nw,nd,nn=load_track(d/'tracks.mat');src=loadmat(SOURCE/rec/(rec+'_actions.mat'),simplify_cells=True);y=annotation_labels(src,n);unknown,flagged=annotation_masks(src,n);b=pd.read_csv(d/'aligned-lunge-bouts.csv')
  offsets=pd.read_csv(d/'frame-offset-diagnostic.csv');zero=float(offsets.loc[offsets.new_frame_offset.eq(0),'median_best_pair_error_pixels'].iloc[0]);offset_bad=zero>offsets.median_best_pair_error_pixels.min()+basecfg['frame_offset_diagnostic']['maximum_zero_offset_excess_median_pair_error_pixels']
  mapping,good,reasons,geometry=decompose(old,new,ow,nw,basecfg['alignment'],offset_bad)
  np.testing.assert_array_equal(mapping+1,saved.new_fly1_maps_to_reference);np.testing.assert_array_equal(good,saved.alignment_reliable)
  grid,base_bouts,valid,truth=coverage(rec,data,mapping,good,y,b)
  cached=pd.read_parquet(BASE/f'reports/days5-7/{rec}/evaluation-coverage.parquet');np.testing.assert_array_equal(valid.ravel(),cached.valid_for_events)
  original_truth=pd.read_csv(BASE/f'reports/days5-7/{rec}/expert-events.csv');assert set(truth.event_id)==set(original_truth.event_id)
  oo=od[:,:,on.index('ori')];no=nd[:,:,nn.index('ori')]
  candidate=align_identity(old,new,oo,no,mapping,good,ow,nw,cfg['reference_assisted_identity_bridge']);cm=candidate['mapping'];cg=candidate['reliable'];cgrid,cb,cv,ct=coverage(rec,data,cm,cg,y,b)
  attempts=pd.DataFrame(candidate['attempts']);attempts['recording']=rec;attempts.to_csv(dest/'identity-bridge-attempts.csv',index=False);all_attempts.append(attempts)
  correspondence=pd.DataFrame({'recording':rec,'frame':np.arange(1,n+1),'v21_new_fly1_reference':mapping+1,'candidate_new_fly1_reference':cm+1,'v21_identity_reliable':good,'candidate_identity_reliable':cg,'evidence_supported_bridge':candidate['bridged'],'proposed_mapping_changed':candidate['mapping_changed'],'reference_warning':ow,'source_warning':nw,**geometry})
  correspondence.to_parquet(dest/'identity-correspondence.parquet',index=False)
  bretain=set(truth.event_id);cretain=set(ct.event_id);evalkeys=base_bouts.source_event_id+(base_bouts.reference_fly_id-1)*1000000
  all_reason_arrays=[];rows=[]
  for ref in [0,1]:
   stream=np.where(mapping==0,ref,1-ref);ix=np.arange(n);finite=np.isfinite(data[stream,ix]).all(axis=1);source_eligible=grid.eligible.to_numpy().reshape(2,n)[stream,ix];eval_valid=valid[stream,ix]
   r={k:np.asarray(v,bool).copy() for k,v in reasons.items()};r.update(nonfinite_feature_measurements=~finite,annotation_unknown=unknown[ref],annotation_flagged_overlap=flagged[ref],whole_bout_event_censoring=source_eligible&~eval_valid)
   bits=np.zeros(n,np.uint32)
   for bit,name in enumerate(REASONS):
    if name in r:bits|=r[name].astype(np.uint32)<<bit
   # All unscorable frames have an explicit direct or whole-bout reason.
   assert (bits[~eval_valid]!=0).all()
   change=np.r_[0,np.flatnonzero((bits[1:]!=bits[:-1])|(eval_valid[1:]!=eval_valid[:-1]))+1,n]
   for a,z in zip(change[:-1],change[1:]):
    if eval_valid[a]:continue
    all_intervals.append({'recording':rec,'reference_fly_id':ref+1,'start_frame':a+1,'end_frame':z,'start_seconds':a/30,'duration_seconds':(z-a)/30,'reason_bitmask':int(bits[a]),'reasons':'|'.join(name for bit,name in enumerate(REASONS) if int(bits[a])&(1<<bit))})
   for row in b[b.reference_fly_id.eq(ref+1)].itertuples():
    a,z=int(row.start_frame)-1,int(row.end_frame);key=int(row.source_event_id+ref*1000000);counts={k:int(v[a:z].sum()) for k,v in r.items()};counts['source_lunge_flag']=(z-a)*int(row.source_flag!=0);counts['assignment_changes_within_bout']=(z-a)*int(np.unique(mapping[a:z]).size>1)
    i=base_bouts[base_bouts.reference_fly_id.eq(ref+1)&base_bouts.source_event_id.eq(row.source_event_id)].iloc[0]
    counts['same_reference_bout_closure']=(z-a)*int(i.excluded_by_overlap_closure)
    if key not in bretain and i.whole_bout_eligible:counts['whole_bout_event_censoring']=z-a
    retained=key in bretain;primary='retained' if retained else next((name for name in REASONS if counts.get(name,0)>0),'UNEXPLAINED')
    assert primary!='UNEXPLAINED';hit=[name for name in REASONS if counts.get(name,0)>0]
    # Mapping can change inside a bout even when its raw feature measurements are finite.
    actual_nonfinite=bool(counts.get('nonfinite_feature_measurements',0))
    rows.append({'recording':rec,'reference_fly_id':ref+1,'source_event_id':row.source_event_id,'evaluation_event_id':key,'start_frame':row.start_frame,'end_frame':row.end_frame,'duration_frames':z-a,'baseline_retained':retained,'candidate_retained':key in cretain,'primary_exclusion':primary,'overlapping_reasons':'|'.join(hit),'legacy_features_finite_flag':row.features_finite,'actual_nonfinite_mapped_features':actual_nonfinite,**{'reason_frames_'+name:counts.get(name,0) for name in REASONS}})
   all_summary.append({'recording':rec,'reference_fly_id':ref+1,'source_bouts':int(b.reference_fly_id.eq(ref+1).sum()),'v21_retained_bouts':int(truth.fly_id.size and truth.reference_fly_id.eq(ref+1).sum()),'candidate_retained_bouts':int(ct.reference_fly_id.eq(ref+1).sum()),'baseline_scorable_reference_frames':int(eval_valid.sum()),'candidate_identity_reliable_frames':int(cg.sum()),'baseline_identity_reliable_frames':int(good.sum())})
   # Derived track view: only reliable rows get a reference identity; raw source arrays remain untouched.
   chosen=np.where(cm==0,ref,1-ref);view=pd.DataFrame(nd[chosen,np.arange(n)],columns=nn);view.loc[~cg,nn]=np.nan
   view.insert(0,'recording',rec);view.insert(1,'reference_fly_id',ref+1);view.insert(2,'frame',np.arange(1,n+1));view['source_fly_id']=np.where(cg,chosen+1,0);view['identity_reliable']=cg;view['v22_bridge']=candidate['bridged']
   folder=derived/rec;folder.mkdir(exist_ok=True);view.to_parquet(folder/f'reference-fly{ref+1}.parquet',index=False)
  table=pd.DataFrame(rows);table.to_csv(dest/'bout-exclusion-audit.csv',index=False);all_bouts.append(table)
  for reason in REASONS:
   col='reason_frames_'+reason;all_causes.append({'recording':rec,'reason':reason,'excluded_bouts_with_reason':int((~table.baseline_retained&table[col].gt(0)).sum()),'primary_excluded_bouts':int(table.primary_exclusion.eq(reason).sum()),'overlap_policy':'cause counts overlap; primary uses documented fixed order'})
  lost=table[~table.baseline_retained].copy();lost['minute_start']=((lost.start_frame-1)//1800).astype(int)
  w=lost.groupby(['recording','reference_fly_id','minute_start']).agg(excluded_bouts=('source_event_id','size'),source_positive_bout_frames=('duration_frames','sum')).reset_index();w['window_start_seconds']=w.minute_start*60;w['window_end_seconds']=w.window_start_seconds+60;all_windows.append(w)
  identity_summary.append({'recording':rec,'baseline_reliable_identity_frames':int(good.sum()),'candidate_reliable_identity_frames':int(cg.sum()),'supported_bridge_frames':int(candidate['bridged'].sum()),'mapping_corrections_on_bridged_frames':int(candidate['mapping_changed'].sum()),'bridges_accepted':int(attempts.accepted.sum()),'uncertain_frames_remaining':int((~cg).sum()),'baseline_whole_events':len(truth),'candidate_whole_events':len(ct),'raw_same_ID_position_error_median_pixels':float(np.nanmedian(np.linalg.norm(old-new,axis=2))),'aligned_baseline_position_error_median_pixels':float(np.nanmedian(geometry['position_error_pixels'][good]))})
  ct.to_csv(dest/'candidate-whole-expert-events.csv',index=False);cb.to_csv(dest/'candidate-bout-eligibility.csv',index=False)
  cgrid['valid_for_events']=cv.ravel();cgrid.to_parquet(dest/'candidate-coverage.parquet',index=False)
 pd.concat(all_bouts,ignore_index=True).to_csv(DEST/'bout-exclusion-audit.csv',index=False);pd.DataFrame(all_summary).to_csv(DEST/'coverage-by-recording-fly.csv',index=False);pd.DataFrame(all_causes).to_csv(DEST/'causes-by-recording.csv',index=False);pd.concat(all_windows,ignore_index=True).sort_values(['excluded_bouts','source_positive_bout_frames'],ascending=False).to_csv(DEST/'worst-time-windows.csv',index=False);pd.DataFrame(all_intervals).to_csv(DEST/'excluded-intervals.csv',index=False);pd.DataFrame(identity_summary).to_csv(DEST/'identity-candidate-summary.csv',index=False);pd.concat(all_attempts,ignore_index=True).to_csv(DEST/'all-identity-attempts.csv',index=False)
 (DEST/'reason-order.json').write_text(json.dumps({'primary_reason_order':REASONS,'overlapping_counts':'not additive','frame_count_semantics':'Direct reasons count affected frames within a bout. Source-lunge flags, within-bout assignment changes and same-reference closure expose the whole affected bout duration; these are not counts of switch frames.','source_bout_keys':['recording','reference_fly_id','source_event_id'],'window_counts':'bout allocated to 60-second window containing its start, without splitting or double counting'},indent=2))
 print(pd.DataFrame(identity_summary).to_string(index=False),flush=True)
if __name__=='__main__':main()
