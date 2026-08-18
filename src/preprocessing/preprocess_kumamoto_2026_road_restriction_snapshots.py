#!/usr/bin/env python3
"""Standardize all versioned MLIT 2026 road-restriction GeoJSON snapshots."""

from __future__ import annotations

import hashlib
import json
import re
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any

import geopandas as gpd
import pandas as pd
from shapely.geometry import shape


ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT / "data/raw/mlit/2026/road_passability"
DST_RECORDS = ROOT / "data/processed/kumamoto_2026_road_restriction_snapshots_preprocessed.parquet"
DST_COVERAGE = ROOT / "data/processed/kumamoto_2026_road_snapshot_coverage_preprocessed.parquet"
JST = "Asia/Tokyo"


def clean(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip()
        if value.casefold() in {"", "null", "none", "nan"}:
            return None
    return value


def pick(properties: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = clean(properties.get(key))
        if value is not None:
            return value
    return None


def snapshot_time(path: Path) -> tuple[pd.Timestamp, str]:
    match = re.fullmatch(r"(\d{2})(\d{2})(\d{2})(?:(\d{2})(\d{2}))?data\.zip", path.name)
    if not match:
        raise ValueError(f"Unrecognized snapshot filename: {path.name}")
    year, month, day = 2000 + int(match[1]), int(match[2]), int(match[3])
    if match[4] is None:
        hour, minute = 8, 0
        precision = "date_only_assumed_0800_from_official_page"
    else:
        hour, minute = int(match[4]), int(match[5])
        precision = "minute"
    return pd.Timestamp(datetime(year, month, day, hour, minute), tz=JST), precision


def parse_jst_datetime(value: Any) -> pd.Timestamp:
    value = clean(value)
    if value is None:
        return pd.NaT
    text = re.sub(r"^(\d{4})/(\d{1,2})/(\d{1,2})/", r"\1/\2/\3 ", str(value))
    parsed = pd.to_datetime(text, errors="coerce")
    if pd.isna(parsed):
        return pd.NaT
    if parsed.tzinfo is None:
        return parsed.tz_localize(JST)
    return parsed.tz_convert(JST)


def classify_observation_state(status: Any) -> str:
    """Normalize explicit source status without inferring openness from non-reporting."""
    status = clean(status)
    if status is None:
        return "unknown_status"
    text = str(status)
    if "解除" in text:
        return "restriction_lifted"
    if "緊急車両" in text:
        return "active_emergency_access_only"
    if "通行止" in text:
        return "active_full_closure"
    return "unknown_status"


def derived_record_id(properties: dict[str, Any], geometry: Any) -> str:
    payload = json.dumps(
        {"properties": properties, "geometry": geometry},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "derived-" + hashlib.sha256(payload).hexdigest()[:20]


def restriction_feature_id(
    archive_name: str,
    feature_index: int,
    record_id: str,
    properties: dict[str, Any],
    geometry: Any,
) -> str:
    """Create a unique row identifier without replacing the source event identifier."""
    payload = json.dumps(
        {
            "archive": archive_name,
            "feature_index": feature_index,
            "record_id": record_id,
            "properties": properties,
            "geometry": geometry,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "feature-" + hashlib.sha256(payload).hexdigest()[:24]


def main() -> None:
    archives = sorted(
        path for path in SRC_DIR.glob("*data.zip") if re.fullmatch(r"\d{6}(?:\d{4})?data\.zip", path.name)
    )
    if len(archives) != 24:
        raise ValueError(f"Expected 24 dated archives, found {len(archives)}")

    records: list[dict[str, Any]] = []
    geometries = []
    coverage_rows: list[dict[str, Any]] = []

    for archive in archives:
        snap_time, time_precision = snapshot_time(archive)
        with zipfile.ZipFile(archive) as bundle:
            names = bundle.namelist()
            restriction_names = [name for name in names if Path(name).name == "dourokisei.geojson"]
            passability_names = [name for name in names if Path(name).name.startswith("tukoujisseki")]
            speed_names = [name for name in names if Path(name).name.startswith("ETC2.0_speed_data")]
            feature_count = 0
            property_names: set[str] = set()

            if restriction_names:
                source_name = restriction_names[0]
                collection = json.loads(bundle.read(source_name).decode("utf-8-sig"))
                features = collection.get("features", [])
                feature_count = len(features)
                for feature_index, feature in enumerate(features):
                    properties = feature.get("properties") or {}
                    property_names.update(properties)
                    geometry_json = feature.get("geometry")
                    record_id = clean(properties.get("name")) or derived_record_id(
                        properties, geometry_json
                    )
                    restriction_status = pick(
                        properties, "規制内容", "規制開始_内容"
                    )
                    records.append(
                        {
                            "Snapshot Time": snap_time,
                            "Snapshot Archive": archive.name,
                            "Restriction Record ID": str(record_id),
                            "Restriction Feature ID": restriction_feature_id(
                                archive.name,
                                feature_index,
                                str(record_id),
                                properties,
                                geometry_json,
                            ),
                            "Prefecture": pick(properties, "県名"),
                            "Municipality": pick(properties, "市町村名"),
                            "Road Type": pick(properties, "道路種別"),
                            "Route Name": pick(properties, "路線名"),
                            "Start Location": pick(properties, "始点", "始点住所"),
                            "End Location": pick(properties, "終点", "終点住所"),
                            "Restriction Type": pick(properties, "規制種別"),
                            "Restriction Reason": pick(properties, "規制理由"),
                            "Restriction Start Time": parse_jst_datetime(
                                pick(properties, "規制開始_日時")
                            ),
                            "Restriction Status": restriction_status,
                            "Restriction Direction": pick(properties, "規制方向"),
                            "Restriction Length (km)": pd.to_numeric(
                                pick(properties, "規制延長_Km", "延長_Km"), errors="coerce"
                            ),
                            "Observation State": classify_observation_state(
                                restriction_status
                            ),
                            "Record Present": True,
                            "Source Feature Index": feature_index,
                            "Original Properties JSON": json.dumps(
                                properties, ensure_ascii=False, sort_keys=True, separators=(",", ":")
                            ),
                        }
                    )
                    geometries.append(shape(geometry_json) if geometry_json else None)

            schema_signature = hashlib.sha256(
                "\n".join(sorted(property_names)).encode("utf-8")
            ).hexdigest()[:16] if property_names else None
            coverage_rows.append(
                {
                    "Snapshot Time": snap_time,
                    "Snapshot Time Precision": time_precision,
                    "Snapshot Archive": archive.name,
                    "Restriction Layer Available": bool(restriction_names),
                    "Restriction Feature Count": feature_count,
                    "Passability Layer Available": bool(passability_names),
                    "Speed Layer Available": bool(speed_names),
                    "Restriction Schema Signature": schema_signature,
                    "Absence Interpretation": "not_observed_not_open",
                }
            )

    restrictions = gpd.GeoDataFrame(records, geometry=geometries, crs="EPSG:4326")
    restrictions = restrictions.rename_geometry("Geometry")
    for column in [
        "Snapshot Archive",
        "Restriction Record ID",
        "Restriction Feature ID",
        "Prefecture",
        "Municipality",
        "Road Type",
        "Route Name",
        "Start Location",
        "End Location",
        "Restriction Type",
        "Restriction Reason",
        "Restriction Status",
        "Restriction Direction",
        "Observation State",
        "Original Properties JSON",
    ]:
        restrictions[column] = restrictions[column].astype("string").str.strip()

    output_columns = [
        "Snapshot Time",
        "Snapshot Archive",
        "Restriction Record ID",
        "Restriction Feature ID",
        "Prefecture",
        "Municipality",
        "Road Type",
        "Route Name",
        "Start Location",
        "End Location",
        "Restriction Type",
        "Restriction Reason",
        "Restriction Start Time",
        "Restriction Status",
        "Restriction Direction",
        "Restriction Length (km)",
        "Observation State",
        "Record Present",
        "Source Feature Index",
        "Original Properties JSON",
        "Geometry",
    ]
    restrictions = restrictions[output_columns].sort_values(
        ["Snapshot Time", "Source Feature Index"], kind="stable"
    ).reset_index(drop=True)
    coverage = pd.DataFrame(coverage_rows).sort_values("Snapshot Time").reset_index(drop=True)

    if restrictions.empty or restrictions.geometry.isna().any():
        raise ValueError("Restriction records or geometries are unexpectedly missing")
    if coverage["Restriction Layer Available"].sum() != 23:
        raise ValueError("Expected restriction layers in 23 of 24 archives")
    if restrictions["Restriction Feature ID"].duplicated().any():
        raise ValueError("Restriction Feature ID must uniquely identify every source feature")
    expected_state_counts = {
        "active_full_closure": 900,
        "active_emergency_access_only": 57,
        "restriction_lifted": 49,
        "unknown_status": 57,
    }
    if restrictions["Observation State"].value_counts().to_dict() != expected_state_counts:
        raise ValueError("Unexpected normalized restriction-state counts")

    DST_RECORDS.parent.mkdir(parents=True, exist_ok=True)
    restrictions.to_parquet(DST_RECORDS, index=False)
    coverage.to_parquet(DST_COVERAGE, index=False, engine="pyarrow")
    print(
        f"Saved {len(restrictions):,} rows x {len(restrictions.columns)} cols -> "
        f"{DST_RECORDS.relative_to(ROOT)}"
    )
    print(
        f"Saved {len(coverage):,} rows x {len(coverage.columns)} cols -> "
        f"{DST_COVERAGE.relative_to(ROOT)}"
    )


if __name__ == "__main__":
    main()
