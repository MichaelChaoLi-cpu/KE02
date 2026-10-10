# Manuscript Revision Changes

Schema: `kila-revision-changes/v1`

## reviewer-2/comment-3

### v2-part-01

- Location: Abstract; Yokoe matched-endpoint sentence
- Reason: Lead with observed restoration and the added spectral evidence; place the component-response limit in Methods and Discussion, not this result sentence.
- Kila decisions: KILA-D-20261009-001, KILA-D-20261009-002, KILA-D-20261009-003, KILA-D-20261009-004
- Mode: `replace`
- Revises prior parts: none
- Timestamp: 2026-10-09T05:56:26Z
- Author: Mike Li
- Markup SHA-256 before: `5e9535fff454c2a5cd2da9d309152ff770f7358bd1c99f23684d1f4756989cc2`
- Markup SHA-256 after: `c0a40f4316b52586b1dddbaeefa9c3c47c3605e8eb79d10bb449012d75bb3d78`
- Revision IDs: `1, 2, 3, 4, 5, 6, 7`
- Backup: `/Volumes/MikesDataBackup/Research/KE02/Rev/revision/.kila-backups/KE02.rev.markup.20261009T145626692340.reviewer-2-comment-3.v2-part-01.docx`
- Paragraph properties preserved: `true`
- Run style source SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- Formula verification: not applicable
- Endnote hyperlinks preserved: `true`
- Endnote hyperlink count: `0`
- Endnote hyperlink XML SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- Endnote relationships SHA-256: `absent`
- Before:

~~~~text
At Yokoe Bridge, a matched-endpoint analysis shows that the same asset fully reopens within 19.61 days after stronger measured shaking, compared with 1,022.4 days after the earlier earthquake, and every admissible restoration-time ratio remains below one.
~~~~

- After:

~~~~text
At Yokoe Bridge, a matched-endpoint analysis shows that the same asset fully reopens within 19.61 days after the later earthquake, compared with 1,022.4 days after the earlier earthquake, and every admissible restoration-time ratio remains below one; estimated MMI, PGA, and pseudo-spectral acceleration at three common periods are higher in the later event.
~~~~

- Minimal tracked fragments:
  1. `replace`
     - Before: "stronger"
     - After: "the"
  2. `replace`
     - Before: "measured"
     - After: "later"
  3. `replace`
     - Before: "shaking"
     - After: "earthquake"
  4. `insert`
     - Before: ""
     - After: "; estimated MMI, PGA, and pseudo-spectral acceleration at three common periods are higher in the later event"

### v2-part-02

- Location: Introduction; design overview
- Reason: Keep the overview consistent with the additional spectral comparison.
- Kila decisions: KILA-D-20261009-001, KILA-D-20261009-002, KILA-D-20261009-003, KILA-D-20261009-004
- Mode: `replace`
- Revises prior parts: none
- Timestamp: 2026-10-09T05:56:27Z
- Author: Mike Li
- Markup SHA-256 before: `c0a40f4316b52586b1dddbaeefa9c3c47c3605e8eb79d10bb449012d75bb3d78`
- Markup SHA-256 after: `2946e191d19b77fd4c813b514614796570f6263ada4384687547e9641567cdc6`
- Revision IDs: `8, 9, 10, 11, 12`
- Backup: `/Volumes/MikesDataBackup/Research/KE02/Rev/revision/.kila-backups/KE02.rev.markup.20261009T145627815358.reviewer-2-comment-3.v2-part-02.docx`
- Paragraph properties preserved: `true`
- Run style source SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- Formula verification: not applicable
- Endnote hyperlinks preserved: `true`
- Endnote hyperlink count: `0`
- Endnote hyperlink XML SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- Endnote relationships SHA-256: `absent`
- Before:

~~~~text
It then matches each case to the strongest available outcome while keeping intensity and acceleration measures separate.
~~~~

- After:

~~~~text
It then matches each case to the strongest available outcome while keeping intensity, peak acceleration, and period-specific spectral estimates separate.
~~~~

- Minimal tracked fragments:
  1. `insert`
     - Before: ""
     - After: ", peak acceleration,"
  2. `replace`
     - Before: "acceleration"
     - After: "period-specific"
  3. `replace`
     - Before: "measures"
     - After: "spectral estimates"

### v2-part-03

- Location: Results — Documented Adaptations; last two sentences
- Reason: Report the opposite spectral directions accurately while retaining the original chronology/exposure distinction.
- Kila decisions: KILA-D-20261009-001, KILA-D-20261009-002, KILA-D-20261009-003, KILA-D-20261009-004
- Mode: `replace`
- Revises prior parts: none
- Timestamp: 2026-10-09T05:56:28Z
- Author: Mike Li
- Markup SHA-256 before: `2946e191d19b77fd4c813b514614796570f6263ada4384687547e9641567cdc6`
- Markup SHA-256 after: `a44acedae3bc3b2706b702036fddd5a7b1576357d0cab21fa231ee7d49d0be40`
- Revision IDs: `13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27`
- Backup: `/Volumes/MikesDataBackup/Research/KE02/Rev/revision/.kila-backups/KE02.rev.markup.20261009T145628907155.reviewer-2-comment-3.v2-part-03.docx`
- Paragraph properties preserved: `true`
- Run style source SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- Formula verification: not applicable
- Endnote hyperlinks preserved: `true`
- Endnote hyperlink count: `0`
- Endnote hyperlink XML SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- Endnote relationships SHA-256: `absent`
- Before:

~~~~text
At Yokoe, Modified Mercalli Intensity and peak ground acceleration both rank the later earthquake as stronger; at Mashiki, intensity is similar across events while acceleration is lower in the later event. Keeping both measures separate prevents a common chronology from being mistaken for uniform exposure equivalence.
~~~~

- After:

~~~~text
At Yokoe, estimated Modified Mercalli Intensity, peak ground acceleration, and pseudo-spectral acceleration at 0.3, 1.0, and 3.0 seconds are higher in the later event; at Mashiki, intensity is similar across events while peak and spectral acceleration are lower in the later event. Keeping these measures separate prevents a common chronology from being mistaken for uniform exposure equivalence.
~~~~

- Minimal tracked fragments:
  1. `insert`
     - Before: ""
     - After: " estimated"
  2. `replace`
     - Before: " and"
     - After: ","
  3. `insert`
     - Before: ""
     - After: ","
  4. `replace`
     - Before: "both"
     - After: "and"
  5. `replace`
     - Before: "rank"
     - After: "pseudo-spectral acceleration at 0.3, 1.0, and 3.0 seconds are higher in"
  6. `replace`
     - Before: "earthquake as stronger"
     - After: "event"
  7. `insert`
     - Before: ""
     - After: "peak and spectral "
  8. `replace`
     - Before: "is"
     - After: "are"
  9. `replace`
     - Before: "both"
     - After: "these"

### v2-part-04

- Location: Results; Yokoe subsection heading
- Reason: The heading must not overstate the engineering inference.
- Kila decisions: KILA-D-20261009-001, KILA-D-20261009-002, KILA-D-20261009-003, KILA-D-20261009-004
- Mode: `replace`
- Revises prior parts: none
- Timestamp: 2026-10-09T05:56:29Z
- Author: Mike Li
- Markup SHA-256 before: `a44acedae3bc3b2706b702036fddd5a7b1576357d0cab21fa231ee7d49d0be40`
- Markup SHA-256 after: `3152e2c522fe0e98b6a45112d9aeaf70bccd7609ebd97f8f1a4ee50544d04dae`
- Revision IDs: `28, 29, 30, 31, 32, 33, 34, 35`
- Backup: `/Volumes/MikesDataBackup/Research/KE02/Rev/revision/.kila-backups/KE02.rev.markup.20261009T145630087523.reviewer-2-comment-3.v2-part-04.docx`
- Paragraph properties preserved: `true`
- Run style source SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- Formula verification: not applicable
- Endnote hyperlinks preserved: `true`
- Endnote hyperlink count: `0`
- Endnote hyperlink XML SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- Endnote relationships SHA-256: `absent`
- Before:

~~~~text
Yokoe Bridge Reopened Faster under Stronger Measured Shaking
~~~~

- After:

~~~~text
Yokoe Bridge Reopened Faster after the Second Shock
~~~~

- Minimal tracked fragments:
  1. `replace`
     - Before: "under"
     - After: "after"
  2. `replace`
     - Before: "Stronger"
     - After: "the"
  3. `replace`
     - Before: "Measured"
     - After: "Second"
  4. `replace`
     - Before: "Shaking"
     - After: "Shock"

### v2-part-05

- Location: Results — Yokoe; final two sentences
- Reason: Present the substantive result and its existing attribution boundary rather than repeat the component-response limit.
- Kila decisions: KILA-D-20261009-001, KILA-D-20261009-002, KILA-D-20261009-003, KILA-D-20261009-004
- Mode: `replace`
- Revises prior parts: none
- Timestamp: 2026-10-09T05:56:30Z
- Author: Mike Li
- Markup SHA-256 before: `3152e2c522fe0e98b6a45112d9aeaf70bccd7609ebd97f8f1a4ee50544d04dae`
- Markup SHA-256 after: `c818796019a8eeafdd323368c764b89fa3097718227ff1c211e36674cee905fd`
- Revision IDs: `36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54`
- Backup: `/Volumes/MikesDataBackup/Research/KE02/Rev/revision/.kila-backups/KE02.rev.markup.20261009T145631195993.reviewer-2-comment-3.v2-part-05.docx`
- Paragraph properties preserved: `true`
- Run style source SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- Formula verification: not applicable
- Endnote hyperlinks preserved: `true`
- Endnote hyperlink count: `0`
- Endnote hyperlink XML SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- Endnote relationships SHA-256: `absent`
- Before:

~~~~text
The later event also raises mean Modified Mercalli Intensity by 1.536 units and peak ground acceleration by a factor of 1.847 at the bridge. Faster restoration therefore remains directionally dominant across endpoints and hazard measures, but the comparison does not isolate reconstruction from changes in inspection, response, or repair capacity.
~~~~

- After:

~~~~text
The later-event product also estimates mean Modified Mercalli Intensity 1.536 units higher and peak ground acceleration 1.847 times higher at the bridge. The 2026/2016 ratios of sampled mean 5%-damped pseudo-spectral acceleration are 1.432, 1.838, and 2.909 at 0.3, 1.0, and 3.0 seconds, respectively (Table 2). Faster restoration remains robust across the admissible endpoints and accompanies higher estimates for the compared ground-motion metrics, but the comparison does not isolate reconstruction from changes in inspection, response, or repair capacity.
~~~~

- Minimal tracked fragments:
  1. `replace`
     - Before: "later"
     - After: "later-event"
  2. `replace`
     - Before: "event"
     - After: "product"
  3. `replace`
     - Before: "raises"
     - After: "estimates"
  4. `delete`
     - Before: "by "
     - After: ""
  5. `insert`
     - Before: ""
     - After: " higher"
  6. `delete`
     - Before: "by a factor of "
     - After: ""
  7. `insert`
     - Before: ""
     - After: " times higher"
  8. `insert`
     - Before: ""
     - After: "The 2026/2016 ratios of sampled mean 5%-damped pseudo-spectral acceleration are 1.432, 1.838, and 2.909 at 0.3, 1.0, and 3.0 seconds, respectively (Table 2). "
  9. `delete`
     - Before: "therefore "
     - After: ""
  10. `replace`
     - Before: "directionally dominant"
     - After: "robust"
  11. `insert`
     - Before: ""
     - After: " the admissible"
  12. `replace`
     - Before: "hazard"
     - After: "accompanies"
  13. `replace`
     - Before: "measures"
     - After: "higher estimates for the compared ground-motion metrics"

