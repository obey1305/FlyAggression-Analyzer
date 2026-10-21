import sys,unittest
from pathlib import Path
import numpy as np,pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts/v22'))
from days3_6 import scale_raw, validate_dataset, boundary_labels
class CalibrationDatasetTests(unittest.TestCase):
 def test_physical_scaling_only(self):
  x=np.ones((2,8,13));names=['vel','ang_vel','min_wing_ang','max_wing_ang','mean_wing_length','axis_ratio','fg_body_ratio','contrast','dist_to_wall','dist_to_other','angle_between','facing_angle','leg_dist']
  y=scale_raw(x,names,1.1)
  np.testing.assert_allclose(y[:,:,0],1.1);np.testing.assert_allclose(y[:,:,4],1.1);np.testing.assert_allclose(y[:,:,1],1);np.testing.assert_array_equal(x,np.ones_like(x))
 def test_invalid_scale(self):
  with self.assertRaises(ValueError):scale_raw(np.ones((2,8,1)),['vel'],0)
 def test_recording_leakage(self):
  d=pd.DataFrame({'recording':['a','a'],'fly_id':[1,1],'frame':[1,2],'target_lunge':[0,1],'x':[1.,2.]})
  with self.assertRaises(ValueError):validate_dataset(d,d,['x'])
 def test_duplicate_keys(self):
  d=pd.DataFrame({'recording':['a','a'],'fly_id':[1,1],'frame':[1,1],'target_lunge':[0,1],'x':[1.,2.]});v=d.assign(recording='b',frame=[1,2])
  with self.assertRaises(ValueError):validate_dataset(d,v,['x'])
 def test_inclusive_annotation_boundaries(self):
  np.testing.assert_array_equal(boundary_labels(6,[(2,3,0),(5,5,1)]),[0,1,1,0,-1,0])
 def test_flagged_overlap_remains_unknown(self):
  np.testing.assert_array_equal(boundary_labels(5,[(2,3,1),(3,4,0)]),[0,-1,-1,1,0])
 def test_out_of_bounds_annotation(self):
  with self.assertRaises(ValueError):boundary_labels(4,[(0,2,0)])
if __name__=='__main__':unittest.main()
