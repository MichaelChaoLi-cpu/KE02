#!/usr/bin/env python3
"""Link exact repeated road corridors to version-pinned USGS ShakeMap rasters.

This is a feasibility analysis, not an effect estimate. It samples the longest
available 2026 restriction geometry for each exact 2016-2026 named endpoint
pair against the 2016 mainshock and 2026 event ShakeMap MMI and PGA surfaces.
The ShakeMap PGA mean raster is stored as ln(g) and is exponentiated to g.
"""
from __future__ import annotations

import hashlib
import json
import tempfile
import zipfile
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from shapely.ops import substring


ROOT = Path(__file__).resolve().parents[2]
RESTRICTIONS = ROOT / "data/processed/kumamoto_2026_road_restriction_snapshots_preprocessed.parquet"
OUTCOME_GATE = ROOT / "data/exp/feasibility-check/2016-road-recovery-linkage/matched_corridor_2026_outcome_gate.csv"
INTERVALS_2016 = ROOT / "data/exp/feasibility-check/2016-road-recovery-linkage/mlit_2016_highway_closure_intervals.csv"
OFFICIAL_INTERVALS_2026 = ROOT / "data/exp/feasibility-check/2016-road-recovery-linkage/official_2026_highway_reopening_intervals.csv"
OUT = ROOT / "data/exp/feasibility-check/2016-road-recovery-linkage"
FEASIBILITY_OUT = OUT.parent
EVENTS = {
    "2016_mainshock": ROOT / "data/raw/usgs/2016/us20005iis",
    "2026_event": ROOT / "data/raw/usgs/2026/us6000tgb9",
}
EXPANDED_OFFICIAL_COVERAGE = {
    "嘉島JCT|益城熊本空港IC": "NEXCO2026-R001",
    "嘉島JCT|松橋IC": "NEXCO2026-R001",
    "嘉島JCT|小池高山IC": "MLIT2026-R003",
    "八代IC|松橋IC": "NEXCO2026-R002",
    "えびのIC|八代IC": "NEXCO2026-R002",
    "八代南IC|日奈久IC": "QSR2026-R004",
    "日奈久IC|田浦IC": "QSR2026-R004",
}
E3A_EXACT_PAIRS = {"八代南IC|日奈久IC", "日奈久IC|田浦IC"}
EXPANDED_2016_COVERAGE = {
    "八代南IC|日奈久IC": "八代JCT|津奈木IC",
    "日奈久IC|田浦IC": "八代JCT|津奈木IC",
}


def normalize_pair(start: object, end: object) -> str:
    import re
    import unicodedata

    def clean(value: object) -> str:
        if value is None or pd.isna(value):
            return ""
        text = unicodedata.normalize("NFKC", str(value))
        return re.sub(r"\s+", "", text).replace("インターチェンジ", "IC")

    return "|".join(sorted([clean(start), clean(end)]))


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def select_corridor_geometries(exact_pairs: set[str]) -> gpd.GeoDataFrame:
    restrictions = gpd.read_parquet(RESTRICTIONS)
    restrictions["Endpoint Pair"] = [
        normalize_pair(start, end)
        for start, end in zip(
            restrictions["Start Location"], restrictions["End Location"], strict=True
        )
    ]
    candidates = restrictions.loc[restrictions["Endpoint Pair"].isin(exact_pairs)].copy()
    candidates["Geometry Length (m)"] = candidates.geometry.to_crs("EPSG:6670").length
    selected = (
        candidates.sort_values(
            ["Endpoint Pair", "Geometry Length (m)", "Snapshot Time"],
            ascending=[True, False, False],
        )
        .drop_duplicates("Endpoint Pair")
        .reset_index(drop=True)
    )
    if set(selected["Endpoint Pair"]) != exact_pairs:
        raise ValueError("At least one exact endpoint pair lacks a 2026 geometry")
    return selected


def line_endpoints(geometry: object) -> list[object]:
    return [geometry.interpolate(0), geometry.interpolate(geometry.length)]


def longest_pair_row(restrictions: gpd.GeoDataFrame, endpoint_pair: str) -> pd.Series:
    rows = restrictions.loc[restrictions["Endpoint Pair"].eq(endpoint_pair)].copy()
    if rows.empty:
        raise ValueError(f"Missing source geometry for {endpoint_pair}")
    rows["Geometry Length (m)"] = rows.geometry.length
    return rows.sort_values(
        ["Geometry Length (m)", "Snapshot Time"], ascending=[False, False]
    ).iloc[0]


