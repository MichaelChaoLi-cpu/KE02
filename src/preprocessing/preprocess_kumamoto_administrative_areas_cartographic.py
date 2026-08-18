#!/usr/bin/env python3
"""Prepare official MLIT N03 2025 Kumamoto boundaries for cartographic support.

Source lineage: exact local reuse of the KE01b audited GeoParquet.
The output is a map background and label layer, not an analytical variable set.
"""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd


ROOT = Path(__file__).resolve().parents[2]
SOURCE = (
    ROOT
    / "data/raw/reused_local/KE01b/administrative_areas"
    / "kumamoto_administrative_areas_preprocessed.parquet"
)
OUTPUT = ROOT / "data/processed/kumamoto_administrative_areas_cartographic_preprocessed.parquet"

COLUMNS = [
    "Municipality Code",
    "Prefecture Name",
    "Subprefecture Name",
    "District Name",
    "Municipality Name",
    "Ward Name",
    "Municipality Label",
    "Geometry",
]
TEXT_COLUMNS = [column for column in COLUMNS if column != "Geometry"]


def main() -> None:
    areas = gpd.read_parquet(SOURCE)
    missing = sorted(set(COLUMNS) - set(areas.columns))
    if missing:
        raise ValueError(f"Missing required N03 columns: {missing}")

    areas = areas[COLUMNS].copy()
    for column in TEXT_COLUMNS:
        areas[column] = areas[column].astype("string").str.strip()

    if len(areas) != 49:
        raise ValueError(f"Expected 49 municipality/ward polygons, found {len(areas)}")
    if areas.crs is None or areas.crs.to_epsg() != 6668:
        raise ValueError(f"Expected JGD2011 EPSG:6668, found {areas.crs}")
    if not areas["Prefecture Name"].dropna().eq("熊本県").all():
        raise ValueError("Administrative layer includes a non-Kumamoto prefecture record")
    if areas["Municipality Code"].isna().any() or not areas["Municipality Code"].is_unique:
        raise ValueError("Municipality Code must be complete and unique")
    if areas.geometry.isna().any() or areas.geometry.is_empty.any():
        raise ValueError("Administrative geometry contains missing or empty values")
    if not areas.geometry.is_valid.all():
        raise ValueError("Administrative geometry contains invalid polygons")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    areas.to_parquet(OUTPUT, index=False)
    print(f"Saved: {OUTPUT.relative_to(ROOT)}")
    print(f"Rows: {len(areas)}; columns: {len(areas.columns)}; CRS: EPSG:6668")


if __name__ == "__main__":
    main()
