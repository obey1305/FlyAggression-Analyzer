"""Standalone scientific figures from frozen development results, no new inference."""
from pathlib import Path
import json
import numpy as np,pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'reports/day10';COLOR='#3265a0'
def main():
 cms=json.loads((D/'frame-confusion-matrices.json').read_text());fig,axes=plt.subplots(1,2,figsize=(9,4.2),layout='constrained');maxcount=max(max(x for row in cm for x in row) for cm in cms.values())
 for ax,(tag,cm) in zip(axes,cms.items()):
  arr=np.array(cm);ax.imshow(arr,cmap='Blues',vmin=0,vmax=maxcount)
  for i,j in np.ndindex((2,2)):ax.text(j,i,f'{arr[i,j]:,}',ha='center',va='center',fontsize=15,color='white' if arr[i,j]>maxcount*.5 else '#172b4d')
  ax.set(xticks=[0,1],xticklabels=['Non-lunge','Lunge'],yticks=[0,1],yticklabels=['Non-lunge','Lunge'],xlabel='Predicted class',ylabel='Provided mapped label',title=tag)
 fig.suptitle('Movie5 frame confusion matrices — development validation',fontsize=13)
 fig.savefig(D/'frame-confusion-matrices.png',dpi=180);plt.close(fig)
 models=['Expert','Version-2.0','Version-2.1'];frames=pd.read_parquet(ROOT/'reports/days5-7/movie5/evaluation-coverage.parquet');truth=pd.read_csv(D/'expert-events.csv');fig,axes=plt.subplots(3,2,figsize=(12,6),sharex=True,layout='constrained')
 for i,model in enumerate(models):
  events=truth if model=='Expert' else pd.read_csv(D/model/'evaluation-events.csv')
  for j,fly in enumerate([1,2]):
   ax=axes[i,j];e=events[events.fly_id.eq(fly)];ax.vlines((e.start_frame-1)/30,0,1,color=COLOR if model=='Version-2.1' else '#666666',linewidth=.9)
   # Invalid portions are shown as a separate grey stripe, not labelled as negatives.
   f=frames[frames.fly_id.eq(fly)];bad=~f.valid_for_events.to_numpy();changes=np.diff(np.r_[False,bad,False].astype(int));starts=np.flatnonzero(changes==1);ends=np.flatnonzero(changes==-1)
   for a,b in zip(starts,ends):ax.broken_barh([(a/30,(b-a)/30)],(-.35,.15),facecolors='#c8c8c8')
   ax.set(ylim=(-.4,1.2),yticks=[],xlim=(0,1800),title=f'{model.replace("-"," ")} · source fly {fly} · {len(e)} events')
   ax.spines[['top','right','left']].set_visible(False)
 for ax in axes[-1]:ax.set(xlabel='Seconds from recording start',xticks=np.arange(0,1801,300))
 fig.suptitle('Movie5 event onsets on common scorable coverage\nGrey stripe marks excluded intervals; development validation',fontsize=13);fig.savefig(D/'movie5-event-timelines.png',dpi=180);plt.close(fig)
 metrics=pd.read_csv(D/'final-performance.csv');fig,ax=plt.subplots(figsize=(8,4.2),layout='constrained');x=np.arange(3);w=.35
 for i,row in enumerate(metrics.itertuples()):
  values=[row.frame_f1,row.event_precision,row.event_f1];bars=ax.bar(x+(i-.5)*w,values,width=w,label=row.model,color='#b8c5d4' if i==0 else COLOR)
  ax.bar_label(bars,labels=[f'{v:.1%}' for v in values],padding=3,fontsize=10)
 ax.set(xticks=x,xticklabels=['Frame F1','Event precision','Event F1'],ylim=(0,1),ylabel='Score',title='Movie5 development comparison · filtered reliable intervals');ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1));ax.legend(frameon=False);ax.spines[['top','right']].set_visible(False);fig.savefig(D/'model-comparison.png',dpi=180);plt.close(fig)
 print('Three scientific PNG figures exported')
if __name__=='__main__':main()