def build_expanded_corridor_geometries(
    base: gpd.GeoDataFrame,
) -> tuple[gpd.GeoDataFrame, pd.DataFrame]:
    """Derive two named 2016 subsegments from official 2026 covering geometries."""
    restrictions = gpd.read_parquet(RESTRICTIONS).to_crs("EPSG:6670")
    restrictions["Endpoint Pair"] = [
        normalize_pair(start, end)
        for start, end in zip(
            restrictions["Start Location"], restrictions["End Location"], strict=True
        )
    ]
    base_projected = base.to_crs("EPSG:6670")
    base_rows = []
    for _, row in base_projected.iterrows():
        base_rows.append(
            {
                "Endpoint Pair": row["Endpoint Pair"],
                "Restriction Record ID": row["Restriction Record ID"],
                "Snapshot Time": row["Snapshot Time"],
                "Geometry Linkage Method": "exact_reported_endpoint_pair",
                "Endpoint Offset Maximum (m)": 0.0,
                "Geometry Length (m)": row["Geometry"].length,
                "Geometry": row["Geometry"],
            }
        )

    for endpoint_pair in sorted(E3A_EXACT_PAIRS):
        observed_e3a = longest_pair_row(restrictions, endpoint_pair)
        base_rows.append(
            {
                "Endpoint Pair": endpoint_pair,
                "Restriction Record ID": observed_e3a["Restriction Record ID"],
                "Snapshot Time": observed_e3a["Snapshot Time"],
                "Geometry Linkage Method": "exact_reported_2026_pair_nested_in_official_2016_corridor",
                "Endpoint Offset Maximum (m)": 0.0,
                "Geometry Length (m)": observed_e3a["Geometry"].length,
                "Geometry": observed_e3a["Geometry"],
            }
        )

    broad_mashiki_matsuhashi = longest_pair_row(
        restrictions, normalize_pair("益城熊本空港IC", "松橋IC")
    )
    exact_mashiki_kashima = base_projected.loc[
        base_projected["Endpoint Pair"].eq(normalize_pair("益城熊本空港IC", "嘉島JCT")),
        "Geometry",
    ].iloc[0]
    broad_endpoints = line_endpoints(broad_mashiki_matsuhashi["Geometry"])
    exact_endpoints = line_endpoints(exact_mashiki_kashima)
    common_i, common_j = min(
        ((i, j) for i in range(2) for j in range(2)),
        key=lambda ij: exact_endpoints[ij[0]].distance(broad_endpoints[ij[1]]),
    )
    kashima_point = exact_endpoints[1 - common_i]
    matsuhashi_point = broad_endpoints[1 - common_j]
    first_start = broad_mashiki_matsuhashi["Geometry"].project(kashima_point)
    first_end = broad_mashiki_matsuhashi["Geometry"].project(matsuhashi_point)
    kashima_matsuhashi = substring(
        broad_mashiki_matsuhashi["Geometry"], first_start, first_end
    )
    first_offsets = [
        kashima_point.distance(broad_mashiki_matsuhashi["Geometry"].interpolate(first_start)),
        matsuhashi_point.distance(broad_mashiki_matsuhashi["Geometry"].interpolate(first_end)),
    ]

    broad_mashiki_ebino = longest_pair_row(
        restrictions, normalize_pair("益城熊本空港IC", "えびのIC")
    )
    exact_matsuhashi_yatsushiro = base_projected.loc[
        base_projected["Endpoint Pair"].eq(normalize_pair("松橋IC", "八代IC")),
        "Geometry",
    ].iloc[0]
    exact_my_endpoints = line_endpoints(exact_matsuhashi_yatsushiro)
    matsuhashi_i = min(
        range(2), key=lambda i: exact_my_endpoints[i].distance(matsuhashi_point)
    )
    yatsushiro_point = exact_my_endpoints[1 - matsuhashi_i]
    long_endpoints = line_endpoints(broad_mashiki_ebino["Geometry"])
    mashiki_reference = broad_endpoints[common_j]
    mashiki_j = min(range(2), key=lambda j: long_endpoints[j].distance(mashiki_reference))
    ebino_point = long_endpoints[1 - mashiki_j]
    second_start = broad_mashiki_ebino["Geometry"].project(yatsushiro_point)
    second_end = broad_mashiki_ebino["Geometry"].project(ebino_point)
    yatsushiro_ebino = substring(broad_mashiki_ebino["Geometry"], second_start, second_end)
    second_offsets = [
        yatsushiro_point.distance(broad_mashiki_ebino["Geometry"].interpolate(second_start)),
        ebino_point.distance(broad_mashiki_ebino["Geometry"].interpolate(second_end)),
    ]

    derived_specs = [
        (
            normalize_pair("嘉島JCT", "松橋IC"),
            broad_mashiki_matsuhashi,
            kashima_matsuhashi,
            first_offsets,
            "substring_of_official_mashiki_matsuhashi_geometry_at_kashima_endpoint",
        ),
        (
            normalize_pair("八代IC", "えびのIC"),
            broad_mashiki_ebino,
            yatsushiro_ebino,
            second_offsets,
            "substring_of_official_mashiki_ebino_geometry_at_yatsushiro_endpoint",
        ),
    ]
    for endpoint_pair, source, geometry, offsets, method in derived_specs:
        if geometry.length < 1_000 or max(offsets) > 250:
            raise ValueError(
                f"Derived geometry gate failed for {endpoint_pair}: "
                f"length={geometry.length:.1f}, max offset={max(offsets):.1f}"
            )
        base_rows.append(
            {
                "Endpoint Pair": endpoint_pair,
                "Restriction Record ID": f"derived-from-{source['Restriction Record ID']}",
                "Snapshot Time": source["Snapshot Time"],
                "Geometry Linkage Method": method,
                "Endpoint Offset Maximum (m)": max(offsets),
                "Geometry Length (m)": geometry.length,
                "Geometry": geometry,
            }
        )

    expanded_projected = gpd.GeoDataFrame(base_rows, geometry="Geometry", crs="EPSG:6670")
    expanded = expanded_projected.to_crs("EPSG:4326").sort_values("Endpoint Pair").reset_index(drop=True)
    audit = expanded.drop(columns="Geometry").copy()
    if len(expanded) != 7 or expanded["Endpoint Pair"].duplicated().any():
        raise ValueError("Expanded corridor geometry set must contain seven unique pairs")
    return expanded, audit


