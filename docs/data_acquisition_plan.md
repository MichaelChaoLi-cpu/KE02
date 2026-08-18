# KE02 data acquisition plan

Status date: 2026-08-18 (Asia/Tokyo)

## Identification requirement

The study is not identified by two post-earthquake images alone. A publishable
repeated-shock design needs a linked chain:

`shaking exposure -> damage or service loss -> intervention completed during 2016-2026`

The same spatial units, outcome definitions, and observation windows must be
used for the 2016 and 2026 events. The 2016 exposure must include both the 14
April foreshock and the 16 April mainshock; the 2016 shaking surface will take
the cell-level maximum across the two events.

## Necessary data

| Priority | Dataset | Analytical role | Current status |
| --- | --- | --- | --- |
| Must | 2016 and 2026 ground-motion surfaces (MMI, PGA, PGV, uncertainty and stations) | Continuous hazard exposure and common-support matching | Downloaded from USGS ShakeMap for 2016-04-14, 2016-04-16, and 2026-07-28 |
| Must | Pre- and post-event orthophotos with acquisition time, footprint, resolution, cloud/alpha coverage and licence | Building/road/landslide outcome measurement | Mashiki and Uki z18 pilots downloaded; matched pre-2026 baselines obtained, but a defensible pre-2016-foreshock baseline remains unresolved |
| Must | Comparable building-damage or functional-loss labels for both events | Primary outcome and validation target | Municipal-level official reports downloaded; building-level labels remain unresolved |
| Must | 2016-2026 intervention ledger with geometry, start/completion date, type, cost/intensity, and provenance | Treatment assignment | First official-source candidate ledger assembled with 20 records; geometry export, post-2021 reconciliation, and completion-date audit remain the main identification bottleneck |
| Must | Stable building footprints and baseline building stock (age, structure, use, floors where available) | Denominator, exposure at risk, and vulnerability controls | PLATEAU FY2023 CityGML downloaded for Mashiki; comparable Uki stock remains pending |
| Must | Administrative units, roads, bridges and critical facilities with stable identifiers | Unit linkage and network outcomes | 2026 road-state time series downloaded; PLATEAU FY2023 roads obtained; Mashiki's official road-network and urban-planning ArcGIS services identified but not yet exported; wider-area baseline layers remain pending |
| Strong | DEM, slope, geology, liquefaction/site-amplification and active faults | Hazard confounding and heterogeneous effects | Four GSI active-fault GeoTIFF packages downloaded; remaining layers pending |
| Strong | ALOS/Sentinel SAR displacement and coherence for both events | Cloud-independent deformation and damage proxy | Pending; product/version comparability must be audited first |
| Strong | Population grids and vulnerable-population measures for 2015/2020/2025 | Exposure and equity outcomes | Pending |
| Strong | Outage, water, shelter, road closure and restoration timestamps | Urban service resilience and recovery speed | MLIT 2026 road restrictions/ETC2.0 snapshots, eight official 2016 general-road restoration maps, and all 32 available 2026 prefectural damage reports downloaded; municipal-road and other-service coverage remain pending |
| Supporting | Rainfall, land cover and antecedent moisture | Landslide attribution and false-positive control | Pending |
| Optional | Night lights, mobile activity, street imagery, social media | Secondary recovery/behaviour outcomes | Do not acquire until the core design passes feasibility gates |

## Data downloaded in the first acquisition batch

- GSI 2016 landslide interpretation (KML ZIP).
- GSI 2026 Kumamoto-Yatsushiro landslide/deposition interpretation (GeoJSON ZIP).
- GSI active-fault GeoTIFF packages: Aso (181), revised Kumamoto (182),
  revised Yatsushiro (193), and Hinagu (194).
- USGS ShakeMap raster, vector, grid, rupture, station, and metadata products
  for `us20005hzn`, `us20005iis`, and `us6000tgb9`.
- MLIT road restriction, passability and ETC2.0 mean-speed snapshots from
  2026-07-29 through 2026-08-17, plus the current GIS map package.
- Latest available official damage snapshots as of 2026-08-17 from FDMA and
  MLIT, and Kumamoto Prefecture's 2016 final damage report dated 2025-04-11.
- Thirteen GSI z14 orthophoto quicklook tiles used for coverage screening.

All ZIP files in this batch passed archive-integrity tests after download.

## Orthophoto screening result

