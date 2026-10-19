"""Independent audits of selected artifacts, metrics and one-to-one event matching."""
from pathlib import Path
import sys,json
import numpy as np,pandas as pd,joblib
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import maximum_bipartite_matching
from train_day4 import sha
from raw_release import validate_release
ROOT=Path(__file__).resolve().parents[1];DEST=ROOT/'reports/days5-7'
def main():
 model,cfg=validate_release();bundle=joblib.load(model);names=cfg['source_feature_names'];protocol=json.loads((ROOT/'config/days5-7-protocol.json').read_text())
 for n,h in protocol['data_sha256'].items():assert sha(ROOT/'data'/n)==h
 train=pd.read_parquet(ROOT/'data/train.parquet');np.testing.assert_array_equal(bundle['pipeline'].named_steps['imputer'].statistics_,np.median(train[names],axis=0))
 frame=pd.read_csv(DEST/'frame-search.csv');assert len(frame)==28 and frame.candidate.nunique()==4
 selected=frame.sort_values(['f1','precision','recall','candidate','threshold'],ascending=[False,False,False,True,False]).iloc[0]
 assert selected.candidate==cfg['candidate_id'] and selected.threshold==cfg['threshold']
 search=pd.read_csv(DEST/'event-search.csv');assert len(search)==27
 selected_event=search.sort_values(['f1','precision','recall','median_window','max_gap_frames','min_event_frames'],ascending=[False,False,False,True,True,True]).iloc[0]
 for k,v in cfg['event_rules'].items():assert selected_event[k]==v
 comparison=pd.read_csv(DEST/'comparison-by-recording.csv');checks=[]
 for rec in ['movie1','movie2','movie3','movie4','movie5']:
  folder=DEST/rec;grid=pd.concat([pd.read_parquet(ROOT/f'data/{rec}/full-grid-fly{i}.parquet') for i in [1,2]],ignore_index=True);coverage=pd.read_parquet(folder/'evaluation-coverage.parquet');truth=pd.read_csv(folder/'expert-events.csv');source=pd.read_csv(ROOT/f'data/{rec}/aligned-lunge-bouts.csv')
  assert len(coverage)==108000 and not coverage.duplicated(['recording','fly_id','frame']).any()
  expected=grid.eligible.to_numpy(bool).copy();keep=source.whole_bout_eligible.to_numpy(bool).copy()
  for _ in range(len(source)+1):
   excluded=source.loc[~keep];blocked=np.zeros(54001,bool)
   for r in excluded.itertuples():blocked[int(r.start_frame):int(r.end_frame)+1]=True
   mask=expected&~blocked[grid.frame.to_numpy(int)]
   remaining=keep.copy()
   for i,r in enumerate(source.itertuples()):
    ix=grid.fly_id.eq(r.new_fly_id)&grid.frame.between(r.start_frame,r.end_frame)
    if not ix.any() or not mask[ix].all():remaining[i]=False
   if np.array_equal(remaining,keep):break
   keep=remaining
  np.testing.assert_array_equal(mask,coverage.valid_for_events)
  assert set(zip(truth.reference_fly_id,truth.source_event_id))==set(zip(source.loc[keep,'reference_fly_id'],source.loc[keep,'source_event_id']))
  for r in truth.itertuples():
   s=source[source.source_event_id.eq(r.source_event_id)&source.reference_fly_id.eq(r.reference_fly_id)].iloc[0];assert s.start_frame==r.start_frame and s.end_frame==r.end_frame and s.new_fly_id==r.fly_id
  for tag in ['original','day4','selected']:
   scores=pd.read_parquet(folder/f'{tag}-full-grid-probabilities.parquet');pd.testing.assert_frame_equal(scores[['recording','fly_id','frame']],coverage[['recording','fly_id','frame']]);np.testing.assert_array_equal(scores.valid_for_events,coverage.valid_for_events)
   pred=pd.read_csv(folder/f'{tag}-predicted-events.csv');matches=pd.read_csv(folder/f'{tag}-matches.csv');row=comparison[comparison.recording.eq(rec)&comparison.model.eq(tag)].iloc[0];tp=0
   for fly in [1,2]:
    a=pred[pred.fly_id.eq(fly)];b=truth[truth.fly_id.eq(fly)]
    for r in a.itertuples():assert mask[(grid.fly_id.eq(fly)&grid.frame.between(r.start_frame,r.end_frame)).to_numpy()].all()
    if len(a) and len(b):
     overlap=np.maximum(0,np.minimum(a.end_frame.to_numpy()[:,None],b.end_frame.to_numpy()[None,:])-np.maximum(a.start_frame.to_numpy()[:,None],b.start_frame.to_numpy()[None,:])+1)
     iou=overlap/(a.end_frame.to_numpy()[:,None]-a.start_frame.to_numpy()[:,None]+b.end_frame.to_numpy()[None,:]-b.start_frame.to_numpy()[None,:]+2-overlap)
     tp+=int((maximum_bipartite_matching(csr_matrix(iou>=.3),perm_type='column')>=0).sum())
   fp=len(pred)-tp;fn=len(truth)-tp;assert len(matches)==tp and row.event_true_positive_events==tp and row.event_false_positive_events==fp and row.event_false_negative_events==fn
   assert abs(row.event_f1-(2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 0))<1e-12
   for r in matches.itertuples():
    a=pred[pred.fly_id.eq(r.fly_id)&pred.event_id.eq(r.pred_event_id)].iloc[0];b=truth[truth.fly_id.eq(r.fly_id)&truth.event_id.eq(r.expert_event_id)].iloc[0];ov=max(0,min(a.end_frame,b.end_frame)-max(a.start_frame,b.start_frame)+1);assert abs(ov/(a.end_frame-a.start_frame+b.end_frame-b.start_frame+2-ov)-r.iou)<1e-12
   threshold=cfg['threshold'] if tag=='selected' else .5;m=grid.eligible.to_numpy(bool);y=grid.loc[m,'target_lunge'].to_numpy();p=scores.loc[m,'probability_lunge'].to_numpy();predicted=p>=threshold;tn=int(((y==0)&~predicted).sum());fp=int(((y==0)&predicted).sum());fn=int(((y==1)&~predicted).sum());tp=int(((y==1)&predicted).sum());assert abs(row.frame_f1-2*tp/(2*tp+fp+fn))<1e-12
   if tag=='selected':np.testing.assert_allclose(bundle['pipeline'].predict_proba(grid[names].replace([np.inf,-np.inf],np.nan))[:,1],scores.probability_lunge,rtol=0,atol=1e-14)
  checks.append({'recording':rec,'whole_expert_events':len(truth),'event_scorable_rows':int(mask.sum()),'status':'PASS'})
 preserve=json.loads((ROOT/'config/preservation.json').read_text());old=ROOT.parent/'drosophila-aggression/models/final-v1'
 for n,h in preserve['frozen_files'].items():assert sha(old/n)==h
 for n,h in preserve['extractor_sources'].items():assert sha(n)==h
 assert sha(ROOT.parent/'FlyAggression-Analyzer-v2.0.zip')==preserve['v2_archive_sha256']
 out={'status':'PASS','recordings':checks,'frame_grid_candidates':28,'event_grid_candidates':27,'manual_frame_metrics':True,'independent_maximum_cardinality_event_matching':True,'whole_bout_coverage_reconstructed':True,'selected_predictions_reproduced':True,'original_frozen_release_archive_and_extractors_preserved':True,'independent_test_available':False,'model_sha256':sha(model)}
 (DEST/'independent-verification.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
if __name__=='__main__':main()
