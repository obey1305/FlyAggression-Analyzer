"""Prepare the fixed2-second native200FPS diagnostic, without label-based selection."""
from pathlib import Path
import subprocess,json,hashlib
ROOT=Path(__file__).resolve().parents[2]
def main():
 src=ROOT.parent/'new-training-data/BoyMeetsBoy/downloads/movie5.avi';target=ROOT/'data/v23-input/native200-probe.avi'
 if target.exists():raise ValueError('Existing native probe must be preserved')
 command=['/opt/homebrew/bin/ffmpeg','-v','error','-ss','640','-i',str(src),'-t','2','-an','-c:v','copy',str(target)];subprocess.run(command,check=True)
 info=json.loads(subprocess.check_output(['/opt/homebrew/bin/ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=nb_frames,r_frame_rate','-of','json',str(target)],text=True))['streams'][0]
 assert info['nb_frames']=='400' and info['r_frame_rate']=='200/1'
 (ROOT/'reports/v23-days1-4/native-probe-import.json').write_text(json.dumps({'command':command,'source_start_seconds':640,'source_frame_1based_start':128001,'source_fps':200,'frames':400,'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'selection':'fixed time, independent of annotations/predictions'},indent=2)+'\n')
if __name__=='__main__':main()
