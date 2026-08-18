#!/usr/bin/env python3
"""Build a conservative FY2020--FY2023 PLATEAU building-change panel for Mashiki."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import shapely

from preprocess_mashiki_building_calibration import load_buildings


CANDIDATE_DISTANCE_METRES = 12.0
STABLE_IOU = 0.60
STABLE_MIN_COVERAGE = 0.75
STABLE_MAX_CENTROID_DISTANCE = 6.0
REBUILD_MAX_GAP = 2.0
REBUILD_MAX_CENTROID_DISTANCE = 8.0
REBUILD_MIN_AREA_SIMILARITY = 0.50
REBUILD_MIN_SCORE = 0.55


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def clean_string(series: pd.Series) -> pd.Series:
    result = series.astype("string").str.strip()
    return result.mask(result.isin(["", "None", "nan", "<NA>"]))


def clean_number(series: pd.Series, *, integer: bool = False) -> pd.Series:
    result = pd.to_numeric(series, errors="coerce")
    if integer:
        return result.astype("Int64")
    return result.astype("float64")


def standardize_buildings(raw: gpd.GeoDataFrame, year: int) -> gpd.GeoDataFrame:
    output = gpd.GeoDataFrame(index=raw.index, geometry=raw.geometry, crs=raw.crs)
    output["GML ID"] = clean_string(raw["gml_id"])
    output["Building ID"] = clean_string(raw["buildingID"])
    output["Height (m)"] = clean_number(raw["measuredHeight"])
    output["Storeys Above Ground"] = clean_number(
        raw["storeysAboveGround"], integer=True
    )
    output["Building Use Code"] = clean_number(raw["usage"], integer=True)
    output["Structure Type Code"] = clean_number(
        raw["buildingStructureType"], integer=True
    )
    output["Survey Year"] = clean_string(raw["surveyYear"])
    if year == 2020:
        output["Construction Year"] = clean_string(raw["yearOfConstruction"]).mask(
            lambda values: values.isin(["0000", "0001", "1", "9999"])
        )
        output["Creation Date"] = pd.Series(pd.NA, index=output.index, dtype="string")
        output["Source Building Area (m2)"] = clean_number(
            raw["buildingFootprintArea"]
        ).where(lambda values: values.gt(0))
    else:
        output["Construction Year"] = pd.Series(
            pd.NA, index=output.index, dtype="string"
        )
        output["Creation Date"] = clean_string(raw["creationDate"])
        output["Source Building Area (m2)"] = clean_number(
            raw["buildingRoofEdgeArea"]
        ).where(lambda values: values.gt(0))

    output["Computed Footprint Area (m2)"] = output.geometry.area
    output["Centroid X (m)"] = output.geometry.centroid.x
    output["Centroid Y (m)"] = output.geometry.centroid.y
    output["PLATEAU Release Year"] = year
    output = output.rename_geometry("Footprint Geometry")
    output = output.sort_values("GML ID", kind="stable").reset_index(drop=True)
    return output


def candidate_pairs(
    buildings_2020: gpd.GeoDataFrame,
    buildings_2023: gpd.GeoDataFrame,
) -> pd.DataFrame:
    left = buildings_2020[["GML ID", "Footprint Geometry"]].copy()
    left["Index 2020"] = np.arange(len(left))
    right = buildings_2023[["GML ID", "Footprint Geometry"]].copy()
    right["Index 2023"] = np.arange(len(right))

    joined = gpd.sjoin(
        left,
        right,
        how="inner",
        predicate="dwithin",
        distance=CANDIDATE_DISTANCE_METRES,
        lsuffix="2020",
        rsuffix="2023",
    ).reset_index(drop=True)
    joined = joined.rename(
        columns={"GML ID_2020": "2020 GML ID", "GML ID_2023": "2023 GML ID"}
    )

    index_2020 = joined["Index 2020"].to_numpy(dtype=int)
    index_2023 = joined["Index 2023"].to_numpy(dtype=int)
    geometry_2020 = buildings_2020.geometry.array.take(index_2020)
    geometry_2023 = buildings_2023.geometry.array.take(index_2023)
    area_2020 = shapely.area(geometry_2020)
    area_2023 = shapely.area(geometry_2023)
    intersection_area = shapely.area(shapely.intersection(geometry_2020, geometry_2023))
    union_area = area_2020 + area_2023 - intersection_area
    coverage_2020 = np.divide(
        intersection_area,
        area_2020,
        out=np.zeros_like(intersection_area),
        where=area_2020 > 0,
    )
    coverage_2023 = np.divide(
        intersection_area,
        area_2023,
        out=np.zeros_like(intersection_area),
        where=area_2023 > 0,
    )
    area_similarity = np.divide(
        np.minimum(area_2020, area_2023),
        np.maximum(area_2020, area_2023),
        out=np.zeros_like(area_2020),
        where=np.maximum(area_2020, area_2023) > 0,
    )
    centroid_distance = shapely.distance(
        shapely.centroid(geometry_2020), shapely.centroid(geometry_2023)
    )
    footprint_gap = shapely.distance(geometry_2020, geometry_2023)

    building_id_2020 = buildings_2020["Building ID"].iloc[index_2020].reset_index(
        drop=True
    )
    building_id_2023 = buildings_2023["Building ID"].iloc[index_2023].reset_index(
        drop=True
    )
    id_agreement = (
        building_id_2020.notna()
        & building_id_2023.notna()
        & building_id_2020.eq(building_id_2023)
    )
    iou = np.divide(
        intersection_area,
        union_area,
        out=np.zeros_like(intersection_area),
        where=union_area > 0,
    )
    pair_score = (
        0.50 * iou
        + 0.20 * np.minimum(coverage_2020, coverage_2023)
        + 0.15 * area_similarity
        + 0.15 * np.exp(-centroid_distance / 4.0)
        + 0.20 * id_agreement.astype(float)
    )
    replacement_score = (
        0.45 * np.maximum(coverage_2020, coverage_2023)
        + 0.25 * area_similarity
        + 0.30 * np.exp(-centroid_distance / 4.0)
    )

    joined["2020 Building ID"] = building_id_2020
    joined["2023 Building ID"] = building_id_2023
    joined["Building ID Agreement"] = id_agreement.to_numpy(dtype=bool)
    joined["2020 Footprint Area (m2)"] = area_2020
    joined["2023 Footprint Area (m2)"] = area_2023
    joined["Intersection Area (m2)"] = intersection_area
    joined["IoU"] = iou
    joined["2020 Coverage Ratio"] = coverage_2020
    joined["2023 Coverage Ratio"] = coverage_2023
    joined["Centroid Distance (m)"] = centroid_distance
    joined["Footprint Gap (m)"] = footprint_gap
    joined["Area Similarity"] = area_similarity
    joined["Pair Score"] = pair_score
    joined["Replacement Score"] = replacement_score
    joined["Candidate Rank for 2020"] = joined.groupby("Index 2020")[
        "Pair Score"
    ].rank(method="first", ascending=False).astype(int)
    joined["Candidate Rank for 2023"] = joined.groupby("Index 2023")[
        "Pair Score"
    ].rank(method="first", ascending=False).astype(int)
    joined["Mutual Best"] = (
        joined["Candidate Rank for 2020"].eq(1)
        & joined["Candidate Rank for 2023"].eq(1)
    )
    return joined.drop(columns=["Footprint Geometry", "index_2023"], errors="ignore")


def classify_pairs(pairs: pd.DataFrame) -> pd.DataFrame:
    pairs = pairs.copy()
    stable = pairs["Mutual Best"] & (
        (
            pairs["IoU"].ge(STABLE_IOU)
            & pairs["2020 Coverage Ratio"].ge(STABLE_MIN_COVERAGE)
            & pairs["2023 Coverage Ratio"].ge(STABLE_MIN_COVERAGE)
            & pairs["Centroid Distance (m)"].le(STABLE_MAX_CENTROID_DISTANCE)
        )
        | (
            pairs["Building ID Agreement"]
            & pairs["Footprint Gap (m)"].le(REBUILD_MAX_GAP)
            & pairs["Centroid Distance (m)"].le(REBUILD_MAX_CENTROID_DISTANCE)
        )
    )
    pairs["Pair Classification"] = "candidate_only"
    pairs.loc[stable, "Pair Classification"] = "retained"

    assigned_2020 = set(pairs.loc[stable, "Index 2020"].astype(int))
    assigned_2023 = set(pairs.loc[stable, "Index 2023"].astype(int))
    residual = pairs.loc[
        ~pairs["Index 2020"].isin(assigned_2020)
        & ~pairs["Index 2023"].isin(assigned_2023)
    ].copy()
    residual["Residual Rank for 2020"] = residual.groupby("Index 2020")[
        "Replacement Score"
    ].rank(method="first", ascending=False)
    residual["Residual Rank for 2023"] = residual.groupby("Index 2023")[
        "Replacement Score"
    ].rank(method="first", ascending=False)
    rebuild = (
        residual["Residual Rank for 2020"].eq(1)
        & residual["Residual Rank for 2023"].eq(1)
        & ~residual["Building ID Agreement"]
        & residual["Footprint Gap (m)"].le(REBUILD_MAX_GAP)
        & residual["Centroid Distance (m)"].le(REBUILD_MAX_CENTROID_DISTANCE)
        & residual["Area Similarity"].ge(REBUILD_MIN_AREA_SIMILARITY)
        & residual["Replacement Score"].ge(REBUILD_MIN_SCORE)
    )
    rebuild_indices = residual.index[rebuild]
    pairs.loc[rebuild_indices, "Pair Classification"] = "suspected_rebuild"
    return pairs


def prefixed_record(row: pd.Series, prefix: str) -> dict[str, object]:
    return {
        f"{prefix} GML ID": row["GML ID"],
        f"{prefix} Building ID": row["Building ID"],
        f"{prefix} Construction Year": row["Construction Year"],
        f"{prefix} Creation Date": row["Creation Date"],
        f"{prefix} Height (m)": row["Height (m)"],
        f"{prefix} Storeys Above Ground": row["Storeys Above Ground"],
        f"{prefix} Building Use Code": row["Building Use Code"],
        f"{prefix} Structure Type Code": row["Structure Type Code"],
        f"{prefix} Survey Year": row["Survey Year"],
        f"{prefix} Source Building Area (m2)": row["Source Building Area (m2)"],
        f"{prefix} Computed Footprint Area (m2)": row[
            "Computed Footprint Area (m2)"
        ],
    }


def build_panel(
    buildings_2020: gpd.GeoDataFrame,
    buildings_2023: gpd.GeoDataFrame,
    pairs: pd.DataFrame,
) -> gpd.GeoDataFrame:
    matched = pairs.loc[
        pairs["Pair Classification"].isin(["retained", "suspected_rebuild"])
    ].copy()
    assigned_2020 = set(matched["Index 2020"].astype(int))
    assigned_2023 = set(matched["Index 2023"].astype(int))
    residual = pairs.loc[
        ~pairs["Index 2020"].isin(assigned_2020)
        & ~pairs["Index 2023"].isin(assigned_2023)
    ].copy()
    meaningful_mask = (
        pairs["Footprint Gap (m)"].le(REBUILD_MAX_GAP)
        | pairs["2020 Coverage Ratio"].ge(0.10)
        | pairs["2023 Coverage Ratio"].ge(0.10)
        | pairs["Centroid Distance (m)"].le(6.0)
    )
    all_meaningful = pairs.loc[meaningful_mask]
    meaningful = residual.loc[
        residual.index.intersection(all_meaningful.index)
    ]
    counts_2020 = all_meaningful.groupby("Index 2020").size()
    counts_2023 = all_meaningful.groupby("Index 2023").size()
    candidates_2020 = meaningful.groupby("Index 2020")["2023 GML ID"].agg(
        lambda values: "|".join(sorted(set(values.dropna().astype(str))))
    )
    candidates_2023 = meaningful.groupby("Index 2023")["2020 GML ID"].agg(
        lambda values: "|".join(sorted(set(values.dropna().astype(str))))
    )

    records: list[dict[str, object]] = []
    geometries: list[object] = []
    metric_columns = [
        "Intersection Area (m2)",
        "IoU",
        "2020 Coverage Ratio",
        "2023 Coverage Ratio",
        "Centroid Distance (m)",
        "Footprint Gap (m)",
        "Area Similarity",
        "Pair Score",
        "Replacement Score",
        "Building ID Agreement",
    ]
    for sequence, (_, pair_series) in enumerate(
        matched.sort_values(["Pair Classification", "Index 2020"]).iterrows(),
        start=1,
    ):
        row_2020 = buildings_2020.iloc[int(pair_series["Index 2020"])]
        row_2023 = buildings_2023.iloc[int(pair_series["Index 2023"])]
        record: dict[str, object] = {
            "Panel ID": f"PAIR-{sequence:06d}",
            "Match Status": pair_series["Pair Classification"],
            "Record Side": "paired",
            "2020 Meaningful Candidate Count": int(
                counts_2020.get(int(pair_series["Index 2020"]), 0)
            ),
            "2023 Meaningful Candidate Count": int(
                counts_2023.get(int(pair_series["Index 2023"]), 0)
            ),
            "Candidate GML IDs": pd.NA,
        }
        record.update(prefixed_record(row_2020, "2020"))
        record.update(prefixed_record(row_2023, "2023"))
        record.update({column: pair_series[column] for column in metric_columns})
        records.append(record)
        geometries.append(
            shapely.union(row_2020["Footprint Geometry"], row_2023["Footprint Geometry"])
        )

    sequence = len(records)
    for index, row in buildings_2020.iterrows():
        if index in assigned_2020:
            continue
        candidate_ids = candidates_2020.get(index, "")
        sequence += 1
        record = {
            "Panel ID": f"Y2020-{sequence:06d}",
            "Match Status": "ambiguous" if candidate_ids else "disappeared",
            "Record Side": "2020_only",
            "2020 Meaningful Candidate Count": int(counts_2020.get(index, 0)),
            "2023 Meaningful Candidate Count": pd.NA,
            "Candidate GML IDs": candidate_ids or pd.NA,
        }
        record.update(prefixed_record(row, "2020"))
        records.append(record)
        geometries.append(row["Footprint Geometry"])

    for index, row in buildings_2023.iterrows():
        if index in assigned_2023:
            continue
        candidate_ids = candidates_2023.get(index, "")
        sequence += 1
        record = {
            "Panel ID": f"Y2023-{sequence:06d}",
            "Match Status": "ambiguous" if candidate_ids else "new",
            "Record Side": "2023_only",
            "2020 Meaningful Candidate Count": pd.NA,
            "2023 Meaningful Candidate Count": int(counts_2023.get(index, 0)),
            "Candidate GML IDs": candidate_ids or pd.NA,
        }
        record.update(prefixed_record(row, "2023"))
        records.append(record)
        geometries.append(row["Footprint Geometry"])

    return gpd.GeoDataFrame(
        records,
        geometry=gpd.GeoSeries(geometries, crs=buildings_2020.crs),
        crs=buildings_2020.crs,
    ).rename_geometry("Panel Geometry")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=project_root())
    arguments = parser.parse_args()
    root = arguments.root.resolve()
    gml_directories = {
        2020: root / "data/raw/plateau/mashiki/2020/citygml/aoi_source/udx/bldg",
        2023: root / "data/raw/plateau/mashiki/2023/citygml/aoi_source/udx/bldg",
    }
    processed_directory = root / "data/processed"
    audit_directory = root / "data/exp/building-panel/mashiki"
    processed_directory.mkdir(parents=True, exist_ok=True)
    audit_directory.mkdir(parents=True, exist_ok=True)

    buildings = {
        year: standardize_buildings(load_buildings(directory), year)
        for year, directory in gml_directories.items()
    }
    for year, frame in buildings.items():
        output = processed_directory / f"mashiki_plateau_{year}_buildings_preprocessed.parquet"
        frame.to_parquet(output, index=False)
        print(f"saved {output}: {len(frame):,} rows")

    pairs = classify_pairs(candidate_pairs(buildings[2020], buildings[2023]))
    pairs_output = (
        processed_directory
        / "mashiki_plateau_2020_2023_match_candidates_preprocessed.parquet"
    )
    pairs.to_parquet(pairs_output, index=False)
    print(f"saved {pairs_output}: {len(pairs):,} rows")

    panel = build_panel(buildings[2020], buildings[2023], pairs)
    panel_output = (
        processed_directory
        / "mashiki_plateau_2020_2023_building_panel_preprocessed.parquet"
    )
    panel.to_parquet(panel_output, index=False)
    print(f"saved {panel_output}: {len(panel):,} rows")

    metadata = {
        "source_building_counts": {str(year): len(frame) for year, frame in buildings.items()},
        "candidate_pair_count": len(pairs),
        "pair_classification_counts": {
            str(key): int(value)
            for key, value in pairs["Pair Classification"].value_counts().items()
        },
        "panel_status_counts": {
            str(key): int(value)
            for key, value in panel["Match Status"].value_counts().items()
        },
        "thresholds": {
            "candidate_distance_metres": CANDIDATE_DISTANCE_METRES,
            "stable_iou": STABLE_IOU,
            "stable_min_coverage": STABLE_MIN_COVERAGE,
            "stable_max_centroid_distance": STABLE_MAX_CENTROID_DISTANCE,
            "rebuild_max_gap": REBUILD_MAX_GAP,
            "rebuild_max_centroid_distance": REBUILD_MAX_CENTROID_DISTANCE,
            "rebuild_min_area_similarity": REBUILD_MIN_AREA_SIMILARITY,
            "rebuild_min_score": REBUILD_MIN_SCORE,
        },
        "interpretation": {
            "retained": "Conservative geometry or source-ID continuity; not proof of unchanged use.",
            "suspected_rebuild": "Candidate footprint replacement only; requires imagery or administrative validation.",
            "disappeared": "FY2020 footprint without a meaningful FY2023 candidate.",
            "new": "FY2023 footprint without a meaningful FY2020 candidate.",
            "ambiguous": "Residual split, merge, adjacency, or weak candidate relationship.",
        },
    }
    metadata_path = audit_directory / "run_metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
