#!/usr/bin/env python3
"""Prepare the four-unit repeated-shock recovery comparison datasets.

The main output retains four independent recovery units and separates the
homogeneous motorway subset from the same-bridge Yokoe descriptive case. The
companion outputs retain both defensible 2016 Yokoe endpoint definitions and
the official same-asset recovery chronology. No values are imputed and no
pooled estimator is constructed.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
EXPERIMENT = ROOT / "data/exp/feasibility-check/stratified-four-unit-sensitivity"
INVENTORY = ROOT / "data/exp/feasibility-check/independent-reopening-regimes"
OUT_UNITS = (
    ROOT / "data/processed/kumamoto_repeated_shock_recovery_units_preprocessed.parquet"
)
OUT_ENDPOINTS = (
    ROOT / "data/processed/yokoe_bridge_endpoint_sensitivity_preprocessed.parquet"
)
OUT_MILESTONES = (
    ROOT / "data/processed/yokoe_bridge_recovery_milestones_preprocessed.parquet"
)


def prepare_units() -> pd.DataFrame:
    units = pd.read_csv(EXPERIMENT / "unit_level_contrasts.csv")
    inventory = pd.read_csv(INVENTORY / "eligible_regime_inventory.csv")
    labels = inventory[["Candidate Regime ID", "Candidate Label"]].rename(
        columns={
            "Candidate Regime ID": "Regime ID",
            "Candidate Label": "Recovery Unit Label",
        }
    )
    units = units.merge(labels, on="Regime ID", how="left", validate="one_to_one")

    units["Analytical Role"] = units["Unit Type"].map(
        {
            "motorway_reopening_cluster": "motorway_descriptive_subset",
            "same_bridge_repeated_damage": "same_asset_descriptive_case",
        }
    )
    units = units.rename(
        columns={
            "Regime ID": "Recovery Unit ID",
            "2016 MMI Mean": "2016 Mean MMI",
            "2026 MMI Mean": "2026 Mean MMI",
            "MMI Difference (2026-2016)": "MMI Difference",
            "PGA Ratio (2026/2016)": "PGA Ratio",
            "2026/2016 Ratio Lower Bound": "Restoration Ratio Lower Bound",
            "2026/2016 Ratio Upper Bound": "Restoration Ratio Upper Bound",
        }
    )
    columns = [
        "Recovery Unit ID",
        "Recovery Unit Label",
        "Unit Type",
        "Analytical Role",
        "Named Segment Count",
        "2016 Mean MMI",
        "2026 Mean MMI",
        "MMI Difference",
        "2016 PGA Mean (g)",
        "2026 PGA Mean (g)",
        "PGA Ratio",
        "Higher 2026 PGA",
        "2016 Restoration Hours Lower Bound",
        "2016 Restoration Hours Upper Bound",
        "2026 Restoration Hours Lower Bound",
        "2026 Restoration Hours Upper Bound",
        "Restoration Ratio Lower Bound",
        "Restoration Ratio Upper Bound",
        "Restoration Ratio Midpoint",
        "Log Restoration Ratio Midpoint",
        "Recovery Direction",
    ]
    units = units[columns].sort_values("Recovery Unit ID").reset_index(drop=True)

    assert len(units) == 4
    assert units["Recovery Unit ID"].is_unique
    assert units.notna().all().all()
    assert units["MMI Difference"].gt(0).all()
    assert np.allclose(
        units["MMI Difference"], units["2026 Mean MMI"] - units["2016 Mean MMI"]
    )
    assert np.allclose(
        units["Restoration Ratio Midpoint"],
        np.sqrt(
            units["Restoration Ratio Lower Bound"]
            * units["Restoration Ratio Upper Bound"]
        ),
    )
    assert np.allclose(
        units["Log Restoration Ratio Midpoint"],
        np.log(units["Restoration Ratio Midpoint"]),
    )
    assert units["Recovery Direction"].value_counts().to_dict() == {
        "slower_in_2026": 2,
        "faster_in_2026": 2,
    }
    assert units["Analytical Role"].value_counts().to_dict() == {
        "motorway_descriptive_subset": 3,
        "same_asset_descriptive_case": 1,
    }
    return units


def prepare_endpoints() -> pd.DataFrame:
    endpoints = pd.read_csv(EXPERIMENT / "yokoe_endpoint_sensitivity.csv")
    endpoints.insert(0, "Recovery Unit ID", "REGIME-YOKOE")
    endpoints.insert(1, "Recovery Unit Label", "Prefectural Route 338 Yokoe Bridge")
    endpoints["Endpoint Role"] = endpoints["Scenario ID"].map(
        {
            "S2_ALL_UNITS_PRIMARY": "primary_full_bridge_reopening",
            "S3_ALL_UNITS_YOKOE_LIGHT_ACCESS": "sensitivity_light_vehicle_access",
        }
    )
    endpoints = endpoints.rename(
        columns={
            "2026/2016 Ratio Lower Bound": "Restoration Ratio Lower Bound",
            "2026/2016 Ratio Upper Bound": "Restoration Ratio Upper Bound",
            "MMI Difference (2026-2016)": "MMI Difference",
        }
    )
    columns = [
        "Recovery Unit ID",
        "Recovery Unit Label",
        "Endpoint Definition",
        "Endpoint Role",
        "2016 Restoration Hours Lower Bound",
        "2016 Restoration Hours Upper Bound",
        "2026 Restoration Hours Lower Bound",
        "2026 Restoration Hours Upper Bound",
        "Restoration Ratio Lower Bound",
        "Restoration Ratio Upper Bound",
        "Restoration Ratio Midpoint",
        "Recovery Direction",
        "MMI Difference",
    ]
    endpoints = endpoints[columns].sort_values("Endpoint Role").reset_index(drop=True)

    assert len(endpoints) == 2
    assert endpoints.notna().all().all()
    assert endpoints["Recovery Direction"].eq("faster_in_2026").all()
    assert endpoints["Restoration Ratio Upper Bound"].lt(1).all()
    assert endpoints["MMI Difference"].gt(0).all()
    assert np.allclose(
        endpoints["Restoration Ratio Midpoint"],
        np.sqrt(
            endpoints["Restoration Ratio Lower Bound"]
            * endpoints["Restoration Ratio Upper Bound"]
        ),
    )
    return endpoints


def prepare_milestones() -> pd.DataFrame:
    source = INVENTORY / "yokoe_bridge_recovery_milestones.csv"
    milestones = pd.read_csv(source)
    milestones["Lower Bound"] = pd.to_datetime(milestones["Lower Bound"], utc=True)
    milestones["Upper Bound"] = pd.to_datetime(milestones["Upper Bound"], utc=True)
    origins = {
        2016: pd.Timestamp("2016-04-15 16:25:06", tz="UTC"),
        2026: pd.Timestamp("2026-07-28 07:27:15.512", tz="UTC"),
    }
    milestones["Event Origin"] = milestones["Episode"].map(origins)
    milestones["Elapsed Days Lower Bound"] = (
        milestones["Lower Bound"] - milestones["Event Origin"]
    ).dt.total_seconds() / 86400
    milestones["Elapsed Days Upper Bound"] = (
        milestones["Upper Bound"] - milestones["Event Origin"]
    ).dt.total_seconds() / 86400
    milestones["Elapsed Days Midpoint"] = (
        milestones["Elapsed Days Lower Bound"]
        + milestones["Elapsed Days Upper Bound"]
    ) / 2
    milestones["Milestone Label"] = milestones["Milestone"].map(
        {
            "full_closure": "Full closure",
            "light_vehicle_bypass": "≤2-tonne bypass",
            "restored_bridge_general_traffic": "Restored bridge reopening",
            "confirmed_general_traffic_reopening": "General-traffic reopening",
        }
    )
    columns = [
        "Episode",
        "Event Origin",
        "Milestone",
        "Milestone Label",
        "Lower Bound",
        "Upper Bound",
        "Elapsed Days Lower Bound",
        "Elapsed Days Upper Bound",
        "Elapsed Days Midpoint",
        "Precision",
        "Traffic Meaning",
        "Source ID",
    ]
    milestones = milestones[columns].sort_values(
        ["Episode", "Elapsed Days Midpoint"]
    ).reset_index(drop=True)
    assert len(milestones) == 5
    assert milestones.notna().all().all()
    assert milestones["Elapsed Days Lower Bound"].ge(0).all()
    return milestones


def main() -> None:
    units = prepare_units()
    endpoints = prepare_endpoints()
    milestones = prepare_milestones()
    OUT_UNITS.parent.mkdir(parents=True, exist_ok=True)
    units.to_parquet(OUT_UNITS, index=False)
    endpoints.to_parquet(OUT_ENDPOINTS, index=False)
    milestones.to_parquet(OUT_MILESTONES, index=False)
    print(f"Saved: {OUT_UNITS.relative_to(ROOT)} ({len(units)} rows, {len(units.columns)} columns)")
    print(
        f"Saved: {OUT_ENDPOINTS.relative_to(ROOT)} "
        f"({len(endpoints)} rows, {len(endpoints.columns)} columns)"
    )
    print(
        f"Saved: {OUT_MILESTONES.relative_to(ROOT)} "
        f"({len(milestones)} rows, {len(milestones.columns)} columns)"
    )


if __name__ == "__main__":
    main()
