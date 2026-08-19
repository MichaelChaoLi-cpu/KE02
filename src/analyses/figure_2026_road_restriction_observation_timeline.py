#!/usr/bin/env python3
"""2026 Road Restriction Observation Timeline.

Plan: Provide a supplementary coverage diagnostic for active, lifted, and
unknown reported states, active reported length, and field completeness.
Framework: Section 6.1 state-specific counts, active observed length, active
length missingness, and state composition; Section 7 bounded temporal reporting.
"""

from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/ke02-matplotlib")

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


ROOT = Path(__file__).resolve().parents[2]
RESTRICTIONS = ROOT / "data/processed/kumamoto_2026_road_restriction_snapshots_preprocessed.parquet"
COVERAGE = ROOT / "data/processed/kumamoto_2026_road_snapshot_coverage_preprocessed.parquet"
OUT = ROOT / "docs/process-records/assets/supplementary/Figure_2026_road_restriction_observation_timeline.png"

STATE_ORDER = [
    "active_full_closure",
    "active_emergency_access_only",
    "restriction_lifted",
    "unknown_status",
]
STATE_LABELS = {
    "active_full_closure": "Active full closure",
    "active_emergency_access_only": "Emergency access only",
    "restriction_lifted": "Restriction lifted",
    "unknown_status": "Status unavailable",
}
STATE_COLORS = {
    "active_full_closure": "#B23A48",
    "active_emergency_access_only": "#E69F00",
    "restriction_lifted": "#0072B2",
    "unknown_status": "#8C8C8C",
}
ACTIVE_STATES = {"active_full_closure", "active_emergency_access_only"}


def prepare_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    restrictions = pd.read_parquet(RESTRICTIONS)
    coverage = pd.read_parquet(COVERAGE).sort_values("Snapshot Time").reset_index(drop=True)

    if len(coverage) != 25 or coverage["Restriction Layer Available"].sum() != 24:
        raise ValueError("Expected 25 snapshots with 24 available restriction layers")
    if set(restrictions["Observation State"].unique()) != set(STATE_ORDER):
        raise ValueError("Unexpected Observation State categories")

    counts = (
        restrictions.groupby(["Snapshot Time", "Observation State"])["Restriction Feature ID"]
        .nunique()
        .unstack(fill_value=0)
        .reindex(columns=STATE_ORDER, fill_value=0)
        .reindex(coverage["Snapshot Time"], fill_value=0)
        .astype(float)
    )
    counts.index.name = "Snapshot Time"

    available = coverage.set_index("Snapshot Time")["Restriction Layer Available"]
    reported = coverage.set_index("Snapshot Time")["Restriction Feature Count"]
    if not counts.loc[available].sum(axis=1).astype(int).eq(reported.loc[available]).all():
        raise ValueError("State counts do not reconcile to official feature counts")
    counts.loc[~available, :] = np.nan

    active = restrictions[restrictions["Observation State"].isin(ACTIVE_STATES)].copy()
    active_summary = active.groupby("Snapshot Time").agg(
        active_feature_count=("Restriction Feature ID", "nunique"),
        active_length_observed_km=("Restriction Length (km)", lambda x: x.sum(min_count=1)),
        active_length_nonmissing=("Restriction Length (km)", "count"),
    )
    active_summary["active_length_missing_pct"] = 100 * (
        1 - active_summary["active_length_nonmissing"] / active_summary["active_feature_count"]
    )
    active_summary = active_summary.reindex(coverage["Snapshot Time"])
    active_summary.loc[~available, :] = np.nan
    return coverage, counts.join(active_summary)