### v2-part-06

- Location: Results — Cross-case synthesis and robustness; third/fourth sentences
- Reason: Retain the inferential distinction between cases. Define the separate supplemental spectral analysis once in the sensitivity Methods.
- Kila decisions: KILA-D-20261009-001, KILA-D-20261009-002, KILA-D-20261009-003, KILA-D-20261009-004
- Mode: `replace`
- Revises prior parts: none
- Timestamp: 2026-10-09T05:56:31Z
- Author: Mike Li
- Markup SHA-256 before: `c818796019a8eeafdd323368c764b89fa3097718227ff1c211e36674cee905fd`
- Markup SHA-256 after: `e44b22b05f2874f248dbed09d4646158140bf425a3dff9a1bb994353fca98025`
- Revision IDs: `55, 56, 57, 58, 59, 60, 61, 62, 63, 64`
- Backup: `/Volumes/MikesDataBackup/Research/KE02/Rev/revision/.kila-backups/KE02.rev.markup.20261009T145632335297.reviewer-2-comment-3.v2-part-06.docx`
- Paragraph properties preserved: `true`
- Run style source SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- Formula verification: not applicable
- Endnote hyperlinks preserved: `true`
- Endnote hyperlink count: `0`
- Endnote hyperlink XML SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- Endnote relationships SHA-256: `absent`
- Before:

~~~~text
Yokoe reaches directional dominance because asset identity, endpoints, and hazard direction align, whereas Mashiki reaches structured comparison because passage is repeatedly observed but hazard ranking and outcome equivalence remain measurement dependent. A second audit applies 12 prespecified checks to hazard metrics, restoration endpoints, observation coverage, selection denominators, geometry rules, and source precedence.
~~~~

- After:

~~~~text
Yokoe supports a directional same-asset restoration contrast because asset identity and endpoints align and the compared ground-motion estimates are higher in the later event, whereas Mashiki reaches structured comparison because passage is repeatedly observed but hazard interpretation and outcome equivalence remain measurement dependent. A second audit applies 12 prespecified checks to hazard metrics, restoration endpoints, observation coverage, selection denominators, geometry rules, and source precedence.
~~~~

- Minimal tracked fragments:
  1. `replace`
     - Before: "reaches"
     - After: "supports a"
  2. `replace`
     - Before: "dominance"
     - After: "same-asset restoration contrast"
  3. `delete`
     - Before: ", endpoints,"
     - After: ""
  4. `replace`
     - Before: "hazard direction"
     - After: "endpoints"
  5. `insert`
     - Before: ""
     - After: " and the compared ground-motion estimates are higher in the later event"
  6. `replace`
     - Before: "ranking"
     - After: "interpretation"

### v2-part-07

- Location: Discussion — Structural and Capacity Pathways; second sentence
- Reason: Keep the Discussion's operational finding clear and consistent with the Results.
- Kila decisions: KILA-D-20261009-001, KILA-D-20261009-002, KILA-D-20261009-003, KILA-D-20261009-004
- Mode: `replace`
- Revises prior parts: none
- Timestamp: 2026-10-09T05:56:33Z
- Author: Mike Li
- Markup SHA-256 before: `e44b22b05f2874f248dbed09d4646158140bf425a3dff9a1bb994353fca98025`
- Markup SHA-256 after: `7254b56b957b09d9f88420cfa26bfb82f26aa24c25768348f9093a68411802b9`
- Revision IDs: `65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86`
- Backup: `/Volumes/MikesDataBackup/Research/KE02/Rev/revision/.kila-backups/KE02.rev.markup.20261009T145633407863.reviewer-2-comment-3.v2-part-07.docx`
- Paragraph properties preserved: `true`
- Run style source SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- Formula verification: not applicable
- Endnote hyperlinks preserved: `true`
- Endnote hyperlink count: `0`
- Endnote hyperlink XML SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- Endnote relationships SHA-256: `absent`
- Before:

~~~~text
Faster reopening persists when the earlier endpoint is relaxed and when both local shaking metrics indicate a more severe later exposure.
~~~~

- After:

~~~~text
Faster reopening persists when the earlier endpoint is relaxed and accompanies higher later-event estimates of MMI, PGA, and pseudo-spectral acceleration at the three compared periods.
~~~~

- Minimal tracked fragments:
  1. `replace`
     - Before: "when"
     - After: "accompanies"
  2. `replace`
     - Before: "both"
     - After: "higher"
  3. `replace`
     - Before: "local"
     - After: "later-event"
  4. `replace`
     - Before: "shaking"
     - After: "estimates"
  5. `replace`
     - Before: "metrics"
     - After: "of"
  6. `replace`
     - Before: "indicate"
     - After: "MMI,"
  7. `replace`
     - Before: "a"
     - After: "PGA,"
  8. `replace`
     - Before: "more"
     - After: "and"
  9. `replace`
     - Before: "severe"
     - After: "pseudo-spectral"
  10. `replace`
     - Before: "later"
     - After: "acceleration"
  11. `replace`
     - Before: "exposure"
     - After: "at the three compared periods"

### v2-part-08

- Location: Discussion — Inference Limits and Transferability; after attribution limit
- Reason: Concentrate the limitations that change interpretation in one passage, without a stacked list of equivalence/severity denials.
- Kila decisions: KILA-D-20261009-001, KILA-D-20261009-002, KILA-D-20261009-003, KILA-D-20261009-004
- Mode: `replace`
- Revises prior parts: none
- Timestamp: 2026-10-09T05:56:34Z
- Author: Mike Li
- Markup SHA-256 before: `7254b56b957b09d9f88420cfa26bfb82f26aa24c25768348f9093a68411802b9`
- Markup SHA-256 after: `13b883770cddee6f25e7fd351e0009876f153033b59fbed81ca124f3449e5d78`
- Revision IDs: `87`
- Backup: `/Volumes/MikesDataBackup/Research/KE02/Rev/revision/.kila-backups/KE02.rev.markup.20261009T145634525622.reviewer-2-comment-3.v2-part-08.docx`
- Paragraph properties preserved: `true`
- Run style source SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- Formula verification: not applicable
- Endnote hyperlinks preserved: `true`
- Endnote hyperlink count: `0`
- Endnote hyperlink XML SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- Endnote relationships SHA-256: `absent`
- Before:

~~~~text
The study therefore establishes chronology, measurement robustness, and directional contrast but cannot allocate that contrast among reconstruction, operations, and context.
~~~~

- After:

~~~~text
The study therefore establishes chronology, measurement robustness, and directional contrast but cannot allocate that contrast among reconstruction, operations, and context. The products use different model generations, ground-motion prediction equations, and grid resolutions, so their ratios are not a harmonized event-only contrast. Ground-motion duration, complete frequency content, and bridge modal properties are not assessed; component response therefore remains outside this comparison.
~~~~

- Minimal tracked fragments:
  1. `insert`
     - Before: ""
     - After: " The products use different model generations, ground-motion prediction equations, and grid resolutions, so their ratios are not a harmonized event-only contrast. Ground-motion duration, complete frequency content, and bridge modal properties are not assessed; component response therefore remains outside this comparison."

### v2-part-09

- Location: Discussion — Inference Limits and Transferability; closing Yokoe/Mashiki summary
- Reason: Align the concluding summary with the bounded evidence.
- Kila decisions: KILA-D-20261009-001, KILA-D-20261009-002, KILA-D-20261009-003, KILA-D-20261009-004
- Mode: `replace`
- Revises prior parts: none
- Timestamp: 2026-10-09T05:56:35Z
- Author: Mike Li
- Markup SHA-256 before: `13b883770cddee6f25e7fd351e0009876f153033b59fbed81ca124f3449e5d78`
- Markup SHA-256 after: `be56408f8ad099cfa61758a1c6bcfa2d55b24dfe3aaeaa6a674b8deb97ecfd65`
- Revision IDs: `88, 89, 90, 91, 92, 93, 94, 95`
- Backup: `/Volumes/MikesDataBackup/Research/KE02/Rev/revision/.kila-backups/KE02.rev.markup.20261009T145635817446.reviewer-2-comment-3.v2-part-09.docx`
- Paragraph properties preserved: `true`
- Run style source SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- Formula verification: not applicable
- Endnote hyperlinks preserved: `true`
- Endnote hyperlink count: `0`
- Endnote hyperlink XML SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- Endnote relationships SHA-256: `absent`
- Before:

~~~~text
Yokoe shows much faster same-asset reopening under stronger measured shaking, while Mashiki shows extensive observed passage through an expanded corridor under a bounded archive.
~~~~

- After:

~~~~text
Yokoe shows much faster same-asset reopening with higher estimates for the compared ground-motion metrics, while Mashiki shows extensive observed passage through an expanded corridor under a bounded archive.
~~~~

- Minimal tracked fragments:
  1. `replace`
     - Before: "under"
     - After: "with"
  2. `replace`
     - Before: "stronger"
     - After: "higher"
  3. `replace`
     - Before: "measured"
     - After: "estimates"
  4. `replace`
     - Before: "shaking"
     - After: "for the compared ground-motion metrics"

### v2-part-10

- Location: Methods — Event-Specific Shaking Characterization; sampling sentence
- Reason: Retain reproducibility and model-estimate semantics while shortening low-level implementation detail; all provenance remains saved locally.
- Kila decisions: KILA-D-20261009-001, KILA-D-20261009-002, KILA-D-20261009-003, KILA-D-20261009-004
- Mode: `replace`
- Revises prior parts: none
- Timestamp: 2026-10-09T05:56:36Z
- Author: Mike Li
- Markup SHA-256 before: `be56408f8ad099cfa61758a1c6bcfa2d55b24dfe3aaeaa6a674b8deb97ecfd65`
- Markup SHA-256 after: `1741ac1018d46828ebd6ab334f1c0aedee56e2422edddbb1c9988b50021e512e`
- Revision IDs: `96`
- Backup: `/Volumes/MikesDataBackup/Research/KE02/Rev/revision/.kila-backups/KE02.rev.markup.20261009T145636865065.reviewer-2-comment-3.v2-part-10.docx`
- Paragraph properties preserved: `true`
- Run style source SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- Formula verification: not applicable
- Endnote hyperlinks preserved: `true`
- Endnote hyperlink count: `0`
- Endnote hyperlink XML SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- Endnote relationships SHA-256: `absent`
- Before:

~~~~text
We sample Modified Mercalli Intensity and peak ground acceleration over each verified case geometry and average them within the same spatial support for the two episodes.
~~~~

- After:

~~~~text
We sample Modified Mercalli Intensity and peak ground acceleration over each verified case geometry and average them within the same spatial support for the two episodes. We additionally compare the common 5%-damped pseudo-spectral acceleration fields at 0.3, 1.0, and 3.0 seconds in the archived USGS ShakeMap products. The sampling retains 51 positions along the selected Yokoe restriction segment and 101 positions along the Mashiki aggregate corridor boundary, using identical within-case coordinates across events. Acceleration rasters are converted from natural logarithms to g before averaging and checked against XML fields in percent-g. The means summarize sampled model estimates: Yokoe positions occupy one grid cell per event, while Mashiki positions occupy three cells in 2016 and seven in 2026. Mashiki averages are boundary-sampled rather than area-weighted. The products have nominal grid spacings of 0.0167 degrees in 2016 and 0.0083 degrees in 2026; their map versions, software builds, and model specifications are retained in the analysis records.
~~~~

