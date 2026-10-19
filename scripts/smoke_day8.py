"""Actual short-video UI-service smoke test; no accuracy claim on this training clip."""
from pathlib import Path
import sys,json,subprocess,time
ROOT=Path(__file__).resolve().parents[1];P=ROOT.parent/'drosophila-aggression';sys.path.insert(0,str(P))
from scripts.auto_calibration import prepare_auto_calibration
from scripts.gui_service import analyze_upload,archive_downloads
from video_service_v21 import analyze_video_upload
from raw_release import validate_release
SOURCE=Path('/Users/adityasinghchauhan/Documents/Codex/2026-10-16/files-mentioned-by-the-user-codex/outputs/day3-videos/external-benchmark/Aggression')
def main():
 dest=ROOT/'reports/day8';dest.mkdir(exist_ok=True);temp=ROOT/'data/day8-smoke';temp.mkdir(exist_ok=True);video=temp/'movie1-first300.mp4'
 subprocess.run(['/opt/homebrew/bin/ffmpeg','-y','-i',str(SOURCE/'movie1/movie1.mp4'),'-frames:v','300','-an','-c:v','copy','-video_track_timescale','30','-loglevel','error',str(video)],check=True)
 start=time.monotonic();auto=prepare_auto_calibration((SOURCE/'movie1/movie1.mp4').read_bytes(),'movie1.mp4',16);(dest/'arena-preview.png').write_bytes(auto['preview']);(temp/'calibration.mat').write_bytes(auto['calibration']);(dest/'calibration-metadata.json').write_text(json.dumps(auto['metadata'],indent=2));print('Automatic calibration passed',flush=True)
 result=analyze_video_upload(video.read_bytes(),video.name,auto['calibration'],True,lambda p,s:print(s,flush=True) if p>=.8 else None)
 model,cfg=validate_release();m=result['manifest'];assert m['model_sha256']==cfg['model_sha256'] and m['model_version']=='2.1.0' and m['threshold']==cfg['threshold'] and m['event_rules']==cfg['event_rules'];assert m['input_schema']['frames_per_fly']==300
 for name,data in result['downloads'].items():(dest/('raw-'+name)).write_bytes(data)
 (dest/'raw-results.zip').write_bytes(archive_downloads(result['downloads']))
 print('Raw upload service passed',flush=True)
 original=analyze_upload((P/'datasets/features/movie5_feat.mat').read_bytes(),'movie5_feat.mat');expected=json.loads((P/'models/final-v1/freeze-manifest.json').read_text())['files']['lunge-detector.joblib'];assert original['manifest']['model_sha256']==expected and original['manifest']['threshold']==.5
 for name,data in original['downloads'].items():(dest/('original-'+name)).write_bytes(data)
 (dest/'smoke-verification.json').write_text(json.dumps({'status':'PASS','fresh_auto_calibration':True,'calibration_source':'full movie1 recording; first300-frame excerpt alone failed two-fly reliability guard','fresh_raw_video_tracking_and_extraction':True,'raw_frames_per_fly':300,'raw_model_version':m['model_version'],'raw_model_sha256':m['model_sha256'],'raw_event_rules':m['event_rules'],'raw_threshold':m['threshold'],'csv_png_zip_exports':True,'matlab_original_model_sha256':expected,'original_matlab_events':len(original['events']),'elapsed_seconds':time.monotonic()-start,'scientific_scope':'functional smoke only: automatic calibration from full training movie1, applied to fresh 10-second tracking excerpt; not accuracy validation'},indent=2));print('SMOKE PASS',flush=True)
if __name__=='__main__':main()
