"""Deterministic frame/time correspondence and configurable rectangular tracking masks."""
import numpy as np,pandas as pd

def validate_rates(source_fps,target_fps):
 if not isinstance(source_fps,int) or not isinstance(target_fps,int) or target_fps<=0 or source_fps<target_fps:raise ValueError('Positive integer rates required; target cannot exceed source')
def frame_map(n,source_fps=200,target_fps=30):
 validate_rates(source_fps,target_fps)
 if not isinstance(n,int) or n<1:raise ValueError('Positive integer source frame count required')
 count=(n*target_fps+source_fps-1)//source_fps;k=np.arange(count,dtype=np.int64);source=np.minimum((2*k*source_fps+target_fps)//(2*target_fps),n-1);analysis_t=k/target_fps;source_t=source/source_fps
 return pd.DataFrame({'analysis_frame':k+1,'source_frame':source+1,'analysis_seconds':analysis_t,'source_seconds':source_t,'sample_error_seconds':source_t-analysis_t})
def project_interval(start,end,mapping):
 if not (isinstance(start,(int,np.integer)) and isinstance(end,(int,np.integer))) or start<1 or end<start:raise ValueError('Positive inclusive source frame interval required')
 inside=mapping.source_frame.between(start,end);selected=mapping.loc[inside,'analysis_frame'];return {'analysis_start_frame':int(selected.min()) if len(selected) else None,'analysis_end_frame':int(selected.max()) if len(selected) else None,'sample_count':len(selected),'lost_by_sampling':len(selected)==0}
def rectangle_mask(width,height,bounds,padding=0):
 if len(bounds)!=4 or not all(isinstance(v,int) for v in [width,height,padding,*bounds]) or min(width,height)<=0 or padding<0:raise ValueError('Integer image geometry and nonnegative padding required')
 x1,y1,x2,y2=bounds
 if not (1<=x1<x2<=width and 1<=y1<y2<=height):raise ValueError('Rectangle must be inside image with positive area')
 mask=np.zeros((height,width),bool);mask[max(0,y1-1-padding):min(height,y2+padding),max(0,x1-1-padding):min(width,x2+padding)]=True;return mask

def selection_filter(n,sf=200,tf=30):
 validate_rates(sf,tf)
 count=(n*tf+sf-1)//sf
 return f"select='lt(floor(n*{tf}/{sf}+0.5),{count})*eq(n,min({n-1},floor(floor(n*{tf}/{sf}+0.5)*{sf}/{tf}+0.5)))',setpts=N/({tf}*TB)"
