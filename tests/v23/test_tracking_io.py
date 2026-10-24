import tempfile,sys,unittest
from pathlib import Path
import numpy as np,h5py
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts/v23'))
from tracking_io import load_track
class TrackingIOTests(unittest.TestCase):
 def fixture(self,p,empty=True):
  with h5py.File(p,'w') as f:
   g=f.create_group('trk');g.create_dataset('data',data=np.zeros((2,20,2)))
   refs=[]
   for i,s in enumerate(['pos x','pos y']):refs.append(f.create_dataset('n'+str(i),data=np.array([ord(c) for c in s],dtype='uint16')).ref)
   g.create_dataset('names',data=np.array(refs,dtype=h5py.ref_dtype))
   ds=g.create_dataset('flags',data=np.array([0,6],dtype='uint64') if empty else np.array([[1,2,5,7,0,0]]).T)
   if empty:ds.attrs['MATLAB_empty']=1
 def test_matlab_empty_dimensions_are_not_warning_rows(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'t.mat';self.fixture(p);xy,w,_,_=load_track(p);self.assertEqual(xy.shape,(2,20,2));self.assertFalse(w.any())
 def test_inclusive_warning_interval(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'t.mat';self.fixture(p,False);_,w,_,_=load_track(p);self.assertEqual(np.flatnonzero(w).tolist(),[4,5,6])
if __name__=='__main__':unittest.main()