- Minimal tracked fragments:
  1. `insert`
     - Before: ""
     - After: " We additionally compare the common 5%-damped pseudo-spectral acceleration fields at 0.3, 1.0, and 3.0 seconds in the archived USGS ShakeMap products. The sampling retains 51 positions along the selected Yokoe restriction segment and 101 positions along the Mashiki aggregate corridor boundary, using identical within-case coordinates across events. Acceleration rasters are converted from natural logarithms to g before averaging and checked against XML fields in percent-g. The means summarize sampled model estimates: Yokoe positions occupy one grid cell per event, while Mashiki positions occupy three cells in 2016 and seven in 2026. Mashiki averages are boundary-sampled rather than area-weighted. The products have nominal grid spacings of 0.0167 degrees in 2016 and 0.0083 degrees in 2026; their map versions, software builds, and model specifications are retained in the analysis records."

### v2-part-11

- Location: Methods — Event-Specific Shaking Characterization; interpretation after Equation 3
- Reason: Give a concise positive scope definition instead of multiple denials of component-demand equivalence or severity.
- Kila decisions: KILA-D-20261009-001, KILA-D-20261009-002, KILA-D-20261009-003, KILA-D-20261009-004
- Mode: `replace`
- Revises prior parts: none
- Timestamp: 2026-10-09T05:56:37Z
- Author: Mike Li
- Markup SHA-256 before: `1741ac1018d46828ebd6ab334f1c0aedee56e2422edddbb1c9988b50021e512e`
- Markup SHA-256 after: `98b28c53efac26a56c8fb66a24102724e110373566a47e6017713e44ac380cf2`
- Revision IDs: `97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132`
- Backup: `/Volumes/MikesDataBackup/Research/KE02/Rev/revision/.kila-backups/KE02.rev.markup.20261009T145637967760.reviewer-2-comment-3.v2-part-11.docx`
- Paragraph properties preserved: `true`
- Run style source SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- Formula verification: not applicable
- Endnote hyperlinks preserved: `true`
- Endnote hyperlink count: `0`
- Endnote hyperlink XML SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- Endnote relationships SHA-256: `absent`
- Before:

~~~~text
A positive difference and a ratio above one jointly indicate stronger later shaking. If the measures disagree, as they do at Mashiki, we classify the hazard premise as measurement dependent rather than selecting the favorable metric.
~~~~

- After:

~~~~text
A positive difference and a ratio above one jointly indicate higher estimated MMI and PGA. For each common spectral period, we also report the later-to-earlier ratio of sampled mean pseudo-spectral acceleration. The analysis characterizes local ground motion rather than component response. At Mashiki, nearly unchanged MMI and lower peak and spectral acceleration support different descriptions of exposure.
~~~~

- Minimal tracked fragments:
  1. `replace`
     - Before: "stronger"
     - After: "higher"
  2. `replace`
     - Before: "later"
     - After: "estimated"
  3. `replace`
     - Before: "shaking"
     - After: "MMI and PGA"
  4. `replace`
     - Before: "If"
     - After: "For"
  5. `replace`
     - Before: "the"
     - After: "each"
  6. `replace`
     - Before: "measures"
     - After: "common"
  7. `replace`
     - Before: "disagree,"
     - After: "spectral"
  8. `replace`
     - Before: "as they do at Mashiki"
     - After: "period"
  9. `replace`
     - Before: "classify"
     - After: "also report"
  10. `replace`
     - Before: "hazard"
     - After: "later-to-earlier"
  11. `replace`
     - Before: "premise"
     - After: "ratio"
  12. `replace`
     - Before: "as"
     - After: "of"
  13. `replace`
     - Before: "measurement"
     - After: "sampled"
  14. `replace`
     - Before: "dependent"
     - After: "mean pseudo-spectral acceleration. The analysis characterizes local ground motion"
  15. `replace`
     - Before: "selecting"
     - After: "component"
  16. `replace`
     - Before: "the"
     - After: "response."
  17. `replace`
     - Before: "favorable"
     - After: "At"
  18. `replace`
     - Before: "metric"
     - After: "Mashiki, nearly unchanged MMI and lower peak and spectral acceleration support different descriptions of exposure"

### v2-part-12

- Location: Methods — Yokoe matched-endpoint analysis; interpretation after Equation 7
- Reason: Define what the endpoint test establishes without repeating the separate engineering limitation.
- Kila decisions: KILA-D-20261009-001, KILA-D-20261009-002, KILA-D-20261009-003, KILA-D-20261009-004
- Mode: `replace`
- Revises prior parts: none
- Timestamp: 2026-10-09T05:56:38Z
- Author: Mike Li
- Markup SHA-256 before: `98b28c53efac26a56c8fb66a24102724e110373566a47e6017713e44ac380cf2`
- Markup SHA-256 after: `9e3826fda58faf86d154b478e0f7da6bacc13245e54b97b953724ee67eef33f3`
- Revision IDs: `133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143, 144, 145, 146, 147, 148, 149, 150`
- Backup: `/Volumes/MikesDataBackup/Research/KE02/Rev/revision/.kila-backups/KE02.rev.markup.20261009T145639115121.reviewer-2-comment-3.v2-part-12.docx`
- Paragraph properties preserved: `true`
- Run style source SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- Formula verification: not applicable
- Endnote hyperlinks preserved: `true`
- Endnote hyperlink count: `0`
- Endnote hyperlink XML SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- Endnote relationships SHA-256: `absent`
- Before:

~~~~text
We require this condition for every admissible endpoint and independently require both shaking measures to rank the later event as stronger at the bridge. Satisfying these rules establishes directional dominance for the observed same-asset contrast.
~~~~

- After:

~~~~text
We require this condition for every admissible endpoint and independently require higher estimated MMI and PGA in the later event at the bridge. Satisfying these rules establishes the direction of the observed same-asset restoration contrast.
~~~~

- Minimal tracked fragments:
  1. `replace`
     - Before: "both"
     - After: "higher"
  2. `replace`
     - Before: "shaking"
     - After: "estimated"
  3. `replace`
     - Before: "measures"
     - After: "MMI"
  4. `replace`
     - Before: "to"
     - After: "and"
  5. `replace`
     - Before: "rank"
     - After: "PGA in"
  6. `delete`
     - Before: " as stronger"
     - After: ""
  7. `replace`
     - Before: "directional"
     - After: "the"
  8. `replace`
     - Before: "dominance"
     - After: "direction"
  9. `replace`
     - Before: "for"
     - After: "of"
  10. `insert`
     - Before: ""
     - After: "restoration "

### v2-part-13

- Location: Methods — Sensitivity checks; second sentence
- Reason: Preserve the original 12-check definition.
- Kila decisions: KILA-D-20261009-001, KILA-D-20261009-002, KILA-D-20261009-003, KILA-D-20261009-004
- Mode: `replace`
- Revises prior parts: none
- Timestamp: 2026-10-09T05:56:39Z
- Author: Mike Li
- Markup SHA-256 before: `9e3826fda58faf86d154b478e0f7da6bacc13245e54b97b953724ee67eef33f3`
- Markup SHA-256 after: `8adbc7dd4f6a9dbb921a1a4b5cd7a7f03926704a56e1cadb336a6f36b41422c7`
- Revision IDs: `151`
- Backup: `/Volumes/MikesDataBackup/Research/KE02/Rev/revision/.kila-backups/KE02.rev.markup.20261009T145640210798.reviewer-2-comment-3.v2-part-13.docx`
- Paragraph properties preserved: `true`
- Run style source SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- Formula verification: not applicable
- Endnote hyperlinks preserved: `true`
- Endnote hyperlink count: `0`
- Endnote hyperlink XML SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- Endnote relationships SHA-256: `absent`
- Before:

~~~~text
The checks vary intensity and acceleration rankings, Yokoe endpoint definitions, Mashiki layer availability and outcome equivalence, candidate denominators, geometry linkage, and source precedence.
~~~~

- After:

~~~~text
The checks vary intensity and acceleration rankings, Yokoe endpoint definitions, Mashiki layer availability and outcome equivalence, candidate denominators, geometry linkage, and source precedence. The three-period spectral comparison is an additional analysis and is not included in the original prespecified check count.
~~~~

- Minimal tracked fragments:
  1. `insert`
     - Before: ""
     - After: " The three-period spectral comparison is an additional analysis and is not included in the original prespecified check count."

### v2-part-14

- Location: Methods — Reproducibility; first sentence
- Reason: Do not falsely imply the additional experimental CSVs already occur in the frozen original writing dictionary.
- Kila decisions: KILA-D-20261009-001, KILA-D-20261009-002, KILA-D-20261009-003, KILA-D-20261009-004
- Mode: `replace`
- Revises prior parts: none
- Timestamp: 2026-10-09T05:56:40Z
- Author: Mike Li
- Markup SHA-256 before: `8adbc7dd4f6a9dbb921a1a4b5cd7a7f03926704a56e1cadb336a6f36b41422c7`
- Markup SHA-256 after: `c19aa170a38147e2f4c61260b44c10414b504bc22a957bff8d75423bd8064027`
- Revision IDs: `152, 153, 154, 155, 156, 157, 158`
- Backup: `/Volumes/MikesDataBackup/Research/KE02/Rev/revision/.kila-backups/KE02.rev.markup.20261009T145641465167.reviewer-2-comment-3.v2-part-14.docx`
- Paragraph properties preserved: `true`
- Run style source SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- Formula verification: not applicable
- Endnote hyperlinks preserved: `true`
- Endnote hyperlink count: `0`
- Endnote hyperlink XML SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- Endnote relationships SHA-256: `absent`
- Before:

~~~~text
Every reported value and display is linked through the content dictionary to a processed dataset, an analysis script, and an official-source record.
~~~~

- After:

~~~~text
Every reported value and display is linked through the content dictionary or revision analysis records to its source data, an analysis script, and an official-source record.
~~~~

- Minimal tracked fragments:
  1. `insert`
     - Before: ""
     - After: "or revision analysis records "
  2. `replace`
     - Before: "a"
     - After: "its"
  3. `replace`
     - Before: "processed"
     - After: "source"
  4. `replace`
     - Before: "dataset"
     - After: "data"

### v2-part-15

- Location: Figure 2 caption title
- Reason: Match the restoration-focused figure and scoped demand comparison.
- Kila decisions: KILA-D-20261009-001, KILA-D-20261009-002, KILA-D-20261009-003, KILA-D-20261009-004
- Mode: `replace`
- Revises prior parts: none
- Timestamp: 2026-10-09T05:56:42Z
- Author: Mike Li
- Markup SHA-256 before: `c19aa170a38147e2f4c61260b44c10414b504bc22a957bff8d75423bd8064027`
- Markup SHA-256 after: `7789ff5b0657d9b9cf03426bc68010a4deb2c9aaa75420de74c0aa8a716f3744`
- Revision IDs: `159, 160, 161, 162`
- Backup: `/Volumes/MikesDataBackup/Research/KE02/Rev/revision/.kila-backups/KE02.rev.markup.20261009T145642755373.reviewer-2-comment-3.v2-part-15.docx`
- Paragraph properties preserved: `true`
- Run style source SHA-256: `5017784f5cca96911d02c75702284e2458f97a555bee88c1cf2aa939b54390c5`
- Formula verification: not applicable
- Endnote hyperlinks preserved: `true`
- Endnote hyperlink count: `0`
- Endnote hyperlink XML SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- Endnote relationships SHA-256: `absent`
- Before:

