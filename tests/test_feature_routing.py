import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'));sys.path.insert(0,str(ROOT.parent/'drosophila-aggression'))
from feature_service_v21 import analyze_upload
class FeatureRoutingTests(unittest.TestCase):
 def test_known_raw_adapter_features_rejected_in_original_mode(self):
  with self.assertRaisesRegex(ValueError,'raw-video-derived'):analyze_upload((ROOT/'data/movie5/features36.mat').read_bytes(),'features.mat')
 def test_valid_original_features_keep_original_model(self):
  p=ROOT.parent/'drosophila-aggression';result=analyze_upload((p/'datasets/features/movie5_feat.mat').read_bytes(),'movie5_feat.mat')
  self.assertEqual(result['manifest']['model_sha256'],'508f49002159bb6da8be4c42f38c76ba43215b692e96aa73276e287cedb86a42');self.assertEqual(len(result['events']),325)
if __name__=='__main__':unittest.main()
