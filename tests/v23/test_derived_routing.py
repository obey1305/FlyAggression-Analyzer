import sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'scripts/v23'),str(ROOT/'scripts'),str(ROOT.parent/'drosophila-aggression')]
from audit_features import save_derived_features
import feature_service_v21
class DerivedRoutingTests(unittest.TestCase):
 def test_generated_mat_cannot_enter_original_workflow(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'f.mat';save_derived_features(p,['x']*36,np.zeros((2,10,36)),['']*36)
   with patch.object(feature_service_v21,'original_analyze_upload',side_effect=AssertionError('Original classifier must not run')):
    with self.assertRaisesRegex(ValueError,'raw-video-derived'):feature_service_v21.analyze_upload(p.read_bytes(),'f.mat')
if __name__=='__main__':unittest.main()