~~~~text
Figure 2. Yokoe restoration timing under repeated stronger shock
~~~~

- After:

~~~~text
Figure 2. Yokoe restoration timing across repeated shocks
~~~~

- Minimal tracked fragments:
  1. `replace`
     - Before: "under"
     - After: "across"
  2. `replace`
     - Before: "stronger shock"
     - After: "shocks"

### v2-part-16

- Location: Figure 2 caption note; panel b and interpretation sentences
- Reason: Let the restoration figure explain its own content; spectral values and engineering scope are already defined elsewhere.
- Kila decisions: KILA-D-20261009-001, KILA-D-20261009-002, KILA-D-20261009-003, KILA-D-20261009-004
- Mode: `replace`
- Revises prior parts: none
- Timestamp: 2026-10-09T05:56:43Z
- Author: Mike Li
- Markup SHA-256 before: `7789ff5b0657d9b9cf03426bc68010a4deb2c9aaa75420de74c0aa8a716f3744`
- Markup SHA-256 after: `6b93d8343cbd025272e047f8db6d6b3f04fef9219758fc59d7632de3600b64f0`
- Revision IDs: `163`
- Backup: `/Volumes/MikesDataBackup/Research/KE02/Rev/revision/.kila-backups/KE02.rev.markup.20261009T145643920977.reviewer-2-comment-3.v2-part-16.docx`
- Paragraph properties preserved: `true`
- Run style source SHA-256: `c21d00426c037a67b0fba1fabff610e453e3a2a5424274c5287e40c65ce00d46`
- Formula verification: not applicable
- Endnote hyperlinks preserved: `true`
- Endnote hyperlink count: `0`
- Endnote hyperlink XML SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- Endnote relationships SHA-256: `absent`
- Before:

~~~~text
Panel b shows that both bounded restoration ratios remain below one while 2026 MMI and PGA are higher. The direction is robust but not a causal reconstruction effect.
~~~~

- After:

~~~~text
Panel b shows that both bounded restoration ratios remain below one while estimated 2026 MMI and PGA are higher. The direction is robust but not a causal reconstruction effect.
~~~~

- Minimal tracked fragments:
  1. `insert`
     - Before: ""
     - After: " estimated"

### v2-part-17

- Location: Table 1; row 'Additional official reconstructions'; column 'Repeated-shock evidence'
- Reason: Limit the contextual screening label to its original metrics; no spectral analysis is claimed for excluded candidates.
- Kila decisions: KILA-D-20261009-001, KILA-D-20261009-002, KILA-D-20261009-003, KILA-D-20261009-004
- Mode: `replace`
- Revises prior parts: none
- Timestamp: 2026-10-09T05:56:44Z
- Author: Mike Li
- Markup SHA-256 before: `6b93d8343cbd025272e047f8db6d6b3f04fef9219758fc59d7632de3600b64f0`
- Markup SHA-256 after: `7fa986d9e73c4cde8ed2b1db5993cc1f63fafdc44da5cee20e52a7dac1836d6f`
- Revision IDs: `164, 165, 166, 167, 168`
- Backup: `/Volumes/MikesDataBackup/Research/KE02/Rev/revision/.kila-backups/KE02.rev.markup.20261009T145645181062.reviewer-2-comment-3.v2-part-17.docx`
- Paragraph properties preserved: `true`
- Run style source SHA-256: `c21d00426c037a67b0fba1fabff610e453e3a2a5424274c5287e40c65ce00d46`
- Formula verification: not applicable
- Endnote hyperlinks preserved: `true`
- Endnote hyperlink count: `0`
- Endnote hyperlink XML SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- Endnote relationships SHA-256: `absent`
- Before:

~~~~text
0; 2026 shaking weaker
~~~~

- After:

~~~~text
0; lower 2026 MMI and PGA in the original screen
~~~~

- Minimal tracked fragments:
  1. `insert`
     - Before: ""
     - After: "lower "
  2. `replace`
     - Before: "shaking"
     - After: "MMI"
  3. `replace`
     - Before: "weaker"
     - After: "and PGA in the original screen"

### v2-part-18

- Location: Table 1; row 'Additional official reconstructions'; column 'Dominant exclusion'
- Reason: Preserve the three contextual exclusions while avoiding an unqualified shaking-severity claim.
- Kila decisions: KILA-D-20261009-001, KILA-D-20261009-002, KILA-D-20261009-003, KILA-D-20261009-004
- Mode: `replace`
- Revises prior parts: none
- Timestamp: 2026-10-09T05:56:46Z
- Author: Mike Li
- Markup SHA-256 before: `7fa986d9e73c4cde8ed2b1db5993cc1f63fafdc44da5cee20e52a7dac1836d6f`
- Markup SHA-256 after: `5b48177177627e5e3edaad6a874e2aa3a90837b3c253300c43f6ce61c77ce04f`
- Revision IDs: `169, 170, 171, 172`
- Backup: `/Volumes/MikesDataBackup/Research/KE02/Rev/revision/.kila-backups/KE02.rev.markup.20261009T145646447669.reviewer-2-comment-3.v2-part-18.docx`
- Paragraph properties preserved: `true`
- Run style source SHA-256: `c21d00426c037a67b0fba1fabff610e453e3a2a5424274c5287e40c65ce00d46`
- Formula verification: not applicable
- Endnote hyperlinks preserved: `true`
- Endnote hyperlink count: `0`
- Endnote hyperlink XML SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- Endnote relationships SHA-256: `absent`
- Before:

~~~~text
Geometry mismatch and weaker 2026 shaking (n=3)
~~~~

- After:

~~~~text
Geometry mismatch and lower 2026 MMI and PGA (n=3)
~~~~

- Minimal tracked fragments:
  1. `replace`
     - Before: "weaker"
     - After: "lower"
  2. `replace`
     - Before: "shaking"
     - After: "MMI and PGA"

### v2-part-19-cell-01

- Location: Table 2; MMI row; Evidence dimension
- Reason: Complete one of the four exact approved v2-part-19 cell patches after the human inserted the three PSA rows; preserve table structure and original inference ceilings.
- Kila decisions: KILA-D-20261009-001, KILA-D-20261009-002, KILA-D-20261009-003, KILA-D-20261009-004, KILA-D-20261009-005
- Mode: `replace`
- Revises prior parts: none
- Timestamp: 2026-10-09T06:31:36Z
- Author: Mike Li
- Markup SHA-256 before: `11b61add1dfc10d55205fdd8e9c5d12f07b3e561a9d64b7c5e9cc45ff0cb30f2`
- Markup SHA-256 after: `c1e180d44a37fabcf62af553320f193e0f4b732c4427e84ce2f4c92773996116`
- Revision IDs: `233, 234`
- Backup: `Rev/revision/.kila-backups/KE02.rev.markup.20261009T153136540212.reviewer-2-comment-3.v2-part-19-cell-01.docx`
- Paragraph properties preserved: `true`
- Run style source SHA-256: `c21d00426c037a67b0fba1fabff610e453e3a2a5424274c5287e40c65ce00d46`
- Formula verification: not applicable
- Endnote hyperlinks preserved: `true`
- Endnote hyperlink count: `0`
- Endnote hyperlink XML SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- Endnote relationships SHA-256: `absent`
- Before:

~~~~text
Shaking: MMI
~~~~

- After:

~~~~text
Estimated MMI
~~~~

- Minimal tracked fragments:
  1. `replace`
     - Before: "Shaking:"
     - After: "Estimated"

### v2-part-19-cell-02

- Location: Table 2; PGA row; Evidence dimension
- Reason: Complete one of the four exact approved v2-part-19 cell patches after the human inserted the three PSA rows; preserve table structure and original inference ceilings.
- Kila decisions: KILA-D-20261009-001, KILA-D-20261009-002, KILA-D-20261009-003, KILA-D-20261009-004, KILA-D-20261009-005
- Mode: `replace`
- Revises prior parts: none
- Timestamp: 2026-10-09T06:31:37Z
- Author: Mike Li
- Markup SHA-256 before: `c1e180d44a37fabcf62af553320f193e0f4b732c4427e84ce2f4c92773996116`
- Markup SHA-256 after: `261530ef8bc91025b4c1642536ab5be05e28326f9e199bf322c59df45fc33e54`
- Revision IDs: `235, 236`
- Backup: `Rev/revision/.kila-backups/KE02.rev.markup.20261009T153138317370.reviewer-2-comment-3.v2-part-19-cell-02.docx`
- Paragraph properties preserved: `true`
- Run style source SHA-256: `c21d00426c037a67b0fba1fabff610e453e3a2a5424274c5287e40c65ce00d46`
- Formula verification: not applicable
- Endnote hyperlinks preserved: `true`
- Endnote hyperlink count: `0`
- Endnote hyperlink XML SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- Endnote relationships SHA-256: `absent`
- Before:

~~~~text
Shaking: PGA
~~~~

- After:

~~~~text
Estimated PGA
~~~~

- Minimal tracked fragments:
  1. `replace`
     - Before: "Shaking:"
     - After: "Estimated"

### v2-part-19-cell-03

- Location: Table 2; Evidence level row; Yokoe Bridge
- Reason: Complete one of the four exact approved v2-part-19 cell patches after the human inserted the three PSA rows; preserve table structure and original inference ceilings.
- Kila decisions: KILA-D-20261009-001, KILA-D-20261009-002, KILA-D-20261009-003, KILA-D-20261009-004, KILA-D-20261009-005
- Mode: `replace`
- Revises prior parts: none
- Timestamp: 2026-10-09T06:31:39Z
- Author: Mike Li
- Markup SHA-256 before: `261530ef8bc91025b4c1642536ab5be05e28326f9e199bf322c59df45fc33e54`
- Markup SHA-256 after: `197e1bf62e4500d0527f54ac925ef3e48ef188cf8ec6075d0be8111c5a0b658b`
- Revision IDs: `237, 238`
- Backup: `Rev/revision/.kila-backups/KE02.rev.markup.20261009T153139906707.reviewer-2-comment-3.v2-part-19-cell-03.docx`
- Paragraph properties preserved: `true`
- Run style source SHA-256: `c21d00426c037a67b0fba1fabff610e453e3a2a5424274c5287e40c65ce00d46`
- Formula verification: not applicable
- Endnote hyperlinks preserved: `true`
- Endnote hyperlink count: `0`
- Endnote hyperlink XML SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- Endnote relationships SHA-256: `absent`
- Before:

~~~~text
Directional dominance
~~~~

- After:

~~~~text
Directional same-asset restoration contrast
~~~~

- Minimal tracked fragments:
  1. `replace`
     - Before: "dominance"
     - After: "same-asset restoration contrast"

### v2-part-19-cell-04

- Location: Table 2; Permissible claim row; Yokoe Bridge
- Reason: Complete one of the four exact approved v2-part-19 cell patches after the human inserted the three PSA rows; preserve table structure and original inference ceilings.
- Kila decisions: KILA-D-20261009-001, KILA-D-20261009-002, KILA-D-20261009-003, KILA-D-20261009-004, KILA-D-20261009-005
- Mode: `replace`
- Revises prior parts: none
- Timestamp: 2026-10-09T06:31:41Z
- Author: Mike Li
- Markup SHA-256 before: `197e1bf62e4500d0527f54ac925ef3e48ef188cf8ec6075d0be8111c5a0b658b`
- Markup SHA-256 after: `3dc9bffcf9d368542362445234eff6d6d9095edefa51660ce7361831419dede2`
- Revision IDs: `239, 240, 241, 242, 243, 244, 245, 246, 247, 248`
- Backup: `Rev/revision/.kila-backups/KE02.rev.markup.20261009T153141812250.reviewer-2-comment-3.v2-part-19-cell-04.docx`
- Paragraph properties preserved: `true`
- Run style source SHA-256: `c21d00426c037a67b0fba1fabff610e453e3a2a5424274c5287e40c65ce00d46`
- Formula verification: not applicable
- Endnote hyperlinks preserved: `true`
- Endnote hyperlink count: `0`
- Endnote hyperlink XML SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- Endnote relationships SHA-256: `absent`
- Before:

