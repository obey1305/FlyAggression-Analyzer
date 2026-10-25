"""Source-pixel visual context for fixed unmatched predictions; no re-labelling."""
import io,subprocess
import pandas as pd,numpy as np
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from prepare_evaluation import ROOT,R,save_json
from tracking_io import load_track

def main():
 source=ROOT.parent/'new-training-data/BoyMeetsBoy/downloads/movie5.avi';xy,_,_,_=load_track(ROOT.parent/'new-training-data/BoyMeetsBoy/extracted/Boy_meets_boy light/movie5/movie5_track.mat');fp=pd.read_csv(R/'unmatched-prediction-diagnostics.csv');cases=[fp[fp.annotator.eq('primary')].iloc[0],fp[fp.overlapping_other_behaviors.fillna('').ne('')].iloc[0]];fig,axes=plt.subplots(2,3,figsize=(12,7),layout='constrained');records=[]
 for i,row in enumerate(cases):
  for j,t in enumerate(np.linspace(row.start_seconds,row.stop_seconds_exclusive,3)):
   native=int(round(t*200));time=native/200;content=subprocess.check_output(['/opt/homebrew/bin/ffmpeg','-v','error','-ss',str(time),'-i',str(source),'-frames:v','1','-f','image2pipe','-vcodec','png','-']);img=Image.open(io.BytesIO(content));ax=axes[i,j];ax.imshow(img)
   positions=xy[:,native];valid=positions[np.isfinite(positions).all(axis=1)]
   if len(valid):
    lo=np.maximum(valid.min(axis=0)-70,[0,0]);hi=np.minimum(valid.max(axis=0)+70,[639,479]);ax.set_xlim(lo[0],hi[0]);ax.set_ylim(hi[1],lo[1])
   label='no overlapping provided behaviour' if pd.isna(row.overlapping_other_behaviors) else row.overlapping_other_behaviors
   ax.set_title(f'{row.annotator}, event{int(row.operational_event_id)}\n{label}; native t={time:.3f}s',fontsize=9);ax.set_axis_off();records.append({'annotator':row.annotator,'operational_event_id':int(row.operational_event_id),'source_frame_1based':native+1,'source_time_seconds':time,'visual_review_scope':'spatial/interaction context only; no new expert label or biological FP adjudication'})
 fig.savefig(R/'unmatched-source-frame-context.png',dpi=150);plt.close(fig);save_json(R/'unmatched-source-frame-context.json',records)
if __name__=='__main__':main()
