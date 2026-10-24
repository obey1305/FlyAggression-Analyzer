"""Deterministic30FPS import; no model/annotation-dependent choices."""
from pathlib import Path
import subprocess,json,time,sys,hashlib
from import_tools import frame_map,selection_filter
ROOT=Path(__file__).resolve().parents[2];SOURCE=ROOT.parent/'new-training-data/BoyMeetsBoy/downloads/movie5.avi';D=ROOT/'data/v23-input';R=ROOT/'reports/v23-days1-4';FF='/opt/homebrew/bin/ffmpeg'
def sha256_file(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for block in iter(lambda:f.read(1048576),b''):h.update(block)
 return h.hexdigest()
def main():
 D.mkdir(exist_ok=True);out=D/'movie5-analysis30.mp4'
 if out.exists():raise ValueError('Existing analysis video must be preserved')
 vf=selection_filter(255929);start=time.monotonic()
 command=[FF,'-v','error','-i',str(SOURCE),'-filter_complex',vf+',split=2[a][b]','-map','[a]','-an','-c:v','libx264','-preset','fast','-crf','0','-pix_fmt','yuvj420p','-color_range','pc','-colorspace','smpte170m','-r','30','-fps_mode','cfr','-movflags','+faststart',str(out),'-map','[b]','-an','-c:v','rawvideo','-pix_fmt','yuvj420p','-r','30','-fps_mode','cfr','-f','framemd5',str(R/'source-selected-frames.framemd5')]
 (R/'conversion-command.json').write_text(json.dumps(command,indent=2)+'\n')
 with (R/'conversion.log').open('w') as log:subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,check=True)
 with (R/'analysis-frame-hash.log').open('w') as log:subprocess.run([FF,'-v','error','-i',str(out),'-an','-c:v','rawvideo','-pix_fmt','yuvj420p','-f','framemd5',str(R/'analysis-decoded-frames.framemd5')],stdout=log,stderr=subprocess.STDOUT,check=True)
 def hashes(p):return [line.split(',')[-1].strip() for line in p.read_text().splitlines() if line and not line.startswith('#')]
 a=hashes(R/'source-selected-frames.framemd5');b=hashes(R/'analysis-decoded-frames.framemd5');assert len(a)==len(b)==38390;assert a==b,'DecodedYUV pixel change'
 m=frame_map(255929);report={'status':'PASS','native_frames':255929,'native_fps':200,'analysis_frames':38390,'analysis_fps':30,'maximum_sample_time_error_seconds':float(m.sample_error_seconds.abs().max()),'source_duration_seconds':255929/200,'analysis_duration_seconds':38390/30,'duration_grid_tail_difference_seconds':38390/30-255929/200,'decoded_yuv_frame_hash_parity':True,'matlab_rgb_decoder_caveat':'readerprobe firstframe differed at most1 intensity unit; compare representative frames separately','elapsed_seconds':time.monotonic()-start,'encoding':'H264CRF0 fullrangeYUV420, no spatialresize or frame interpolation','video_sha256':sha256_file(out)};(R/'conversion-verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
