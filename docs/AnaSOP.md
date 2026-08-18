# Analysis SOP

## 1. Research Objective

### Central Research Question

- Research type: applied
- Research question: Among road segments and communities exposed to comparable 2026 ground shaking, is stronger 2016 earthquake exposure and the resilience legacy accumulated during 2016-2026 associated with less severe transport disruption and faster restoration after the 2026 earthquake?
- Why it matters: A repeated earthquake in the same urban region creates a rare opportunity to test whether disaster experience, institutional learning, and completed resilience investment translate into observable performance when infrastructure is stressed again.
- Data support currently visible: Official shaking surfaces exist for both earthquake sequences; a versioned 2026 road-state time series and pilot road/building networks have been acquired. A spatially and temporally linkable 2016 road-restoration record and a 2016-2026 intervention ledger remain the principal missing inputs.
- Candidate constructs, subject to feasibility confirmation: 2016 Shaking Exposure, 2026 Shaking Intensity, Documented Resilience Intervention, 2026 Road Disruption, Road Restoration Time, Community Isolation Duration, and Critical Facility Access Loss.
- What would verify it: On a defensible common-support sample, previously exposed or demonstrably upgraded locations show shorter disruption or restoration duration after conditioning on 2026 hazard, baseline network structure, terrain, and settlement characteristics; the relationship remains directionally stable across exposure, restoration, and missing-data definitions.
- What would falsify or weaken it: The necessary records cannot be linked in space and time; exposed and comparison locations lack common hazard support; restoration timestamps are too incomplete; or the estimated resilience difference disappears under reasonable adjustment and sensitivity checks.
- Required next feasibility check: Construct inventories of official 2016/2026 road disruption records and 2016-2026 completed interventions, then test temporal precision, spatial linkage, common support, and outcome completeness before choosing an estimator.

### Supporting Research Questions

#### Supporting Point 1: Intervention mechanism

- Research question: Do documented road, bridge, land-readjustment, evacuation, and critical-facility interventions completed after 2016 explain part of the association between prior earthquake exposure and 2026 restoration performance?
- Why it matters: It separates a generic experience legacy from observable physical or organizational investment that cities can replicate.
- Data support currently visible: Project categories and official post-2016 recovery documents are identifiable, but a geocoded completion-date and expenditure ledger has not yet been assembled.
- What would verify it: Completed and spatially relevant interventions predict lower disruption or faster restoration, with temporal ordering established before the 2026 event.
- What would falsify or weaken it: Project locations or completion dates cannot be recovered, or intervention associations vanish after conditioning on hazard and baseline network characteristics.
- Required feasibility check: Recover stable project identifiers, geometry, start/completion dates, type, and cost or intensity from official national, prefectural, and municipal records.

#### Supporting Point 2: Network and service mechanism

- Research question: Did the 2016-2026 resilience legacy preserve access to hospitals, shelters, emergency routes, and municipal centres by reducing network fragmentation and community isolation in 2026?
- Why it matters: Network accessibility is closer to lived urban resilience than building-level image change and connects infrastructure performance to essential services.
- Data support currently visible: A 2026 road-state series and partial road and critical-facility layers are available; stable baseline networks and facility identifiers require completion.
- What would verify it: Previously exposed or upgraded areas experience smaller increases in travel time, fewer disconnected communities, or shorter isolation duration under comparable 2026 shaking.
- What would falsify or weaken it: Road observations cannot be converted into time-varying passability, or facility and community access outcomes are insensitive to observed disruptions.
- Required feasibility check: Test whether road-state snapshots can be linked to stable segments and whether closures generate measurable changes in facility access and component connectivity.

#### Supporting Point 3: Spatial inequality and heterogeneity

- Research question: Is any resilience legacy weaker in peripheral, topographically constrained, ageing, or poorly connected communities than in central and redundant parts of the urban network?
- Why it matters: Average recovery can conceal unequal protection and persistent isolation risks that are central to urban policy.
- Data support currently visible: Terrain, administrative geography, road geometry, and critical facilities are partly available; population and comparable baseline socioeconomic measures still require a linkage audit.
- What would verify it: Restoration or access benefits vary systematically with baseline remoteness, network redundancy, terrain, or demographic vulnerability, with adequate observations in each subgroup.
- What would falsify or weaken it: Subgroup support is sparse, measures are temporally inconsistent, or heterogeneity estimates are dominated by a few locations.
- Required feasibility check: Audit stable small-area population, age structure, terrain, and network-centrality coverage for both events.

#### Supporting Point 4: Robustness and evidence boundaries

- Research question: How sensitive are the repeated-shock findings to alternative shaking measures, restoration endpoints, intervention definitions, censoring rules, missing road observations, and the exclusion of unsupported building-reconstruction proxies?
- Why it matters: The current pilot shows that outcome definition and measurement error can dominate apparent results.
- Data support currently visible: Multiple shaking measures, versioned 2026 road snapshots, and explicit failed building-level measurement gates permit transparent sensitivity analysis.
- What would verify it: The central direction survives prespecified alternative definitions, common-support restrictions, and plausible measurement-error scenarios.
- What would falsify or weaken it: Sign, magnitude, or substantive interpretation changes across reasonable definitions, or results depend on failed individualized building probabilities.
- Required feasibility check: Predefine the admissible exposure, outcome, treatment, censoring, and missingness scenarios before estimation.

### Scope of Analysis

