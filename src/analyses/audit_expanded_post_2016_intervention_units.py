#!/usr/bin/env python3
"""Expand exact post-2016 road-intervention units without over-assigning geometry."""
from __future__ import annotations

import subprocess
import zipfile
from pathlib import Path

import geopandas as gpd
import pandas as pd

from audit_kumamoto_takamori_probe_passage import (
    ARCHIVE_DIR,
    METRIC_CRS,
    MIN_ALIGNMENT_RATIO,
    MIN_TRACE_LENGTH_M,
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
KT_GEOMETRY = (
    ROOT
    / "data/exp/feasibility-check/intervention-geometry/"
    "kumamoto_takamori_intervention_corridor.parquet"
)
KT_PASSAGE = (
    ROOT
    / "data/exp/feasibility-check/intervention-geometry/"
    "kumamoto_takamori_probe_passage_snapshots.csv"
)
SOURCES = {
    "INT-EW3": {
        "path": ROOT
        / "data/raw/official_resilience/interventions/"
        "mashiki_east_west_section3_opening_newsletter_2025.pdf",
        "terms": ("益城東西線", "3月16日", "244"),
    },
    "INT-2NS1": {
        "path": ROOT
        / "data/raw/official_resilience/interventions/"
        "mashiki_second_north_south_opening_council_2026.pdf",
        "terms": ("第２南北線１工区", "２月22日", "一部が開通"),
    },
    "INT-YOKOMACHI": {
        "path": ROOT
        / "data/raw/official_resilience/interventions/"
        "mashiki_yokomachi_kiyama_bridge_opening_council_2023.pdf",
        "terms": ("横町線", "９月３日", "供用を開始"),
    },
}
OUT = ROOT / "data/exp/feasibility-check/intervention-geometry"


def verify_pdf(source: dict[str, object]) -> None:
    path = source["path"]
    result = subprocess.run(
        ["pdftotext", "-layout", str(path), "-"],
        check=True,
        capture_output=True,
        text=True,
    )
    compact = result.stdout.replace(" ", "")
    missing = [term for term in source["terms"] if term not in compact]
    if missing:
        raise ValueError(f"{path.name} is missing bound terms: {missing}")


def build_inventory() -> tuple[pd.DataFrame, gpd.GeoDataFrame]:
    for source in SOURCES.values():
        verify_pdf(source)
    facilities = gpd.read_file(FACILITIES).to_crs(METRIC_CRS)
    ew = facilities.loc[
        facilities["tf_name"].eq("益城東西線") & facilities["OBJECTID"].eq(15)
    ].copy()
    if len(ew) != 1:
        raise ValueError("Expected one East-West Line OBJECTID 15 polygon")
    _, _, ew_span = corridor_axis(ew.geometry.iloc[0])
    if abs(ew_span - 244.0) > 15.0:
        raise ValueError(f"East-West section span does not match 244 m: {ew_span}")

    kt = gpd.read_parquet(KT_GEOMETRY).to_crs(METRIC_CRS)
    kt_geometry = kt.geometry.iloc[0]
    ew_geometry = ew.geometry.iloc[0]
    if not kt_geometry.disjoint(ew_geometry):
        raise ValueError("The two exact intervention polygons unexpectedly overlap")

    inventory = pd.DataFrame(
        [
            {
                "Intervention Unit ID": "INT-KT-FOUR-LANING",
                "Intervention": "Kumamoto-Takamori four-laning / Mashiki Central Line",
                "Opening Date": "2026-03-20",
                "Reported Opened Length (m)": 3800.0,
                "Official Geometry Feature": "益城中央線 OBJECTID 2",
                "Geometry Match": "official aggregate planning polygon",
                "Geometry Eligible": True,
                "Outcome Eligible": True,
                "Independent Project Unit": True,
                "Eligibility": "eligible_descriptive_treatment_unit",
                "Binding Gap": "one selected corridor; no pre-event baseline or causal control",
            },
            {
                "Intervention Unit ID": "INT-EW3",
                "Intervention": "Mashiki East-West Line section 3",
                "Opening Date": "2025-03-16",
                "Reported Opened Length (m)": 244.0,
                "Official Geometry Feature": "益城東西線 OBJECTID 15",
                "Geometry Match": f"official polygon longitudinal span {ew_span:.1f} m",
                "Geometry Eligible": True,
                "Outcome Eligible": True,
                "Independent Project Unit": True,
                "Eligibility": "eligible_descriptive_treatment_unit",
                "Binding Gap": "short segment; sparse probe passage; no pre-event baseline or causal control",
            },
            {
                "Intervention Unit ID": "INT-YOKOMACHI",
                "Intervention": "Yokomachi Line Kiyama Bridge and surrounding roads",
                "Opening Date": "2023-09-03",
                "Reported Opened Length (m)": pd.NA,
                "Official Geometry Feature": "横町線 OBJECTID 5 is the full 650 m plan",
                "Geometry Match": "opening record does not define the completed subsegment boundary",
                "Geometry Eligible": False,
                "Outcome Eligible": False,
                "Independent Project Unit": True,
                "Eligibility": "pending_exact_opened_subsegment_geometry",
                "Binding Gap": "partial opening cannot be assigned the full planning polygon",
            },
            {
                "Intervention Unit ID": "INT-2NS1",
                "Intervention": "Second North-South Line section 1 partial opening",
                "Opening Date": "2026-02-22",
                "Reported Opened Length (m)": pd.NA,
                "Official Geometry Feature": "第二南北線 OBJECTID 9 is the full 810 m plan",
                "Geometry Match": "opening record says part of section 1 without an exact boundary",
                "Geometry Eligible": False,
                "Outcome Eligible": False,
                "Independent Project Unit": True,
                "Eligibility": "pending_exact_opened_subsegment_geometry",
                "Binding Gap": "partial opening cannot be assigned the full planning polygon",
            },
        ]
    )
    exact = gpd.GeoDataFrame(
        [
            {
                "Intervention Unit ID": "INT-KT-FOUR-LANING",
                "Intervention": inventory.iloc[0]["Intervention"],
                "Opening Date": pd.Timestamp("2026-03-20"),
                "Official Geometry Feature": "益城中央線 OBJECTID 2",
                "geometry": kt_geometry,
            },
            {
                "Intervention Unit ID": "INT-EW3",
                "Intervention": inventory.iloc[1]["Intervention"],
                "Opening Date": pd.Timestamp("2025-03-16"),
                "Official Geometry Feature": "益城東西線 OBJECTID 15",
                "geometry": ew_geometry,
            },
        ],
        geometry="geometry",
        crs=METRIC_CRS,
    )
    return inventory, exact


def east_west_passage(geometry: object) -> pd.DataFrame:
    origin, axis, span = corridor_axis(geometry)
    rows = []
    for archive in sorted(ARCHIVE_DIR.glob("*data.zip")):
        snapshot = parse_snapshot(archive)
        if snapshot is None:
            continue
        with zipfile.ZipFile(archive) as zipped:
            available = PASSAGE_MEMBER in set(zipped.namelist())
        traces = gpd.GeoDataFrame(geometry=[], crs=METRIC_CRS)
        if available:
            passage = read_geojson_member(archive, PASSAGE_MEMBER).to_crs(METRIC_CRS)
            traces = select_corridor_traces(
                gpd.clip(passage, geometry),
                origin,
                axis,
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
        rows.append(
            {
                "Snapshot Time (JST)": snapshot.isoformat(),
                "Intervention Unit ID": "INT-EW3",
                "Passage Layer Available": available,
                "Observed Corridor-Aligned Passage": len(traces) > 0,
                "Unique Corridor-Aligned Traces": len(traces),
                "Longitudinal Coverage Proxy": min(
                    merged_interval_length(intervals) / span, 1.0
                ),
            }
        )
    return pd.DataFrame(rows)


def build_outcome_summary(east_west: pd.DataFrame) -> pd.DataFrame:
    kt = pd.read_csv(KT_PASSAGE)
    kt_available = kt.loc[kt["Passage Layer Available"]]
    ew_available = east_west.loc[east_west["Passage Layer Available"]]
    return pd.DataFrame(
        [
            {
                "Intervention Unit ID": "INT-KT-FOUR-LANING",
                "Available Snapshots": len(kt_available),
                "Snapshots With Observed Passage": int(
                    kt_available["Observed Corridor-Aligned Passage"].sum()
                ),
                "Snapshots With Coverage Proxy >= 0.80": int(
                    kt_available["Longitudinal Coverage Proxy"].ge(0.80).sum()
                ),
                "Median Coverage Proxy": float(
                    kt_available["Longitudinal Coverage Proxy"].median()
                ),
            },
            {
                "Intervention Unit ID": "INT-EW3",
                "Available Snapshots": len(ew_available),
                "Snapshots With Observed Passage": int(
                    ew_available["Observed Corridor-Aligned Passage"].sum()
                ),
                "Snapshots With Coverage Proxy >= 0.80": int(
                    ew_available["Longitudinal Coverage Proxy"].ge(0.80).sum()
                ),
                "Median Coverage Proxy": float(
                    ew_available["Longitudinal Coverage Proxy"].median()
                ),
            },
        ]
    )


def build_gates(inventory: pd.DataFrame, outcomes: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            ("E1", "Official pre-event opening", "pass", "Four post-2016 project openings are officially dated before the 2026 earthquake"),
            ("E2", "Exact treatment geometry", "partial", f"{int(inventory['Geometry Eligible'].sum())}/4 candidates have defensible exact or aggregate geometry"),
            ("E3", "Repeated route-consistent outcome", "pass", "Both geometry-eligible units have repeated MLIT probe observations, including explicit non-observation"),
            ("E4", "Independent treatment units", "partial", "Two spatially disjoint project units; network dependence and common policy origin remain"),
            ("E5", "Outcome consistency", "fail", f"Observed-passage snapshots differ sharply: {int(outcomes.iloc[0]['Snapshots With Observed Passage'])}/21 versus {int(outcomes.iloc[1]['Snapshots With Observed Passage'])}/21"),
            ("E6", "Pre-event baseline and causal controls", "fail", "Neither exact unit has pre-event probe outcomes or an exogenous matched control"),
            ("E7", "Common resilience effect", "fail", "Two selected and heterogeneous units cannot identify a common treatment effect"),
        ],
        columns=["Gate ID", "Gate", "Status", "Evidence"],
    )


def write_readme(
    inventory: pd.DataFrame, outcomes: pd.DataFrame, gates: pd.DataFrame
) -> None:
    lines = [
        "# Expanded post-2016 intervention-unit audit",
        "",
        "## Result",
        "",
        "The verified intervention sample increases from one to two geometry-eligible project units. The second is Mashiki East-West Line section 3: the official opening record reports 244 m opened on 16 March 2025, and official ArcGIS feature OBJECTID 15 has a 235.7 m longitudinal span and no overlap with the Mashiki Central Line polygon.",
        "",
        "The additional unit does not stabilize a common effect. Mashiki Central records corridor-aligned passage in 20/21 available snapshots, whereas East-West section 3 records it in only 3/21. This is useful falsification evidence: the probe outcome is not mechanically saturated and post-2016 construction does not imply uniformly strong observed passage.",
        "",
        "Yokomachi/Kiyama Bridge and Second North-South section 1 remain candidate units only. Their official records confirm partial openings before the earthquake, but the opened subsegment boundaries cannot be assigned to the entire planning polygons.",
        "",
        "## Candidate inventory",
        "",
        inventory.to_markdown(index=False),
        "",
        "## Outcome summary",
        "",
        outcomes.to_markdown(index=False, floatfmt=".3f"),
        "",
        "## Gates",
        "",
        gates.to_markdown(index=False),
        "",
        "## Rebuild",
        "",
        "```bash",
        "UV_CACHE_DIR=/private/tmp/ke02-uv-cache uv run python src/analyses/audit_expanded_post_2016_intervention_units.py",
        "```",
    ]
    (OUT / "EXPANDED_INTERVENTION_UNIT_AUDIT.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def main() -> None:
    inventory, exact = build_inventory()
    east_west = east_west_passage(exact.loc[exact["Intervention Unit ID"].eq("INT-EW3")].geometry.iloc[0])
    outcomes = build_outcome_summary(east_west)
    gates = build_gates(inventory, outcomes)
    inventory.to_csv(OUT / "expanded_post_2016_intervention_inventory.csv", index=False)
    exact.to_crs(4326).to_parquet(
        OUT / "expanded_post_2016_intervention_geometries.parquet", index=False
    )
    east_west.to_csv(OUT / "east_west_section3_probe_passage_snapshots.csv", index=False)
    outcomes.to_csv(OUT / "expanded_post_2016_intervention_outcomes.csv", index=False)
    gates.to_csv(OUT / "expanded_post_2016_intervention_gate.csv", index=False)
    write_readme(inventory, outcomes, gates)
    print(
        "PARTIAL PASS: exact treatment units increased from 1 to 2; "
        "strong outcome heterogeneity and causal-design failures remain."
    )


if __name__ == "__main__":
    main()
