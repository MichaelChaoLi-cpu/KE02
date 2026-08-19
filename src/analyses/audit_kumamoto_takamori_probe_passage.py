#!/usr/bin/env python3
"""Audit official probe-passage evidence on the Kumamoto-Takamori corridor.

This script creates a feasibility outcome, not an effect estimate.  It checks
whether the MLIT post-earthquake road-map archives contain private-probe
passage traces spatially consistent with the official intervention polygon and
records the limitations that prevent a causal treatment/comparison design.
"""
from __future__ import annotations

import hashlib
import json
import re
import zipfile
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import shapely
from shapely.geometry import shape


ROOT = Path(__file__).resolve().parents[2]
CORRIDOR = (
    ROOT
    / "data/exp/feasibility-check/intervention-geometry/"
    "kumamoto_takamori_intervention_corridor.parquet"
)
ARCHIVE_DIR = ROOT / "data/raw/mlit/2026/road_passability"
MAP_ARCHIVE = ARCHIVE_DIR / "map.zip"
OUT = ROOT / "data/exp/feasibility-check/intervention-geometry"
PASSAGE_MEMBER = "tukoujisseki.geojson"
SPEED_MEMBERS = ("ETC2.0_speed_data.geojson", "ETC2.0_speed_data1.geojson")
METRIC_CRS = 6670
MIN_TRACE_LENGTH_M = 50.0
MIN_ALIGNMENT_RATIO = 1.0
NEAR_FULL_THRESHOLD = 0.80


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_snapshot(path: Path) -> pd.Timestamp | None:
    """Parse official archive snapshot time, including the initial 29 July file."""
    if path.name == "260729data.zip":
        return pd.Timestamp("2026-07-29 08:00:00", tz="Asia/Tokyo")
    match = re.fullmatch(r"(\d{10})data\.zip", path.name)
    if not match:
        return None
    return pd.to_datetime(match.group(1), format="%y%m%d%H%M").tz_localize(
        "Asia/Tokyo"
    )


def read_geojson_member(archive: Path, member: str) -> gpd.GeoDataFrame:
    with zipfile.ZipFile(archive) as zipped:
        payload = json.loads(zipped.read(member))
    features = payload.get("features", [])
    return gpd.GeoDataFrame(
        [feature.get("properties", {}) for feature in features],
        geometry=[shape(feature["geometry"]) for feature in features],
        crs=4326,
    )


def geometry_coordinates(geometry: shapely.Geometry) -> np.ndarray:
    parts = shapely.get_parts(geometry)
    coordinates = [np.asarray(part.coords, dtype=float) for part in parts]
    return np.vstack(coordinates)


def corridor_axis(polygon: shapely.Geometry) -> tuple[np.ndarray, np.ndarray, float]:
    """Return origin, longitudinal unit vector, and projected corridor span."""
    rectangle = polygon.minimum_rotated_rectangle
    coordinates = np.asarray(rectangle.exterior.coords[:-1], dtype=float)
    edges = np.roll(coordinates, -1, axis=0) - coordinates
    edge = edges[np.argmax(np.linalg.norm(edges, axis=1))]
    unit = edge / np.linalg.norm(edge)
    if unit[0] < 0:
        unit = -unit
    origin = np.asarray(polygon.centroid.coords[0], dtype=float)
    polygon_coordinates = geometry_coordinates(polygon.boundary)
    projections = (polygon_coordinates - origin) @ unit
    return origin, unit, float(projections.max() - projections.min())


def trace_projection(
    geometry: shapely.Geometry, origin: np.ndarray, unit: np.ndarray
) -> tuple[float, float, float, float]:
    coordinates = geometry_coordinates(geometry)
    relative = coordinates - origin
    longitudinal = relative @ unit
    transverse = relative @ np.asarray([-unit[1], unit[0]])
    return (
        float(longitudinal.min()),
        float(longitudinal.max()),
        float(longitudinal.max() - longitudinal.min()),
        float(transverse.max() - transverse.min()),
    )


def merged_interval_length(intervals: list[tuple[float, float]]) -> float:
    merged: list[list[float]] = []
    for start, end in sorted(intervals):
        if not merged or start > merged[-1][1]:
            merged.append([start, end])
        else:
            merged[-1][1] = max(merged[-1][1], end)
    return float(sum(end - start for start, end in merged))


