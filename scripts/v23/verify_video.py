"""Verify complete native decode and all output frame timestamps, independent of labels."""
from pathlib import Path
import subprocess,json,numpy as np
ROOT=Path(__file__).resolve().parents[2];R=ROOT/'reports/v23-days1-4';FF='/opt/homebrew/bin/ffmpeg';PROBE='/opt/homebrew/bin/ffprobe'
def main():
 source=ROOT.parent/'new-training-data/BoyMeetsBoy/downloads/movie5.avi';target=ROOT/'data/v23-input/movie5-analysis30.mp4'
 with (R/'native-full-decode-final.log').open('w') as log:
  result=subprocess.run([FF,'-v','error','-xerror','-i',str(source),'-an','-progress','pipe:1','-nostats','-f','null','-'],stdout=subprocess.PIPE,stderr=log,text=True,check=True)
 pairs=[line.split('=',1) for line in result.stdout.splitlines() if '=' in line];progress=dict(pairs);assert int(progress['frame'])==255929 and progress['progress']=='end'
 cmd=[PROBE,'-v','error','-select_streams','v:0','-show_entries','frame=best_effort_timestamp_time','-of','json',str(target)]
 frames=json.loads(subprocess.check_output(cmd,text=True))['frames'];t=np.array([float(f['best_effort_timestamp_time']) for f in frames]);assert len(t)==38390 and np.all(np.diff(t)>0);error=np.max(np.abs(t-np.arange(len(t))/30));assert error<1e-6
 (R/'full-video-verification.json').write_text(json.dumps({'status':'PASS','native_decode_exit_code':result.returncode,'native_decoded_frames':int(progress['frame']),'analysis_decoded_frames':len(t),'all_analysis_timestamps_monotonic':True,'max_analysis_grid_timestamp_error_seconds':float(error),'first_analysis_timestamp_seconds':float(t[0]),'last_analysis_timestamp_seconds':float(t[-1]),'native_decode_error_log_bytes':(R/'native-full-decode-final.log').stat().st_size},indent=2)+'\n')
if __name__=='__main__':main()
