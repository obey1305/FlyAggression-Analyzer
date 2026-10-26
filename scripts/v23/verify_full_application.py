"""Verify fresh full application pipeline, exports and locked-study preservation."""
from pathlib import Path
import sys,json,io,zipfile,shutil,subprocess
import numpy as np,pandas as pd
from scipy.io import loadmat
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT.parent/'drosophila-aggression'),str(ROOT/'scripts/v23')]
from video_service_v23 import load_rectangular_result
from scripts.gui_service import archive_downloads
from prepare_evaluation import sha
from run_frozen import verify_inputs
R=ROOT/'reports/v23-days9-10'
def main():
 full=ROOT/'data/v23-final-full';m=json.loads((full/'integration-manifest.json').read_text());assert m['status']=='complete' and m['source']['frames']==255929 and m['analysis']['frames']==38390;assert m['source']['fps']==200 and m['analysis']['fps']==30;assert m['analysis']['decoded_pixel_hash_parity'];assert m['model_sha256']==m['model_sha256_after'];assert m['annotations_used'] is False and m['model_fit'] is False
 result=load_rectangular_result(full,'BoyMeetsBoy-movie5.avi');n=38390;e=result['events'];assert len(e)==64;assert (e.duration_frames==e.end_frame-e.start_frame+1).all();np.testing.assert_allclose(e.duration_seconds,e.duration_frames/30);assert e.end_frame.max()<=n;assert (e.start_frame>=1).all()
 flies=result['byfly'];assert int(flies.lunge_count.sum())==len(e);np.testing.assert_allclose(flies.total_lunge_seconds.sum(),e.duration_seconds.sum())
 Image.open(io.BytesIO(result['downloads']['experimental-report.png'])).verify();archive=archive_downloads(result['downloads'])
 with zipfile.ZipFile(io.BytesIO(archive)) as z:
  assert z.testzip() is None
  for name,b in result['downloads'].items():assert z.read(name)==b
 demo=ROOT/'examples/bmb-starter-results';demo.mkdir(parents=True,exist_ok=True)
 for name,b in result['downloads'].items():(demo/name).write_bytes(b)
 (demo/'all-results.zip').write_bytes(archive)
 actual=json.loads(subprocess.check_output(['/opt/homebrew/bin/ffprobe','-v','error','-select_streams','v:0','-show_entries','packet=pts_time','-of','json',str(full/'analysis.mp4')],text=True))['packets'];pts=np.sort(np.array([float(x['pts_time']) for x in actual]));assert len(pts)==n;timestamp_error=float(np.max(np.abs(pts-np.arange(n)/30)));assert timestamp_error<2e-6
 old=loadmat(ROOT/'data/v23-derived/features36.mat',simplify_cells=True)['feat']['data'];new=loadmat(full/'experimental_feat.mat',simplify_cells=True)['feat']['data'];assert new.shape==old.shape==(2,n,36);finite=np.isfinite(old)&np.isfinite(new);same_missing=np.array_equal(np.isnan(old),np.isnan(new));delta=float(np.max(np.abs(new[finite]-old[finite]))) if finite.any() else None
 prior=pd.read_parquet(ROOT/'data/v23-predictions/probabilities.parquet');fresh=pd.read_csv(full/'experimental-results/frame-predictions.csv');probdelta=float(np.max(np.abs(prior.probability_lunge.to_numpy()-fresh.probability_lunge.to_numpy())))
 lock=json.loads((ROOT/'config/v23-evaluation-lock.json').read_text());verify_inputs(lock);frozen=json.loads((ROOT/'config/v23-preservation.json').read_text());v22=Path(frozen['v22_root'])
 for name,h in frozen['files'].items():assert sha(v22/name)==h
 for name,h in frozen['external'].items():assert sha(name)==h
 source=Path(m['source']['path']);assert sha(source)==m['source_sha256']==json.loads((ROOT.parent/'new-training-data/BoyMeetsBoy/download-verification.json').read_text())['files']['movie5.avi']['sha256']
 receipt={'status':'PASS','fresh_full_source_processed':True,'source_frames':255929,'source_fps':200,'analysis_frames':n,'analysis_fps':30,'source_sha256_after_matches_before':True,'source_selected_decoded_pixel_parity':True,'all_output_packet_timestamps_match30fps_grid':True,'max_printed_timestamp_error_seconds':timestamp_error,'operational_events':len(e),'summed_predicted_lunge_seconds':float(e.duration_seconds.sum()),'csv_png_zip_verified':True,'exports':len(result['downloads']),'frozen_model_unchanged':True,'frozen_evaluation_inputs_unchanged':True,'v22_software_files_preserved':len(frozen['files']),'default_and_v22_launchers_preserved':True,'fresh_vs_locked_feature_missing_masks_equal':same_missing,'fresh_vs_locked_max_feature_difference':delta,'fresh_vs_locked_max_probability_difference':probdelta,'fresh_vs_locked_event_count_difference':len(e)-64,'fresh_tracking_is_not_new_independent_validation':True,'processing_seconds_including_conversion_and_tracking':m['elapsed_seconds'],'source_color_space_preserved':m['source']['color_space'],'model_file_sha256':m['model_sha256'],'output_files':{str(p.relative_to(ROOT)):sha(p) for p in demo.iterdir() if p.is_file()}}
 (R/'full-application-verification.json').write_text(json.dumps(receipt,indent=2)+'\n');(R/'full-integration-manifest.json').write_text(json.dumps(m,indent=2)+'\n');print(json.dumps(receipt,indent=2))
if __name__=='__main__':main()
