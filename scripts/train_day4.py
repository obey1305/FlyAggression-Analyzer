"""Single predeclared raw-feature baseline. No threshold or parameter search."""
from pathlib import Path
import hashlib,json,time,platform
import numpy as np,pandas as pd,joblib,sklearn
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix,precision_score,recall_score,f1_score,average_precision_score
ROOT=Path(__file__).resolve().parents[1]
OLD=ROOT.parent/'drosophila-aggression/models/final-v1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def validate_splits(train,val,names):
 if set(train.recording)&set(val.recording):raise ValueError('Recording leakage')
 for d in (train,val):
  if len(names)!=len(set(names)) or not np.isfinite(d[names].to_numpy()).all():raise ValueError('Invalid predictors')
  if set(d.target_lunge)!={0,1}:raise ValueError('Both binary classes required')
  if d.duplicated([c for c in ['recording','fly_id','frame'] if c in d]).any():raise ValueError('Duplicate row keys')
def make_pipeline(y):
 weight=float(np.sqrt(np.sum(y==0)/np.sum(y==1)))
 return Pipeline([('imputer',SimpleImputer(strategy='median',keep_empty_features=True)),('classifier',RandomForestClassifier(n_estimators=128,max_depth=20,min_samples_leaf=2,max_features='sqrt',bootstrap=True,class_weight={0:1.,1:weight},random_state=501,n_jobs=4))])
def frame_metrics(y,p):
 pred=p>=.5
 return {'frames':len(y),'positive_frames':int(np.sum(y==1)),'predicted_positive_frames':int(pred.sum()),'confusion_matrix':confusion_matrix(y,pred,labels=[0,1]).tolist(),'precision':float(precision_score(y,pred,zero_division=0)),'recall':float(recall_score(y,pred,zero_division=0)),'f1':float(f1_score(y,pred,zero_division=0)),'average_precision':float(average_precision_score(y,p))}
