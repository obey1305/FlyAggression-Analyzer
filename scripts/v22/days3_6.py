"""Offline V2.2 calibration audit, conservative dataset rebuild, one fit and bounded event search."""
from pathlib import Path
import sys,json,hashlib,time,itertools,tempfile,platform
import numpy as np,pandas as pd,h5py,joblib,sklearn
from scipy.io import loadmat,savemat
from sklearn.base import clone
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT.parent/'flyaggression-v2.1';OUT=ROOT/'reports/v22-days3-6'
sys.path.insert(0,str(BASE/'scripts'));sys.path.insert(0,str(ROOT.parent/'raw-video-integration/day5'))
from adapter import read_and_convert
from prepare_aligned import load_track,annotation_labels,SOURCE
from optimize_days5_7 import event_reference,event_eval,measure_frames
from audit_exclusions import coverage
SCALE={'vel','mean_wing_length','dist_to_wall','dist_to_other','leg_dist'}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def scale_raw(data,names,factor):
 if not np.isfinite(factor) or factor<=0:raise ValueError('Positive finite physical scale factor required')
 out=np.array(data,dtype=float,copy=True)
 for i,n in enumerate(names):
  if n in SCALE:out[:,:,i]*=factor
 return out
def validate_dataset(train,val,names):
 if set(train.recording)&set(val.recording):raise ValueError('Recording leakage')
 for d in [train,val]:
  if d.duplicated(['recording','fly_id','frame']).any():raise ValueError('Duplicate keys')
  if set(d.target_lunge)!={0,1} or not np.isfinite(d[names]).all().all():raise ValueError('Invalid labels or features')
def boundary_labels(n,bouts):
 y=np.zeros(n,dtype=np.int8);unknown=np.zeros(n,bool)
 for a,b,flag in bouts:
  if not np.isfinite([a,b,flag]).all() or a!=int(a) or b!=int(b) or not 1<=a<=b<=n:raise ValueError('Invalid interval')
  y[int(a)-1:int(b)]=1
  if flag!=0:unknown[int(a)-1:int(b)]=True
 y[unknown]=-1
 return y

def native(path):
 if h5py.is_hdf5(path):
  with h5py.File(path) as f:
   g=f['feat'];names=[''.join(chr(int(c)) for c in np.asarray(f[r]).ravel()) for r in np.asarray(g['names']).ravel()];data=np.asarray(g['data']).transpose(2,1,0)
 else:
  f=loadmat(path,simplify_cells=True)['feat'];names=list(f['names']);data=f['data']
 return names,data