- **Mashiki:** full and visually usable coverage in the tested 2016-04-15,
  2016-04-16 and 2026-08-03 tiles. This is the strongest first pilot because
  it also preserves the interval between the 2016 foreshock and mainshock.
- **Uki:** full and visually usable coverage in the selected 2016 and
  2026-07-30 layers. This is the second first-stage pilot.
- **Hikawa:** the earliest 2016 layers have alpha/coverage gaps. The
  2016-04-20 Yatsushiro layer fills the tested tile, but its later acquisition
  date introduces more clearance/recovery contamination and must be flagged.

GSI distributes the earthquake orthophotos as XYZ PNG tiles, not as a directly
linked orthophoto GeoTIFF. Every project mosaic is therefore labelled as a
derived, georeferenced GeoTIFF and retains the original layer ID, tile list,
acquisition date, processing script, and GSI attribution.

## High-resolution pilot acquisition result

Both pilots use compact WGS84 bounding boxes and GSI zoom level 18:

| Pilot | Bounding box (west, south, east, north) | Approximate scope |
| --- | --- | --- |
| Mashiki | `130.80632, 32.78266, 130.82768, 32.80000` | 2 km by 2 km centred on the built-up area |
| Uki | `130.67330, 32.64000, 130.69470, 32.65800` | 2 km by 2 km built-up comparison area |

The retained source tiles, SHA-256 tile manifests, metadata JSON, VRTs and
derived EPSG:3857 GeoTIFFs are under `data/raw/gsi/orthophoto_z18/`.

| Pilot | Time | GSI layer | Audit result |
| --- | --- | --- | --- |
| Mashiki | 2016-04-15, after foreshock and before mainshock | `20160414kumamoto_0415dol1` | 256/256 tiles retrieved |
| Mashiki | 2016-04-16, after mainshock | `20160414kumamoto_0416dol1` plus `20160414kumamoto_0416dol4` | Primary strip alone was 60.96% opaque; same-day supplement raises the combined mosaic to approximately 100% |
| Mashiki | 2026-08-03, after event | `20260729kumamoto_kumamoto1_0803do` plus `20260729kumamoto_kumamoto2_0729_0802do` | Combined mosaic has full AOI coverage |
| Uki | 2016-04-15, after foreshock and before mainshock | `20160414kumamoto_0415dol3` | 272/272 tiles retrieved |
| Uki | 2016-04-16, after mainshock | `20160414kumamoto_0416dol2` | 272/272 tiles retrieved |
| Uki | 2026-07-30, after event | `20260729kumamoto_kumamoto4_0730do` | 272/272 tiles retrieved |

The Mashiki 2016-04-16 composite contains a visible radiometric seam between
same-day flight strips. It is suitable for coverage and manual screening but
must receive seam masking or radiometric normalisation before pixel-based
machine learning. The 2016-04-15 images are not true pre-2016-event baselines:
they were acquired after the 14 April foreshock. They can identify incremental
mainshock change but cannot measure total 2016 sequence damage without an
earlier baseline or authoritative damage labels.

## Matched pre-2026 baselines and building stock

- **Mashiki:** the MLIT Project PLATEAU FY2023 package provides original
  GeoTIFF orthophotos. Nine standard mesh tiles intersecting the pilot were
  extracted and cropped to a 0.5 m EPSG:3857 pilot raster. The associated
  source register dates the aerial-photo inputs to 2024-03-31; this should be
  treated as a source reference date, not an exact flight timestamp, unless a
  more precise flight record is recovered.
- **Mashiki buildings and roads:** the PLATEAU CityGML archive passed ZIP
  integrity testing. The same nine meshes contain 8,271 building features
  before exact AOI clipping, including height, storeys, usage, structure and
  planning attributes, plus LOD1 road geometry.
- **Uki:** the GSI seamless orthophoto source-period geometry identifies the
  pilot imagery as November 2023. It provides a recent, complete pre-2026
  baseline. No comparable PLATEAU city model was found in the first official
  catalogue search, so an official 2D building source is still required.
- **Rejected as Mashiki's primary pre-2026 baseline:** the GSI seamless image
  in the pilot is sourced from April-July 2016 and visibly includes blue-tarp
  post-earthquake conditions. It remains useful as a post-2016 recovery-state
  image, not as the preferred 2026 baseline.

