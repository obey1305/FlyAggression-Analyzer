import sys,unittest
from pathlib import Path
import pandas as pd,numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from optimize_days5_7 import event_reference,measure_frames
class OptimizationTests(unittest.TestCase):
 def test_uncertain_bout_is_removed_whole_from_both_streams(self):
  grid=pd.DataFrame({'recording':['x']*20,'fly_id':np.repeat([1,2],10),'frame':list(range(1,11))*2,'eligible':True})
  bouts=pd.DataFrame([dict(recording='x',source_event_id=1,new_fly_id=1,start_frame=3,end_frame=5,whole_bout_eligible=False),dict(recording='x',source_event_id=2,new_fly_id=2,start_frame=5,end_frame=7,whole_bout_eligible=True)])
  valid,truth=event_reference(grid,bouts)
  self.assertEqual(len(truth),0)
  self.assertFalse(valid[grid.frame.between(3,7)].any())
  self.assertTrue(valid[grid.frame.eq(8)].all())
 def test_preserve_source_event_endpoints_and_mapped_id(self):
  grid=pd.DataFrame({'recording':['x']*10,'fly_id':[2]*10,'frame':range(1,11),'eligible':True})
  bouts=pd.DataFrame([dict(recording='x',source_event_id=7,new_fly_id=2,start_frame=3,end_frame=5,whole_bout_eligible=True)])
  valid,truth=event_reference(grid,bouts)
  self.assertTrue(valid.all());self.assertEqual(truth.iloc[0][['fly_id','event_id','start_frame','end_frame']].tolist(),[2,7,3,5])
 def test_source_ids_remain_unique_after_time_varying_mapping(self):
  grid=pd.DataFrame({'recording':['x']*10,'fly_id':[2]*10,'frame':range(1,11),'eligible':True})
  bouts=pd.DataFrame([dict(recording='x',source_event_id=1,reference_fly_id=ref,new_fly_id=2,start_frame=start,end_frame=start+1,whole_bout_eligible=True) for ref,start in [(1,2),(2,6)]])
  valid,truth=event_reference(grid,bouts)
  self.assertFalse(truth.duplicated(['recording','fly_id','event_id']).any())
  self.assertEqual(set(zip(truth.reference_fly_id,truth.source_event_id)),{(1,1),(2,1)})
 def test_threshold_recall_and_confusion(self):
  low=measure_frames([0,0,1,1],[.1,.3,.2,.8],.2)
  self.assertEqual(low['confusion_matrix'],[[1,1],[0,2]])
  self.assertEqual(low['recall'],1.)
if __name__=='__main__':unittest.main()
