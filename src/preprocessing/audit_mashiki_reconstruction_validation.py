#!/usr/bin/env python3
"""Audit reconstruction-validation artifacts without changing analytical labels."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import geopandas as gpd
import pandas as pd
import rasterio


ROOT = Path(__file__).resolve().parents[2]
EXP = ROOT / "data/exp/reconstruction-validation/mashiki"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    sample = gpd.read_parquet(
        ROOT / "data/processed/mashiki_reconstruction_validation_sample_preprocessed.parquet"
    )
    final = gpd.read_parquet(
        ROOT / "data/processed/mashiki_reconstruction_validation_final_preprocessed.parquet"
    )
    round1 = pd.read_csv(EXP / "labels_round1.csv", dtype=str)
    round2 = pd.read_csv(EXP / "round2/labels_round2.csv", dtype=str)
    round2_design = pd.read_csv(EXP / "round2/review_design_round2.csv", dtype=str)
    metadata_path = ROOT / "data/raw/plateau/mashiki/2020/orthophoto/metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    archive = metadata_path.parent / metadata["archive"]["path"]
    raster = metadata_path.parent / metadata["derived_orthophoto"]

    checks: dict[str, bool] = {
        "sample_has_100_rows": len(sample) == 100,
        "final_has_100_rows": len(final) == 100,
        "sample_ids_unique": sample["Validation ID"].is_unique,
        "final_ids_unique": final["Validation ID"].is_unique,
        "sample_statuses_balanced": sample["Source Match Status"].value_counts().eq(20).all(),
        "sample_geometry_valid": sample.geometry.is_valid.all() and (~sample.geometry.is_empty).all(),
        "final_geometry_valid": final.geometry.is_valid.all() and (~final.geometry.is_empty).all(),
        "round1_complete": round1.filter(like="Label").notna().all().all()
        and round1.filter(like="Confidence").notna().all().all(),
        "round2_complete": len(round2) == 53
        and round2[["Round 2 Label", "Round 2 Confidence"]].notna().all().all(),
        "round2_design_is_fixed": len(round2_design) == 53
        and round2_design["Review ID"].is_unique
        and set(round2_design["Review ID"]) == set(round2["Review ID"]),
        "round1_chip_count": len(list((EXP / "chips_blind_round1").glob("*.png"))) == 100,
        "round1_sheet_count": len(list((EXP / "contact_sheets_blind_round1").glob("*.png"))) == 17,
        "round2_chip_count": len(list((EXP / "round2/chips_blind").glob("*.png"))) == 53,
        "round2_sheet_count": len(list((EXP / "round2/contact_sheets_blind").glob("*.png"))) == 11,
        "inventory_eligible_count_is_91": int(final["Final Inventory Validation Eligible"].sum()) == 91,
        "longitudinal_eligible_count_is_82": int(final["Final Longitudinal Validation Eligible"].sum()) == 82,
        "archive_size_matches": archive.stat().st_size == metadata["archive"]["bytes"],
        "raster_size_matches": raster.stat().st_size == metadata["derived_orthophoto_bytes"],
        "archive_sha256_matches": sha256(archive) == metadata["archive"]["sha256"],
        "raster_sha256_matches": sha256(raster) == metadata["derived_orthophoto_sha256"],
    }
    with rasterio.open(raster) as source:
        checks.update(
            {
                "raster_crs_is_epsg3857": source.crs.to_epsg() == 3857,
                "raster_dimensions_match": (source.width, source.height)
                == (
                    metadata["derived_orthophoto_width_pixels"],
                    metadata["derived_orthophoto_height_pixels"],
                ),
                "raster_resolution_matches": abs(source.res[0] - 0.5) < 1e-9
                and abs(source.res[1] - 0.5) < 1e-9,
                "raster_has_three_bands": source.count == 3,
            }
        )
    checks = {name: bool(value) for name, value in checks.items()}
    result = {
        "all_passed": all(checks.values()),
        "checks": checks,
        "counts": {
            "sample": len(sample),
            "round1_pair_labels": 300,
            "round2_pair_labels": len(round2),
            "inventory_validation_eligible": int(
                final["Final Inventory Validation Eligible"].sum()
            ),
            "longitudinal_validation_eligible": int(
                final["Final Longitudinal Validation Eligible"].sum()
            ),
        },
    }
    (EXP / "audit_integrity.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, indent=2))
    if not result["all_passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
