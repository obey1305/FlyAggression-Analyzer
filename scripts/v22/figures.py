"""Standalone exclusion timelines and coverage figures; no classifier predictions."""
from pathlib import Path
import json
import numpy as np,pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
ROOT=Path(__file__).resolve().parents[2];D=ROOT/'reports/v22-days1-2'
def main():
 causes=pd.read_csv(D/'causes-by-recording.csv');summary=pd.read_csv(D/'coverage-by-recording-fly.csv');intervals=pd.read_csv(D/'excluded-intervals.csv');order=json.loads((D/'reason-order.json').read_text())['primary_reason_order'];total=causes.groupby('reason').excluded_bouts_with_reason.sum().sort_values(ascending=False);shown=total[total.gt(0)].sort_values()
 labels={x:x.replace('_',' ') for x in shown.index};fig,ax=plt.subplots(figsize=(11,6),layout='constrained');bars=ax.barh([labels[x] for x in shown.index],shown.values,color='#3265a0');ax.bar_label(bars,padding=4);ax.set(xlabel='Excluded source bouts touching this reason (counts overlap)',xlim=(0,total.max()*1.12),title='Movies1–5 exclusion causes · overlapping counts');ax.spines[['top','right']].set_visible(False);fig.savefig(D/'exclusion-causes.png',dpi=170);plt.close(fig)
 g=summary.groupby('recording')[['source_bouts','v21_retained_bouts','candidate_retained_bouts']].sum();fig,ax=plt.subplots(figsize=(10,4.8),layout='constrained');x=np.arange(len(g));ax.bar(x,g.v21_retained_bouts,label='Retained Version2.1',color='#3265a0');ax.bar(x,g.source_bouts-g.v21_retained_bouts,bottom=g.v21_retained_bouts,label='Excluded',color='#c8cdd2')
 for i,row in enumerate(g.itertuples()):ax.text(i,row.source_bouts+8,f'{row.v21_retained_bouts}/{row.source_bouts}\n{row.v21_retained_bouts/row.source_bouts:.1%}',ha='center',va='bottom')
 ax.set(xticks=x,xticklabels=g.index,ylabel='Provided source lunge bouts',ylim=(0,g.source_bouts.max()*1.18),title='Whole-bout evaluation coverage · candidate adds no retained bouts');ax.legend(frameon=False);ax.spines[['top','right']].set_visible(False);fig.savefig(D/'coverage-by-recording.png',dpi=170);plt.close(fig)
 groups={'Missing measurement':'#222222','Annotation uncertainty':'#ad771e','Identity/track evidence':'#3265a0','Context/whole-bout rules':'#b8c5d4'}
 def group(bits):
  names={n for i,n in enumerate(order) if bits&(1<<i)}
  if names&{'missing_track_coordinates','nonfinite_feature_measurements'}:return 'Missing measurement'
  if names&{'annotation_unknown','annotation_flagged_overlap','source_lunge_flag'}:return 'Annotation uncertainty'
  if names&{'reference_tracking_warning','new_tracking_warning','position_disagreement','assignment_margin','close_contact_separation','assignment_changes_within_bout'}:return 'Identity/track evidence'
  return 'Context/whole-bout rules'
 fig,axes=plt.subplots(5,1,figsize=(12,8),sharex=True,layout='constrained')
 for ax,rec in zip(axes,g.index):
  d=intervals[intervals.recording.eq(rec)]
  for category,color in groups.items():
   sub=d[d.reason_bitmask.apply(lambda bits:group(int(bits))==category)]
   for fly in [1,2]:
    f=sub[sub.reference_fly_id.eq(fly)];ax.broken_barh(list(zip(f.start_seconds/60,f.duration_seconds/60)),(fly-.32,.64),facecolors=color)
  ax.set(yticks=[1,2],yticklabels=['Ref fly1','Ref fly2'],title=rec,ylim=(.5,2.5),xlim=(0,30));ax.spines[['top','right']].set_visible(False)
 axes[-1].set(xlabel='Minutes from recording start',xticks=np.arange(0,31,5));fig.suptitle('Excluded Version2.1 evaluation intervals\nDisplay priority: missing → annotation → identity → context; CSV retains all overlapping reasons',fontsize=12);fig.legend(handles=[Patch(color=c,label=n) for n,c in groups.items()],loc='outside lower center',ncol=4,frameon=False);fig.savefig(D/'excluded-interval-timelines.png',dpi=170);plt.close(fig)
 print('Three scientific figures exported')
if __name__=='__main__':main()
