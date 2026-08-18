#!/usr/bin/env python3
"""Preprocess the official Mashiki road-network FeatureServer export."""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "data/raw/official_resilience/mashiki_arcgis/mashiki_road_network_routes.geojson"
DST = ROOT / "data/processed/mashiki_official_road_network_preprocessed.parquet"


def main() -> None:
    roads = gpd.read_file(SRC)
    if roads.crs is None:
        roads = roads.set_crs("EPSG:4326")
    else:
        roads = roads.to_crs("EPSG:4326")

    rename_map = {
        "OBJECTID": "Road Segment ID",
        "rosenNo": "Route Number",
        "路線級": "Route Class",
        "確認": "Verification Code",
        "区分": "Route Component",
        "路線名": "Route Name",
        "Shape__Length": "Official Geometry Length (m)",
        "geometry": "Geometry",
    }
    missing = sorted(set(rename_map) - set(roads.columns))
    if missing:
        raise ValueError(f"Missing source columns: {missing}")
    roads = roads[list(rename_map)].rename(columns=rename_map)
    roads = roads.set_geometry("Geometry")

    for column in ["Road Segment ID", "Route Number", "Route Class", "Verification Code"]:
        roads[column] = pd.to_numeric(roads[column], errors="coerce").astype("Int64")
    roads["Official Geometry Length (m)"] = pd.to_numeric(
        roads["Official Geometry Length (m)"], errors="coerce"
    )
    for column in ["Route Component", "Route Name"]:
        roads[column] = roads[column].astype("string").str.strip()

    roads["Geometry Type"] = roads.geometry.geom_type.astype("string")
    projected_centroids = roads.to_crs("EPSG:6670").geometry.centroid
    centroid_wgs84 = gpd.GeoSeries(projected_centroids, crs="EPSG:6670").to_crs("EPSG:4326")
    roads["Centroid Longitude"] = centroid_wgs84.x
    roads["Centroid Latitude"] = centroid_wgs84.y

    output_columns = [
        "Road Segment ID",
        "Route Number",
        "Route Class",
        "Verification Code",
        "Route Component",
        "Route Name",
        "Official Geometry Length (m)",
        "Geometry Type",
        "Centroid Longitude",
        "Centroid Latitude",
        "Geometry",
    ]
    roads = roads[output_columns]

    if roads["Road Segment ID"].isna().any() or not roads["Road Segment ID"].is_unique:
        raise ValueError("Road Segment ID must be complete and unique")
    if roads.geometry.isna().any() or roads.geometry.is_empty.any():
        raise ValueError("Road geometry is missing or empty")
    if (~roads.geometry.is_valid).any():
        raise ValueError("Invalid road geometry detected")

    DST.parent.mkdir(parents=True, exist_ok=True)
    roads.to_parquet(DST, index=False)
    print(
        f"Saved {len(roads):,} rows x {len(roads.columns)} cols -> "
        f"{DST.relative_to(ROOT)}"
    )


if __name__ == "__main__":
    main()