- Geographic scope: Kumamoto Prefecture, with Mashiki as the core repeated-shock pilot and Uki or Hikawa added only when comparable road, intervention, and hazard coverage passes feasibility gates.
- Units of analysis: Road segment by observation time for disruption and restoration; community or network node for isolation and critical-facility access; municipality only for aggregate robustness checks.
- Period: The 2016 earthquake sequence, interventions completed during 2016-2026, and the 2026 earthquake disruption and recovery window.
- Excluded central outcomes: Unvalidated building reconstruction probabilities and long-interval orthophoto change attributed directly to the 2026 earthquake.

### Study Design Declaration

- Research type: applied
- Study design: Repeated-shock observational panel with hazard common-support matching and time-to-restoration or network-access outcomes; a quasi-experimental interpretation is conditional on later feasibility and identification checks.
- Interpretation limit: Prior 2016 exposure is geographically patterned rather than randomized. No causal resilience dividend will be claimed unless intervention timing, comparison support, pre-event differences, and spatial confounding can be addressed.

## 2. Theoretical Background  /  Conceptual Framework  /  Problem Formulation

### Research Gap

Disaster studies commonly examine damage or short-run recovery after one event. Much less is known about whether the combined legacy of prior exposure, institutional learning, and completed resilience investment improves observable urban-system performance when the same region is struck again years later. Existing building imagery in this project cannot supply a validated reconstruction outcome, but repeated shaking and road-state observations can potentially test a more policy-relevant resilience question based on disruption, restoration, and access.

### Conceptual Framework

The applied framework is:

1. The 2016 earthquake generates heterogeneous exposure, damage experience, learning, and political demand.
2. During 2016-2026, governments and communities may implement physical upgrades, land and road restructuring, preparedness changes, and service-network adaptations.
3. The 2026 earthquake supplies a new stress test with spatially heterogeneous shaking.
4. Urban resilience is observed as reduced disruption severity, shorter restoration time, preserved network connectivity, and maintained access to critical services.

The main pathway is `2016 exposure -> learning and completed intervention -> 2026 preparedness and network redundancy -> 2026 disruption and restoration`. Potential confounding arises from hazard geography, terrain, pre-existing urban form, network centrality, population change, public investment capacity, and selective intervention placement. Prior exposure and completed intervention must therefore be distinguished empirically whenever the records allow it.

### Problem Formulation

Let \(T_i^{2026}\) denote restoration time or isolation duration for road segment or community \(i\), \(E_i^{2016}\) prior earthquake exposure, \(I_i^{2016-2026}\) completed resilience intervention, \(H_i^{2026}\) 2026 hazard intensity, and \(X_i\) pre-event geographic, network, and settlement characteristics. The empirical problem is represented conceptually as:

\[
T_i^{2026} = f(E_i^{2016}, I_i^{2016-2026}, H_i^{2026}, X_i) + \epsilon_i.
\]

This expression defines the required data flow rather than a final estimator. Restoration may be interval-censored between official snapshots, interventions may be selectively located, road observations may be incomplete, and outcomes on nearby segments may be spatially dependent. The next feasibility check must determine whether treatment timing, stable segment linkage, common support, censoring, and spatial dependence can be handled well enough for estimation. Until then, the analysis supports descriptive and associational resilience comparisons rather than causal claims.

## 3. Data Overview

### 3.1 Resilience mainline scope

| Analytical source | Unit | Rows | Columns | Current role |
|---|---|---:|---:|---|
| Official Mashiki road network | road feature | 433 | 11 | Stable local network geometry and route attributes |
| 2026 road-restriction series | reported restriction feature by snapshot | 1,063 | 21 | Descriptive disruption timing, composition, and spatial progression |
| Restriction snapshot coverage | official archive | 24 | 9 | Observation-window and missing-layer audit |
| Candidate resilience interventions | documented intervention | 20 | 20 | Completion timing, candidate route linkage, and eligibility audit |

All 433 road geometries and 1,063 restriction geometries are present, valid, and retained in WGS84. The restriction features occur in 23 restriction-bearing snapshots; the 24th archive has no restriction layer and is retained as unavailable observation coverage rather than as zero disruption.

### 3.2 Temporal structure

- The official restriction observation window runs from 29 July 2026 at 08:00 Japan Standard Time through 17 August 2026 at 09:00 Japan Standard Time.
- Snapshot Time is the primary repeated-observation variable. Restriction Start Time supplies event timing when reported but is missing for 20.8% of restriction features.
- Completion Date Earliest and Completion Date Latest encode uncertainty in reported intervention completion expressions. All 20 latest completion bounds precede the 28 July 2026 event.
- The exploratory scanner identified additional date-like building and metadata fields, but these are not treated as repeated observations for the road-resilience mainline.

### 3.3 Coverage, missingness, and distributions

- The data briefing read 28 tabular sources, summarized 693 variables, generated 80 exploratory distribution plots, and skipped no files.
- Within the road-restriction series, Restriction Direction is 89.3% missing, Restriction Length (km) is 21.8% missing, Restriction Start Time is 20.8% missing, and Prefecture and Municipality are each 20.5% missing.
- Missing values remain unfilled. Observed reported length is therefore not equivalent to total restricted network length.
- Repeated source Restriction Record ID values are retained because one reported event may contain multiple sections or features; Restriction Feature ID is the unique row-level identifier.
- Observation State distinguishes active full closure, active emergency access only, restriction lifted, and unknown status. It does not infer openness from layer absence or non-reporting.
- The exploratory distributions describe the available records and do not estimate closure prevalence, restoration, treatment effects, or causal relationships.

### 3.4 Retained building evidence

The earlier building work remains available as an appendix and measurement-boundary exercise. It includes an image-covered candidate frame of 2,614 buildings, a 9,039-record cross-release panel, and 100-record calibration and validation samples. These records cannot supply a central 2026 event-damage or individualized reconstruction outcome because the relevant attribution and prediction gates failed.

