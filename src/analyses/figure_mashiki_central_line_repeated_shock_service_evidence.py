#!/usr/bin/env python3
"""Mashiki Central Line Repeated-Shock Service Evidence.

Plan: Preserve the 2016 official restriction observations and show the 2026
probe-passage trajectory, observation coverage, and first near-full passage
bound without treating the two measurement systems as equivalent outcomes.
Framework: AnaSOP Sections 5.2 and 5.5, Section 6.2, and Analytical Workflow
step 3. The 2026 series describes observed service presence, not reopening time,
normal traffic, full capacity, or an undamaged road.
"""
from __future__ import annotations

import math
import re
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
SOURCE = (
    ROOT
    / "data/processed"
    / "mashiki_repeated_shock_event_state_preprocessed.parquet"
)
OUT = (
    ROOT
    / "data/results/figures"
    / "Figure_mashiki_central_line_repeated_shock_service_evidence.png"
)

FULL_CLOSURE_COLOR = "#B33A3A"
ONE_SIDE_COLOR = "#D97706"
PASSAGE_COLOR = "#197A6A"
TRACE_COLOR = "#C8D2D8"
UNAVAILABLE_COLOR = "#7B858C"
NO_PASSAGE_COLOR = "#B33A3A"
TEXT_COLOR = "#263238"
GRID_COLOR = "#D8DEE2"
NEAR_FULL_THRESHOLD = 0.80


SUBSEGMENT_LABELS = {
    "Mashiki Soryo-Miyazono": "Soryo–Miyazono",
    "Kiyama intersection-Terasako intersection": "Kiyama–Terasako",
    "Kiyama intersection-Mamizu Bridge": "Kiyama–Mamizu Bridge",
}


def observed_day_bounds(bound_text: str) -> tuple[int, int, int | None]:
    numbers = [int(value) for value in re.findall(r"\+(\d+)", bound_text)]
    if "release observed" in bound_text:
        if len(numbers) < 2:
            raise RuntimeError(f"Cannot parse 2016 observation bound: {bound_text}")
        return 0, numbers[0], numbers[1]
    if len(numbers) < 2:
        raise RuntimeError(f"Cannot parse 2016 observation bound: {bound_text}")
    return numbers[0], numbers[1], None


def plot_2016(axis: plt.Axes, records: pd.DataFrame) -> None:
    records = records.copy().reset_index(drop=True)
    records["Display Label"] = records["Subsegment"].map(SUBSEGMENT_LABELS)
    if records["Display Label"].isna().any():
        raise RuntimeError("A 2016 Mashiki subsegment lacks a display label.")

    y_positions = np.arange(len(records))[::-1]
    for y, (_, row) in zip(y_positions, records.iterrows(), strict=True):
        start, end, release = observed_day_bounds(str(row["Event-Time Bound"]))
        is_full = row["Observation State"] == "official full closure"
        color = FULL_CLOSURE_COLOR if is_full else ONE_SIDE_COLOR
        axis.hlines(y, start, end, color=color, linewidth=8.0, zorder=3)
        axis.scatter(
            [start, end],
            [y, y],
            s=35,
            color=color,
            edgecolor="white",
            linewidth=0.8,
            zorder=4,
        )
        if release is not None:
            axis.scatter(
                release,
                y,
                s=49,
                marker="D",
                color=PASSAGE_COLOR,
                edgecolor="white",
                linewidth=0.8,
                zorder=5,
            )
            axis.annotate(
                "release observed",
                xy=(release, y),
                xytext=(10, 12),
                textcoords="offset points",
                fontsize=8.4,
                color=PASSAGE_COLOR,
                arrowprops={"arrowstyle": "-", "color": PASSAGE_COLOR, "lw": 0.7},
            )

    axis.axvline(0, color="#4E5961", linewidth=0.9, linestyle=(0, (3, 3)), zorder=1)
    axis.text(
        0,
        1.02,
        "2016 official restriction observations",
        transform=axis.transAxes,
        ha="left",
        va="bottom",
        fontsize=11.5,
        fontweight="bold",
        color=TEXT_COLOR,
    )
    axis.text(
        0.98,
        0.95,
        "calendar-day precision",
        transform=axis.transAxes,
        ha="right",
        va="top",
        fontsize=8.7,
        color="#66727A",
        bbox={"boxstyle": "round,pad=0.22", "fc": "white", "ec": "none"},
    )
    axis.set_xlim(-5, 138)
    axis.set_ylim(-0.65, len(records) - 0.35)
    axis.set_yticks(y_positions)
    axis.set_yticklabels(records["Display Label"], fontsize=9.3)
    axis.set_xlabel("Days since the 2016 mainshock", fontsize=10)
    axis.set_ylabel("")
    axis.grid(axis="x", color=GRID_COLOR, linewidth=0.6, linestyle=(0, (2.5, 3.5)))
    axis.tick_params(axis="x", labelsize=8.8, colors="#4B5962")
    axis.tick_params(axis="y", length=0, pad=6, colors=TEXT_COLOR)
    for side in ("top", "right", "left"):
        axis.spines[side].set_visible(False)
    axis.spines["bottom"].set_color("#69757D")

    handles = [
        Line2D([0], [0], color=FULL_CLOSURE_COLOR, lw=7, label="Full closure observed"),
        Line2D([0], [0], color=ONE_SIDE_COLOR, lw=7, label="One-side closure observed"),
        Line2D(
            [0],
            [0],
            marker="D",
            color="none",
            markerfacecolor=PASSAGE_COLOR,
            markeredgecolor="white",
            markersize=6.5,
            label="Release observed",
        ),
    ]
    axis.legend(
        handles=handles,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.22),
        ncol=3,
        frameon=False,
        fontsize=8.3,
        handlelength=2.0,
        columnspacing=1.2,
    )


