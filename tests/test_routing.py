import sys,unittest,tempfile,json,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from raw_release import validate_release
class RoutingTests(unittest.TestCase):
 def test_changed_model_rejected_before_loading(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t);(p/'lunge-detector.joblib').write_bytes(b'not executable joblib')
   (p/'configuration.json').write_text('{}')
   (p/'freeze-manifest.json').write_text(json.dumps({'files':{'lunge-detector.joblib':'wrong','configuration.json':'wrong'}}))
   with self.assertRaisesRegex(ValueError,'integrity'):validate_release(p)
 def test_missing_release_has_clear_error(self):
  with tempfile.TemporaryDirectory() as t:
   with self.assertRaisesRegex(ValueError,'release'):validate_release(Path(t))
if __name__=='__main__':unittest.main()