### 3.5 Data limitations relative to the research objective

- The 2026 restriction series records reported closures and restrictions, not a complete census of road state. Non-reporting is not passability.
- Four source record IDs appear with a restriction-lifted status, but only one is observed first in an active state and later in a lifted state. This is insufficient for a general Road Restoration Time outcome.
- Twelve of 20 interventions have a unique candidate route-name match, but none has verified completed-subsegment geometry; treatment assignment is therefore unavailable.
- A spatially linkable 2016 road-restoration record, comparable road-level shaking exposure for both events, community and critical-facility nodes, demographic vulnerability, terrain, and network-redundancy measures remain outside the final-variable set.
- The current data support bounded descriptive and evidence-readiness analysis. They do not yet support the central repeated-shock causal or associational comparison.
## 4. Variable Construction  /  Key Variables

### 4.1 Resilience mainline datasets

| Analytical dataset | Unit / rows | Role | Status |
|---|---:|---|---|
| Official Mashiki road network | road feature / 433 | Stable local road geometry and route attributes | Reproducible; all geometries valid |
| Kumamoto 2026 road-restriction series | restriction feature by snapshot / 1,063 | Observed closure or restriction states across 23 published snapshots | Reproducible; absence is not coded as open |
| Restriction snapshot coverage | official archive / 24 | Distinguishes restriction-bearing snapshots from a missing restriction layer | Reproducible; one explicit layer absence |
| Candidate resilience interventions | documented intervention / 20 | Completion timing and conservative candidate route linkage | Reproducible; no record is yet treatment eligible |

### 4.2 Resilience mainline final variables

| Dataset | Final variables | Construction / interpretation |
|---|---|---|
| Road network | Road Segment ID; Route Number; Route Class; Route Component; Route Name; Official Geometry Length (m); Centroid Longitude; Centroid Latitude; Geometry | Source attributes are type-normalized, whitespace-trimmed, and retained with valid WGS84 line geometry. |
| Road restrictions | Snapshot Time; Restriction Record ID; Restriction Feature ID; Prefecture; Municipality; Road Type; Route Name; Start Location; End Location; Restriction Type; Restriction Reason; Restriction Start Time; Restriction Status; Restriction Direction; Restriction Length (km); Observation State; Record Present; Geometry | Snapshot time is retained in Japan Standard Time. The source record ID identifies a reported event; the deterministic feature ID uniquely identifies a source feature without collapsing multi-section events. Observation State is derived from explicit reported status and distinguishes active full closure, active emergency access only, restriction lifted, and unknown status. |
| Snapshot coverage | Restriction Layer Available; Restriction Feature Count; Absence Interpretation | These fields distinguish a published restriction layer and its feature count from a snapshot in which the layer is absent. Absence is coded as `not_observed_not_open` and never as zero disruption. |
| Interventions | Intervention ID; Area; Asset Name; Asset Type; Reported Completed Extent; Completed Extent (m); Reported Completion Time; Completion Date Earliest; Completion Date Latest; Completion Status at 2026 Event; Completed Before 2026 Event; Geometry Status; Matched Network Layer; Matched Official Feature IDs; Matched Official Feature Names; Route Match Count; Geometry Use Eligible; Treatment Use Eligible; Quality Flag | Reported completion expressions are retained and translated into explicit earliest/latest intervals. Route-name matching is candidate linkage only; it does not define a completed treatment geometry. |

### 4.3 Missingness and quality controls for the resilience mainline

- No missing value is imputed. Changing official schemas explain much of the observed field missingness, including 89.3% for restriction direction, 21.8% for reported restriction length, and 20.8% for restriction start time.
- All 1,063 restriction geometries and all 433 road geometries are present and valid in WGS84.
- Observation State contains 900 active full-closure rows, 57 active emergency-access-only rows, 49 restriction-lifted rows, and 57 unknown-status rows. Roads absent from a snapshot are unobserved, not open.
- The first archive has no restriction layer. It is retained in the coverage series as `not_observed_not_open` rather than as a zero-restriction snapshot.
- The source restriction event ID repeats within 30 snapshot-event groups because some reported events contain multiple road sections or features. All source features are retained and receive unique deterministic feature IDs.
- All 20 intervention completion intervals end before the 2026 event, but a completion date alone does not prove that the recorded whole route was upgraded. Partial completion and geometry uncertainty remain explicit.

### 4.4 Resilience analysis gate

- The restriction time series is eligible for descriptive disruption timing, spatial extent, and network-overlay analyses.
- Twelve intervention records have a unique candidate official route-name match, but no record has verified completed-subsegment geometry. `Geometry Use Eligible` and `Treatment Use Eligible` are therefore false for all 20 records.
- A route-name match cannot serve as a treatment boundary. The intervention-effect design remains blocked until exact completed subsegments are recovered or an independently validated alternative exposure definition is established.
- The processed data do not convert non-reporting into passability. Only one source record ID has an observed active-to-lifted transition, while three other lifted IDs enter the series already lifted; this is not enough to identify a general reopening-time outcome.

### 4.5 Retained building appendix

The earlier building and imagery work is retained as a measurement appendix rather than as the central outcome. Its failed attribution and individualization gates are evidence boundaries for the road-resilience study.

#### 4.5.1 Processed datasets

| Dataset | Unit / rows | Role | Status |
|---|---:|---|---|
| Image-covered building candidate frame | PLATEAU building / 2,614 | Candidate frame with screening scores | Reproducible |
| Building calibration sample | sampled building / 100 | Deterministic, enriched, spatially balanced calibration panel | Reproducible; not prevalence-representative |
| Labeled building calibration sample | sampled building / 100 | Two-pass AI-reviewed visible-change labels and temporal limitations | Exploratory; not independent validation |

