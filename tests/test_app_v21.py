import sys,unittest,json,tempfile,shutil,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'));sys.path.insert(0,str(ROOT.parent/'drosophila-aggression'))
from raw_release import validate_release
class IntegrationTests(unittest.TestCase):
 def test_release_configuration_is_consistent(self):
  model,cfg=validate_release();self.assertTrue(model.is_file());self.assertEqual(cfg['mode'],'raw-video-only');self.assertEqual(cfg['release_version'],'2.1.0')
 def test_model_and_config_cannot_silently_mix(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)
   for n in ['configuration.json','freeze-manifest.json','lunge-detector.joblib']:shutil.copy2(ROOT/'models/raw-v2.1'/n,p/n)
   cfg=json.loads((p/'configuration.json').read_text());cfg['threshold']=.99;(p/'configuration.json').write_text(json.dumps(cfg))
   manifest=json.loads((p/'freeze-manifest.json').read_text());manifest['files']['configuration.json']=hashlib.sha256((p/'configuration.json').read_bytes()).hexdigest();(p/'freeze-manifest.json').write_text(json.dumps(manifest))
   with self.assertRaisesRegex(ValueError,'configuration mismatch'):validate_release(p)
 def test_app_both_modes_and_original_example(self):
  from streamlit.testing.v1 import AppTest
  app=AppTest.from_file(str(ROOT/'app.py')).run(timeout=30)
  self.assertEqual(len(app.exception),0)
  self.assertFalse(any('local Streamlit interface to frozen release 1.0.0' in w.value for w in app.markdown))
  app.button[1].click().run(timeout=30)
  self.assertEqual(len(app.exception),0);self.assertEqual(app.metric[0].value,'325')
  self.assertTrue(any('1.0.0' in w.value for w in app.markdown))
  app.radio[0].set_value('Experimental raw video').run(timeout=30)
  self.assertEqual(len(app.exception),0);self.assertEqual(len(app.metric),0)
  self.assertTrue(any('2.1' in w.value for w in app.warning))
  self.assertTrue(any(b.label=='Analyse video' and b.disabled for b in app.button))
 def test_actual_raw_result_renders_with_correct_provenance(self):
  from streamlit.testing.v1 import AppTest
  import pandas as pd
  folder=ROOT/'reports/day8'
  manifest=json.loads((folder/'raw-run-manifest.json').read_text())
  result={'filename':'movie1-first300.mp4','experimental':True,'manifest':manifest,'events':pd.read_csv(folder/'raw-lunge-events.csv'),'byfly':pd.read_csv(folder/'raw-summary-by-fly.csv'),'byrecording':pd.read_csv(folder/'raw-summary-by-recording.csv'),'downloads':{p.name.removeprefix('raw-'):p.read_bytes() for p in folder.glob('raw-*') if p.suffix in ['.csv','.json','.png','.txt']}}
  app=AppTest.from_file(str(ROOT/'app.py')).run(timeout=30)
  app.radio[0].set_value('Experimental raw video').run(timeout=30)
  app.session_state['result']=result
  app.run(timeout=30)
  self.assertEqual(len(app.exception),0);self.assertEqual(len(app.metric),4)
  self.assertTrue(any('2.1.0' in w.value for w in app.markdown))
  self.assertTrue(any('Threshold 0.15' in w.value for w in app.markdown))
  self.assertGreaterEqual(len(app.get('download_button')),7)
if __name__=='__main__':unittest.main()
