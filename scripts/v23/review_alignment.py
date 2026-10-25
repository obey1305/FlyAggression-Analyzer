"""Inspect pre-inference uncertain correspondence examples; never changes eligibility."""
from pathlib import Path
import subprocess,io,json
import numpy as np,pandas as pd
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from tracking_io import load_track
ROOT=Path(__file__).resolve().parents[2];R=ROOT/'reports/v23-days5-8'
def main():
 b=pd.read_csv(R/'primary-all-source-bouts.csv');selected=b[~b.retained].groupby('exclusion_reasons',sort=True).head(1).head(4);m=pd.read_csv(ROOT/'reports/v23-days1-4/frame-time-map.csv')
 ref,_,_,_=load_track(ROOT.parent/'new-training-data/BoyMeetsBoy/extracted/Boy_meets_boy light/movie5/movie5_track.mat');new,_,_,_=load_track(ROOT/'data/v23-tracking/movie5-analysis30/movie5-analysis30-track.mat')
 fig,axes=plt.subplots(2,2,figsize=(12,10),layout='constrained');rows=[]
 for ax,row in zip(axes.ravel(),selected.itertuples()):
  k=(int(row.cover_start)+int(row.cover_stop)-1)//2;native=int(m.source_frame.iloc[k])-1
  content=subprocess.check_output(['/opt/homebrew/bin/ffmpeg','-v','error','-ss',str(k/30),'-i',str(ROOT/'data/v23-input/movie5-analysis30.mp4'),'-frames:v','1','-f','image2pipe','-vcodec','png','-']);ax.imshow(Image.open(io.BytesIO(content)))
  for fly in (0,1):
   for label,xy,marker,color in [('reference',ref[:,native],'o','#00bbcc'),('new',new[:,k],'+','#ff3333')]:
    if np.isfinite(xy[fly]).all():ax.scatter(*xy[fly],marker=marker,c=color,s=60);ax.annotate(f'{label} {fly+1}',xy[fly],xytext=(7,-12 if label=='reference' else 12),textcoords='offset points',color=color,fontsize=8,bbox=dict(facecolor='white',alpha=.6,edgecolor='none',pad=1))
  ax.set_title(f'Expert{row.event_id}, t={k/30:.3f}s\n{row.exclusion_reasons.replace(";",chr(10))}',fontsize=9);ax.set_axis_off();rows.append({'source_event_id':int(row.event_id),'analysis_frame':k+1,'source_frame':native+1,'exclusion_reasons':row.exclusion_reasons,'review_scope':'position correspondence only; no expert biological identity adjudication'})
 for ax in axes.ravel()[len(rows):]:ax.set_axis_off()
 fig.savefig(R/'uncertain-alignment-examples.png',dpi=140);plt.close(fig);(R/'uncertain-alignment-examples.json').write_text(json.dumps(rows,indent=2)+'\n')
if __name__=='__main__':main()