The PLATEAU source archives, extracted AOI meshes, metadata, codelists and the
derived pilot raster are retained under `data/raw/plateau/mashiki/2023/`.

## Next acquisition gates

1. Preprocess the downloaded eight-map 2016 MLIT sequence and 32-report 2026
   Kumamoto Prefecture sequence. These sources support corridor and
   municipality outcomes, but not a complete municipal-road survival process.
2. Link the exported 433-route Mashiki road network and 21 official
   urban-planning features to event and intervention records; service metadata,
   edit timestamps, original spatial references, and query parameters are
   retained beside the exports.
3. Reconcile the 20-record candidate intervention ledger against official maps
   and later progress reports. Encode only assets completed before
   2026-07-28; planned, partial, and completed states must remain distinct.
4. Build a road-observation panel with four explicit states: `open`, `closed`,
   `not observed`, and `outside reporting scope`. Absence from the MLIT
   restriction layer must never be converted automatically to `open`.
5. Run hazard-treatment-outcome overlap diagnostics at corridor and
   municipality scales. Nearest-cell 2026 USGS MMI is approximately 8.5 in
   Mashiki, 8.5 in Uki, and 9.1 in Hikawa, so hazard common support is not the
   immediate bottleneck; consistent outcome reporting is.
6. Keep the building reconstruction work as a validated descriptive appendix.
   Its individual probabilities failed discrimination checks and must not be
   reused as an intervention or causal outcome.
7. Treat all 2026 reports as versioned snapshots. Do not overwrite earlier
   files when agencies publish revisions.

The detailed feasibility audit and official-source inventory are under
`data/exp/feasibility-check/`. If municipal outcome coverage remains
unavailable after these gates, the paper must use consistently reported
national/prefectural corridors across the wider Kumamoto area and be framed as
repeated-shock resilience measurement rather than a clean natural experiment.

## Primary official source pages

- [GSI 2026 Kumamoto earthquake portal](https://www.gsi.go.jp/BOUSAI/20260728_kumamoto_earthquake.html)
- [GSI 2016 Kumamoto earthquake portal](https://www.gsi.go.jp/BOUSAI/H27-kumamoto-earthquake-index.html)
- [GSI tile specification and layer list](https://maps.gsi.go.jp/development/siyou.html)
- [NIED 2026 strong-motion summary](https://www.kyoshin.bosai.go.jp/ja/topics/20260728162700/)
- [USGS earthquake catalogue API](https://earthquake.usgs.gov/fdsnws/event/1/)
- [MLIT 2026 road passability map and GIS downloads](https://www.mlit.go.jp/road/saigai/r8kumamoto/index.html)
- [MLIT 2016 road response and restoration snapshots](https://www.mlit.go.jp/road/road_fr1_000083.html)
- [Kyushu Regional Development Bureau 2016 road restoration history](https://www.qsr.mlit.go.jp/kumamoto/fukkyuu.html)
- [MLIT 2026 damage reports](https://www.mlit.go.jp/saigai/saigai_260728.html)
- [FDMA 2026 disaster reports](https://www.fdma.go.jp/disaster/info/2026/)
- [Kumamoto Prefecture 2026 damage-report sequence](https://www.pref.kumamoto.jp/soshiki/222/276831.html)
- [Kumamoto Prefecture 2016-2026 recovery archive](https://www.pref.kumamoto.jp/soshiki/5/1453.html)
- [Mashiki official road-network FeatureServer](https://services8.arcgis.com/axHvRSDfbBIXHkRF/ArcGIS/rest/services/%E9%81%93%E8%B7%AF%E7%B6%B2%E5%9B%B3/FeatureServer)
- [Mashiki evacuation-route and site progress table](https://www.town.mashiki.lg.jp/kiji0034786/3_4786_9683_up_v2iyyrgw.pdf)
- [Project PLATEAU Mashiki FY2023 dataset](https://www.geospatial.jp/ckan/dataset/plateau-43443-mashiki-machi-2023)

## Restricted or non-direct sources

NIED K-NET/KiK-net waveform downloads require user registration. They are
valuable for validating the ShakeMap exposure surface, but the openly
downloadable ShakeMap data are sufficient to begin spatial harmonisation.
JMA's gridded estimated-intensity data may require acquisition through the
Japan Meteorological Business Support Center; it should be treated as a
validation source rather than a blocker for the first pilot.
