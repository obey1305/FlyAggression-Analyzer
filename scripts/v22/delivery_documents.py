"""Create final scientific report and concise PRJ501 slides from verified local evidence."""
from pathlib import Path
import csv,json,html
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from pptx import Presentation
from pptx.util import Inches,Pt
from pptx.dml.color import RGBColor
R=Path(__file__).resolve().parents[2];E=R/'reports/v22-days7-10'
def main():
 proof=json.loads((E/'full-movie1/verification.json').read_text());metrics=list(csv.DictReader((E/'performance-by-recording.csv').open()));coverage=list(csv.DictReader((E/'evaluation-coverage.csv').open()));rows=[x for x in metrics if x['model']=='v22'];q=proof['audit'];seconds=proof['total_seconds']
 per='\n'.join(f"| {x['recording']} | {'Training resubstitution' if x['recording']!='movie5' else 'Retrospective development'} | {float(x['frame_f1']):.2%} | {float(x['event_f1']):.2%} | {x['event_true_positive_events']} / {x['event_false_positive_events']} / {x['event_false_negative_events']} |" for x in rows)
 text=f'''# FlyAggression Analyzer Version 2.2 — Final Progress Report

23 October 2026 · PRJ 501 · Research prototype · Retrospective evaluation

## Outcome

A separately frozen Version 2.2 application and model are available with both analysis modes, reproducible exclusion/calibration audits, labelled dataset rebuild, a fresh classifier fit, fixed retrospective evaluation and a new complete MP4 demonstration. **No accuracy, usable-annotation coverage or biological identity improvement was demonstrated over Version 2.1.** No genuinely untouched expert-annotated recording was available in the supplied collection. The original feature classifier, Version 2.1 release and default Desktop launcher remain unchanged.

## Days 7–10 status

- Day 7: The candidate and evaluation protocol were locked before this phase's scoring. Independent-data success criterion is unmet; the approved retrospective fallback was used. Supplied benchmark movies 1–10 were already consumed; reference/example clips lacked the required independent expert correspondence. No expert labels or physical measurements were fabricated.
- Day 8: Frozen models were scored under identical features, masks, thresholds and event matching. All paired probabilities are equal. Movies 1–4 are training resubstitution and movie5 was previously used for development selection. These results establish reproducibility, not independent generalization.
- Day 9: The Version 2.2 raw model is separately routed in the local app; original MATLAB features use the original classifier. Automatic calibration, fresh tracking/features, inference and CSV/PNG/ZIP exports passed a full movie1 functional run. Regression, input and UI checks accompany the release.
- Day 10: Model/configuration freeze, performance tables, confusion matrices, timelines, installation/user/demo guidance, a separate research package and PRJ501 presentation materials are saved. The label “Version 2.2” identifies this audited research build, not a proven accuracy upgrade.

## Locked scientific method

The existing raw-video-specific classifier was freshly refitted in Days3–6 on movies 1–4 using the same36 features and estimator settings:128 trees, unlimited depth, minimum leaf1, sqrt feature selection, seed501. Median imputation was fitted only on training rows. Whole-recording per-fly median normalization in the existing extractor remains documented; no validation-fitted cohort scaler was added.

This phase performed no fitting or parameter selection. Threshold0.15, median3, merge gap1, minimum span3 frames and event IoU0.30 were locked with model/config hashes. The saved Day1–4 reference-assisted masks are used only for retrospective annotation correspondence; they are not an autonomous identity-correction feature in production. Full-video inference does not read expert annotation files. Post-inference reference comparison is an audit.

## Paired retrospective measurements

Versions 2.1 and2.2 have identical values in every row below. Training results must not be pooled with movie5 and presented as generalization accuracy.

| Recording | Evaluation role | Frame F1 | Event F1 | Event TP / FP / FN |
|---|---|---:|---:|---:|
{per}

Movie5 frame precision55.67%, recall70.78%, F162.32%; event precision78.95%, recall72.58%, F175.63%. Event counts:114 predicted,124 retained expert,90 matched,24 false positives and34 misses. Frame confusion matrix, true rows/predicted columns [non-lunge,lunge]: [[99655,297],[154,373]]. Scores use the same selected reliable subset; they are not full-recording biological performance. The original feature-model79.53% eventF1 belongs to its separate earlier evaluation and is not evidence for this raw-video release.

![Movie5 confusion matrix](reports/v22-days7-10/movie5-confusion.png)

## Coverage, calibration and identity

Across movies 1–5,761 of1528 source expert bouts are retained and767 excluded. Movie5 retains124/303 (40.92%). No additional safe identity corrections or bout recoveries were supported. Exclusions have explicit overlapping causes and exclusive primary categories in the Days1–2 audit. Native tracking warnings, context buffers and short stable intervals account for substantial losses. Source IDs may switch; biological identity continuity is not certified.

![Coverage](reports/v22-days7-10/final-coverage.png)

Nominal 16 mm arena diameter was inherited from cohort provenance, not independently measured per recording. Saved scale arithmetic is consistent: movie1/5 use8.125px/mm, movies2–4 use8.25px/mm. Body and contrast parameters and36-feature profiles are recorded. Fixed-track ±10% scale sensitivity identifies distance/leg-distance/velocity dependence; it is not corrected calibration or evidence of better tracking. No diameter or contrast threshold was tuned to improve F1.

## Fresh raw-video functional demonstration

The full30-minute movie1 training-source MP4 was freshly processed through automatic geometry calibration, Caltech FlyTracker, feature conversion and the frozen Version 2.2 model. The benchmark nominal 16 mm assumption is explicitly retained. It produced two tracks ×54,000 frames ×36 features.

Measured total runtime: **{seconds:.1f} seconds ({seconds/60:.2f} minutes)**, including automatic calibration **{proof['automatic_calibration_seconds']:.1f}s** and tracking/adapter/prediction **{proof['tracking_adapter_prediction_seconds']:.1f}s**. This is one measurement on this Mac, not a promise for uploads of other length/codec/quality.

Exports contained **{q['total_events']} predicted events** and **{q['total_fly_seconds']:.2f} summed fly-seconds**. Inclusive durations, contiguous frame keys, count totals and per-fly/fly-minute frequency denominators were independently checked. PNG decoding and ZIP member-byte parity passed. Source identity reliability was audited after inference; it remains uncertain and no full-video accuracy is claimed. The functional demo uses a training recording and must not be called an independent test.

![Full movie1 predicted report](reports/v22-days7-10/full-movie1/exports/experimental-report.png)

## Software and release

Original MAT mode preserves the frozen original model; known raw-adapter feature MATs are rejected in that mode. Raw MP4 mode uses only the Version 2.2 hash/schema/adapter-checked model, with separate provenance and experimental warnings. Automatic geometry still requires a physically known diameter and user boundary confirmation. Supported/tested conditions are one circular arena, two flies,30FPS and readable MP4;200MB UI limit;30-minute analysis timeout. No additional behaviours are supported.

The separate Desktop Version 2.2 launcher uses port8504. Existing Version 2.1 launcher/port remains untouched. The extracted research package launcher uses port8505 and requires local Python dependencies and licensed compatible MATLAB; neither environment nor MATLAB is bundled. Included FlyTracker binaries are platform dependent. See INSTALLATION-V22.md and DEMONSTRATION-V22.md.

Tests and checks are saved under reports/v22-days7-10: original and Version 2.1 regression logs, Version 2.2 routing/UI tests, invalid-input results, quantification audit, evaluation lock/hash check and package verification. Source preservation checks cover438 Version 2.1 files, the Version 2.1 release archive, default Desktop launcher and original model/runtime integrity. Code review found no material routing or evaluation-scope issue.

## Remaining scientific requirements

Independent raw recordings with expert per-fly annotations, physical arena measurements and reviewed identities are still needed. More permissive exclusion masks would increase apparent coverage without establishing label reliability and were not used. Further work should address source tracking/annotation ambiguity before claiming an improved detector. Version 2.2 is a functional, reproducible research delivery with transparent limits; the planned independent-data, improved-coverage and higher-accuracy targets remain unmet.

## Inspectable sources

- config/v22-evaluation-lock.json: pre-scoring protocol and frozen hashes.
- reports/v22-days7-10/performance-by-recording.csv, evaluation-coverage.csv and frame-confusion-matrices.json: paired numbers and scope.
- reports/v22-days7-10/evaluation/: per-record scores, events and source matches.
- reports/v22-days7-10/full-movie1/verification.json and exports/: fresh functional run and downloads.
- DAYS1-2-REPORT.md and DAYS3-6-REPORT.md: exclusion, calibration, annotation and model-development evidence.
- models/raw-v2.2/ and models/raw-v2.2-candidate/: frozen release and source candidate.
'''
 text=text.replace('Source identity reliability was audited after inference;', 'On these fresh features, frozen Versions 2.1 and 2.2 again give identical predictions and 69 events. The prior fresh Version 2.1 run produced 68 events: 198 finite feature values differ from the cached extraction, showing upstream tracking repeatability limitations, not a classifier gain. Source identity reliability was audited after inference;')
 (R/'FINAL-REPORT-V22.md').write_text(text)
 # Printable report: controlled pages with readable prose and evidence tables.
 styles=getSampleStyleSheet();styles['BodyText'].fontSize=10;styles['BodyText'].leading=14;story=[]
 def p(t,style='BodyText'):
  for a,b in [('Version 2.','Version 2.'),('Movies 1','Movies 1'),('movies 1','movies 1'),('movies 6','movies 6'),('of 303','of 303'),('124 of 303','124 of 303'),('two flies,30FPS','two flies, 30 FPS'),('30FPS','30 FPS'),('30minutes','30 minutes'),('54000frames','54,000 frames'),('36features','36 features'),('124 retained','124 retained'),('Movie5:114','Movie5: 114'),('threshold0.15','threshold 0.15'),('median3/gap1/min3','median 3/gap 1/min 3'),('IoU0.30','IoU 0.30'),('runtime/analyze','runtime/analyze'),('16 mm','16 mm'),('two flies,','two flies,'),('port8504','port 8504'),('port8505','port 8505'),('Python3.12','Python 3.12'),('frozen2.2','frozen 2.2'),('checked2.2','checked 2.2')]:t=t.replace(a,b)
  story.append(Paragraph(html.escape(t),styles[style]));story.append(Spacer(1,8))
 def table(data,widths=None):
  t=Table(data,colWidths=widths,repeatRows=1);t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#173c61')),('TEXTCOLOR',(0,0),(-1,0),colors.white),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTSIZE',(0,0),(-1,-1),9),('BOTTOMPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),8),('GRID',(0,0),(-1,-1),.3,colors.HexColor('#d3dbe5'))]));story.append(t);story.append(Spacer(1,12))
 p('FlyAggression Analyzer 2.2','Title');p('PRJ 501 | Final progress report | 23 October 2026','Heading2');p('Research prototype with retrospective evaluation','Heading2');p('No measured accuracy, identity or annotation-coverage improvement over Version 2.1. No independent annotated test recording was available. The original classifier and Version 2.1 release remain preserved.')
 p('What was delivered','Heading2');p('A separately frozen raw-video classifier and application route; tracking/exclusion and calibration audits; reproducible labelled-data rebuild and training; locked retrospective evaluation; fresh full-MP4 functional demonstration; exports and user guidance.')
 p('What remains unresolved','Heading2');p('Physical arena diameters are nominal, not newly measured. Biological fly identity continuity is uncertain. Movie5 evaluation retains only124 of 303 expert bouts. Independent generalization and the higher accuracy targets remain unestablished.')
 table([['Metric on movie5 development','V2.1','V2.2'],['Frame precision','55.67%','55.67%'],['Frame recall','70.78%','70.78%'],['Frame F1','62.32%','62.32%'],['Event precision','78.95%','78.95%'],['Event recall','72.58%','72.58%'],['Event F1','75.63%','75.63%']], [300,85,85]);p('Both versions produce exactly equal probabilities on the five retrospective feature grids. No model fitting or parameter tuning occurred in the final evaluation phase.');story.append(PageBreak())
 p('Evaluation and coverage','Title');p('Movies 1–4 are training resubstitution; movie5 is retrospective development selection. Previously consumed movies 6–10 were not relabelled as independent test data. Common eligible-frame and whole-bout event masks, threshold0.15, median3/gap1/min3 and IoU0.30 were fixed before scoring.')
 table([['Movie','Role','Frame F1','Event F1']]+[[x['recording'],'Training' if x['recording']!='movie5' else 'Development',f"{float(x['frame_f1']):.2%}",f"{float(x['event_f1']):.2%}"] for x in rows],[85,150,110,110]);story.append(Image(str(E/'movie5-confusion.png'),width=300,height=250));p('Movie5:114 predicted events,124 retained expert events,90 matched,24 false positives and34 misses. Source expert bouts total303; restricted coverage40.92%. The original feature-model79.53% eventF1 is a separate scientific result, not raw-video evidence.');story.append(PageBreak())
 p('Fresh MP4 demonstration','Title');p(f'Full movie1:30minutes at30FPS; two tracks,54000frames each,36features. Fresh automatic geometry calibration, FlyTracker extraction and frozen2.2 inference completed in {seconds:.1f}s ({seconds/60:.2f}min). Calibration took {proof["automatic_calibration_seconds"]:.1f}s. This is a functional run on a training recording, not independent accuracy.')
 p(f'{q["total_events"]} predicted events; {q["total_fly_seconds"]:.2f} summed fly-seconds. Inclusive durations, frame ordering, event counts and frequency denominators passed audit. PNG and ZIP member bytes passed checks. Runtime varies with hardware and video characteristics.')
 story.append(Image(str(E/'full-movie1/exports/experimental-report.png'),width=470,height=235));p('Both frozen models produce identical 69-event results on this fresh extraction. The prior fresh 2.1 run produced 68 events, with 198 finite feature values changing upstream. Repeat tracking is not bitwise identical; this is not an accuracy gain.');p('Nominal 16 mm benchmark diameter was used with explicit uncertainty. Own recordings require actual physical scale. Source IDs may switch. Calibration sensitivity and body/contrast checks did not establish a defensible correction or additional recoverable events.');p('Software workflows','Heading2');p('Original compatible MATLAB features use the frozen original classifier. MP4 uploads use the separately checked2.2 model. Experimental/identity warnings and provenance are visible. CSV, PNG and ZIP downloads remain available. Supported tested conditions:two flies, one circular arena,30FPS, readable MP4.');story.append(PageBreak())
 p('Use, evidence and next steps','Title');p('Use the separate Desktop Version 2.2 launcher (port8504). The extracted package uses port8505. Follow INSTALLATION-V22.md for Python3.12 dependencies and licensed MATLAB requirements. Existing Version 2.1 release and default launcher remain unchanged.');p('Reproducible demonstration','Heading2');p('Show the original feature-mode development example, then a matching MP4/calibration and the saved completed movie1 exports. Explain that automatic geometry cannot determine real millimetres. Open the confusion/coverage tables, show uncertainty and avoid describing training/development measurements as independent validation.');p('Inspectable evidence','Heading2');p('config/v22-evaluation-lock.json; reports/v22-days7-10/performance-by-recording.csv; evaluation-coverage.csv; frame-confusion-matrices.json; full-movie1/verification.json; invalid-input-results.json; regression logs; frozen manifests and package verification. Detailed earlier evidence: DAYS1-2-REPORT.md and DAYS3-6-REPORT.md.');p('Next scientific work','Heading2');p('Obtain independently collected expert-labelled recordings, confirm physical arena measurements, review ambiguous identities and labels, then evaluate the frozen model under a predeclared protocol. No accuracy/coverage increase is claimed by this release.')
 SimpleDocTemplate(str(R/'FINAL-REPORT-V22.pdf'),pagesize=(595,842),rightMargin=48,leftMargin=48,topMargin=42,bottomMargin=42).build(story)
 # Editable presentation: short text, native table, one real evidence image.
 slides=[('FlyAggression Analyzer 2.2',['PRJ 501 · Research prototype','Retrospective evaluation · 23 October 2026']),('Two preserved workflows',['Original MATLAB features → original frozen classifier','Raw MP4 → calibration → FlyTracker → 36 features → Version 2.2 RF','Both workflows produce event counts, durations, timelines and downloads.']),('Scientific scope',['No new independent annotated recording was available.','Movies 1–4: training resubstitution. Movie5: reused development selection.','No measured accuracy, identity or coverage improvement over 2.1.']),('Paired movie5 results',[]),('Coverage and calibration',['124 of 303 movie5 expert bouts retained (40.92%).','No additional safe identity corrections or bouts recovered.','Nominal 16 mm scale; per-record physical measurements unavailable.']),('Fresh complete MP4 demonstration',[f'30-minute movie1 → two tracks ×54,000 frames ×36 features',f'{seconds:.1f}s measured runtime; {q["total_events"]} predicted events; {q["total_fly_seconds"]:.2f} fly-seconds','Training-source functional test; not independent biological accuracy.']),('Software reliability',['Original feature route preserved; raw model/configuration checked together.','CSV, PNG and ZIP exports audited. Experimental and identity warnings retained.','Separate 2.2 launcher; Version 2.1 release remains unchanged.']),('Remaining scientific work',['Collect independent recordings and expert per-fly annotations.','Measure physical scale and review identity correspondence.','Evaluate the locked model once; report coverage alongside accuracy.'])]
 prs=Presentation();prs.slide_width=Inches(13.333);prs.slide_height=Inches(7.5)
 for i,(title,body) in enumerate(slides):
  slide=prs.slides.add_slide(prs.slide_layouts[6]);box=slide.shapes.add_textbox(Inches(.7),Inches(.5),Inches(12),Inches(1));tf=box.text_frame;tf.text=title
  for para in tf.paragraphs:
   para.font.name='Arial';para.font.size=Pt(40 if i==0 else 32);para.font.bold=True;para.font.color.rgb=RGBColor.from_string('173C61')
  if i==3:
   data=[['Metric','Version 2.1','Version 2.2'],['Frame precision','55.67%','55.67%'],['Frame recall','70.78%','70.78%'],['Frame F1','62.32%','62.32%'],['Event precision','78.95%','78.95%'],['Event recall','72.58%','72.58%'],['Event F1','75.63%','75.63%']];t=slide.shapes.add_table(7,3,Inches(.8),Inches(1.8),Inches(11.7),Inches(4.4)).table
   for rr,row in enumerate(data):
    for cc,value in enumerate(row):
     cell=t.cell(rr,cc);cell.text=value
     for pp in cell.text_frame.paragraphs:pp.font.size=Pt(22);pp.font.name='Arial'
   note='Movie5 is retrospective development selection; not independent final-test accuracy. Identical paired predictions, common coverage.'
   foot=slide.shapes.add_textbox(Inches(.8),Inches(6.5),Inches(11.7),Inches(.55));foot.text_frame.text='Retrospective development · 124/303 expert bouts retained · no independent test'
   for pp in foot.text_frame.paragraphs:pp.font.name='Arial';pp.font.size=Pt(18)
  else:
   box=slide.shapes.add_textbox(Inches(.8),Inches(2),Inches(11.7),Inches(4.4));tf=box.text_frame;tf.word_wrap=True
   for j,line in enumerate(body):
    pp=tf.paragraphs[0] if j==0 else tf.add_paragraph();pp.text=line;pp.font.name='Arial';pp.font.size=Pt(26);pp.space_after=Pt(26)
   note='Source: FINAL-REPORT-V22.md and reports/v22-days7-10 local evidence. Do not imply independent validation or measured improvement.'
  slide.notes_slide.notes_text_frame.text=note
 prs.save(R/'PRJ501-PRESENTATION.pptx')
 (R/'PRJ501-PRESENTATION.md').write_text('\n\n'.join(f'# Slide{i+1}: {title}\n\n'+'\n'.join(body if body else ['Editable paired metrics table: frameF1 62.32%, eventF1 75.63%, identical bothversions.'])+'\n\nSpeaker note: '+('Explain retrospective scope and no improvement; cite final report and saved evidence.') for i,(title,body) in enumerate(slides))+'\n')
 print('Final Markdown/PDF report and eight-slide presentation exported')
if __name__=='__main__':main()
