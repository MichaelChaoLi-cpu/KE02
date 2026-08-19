#!/usr/bin/env python3
"""Experiments for evidence-led road-restriction output planning.

These diagnostics test record-ID continuity, feature-versus-record weighting,
snapshot multiplicity, and road-overlap tolerance sensitivity. All outputs are
exploratory and remain outside data/results.
"""

from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/ke02-matplotlib")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from figure_mashiki_road_network_and_reported_restriction_overlap import (
    prepare_data as prepare_overlap_data,
)


ROOT = Path(__file__).resolve().parents[2]
RESTRICTIONS = ROOT / "data/processed/kumamoto_2026_road_restriction_snapshots_preprocessed.parquet"
COVERAGE = ROOT / "data/processed/kumamoto_2026_road_snapshot_coverage_preprocessed.parquet"
OUT = ROOT / "data/exp/figure-table-planning"

REASON_LABELS = {
    "落石": "Rockfall",
    "橋梁損傷": "Bridge damage",
    "道路損壊": "Road damage",
    "地震": "Earthquake",
    "落下物・飛来物": "Falling or flying objects",
    "法面崩落": "Slope failure",
    "地震による路面段差": "Earthquake-related surface step",
    "土砂流入": "Sediment inflow",
    "倒木": "Fallen trees",
    "地震による橋台段差": "Earthquake-related abutment step",
    "Missing": "Not reported",
}


def canonical_value(series: pd.Series) -> str:
    values = series.fillna("Missing").astype("string")
    modes = values.mode()
    return str(modes.iloc[0]) if not modes.empty else "Missing"


def record_identity_stability(restrictions: pd.DataFrame) -> pd.DataFrame:
    fields = [
        "Route Name",
        "Start Location",
        "End Location",
        "Restriction Type",
        "Restriction Reason",
        "Road Type",
        "Municipality",
    ]
    rows: list[dict[str, object]] = []
    record_count = restrictions["Restriction Record ID"].nunique()
    for field in fields:
        unique_counts = restrictions.groupby("Restriction Record ID")[field].agg(
            lambda values: values.dropna().astype("string").nunique()
        )
        rows.append(
            {
                "Identity Field": field,
                "Record Count": record_count,
                "Stable or All Missing": int(unique_counts.le(1).sum()),
                "Multiple Nonmissing Values": int(unique_counts.gt(1).sum()),
                "All Missing": int(unique_counts.eq(0).sum()),
                "Stable Share": float(unique_counts.le(1).mean()),
            }
        )

    def geometry_key(value: object) -> object:
        if value is None:
            return None
        if isinstance(value, (bytes, bytearray, memoryview)):
            return bytes(value)
        return value.wkb if hasattr(value, "wkb") else repr(value)

    geometry_counts = (
        restrictions.assign(_geometry=restrictions["Geometry"].map(geometry_key))
        .groupby("Restriction Record ID")["_geometry"]
        .nunique()
    )
    rows.append(
        {
            "Identity Field": "Geometry",
            "Record Count": record_count,
            "Stable or All Missing": int(geometry_counts.le(1).sum()),
            "Multiple Nonmissing Values": int(geometry_counts.gt(1).sum()),
            "All Missing": int(geometry_counts.eq(0).sum()),
            "Stable Share": float(geometry_counts.le(1).mean()),
        }
    )
    return pd.DataFrame(rows)


def record_persistence(
    restrictions: pd.DataFrame,
    coverage: pd.DataFrame,
) -> pd.DataFrame:
    available_times = list(
        coverage.loc[coverage["Restriction Layer Available"], "Snapshot Time"].sort_values()
    )
    positions = {pd.Timestamp(time): index for index, time in enumerate(available_times)}
    rows: list[dict[str, object]] = []
    for record_id, group in restrictions.groupby("Restriction Record ID"):
        observed_times = sorted(pd.Timestamp(time) for time in group["Snapshot Time"].unique())
        observed_positions = [positions[time] for time in observed_times]
        expected_snapshots = observed_positions[-1] - observed_positions[0] + 1
        run_count = 1 + sum(
            current - previous > 1
            for previous, current in zip(
                observed_positions,
                observed_positions[1:],
                strict=False,
            )
        )
        rows.append(
            {
                "Restriction Record ID": record_id,
                "Observed Snapshot Count": len(observed_times),
                "Expected Available Snapshots Between First and Last": expected_snapshots,
                "Continuity Ratio": len(observed_times) / expected_snapshots,
                "Internal Missing Snapshot Count": expected_snapshots - len(observed_times),
                "Observed Run Count": run_count,
                "First Observed Time": observed_times[0],
                "Last Observed Time": observed_times[-1],
                "Observed Span (hours)": (
                    observed_times[-1] - observed_times[0]
                ).total_seconds()
                / 3600,
                "Maximum Features Per Snapshot": int(
                    group.groupby("Snapshot Time").size().max()
                ),
                "Canonical Restriction Reason": canonical_value(group["Restriction Reason"]),
                "Canonical Road Type": canonical_value(group["Road Type"]),
                "Canonical Observation State": canonical_value(group["Observation State"]),
            }
        )
    return pd.DataFrame(rows).sort_values("Restriction Record ID").reset_index(drop=True)


