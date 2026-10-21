"""Inspect pose and movement around changes in reference correspondence; no automatic relabeling."""
from pathlib import Path
import sys,json,subprocess,io
import numpy as np,pandas as pd
from PIL import Image,ImageDraw
from identity_alignment import runs,axial_error
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT.parent/'flyaggression-v2.1';DEST=ROOT/'reports/v22-days1-2'
sys.path.insert(0,str(BASE/'scripts'));from prepare_aligned import load_track,SOURCE

def anchor(mapping,good,lo,hi,last):
 candidates=[]
 for a,b in runs(good[max(0,lo):min(len(good),hi)]):
  a+=max(0,lo);b+=max(0,lo)
  if b-a>=15 and np.unique(mapping[a:b]).size==1:candidates.append((a,b,int(mapping[a])))
 return (candidates[-1] if last else candidates[0]) if candidates else None

def main():
 rows=[];cases=[]
 for rec in ['movie1','movie2','movie3','movie4','movie5']:
  dest=DEST/rec;audit=pd.read_parquet(dest/'identity-correspondence.parquet');mapping=audit.v21_new_fly1_reference.to_numpy()-1;good=audit.v21_identity_reliable.to_numpy();changes=np.flatnonzero(np.diff(mapping)!=0)+1;groups=[]
  for f in changes:
   if groups and f-groups[-1][-1]<=30:groups[-1].append(f)
   else:groups.append([f])
  old,ow,od,on=load_track(SOURCE/rec/(rec+'_track.mat'));new,nw,nd,nn=load_track(BASE/f'data/{rec}/tracks.mat');oo=od[:,:,on.index('ori')];no=nd[:,:,nn.index('ori')];local=[]
  for j,group in enumerate(groups):
   start,end=int(group[0]),int(group[-1]);left=anchor(mapping,good,start-120,start,True);right=anchor(mapping,good,end+1,end+121,False);classification='unresolved_anchor_evidence'
   if left and right:classification='supported_reference_correspondence_change' if left[2]!=right[2] else 'ambiguous_pairing_flicker'
   lo=max(0,start-30);hi=min(len(mapping),end+31);frames=np.arange(lo,hi);aligned=np.stack([new[np.where(mapping[frames]==0,ref,1-ref),frames] for ref in [0,1]])
   step=np.linalg.norm(np.diff(new[:,frames],axis=1),axis=2);refstep=np.linalg.norm(np.diff(old[:,frames],axis=1),axis=2);residual=np.linalg.norm(np.diff(aligned,axis=1)-np.diff(old[:,frames],axis=1),axis=2)
   pose=np.stack([axial_error(oo[ref,frames],no[np.where(mapping[frames]==0,ref,1-ref),frames]) for ref in [0,1]])
   row={'recording':rec,'cluster_id':j+1,'first_change_frame':start+1,'last_change_frame':end+1,'pointwise_changes':len(group),'classification':classification,'left_anchor_reference':left[2]+1 if left else 0,'right_anchor_reference':right[2]+1 if right else 0,'window_start_frame':lo+1,'window_end_frame':hi,'source_warning_frames':int(nw[frames].sum()),'reference_warning_frames':int(ow[frames].sum()),'raw_step_max_pixels':float(np.nanmax(step)),'reference_step_max_pixels':float(np.nanmax(refstep)),'mapped_step_residual_max_pixels':float(np.nanmax(residual)),'mapped_axial_orientation_error_median_degrees':float(np.degrees(np.nanmedian(pose))),'minimum_body_separation_pixels':float(np.nanmin(audit.separation_pixels.iloc[frames]))}
   local.append(row);rows.append(row)
  if not local:continue
  selected=sorted(local,key=lambda r:(r['classification']!='supported_reference_correspondence_change',-r['pointwise_changes'],r['first_change_frame']))[0];f=selected['first_change_frame'];frames=np.clip(np.array([f-20,f-5,f,f+5,f+20]),1,54000);canvas=Image.new('RGB',(1300,310),'white');draw=ImageDraw.Draw(canvas);draw.text((5,2),f"{rec} · change at {f} · {selected['classification']} · blue=reference R, red=source N; lines=axial orientation",fill='black')
  for k,frame in enumerate(frames):
   raw=subprocess.run(['/opt/homebrew/bin/ffmpeg','-ss',str((frame-1)/30),'-i',str(SOURCE/rec/(rec+'.mp4')),'-frames:v','1','-f','image2pipe','-vcodec','png','-loglevel','error','-'],capture_output=True,check=True).stdout
   im=Image.open(io.BytesIO(raw)).convert('RGB').resize((250,250));dr=ImageDraw.Draw(im);scale=250/144
   for prefix,xy,ori,color in [('R',old,oo,'blue'),('N',new,no,'red')]:
    for fly in [0,1]:
     x,y=xy[fly,frame-1]*scale;angle=ori[fly,frame-1]
     if not np.isfinite([x,y,angle]).all():continue
     dx,dy=np.cos(angle)*10,-np.sin(angle)*10;dr.line((x-dx,y-dy,x+dx,y+dy),fill=color,width=2);dr.ellipse((x-3,y-3,x+3,y+3),outline=color,width=2);dr.text((x+5,y+(-15 if prefix=='R' else 5)),prefix+str(fly+1),fill=color)
   canvas.paste(im,(k*260,28));draw.text((k*260+5,284),f'Frame {frame} · map N1→R{mapping[frame-1]+1}',fill='black')
  canvas.save(dest/'selected-switch-review.png');begin=max(0,(f-61)/30);subprocess.run(['/opt/homebrew/bin/ffmpeg','-y','-ss',str(begin),'-i',str(SOURCE/rec/(rec+'.mp4')),'-t','4','-an','-c:v','mpeg4','-q:v','2','-loglevel','error',str(dest/'selected-switch-review.mp4')],check=True)
  selected['review_frames']=frames.tolist();cases.append(selected)
  # Export raw and reference trajectories with explicit units for every reviewed cluster neighborhood.
  details=[]
  for row in local:
   for frame in range(row['window_start_frame'],row['window_end_frame']+1):
    t=frame-1
    for ref in [0,1]:
     source=ref if mapping[t]==0 else 1-ref
     details.append({'recording':rec,'cluster_id':row['cluster_id'],'frame':frame,'reference_fly_id':ref+1,'source_fly_id_proposed':source+1,'identity_reliable':bool(good[t]),'reference_x_pixels':old[ref,t,0],'reference_y_pixels':old[ref,t,1],'source_x_pixels':new[source,t,0],'source_y_pixels':new[source,t,1],'reference_orientation_radians':oo[ref,t],'source_orientation_radians':no[source,t],'axial_orientation_error_radians':axial_error(oo[ref,t],no[source,t])})
  pd.DataFrame(details).to_csv(dest/'switch-window-trajectories.csv',index=False)
 pd.DataFrame(rows).to_csv(DEST/'suspected-switch-clusters.csv',index=False);(DEST/'manual-review-cases.json').write_text(json.dumps(cases,indent=2));print(pd.DataFrame(rows).groupby(['recording','classification']).size().to_string())
if __name__=='__main__':main()