~~~~text
Faster same-asset restoration under stronger 2026 MMI and PGA.
~~~~

- After:

~~~~text
Faster same-asset restoration with higher compared ground-motion estimates.
~~~~

- Minimal tracked fragments:
  1. `replace`
     - Before: "under"
     - After: "with"
  2. `replace`
     - Before: "stronger"
     - After: "higher"
  3. `replace`
     - Before: "2026"
     - After: "compared"
  4. `replace`
     - Before: "MMI"
     - After: "ground-motion"
  5. `replace`
     - Before: "and PGA"
     - After: "estimates"

### v2-part-20

- Location: Table 3; row 'Mashiki 2026 service-presence trajectory'; column 'Result'
- Reason: Summarize robustness without duplicating the six PSA ratios displayed in Table 2.
- Kila decisions: KILA-D-20261009-001, KILA-D-20261009-002, KILA-D-20261009-003, KILA-D-20261009-004
- Mode: `replace`
- Revises prior parts: none
- Timestamp: 2026-10-09T06:31:43Z
- Author: Mike Li
- Markup SHA-256 before: `3dc9bffcf9d368542362445234eff6d6d9095edefa51660ce7361831419dede2`
- Markup SHA-256 after: `4d7e7cb36072895372ae849a2d4f78cf30052bc60bfafc432c2bf078248209c6`
- Revision IDs: `249, 250, 251`
- Backup: `/Volumes/MikesDataBackup/Research/KE02/Rev/revision/.kila-backups/KE02.rev.markup.20261009T153143671043.reviewer-2-comment-3.v2-part-20.docx`
- Paragraph properties preserved: `true`
- Run style source SHA-256: `c21d00426c037a67b0fba1fabff610e453e3a2a5424274c5287e40c65ce00d46`
- Formula verification: not applicable
- Endnote hyperlinks preserved: `true`
- Endnote hyperlink count: `0`
- Endnote hyperlink XML SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- Endnote relationships SHA-256: `absent`
- Before:

~~~~text
Positive passage trajectory observed; MMI is similar, PGA is lower, and the event outcomes are non-equivalent.
~~~~

- After:

~~~~text
Positive passage trajectory observed; MMI is similar, PGA and all three compared PSA estimates are lower in 2026, and the event outcomes are non-equivalent.
~~~~

- Minimal tracked fragments:
  1. `replace`
     - Before: "is"
     - After: "and all three compared PSA estimates are"
  2. `insert`
     - Before: ""
     - After: " in 2026"

### v2-part-21

- Location: Table 3; row 'Mashiki 2026 service-presence trajectory'; column 'Measurement dependence'
- Reason: Clarify Mashiki's measurement dependence without repeating model/grid limitations from Discussion.
- Kila decisions: KILA-D-20261009-001, KILA-D-20261009-002, KILA-D-20261009-003, KILA-D-20261009-004
- Mode: `replace`
- Revises prior parts: none
- Timestamp: 2026-10-09T06:31:44Z
- Author: Mike Li
- Markup SHA-256 before: `4d7e7cb36072895372ae849a2d4f78cf30052bc60bfafc432c2bf078248209c6`
- Markup SHA-256 after: `3047db9e8c140400c24ece472db41726890a2157defcc4dcf9339d531e36a105`
- Revision IDs: `252, 253, 254, 255, 256, 257, 258, 259, 260, 261`
- Backup: `/Volumes/MikesDataBackup/Research/KE02/Rev/revision/.kila-backups/KE02.rev.markup.20261009T153145676269.reviewer-2-comment-3.v2-part-21.docx`
- Paragraph properties preserved: `true`
- Run style source SHA-256: `c21d00426c037a67b0fba1fabff610e453e3a2a5424274c5287e40c65ce00d46`
- Formula verification: not applicable
- Endnote hyperlinks preserved: `true`
- Endnote hyperlink count: `0`
- Endnote hyperlink XML SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- Endnote relationships SHA-256: `absent`
- Before:

~~~~text
Yes—hazard ranking differs by metric; 2016 restrictions and 2026 probe passage measure different states.
~~~~

- After:

~~~~text
Yes—nearly unchanged MMI and lower peak and spectral acceleration support different descriptions of exposure; 2016 restrictions and 2026 probe passage measure different states.
~~~~

- Minimal tracked fragments:
  1. `replace`
     - Before: "hazard"
     - After: "nearly"
  2. `replace`
     - Before: "ranking"
     - After: "unchanged"
  3. `replace`
     - Before: "differs"
     - After: "MMI"
  4. `replace`
     - Before: "by"
     - After: "and"
  5. `replace`
     - Before: "metric"
     - After: "lower peak and spectral acceleration support different descriptions of exposure"

### v2-part-22

- Location: Table 3; row 'Yokoe faster restoration under stronger 2026 shaking'; column 'Claim'
- Reason: Narrow the table's claim label from overall shaking severity to observed restoration and selected estimates.
- Kila decisions: KILA-D-20261009-001, KILA-D-20261009-002, KILA-D-20261009-003, KILA-D-20261009-004
- Mode: `replace`
- Revises prior parts: none
- Timestamp: 2026-10-09T06:31:46Z
- Author: Mike Li
- Markup SHA-256 before: `3047db9e8c140400c24ece472db41726890a2157defcc4dcf9339d531e36a105`
- Markup SHA-256 after: `0df19572031e97e82ddeaf28b1d6f0a52f275f3b1af2999acbac6dcde8197231`
- Revision IDs: `262, 263, 264, 265, 266, 267, 268, 269, 270`
- Backup: `/Volumes/MikesDataBackup/Research/KE02/Rev/revision/.kila-backups/KE02.rev.markup.20261009T153147348886.reviewer-2-comment-3.v2-part-22.docx`
- Paragraph properties preserved: `true`
- Run style source SHA-256: `c21d00426c037a67b0fba1fabff610e453e3a2a5424274c5287e40c65ce00d46`
- Formula verification: not applicable
- Endnote hyperlinks preserved: `true`
- Endnote hyperlink count: `0`
- Endnote hyperlink XML SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- Endnote relationships SHA-256: `absent`
- Before:

~~~~text
Yokoe faster restoration under stronger 2026 shaking
~~~~

- After:

~~~~text
Yokoe faster same-asset restoration with higher compared ground-motion estimates
~~~~

- Minimal tracked fragments:
  1. `insert`
     - Before: ""
     - After: "same-asset "
  2. `replace`
     - Before: "under"
     - After: "with"
  3. `replace`
     - Before: "stronger"
     - After: "higher"
  4. `replace`
     - Before: "2026"
     - After: "compared"
  5. `replace`
     - Before: "shaking"
     - After: "ground-motion estimates"

### v2-part-23

- Location: Table 3; row 'Yokoe faster restoration under stronger 2026 shaking'; column 'Result'
- Reason: Give a concise summary of the supported result without another component-demand denial.
- Kila decisions: KILA-D-20261009-001, KILA-D-20261009-002, KILA-D-20261009-003, KILA-D-20261009-004
- Mode: `replace`
- Revises prior parts: none
- Timestamp: 2026-10-09T06:31:48Z
- Author: Mike Li
- Markup SHA-256 before: `0df19572031e97e82ddeaf28b1d6f0a52f275f3b1af2999acbac6dcde8197231`
- Markup SHA-256 after: `797620edd2059efd69e0ab58389501a2aa9579a6007e924b30a6257995e7c39a`
- Revision IDs: `271, 272, 273, 274, 275, 276, 277, 278, 279, 280, 281, 282, 283, 284, 285, 286`
- Backup: `/Volumes/MikesDataBackup/Research/KE02/Rev/revision/.kila-backups/KE02.rev.markup.20261009T153148998544.reviewer-2-comment-3.v2-part-23.docx`
- Paragraph properties preserved: `true`
- Run style source SHA-256: `c21d00426c037a67b0fba1fabff610e453e3a2a5424274c5287e40c65ce00d46`
- Formula verification: not applicable
- Endnote hyperlinks preserved: `true`
- Endnote hyperlink count: `0`
- Endnote hyperlink XML SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- Endnote relationships SHA-256: `absent`
- Before:

~~~~text
Faster in 2026 under both admissible endpoints; MMI and PGA both rank 2026 shaking as stronger.
~~~~

- After:

~~~~text
Faster in 2026 under both admissible endpoints; estimated MMI, PGA, and PSA at all three compared periods are higher.
~~~~

- Minimal tracked fragments:
  1. `insert`
     - Before: ""
     - After: "estimated "
  2. `insert`
     - Before: ""
     - After: ", PGA,"
  3. `replace`
     - Before: "PGA"
     - After: "PSA"
  4. `replace`
     - Before: "both"
     - After: "at"
  5. `replace`
     - Before: "rank"
     - After: "all"
  6. `replace`
     - Before: "2026"
     - After: "three"
  7. `replace`
     - Before: "shaking"
     - After: "compared"
  8. `replace`
     - Before: "as"
     - After: "periods"
  9. `replace`
     - Before: "stronger"
     - After: "are higher"

### v2-part-24

- Location: Table 3; row 'Yokoe faster restoration under stronger 2026 shaking'; column 'Inference ceiling'
- Reason: Retain an interpretable table boundary without enumerating multiple overlapping equivalence/severity prohibitions.
- Kila decisions: KILA-D-20261009-001, KILA-D-20261009-002, KILA-D-20261009-003, KILA-D-20261009-004
- Mode: `replace`
- Revises prior parts: none
- Timestamp: 2026-10-09T06:31:49Z
- Author: Mike Li
- Markup SHA-256 before: `797620edd2059efd69e0ab58389501a2aa9579a6007e924b30a6257995e7c39a`
- Markup SHA-256 after: `56229d8671e5312082a4026e6dea07c9cabc6af7a8e90b7fec32cca72fd8b1ee`
- Revision IDs: `287, 288, 289, 290, 291, 292, 293, 294, 295, 296`
- Backup: `/Volumes/MikesDataBackup/Research/KE02/Rev/revision/.kila-backups/KE02.rev.markup.20261009T153151070158.reviewer-2-comment-3.v2-part-24.docx`
- Paragraph properties preserved: `true`
- Run style source SHA-256: `c21d00426c037a67b0fba1fabff610e453e3a2a5424274c5287e40c65ce00d46`
- Formula verification: not applicable
- Endnote hyperlinks preserved: `true`
- Endnote hyperlink count: `0`
- Endnote hyperlink XML SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- Endnote relationships SHA-256: `absent`
- Before:

~~~~text
No causal reconstruction effect or inference that shaking intensity equals bridge damage severity.
~~~~

- After:

~~~~text
No causal reconstruction effect or validated comparison of component response.
~~~~

- Minimal tracked fragments:
  1. `replace`
     - Before: "inference"
     - After: "validated"
  2. `replace`
     - Before: "that"
     - After: "comparison"
  3. `replace`
     - Before: "shaking"
     - After: "of"
  4. `replace`
     - Before: "intensity"
     - After: "component"
  5. `replace`
     - Before: "equals bridge damage severity"
     - After: "response"

