"""Version 2.1 two-fly video -> existing FlyTracker -> frozen raw-video classifier."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

BUILD=Path(__file__).resolve().parents[1]
ROOT=BUILD.parent/'raw-video-integration'
from raw_release import validate_release
FINAL=ROOT.parent/'drosophila-aggression/models/final-v1'
MATLAB=Path('/Applications/MATLAB_R2026a.app/bin/matlab')
sys.path.insert(0,str(ROOT/'day5'))
from adapter import convert_file

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def matstr(value):return "'"+str(value).replace("'","''")+"'"
def verify_freeze():
    expected=json.loads((FINAL/'freeze-manifest.json').read_text())['files']
    actual={name:sha(FINAL/name) for name in expected}
    if actual!=expected:raise ValueError('Frozen model/runtime integrity check failed')
    return actual

def run(video,calibration,output,allow_experimental=False,matlab=MATLAB):
    if not allow_experimental:raise ValueError('Explicit --allow-experimental required: raw-feature numerical compatibility is unresolved')
    before=verify_freeze()
    selected_model,model_config=validate_release()
    video=Path(video).resolve();calibration=Path(calibration).resolve();output=Path(output).resolve();matlab=Path(matlab)
    if not video.is_file() or video.suffix.lower()!='.mp4':raise ValueError('Provide an existing supported MP4 video')
    if not calibration.is_file():raise ValueError('Provide an existing FlyTracker calibration MAT file')
    if not matlab.is_file():raise ValueError('MATLAB executable not found')
    if output.exists():raise ValueError('Output folder already exists; choose a fresh folder')
    output.mkdir(parents=True);started=time.monotonic()
    manifest={'status':'running','experimental':True,'scientific_compatibility':False,'video':str(video),'video_sha256':sha(video),'calibration':str(calibration),'calibration_sha256':sha(calibration),'frozen_files_before':before,'model_release':model_config,'accuracy_claim':'Development validation only; selected reliable subset, no independent final raw-video test','stages':[]}
    def save(): (output/'integration-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    save()
    try:
        # A fixed staged name avoids FlyTracker wildcard interpretation of source names.
        input_dir=output/'input';input_dir.mkdir();os.symlink(video,input_dir/'recording.mp4')
        script=output/'track_video.m'
        script.write_text(f'''restoredefaultpath; addpath({matstr(ROOT/'FlyTracker')}); modpath;
c=load({matstr(calibration)});assert(isfield(c,'calib'),'Missing calib struct');
assert(c.calib.n_flies==2,'Expected two flies');assert(c.calib.FPS==30,'Calibration must specify 30 FPS');
assert(isfinite(c.calib.PPM) && c.calib.PPM>0,'Invalid pixels per mm');
v=VideoReader({matstr(video)});assert(abs(v.FrameRate-30)<1e-6,'Video must be 30 FPS');
videos=struct('dir_in',{matstr(input_dir)},'dir_out',{matstr(output/'tracking')},'filter','recording.mp4');
options=struct('num_cores',4,'num_chunks',16,'save_JAABA',false,'save_xls',false,'save_seg',false,'isdisplay',false,'do_delete_intermediate_results',true,'do_use_scratch_folder_for_intermediates',false,'n_flies',2,'do_compute_relative_features',true);
tracker(videos,options,{matstr(calibration)});
f=load({matstr(output/'tracking/recording/recording-feat.mat')});
assert(size(f.feat.data,1)==2 && abs(size(f.feat.data,2)-v.Duration*v.FrameRate)<=1,'Feature/video frame mismatch');
fprintf('RAW_VIDEO_TRACKING_PASS\\n');
''')
        with (output/'tracking.log').open('w') as log:
            subprocess.run([str(matlab),'-batch',f'run({matstr(script)})'],stdout=log,stderr=subprocess.STDOUT,check=True)
        manifest['stages'].append('fresh video tracking and feature extraction');save()
        feature=output/'experimental_feat.mat'
        manifest['adapter']=convert_file(output/'tracking/recording/recording-feat.mat',feature,allow_experimental=True)
        manifest['stages'].append('Python feature adapter');save()
        with (output/'prediction.log').open('w') as log:
            subprocess.run([sys.executable,str(FINAL/'runtime/analyze.py'),'--input',str(feature),'--output-dir',str(output/'experimental-results'),'--model',str(selected_model),'--fps','30','--recording-id',video.stem],cwd=FINAL/'runtime',stdout=log,stderr=subprocess.STDOUT,check=True)
        manifest['stages'].append('frozen Version 2.1 raw-specific inference and selected event rules')
        manifest['frozen_files_after']=verify_freeze()
        manifest['status']='complete';manifest['elapsed_seconds']=time.monotonic()-started
        (output/'experimental-results/EXPERIMENTAL-RESULTS.txt').write_text('EXPERIMENTAL VERSION 2.1 RAW-VIDEO RESULTS. Development validation on selected reliable intervals only; full-video biological accuracy is not established. Source identities preserved, including possible switches. Original feature classifier unchanged.\n')
        save();return manifest
    except Exception as exc:
        manifest.update(status='failed',error=str(exc),elapsed_seconds=time.monotonic()-started);save();raise

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--video',type=Path,required=True);p.add_argument('--calibration',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--matlab',type=Path,default=MATLAB);p.add_argument('--allow-experimental',action='store_true')
    a=p.parse_args()
    try:r=run(a.video,a.calibration,a.output,a.allow_experimental,a.matlab)
    except (ValueError,OSError,subprocess.CalledProcessError) as e:p.exit(2,f'Integration error: {e}; inspect stage logs in output folder\n')
    print(f"Complete (experimental), {r['elapsed_seconds']:.1f}s. Results: {a.output}/experimental-results")
if __name__=='__main__':main()
