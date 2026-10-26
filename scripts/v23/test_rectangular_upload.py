"""Actual browser-upload service route on a fixed20-second200FPS source excerpt."""
from pathlib import Path
import sys,subprocess,json,time
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT.parent/'drosophila-aggression')]
from video_service_v23 import analyze_rectangular_upload

def main():
 clip=ROOT/'data/v23-rectangular-upload.avi'
 if not clip.exists():subprocess.run(['/opt/homebrew/bin/ffmpeg','-v','error','-ss','600','-i',str(ROOT.parent/'new-training-data/BoyMeetsBoy/downloads/movie5.avi'),'-t','20','-an','-c:v','copy',str(clip)],check=True)
 start=time.monotonic();result=analyze_rectangular_upload(clip.read_bytes(),'Rectangular Service Test.avi',[20,10,620,479],12,12,'published-nominal',True,output=ROOT/'data/v23-rectangular-upload-run');assert result['filename']=='Rectangular Service Test.avi';assert result['manifest']['source_import']['original_filename']=='Rectangular Service Test.avi';assert result['manifest']['input_schema']['frames_per_fly']==600;assert set(result['events'].recording)<= {'Rectangular Service Test'}
 (ROOT/'reports/v23-days9-10/rectangular-upload-verification.json').write_text(json.dumps({'status':'PASS','actual_uploaded_bytes_service_success':True,'original_filename_preserved':True,'source_fps':200,'analysis_fps':30,'analysis_frames_per_fly':600,'events':len(result['events']),'elapsed_seconds':time.monotonic()-start,'scope':'functional fixed20second excerpt from already examined external recording; not fresh independent accuracy'},indent=2)+'\n')
if __name__=='__main__':main()