#### 4.5.2 Source and constructed variables

| Variable | Type | Construction / interpretation | Analysis status |
|---|---|---|---|
| `GML ID` | string | Stable PLATEAU source identifier | Candidate linkage key |
| `Footprint Geometry` | EPSG:3857 geometry | CityGML building surfaces converted to XY multipolygons and repaired with `buffer(0)` | Screening geometry; some roof-edge surfaces remain unusable |
| `Height (m)` | float | PLATEAU `measuredHeight`; nonpositive and 9,999 sentinels converted to missing | Candidate covariate |
| `Storeys Above Ground` | nullable integer | PLATEAU `storeysAboveGround`; 9,999 converted to missing | Candidate covariate |
| `Survey Year` | nullable string | PLATEAU survey year; `0001` sentinel converted to missing | Provenance / quality field |
| `2016 Change Score` | float | Histogram-matched SSIM, edge difference, and RGB difference after local phase-correlation alignment | Candidate enrichment only; not a damage label |
| `2026 Change Score` | float | Same construction for FY2023 baseline versus 2026 post-event imagery | Long-interval change screening only |
| `Sampling Stratum` | category | 25 stable-low, 25 high-2016, 25 high-2026, and 25 general spatial candidates, sampled with seed 20260818 | Calibration design; no population prevalence inference |
| `Adjudicated 2016 Label` | category | `clear_visible_change`, `possible_visible_change`, `no_visible_change`, or `target_absent_or_uninterpretable` | Candidate mainshock proxy only |
| `2016 Mainshock Proxy Status` | category | Maps the adjudicated label to candidate/uncertain/no-change/not-usable status | Baseline is already post-foreshock |
| `Adjudicated 2026 Label` | category | Same visual vocabulary applied to FY2023–2026 comparison | Not an event-damage variable |
| `2026 Event Attribution Eligible` | boolean | Fixed to `False` because the baseline-to-event interval is too long | Excluded from causal damage analysis |

#### 4.5.3 Missingness and quality controls

- Four of 2,614 candidates have missing height, 362 have missing storeys, and 325 have missing survey year after sentinel normalization. The 100-building calibration panel has 0, 14, and 11 missing values, respectively.
- Candidate footprints require 99.5% primary-flight-strip alpha coverage in both 2016 and 2026 and roof area between 40 and 400 square metres.
- Raw GSI and PLATEAU files are never modified.
- Blind review was followed by a date-revealed consistency pass by the same AI reviewer. This does not establish inter-rater reliability or validated damage ground truth.

#### 4.5.4 Calibration gate

- 2016 imagery conditionally supports visual screening of candidate changes occurring between the post-foreshock and post-mainshock acquisitions.
- 2026 imagery fails the event-attribution gate with the FY2023 baseline.
- The automated change score fails the stand-alone classification gate (2016 enriched-panel ROC AUC 0.618; 2026 long-interval-change ROC AUC 0.683).
- Detailed results are retained in the building-label calibration audit.

#### 4.5.5 PLATEAU cross-release building panel

| Dataset | Unit / rows | Role | Status |
|---|---:|---|---|
| Earlier building inventory | PLATEAU building / 7,223 | Standardized earlier building inventory | Reproducible |
| Later building inventory | PLATEAU building / 8,252 | Standardized later building inventory | Reproducible |
| Cross-release match candidates | spatial candidate pair / 34,367 | Continuous geometry-linkage metrics within 12 m | Reproducible; not one-to-one |
| Cross-release building panel | panel record / 9,039 | Conservative one-to-one links plus unmatched and ambiguous records | Candidate reconstruction panel; not validated outcome |

| Variable | Type | Construction / interpretation | Analysis status |
|---|---|---|---|
| `Construction Year` | nullable string | Source-reported construction year; unknown sentinels normalized to missing | Covariate; available only in the earlier release and 57.8% missing |
| `Building Use Code` | nullable integer | Source building-use category | Descriptive covariate |
| `Structure Type Code` | nullable integer | Source structural-system category | Descriptive covariate |
| `Computed Footprint Area (m2)` | float | Area of repaired EPSG:3857 footprint geometry | Matching input |
| `IoU` | float | Intersection area divided by union area for a candidate pair | Continuous linkage evidence |
| `2020 Coverage Ratio` | float | Pair intersection area divided by the earlier footprint area | Split / merge diagnostic |
| `2023 Coverage Ratio` | float | Pair intersection area divided by the later footprint area | Split / merge diagnostic |
| `Centroid Distance (m)` | float | Distance between candidate footprint centroids | Linkage diagnostic |
| `Footprint Gap (m)` | float | Minimum boundary-to-boundary distance between candidate footprints | Linkage diagnostic |
| `Area Similarity` | float | Smaller computed footprint area divided by larger computed footprint area | Linkage diagnostic |
| `Match Status` | category | `retained`, `suspected_rebuild`, `disappeared`, `new`, or `ambiguous` under recorded conservative thresholds | Screening status only |

