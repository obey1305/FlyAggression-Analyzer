"""Actual successful upload-service call using matching full-movie calibration and short excerpt."""
from pathlib import Path
import sys,json,time,zipfile,io
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'scripts'));sys.path.insert(0,str(ROOT.parent/'drosophila-aggression'))
from video_service_v21 import analyze_video_upload
from scripts.gui_service import archive_downloads
from raw_release import validate_release

def main():
 folder=ROOT/'reports/v22-days7-10/upload-smoke';folder.mkdir(exist_ok=True);video=ROOT.parent/'flyaggression-v2.1/data/day8-smoke/movie1-first300.mp4';cal=ROOT/'reports/v22-days7-10/full-movie1/calibration.mat';start=time.monotonic();result=analyze_video_upload(video.read_bytes(),video.name,cal.read_bytes(),True)
 _,cfg=validate_release();assert result['manifest']['model_version']=='2.2.0' and result['manifest']['model_sha256']==cfg['model_sha256'];assert result['manifest']['input_schema']['frames_per_fly']==300
 for name,b in result['downloads'].items():(folder/name).write_bytes(b)
 archive=archive_downloads(result['downloads']);(folder/'all-results.zip').write_bytes(archive);Image.open(io.BytesIO(result['downloads']['experimental-report.png'])).verify()
 with zipfile.ZipFile(io.BytesIO(archive)) as z:
  for n,b in result['downloads'].items():assert z.read(n)==b
 (folder/'verification.json').write_text(json.dumps({'status':'PASS','model_version':'2.2.0','frames_per_fly':300,'actual_upload_service_success':True,'elapsed_seconds':time.monotonic()-start,'png_zip_verified':True,'scope':'functional10second training-source excerpt with calibration from matching fullmovie; no independentaccuracy'},indent=2)+'\n')
if __name__=='__main__':main()
