#!/usr/bin/env python3
"""Audit full-panel reconstruction calibration outputs and write a concise report."""

from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
EXP = ROOT / "data/exp/reconstruction-calibration/mashiki"
PANEL_PATH = (
    ROOT / "data/processed/mashiki_plateau_2020_2023_building_panel_preprocessed.parquet"
)
OUTPUT_PATH = (
    ROOT / "data/processed/mashiki_reconstruction_probability_calibrated_preprocessed.parquet"
)
DEFINITIONS = [
    "Conservative Recovery",
    "Inclusive Visible Replacement",
    "Shock Linked Recovery",
]


def main() -> None:
    source = gpd.read_parquet(PANEL_PATH)
    output = gpd.read_parquet(OUTPUT_PATH)
    calibration = pd.read_csv(EXP / "status_posterior_calibration.csv")
    aggregate = pd.read_csv(EXP / "population_poststratified_summary.csv")
    thresholds = pd.read_csv(EXP / "probability_threshold_sensitivity.csv")
    error = pd.read_csv(EXP / "measurement_error_sensitivity.csv")
    diagnostics = pd.read_csv(EXP / "individual_model_cross_validation.csv")

    checks: dict[str, bool] = {
        "source_has_9039_rows": len(source) == 9_039,
        "output_has_9039_rows": len(output) == 9_039,
        "panel_ids_preserved": source["Panel ID"].equals(output["Panel ID"]),
        "panel_ids_unique": output["Panel ID"].is_unique,
        "geometry_preserved": source.geometry.equals(output.geometry),
        "geometry_valid": output.geometry.is_valid.all() and (~output.geometry.is_empty).all(),
        "calibration_has_15_status_rows": len(calibration) == 15,
        "aggregate_has_6_rows": len(aggregate) == 6,
        "threshold_table_has_18_rows": len(thresholds) == 18,
        "measurement_error_table_has_126_rows": len(error) == 126,
        "diagnostics_have_3_rows": len(diagnostics) == 3,
        "sampling_domain_count_is_4582": int(
            output["Calibration Domain"].eq("in_sampling_domain").sum()
        )
        == 4_582,
        "outside_domain_count_is_4457": int(
            output["Calibration Domain"].eq("outside_image_or_size_domain").sum()
        )
        == 4_457,
        "all_individual_models_fail_gate": not diagnostics[
            "individualized_model_gate_passed"
        ].any(),
        "no_record_is_individually_eligible": not output[
            "Individual Probability Use Eligible"
        ].any(),
    }
    for definition in DEFINITIONS:
        mean = output[f"{definition} Status-Calibrated Probability"]
        lower = output[f"{definition} Probability 95% Low"]
        upper = output[f"{definition} Probability 95% High"]
        diagnostic = output[f"{definition} Individual Diagnostic Probability"]
        checks[f"{definition}_probabilities_bounded"] = bool(
            mean.between(0, 1).all()
            and lower.between(0, 1).all()
            and upper.between(0, 1).all()
            and diagnostic.between(0, 1).all()
        )
        checks[f"{definition}_intervals_ordered"] = bool(
            (lower <= mean).all() and (mean <= upper).all()
        )
        checks[f"{definition}_status_constant"] = bool(
            output.groupby("Match Status")[mean.name].nunique().eq(1).all()
        )
    checks = {key: bool(value) for key, value in checks.items()}
    result = {"all_passed": all(checks.values()), "checks": checks}
    (EXP / "audit_integrity.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )

    full = aggregate.loc[aggregate["scope"].eq("full_panel")].copy()
    full["expected_positive_count"] = full["expected_positive_count"].round(0).astype(int)
    full["expected_positive_count_95_low"] = (
        full["expected_positive_count_95_low"].round(0).astype(int)
    )
    full["expected_positive_count_95_high"] = (
        full["expected_positive_count_95_high"].round(0).astype(int)
    )
    full["expected_positive_share"] = (full["expected_positive_share"] * 100).round(1)
    full["expected_positive_share_95_low"] = (
        full["expected_positive_share_95_low"] * 100
    ).round(1)
    full["expected_positive_share_95_high"] = (
        full["expected_positive_share_95_high"] * 100
    ).round(1)
    diagnostic_report = diagnostics[
        [
            "definition",
            "n",
            "positive",
            "roc_auc",
            "roc_auc_95_low",
            "roc_auc_95_high",
            "brier_score",
            "constant_prevalence_brier",
            "individualized_model_gate_passed",
        ]
    ].copy()
    numeric = diagnostic_report.select_dtypes(include="number").columns
    diagnostic_report[numeric] = diagnostic_report[numeric].round(3)
    report = f"""# Mashiki reconstruction probability calibration audit

## Outcome

All integrity checks passed: `{result['all_passed']}`.

The requested 9,039-record output is complete, but none of the individualized models passed the predeclared use gate. Consequently, zero records are eligible for individualized probability interpretation. The defensible outputs are status-stratified posterior probabilities, their wide uncertainty intervals, and scenario sensitivity results.

## Coverage

- Full panel: 9,039 records.
- In the original image/size sampling domain: 4,582 records.
- Outside that domain: 4,457 records; these retain status-level calibration but are explicit extrapolations.

## Population-weighted sensitivity across outcome definitions

{full.to_markdown(index=False)}

## Spatially grouped cross-validation

{diagnostic_report.to_markdown(index=False)}

## Interpretation

- The conservative definition implies an expected 4,461 positive signals, but its 95% interval spans 2,639-6,269. This is too wide for a credible reconstruction count.
- Changing only the label definition moves the expected share from 18.7% (shock-linked) to 75.8% (inclusive), demonstrating dominant outcome-definition uncertainty.
- Geometry and inventory variables do not predict the visual labels out of sample: all ROC AUC estimates are near 0.5, and all Brier scores are worse than the constant-prevalence benchmark.
- The current data can support measurement-error bounds and status-level descriptive calibration. They cannot support building-level ranking, causal reconstruction estimates, or a Nature Cities-level central outcome without official external records or a larger independent validation sample.

## Files

- Full scored panel: `data/processed/mashiki_reconstruction_probability_calibrated_preprocessed.parquet`
- Status posterior calibration: `data/exp/reconstruction-calibration/mashiki/status_posterior_calibration.csv`
- Population summary: `data/exp/reconstruction-calibration/mashiki/population_poststratified_summary.csv`
- Threshold sensitivity: `data/exp/reconstruction-calibration/mashiki/probability_threshold_sensitivity.csv`
- Measurement-error sensitivity: `data/exp/reconstruction-calibration/mashiki/measurement_error_sensitivity.csv`
- Cross-validation diagnostics: `data/exp/reconstruction-calibration/mashiki/individual_model_cross_validation.csv`
"""
    (EXP / "audit.md").write_text(report, encoding="utf-8")
    print(json.dumps(result, indent=2))
    print(report)
    if not result["all_passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
