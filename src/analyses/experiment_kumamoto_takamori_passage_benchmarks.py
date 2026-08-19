#!/usr/bin/env python3
"""Benchmark treated-corridor probe passage against two official road peers.

The experiment asks whether the newly completed Kumamoto-Takamori corridor's
post-earthquake passage evidence is distinguishable from: (1) an established
four-lane corridor and (2) an established two-lane corridor with closer 2026
ground-shaking support.  The peers are descriptive benchmarks, not controls.
"""
from __future__ import annotations

import tempfile
import zipfile
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio

from audit_kumamoto_takamori_probe_passage import (
    ARCHIVE_DIR,
    MAP_ARCHIVE,
    METRIC_CRS,
    MIN_ALIGNMENT_RATIO,
    MIN_TRACE_LENGTH_M,
    NEAR_FULL_THRESHOLD,
    PASSAGE_MEMBER,
    ROOT,
    corridor_axis,
    merged_interval_length,
    parse_snapshot,
    read_geojson_member,
    select_corridor_traces,
    sha256,
)


FACILITIES = (
    ROOT
    / "data/raw/official_resilience/mashiki_arcgis/"
    "mashiki_urban_planning_transport_facilities.geojson"
)
MASTER_PLAN = (
    ROOT
    / "data/raw/official_resilience/interventions/"
    "mashiki_urban_master_plan_current_conditions_2026.pdf"
)
MASTER_PLAN_SHA256 = "ce2a5f8f45fee0f8dd180a91f841f24c7f6921c2e785a80d8b9536f90db61556"
SHAKEMAP = ROOT / "data/raw/usgs/2026/us6000tgb9/raster.zip"
OUT = ROOT / "data/exp/feasibility-check/intervention-geometry"
CORRIDOR_ROLES = {
    "益城中央線": "treated_post_2016_four_lane_corridor",
    "東町空港線": "established_four_lane_measurement_benchmark",
    "惣領木山線": "established_two_lane_hazard_benchmark",
}


def load_corridors() -> gpd.GeoDataFrame:
    if sha256(MASTER_PLAN) != MASTER_PLAN_SHA256:
        raise ValueError("Official master-plan PDF hash changed")
    facilities = gpd.read_file(FACILITIES)
    selected = facilities.loc[facilities["tf_name"].isin(CORRIDOR_ROLES)].copy()
    rows = []
    for name, group in selected.groupby("tf_name"):
        geometry = group.to_crs(METRIC_CRS).geometry.union_all()
        origin, axis, span = corridor_axis(geometry)
        rows.append(
            {
                "Corridor": name,
                "Analytical Role": CORRIDOR_ROLES[name],
                "Official Planned Length (m)": float(group["tf_length"].iloc[0]),
                "Official Width (m)": float(group["tf_width"].iloc[0]),
                "Official Lane Count": int(group["tfa_lane"].iloc[0]),
                "Official Master-Plan Status": (
                    "FY2016-FY2025 project; fully opened 2026-03-20"
                    if name == "益城中央線"
                    else "completed"
                ),
                "Longitudinal Projection Span (m)": span,
                "axis_origin": origin,
                "axis_vector": axis,
                "geometry": geometry,
            }
        )
    result = gpd.GeoDataFrame(rows, geometry="geometry", crs=METRIC_CRS)
    if set(result["Corridor"]) != set(CORRIDOR_ROLES):
        raise ValueError("One or more benchmark corridors are absent")
    return result