def build_expanded_outcome_gate(base_gate: pd.DataFrame) -> pd.DataFrame:
    intervals_2016 = pd.read_csv(INTERVALS_2016)
    intervals_2026 = pd.read_csv(OFFICIAL_INTERVALS_2026)
    target_pairs = set(EXPANDED_OFFICIAL_COVERAGE)
    rows: list[dict[str, object]] = []
    for endpoint_pair in sorted(target_pairs):
        old_source_pair = EXPANDED_2016_COVERAGE.get(endpoint_pair, endpoint_pair)
        old = intervals_2016.loc[intervals_2016["Endpoint Pair"].eq(old_source_pair)]
        if old.empty:
            raise ValueError(f"Expanded pair lacks 2016 interval: {endpoint_pair}")
        covering_id = EXPANDED_OFFICIAL_COVERAGE.get(endpoint_pair, "")
        covering = intervals_2026.loc[
            intervals_2026["Official 2026 Interval ID"].eq(covering_id)
        ]
        base = base_gate.loc[base_gate["Endpoint Pair"].eq(endpoint_pair)]
        if len(covering) == 1:
            source = covering.iloc[0]
            restoration_hours = float(source["Observed Closure Hours"])
            endpoint = source["General Traffic Reopening"]
            eligible = True
            outcome_gate = "eligible_official_covering_corridor_reopening"
            precision = source["Reopening Time Precision"]
            endpoint_lower = endpoint
            endpoint_upper = endpoint
            restoration_lower = restoration_hours
            restoration_upper = restoration_hours
        elif len(base) == 1:
            source = None
            restoration_hours = base.iloc[0]["Restoration Time (hours)"]
            endpoint = base.iloc[0]["Restoration Endpoint"]
            eligible = bool(base.iloc[0]["Restoration Outcome Eligible"])
            outcome_gate = base.iloc[0]["2026 Outcome Gate"]
            precision = base.iloc[0]["Covering Reopening Time Precision"]
            endpoint_lower = endpoint
            endpoint_upper = endpoint
            restoration_lower = restoration_hours
            restoration_upper = restoration_hours
        else:
            raise ValueError(f"Expanded pair lacks 2026 outcome evidence: {endpoint_pair}")
        rows.append(
            {
                "Endpoint Pair": endpoint_pair,
                "2016 Interval Count": len(old),
                "2016 Covering Endpoint Pair": old_source_pair,
                "2016 Closure Hours": "; ".join(f"{value:.2f}" for value in old["Observed Closure Hours"]),
                "2026 Restoration Endpoint": endpoint,
                "2026 Restoration Endpoint Lower Bound": endpoint_lower,
                "2026 Restoration Endpoint Upper Bound": endpoint_upper,
                "2026 Restoration Hours": restoration_hours,
                "2026 Restoration Hours Lower Bound": restoration_lower,
                "2026 Restoration Hours Upper Bound": restoration_upper,
                "2026 Reopening Time Precision": precision,
                "Covering Official Interval ID": covering_id,
                "Restoration Outcome Eligible": eligible,
                "2026 Outcome Gate": outcome_gate,
                "Pair Origin": (
                    "exact_pair_in_2026_restriction_rows"
                    if len(base) == 1 or endpoint_pair in E3A_EXACT_PAIRS
                    else "2016_named_pair_nested_in_official_2026_corridor"
                ),
            }
        )
    return pd.DataFrame(rows)


