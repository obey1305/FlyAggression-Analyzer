"""Independent exported measurement checks; inclusive frame durations at 30 fps."""
import numpy as np

def audit_tables(frames,events,flies,records,fps=30):
 assert not frames.duplicated(['recording','fly_id','frame']).any()
 assert not events.duplicated(['recording','fly_id','event_id']).any()
 assert set(frames.fly_id)=={1,2}
 for (rec,fly),f in frames.groupby(['recording','fly_id'],sort=False):
  np.testing.assert_array_equal(f.frame,np.arange(1,len(f)+1))
  e=events[events.recording.eq(rec)&events.fly_id.eq(fly)]
  assert e.start_frame.ge(1).all() and e.end_frame.le(len(f)).all() and e.end_frame.ge(e.start_frame).all()
  ordered=e.sort_values('start_frame');assert not len(ordered)>1 or np.all(ordered.start_frame.to_numpy()[1:]>ordered.end_frame.to_numpy()[:-1])
  durations=(e.end_frame-e.start_frame+1).to_numpy()
  np.testing.assert_array_equal(e.duration_frames,durations);np.testing.assert_allclose(e.duration_seconds,durations/fps,rtol=0,atol=1e-12)
  if 'start_seconds' in e:np.testing.assert_allclose(e.start_seconds,(e.start_frame-1)/fps,rtol=0,atol=1e-10)
  if 'stop_seconds_exclusive' in e:np.testing.assert_allclose(e.stop_seconds_exclusive,e.end_frame/fps,rtol=0,atol=1e-10)
  if 'event_positive' in f or 'event_id' in f:
   ids=np.zeros(len(f),int)
   for row in e.itertuples():ids[int(row.start_frame)-1:int(row.end_frame)]=int(row.event_id)
   if 'event_positive' in f:np.testing.assert_array_equal(f.event_positive.to_numpy(bool),ids>0)
   if 'event_id' in f:np.testing.assert_array_equal(f.event_id,ids)
  s=flies[flies.recording.eq(rec)&flies.fly_id.eq(fly)];assert len(s)==1;s=s.iloc[0]
  assert s.frame_count==len(f) and s.lunge_count==len(e) and s.total_lunge_frames==durations.sum()
  np.testing.assert_allclose([s.recording_seconds,s.total_lunge_seconds,s.lunge_frequency_per_minute],[len(f)/fps,durations.sum()/fps,len(e)/(len(f)/fps/60)],rtol=0,atol=1e-10)
 for rec,f in frames.groupby('recording'):
  by=flies[flies.recording.eq(rec)];e=events[events.recording.eq(rec)];r=records[records.recording.eq(rec)];assert len(r)==1;r=r.iloc[0]
  assert by.frame_count.nunique()==1 and r.summed_fly_event_count==len(e)
  np.testing.assert_allclose([r.recording_seconds,r.total_lunge_fly_seconds,r.events_per_fly_minute],[by.frame_count.iloc[0]/fps,e.duration_frames.sum()/fps,len(e)/(by.frame_count.sum()/fps/60)],rtol=0,atol=1e-10)
 return {'status':'PASS','full_grid_rows':len(frames),'total_events':len(events),'total_fly_seconds':float(events.duration_frames.sum()/fps),'inclusive_durations_verified':True,'per_fly_and_recording_frequency_denominators_verified':True,'source_frame_order_and_keys_verified':True}
