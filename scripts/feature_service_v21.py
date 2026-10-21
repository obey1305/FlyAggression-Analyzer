"""Keep known adapter-produced features out of the original feature workflow."""
from pathlib import Path
import io
from scipy.io import loadmat
from scripts.gui_service import analyze_upload as original_analyze_upload,MAX_BYTES

def analyze_upload(content,filename,progress=None):
 if content and len(content)<=MAX_BYTES and Path(filename).suffix.lower()=='.mat':
  try:feat=loadmat(io.BytesIO(content),variable_names=['feat'],simplify_cells=True).get('feat')
  except (ValueError,OSError,NotImplementedError,TypeError,IndexError):feat=None
  if isinstance(feat,dict) and 'integration_status' in feat:
   raise ValueError('This MAT file contains raw-video-derived features. Use Experimental raw video with its source MP4 and the Version 2.1 model; original-feature mode requires compatible original features.')
 return original_analyze_upload(content,filename,progress)
