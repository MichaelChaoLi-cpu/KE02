#!/usr/bin/env python3
"""Test whether same-named 2016/2026 restriction records share locations."""
from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
SOURCE_2016 = (
    ROOT
    / "data/exp/feasibility-check/nied-2016-road-condition/"
    "nied_2016_kumamoto_road_condition.geojson"
)
SOURCE_2026 = (
    ROOT / "data/processed/kumamoto_2026_road_restriction_snapshots_preprocessed.parquet"
)
OUT = ROOT / "data/exp/feasibility-check/nied-2016-road-condition"
METRIC_CRS = "EPSG:6670"
EXACT_THRESHOLD_M = 250.0
SENSITIVITY_THRESHOLD_M = 1000.0


def normalize_route(value: object) -> str:
    return "".join(str(value).replace("　", " ").split()).strip()


def load_unique_sites() -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame, list[str]]:
    earlier = gpd.read_file(SOURCE_2016).to_crs(METRIC_CRS)
    current = gpd.read_parquet(SOURCE_2026).to_crs(METRIC_CRS)
    earlier["Normalized Route Name"] = earlier["路線_路線"].map(normalize_route)
    current["Normalized Route Name"] = current["Route Name"].map(normalize_route)
    shared = sorted(
        set(earlier["Normalized Route Name"])
        & set(current["Normalized Route Name"])
        - {""}
    )
    earlier = earlier.loc[earlier["Normalized Route Name"].isin(shared)].copy()
    current = current.loc[current["Normalized Route Name"].isin(shared)].copy()

    earlier["Geometry Key"] = earlier.geometry.apply(lambda value: value.wkb_hex)
    current["Geometry Key"] = current.geometry.apply(lambda value: value.wkb_hex)
    earlier = earlier.drop_duplicates(
        subset=["Normalized Route Name", "Geometry Key"]
    ).copy()
    current = current.drop_duplicates(
        subset=["Normalized Route Name", "Geometry Key"]
    ).copy()
    return earlier, current, shared


def calculate_distances(
    earlier: gpd.GeoDataFrame, current: gpd.GeoDataFrame
) -> pd.DataFrame:
    rows = []
    for _, old in earlier.iterrows():
        candidates = current.loc[
            current["Normalized Route Name"].eq(old["Normalized Route Name"])
        ].copy()
        candidates["Distance (m)"] = candidates.geometry.distance(old.geometry)
        nearest_index = candidates["Distance (m)"].idxmin()
        nearest = candidates.loc[nearest_index]
        distance = float(nearest["Distance (m)"])
        rows.append(
            {
                "Normalized Route Name": old["Normalized Route Name"],
                "2016 Start Location": str(old.get("箇所_始点", "")).strip(),
                "2016 End Location": str(old.get("箇所_終点", "")).strip(),
                "2016 Geometry Key": old["Geometry Key"],
                "Nearest 2026 Start Location": str(
                    nearest.get("Start Location", "")
                ).strip(),
                "Nearest 2026 End Location": str(
                    nearest.get("End Location", "")
                ).strip(),
                "Nearest Distance (m)": distance,
                "Within 250 m": distance <= EXACT_THRESHOLD_M,
                "Within 1 km": distance <= SENSITIVITY_THRESHOLD_M,
            }
        )
    return pd.DataFrame(rows)


def summarize(
    distances: pd.DataFrame,
    earlier: gpd.GeoDataFrame,
    current: gpd.GeoDataFrame,
    shared: list[str],
) -> pd.DataFrame:
    rows = []
    for route in shared:
        subset = distances.loc[distances["Normalized Route Name"].eq(route)]
        rows.append(
            {
                "Normalized Route Name": route,
                "Unique 2016 Points": int(
                    earlier["Normalized Route Name"].eq(route).sum()
                ),
                "Unique 2026 Geometries": int(
                    current["Normalized Route Name"].eq(route).sum()
                ),
                "Minimum Cross-Event Distance (m)": float(
                    subset["Nearest Distance (m)"].min()
                ),
                "2016 Points Within 250 m": int(subset["Within 250 m"].sum()),
                "2016 Points Within 1 km": int(subset["Within 1 km"].sum()),
                "Spatial Support": "fail_no_common_restricted_location"
                if not subset["Within 1 km"].any()
                else "candidate_requires_manual_geometry_audit",
            }
        )
    return pd.DataFrame(rows)