- PLATEAU release year is not the same as source observation year. All 7,223 earlier-release buildings report survey year 2017. In the later release, 5,777 buildings report survey year 2021 and 2,475 have no survey year. The common creation date 2024-03-31 is a record date, not a building construction date.
- Cross-release building identifiers do not provide continuity: none of the selected one-to-one pairs has an identical source `Building ID`. Matching therefore rests on geometry rather than a persistent administrative identifier.
- Baseline classification yields 5,738 retained pairs, 698 suspected rebuild pairs, 550 disappeared earlier footprints, 1,595 new later footprints, and 458 ambiguous records.
- The retained-versus-suspected-rebuild boundary is threshold-sensitive: suspected rebuild counts range from 341 to 989 across the recorded relaxed and strict scenarios. `suspected_rebuild` is therefore a candidate footprint-replacement state, not a validated reconstruction outcome.
- Detailed integrity checks, metric quantiles, missingness, and threshold sensitivity are retained in the building-panel audit.

#### 4.5.6 Multi-date reconstruction-candidate validation

| Dataset | Unit / rows | Role | Status |
|---|---:|---|---|
| Reconstruction-validation sample | sampled panel building / 100 | Deterministic spatial sample with 20 buildings per candidate status and pairwise image metrics | Reproducible; stratified, not prevalence-representative |
| First-round adjudicated sample | sampled panel building / 100 | Date-revealed first-round labels and adjacent-pair consistency checks | Intermediate review evidence |
| Final reconstruction-validation sample | sampled panel building / 100 | Two-round conservative labels, exclusions, inventory-status assessment, and eligibility flags | Calibration evidence; not official reconstruction truth |

| Variable | Type | Construction / interpretation | Analysis status |
|---|---|---|---|
| `Source Match Status` | category | Stratification variable copied from the cross-release panel; 20 each of retained, suspected rebuild, disappeared, new, and ambiguous | Sampling only; hidden during visual review |
| `Pair 1 Ordered Transition` | category | Blind visual comparison of 2016-04-15 post-foreshock versus 2016-04-16 post-mainshock imagery, restored to date order after labeling | Image-visible event-window transition |
| `Pair 2 Ordered Transition` | category | Blind comparison of 2016-04-16 post-mainshock versus official 2020-11 PLATEAU orthophoto | Recovery-period visible transition |
| `Pair 3 Ordered Transition` | category | Blind comparison of the 2020-11 orthophoto versus the FY2023 orthophoto release | Inventory calibration; exact later flight date unresolved |
| `Final Pair * Confidence` | ordered category | High, medium, or low reviewer confidence after targeted second-round review | Required for eligibility filtering |
| `Final * Cross-Pair Consistent` | boolean | Checks whether the same intermediate date is assigned a compatible presence state in adjacent comparisons | Record-level quality flag |
| `Final Inventory Status Visual Assessment` | category | Conservative comparison between the final image-pair transition and the candidate PLATEAU status | Calibration assessment only |
| `Final Inventory Validation Eligible` | boolean | Requires high/medium confidence for pairs 2-3, interpretable nonconflicting transitions, and consistent 2020 state | Primary inventory-calibration subset |
| `Final Longitudinal Validation Eligible` | boolean | Applies the same restrictions across all three date pairs and both intermediate dates | Four-image trajectory subset |

- The first round completed all 300 pair labels; 268 (89.3%) were high or medium confidence and 6 (2.0%) were uninterpretable.
- A second independently re-randomized blind pass targeted 53 low-confidence or cross-pair-inconsistent comparisons. Exact ordered-transition agreement in this deliberately difficult subset was 20/53 (37.7%); 10 equal-confidence disagreements were excluded instead of being forced.
- The conservative final sample contains 91 inventory-validation-eligible records and 82 fully longitudinal eligible records. These counts describe a balanced calibration sample and cannot estimate population prevalence.
- The official FY2020 orthophoto was photographed in November 2020 at 40 cm source resolution. The FY2023 orthophoto release does not yet have a verified flight date, so release year is not treated as acquisition year.
- Image review validates visible presence or form change, not earthquake causation, ownership, demolition permits, or legally recorded reconstruction. External validation against the requested official reconstruction register remains necessary.
- Round-specific and final evidence is retained in the reconstruction-validation audits.

#### 4.5.7 Full-panel reconstruction calibration and failed individualization gate

| Variable | Type | Construction / interpretation | Analysis status |
|---|---|---|---|
| `Calibration Domain` | category | `in_sampling_domain` applies the validation sample's four-image coverage, 30-800 m2 area, maximum 60 m width/height, and 37 m edge-margin rules; all other records are explicit extrapolations | Required stratification flag |
| `Conservative Recovery Status-Calibrated Probability` | float | Jeffreys-Beta posterior mean within each source match status; positive means absent immediately after the mainshock and present in 2020, while visible-change-only cases are excluded | Primary status-level sensitivity parameter; not an individual probability |
| `Conservative Recovery Probability 95% Low/High` | float | Equal-tailed 95% posterior interval for the status-level conservative probability | Required uncertainty bounds |
| `Inclusive Visible Replacement Status-Calibrated Probability` | float | Treats absent-to-present and changed-present-to-present as positive | Upper-definition sensitivity only |
| `Inclusive Visible Replacement Probability 95% Low/High` | float | Equal-tailed 95% posterior interval for the inclusive definition | Sensitivity bounds |
| `Shock Linked Recovery Status-Calibrated Probability` | float | Requires present-to-absent across the mainshock and absent-to-present by 2020 | Event-linked sensitivity definition |
| `Shock Linked Recovery Probability 95% Low/High` | float | Equal-tailed 95% posterior interval for the shock-linked definition | Sensitivity bounds |
| `Individual Probability Use Eligible` | boolean | Requires the predeclared spatial cross-validation gate for individual prediction | Fixed to `False` for all 9,039 records |

