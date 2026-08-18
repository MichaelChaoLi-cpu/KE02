#!/usr/bin/env python3
"""Create a blinded multi-date validation sample for Mashiki reconstruction states."""

from __future__ import annotations

import argparse
import contextlib
import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from PIL import Image, ImageDraw, ImageFont

from preprocess_mashiki_building_calibration import (
    align_and_score,
    load_raster,
    outline_coordinates,
    read_chip,
    spatial_sample,
)


SEED = 20260818
SAMPLE_PER_STATUS = 20
CHIP_SIZE_METRES = 72.0
METRIC_PIXELS = 128
DISPLAY_PIXELS = 224
ROWS_PER_SHEET = 6
STATUSES = ("retained", "suspected_rebuild", "disappeared", "new", "ambiguous")
PAIR_DATES = (
    ("2016-04-15 post-foreshock", "2016-04-16 post-mainshock"),
    ("2016-04-16 post-mainshock", "2020-11 orthophoto"),
    ("2020-11 orthophoto", "PLATEAU FY2023 orthophoto"),
)


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def chip_bounds(x: float, y: float) -> tuple[float, float, float, float]:
    half = CHIP_SIZE_METRES / 2.0
    return x - half, y - half, x + half, y + half


def render_panel(
    rgb: np.ndarray,
    geometry,
    bounds: tuple[float, float, float, float],
    label: str,
) -> Image.Image:
    image = Image.fromarray(np.clip(rgb * 255.0, 0, 255).astype(np.uint8)).resize(
        (DISPLAY_PIXELS, DISPLAY_PIXELS), Image.Resampling.LANCZOS
    )
    draw = ImageDraw.Draw(image)
    for coordinates in outline_coordinates(geometry, bounds, DISPLAY_PIXELS):
        draw.line(coordinates, fill=(255, 230, 0), width=2, joint="curve")
    draw.rectangle((0, 0, 30, 24), fill=(0, 0, 0))
    draw.text((8, 4), label, fill=(255, 255, 255), font=ImageFont.load_default())
    return image


