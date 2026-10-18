# Selected-event visual review — 19 October 2026

Scope: ten provided expert-labelled lunge intervals, one per reference fly per selected recording, with seven decoded source-video frames spanning each bout and its immediate surroundings (70 stills total). Blue R labels denote original reference tracks; red N labels denote newly generated source tracks. The reviewer inspected the contact-sheet images. Short native-view MP4 clips are retained for additional human review; no claim is made that a new independent expert annotation study was performed.

| Recording | Reference fly → new source fly | Source lunge bounds | Finding in inspected sequence |
|---|---|---|---|
| movie1 | 1 → 1 | 36219–36223 | Reference/new centres stay on the same visible fly; actor/frame neighbourhood matches source annotation IDs. |
| movie1 | 2 → 2 | 40909–40913 | Reference/new centres agree on the labelled fly through sampled movement. |
| movie2 | 1 → 2 | 47576–47580 | Opposite numerical IDs refer to the same visible body; remapping is supported in the inspected sequence. |
| movie2 | 2 → 2 | 6167–6171 | Earlier sequence has direct correspondence, demonstrating why one global recording-wide swap is insufficient. |
| movie3 | 1 → 1 | 12471–12475 | Sampled reference/new actor centres agree and source frame bounds are consistent. |
| movie3 | 2 → 2 | 50416–50420 | Actor moves while both pipelines' centres remain on the same visible fly. |
| movie4 | 1 → 2 | 24588–24592 | Reference/new IDs differ while centres identify the same visible actor. |
| movie4 | 2 → 2 | 44956–44960 | Direct correspondence in a later interval; fixed global renaming would be inappropriate. |
| movie5 | 1 → 2 | 36285–36289 | Opposite numerical IDs correspond to the same upper/left visible fly. |
| movie5 | 2 → 1 | 36279–36283 | The other labelled actor has the complementary mapping in the preceding interval. |

These are targeted samples chosen from well-covered source-positive intervals. They do not certify all retained frames, resolve every original identity error or prove that all source actions are biologically correct lunges. Source annotations are retained as provided. Ambiguous/contact intervals remain excluded; no uncertain identity is manually forced into training. Missing or excluded frames within/around a source bout remain subject to the stored masks even when its neighbours are visually plausible.

Every source frame in a recording remains in the full-grid audit; model-ready rows require the declared geometric, annotation and finite-feature criteria. Each recording's selected-review-cases.json records exact displayed frames and saved clip paths. PNGs and short MP4s in this directory preserve the visual evidence. The feature-distribution plot was also visually inspected for clipping, labels and agreement with source tables; it uses medians and percentile ranges, not confidence intervals.
