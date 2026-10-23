"""Fresh full-length training-source MP4 functional check, not independent accuracy."""
from pathlib import Path
import sys,json,time,zipfile,io,hashlib
import numpy as np,pandas as pd
from scipy.io import loadmat
ROOT=Path(__file__).resolve().parents[2];P=ROOT.parent/'drosophila-aggression';sys.path.insert(0,str(P));sys.path.insert(0,str(ROOT/'scripts'))
from scripts.auto_calibration import prepare_auto_calibration
from scripts.gui_service import archive_downloads
from video_service_v21 import load_video_result
from video_to_lunges_v21 import run
from raw_release import validate_release
from prepare_aligned import SOURCE,load_track,align_positions
from audit_quantification import audit_tables

def main():
 dest=ROOT/'reports/v22-days7-10/full-movie1';dest.mkdir(parents=True,exist_ok=True);video=SOURCE/'movie1/movie1.mp4';started=time.monotonic()
 if (dest/'verification.json').exists():raise ValueError('Completed run exists; preserve it before intentionally starting another run')
 t=time.monotonic();auto=prepare_auto_calibration(video.read_bytes(),video.name,16);auto_seconds=time.monotonic()-t
 cal=dest/'calibration.mat';cal.write_bytes(auto['calibration']);(dest/'arena-preview.png').write_bytes(auto['preview']);(dest/'calibration-metadata.json').write_text(json.dumps(auto['metadata'],indent=2));print('Fresh full-video calibration passed',auto_seconds,flush=True)
 manifest=run(video,cal,dest/'run',True);result=load_video_result(dest/'run','movie1.mp4');out=dest/'run/experimental-results'
 frames=pd.read_csv(out/'frame-predictions.csv');events=result['events'];audit=audit_tables(frames,events,result['byfly'],result['byrecording'])
 model,cfg=validate_release();assert result['manifest']['model_sha256']==cfg['model_sha256'] and result['manifest']['event_rules']==cfg['event_rules'] and result['manifest']['threshold']==cfg['threshold']
 features=loadmat(dest/'run/experimental_feat.mat',simplify_cells=True)['feat'];assert list(features['names'])==cfg['source_feature_names'] and features['data'].shape==(2,54000,36)
 old,ow,*_=load_track(SOURCE/'movie1/movie1_track.mat');new,nw,*_=load_track(dest/'run/tracking/recording/recording-track.mat');assert new.shape==(2,54000,2)
 alignment_cfg=json.loads((ROOT/'config/preparation.json').read_text())['alignment'];mapping,reliable,geometry=align_positions(old,new,ow,nw,alignment_cfg)
 pd.DataFrame({'frame':np.arange(1,54001),'new_fly1_maps_to_reference':mapping+1,'reference_mapping_reliable':reliable,'new_tracking_warning':nw,'reference_tracking_warning':ow,**geometry}).to_csv(dest/'tracking-identity-diagnostics.csv',index=False)
 # CSV parity, all download members, valid PNG and ZIP byte parity.
 exports=dest/'exports';exports.mkdir(exist_ok=True)
 for n,b in result['downloads'].items():(exports/n).write_bytes(b)
 archive=archive_downloads(result['downloads']);(dest/'all-results.zip').write_bytes(archive)
 from PIL import Image
 Image.open(io.BytesIO(result['downloads']['experimental-report.png'])).verify()
 with zipfile.ZipFile(io.BytesIO(archive)) as z:
  assert set(z.namelist())==set(result['downloads'])
  for n,b in result['downloads'].items():assert z.read(n)==b
 proof={'status':'PASS','run_type':'fresh complete 30-minute movie1 training-source functional test; not independent accuracy','video_sha256':hashlib.sha256(video.read_bytes()).hexdigest(),'automatic_calibration_seconds':auto_seconds,'tracking_adapter_prediction_seconds':manifest['elapsed_seconds'],'total_seconds':time.monotonic()-started,'model_sha256':cfg['model_sha256'],'threshold':cfg['threshold'],'event_rules':cfg['event_rules'],'audit':audit,'features_shape':list(features['data'].shape),'nominal_arena_mm':16,'physical_diameter_caveat':'published benchmark nominal, not independently measured per recording','tracking_identity_audit':{'frames':54000,'reliable_reference_mapping_frames':int(reliable.sum()),'uncertain_reference_mapping_frames':int((~reliable).sum()),'pointwise_mapping_changes':int((np.diff(mapping)!=0).sum()),'new_tracking_warning_frames':int(nw.sum()),'biological_identity_continuity_certified':False},'csv_png_zip_parity':True,'inference_annotation_files_read':result['manifest']['annotation_files_read'],'reference_tracks_used_after_inference_for_audit_only':True}
 import subprocess
 baseline=ROOT.parent/'flyaggression-v2.1/models/raw-v2.1/lunge-detector.joblib'
 subprocess.run([sys.executable,str(P/'models/final-v1/runtime/analyze.py'),'--input',str(dest/'run/experimental_feat.mat'),'--output-dir',str(dest/'baseline-paired-results'),'--model',str(baseline),'--fps','30','--recording-id','movie1'],check=True,stdout=subprocess.DEVNULL)
 for name in ['frame-predictions.csv','lunge-events.csv']:
  pd.testing.assert_frame_equal(pd.read_csv(dest/'run/experimental-results'/name),pd.read_csv(dest/'baseline-paired-results'/name))
 (dest/'verification.json').write_text(json.dumps(proof,indent=2));print(json.dumps(proof,indent=2),flush=True)
if __name__=='__main__':main()
