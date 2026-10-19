"""Bounded development experiments. Fit only movies1–4; all selection uses movie5."""
from pathlib import Path
import sys,json,time,itertools,hashlib,importlib.util
import numpy as np,pandas as pd,joblib
from sklearn.metrics import precision_score,recall_score,f1_score,confusion_matrix,average_precision_score
from train_day4 import make_pipeline,validate_splits,sha
ROOT=Path(__file__).resolve().parents[1];OLD=ROOT.parent/'drosophila-aggression/models/final-v1';DEST=ROOT/'reports/days5-7'
spec=importlib.util.spec_from_file_location('frozen_event_detection',OLD/'runtime/scripts/event_detection.py');event=importlib.util.module_from_spec(spec);spec.loader.exec_module(event)
THRESHOLDS=[.1,.15,.2,.25,.3,.4,.5]
VARIANTS={'day4':{},'balanced':{'class_weight':'balanced'},'deep':{'max_depth':None,'min_samples_leaf':1},'subsample':{'class_weight':'balanced_subsample','min_samples_leaf':4}}
def measure_frames(y,p,t):
 y=np.asarray(y);p=np.asarray(p);pred=p>=t
 return {'threshold':float(t),'frames':len(y),'positive_frames':int(y.sum()),'predicted_positive_frames':int(pred.sum()),'confusion_matrix':confusion_matrix(y,pred,labels=[0,1]).tolist(),'precision':float(precision_score(y,pred,zero_division=0)),'recall':float(recall_score(y,pred,zero_division=0)),'f1':float(f1_score(y,pred,zero_division=0)),'average_precision':float(average_precision_score(y,p))}
def event_reference(grid,bouts):
 """Common conservative coverage; never split original expert endpoints."""
 valid=grid.eligible.to_numpy(bool).copy();b=bouts.copy();keep=b.whole_bout_eligible.to_numpy(bool).copy()
 # Uncertain identity can belong to either stream: censor both over its whole bout.
 while True:
  before=valid.copy();previous=keep.copy()
  for i,row in enumerate(b.itertuples()):
   inside=grid.frame.between(row.start_frame,row.end_frame).to_numpy()
   mapped=inside&grid.fly_id.eq(row.new_fly_id).to_numpy()
   if not keep[i] or not mapped.any() or not valid[mapped].all():
    keep[i]=False;valid[inside]=False
  if np.array_equal(before,valid) and np.array_equal(previous,keep):break
 cols=['recording','source_event_id','new_fly_id','start_frame','end_frame']+(['reference_fly_id'] if 'reference_fly_id' in b else [])
 truth=b.loc[keep,cols].rename(columns={'new_fly_id':'fly_id'}).copy()
 if 'reference_fly_id' not in truth:truth['reference_fly_id']=1
 truth['event_id']=truth.source_event_id+(truth.reference_fly_id-1)*1000000
 if truth.duplicated(['recording','fly_id','event_id']).any():raise ValueError('Duplicate compound source event keys')
 return valid,truth

def event_eval(grid,p,valid,truth,rules,threshold):
 scores=grid[['recording','fly_id','frame']].copy();scores['probability_lunge']=p;scores['valid_for_events']=valid
 predicted,processed=event.detect_events(scores,threshold=threshold,**rules)
 metrics,matches,po,go=event.match_events(predicted,truth,.3)
 # Fragmentation: expert event touched by >1 prediction, regardless of matching.
 fragments=sum(sum((predicted.recording.eq(r.recording)&predicted.fly_id.eq(r.fly_id)&predicted.start_frame.le(r.end_frame)&predicted.end_frame.ge(r.start_frame)))>1 for r in truth.itertuples())
 metrics['fragmented_expert_events']=int(fragments)
 return metrics,predicted,processed,matches,po,go

