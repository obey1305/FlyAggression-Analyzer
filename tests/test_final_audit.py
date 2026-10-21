import sys,unittest
from pathlib import Path
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from audit_quantification import audit_tables
class FinalAuditTests(unittest.TestCase):
 def tables(self):
  frames=pd.DataFrame({'recording':['x']*20,'fly_id':[1]*10+[2]*10,'frame':list(range(1,11))*2})
  events=pd.DataFrame({'recording':['x'],'fly_id':[1],'event_id':[1],'start_frame':[3],'end_frame':[5],'duration_frames':[3],'duration_seconds':[.1]})
  flies=pd.DataFrame({'recording':['x','x'],'fly_id':[1,2],'frame_count':[10,10],'recording_seconds':[10/30]*2,'lunge_count':[1,0],'total_lunge_frames':[3,0],'total_lunge_seconds':[.1,0.],'lunge_frequency_per_minute':[180.,0.]})
  records=pd.DataFrame({'recording':['x'],'summed_fly_event_count':[1],'total_lunge_fly_seconds':[.1],'events_per_fly_minute':[90.],'recording_seconds':[10/30]})
  return frames,events,flies,records
 def test_valid_inclusive_measurements(self):self.assertEqual(audit_tables(*self.tables())['total_events'],1)
 def test_off_by_one_duration_rejected(self):
  f,e,b,r=self.tables();e['duration_seconds']=2/30
  with self.assertRaises(AssertionError):audit_tables(f,e,b,r)
 def test_frequency_denominator_rejected(self):
  f,e,b,r=self.tables();r['events_per_fly_minute']=180
  with self.assertRaises(AssertionError):audit_tables(f,e,b,r)
 def test_wrong_event_onset_rejected(self):
  f,e,b,r=self.tables();e['start_seconds']=.1;e['stop_seconds_exclusive']=5/30
  with self.assertRaises(AssertionError):audit_tables(f,e,b,r)
 def test_swapped_frame_order_rejected(self):
  f,e,b,r=self.tables();f.loc[[0,1],'frame']=[2,1]
  with self.assertRaises(AssertionError):audit_tables(f,e,b,r)
if __name__=='__main__':unittest.main()