def build_gates(summary: pd.DataFrame) -> pd.DataFrame:
    exact = int(summary["2016 Points Within 250 m"].sum())
    sensitivity = int(summary["2016 Points Within 1 km"].sum())
    return pd.DataFrame(
        [
            ("X1", "Exact route-name overlap", "pass", "Four normalized national-route names occur in both positive-report archives"),
            ("X2", "Common restricted location at 250 m", "fail", f"{exact} 2016 points lie within 250 m of a same-route 2026 restriction geometry"),
            ("X3", "Common restricted location at 1 km", "fail", f"{sensitivity} 2016 points lie within 1 km under the wider sensitivity threshold"),
            ("X4", "Positive-positive repeated-site panel", "fail", "Same route names refer to different damaged/restricted subsegments in the two events"),
            ("X5", "Absence-based comparison", "prohibited", "A site missing from either positive-report archive cannot be treated as open or unaffected"),
        ],
        columns=["Gate ID", "Gate", "Status", "Evidence"],
    )


def render_markdown(
    summary: pd.DataFrame, distances: pd.DataFrame, gates: pd.DataFrame
) -> str:
    nearest = (
        distances.sort_values("Nearest Distance (m)")
        .groupby("Normalized Route Name", as_index=False)
        .first()
    )
    return f"""# Cross-event restriction spatial-support audit

## Result

The four exact route-name overlaps do not produce a repeated-site restriction panel. No 2016 restriction point lies within 250 m of a 2026 restriction geometry on the same route; this remains zero under a 1 km sensitivity threshold. The nearest route-level distances range from {summary['Minimum Cross-Event Distance (m)'].min():.1f} m to {summary['Minimum Cross-Event Distance (m)'].max():.1f} m.

This falsifies the tempting shortcut of treating a repeated route name as a repeated road unit. The 2016 and 2026 positive-report archives identify different subsegments on National Routes 218, 219, 266, and 445. Because archive absence is not evidence of openness, unmatched 2016 locations cannot be used as 2026 zero-closure observations and unmatched 2026 locations cannot be used as 2016 zero-closure observations.

## Route-level support

{summary.to_markdown(index=False, floatfmt='.1f')}

## Nearest cross-event pairs

{nearest.to_markdown(index=False, floatfmt='.1f')}

## Gates

{gates.to_markdown(index=False)}

## Consequence for the study

- The NIED archive materially strengthens the Mashiki Central same-corridor case because that linkage uses an official treatment polygon plus a 2026 positive passage observation.
- It does not yet create a multi-route, same-outcome repeated-event panel.
- The next viable expansion must use 2016 passage traces, a complete road-state denominator, or additional 2026 positive observations at the exact 2016 restricted sites—not route names alone.

## Rebuild

```bash
UV_CACHE_DIR=/private/tmp/ke02-uv-cache uv run python src/analyses/audit_cross_event_restriction_spatial_support.py
```
"""


def main() -> None:
    earlier, current, shared = load_unique_sites()
    if shared != ["国道218号", "国道219号", "国道266号", "国道445号"]:
        raise ValueError(f"Unexpected exact route-name overlap: {shared}")
    distances = calculate_distances(earlier, current)
    summary = summarize(distances, earlier, current, shared)
    gates = build_gates(summary)
    if summary["2016 Points Within 1 km"].sum() != 0:
        raise ValueError("A spatial candidate emerged and requires a revised audit")
    distances.to_csv(OUT / "cross_event_same_route_point_distances.csv", index=False)
    summary.to_csv(OUT / "cross_event_spatial_support_summary.csv", index=False)
    gates.to_csv(OUT / "cross_event_spatial_support_gate.csv", index=False)
    (OUT / "CROSS_EVENT_RESTRICTION_SPATIAL_SUPPORT_AUDIT.md").write_text(
        render_markdown(summary, distances, gates), encoding="utf-8"
    )
    print(OUT / "CROSS_EVENT_RESTRICTION_SPATIAL_SUPPORT_AUDIT.md")


if __name__ == "__main__":
    main()
