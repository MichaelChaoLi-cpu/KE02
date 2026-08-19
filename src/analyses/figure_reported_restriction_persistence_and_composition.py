#!/usr/bin/env python3
"""Reported Restriction Persistence and Composition.

Plan: Show unique-record persistence over increasing snapshot thresholds with
a gap-free sensitivity, and compare record-weighted with feature-snapshot
restriction-reason composition, including a missing-excluded sensitivity.
Framework: Section 6.1 P_j, C_j, S(m), S_G(m), rho_record, rho_feature,
rho_record_nm, and rho_feature_nm; reporting persistence is not closure
duration or restoration time.
"""

from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/ke02-matplotlib")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.lines import Line2D


ROOT = Path(__file__).resolve().parents[2]
RESTRICTIONS = ROOT / "data/processed/kumamoto_2026_road_restriction_snapshots_preprocessed.parquet"
COVERAGE = ROOT / "data/processed/kumamoto_2026_road_snapshot_coverage_preprocessed.parquet"
OUT = ROOT / "docs/process-records/assets/supplementary/Figure_reported_restriction_persistence_and_composition.png"

REASON_LABELS = {
    "落石": "Rockfall",
    "橋梁損傷": "Bridge damage",
    "道路損壊": "Road damage",
    "地震": "Earthquake",
    "落下物・飛来物": "Falling or flying objects",
    "Missing": "Not reported",
}


def canonical_value(series: pd.Series) -> str:
    values = series.dropna().astype("string")
    if values.empty:
        return "Missing"
    modes = values.mode()
    return str(sorted(str(value) for value in modes)[0])


def prepare_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    restrictions = pd.read_parquet(RESTRICTIONS)
    coverage = pd.read_parquet(COVERAGE)
    required_restrictions = {
        "Restriction Record ID",
        "Restriction Feature ID",
        "Snapshot Time",
        "Restriction Reason",
    }
    required_coverage = {"Snapshot Time", "Restriction Layer Available"}
    if missing := sorted(required_restrictions - set(restrictions.columns)):
        raise ValueError(f"Missing required restriction columns: {missing}")
    if missing := sorted(required_coverage - set(coverage.columns)):
        raise ValueError(f"Missing required coverage columns: {missing}")

    available_times = list(
        coverage.loc[coverage["Restriction Layer Available"], "Snapshot Time"].sort_values()
    )
    if len(available_times) != 24:
        raise ValueError("Expected 24 snapshots with an available restriction layer")
    positions = {pd.Timestamp(time): index for index, time in enumerate(available_times)}

    rows: list[dict[str, object]] = []
    for record_id, group in restrictions.groupby("Restriction Record ID"):
        observed_times = sorted(pd.Timestamp(time) for time in group["Snapshot Time"].unique())
        observed_positions = [positions[time] for time in observed_times]
        expected = observed_positions[-1] - observed_positions[0] + 1
        rows.append(
            {
                "Restriction Record ID": record_id,
                "Observed Snapshot Count": len(observed_times),
                "Gap Free": len(observed_times) == expected,
                "Canonical Restriction Reason": canonical_value(group["Restriction Reason"]),
            }
        )
    persistence = pd.DataFrame(rows)
    if len(persistence) != 163 or persistence["Gap Free"].sum() != 134:
        raise ValueError("Record-persistence validation counts changed")

    record_reason = persistence["Canonical Restriction Reason"]
    record_share = record_reason.value_counts(normalize=True)
    record_nonmissing_share = record_reason.loc[
        record_reason.ne("Missing")
    ].value_counts(normalize=True)
    feature_reason = restrictions["Restriction Reason"].fillna("Missing").astype("string")
    feature_share = feature_reason.value_counts(normalize=True)
    feature_nonmissing_share = feature_reason.loc[
        feature_reason.ne("Missing")
    ].value_counts(normalize=True)
    top_reasons = list(record_share.nlargest(6).index)
    composition_rows: list[dict[str, object]] = []
    for reason in top_reasons:
        composition_rows.append(
            {
                "Reason": REASON_LABELS.get(reason, reason),
                "Unique records": float(record_share.get(reason, 0)),
                "Feature-snapshot rows": float(feature_share.get(reason, 0)),
                "Unique records excluding missing": (
                    np.nan
                    if reason == "Missing"
                    else float(record_nonmissing_share.get(reason, 0))
                ),
                "Feature-snapshot rows excluding missing": (
                    np.nan
                    if reason == "Missing"
                    else float(feature_nonmissing_share.get(reason, 0))
                ),
            }
        )
    nonmissing_top_reasons = [reason for reason in top_reasons if reason != "Missing"]
    composition_rows.append(
        {
            "Reason": "Other reasons",
            "Unique records": float(1 - record_share.reindex(top_reasons, fill_value=0).sum()),
            "Feature-snapshot rows": float(
                1 - feature_share.reindex(top_reasons, fill_value=0).sum()
            ),
            "Unique records excluding missing": float(
                1
                - record_nonmissing_share.reindex(
                    nonmissing_top_reasons, fill_value=0
                ).sum()
            ),
            "Feature-snapshot rows excluding missing": float(
                1
                - feature_nonmissing_share.reindex(
                    nonmissing_top_reasons, fill_value=0
                ).sum()
            ),
        }
    )
    composition = pd.DataFrame(composition_rows)
    if not np.isclose(composition["Unique records"].sum(), 1):
        raise ValueError("Record-weighted composition does not sum to one")
    if not np.isclose(composition["Feature-snapshot rows"].sum(), 1):
        raise ValueError("Feature-snapshot composition does not sum to one")
    nonmissing = composition["Reason"].ne("Not reported")
    if not np.isclose(
        composition.loc[nonmissing, "Unique records excluding missing"].sum(), 1
    ):
        raise ValueError("Missing-excluded record composition does not sum to one")
    if not np.isclose(
        composition.loc[
            nonmissing, "Feature-snapshot rows excluding missing"
        ].sum(),
        1,
    ):
        raise ValueError("Missing-excluded feature composition does not sum to one")
    return persistence, composition


