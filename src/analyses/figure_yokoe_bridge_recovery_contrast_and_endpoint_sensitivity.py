#!/usr/bin/env python3
"""Yokoe Bridge Recovery Contrast and Endpoint Sensitivity.

Plan: Show the official same-bridge recovery chronology and whether the
faster-2026 direction changes across two defensible 2016 endpoint definitions.
Framework: AnaSOP Sections 5.1-5.4, 6.3, 6.5, and 7. This is a descriptive
same-asset case and does not identify a causal reconstruction effect.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "data/processed/yokoe_bridge_endpoint_sensitivity_preprocessed.parquet"
MILESTONES = ROOT / "data/processed/yokoe_bridge_recovery_milestones_preprocessed.parquet"
OUT = (
    ROOT
    / "docs/process-records/assets/superseded/Figure_yokoe_bridge_recovery_contrast_and_endpoint_sensitivity.png"
)

COLOR_2016 = "#777777"
COLOR_2026 = "#2878B5"
FASTER = "#2878B5"
GRID = "#D8D8D8"
TEXT = "#222222"


def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    df = pd.read_parquet(SOURCE)
    milestones = pd.read_parquet(MILESTONES)
    assert len(df) == 2
    assert df["Recovery Unit ID"].eq("REGIME-YOKOE").all()
    assert df["Recovery Direction"].eq("faster_in_2026").all()
    assert df["Restoration Ratio Upper Bound"].lt(1).all()
    assert len(milestones) == 5
    assert set(milestones["Episode"]) == {2016, 2026}
    return df.set_index("Endpoint Role"), milestones


def interval_point(
    ax: plt.Axes,
    lower: float,
    upper: float,
    y: float,
    color: str,
    marker: str,
    size: float,
) -> float:
    midpoint = float(np.sqrt(lower * upper))
    ax.plot(
        [lower, upper],
        [y, y],
        color=color,
        linewidth=2.4,
        solid_capstyle="round",
        zorder=3,
    )
    ax.scatter(
        midpoint,
        y,
        s=size,
        marker=marker,
        color=color,
        edgecolor="white",
        linewidth=0.8,
        zorder=4,
    )
    return midpoint


def main() -> None:
    df, milestones = load_data()

    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 9.5,
            "axes.labelcolor": TEXT,
            "xtick.color": TEXT,
            "ytick.color": TEXT,
        }
    )
    fig, (ax_time, ax_ratio) = plt.subplots(
        1,
        2,
        figsize=(11.8, 4.9),
        gridspec_kw={"width_ratios": [1.05, 1.05], "wspace": 0.32},
    )

    for ax in (ax_time, ax_ratio):
        ax.spines[["top", "right", "left"]].set_visible(False)
        ax.tick_params(axis="y", length=0)
        ax.grid(axis="x", color=GRID, linewidth=0.7, alpha=0.75, zorder=0)

    # Panel a: official chronology in elapsed event time.
    y_time = {2016: 1, 2026: 0}
    colors = {2016: COLOR_2016, 2026: COLOR_2026}
    ax_time.scatter(0, 1, marker="|", s=150, color=COLOR_2016, zorder=4)
    ax_time.scatter(0, 0, marker="|", s=150, color=COLOR_2026, zorder=4)
    for episode, group in milestones.groupby("Episode"):
        group = group.sort_values("Elapsed Days Midpoint")
        y_value = y_time[int(episode)]
        color = colors[int(episode)]
        ax_time.plot(
            [0, group["Elapsed Days Upper Bound"].max()],
            [y_value, y_value],
            color=color,
            linewidth=2.2,
            alpha=0.55,
            zorder=2,
        )
        for _, row in group.iterrows():
            midpoint = float(row["Elapsed Days Midpoint"])
            ax_time.plot(
                [row["Elapsed Days Lower Bound"], row["Elapsed Days Upper Bound"]],
                [y_value, y_value],
                color=color,
                linewidth=4.0,
                solid_capstyle="round",
                zorder=3,
            )
            marker = (
                "X"
                if row["Milestone"] == "full_closure"
                else "D"
                if "reopening" in row["Milestone"]
                else "o"
            )
            ax_time.scatter(
                midpoint,
                y_value,
                s=66,
                marker=marker,
                color=color,
                edgecolor="white",
                linewidth=0.8,
                zorder=4,
            )
            day_label = (
                "≤0.04 d"
                if row["Milestone"] == "full_closure" and episode == 2016
                else f"{midpoint:,.0f} d"
                if midpoint >= 100
                else f"{midpoint:.1f} d"
            )
            if row["Milestone"] in {"full_closure", "light_vehicle_bypass"}:
                offset_y, va = 16, "bottom"
            else:
                offset_y, va = -14, "top"
            ax_time.annotate(
                f"{row['Milestone Label']}\n{day_label}",
                (midpoint, y_value),
                xytext=(0, offset_y),
                textcoords="offset points",
                ha="center",
                va=va,
                fontsize=8.2,
                color=color,
                fontweight="semibold",
            )
    ax_time.set_xscale("symlog", linthresh=1)
    ax_time.set_xlim(-0.15, 1500)
    ax_time.set_xticks([0, 1, 10, 100, 1000])
    ax_time.set_xticklabels(["0", "1", "10", "100", "1,000"])
    ax_time.set_yticks([1, 0], ["2016", "2026"])
    ax_time.set_ylim(-0.55, 1.55)
    ax_time.set_xlabel("Days since earthquake (symmetric log scale)", labelpad=9)

    # Panel b: sensitivity to the selected 2016 endpoint.
    ordered_roles = [
        "primary_full_bridge_reopening",
        "sensitivity_light_vehicle_access",
    ]
    endpoint_labels = {
        "primary_full_bridge_reopening": "Full bridge",
        "sensitivity_light_vehicle_access": "≤2-t bypass",
    }
    y_ratio = [1, 0]
    ax_ratio.axvline(1, color="#333333", linewidth=1.1, linestyle="--", zorder=1)
    for y, role in zip(y_ratio, ordered_roles, strict=True):
        row = df.loc[role]
        midpoint = interval_point(
            ax_ratio,
            float(row["Restoration Ratio Lower Bound"]),
            float(row["Restoration Ratio Upper Bound"]),
            y,
            FASTER,
            "D" if role == "primary_full_bridge_reopening" else "o",
            72,
        )
        ax_ratio.annotate(
            f"{endpoint_labels[role]}  {midpoint:.3g}×",
            (midpoint, y),
            xytext=(8, 0),
            textcoords="offset points",
            ha="left",
            va="center",
            fontsize=9,
            color=FASTER,
            fontweight="bold",
        )
    ax_ratio.set_xscale("log")
    ax_ratio.set_xlim(0.012, 1.35)
    ax_ratio.set_xticks([0.02, 0.05, 0.1, 0.2, 0.5, 1])
    ax_ratio.set_xticklabels(["0.02", "0.05", "0.1", "0.2", "0.5", "1"])
    ax_ratio.set_yticks(y_ratio, ["", ""])
    ax_ratio.set_ylim(-0.55, 1.55)
    ax_ratio.set_xlabel("2026 / 2016 restoration time (log scale)", labelpad=9)
    ax_ratio.text(
        0.02,
        1.42,
        "Faster in 2026",
        color=FASTER,
        ha="left",
        va="center",
        fontsize=8.7,
    )

    ax_time.text(-0.13, 1.03, "a", transform=ax_time.transAxes, fontsize=12, fontweight="bold", va="bottom")
    ax_ratio.text(-0.13, 1.03, "b", transform=ax_ratio.transAxes, fontsize=12, fontweight="bold", va="bottom")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.subplots_adjust(left=0.12, right=0.985, top=0.90, bottom=0.22)
    fig.savefig(OUT, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Saved: {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
