"""Offline reference-assisted identity alignment. No interpolation or feature/model changes."""
import numpy as np

def runs(mask):
 changes=np.diff(np.r_[False,np.asarray(mask,bool),False].astype(int))
 return list(zip(np.flatnonzero(changes==1),np.flatnonzero(changes==-1)))
def axial_error(a,b):return np.abs((np.asarray(a)-np.asarray(b)+np.pi/2)%np.pi-np.pi/2)
def align_identity(old,new,old_ori,new_ori,baseline_mapping,baseline_reliable,old_warning,new_warning,cfg):
 old=np.asarray(old);new=np.asarray(new);old_ori=np.asarray(old_ori);new_ori=np.asarray(new_ori)
 if old.shape!=new.shape or old.shape[0]!=2 or old.shape[2]!=2 or old_ori.shape!=old.shape[:2] or new_ori.shape!=old_ori.shape:raise ValueError('Paired, frame-aligned position and orientation grids required')
 n=old.shape[1];mapping=np.asarray(baseline_mapping,int).copy();reliable=np.asarray(baseline_reliable,bool).copy();bridged=np.zeros(n,bool);attempts=[]
 if len(mapping)!=n or len(reliable)!=n or not np.isin(mapping,[0,1]).all():raise ValueError('Invalid baseline mapping')
 positions=np.stack([np.linalg.norm(old-new,axis=2).max(axis=0),np.linalg.norm(old-new[::-1],axis=2).max(axis=0)])
 angles=np.stack([axial_error(old_ori,new_ori).max(axis=0),axial_error(old_ori,new_ori[::-1]).max(axis=0)])
 separation=np.minimum(np.linalg.norm(old[0]-old[1],axis=1),np.linalg.norm(new[0]-new[1],axis=1))
 finite=np.isfinite(old).all(axis=(0,2))&np.isfinite(new).all(axis=(0,2))&np.isfinite(old_ori).all(axis=0)&np.isfinite(new_ori).all(axis=0)
 warning=np.asarray(old_warning,bool)|np.asarray(new_warning,bool);anchor=cfg['anchor_frames_each_side'];candidate=(angles[1]<angles[0]).astype(int)
 for a,b in runs(~np.asarray(baseline_reliable,bool)):
  reason=None;lo=a-anchor;hi=b+anchor
  if b-a>cfg['maximum_gap_frames']:reason='gap_too_long'
  elif lo<0 or hi>n:reason='missing_two_sided_anchors'
  elif not (baseline_reliable[lo:a].all() and baseline_reliable[b:hi].all()):reason='anchors_not_reliable'
  elif np.unique(mapping[lo:a]).size!=1 or np.unique(mapping[b:hi]).size!=1:reason='anchors_not_stable'
  elif warning[a:b].any():reason='tracking_warning'
  elif not finite[lo:hi].all():reason='missing_position_or_orientation'
  else:
   chosen=candidate[a:b];ix=np.arange(a,b);alt=1-chosen
   if (separation[a:b]<cfg['minimum_separation_pixels']).any():reason='bodies_too_close'
   elif (positions[chosen,ix]>cfg['maximum_pair_error_pixels']).any():reason='position_disagreement'
   elif (angles[chosen,ix]>cfg['maximum_axial_orientation_error_radians']).any():reason='orientation_disagreement'
   elif ((angles[alt,ix]-angles[chosen,ix])<cfg['minimum_orientation_advantage_radians']).any():reason='orientation_not_discriminating'
   else:
    path=np.r_[mapping[a-1],chosen,mapping[b]]
    if (np.diff(path)!=0).sum()>cfg['maximum_assignment_changes_within_bridge']:reason='multiple_assignment_changes'
    else:
     window=np.arange(a-1,b+1);aligned=np.empty((2,len(window),2));chosen_path=path
     for ref in [0,1]:aligned[ref]=new[np.where(chosen_path==0,ref,1-ref),window]
     residual=np.linalg.norm(np.diff(aligned,axis=1)-np.diff(old[:,window],axis=1),axis=2)
     anchor_ix=np.r_[np.arange(lo,a),np.arange(b,hi)]
     if (angles[mapping[anchor_ix],anchor_ix]>cfg['maximum_axial_orientation_error_radians']).any():reason='anchor_orientation_disagreement'
     elif (residual>cfg['maximum_aligned_step_residual_pixels']).any():reason='movement_discontinuity'
     else:mapping[a:b]=chosen;reliable[a:b]=True;bridged[a:b]=True
  attempts.append({'start_frame':a+1,'end_frame':b,'frames':b-a,'accepted':reason is None,'reason':reason or 'position_pose_motion_and_two_sided_anchors'})
 return {'mapping':mapping,'reliable':reliable,'bridged':bridged,'mapping_changed':mapping!=np.asarray(baseline_mapping),'attempts':attempts,'position_errors_by_assignment':positions,'orientation_errors_by_assignment':angles}
