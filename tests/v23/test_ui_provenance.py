import sys,subprocess,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/v23')]
from video_pipeline import recording_identity
from video_service_v23 import preview_video,upload_identity
class UIProvenanceTests(unittest.TestCase):
 def test_upload_display_name_separate_from_storage(self):
  self.assertEqual(recording_identity('/cache/abcd1234.avi','Experiment A.avi'),('Experiment A.avi','Experiment A'))
 def test_same_content_renamed_upload_changes_result_identity(self):
  self.assertNotEqual(upload_identity('digest','A.avi'),upload_identity('digest','B.avi'))
 def test_decode_failure_has_user_error(self):
  with patch('video_service_v23.inspect_video',return_value={}),patch('video_service_v23.subprocess.check_output',side_effect=subprocess.CalledProcessError(1,['ffmpeg'])):
   with self.assertRaisesRegex(ValueError,'decode'):preview_video('broken.avi')
if __name__=='__main__':unittest.main()