def sample_points(geometry: object, count: int = 51) -> list[tuple[float, float]]:
    return [
        (point.x, point.y)
        for point in (geometry.interpolate(value, normalized=True) for value in np.linspace(0, 1, count))
    ]


def event_metadata(event_dir: Path) -> dict[str, object]:
    info = json.loads((event_dir / "info.json").read_text(encoding="utf-8"))
    event = info["input"]["event_information"]
    versions = info["processing"]["shakemap_versions"]
    return {
        "USGS Event ID": event["event_id"],
        "Magnitude": float(event["magnitude"]),
        "Origin Time UTC": event["origin_time"],
        "ShakeMap Version": versions["map_version"],
        "ShakeMap Process Time UTC": versions["process_time"],
    }


def sample_event(
    event_label: str,
    event_dir: Path,
    corridors: gpd.GeoDataFrame,
) -> list[dict[str, object]]:
    raster_zip = event_dir / "raster.zip"
    metadata = event_metadata(event_dir)
    rows: list[dict[str, object]] = []
    with tempfile.TemporaryDirectory(prefix="ke02-shakemap-") as temp_dir:
        with zipfile.ZipFile(raster_zip) as bundle:
            for filename in ["mmi_mean.flt", "mmi_mean.hdr", "pga_mean.flt", "pga_mean.hdr"]:
                bundle.extract(filename, temp_dir)
        with rasterio.open(Path(temp_dir) / "mmi_mean.flt") as mmi_ds, rasterio.open(
            Path(temp_dir) / "pga_mean.flt"
        ) as pga_ds:
            for _, corridor in corridors.iterrows():
                points = sample_points(corridor["Geometry"])
                mmi = np.array([value[0] for value in mmi_ds.sample(points)], dtype=float)
                ln_pga = np.array([value[0] for value in pga_ds.sample(points)], dtype=float)
                valid = (mmi != 999.0) & (ln_pga != 999.0) & np.isfinite(mmi) & np.isfinite(ln_pga)
                if not valid.any():
                    raise ValueError(f"No valid ShakeMap samples for {corridor['Endpoint Pair']}")
                pga_g = np.exp(ln_pga[valid])
                rows.append(
                    {
                        "Endpoint Pair": corridor["Endpoint Pair"],
                        "Event": event_label,
                        **metadata,
                        "Sample Count": len(points),
                        "Valid Sample Count": int(valid.sum()),
                        "MMI Mean": float(mmi[valid].mean()),
                        "MMI Minimum": float(mmi[valid].min()),
                        "MMI Maximum": float(mmi[valid].max()),
                        "PGA Mean (g)": float(pga_g.mean()),
                        "PGA Minimum (g)": float(pga_g.min()),
                        "PGA Maximum (g)": float(pga_g.max()),
                        "Geometry Source Record ID": corridor["Restriction Record ID"],
                        "Geometry Source Snapshot": corridor["Snapshot Time"],
                        "Geometry Linkage Method": corridor["Geometry Linkage Method"],
                        "Geometry Length (m)": corridor["Geometry Length (m)"],
                        "Endpoint Offset Maximum (m)": corridor["Endpoint Offset Maximum (m)"],
                        "Raster ZIP": raster_zip.relative_to(ROOT).as_posix(),
                        "Raster ZIP SHA256": file_sha256(raster_zip),
                    }
                )
    return rows


