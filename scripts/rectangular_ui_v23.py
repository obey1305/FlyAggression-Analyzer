"""Rectangular import controls with explicit metadata and boundary review."""
from pathlib import Path
import hashlib,json
import streamlit as st
from video_service_v23 import BUILD,inspect_video,preview_video,upload_identity

def controls():
 st.warning('Frozen Version2.2 model with Version2.3 video import. Only restricted external subsets were evaluated; full-video accuracy and biological fly identity are not established.')
 source=st.radio('Video location',['Upload (up to200MB)','Local file (large recordings)'])
 path=None;identity=None;display_name=None
 if source.startswith('Upload'):
  video=st.file_uploader('Rectangular video (AVI or MP4)',type=['avi','mp4'],key='rect-upload')
  if video:
   content=video.getvalue();display_name=video.name
   if len(content)>200*1024*1024:st.error('Use the local-file option for videos above200MB.')
   else:
    digest=hashlib.sha256(content).hexdigest();path=BUILD/'.runtime/v23-inputs'/(digest+Path(video.name).suffix.lower());identity=upload_identity(digest,video.name)
 else:
  value=st.text_input('Local video path',key='rect-path',help='A readable local AVI/MP4; original video is preserved. Use this for the7.3GBstarter.')
  if value:
   path=Path(value).expanduser();display_name=path.name
   try:
    stat=path.stat();identity=('local',str(path.resolve()),stat.st_size,stat.st_mtime_ns)
   except OSError:st.error('That local file is not readable.');path=None
 key=hashlib.sha256(repr(identity).encode()).hexdigest()
 if st.button('Inspect rectangular video',disabled=path is None):
  try:
   if source.startswith('Upload'):
    path.parent.mkdir(parents=True,exist_ok=True)
    if not path.exists():path.write_bytes(content)
   meta=inspect_video(path);preview=preview_video(path);st.session_state['rect-inspected']={'key':key,'meta':meta,'preview':preview}
  except (ValueError,OSError) as e:st.error(str(e))
 inspected=st.session_state.get('rect-inspected');inspected=inspected if inspected and inspected['key']==key else None
 if inspected:
  m=inspected['meta'];st.image(inspected['preview'],caption='Source frame: use pixel coordinates to define the tracking region.');st.caption(f"Source {m['fps']} FPS · {m['width']}×{m['height']} · {m['frames']:,}frames → analysis30FPS. Short events may lose temporal detail.")
 st.caption('Manual inclusive pixel bounds. Defaults match the Boy Meets Boy starter; review them for every recording. Padding expands the tracking region, not physical arena size.')
 x1=int(st.number_input('Left x (pixels)',min_value=1,value=20,step=1));y1=int(st.number_input('Top y (pixels)',min_value=1,value=10,step=1));x2=int(st.number_input('Right x (pixels)',min_value=2,value=620,step=1));y2=int(st.number_input('Bottom y (pixels)',min_value=2,value=479,step=1));pad=int(st.number_input('Tracking padding (pixels)',min_value=0,value=12,step=1));ppm=st.number_input('Pixels per millimetre',min_value=0.,value=0.,step=.1,help='Supply measured scale or an explicitly identified published nominal value. The video cannot determine physical size.')
 evidence=st.selectbox('Scale evidence',['user-measured','published-nominal','unverified-user-value']);st.caption('Boy Meets Boy publication reports nominal12pixels/mm. It is not a per-recording measurement certificate.')
 boundary=st.checkbox('I checked the rectangular boundary and scale');consent=st.checkbox('I understand these are experimental predictions',key='rect-consent');params={'bounds':[x1,y1,x2,y2],'padding':pad,'ppm':ppm,'scale_source':evidence}
 clicked=st.button('Analyse rectangular video',type='primary',disabled=not inspected or not boundary or not consent or ppm<=0)
 demo=st.button('Load completed starter demonstration',disabled=not (BUILD/'examples/bmb-starter-results').exists())
 st.caption('The completed demonstration uses saved results, not a fresh analysis of the selected file.')
 return {'path':path,'display_name':display_name,'params':params,'experimental':consent,'analyze':clicked,'demo':demo,'identity':(identity,display_name,json.dumps(params,sort_keys=True),boundary,consent)}