### v2-part-19-human-rows — observed saved native Word revisions

- Location: Table 2, immediately after Estimated PGA and before Outcome comparability.
- Operation: Human inserted the three approved PSA rows; agent did not perform the structural write.
- Kila decisions: KILA-D-20261009-004, KILA-D-20261009-005.
- Native revision author: Chao Li; row insertion revision IDs: 212, 219, 226. Native UTC timestamp (`w16du:dateUtc`): 2026-10-09T06:21:00Z; legacy `w:date` is not used to infer UTC here.
- Saved checkpoint SHA-256: `11b61add1dfc10d55205fdd8e9c5d12f07b3e561a9d64b7c5e9cc45ff0cb30f2`.
- Recoverable checkpoint: `Rev/revision/.kila-backups/KE02.rev.markup.20261009T153136540212.reviewer-2-comment-3.v2-part-19-cell-01.docx`.
- Prior agent checkpoint SHA-256, recorded historically before human save: `5b48177177627e5e3edaad6a874e2aa3a90837b3c253300c43f6ce61c77ce04f`. No agent-generated receipt for the human action is asserted.
- Before: These three rows were absent. After (Evidence dimension; Mashiki; Yokoe):
  - Estimated PSA, T = 0.3 s (g); 2.118 to 1.708 (ratio 0.806); 0.737 to 1.055 (ratio 1.432).
  - Estimated PSA, T = 1.0 s (g); 0.999 to 0.742 (ratio 0.743); 0.504 to 0.927 (ratio 1.838).
  - Estimated PSA, T = 3.0 s (g); 0.269 to 0.187 (ratio 0.695); 0.088 to 0.255 (ratio 2.909).
- Verification: True row/cell insertions; accepted clean equals the approved three-row contract; rejected-view original table is recoverable; original table properties and non-target content preserved. The four old cell patches were still absent in this human checkpoint and were subsequently implemented by the four separately logged bundled-writer parts above.
- Consolidated rendered clean Table 2: page 28, all rows fit without overflow. This observation record does not mark the reviewer comment done.

### v2-part-25-human-image — observed saved native Word revisions

- Location: Figure 2 image paragraph; no caption edit in this human operation.
- Operation: Human deleted the original image and inserted the approved-content 300 DPI export. Agent verified the saved object, not an alternative formal XML write.
- Kila decisions: KILA-D-20261009-004, KILA-D-20261009-005; the separate resolution export follows the human 300 DPI requirement.
- Native revision author: Chao Li; deleted-picture revision ID 196, inserted-picture revision ID 197. Native UTC timestamp (`w16du:dateUtc`): 2026-10-09T06:25:00Z.
- Saved checkpoint and recoverable backup: same human checkpoint as the immediately preceding human-row record.
- Original image SHA-256: `7bf216aa938875fb25496ed500f36e562ac27d3cbb113354132c2d6d62754b0c`.
- Replacement asset: `data/results/figures/revision/Figure_2_yokoe_restoration_300dpi.png`, SHA-256 `4bcb00d524d288e57752d65b00246c2bc34abdedf6811e0d88130ad0e8f40821`; 4300 x 1463 pixels, metadata 299.9994 DPI.
- Content change: Remove only the unsupported "2026 stronger:" prefix from the panel-b annotation; restoration values, ratios, axes, other labels, colors and scientific meaning remain as approved. The 300 DPI export is a native re-render of that replacement, not new evidence.
- Drawing checks: Original width 5486400 EMU (15.24 cm) retained; inline placement and empty alt text retained. Height changes from 1865376 to 1866265 EMU: +889 EMU / +0.024694 mm proportional rounding, not an intentionally larger figure. Other three figures match their original hashes.
- Verification: Accepted clean contains only the replacement; rejected-view original image is recoverable. Markup page 24 displays the old image with deletion marking and the new inserted image. Clean page 24 displays the replacement alone.
- Outstanding visual finding: Final-width lettering remains approximately 3–4 pt despite 300 DPI. A typography/layout re-edit would overlap this recorded part and requires supplemental human confirmation. No tool-extension approval, final visual adequacy, response approval or submission readiness is inferred.

### v2-part-25-human-print-reedit — observed saved native Word typography update

- Location: Same Figure 2 image as `v2-part-25-human-image`; this is a controlled re-edit, not an additional manuscript location.
- Operation: Following explicit human approval of the typography/layout adjustment, the human saves the replacement in Word. Agent performs read-only object verification and accepts a separate copy for clean review; no formal markup object/XML write by agent.
- Scientific decisions: KILA-D-20261009-001 through KILA-D-20261009-005 remain applicable. No new research-decision record for this formatting-only action; no response approval inferred.
- Prior formal markup SHA-256: `56229d8671e5312082a4026e6dea07c9cabc6af7a8e90b7fec32cca72fd8b1ee`. Current saved markup SHA-256: `2492c185b31e7a70a529ef5c8d483fe70e82ea075aa47ae71d7eea8301ec7f00`.
- Recoverable current markup: `Rev/revision/.kila-backups/KE02.rev.markup.20261009-figure2-print-human-saved.docx`. Prior accepted image remains in `Rev/revision/.kila-backups/KE02.rev.clean.20261009-pre-figure2-print.docx` and the retained prior 300 DPI asset.
- Replacement asset: `data/results/figures/revision/Figure_2_yokoe_restoration_print_300dpi.png`, SHA-256 `8112965139c5c0e419ed46c62db398b13f6168725a1810ea4640eb72869e4f68`; 1800 x 1440 pixels, PNG metadata 299.9994 DPI, nominal minimum lettering 8.5 pt at 15.24 cm width.
- Native revision evidence: Original-image deletion ID 196 remains; existing inserted-image revision ID 197 contains the new asset. Author Chao Li; current insertion `w16du:dateUtc` 2026-10-09T07:38:00Z. Do not interpret the local-time-valued legacy `w:date` as UTC. Native Word reserializes some unrelated paragraph-mark revision IDs; this is not claimed as an additional agent edit.
- Drawing dimensions: Width 5486400 EMU (15.24 cm), height 4381500 EMU (12.170833 cm). Actual height is 0.211667 mm below the 12.192 cm design; lettering difference is below 0.02 pt. Inline placement and empty alt text retained. No claim of exact proportional geometry.
- Content: Original panels a/b now stack vertically; lettering is enlarged, and the rightmost time annotation moves left of its unchanged point. Values, intervals, scales, limits, labels and colors remain unchanged; the previously approved removal of the unsupported stronger-shaking prefix is retained.
- Verification: All 25 approved content contracts pass; all 49 OMML objects and 52 field-code nodes match original; non-target text/tables and other three figures remain protected. Rejected-view original manuscript/table/image content is recoverable.
- Clean provenance: `Rev/revision/KE02.rev.clean.docx`, SHA-256 `1c5c272d81bb8023565489b6b6fbc19b14d1e8ecc623500327cd3c7fcecde17c`, generated once from the current saved markup through the bundled acceptance helper.
- Current visual review: Both renders have 32 pages. In each render, 31 pages are pixel-identical to the preceding individually reviewed pages; current page 24 is individually inspected and passes. Clean Figure 2 lettering, plotted marks, axes and caption are complete and readable at final size; markup shows the deleted original and inserted new image without overlap or overflow. Current Tables 1–3 pages 27–29 are additionally rechecked. Evidence: `Rev/docs/qa/R2C3-v2-print/response-evidence.json` and `verification.json`.
- Comment status: Manuscript review passes for the approved bounded comparison. The response still requires human review; no reviewer comment is marked done by this observation.

## reviewer-1/comment-1

### part-02

- Location: Results > Yokoe Bridge Reopened Faster after the Second Shock; opening paragraph
- Reason: Make the observed later damage and repair explicit rather than imply faster reopening means absence of damage.
- Kila decisions: KILA-D-20261009-007, KILA-D-20261009-008, KILA-D-20261009-009
- Mode: `replace`
- Revises prior parts: none
- Timestamp: 2026-10-09T11:50:37Z
- Author: Mike Li
- Markup SHA-256 before: `2492c185b31e7a70a529ef5c8d483fe70e82ea075aa47ae71d7eea8301ec7f00`
- Markup SHA-256 after: `f8db82d625217e654085ae84bfaa9628a1af8e54b4b31f96a019726a2e45fddf`
- Revision IDs: `297`
- Backup: `Rev/revision/.kila-backups/KE02.rev.markup.20261009T205042373467.reviewer-1-comment-1.part-02.docx`
- Paragraph properties preserved: `true`
- Run style source SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- Formula verification: not applicable
- Endnote hyperlinks preserved: `true`
- Endnote hyperlink count: `0`
- Endnote hyperlink XML SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- Endnote relationships SHA-256: `absent`
- Before:

~~~~text
Yokoe provides the strongest within-asset comparison because the same physical bridge appears in official damage and restoration records for both earthquakes.
~~~~

- After:

~~~~text
Yokoe provides the strongest within-asset comparison because the same physical bridge appears in official damage and restoration records for both earthquakes. The official 2026 restoration release documents pier settlement and an abutment joint level difference, with settlement countermeasures and joint repairs in progress.
~~~~

- Minimal tracked fragments:
  1. `insert`
     - Before: ""
     - After: " The official 2026 restoration release documents pier settlement and an abutment joint level difference, with settlement countermeasures and joint repairs in progress."

### part-03

- Location: Discussion > Structural and Capacity Pathways Produce Asymmetric Evidence; opening sentence
- Reason: Compare the specific engineering design target with the operational finding, using one necessary compliance boundary rather than general repeated disclaimers.
- Kila decisions: KILA-D-20261009-007, KILA-D-20261009-008, KILA-D-20261009-009
- Mode: `replace`
- Revises prior parts: none
- Timestamp: 2026-10-09T11:51:21Z
- Author: Mike Li
- Markup SHA-256 before: `f8db82d625217e654085ae84bfaa9628a1af8e54b4b31f96a019726a2e45fddf`
- Markup SHA-256 after: `84957293c64ae93f726c31e8ac0a0d5daccf79c0225bba4f22b8e79d7eb27758`
- Revision IDs: `298`
- Backup: `Rev/revision/.kila-backups/KE02.rev.markup.20261009T205125902684.reviewer-1-comment-1.part-03.docx`
- Paragraph properties preserved: `true`
- Run style source SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- Formula verification: not applicable
- Endnote hyperlinks preserved: `true`
- Endnote hyperlink count: `0`
- Endnote hyperlink XML SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- Endnote relationships SHA-256: `absent`
- Before:

~~~~text
The structural pathway supports the stronger conclusion because Yokoe maintains physical identity and operational endpoint comparability across events.
~~~~

- After:

~~~~text
The structural pathway supports the stronger conclusion because Yokoe maintains physical identity and operational endpoint comparability across events. The reconstruction targets P3 foundation performance under Level 2 ground motion. Repairs are still necessary in 2026, but traffic returns much sooner; this demonstrates faster operational restoration rather than verified attainment of the P3 design target.
~~~~

- Minimal tracked fragments:
  1. `insert`
     - Before: ""
     - After: " The reconstruction targets P3 foundation performance under Level 2 ground motion. Repairs are still necessary in 2026, but traffic returns much sooner; this demonstrates faster operational restoration rather than verified attainment of the P3 design target."

### part-04

