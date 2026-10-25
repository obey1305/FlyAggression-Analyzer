"""Predeclared coverage and continuous-time one-to-one event scoring."""
import numpy as np,pandas as pd
from scipy.optimize import linear_sum_assignment
MATCH_COLUMNS=['recording','fly_id','pred_event_id','expert_event_id','iou','overlap_seconds','onset_error_seconds','offset_error_seconds','duration_error_seconds']
def native_bins(start,end,source_fps=200,analysis_fps=30):
 if not 1<=start<=end or int(start)!=start or int(end)!=end:raise ValueError('Invalid inclusive native interval')
 return ((int(start)-1)*analysis_fps//source_fps,(int(end)*analysis_fps+source_fps-1)//source_fps)
def close_coverage(mask,bounds,initial_keep):
 valid=np.asarray(mask,bool).copy();keep=np.asarray(initial_keep,bool).copy();bounds=np.asarray(bounds,int).reshape(-1,2)
 if len(bounds)!=len(keep) or (len(bounds) and not ((bounds[:,0]>=0)&(bounds[:,1]>bounds[:,0])&(bounds[:,1]<=len(valid))).all()):raise ValueError('Invalid coverage bounds')
 while True:
  old=valid.copy();previous=keep.copy()
  for i,(a,b) in enumerate(bounds):
   if not keep[i] or not valid[a:b].all():keep[i]=False;valid[a:b]=False
  if np.array_equal(old,valid) and np.array_equal(previous,keep):return valid,keep

def whole_prediction(start,end,mask,mapping):
 a,b=int(start)-1,int(end)
 if not 0<=a<b<=len(mask):raise ValueError('Prediction outside grid')
 if not np.asarray(mask,bool)[a:b].all():return False,'coverage_or_unknown_boundary'
 if len(np.unique(mapping[a:b]))!=1:return False,'identity_mapping_switch'
 return True,''
def assign_iou(iou,threshold):
 if not 0<threshold<=1:raise ValueError('Invalid IoU threshold')
 a=np.asarray(iou,float)
 if a.ndim!=2 or not np.isfinite(a).all() or np.any((a<0)|(a>1+1e-12)):raise ValueError('Invalid IoU matrix')
 if 0 in a.shape:return []
 allowed=a>=threshold;score=np.where(allowed,min(a.shape)+1+a,0.)
 r,c=linear_sum_assignment(score,maximize=True)
 return [(int(i),int(j)) for i,j in zip(r,c) if allowed[i,j]]
def match_time(predicted,expert,threshold=.3):
 p=predicted.reset_index(drop=True).copy();g=expert.reset_index(drop=True).copy()
 cols=['recording','fly_id','event_id','start_seconds','stop_seconds_exclusive']
 for d in (p,g):
  if not set(cols)<=set(d) or d.duplicated(cols[:3]).any():raise ValueError('Invalid event keys')
  t=d[cols[-2:]].to_numpy(float)
  if not np.isfinite(t).all() or not (t[:,1]>t[:,0]).all():raise ValueError('Invalid half-open event intervals')
 p['outcome']='FP';g['outcome']='FN';p['matched_expert_event_id']=0;g['matched_pred_event_id']=0;p['overlaps_any_expert']=False;g['overlaps_any_prediction']=False;matches=[]
 for rec,fly in sorted(set(zip(p.recording,p.fly_id))|set(zip(g.recording,g.fly_id))):
  pp=p[p.recording.eq(rec)&p.fly_id.eq(fly)];gg=g[g.recording.eq(rec)&g.fly_id.eq(fly)]
  if pp.empty or gg.empty:continue
  a=pp.start_seconds.to_numpy()[:,None];z=pp.stop_seconds_exclusive.to_numpy()[:,None];b=gg.start_seconds.to_numpy()[None,:];w=gg.stop_seconds_exclusive.to_numpy()[None,:]
  overlap=np.maximum(0,np.minimum(z,w)-np.maximum(a,b));iou=overlap/((z-a)+(w-b)-overlap)
  p.loc[pp.index,'overlaps_any_expert']=(overlap>0).any(axis=1);g.loc[gg.index,'overlaps_any_prediction']=(overlap>0).any(axis=0)
  for i,j in assign_iou(iou,threshold):
   pi,gi=pp.index[i],gg.index[j];pr=p.loc[pi];gt=g.loc[gi]
   p.loc[pi,['outcome','matched_expert_event_id']]=['TP',gt.event_id];g.loc[gi,['outcome','matched_pred_event_id']]=['matched',pr.event_id]
   matches.append(dict(recording=rec,fly_id=int(fly),pred_event_id=int(pr.event_id),expert_event_id=int(gt.event_id),iou=float(iou[i,j]),overlap_seconds=float(overlap[i,j]),onset_error_seconds=float(pr.start_seconds-gt.start_seconds),offset_error_seconds=float(pr.stop_seconds_exclusive-gt.stop_seconds_exclusive),duration_error_seconds=float((pr.stop_seconds_exclusive-pr.start_seconds)-(gt.stop_seconds_exclusive-gt.start_seconds))))
 tp=len(matches);fp=len(p)-tp;fn=len(g)-tp;precision=tp/(tp+fp) if tp+fp else 0.;recall=tp/(tp+fn) if tp+fn else 0.
 metrics={'iou_threshold':threshold,'predicted_events':len(p),'expert_events':len(g),'true_positive_events':tp,'false_positive_events':fp,'false_negative_events':fn,'precision':precision,'recall':recall,'f1':2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 0.}
 return metrics,pd.DataFrame(matches,columns=MATCH_COLUMNS),p,g
