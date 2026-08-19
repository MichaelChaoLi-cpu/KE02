#!/usr/bin/env python3
"""Audit the Kumamoto-Takamori four-laning corridor as an intervention geometry.

This is a feasibility audit, not an effect estimator. It tests whether an
official post-2016 resilience intervention can be assigned a defensible
aggregate geometry and whether the current 2026 outcome archive can support a
treatment/comparison design on that geometry.
"""
from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

import geopandas as gpd
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
FACILITIES = (
    ROOT
    / "data/raw/official_resilience/mashiki_arcgis/"
    "mashiki_urban_planning_transport_facilities.geojson"
)
FACILITIES_METADATA = (
    ROOT
    / "data/raw/official_resilience/mashiki_arcgis/"
    "mashiki_urban_planning_transport_facilities_metadata.json"
)
ROADMAP = (
    ROOT
    / "data/raw/official_resilience/interventions/"
    "kumamoto_takamori_four_laning_recovery_roadmap_2026.pdf"
)
INTERVENTIONS = ROOT / "data/exp/feasibility-check/candidate_intervention_ledger.csv"
RESTRICTIONS = (
    ROOT / "data/processed/kumamoto_2026_road_restriction_snapshots_preprocessed.parquet"
)
OUT = ROOT / "data/exp/feasibility-check/intervention-geometry"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_completion_source() -> None:
    result = subprocess.run(
        ["pdftotext", "-layout", str(ROADMAP), "-"],
        check=True,
        capture_output=True,
        text=True,
    )
    compact = result.stdout.replace(" ", "")
    required = ["県道熊本高森線４車線化", "2026年3月20日", "約3.8km"]
    missing = [term for term in required if term not in compact]
    if missing:
        raise ValueError(f"Completion source is missing required terms: {missing}")


def build_geometry() -> gpd.GeoDataFrame:
    facilities = gpd.read_file(FACILITIES)
    selected = facilities.loc[facilities["tf_name"].eq("益城中央線")].copy()
    if len(selected) != 1:
        raise ValueError("Expected exactly one official Mashiki Central Line feature")
    row = selected.iloc[0]
    if not row.geometry.is_valid:
        raise ValueError("Official intervention corridor geometry is invalid")
    if str(row["tf_length"]) != "3510" or str(row["tf_width"]) != "27":
        raise ValueError("Unexpected official corridor length or width")
    if str(row["tfa_lane"]) != "4":
        raise ValueError("Unexpected official lane count")

    output = gpd.GeoDataFrame(
        [
            {
                "Intervention Cluster ID": "INT-KT-FOUR-LANING",
                "Intervention Name": "Kumamoto-Takamori Line four-laning",
                "Official Planning Feature": row["tf_name"],
                "Official Feature ID": int(row["OBJECTID"]),
                "Planning Decision Date": pd.Timestamp(row["tf_from"]),
                "Planning Notice": row["tf_f_num"],
                "Official Start Location": row["tf_start"],
                "Official End Location": row["tf_end"],
                "Official Planned Length (m)": float(row["tf_length"]),
                "Official Planned Width (m)": float(row["tf_width"]),
                "Official Lane Count": int(row["tfa_lane"]),
                "Reported Project Length (m)": 3800.0,
                "Full Opening Date": pd.Timestamp("2026-03-20"),
                "Completed Before 2026 Event": True,
                "Geometry Role": "official_aggregate_planning_corridor_polygon",
                "Geometry Use Eligible": True,
                "Treatment Use Eligible": True,
                "Treatment Unit Count": 1,
                "Geometry Source": FACILITIES.relative_to(ROOT).as_posix(),
                "Geometry Source SHA-256": sha256(FACILITIES),
                "Geometry Metadata SHA-256": sha256(FACILITIES_METADATA),
                "Completion Source": ROADMAP.relative_to(ROOT).as_posix(),
                "Completion Source SHA-256": sha256(ROADMAP),
                "Completion Page URL": "https://www.pref.kumamoto.jp/soshiki/103/273963.html",
                "Geometry": row.geometry,
            }
        ],
        geometry="Geometry",
        crs=facilities.crs,
    )
    return output