def main():
 dest=ROOT/'reports/day4';dest.mkdir(parents=True,exist_ok=True);models=ROOT/'models';models.mkdir(exist_ok=True)
 manifest=json.loads((ROOT/'reports/data-manifest.json').read_text())['data_files']
 for name,item in manifest.items():
  if sha(ROOT/name)!=item['sha256']:raise ValueError('Dataset hash mismatch: '+name)
 preserve=json.loads((ROOT/'config/preservation.json').read_text())
 def check_frozen():
  for name,h in preserve['frozen_files'].items():
   if sha(OLD/name)!=h:raise ValueError('Frozen model changed: '+name)
 check_frozen()
 names=json.loads((ROOT/'config/feature-columns.json').read_text());train=pd.read_parquet(ROOT/'data/train.parquet');val=pd.read_parquet(ROOT/'data/validation.parquet')
 validate_splits(train,val,names)
 assert set(train.recording)=={'movie1','movie2','movie3','movie4'} and set(val.recording)=={'movie5'}
 y=train.target_lunge.to_numpy();pipeline=make_pipeline(y)
 protocol={'candidate':'day4-raw-random-forest','training_recordings':sorted(train.recording.unique()),'validation_recordings':['movie5'],'feature_names':names,'n_estimators':128,'max_depth':20,'min_samples_leaf':2,'max_features':'sqrt','random_state':501,'n_jobs':4,'class_weights':pipeline.named_steps['classifier'].class_weight,'weight_rule':'negative=1; positive=sqrt(training_negative/training_positive)','preprocessing':'median imputer fitted only on training rows; no scaling','threshold':.5,'searches':0,'independent_test_evaluated':False,'input_sha256':{n:sha(ROOT/'data'/n) for n in ['train.parquet','validation.parquet']},'original_model_sha256':sha(OLD/'lunge-detector.joblib'),'python':platform.python_version(),'sklearn':sklearn.__version__}
 (ROOT/'config/day4-training.json').write_text(json.dumps(protocol,indent=2))
 print('Training fixed RF on',len(train),'rows',flush=True);start=time.monotonic();pipeline.fit(train[names],y);fit_seconds=time.monotonic()-start
 np.testing.assert_allclose(pipeline.named_steps['imputer'].statistics_,np.median(train[names].to_numpy(),axis=0),rtol=0,atol=0)
 original=joblib.load(OLD/'lunge-detector.joblib');assert original['source_feature_names']==names and original['feature_engineering_version']==0
 grid=pd.concat([pd.read_parquet(ROOT/f'data/movie5/full-grid-fly{i}.parquet') for i in [1,2]],ignore_index=True)
 scores=grid[['recording','fly_id','frame','eligible','target_lunge']].copy()
 for tag,pipe in [('candidate',pipeline),('previous',original['pipeline'])]:
  p=pipe.predict_proba(grid[names])[:,list(pipe.classes_).index(1)];assert np.isfinite(p).all() and ((p>=0)&(p<=1)).all();scores[tag+'_probability']=p
 scores.to_parquet(dest/'movie5-full-grid-probabilities.parquet',index=False)
 eligible=val[['recording','fly_id','frame','target_lunge']].merge(scores.drop(columns=['eligible','target_lunge']),on=['recording','fly_id','frame'],validate='one_to_one')
 assert len(eligible)==len(val)
 metrics={tag:frame_metrics(eligible.target_lunge.to_numpy(),eligible[tag+'_probability'].to_numpy()) for tag in ['candidate','previous']}
 eligible.to_csv(dest/'movie5-eligible-probabilities.csv',index=False)
 bundle={'pipeline':pipeline,'source_feature_names':names,'feature_names':names,'feature_engineering_version':0,'target':'lunge','positive_class':1,'threshold':.5,'train_recordings':protocol['training_recordings'],'validation_recordings':['movie5'],'event_rules':original['event_rules'],'release_status':'experimental-day4-candidate-not-integrated','release_version':'2.1-day4','training_protocol':protocol,'validation_metrics':metrics['candidate']}
 model=models/'day4-raw-random-forest.joblib';joblib.dump(bundle,model,compress=3)
 loaded=joblib.load(model);np.testing.assert_allclose(loaded['pipeline'].predict_proba(grid[names])[:,1],scores.candidate_probability,rtol=0,atol=1e-14)
 check_frozen()
 result={'status':'PASS','fit_seconds':fit_seconds,'training_rows':len(train),'training_positive_frames':int(y.sum()),'metrics':metrics,'f1_difference':metrics['candidate']['f1']-metrics['previous']['f1'],'threshold':.5,'comparison':'same auto-extracted movie5 features and identical eligible aligned labels; unsmoothed frame probabilities','full_grid_predictions':len(scores),'model_sha256':sha(model),'reload_probability_tolerance':1e-14,'training_only_imputer_verified':True,'original_frozen_files_unchanged':True,'input_sha256':protocol['input_sha256'],'independent_test_available':False}
 (dest/'metrics.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2),flush=True)
 pd.Series(pipeline.named_steps['classifier'].feature_importances_,index=names,name='importance').sort_values(ascending=False).to_csv(dest/'feature-importances.csv')
 lines=['# FlyAggression Analyzer 2.1 — Day 4 training report','','A separate raw-video-specific Random Forest candidate was trained on movies 1–4 and evaluated on movie5. The original frozen classifier and application remain unchanged.','','| Model | Precision | Recall | Frame F1 |','|---|---:|---:|---:|']
 for tag in ['previous','candidate']:
  m=metrics[tag];lines.append(f"| {tag} | {m['precision']:.2%} | {m['recall']:.2%} | {m['f1']:.2%} |")
 lines += ['',f"Candidate minus previous frame F1: {result['f1_difference']*100:+.2f} percentage points. Training took {fit_seconds:.1f} seconds.",'','## Method',f"Training: {len(train):,} rows, {int(y.sum()):,} lunging frames; validation: {len(val):,} rows, {int(val.target_lunge.sum()):,} lunging frames. All 36 predictor names and ordering are explicit; fly IDs, frame numbers, split and labels are excluded from predictors. Median imputation was fitted only on training rows and verified against training medians. RF: 128 trees, maximum depth 20, minimum leaf 2, sqrt feature selection, seed 501, four workers. Positive class weight is sqrt(training negatives / training positives), {protocol['class_weights'][1]:.6f}; negative weight 1. Fixed threshold 0.5, one candidate, no parameter or threshold search.",'','Both models score the same 108,000-row newly extracted movie5 grid. Frame metrics use exactly the same 100,479 eligible aligned validation rows. Confusion matrices in metrics.json use true classes as rows and predicted classes as columns, ordered [0,1]. These are unsmoothed frame metrics; event detection optimization and event-level validation remain future work. Original event rules are copied as defaults only.','','## Limits','Only 527 of 1,186 annotation-reliable movie5 positive frames (44.44%) survived alignment and feature quality exclusions. Training retained 2,711 of 4,812 positives (56.34%). Scores describe this selected reliable subset, not full-recording biological accuracy. Absent annotated bouts are inferred negatives under an exhaustive-annotation assumption. Track identities and nominal 16 mm arena calibration have documented uncertainty. Whole-recording feature normalization remains part of the existing extractor; the newly fitted imputer uses training rows only. Movie5 was already used for previous model development and is not independent validation. Movies6–10 were previously examined and were not used here; fresh independent recordings are required for a new generalization claim. Previous raw-video frame F1 38.05% and event F1 39.84% came from different recordings/calibration and must not be treated as the baseline for this table.','','## Saved artifacts','- models/day4-raw-random-forest.joblib: separate candidate and trained imputer.','- config/day4-training.json: fixed protocol, feature order, weights, versions and input hashes.','- reports/day4/metrics.json: paired metrics and verification.','- reports/day4/movie5-full-grid-probabilities.parquet: both models, full grid.','- reports/day4/movie5-eligible-probabilities.csv: common scored validation subset.','- reports/day4/feature-importances.csv: descriptive fitted importances.','','Verification: all source dataset manifest hashes matched; recording splits disjoint; complete finite binary training/validation subsets; imputer statistics equal training medians; serialized model predictions agree within 1e-14; all nine original frozen file hashes unchanged. Candidate has not replaced the application model.']
 (ROOT/'DAY4-REPORT.md').write_text('\n'.join(lines)+'\n')
if __name__=='__main__':main()
