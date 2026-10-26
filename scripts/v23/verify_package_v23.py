"""Verify archive bytes and relocation using real original and completed app examples."""
from pathlib import Path
import json,subprocess,sys,zipfile,shutil
from video_pipeline import sha
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT.parent;R=ROOT/'reports/v23-days9-10'
def main():
 package=OUT/'FlyAggression-Analyzer-v2.3-Release';archive=OUT/'FlyAggression-Analyzer-v2.3-Release.zip';sums=json.loads((package/'SHA256SUMS.json').read_text());subprocess.run([sys.executable,str(package/'verify_package.py')],check=True)
 with zipfile.ZipFile(archive) as z:
  assert z.testzip() is None
  for name,h in sums.items():
   import hashlib
   assert hashlib.sha256(z.read(package.name+'/'+name)).hexdigest()==h
 # Relocated folder is a separate copy, without source-worktree imports.
 relocated=ROOT/'data/v23-relocated-package'
 if relocated.exists():raise ValueError('Preserve previous relocation evidence')
 shutil.copytree(package,relocated);script=ROOT/'data/v23-relocated-app-check.py';script.write_text('''from pathlib import Path
import sys
from streamlit.testing.v1 import AppTest
root=Path(sys.argv[1]);app=AppTest.from_file(str(root/'flyaggression-v2.3/app.py')).run(timeout=30)
assert not app.exception
next(b for b in app.button if b.label=='Load development example').click().run(timeout=30)
assert not app.exception and app.metric[0].value=='325'
app.radio[0].set_value('Experimental raw video').run(timeout=30)
next(r for r in app.radio if r.label=='Arena geometry').set_value('Rectangular (30/200FPS)').run(timeout=30)
next(b for b in app.button if b.label=='Load completed starter demonstration').click().run(timeout=30)
assert not app.exception and app.metric[0].value=='64'
import raw_release
assert raw_release.ROOT.resolve()==(root/'flyaggression-v2.3').resolve()
import scripts.gui_service
assert scripts.gui_service.ROOT.resolve()==(root/'drosophila-aggression').resolve()
print('RELOCATED_APP_PASS original325 rawdemo64; all imports from relocated package')
''')
 with (R/'relocated-app-tests.log').open('w') as log:subprocess.run([sys.executable,str(script),str(relocated)],stdout=log,stderr=subprocess.STDOUT,check=True)
 receipt={'status':'PASS','package_files_verified':len(sums),'zip_crc_and_all_manifest_bytes_verified':True,'relocated_original_feature_example_events':325,'relocated_rectangular_demo_events':64,'imports_verified_from_relocated_package':True,'model_sha256':sha(relocated/'flyaggression-v2.3/models/raw-v2.2/lunge-detector.joblib'),'large_source_videos_bundled':False,'matlab_python_environment_bundled':False};(R/'package-verification.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
if __name__=='__main__':main()