def build_linkage_audit(corridor: gpd.GeoDataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    candidates = pd.read_csv(INTERVENTIONS)
    source_rows = candidates.loc[candidates["intervention_id"].isin(["I001", "I002", "I003"])]
    if len(source_rows) != 3:
        raise ValueError("Expected three Kumamoto-Takamori candidate segments")
    if abs(source_rows["completed_extent"].str.replace(" km", "", regex=False).astype(float).sum() - 3.8) > 1e-9:
        raise ValueError("Candidate segment lengths do not sum to the reported 3.8 km")

    restrictions = gpd.read_parquet(RESTRICTIONS)
    corridor_metric = corridor.to_crs(6670).geometry.iloc[0]
    restrictions_metric = restrictions.to_crs(6670)
    nearby = restrictions_metric.loc[
        restrictions_metric.geometry.distance(corridor_metric).le(100)
    ].copy()
    route_consistent = nearby.loc[
        nearby["Route Name"].fillna("").str.contains("熊本高森", regex=False)
    ]
    nearby_routes = "; ".join(sorted(nearby["Route Name"].dropna().unique()))

    linkage = pd.DataFrame(
        [
            {
                "Intervention Cluster ID": "INT-KT-FOUR-LANING",
                "Consolidated Candidate IDs": "; ".join(source_rows["intervention_id"]),
                "Consolidated Candidate Length (m)": 3800.0,
                "Official Planning Length (m)": corridor["Official Planned Length (m)"].iloc[0],
                "Length Difference (m)": 290.0,
                "Geometry Interpretation": "planning polygon covers the official Mashiki corridor; reported project length is approximate and includes the full project extent",
                "Nearby Restriction Feature-Snapshots (100 m)": len(nearby),
                "Nearby Restriction Record Count (100 m)": nearby["Restriction Record ID"].nunique(),
                "Nearby Reported Routes": nearby_routes,
                "Route-Consistent Restriction Record Count": route_consistent["Restriction Record ID"].nunique(),
                "Outcome Linkage Status": "fail_no_route_consistent_2026_outcome",
                "Comparison Status": "fail_one_treated_cluster_no_predeclared_comparison",
            }
        ]
    )
    gates = pd.DataFrame(
        [
            ("G1", "Official completion", "pass", "Full 3.8 km project reported open on 2026-03-20"),
            ("G2", "Official aggregate geometry", "pass", "One valid official Mashiki Central Line planning polygon; 3,510 m, 27 m, four lanes"),
            ("G3", "Temporal ordering", "pass", "Full opening precedes the 2026-07-28 earthquake"),
            ("G4", "Route-consistent 2026 outcome", "fail", "No restriction record for Kumamoto-Takamori Line; nearby records are crossing motorways"),
            ("G5", "Independent treated units", "fail", "The three staged openings form one completed corridor intervention cluster"),
            ("G6", "Comparison and common support", "fail", "No predeclared untreated corridor and no validated passability/service outcome"),
        ],
        columns=["Gate ID", "Gate", "Status", "Evidence"],
    )
    return linkage, gates


def write_readme(linkage: pd.DataFrame, gates: pd.DataFrame) -> None:
    row = linkage.iloc[0]
    lines = [
        "# Kumamoto-Takamori intervention-geometry audit",
        "",
        "## Result",
        "",
        "The aggregate intervention-geometry gate now passes for one post-2016 resilience project. The official Mashiki urban-planning layer contains one valid Mashiki Central Line corridor polygon (3,510 m planned length, 27 m width, four lanes), and the official recovery record states that the approximately 3.8 km Kumamoto-Takamori four-laning project fully opened on 20 March 2026.",
        "",
        "The three staged candidate rows I001-I003 must therefore be consolidated into one treatment cluster rather than counted as three independent interventions. This resolves the zero-geometry problem only for that aggregate corridor.",
        "",
        "## Remaining identification failure",
        "",
        f"- {int(row['Nearby Restriction Feature-Snapshots (100 m)'])} restriction feature-snapshots fall within 100 m of the polygon, but all belong to crossing motorway records ({row['Nearby Reported Routes']}).",
        "- No route-consistent 2026 restriction or verified passability/service outcome exists for the treated corridor.",
        "- One completed corridor is one treated cluster. Staged openings and internal road segments do not create independent treatment units.",
        "- No untreated comparison corridor and no hazard/common-support design have passed.",
        "",
        "Accordingly, the corridor geometry may enter a future treatment inventory, but it cannot yet enter an effect estimator.",
        "",
        "## Gate table",
        "",
        gates.to_markdown(index=False),
        "",
        "## Rebuild",
        "",
        "```bash",
        "UV_CACHE_DIR=/private/tmp/ke02-uv-cache uv run python src/analyses/audit_kumamoto_takamori_intervention_geometry.py",
        "```",
    ]
    (OUT / "INTERVENTION_GEOMETRY_AUDIT.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    verify_completion_source()
    corridor = build_geometry()
    linkage, gates = build_linkage_audit(corridor)
    corridor.to_parquet(OUT / "kumamoto_takamori_intervention_corridor.parquet", index=False)
    linkage.to_csv(OUT / "kumamoto_takamori_intervention_linkage_audit.csv", index=False)
    gates.to_csv(OUT / "kumamoto_takamori_intervention_gate.csv", index=False)
    write_readme(linkage, gates)
    print(
        "PASS: one aggregate intervention geometry recovered; outcome and comparison gates remain failed."
    )


if __name__ == "__main__":
    main()
