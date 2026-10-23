"""FlyAggression Analyzer Version 2.2 local integration build."""
from pathlib import Path
import sys
BUILD=Path(__file__).resolve().parent
sys.path.insert(0,str(BUILD.parent/'drosophila-aggression'))
sys.path.insert(0,str(BUILD/'scripts'))
from pathlib import Path
import hashlib,json,io
import pandas as pd
import streamlit as st
import altair as alt
from scripts.gui_service import chart_data,archive_downloads,ROOT
from feature_service_v21 import analyze_upload
from video_service_v21 import analyze_video_upload,graphical_report
from scripts.auto_calibration import prepare_auto_calibration
st.set_page_config(page_title='FlyAggression Analyzer',page_icon='🪰',layout='wide')
st.markdown('''<style>.block-container{padding-top:3.5rem;max-width:1280px} [data-testid="stMetric"]{background:#f4f7fb;border:1px solid #e1e7f0;border-radius:12px;padding:18px} [data-testid="stMetric"] *{color:#172b4d!important} [data-testid="stMetricValue"]{font-size:1.6rem} .eyebrow{font-size:12px;font-weight:600;color:#75a2d4;letter-spacing:.12em} h1{letter-spacing:-.035em}</style>''',unsafe_allow_html=True)
st.markdown('<div class="eyebrow">RAW VIDEO RESEARCH PROTOTYPE · VERSION 2.2</div>',unsafe_allow_html=True)
st.title('FlyAggression Analyzer')
st.write('Analyse compatible MATLAB features or experimental two-fly raw videos.')
with st.sidebar:
 st.header('New analysis')
 mode=st.radio('Input mode',['MATLAB features','Experimental raw video'])
 upload=None;video=None;calibration=None;consent=False
 if mode=='Experimental raw video':
  st.warning('Experimental Version 2.2 raw-video model. No measured accuracy gain over 2.1; retrospective evaluation only; full-video biological accuracy is not established. Requires two flies, 30 fps and matching calibration.')
  video=st.file_uploader('Raw video (MP4)',type=['mp4'])
  calibration_mode=st.radio('Arena calibration',['Automatic arena detection','Upload calibration file'])
  boundary_ok=True
  if calibration_mode=='Automatic arena detection':
   diameter=st.number_input('Measured arena diameter (mm)',min_value=0.,value=0.,step=0.5,help='Enter the real measured diameter of the visible circular arena. The video cannot determine physical size. Zero means not supplied.')
   st.caption('One circular arena · two flies. Physical diameter must be measured; it is never guessed.')
   auto_key=(hashlib.sha256(video.getvalue()).hexdigest(),diameter,'auto-calibration-v2') if video else None
   if st.session_state.get('auto_calibration_key')!=auto_key:
    st.session_state.pop('auto_calibration',None);st.session_state['auto_calibration_key']=auto_key
   if st.button('Detect arena automatically',disabled=video is None or diameter<=0):
    try:
     with st.spinner('Detecting arena and generating calibration…'):
      st.session_state['auto_calibration']=prepare_auto_calibration(video.getvalue(),video.name,diameter)
    except (ValueError,OSError) as exc:st.error(str(exc))
   auto=st.session_state.get('auto_calibration')
   boundary_ok=False
   if auto:
    st.image(auto['preview'],caption='Detected arena boundary in red. Check that it follows the arena edge.')
    meta=auto['metadata'];st.caption(f"{meta['fps']:g} fps · radius {meta['radius_pixels']:.1f} px · {meta['pixels_per_mm']:.3f} px/mm")
    boundary_ok=st.checkbox('The highlighted arena boundary is correct',key='boundary-'+str(auto_key))
    calibration=io.BytesIO(auto['calibration'])
    st.download_button('Download generated calibration',auto['calibration'],file_name='automatic-calibration.mat',mime='application/octet-stream',on_click='ignore')
  else:
   calibration=st.file_uploader('FlyTracker arena calibration',type=['mat'],help='Arena geometry, pixels per mm, FPS and two-fly settings. This is not a behavioural feature file.')
  consent=st.checkbox('I understand these are experimental predictions')
  video_analyze=st.button('Analyse video',disabled=video is None or calibration is None or not boundary_ok or not consent,type='primary')
 else:
  video_analyze=False
  upload=st.file_uploader('MATLAB feature file',type=['mat'],help='A scalar feat structure with names and data: two flies × consecutive frames × 36 named features. Maximum 200 MB.')
 if mode=='MATLAB features':st.caption('Compatible paired-fly features · 30 fps. Feature upload supports MATLAB through v7.2.')
 analyze=st.button('Analyse uploaded file',type='primary',disabled=upload is None,width='stretch') if mode=='MATLAB features' else False
 st.divider()
 example=st.button('Load development example',width='stretch') if mode=='MATLAB features' else False
 if mode=='MATLAB features':st.caption('Movie5 is a known development recording, not an independent test.')
 st.divider();st.caption(('Raw-video model 2.2.0' if mode=='Experimental raw video' else 'Original feature model 1.0.0')+' · 36 features\n\nAdditional behaviours are not included in these results.')

