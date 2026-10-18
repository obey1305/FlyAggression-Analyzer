import sys, unittest
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from train_day4 import validate_splits, make_pipeline, frame_metrics
class TrainingTests(unittest.TestCase):
 def test_recording_leakage_rejected(self):
  a=pd.DataFrame({'recording':['movie1','movie2'],'target_lunge':[0,1],'x':[1.,2.]})
  with self.assertRaises(ValueError):validate_splits(a,a,['x'])
 def test_imputer_fits_training_only(self):
  p=make_pipeline(np.array([0,0,1,1]));p.set_params(classifier__n_estimators=2)
  p.fit(pd.DataFrame({'x':[1.,3.,5.,np.nan]}),[0,0,1,1])
  before=p.named_steps['imputer'].statistics_.copy()
  p.predict_proba(pd.DataFrame({'x':[10000.,np.nan]}))
  np.testing.assert_array_equal(before,[3.]);np.testing.assert_array_equal(before,p.named_steps['imputer'].statistics_)
 def test_confusion_and_threshold(self):
  m=frame_metrics(np.array([0,0,1,1]),np.array([.1,.5,.8,.2]))
  self.assertEqual(m['confusion_matrix'],[[1,1],[1,1]])
  self.assertEqual(m['f1'],.5)
if __name__=='__main__':unittest.main()