def snapshot_sensitivity(restrictions: pd.DataFrame, coverage: pd.DataFrame) -> pd.DataFrame:
    available = coverage[["Snapshot Time", "Restriction Layer Available"]].copy()
    snapshot = restrictions.groupby("Snapshot Time").agg(
        Unique_Restriction_Records=("Restriction Record ID", "nunique"),
        Restriction_Features=("Restriction Feature ID", "nunique"),
        Length_Nonmissing=("Restriction Length (km)", "count"),
        Length_Total=("Restriction Length (km)", "size"),
    )
    snapshot["Feature to Record Ratio"] = (
        snapshot["Restriction_Features"] / snapshot["Unique_Restriction_Records"]
    )
    snapshot["Length Missing Share"] = 1 - (
        snapshot["Length_Nonmissing"] / snapshot["Length_Total"]
    )
    return available.merge(snapshot, how="left", left_on="Snapshot Time", right_index=True)


def composition_sensitivity(
    restrictions: pd.DataFrame,
    persistence: pd.DataFrame,
) -> pd.DataFrame:
    configurations = [
        ("Restriction Reason", "Canonical Restriction Reason"),
        ("Road Type", "Canonical Road Type"),
        ("Observation State", "Canonical Observation State"),
    ]
    rows: list[dict[str, object]] = []
    for feature_column, record_column in configurations:
        feature_shares = (
            restrictions[feature_column].fillna("Missing").astype("string").value_counts(normalize=True)
        )
        record_shares = persistence[record_column].value_counts(normalize=True)
        categories = feature_shares.index.union(record_shares.index)
        total_variation = 0.5 * float(
            (
                feature_shares.reindex(categories, fill_value=0)
                - record_shares.reindex(categories, fill_value=0)
            )
            .abs()
            .sum()
        )
        for category in categories:
            rows.append(
                {
                    "Variable": feature_column,
                    "Category": str(category),
                    "Unique Record Share": float(record_shares.get(category, 0)),
                    "Feature-Snapshot Share": float(feature_shares.get(category, 0)),
                    "Absolute Share Difference": abs(
                        float(record_shares.get(category, 0))
                        - float(feature_shares.get(category, 0))
                    ),
                    "Total Variation Distance": total_variation,
                }
            )
    return pd.DataFrame(rows)


