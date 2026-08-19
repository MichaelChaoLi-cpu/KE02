#!/usr/bin/env python3
"""Screen post-2016 Mashiki road projects for repeated-shock support.

This is a permissive candidate screen, not an eligibility decision.  It uses
the complete matched official road geometry to find projects worth exact
subsegment reconstruction.  A whole-route match must never be interpreted as
evidence that the reported completed project section itself was affected.
"""
from __future__ import annotations

import zipfile
import unicodedata
from pathlib import Path

import geopandas as gpd
import pandas as pd

from audit_kumamoto_takamori_probe_passage import (
    ARCHIVE_DIR,
    PASSAGE_MEMBER,
    parse_snapshot,
    read_geojson_member,
)


ROOT = Path(__file__).resolve().parents[2]
INTERVENTIONS = (
    ROOT / "data/processed/mashiki_resilience_interventions_preprocessed.parquet"
)
ROAD_NETWORK = (
    ROOT / "data/processed/mashiki_official_road_network_preprocessed.parquet"
)
PLANNING_FACILITIES = (
    ROOT
    / "data/raw/official_resilience/mashiki_arcgis/"
    "mashiki_urban_planning_transport_facilities.geojson"
)
NIED_2016 = (
    ROOT
    / "data/exp/feasibility-check/nied-2016-road-condition/"
    "nied_2016_kumamoto_road_condition.geojson"
)
OUT = ROOT / "data/exp/feasibility-check/additional-intervention-screen"
METRIC_CRS = 6670
PASSAGE_BUFFER_M = 30.0
MIN_PASSAGE_INTERSECTION_M = 25.0


def normalize_name(value: object) -> str:
    return "".join(
        unicodedata.normalize("NFKC", str(value)).replace("　", " ").split()
    )


def route_is_compatible(intervention_id: str, official: str, nied: str) -> bool:
    aliases = {
        "I001": {"熊本高森線"},
        "I002": {"熊本高森線"},
        "I003": {"熊本高森線"},
    }
    expected = aliases.get(intervention_id, {normalize_name(official)})
    return normalize_name(nied) in expected


def load_passage_snapshots() -> list[tuple[pd.Timestamp, gpd.GeoDataFrame]]:
    layers: list[tuple[pd.Timestamp, gpd.GeoDataFrame]] = []
    for archive in sorted(ARCHIVE_DIR.glob("*data.zip")):
        snapshot = parse_snapshot(archive)
        if snapshot is None:
            continue
        with zipfile.ZipFile(archive) as zipped:
            if PASSAGE_MEMBER not in set(zipped.namelist()):
                continue
        layer = read_geojson_member(archive, PASSAGE_MEMBER).to_crs(METRIC_CRS)
        layers.append((snapshot, layer))
    return layers


def stable_nied_sites() -> gpd.GeoDataFrame:
    nied = gpd.read_file(NIED_2016).to_crs(METRIC_CRS)
    nied["Geometry Key"] = nied.geometry.map(lambda value: value.wkb_hex)
    return nied.drop_duplicates("Geometry Key").copy()