- The full scored panel contains 9,039 records: 4,582 are in the original image/size sampling domain and 4,457 are flagged as extrapolations.
- The conservative status-calibrated expected count is 4,461, with a 95% interval of 2,639-6,269. It is an uncertainty scenario rather than a credible reconstruction total.
- Outcome-definition sensitivity dominates: the population-weighted expected share ranges from 18.7% under the shock-linked definition to 75.8% under the inclusive definition.
- Five-fold spatially grouped ROC AUC is 0.557 for conservative recovery, 0.493 for inclusive visible replacement, and 0.483 for shock-linked recovery. All Brier scores are worse than the matching constant-prevalence benchmark.
- All three individualized models fail the predeclared gate of ROC AUC at least 0.70 and Brier improvement of at least 0.02. Individual diagnostic scores remain reproducibility evidence only and must not be used for ranking, thresholding, causal estimation, or publication claims.
- Symmetric and asymmetric false-positive/false-negative scenarios from 0% to 20% are retained in the measurement-error sensitivity evidence.
- The reconstruction-calibration audit preserves the full diagnostics. Official reconstruction records or a substantially larger independent labeled sample are required before reconstruction can serve as the central outcome.

## 5. Identification Strategy

### 5.1 Current-stage design principle

The current stage is a bounded descriptive infrastructure-disruption and evidence-readiness study. It estimates properties of the official 2026 restriction record, its spatial relationship to the Mashiki road network, and the analytical eligibility of intervention and building evidence. It does not estimate a resilience dividend, restoration effect, or causal intervention effect.

The unit of the temporal analysis is the reported restriction feature by official snapshot. The unit of the spatial diagnostic is the official road feature overlaid with reported restriction geometry. The unit of the intervention audit is the documented intervention. These units are not treated as interchangeable.

### 5.2 Identification logic

| Evidence layer | Section 4 inputs | Identification role | Permitted interpretation | Prohibited interpretation |
|---|---|---|---|---|
| Observation coverage | Snapshot Time; Restriction Feature ID; Record Present; Observation State; Restriction Layer Available; Restriction Feature Count; Absence Interpretation | Establishes when restriction features were observable, whether a restriction layer was supplied, and whether reported features were active, lifted, or unknown | Officially observed reporting intensity and state composition | Absence means open; all listed features are active; falling counts mean recovery |
| Restriction composition | Restriction Type; Restriction Status; Restriction Reason; Road Type; Municipality; Restriction Length (km) | Describes the reported disruption portfolio and field completeness | Composition and extent among reported features | Population-wide closure prevalence or total affected length |
| Spatial progression | Snapshot Time; Geometry; Municipality; Road Type; Route Name | Shows where reported restrictions appear and persist across snapshots | Geography of reported disruption | Stable road-segment restoration without validated linkage |
| Road-network overlap | Road Segment ID; Route Class; Route Name; Geometry; Restriction Feature ID | Tests whether reported geometries can be related to the official Mashiki network | Spatial-linkage readiness and sensitivity | A definitive segment treatment or reopening state |
| Intervention eligibility | Intervention ID; Asset Type; Completion Date Earliest; Completion Date Latest; Route Match Count; Geometry Use Eligible; Treatment Use Eligible; Quality Flag | Tests whether documented interventions have the timing and geometry needed for exposure assignment | Evidence maturity and remaining linkage loss | Causal effects of reconstruction investment |
| Measurement gates | Final Inventory Validation Eligible; Final Longitudinal Validation Eligible; 2026 Event Attribution Eligible; Individual Probability Use Eligible; Geometry Use Eligible; Treatment Use Eligible | Makes exclusion rules observable and reproducible | Which evidence streams may enter later analysis | Treating a failed proxy as an outcome or treatment |

### 5.3 Relationship to the research questions

- The central repeated-shock question remains inconclusive because 2016 exposure, comparable 2026 hazard, stable road-level restoration time, and eligible intervention geometry do not yet form a linked analytical panel.
- The intervention-mechanism question is not currently testable: all 20 Treatment Use Eligible values are false.
- The network and service mechanism is only partially addressed through road-network overlap. Community isolation and critical-facility access variables are not available as final variables.
- The spatial-inequality question is not currently testable because comparable demographic vulnerability, terrain, and network-redundancy measures are not present in the final-variable set.
- The robustness and evidence-boundary question is directly supported through explicit observation, missingness, geometry, attribution, and eligibility gates.

### 5.4 Interpretation limits and stopping rules

- Active, lifted, and unknown reported states are shown separately. A decline in active features is described as a reporting-series change, not restoration, unless stable segment linkage and an observed transition to a passable state are established.
- Reported restriction length is summarized only among nonmissing values and is accompanied by its missing fraction.
- A spatial overlay is a linkage diagnostic. It does not create a treatment indicator.
- Candidate route-name matching is never substituted for completed-subsegment geometry.
- No regression coefficient, survival curve, or causal contrast is produced at this stage.
- Restriction Layer Available, Restriction Feature Count, and Absence Interpretation are final variables. The first timeline figure and snapshot-coverage table may use them while retaining the non-reporting safeguard.

## 6. Main Estimation Framework

### 6.1 Snapshot-level reporting statistics

For each official snapshot and normalized observation state, the observed feature count, active-state reported length, and active-state length-field missing fraction are:

\[
N_{st} = \sum_{k=1}^{K} 1(T_k=t)1(S_k=s), \qquad
N_t = \sum_s N_{st}.
\]

\[
L_t^{active,obs} = \sum_{k:T_k=t} 1(A_k=1)1(M_k=1)\ell_k, \qquad
q_t^{active} = 1 - \frac{\sum_{k:T_k=t}1(A_k=1)1(M_k=1)}{\sum_{k:T_k=t}1(A_k=1)}.
\]