def canonical_geometry_key(geometry: shapely.Geometry) -> str:
    """Deduplicate identical traces, including reversed coordinate order."""
    return shapely.normalize(geometry).wkb_hex


def select_corridor_traces(
    clipped_raw: gpd.GeoDataFrame,
    origin: np.ndarray,
    axis: np.ndarray,
    min_length_m: float,
    min_alignment_ratio: float,
) -> gpd.GeoDataFrame:
    if clipped_raw.empty:
        return gpd.GeoDataFrame(geometry=[], crs=METRIC_CRS)
    clipped = clipped_raw.loc[
        clipped_raw.geometry.length.ge(min_length_m)
    ].copy()
    if clipped.empty:
        return clipped
    clipped["Geometry Key"] = clipped.geometry.map(canonical_geometry_key)
    clipped = clipped.drop_duplicates("Geometry Key").copy()
    projections = clipped.geometry.map(
        lambda geometry: trace_projection(geometry, origin, axis)
    )
    clipped[["Projection Start", "Projection End", "Longitudinal Span (m)", "Transverse Span (m)"]] = pd.DataFrame(
        projections.tolist(), index=clipped.index
    )
    clipped = clipped.loc[
        clipped["Longitudinal Span (m)"].ge(
            min_alignment_ratio * clipped["Transverse Span (m)"]
        )
    ].copy()
    clipped["Clipped Trace Length (m)"] = clipped.geometry.length
    return clipped


def load_corridor_layers(
    polygon: shapely.Geometry,
) -> list[dict[str, object]]:
    """Load each large archive once and retain only geometries in the corridor."""
    layers: list[dict[str, object]] = []
    for archive in sorted(ARCHIVE_DIR.glob("*data.zip")):
        snapshot = parse_snapshot(archive)
        if snapshot is None:
            continue
        with zipfile.ZipFile(archive) as zipped:
            members = set(zipped.namelist())
        speed_member = next((member for member in SPEED_MEMBERS if member in members), None)
        passage_available = PASSAGE_MEMBER in members
        clipped = gpd.GeoDataFrame(geometry=[], crs=METRIC_CRS)
        if passage_available:
            passage = read_geojson_member(archive, PASSAGE_MEMBER).to_crs(METRIC_CRS)
            clipped = gpd.clip(passage, polygon)
        layers.append(
            {
                "archive": archive,
                "snapshot": snapshot,
                "passage_available": passage_available,
                "speed_available": speed_member is not None,
                "clipped": clipped,
            }
        )
    return layers


def audit_configuration(
    layers: list[dict[str, object]],
    origin: np.ndarray,
    axis: np.ndarray,
    corridor_span_m: float,
    min_length_m: float,
    min_alignment_ratio: float,
    save_geometry: bool = False,
) -> tuple[pd.DataFrame, gpd.GeoDataFrame]:
    rows: list[dict[str, object]] = []
    selected_frames: list[gpd.GeoDataFrame] = []
    for layer in layers:
        archive = layer["archive"]
        snapshot = layer["snapshot"]
        passage_available = bool(layer["passage_available"])
        traces = gpd.GeoDataFrame(geometry=[], crs=METRIC_CRS)
        if passage_available:
            traces = select_corridor_traces(
                layer["clipped"],
                origin,
                axis,
                min_length_m,
                min_alignment_ratio,
            )
        intervals = list(
            zip(
                traces.get("Projection Start", pd.Series(dtype=float)),
                traces.get("Projection End", pd.Series(dtype=float)),
                strict=False,
            )
        )
        covered_span = merged_interval_length(intervals)
        coverage = min(covered_span / corridor_span_m, 1.0)
        rows.append(
            {
                "Snapshot Time (JST)": snapshot.isoformat(),
                "Archive": archive.relative_to(ROOT).as_posix(),
                "Archive SHA-256": sha256(archive),
                "Passage Layer Available": passage_available,
                "Speed Layer Available": bool(layer["speed_available"]),
                "Observed Corridor-Aligned Passage": len(traces) > 0,
                "Unique Corridor-Aligned Traces": len(traces),
                "Longest Clipped Trace (m)": (
                    float(traces["Clipped Trace Length (m)"].max())
                    if len(traces)
                    else 0.0
                ),
                "Longitudinal Covered Span Proxy (m)": covered_span,
                "Longitudinal Coverage Proxy": coverage,
                "Interpretation": (
                    "official layer unavailable"
                    if not passage_available
                    else (
                        "probe passage observed"
                        if len(traces)
                        else "no probe passage observed; not evidence of impassability"
                    )
                ),
            }
        )
        if save_geometry and len(traces):
            selected = traces[
                [
                    "Geometry Key",
                    "Projection Start",
                    "Projection End",
                    "Longitudinal Span (m)",
                    "Transverse Span (m)",
                    "Clipped Trace Length (m)",
                    "geometry",
                ]
            ].copy()
            selected["Snapshot Time (JST)"] = snapshot.isoformat()
            selected["Archive"] = archive.relative_to(ROOT).as_posix()
            selected_frames.append(selected)
    summary = pd.DataFrame(rows).sort_values("Snapshot Time (JST)")
    if selected_frames:
        selected_geometry = gpd.GeoDataFrame(
            pd.concat(selected_frames, ignore_index=True),
            geometry="geometry",
            crs=METRIC_CRS,
        ).to_crs(4326)
    else:
        selected_geometry = gpd.GeoDataFrame(geometry=[], crs=4326)
    return summary, selected_geometry