# A changed upload clears old results to prevent downloading a previous recording as the new file.
identity=('2.2',mode,upload.name,hashlib.sha256(upload.getvalue()).hexdigest()) if upload is not None else (mode,video.name,hashlib.sha256(video.getvalue()).hexdigest(),hashlib.sha256(calibration.getvalue()).hexdigest() if calibration else None,consent) if video else (mode,None)
if st.session_state.get('upload_identity')!=identity:
 st.session_state['upload_identity']=identity;st.session_state.pop('result',None);st.session_state.pop('analysis_error',None)
if analyze or example or video_analyze:
 st.session_state.pop('result',None);st.session_state.pop('analysis_error',None)
 bar=st.progress(0,text='Starting analysis…')
 try:
  if video_analyze:
   result=analyze_video_upload(video.getvalue(),video.name,calibration.getvalue(),consent,lambda p,s:bar.progress(p,text=s))
   st.session_state['result']=result
  else:
   content=upload.getvalue() if analyze else (ROOT/'datasets/features/movie5_feat.mat').read_bytes()
   name=upload.name if analyze else 'movie5_feat.mat'
   result=analyze_upload(content,name,lambda p,s:bar.progress(p,text=s));st.session_state['result']=result
 except (ValueError,OSError,KeyError) as exc:st.session_state['analysis_error']=str(exc)
 finally:bar.empty()
if st.session_state.get('analysis_error'):st.error(st.session_state['analysis_error'])
result=st.session_state.get('result')
if result is None:
 st.info('Upload an MP4, enter the measured arena diameter and detect its arena, or upload a calibration file.' if mode=='Experimental raw video' else 'Upload a compatible MATLAB file to begin, or load the development example.')
 st.subheader('From features to measurements')
 a,b,c=st.columns(3)
 a.markdown('**1 · Upload**\n\nSupply a two-fly MP4 and calibrate its arena automatically or upload calibration.' if mode=='Experimental raw video' else '**1 · Upload**\n\nUse paired-fly behavioural features in the supported MATLAB format.')
 b.markdown('**2 · Detect**\n\nThe selected model identifies lunges and groups frame predictions into events.')
 c.markdown('**3 · Explore & export**\n\nReview per-fly timelines, compare measurements and download CSV tables.')
 st.stop()
if result.get('experimental') and result.get('report_version')!=2:
 result['downloads']['experimental-report.png']=graphical_report(result);result['report_version']=2
st.success('Analysis complete · '+result['filename'])
if result.get('experimental'):st.warning('Experimental Version 2.2 raw-video predictions. No measured accuracy improvement. Source identities may switch. Validation used selected reliable intervals from a development recording; full-video accuracy is not established.')
flies=result['byfly'];events=result['events'];record=result['byrecording'].iloc[0];charts=chart_data(result)
a,b=st.columns(2)
c,d=st.columns(2)
a.metric('Detected lunge events',str(int(record.summed_fly_event_count)))
b.metric('Total lunge time',f'{record.total_lunge_fly_seconds:.2f} s')
c.metric('Events / fly-min',f'{record.events_per_fly_minute:.2f}')
d.metric('Recording length',f'{record.recording_minutes:.1f} min')
st.caption('Events are counted per fly. Total time sums both fly tracks; simultaneous events can overlap. These are model predictions, not confirmed expert annotations.')
missing=result['manifest']['input_schema']['nonfinite_source_values']
if missing:st.warning(f'{missing:,} nonfinite source measurements were replaced using the saved training medians.')
summary_tab,timeline_tab,download_tab=st.tabs(['Overview','Timeline & events','Download results'])
with summary_tab:
 st.subheader('Per-fly measurements')
 display=flies[['fly_id','lunge_count','total_lunge_seconds','lunge_frequency_per_minute','mean_event_seconds']].rename(columns={'fly_id':'Fly','lunge_count':'Lunge events','total_lunge_seconds':'Lunge time (s)','lunge_frequency_per_minute':'Events / min','mean_event_seconds':'Mean event (s)'})
 st.dataframe(display,hide_index=True,width='stretch')
 left=st.container();right=st.container()
 with left:
  st.subheader('Events by fly')
  st.altair_chart(alt.Chart(flies).mark_bar(color='#3265a0',cornerRadiusTopLeft=4,cornerRadiusTopRight=4).encode(x=alt.X('fly_id:N',title='Fly'),y=alt.Y('lunge_count:Q',title='Detected events'),tooltip=['fly_id:N','lunge_count:Q']).properties(height=240),width='stretch')
 with right:
  st.subheader('Behaviour distribution')
  st.altair_chart(alt.Chart(charts['distribution']).mark_bar().encode(x=alt.X('seconds:Q',title='Summed track time (seconds)'),y=alt.Y('state:N',title=None),color=alt.Color('state:N',scale=alt.Scale(domain=['Predicted lunge','Remaining track time'],range=['#3265a0','#cbd5e1']),legend=None),tooltip=['state:N',alt.Tooltip('seconds:Q',format='.2f')]).properties(height=240),width='stretch')
  st.caption('Remaining time is not a confirmed non-aggression label. Other behaviours are not classified here.')
 st.subheader('Lunge duration distribution')
 st.altair_chart(alt.Chart(charts['duration_histogram']).mark_bar(color='#3265a0').encode(x=alt.X('start_seconds:Q',bin='binned',title='Event duration (seconds)'),x2='end_seconds:Q',y=alt.Y('count:Q',title='Events'),tooltip=[alt.Tooltip('start_seconds:Q',format='.3f'),alt.Tooltip('end_seconds:Q',format='.3f'),'count:Q']).properties(height=220),width='stretch')
