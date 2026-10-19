"""Selected false-positive/negative source frames for limited visual correspondence review."""
from pathlib import Path
import json,subprocess,io
import pandas as pd,numpy as np
from PIL import Image,ImageDraw
from prepare_aligned import ROOT,SOURCE,load_track
DEST=ROOT/'reports/days5-7'
def main():
 d=pd.read_csv(DEST/'validation-frame-outcomes.csv');cases=[]
 for outcome,ascending in [('FP',False),('FN',True)]:
  selected=[]
  for row in d[d.outcome.eq(outcome)].sort_values('probability_lunge',ascending=ascending).itertuples():
   if all(abs(row.frame-r.frame)>100 for r in selected):selected.append(row)
   if len(selected)==3:break
  cases.extend(selected)
 old,*_=load_track(SOURCE/'movie5/movie5_track.mat');new,*_=load_track(ROOT/'data/movie5/tracks.mat');canvas=Image.new('RGB',(810,300*len(cases)),'white');draw=ImageDraw.Draw(canvas);audit=[]
 for i,row in enumerate(cases):
  draw.text((5,i*300+2),f'{row.outcome}: frame {row.frame}, new fly {row.fly_id} -> reference {row.reference_fly_id}, probability {row.probability_lunge:.3f}',fill='black')
  audit.append({k:getattr(row,k) for k in ['outcome','frame','fly_id','reference_fly_id','probability_lunge','position_error_pixels','separation_pixels']})
  for j,f in enumerate([row.frame-2,row.frame,row.frame+2]):
   raw=subprocess.run(['/opt/homebrew/bin/ffmpeg','-ss',str((f-1)/30),'-i',str(SOURCE/'movie5/movie5.mp4'),'-frames:v','1','-f','image2pipe','-vcodec','png','-loglevel','error','-'],capture_output=True,check=True).stdout
   im=Image.open(io.BytesIO(raw)).convert('RGB').resize((260,260));dr=ImageDraw.Draw(im)
   for prefix,points,color in [('R',old,'blue'),('N',new,'red')]:
    for fly in [0,1]:
     x,y=points[fly,f-1]*(260/144)
     if np.isfinite([x,y]).all():dr.ellipse((x-4,y-4,x+4,y+4),outline=color,width=2);dr.text((x+4,y+(-14 if prefix=='R' else 3)),prefix+str(fly+1),fill=color)
   canvas.paste(im,(j*270,i*300+22));draw.text((j*270+5,i*300+284),f'Frame {f}',fill='black')
 canvas.save(DEST/'selected-error-review.png');(DEST/'selected-error-cases.json').write_text(json.dumps(audit,indent=2))
 print('Saved',len(cases),'cases /',len(cases)*3,'stills; review correspondence, not new expert labels.')
if __name__=='__main__':main()