def build_pilot_contrasts(
    comparison: pd.DataFrame,
    gate: pd.DataFrame,
) -> pd.DataFrame:
    intervals = pd.read_csv(INTERVALS_2016)
    intervals["Restriction End"] = pd.to_datetime(intervals["Restriction End"]).dt.tz_localize(
        "Asia/Tokyo"
    )
    selected_2016 = (
        intervals.sort_values(["Endpoint Pair", "Restriction End"])
        .drop_duplicates("Endpoint Pair", keep="last")
        [["Endpoint Pair", "Restriction End", "Observed Closure Hours"]]
        .rename(
            columns={
                "Restriction End": "2016 Official Reopening",
                "Observed Closure Hours": "Selected Official Closure Interval Hours",
            }
        )
        .reset_index(drop=True)
    )
    selected_2016["2016 Source Endpoint Pair"] = selected_2016["Endpoint Pair"]
    for target_pair, source_pair in EXPANDED_2016_COVERAGE.items():
        source_row = selected_2016.loc[
            selected_2016["Endpoint Pair"].eq(source_pair)
        ].copy()
        if len(source_row) != 1:
            raise ValueError(f"Missing unique 2016 covering interval for {target_pair}")
        source_row["Endpoint Pair"] = target_pair
        selected_2016 = pd.concat([selected_2016, source_row], ignore_index=True)
    mainshock_info = json.loads((EVENTS["2016_mainshock"] / "info.json").read_text(encoding="utf-8"))
    mainshock_origin = pd.Timestamp(
        mainshock_info["input"]["event_information"]["origin_time"]
    ).tz_convert("Asia/Tokyo")
    selected_2016["2016 Mainshock Time"] = mainshock_origin
    selected_2016["2016 Mainshock-to-Reopening Hours"] = (
        selected_2016["2016 Official Reopening"] - mainshock_origin
    ).dt.total_seconds() / 3600
    keep = gate[
        [
            "Endpoint Pair",
            "2026 Restoration Hours",
            "2026 Restoration Hours Lower Bound",
            "2026 Restoration Hours Upper Bound",
            "Restoration Outcome Eligible",
            "2026 Outcome Gate",
            "Pair Origin",
            "Covering Official Interval ID",
        ]
    ]
    contrasts = (
        keep.merge(selected_2016, on="Endpoint Pair", how="left", validate="one_to_one")
        .merge(comparison, on="Endpoint Pair", how="left", validate="one_to_one")
    )
    contrasts["2016 Interval Selection Rule"] = np.where(
        contrasts["2016 Source Endpoint Pair"].eq(contrasts["Endpoint Pair"]),
        "latest official reopening for the exact pair; restoration clock begins at the 2016 mainshock",
        "latest official reopening for the covering 2016 corridor; restoration clock begins at the 2016 mainshock",
    )
    contrasts["Restoration Difference Hours (2026-2016)"] = (
        contrasts["2026 Restoration Hours"] - contrasts["2016 Mainshock-to-Reopening Hours"]
    )
    contrasts["Restoration Ratio (2026/2016)"] = (
        contrasts["2026 Restoration Hours"] / contrasts["2016 Mainshock-to-Reopening Hours"]
    )
    contrasts["Descriptive Direction"] = np.select(
        [
            ~contrasts["Restoration Outcome Eligible"],
            contrasts["Restoration Difference Hours (2026-2016)"].lt(0),
            contrasts["Restoration Difference Hours (2026-2016)"].gt(0),
        ],
        ["right_censored", "shorter_in_2026", "longer_in_2026"],
        default="same_duration",
    )
    first = [
        "Endpoint Pair",
        "2016 Mainshock Time",
        "2016 Official Reopening",
        "2016 Mainshock-to-Reopening Hours",
        "Selected Official Closure Interval Hours",
        "2016 Source Endpoint Pair",
        "2026 Restoration Hours",
        "2026 Restoration Hours Lower Bound",
        "2026 Restoration Hours Upper Bound",
        "Restoration Difference Hours (2026-2016)",
        "Restoration Ratio (2026/2016)",
        "Descriptive Direction",
        "Restoration Outcome Eligible",
        "2026 Outcome Gate",
        "Pair Origin",
        "Covering Official Interval ID",
        "2016 Interval Selection Rule",
        "MMI Mean - 2016_mainshock",
        "MMI Mean - 2026_event",
        "MMI Mean Difference (2026-2016)",
        "PGA Mean (g) - 2016_mainshock",
        "PGA Mean (g) - 2026_event",
        "PGA Mean Ratio (2026/2016)",
    ]
    return contrasts[first]


