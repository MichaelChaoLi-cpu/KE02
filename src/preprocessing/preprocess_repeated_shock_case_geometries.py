#!/usr/bin/env python3
"""Preprocess verified Mashiki and Yokoe geometries into the final contract.

Output: data/processed/repeated_shock_case_geometries_preprocessed.parquet

Both geometries are display and linkage inputs, not additional observations.
"""
from __future__ import annotations

from pathlib import Path

import geopandas as gpd


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "data/exp/data-preprocessing/staging/case_geometries.parquet"
OUT = (
    ROOT
    / "data/processed"
    / "repeated_shock_case_geometries_preprocessed.parquet"
)
GEOGRAPHIC_CRS = "EPSG:4326"
FINAL_COLUMNS = [
    "Case ID",
    "Case Label",
    "Adaptation Pathway",
    "Geometry Role",
    "Gate Unit",
    "Geometry Gate",
    "Geometry Gate Basis",
    "Geometry Source Reference",
    "Geometry",
]


def main() -> None:
    output = gpd.read_parquet(SOURCE).to_crs(GEOGRAPHIC_CRS)[FINAL_COLUMNS].copy()
    for column in [
        "Case ID",
        "Case Label",
        "Adaptation Pathway",
        "Geometry Role",
        "Gate Unit",
        "Geometry Gate Basis",
        "Geometry Source Reference",
    ]:
        output[column] = output[column].str.strip()
    if (
        len(output) != 2
        or set(output["Case ID"]) != {"MASHIKI-CENTRAL", "YOKOE-BRIDGE"}
        or output["Case ID"].duplicated().any()
        or not output["Geometry Gate"].all()
        or output.geometry.is_empty.any()
    ):
        raise RuntimeError("The final case-geometry contract is invalid.")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    output.to_parquet(OUT, index=False)
    print(f"Saved {len(output):,} rows x {len(output.columns)} cols -> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