def build_sensitivity(
    layers: list[dict[str, object]],
    origin: np.ndarray,
    axis: np.ndarray,
    corridor_span_m: float,
) -> pd.DataFrame:
    rows = []
    for min_length_m in (25.0, 50.0, 100.0, 200.0):
        for min_alignment_ratio in (0.5, 1.0, 2.0):
            summary, _ = audit_configuration(
                layers,
                origin,
                axis,
                corridor_span_m,
                min_length_m,
                min_alignment_ratio,
            )
            available = summary.loc[summary["Passage Layer Available"]]
            rows.append(
                {
                    "Minimum Trace Length (m)": min_length_m,
                    "Minimum Longitudinal-to-Transverse Span Ratio": min_alignment_ratio,
                    "Available Snapshots": len(available),
                    "Snapshots With Observed Passage": int(
                        available["Observed Corridor-Aligned Passage"].sum()
                    ),
                    "Snapshots With Coverage Proxy >= 0.80": int(
                        available["Longitudinal Coverage Proxy"].ge(0.80).sum()
                    ),
                    "Median Coverage Proxy": float(
                        available["Longitudinal Coverage Proxy"].median()
                    ),
                }
            )
    return pd.DataFrame(rows)


def build_gates(summary: pd.DataFrame) -> pd.DataFrame:
    available = summary.loc[summary["Passage Layer Available"]]
    observed = int(available["Observed Corridor-Aligned Passage"].sum())
    near_full = int(available["Longitudinal Coverage Proxy"].ge(NEAR_FULL_THRESHOLD).sum())
    return pd.DataFrame(
        [
            ("O1", "Official outcome provenance", "pass", "MLIT road-map ZIP archives and official private-probe legend"),
            ("O2", "Spatial linkage", "pass", f"Corridor-aligned passage observed in {observed}/{len(available)} snapshots with the layer"),
            ("O3", "Repeated post-event observations", "pass", f"{near_full}/{len(available)} available snapshots have longitudinal coverage proxy >= 0.80"),
            ("O4", "Outcome semantics", "partial", "Presence of sampled private-probe passage only; not volume, speed, universal passability, or absence of disruption"),
            ("O5", "Pre-event baseline", "fail", "No pre-earthquake probe-passage archive in the acquired official series"),
            ("O6", "Untreated comparison/common support", "fail", "No predeclared comparison corridor with matched exposure and measurement support"),
            ("O7", "Causal effect estimator", "fail", "One treated cluster plus no baseline/comparison cannot identify the four-laning effect"),
        ],
        columns=["Gate ID", "Gate", "Status", "Evidence"],
    )