def main():
 OUT.mkdir(parents=True,exist_ok=True);dest=ROOT/'data/v22-revised';dest.mkdir(parents=True,exist_ok=True)
 names=json.loads((BASE/'config/feature-columns.json').read_text());baseline=joblib.load(BASE/'models/raw-v2.1/lunge-detector.joblib')
 protocol={'scope':'offline Days3–6; no app integration','training_recordings':['movie1','movie2','movie3','movie4'],'selection_recordings':['movie5'],'untouched_test_recordings':[],'excluded_consumed_recordings':['movie6','movie7','movie8','movie9','movie10'],'scale_factors':[.9,1.,1.1],'scale_experiment':'hypothetical diameter ±10%, fixed tracks/body/contrast; not corrected physical measurement or retracking','annotation_rules':'unchanged source flags and Day1–2 candidate reliability; no unsupported recovery','candidate':'one fresh fit cloning frozen v2.1 estimator settings; no hyperparameter search','seed':501,'frame_threshold':float(baseline['threshold']),'event_grid':{'median_window':[1,3,5],'max_gap_frames':[0,1,2],'min_event_frames':[1,2,3]},'event_iou':.3,'selection':'movie5 event F1, precision, recall descending; smaller median/gap/duration tie','feature_names':names,'baseline_model_sha256':sha(BASE/'models/raw-v2.1/lunge-detector.joblib'),'python':platform.python_version(),'sklearn':sklearn.__version__}
 (ROOT/'config/v22-days3-6.json').write_text(json.dumps(protocol,indent=2)+'\n')
 cal=[];paramrows=[];profiles=[];sensitivity=[];alignment=[];parts={'train':[],'validation':[]};manifest={}
 for rec in protocol['training_recordings']+['movie5']:
  print('Calibration/alignment',rec,flush=True);d=BASE/'data'/rec;folder=OUT/rec;folder.mkdir(exist_ok=True);meta=json.loads((d/'calibration-metadata.json').read_text())
  with h5py.File(d/'calibration.mat') as f:
   g=f['calib'];ppm=float(g['PPM'][0,0]);radius=float(g['r'][0,0]);fps=float(g['FPS'][0,0]);pars={k:np.asarray(v).tolist() for k,v in g['params'].items() if isinstance(v,h5py.Dataset) and v.dtype.kind not in 'OV'}
   for k,v in pars.items():paramrows.append({'recording':rec,'parameter':k,'value':json.dumps(v)})
  assert abs(2*radius/meta['arena_diameter_mm']-ppm)<1e-12 and abs(ppm-meta['pixels_per_mm'])<1e-12 and fps==meta['fps']==30
  cal.append({'recording':rec,'radius_pixels':radius,'diameter_mm_nominal':meta['arena_diameter_mm'],'pixels_per_mm':ppm,'fps':fps,'physical_measurement_verified':False,'diameter_evidence':'existing published nominal cohort provenance only; no per-recording measurement found','boundary_edge_support':meta['boundary_edge_support'],'body_mean_area_pixels':float(np.asarray(pars['mean_area']).ravel()[0]),'body_mean_major_axis_pixels':float(np.asarray(pars['mean_major_axis']).ravel()[0]),'contrast_threshold':float(np.asarray(pars['contrast_th']).ravel()[0]),'calibration_sha256':sha(d/'calibration.mat'),'raw_features_sha256':sha(d/'raw-features.mat'),'features36_sha256':sha(d/'features36.mat')})
  raw_names,raw=native(d/'raw-features.mat');fn,original,_=read_and_convert(d/'raw-features.mat');saved=loadmat(d/'features36.mat',simplify_cells=True)['feat'];assert fn==names==list(saved['names']);np.testing.assert_allclose(original,saved['data'],rtol=0,atol=0,equal_nan=True)
  for j,n in enumerate(names):
   x=original[:,:,j];v=x[np.isfinite(x)];q=np.quantile(v,[.01,.25,.5,.75,.99]);profiles.append({'recording':rec,'feature':n,'finite_fraction':float(np.isfinite(x).mean()),**dict(zip(['q01','q25','median','q75','q99'],map(float,q)))})
  with tempfile.TemporaryDirectory(prefix='v22-scale-') as tmp:
   for factor in [.9,1.1]:
    p=Path(tmp)/'scaled.mat';savemat(p,{'feat':{'names':np.array(raw_names,dtype=object),'data':scale_raw(raw,raw_names,factor)}});_,converted,_=read_and_convert(p)
    for j,n in enumerate(names):
     diff=converted[:,:,j]-original[:,:,j];finite=np.isfinite(diff);v=original[:,:,j];iqr=float(np.nanquantile(v,.75)-np.nanquantile(v,.25));sensitivity.append({'recording':rec,'feature':n,'diameter_factor':factor,'median_absolute_change':float(np.median(np.abs(diff[finite]))),'maximum_absolute_change':float(np.max(np.abs(diff[finite]))),'median_absolute_change_over_baseline_iqr':float(np.median(np.abs(diff[finite]))/max(iqr,1e-12)),'interpretation':'fixed-track hypothetical scale perturbation'})
  corr=pd.read_parquet(ROOT/f'reports/v22-days1-2/{rec}/identity-correspondence.parquet');mapping=corr.candidate_new_fly1_reference.to_numpy()-1;good=corr.candidate_identity_reliable.to_numpy();src=loadmat(SOURCE/rec/(rec+'_actions.mat'),simplify_cells=True);y=annotation_labels(src,original.shape[1]);source_bouts=pd.read_csv(d/'aligned-lunge-bouts.csv')
  # Independently check source endpoint inclusivity and unknown/flag override semantics.
  for ref in [0,1]:
   bouts=np.asarray(src['bouts'][ref,list(src['behs']).index('lunge')]).reshape(-1,3);simple=boundary_labels(original.shape[1],bouts)
   for j,beh in enumerate(src['behs']):
    for a,b,flag in np.asarray(src['bouts'][ref,j]).reshape(-1,3):
     if beh=='unknown' or flag!=0:simple[int(a)-1:int(b)]=-1
   np.testing.assert_array_equal(simple,y[ref])
  grid,bouts,valid,truth=coverage(rec,original,mapping,good,y,source_bouts);bouts.to_csv(folder/'revised-bout-eligibility.csv',index=False);truth.to_csv(folder/'expert-events.csv',index=False)
  grid['valid_for_events']=valid.ravel();grid.to_parquet(folder/'evaluation-coverage.parquet',index=False)
  split='validation' if rec=='movie5' else 'train';recordparts=[]
  for fly in [0,1]:
   df=pd.read_parquet(d/f'full-grid-fly{fly+1}.parquet');reference=np.where(mapping==0,fly,1-fly);labels=y[reference,np.arange(len(df))];eligible=good&(labels>=0)&np.isfinite(original[fly]).all(axis=1)
   df['reference_fly_id']=reference+1;df['alignment_reliable']=good;df['eligible']=eligible;df['target_lunge']=np.where(eligible,labels,-1);df['source_lunge_label']=labels
   df.to_parquet(dest/f'{rec}-fly{fly+1}.parquet',index=False);recordparts.append(df);parts[split].append(df.loc[eligible,names+['recording','split','fly_id','frame','reference_fly_id','target_lunge']])
  rebuilt=pd.concat(recordparts,ignore_index=True);old=pd.read_parquet(d/'eligible.parquet');new=rebuilt.loc[rebuilt.eligible,names+['recording','split','fly_id','frame','reference_fly_id','target_lunge']].reset_index(drop=True);pd.testing.assert_frame_equal(new,old.reset_index(drop=True))
  prior=pd.read_csv(BASE/f'reports/days5-7/{rec}/expert-events.csv');assert set(prior.event_id)==set(truth.event_id)
  oldoffset=pd.read_csv(d/'frame-offset-diagnostic.csv');oldxy,*_=load_track(SOURCE/rec/(rec+'_track.mat'));newxy,*_=load_track(d/'tracks.mat');offsets=[]
  for shift in [-3,-2,-1,0,1,2,3]:
   lo=max(0,-shift);hi=min(len(corr),len(corr)-shift);a=oldxy[:,lo:hi];b=newxy[:,lo+shift:hi+shift];v=np.minimum(np.linalg.norm(a-b,axis=2).sum(axis=0),np.linalg.norm(a-b[::-1],axis=2).sum(axis=0));offsets.append(float(np.nanmedian(v)))
  np.testing.assert_allclose(offsets,oldoffset.median_best_pair_error_pixels,rtol=0,atol=1e-12)
  pd.DataFrame({'offset':range(-3,4),'median_pair_error_pixels':offsets}).to_csv(folder/'frame-offsets.csv',index=False)
  alignment.append({'recording':rec,'source_bouts':len(source_bouts),'retained_expert_bouts':len(truth),'recovered_bouts':0,'remaining_excluded_bouts':len(source_bouts)-len(truth),'eligible_frames':len(new),'positive_frames':int(new.target_lunge.sum()),'best_offset':int(np.argmin(offsets)-3),'zero_offset_error':offsets[3],'dataset_identical_to_v21':True})
 for split,pieces in parts.items():
  df=pd.concat(pieces,ignore_index=True);p=dest/f'{split}.parquet';df.to_parquet(p,index=False);manifest[str(p.relative_to(ROOT))]=sha(p)
 pd.DataFrame(cal).to_csv(OUT/'calibration-audit.csv',index=False);pd.DataFrame(paramrows).to_csv(OUT/'body-contrast-parameters.csv',index=False);pd.DataFrame(profiles).to_csv(OUT/'feature-distributions.csv',index=False);pd.DataFrame(sensitivity).to_csv(OUT/'scale-sensitivity.csv',index=False);pd.DataFrame(alignment).to_csv(OUT/'alignment-summary.csv',index=False)
 (OUT/'dataset-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 train=pd.read_parquet(dest/'train.parquet');val=pd.read_parquet(dest/'validation.parquet');validate_dataset(train,val,names)
 print('Fresh fit',len(train),'rows',flush=True);pipe=clone(baseline['pipeline']);start=time.monotonic();pipe.fit(train[names],train.target_lunge);fitsec=time.monotonic()-start
 np.testing.assert_array_equal(pipe.named_steps['imputer'].statistics_,np.median(train[names],axis=0))
 modeldir=ROOT/'models/raw-v2.2-candidate';modeldir.mkdir(parents=True,exist_ok=True)
 g=pd.concat([pd.read_parquet(dest/f'movie5-fly{fly}.parquet') for fly in [1,2]],ignore_index=True);v=pd.read_parquet(OUT/'movie5/evaluation-coverage.parquet').valid_for_events.to_numpy();truth=pd.read_csv(OUT/'movie5/expert-events.csv');mask=g.eligible.to_numpy();p=pipe.predict_proba(g[names])[:,list(pipe.classes_).index(1)];bp=baseline['pipeline'].predict_proba(g[names])[:,list(baseline['pipeline'].classes_).index(1)];threshold=protocol['frame_threshold']
 frame={'candidate':measure_frames(g.loc[mask,'target_lunge'],p[mask],threshold),'v21':measure_frames(g.loc[mask,'target_lunge'],bp[mask],threshold)}
 searches=[]
 for median,gap,duration in itertools.product([1,3,5],[0,1,2],[1,2,3]):
  rules={'median_window':median,'max_gap_frames':gap,'min_event_frames':duration};m,*_=event_eval(g,p,v,truth,rules,threshold);searches.append({**rules,**m})
 search=pd.DataFrame(searches).sort_values(['f1','precision','recall','median_window','max_gap_frames','min_event_frames'],ascending=[False,False,False,True,True,True]);search.to_csv(OUT/'event-search.csv',index=False);rules={k:int(search.iloc[0][k]) for k in ['median_window','max_gap_frames','min_event_frames']}
 comparisons=[]
 for tag,prob,rr in [('v21',bp,baseline['event_rules']),('candidate',p,rules)]:
  em,pred,processed,matches,po,go=event_eval(g,prob,v,truth,rr,threshold);comparisons.append({'model':tag,'recording':'movie5','scope':'development selection, not independent validation',**{'frame_'+k:frame[tag][k] for k in ['precision','recall','f1']},**{'event_'+k:value for k,value in em.items()}})
  for name,df in [('events',pred),('processed',processed),('matches',matches),('prediction-outcomes',po),('expert-outcomes',go)]:df.to_csv(OUT/f'{tag}-{name}.csv',index=False)
  timing=matches.copy()
  if len(timing):
   # Explicitly join matched event endpoints instead of assuming match table naming.
   timing.to_csv(OUT/f'{tag}-matched-timing-input.csv',index=False)
 bundle={**baseline,'pipeline':pipe,'threshold':threshold,'event_rules':rules,'release_version':'2.2-days3-6-candidate','release_status':'offline-development-candidate-not-integrated','training_protocol':protocol,'scientific_status':'development movie5, unchanged calibration uncertainty and coverage; not independent accuracy'}
 bundle.pop('development_protocol',None);bundle['candidate_id']='v22-same-settings-fresh-fit';bundle['validation_metrics']=frame['candidate']
 path=modeldir/'lunge-detector.joblib';joblib.dump(bundle,path,compress=3);reload=joblib.load(path);np.testing.assert_allclose(reload['pipeline'].predict_proba(g[names])[:,1],p,rtol=0,atol=1e-14)
 configuration={'version':'2.2-days3-6-candidate','threshold':threshold,'event_rules':rules,'feature_names':names,'model_sha256':sha(path),'protocol_sha256':sha(ROOT/'config/v22-days3-6.json'),'baseline_model_sha256':protocol['baseline_model_sha256'],'integration_status':'not integrated','selection_scope':'movie5 development','fit_seconds':fitsec}
 (modeldir/'configuration.json').write_text(json.dumps(configuration,indent=2)+'\n');(modeldir/'freeze-manifest.json').write_text(json.dumps({'files':{n:sha(modeldir/n) for n in ['lunge-detector.joblib','configuration.json']}},indent=2)+'\n')
 scores=g[['recording','fly_id','frame','eligible','target_lunge']].copy();scores['candidate_probability']=p;scores['v21_probability']=bp;scores.to_parquet(OUT/'movie5-probabilities.parquet',index=False)
 pd.DataFrame(comparisons).to_csv(OUT/'comparison.csv',index=False)
 result={'status':'PASS','fit_seconds':fitsec,'training_rows':len(train),'training_positive_frames':int(train.target_lunge.sum()),'validation_rows':len(val),'validation_positive_frames':int(val.target_lunge.sum()),'training_only_imputer_verified':True,'max_probability_difference_vs_v21':float(np.max(np.abs(p-bp))),'frame_metrics':frame,'event_rules':rules,'recovered_bouts':0,'physical_scale_verified':False,'classifier_fits':1,'temporal_configurations':27,'model_reload_verified':True,'independent_test':False}
 (OUT/'results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2),flush=True)
if __name__=='__main__':main()
