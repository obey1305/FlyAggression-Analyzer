# PRJ501 — Version2.3 demonstration

1. Launch the separate2.3application. State that the app uses the unchanged frozen2.2raw-video Random Forest and original1.0feature classifier.
2. Show **MATLAB features → Load development example**:325predicted events. Explain that this is a known development example.
3. Switch to **Experimental raw video**, show that circular30FPS support remains available, then select **Rectangular (30/200FPS)**.
4. For a fast walkthrough, choose **Load completed starter demonstration**. Identify it explicitly as saved completed output. Show source200FPS→analysis30FPS, nominal scale provenance, warning counts, event timeline, per-fly counts/durations/frequency and downloads.
5. Show the separate locked external study: native-time eventF1.750primary on9/42bouts, .718secondary on32/48. Explain why these are selected-coverage results. Three primary misses had model responses excluded by boundary rules; the full-video detector count is not the scored prediction count.
6. Show conditional frame confusion matrices, event matching and the projected-grid sensitivity. A different annotation-time representation changes scores; the protocol was locked before prediction.
7. For a live long run, use the local Boy Meets Boy AVI path, inspect it, supply bounds[20,10,620,479],padding12,12px/mm and **published-nominal** scale. Confirm boundary/experimental status and analyse. This performs fresh conversion/calibration/tracking/feature extraction/inference and may take several minutes. The large source video is not bundled with the release.
8. Conclude with the documented limits: no model retraining/threshold tuning, nominal physical scale, uncertain biological identities, short-event sampling, incomplete expert coverage and a single selected external recording. Do not describe restricted-subsetF1 as whole-recording accuracy or expert equivalence.

Supporting files: `FINAL-REPORT-V23.md`, `USER-GUIDE-V23.md`, `reports/v23-days9-10/` final figures/verification, `DAYS5-8-REPORT-V23.md` scientific detail. `examples/bmb-starter-results/` contains the completed app exports for the fast demonstration.