def main() -> None:
    coverage, summary = prepare_data()
    times = summary.index
    unavailable_time = coverage.loc[
        ~coverage["Restriction Layer Available"], "Snapshot Time"
    ].iloc[0]

    sns.set_theme(style="ticks", context="paper", font_scale=1.05)
    fig = plt.figure(figsize=(11.5, 9.6))
    grid = fig.add_gridspec(
        3,
        2,
        width_ratios=(1, 0.025),
        hspace=0.52,
        wspace=0.05,
    )
    axes = np.array([fig.add_subplot(grid[row, 0]) for row in range(3)])
    colorbar_ax = fig.add_subplot(grid[2, 1])

    for state in STATE_ORDER:
        axes[0].plot(
            times,
            summary[state],
            color=STATE_COLORS[state],
            linewidth=2.0,
            marker="o",
            markersize=4,
            label=STATE_LABELS[state],
        )
    axes[0].set_ylabel("Reported features")
    axes[0].set_ylim(bottom=0)
    axes[0].legend(
        frameon=False,
        ncol=4,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.12),
        columnspacing=1.5,
        handlelength=2.1,
    )

    axes[1].plot(
        times,
        summary["active_length_observed_km"],
        color="#2A6F97",
        linewidth=2.2,
        marker="o",
        markersize=4,
        label="Observed active length",
    )
    axes[1].set_ylabel("Observed active length (km)", color="#2A6F97")
    axes[1].tick_params(axis="y", colors="#2A6F97")
    axes[1].set_ylim(bottom=0)
    missing_ax = axes[1].twinx()
    missing_ax.plot(
        times,
        summary["active_length_missing_pct"],
        color="#CC7A00",
        linewidth=1.8,
        linestyle="--",
        marker="s",
        markersize=3.5,
        label="Active length missing",
    )
    missing_ax.set_ylabel("Active length missing (%)", color="#CC7A00")
    missing_ax.tick_params(axis="y", colors="#CC7A00")
    missing_ax.set_ylim(0, 100)

    shares = summary[STATE_ORDER].div(summary[STATE_ORDER].sum(axis=1), axis=0) * 100
    date_values = mdates.date2num(pd.DatetimeIndex(times).to_pydatetime())
    date_midpoints = (date_values[:-1] + date_values[1:]) / 2
    date_edges = np.concatenate(
        (
            [date_values[0] - (date_midpoints[0] - date_values[0])],
            date_midpoints,
            [date_values[-1] + (date_values[-1] - date_midpoints[-1])],
        )
    )
    heatmap_cmap = sns.light_palette("#7B2CBF", as_cmap=True)
    heatmap_cmap.set_bad("#E6E6E6")
    heatmap = axes[2].pcolormesh(
        date_edges,
        np.arange(len(STATE_ORDER) + 1),
        np.ma.masked_invalid(shares[STATE_ORDER].T.to_numpy()),
        cmap=heatmap_cmap,
        vmin=0,
        vmax=100,
        shading="flat",
        linewidth=0.35,
        edgecolors="white",
    )
    colorbar = fig.colorbar(heatmap, cax=colorbar_ax)
    colorbar.set_label("Share (%)")
    axes[2].set_ylabel("")
    axes[2].set_xlabel("Official snapshot time (JST)")
    axes[2].set_yticks(np.arange(len(STATE_ORDER)) + 0.5)
    axes[2].set_yticklabels([STATE_LABELS[state] for state in STATE_ORDER])
    axes[2].invert_yaxis()
    axes[2].text(
        mdates.date2num(pd.Timestamp(unavailable_time).to_pydatetime()),
        len(STATE_ORDER) / 2,
        "NA",
        ha="center",
        va="center",
        fontsize=8,
        fontweight="bold",
        color="#333333",
    )

    for ax in axes[:2]:
        ax.axvline(unavailable_time, color="#333333", linewidth=1.0, linestyle=":")
        ax.grid(axis="y", color="#D9D9D9", linewidth=0.7)
        sns.despine(ax=ax)
    axes[0].annotate(
        "Restriction layer unavailable\n(not a zero-observation)",
        xy=(unavailable_time, 0),
        xytext=(18, 22),
        textcoords="offset points",
        ha="left",
        va="bottom",
        fontsize=9,
        color="#333333",
        arrowprops={"arrowstyle": "-", "color": "#555555", "linewidth": 0.8},
    )

    for ax in axes:
        ax.set_xlim(date_edges[0], date_edges[-1])
        ax.xaxis.set_major_locator(mdates.AutoDateLocator(minticks=6, maxticks=10))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    axes[0].tick_params(axis="x", labelbottom=False)
    for label, ax in zip("abc", axes):
        ax.text(
            -0.075,
            1.04,
            label,
            transform=ax.transAxes,
            fontsize=12,
            fontweight="bold",
            va="top",
        )

    fig.subplots_adjust(left=0.16, right=0.94, top=0.98, bottom=0.08)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
