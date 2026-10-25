import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts/v23'))
from analyze_failures import attainable_iou
class TemporalLimitTests(unittest.TestCase):
 def test_short_interval_cannot_match_minimum_duration(self):
  self.assertLess(attainable_iou(201,205),.3)
 def test_exact_three_frame_interval_can_match(self):
  self.assertAlmostEqual(attainable_iou(201,220),1.)
if __name__=='__main__':unittest.main()