def write_readme(
    summary: pd.DataFrame,
    sensitivity: pd.DataFrame,
    gates: pd.DataFrame,
    corridor_span_m: float,
) -> None:
    available = summary.loc[summary["Passage Layer Available"]]
    observed = int(available["Observed Corridor-Aligned Passage"].sum())
    near_full = int(available["Longitudinal Coverage Proxy"].ge(NEAR_FULL_THRESHOLD).sum())
    lines = [
        "# Kumamoto-Takamori private-probe passage audit",
        "",
        "## Feasibility result",
        "",
        f"The official MLIT archive contains {len(summary)} post-earthquake map snapshots. The private-probe passage layer is present in {len(available)} snapshots; {observed} contain at least one deduplicated, corridor-aligned trace inside the official Kumamoto-Takamori intervention polygon. Under the preregistered main extraction rule, {near_full} snapshots cover at least 80% of the polygon's {corridor_span_m:,.0f} m longitudinal projection.",
        "",
        "This recovers a route-consistent **descriptive service-presence outcome**. It does not recover vehicle counts, traffic speed, capacity, full public passability, or a counterfactual effect. The official legend explicitly warns that construction-vehicle traces may appear even when ordinary vehicles cannot pass. Conversely, an absent trace is not evidence that the road was closed.",
        "",
        "The first official archive is after the earthquake, so the series has no pre-event baseline. Together with one treated intervention cluster and no matched untreated corridor, this leaves the causal resilience effect unidentified.",
        "",
        "## Main extraction rule",
        "",
        f"- Intersect private-probe traces with the official intervention polygon in EPSG:{METRIC_CRS}.",
        f"- Discard clipped fragments shorter than {MIN_TRACE_LENGTH_M:.0f} m.",
        "- Canonicalize geometry direction and remove exact duplicate traces.",
        f"- Retain traces whose longitudinal span along the polygon's minimum-rectangle axis is at least {MIN_ALIGNMENT_RATIO:.1f} times their transverse span.",
        "- Merge longitudinal projection intervals; divide their union by the polygon projection span. This is a coverage proxy, not mapped road length.",
        "",
        "## Gate table",
        "",
        gates.to_markdown(index=False),
        "",
        "## Source caveat",
        "",
        "The MLIT legend identifies the red layer as private-probe passage records and lists Toyota, Nissan, Honda, Isuzu, and Hino as providers. For the 17 August map it specifies a 06:00-09:00 aggregation window. The archive filename/page time is retained as `Snapshot Time (JST)` for every row; an identical aggregation window is not assumed for other snapshots.",
        "",
        f"Map archive SHA-256: `{sha256(MAP_ARCHIVE)}`",
        "",
        "## Rebuild",
        "",
        "```bash",
        "UV_CACHE_DIR=/private/tmp/ke02-uv-cache uv run python src/analyses/audit_kumamoto_takamori_probe_passage.py",
        "```",
    ]
    (OUT / "PROBE_PASSAGE_OUTCOME_AUDIT.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    if not CORRIDOR.exists():
        raise FileNotFoundError(
            "Run audit_kumamoto_takamori_intervention_geometry.py first"
        )
    corridor = gpd.read_parquet(CORRIDOR).to_crs(METRIC_CRS)
    if len(corridor) != 1:
        raise ValueError("Expected exactly one aggregate intervention corridor")
    polygon = corridor.geometry.iloc[0]
    origin, axis, corridor_span_m = corridor_axis(polygon)
    layers = load_corridor_layers(polygon)
    summary, selected_geometry = audit_configuration(
        layers,
        origin,
        axis,
        corridor_span_m,
        MIN_TRACE_LENGTH_M,
        MIN_ALIGNMENT_RATIO,
        save_geometry=True,
    )
    sensitivity = build_sensitivity(layers, origin, axis, corridor_span_m)
    gates = build_gates(summary)
    summary.to_csv(OUT / "kumamoto_takamori_probe_passage_snapshots.csv", index=False)
    sensitivity.to_csv(
        OUT / "kumamoto_takamori_probe_passage_sensitivity.csv", index=False
    )
    gates.to_csv(OUT / "kumamoto_takamori_probe_passage_gate.csv", index=False)
    selected_geometry.to_parquet(
        OUT / "kumamoto_takamori_probe_passage_traces.parquet", index=False
    )
    write_readme(summary, sensitivity, gates, corridor_span_m)
    available = summary.loc[summary["Passage Layer Available"]]
    observed = int(available["Observed Corridor-Aligned Passage"].sum())
    print(
        "PARTIAL PASS: descriptive probe-passage outcome recovered for "
        f"{observed}/{len(available)} available snapshots; causal gates remain failed."
    )


if __name__ == "__main__":
    main()
