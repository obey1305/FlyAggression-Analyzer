"""V2.3 local-file/upload bridge for rectangular30/200FPS analysis."""
from pathlib import Path
import io,json,os,signal,subprocess,sys,time,tempfile,uuid
import pandas as pd
BUILD=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BUILD.parent/'drosophila-aggression'))
sys.path.insert(0,str(BUILD/'scripts/v23'))
from video_pipeline import inspect_video,validate_rectangle,sha
from video_service_v21 import graphical_report
MAX_BYTES=200*1024*1024
RUNS=BUILD/'.runtime/v23-runs'

def upload_identity(digest,filename):return ('upload',digest,Path(filename).name)
def preview_video(path):
 from video_pipeline import FF
 inspect_video(path)
 try:return subprocess.check_output([FF,'-v','error','-i',str(path),'-frames:v','1','-f','image2pipe','-vcodec','png','-'],stderr=subprocess.PIPE)
 except subprocess.CalledProcessError as exc:raise ValueError('The first video frame could not be decoded; inspect the codec or file integrity') from exc
def load_rectangular_result(folder,filename=None):
 folder=Path(folder);integration=json.loads((folder/'integration-manifest.json').read_text())
 if integration.get('status')!='complete':raise ValueError('The analysis run is not complete; inspect its preserved logs')
 from raw_release import validate_release
 _,cfg=validate_release()
 if integration['model_sha256']!=cfg['model_sha256'] or integration['model_sha256_after']!=cfg['model_sha256']:raise ValueError('Result does not match the frozen Version2.2model')
 out=folder/'experimental-results';downloads={p.name:p.read_bytes() for p in out.iterdir() if p.suffix in ('.csv','.json','.txt')};manifest=json.loads((out/'run-manifest.json').read_text());manifest.update(model_version='2.2.0',application_version='2.3.0',analysis_mode='rectangular-raw-video',scientific_status='operational predictions; no whole-recording accuracy established',source_import=integration['source'],analysis_import=integration['analysis'],scale_source=integration['scale_source'],tracking_quality=integration['quality'],arena_calibration=integration['geometry']);downloads['run-manifest.json']=(json.dumps(manifest,indent=2)+'\n').encode()
 result={'filename':filename or Path(integration['source']['path']).name,'events':pd.read_csv(out/'lunge-events.csv'),'byfly':pd.read_csv(out/'summary-by-fly.csv'),'byrecording':pd.read_csv(out/'summary-by-recording.csv'),'manifest':manifest,'downloads':downloads,'experimental':True,'pipeline_version':'2.3.0','run_directory':str(folder)}
 for name in ['integration-manifest.json','frame-time-map.csv','tracking-quality.json']:
  downloads[name]=(folder/name).read_bytes()
 if (folder/'rectangular-calibration.mat.png').exists():downloads['arena-calibration.png']=(folder/'rectangular-calibration.mat.png').read_bytes()
 downloads['calibration.mat']=(folder/'rectangular-calibration.mat').read_bytes()
 parameters=json.loads((folder/'rectangular-calibration.mat.json').read_text());parameters.update(scale_source=integration['scale_source'],independently_verified=False);downloads['calibration-parameters.json']=(json.dumps(parameters,indent=2)+'\n').encode()
 downloads['experimental-report.png']=graphical_report(result);return result

def analyze_rectangular_path(path,bounds,padding,ppm,scale_source,experimental,progress=None,output=None,display_name=None):
 if not experimental:raise ValueError('Confirm experimental predictions before starting')
 path=Path(path).expanduser().resolve();meta=inspect_video(path);validate_rectangle(meta['width'],meta['height'],bounds,padding,ppm)
 RUNS.mkdir(parents=True,exist_ok=True);output=Path(output) if output else RUNS/str(uuid.uuid4())
 if output.exists():raise ValueError('Existing run must be preserved; choose a new output folder')
 report=progress or (lambda p,s:None);logpath=RUNS/(output.name+'-driver.log');command=[sys.executable,str(BUILD/'scripts/v23/video_pipeline.py'),'--video',str(path),'--output',str(output),'--bounds',*map(str,bounds),'--padding',str(padding),'--ppm',str(ppm),'--scale-source',scale_source,'--display-name',Path(display_name or path).name]
 with logpath.open('w') as log:
  proc=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);start=time.monotonic()
  try:
   while proc.poll() is None:
    if time.monotonic()-start>7200:raise ValueError('Analysis exceeded two hours; run logs were preserved')
    stage='Starting import';manifest=output/'integration-manifest.json'
    if manifest.exists():
     try:stage=json.loads(manifest.read_text()).get('stage',stage)
     except json.JSONDecodeError:pass
    report(.2,str(stage)+f' · {int(time.monotonic()-start)}s elapsed (stage, not percentage)');time.sleep(1)
  finally:
   if proc.poll() is None:
    os.killpg(proc.pid,signal.SIGTERM)
    try:proc.wait(timeout=10)
    except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);proc.wait()
 if proc.returncode:
  detail=json.loads((output/'integration-manifest.json').read_text()).get('error','') if (output/'integration-manifest.json').exists() else logpath.read_text(errors='replace')[-500:]
  raise ValueError(f'Rectangular video analysis failed: {detail}. Logs retained at {output}')
 result=load_rectangular_result(output,Path(display_name or path).name);report(1.,'Analysis complete');return result

def analyze_rectangular_upload(content,filename,*args,**kwargs):
 if not content:raise ValueError('The uploaded video is empty')
 if len(content)>MAX_BYTES:raise ValueError('Upload exceeds200MB; use the local-file path option')
 if Path(filename).suffix.lower() not in ('.mp4','.avi'):raise ValueError('Choose an AVI or MP4 video')
 RUNS.mkdir(parents=True,exist_ok=True)
 with tempfile.TemporaryDirectory(prefix='upload-',dir=RUNS) as t:
  path=Path(t)/('source'+Path(filename).suffix.lower());path.write_bytes(content);result=analyze_rectangular_path(path,*args,display_name=Path(filename).name,**kwargs);result['filename']=Path(filename).name;return result

def load_completed_demo():
 d=BUILD/'examples/bmb-starter-results'
 if not d.exists():raise ValueError('Completed starter demonstration is not installed')
 manifest=json.loads((d/'run-manifest.json').read_text())
 from raw_release import validate_release
 _,cfg=validate_release()
 if manifest.get('model_sha256')!=cfg['model_sha256']:raise ValueError('Demo model provenance mismatch')
 result={'filename':'BoyMeetsBoy-movie5 (completed demonstration)','events':pd.read_csv(d/'lunge-events.csv'),'byfly':pd.read_csv(d/'summary-by-fly.csv'),'byrecording':pd.read_csv(d/'summary-by-recording.csv'),'manifest':manifest,'downloads':{p.name:p.read_bytes() for p in d.iterdir() if p.is_file() and p.name!='all-results.zip'},'experimental':True,'pipeline_version':'2.3.0','completed_demo':True};return result
