import sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts/v23'))
from run_frozen import verify_inputs,claim_output
from prepare_evaluation import sha
class FrozenGuardTests(unittest.TestCase):
 def test_changed_locked_input_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'input';p.write_bytes(b'locked');lock={'input_hashes':{str(p):sha(p)}};verify_inputs(lock);p.write_bytes(b'changed')
   with self.assertRaisesRegex(ValueError,'Locked input changed'):verify_inputs(lock)
 def test_existing_prediction_run_not_overwritten(self):
  with tempfile.TemporaryDirectory() as d:
   with self.assertRaisesRegex(ValueError,'preserved'):claim_output(Path(d))
if __name__=='__main__':unittest.main()
