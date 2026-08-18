#!/usr/bin/env python3
"""Calibrate uncertainty-aware reconstruction signals for the full Mashiki panel."""

from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from scipy.stats import beta
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    balanced_accuracy_score,
    brier_score_loss,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


ROOT = Path(__file__).resolve().parents[2]
PANEL_PATH = (
    ROOT / "data/processed/mashiki_plateau_2020_2023_building_panel_preprocessed.parquet"
)
VALIDATION_PATH = (
    ROOT / "data/processed/mashiki_reconstruction_validation_final_preprocessed.parquet"
)
OUTPUT_PATH = (
    ROOT / "data/processed/mashiki_reconstruction_probability_calibrated_preprocessed.parquet"
)
EXP = ROOT / "data/exp/reconstruction-calibration/mashiki"
SEED = 20260818
BOOTSTRAP_DRAWS = 20_000
STATUS_ORDER = ["retained", "suspected_rebuild", "disappeared", "new", "ambiguous"]
CATEGORICAL_FEATURES = ["Match Status", "Record Side"]
NUMERIC_FEATURES = [
    "Replacement Score",
    "IoU",
    "Area Similarity",
    "Centroid Distance (m)",
    "2020 Computed Footprint Area (m2)",
    "2023 Computed Footprint Area (m2)",
    "2020 Height (m)",
    "2023 Height (m)",
]
RASTERS = [
    ROOT
    / "data/raw/gsi/orthophoto_z18/mashiki/2016-04-15_post_foreshock/mashiki_2016-04-15_post_foreshock.tif",
    ROOT
    / "data/raw/gsi/orthophoto_z18/mashiki/combined/mashiki_2016-04-16_post_mainshock_combined.tif",
    ROOT
    / "data/raw/plateau/mashiki/2020/orthophoto/aoi/mashiki_plateau_2020_reconstruction_validation_epsg3857.tif",
    ROOT
    / "data/raw/plateau/mashiki/2023/orthophoto/aoi/mashiki_plateau_fy2023_pre_2026_baseline_epsg3857.tif",
]


def outcome_frames(validation: gpd.GeoDataFrame) -> dict[str, tuple[gpd.GeoDataFrame, pd.Series]]:
    inventory = validation.loc[validation["Final Inventory Validation Eligible"]].copy()
    pair2 = inventory["Final Pair 2 Ordered Transition"]
    conservative = pair2.map(
        {
            "absent_to_present": 1,
            "absent_to_absent": 0,
            "present_to_absent": 0,
            "stable_present_to_present": 0,
        }
    )
    inclusive = pair2.map(
        {
            "absent_to_present": 1,
            "changed_present_to_present": 1,
            "absent_to_absent": 0,
            "present_to_absent": 0,
            "stable_present_to_present": 0,
        }
    )
    longitudinal = validation.loc[
        validation["Final Longitudinal Validation Eligible"]
    ].copy()
    shock_linked = (
        longitudinal["Final Pair 1 Ordered Transition"].eq("present_to_absent")
        & longitudinal["Final Pair 2 Ordered Transition"].eq("absent_to_present")
    ).astype(int)
    return {
        "conservative_recovery": (inventory.loc[conservative.notna()].copy(), conservative.dropna().astype(int)),
        "inclusive_visible_replacement": (inventory.loc[inclusive.notna()].copy(), inclusive.dropna().astype(int)),
        "shock_linked_recovery": (longitudinal, shock_linked),
    }


def sampling_domain(panel: gpd.GeoDataFrame) -> pd.Series:
    opened = [rasterio.open(path) for path in RASTERS]
    try:
        west = max(source.bounds.left for source in opened)
        south = max(source.bounds.bottom for source in opened)
        east = min(source.bounds.right for source in opened)
        north = min(source.bounds.top for source in opened)
    finally:
        for source in opened:
            source.close()
    geometry = panel.geometry
    centroids = geometry.centroid
    bounds = geometry.bounds
    margin = 37.0
    return (
        geometry.area.between(30.0, 800.0)
        & (bounds.maxx - bounds.minx).le(60.0)
        & (bounds.maxy - bounds.miny).le(60.0)
        & centroids.x.between(west + margin, east - margin)
        & centroids.y.between(south + margin, north - margin)
    )


