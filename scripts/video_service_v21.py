"""Experimental raw-video UI bridge, isolated from frozen feature runtime."""
from pathlib import Path
import io,json,subprocess,sys,tempfile,time,os,signal
import pandas as pd
from scripts.gui_service import ROOT,WORK,MAX_BYTES
from raw_release import validate_release
BUILD=Path(__file__).resolve().parents[1]
EXT=ROOT.parent/'raw-video-integration'

def load_video_result(folder,filename):
 folder=Path(folder);out=folder/'experimental-results'
 downloads={p.name:p.read_bytes() for p in out.iterdir() if p.suffix in ['.csv','.json','.txt']}
 manifest=json.loads((out/'run-manifest.json').read_text())
 result={'filename':filename,'events':pd.read_csv(out/'lunge-events.csv'),'byfly':pd.read_csv(out/'summary-by-fly.csv'),'byrecording':pd.read_csv(out/'summary-by-recording.csv'),'manifest':manifest,'downloads':downloads,'experimental':True}
 downloads['integration-manifest.json']=(folder/'integration-manifest.json').read_bytes()
 integration=json.loads(downloads['integration-manifest.json'])
 release=integration['model_release']
 manifest.update(model_version=release['release_version'],analysis_mode='raw-video',scientific_status=release['scientific_status'])
 downloads['run-manifest.json']=(json.dumps(manifest,indent=2)+'\n').encode()
 downloads['experimental-report.png']=graphical_report(result)
 return result

def graphical_report(result):
 import matplotlib
 matplotlib.use('Agg')
 from matplotlib.figure import Figure
 fig=Figure(figsize=(10,5),layout='constrained');axes=fig.subplots(2,1)
 f=result['byfly'];e=result['events']
 axes[0].bar(f.fly_id.astype(str),f.lunge_count,color='#3265a0');axes[0].set(xlabel='Source fly',ylabel='Predicted events')
 for fly in [1,2]:
  g=e[e.fly_id==fly]
  axes[1].vlines(g.start_seconds,fly-.25,fly+.25,color='#3265a0',linewidth=1)
 axes[1].set(xlabel='Event onset time (seconds)',ylabel='Source fly',yticks=[1,2],xlim=(0,float(f.recording_seconds.max())))
 fig.suptitle('Experimental raw-video predictions — accuracy not established')
 b=io.BytesIO();fig.savefig(b,format='png',dpi=150);return b.getvalue()

def analyze_video_upload(content,filename,calibration,experimental,progress=None):
 if not experimental:raise ValueError('Confirm experimental raw-video analysis before starting.')
 if not content:raise ValueError('The uploaded video is empty.')
 if Path(filename).suffix.lower()!='.mp4':raise ValueError('Choose a supported MP4 video.')
 if len(content)>MAX_BYTES:raise ValueError('Video exceeds the 200 MB limit.')
 if not calibration:raise ValueError('Provide a FlyTracker arena calibration MAT file.')
 if len(calibration)>10*1024*1024:raise ValueError('Calibration exceeds 10 MB.')
 validate_release()
 report=progress or (lambda p,s:None);WORK.mkdir(parents=True,exist_ok=True)
 with tempfile.TemporaryDirectory(prefix='video-',dir=WORK) as t:
  t=Path(t);video=t/Path(filename).name;video.write_bytes(content);cal=t/'calibration.mat';cal.write_bytes(calibration);out=t/'run'
  with (t/'command.log').open('w') as log:
   proc=subprocess.Popen([sys.executable,str(BUILD/'scripts/video_to_lunges_v21.py'),'--video',str(video),'--calibration',str(cal),'--output',str(out),'--allow-experimental'],stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
   start=time.monotonic()
   try:
    while proc.poll() is None:
     elapsed=int(time.monotonic()-start)
     if elapsed>1800:raise ValueError('Video analysis exceeded 30 minutes; try a shorter compatible recording.')
     stage='Tracking two flies and extracting features'
     mp=out/'integration-manifest.json'
     if mp.exists():
      try:
       stages=json.loads(mp.read_text()).get('stages',[])
       if len(stages)==1:stage='Converting behavioural features'
       if len(stages)>=2:stage='Detecting lunges and writing reports'
      except json.JSONDecodeError:pass
     report(.15 if 'Tracking' in stage else .8,f'{stage} · {elapsed}s elapsed (stage indicator, not completion percentage)')
     time.sleep(1)
   finally:
    if proc.poll() is None:
     os.killpg(proc.pid,signal.SIGTERM)
     try:proc.wait(timeout=10)
     except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);proc.wait()
  if proc.returncode:
   detail=(out/'tracking.log').read_text(errors='replace')[-1800:] if (out/'tracking.log').exists() else (t/'command.log').read_text(errors='replace')[-1800:]
   if 'Video must be 30 FPS' in detail:detail='The video must be recorded at 30 fps.'
   elif 'codec' in detail.lower():detail='The MP4 is unreadable or uses an unsupported codec.'
   elif 'Error using load' in detail:detail='The calibration MAT file could not be read.'
   elif 'Expected two flies' in detail:detail='The calibration must specify exactly two flies.'
   else:detail='Check MP4 readability, two-fly/30 fps calibration, and the local MATLAB installation. '+detail.replace('\b','')[:400]
   raise ValueError('Video processing failed: '+detail)
  report(.95,'Preparing experimental CSV and graphical downloads')
  result=load_video_result(out,Path(filename).name)
 report(1.,'Experimental analysis complete');return result