def build_reopening_cluster_contrasts(contrasts: pd.DataFrame) -> pd.DataFrame:
    eligible = contrasts.loc[contrasts["Restoration Outcome Eligible"]].copy()
    regime_ids = {
        "NEXCO2026-R001": "REGIME-NORTH",
        "MLIT2026-R003": "REGIME-NORTH",
        "NEXCO2026-R002": "REGIME-SOUTH",
        "QSR2026-R004": "REGIME-E3A",
    }
    eligible["Reopening Regime ID"] = eligible["Covering Official Interval ID"].map(
        regime_ids
    )
    if eligible["Reopening Regime ID"].isna().any():
        raise ValueError("At least one official interval lacks an independence-regime mapping")
    names = {
        "REGIME-NORTH": "joint_north_kashima_mashiki_to_matsuhashi",
        "REGIME-SOUTH": "south_matsuhashi_to_ebino",
        "REGIME-E3A": "minami_kyushu_yatsushirominami_to_tanoura",
    }
    rows: list[dict[str, object]] = []
    for cluster_id, group in eligible.groupby("Reopening Regime ID"):
        restoration_values = group["2026 Restoration Hours"].dropna().unique()
        if len(restoration_values) != 1:
            raise ValueError(f"Cluster {cluster_id} has inconsistent 2026 restoration times")
        rows.append(
            {
                "Reopening Cluster ID": cluster_id,
                "Cluster Label": names.get(cluster_id, ""),
                "Named Segment Count": len(group),
                "Independent 2026 Reopening Regimes": 1,
                "Pseudo-replication Warning": len(group) > 1,
                "Official Interval IDs": "; ".join(
                    sorted(group["Covering Official Interval ID"].unique())
                ),
                "Endpoint Pairs": "; ".join(group["Endpoint Pair"]),
                "2016 MMI Mean Across Segments": group["MMI Mean - 2016_mainshock"].mean(),
                "2026 MMI Mean Across Segments": group["MMI Mean - 2026_event"].mean(),
                "2016 PGA Mean (g) Across Segments": group[
                    "PGA Mean (g) - 2016_mainshock"
                ].mean(),
                "2026 PGA Mean (g) Across Segments": group[
                    "PGA Mean (g) - 2026_event"
                ].mean(),
                "PGA Mean Ratio (2026/2016)": group[
                    "PGA Mean (g) - 2026_event"
                ].mean()
                / group["PGA Mean (g) - 2016_mainshock"].mean(),
                "2016 Mainshock-to-Reopening Mean Hours": group[
                    "2016 Mainshock-to-Reopening Hours"
                ].mean(),
                "2026 General-Traffic Restoration Hours": restoration_values[0],
                "2026 Restoration Hours Lower Bound": group[
                    "2026 Restoration Hours Lower Bound"
                ].min(),
                "2026 Restoration Hours Upper Bound": group[
                    "2026 Restoration Hours Upper Bound"
                ].max(),
                "Mean Restoration Difference Hours (2026-2016)": group[
                    "Restoration Difference Hours (2026-2016)"
                ].mean(),
                "Mean Segment Restoration Ratio (2026/2016)": group[
                    "Restoration Ratio (2026/2016)"
                ].mean(),
            }
        )
    clusters = pd.DataFrame(rows).sort_values("Reopening Cluster ID").reset_index(drop=True)
    if len(clusters) != 3:
        raise ValueError("Expected exactly three independent 2026 reopening regimes")
    return clusters


