"""V2.3 rectangular video import→tracking→frozen-model reports. No fitting or labels."""
from pathlib import Path
from fractions import Fraction
import argparse,json,subprocess,sys,os,time,hashlib
import numpy as np,pandas as pd
from scipy.io import savemat
from import_tools import frame_map,selection_filter,rectangle_mask
from tracking_io import load_track
ROOT=Path(__file__).resolve().parents[2]
FF=os.environ.get('FLYAGGRESSION_FFMPEG','/opt/homebrew/bin/ffmpeg');PROBE=os.environ.get('FLYAGGRESSION_FFPROBE','/opt/homebrew/bin/ffprobe');MATLAB=os.environ.get('FLYAGGRESSION_MATLAB','/Applications/MATLAB_R2026a.app/bin/matlab')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def validate_metadata(v):
 try:
  rate=Fraction(v['r_frame_rate']);avg=Fraction(v['avg_frame_rate']);n=int(v['nb_frames']);w=int(v['width']);h=int(v['height'])
 except (KeyError,ValueError,ZeroDivisionError) as e:raise ValueError('Video must provide a valid frame count and constant frame rate') from e
 if rate!=avg or rate.denominator!=1 or int(rate) not in (30,200):raise ValueError('Supported rates are constant30 or200FPS; variable/fractional rates are unsupported')
 if n<10 or min(w,h)<32 or n/int(rate)>3600:raise ValueError('Video must have at least10frames, valid dimensions and duration at most60minutes')
 if v.get('duration') not in (None,'N/A') and abs(float(v['duration'])-n/int(rate))>max(.02,1/int(rate)):raise ValueError('Video duration/frame count mismatch')
 return {'width':w,'height':h,'frames':n,'fps':int(rate),'duration_seconds':n/int(rate),'analysis_fps':30}
def inspect_video(path):
 path=Path(path).expanduser().resolve()
 if not path.is_file() or path.suffix.lower() not in ('.avi','.mp4'):raise ValueError('Choose an existing AVI or MP4 video')
 try:
  info=json.loads(subprocess.check_output([PROBE,'-v','error','-select_streams','v:0','-show_entries','stream=width,height,nb_frames,r_frame_rate,avg_frame_rate,duration,pix_fmt,color_range,color_space','-of','json',str(path)],stderr=subprocess.PIPE,text=True))['streams'][0];meta=validate_metadata(info)
 except (subprocess.CalledProcessError,KeyError,IndexError,json.JSONDecodeError) as exc:raise ValueError('Video is unreadable or incompatible') from exc
 if info.get('pix_fmt') not in ('yuv420p','yuvj420p'):raise ValueError('Only tested8-bitYUV420 videos are supported')
 meta.update(path=str(path),pix_fmt=info['pix_fmt'],color_range=info.get('color_range','pc' if info['pix_fmt']=='yuvj420p' else 'tv'),color_space=info.get('color_space','smpte170m'));return meta
def validate_rectangle(w,h,bounds,padding,ppm):
 if not np.isfinite(ppm) or ppm<=0:raise ValueError('Supply a positive pixels-per-mm scale and its evidence')
 mask=rectangle_mask(w,h,list(bounds),padding)
 if mask.all():raise ValueError('Leave outside pixels around the tracking mask; a full-image mask gives invalid wall distances')
 y,x=np.where(mask);return {'bounds':list(bounds),'padding':padding,'pixels_per_mm':float(ppm),'tracking_bounds':[int(x.min()+1),int(y.min()+1),int(x.max()+1),int(y.max()+1)]}
def recording_identity(path,display_name=None):
 name=Path(display_name or path).name
 return name,Path(name).stem
