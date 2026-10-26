import sys,unittest,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts/v23'))
from video_pipeline import validate_metadata,validate_rectangle
class VideoIntegrationTests(unittest.TestCase):
 def test_supported_native_metadata(self):
  self.assertEqual(validate_metadata({'width':640,'height':480,'r_frame_rate':'200/1','avg_frame_rate':'200/1','nb_frames':'255929','duration':'1279.645'})['frames'],255929)
 def test_variable_or_fractional_rate_rejected(self):
  for r,a in [('30000/1001','30000/1001'),('200/1','199/1')]:
   with self.assertRaises(ValueError):validate_metadata({'width':640,'height':480,'r_frame_rate':r,'avg_frame_rate':a,'nb_frames':'100','duration':'1'})
 def test_rectangle_not_full_mask(self):
  self.assertEqual(validate_rectangle(640,480,[20,10,620,479],12,12)['tracking_bounds'],[8,1,632,480])
  with self.assertRaises(ValueError):validate_rectangle(640,480,[1,1,640,480],0,12)
 def test_unknown_scale_and_outside_bounds_rejected(self):
  with self.assertRaises(ValueError):validate_rectangle(640,480,[20,10,620,479],12,0)
  with self.assertRaises(ValueError):validate_rectangle(640,480,[20,10,650,479],12,12)
if __name__=='__main__':unittest.main()
