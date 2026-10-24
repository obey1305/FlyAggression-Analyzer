from pathlib import Path
import sys,subprocess,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts/v23'))
from import_tools import frame_map,selection_filter
FF='/opt/homebrew/bin/ffmpeg'
def hashes(arguments):
 s=subprocess.check_output([FF,'-v','error','-f','lavfi','-i','nullsrc=size=16x16:rate=200:duration=0.2,geq=lum=N:cb=128:cr=128',*arguments,'-c:v','rawvideo','-f','framemd5','-'],text=True)
 return [x.split(',')[-1].strip() for x in s.splitlines() if x and not x.startswith('#')]
class EncodedSelectionTests(unittest.TestCase):
 def test_selection_matches_map_including_partial_tail(self):
  native=hashes([])
  for n in (7,8,13,31,40):
   with self.subTest(n=n):
    selected=hashes(['-vf',f'trim=end_frame={n},'+selection_filter(n),'-r','30','-fps_mode','cfr'])
    self.assertEqual(selected,[native[i-1] for i in frame_map(n).source_frame])
if __name__=='__main__':unittest.main()
