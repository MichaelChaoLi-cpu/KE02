#!/usr/bin/env python3
"""Audit integrity and threshold sensitivity of the Mashiki PLATEAU panel."""

from __future__ import annotations

import argparse
from pathlib import Path

import geopandas as gpd
import pandas as pd


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def classify_counts(
    pairs: pd.DataFrame,
    *,
    stable_iou: float,
    stable_coverage: float,
    stable_distance: float,
    rebuild_gap: float,
    rebuild_distance: float,
    rebuild_area_similarity: float,
    rebuild_score: float,
) -> dict[str, int]:
    stable = pairs["Mutual Best"] & (
        (
            pairs["IoU"].ge(stable_iou)
            & pairs["2020 Coverage Ratio"].ge(stable_coverage)
            & pairs["2023 Coverage Ratio"].ge(stable_coverage)
            & pairs["Centroid Distance (m)"].le(stable_distance)
        )
        | (
            pairs["Building ID Agreement"]
            & pairs["Footprint Gap (m)"].le(rebuild_gap)
            & pairs["Centroid Distance (m)"].le(rebuild_distance)
        )
    )
    assigned_2020 = set(pairs.loc[stable, "Index 2020"])
    assigned_2023 = set(pairs.loc[stable, "Index 2023"])
    residual = pairs.loc[
        ~pairs["Index 2020"].isin(assigned_2020)
        & ~pairs["Index 2023"].isin(assigned_2023)
    ].copy()
    residual["Rank 2020"] = residual.groupby("Index 2020")["Replacement Score"].rank(
        method="first", ascending=False
    )
    residual["Rank 2023"] = residual.groupby("Index 2023")["Replacement Score"].rank(
        method="first", ascending=False
    )
    rebuild = (
        residual["Rank 2020"].eq(1)
        & residual["Rank 2023"].eq(1)
        & ~residual["Building ID Agreement"]
        & residual["Footprint Gap (m)"].le(rebuild_gap)
        & residual["Centroid Distance (m)"].le(rebuild_distance)
        & residual["Area Similarity"].ge(rebuild_area_similarity)
        & residual["Replacement Score"].ge(rebuild_score)
    )
    return {"retained_pairs": int(stable.sum()), "suspected_rebuild_pairs": int(rebuild.sum())}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=project_root())
    arguments = parser.parse_args()
    root = arguments.root.resolve()
    processed = root / "data/processed"
    audit = root / "data/exp/building-panel/mashiki"
    audit.mkdir(parents=True, exist_ok=True)

    buildings_2020 = gpd.read_parquet(
        processed / "mashiki_plateau_2020_buildings_preprocessed.parquet"
    )
    buildings_2023 = gpd.read_parquet(
        processed / "mashiki_plateau_2023_buildings_preprocessed.parquet"
    )
    pairs = pd.read_parquet(
        processed / "mashiki_plateau_2020_2023_match_candidates_preprocessed.parquet"
    )
    panel = gpd.read_parquet(
        processed / "mashiki_plateau_2020_2023_building_panel_preprocessed.parquet"
    )

    assertions = {
        "2020_gml_id_unique": buildings_2020["GML ID"].is_unique,
        "2023_gml_id_unique": buildings_2023["GML ID"].is_unique,
        "candidate_pairs_unique": ~pairs.duplicated(["Index 2020", "Index 2023"]).any(),
        "panel_id_unique": panel["Panel ID"].is_unique,
        "panel_geometry_valid": panel.geometry.is_valid.all(),
        "panel_geometry_nonempty": (~panel.geometry.is_empty).all(),
        "2020_represented_once": (
            panel["2020 GML ID"].dropna().nunique() == len(buildings_2020)
            and panel["2020 GML ID"].notna().sum() == len(buildings_2020)
        ),
        "2023_represented_once": (
            panel["2023 GML ID"].dropna().nunique() == len(buildings_2023)
            and panel["2023 GML ID"].notna().sum() == len(buildings_2023)
        ),
    }
    if not all(assertions.values()):
        failures = [name for name, passed in assertions.items() if not passed]
        raise AssertionError(f"panel audit failed: {failures}")

    missingness_records = []
    fields = [
        "Building ID",
        "Construction Year",
        "Creation Date",
        "Height (m)",
        "Storeys Above Ground",
        "Building Use Code",
        "Structure Type Code",
        "Survey Year",
        "Source Building Area (m2)",
        "Computed Footprint Area (m2)",
    ]
    for year, frame in ((2020, buildings_2020), (2023, buildings_2023)):
        for field in fields:
            missingness_records.append(
                {
                    "PLATEAU Release Year": year,
                    "Variable": field,
                    "Rows": len(frame),
                    "Missing Count": int(frame[field].isna().sum()),
                    "Missing Percent": float(frame[field].isna().mean() * 100),
                }
            )
    missingness = pd.DataFrame(missingness_records)
    missingness.to_csv(audit / "variable_missingness.csv", index=False)

    metric_fields = [
        "IoU",
        "2020 Coverage Ratio",
        "2023 Coverage Ratio",
        "Centroid Distance (m)",
        "Footprint Gap (m)",
        "Area Similarity",
        "Pair Score",
        "Replacement Score",
    ]
    selected_pairs = pairs.loc[
        pairs["Pair Classification"].isin(["retained", "suspected_rebuild"])
    ]
    metric_summary = (
        selected_pairs.groupby("Pair Classification")[metric_fields]
        .quantile([0.05, 0.25, 0.50, 0.75, 0.95])
        .rename_axis(index=["Pair Classification", "Quantile"])
        .reset_index()
    )
    metric_summary.to_csv(audit / "matched_pair_metric_quantiles.csv", index=False)

    scenarios = {
        "strict": dict(
            stable_iou=0.70,
            stable_coverage=0.80,
            stable_distance=5.0,
            rebuild_gap=1.0,
            rebuild_distance=6.0,
            rebuild_area_similarity=0.60,
            rebuild_score=0.65,
        ),
        "baseline": dict(
            stable_iou=0.60,
            stable_coverage=0.75,
            stable_distance=6.0,
            rebuild_gap=2.0,
            rebuild_distance=8.0,
            rebuild_area_similarity=0.50,
            rebuild_score=0.55,
        ),
        "relaxed": dict(
            stable_iou=0.50,
            stable_coverage=0.65,
            stable_distance=8.0,
            rebuild_gap=3.0,
            rebuild_distance=10.0,
            rebuild_area_similarity=0.40,
            rebuild_score=0.45,
        ),
    }
    sensitivity_records = []
    for scenario, thresholds in scenarios.items():
        counts = classify_counts(pairs, **thresholds)
        sensitivity_records.append({"Scenario": scenario, **thresholds, **counts})
    sensitivity = pd.DataFrame(sensitivity_records)
    sensitivity.to_csv(audit / "threshold_sensitivity.csv", index=False)

    status_counts = panel["Match Status"].value_counts().sort_index()
    audit_lines = [
        "# Mashiki PLATEAU FY2020-FY2023 Building Panel Audit",
        "",
        "## Integrity",
        "",
        *[f"- {name}: {'PASS' if passed else 'FAIL'}" for name, passed in assertions.items()],
        "",
        "## Panel counts",
        "",
        f"- FY2020 source buildings: {len(buildings_2020):,}",
        f"- FY2023 source buildings: {len(buildings_2023):,}",
        f"- Candidate pairs within 12 m: {len(pairs):,}",
        f"- Panel records: {len(panel):,}",
        *[f"- {status}: {count:,}" for status, count in status_counts.items()],
        "",
        "## Threshold sensitivity",
        "",
        sensitivity.to_markdown(index=False),
        "",
        "## Interpretation gate",
        "",
        "- `suspected_rebuild` is a footprint-replacement candidate, not a validated reconstruction event.",
        "- PLATEAU version-to-version geometry revisions can mimic physical building change.",
        "- Use 2020/2023 orthophotos, construction records, or the requested AIJ data before treating this class as an outcome.",
        "- `disappeared` and `new` remain conservative unmatched-footprint states, not causal earthquake labels.",
        "",
    ]
    (audit / "audit.md").write_text("\n".join(audit_lines), encoding="utf-8")
    print("\n".join(audit_lines))


if __name__ == "__main__":
    main()