def plot_persistence_and_composition(
    persistence: pd.DataFrame,
    composition: pd.DataFrame,
) -> None:
    sns.set_theme(style="whitegrid", context="paper", font_scale=1.0)
    fig, (persistence_ax, composition_ax) = plt.subplots(
        1,
        2,
        figsize=(12.4, 5.5),
        gridspec_kw={"width_ratios": [0.92, 1.08], "wspace": 0.39},
    )

    thresholds = np.arange(1, int(persistence["Observed Snapshot Count"].max()) + 1)
    survivor_counts = np.array(
        [(persistence["Observed Snapshot Count"] >= threshold).sum() for threshold in thresholds]
    )
    persistence_ax.step(
        thresholds,
        survivor_counts,
        where="post",
        color="#315E75",
        linewidth=2.2,
    )
    persistence_ax.fill_between(
        thresholds,
        survivor_counts,
        step="post",
        color="#7DA7B8",
        alpha=0.22,
    )
    persistence_ax.set_xlabel("Minimum number of snapshots reported")
    persistence_ax.set_ylabel("Unique restriction records")
    persistence_ax.set_xlim(1, thresholds.max())
    persistence_ax.set_ylim(0, len(persistence) * 1.04)
    persistence_ax.set_xticks([1, 4, 8, 12, 16, 20, 23])
    persistence_ax.grid(axis="y", color="#DCE1E4", linewidth=0.7)
    persistence_ax.grid(axis="x", visible=False)
    for threshold in (1, 4, 10, 23):
        count = int((persistence["Observed Snapshot Count"] >= threshold).sum())
        persistence_ax.text(
            threshold + 0.25,
            count + 3,
            str(count),
            color="#26343B",
            fontsize=8.8,
        )

    reason = composition.loc[composition["Variable"].eq("Restriction Reason")].copy()
    reason = reason.nlargest(7, "Unique Record Share").sort_values("Unique Record Share")
    reason["Label"] = reason["Category"].map(REASON_LABELS).fillna(reason["Category"])
    y = np.arange(len(reason))
    height = 0.34
    composition_ax.barh(
        y - height / 2,
        100 * reason["Unique Record Share"],
        height=height,
        color="#315E75",
        label="Unique records",
    )
    composition_ax.barh(
        y + height / 2,
        100 * reason["Feature-Snapshot Share"],
        height=height,
        color="#D19A54",
        label="Feature-snapshot rows",
    )
    composition_ax.set_yticks(y, reason["Label"])
    composition_ax.set_xlabel("Share within counting unit (%)")
    composition_ax.set_xlim(0, 27)
    composition_ax.grid(axis="x", color="#DCE1E4", linewidth=0.7)
    composition_ax.grid(axis="y", visible=False)
    composition_ax.legend(
        frameon=False,
        ncol=2,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.15),
    )

    for label, ax in zip("ab", (persistence_ax, composition_ax), strict=True):
        ax.text(
            -0.12,
            1.04,
            label,
            transform=ax.transAxes,
            fontsize=12,
            fontweight="bold",
            va="top",
        )
        sns.despine(ax=ax)

    fig.subplots_adjust(left=0.10, right=0.98, top=0.96, bottom=0.20)
    fig.savefig(OUT / "prototype_persistence_and_composition.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_overlap_sensitivity(overlap: pd.DataFrame) -> None:
    latest_time = overlap["Snapshot Time"].max()
    latest = overlap.loc[overlap["Snapshot Time"].eq(latest_time)].copy()
    x = np.arange(len(latest))
    width = 0.36
    sns.set_theme(style="whitegrid", context="paper", font_scale=1.0)
    fig, ax = plt.subplots(figsize=(7.1, 4.8))
    ax.bar(
        x - width / 2,
        latest["Matched Segment Share (%)"],
        width=width,
        color="#4B7F93",
        label="Road segments",
    )
    ax.bar(
        x + width / 2,
        latest["Matched Length Share (%)"],
        width=width,
        color="#C58B45",
        label="Road length",
    )
    ax.set_xticks(x, [f"{int(value)} m" for value in latest["Tolerance (m)"]])
    ax.set_xlabel("Spatial tolerance")
    ax.set_ylabel("Matched share of Mashiki network (%)")
    ax.grid(axis="y", color="#DCE1E4", linewidth=0.7)
    ax.grid(axis="x", visible=False)
    ax.legend(frameon=False, ncol=2, loc="upper left")
    sns.despine(ax=ax)
    fig.tight_layout()
    fig.savefig(OUT / "prototype_overlap_sensitivity.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def write_findings(
    persistence: pd.DataFrame,
    identity: pd.DataFrame,
    snapshots: pd.DataFrame,
    composition: pd.DataFrame,
    overlap: pd.DataFrame,
) -> None:
    perfect = int(persistence["Continuity Ratio"].eq(1).sum())
    gapped = int(persistence["Internal Missing Snapshot Count"].gt(0).sum())
    single = int(persistence["Observed Snapshot Count"].eq(1).sum())
    long = int(persistence["Observed Snapshot Count"].ge(10).sum())
    multiple = int(persistence["Maximum Features Per Snapshot"].gt(1).sum())
    available_snapshots = snapshots.loc[snapshots["Restriction Layer Available"]]
    record_feature_correlation = float(
        available_snapshots[["Unique_Restriction_Records", "Restriction_Features"]]
        .corr()
        .iloc[0, 1]
    )
    max_ratio = float(available_snapshots["Feature to Record Ratio"].max())
    identity_lookup = identity.set_index("Identity Field")
    tv = (
        composition.groupby("Variable")["Total Variation Distance"]
        .first()
        .to_dict()
    )
    latest_time = overlap["Snapshot Time"].max()
    latest = overlap.loc[overlap["Snapshot Time"].eq(latest_time)].set_index("Tolerance (m)")
    exact_count = int(latest.loc[0.0, "Matched Segment Count"])
    tolerant_count = int(latest.loc[50.0, "Matched Segment Count"])
    overlap_ranges = overlap.groupby("Tolerance (m)")["Matched Segment Count"].agg(["min", "max"])
    stable_tolerances = int((overlap_ranges["min"] == overlap_ranges["max"]).sum())

    text = f"""# Road-restriction output-design experiments

## Scope

These experiments test whether record persistence, category composition,
snapshot summaries, and road-network overlap can support formal Results
outputs. They are exploratory and do not estimate restoration or causal effects.

## Record continuity

- Unique restriction records: {len(persistence)}.
- Gap-free between first and last observed snapshots: {perfect} ({perfect / len(persistence):.1%}).
- At least one internal missing snapshot: {gapped} ({gapped / len(persistence):.1%}).
- Observed in exactly one snapshot: {single} ({single / len(persistence):.1%}).
- Observed in at least ten snapshots: {long} ({long / len(persistence):.1%}).

**Decision implication:** persistence is informative as persistence in the
official reporting archive, but it must not be interpreted as closure duration.
Any final view should disclose internal gaps or include a gap-free sensitivity.

## Record identity stability

- Stable route name: {int(identity_lookup.loc['Route Name', 'Stable or All Missing'])} of {len(persistence)} records ({identity_lookup.loc['Route Name', 'Stable Share']:.1%}).
- Stable start location: {int(identity_lookup.loc['Start Location', 'Stable or All Missing'])} of {len(persistence)} records ({identity_lookup.loc['Start Location', 'Stable Share']:.1%}).
- Stable end location: {int(identity_lookup.loc['End Location', 'Stable or All Missing'])} of {len(persistence)} records ({identity_lookup.loc['End Location', 'Stable Share']:.1%}).
- Stable restriction reason: {int(identity_lookup.loc['Restriction Reason', 'Stable or All Missing'])} of {len(persistence)} records ({identity_lookup.loc['Restriction Reason', 'Stable Share']:.1%}).
- Stable geometry: {int(identity_lookup.loc['Geometry', 'Stable or All Missing'])} of {len(persistence)} records ({identity_lookup.loc['Geometry', 'Stable Share']:.1%}).

**Decision implication:** the source record ID is sufficiently stable for a
bounded reporting-persistence result. The small number of inconsistent records
must be flagged in the supporting table rather than silently harmonized.

## Counting-unit sensitivity

- Records with multiple features in at least one snapshot: {multiple} ({multiple / len(persistence):.1%}).
- Correlation between snapshot record counts and feature counts: {record_feature_correlation:.3f}.
- Maximum feature-to-record count ratio in one snapshot: {max_ratio:.3f}.
- Total-variation distance, restriction reason: {tv['Restriction Reason']:.3f}.
- Total-variation distance, road type: {tv['Road Type']:.3f}.
- Total-variation distance, observation state: {tv['Observation State']:.3f}.

**Decision implication:** unique records should be the primary unit for
composition. Feature-snapshot shares are a persistence-weighted sensitivity,
not the main percentage.

## Road-overlap sensitivity

- Exact-intersection matched segments at the latest snapshot: {exact_count}.
- Matched segments within 50 m at the latest snapshot: {tolerant_count}.
- Tolerances with identical matched counts across all snapshots: {stable_tolerances} of {len(overlap_ranges)}.

**Decision implication:** the temporal overlap curve is largely redundant.
A map plus a compact tolerance comparison communicates the result more directly.

## Provisional output recommendation

1. Retain the four-snapshot spatial-progression map as a Results figure.
2. Add a two-panel reporting-persistence and counting-unit-sensitivity figure.
3. Revise the Mashiki overlap figure so its second panel compares tolerances
   directly rather than emphasizing an almost-flat time series.
4. Keep the observation timeline as supplementary material.
5. Use unique restriction records as the primary unit in composition tables,
   with feature-snapshot results shown only as sensitivity columns.
6. Keep coverage, eligibility, and evidence-gate diagnostics in docs/process-records.
"""
    (OUT / "experiment_findings.md").write_text(text, encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    restrictions = pd.read_parquet(RESTRICTIONS)
    coverage = pd.read_parquet(COVERAGE)
    persistence = record_persistence(restrictions, coverage)
    identity = record_identity_stability(restrictions)
    snapshots = snapshot_sensitivity(restrictions, coverage)
    composition = composition_sensitivity(restrictions, persistence)
    _, _, _, overlap, _, _ = prepare_overlap_data()

    persistence.to_csv(OUT / "record_persistence_diagnostics.csv", index=False)
    identity.to_csv(OUT / "record_identity_stability.csv", index=False)
    snapshots.to_csv(OUT / "snapshot_counting_unit_sensitivity.csv", index=False)
    composition.to_csv(OUT / "composition_weighting_sensitivity.csv", index=False)
    overlap.to_csv(OUT / "road_overlap_tolerance_sensitivity.csv", index=False)
    plot_persistence_and_composition(persistence, composition)
    plot_overlap_sensitivity(overlap)
    write_findings(persistence, identity, snapshots, composition, overlap)
    print(f"Saved experimental outputs: {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
