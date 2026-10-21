import sys,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts/v22'))
from identity_alignment import align_identity
CFG={'maximum_gap_frames':12,'anchor_frames_each_side':15,'maximum_pair_error_pixels':3,'minimum_separation_pixels':4,'maximum_axial_orientation_error_radians':np.pi/6,'minimum_orientation_advantage_radians':np.pi/4,'maximum_aligned_step_residual_pixels':2,'maximum_assignment_changes_within_bridge':1}
class IdentityTests(unittest.TestCase):
 def fixture(self):
  n=60;old=np.zeros((2,n,2));old[0,:,0]=np.arange(n)*.1;old[1,:,0]=old[0,:,0]+6;ori=np.tile([[0.],[np.pi/2]],(1,n));mapping=np.zeros(n,dtype=int);base=np.ones(n,bool);base[25:31]=False
  return old,ori,mapping,base,np.zeros(n,bool)
 def test_pose_and_continuity_supported_bridge(self):
  old,ori,m,b,w=self.fixture();new=old.copy();new[:,27:]=new[::-1,27:];no=ori.copy();no[:,27:]=no[::-1,27:];m[27:]=1
  result=align_identity(old,new,ori,no,m,b,w,w,CFG)
  self.assertTrue(result['reliable'][25:31].all());self.assertEqual(result['mapping'][27],1);self.assertEqual(result['mapping'][28],1)
 def test_warning_not_overridden(self):
  old,ori,m,b,w=self.fixture();bad=w.copy();bad[27]=True
  r=align_identity(old,old,ori,ori,m,b,bad,w,CFG);self.assertFalse(r['reliable'][25:31].any())
 def test_ambiguous_parallel_axes_remain_uncertain(self):
  old,ori,m,b,w=self.fixture();ori[:]=0
  r=align_identity(old,old,ori,ori,m,b,w,w,CFG);self.assertFalse(r['reliable'][25:31].any())
 def test_long_gap_not_filled(self):
  old,ori,m,b,w=self.fixture();b[20:40]=False
  r=align_identity(old,old,ori,ori,m,b,w,w,CFG);self.assertFalse(r['reliable'][20:40].any())
 def test_motion_disagreement_not_bridged(self):
  old,ori,m,b,w=self.fixture();new=old.copy();new[:,27,1]+=2.5
  r=align_identity(old,new,ori,ori,m,b,w,w,CFG);self.assertFalse(r['reliable'][25:31].any())
 def test_missing_orientation_not_interpolated(self):
  old,ori,m,b,w=self.fixture();no=ori.copy();no[0,27]=np.nan
  r=align_identity(old,old,ori,no,m,b,w,w,CFG);self.assertFalse(r['reliable'][25:31].any())
 def test_original_arrays_unmodified(self):
  old,ori,m,b,w=self.fixture();before=old.copy();align_identity(old,old,ori,ori,m,b,w,w,CFG);np.testing.assert_array_equal(old,before)
if __name__=='__main__':unittest.main()