- Location: Discussion > From Asset Performance to Urban Resilience Learning; paragraph beginning 'Linking historical hazard events'
- Reason: Replace unmeasured asset-integrity, repairability and operational-tolerance claims with the evidence actually assessed.
- Kila decisions: KILA-D-20261009-007, KILA-D-20261009-008, KILA-D-20261009-009
- Mode: `replace`
- Revises prior parts: none
- Timestamp: 2026-10-09T11:54:29Z
- Author: Mike Li
- Markup SHA-256 before: `84957293c64ae93f726c31e8ac0a0d5daccf79c0225bba4f22b8e79d7eb27758`
- Markup SHA-256 after: `152a430408527e0f4ca93aa0f5f4b19189d53db883dcc76e3016aec4e26089c8`
- Revision IDs: `299, 300, 301, 302, 303, 304, 305, 306, 307, 308, 309, 310`
- Backup: `Rev/revision/.kila-backups/KE02.rev.markup.20261009T205436027495.reviewer-1-comment-1.part-04.docx`
- Paragraph properties preserved: `true`
- Run style source SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- Formula verification: not applicable
- Endnote hyperlinks preserved: `true`
- Endnote hyperlink count: `0`
- Endnote hyperlink XML SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- Endnote relationships SHA-256: `absent`
- Before:

~~~~text
In this audit, structural reconstruction is evaluated through asset integrity, repairability, and reopening, whereas corridor-capacity expansion is evaluated through route space, observed passage, and operational tolerance.
~~~~

- After:

~~~~text
In this audit, structural reconstruction is evaluated through documented damage, repair work, and matched reopening endpoints, whereas corridor-capacity expansion is evaluated through the expanded route space and observed passage.
~~~~

- Minimal tracked fragments:
  1. `replace`
     - Before: "asset"
     - After: "documented"
  2. `replace`
     - Before: "integrity"
     - After: "damage"
  3. `replace`
     - Before: "repairability"
     - After: "repair work"
  4. `insert`
     - Before: ""
     - After: "matched "
  5. `insert`
     - Before: ""
     - After: " endpoints"
  6. `insert`
     - Before: ""
     - After: "the expanded "
  7. `replace`
     - Before: ","
     - After: " and"
  8. `delete`
     - Before: ", and operational tolerance"
     - After: ""

### part-05

- Location: Table 2 > Documented intervention > Yokoe Bridge
- Reason: Clarify the targeted reconstruction scope in the comparison table without adding rows or changing numerical results.
- Kila decisions: KILA-D-20261009-007, KILA-D-20261009-008, KILA-D-20261009-009
- Mode: `replace`
- Revises prior parts: none
- Timestamp: 2026-10-09T11:55:00Z
- Author: Mike Li
- Markup SHA-256 before: `152a430408527e0f4ca93aa0f5f4b19189d53db883dcc76e3016aec4e26089c8`
- Markup SHA-256 after: `f74b95d4c6e2d15d8d785120b5893776f787b0dbaa955f903489891801dfd2eb`
- Revision IDs: `311, 312, 313, 314, 315, 316, 317, 318, 319, 320, 321, 322, 323, 324, 325, 326`
- Backup: `Rev/revision/.kila-backups/KE02.rev.markup.20261009T205504761399.reviewer-1-comment-1.part-05.docx`
- Paragraph properties preserved: `true`
- Run style source SHA-256: `c21d00426c037a67b0fba1fabff610e453e3a2a5424274c5287e40c65ce00d46`
- Formula verification: not applicable
- Endnote hyperlinks preserved: `true`
- Endnote hyperlink count: `0`
- Endnote hyperlink XML SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- Endnote relationships SHA-256: `absent`
- Before:

~~~~text
Reconstruction of the same bridge after 2016 damage
~~~~

- After:

~~~~text
P3 reconstruction for Level 2 ground motion; retained components repaired
~~~~

- Minimal tracked fragments:
  1. `replace`
     - Before: "Reconstruction"
     - After: "P3"
  2. `replace`
     - Before: "of"
     - After: "reconstruction"
  3. `replace`
     - Before: "the"
     - After: "for"
  4. `replace`
     - Before: "same"
     - After: "Level"
  5. `replace`
     - Before: "bridge"
     - After: "2"
  6. `replace`
     - Before: "after"
     - After: "ground"
  7. `replace`
     - Before: "2016"
     - After: "motion;"
  8. `replace`
     - Before: "damage"
     - After: "retained components repaired"

### part-01-human-methods — observed approved human save

- Location: Methods > Earthquake Episodes and Adaptation Chronology; paragraph beginning 'Temporal validity requires'.
- Operation: Human appends the four approved engineering-context sentences; agent does not write Word in this observation.
- Kila decisions: KILA-D-20261009-007, KILA-D-20261009-008, KILA-D-20261009-009.
- Prior agent checkpoint SHA-256: `f74b95d4c6e2d15d8d785120b5893776f787b0dbaa955f903489891801dfd2eb`; saved human checkpoint SHA-256: `0884e13c80f1e2d960de06ed829392f54a244656b4bf4ffa122f97abfa5ae48b`. These are checkpoints around the combined human Methods/citation save, not independent per-part writes.
- Recoverable human checkpoint: `Rev/revision/.kila-backups/KE02.rev.markup.20261009T221540Z.R1C1-human-saved-readonly.docx`.
- Evidence: `Rev/docs/qa/R1C1-v1-saved/saved-check.json`; accepted clean SHA-256 `b6bf63a6dd30e8dac1c3f5f2a97f2fdcd93b483c52299f2233d5960bf9f4fa62`. Native revision-ID attribution is not asserted by this observation; the package-level tracked-wrapper, formula and source-immutability checks are recorded in that receipt.
- Before (complete approved target span; historical prior clean confirms the retained sentence):

~~~~text
This rule prevents incomplete or merely planned works from being interpreted as tested adaptations.
~~~~

- After (complete target span in the current clean, including human citation displays):

~~~~text
This rule prevents incomplete or merely planned works from being interpreted as tested adaptations. Kumamoto Prefecture's bridge-restoration report identifies Yokoe as a 200 m long, 8 m wide steel girder-and-truss bridge completed in 1979 under the 1972 Specifications for Highway Bridges. It attributes the 2016 P3 foundation failure and approximately 2.5 m settlement to liquefaction and reduced lateral ground resistance. Reconstruction uses a PC-well foundation at P3 designed for Level 2 ground motion, with repairs to retained superstructure and bearings 33. At Mashiki, the two-to-four-lane widening aims to improve traffic flow, pedestrian safety and disaster-prevention function after collapsed buildings blocked the earlier road 34.
~~~~

- Minimal change: Retain the original sentence and append four sentences. Citation fields 33/34 belong to the separately approved human part-06.
- Verification: Exact approved prose confirmed after omitting only the adjacent citation displays; surrounding Methods text, native math, media and table structure match the comparison contract. Clean page 15 lines 312-319 contains the added passage. This is one manuscript location, not four sentence locations.

### part-06-human-citations — observed approved human save

- Locations: Citation fields within the already counted Methods and Results paragraphs; three bibliography paragraphs, currently references 18, 33 and 34.
- Operation: Human inserts the three approved official-source citation fields and updates bibliography/automatic numbering through the existing Word citation manager. Agent does not modify fields, library records or bibliography.
- Kila decisions: KILA-D-20261009-007, KILA-D-20261009-008, KILA-D-20261009-009.
- Checkpoints and recoverable saved source: Same combined human checkpoint as part-01-human-methods above; no fictitious separate agent write or native revision IDs are attributed.
- Before: These three approved source fields and source-specific bibliography paragraphs are absent from the prior clean. The Results addition was already written by machine part-02 before the human save, without its source field; the Methods anchor sentences are added in human part-01. Reference 18 previously labels the Zhu/Xu/Wang redundancy-design paper, which is retained under automatic renumbering; the number alone is not source identity.
- After (complete citation-anchor sentences, displays and source metadata):

~~~~text
Reconstruction uses a PC-well foundation at P3 designed for Level 2 ground motion, with repairs to retained superstructure and bearings 33.
~~~~

  - R1C1-S1: display 33; EndNote record 3701; title: Summary of bridge disaster restoration based on experience from the Kumamoto earthquake (restoration construction works) [in Japanese]; year: 2021; URL: https://www.pref.kumamoto.jp/uploaded/attachment/134518.PDF; reference type: Report.

~~~~text
The official 2026 restoration release documents pier settlement and an abutment joint level difference, with settlement countermeasures and joint repairs in progress 18.
~~~~

  - R1C1-S2: display 18; EndNote record 3702; title: Four major arterial routes between Uki and Yatsushiro become passable 20 days after the 2026 Kumamoto earthquake [in Japanese]; year: 2026; URL: https://www.qsr.mlit.go.jp/content/000002804.pdf; reference type: Report.

~~~~text
At Mashiki, the two-to-four-lane widening aims to improve traffic flow, pedestrian safety and disaster-prevention function after collapsed buildings blocked the earlier road 34.
~~~~

  - R1C1-S3: display 34; EndNote record 3703; title: Governor's regular press conference of 13 February 2026 [in Japanese]; year: 2026; URL: https://www.pref.kumamoto.jp/site/chiji/259353.html; reference type: Journal Article.

- After (complete three source-specific bibliography paragraphs):

~~~~text
18Kyushu Regional Development Bureau, Kumamoto Prefecture & Nexco West. Four major arterial routes between Uki and Yatsushiro become passable 20 days after the 2026 Kumamoto earthquake [in Japanese]. (Kyushu Regional Development Bureau, 2026).
33Kumamoto Prefecture. Summary of bridge disaster restoration based on experience from the Kumamoto earthquake (restoration construction works) [in Japanese]. (Kumamoto Prefecture, 2021).
34Kumamoto Prefecture. Governor's regular press conference of 13 February 2026 [in Japanese].  (2026).
~~~~

- Verification: All three fields immediately adjoin the intended approved anchor and contain the correct source title/year/URL. Reference 18 is on clean page 31; references 33-34 are on page 32. Existing sources and non-target prose remain under the authorized automatic-renumbering comparison; no EndNote hyperlink deletion is asserted or performed.
- Remaining formatting issue: Record 3703 is typed Journal Article and reference 34 omits the visible web URL. On 10 October 2026 the human defers this non-substantive formatting correction; retain it for final bibliography QA before submission. The issue is not fixed or erased and does not change the selected source, engineering facts or response position.
- Response-location inventory: Five prose/table locations (parts 01-05) plus three bibliography paragraphs = eight distinct locations. Co-located citation fields do not duplicate the Methods/Results locations. Use five exact quotations under the response skill's 6-10-location rule; this bookkeeping remains internal. The response is pending human review, not comment completion.

## reviewer-2/comment-5

### part-01

- Location: Methods > Case-Selection and Geometry Gates; first sentence of paragraph beginning 'We define the selection denominator'
- Reason: Clarify source-entry counting and the deliberate exact same-asset overlap without redefining the 65-row denominator.
- Kila decisions: KILA-D-20261010-002
- Mode: `replace`
- Revises prior parts: none
- Timestamp: 2026-10-09T23:29:58Z
- Author: Kila
- Markup SHA-256 before: `0884e13c80f1e2d960de06ed829392f54a244656b4bf4ffa122f97abfa5ae48b`
- Markup SHA-256 after: `fa9fc3ed3c407fe512ecf122aa40104c8d00aa8fc6daec7edf482840608d5ed5`
- Revision IDs: `333`
- Backup: `Rev/revision/.kila-backups/KE02.rev.markup.20261010T083000711107.reviewer-2-comment-5.part-01.docx`
- Paragraph properties preserved: `true`
- Run style source SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- Formula verification: not applicable
- Endnote hyperlinks preserved: `true`
- Endnote hyperlink count: `0`
- Endnote hyperlink XML SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- Endnote relationships SHA-256: `absent`
- Before:

