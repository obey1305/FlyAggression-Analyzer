"""Independent artifact verification; does not fit or modify either model."""
from pathlib import Path
import hashlib,json
import joblib,numpy as np,pandas as pd
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 report=json.loads((ROOT/'reports/day4/metrics.json').read_text());cfg=json.loads((ROOT/'config/day4-training.json').read_text());names=json.loads((ROOT/'config/feature-columns.json').read_text())
 train=pd.read_parquet(ROOT/'data/train.parquet');val=pd.read_parquet(ROOT/'data/validation.parquet');scores=pd.read_parquet(ROOT/'reports/day4/movie5-full-grid-probabilities.parquet')
 for n,h in cfg['input_sha256'].items():assert sha(ROOT/'data'/n)==h
 assert set(train.recording)=={'movie1','movie2','movie3','movie4'} and set(val.recording)=={'movie5'}
 assert len(scores)==108000 and not scores.duplicated(['recording','fly_id','frame']).any()
 assert scores.groupby('fly_id').frame.apply(lambda x:np.array_equal(x,np.arange(1,54001))).all()
 common=val.merge(scores,on=['recording','fly_id','frame'],validate='one_to_one',suffixes=('_expected','_scored'))
 assert len(common)==100479 and common.eligible.all()
 np.testing.assert_array_equal(common.target_lunge_expected,common.target_lunge_scored)
 for tag in ['candidate','previous']:
  y=common.target_lunge_expected.to_numpy();pred=common[tag+'_probability'].to_numpy()>=.5
  tn=int(((y==0)&(~pred)).sum());fp=int(((y==0)&pred).sum());fn=int(((y==1)&(~pred)).sum());tp=int(((y==1)&pred).sum())
  m=report['metrics'][tag];assert m['confusion_matrix']==[[tn,fp],[fn,tp]]
  for key,expected in {'precision':tp/(tp+fp) if tp+fp else 0,'recall':tp/(tp+fn),'f1':2*tp/(2*tp+fp+fn)}.items():assert abs(m[key]-expected)<1e-14
 model=ROOT/'models/day4-raw-random-forest.joblib';bundle=joblib.load(model);assert sha(model)==report['model_sha256']
 assert bundle['feature_names']==names and bundle['pipeline'].feature_names_in_.tolist()==names
 np.testing.assert_array_equal(bundle['pipeline'].named_steps['imputer'].statistics_,np.median(train[names].to_numpy(),axis=0))
 grid=pd.concat([pd.read_parquet(ROOT/f'data/movie5/full-grid-fly{i}.parquet') for i in [1,2]],ignore_index=True)
 old=ROOT.parent/'drosophila-aggression/models/final-v1';original=joblib.load(old/'lunge-detector.joblib')
 for tag,pipe in [('candidate',bundle['pipeline']),('previous',original['pipeline'])]:
  np.testing.assert_allclose(pipe.predict_proba(grid[names])[:,1],scores[tag+'_probability'],rtol=0,atol=1e-14)
 preserve=json.loads((ROOT/'config/preservation.json').read_text())
 for n,h in preserve['frozen_files'].items():assert sha(old/n)==h
 assert sha(ROOT.parent/'FlyAggression-Analyzer-v2.0.zip')==preserve['v2_archive_sha256']
 result={'status':'PASS','manual_confusion_metrics_match':True,'both_saved_models_reproduce_full_grid_probabilities':True,'training_medians_match':True,'dataset_hashes_unchanged':True,'frozen_nine_files_and_v2_archive_unchanged':True,'full_grid_rows':len(scores),'common_eligible_rows':len(common),'model_sha256':sha(model)}
 (ROOT/'reports/day4/independent-verification.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if __name__=='__main__':main()