def logistic_pipeline() -> Pipeline:
    transformer = ColumnTransformer(
        [
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore"),
                CATEGORICAL_FEATURES,
            ),
            (
                "numeric",
                Pipeline(
                    [
                        (
                            "impute",
                            SimpleImputer(strategy="median", add_indicator=True),
                        ),
                        ("scale", StandardScaler()),
                    ]
                ),
                NUMERIC_FEATURES,
            ),
        ]
    )
    return Pipeline(
        [
            ("transform", transformer),
            ("model", LogisticRegression(C=0.2, max_iter=5_000)),
        ]
    )


def auc_interval(y: pd.Series, prediction: np.ndarray, rng: np.random.Generator) -> tuple[float, float]:
    values: list[float] = []
    y_array = y.to_numpy()
    for _ in range(2_000):
        indices = rng.integers(0, len(y_array), len(y_array))
        if len(np.unique(y_array[indices])) != 2:
            continue
        values.append(roc_auc_score(y_array[indices], prediction[indices]))
    return float(np.quantile(values, 0.025)), float(np.quantile(values, 0.975))


def diagnostic_model(
    name: str,
    frame: gpd.GeoDataFrame,
    target: pd.Series,
    panel: gpd.GeoDataFrame,
    rng: np.random.Generator,
) -> tuple[dict[str, object], np.ndarray]:
    target = target.loc[frame.index].astype(int)
    folds = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=SEED)
    prediction = np.zeros(len(frame), dtype=float)
    for train, test in folds.split(frame, target, groups=frame["Spatial Grid"]):
        model = logistic_pipeline()
        model.fit(frame.iloc[train], target.iloc[train])
        prediction[test] = model.predict_proba(frame.iloc[test])[:, 1]
    prevalence = float(target.mean())
    auc = float(roc_auc_score(target, prediction))
    auc_low, auc_high = auc_interval(target, prediction, rng)
    brier = float(brier_score_loss(target, prediction))
    base_brier = float(brier_score_loss(target, np.repeat(prevalence, len(target))))
    gate_passed = auc >= 0.70 and brier <= base_brier - 0.02
    fitted = logistic_pipeline()
    fitted.fit(frame, target)
    full_prediction = fitted.predict_proba(panel)[:, 1]
    metrics: dict[str, object] = {
        "definition": name,
        "n": int(len(target)),
        "positive": int(target.sum()),
        "negative": int((1 - target).sum()),
        "prevalence": prevalence,
        "roc_auc": auc,
        "roc_auc_95_low": auc_low,
        "roc_auc_95_high": auc_high,
        "average_precision": float(average_precision_score(target, prediction)),
        "brier_score": brier,
        "constant_prevalence_brier": base_brier,
        "balanced_accuracy_at_0_5": float(
            balanced_accuracy_score(target, prediction >= 0.5)
        ),
        "individualized_model_gate_passed": bool(gate_passed),
    }
    return metrics, full_prediction