def plot_2026(axis: plt.Axes, records: pd.DataFrame) -> None:
    records = records.sort_values("Elapsed Hours Since Event").copy()
    available = records["Passage Layer Available"].fillna(False).astype(bool)
    passage = records["Observed Corridor Passage"].fillna(False).astype(bool)
    hours = records["Elapsed Hours Since Event"].astype(float).to_numpy()
    coverage = records["Longitudinal Coverage Proxy"].astype(float).to_numpy()
    traces = records["Unique Corridor Traces"].astype(float).to_numpy()

    coverage_line = coverage.copy()
    coverage_line[~available.to_numpy()] = np.nan

    trace_axis = axis.twinx()
    bar_width = np.full(len(records), 7.0)
    trace_axis.bar(
        hours[available],
        traces[available],
        width=bar_width[available],
        color=TRACE_COLOR,
        edgecolor="none",
        alpha=0.72,
        zorder=1,
    )
    trace_axis.set_ylim(0, max(25, math.ceil(np.nanmax(traces) / 5) * 5))
    trace_axis.set_ylabel("Unique corridor traces", fontsize=9.5, color="#69757D")
    trace_axis.tick_params(axis="y", labelsize=8.3, colors="#69757D", length=0)
    trace_axis.spines["top"].set_visible(False)
    trace_axis.spines["right"].set_color("#AAB2B8")

    axis.plot(
        hours,
        coverage_line,
        color=PASSAGE_COLOR,
        linewidth=1.65,
        marker="o",
        markersize=5.8,
        markerfacecolor=PASSAGE_COLOR,
        markeredgecolor="white",
        markeredgewidth=0.75,
        zorder=4,
    )
    no_passage = available & ~passage
    axis.scatter(
        hours[no_passage],
        coverage[no_passage],
        s=48,
        facecolor="white",
        edgecolor=NO_PASSAGE_COLOR,
        linewidth=1.4,
        zorder=6,
    )
    axis.scatter(
        hours[~available],
        np.full((~available).sum(), -0.075),
        marker="x",
        s=35,
        color=UNAVAILABLE_COLOR,
        linewidth=1.2,
        clip_on=False,
        zorder=6,
    )

    axis.axhline(
        NEAR_FULL_THRESHOLD,
        color="#8A949B",
        linewidth=0.9,
        linestyle=(0, (4, 3)),
        zorder=2,
    )
    axis.text(
        500,
        NEAR_FULL_THRESHOLD + 0.025,
        "Near-full threshold (0.80)",
        ha="right",
        va="bottom",
        fontsize=8.4,
        color="#657078",
    )

    near_full = available & passage & records["Longitudinal Coverage Proxy"].ge(
        NEAR_FULL_THRESHOLD
    )
    first_near = float(records.loc[near_full, "Elapsed Hours Since Event"].min())
    axis.axvline(
        first_near,
        color=PASSAGE_COLOR,
        linewidth=1.0,
        linestyle=(0, (3, 3)),
        zorder=2,
    )
    axis.annotate(
        f"First observed near-full passage\n≤{first_near:.2f} h",
        xy=(first_near, 0.99),
        xytext=(0.19, 0.68),
        textcoords=axis.transAxes,
        fontsize=9.1,
        color="#125F53",
        ha="left",
        va="center",
        arrowprops={"arrowstyle": "-", "color": PASSAGE_COLOR, "lw": 0.8},
        bbox={
            "boxstyle": "round,pad=0.30",
            "fc": "white",
            "ec": "#C9D8D4",
            "alpha": 1.0,
        },
        zorder=7,
    )

    available_count = int(available.sum())
    passage_count = int((available & passage).sum())
    near_count = int(near_full.sum())
    axis.text(
        0,
        1.02,
        "2026 probe-passage observations",
        transform=axis.transAxes,
        ha="left",
        va="bottom",
        fontsize=11.5,
        fontweight="bold",
        color=TEXT_COLOR,
    )
    axis.text(
        1,
        1.02,
        f"{passage_count}/{available_count} passage; "
        f"{near_count}/{available_count} near-full",
        transform=axis.transAxes,
        ha="right",
        va="bottom",
        fontsize=9.0,
        color="#66727A",
    )
    axis.set_xlim(0, 510)
    axis.set_ylim(-0.10, 1.08)
    axis.set_xlabel("Hours since the 2026 earthquake", fontsize=10)
    axis.set_ylabel("Longitudinal coverage proxy", fontsize=9.5)
    axis.set_yticks(np.linspace(0, 1, 6))
    axis.set_yticklabels([f"{value:.1f}" for value in np.linspace(0, 1, 6)])
    axis.grid(axis="both", color=GRID_COLOR, linewidth=0.55, linestyle=(0, (2.5, 3.5)))
    axis.tick_params(axis="both", labelsize=8.6, colors="#4B5962")
    for side in ("top", "right"):
        axis.spines[side].set_visible(False)
    axis.spines["left"].set_color("#69757D")
    axis.spines["bottom"].set_color("#69757D")

    handles = [
        Line2D(
            [0],
            [0],
            color=PASSAGE_COLOR,
            marker="o",
            markerfacecolor=PASSAGE_COLOR,
            markeredgecolor="white",
            lw=1.5,
            label="Observed coverage",
        ),
        Line2D(
            [0],
            [0],
            marker="o",
            markerfacecolor="white",
            markeredgecolor=NO_PASSAGE_COLOR,
            color="none",
            label="No passage observed",
        ),
        Line2D(
            [0],
            [0],
            marker="x",
            color=UNAVAILABLE_COLOR,
            lw=0,
            label="Passage layer unavailable",
        ),
        Line2D([0], [0], color=TRACE_COLOR, lw=6, label="Unique trace count"),
    ]
    axis.legend(
        handles=handles,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.19),
        ncol=2,
        frameon=False,
        fontsize=8.2,
        handlelength=2.2,
        columnspacing=1.1,
    )


