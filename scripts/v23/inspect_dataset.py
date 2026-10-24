"""Read-only provider inventory, timing projection and reference-mask audit."""
from pathlib import Path
import json,sys,hashlib
import numpy as np,pandas as pd
from scipy.io import loadmat
from import_tools import frame_map,project_interval,rectangle_mask
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT.parent;BMB=OUT/'new-training-data/BoyMeetsBoy';R=ROOT/'reports/v23-days1-4';SRC=BMB/'extracted/Boy_meets_boy light'
sys.path.insert(0,str(ROOT/'scripts'))
from tracking_io import load_track

def main():
 inventory=[]
 for d in sorted(SRC.glob('movie*')):
  for p in sorted(d.glob('*.mat')):
   content=loadmat(p,simplify_cells=True);entry={'recording':d.name,'file':str(p.relative_to(BMB)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'top_level_keys':[k for k in content if not k.startswith('__')]}
   if p.name.endswith('_actions.mat'):
    behaviors=list(content['behs']);entry['behaviors']=behaviors;entry['bouts_cell_shape']=list(content['bouts'].shape);counts=[]
    for fly in range(2):
     for j,b in enumerate(behaviors):
      a=np.asarray(content['bouts'][fly,j]);counts.append({'reference_fly':fly+1,'behavior':str(b),'shape':list(a.shape),'count':int(len(np.atleast_2d(a))) if a.size else 0})
    entry['bouts']=counts
   elif p.name.endswith('_track.mat'):
    xy,w,data,names=load_track(p);entry.update(shape=list(data.shape),names=[str(n) for n in names],warning_frames=int(w.sum()))
   elif 'feat' in content:
    f=content['feat'];entry.update(shape=list(np.asarray(f['data']).shape),names=[str(n) for n in np.asarray(f['names']).ravel()])
   inventory.append(entry)
 (R/'dataset-inventory.json').write_text(json.dumps(inventory,indent=2)+'\n')
 decode=json.loads((R/'full-video-verification.json').read_text()) if (R/'full-video-verification.json').exists() else {}
 m=frame_map(255929);m.to_csv(R/'frame-time-map.csv',index=False);rows=[]
 for annotator,suffix in [('primary','actions'),('secondary','second_actions')]:
  g=loadmat(SRC/'movie5'/f'movie5_{suffix}.mat',simplify_cells=True);j=list(g['behs']).index('lunge')
  for fly in range(2):
   cell=np.asarray(g['bouts'][fly,j]);a=np.atleast_2d(cell) if cell.size else []
   for i,row in enumerate(a,1):
    start,end=map(int,row[:2]);assert 1<=start<=end<=255929
    p=project_interval(start,end,m);p.update(annotator=annotator,reference_fly=fly+1,event_id=i,source_start_frame=start,source_end_frame=end,source_onset_seconds=(start-1)/200,source_stop_exclusive_seconds=end/200,source_extra_columns=json.dumps(row[2:].tolist()))
    if p['sample_count']:
     p['onset_grid_shift_seconds']=(p['analysis_start_frame']-1)/30-(start-1)/200;p['stop_grid_shift_seconds']=p['analysis_end_frame']/30-end/200
    rows.append(p)
 bouts=pd.DataFrame(rows);bouts.to_csv(R/'lunge-time-projection.csv',index=False)
 xy,w,data,names=load_track(SRC/'movie5/movie5_track.mat');mask=rectangle_mask(640,480,[20,10,620,479],12)
 finite=np.isfinite(xy).all(axis=2);ix=np.rint(np.nan_to_num(xy[:,:,0],nan=-1000)).astype(int)-1;iy=np.rint(np.nan_to_num(xy[:,:,1],nan=-1000)).astype(int)-1;inside=finite&(ix>=0)&(ix<640)&(iy>=0)&(iy<480);inside[inside]=mask[iy[inside],ix[inside]]
 summary={'namespace':'flyvsfly_boymeetsboy_movie5','source_frames':255929,'source_fps':200,'analysis_frames':len(m),'analysis_fps':30,'native_full_decode_exit_code':decode.get('native_decode_exit_code'),'native_full_decode_error_log_bytes':(R/'native-full-decode.log').stat().st_size,'reference_shape':list(data.shape),'reference_warning_frames':int(w.sum()),'reference_position_min':np.nanmin(xy,axis=(0,1)).tolist(),'reference_position_max':np.nanmax(xy,axis=(0,1)).tolist(),'reference_centroids_inside_padded_mask':int(inside.sum()),'reference_centroids_total':int(inside.size),'reference_centroids_nonfinite':int((~finite).sum()),'finite_reference_centroids_outside_mask':int((finite&~inside).sum()),'mask_bounds_inclusive':[8,1,632,480],'scale_pixels_per_mm':12,'scale_evidence':'Published cohort-level nominal; not independently measured per recording','annotation_indexing':'MATLAB 1-based inclusive frame ranges, confirmed by provider visualizer.m start:end indexing','extra_annotation_columns':'Preserved, semantics not assumed; annotators remain separate','model_inference_performed':False,'training_performed':False,'timing':{k:{'bouts':len(g),'lost_entirely':int(g.lost_by_sampling.sum()),'one_or_two_analysis_samples':int(g.sample_count.le(2).sum()),'median_analysis_samples':float(g.sample_count.median()),'max_absolute_onset_grid_shift_seconds':float(g.onset_grid_shift_seconds.abs().max()),'max_absolute_stop_grid_shift_seconds':float(g.stop_grid_shift_seconds.abs().max())} for k,g in bouts.groupby('annotator')}}
 (R/'inspection-summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
