"""Real invalid-input calls through app services; never bypass calibration/model guards."""
from pathlib import Path
import sys,json,subprocess,time
ROOT=Path(__file__).resolve().parents[2];P=ROOT.parent/'drosophila-aggression';sys.path.insert(0,str(P));sys.path.insert(0,str(ROOT/'scripts'))
from scripts.auto_calibration import prepare_auto_calibration
from scripts.gui_service import analyze_upload
from video_service_v21 import analyze_video_upload

def main():
 dest=ROOT/'reports/v22-days7-10';dest.mkdir(exist_ok=True);temp=ROOT/'data/v22-invalid';temp.mkdir(exist_ok=True)
 video=ROOT.parent/'flyaggression-v2.1/data/day8-smoke/movie1-first300.mp4';content=video.read_bytes();cal=(ROOT.parent/'flyaggression-v2.1/data/day8-smoke/calibration.mat').read_bytes()
 low=temp/'15fps.mp4';subprocess.run(['/opt/homebrew/bin/ffmpeg','-y','-i',str(video),'-r','15','-c:v','mpeg4','-q:v','2','-video_track_timescale','30','-an','-loglevel','error',str(low)],check=True)
 cases=[('empty MP4',lambda:analyze_video_upload(b'','x.mp4',cal,True)),('wrong video extension',lambda:analyze_video_upload(content,'x.avi',cal,True)),('missing consent',lambda:analyze_video_upload(content,'x.mp4',cal,False)),('missing calibration',lambda:analyze_video_upload(content,'x.mp4',b'',True)),('invalid physical diameter',lambda:prepare_auto_calibration(content,'x.mp4',0)),('corrupted MP4 calibration',lambda:prepare_auto_calibration(b'not a video','broken.mp4',16)),('incompatible 15fps MP4 calibration',lambda:prepare_auto_calibration(low.read_bytes(),'15fps.mp4',16)),('corrupted calibration raw analysis',lambda:analyze_video_upload(content,'x.mp4',b'not a MAT file',True)),('corrupted MATLAB features',lambda:analyze_upload(b'not MAT','broken.mat'))]
 results=[]
 for name,call in cases:
  start=time.monotonic()
  try:call()
  except ValueError as e:results.append({'case':name,'status':'PASS','handled_error':str(e),'seconds':time.monotonic()-start});print(name,'PASS',flush=True)
  else:raise AssertionError('Invalid input accepted: '+name)
 (dest/'invalid-input-results.json').write_text(json.dumps({'status':'PASS','cases':results},indent=2))
if __name__=='__main__':main()
