"""Build a separate relocatable research package from the preserved prior release."""
from pathlib import Path
import shutil,json,hashlib,zipfile
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT.parent;DEST=OUT/'FlyAggression-Analyzer-v2.2-Release'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def copy(src,dst):dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
def main():
 if DEST.exists():raise ValueError('Release exists; preserve before rebuilding')
 shutil.copytree(OUT/'FlyAggression-Analyzer-v2.1-Release',DEST);old=DEST/'flyaggression-v2.1';build=DEST/'flyaggression-v2.2';old.rename(build)
 for n in ['app.py','FINAL-REPORT-V22.md','FINAL-REPORT-V22.pdf','INSTALLATION-V22.md','DEMONSTRATION-V22.md','PRJ501-PRESENTATION.md','PRJ501-PRESENTATION.pptx','DAYS1-2-REPORT.md','DAYS3-6-REPORT.md']:copy(ROOT/n,build/n)
 for n in ['raw_release.py','video_service_v21.py','video_to_lunges_v21.py','feature_service_v21.py','audit_quantification.py']:copy(ROOT/'scripts'/n,build/'scripts'/n)
 shutil.copytree(ROOT/'models/raw-v2.2',build/'models/raw-v2.2');shutil.copytree(ROOT/'models/raw-v2.2-candidate',build/'models/raw-v2.2-candidate')
 for n in ['v22-evaluation-lock.json','v22-days1-2.json','v22-days3-6.json']:copy(ROOT/'config'/n,build/'config'/n)
 for n in ['INSTALLATION-V22.md','DEMONSTRATION-V22.md','FINAL-REPORT-V22.pdf','PRJ501-PRESENTATION.pptx']:copy(ROOT/n,DEST/n)
 # Remove ambiguous prior root final report/guides; prior baseline model is retained inside this separate package.
 for n in ['FINAL-REPORT.pdf','INSTALLATION.md','DEMONSTRATION.md']:
  p=DEST/n
  if p.exists():p.unlink()
 evidence=DEST/'evidence-v22';evidence.mkdir()
 for p in (ROOT/'reports/v22-days7-10').iterdir():
  if p.is_file():copy(p,evidence/p.name)
 for folder in ['v22-days1-2','v22-days3-6']:
  for p in (ROOT/'reports'/folder).glob('*.png'):copy(p,build/'reports'/folder/p.name)
  for n in ['verification.json','results.json','coverage-by-recording-fly.csv','bout-exclusion-audit.csv','calibration-audit.csv','scale-sensitivity.csv']:
   p=ROOT/'reports'/folder/n
   if p.exists():copy(p,evidence/f'{folder}-{n}')
 for p in (ROOT/'reports/v22-days7-10').glob('*.png'):copy(p,build/'reports/v22-days7-10'/p.name)
 demo=ROOT/'reports/v22-days7-10/full-movie1'
 shutil.rmtree(DEST/'examples/completed-movie1-report');shutil.copytree(demo/'exports',DEST/'examples/completed-movie1-report')
 for n in ['verification.json','tracking-identity-diagnostics.csv','calibration-metadata.json']:copy(demo/n,evidence/'full-movie1'/n)
 copy(demo/'calibration.mat',DEST/'examples/movie1-calibration.mat');copy(demo/'exports/experimental-report.png',build/'reports/v22-days7-10/full-movie1/exports/experimental-report.png')
 # Prior package contained an old feature fixture; replace it with the fresh matching run.
 copy(demo/'run/experimental_feat.mat',DEST/'examples/movie1-raw-features.mat')
 (DEST/'README.md').write_text('# FlyAggression Analyzer2.2 research release\n\nStart with INSTALLATION-V22.md and FINAL-REPORT-V22.pdf. No measured accuracy improvement over2.1; no independent validation. Historical Version2.1 model/evidence retained for baseline provenance. Detailed research datasets remain in the development workspace.\n')
 (DEST/'Launch_Analyzer.command').write_text('''#!/bin/zsh
set -e
HERE="${0:A:h}"
PYTHON="${FLYAGGRESSION_PYTHON:-$HERE/drosophila-aggression/.venv/bin/python}"
if [[ ! -x "$PYTHON" ]]; then
 print 'Create the Python environment using INSTALLATION-V22.md.'
 exit 1
fi
cd -- "$HERE"
"$PYTHON" verify_package.py
exec "$PYTHON" -m streamlit run "$HERE/flyaggression-v2.2/app.py" --server.address 127.0.0.1 --server.port 8505 --browser.gatherUsageStats false
''');(DEST/'Launch_Analyzer.command').chmod(0o755)
 sums={str(p.relative_to(DEST)):sha(p) for p in sorted(DEST.rglob('*')) if p.is_file() and p.name!='SHA256SUMS.json'};(DEST/'SHA256SUMS.json').write_text(json.dumps(sums,indent=2)+'\n')
 archive=OUT/'FlyAggression-Analyzer-v2.2-Release.zip'
 with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for p in sorted(DEST.rglob('*')):
   if p.is_file():z.write(p,str(Path(DEST.name)/p.relative_to(DEST)))
 (ROOT/'reports/v22-days7-10/release-build.json').write_text(json.dumps({'package':str(DEST),'archive':str(archive),'archive_sha256':sha(archive),'archive_bytes':archive.stat().st_size,'files':len(sums),'python_environment_bundled':False,'matlab_bundled':False},indent=2)+'\n');print('Built',archive)
if __name__=='__main__':main()
