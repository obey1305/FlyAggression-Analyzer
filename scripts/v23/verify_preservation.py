"""Verify frozen releases, original extractor sources and recorded upstream dependencies."""
from pathlib import Path
import json,hashlib,subprocess
ROOT=Path(__file__).resolve().parents[2]
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def main():
 m=json.loads((ROOT/'config/v23-preservation.json').read_text());v22=Path(m['v22_root']);bad=[]
 for name,digest in m['files'].items():
  if sha(v22/name)!=digest:bad.append('v22:'+name)
 for name,digest in m['external'].items():
  if sha(name)!=digest:bad.append(name)
 for name,digest in json.loads((ROOT/'config/v23-dependencies.json').read_text())['files'].items():
  if sha(name)!=digest:bad.append(name)
 original=json.loads((ROOT/'config/preservation.json').read_text())
 for name,digest in original['extractor_sources'].items():
  if sha(name)!=digest:bad.append(name)
 frozen=ROOT.parent/'drosophila-aggression/models/final-v1'
 for name,digest in original['frozen_files'].items():
  if sha(frozen/name)!=digest:bad.append(str(frozen/name))
 # V2.3 inherits original tracked files unchanged: all modifications are new paths.
 diff=subprocess.check_output(['git','diff',m['base_commit'],'--name-only'],cwd=ROOT,text=True).splitlines()
 if any(x in m['files'] for x in diff):bad+=['modified inherited:'+x for x in diff if x in m['files']]
 assert not bad,bad
 report={'status':'PASS','v22_tracked_regular_files_verified':len(m['files']),'external_release_and_launchers_verified':len(m['external']),'original_frozen_files_verified':len(original['frozen_files']),'original_extractor_sources_verified':len(original['extractor_sources']),'pinned_dependency_files_verified':len(json.loads((ROOT/'config/v23-dependencies.json').read_text())['files']),'inherited_v23_files_changed':0,'v22_worktree_status':subprocess.check_output(['git','status','--porcelain'],cwd=v22,text=True).strip(),'model_inference_in_v23_audit':False}
 assert not report['v22_worktree_status'];(ROOT/'reports/v23-days1-4/preservation-verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
