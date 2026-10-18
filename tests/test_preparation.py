import sys,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
class PreparationTests(unittest.TestCase):
 def test_alignment_module(self):
  self.assertTrue((Path(__file__).resolve().parents[1]/'scripts/prepare_aligned.py').exists())
 def test_swapped_ids_and_ambiguity(self):
  from prepare_aligned import align_positions
  n=120;old=np.zeros((2,n,2));old[1,:,0]=30
  new=old.copy();new[:,60:]=new[::-1,60:];new[:,25:30,0]=15
  mapping,valid,info=align_positions(old,new,np.zeros(n,bool),np.zeros(n,bool),dict(maximum_position_error_pixels=3,minimum_assignment_margin_pixels=4,minimum_reference_separation_pixels=8,minimum_stable_mapping_frames=15,boundary_exclusion_frames=5))
  self.assertEqual(mapping[10],0);self.assertEqual(mapping[100],1)
  self.assertFalse(valid[27]);self.assertFalse(valid[59]);self.assertTrue(valid[100])
 def test_unknown_flag_and_inclusive_boundaries(self):
  from prepare_aligned import annotation_labels
  bouts=np.empty((2,2),object)
  for i in range(2):
   for j in range(2):bouts[i,j]=np.empty((0,3))
  bouts[0,0]=np.array([[3,5,0]]);bouts[0,1]=np.array([[4,4,0]])
  y=annotation_labels({'bouts':bouts,'behs':['lunge','unknown']},10)
  np.testing.assert_array_equal(y[0],[0,0,1,-1,1,0,0,0,0,0])
 def test_reference_warning_is_buffered(self):
  from prepare_aligned import align_positions
  n=120;old=np.zeros((2,n,2));old[1,:,0]=30;warning=np.zeros(n,bool);warning[60]=True
  cfg=dict(maximum_position_error_pixels=3,minimum_assignment_margin_pixels=4,minimum_reference_separation_pixels=8,minimum_stable_mapping_frames=15,boundary_exclusion_frames=5)
  _,valid,_=align_positions(old,old.copy(),warning,np.zeros(n,bool),cfg)
  self.assertFalse(valid[55:66].any());self.assertTrue(valid[30]);self.assertTrue(valid[90])
 def test_overlapping_flies_never_confirmed(self):
  from prepare_aligned import align_positions
  old=np.zeros((2,120,2));cfg=dict(maximum_position_error_pixels=3,minimum_assignment_margin_pixels=4,minimum_reference_separation_pixels=8,minimum_stable_mapping_frames=15,boundary_exclusion_frames=5)
  _,valid,_=align_positions(old,old.copy(),np.zeros(120,bool),np.zeros(120,bool),cfg)
  self.assertFalse(valid.any())
 def test_bout_exclusion_overlap_closure(self):
  import pandas as pd
  from prepare_aligned import close_bout_exclusions
  d=pd.DataFrame({'reference_fly_id':[1,1,1,1],'start_frame':[3,5,7,11],'end_frame':[5,7,9,12],'whole_bout_eligible':[False,True,True,True]})
  result=close_bout_exclusions(d)
  self.assertEqual(result.whole_bout_eligible.tolist(),[False,False,False,True])
if __name__=='__main__':unittest.main()