def quote(p):return "'"+str(p).replace("'","''")+"'"
def save(p,x):p.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def run(video,output,bounds,padding,ppm,scale_source,display_name=None):
 meta=inspect_video(video);original_name,recording_id=recording_identity(video,display_name);meta['original_filename']=original_name;geometry=validate_rectangle(meta['width'],meta['height'],bounds,padding,ppm)
 if scale_source not in ('user-measured','published-nominal','unverified-user-value'):raise ValueError('Choose scale provenance')
 output=Path(output).resolve()
 if output.exists():raise ValueError('Output already exists; preserve the completed or failed run')
 output.mkdir(parents=True);start=time.monotonic();sys.path.insert(0,str(ROOT/'scripts'));from raw_release import validate_release
 model,cfg=validate_release();frozen_before=sha(model);manifest={'status':'running','pipeline_version':'2.3.0','source':meta,'geometry':geometry,'scale_source':scale_source,'scale_independently_verified':False,'model_release':cfg,'source_sha256':sha(video),'model_sha256':frozen_before,'stages':[],'annotations_used':False,'model_fit':False}
 def stage(s):manifest['stage']=s;save(output/'integration-manifest.json',manifest)
 try:
  stage('Checking original video timestamps')
  packets=json.loads(subprocess.check_output([PROBE,'-v','error','-select_streams','v:0','-show_entries','packet=pts_time','-of','json',str(video)],text=True))['packets'];pts=np.sort(np.array([float(p['pts_time']) for p in packets]));assert len(pts)==meta['frames'],'Packet/frame count mismatch';error=float(np.max(np.abs(pts-pts[0]-np.arange(len(pts))/meta['fps'])))
  if error>2e-6:raise ValueError('Actual source timestamps are not a constant-rate grid; conversion refused')
  manifest['source_timestamp_max_error_seconds']=error;manifest['source_start_timestamp_seconds']=float(pts[0]);mapping=frame_map(meta['frames'],meta['fps'],30);mapping.to_csv(output/'frame-time-map.csv',index=False)
  stage('Converting video to30FPS with explicit source mapping');analysis=output/'analysis.mp4';pixel=meta['pix_fmt'];space=meta['color_space'] if meta['color_space'] not in ('unknown','reserved') else 'smpte170m'
  vf=selection_filter(meta['frames'],meta['fps'],30)+',split=2[a][b]';cmd=[FF,'-v','error','-i',str(video),'-filter_complex',vf,'-map','[a]','-an','-c:v','libx264','-preset','fast','-crf','0','-pix_fmt',pixel,'-color_range',meta['color_range'],'-colorspace',space,'-r','30','-fps_mode','cfr','-movflags','+faststart',str(analysis),'-map','[b]','-an','-c:v','rawvideo','-pix_fmt',pixel,'-r','30','-fps_mode','cfr','-f','framemd5',str(output/'source-selected.framemd5')];save(output/'conversion-command.json',cmd)
  with (output/'conversion.log').open('w') as log:subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True)
  with (output/'decoded.framemd5').open('w') as dest,(output/'decode.log').open('w') as log:subprocess.run([FF,'-v','error','-xerror','-i',str(analysis),'-an','-c:v','rawvideo','-pix_fmt',pixel,'-f','framemd5','-'],stdout=dest,stderr=log,check=True)
  hashes=lambda p:[s.split(',')[-1].strip() for s in p.read_text().splitlines() if s and not s.startswith('#')]
  a=hashes(output/'source-selected.framemd5');b=hashes(output/'decoded.framemd5')
  if len(a)!=len(mapping) or a!=b:raise ValueError('Converted video frame count or decoded pixels changed')
  converted=inspect_video(analysis);assert converted['fps']==30 and converted['frames']==len(mapping);manifest['analysis']={**converted,'maximum_sample_time_error_seconds':float(mapping.sample_error_seconds.abs().max()),'decoded_pixel_hash_parity':True,'duration_grid_tail_difference_seconds':len(mapping)/30-meta['duration_seconds']};manifest['stages'].append('lossless mapped30FPS import')
  stage('Calibrating rectangular arena and body/contrast parameters');track=output/'tracking';cal=output/'rectangular-calibration.mat';script=output/'track.m';bs=' '.join(map(str,bounds));script.write_text(f"restoredefaultpath;addpath({quote(ROOT/'scripts/v23')});\nrectangular_calibration({quote(analysis)},{quote(cal)},{ppm},[{bs}],{padding});\nload({quote(cal)},'calib');calib.v23.physical_scale_status={quote(scale_source+'; user-supplied scale, not independently verified')};save({quote(cal)},'calib','-v7.3');\nvideos=struct('dir_in',{quote(output)},'dir_out',{quote(track)},'filter','analysis.mp4');options=struct('num_cores',4,'num_chunks',16,'save_JAABA',false,'save_xls',false,'save_seg',false,'isdisplay',false,'do_delete_intermediate_results',true,'do_use_scratch_folder_for_intermediates',false,'n_flies',2,'do_compute_relative_features',true);\ntracker(videos,options,{quote(cal)});\n")
  stage('Tracking two flies and extracting raw features')
  with (output/'tracking.log').open('w') as log:subprocess.run([MATLAB,'-batch',f'run({quote(script)})'],stdout=log,stderr=subprocess.STDOUT,check=True)
  manifest['stages'].append('fresh full rectangular tracking');stage('Converting36features and checking tracking quality')
  sys.path.insert(0,str(ROOT.parent/'raw-video-integration/day5'));from adapter import read_and_convert,STATUS
  raw=track/'analysis/analysis-feat.mat';names,data,units=read_and_convert(raw);assert data.shape==(2,len(mapping),36) and names==cfg['source_feature_names'];feat=output/'experimental_feat.mat';savemat(feat,{'feat':{'names':np.array(names,dtype=object),'units':np.array(units,dtype=object),'data':data,'integration_status':STATUS}},do_compression=True)
  xy,w,_,_=load_track(track/'analysis/analysis-track.mat');quality={'tracking_warning_frames':int(w.sum()),'missing_xy_rows_by_fly':[int((~np.isfinite(xy[f]).all(axis=1)).sum()) for f in range(2)],'nonfinite36feature_rows_by_fly':[int((~np.isfinite(data[f]).all(axis=1)).sum()) for f in range(2)],'identity_policy':'native FlyTracker IDs retained; biological continuity not verified','reference_identity_or_expert_annotations_used':False};save(output/'tracking-quality.json',quality);manifest['quality']=quality;manifest['stages'].append('pinned36feature conversion')
  stage('Running frozen2.2model and writing prediction reports');runtime=ROOT.parent/'drosophila-aggression/models/final-v1/runtime';results=output/'experimental-results'
  with (output/'prediction.log').open('w') as log:subprocess.run([sys.executable,str(runtime/'analyze.py'),'--input',str(feat),'--output-dir',str(results),'--model',str(model),'--fps','30','--recording-id',recording_id],cwd=runtime,stdout=log,stderr=subprocess.STDOUT,check=True)
  events=pd.read_csv(results/'lunge-events.csv');events['native_start_frame_nearest']=mapping.source_frame.to_numpy()[events.start_frame.to_numpy(int)-1];events['native_end_frame_nearest']=mapping.source_frame.to_numpy()[events.end_frame.to_numpy(int)-1];events.to_csv(results/'lunge-events.csv',index=False)
  assert sha(model)==frozen_before;manifest.update(status='complete',stage='Complete',elapsed_seconds=time.monotonic()-start,event_count=len(events),feature_sha256=sha(feat),analysis_video_sha256=sha(analysis),model_sha256_after=sha(model));manifest['stages'].append('frozen model prediction; no tuning');save(output/'integration-manifest.json',manifest);return manifest
 except Exception as exc:manifest.update(status='failed',error=str(exc),elapsed_seconds=time.monotonic()-start);save(output/'integration-manifest.json',manifest);raise

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--video',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--bounds',type=int,nargs=4,required=True);parser.add_argument('--padding',type=int,default=12);parser.add_argument('--ppm',type=float,required=True);parser.add_argument('--scale-source',choices=['user-measured','published-nominal','unverified-user-value'],required=True);parser.add_argument('--display-name');a=parser.parse_args();run(a.video,a.output,a.bounds,a.padding,a.ppm,a.scale_source,a.display_name)
if __name__=='__main__':main()