Here, \(N_{st}\) is the number of unique Restriction Feature ID values in Observation State \(s\) at Snapshot Time \(t\); \(K\) is the total number of observed features; \(T_k\) is the Snapshot Time of feature \(k\); \(S_k\) is its Observation State; and \(N_t\) is the total reported feature count. \(A_k\) equals one for active full closure or active emergency access only; \(M_k\) equals one when Restriction Length (km) is observed; \(\ell_k\) is the reported length of feature \(k\); \(L_t^{active,obs}\) is observed reported length among active features; and \(q_t^{active}\) is the active-feature length missing fraction. \(L_t^{active,obs}\) is not interpreted as total restricted network length.

For category \(c\), the reported composition at snapshot \(t\) is:

\[
\pi_{ct} = \frac{\sum_{k=1}^{K}1(T_k=t)1(C_k=c)}{N_t}.
\]

Here, \(\pi_{ct}\) is the share of observed features in category \(c\), and \(C_k\) is the selected Observation State, Restriction Type, Restriction Status, Road Type, or Municipality category for feature \(k\). Categories with missing values remain an explicit missing group.

These statistics generate 2026 Road Restriction Observation Timeline and Road Restriction Composition and Missingness.

### 6.2 Spatial-progression and network-overlap diagnostics

Reported restriction Geometry is plotted at four representative Snapshot Time values selected to show the beginning, early expansion, intermediate phase, and latest available observation. The selection must be based on observation coverage rather than on visually maximizing change.

For road feature \(i\), snapshot \(t\), and diagnostic tolerance \(d\), spatial proximity is defined as:

\[
O_{it}(d) = 1\{\operatorname{dist}(G_i,R_t) \le d\}.
\]

Here, \(O_{it}(d)\) is a diagnostic overlap indicator; \(G_i\) is the Geometry of Road Segment ID \(i\); \(R_t\) is the union of reported restriction Geometry at Snapshot Time \(t\); and \(d\) is a metric spatial tolerance after projecting working copies to a suitable local coordinate system. The sensitivity grid is \(d \in \{0,10,25,50\}\) metres. The stored WGS84 geometry is not overwritten.

\(O_{it}(d)\) is used only to assess linkage sensitivity for Mashiki Road Network and Reported Restriction Overlap. It is not a passability, treatment, or restoration outcome.

### 6.3 Intervention-linkage and measurement-gate statistics

For eligibility stage \(s\), the number and share of documented interventions passing the stage are:

\[
F_s = \sum_{j=1}^{J}1(E_{js}=1), \qquad
r_s = \frac{F_s}{J}.
\]

Here, \(J\) is the number of Intervention ID values; \(E_{js}\) indicates whether intervention \(j\) passes stage \(s\); \(F_s\) is the passing count; and \(r_s\) is the passing share. Stages include Completed Before 2026 Event, positive Route Match Count, Geometry Use Eligible, and Treatment Use Eligible.

For measurement gate \(g\), the eligible share is:

\[
p_g = \frac{\sum_{u=1}^{U_g}1(A_{ug}=1)}{U_g}.
\]

Here, \(U_g\) is the number of records assessed under gate \(g\); \(A_{ug}\) is the relevant Final Inventory Validation Eligible, Final Longitudinal Validation Eligible, 2026 Event Attribution Eligible, Individual Probability Use Eligible, Geometry Use Eligible, or Treatment Use Eligible value for record \(u\); and \(p_g\) is the eligible share.

These quantities generate Intervention Linkage and Eligibility Funnel, Measurement Gates and Excluded Outcomes, Candidate Intervention Linkage and Eligibility, and Evidence Readiness and Identification Boundary.

### 6.4 Robustness and failure-mode plan

- Recalculate state-specific temporal counts with Restriction Feature ID and, separately, Restriction Record ID to show the consequence of multi-feature reported events.
- Report active-state restriction length together with \(q_t^{active}\); do not impute missing lengths.
- Preserve missing categories in composition statistics and show results both including and excluding the missing group.
- Evaluate road-network overlap across the full \(d\) sensitivity grid. A conclusion that depends on one tolerance is classified as unstable.
- Keep the archive with no restriction layer outside \(N_t\) trend interpretation and display it explicitly as unavailable coverage.
- Treat restriction-lifted and unknown-status rows as separate reported states; neither is counted as an active restriction.
- Treat all Geometry Use Eligible, Treatment Use Eligible, 2026 Event Attribution Eligible, and Individual Probability Use Eligible failures as hard exclusions.
- Do not estimate heterogeneity, common-support, restoration, or causal intervention models until their required final variables exist.

## 7. Analytical Workflow