~~~~text
We define the selection denominator before evaluating outcomes and compute gate-specific counts within each candidate universe.
~~~~

- After:

~~~~text
We define the selection denominator before evaluating outcomes and compute gate-specific counts within each candidate universe. Each candidate is a source-specific screening entry, not necessarily a distinct physical asset. Yokoe appears once in the restored-bridge inventory and once in the later damage register; these two entries map to one bridge.
~~~~

- Minimal tracked fragments:
  1. `insert`
     - Before: ""
     - After: " Each candidate is a source-specific screening entry, not necessarily a distinct physical asset. Yokoe appears once in the restored-bridge inventory and once in the later damage register; these two entries map to one bridge."

### part-02

- Location: Methods > Reproducibility; first sentence
- Reason: State the actual generation and deduplication rules instead of relying on a generic deterministic-code claim; identify the supplementary set as explicitly enumerated, not a regional census.
- Kila decisions: KILA-D-20261010-002
- Mode: `replace`
- Revises prior parts: none
- Timestamp: 2026-10-09T23:30:09Z
- Author: Kila
- Markup SHA-256 before: `fa9fc3ed3c407fe512ecf122aa40104c8d00aa8fc6daec7edf482840608d5ed5`
- Markup SHA-256 after: `9250f05398f3ec40089c5700ab027b70498d4742aa4d8600641744efe52e0b39`
- Revision IDs: `334`
- Backup: `Rev/revision/.kila-backups/KE02.rev.markup.20261010T083011313904.reviewer-2-comment-5.part-02.docx`
- Paragraph properties preserved: `true`
- Run style source SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- Formula verification: not applicable
- Endnote hyperlinks preserved: `true`
- Endnote hyperlink count: `0`
- Endnote hyperlink XML SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- Endnote relationships SHA-256: `absent`
- Before:

~~~~text
All analytical products are generated from versioned raw and processed data using deterministic preprocessing and output scripts.
~~~~

- After:

~~~~text
All analytical products are generated from versioned raw and processed data using deterministic preprocessing and output scripts. Candidate generation links 20 locally documented road-project entries to official road features and retains 12 entries with a match and a reported work-completion date before the later event. The bridge inventory contains 37 entries transcribed from the prefectural restoration report. Filtering the later restriction snapshots for bridge-related reasons and deduplicating by normalized route, start location and end location yields 13 records. Three explicitly listed reconstruction candidates form the supplementary screening set.
~~~~

- Minimal tracked fragments:
  1. `insert`
     - Before: ""
     - After: " Candidate generation links 20 locally documented road-project entries to official road features and retains 12 entries with a match and a reported work-completion date before the later event. The bridge inventory contains 37 entries transcribed from the prefectural restoration report. Filtering the later restriction snapshots for bridge-related reasons and deduplicating by normalized route, start location and end location yields 13 records. Three explicitly listed reconstruction candidates form the supplementary screening set."

### part-03

- Location: Figure 4 caption note; first sentence
- Reason: Include both Mashiki nested stages and Yokoe cross-source duplicate representation in the existing caption.
- Kila decisions: KILA-D-20261010-002
- Mode: `replace`
- Revises prior parts: none
- Timestamp: 2026-10-09T23:30:19Z
- Author: Kila
- Markup SHA-256 before: `9250f05398f3ec40089c5700ab027b70498d4742aa4d8600641744efe52e0b39`
- Markup SHA-256 after: `65d7facfb0daa27155228261e0f12bce01fc92194c909924201688e26a4e0137`
- Revision IDs: `335`
- Backup: `Rev/revision/.kila-backups/KE02.rev.markup.20261010T083021866299.reviewer-2-comment-5.part-03.docx`
- Paragraph properties preserved: `true`
- Run style source SHA-256: `c21d00426c037a67b0fba1fabff610e453e3a2a5424274c5287e40c65ce00d46`
- Formula verification: not applicable
- Endnote hyperlinks preserved: `true`
- Endnote hyperlink count: `0`
- Endnote hyperlink XML SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- Endnote relationships SHA-256: `absent`
- Before:

~~~~text
Panel a reports screened and gate-passing records for four official candidate universes before collapsing nested records to two physical cases.
~~~~

- After:

~~~~text
Panel a reports screened and gate-passing records for four official candidate universes before collapsing nested and cross-source records to two physical cases.
~~~~

- Minimal tracked fragments:
  1. `insert`
     - Before: ""
     - After: "and cross-source "

## reviewer-2/comment-4

### part-01

- Location: Methods > Mashiki Corridor Service-Presence Analysis; paragraph beginning 'The Mashiki event-state layer retains'
- Reason: Define the geometric numerator and denominator, state the physical allowance implied by 0.80 without inventing calibration, and identify the bounded alternative cutoffs.
- Kila decisions: KILA-D-20261010-004, KILA-D-20261010-005
- Mode: `replace`
- Revises prior parts: none
- Timestamp: 2026-10-10T00:07:51Z
- Author: Kila
- Markup SHA-256 before: `65d7facfb0daa27155228261e0f12bce01fc92194c909924201688e26a4e0137`
- Markup SHA-256 after: `ad20a02580800a6f73966b87cb8e6ece4b134231489fdefa90f3d6a4a5280be5`
- Revision IDs: `336`
- Backup: `Rev/revision/.kila-backups/KE02.rev.markup.20261010T090753771498.reviewer-2-comment-4.part-01.docx`
- Paragraph properties preserved: `true`
- Run style source SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- Formula verification: not applicable
- Endnote hyperlinks preserved: `true`
- Endnote hyperlink count: `0`
- Endnote hyperlink XML SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- Endnote relationships SHA-256: `absent`
- Before:

~~~~text
For each later snapshot, we record layer availability, observed corridor passage, unique corridor traces, longitudinal coverage, elapsed time, and the interpretation of the time bound.
~~~~

- After:

~~~~text
For each later snapshot, we record layer availability, observed corridor passage, unique corridor traces, longitudinal coverage, elapsed time, and the interpretation of the time bound. Longitudinal coverage is the union length of selected trace intervals on the polygon's longitudinal axis divided by its projected span, capped at one. The 0.80 cutoff permits up to 20% of this span to remain unrepresented; it is a descriptive classification, not a calibrated lane-availability or capacity threshold. Cutoff sensitivity uses 0.70, 0.80 and 0.90 with trace extraction held fixed.
~~~~

- Minimal tracked fragments:
  1. `insert`
     - Before: ""
     - After: " Longitudinal coverage is the union length of selected trace intervals on the polygon's longitudinal axis divided by its projected span, capped at one. The 0.80 cutoff permits up to 20% of this span to remain unrepresented; it is a descriptive classification, not a calibrated lane-availability or capacity threshold. Cutoff sensitivity uses 0.70, 0.80 and 0.90 with trace extraction held fixed."

### part-02

- Location: Results > Mashiki Central Line; paragraph beginning 'Mashiki links a capacity-expansion corridor'
- Reason: Report both the frequency change under the stricter cutoff and the unchanged first-observation bound, rather than claiming every result is invariant.
- Kila decisions: KILA-D-20261010-004, KILA-D-20261010-005
- Mode: `replace`
- Revises prior parts: none
- Timestamp: 2026-10-10T00:25:10Z
- Author: Kila
- Markup SHA-256 before: `ad20a02580800a6f73966b87cb8e6ece4b134231489fdefa90f3d6a4a5280be5`
- Markup SHA-256 after: `db4c84a86eb81e6d74b293e5f5756f27a635d5cc6f8f5dc0b996873045b6005b`
- Revision IDs: `337`
- Backup: `Rev/revision/.kila-backups/KE02.rev.markup.20261010T092512883995.reviewer-2-comment-4.part-02.docx`
- Paragraph properties preserved: `true`
- Run style source SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- Formula verification: not applicable
- Endnote hyperlinks preserved: `true`
- Endnote hyperlink count: `0`
- Endnote hyperlink XML SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- Endnote relationships SHA-256: `absent`
- Before:

~~~~text
The first near-full positive observation occurs no later than 43.55 hours after the earthquake origin.
~~~~

- After:

~~~~text
The first near-full positive observation occurs no later than 43.55 hours after the earthquake origin. Cutoffs of 0.70, 0.80 and 0.90 yield 19, 19 and 17 qualifying snapshots out of 21 (90.5%, 90.5% and 81.0%), respectively, with the same 43.55-hour first-observation bound.
~~~~

- Minimal tracked fragments:
  1. `insert`
     - Before: ""
     - After: " Cutoffs of 0.70, 0.80 and 0.90 yield 19, 19 and 17 qualifying snapshots out of 21 (90.5%, 90.5% and 81.0%), respectively, with the same 43.55-hour first-observation bound."

## reviewer-1/comment-2

### part-01

- Location: Discussion > Inference Limits and Transferability; paragraph beginning 'The principal identification limit is the absence of a credible counterfactual.'
- Reason: Address M7.5, case-specific adverse damage and blockage, and further shocks during recovery, explaining how operational inferences might change without quantitative predictions.
- Kila decisions: KILA-D-20261010-007, KILA-D-20261010-008
- Mode: `replace`
- Revises prior parts: none
- Timestamp: 2026-10-10T01:08:32Z
- Author: Kila
- Markup SHA-256 before: `db4c84a86eb81e6d74b293e5f5756f27a635d5cc6f8f5dc0b996873045b6005b`
- Markup SHA-256 after: `0517242829a22cd646b235fce5542fec7efbd956ed6e985877309c66bc7a9c2d`
- Revision IDs: `338`
- Backup: `Rev/revision/.kila-backups/KE02.rev.markup.20261010T100834244514.reviewer-1-comment-2.part-01.docx`
- Paragraph properties preserved: `true`
- Run style source SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- Formula verification: not applicable
- Endnote hyperlinks preserved: `true`
- Endnote hyperlink count: `0`
- Endnote hyperlink XML SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- Endnote relationships SHA-256: `absent`
- Before:

~~~~text
The two cases demonstrate an audit logic, not prevalence across assets or cities.
~~~~

- After:

~~~~text
The two cases demonstrate an audit logic, not prevalence across assets or cities. A hypothetical M7.5 event does not by itself specify demand at either asset; rupture geometry, distance and site conditions also matter. At Yokoe, stronger component-relevant shaking or greater ground deformation could cause extensive foundation or retained-component damage, increasing repair needs and weakening or reversing the reopening contrast. At Mashiki, debris or ground damage blocking the available carriageways or their connections could interrupt passage despite widening. Further strong shocks before inspection and repair are complete could compound damage or renew closures in either case. These downward counterfactuals identify conditions under which the observed restoration and passage findings may cease to transfer; they do not estimate outcomes under an alternative sequence.
~~~~

- Minimal tracked fragments:
  1. `insert`
     - Before: ""
     - After: " A hypothetical M7.5 event does not by itself specify demand at either asset; rupture geometry, distance and site conditions also matter. At Yokoe, stronger component-relevant shaking or greater ground deformation could cause extensive foundation or retained-component damage, increasing repair needs and weakening or reversing the reopening contrast. At Mashiki, debris or ground damage blocking the available carriageways or their connections could interrupt passage despite widening. Further strong shocks before inspection and repair are complete could compound damage or renew closures in either case. These downward counterfactuals identify conditions under which the observed restoration and passage findings may cease to transfer; they do not estimate outcomes under an alternative sequence."
