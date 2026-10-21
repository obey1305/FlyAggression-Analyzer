"""Assemble relocatable local macOS research release; no environment or licensed MATLAB bundled."""
from pathlib import Path
import shutil,json,hashlib,zipfile
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT.parent;P=OUT/'drosophila-aggression';R=OUT/'raw-video-integration';DEST=OUT/'FlyAggression-Analyzer-v2.1-Release'
def copy(src,dst):dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
def package_docs(dest):
 p=dest/'flyaggression-v2.1/FINAL-REPORT.md';text=p.read_text().split('## Inspectable evidence')[0]
 text+='## Inspectable evidence in this package\n\n- ../evidence/final-performance.csv and frame-confusion-matrices.json: paired movie5 metrics.\n- ../evidence/full-movie1/verification.json and tracking-identity-diagnostics.csv: full-run audit.\n- ../evidence/invalid-input-results.json and day9-final-verification.json: final input/regression/preservation checks.\n- ../examples/completed-movie1-report/: complete verified full movie1 exports.\n- models/raw-v2.1/: raw-specific model and settings.\n- ../drosophila-aggression/models/final-v1/: original frozen model and runtime.\n- INSTALLATION.md and DEMONSTRATION.md: package use and presentation.\n\nDetailed per-model full-grid inference and matching files remain in the development workspace; they are not all duplicated in this compact release.\n'
 p.write_text(text)
 p=dest/'flyaggression-v2.1/INTEGRATION-GUIDE.md';p.write_text('Extracted-package note: this guide describes workspace integration. For this package, follow the root INSTALLATION.md and Launch_Analyzer.command (port8503); workspace launcher paths below are historical context.\n\n'+p.read_text())

def seal():
 sums={str(p.relative_to(DEST)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(DEST.rglob('*')) if p.is_file() and p.name!='SHA256SUMS.json'};(DEST/'SHA256SUMS.json').write_text(json.dumps(sums,indent=2))
 archive=OUT/'FlyAggression-Analyzer-v2.1-Release.zip'
 with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for p in sorted(DEST.rglob('*')):
   if p.is_file():z.write(p,str(Path(DEST.name)/p.relative_to(DEST)))
 (ROOT/'reports/day10/release-build.json').write_text(json.dumps({'release_folder':str(DEST),'archive':str(archive),'files':len(sums),'archive_bytes':archive.stat().st_size,'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'matlab_or_python_environment_bundled':False,'tracker_git_metadata_bundled':False},indent=2));print('Release built',archive,archive.stat().st_size)

def main():
 if DEST.exists():raise ValueError('Release folder exists; preserve it before intentionally rebuilding')
 DEST.mkdir()
 for n in ['app.py','FINAL-REPORT.md','FINAL-REPORT.pdf','INSTALLATION.md','DEMONSTRATION.md','INTEGRATION-GUIDE.md']:
  copy(ROOT/n,DEST/'flyaggression-v2.1'/n)
 for n in ['raw_release.py','video_service_v21.py','video_to_lunges_v21.py','feature_service_v21.py','audit_quantification.py']:
  copy(ROOT/'scripts'/n,DEST/'flyaggression-v2.1/scripts'/n)
 for n in ['feature-columns.json','days5-7-protocol.json','toolchain.json','feature-definitions.md']:
  copy(ROOT/'config'/n,DEST/'flyaggression-v2.1/config'/n)
 shutil.copytree(ROOT/'models/raw-v2.1',DEST/'flyaggression-v2.1/models/raw-v2.1')
 for n in ['gui_service.py','auto_calibration.py']:copy(P/'scripts'/n,DEST/'drosophila-aggression/scripts'/n)
 shutil.copytree(P/'models/final-v1',DEST/'drosophila-aggression/models/final-v1',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
 copy(P/'requirements-lock.txt',DEST/'requirements-lock.txt');copy(P/'datasets/features/movie5_feat.mat',DEST/'drosophila-aggression/datasets/features/movie5_feat.mat');copy(P/'results/day18/final-test-metrics.json',DEST/'drosophila-aggression/results/day18/final-test-metrics.json')
 shutil.copytree(R/'FlyTracker',DEST/'raw-video-integration/FlyTracker',ignore=shutil.ignore_patterns('.git','__pycache__','.DS_Store'))
 copy(R/'day5/adapter.py',DEST/'raw-video-integration/day5/adapter.py')
 for file in (R/'auto-calibration').glob('*.m'):copy(file,DEST/'raw-video-integration/auto-calibration'/file.name)
 copy(ROOT/'reports/day9/movie1/run/experimental_feat.mat',DEST/'examples/movie1-raw-features.mat')
 source=Path('/Users/adityasinghchauhan/Documents/Codex/2026-10-16/files-mentioned-by-the-user-codex/outputs/day3-videos/external-benchmark/Aggression/movie1/movie1.mp4');copy(source,DEST/'examples/movie1.mp4');copy(ROOT/'reports/day9/movie1/calibration.mat',DEST/'examples/movie1-calibration.mat');copy(ROOT/'data/day8-smoke/movie1-first300.mp4',DEST/'examples/movie1-first300.mp4')
 for file in (ROOT/'reports/day10').glob('*'):
  if file.is_file():
   copy(file,DEST/'evidence'/file.name)
   if file.suffix=='.png':copy(file,DEST/'flyaggression-v2.1/reports/day10'/file.name)
 for n in ['verification.json','tracking-identity-diagnostics.csv']:copy(ROOT/'reports/day9/movie1'/n,DEST/'evidence/full-movie1'/n)
 shutil.copytree(ROOT/'reports/day9/movie1/exports',DEST/'examples/completed-movie1-report')
 for n in ['day9/invalid-input-results.json','day9-regression-v21.log','day9-regression-original.log','day9-final-verification.json']:
  copy(ROOT/'reports'/n,DEST/'evidence'/Path(n).name)
 copy(ROOT/'INSTALLATION.md',DEST/'INSTALLATION.md');copy(ROOT/'DEMONSTRATION.md',DEST/'DEMONSTRATION.md');copy(ROOT/'FINAL-REPORT.pdf',DEST/'FINAL-REPORT.pdf')
 (DEST/'verify_package.py').write_text('''from pathlib import Path
import hashlib,json
root=Path(__file__).resolve().parent
manifest=json.loads((root/'SHA256SUMS.json').read_text())
for name,expected in manifest.items():
 path=root/name
 if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=expected:raise SystemExit('Package integrity failed: '+name)
print('PASS:',len(manifest),'packaged files verified')
''')
 launcher='''#!/bin/zsh
set -e
HERE="${0:A:h}"
PYTHON="${FLYAGGRESSION_PYTHON:-$HERE/drosophila-aggression/.venv/bin/python}"
if [[ ! -x "$PYTHON" ]]; then
 print 'Python environment missing. Follow INSTALLATION.md to create drosophila-aggression/.venv.'
 exit 1
fi
cd -- "$HERE"
"$PYTHON" verify_package.py
exec "$PYTHON" -m streamlit run "$HERE/flyaggression-v2.1/app.py" --server.address 127.0.0.1 --server.port 8503 --browser.gatherUsageStats false
'''
 (DEST/'Launch_Analyzer.command').write_text(launcher);(DEST/'Launch_Analyzer.command').chmod(0o755)
 package_docs(DEST)
 seal()
if __name__=='__main__':main()
