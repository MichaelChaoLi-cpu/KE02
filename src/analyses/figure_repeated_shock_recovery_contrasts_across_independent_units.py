#!/usr/bin/env python3
"""Repeated-Shock Recovery Contrasts Across Independent Units.

Plan: Compare unit-level 2026-to-2016 restoration ratios and event-specific
mean MMI and PGA while separating motorway clusters from the same-asset
Yokoe case.
Framework: AnaSOP Sections 5.1-5.4, 6.3, 6.5, and 7. No pooled summary or
population inference is produced.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
SOURCE = (
    ROOT / "data/processed/kumamoto_repeated_shock_recovery_units_preprocessed.parquet"
)
OUT = (
    ROOT
    / "docs/process-records/assets/superseded/Figure_repeated_shock_recovery_contrasts_across_independent_units.png"
)

FASTER = "#2878B5"
SLOWER = "#D55E00"
MMI_2016 = "#7A7A7A"
MMI_2026 = "#6A3D9A"
PGA_2016 = "#7A7A7A"
PGA_2026 = "#008F8C"
GRID = "#D8D8D8"
TEXT = "#222222"

DISPLAY_LABELS = {
    "REGIME-E3A": "E3A Yatsushiro-minami–Tanoura",
    "REGIME-NORTH": "Northern E3/E77",
    "REGIME-SOUTH": "Southern E3",
    "REGIME-YOKOE": "Yokoe Bridge",
}
ORDER = ["REGIME-E3A", "REGIME-NORTH", "REGIME-SOUTH", "REGIME-YOKOE"]


def load_data() -> pd.DataFrame:
    df = pd.read_parquet(SOURCE).set_index("Recovery Unit ID").loc[ORDER].reset_index()
    assert len(df) == 4
    assert df["MMI Difference"].gt(0).all()
    assert set(df["Recovery Direction"]) == {"faster_in_2026", "slower_in_2026"}
    assert df["Analytical Role"].value_counts().to_dict() == {
        "motorway_descriptive_subset": 3,
        "same_asset_descriptive_case": 1,
    }
    return df


def main() -> None:
    df = load_data()
    y = np.arange(len(df))[::-1]
    labels = [DISPLAY_LABELS[value] for value in df["Recovery Unit ID"]]

    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 9.5,
            "axes.labelcolor": TEXT,
            "xtick.color": TEXT,
            "ytick.color": TEXT,
        }
    )
    fig, (ax_ratio, ax_mmi, ax_pga) = plt.subplots(
        1,
        3,
        figsize=(15.6, 5.4),
        sharey=True,
        gridspec_kw={"width_ratios": [1.22, 1.0, 1.0], "wspace": 0.14},
    )

    for ax in (ax_ratio, ax_mmi, ax_pga):
        ax.axhspan(0.5, 3.5, color="#F4F4F4", zorder=0)
        ax.axhspan(-0.5, 0.5, color="#EEF4F8", zorder=0)
        ax.axhline(0.5, color="#A9A9A9", linewidth=0.8, zorder=1)
        ax.set_ylim(-0.65, 3.85)
        ax.spines[["top", "right", "left"]].set_visible(False)
        ax.tick_params(axis="y", length=0)
        ax.grid(axis="x", color=GRID, linewidth=0.7, alpha=0.7, zorder=0)

    # Panel a: interval-valued restoration ratios.
    ax_ratio.axvline(1, color="#333333", linewidth=1.1, linestyle="--", zorder=1)
    for row_y, (_, row) in zip(y, df.iterrows(), strict=True):
        midpoint = row["Restoration Ratio Midpoint"]
        lower = row["Restoration Ratio Lower Bound"]
        upper = row["Restoration Ratio Upper Bound"]
        faster = row["Recovery Direction"] == "faster_in_2026"
        color = FASTER if faster else SLOWER
        marker = "D" if row["Analytical Role"] == "same_asset_descriptive_case" else "o"
        ax_ratio.plot(
            [lower, upper],
            [row_y, row_y],
            color=color,
            linewidth=2.2,
            solid_capstyle="round",
            zorder=3,
        )
        ax_ratio.scatter(
            midpoint,
            row_y,
            s=72 if marker == "D" else 62,
            marker=marker,
            color=color,
            edgecolor="white",
            linewidth=0.8,
            zorder=4,
        )
        alignment = "right" if midpoint > 1 else "left"
        offset = -8 if midpoint > 1 else 8
        ax_ratio.annotate(
            f"{midpoint:.3g}×",
            (midpoint, row_y),
            xytext=(offset, 0),
            textcoords="offset points",
            ha=alignment,
            va="center",
            fontsize=8.8,
            color=color,
            fontweight="semibold",
        )

    ax_ratio.set_xscale("log")
    ax_ratio.set_xlim(0.012, 9.0)
    ax_ratio.set_xticks([0.02, 0.05, 0.1, 0.2, 0.5, 1, 2, 5])
    ax_ratio.set_xticklabels(["0.02", "0.05", "0.1", "0.2", "0.5", "1", "2", "5"])
    ax_ratio.set_yticks(y, labels)
    ax_ratio.set_xlabel("2026 / 2016 restoration time (log scale)", labelpad=9)
    ax_ratio.text(
        0.02,
        3.70,
        "Faster in 2026",
        ha="left",
        va="center",
        fontsize=8.5,
        color=FASTER,
    )
    ax_ratio.text(
        5.0,
        3.70,
        "Slower in 2026",
        ha="right",
        va="center",
        fontsize=8.5,
        color=SLOWER,
    )
    ax_ratio.legend(
        handles=[
            Line2D([0], [0], marker="o", color="none", markerfacecolor="#666666", markeredgecolor="white", markersize=7, label="Motorway reopening cluster"),
            Line2D([0], [0], marker="D", color="none", markerfacecolor="#666666", markeredgecolor="white", markersize=7, label="Same-bridge case"),
        ],
        loc="upper center",
        bbox_to_anchor=(0.5, -0.20),
        ncol=2,
        frameon=False,
        fontsize=8.5,
        handletextpad=0.5,
        columnspacing=1.4,
    )

    # Panel b: paired event-specific MMI values.
    for row_y, (_, row) in zip(y, df.iterrows(), strict=True):
        mmi_2016 = row["2016 Mean MMI"]
        mmi_2026 = row["2026 Mean MMI"]
        ax_mmi.plot(
            [mmi_2016, mmi_2026],
            [row_y, row_y],
            color="#B7B7B7",
            linewidth=2.0,
            zorder=2,
        )
        ax_mmi.scatter(
            mmi_2016,
            row_y,
            s=50,
            color=MMI_2016,
            edgecolor="white",
            linewidth=0.7,
            zorder=3,
        )
        ax_mmi.scatter(
            mmi_2026,
            row_y,
            s=58,
            marker="s",
            color=MMI_2026,
            edgecolor="white",
            linewidth=0.7,
            zorder=3,
        )
        ax_mmi.annotate(
            f"+{row['MMI Difference']:.2f}",
            (mmi_2026, row_y),
            xytext=(7, 0),
            textcoords="offset points",
            ha="left",
            va="center",
            fontsize=8.5,
            color=MMI_2026,
        )

    ax_mmi.set_xlim(5.7, 9.45)
    ax_mmi.set_xticks([6, 7, 8, 9])
    ax_mmi.tick_params(axis="y", labelleft=False)
    ax_mmi.set_xlabel("Mean Modified Mercalli Intensity", labelpad=9)
    ax_mmi.legend(
        handles=[
            Line2D([0], [0], marker="o", color="none", markerfacecolor=MMI_2016, markersize=7, label="2016"),
            Line2D([0], [0], marker="s", color="none", markerfacecolor=MMI_2026, markersize=7, label="2026"),
        ],
        loc="upper center",
        bbox_to_anchor=(0.5, -0.20),
        ncol=2,
        frameon=False,
        fontsize=8.5,
        handletextpad=0.5,
        columnspacing=1.5,
    )

    # Panel c: PGA sensitivity. Unlike MMI, the event direction is not uniform.
    for row_y, (_, row) in zip(y, df.iterrows(), strict=True):
        pga_2016 = row["2016 PGA Mean (g)"]
        pga_2026 = row["2026 PGA Mean (g)"]
        ax_pga.plot(
            [pga_2016, pga_2026],
            [row_y, row_y],
            color="#B7B7B7",
            linewidth=2.0,
            zorder=2,
        )
        ax_pga.scatter(
            pga_2016,
            row_y,
            s=50,
            color=PGA_2016,
            edgecolor="white",
            linewidth=0.7,
            zorder=3,
        )
        ax_pga.scatter(
            pga_2026,
            row_y,
            s=58,
            marker="s",
            color=PGA_2026,
            edgecolor="white",
            linewidth=0.7,
            zorder=3,
        )
        ratio = row["PGA Ratio"]
        direction = "↑" if ratio > 1 else "↓"
        ax_pga.annotate(
            f"{direction} {ratio:.2f}×",
            (max(pga_2016, pga_2026), row_y),
            xytext=(7, 0),
            textcoords="offset points",
            ha="left",
            va="center",
            fontsize=8.5,
            color=PGA_2026,
        )

    ax_pga.set_xlim(0.08, 1.02)
    ax_pga.set_xticks([0.1, 0.3, 0.5, 0.7, 0.9])
    ax_pga.tick_params(axis="y", labelleft=False)
    ax_pga.set_xlabel("Mean peak ground acceleration (g)", labelpad=9)
    ax_pga.legend(
        handles=[
            Line2D([0], [0], marker="o", color="none", markerfacecolor=PGA_2016, markersize=7, label="2016"),
            Line2D([0], [0], marker="s", color="none", markerfacecolor=PGA_2026, markersize=7, label="2026"),
        ],
        loc="upper center",
        bbox_to_anchor=(0.5, -0.20),
        ncol=2,
        frameon=False,
        fontsize=8.5,
        handletextpad=0.5,
        columnspacing=1.5,
    )

    ax_ratio.text(-0.16, 1.02, "a", transform=ax_ratio.transAxes, fontsize=12, fontweight="bold", va="bottom")
    ax_mmi.text(-0.07, 1.02, "b", transform=ax_mmi.transAxes, fontsize=12, fontweight="bold", va="bottom")
    ax_pga.text(-0.07, 1.02, "c", transform=ax_pga.transAxes, fontsize=12, fontweight="bold", va="bottom")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.subplots_adjust(left=0.205, right=0.985, top=0.92, bottom=0.24)
    fig.savefig(OUT, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Saved: {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