def main() -> None:
    data = pd.read_parquet(SOURCE)
    if set(data["Event"]) != {"2016 mainshock", "2026 earthquake"}:
        raise RuntimeError("Unexpected event coverage in the Mashiki event-state layer.")
    records_2016 = data.loc[data["Event"].eq("2016 mainshock")]
    records_2026 = data.loc[data["Event"].eq("2026 earthquake")]
    if len(records_2016) != 3 or len(records_2026) != 25:
        raise RuntimeError("Unexpected Mashiki event-state dimensions.")

    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "axes.facecolor": "white",
            "figure.facecolor": "white",
            "savefig.facecolor": "white",
        }
    )
    fig, axes = plt.subplots(
        1,
        2,
        figsize=(16.2, 6.5),
        gridspec_kw={"width_ratios": (0.94, 1.38), "wspace": 0.34},
    )
    plot_2016(axes[0], records_2016)
    plot_2026(axes[1], records_2026)

    for label, axis in zip("ab", axes, strict=True):
        axis.text(
            -0.105,
            1.055,
            label,
            transform=axis.transAxes,
            fontsize=13,
            fontweight="bold",
            color="#1F2933",
            va="top",
            ha="left",
            clip_on=False,
        )

    fig.subplots_adjust(left=0.105, right=0.945, top=0.89, bottom=0.22)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