def main() -> None:
    EXP.mkdir(parents=True, exist_ok=True)
    panel = gpd.read_parquet(PANEL_PATH)
    validation = gpd.read_parquet(VALIDATION_PATH)
    if len(panel) != 9_039 or len(validation) != 100:
        raise RuntimeError("unexpected panel or validation row count")
    if not panel["Panel ID"].is_unique:
        raise RuntimeError("Panel ID is not unique")
    panel["Calibration Domain"] = np.where(
        sampling_domain(panel),
        "in_sampling_domain",
        "outside_image_or_size_domain",
    )
    outcomes = outcome_frames(validation)
    rng = np.random.default_rng(SEED)
    calibration_rows: list[dict[str, object]] = []
    aggregate_rows: list[dict[str, object]] = []
    threshold_rows: list[dict[str, object]] = []
    measurement_error_rows: list[dict[str, object]] = []
    diagnostic_rows: list[dict[str, object]] = []

    full_status_counts = panel["Match Status"].value_counts().reindex(STATUS_ORDER)
    domain_status_counts = (
        panel.loc[panel["Calibration Domain"].eq("in_sampling_domain"), "Match Status"]
        .value_counts()
        .reindex(STATUS_ORDER)
        .fillna(0)
        .astype(int)
    )

    for name, (frame, target) in outcomes.items():
        if not frame.index.equals(target.index):
            target = target.reindex(frame.index)
        posterior_draws: dict[str, np.ndarray] = {}
        status_means: dict[str, float] = {}
        status_lowers: dict[str, float] = {}
        status_uppers: dict[str, float] = {}
        for status in STATUS_ORDER:
            selected = target.loc[frame["Source Match Status"].eq(status)]
            positive = int(selected.sum())
            total = int(len(selected))
            if total == 0:
                raise RuntimeError(f"no calibration observations for {name}/{status}")
            alpha = positive + 0.5
            beta_parameter = total - positive + 0.5
            mean = alpha / (alpha + beta_parameter)
            lower, upper = beta.ppf([0.025, 0.975], alpha, beta_parameter)
            posterior_draws[status] = rng.beta(alpha, beta_parameter, BOOTSTRAP_DRAWS)
            status_means[status] = float(mean)
            status_lowers[status] = float(lower)
            status_uppers[status] = float(upper)
            calibration_rows.append(
                {
                    "definition": name,
                    "source_match_status": status,
                    "n": total,
                    "positive": positive,
                    "negative": total - positive,
                    "posterior_mean": mean,
                    "posterior_95_low": lower,
                    "posterior_95_high": upper,
                }
            )
        prefix = name.replace("_", " ").title()
        panel[f"{prefix} Status-Calibrated Probability"] = panel["Match Status"].map(status_means)
        panel[f"{prefix} Probability 95% Low"] = panel["Match Status"].map(status_lowers)
        panel[f"{prefix} Probability 95% High"] = panel["Match Status"].map(status_uppers)

        for scope, counts in (
            ("full_panel", full_status_counts),
            ("in_sampling_domain", domain_status_counts),
        ):
            total_count = int(counts.sum())
            expected_draws = sum(
                counts[status] * posterior_draws[status] for status in STATUS_ORDER
            )
            expected_mean = sum(
                counts[status] * status_means[status] for status in STATUS_ORDER
            )
            aggregate_rows.append(
                {
                    "definition": name,
                    "scope": scope,
                    "panel_records": total_count,
                    "expected_positive_count": expected_mean,
                    "expected_positive_count_95_low": np.quantile(expected_draws, 0.025),
                    "expected_positive_count_95_high": np.quantile(expected_draws, 0.975),
                    "expected_positive_share": expected_mean / total_count,
                    "expected_positive_share_95_low": np.quantile(expected_draws, 0.025) / total_count,
                    "expected_positive_share_95_high": np.quantile(expected_draws, 0.975) / total_count,
                }
            )
            for threshold in (0.25, 0.50, 0.75):
                selected_count = sum(
                    int(counts[status])
                    for status in STATUS_ORDER
                    if status_means[status] >= threshold
                )
                threshold_rows.append(
                    {
                        "definition": name,
                        "scope": scope,
                        "threshold": threshold,
                        "records_at_or_above_threshold": selected_count,
                        "share_at_or_above_threshold": selected_count / total_count,
                    }
                )

        error_scenarios = {
            "no_correction": (0.00, 0.00),
            "symmetric_5pct": (0.05, 0.05),
            "symmetric_10pct": (0.10, 0.10),
            "symmetric_20pct": (0.20, 0.20),
            "false_negative_20_false_positive_10": (0.10, 0.20),
            "false_negative_10_false_positive_20": (0.20, 0.10),
        }
        for scenario, (false_positive_rate, false_negative_rate) in error_scenarios.items():
            denominator = 1.0 - false_positive_rate - false_negative_rate
            corrected = {
                status: float(
                    np.clip(
                        (status_means[status] - false_positive_rate) / denominator,
                        0.0,
                        1.0,
                    )
                )
                for status in STATUS_ORDER
            }
            for status in STATUS_ORDER:
                measurement_error_rows.append(
                    {
                        "definition": name,
                        "scope": "status",
                        "source_match_status": status,
                        "scenario": scenario,
                        "false_positive_rate": false_positive_rate,
                        "false_negative_rate": false_negative_rate,
                        "corrected_probability": corrected[status],
                        "panel_records": int(full_status_counts[status]),
                        "corrected_expected_positive_count": corrected[status]
                        * int(full_status_counts[status]),
                    }
                )
            for scope, counts in (
                ("full_panel", full_status_counts),
                ("in_sampling_domain", domain_status_counts),
            ):
                total_count = int(counts.sum())
                expected = sum(
                    int(counts[status]) * corrected[status] for status in STATUS_ORDER
                )
                measurement_error_rows.append(
                    {
                        "definition": name,
                        "scope": scope,
                        "source_match_status": "All",
                        "scenario": scenario,
                        "false_positive_rate": false_positive_rate,
                        "false_negative_rate": false_negative_rate,
                        "corrected_probability": expected / total_count,
                        "panel_records": total_count,
                        "corrected_expected_positive_count": expected,
                    }
                )

        metrics, full_prediction = diagnostic_model(name, frame, target, panel, rng)
        diagnostic_rows.append(metrics)
        panel[f"{prefix} Individual Diagnostic Probability"] = full_prediction
        panel[f"{prefix} Individual Model Gate Passed"] = bool(
            metrics["individualized_model_gate_passed"]
        )

    calibration = pd.DataFrame(calibration_rows)
    aggregate = pd.DataFrame(aggregate_rows)
    thresholds = pd.DataFrame(threshold_rows)
    measurement_error = pd.DataFrame(measurement_error_rows)
    diagnostics = pd.DataFrame(diagnostic_rows)
    panel["Individual Probability Use Eligible"] = (
        panel["Calibration Domain"].eq("in_sampling_domain")
        & all(diagnostics["individualized_model_gate_passed"])
    )
    panel.to_parquet(OUTPUT_PATH, index=False)
    calibration.to_csv(EXP / "status_posterior_calibration.csv", index=False)
    aggregate.to_csv(EXP / "population_poststratified_summary.csv", index=False)
    thresholds.to_csv(EXP / "probability_threshold_sensitivity.csv", index=False)
    measurement_error.to_csv(EXP / "measurement_error_sensitivity.csv", index=False)
    diagnostics.to_csv(EXP / "individual_model_cross_validation.csv", index=False)

    summary = {
        "seed": SEED,
        "panel_records": len(panel),
        "in_sampling_domain": int(panel["Calibration Domain"].eq("in_sampling_domain").sum()),
        "outside_sampling_domain": int(panel["Calibration Domain"].ne("in_sampling_domain").sum()),
        "definitions": {
            row["definition"]: {
                "n": int(row["n"]),
                "positive": int(row["positive"]),
                "roc_auc": float(row["roc_auc"]),
                "brier_score": float(row["brier_score"]),
                "individualized_model_gate_passed": bool(
                    row["individualized_model_gate_passed"]
                ),
            }
            for _, row in diagnostics.iterrows()
        },
        "individual_probability_use_eligible_records": int(
            panel["Individual Probability Use Eligible"].sum()
        ),
        "primary_estimator": "Jeffreys-Beta posterior within Source Match Status",
        "primary_definition": "conservative_recovery",
    }
    (EXP / "run_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))
    print("\nPopulation post-stratified summary")
    print(aggregate.to_string(index=False))
    print("\nIndividual model cross-validation")
    print(diagnostics.to_string(index=False))


if __name__ == "__main__":
    main()
