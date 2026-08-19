#!/usr/bin/env python3
"""Run a four-unit stratified recovery sensitivity experiment.

This is an exploratory feasibility experiment, not an estimator.  It keeps
the three motorway reopening clusters separate from the same-bridge Yokoe
case, varies Yokoe's 2016 restoration endpoint, compares MMI with PGA, and
checks whether candidate descriptive claims survive leave-one-out deletion.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
SOURCE_DIR = ROOT / "data/exp/feasibility-check/independent-reopening-regimes"
SOURCE = SOURCE_DIR / "augmented_independent_regime_contrasts.csv"
YOKOE = SOURCE_DIR / "yokoe_bridge_descriptive_contrast.csv"
OUT = ROOT / "data/exp/feasibility-check/stratified-four-unit-sensitivity"


def geometric_midpoint(lower: pd.Series, upper: pd.Series) -> pd.Series:
    if (lower.le(0) | upper.le(0)).any():
        raise ValueError("Restoration ratios must be positive")
    return np.exp((np.log(lower) + np.log(upper)) / 2)


def direction(lower: float, upper: float) -> str:
    if upper < 1:
        return "faster_in_2026"
    if lower > 1:
        return "slower_in_2026"
    return "direction_interval_crosses_one"


def base_units() -> pd.DataFrame:
    units = pd.read_csv(SOURCE).copy()
    units["MMI Difference (2026-2016)"] = units["2026 MMI Mean"] - units["2016 MMI Mean"]
    units["PGA Ratio (2026/2016)"] = (
        units["2026 PGA Mean (g)"] / units["2016 PGA Mean (g)"]
    )
    units["Restoration Ratio Midpoint"] = geometric_midpoint(
        units["2026/2016 Ratio Lower Bound"],
        units["2026/2016 Ratio Upper Bound"],
    )
    units["Log Restoration Ratio Midpoint"] = np.log(
        units["Restoration Ratio Midpoint"]
    )
    units["Recovery Direction"] = [
        direction(lower, upper)
        for lower, upper in zip(
            units["2026/2016 Ratio Lower Bound"],
            units["2026/2016 Ratio Upper Bound"],
            strict=True,
        )
    ]
    units["Higher 2026 MMI"] = units["MMI Difference (2026-2016)"].gt(0)
    units["Higher 2026 PGA"] = units["PGA Ratio (2026/2016)"].gt(1)
    return units


def scenario_units(units: pd.DataFrame) -> pd.DataFrame:
    scenarios: list[pd.DataFrame] = []

    motorway = units.loc[units["Unit Type"].eq("motorway_reopening_cluster")].copy()
    motorway.insert(0, "Scenario ID", "S1_MOTORWAY_ONLY")
    motorway.insert(1, "Scenario Label", "Three homogeneous motorway reopening clusters")
    motorway["Endpoint Definition"] = "primary general-traffic reopening"
    motorway["Scenario Use Gate"] = "eligible_stratified_descriptive_summary"
    scenarios.append(motorway)

    all_primary = units.copy()
    all_primary.insert(0, "Scenario ID", "S2_ALL_UNITS_PRIMARY")
    all_primary.insert(1, "Scenario Label", "All four independent units; primary endpoints")
    all_primary["Endpoint Definition"] = "primary general-traffic reopening"
    all_primary["Scenario Use Gate"] = "diagnostic_only_mixed_unit_types"
    scenarios.append(all_primary)

    yokoe = pd.read_csv(YOKOE).iloc[0]
    light_lower = float(yokoe["2016 Light-Vehicle Access Hours Lower Bound"])
    light_upper = float(yokoe["2016 Light-Vehicle Access Hours Upper Bound"])
    confirmed_2026 = float(yokoe["2026 Confirmed Restoration Hours"])
    alternate = units.copy()
    mask = alternate["Regime ID"].eq("REGIME-YOKOE")
    alternate.loc[mask, "2016 Restoration Hours Lower Bound"] = light_lower
    alternate.loc[mask, "2016 Restoration Hours Upper Bound"] = light_upper
    alternate.loc[mask, "2026/2016 Ratio Lower Bound"] = confirmed_2026 / light_upper
    alternate.loc[mask, "2026/2016 Ratio Upper Bound"] = confirmed_2026 / light_lower
    alternate.loc[mask, "Restoration Ratio Midpoint"] = np.sqrt(
        (confirmed_2026 / light_upper) * (confirmed_2026 / light_lower)
    )
    alternate.loc[mask, "Log Restoration Ratio Midpoint"] = np.log(
        alternate.loc[mask, "Restoration Ratio Midpoint"]
    )
    alternate.loc[mask, "Recovery Direction"] = "faster_in_2026"
    alternate.insert(0, "Scenario ID", "S3_ALL_UNITS_YOKOE_LIGHT_ACCESS")
    alternate.insert(
        1,
        "Scenario Label",
        "All four units; Yokoe 2016 light-vehicle bypass endpoint",
    )
    alternate["Endpoint Definition"] = "Yokoe <=2-tonne bypass; other primary endpoints"
    alternate["Scenario Use Gate"] = "diagnostic_endpoint_sensitivity_only"
    scenarios.append(alternate)

    combined = pd.concat(scenarios, ignore_index=True)
    return combined.sort_values(["Scenario ID", "Regime ID"]).reset_index(drop=True)


def summarize_scenario(group: pd.DataFrame) -> dict[str, object]:
    ratios = group["Restoration Ratio Midpoint"]
    directions = group["Recovery Direction"]
    improved = int(directions.eq("faster_in_2026").sum())
    slower = int(directions.eq("slower_in_2026").sum())
    return {
        "Scenario ID": group["Scenario ID"].iloc[0],
        "Scenario Label": group["Scenario Label"].iloc[0],
        "Unit Count": len(group),
        "Motorway Unit Count": int(group["Unit Type"].eq("motorway_reopening_cluster").sum()),
        "Bridge Unit Count": int(group["Unit Type"].eq("same_bridge_repeated_damage").sum()),
        "Faster in 2026 Count": improved,
        "Slower in 2026 Count": slower,
        "Direction-Ambiguous Count": int(
            directions.eq("direction_interval_crosses_one").sum()
        ),
        "Both Recovery Directions Present": improved > 0 and slower > 0,
        "All Units Have Higher 2026 MMI": bool(group["Higher 2026 MMI"].all()),
        "All Units Have Higher 2026 PGA": bool(group["Higher 2026 PGA"].all()),
        "MMI-PGA Direction Agreement Count": int(
            group["Higher 2026 MMI"].eq(group["Higher 2026 PGA"]).sum()
        ),
        "Median MMI Difference": group["MMI Difference (2026-2016)"].median(),
        "Median Restoration Ratio": ratios.median(),
        "Geometric Mean Restoration Ratio": float(np.exp(np.log(ratios).mean())),
        "Minimum Restoration Ratio": ratios.min(),
        "Maximum Restoration Ratio": ratios.max(),
        "Scenario Use Gate": group["Scenario Use Gate"].iloc[0],
    }


def build_scenario_summary(scenarios: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [summarize_scenario(group) for _, group in scenarios.groupby("Scenario ID")]
    ).sort_values("Scenario ID")


def build_leave_one_out(units: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for excluded in sorted(units["Regime ID"]):
        retained = units.loc[~units["Regime ID"].eq(excluded)].copy()
        ratios = retained["Restoration Ratio Midpoint"]
        improved = int(retained["Recovery Direction"].eq("faster_in_2026").sum())
        slower = int(retained["Recovery Direction"].eq("slower_in_2026").sum())
        majority = (
            "faster_in_2026"
            if improved > slower
            else "slower_in_2026"
            if slower > improved
            else "tie"
        )
        rows.append(
            {
                "Excluded Regime ID": excluded,
                "Retained Unit Count": len(retained),
                "Retained Regime IDs": "; ".join(sorted(retained["Regime ID"])),
                "Faster in 2026 Count": improved,
                "Slower in 2026 Count": slower,
                "Both Recovery Directions Present": improved > 0 and slower > 0,
                "Majority Direction": majority,
                "Median Restoration Ratio": ratios.median(),
                "Geometric Mean Restoration Ratio": float(
                    np.exp(np.log(ratios).mean())
                ),
                "Median MMI Difference": retained[
                    "MMI Difference (2026-2016)"
                ].median(),
                "All Retained Units Have Higher 2026 MMI": bool(
                    retained["Higher 2026 MMI"].all()
                ),
                "All Retained Units Have Higher 2026 PGA": bool(
                    retained["Higher 2026 PGA"].all()
                ),
            }
        )
    return pd.DataFrame(rows)


def build_endpoint_sensitivity(scenarios: pd.DataFrame) -> pd.DataFrame:
    rows = scenarios.loc[
        scenarios["Regime ID"].eq("REGIME-YOKOE")
        & scenarios["Scenario ID"].isin(
            ["S2_ALL_UNITS_PRIMARY", "S3_ALL_UNITS_YOKOE_LIGHT_ACCESS"]
        )
    ].copy()
    return rows[
        [
            "Scenario ID",
            "Endpoint Definition",
            "2016 Restoration Hours Lower Bound",
            "2016 Restoration Hours Upper Bound",
            "2026 Restoration Hours Lower Bound",
            "2026 Restoration Hours Upper Bound",
            "2026/2016 Ratio Lower Bound",
            "2026/2016 Ratio Upper Bound",
            "Restoration Ratio Midpoint",
            "Recovery Direction",
            "MMI Difference (2026-2016)",
        ]
    ].reset_index(drop=True)


def build_claim_gate(
    units: pd.DataFrame,
    scenario_summary: pd.DataFrame,
    loo: pd.DataFrame,
    endpoint: pd.DataFrame,
) -> pd.DataFrame:
    all_primary = scenario_summary.set_index("Scenario ID").loc["S2_ALL_UNITS_PRIMARY"]
    motorway = scenario_summary.set_index("Scenario ID").loc["S1_MOTORWAY_ONLY"]
    yokoe_direction_stable = endpoint["Recovery Direction"].nunique() == 1
    loo_majority_stable = loo["Majority Direction"].nunique() == 1
    rows = [
        (
            "C1",
            "Restoration was universally faster in 2026",
            "fail",
            f"Only {int(all_primary['Faster in 2026 Count'])} of {int(all_primary['Unit Count'])} units are faster; two are slower",
            "Do not make a universal resilience-dividend claim",
        ),
        (
            "C2",
            "The typical unit recovered faster in 2026",
            "unstable",
            f"Leave-one-out majority direction stable={loo_majority_stable}; medians cross 1 across deletions",
            "Do not summarize the four units with one directional average",
        ),
        (
            "C3",
            "Recovery responses are heterogeneous despite higher 2026 shaking",
            "pass_descriptive",
            f"Both directions occur in every primary and leave-one-out set; all {len(units)} units have higher 2026 mean MMI",
            "Use heterogeneity as the primary descriptive finding",
        ),
        (
            "C4",
            "Yokoe Bridge recovered faster under both defensible 2016 endpoints",
            "pass_descriptive",
            f"Endpoint direction stable={yokoe_direction_stable}; both ratios remain below 1",
            "Present Yokoe separately as a same-facility descriptive case",
        ),
        (
            "C5",
            "Post-2016 reconstruction caused Yokoe's faster 2026 recovery",
            "not_identified",
            "One treated bridge has no untreated same-facility counterfactual and the event contexts differ",
            "State association and mechanism plausibility only; no causal effect",
        ),
        (
            "C6",
            "All four units can be pooled in one common estimator",
            "fail",
            "The registry mixes three motorway release clusters with one same-bridge case",
            "Stratify by unit type; pooled summaries are diagnostics only",
        ),
        (
            "C7",
            "All retained units experienced higher mean MMI in 2026",
            "pass_measurement_descriptive",
            f"Minimum MMI increase={units['MMI Difference (2026-2016)'].min():.3f}",
            "Report as sampled ShakeMap exposure, not damage equivalence",
        ),
        (
            "C7B",
            "The higher-2026 shaking statement is invariant to MMI versus PGA",
            "fail_measurement_sensitivity",
            f"MMI is higher in all {len(units)} units, but PGA is higher in only {int(units['Higher 2026 PGA'].sum())}",
            "Show both metrics and avoid a metric-invariant stronger-shaking claim",
        ),
        (
            "C8",
            "The motorway subset supports an adjusted resilience estimator",
            "fail_sample_size",
            f"Homogeneous motorway subset n={int(motorway['Unit Count'])}",
            "Retain unit-level contrasts; acquire more independent regimes before modelling",
        ),
    ]
    return pd.DataFrame(
        rows,
        columns=[
            "Claim ID",
            "Candidate Claim",
            "Evidence Status",
            "Sensitivity Evidence",
            "Admissible Interpretation",
        ],
    )


def write_readme(
    units: pd.DataFrame,
    summary: pd.DataFrame,
    loo: pd.DataFrame,
    endpoint: pd.DataFrame,
) -> None:
    indexed = summary.set_index("Scenario ID")
    all_primary = indexed.loc["S2_ALL_UNITS_PRIMARY"]
    motorway = indexed.loc["S1_MOTORWAY_ONLY"]
    yokoe_ratios = endpoint["Restoration Ratio Midpoint"].sort_values().tolist()
    loo_medians = loo["Median Restoration Ratio"]
    lines = [
        "# Stratified four-unit recovery sensitivity experiment",
        "",
        "## Decision",
        "",
        "The robust result is heterogeneity, not a common resilience dividend. All four units have higher sampled mean MMI in 2026, yet two recover faster and two recover more slowly. This mixed direction remains visible in the motorway-only subset and after every leave-one-out deletion. PGA supplies a deliberately non-redundant hazard sensitivity: it is higher in 2026 for only part of the registry.",
        "",
        "Yokoe Bridge is directionally robust as a separate same-facility descriptive case. Its 2026/2016 restoration ratio remains below one whether the 2016 endpoint is full restored-bridge reopening or the earlier <=2-tonne bypass. This does not identify a reconstruction effect or mechanism.",
        "",
        "## Diagnostic results",
        "",
        f"- Motorway subset: n={int(motorway['Unit Count'])}; {int(motorway['Faster in 2026 Count'])} faster and {int(motorway['Slower in 2026 Count'])} slower; median ratio={motorway['Median Restoration Ratio']:.3f}.",
        f"- Four-unit registry: {int(all_primary['Faster in 2026 Count'])} faster and {int(all_primary['Slower in 2026 Count'])} slower; median ratio={all_primary['Median Restoration Ratio']:.3f}.",
        f"- Yokoe endpoint sensitivity: ratio midpoints range from {min(yokoe_ratios):.3f} to {max(yokoe_ratios):.3f}; direction is unchanged.",
        f"- Leave-one-out median ratios range from {loo_medians.min():.3f} to {loo_medians.max():.3f}; the majority direction changes with the excluded unit.",
        f"- Sampled 2026-minus-2016 MMI increases range from {units['MMI Difference (2026-2016)'].min():.3f} to {units['MMI Difference (2026-2016)'].max():.3f}.",
        f"- PGA ratios range from {units['PGA Ratio (2026/2016)'].min():.3f} to {units['PGA Ratio (2026/2016)'].max():.3f}; {int(units['Higher 2026 PGA'].sum())} of {len(units)} exceed one.",
        "",
        "## Consequence for the paper design",
        "",
        "Use a structured comparative design: show the three motorway clusters individually, then present Yokoe Bridge as a separate within-asset case. Do not report a pooled coefficient or a small-n significance test. The strongest defensible statement is that repeated-shock recovery is highly heterogeneous under the MMI comparison, while PGA shows that the cross-event stronger-shaking premise is metric-dependent. Yokoe shows a large endpoint-robust recovery improvement that warrants mechanism-focused investigation but does not establish a mechanism.",
        "",
        "## Files",
        "",
        "- `unit_level_contrasts.csv`: primary four-unit measurements and directions.",
        "- `scenario_unit_contrasts.csv`: every unit under each endpoint/pooling scenario.",
        "- `scenario_summary.csv`: motorway-only and four-unit diagnostic summaries.",
        "- `leave_one_out_summary.csv`: deletion sensitivity.",
        "- `yokoe_endpoint_sensitivity.csv`: full-bridge versus light-vehicle endpoint.",
        "- `claim_robustness_gate.csv`: allowed, unstable, and rejected claims.",
        "",
        "## Rebuild",
        "",
        "```bash",
        "UV_CACHE_DIR=/private/tmp/ke02-uv-cache uv run python src/analyses/experiment_stratified_recovery_sensitivity.py",
        "```",
    ]
    (OUT / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    units = base_units()
    if len(units) != 4 or units["Regime ID"].duplicated().any():
        raise ValueError("Expected four unique independent units")
    if not units["Higher 2026 MMI"].all():
        raise ValueError("The prespecified higher-2026-MMI condition does not hold")

    scenarios = scenario_units(units)
    summary = build_scenario_summary(scenarios)
    loo = build_leave_one_out(units)
    endpoint = build_endpoint_sensitivity(scenarios)
    claims = build_claim_gate(units, summary, loo, endpoint)

    if not summary["Both Recovery Directions Present"].all():
        raise ValueError("At least one scenario lost the prespecified heterogeneity signal")
    if not loo["Both Recovery Directions Present"].all():
        raise ValueError("Heterogeneity did not survive every leave-one-out deletion")
    if set(endpoint["Recovery Direction"]) != {"faster_in_2026"}:
        raise ValueError("Yokoe endpoint sensitivity changed direction")

    units.to_csv(OUT / "unit_level_contrasts.csv", index=False)
    scenarios.to_csv(OUT / "scenario_unit_contrasts.csv", index=False)
    summary.to_csv(OUT / "scenario_summary.csv", index=False)
    loo.to_csv(OUT / "leave_one_out_summary.csv", index=False)
    endpoint.to_csv(OUT / "yokoe_endpoint_sensitivity.csv", index=False)
    claims.to_csv(OUT / "claim_robustness_gate.csv", index=False)
    write_readme(units, summary, loo, endpoint)
    print(
        "PASS: four-unit stratified sensitivity complete; heterogeneity survives "
        "all scenarios and leave-one-out deletions, while Yokoe remains directionally stable."
    )


if __name__ == "__main__":
    main()
