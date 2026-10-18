"""Day1 cohort preparation. Reuse verified movie1; fresh auto-calibrated movies2–5."""
from pathlib import Path
import sys,json,hashlib,shutil,subprocess,time
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT.parent;P=OUT/'drosophila-aggression';R=OUT/'raw-video-integration'
SOURCE=Path('/Users/adityasinghchauhan/Documents/Codex/2026-10-16/files-mentioned-by-the-user-codex/outputs/day3-videos/external-benchmark/Aggression')
sys.path.insert(0,str(P));sys.path.insert(0,str(R/'day5'))
from scripts.auto_calibration import prepare_auto_calibration
from adapter import convert_file
MATLAB='/Applications/MATLAB_R2026a.app/bin/matlab'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def quote(p):return "'"+str(p).replace("'","''")+"'"
def main():
 snapshot=ROOT/'source-snapshot';snapshot.mkdir(exist_ok=True)
 sourcefiles=[P/'app.py',P/'scripts/auto_calibration.py',R/'day5/adapter.py',*sorted((R/'auto-calibration').glob('*.m'))]
 for p in sourcefiles:shutil.copy2(p,snapshot/p.name)
 preservation={'v2_archive_sha256':sha(OUT/'FlyAggression-Analyzer-v2.0.zip'),'frozen_files':json.loads((P/'models/final-v1/freeze-manifest.json').read_text())['files'],'extractor_sources':{str(p):sha(p) for p in sourcefiles}}
 (ROOT/'config/preservation.json').write_text(json.dumps(preservation,indent=2))
 inventory=[]
 for i in range(1,11):
  rec=f'movie{i}';folder=SOURCE/rec
  inventory.append({'recording':rec,'selected':i<=5,'files':{suffix:{'path':str(folder/(rec+suffix)),'exists':(folder/(rec+suffix)).is_file(),'sha256':sha(folder/(rec+suffix))} for suffix in ['.mp4','_track.mat','_actions.mat','_feat.mat']},'diameter_mm':16,'diameter_evidence':'published nominal Aggression assay dimension; no per-recording measurement certificate','already_examined_original_test':i>=6})
 (ROOT/'config/source-inventory.json').write_text(json.dumps(inventory,indent=2))
 for i in range(1,6):
  rec=f'movie{i}';d=ROOT/'data'/rec;d.mkdir(exist_ok=True);started=time.monotonic()
  if (d/'generation.json').exists():print('Already complete',rec,flush=True);continue
  video=SOURCE/rec/(rec+'.mp4');cal=d/'calibration.mat';native=d/'raw-features.mat';track=d/'tracks.mat'
  if i==1:
   old=R/'auto-calibration/movie1-verified-run';m=json.loads((old/'integration-manifest.json').read_text())
   assert m['status']=='complete' and sha(video)==m['video_sha256']
   assert sha(R/'auto-calibration/test-movie1/calibration.mat')==m['calibration_sha256']
   for src,dest in [(R/'auto-calibration/test-movie1/calibration.mat',cal),(old/'tracking/recording/recording-feat.mat',native),(old/'tracking/recording/recording-track.mat',track)]:shutil.copy2(src,dest)
   metadata=json.loads((R/'auto-calibration/test-movie1/metadata.json').read_text());reuse=str(old)
  else:
   print('Calibrating',rec,flush=True)
   auto=prepare_auto_calibration(video.read_bytes(),video.name,16)
   cal.write_bytes(auto['calibration']);(d/'arena-preview.png').write_bytes(auto['preview']);metadata=auto['metadata'];reuse=None
   stage=d/'input';stage.mkdir(exist_ok=True)
   if not (stage/(rec+'.mp4')).exists():(stage/(rec+'.mp4')).symlink_to(video)
   script=d/'track.m';script.write_text(f"restoredefaultpath;addpath({quote(R/'FlyTracker')});modpath;\nvideos=struct('dir_in',{quote(stage)},'dir_out',{quote(d/'tracking')},'filter',{quote(rec+'.mp4')});\noptions=struct('num_cores',4,'num_chunks',16,'save_JAABA',false,'save_xls',false,'save_seg',false,'isdisplay',false,'do_delete_intermediate_results',true,'do_use_scratch_folder_for_intermediates',false,'n_flies',2,'do_compute_relative_features',true);\ntracker(videos,options,{quote(cal)});\n")
   print('Tracking',rec,flush=True)
   with (d/'tracking.log').open('w') as log:subprocess.run([MATLAB,'-batch',f'run({quote(script)})'],stdout=log,stderr=subprocess.STDOUT,check=True)
   shutil.copy2(d/f'tracking/{rec}/{rec}-feat.mat',native);shutil.copy2(d/f'tracking/{rec}/{rec}-track.mat',track)
  (d/'calibration-metadata.json').write_text(json.dumps(metadata,indent=2))
  converted=d/'features36.mat'
  if not converted.exists():convert_file(native,converted,allow_experimental=True)
  result={'recording':rec,'elapsed_seconds':time.monotonic()-started,'reuse':reuse,'calibration':metadata,'diameter_status':'published nominal, not individual physical measurement','video_sha256':sha(video),'files':{n:sha(d/n) for n in ['calibration.mat','tracks.mat','raw-features.mat','features36.mat']},'training_performed':False}
  (d/'generation.json').write_text(json.dumps(result,indent=2));print('Complete',rec,flush=True)
 for p,h in preservation['extractor_sources'].items():assert sha(p)==h
 assert sha(OUT/'FlyAggression-Analyzer-v2.0.zip')==preservation['v2_archive_sha256']
 print('COHORT_GENERATION_COMPLETE',flush=True)
if __name__=='__main__':main()