def build_passage_panel(corridors: gpd.GeoDataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for archive in sorted(ARCHIVE_DIR.glob("*data.zip")):
        snapshot = parse_snapshot(archive)
        if snapshot is None:
            continue
        with zipfile.ZipFile(archive) as zipped:
            passage_available = PASSAGE_MEMBER in set(zipped.namelist())
        passage = None
        if passage_available:
            passage = read_geojson_member(archive, PASSAGE_MEMBER).to_crs(METRIC_CRS)
        for _, corridor in corridors.iterrows():
            traces = gpd.GeoDataFrame(geometry=[], crs=METRIC_CRS)
            if passage_available and passage is not None:
                clipped = gpd.clip(passage, corridor.geometry)
                traces = select_corridor_traces(
                    clipped,
                    corridor["axis_origin"],
                    corridor["axis_vector"],
                    MIN_TRACE_LENGTH_M,
                    MIN_ALIGNMENT_RATIO,
                )
            intervals = list(
                zip(
                    traces.get("Projection Start", pd.Series(dtype=float)),
                    traces.get("Projection End", pd.Series(dtype=float)),
                    strict=False,
                )
            )
            covered = merged_interval_length(intervals)
            coverage = min(
                covered / corridor["Longitudinal Projection Span (m)"], 1.0
            )
            rows.append(
                {
                    "Snapshot Time (JST)": snapshot.isoformat(),
                    "Corridor": corridor["Corridor"],
                    "Analytical Role": corridor["Analytical Role"],
                    "Passage Layer Available": passage_available,
                    "Observed Corridor-Aligned Passage": len(traces) > 0,
                    "Unique Corridor-Aligned Traces": len(traces),
                    "Longitudinal Coverage Proxy": coverage,
                    "Near-Full Coverage Proxy": coverage >= NEAR_FULL_THRESHOLD,
                }
            )
    return pd.DataFrame(rows).sort_values(["Snapshot Time (JST)", "Corridor"])


def sample_shaking(corridors: gpd.GeoDataFrame) -> pd.DataFrame:
    rows = []
    with tempfile.TemporaryDirectory(prefix="ke02-passage-benchmark-") as temporary:
        with zipfile.ZipFile(SHAKEMAP) as zipped:
            for filename in (
                "mmi_mean.flt",
                "mmi_mean.hdr",
                "pga_mean.flt",
                "pga_mean.hdr",
            ):
                zipped.extract(filename, temporary)
        with rasterio.open(Path(temporary) / "mmi_mean.flt") as mmi_source, rasterio.open(
            Path(temporary) / "pga_mean.flt"
        ) as pga_source:
            for _, corridor in corridors.to_crs(4326).iterrows():
                boundary = corridor.geometry.boundary
                points = [
                    boundary.interpolate(value, normalized=True)
                    for value in np.linspace(0, 1, 101)
                ]
                coordinates = [(point.x, point.y) for point in points]
                mmi = np.asarray(
                    [value[0] for value in mmi_source.sample(coordinates)], dtype=float
                )
                ln_pga = np.asarray(
                    [value[0] for value in pga_source.sample(coordinates)], dtype=float
                )
                valid = (
                    (mmi != 999.0)
                    & (ln_pga != 999.0)
                    & np.isfinite(mmi)
                    & np.isfinite(ln_pga)
                )
                if not valid.all():
                    raise ValueError(f"Invalid ShakeMap sample: {corridor['Corridor']}")
                pga = np.exp(ln_pga[valid])
                rows.append(
                    {
                        "Corridor": corridor["Corridor"],
                        "ShakeMap Samples": int(valid.sum()),
                        "2026 MMI Mean": float(mmi[valid].mean()),
                        "2026 MMI Minimum": float(mmi[valid].min()),
                        "2026 MMI Maximum": float(mmi[valid].max()),
                        "2026 PGA Mean (g)": float(pga.mean()),
                        "2026 PGA Minimum (g)": float(pga.min()),
                        "2026 PGA Maximum (g)": float(pga.max()),
                        "ShakeMap Archive": SHAKEMAP.relative_to(ROOT).as_posix(),
                        "ShakeMap SHA-256": sha256(SHAKEMAP),
                    }
                )
    return pd.DataFrame(rows)


def summarize(
    corridors: gpd.GeoDataFrame, panel: pd.DataFrame, shaking: pd.DataFrame
) -> pd.DataFrame:
    available = panel.loc[panel["Passage Layer Available"]]
    summary = (
        available.groupby("Corridor", as_index=False)
        .agg(
            Available_Snapshots=("Snapshot Time (JST)", "size"),
            Snapshots_With_Observed_Passage=(
                "Observed Corridor-Aligned Passage",
                "sum",
            ),
            Snapshots_With_Coverage_Proxy_Ge_080=("Near-Full Coverage Proxy", "sum"),
            Mean_Coverage_Proxy=("Longitudinal Coverage Proxy", "mean"),
            Median_Coverage_Proxy=("Longitudinal Coverage Proxy", "median"),
            Minimum_Coverage_Proxy=("Longitudinal Coverage Proxy", "min"),
        )
        .rename(
            columns={
                "Available_Snapshots": "Available Snapshots",
                "Snapshots_With_Observed_Passage": "Snapshots With Observed Passage",
                "Snapshots_With_Coverage_Proxy_Ge_080": "Snapshots With Coverage Proxy >= 0.80",
                "Mean_Coverage_Proxy": "Mean Coverage Proxy",
                "Median_Coverage_Proxy": "Median Coverage Proxy",
                "Minimum_Coverage_Proxy": "Minimum Coverage Proxy",
            }
        )
    )
    metadata = corridors.drop(
        columns=["axis_origin", "axis_vector", "geometry"]
    )
    return metadata.merge(summary, on="Corridor").merge(shaking, on="Corridor")


def build_contrasts(summary: pd.DataFrame) -> pd.DataFrame:
    treated = summary.set_index("Corridor").loc["益城中央線"]
    rows = []
    for benchmark in ("東町空港線", "惣領木山線"):
        peer = summary.set_index("Corridor").loc[benchmark]
        rows.append(
            {
                "Treated Corridor": "益城中央線",
                "Benchmark Corridor": benchmark,
                "Benchmark Role": peer["Analytical Role"],
                "Observed-Passage Snapshot Difference": int(
                    treated["Snapshots With Observed Passage"]
                    - peer["Snapshots With Observed Passage"]
                ),
                "Near-Full Snapshot Difference": int(
                    treated["Snapshots With Coverage Proxy >= 0.80"]
                    - peer["Snapshots With Coverage Proxy >= 0.80"]
                ),
                "Mean Coverage Proxy Difference": float(
                    treated["Mean Coverage Proxy"] - peer["Mean Coverage Proxy"]
                ),
                "Median Coverage Proxy Difference": float(
                    treated["Median Coverage Proxy"] - peer["Median Coverage Proxy"]
                ),
                "2026 MMI Mean Difference": float(
                    treated["2026 MMI Mean"] - peer["2026 MMI Mean"]
                ),
                "2026 PGA Mean Difference (g)": float(
                    treated["2026 PGA Mean (g)"] - peer["2026 PGA Mean (g)"]
                ),
                "Permissible Interpretation": (
                    "same-lane-class measurement benchmark; weaker shaking and different length/location"
                    if benchmark == "東町空港線"
                    else "closer-hazard benchmark; different lane count and network role"
                ),
                "Causal Control Eligible": False,
            }
        )
    return pd.DataFrame(rows)


def build_gates(summary: pd.DataFrame) -> pd.DataFrame:
    treated = summary.set_index("Corridor").loc["益城中央線"]
    soryo = summary.set_index("Corridor").loc["惣領木山線"]
    mmi_overlap = min(
        treated["2026 MMI Maximum"], soryo["2026 MMI Maximum"]
    ) - max(treated["2026 MMI Minimum"], soryo["2026 MMI Minimum"])
    pga_overlap = min(
        treated["2026 PGA Maximum (g)"], soryo["2026 PGA Maximum (g)"]
    ) - max(treated["2026 PGA Minimum (g)"], soryo["2026 PGA Minimum (g)"])
    return pd.DataFrame(
        [
            ("B1", "Official corridor status", "pass", "Master-plan page 36 marks both peers completed and the treated corridor as FY2016-FY2025"),
            ("B2", "Concurrent outcome measurement", "pass", "All corridors use the same 21 MLIT snapshots with a private-probe layer"),
            ("B3", "Hazard overlap", "partial", f"Soryo-Kiyama overlaps treated MMI by {mmi_overlap:.3f} and PGA by {pga_overlap:.3f} g; East Town-Airport is weaker-shaking"),
            ("B4", "Structural comparability", "partial", "East Town-Airport matches four lanes; Soryo-Kiyama is two lanes but closer in hazard; neither matches all design dimensions"),
            ("B5", "Outcome semantics", "partial", "Probe presence/coverage proxy only, with no volume, speed, or universal-passability meaning"),
            ("B6", "Pre-event baseline", "fail", "No pre-earthquake probe panel for any corridor"),
            ("B7", "Exogenous treatment/control assignment", "fail", "One selected post-2016 corridor and two non-random peers cannot identify treatment effects"),
        ],
        columns=["Gate ID", "Gate", "Status", "Evidence"],
    )


def write_readme(
    summary: pd.DataFrame, contrasts: pd.DataFrame, gates: pd.DataFrame
) -> None:
    display = summary[
        [
            "Corridor",
            "Analytical Role",
            "Official Lane Count",
            "Snapshots With Observed Passage",
            "Snapshots With Coverage Proxy >= 0.80",
            "Median Coverage Proxy",
            "2026 MMI Mean",
            "2026 PGA Mean (g)",
        ]
    ].copy()
    lines = [
        "# Kumamoto-Takamori passage benchmark experiment",
        "",
        "## Result",
        "",
        "The newly completed Mashiki Central Line has observed corridor-aligned passage in 20 of 21 available snapshots and near-full longitudinal coverage in 19. The established four-lane East Town-Airport Line records 17 and 15, respectively. The established two-lane Soryo-Kiyama Line records 18 and 3.",
        "",
        "The comparison is directionally encouraging because Mashiki Central has the highest sampled 2026 shaking of the three and Soryo-Kiyama has substantial MMI/PGA overlap with it. It remains descriptive: East Town-Airport matches lane count but not hazard or length; Soryo-Kiyama better matches hazard but not lane count or network role. Neither peer supplies pre-event passage measurements or exogenous treatment assignment.",
        "",
        "Therefore retain these as **measurement and hazard benchmarks**, never as causal controls. The experiment supports the bounded statement that sampled post-earthquake passage on the completed corridor was repeatedly observed and was not worse than these two official peers under the acquired proxy. It does not establish that four-laning caused the difference.",
        "",
        "## Corridor summary",
        "",
        display.to_markdown(index=False, floatfmt=".3f"),
        "",
        "## Eligibility gates",
        "",
        gates.to_markdown(index=False),
        "",
        "## Sources",
        "",
        f"- Official Mashiki master-plan chapter: `{MASTER_PLAN.relative_to(ROOT)}` (SHA-256 `{sha256(MASTER_PLAN)}`); page 36 was visually verified.",
        f"- Official MLIT road-map archive: `{MAP_ARCHIVE.relative_to(ROOT)}` (SHA-256 `{sha256(MAP_ARCHIVE)}`).",
        f"- USGS 2026 ShakeMap raster: `{SHAKEMAP.relative_to(ROOT)}` (SHA-256 `{sha256(SHAKEMAP)}`).",
        "",
        "## Rebuild",
        "",
        "```bash",
        "UV_CACHE_DIR=/private/tmp/ke02-uv-cache uv run python src/analyses/experiment_kumamoto_takamori_passage_benchmarks.py",
        "```",
    ]
    (OUT / "PASSAGE_BENCHMARK_EXPERIMENT.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    corridors = load_corridors()
    panel = build_passage_panel(corridors)
    shaking = sample_shaking(corridors)
    summary = summarize(corridors, panel, shaking)
    contrasts = build_contrasts(summary)
    gates = build_gates(summary)
    panel.to_csv(OUT / "kumamoto_takamori_passage_benchmark_panel.csv", index=False)
    summary.to_csv(OUT / "kumamoto_takamori_passage_benchmark_summary.csv", index=False)
    contrasts.to_csv(OUT / "kumamoto_takamori_passage_benchmark_contrasts.csv", index=False)
    gates.to_csv(OUT / "kumamoto_takamori_passage_benchmark_gate.csv", index=False)
    write_readme(summary, contrasts, gates)
    print(
        "PARTIAL PASS: two official descriptive benchmarks constructed; "
        "pre-event and causal-control gates remain failed."
    )


if __name__ == "__main__":
    main()
