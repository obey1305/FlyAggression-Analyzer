# SDD ledger — plan: docs/superpowers/plans/2026-10-25-v23-days5-8.md
Baseline816f6d5. Existing isolatedv2.3worktree verified clean before work. User approved Days5–8 and fixed-model/exclusion-before-prediction approach.
Pre-flight: Task1 locked masks/native source bounds -> Task2 annotation-independent full-grid probabilities -> Task3 fixed whole-event evaluation -> Task4 diagnostics. No incompatible schemas; native temporal bounds deliberately differ from previous development30FPS-grid scoring.
Ruling: preserve operational full-grid detector outputs and censor whole predictions at scoring boundaries, rather than label-dependent re-smoothing. Continuous-time IoU>=.30 primary, projected-grid sensitivity secondary. Costs: not an equivalent old-development protocol; disclose differences.
Task1: core coverage/matching tests watched RED(module absent) then GREEN7tests. Preparing real dataset/lock before model loading. Unknown intervals and nonzero unverified extra columns excluded conservatively. No short-bout length exclusion.

Task1: complete. Native-time eligibility/masks/source-bout exclusions locked and committed before model loading. Coverage9/42primary and32/48secondary. Reviewed uncertain position examples; no eligibility adjustments.

Task2: complete. One successful prediction run,64operational events,76780probabilities, fitted imputer unchanged. Task3: complete. Native-time primaryF1.750(9/42coverage),secondary.71795(32/48). Projected-grid sensitivity .625/.6410. Masks unchanged; common-mask metrics identical. Task4: diagnostics in progress, no model/rule changes.

Task4: complete. Frozen results reproduced byte-identically without new inference.21Version2.3tests and6inheritedalignmenttests pass; preservation and all-event accounting verified. Fresh-context review: no material findings. Report/reproduction guide created, source-frame contexts reviewed without biological re-labelling.
Ruling: keep separatev2.3branch and worktree as requested; no merge into frozenv2.2 or UI integration.
Future hardening: exact-threshold boundary regression for new timestamps; currentpairs checked on600Hz lattice with0discrepancies. No locked code changed.