| step | variables used | formula/model used | generated figure/table title | theory or claim evaluated | support status |
|---|---|---|---|---|---|
| Verify observation coverage | Snapshot Time; Restriction Feature ID; Record Present; Observation State; Restriction Layer Available; Restriction Feature Count; Absence Interpretation | Coverage audit and explicit unavailable-layer rule | 2026 Road Restriction Observation Timeline; Road Restriction Snapshot Coverage Audit | Whether the reporting series can support temporal description | Supported for bounded descriptive use |
| Summarize temporal reporting | Snapshot Time; Restriction Feature ID; Restriction Record ID; Restriction Length (km); Restriction Type; Restriction Status; Observation State | \(N_{st}\), \(N_t\), \(L_t^{active,obs}\), \(q_t^{active}\), and \(\pi_{ct}\) | 2026 Road Restriction Observation Timeline; Road Restriction Composition and Missingness | Whether active, lifted, and unknown reported states evolve measurably through time | Supports descriptive reporting-state change only |
| Map reported disruption | Snapshot Time; Geometry; Restriction Type; Municipality; Road Type | Coverage-based representative-snapshot selection | Spatiotemporal Progression of Reported Road Restrictions | Whether reported disruption has spatially differentiated patterns | Supports descriptive geography only |
| Diagnose road-network linkage | Road Segment ID; Route Class; Route Name; Restriction Feature ID; Snapshot Time; Geometry | \(O_{it}(d)\) across the tolerance grid | Mashiki Road Network and Reported Restriction Overlap | Whether restriction geometry can be related robustly to the Mashiki network | Inconclusive until overlap sensitivity is observed |
| Audit intervention evidence | Intervention ID; Asset Type; Completion Date Earliest; Completion Date Latest; Route Match Count; Geometry Use Eligible; Treatment Use Eligible; Quality Flag | \(F_s\) and \(r_s\) | Intervention Linkage and Eligibility Funnel; Candidate Intervention Linkage and Eligibility | Whether documented interventions can operationalize the intervention mechanism | Not supported at present because no treatment-eligible geometry exists |
| Audit measurement eligibility | Final Inventory Validation Eligible; Final Longitudinal Validation Eligible; 2026 Event Attribution Eligible; Individual Probability Use Eligible; Geometry Use Eligible; Treatment Use Eligible | \(p_g\) | Measurement Gates and Excluded Outcomes; Evidence Readiness and Identification Boundary | Whether unsupported proxies are excluded consistently | Supported as an evidence-boundary claim |
| Evaluate the central research contract | All eligible variables above | Cross-output identification audit; no causal estimator | Evidence Readiness and Identification Boundary | Whether the available evidence answers the repeated-shock resilience question | Inconclusive; 2016 exposure, 2026 hazard comparability, restoration outcomes, intervention geometry, and service-access variables remain missing |

The workflow stops after evidence-readiness assessment. Progression to a repeated-shock causal or associational model requires a revised final-variable contract, a revised output plan containing direct tests of the central question, and a new estimation-framework review.

## 8. Figure and Table Plan

The confirmed first-stage output package documents the observed 2026 disruption record, its spatial relationship to the Mashiki road network, intervention-linkage readiness, and explicit measurement gates. Causal resilience-effect, restoration-survival, and critical-service-access outputs are deferred until their required variables pass the analytical eligibility gates.

### Figures

| title | what it expresses | figure type | subpanels | key variables | status |
|---|---|---|---:|---|---|
| 2026 Road Restriction Observation Timeline | Supplementary diagnostic showing official observation coverage, active reported length, field completeness, and the composition of active, lifted, and unknown reported states without interpreting non-reporting as openness or decline as restoration. | line | 3 | Snapshot Time; Restriction Feature ID; Restriction Length (km); Restriction Type; Restriction Status; Observation State; Restriction Layer Available; Restriction Feature Count; Absence Interpretation | done |
| Spatiotemporal Progression of Reported Road Restrictions | Shows the geography and composition of reported road restrictions at four representative observation times. | map | 4 | Snapshot Time; Geometry; Restriction Type; Municipality; Road Type | done |
| Mashiki Road Network and Reported Restriction Overlap | Assesses the spatial coverage and limits of linking reported restrictions to the official Mashiki road network. | map | 2 | Road Segment ID; Route Class; Route Name; Restriction Feature ID; Snapshot Time; Geometry | done |
| Intervention Linkage and Eligibility Funnel | Shows how the 20 documented interventions move from official evidence through candidate route matching to geometry and treatment eligibility. | bar | 2 | Asset Type; Route Match Count; Geometry Use Eligible; Treatment Use Eligible; Quality Flag | pending |
| Measurement Gates and Excluded Outcomes | Makes transparent which building and intervention measurements pass validation gates and which outcomes are excluded from causal interpretation. | stacked_bar | 2 | Final Inventory Validation Eligible; Final Longitudinal Validation Eligible; 2026 Event Attribution Eligible; Individual Probability Use Eligible; Geometry Use Eligible; Treatment Use Eligible | pending |

### Tables

| title | what it expresses | rows | columns | row meaning | column meaning | status |
|---|---|---:|---:|---|---|---|
| Road Restriction Snapshot Coverage Audit | Audits official observation timing, restriction-layer availability, feature counts, reported-field completeness, and the interpretation of layer absence. | 24 | 8 | One official snapshot | Snapshot Time, Restriction Layer Available, Restriction Feature Count, observed record and length completeness, category coverage, and Absence Interpretation | pending |
| Road Restriction Composition and Missingness | Summarizes the composition, temporal coverage, and missingness of the principal reported restriction fields. | approximately 15 | 7 | One variable or major reported category | Count, proportion, missingness, and first and last observed times | pending |
| Candidate Intervention Linkage and Eligibility | Presents all documented interventions, completion intervals, candidate network matches, and conservative eligibility decisions. | 20 | 12 | One documented intervention | Asset Type, reported and normalized extent, completion interval, Route Match Count, Geometry Use Eligible, Treatment Use Eligible, and Quality Flag | pending |
| Evidence Readiness and Identification Boundary | Distinguishes evidence streams that support description from constructs that remain unavailable for causal or network-service analysis. | approximately 8 | 7 | One research construct or evidence stream | Spatial precision, temporal precision, linkage status, analytical eligibility, permitted claim, and remaining blocker | pending |

### Variable coverage status

All variables referenced by the confirmed first-stage figures and tables now appear in Section 4 as final analytical or diagnostic variables. This resolves the prior snapshot-coverage warning but does not resolve the separate absence of variables needed for the central repeated-shock causal question.
