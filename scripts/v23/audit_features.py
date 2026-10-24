"""Tracking/feature compatibility audit. Never loads or invokes a classifier."""
from pathlib import Path
import sys,json,hashlib
import numpy as np,pandas as pd
from scipy.io import savemat,loadmat
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT.parent;R=ROOT/'reports/v23-days1-4';D=ROOT/'data/v23-derived'
sys.path[:0]=[str(ROOT/'scripts'),str(OUT/'raw-video-integration/day5')]
from prepare_aligned import align_positions,ranges
from tracking_io import load_track
from adapter import read_and_convert,STATUS

def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def profile(x):
 v=x[np.isfinite(x)]
 return dict(zip(['q01','q25','median','q75','q99'],map(float,np.quantile(v,[.01,.25,.5,.75,.99])))) if len(v) else {k:None for k in ['q01','q25','median','q75','q99']}
def save_derived_features(path,names,data,units):
 savemat(path,{'feat':{'names':np.array(names,dtype=object),'units':np.array(units,dtype=object),'data':data,'integration_status':STATUS}},do_compression=True)
def main():
 D.mkdir(exist_ok=True);track=ROOT/'data/v23-tracking/movie5-analysis30/movie5-analysis30-track.mat';raw=track.with_name('movie5-analysis30-feat.mat')
 names,data,units=read_and_convert(raw);expected=json.loads((ROOT/'config/feature-columns.json').read_text());assert names==expected and data.shape==(2,38390,36)
 save_derived_features(D/'features36.mat',names,data,units)
 m=pd.read_csv(R/'frame-time-map.csv');idx=m.source_frame.to_numpy()-1
 old,ow,ot,on=load_track(OUT/'new-training-data/BoyMeetsBoy/extracted/Boy_meets_boy light/movie5/movie5_track.mat');new,nw,nt,nn=load_track(track)
 assert new.shape==(2,38390,2)
 # Warning coverage: retain any flagged native frame in the nearest analysis-time bin,
 # including flags that fall between sampled source indices.
 b=np.minimum(np.floor(np.arange(len(ow))*30/200+.5).astype(int),len(m)-1);mapped_ow=np.zeros(len(m),bool);np.logical_or.at(mapped_ow,b,ow)
 cfg=json.loads((ROOT/'config/preparation.json').read_text())['alignment'];mapping,good,diag=align_positions(old[:,idx],new,mapped_ow,nw,cfg)
 offsets=[]
 for shift in range(-3,4):
  lo=max(0,-shift);hi=min(len(m),len(m)-shift);aa=old[:,idx[lo:hi]];bb=new[:,lo+shift:hi+shift];direct=np.linalg.norm(aa-bb,axis=2).sum(axis=0);swap=np.linalg.norm(aa-bb[::-1],axis=2).sum(axis=0);err=np.minimum(direct,swap);offsets.append({'new_analysis_frame_offset':shift,'median_best_pair_error_pixels':float(np.nanmedian(err))})
 pd.DataFrame(offsets).to_csv(R/'frame-offset-diagnostic.csv',index=False)
 zero=offsets[3]['median_best_pair_error_pixels'];excess=zero-min(x['median_best_pair_error_pixels'] for x in offsets);timing_review=excess>.05
 if timing_review:good[:]=False
 audit=pd.DataFrame({'analysis_frame':np.arange(1,len(m)+1),'source_frame':idx+1,'new_fly1_reference_id':mapping+1,'conservative_geometric_mapping_reliable':good,'reference_warning_in_time_bin':mapped_ow,'new_tracking_warning':nw,**diag});audit.to_csv(R/'trajectory-comparison.csv',index=False)
 intervals=[]
 for state in (0,1):
  for a,b in ranges(good&(mapping==state)):intervals.append({'start_analysis_frame':a+1,'end_analysis_frame':b,'new_fly1_reference_id':state+1,'evidence':'stable geometric correspondence only; neither source identity biologically certified'})
 pd.DataFrame(intervals).to_csv(R/'geometric-mapping-intervals.csv',index=False)
 training=pd.read_parquet(OUT/'flyaggression-v2.2/data/v22-revised/train.parquet',columns=names)
 profiles=[]
 for j,name in enumerate(names):
  q=profile(training[name].to_numpy());scale=q['q75']-q['q25']
  for fly in range(2):
   x=data[fly,:,j];p=profile(x);finite=x[np.isfinite(x)];profiles.append({'feature':name,'fly_id':fly+1,'transformed_unit':units[j],'nan':int(np.isnan(x).sum()),'inf':int(np.isinf(x).sum()),**p,**{'training_'+k:v for k,v in q.items()},'median_shift_training_iqr':(p['median']-q['median'])/scale if p['median'] is not None and scale>0 else None,'fraction_outside_training_q01_q99':float(((finite<q['q01'])|(finite>q['q99'])).mean()) if len(finite) else None})
 pd.DataFrame(profiles).to_csv(R/'feature-distribution-comparison.csv',index=False)
 missing=[];missing_intervals=[]
 for fly in range(2):
  bad=~np.isfinite(new[fly]).all(axis=1)
  for origin,mask in [('new_xy',bad),('sampled_reference_xy',~np.isfinite(old[fly,idx]).all(axis=1)),('new_36features',~np.isfinite(data[fly]).all(axis=1))]:
   for start,stop in ranges(mask):missing_intervals.append({'fly':fly+1,'origin':origin,'start_analysis_frame':int(start+1),'end_analysis_frame':int(stop),'start_seconds':float(start/30),'stop_exclusive_seconds':float(stop/30),'frames':int(stop-start)})
  missing.append({'fly':fly+1,'missing_position_frames':int(bad.sum()),'missing_with_both_reference_positions_finite':int((bad&np.isfinite(old[:,idx]).all(axis=(0,2))).sum()),'missing_with_any_reference_position_nonfinite':int((bad&~np.isfinite(old[:,idx]).all(axis=(0,2))).sum()),'longest_missing_position_gap_frames':int(max([b-a for a,b in ranges(bad)],default=0)),'nonfinite_36feature_rows':int((~np.isfinite(data[fly]).all(axis=1)).sum())})
 pd.DataFrame(missing_intervals).to_csv(R/'missing-data-intervals.csv',index=False)
 e=diag['position_error_pixels'];finite=e[np.isfinite(e)];result={'status':'tracking and schema extraction completed; scientific compatibility remains qualified','raw_feature_shape':[2,38390,13],'converted_shape':list(data.shape),'feature_names_and_order_match':True,'model_inference_performed':False,'training_performed':False,'identity_corrections_applied':False,'reference_warning_time_bins':int(mapped_ow.sum()),'new_tracking_warning_frames':int(nw.sum()),'finite_position_comparison_frames':int(len(finite)),'best_assignment_max_per_fly_error_pixels_quantiles':profile(finite),'conservative_geometric_mapping_reliable_frames':int(good.sum()),'conservative_geometric_mapping_reliable_fraction':float(good.mean()),'best_assignment_changes':int((np.diff(mapping)!=0).sum()),'assignment_changes_warning':'Changes include ambiguous close interactions and missing values; not a certified identity-switch count','mapping_rules':cfg,'frame_offset_diagnostic':offsets,'zero_offset_excess_median_pair_error_pixels':excess,'timing_alignment_review_required':timing_review,'missingness':missing,'normalization':'Pinned adapter, whole-recording per-fly median/log transforms and fixed five-sample derivatives; no fitted imputer or scaler. Upstream feat_compute interpolates internal gaps, so finite features do not certify valid original tracking.','wall_distance':'Excluded from36 schema; padded tracking-mask distance is not a physical wall measurement','files':{str(p.relative_to(ROOT)):sha(p) for p in [track,raw,D/'features36.mat']}}
 (R/'feature-compatibility.json').write_text(json.dumps(result,indent=2)+'\n');(D/'features36.json').write_text(json.dumps({'source_sha256':sha(raw),'output_sha256':sha(D/'features36.mat'),'fps':30,'physical_scale':'nominal12pixels/mm','scientific_compatibility_verified':False,'feature_names':names,'units':units,'identity_policy':'Unchanged FlyTracker IDs; inspect trajectory-comparison.csv; no forced reassignment'},indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
