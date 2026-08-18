#!/usr/bin/env python3
"""Preprocess and conservatively link the candidate resilience-intervention ledger."""

from __future__ import annotations

import re
from pathlib import Path

import geopandas as gpd
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "data/exp/feasibility-check/candidate_intervention_ledger.csv"
ROAD_SRC = ROOT / "data/raw/official_resilience/mashiki_arcgis/mashiki_road_network_routes.geojson"
TRANSPORT_SRC = ROOT / "data/raw/official_resilience/mashiki_arcgis/mashiki_urban_planning_transport_facilities.geojson"
DST = ROOT / "data/processed/mashiki_resilience_interventions_preprocessed.parquet"
EVENT_DATE = pd.Timestamp("2026-07-28")


MATCH_RULES = {
    "I001": ("Mashiki Urban Planning Transport Facilities", "益城中央線"),
    "I002": ("Mashiki Urban Planning Transport Facilities", "益城中央線"),
    "I003": ("Mashiki Urban Planning Transport Facilities", "益城中央線"),
    "I005": ("Mashiki Official Road Network", "府内古閑線"),
    "I007": ("Mashiki Official Road Network", "惣領南線"),
    "I008": ("Mashiki Official Road Network", "五楽安永線"),
    "I009": ("Mashiki Official Road Network", "大久保古川線"),
    "I011": ("Mashiki Official Road Network", "道安寺線"),
    "I012": ("Mashiki Official Road Network", "道安寺線"),
    "I013": ("Mashiki Official Road Network", "田中線"),
    "I015": ("Mashiki Official Road Network", "堤黒石崎線"),
    "I019": ("Mashiki Official Road Network", "上小谷線"),
}


def completion_interval(value: str) -> tuple[pd.Timestamp, pd.Timestamp]:
    value = value.strip()
    fiscal_match = re.fullmatch(r"FY(\d{4})", value)
    if fiscal_match:
        year = int(fiscal_match.group(1))
        return (
            pd.Timestamp(year=year, month=4, day=1),
            pd.Timestamp(year=year + 1, month=3, day=31),
        )
    date = pd.to_datetime(value, format="%Y-%m-%d", errors="raise")
    return date, date


def extent_metres(value: str) -> float:
    match = re.fullmatch(r"\s*([0-9.]+)\s*(km|m)\s*", value)
    if not match:
        raise ValueError(f"Unrecognized completed extent: {value!r}")
    amount = float(match.group(1))
    return amount * 1000.0 if match.group(2) == "km" else amount


def main() -> None:
    ledger = pd.read_csv(SRC, encoding="utf-8")
    roads = gpd.read_file(ROAD_SRC)
    transport = gpd.read_file(TRANSPORT_SRC)

    road_lookup = {
        str(row["路線名"]).strip(): (int(row["OBJECTID"]), str(row["路線名"]).strip())
        for _, row in roads.iterrows()
    }
    transport_lookup: dict[str, list[tuple[int, str]]] = {}
    for _, row in transport.iterrows():
        name = str(row["tf_name"]).strip()
        transport_lookup.setdefault(name, []).append((int(row["OBJECTID"]), name))

    earliest = []
    latest = []
    completed_extent_m = []
    matched_layers = []
    matched_ids = []
    matched_names = []
    match_counts = []

    for row in ledger.itertuples(index=False):
        first, last = completion_interval(str(row.completion_time))
        earliest.append(first)
        latest.append(last)
        completed_extent_m.append(extent_metres(str(row.completed_extent)))

        rule = MATCH_RULES.get(str(row.intervention_id))
        matches: list[tuple[int, str]] = []
        layer = None
        if rule:
            layer, official_name = rule
            if layer == "Mashiki Official Road Network":
                if official_name in road_lookup:
                    matches = [road_lookup[official_name]]
            else:
                matches = transport_lookup.get(official_name, [])
        matched_layers.append(layer)
        matched_ids.append(";".join(str(item[0]) for item in matches) or None)
        matched_names.append(";".join(item[1] for item in matches) or None)
        match_counts.append(len(matches))

    rename_map = {
        "intervention_id": "Intervention ID",
        "area": "Area",
        "asset_name": "Asset Name",
        "asset_type": "Asset Type",
        "completed_extent": "Reported Completed Extent",
        "completion_time": "Reported Completion Time",
        "status_at_2026_event": "Completion Status at 2026 Event",
        "geometry_status": "Geometry Status",
        "source_url": "Source URL",
        "quality_flag": "Quality Flag",
    }
    output = ledger[list(rename_map)].rename(columns=rename_map)
    output["Completed Extent (m)"] = completed_extent_m
    output["Completion Date Earliest"] = earliest
    output["Completion Date Latest"] = latest
    output["Completed Before 2026 Event"] = output["Completion Date Latest"] < EVENT_DATE
    output["Matched Network Layer"] = pd.Series(matched_layers, dtype="string")
    output["Matched Official Feature IDs"] = pd.Series(matched_ids, dtype="string")
    output["Matched Official Feature Names"] = pd.Series(matched_names, dtype="string")
    output["Route Match Count"] = pd.Series(match_counts, dtype="Int64")

    # A whole-route match does not identify the completed intervention subsegment.
    output["Geometry Use Eligible"] = False
    output["Treatment Use Eligible"] = False

    for column in [
        "Intervention ID",
        "Area",
        "Asset Name",
        "Asset Type",
        "Reported Completed Extent",
        "Reported Completion Time",
        "Completion Status at 2026 Event",
        "Geometry Status",
        "Source URL",
        "Quality Flag",
    ]:
        output[column] = output[column].astype("string").str.strip()

    output_columns = [
        "Intervention ID",
        "Area",
        "Asset Name",
        "Asset Type",
        "Reported Completed Extent",
        "Completed Extent (m)",
        "Reported Completion Time",
        "Completion Date Earliest",
        "Completion Date Latest",
        "Completion Status at 2026 Event",
        "Completed Before 2026 Event",
        "Geometry Status",
        "Matched Network Layer",
        "Matched Official Feature IDs",
        "Matched Official Feature Names",
        "Route Match Count",
        "Geometry Use Eligible",
        "Treatment Use Eligible",
        "Source URL",
        "Quality Flag",
    ]
    output = output[output_columns]

    if output["Intervention ID"].isna().any() or not output["Intervention ID"].is_unique:
        raise ValueError("Intervention ID must be complete and unique")
    if not output["Completed Before 2026 Event"].all():
        raise ValueError("Candidate ledger contains an intervention not completed before the event")
    if output["Geometry Use Eligible"].any() or output["Treatment Use Eligible"].any():
        raise ValueError("Unverified intervention geometry must remain ineligible")

    DST.parent.mkdir(parents=True, exist_ok=True)
    output.to_parquet(DST, index=False, engine="pyarrow")
    print(
        f"Saved {len(output):,} rows x {len(output.columns)} cols -> "
        f"{DST.relative_to(ROOT)}"
    )


if __name__ == "__main__":
    main()