def main():
 DEST.mkdir(parents=True,exist_ok=True);(ROOT/'models/candidates').mkdir(parents=True,exist_ok=True)
 for n,info in json.loads((ROOT/'reports/data-manifest.json').read_text())['data_files'].items():assert sha(ROOT/n)==info['sha256'],n
 names=json.loads((ROOT/'config/feature-columns.json').read_text());train=pd.read_parquet(ROOT/'data/train.parquet');val=pd.read_parquet(ROOT/'data/validation.parquet');validate_splits(train,val,names)
 assert set(train.recording)=={'movie1','movie2','movie3','movie4'} and set(val.recording)=={'movie5'}
 protocol={'training_recordings':['movie1','movie2','movie3','movie4'],'selection_recordings':['movie5'],'untouched_test_recordings':[],'excluded_consumed_recordings':['movie6','movie7','movie8','movie9','movie10'],'additional_fits':3,'variants':VARIANTS,'thresholds':THRESHOLDS,'threshold_selection':'frame F1, precision, recall descending; candidate ID ascending; higher threshold tie','event_grid':{'median_window':[1,3,5],'max_gap_frames':[0,1,2],'min_event_frames':[1,2,3]},'event_selection':'event F1, precision, recall descending; smaller median, gap, duration tie','event_iou':.3,'coverage':'same conservative whole-bout overlap closure for all models; uncertain source bouts censor both streams','labels':'provided mapped expert intervals; no new manual biology labels','fit_preprocessing':'training rows only','feature_names':names,'random_seed':501,'data_sha256':{n:sha(ROOT/'data'/n) for n in ['train.parquet','validation.parquet']}}
 (ROOT/'config/days5-7-protocol.json').write_text(json.dumps(protocol,indent=2))
 base=joblib.load(ROOT/'models/day4-raw-random-forest.joblib');old=joblib.load(OLD/'lunge-detector.joblib');bundles={'day4':base};rows=[];valp={};fits={}
 y=train.target_lunge.to_numpy()
 for name,params in VARIANTS.items():
  if name!='day4':
   cache=ROOT/f'models/candidates/{name}.joblib'
   if '--resume' in sys.argv and cache.exists():
    b=joblib.load(cache);assert b['training_protocol']==protocol and b['candidate_id']==name
    fits[name]=b.get('fit_seconds');print('Reused verified completed fit',name,flush=True)
   else:
    print('Fitting',name,flush=True);pipe=make_pipeline(y);pipe.set_params(**{'classifier__'+k:v for k,v in params.items()});start=time.monotonic();pipe.fit(train[names],y);fits[name]=time.monotonic()-start
    b={k:v for k,v in base.items() if k not in ['pipeline','validation_metrics','training_protocol']};b.update(pipeline=pipe,release_status='development-candidate',training_protocol=protocol,candidate_id=name,fit_seconds=fits[name]);joblib.dump(b,cache,compress=3)
   bundles[name]=b
  pipe=bundles[name]['pipeline'];np.testing.assert_array_equal(pipe.named_steps['imputer'].statistics_,np.median(train[names].to_numpy(),axis=0));p=pipe.predict_proba(val[names])[:,1];valp[name]=p
  for t in THRESHOLDS:rows.append({'candidate':name,**measure_frames(val.target_lunge,p,t)})
  print(name,'complete',flush=True)
 table=pd.DataFrame(rows);table.sort_values(['f1','precision','recall','candidate','threshold'],ascending=[False,False,False,True,False]).to_json(DEST/'frame-search.json',orient='records',indent=2)
 flat=table.drop(columns=['confusion_matrix']);flat.to_csv(DEST/'frame-search.csv',index=False)
 win=table.sort_values(['f1','precision','recall','candidate','threshold'],ascending=[False,False,False,True,False]).iloc[0];chosen=str(win.candidate);threshold=float(win.threshold);selected=bundles[chosen]
 print('Selected frame candidate',chosen,'threshold',threshold,'F1',win.f1,flush=True)
 # Error diagnosis and feature shift summaries: descriptive only, no additional fits.
 errors=val[['recording','fly_id','frame','reference_fly_id','target_lunge']].copy();errors['probability_lunge']=valp[chosen];errors['prediction']=errors.probability_lunge.ge(threshold);errors['outcome']=np.where(errors.target_lunge.eq(1),np.where(errors.prediction,'TP','FN'),np.where(errors.prediction,'FP','TN'))
 audit=pd.read_parquet(ROOT/'data/movie5/alignment-audit.parquet');errors=errors.merge(audit,on='frame',validate='many_to_one');errors.to_csv(DEST/'validation-frame-outcomes.csv',index=False)
 profiles=[]
 for rec,d in pd.concat([train,val]).groupby('recording'):
  for n in names:
   q=d[n].quantile([.01,.25,.5,.75,.99]);tq=train[n].quantile([.25,.5,.75]);profiles.append({'recording':rec,'feature':n,'q01':q.loc[.01],'q25':q.loc[.25],'median':q.loc[.5],'q75':q.loc[.75],'q99':q.loc[.99],'median_shift_training_iqr':float((q.loc[.5]-tq.loc[.5])/max(tq.loc[.75]-tq.loc[.25],1e-12))})
 pd.DataFrame(profiles).to_csv(DEST/'feature-profiles.csv',index=False)
 diagnostics=[]
 for n in names:
  row={'feature':n,'fitted_importance':selected['pipeline'].named_steps['classifier'].feature_importances_[names.index(n)]}
  for outcome in ['TP','FN','FP','TN']:row[outcome+'_median']=float(val.loc[errors.outcome.eq(outcome).to_numpy(),n].median())
  diagnostics.append(row)
 pd.DataFrame(diagnostics).sort_values('fitted_importance',ascending=False).to_csv(DEST/'feature-error-diagnostics.csv',index=False)
 errors.groupby('outcome')[['position_error_pixels','assignment_margin_pixels','separation_pixels']].agg(['count','median','max']).to_csv(DEST/'tracking-error-diagnostics.csv')
 grid=pd.concat([pd.read_parquet(ROOT/f'data/movie5/full-grid-fly{i}.parquet') for i in [1,2]],ignore_index=True);bouts=pd.read_csv(ROOT/'data/movie5/aligned-lunge-bouts.csv');valid,truth=event_reference(grid,bouts)
 p=selected['pipeline'].predict_proba(grid[names])[:,1];eventrows=[]
 for median,gap,duration in itertools.product([1,3,5],[0,1,2],[1,2,3]):
  rules={'median_window':median,'max_gap_frames':gap,'min_event_frames':duration};metrics,*_=event_eval(grid,p,valid,truth,rules,threshold);eventrows.append({**rules,**metrics})
 er=pd.DataFrame(eventrows).sort_values(['f1','precision','recall','median_window','max_gap_frames','min_event_frames'],ascending=[False,False,False,True,True,True]);er.to_csv(DEST/'event-search.csv',index=False)
 rules={k:int(er.iloc[0][k]) for k in ['median_window','max_gap_frames','min_event_frames']};print('Selected event rules',rules,'F1',er.iloc[0].f1,flush=True)
 selected={**selected,'threshold':threshold,'event_rules':rules,'release_version':'2.1.0','release_status':'frozen-development-selection','candidate_id':chosen,'development_protocol':protocol,'validation_metrics':measure_frames(val.target_lunge,valp[chosen],threshold),'scientific_status':'development validation; selected uncertain-frame subset; no untouched final test'}
 release=ROOT/'models/raw-v2.1';release.mkdir(exist_ok=True);model=release/'lunge-detector.joblib';joblib.dump(selected,model,compress=3)
 config={'release_version':'2.1.0','candidate_id':chosen,'threshold':threshold,'event_rules':rules,'source_feature_names':names,'feature_engineering_version':0,'mode':'raw-video-only','model_sha256':sha(model),'adapter_sha256':sha(ROOT.parent/'raw-video-integration/day5/adapter.py'),'training_recordings':protocol['training_recordings'],'selection_recordings':['movie5'],'scientific_status':selected['scientific_status'],'protocol_sha256':sha(ROOT/'config/days5-7-protocol.json'),'fit_seconds':fits}
 (release/'configuration.json').write_text(json.dumps(config,indent=2))
 comparisons=[]
 # Every per-record training result is explicitly labelled resubstitution, not validation.
 for rec in protocol['training_recordings']+['movie5']:
  g=pd.concat([pd.read_parquet(ROOT/f'data/{rec}/full-grid-fly{i}.parquet') for i in [1,2]],ignore_index=True);v,gt=event_reference(g,pd.read_csv(ROOT/f'data/{rec}/aligned-lunge-bouts.csv'));folder=DEST/rec;folder.mkdir(exist_ok=True)
  coverage=g[['recording','fly_id','frame','eligible']].copy();coverage['valid_for_events']=v;coverage.to_parquet(folder/'evaluation-coverage.parquet',index=False);gt.to_csv(folder/'expert-events.csv',index=False)
  for tag,b in [('original',old),('day4',base),('selected',selected)]:
   prob=b['pipeline'].predict_proba(g[names].replace([np.inf,-np.inf],np.nan))[:,1];m=g.eligible.to_numpy(bool);fm=measure_frames(g.loc[m,'target_lunge'],prob[m],b['threshold']);em,pred,processed,matches,po,go=event_eval(g,prob,v,gt,b['event_rules'],b['threshold'])
   row={'recording':rec,'model':tag,'split':'development-validation' if rec=='movie5' else 'training-resubstitution','eligible_frame_rows':int(m.sum()),'event_scorable_rows':int(v.sum()),'source_bouts':len(pd.read_csv(ROOT/f'data/{rec}/aligned-lunge-bouts.csv')),'retained_expert_events':len(gt),**{'frame_'+k:fm[k] for k in ['precision','recall','f1','average_precision']},**{'event_'+k:em[k] for k in em}}
   comparisons.append(row)
   for suffix,df in [('predicted-events',pred),('matches',matches),('prediction-outcomes',po),('expert-outcomes',go)]:df.to_csv(folder/f'{tag}-{suffix}.csv',index=False)
   saved=g[['recording','fly_id','frame']].copy();saved['probability_lunge']=prob;saved['eligible_for_frame_metrics']=m;saved['valid_for_events']=v;saved.to_parquet(folder/f'{tag}-full-grid-probabilities.parquet',index=False)
 comparison=pd.DataFrame(comparisons);comparison.to_csv(DEST/'comparison-by-recording.csv',index=False)
 reloaded=joblib.load(model);np.testing.assert_allclose(reloaded['pipeline'].predict_proba(grid[names])[:,1],p,rtol=0,atol=1e-14)
 frozen={'files':{n:sha(release/n) for n in ['lunge-detector.joblib','configuration.json']},'validation_scope':'development movie5; no independent test','selection_complete':True}
 (release/'freeze-manifest.json').write_text(json.dumps(frozen,indent=2));print(comparison[comparison.recording.eq('movie5')].to_string(index=False),flush=True)
if __name__=='__main__':main()
