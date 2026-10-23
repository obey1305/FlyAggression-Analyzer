import unittest,sys,json,tempfile,shutil,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'scripts'));sys.path.insert(0,str(ROOT.parent/'drosophila-aggression'))
from raw_release import validate_release
class Release22Tests(unittest.TestCase):
 def test_raw_routes_to_22(self):
  model,cfg=validate_release();self.assertEqual(cfg['release_version'],'2.2.0');self.assertEqual(model.parent.name,'raw-v2.2');self.assertIn('retrospective',cfg['scientific_status'])
 def test_candidate_does_not_mix_with_21(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)
   for n in ['lunge-detector.joblib','configuration.json','freeze-manifest.json']:shutil.copy2(ROOT/'models/raw-v2.1'/n,p/n)
   with self.assertRaisesRegex(ValueError,'routing mismatch'):validate_release(p)
 def test_altered_threshold_rejected(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)
   for n in ['lunge-detector.joblib','configuration.json','freeze-manifest.json']:shutil.copy2(ROOT/'models/raw-v2.2'/n,p/n)
   c=json.loads((p/'configuration.json').read_text());c['threshold']=.99;(p/'configuration.json').write_text(json.dumps(c));m=json.loads((p/'freeze-manifest.json').read_text());m['files']['configuration.json']=hashlib.sha256((p/'configuration.json').read_bytes()).hexdigest();(p/'freeze-manifest.json').write_text(json.dumps(m))
   with self.assertRaisesRegex(ValueError,'configuration mismatch'):validate_release(p)
 def test_app_version_warning_and_feature_example(self):
  from streamlit.testing.v1 import AppTest
  a=AppTest.from_file(str(ROOT/'app.py')).run(timeout=30);self.assertEqual(len(a.exception),0);self.assertTrue(any('VERSION 2.2' in x.value for x in a.markdown));a.button[1].click().run(timeout=30);self.assertEqual(len(a.exception),0);self.assertEqual(a.metric[0].value,'325');a.radio[0].set_value('Experimental raw video').run(timeout=30);self.assertEqual(len(a.metric),0);self.assertTrue(any('2.2' in x.value for x in a.warning));self.assertTrue(any(x.label=='Analyse video' and x.disabled for x in a.button))
if __name__=='__main__':unittest.main()
