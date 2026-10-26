import sys,unittest,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT.parent/'drosophila-aggression')]
from streamlit.testing.v1 import AppTest
class AppV23Tests(unittest.TestCase):
 def test_original_example_still_325_and_rectangular_controls(self):
  app=AppTest.from_file(str(ROOT/'app.py')).run(timeout=30);self.assertEqual(len(app.exception),0)
  next(b for b in app.button if b.label=='Load development example').click().run(timeout=30);self.assertEqual(len(app.exception),0);self.assertEqual(app.metric[0].value,'325')
  app.radio[0].set_value('Experimental raw video').run(timeout=30);self.assertEqual(len(app.metric),0);self.assertEqual(len(app.exception),0)
  next(r for r in app.radio if r.label=='Arena geometry').set_value('Rectangular (30/200FPS)').run(timeout=30);self.assertEqual(len(app.exception),0);self.assertTrue(any(b.label=='Analyse rectangular video' and b.disabled for b in app.button));self.assertTrue(any(n.label=='Pixels per millimetre' for n in app.number_input))
  next(r for r in app.radio if r.label=='Video location').set_value('Local file (large recordings)').run(timeout=30);self.assertTrue(any(t.label=='Local video path' for t in app.text_input));self.assertTrue(any('restricted' in w.value.lower() for w in app.warning))
 def test_corrupt_rectangular_video_rejected(self):
  from video_service_v23 import analyze_rectangular_path
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'broken.avi';p.write_bytes(b'broken')
   with self.assertRaisesRegex(ValueError,'unreadable'):analyze_rectangular_path(p,[20,10,620,479],12,12,'published-nominal',True)
 def test_consent_and_empty_upload(self):
  from video_service_v23 import analyze_rectangular_path,analyze_rectangular_upload
  with self.assertRaisesRegex(ValueError,'Confirm'):analyze_rectangular_path('missing.avi',[20,10,620,479],12,12,'published-nominal',False)
  with self.assertRaisesRegex(ValueError,'empty'):analyze_rectangular_upload(b'','empty.avi')
if __name__=='__main__':unittest.main()
