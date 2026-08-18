#!/usr/bin/env python3
"""Build a traceable 100-building orthophoto calibration sample for Mashiki.

The raw GSI and PLATEAU files are never modified. PLATEAU CityGML
PolyhedralSurface geometries are first converted to two-dimensional
MultiPolygons with GDAL, then repaired and projected to EPSG:3857. The sample
is deliberately stratified for calibration and must not be used to estimate
population damage prevalence without sampling weights.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import subprocess
import tempfile
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from PIL import Image, ImageDraw, ImageFont
from rasterio.windows import from_bounds
from scipy.ndimage import shift as image_shift
from skimage import color, exposure, filters
from skimage.metrics import structural_similarity
from skimage.registration import phase_cross_correlation


SEED = 20260818
CHIP_SIZE_METRES = 48.0
METRIC_PIXELS = 128
DISPLAY_PIXELS = 256
SAMPLE_SIZE = 100


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def clean_gdal_environment() -> dict[str, str]:
    environment = os.environ.copy()
    environment.pop("PROJ_LIB", None)
    environment.pop("PROJ_DATA", None)
    environment.pop("GDAL_DATA", None)
    return environment


def convert_citygml_buildings(gml_path: Path, gpkg_path: Path) -> gpd.GeoDataFrame:
    subprocess.run(
        [
            "ogr2ogr",
            "-f",
            "GPKG",
            str(gpkg_path),
            str(gml_path),
            "Building",
            "-dim",
            "XY",
            "-nlt",
            "MULTIPOLYGON",
            "-skipfailures",
        ],
        check=True,
        env=clean_gdal_environment(),
        stdout=subprocess.DEVNULL,
    )
    return gpd.read_file(gpkg_path, layer="Building")


def load_buildings(gml_directory: Path) -> gpd.GeoDataFrame:
    frames: list[gpd.GeoDataFrame] = []
    with tempfile.TemporaryDirectory(prefix="ke02-mashiki-citygml-") as temporary:
        temporary_root = Path(temporary)
        for index, gml_path in enumerate(sorted(gml_directory.glob("*.gml"))):
            frames.append(
                convert_citygml_buildings(
                    gml_path,
                    temporary_root / f"building_{index:02d}.gpkg",
                )
            )
    if not frames:
        raise RuntimeError(f"no CityGML building files found in {gml_directory}")

    buildings = gpd.GeoDataFrame(
        pd.concat(frames, ignore_index=True),
        crs=frames[0].crs,
    )
    buildings = buildings.drop_duplicates(subset="gml_id", keep="first")
    buildings = buildings.to_crs(3857)
    # Projected roof and ground surfaces overlap; zero-width wall faces make
    # the source MultiPolygons invalid in 2D. buffer(0) dissolves the projected
    # surfaces into one valid footprint per source building.
    buildings.geometry = buildings.geometry.buffer(0)
    buildings = buildings.loc[
        buildings.geometry.notna()
        & ~buildings.geometry.is_empty
        & buildings.geometry.is_valid
    ].copy()
    # PLATEAU uses sentinel values rather than nulls for some unknown fields.
    # Normalize them before any processed artifact is written so that models
    # cannot interpret 9,999 storeys, -9,999 metres, or year 0001 literally.
    buildings["measuredHeight"] = pd.to_numeric(
        buildings["measuredHeight"], errors="coerce"
    ).where(lambda values: values.gt(0) & values.lt(9999))
    buildings["storeysAboveGround"] = (
        pd.to_numeric(buildings["storeysAboveGround"], errors="coerce")
        .mask(lambda values: values.ge(9999))
        .astype("Int64")
    )
    buildings["surveyYear"] = buildings["surveyYear"].astype("string").mask(
        buildings["surveyYear"].astype("string").isin(["0001", "1", ""])
    )
    return buildings


def chip_bounds(centroid_x: float, centroid_y: float) -> tuple[float, float, float, float]:
    half = CHIP_SIZE_METRES / 2.0
    return (
        centroid_x - half,
        centroid_y - half,
        centroid_x + half,
        centroid_y + half,
    )


def load_raster(source: rasterio.io.DatasetReader) -> dict[str, object]:
    rgb = np.moveaxis(source.read([1, 2, 3]), 0, -1)
    if source.count >= 4:
        alpha = source.read(4)
    else:
        alpha = np.full((source.height, source.width), 255, dtype=np.uint8)
    return {
        "rgb": rgb,
        "alpha": alpha,
        "transform": source.transform,
        "width": source.width,
        "height": source.height,
    }


def read_chip(
    source: dict[str, object],
    bounds: tuple[float, float, float, float],
    pixels: int,
) -> tuple[np.ndarray, np.ndarray]:
    window = from_bounds(*bounds, transform=source["transform"])
    column_start = max(0, int(np.floor(window.col_off)))
    row_start = max(0, int(np.floor(window.row_off)))
    column_stop = min(
        int(source["width"]),
        int(np.ceil(window.col_off + window.width)),
    )
    row_stop = min(
        int(source["height"]),
        int(np.ceil(window.row_off + window.height)),
    )
    rgb_crop = source["rgb"][row_start:row_stop, column_start:column_stop]
    alpha_crop = source["alpha"][row_start:row_stop, column_start:column_stop]
    if rgb_crop.size == 0:
        raise RuntimeError(f"empty raster crop for bounds {bounds}")
    rgb = np.asarray(
        Image.fromarray(rgb_crop).resize((pixels, pixels), Image.Resampling.BILINEAR),
        dtype=np.float32,
    ) / 255.0
    alpha = np.asarray(
        Image.fromarray(alpha_crop).resize((pixels, pixels), Image.Resampling.NEAREST),
        dtype=np.float32,
    ) / 255.0
    return rgb, alpha


def align_and_score(reference: np.ndarray, comparison: np.ndarray) -> dict[str, float]:
    reference_gray = color.rgb2gray(reference)
    comparison_gray = color.rgb2gray(comparison)
    reference_edge = filters.sobel(reference_gray)
    comparison_edge = filters.sobel(comparison_gray)
    shift, registration_error, _ = phase_cross_correlation(
        reference_edge,
        comparison_edge,
        upsample_factor=4,
        normalization="phase",
    )
    shift = np.clip(shift, -12.0, 12.0)
    aligned = image_shift(
        comparison,
        shift=(float(shift[0]), float(shift[1]), 0.0),
        order=1,
        mode="nearest",
        prefilter=False,
    )
    matched = exposure.match_histograms(aligned, reference, channel_axis=-1)
    matched = np.clip(matched, 0.0, 1.0)
    ssim_value = structural_similarity(
        reference,
        matched,
        channel_axis=-1,
        data_range=1.0,
    )
    matched_edge = filters.sobel(color.rgb2gray(matched))
    edge_mae = float(np.mean(np.abs(reference_edge - matched_edge)))
    rgb_mae = float(np.mean(np.abs(reference - matched)))
    score = (
        0.60 * (1.0 - float(ssim_value))
        + 0.25 * min(1.0, edge_mae * 4.0)
        + 0.15 * min(1.0, rgb_mae * 2.0)
    )
    return {
        "score": float(score),
        "ssim": float(ssim_value),
        "edge_mae": edge_mae,
        "rgb_mae": rgb_mae,
        "shift_row_pixels": float(shift[0]),
        "shift_col_pixels": float(shift[1]),
        "registration_error": float(registration_error),
    }


def outline_coordinates(
    geometry,
    bounds: tuple[float, float, float, float],
    pixels: int,
) -> list[list[tuple[float, float]]]:
    west, south, east, north = bounds
    polygons = list(geometry.geoms) if geometry.geom_type == "MultiPolygon" else [geometry]
    output: list[list[tuple[float, float]]] = []
    for polygon in polygons:
        coordinates = []
        for x_coordinate, y_coordinate in polygon.exterior.coords:
            pixel_x = (x_coordinate - west) / (east - west) * pixels
            pixel_y = (north - y_coordinate) / (north - south) * pixels
            coordinates.append((pixel_x, pixel_y))
        output.append(coordinates)
    return output


def render_panel(
    rgb: np.ndarray,
    geometry,
    bounds: tuple[float, float, float, float],
    panel_label: str,
) -> Image.Image:
    array = np.clip(rgb * 255.0, 0, 255).astype(np.uint8)
    image = Image.fromarray(array).resize(
        (DISPLAY_PIXELS, DISPLAY_PIXELS),
        Image.Resampling.LANCZOS,
    )
    draw = ImageDraw.Draw(image)
    for coordinates in outline_coordinates(geometry, bounds, DISPLAY_PIXELS):
        draw.line(coordinates, fill=(255, 230, 0), width=2, joint="curve")
    draw.rectangle((0, 0, 28, 24), fill=(0, 0, 0))
    draw.text((8, 4), panel_label, fill=(255, 255, 255), font=ImageFont.load_default())
    return image


def spatial_sample(
    frame: pd.DataFrame,
    count: int,
    rng: np.random.Generator,
) -> pd.Index:
    if frame.empty or count <= 0:
        return pd.Index([])
    working = frame.copy()
    working["_random"] = rng.random(len(working))
    working = working.sort_values(["Spatial Grid", "_random"])
    groups = [group.index.tolist() for _, group in working.groupby("Spatial Grid")]
    selected: list[int] = []
    while groups and len(selected) < min(count, len(working)):
        next_groups = []
        for group in groups:
            if group and len(selected) < count:
                selected.append(group.pop(0))
            if group:
                next_groups.append(group)
        groups = next_groups
    return pd.Index(selected)


def create_sample(candidates: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    rng = np.random.default_rng(SEED)
    selected: list[int] = []
    assignments: dict[int, str] = {}
    q2016_low = candidates["2016 Change Score"].quantile(0.30)
    q2026_low = candidates["2026 Change Score"].quantile(0.30)
    q2016_high = candidates["2016 Change Score"].quantile(0.85)
    q2026_high = candidates["2026 Change Score"].quantile(0.85)

    strata = [
        (
            "Stable Low Change",
            candidates.loc[
                (candidates["2016 Change Score"] <= q2016_low)
                & (candidates["2026 Change Score"] <= q2026_low)
            ],
            25,
        ),
        (
            "High 2016 Change",
            candidates.loc[candidates["2016 Change Score"] >= q2016_high],
            25,
        ),
        (
            "High 2026 Change",
            candidates.loc[candidates["2026 Change Score"] >= q2026_high],
            25,
        ),
    ]
    for stratum_name, stratum, count in strata:
        available = stratum.loc[~stratum.index.isin(selected)]
        chosen = spatial_sample(available, count, rng)
        selected.extend(chosen.tolist())
        assignments.update({int(index): stratum_name for index in chosen})

    remainder = candidates.loc[~candidates.index.isin(selected)]
    chosen = spatial_sample(remainder, SAMPLE_SIZE - len(selected), rng)
    selected.extend(chosen.tolist())
    assignments.update({int(index): "General Spatial Sample" for index in chosen})

    sample = candidates.loc[selected].copy()
    sample["Sampling Stratum"] = [assignments[int(index)] for index in sample.index]
    sample["_sort"] = rng.random(len(sample))
    sample = sample.sort_values("_sort").drop(columns="_sort").reset_index(drop=True)
    sample["Calibration ID"] = [f"M{index:03d}" for index in range(1, len(sample) + 1)]
    sample["Pair 1 Left Is"] = np.where(
        rng.integers(0, 2, len(sample)) == 0,
        "2016-04-15 post-foreshock",
        "2016-04-16 post-mainshock",
    )
    sample["Pair 2 Left Is"] = np.where(
        rng.integers(0, 2, len(sample)) == 0,
        "PLATEAU FY2023 pre-2026 baseline",
        "2026 post-event",
    )
    return sample


def make_contact_sheets(chip_paths: list[Path], output_directory: Path) -> None:
    output_directory.mkdir(parents=True, exist_ok=True)
    rows_per_sheet = 5
    row_height = DISPLAY_PIXELS + 26
    for sheet_index in range(0, len(chip_paths), rows_per_sheet):
        selected = chip_paths[sheet_index : sheet_index + rows_per_sheet]
        sheet = Image.new(
            "RGB",
            (DISPLAY_PIXELS * 4, row_height * len(selected)),
            (245, 245, 245),
        )
        draw = ImageDraw.Draw(sheet)
        for row_index, path in enumerate(selected):
            chip = Image.open(path).convert("RGB")
            y_offset = row_index * row_height
            sheet.paste(chip, (0, y_offset + 26))
            draw.text(
                (6, y_offset + 6),
                path.stem,
                fill=(0, 0, 0),
                font=ImageFont.load_default(),
            )
        destination = output_directory / f"sheet_{sheet_index // rows_per_sheet + 1:02d}.png"
        sheet.save(destination, optimize=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=project_root())
    arguments = parser.parse_args()
    root = arguments.root.resolve()

    gml_directory = (
        root
        / "data/raw/plateau/mashiki/2023/citygml/aoi_source/udx/bldg"
    )
    raster_paths = {
        "2016_pre": root
        / "data/raw/gsi/orthophoto_z18/mashiki/2016-04-15_post_foreshock/mashiki_2016-04-15_post_foreshock.tif",
        "2016_post": root
        / "data/raw/gsi/orthophoto_z18/mashiki/combined/mashiki_2016-04-16_post_mainshock_combined.tif",
        "2016_post_primary": root
        / "data/raw/gsi/orthophoto_z18/mashiki/2016-04-16_post_mainshock/mashiki_2016-04-16_post_mainshock.tif",
        "2026_pre": root
        / "data/raw/plateau/mashiki/2023/orthophoto/aoi/mashiki_plateau_fy2023_pre_2026_baseline_epsg3857.tif",
        "2026_post": root
        / "data/raw/gsi/orthophoto_z18/mashiki/combined/mashiki_2026-07-29_08-03_post_event_combined.tif",
        "2026_post_primary": root
        / "data/raw/gsi/orthophoto_z18/mashiki/2026-08-03_post_event/mashiki_2026-08-03_post_event.tif",
    }
    for path in raster_paths.values():
        if not path.is_file():
            raise FileNotFoundError(path)

    output_directory = root / "data/exp/building-label-calibration/mashiki"
    chip_directory = output_directory / "chips_blind_round1"
    sheet_directory = output_directory / "contact_sheets_blind_round1"
    processed_directory = root / "data/processed"
    processed_directory.mkdir(parents=True, exist_ok=True)
    chip_directory.mkdir(parents=True, exist_ok=True)

    buildings = load_buildings(gml_directory)
    buildings["Centroid X (m)"] = buildings.geometry.centroid.x
    buildings["Centroid Y (m)"] = buildings.geometry.centroid.y
    buildings["Roof Area (m2)"] = pd.to_numeric(
        buildings["buildingRoofEdgeArea"], errors="coerce"
    )

    with contextlib.ExitStack() as stack:
        sources = {
            name: stack.enter_context(rasterio.open(path))
            for name, path in raster_paths.items()
        }
        raster_data = {name: load_raster(source) for name, source in sources.items()}
        common_west = max(source.bounds.left for source in sources.values())
        common_south = max(source.bounds.bottom for source in sources.values())
        common_east = min(source.bounds.right for source in sources.values())
        common_north = min(source.bounds.top for source in sources.values())
        margin = CHIP_SIZE_METRES / 2.0 + 2.0
        buildings = buildings.loc[
            buildings["Roof Area (m2)"].between(40.0, 400.0)
            & buildings["Centroid X (m)"].between(common_west + margin, common_east - margin)
            & buildings["Centroid Y (m)"].between(common_south + margin, common_north - margin)
        ].copy()

        records: list[dict[str, float | str]] = []
        total = len(buildings)
        for progress, (index, row) in enumerate(buildings.iterrows(), start=1):
            bounds = chip_bounds(row["Centroid X (m)"], row["Centroid Y (m)"])
            chips = {
                name: read_chip(source, bounds, METRIC_PIXELS)
                for name, source in raster_data.items()
            }
            coverage_2016 = float(chips["2016_post_primary"][1].mean())
            coverage_2026 = float(chips["2026_post_primary"][1].mean())
            if min(coverage_2016, coverage_2026) < 0.995:
                continue
            metric_2016 = align_and_score(chips["2016_pre"][0], chips["2016_post"][0])
            metric_2026 = align_and_score(chips["2026_pre"][0], chips["2026_post"][0])
            records.append(
                {
                    "_source_index": int(index),
                    "2016 Primary Coverage": coverage_2016,
                    "2026 Primary Coverage": coverage_2026,
                    "2016 Change Score": metric_2016["score"],
                    "2016 SSIM": metric_2016["ssim"],
                    "2016 Edge MAE": metric_2016["edge_mae"],
                    "2016 RGB MAE": metric_2016["rgb_mae"],
                    "2016 Shift Row (pixels)": metric_2016["shift_row_pixels"],
                    "2016 Shift Col (pixels)": metric_2016["shift_col_pixels"],
                    "2026 Change Score": metric_2026["score"],
                    "2026 SSIM": metric_2026["ssim"],
                    "2026 Edge MAE": metric_2026["edge_mae"],
                    "2026 RGB MAE": metric_2026["rgb_mae"],
                    "2026 Shift Row (pixels)": metric_2026["shift_row_pixels"],
                    "2026 Shift Col (pixels)": metric_2026["shift_col_pixels"],
                }
            )
            if progress % 500 == 0:
                print(f"scored {progress}/{total} filtered buildings", flush=True)

        metrics = pd.DataFrame(records).set_index("_source_index")
        buildings = buildings.join(metrics, how="inner")
        buildings["Spatial Grid"] = (
            ((buildings["Centroid X (m)"] - common_west) / (common_east - common_west) * 5)
            .clip(0, 4.999)
            .astype(int)
            .astype(str)
            + "-"
            + ((buildings["Centroid Y (m)"] - common_south) / (common_north - common_south) * 5)
            .clip(0, 4.999)
            .astype(int)
            .astype(str)
        )

        sample = create_sample(buildings)
        if len(sample) != SAMPLE_SIZE:
            raise RuntimeError(f"expected {SAMPLE_SIZE} sample buildings, got {len(sample)}")

        chip_paths: list[Path] = []
        for _, row in sample.iterrows():
            bounds = chip_bounds(row["Centroid X (m)"], row["Centroid Y (m)"])
            raw = {
                name: read_chip(raster_data[name], bounds, DISPLAY_PIXELS)[0]
                for name in ("2016_pre", "2016_post", "2026_pre", "2026_post")
            }
            if row["Pair 1 Left Is"] == "2016-04-15 post-foreshock":
                pair1 = (raw["2016_pre"], raw["2016_post"])
            else:
                pair1 = (raw["2016_post"], raw["2016_pre"])
            if row["Pair 2 Left Is"] == "PLATEAU FY2023 pre-2026 baseline":
                pair2 = (raw["2026_pre"], raw["2026_post"])
            else:
                pair2 = (raw["2026_post"], raw["2026_pre"])
            panels = [
                render_panel(pair1[0], row.geometry, bounds, "A"),
                render_panel(pair1[1], row.geometry, bounds, "B"),
                render_panel(pair2[0], row.geometry, bounds, "C"),
                render_panel(pair2[1], row.geometry, bounds, "D"),
            ]
            composite = Image.new(
                "RGB",
                (DISPLAY_PIXELS * 4, DISPLAY_PIXELS),
                (255, 255, 255),
            )
            for panel_index, panel in enumerate(panels):
                composite.paste(panel, (panel_index * DISPLAY_PIXELS, 0))
            destination = chip_directory / f"{row['Calibration ID']}.png"
            composite.save(destination, optimize=True)
            chip_paths.append(destination)

    make_contact_sheets(chip_paths, sheet_directory)

    selected_columns = {
        "gml_id": "GML ID",
        "buildingID": "Building ID",
        "creationDate": "Creation Date",
        "measuredHeight": "Height (m)",
        "storeysAboveGround": "Storeys Above Ground",
        "usage": "Building Use Code",
        "buildingStructureType": "Structure Type Code",
        "surveyYear": "Survey Year",
        "geometry": "Footprint Geometry",
    }
    candidate_columns = [
        *selected_columns.keys(),
        "Roof Area (m2)",
        "Centroid X (m)",
        "Centroid Y (m)",
        "Spatial Grid",
        "2016 Primary Coverage",
        "2026 Primary Coverage",
        "2016 Change Score",
        "2016 SSIM",
        "2016 Edge MAE",
        "2016 RGB MAE",
        "2016 Shift Row (pixels)",
        "2016 Shift Col (pixels)",
        "2026 Change Score",
        "2026 SSIM",
        "2026 Edge MAE",
        "2026 RGB MAE",
        "2026 Shift Row (pixels)",
        "2026 Shift Col (pixels)",
    ]
    candidates_output = buildings[candidate_columns].rename(columns=selected_columns)
    candidates_output = candidates_output.set_geometry("Footprint Geometry")
    candidates_output.to_parquet(
        processed_directory / "mashiki_building_candidates_preprocessed.parquet",
        index=False,
    )

    sample_columns = [
        "Calibration ID",
        "Sampling Stratum",
        "Pair 1 Left Is",
        "Pair 2 Left Is",
        *candidate_columns,
    ]
    sample_output = sample[sample_columns].rename(columns=selected_columns)
    sample_output = sample_output.set_geometry("Footprint Geometry")
    sample_output.to_parquet(
        processed_directory / "mashiki_calibration_sample_preprocessed.parquet",
        index=False,
    )

    label_template = sample[["Calibration ID", "Sampling Stratum"]].copy()
    for column in [
        "Round 1 Pair 1 Label",
        "Round 1 Pair 1 Confidence",
        "Round 1 Pair 2 Label",
        "Round 1 Pair 2 Confidence",
        "Round 1 Exclusion Reason",
        "Round 2 Pair 1 Label",
        "Round 2 Pair 1 Confidence",
        "Round 2 Pair 2 Label",
        "Round 2 Pair 2 Confidence",
        "Round 2 Exclusion Reason",
        "Adjudicated 2016 Label",
        "Adjudicated 2016 Confidence",
        "Adjudicated 2026 Label",
        "Adjudicated 2026 Confidence",
        "Adjudication Note",
    ]:
        label_template[column] = ""
    label_template.to_csv(output_directory / "labels.csv", index=False)

    run_metadata = {
        "seed": SEED,
        "sample_size": len(sample),
        "candidate_count": len(buildings),
        "chip_size_metres": CHIP_SIZE_METRES,
        "metric_pixels": METRIC_PIXELS,
        "display_pixels": DISPLAY_PIXELS,
        "sampling_design": "25 stable-low, 25 high-2016-change, 25 high-2026-change, remainder general spatial sample; de-duplicated and spatial-grid balanced",
        "label_target": "visible structural change, not asserted earthquake causation",
        "raw_files_modified": False,
    }
    (output_directory / "run_metadata.json").write_text(
        json.dumps(run_metadata, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(run_metadata, indent=2))


if __name__ == "__main__":
    main()
