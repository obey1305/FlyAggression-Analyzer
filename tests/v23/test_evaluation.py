import sys,unittest
from pathlib import Path
import numpy as np,pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts/v23'))
from evaluation_core import native_bins,close_coverage,assign_iou,match_time,whole_prediction
class EvaluationTests(unittest.TestCase):
 def test_native_half_open_bin_boundaries(self):
  self.assertEqual(native_bins(1,20,200,30),(0,3));self.assertEqual(native_bins(8,8,200,30),(1,2))
 def test_cardinality_precedes_iou(self):
  pairs=assign_iou(np.array([[.9,.31],[.3,0.]]),.3);self.assertEqual(set(pairs),{(0,1),(1,0)})
 def test_censor_closure_retains_short_complete_bout(self):
  mask=np.ones(30,bool);mask[8]=False
  new,keep=close_coverage(mask,[(7,10),(9,12),(20,21)],[True,True,True]);self.assertEqual(keep.tolist(),[False,False,True]);self.assertFalse(new[7:12].any())
 def test_initially_excluded_bout_censors_other_stream(self):
  new,keep=close_coverage(np.ones(10,bool),[(1,3),(2,4)],[False,True]);self.assertFalse(keep.any());self.assertFalse(new[1:4].any())
 def test_prediction_crossing_mask_or_mapping_is_excluded(self):
  mask=np.ones(10,bool);mapping=np.zeros(10,int);mapping[5:]=1
  self.assertFalse(whole_prediction(4,7,mask,mapping)[0]);mask[2]=False;self.assertFalse(whole_prediction(1,4,mask,mapping)[0]);self.assertTrue(whole_prediction(7,9,mask,mapping)[0])
 def test_continuous_match_not_frame_count_iou(self):
  p=pd.DataFrame([dict(recording='r',fly_id=1,event_id=1,start_seconds=0.,stop_seconds_exclusive=.1)])
  g=pd.DataFrame([dict(recording='r',fly_id=1,event_id=2,start_seconds=.02,stop_seconds_exclusive=.08)])
  m,match,_,_=match_time(p,g,.3);self.assertEqual(m['true_positive_events'],1);self.assertAlmostEqual(match.iloc[0].iou,.6);self.assertAlmostEqual(match.iloc[0].onset_error_seconds,-.02)
 def test_no_predictions_preserves_missed_event(self):
  cols=['recording','fly_id','event_id','start_seconds','stop_seconds_exclusive'];p=pd.DataFrame(columns=cols);g=pd.DataFrame([['r',1,1,0.,.1]],columns=cols)
  m,*_=match_time(p,g,.3);self.assertEqual(m['false_negative_events'],1);self.assertEqual(m['f1'],0.)
if __name__=='__main__':unittest.main()
