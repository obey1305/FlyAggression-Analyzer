"""Actual preserved circular upload path, with matching10-second source/calibration."""
from pathlib import Path
import sys,json,io,zipfile,time
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT.parent/'drosophila-aggression')]
from video_service_v21 import analyze_video_upload
from scripts.gui_service import archive_downloads

def main():
 source=ROOT.parent/'flyaggression-v2.1/data/day8-smoke/movie1-first300.mp4';cal=ROOT.parent/'flyaggression-v2.2/reports/v22-days7-10/full-movie1/calibration.mat';start=time.monotonic();result=analyze_video_upload(source.read_bytes(),source.name,cal.read_bytes(),True);assert result['manifest']['input_schema']['frames_per_fly']==300;assert result['manifest']['model_version']=='2.2.0';Image.open(io.BytesIO(result['downloads']['experimental-report.png'])).verify();content=archive_downloads(result['downloads'])
 with zipfile.ZipFile(io.BytesIO(content)) as z:
  assert z.testzip() is None
  for n,b in result['downloads'].items():assert z.read(n)==b
 d=ROOT/'data/v23-circle-smoke';d.mkdir(exist_ok=True)
 for n,b in result['downloads'].items():(d/n).write_bytes(b)
 (ROOT/'reports/v23-days9-10/circular-regression.json').write_text(json.dumps({'status':'PASS','actual_circular_upload_success':True,'frames_per_fly':300,'frozen_model_version':'2.2.0','png_zip_csv_verified':True,'event_count':len(result['events']),'elapsed_seconds':time.monotonic()-start,'scope':'functional regression on known training-source excerpt; not accuracy validation'},indent=2)+'\n')
if __name__=='__main__':main()
