"""Decode selected source lunge sequences for manual correspondence/timing review."""
from pathlib import Path
import sys,json,subprocess,io
import numpy as np,pandas as pd
from scipy.io import loadmat
from PIL import Image,ImageDraw
from prepare_aligned import load_track,prepare,SOURCE,ROOT

def review(rec):
 d=ROOT/'data'/rec
 prepare(rec)
 audit=pd.read_parquet(d/'alignment-audit.parquet').set_index('frame');eligible=pd.read_parquet(d/'eligible.parquet')
 old,*_=load_track(SOURCE/rec/(rec+'_track.mat'));new,*_=load_track(d/'tracks.mat')
 src=loadmat(SOURCE/rec/(rec+'_actions.mat'),simplify_cells=True);idx=list(src['behs']).index('lunge');cases=[]
 for ref in [1,2]:
  a=np.asarray(src['bouts'][ref-1,idx]);a=a.reshape(-1,3) if a.size else []
  candidates=[]
  for start,end,flag in a:
   start,end=int(start),int(end)
   if flag!=0:continue
   group=eligible[eligible.reference_fly_id.eq(ref)&eligible.frame.between(start,end)]
   if len(group)/(end-start+1)>=.8 and group.fly_id.nunique()==1:candidates.append((end-start+1,start,end,int(group.fly_id.iloc[0])))
  if not candidates:continue
  _,start,end,fly=max(candidates)
  frames=np.linspace(max(1,start-3),min(54000,end+3),7).round().astype(int)
  cases.append({'recording':rec,'reference_fly':ref,'new_source_fly':fly,'start_frame':start,'end_frame':end,'frames':frames.tolist(),'review_scope':'source ID correspondence and annotated temporal neighborhood; not independent expert behavior confirmation'})
 if not cases:raise ValueError('No eligible positive review examples for '+rec)
 canvas=Image.new('RGB',(7*300,len(cases)*330+30),'white');draw=ImageDraw.Draw(canvas)
 for row,c in enumerate(cases):
  clip=ROOT/'reports'/f"{rec}-reference{c['reference_fly']}-source{c['new_source_fly']}-event{c['start_frame']}.mp4"
  begin=max(0,(c['start_frame']-11)/30);duration=(c['end_frame']-c['start_frame']+21)/30
  subprocess.run(['/opt/homebrew/bin/ffmpeg','-y','-ss',str(begin),'-i',str(SOURCE/rec/(rec+'.mp4')),'-t',str(duration),'-an','-c:v','libx264','-pix_fmt','yuv420p','-loglevel','error',str(clip)],check=True)
  c['review_clip']=str(clip.relative_to(ROOT))
  draw.text((5,row*330),f"{rec}: reference fly {c['reference_fly']} -> new fly {c['new_source_fly']}, source lunge {c['start_frame']} to {c['end_frame']}",fill='black')
  for col,frame in enumerate(c['frames']):
   cmd=['/opt/homebrew/bin/ffmpeg','-ss',str((frame-1)/30),'-i',str(SOURCE/rec/(rec+'.mp4')),'-frames:v','1','-f','image2pipe','-vcodec','png','-loglevel','error','-']
   raw=subprocess.run(cmd,capture_output=True,check=True).stdout;im=Image.open(io.BytesIO(raw)).convert('RGB').resize((288,288));dr=ImageDraw.Draw(im)
   for prefix,points,color in [('R',old,'blue'),('N',new,'red')]:
    for fly in [0,1]:
     x,y=points[fly,frame-1]*2
     if np.isfinite([x,y]).all():
      dr.ellipse((x-5,y-5,x+5,y+5),outline=color,width=2);dr.text((x+6,y+(-17 if prefix=='R' else 4)),prefix+str(fly+1),fill=color)
   canvas.paste(im,(col*300,row*330+30));draw.text((col*300+5,row*330+315),f'Frame {frame}',fill='black')
 canvas.save(ROOT/'reports'/f'{rec}-selected-lunge-review.png')
 (d/'selected-review-cases.json').write_text(json.dumps(cases,indent=2));return cases
if __name__=='__main__':
 recs=sys.argv[1:] or [f'movie{i}' for i in range(1,6)]
 for rec in recs:print(json.dumps(review(rec),indent=2))