def make_contact_sheets(chips: list[Path], destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    row_height = DISPLAY_PIXELS + 28
    width = DISPLAY_PIXELS * 6
    for offset in range(0, len(chips), ROWS_PER_SHEET):
        selected = chips[offset : offset + ROWS_PER_SHEET]
        sheet = Image.new("RGB", (width, row_height * len(selected)), (245, 245, 245))
        draw = ImageDraw.Draw(sheet)
        for row_index, path in enumerate(selected):
            y = row_index * row_height
            draw.text((6, y + 7), path.stem, fill=(0, 0, 0), font=ImageFont.load_default())
            with Image.open(path) as chip:
                sheet.paste(chip.convert("RGB"), (0, y + 28))
        sheet.save(
            destination / f"sheet_{offset // ROWS_PER_SHEET + 1:02d}.png",
            optimize=True,
        )


def choose_sample(frame: gpd.GeoDataFrame, rng: np.random.Generator) -> gpd.GeoDataFrame:
    chosen: list[int] = []
    strata: dict[int, str] = {}
    for status in STATUSES:
        available = frame.loc[frame["Match Status"].eq(status)]
        selected = spatial_sample(available, SAMPLE_PER_STATUS, rng)
        if len(selected) != SAMPLE_PER_STATUS:
            raise RuntimeError(
                f"expected {SAMPLE_PER_STATUS} records for {status}; got {len(selected)}"
            )
        chosen.extend(selected.tolist())
        strata.update({int(index): status for index in selected})
    sample = frame.loc[chosen].copy()
    sample["Source Match Status"] = [strata[int(index)] for index in sample.index]
    sample["_random"] = rng.random(len(sample))
    sample = sample.sort_values("_random").drop(columns="_random").reset_index(drop=True)
    sample["Validation ID"] = [f"RV{number:03d}" for number in range(1, len(sample) + 1)]
    for pair_number, (earlier, later) in enumerate(PAIR_DATES, start=1):
        flips = rng.integers(0, 2, len(sample))
        sample[f"Pair {pair_number} Left Is"] = np.where(flips == 0, earlier, later)
    return sample


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=project_root())
    arguments = parser.parse_args()
    root = arguments.root.resolve()
    panel_path = (
        root
        / "data/processed/mashiki_plateau_2020_2023_building_panel_preprocessed.parquet"
    )
    raster_paths = {
        "2016-04-15 post-foreshock": root
        / "data/raw/gsi/orthophoto_z18/mashiki/2016-04-15_post_foreshock/mashiki_2016-04-15_post_foreshock.tif",
        "2016-04-16 post-mainshock": root
        / "data/raw/gsi/orthophoto_z18/mashiki/combined/mashiki_2016-04-16_post_mainshock_combined.tif",
        "2020-11 orthophoto": root
        / "data/raw/plateau/mashiki/2020/orthophoto/aoi/mashiki_plateau_2020_reconstruction_validation_epsg3857.tif",
        "PLATEAU FY2023 orthophoto": root
        / "data/raw/plateau/mashiki/2023/orthophoto/aoi/mashiki_plateau_fy2023_pre_2026_baseline_epsg3857.tif",
    }
    for path in (panel_path, *raster_paths.values()):
        if not path.is_file():
            raise FileNotFoundError(path)

    output = root / "data/exp/reconstruction-validation/mashiki"
    chips_directory = output / "chips_blind_round1"
    sheets_directory = output / "contact_sheets_blind_round1"
    chips_directory.mkdir(parents=True, exist_ok=True)
    sheets_directory.mkdir(parents=True, exist_ok=True)

    panel = gpd.read_parquet(panel_path)
    panel["Centroid X (m)"] = panel.geometry.centroid.x
    panel["Centroid Y (m)"] = panel.geometry.centroid.y
    panel["Panel Area (m2)"] = panel.geometry.area
    bounds = panel.geometry.bounds
    panel["Panel Width (m)"] = bounds.maxx - bounds.minx
    panel["Panel Height (m)"] = bounds.maxy - bounds.miny

    with contextlib.ExitStack() as stack:
        rasters = {
            name: stack.enter_context(rasterio.open(path))
            for name, path in raster_paths.items()
        }
        sources = {name: load_raster(raster) for name, raster in rasters.items()}
        west = max(raster.bounds.left for raster in rasters.values())
        south = max(raster.bounds.bottom for raster in rasters.values())
        east = min(raster.bounds.right for raster in rasters.values())
        north = min(raster.bounds.top for raster in rasters.values())
        margin = CHIP_SIZE_METRES / 2.0 + 1.0
        eligible = panel.loc[
            panel["Panel Area (m2)"].between(30.0, 800.0)
            & panel["Panel Width (m)"].le(CHIP_SIZE_METRES - 12.0)
            & panel["Panel Height (m)"].le(CHIP_SIZE_METRES - 12.0)
            & panel["Centroid X (m)"].between(west + margin, east - margin)
            & panel["Centroid Y (m)"].between(south + margin, north - margin)
        ].copy()
        eligible["Spatial Grid"] = (
            ((eligible["Centroid X (m)"] - west) / (east - west) * 5)
            .clip(0, 4.999)
            .astype(int)
            .astype(str)
            + "-"
            + ((eligible["Centroid Y (m)"] - south) / (north - south) * 5)
            .clip(0, 4.999)
            .astype(int)
            .astype(str)
        )
        rng = np.random.default_rng(SEED)
        sample = choose_sample(eligible, rng)
        geometry_column = sample.geometry.name

        chip_paths: list[Path] = []
        metric_records: list[dict[str, object]] = []
        for _, row in sample.iterrows():
            bounds_tuple = chip_bounds(row["Centroid X (m)"], row["Centroid Y (m)"])
            images = {
                name: read_chip(source, bounds_tuple, DISPLAY_PIXELS)[0]
                for name, source in sources.items()
            }
            metrics_images = {
                name: read_chip(source, bounds_tuple, METRIC_PIXELS)[0]
                for name, source in sources.items()
            }
            record: dict[str, object] = {"Validation ID": row["Validation ID"]}
            panels: list[Image.Image] = []
            labels = iter("ABCDEF")
            for pair_number, (earlier, later) in enumerate(PAIR_DATES, start=1):
                left = row[f"Pair {pair_number} Left Is"]
                right = later if left == earlier else earlier
                panels.extend(
                    [
                        render_panel(
                            images[left], row[geometry_column], bounds_tuple, next(labels)
                        ),
                        render_panel(
                            images[right], row[geometry_column], bounds_tuple, next(labels)
                        ),
                    ]
                )
                score = align_and_score(metrics_images[earlier], metrics_images[later])
                for key, value in score.items():
                    record[f"Pair {pair_number} {key.replace('_', ' ').title()}"] = value
            composite = Image.new(
                "RGB", (DISPLAY_PIXELS * 6, DISPLAY_PIXELS), (255, 255, 255)
            )
            for panel_index, image in enumerate(panels):
                composite.paste(image, (panel_index * DISPLAY_PIXELS, 0))
            chip_path = chips_directory / f"{row['Validation ID']}.png"
            composite.save(chip_path, optimize=True)
            chip_paths.append(chip_path)
            metric_records.append(record)

    make_contact_sheets(chip_paths, sheets_directory)
    metrics = pd.DataFrame(metric_records)
    sample = sample.merge(metrics, on="Validation ID", how="left", validate="one_to_one")
    sample.to_parquet(
        root / "data/processed/mashiki_reconstruction_validation_sample_preprocessed.parquet",
        index=False,
    )
    mapping_columns = [
        "Validation ID",
        "Source Match Status",
        "Pair 1 Left Is",
        "Pair 2 Left Is",
        "Pair 3 Left Is",
        "2020 GML ID",
        "2023 GML ID",
    ]
    sample[mapping_columns].to_csv(output / "blind_mapping.csv", index=False)

    labels = sample[["Validation ID"]].copy()
    for pair_number in range(1, 4):
        labels[f"Round 1 Pair {pair_number} Label"] = ""
        labels[f"Round 1 Pair {pair_number} Confidence"] = ""
    labels["Round 1 Exclusion Reason"] = ""
    labels.to_csv(output / "labels_round1.csv", index=False)

    metadata = {
        "seed": SEED,
        "sample_per_source_status": SAMPLE_PER_STATUS,
        "sample_size": len(sample),
        "chip_size_metres": CHIP_SIZE_METRES,
        "display_pixels_per_panel": DISPLAY_PIXELS,
        "pair_definitions": [list(pair) for pair in PAIR_DATES],
        "source_status_counts_eligible": {
            str(key): int(value)
            for key, value in eligible["Match Status"].value_counts().items()
        },
        "sample_status_counts": {
            str(key): int(value)
            for key, value in sample["Source Match Status"].value_counts().items()
        },
        "blind_fields_hidden": [
            "Source Match Status",
            "Pair 1 Left Is",
            "Pair 2 Left Is",
            "Pair 3 Left Is",
        ],
    }
    (output / "run_metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