with timeline_tab:
 st.subheader('Aggression timeline')
 selected=st.multiselect('Fly tracks',options=[int(v) for v in flies.fly_id],default=[int(v) for v in flies.fly_id])
 length=float(record.recording_seconds)
 window=st.slider('Time window (seconds)',min_value=0.,max_value=length,value=(0.,length),step=min(1.,length))
 shown=events[events.fly_id.isin(selected)&events.start_seconds.lt(window[1])&events.stop_seconds_exclusive.gt(window[0])].copy()
 if shown.empty:st.info('No predicted events in the selected tracks and time window.')
 else:
  st.altair_chart(alt.Chart(shown).mark_bar(size=24,color='#3265a0',stroke='#3265a0',strokeWidth=1,clip=True).encode(x=alt.X('start_seconds:Q',title='Seconds from recording start',scale=alt.Scale(domain=list(window))),x2='stop_seconds_exclusive:Q',y=alt.Y('fly_id:N',title='Fly'),tooltip=['fly_id:N','event_id:Q','start_frame:Q','end_frame:Q',alt.Tooltip('duration_seconds:Q',format='.3f')]).properties(height=180),width='stretch')
 st.dataframe(shown[['fly_id','event_id','start_frame','end_frame','start_seconds','duration_seconds']],hide_index=True,width='stretch')
 st.caption('Source frames are 1-based and inclusive. Duration = (end frame − start frame + 1) / 30.')
with download_tab:
 st.subheader('Download analysis')
 st.download_button('Download all results (.zip)',data=archive_downloads(result['downloads']),file_name=Path(result['filename']).stem+'-lunge-results.zip',mime='application/zip',type='primary',on_click='ignore')
 for name,data in result['downloads'].items():st.download_button('Download '+name,data=data,file_name=name,mime='image/png' if name.endswith('.png') else 'application/json' if name.endswith('.json') else 'text/plain' if name.endswith('.txt') else 'text/csv',key='download-'+name,on_click='ignore')
 st.caption('Downloads contain all frames and events; timeline filters do not alter the exported data.')
with st.expander('Analysis details'):
 st.write(f"Selected model: {result['manifest'].get('model_version','1.0.0')} · Random Forest · 36 features · 30 fps")
 rules=result['manifest']['event_rules']
 st.write(f"Threshold {result['manifest']['threshold']:g} · Median window {rules['median_window']} · Merge gap {rules['max_gap_frames']} frame(s) · Minimum event span {rules['min_event_frames']} frame(s)")
 st.code(result['manifest']['model_sha256'],language=None)
 evaluation_path=ROOT/'results/day18/final-test-metrics.json'
 if result.get('experimental'):st.caption('Raw-video performance must be evaluated separately. No feature-based accuracy claim applies to this run.')
 elif evaluation_path.exists():
  evaluation=json.loads(evaluation_path.read_text())['event_micro']
  st.caption(f"Independent evaluation on five held-out recordings: event precision {evaluation['precision']:.1%}, recall {evaluation['recall']:.1%}, F1 {evaluation['f1']:.3f}. Predictions still require appropriate research review.")
 else:st.caption('The model has development validation only. Independent final testing remains pending.')
