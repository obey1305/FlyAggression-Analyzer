from pathlib import Path
import json,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np,pandas as pd
R=Path(__file__).resolve().parents[2]/'reports/v22-days7-10'
def main():
 m=json.loads((R/'frame-confusion-matrices.json').read_text());fig,ax=plt.subplots(figsize=(6,5));a=np.array(m['movie5-v22']);norm=a/a.sum(axis=1,keepdims=True);im=ax.imshow(norm,cmap='Blues',vmin=0,vmax=1)
 for i in range(2):
  for j in range(2):ax.text(j,i,f'{a[i,j]:,}\n{norm[i,j]:.1%}',ha='center',va='center',color='white' if norm[i,j]>.5 else 'black',fontsize=16)
 ax.set_xticks([0,1],['Non-lunge','Lunge']);ax.set_yticks([0,1],['Non-lunge','Lunge']);ax.set(xlabel='Predicted',ylabel='Expert aligned label',title='Movie5 · retrospective development\nV2.1 = V2.2 · eligible frames only');fig.colorbar(im,ax=ax,label='Fraction within true class');fig.tight_layout();fig.savefig(R/'movie5-confusion.png',dpi=160);plt.close(fig)
 c=pd.read_csv(R/'evaluation-coverage.csv');fig,ax=plt.subplots(figsize=(8,4));ax.bar(c.recording,c.retained_expert_bouts,label='Retained',color='#3466a0');ax.bar(c.recording,c.excluded_expert_bouts,bottom=c.retained_expert_bouts,label='Excluded',color='#b7c1cf');ax.legend();ax.set(ylabel='Source expert bouts',title='Coverage alongside accuracy · unchanged from V2.1')
 for i,row in c.iterrows():ax.text(i,row.source_expert_bouts+8,f'{row.retained_expert_bouts}/{row.source_expert_bouts}',ha='center')
 ax.set_ylim(0,c.source_expert_bouts.max()*1.18);fig.tight_layout();fig.savefig(R/'final-coverage.png',dpi=160);plt.close(fig)
if __name__=='__main__':main()