def main() -> None:
    persistence, composition = prepare_data()
    thresholds = np.arange(1, int(persistence["Observed Snapshot Count"].max()) + 1)
    all_counts = np.array(
        [(persistence["Observed Snapshot Count"] >= threshold).sum() for threshold in thresholds]
    )
    gap_free = persistence.loc[persistence["Gap Free"]]
    gap_free_counts = np.array(
        [(gap_free["Observed Snapshot Count"] >= threshold).sum() for threshold in thresholds]
    )

    sns.set_theme(style="whitegrid", context="paper", font_scale=1.0)
    fig, (persistence_ax, composition_ax) = plt.subplots(
        1,
        2,
        figsize=(12.5, 5.55),
        gridspec_kw={"width_ratios": [0.92, 1.08], "wspace": 0.40},
    )

    persistence_ax.step(
        thresholds,
        all_counts,
        where="post",
        color="#315E75",
        linewidth=2.25,
        label="All unique records (n=163)",
    )
    persistence_ax.step(
        thresholds,
        gap_free_counts,
        where="post",
        color="#C58B45",
        linewidth=2.0,
        linestyle=(0, (4, 2)),
        label="No internal gap (n=134)",
    )
    persistence_ax.fill_between(
        thresholds,
        all_counts,
        step="post",
        color="#7DA7B8",
        alpha=0.17,
    )
    persistence_ax.set_xlabel("Minimum snapshots in which record appears")
    persistence_ax.set_ylabel("Unique restriction records")
    persistence_ax.set_xlim(1, thresholds.max())
    persistence_ax.set_ylim(0, len(persistence) * 1.04)
    persistence_ax.set_xticks([1, 4, 8, 12, 16, 20, 24])
    persistence_ax.grid(axis="y", color="#DCE1E4", linewidth=0.7)
    persistence_ax.grid(axis="x", visible=False)
    persistence_ax.legend(
        frameon=False,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.15),
        ncol=1,
    )
    for threshold in (1, 4, 10, 24):
        count = int((persistence["Observed Snapshot Count"] >= threshold).sum())
        persistence_ax.text(
            threshold + 0.22,
            count + 3,
            str(count),
            fontsize=8.7,
            color="#26343B",
        )

    composition = composition.iloc[::-1].reset_index(drop=True)
    y = np.arange(len(composition))
    height = 0.34
    record_bars = composition_ax.barh(
        y - height / 2,
        100 * composition["Unique records"],
        height=height,
        color="#315E75",
        label="Unique records",
    )
    feature_bars = composition_ax.barh(
        y + height / 2,
        100 * composition["Feature-snapshot rows"],
        height=height,
        color="#D5A15B",
        label="Feature-snapshot rows",
    )
    composition_ax.scatter(
        100 * composition["Unique records excluding missing"],
        y - height / 2,
        marker="D",
        s=31,
        facecolor="white",
        edgecolor="#315E75",
        linewidth=1.25,
        zorder=5,
    )
    composition_ax.scatter(
        100 * composition["Feature-snapshot rows excluding missing"],
        y + height / 2,
        marker="D",
        s=31,
        facecolor="white",
        edgecolor="#D5A15B",
        linewidth=1.25,
        zorder=5,
    )
    composition_ax.set_yticks(y, composition["Reason"])
    composition_ax.set_xlabel("Share within counting unit (%)")
    composition_ax.set_xlim(0, 28)
    composition_ax.grid(axis="x", color="#DCE1E4", linewidth=0.7)
    composition_ax.grid(axis="y", visible=False)
    handles, labels = composition_ax.get_legend_handles_labels()
    handles.append(
        Line2D(
            [0],
            [0],
            marker="D",
            linestyle="none",
            markerfacecolor="white",
            markeredgecolor="#4B5563",
            markeredgewidth=1.25,
            markersize=5.5,
        )
    )
    labels.append("Diamonds: excluding Not reported")
    composition_ax.legend(
        handles,
        labels,
        frameon=False,
        ncol=3,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.15),
        columnspacing=0.9,
        handletextpad=0.5,
        fontsize=8.0,
    )
    for bars in (record_bars, feature_bars):
        for bar in bars:
            composition_ax.text(
                bar.get_width() - 0.30,
                bar.get_y() + bar.get_height() / 2,
                f"{bar.get_width():.1f}",
                ha="right",
                va="center",
                fontsize=8.0,
                color="white",
                fontweight="bold",
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

    fig.subplots_adjust(left=0.10, right=0.98, top=0.96, bottom=0.22)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