def screen() -> pd.DataFrame:
    interventions = pd.read_parquet(INTERVENTIONS)
    roads = gpd.read_parquet(ROAD_NETWORK).to_crs(METRIC_CRS)
    facilities = gpd.read_file(PLANNING_FACILITIES).to_crs(METRIC_CRS)
    nied = stable_nied_sites()
    passage_layers = load_passage_snapshots()
    rows: list[dict[str, object]] = []

    matched = interventions.loc[
        interventions["Matched Official Feature IDs"].notna()
        & interventions["Completed Before 2026 Event"]
    ].copy()
    for _, intervention in matched.iterrows():
        feature_id = int(intervention["Matched Official Feature IDs"])
        layer_name = intervention["Matched Network Layer"]
        if layer_name == "Mashiki Official Road Network":
            selected = roads.loc[roads["Road Segment ID"].eq(feature_id)]
            official_name_column = "Route Name"
        elif layer_name == "Mashiki Urban Planning Transport Facilities":
            selected = facilities.loc[facilities["OBJECTID"].eq(feature_id)]
            official_name_column = "tf_name"
        else:
            raise ValueError(f"Unsupported matched network layer: {layer_name}")
        if len(selected) != 1:
            raise ValueError(
                f"Expected one official feature {feature_id} in {layer_name}"
            )
        road = selected.geometry.iloc[0]
        official_name = str(selected.iloc[0][official_name_column]).strip()
        distances = nied.geometry.distance(road)
        nearest_index = distances.idxmin()
        nearest = nied.loc[nearest_index]
        nearest_route = str(nearest.get("路線_路線", "")).strip()
        compatible = route_is_compatible(
            str(intervention["Intervention ID"]), official_name, nearest_route
        )
        corridor = road.buffer(PASSAGE_BUFFER_M)
        observed_snapshots = 0
        intersection_lengths: list[float] = []
        for _, passage in passage_layers:
            candidates = passage.loc[passage.geometry.intersects(corridor)]
            if candidates.empty:
                continue
            clipped = candidates.geometry.intersection(corridor)
            length = float(clipped.length.sum())
            if length >= MIN_PASSAGE_INTERSECTION_M:
                observed_snapshots += 1
                intersection_lengths.append(length)
        rows.append(
            {
                "Intervention ID": intervention["Intervention ID"],
                "Area": intervention["Area"],
                "Asset Name": intervention["Asset Name"],
                "Completion Status": intervention[
                    "Completion Status at 2026 Event"
                ],
                "Completed Extent (m)": intervention["Completed Extent (m)"],
                "Official Road Feature ID": feature_id,
                "Official Source Layer": layer_name,
                "Official Road Name": official_name,
                "Full Official Road Length (m)": float(road.length),
                "Nearest 2016 Point Distance (m)": float(distances.min()),
                "2016 Unique Points Within 50 m": int(distances.le(50).sum()),
                "2016 Unique Points Within 100 m": int(distances.le(100).sum()),
                "2016 Unique Points Within 250 m": int(distances.le(250).sum()),
                "Nearest 2016 Route": nearest_route,
                "2016 Route Compatible": compatible,
                "Nearest 2016 Start Location": str(
                    nearest.get("箇所_始点", "")
                ).strip(),
                "Nearest 2016 End Location": str(
                    nearest.get("箇所_終点", "")
                ).strip(),
                "2026 Passage-Layer Snapshots": len(passage_layers),
                "2026 Snapshots With Full-Road Passage": observed_snapshots,
                "Median Full-Road Passage Intersection (m)": (
                    float(pd.Series(intersection_lengths).median())
                    if intersection_lengths
                    else 0.0
                ),
                "Exact Project Geometry Available": bool(
                    intervention["Geometry Use Eligible"]
                ),
                "Screen Status": (
                    "priority_exact_subsegment_reconstruction"
                    if compatible and distances.min() <= 100 and observed_snapshots > 0
                    else (
                        "secondary_spatial_candidate"
                        if compatible
                        and distances.min() <= 250
                        and observed_snapshots > 0
                        else (
                            "fail_route_mismatch_spatial_proximity"
                            if distances.min() <= 250 and observed_snapshots > 0
                            else "fail_initial_repeated_shock_screen"
                        )
                    )
                ),
                "Interpretation Boundary": (
                    "whole official road screened; exact completed subsegment still required"
                ),
            }
        )
    result = pd.DataFrame(rows)
    return result.sort_values(
        [
            "Screen Status",
            "Nearest 2016 Point Distance (m)",
            "Intervention ID",
        ]
    ).reset_index(drop=True)


def write_readme(result: pd.DataFrame) -> None:
    priority = result.loc[
        result["Screen Status"].eq("priority_exact_subsegment_reconstruction")
    ]
    secondary = result.loc[
        result["Screen Status"].eq("secondary_spatial_candidate")
    ]
    lines = [
        "# Additional intervention-unit candidate screen",
        "",
        "## Purpose",
        "",
        "This is a permissive whole-road screen for deciding which official project maps deserve exact subsegment reconstruction. It is not an intervention sample and does not make a treatment-effect claim.",
        "",
        "## Result",
        "",
        f"The official road-name linkage covers {len(result)} post-2016 project records. {len(priority)} pass the priority screen (a route-compatible stable 2016 restriction point within 100 m and positive 2026 passage somewhere on the matched official road), and {len(secondary)} pass only the 100-250 m secondary screen.",
        "",
        "Projects sharing one road feature are not independent units. Full-road passage and a nearby 2016 point only justify reconstructing the exact completed section from the official project figure. They do not show that the treatment section itself experienced either observation.",
        "",
        "## Screen",
        "",
        result.to_markdown(index=False, floatfmt=".1f"),
        "",
        "## Next gate",
        "",
        "For each priority project: recover exact endpoints from the official project map; intersect that reconstructed subsegment with the 2016 NIED point archive and the 2026 probe traces; reject the project if either positive observation falls outside the exact subsegment.",
        "",
        "## Rebuild",
        "",
        "```bash",
        "UV_CACHE_DIR=/private/tmp/ke02-uv-cache uv run python src/analyses/screen_additional_intervention_units.py",
        "```",
    ]
    (OUT / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    result = screen()
    result.to_csv(OUT / "candidate_screen.csv", index=False)
    write_readme(result)
    print(OUT / "README.md")


if __name__ == "__main__":
    main()
