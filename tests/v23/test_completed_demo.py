import sys,unittest,io,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT.parent/'drosophila-aggression')]
from streamlit.testing.v1 import AppTest
from video_service_v23 import load_completed_demo
from scripts.gui_service import archive_downloads
class CompletedDemoTests(unittest.TestCase):
 def test_saved_demo_renders64_and_is_explicitly_saved(self):
  app=AppTest.from_file(str(ROOT/'app.py')).run(timeout=30);app.radio[0].set_value('Experimental raw video').run(timeout=30);next(r for r in app.radio if r.label=='Arena geometry').set_value('Rectangular (30/200FPS)').run(timeout=30);next(b for b in app.button if b.label=='Load completed starter demonstration').click().run(timeout=30);self.assertEqual(len(app.exception),0);self.assertEqual(app.metric[0].value,'64');self.assertTrue(any('Saved completed' in x.value for x in app.info));self.assertTrue(any('Source 200 FPS' in x.value for x in app.caption));self.assertTrue(any('Scale 12' in x.value for x in app.caption))
 def test_saved_demo_downloads_include_mapping_and_calibration(self):
  result=load_completed_demo();self.assertEqual(len(result['events']),64);self.assertIn('frame-time-map.csv',result['downloads']);self.assertIn('calibration-parameters.json',result['downloads']);self.assertIn('calibration.mat',result['downloads']);self.assertNotIn('all-results.zip',result['downloads'])
  with zipfile.ZipFile(io.BytesIO(archive_downloads(result['downloads']))) as z:self.assertIsNone(z.testzip())
if __name__=='__main__':unittest.main()
