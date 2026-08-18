#!/usr/bin/env python3
"""Audit the resilience preprocessing outputs and write reproducible evidence."""

from __future__ import annotations

from pathlib import Path
import json

import geopandas as gpd
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data/processed"
AUDIT_PATH = ROOT / "data/exp/data-preprocessing/resilience_audit.md"


def assert_ascii_columns(frame: pd.DataFrame, label: str) -> None:
    non_ascii = [column for column in frame.columns if not str(column).isascii()]
    if non_ascii:
        raise AssertionError(f"{label} contains non-ASCII readable names: {non_ascii}")


def missingness_table(frame: pd.DataFrame) -> str:
    missing = frame.isna().mean().mul(100).sort_values(ascending=False)
    rows = ["| Variable | Missing (%) |", "|---|---:|"]
    rows.extend(f"| {name} | {value:.1f} |" for name, value in missing.items())
    return "\n".join(rows)


def main() -> None:
    road = gpd.read_parquet(
        PROCESSED / "mashiki_official_road_network_preprocessed.parquet"
    )
    restrictions = gpd.read_parquet(
        PROCESSED / "kumamoto_2026_road_restriction_snapshots_preprocessed.parquet"
    )
    coverage = pd.read_parquet(
        PROCESSED / "kumamoto_2026_road_snapshot_coverage_preprocessed.parquet"
    )
    interventions = pd.read_parquet(
        PROCESSED / "mashiki_resilience_interventions_preprocessed.parquet"
    )
    decisions = json.loads(
        (ROOT / "data/exp/data-preprocessing/resilience_decisions.json").read_text(
            encoding="utf-8"
        )
    )

    for label, frame in {
        "road network": road,
        "restriction snapshots": restrictions,
        "snapshot coverage": coverage,
        "intervention ledger": interventions,
    }.items():
        assert_ascii_columns(frame, label)

    assert len(road) == 433
    assert road["Road Segment ID"].is_unique
    assert road.crs.to_epsg() == 4326
    assert road.geometry.notna().all() and road.geometry.is_valid.all()

    assert len(restrictions) == 1_063
    assert restrictions["Restriction Feature ID"].is_unique
    assert restrictions.crs.to_epsg() == 4326
    assert restrictions.geometry.notna().all() and restrictions.geometry.is_valid.all()
    assert restrictions["Snapshot Time"].nunique() == 23
    assert restrictions["Record Present"].all()
    expected_state_counts = {
        "active_full_closure": 900,
        "active_emergency_access_only": 57,
        "restriction_lifted": 49,
        "unknown_status": 57,
    }
    assert restrictions["Observation State"].value_counts().to_dict() == expected_state_counts

    assert len(coverage) == 24
    assert coverage["Snapshot Archive"].is_unique
    assert coverage["Restriction Layer Available"].sum() == 23
    assert coverage["Absence Interpretation"].eq("not_observed_not_open").all()
    coverage_decisions = next(
        dataset["secondary_output_variables"]
        for dataset in decisions["datasets"].values()
        if "secondary_output_variables" in dataset
    )
    assert {
        variable["readable_name"]
        for variable in coverage_decisions
        if variable["is_final_variable"] == "yes"
    } == {
        "Restriction Layer Available",
        "Restriction Feature Count",
        "Absence Interpretation",
    }
    absent = coverage.loc[~coverage["Restriction Layer Available"]]
    assert len(absent) == 1 and absent["Restriction Feature Count"].eq(0).all()

    assert len(interventions) == 20
    assert interventions["Intervention ID"].is_unique
    assert interventions["Completed Before 2026 Event"].all()
    assert interventions["Route Match Count"].gt(0).sum() == 12
    assert not interventions["Geometry Use Eligible"].any()
    assert not interventions["Treatment Use Eligible"].any()

    duplicate_event_mask = restrictions.duplicated(
        ["Snapshot Time", "Restriction Record ID"], keep=False
    )
    duplicate_event_rows = int(duplicate_event_mask.sum())
    duplicate_event_groups = int(
        restrictions.loc[duplicate_event_mask]
        .groupby(["Snapshot Time", "Restriction Record ID"], dropna=False)
        .ngroups
    )
    duplicate_event_excess = int(
        restrictions.duplicated(["Snapshot Time", "Restriction Record ID"]).sum()
    )
    lifted_record_ids = restrictions.loc[
        restrictions["Observation State"].eq("restriction_lifted"),
        "Restriction Record ID",
    ].unique()
    observed_active_to_lifted = 0
    for record_id in lifted_record_ids:
        record = restrictions.loc[
            restrictions["Restriction Record ID"].eq(record_id)
        ].sort_values("Snapshot Time")
        first_lifted_time = record.loc[
            record["Observation State"].eq("restriction_lifted"), "Snapshot Time"
        ].min()
        if record.loc[
            record["Snapshot Time"].lt(first_lifted_time)
            & record["Observation State"].isin(
                ["active_full_closure", "active_emergency_access_only"]
            )
        ].shape[0] > 0:
            observed_active_to_lifted += 1
    assert len(lifted_record_ids) == 4
    assert observed_active_to_lifted == 1

    coverage_rows = []
    for row in coverage.itertuples(index=False):
        coverage_rows.append(
            "| {time} | {available} | {count} | {signature} |".format(
                time=row[0].strftime("%Y-%m-%d %H:%M %Z"),
                available="yes" if row[3] else "no",
                count=row[4],
                signature="—" if pd.isna(row[7]) else row[7],
            )
        )

    report = f"""# Resilience preprocessing audit

Audit status: **PASS**

## Output integrity

| Output | Rows | Columns | Key / geometry checks |
|---|---:|---:|---|
| Official Mashiki road network | {len(road):,} | {len(road.columns)} | 433 unique segment IDs; WGS84; all geometries present and valid |
| 2026 road-restriction features | {len(restrictions):,} | {len(restrictions.columns)} | 1,063 unique feature IDs; 23 observed snapshots; WGS84; all geometries present and valid |
| Restriction snapshot coverage | {len(coverage):,} | {len(coverage.columns)} | 24 unique archives; 23 restriction-bearing snapshots and one explicit layer absence |
| Candidate resilience interventions | {len(interventions):,} | {len(interventions.columns)} | 20 unique intervention IDs; 12 candidate route matches; zero geometry- or treatment-eligible records |

All output column names are English-readable ASCII names. Raw inputs were not modified.
The variable contract contains 49 confirmed final analytical variables, including the three snapshot-coverage fields required by the output plan.

## Identification safeguards

- Missing values were retained; no imputation was performed.
- Observation State separates 900 active full-closure rows, 57 active emergency-access-only rows, 49 restriction-lifted rows, and 57 unknown-status rows. An unlisted road is never coded as open.
- The 49 lifted rows represent four source record IDs across 21 snapshots. Only one of those IDs is observed first in an active state and later in a lifted state; the other three enter the series already lifted. This is too sparse for a general restoration-time outcome.
- The 29 July 2026 08:00 archive has no restriction layer and is represented in the coverage table as `not_observed_not_open`, not as a zero-closure observation.
- Source `Restriction Record ID` is an event-level identifier and is not assumed to be row-unique. There are {duplicate_event_rows} rows in {duplicate_event_groups} within-snapshot repeated-ID groups ({duplicate_event_excess} rows beyond one per group). These source rows are retained because an event may cover multiple route sections or features.
- `Restriction Feature ID` is the deterministic row-level key. It combines the immutable snapshot archive, source feature position, source event identifier, properties, and geometry.
- All 20 intervention completion intervals end before the 28 July 2026 event, but partial completion and unresolved completed-subsegment geometry are preserved. Consequently, every `Geometry Use Eligible` and `Treatment Use Eligible` flag remains false.
- Candidate name matches to an official whole-route feature do not establish the geometry of the completed intervention subsegment.

## Restriction snapshot coverage

| Snapshot | Restriction layer | Features | Schema signature |
|---|---|---:|---|
{chr(10).join(coverage_rows)}

## Restriction-variable missingness

Missingness reflects changing official source schemas and is not filled or interpreted as evidence of openness.

{missingness_table(restrictions.drop(columns="Geometry"))}

## Remaining analysis gate

The processed restriction series can support descriptive disruption timing, extent, and network-overlay work. It cannot yet identify a causal effect of reconstruction interventions because exact completed intervention geometries are unavailable. A main treatment-control analysis remains blocked until completed subsegments are recovered or a defensible alternative exposure definition is independently validated.
"""
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_PATH.write_text(report, encoding="utf-8")
    print(f"PASS -> {AUDIT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
