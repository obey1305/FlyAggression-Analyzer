"""Final locked-study confusion matrices and operational onset/matching figures."""
import json
import numpy as np,pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from prepare_evaluation import ROOT
R=ROOT/'reports/v23-days9-10';STUDY=ROOT/'reports/v23-days5-8'
def main():
 result=json.loads((STUDY/'evaluation.json').read_text());fig,axes=plt.subplots(1,2,figsize=(9,4.5),layout='constrained')
 for ax,tag in zip(axes,['primary','secondary']):
  cm=np.array(result['metrics'][tag]['conditional_frame_metrics']['confusion_matrix_TN_FP_FN_TP']);ax.imshow(np.maximum(cm,1),norm=LogNorm(vmin=1,vmax=70000),cmap='Blues')
  for i in range(2):
   for j in range(2):ax.text(j,i,f'{cm[i,j]:,}',ha='center',va='center',color='white' if cm[i,j]>1000 else 'black',fontsize=12)
  ax.set(xticks=[0,1],yticks=[0,1],xticklabels=['No lunge','Lunge'],yticklabels=['No lunge','Lunge'],xlabel='Frozen threshold prediction',ylabel='Provided annotation label',title=tag.capitalize()+' · conditional frame counts')
 fig.suptitle('Unlabelled frames assumed negative; not confirmed expert negatives',fontsize=11);fig.savefig(R/'conditional-confusion-matrices.png',dpi=170);plt.close(fig)
 ops=pd.read_csv(STUDY/'operational-predicted-events.csv');fig,axes=plt.subplots(3,1,figsize=(11,7),sharex=True,layout='constrained')
 for ax,tag in zip(axes,['operational','primary','secondary']):
  if tag=='operational':d=ops;fly='fly_id';color='#276978';title='64operational event onsets · native FlyTracker IDs'
  else:d=pd.read_csv(STUDY/f'{tag}-all-source-bouts.csv');fly='reference_fly_id';color='#b65c32';title=tag.capitalize()+f' expert onsets · all{len(d)}source bouts, including excluded events'
  for i in [1,2]:ax.vlines(d.loc[d[fly].eq(i),'start_seconds'],i-.3,i+.3,color=color,lw=1)
  ax.set(yticks=[1,2],ylabel='Fly',title=title,ylim=(.4,2.6))
 axes[-1].set(xlabel='Recording time (seconds)',xlim=(0,1280));fig.savefig(R/'aggression-onset-timelines.png',dpi=170);plt.close(fig)
 fig,ax=plt.subplots(figsize=(8,4),layout='constrained');rows=[]
 for tag in ['primary','secondary']:
  m=result['metrics'][tag]['native_time_event_metrics'];rows.append([m['true_positive_events'],m['false_positive_events'],m['false_negative_events']])
 x=np.arange(2);bottom=np.zeros(2)
 for j,(label,color) in enumerate([('Matched','#276978'),('Unmatched prediction','#b65c32'),('Unmatched expert','#a5adb8')]):
  values=np.array(rows)[:,j];ax.bar(x,values,bottom=bottom,label=label,color=color);bottom+=values
 ax.set(xticks=x,xticklabels=['Primary:9/42retained','Secondary:32/48retained'],ylabel='Scored event outcomes',title='Native-time one-to-one IoU≥0.30 · excluded events separate');ax.legend();fig.savefig(R/'event-matching-counts.png',dpi=170);plt.close(fig)
if __name__=='__main__':main()
