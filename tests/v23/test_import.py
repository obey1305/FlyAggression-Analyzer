from pathlib import Path
import sys,unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts/v23'))
from import_tools import frame_map,project_interval,rectangle_mask,validate_rates
class ImportTests(unittest.TestCase):
 def test_long_video_no_drift(self):
  m=frame_map(255929,200,30);self.assertEqual(len(m),38390);self.assertEqual(m.source_frame.iloc[:4].tolist(),[1,8,14,21]);self.assertTrue((np.diff(m.source_frame)>0).all());self.assertLessEqual(m.sample_error_seconds.abs().max(),1/400);self.assertAlmostEqual(m.analysis_seconds.iloc[-1],38389/30)
 def test_short_tail_is_clipped(self):
  m=frame_map(7,200,30);self.assertEqual(m.source_frame.tolist(),[1,7]);self.assertTrue(m.source_frame.le(7).all())
 def test_unobserved_lunge_is_flagged(self):
  self.assertEqual(project_interval(6,6,frame_map(100,200,30))['sample_count'],0)
 def test_inclusive_single_source_frame(self):
  x=project_interval(8,8,frame_map(100,200,30));self.assertEqual((x['analysis_start_frame'],x['analysis_end_frame'],x['sample_count']),(2,2,1))
 def test_rectangle_edges_inclusive(self):
  a=rectangle_mask(10,8,[2,3,9,7],1);self.assertEqual(a.shape,(8,10));self.assertTrue(a[2,1]);self.assertFalse(a[0,0]);self.assertTrue(a[6,8]);self.assertTrue(a[7,9])
 def test_invalid_geometry_and_rate(self):
  with self.assertRaises(ValueError):rectangle_mask(10,8,[9,1,2,8],0)
  with self.assertRaises(ValueError):frame_map(0,200,30)
  with self.assertRaises(ValueError):validate_rates(30,200)
if __name__=='__main__':unittest.main()