def write_readme(
    long: pd.DataFrame,
    comparison: pd.DataFrame,
    contrasts: pd.DataFrame,
    clusters: pd.DataFrame,
) -> None:
    spread_2026 = long.loc[long["Event"].eq("2026_event"), "MMI Mean"].agg(["min", "max"])
    spread_2016 = long.loc[long["Event"].eq("2016_mainshock"), "MMI Mean"].agg(["min", "max"])
    eligible = contrasts.loc[contrasts["Restoration Outcome Eligible"]]
    direction_counts = eligible["Descriptive Direction"].value_counts()
    north = clusters.loc[clusters["Reopening Cluster ID"].eq("REGIME-NORTH")].iloc[0]
    south = clusters.loc[clusters["Reopening Cluster ID"].eq("REGIME-SOUTH")].iloc[0]
    e3a = clusters.loc[clusters["Reopening Cluster ID"].eq("REGIME-E3A")].iloc[0]
    south_to_north_restoration_ratio = (
        south["2026 General-Traffic Restoration Hours"]
        / north["2026 General-Traffic Restoration Hours"]
    )
    lines = [
        "# Repeated-corridor ShakeMap linkage audit",
        "",
        "## Result",
        "",
        f"- All {comparison.shape[0]} named repeated-corridor pilot units have valid samples in both version-pinned ShakeMap rasters.",
        f"- Mean 2016-mainshock MMI across corridors ranges from {spread_2016['min']:.2f} to {spread_2016['max']:.2f}; mean 2026 MMI ranges from {spread_2026['min']:.2f} to {spread_2026['max']:.2f}.",
        f"- This passes the technical spatial-linkage gate for {comparison.shape[0]} pilot corridors, but that sample cannot establish common support or identify a hazard-adjusted comparison design.",
        "- ShakeMap model generations and grid resolutions differ. MMI and PGA are comparable physical measures, but cross-event differences remain model-dependent and require sensitivity analysis.",
        f"- The binding feasibility failure is that {len(eligible)} named segments provide only {len(clusters)} independent reopening regimes, together with the absence of a treatment/comparison sample; it is no longer pilot endpoint coverage or raster coverage.",
        f"- Of {len(eligible)} corridors with eligible restoration endpoints, {int(direction_counts.get('shorter_in_2026', 0))} are shorter in 2026 and {int(direction_counts.get('longer_in_2026', 0))} are longer. The pilot therefore has no common segment-level directional restoration signal.",
        f"- Those {len(eligible)} segments collapse to {len(clusters)} independent official reopening regimes. The northern regime reopened in {north['2026 General-Traffic Restoration Hours']:.1f} hours and the southern Kyushu Expressway regime in {south['2026 General-Traffic Restoration Hours']:.1f} hours ({south_to_north_restoration_ratio:.1f} times longer). The E3A regime reopened in {e3a['2026 General-Traffic Restoration Hours']:.1f} hours at the exact minute stated in the regional-bureau release.",
        f"- Mean 2026 MMI is higher in the northern regime ({north['2026 MMI Mean Across Segments']:.2f}) than the southern Kyushu Expressway regime ({south['2026 MMI Mean Across Segments']:.2f}), yet the northern regime reopened sooner. This is a hypothesis-generating resilience pattern, not causal evidence: the effective sample is {len(clusters)}, bridge-specific damage differs, and intervention geometry is unavailable.",
        "",
        "## Method",
        "",
        "Five pairs use an exact reported 2026 restriction geometry. Two additional 2016-named subsegments are cut from official covering-corridor geometries at IC endpoints already observed in the exact records; each derived geometry must be longer than 1 km and have endpoint projection error below 250 m. The two E3A pairs are nested within a broader official 2016 corridor and share the exact 2026 reopening endpoint in one joint official release. A formal final release overrides a lagging passable-map state. Every corridor is sampled at 51 equally spaced locations. USGS `mmi_mean` is used directly; `pga_mean` is exponentiated from ln(g) to g. No interpolation beyond rasterio's containing-cell sample is applied.",
        "",
        "## Files",
        "",
        "- `matched_corridor_shaking_exposure_long.csv`: event-specific sampled summaries and immutable source hashes.",
        "- `matched_corridor_shaking_comparison.csv`: cross-event MMI/PGA comparison by exact corridor.",
        "- `matched_corridor_pilot_contrasts.csv`: descriptive 2016-mainshock-to-reopening versus 2026 restoration and shaking contrasts; not an effect estimate.",
        "- `expanded_repeated_corridor_outcome_gate.csv`: seven-unit outcome eligibility, source-precedence, and coverage audit.",
        "- `expanded_repeated_corridor_geometry_audit.csv`: exact/derived geometry construction and topology checks.",
        "- `expanded_repeated_corridor_geometries.parquet`: experimental geometry layer used for raster sampling.",
        "- `reopening_cluster_pilot_contrasts.csv`: three-regime aggregation that prevents seven nested segments from being treated as independent outcomes.",
    ]
    (OUT / "SHAKING_LINKAGE_README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def update_audited_feasibility(
    contrasts: pd.DataFrame,
    clusters: pd.DataFrame,
) -> None:
    """Promote the expanded pilot facts into the question-level audit.

    The base corridor audit runs first and records only exact reported endpoint
    pairs. This second-stage audit adds two topology-gated subsegments and must
    therefore update, rather than contradict, the base RQ1 evidence summary.
    """
    audit_path = FEASIBILITY_OUT / "audited_question_feasibility.csv"
    if not audit_path.exists():
        raise FileNotFoundError(f"Missing base feasibility audit: {audit_path}")
    audited = pd.read_csv(audit_path)
    rq1 = audited["ID"].eq("RQ1")
    if int(rq1.sum()) != 1:
        raise ValueError("Expected exactly one RQ1 row in the audited feasibility table")

    eligible = int(contrasts["Restoration Outcome Eligible"].sum())
    corridor_count = len(contrasts)
    regime_count = len(clusters)
    audited.loc[rq1, "Audited Status"] = "weakly-testable"
    audited.loc[rq1, "Evidence Now Available"] = (
        f"{corridor_count} named 2016-2026 highway pilot corridors; official 2016 "
        f"reopening intervals; {eligible} source-validated 2026 restoration endpoints; "
        "valid version-pinned 2016/2026 ShakeMap samples for every corridor"
    )
    audited.loc[rq1, "Binding Gap"] = (
        f"The {eligible} endpoint-eligible segments collapse to only {regime_count} "
        "independent 2026 reopening regimes; no common-support, intervention-geometry, "
        "or counterfactual sample"
    )
    audited.loc[rq1, "Permissible Claim"] = (
        "Technical linkage feasibility and pilot restoration contrasts only; no adjusted "
        "or causal effect"
    )
    audited.to_csv(audit_path, index=False)

    status_counts = audited["Audited Status"].value_counts()
    lines = [
        "# Audited Feasibility Judgment",
        "",
        "This evidence audit supersedes the filename/column-keyword diagnostic in `question_feasibility.csv`. The bundled scanner does not read Parquet or PDF evidence and therefore remains intentionally conservative.",
        "",
        "## Status",
        "",
        f"- `partly-testable`: {int(status_counts.get('partly-testable', 0))}",
        f"- `weakly-testable`: {int(status_counts.get('weakly-testable', 0))}",
        f"- `not-yet-testable`: {int(status_counts.get('not-yet-testable', 0))}",
        "",
        "## Decision",
        "",
        f"The exact-pair core contains three corridors, while the coverage- and topology-gated expanded pilot contains {corridor_count} named repeated corridors and {eligible} source-validated 2026 restoration endpoints. Those eligible segments reduce to only {regime_count} independent reopening regimes. Cross-event shaking and restoration linkage is therefore technically feasible, but the effective sample remains too small for an adjusted repeated-shock estimator. Preserve RQ1 as the target and expand independent reopening regimes rather than changing the question or advancing to manuscript handoff.",
        "",
        "## Reproducible Evidence",
        "",
        "- `audited_question_feasibility.csv`: question-level final evidence judgment.",
        "- `2016-road-recovery-linkage/matched_corridor_2026_outcome_gate.csv`: exact-corridor endpoint gate.",
        f"- `2016-road-recovery-linkage/expanded_repeated_corridor_outcome_gate.csv`: {corridor_count}-corridor endpoint, source-precedence, and coverage gate.",
        "- `2016-road-recovery-linkage/expanded_repeated_corridor_geometry_audit.csv`: exact and topology-gated derived geometry audit.",
        "- `2016-road-recovery-linkage/reopening_cluster_pilot_contrasts.csv`: independent-regime aggregation and pseudo-replication warning.",
        "- `2016-road-recovery-linkage/matched_corridor_shaking_exposure_long.csv`: version-pinned cross-event shaking samples.",
        "- `independent-reopening-regimes/`: conservative expansion inventory, candidate waiting/exclusion log, and official-source watchlist.",
    ]
    (FEASIBILITY_OUT / "AUDITED_README.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def main() -> None:
    base_gate = pd.read_csv(OUTCOME_GATE)
    exact_pairs = set(base_gate["Endpoint Pair"])
    base_corridors = select_corridor_geometries(exact_pairs)
    corridors, geometry_audit = build_expanded_corridor_geometries(base_corridors)
    gate = build_expanded_outcome_gate(base_gate)
    if set(corridors["Endpoint Pair"]) != set(gate["Endpoint Pair"]):
        raise ValueError("Expanded geometry and outcome-gate pairs do not match")
    rows: list[dict[str, object]] = []
    for event_label, event_dir in EVENTS.items():
        rows.extend(sample_event(event_label, event_dir, corridors))
    long = pd.DataFrame(rows).sort_values(["Endpoint Pair", "Event"]).reset_index(drop=True)
    metrics = ["MMI Mean", "MMI Minimum", "MMI Maximum", "PGA Mean (g)", "PGA Minimum (g)", "PGA Maximum (g)"]
    comparison = long.pivot(index="Endpoint Pair", columns="Event", values=metrics)
    comparison.columns = [f"{metric} - {event}" for metric, event in comparison.columns]
    comparison = comparison.reset_index()
    comparison["MMI Mean Difference (2026-2016)"] = (
        comparison["MMI Mean - 2026_event"] - comparison["MMI Mean - 2016_mainshock"]
    )
    comparison["PGA Mean Ratio (2026/2016)"] = (
        comparison["PGA Mean (g) - 2026_event"] / comparison["PGA Mean (g) - 2016_mainshock"]
    )
    contrasts = build_pilot_contrasts(comparison, gate)
    clusters = build_reopening_cluster_contrasts(contrasts)
    long.to_csv(OUT / "matched_corridor_shaking_exposure_long.csv", index=False)
    comparison.to_csv(OUT / "matched_corridor_shaking_comparison.csv", index=False)
    contrasts.to_csv(OUT / "matched_corridor_pilot_contrasts.csv", index=False)
    gate.to_csv(OUT / "expanded_repeated_corridor_outcome_gate.csv", index=False)
    geometry_audit.to_csv(OUT / "expanded_repeated_corridor_geometry_audit.csv", index=False)
    corridors.to_parquet(OUT / "expanded_repeated_corridor_geometries.parquet", index=False)
    clusters.to_csv(OUT / "reopening_cluster_pilot_contrasts.csv", index=False)
    write_readme(long, comparison, contrasts, clusters)
    update_audited_feasibility(contrasts, clusters)
    print(
        f"PASS: {len(corridors)} repeated corridors sampled for {len(EVENTS)} events; "
        f"{int(long['Valid Sample Count'].sum())} valid point-event samples."
    )


if __name__ == "__main__":
    main()
