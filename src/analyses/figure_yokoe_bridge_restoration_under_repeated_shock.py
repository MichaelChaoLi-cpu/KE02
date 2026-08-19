#!/usr/bin/env python3
"""Yokoe Bridge Restoration Under Repeated Shock.

Plan: Compare event-to-restoration time for the same bridge and test whether the
faster-2026 direction survives the admissible 2016 endpoint definition.
Framework: AnaSOP Sections 5.2 and 5.5, Section 6.3, and Analytical Workflow
step 4. Ratio intervals preserve timing precision; the figure supports a
directional same-asset contrast, not a causal reconstruction effect.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, LogLocator, NullFormatter
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "data/processed/yokoe_matched_endpoint_preprocessed.parquet"
OUT = (
    ROOT
    / "data/results/figures"
    / "Figure_yokoe_bridge_restoration_under_repeated_shock.png"
)

PRIMARY_COLOR = "#2563A8"
SENSITIVITY_COLOR = "#D97706"
RESTORED_2026_COLOR = "#25875A"
REFERENCE_COLOR = "#59636A"
GRID_COLOR = "#D8DEE2"
TEXT_COLOR = "#263238"


def log_number(value: float, _: int) -> str:
    if value >= 1000:
        return f"{value:,.0f}"
    if value >= 1:
        return f"{value:g}"
    return f"{value:.2g}"


def interval_error(lower: float, upper: float, midpoint: float) -> np.ndarray:
    return np.asarray([[midpoint - lower], [upper - midpoint]], dtype=float)


def plot_restoration_time(axis: plt.Axes, data: pd.DataFrame) -> None:
    primary = data.loc[data["Endpoint Role"].eq("primary matched endpoint")].iloc[0]
    sensitivity = data.loc[
        data["Endpoint Role"].eq("2016 early-access sensitivity")
    ].iloc[0]

    rows = [
        {
            "label": "2016 full reopening\n(primary endpoint)",
            "lower": float(primary["Restoration Hours Lower Bound 2016"]) / 24,
            "upper": float(primary["Restoration Hours Upper Bound 2016"]) / 24,
            "color": PRIMARY_COLOR,
            "marker": "o",
            "format": ".1f",
        },
        {
            "label": "2016 ≤2-tonne access\n(sensitivity endpoint)",
            "lower": float(sensitivity["Restoration Hours Lower Bound 2016"]) / 24,
            "upper": float(sensitivity["Restoration Hours Upper Bound 2016"]) / 24,
            "color": SENSITIVITY_COLOR,
            "marker": "^",
            "format": ".1f",
        },
        {
            "label": "2026 full reopening",
            "lower": float(primary["Restoration Hours Lower Bound 2026"]) / 24,
            "upper": float(primary["Restoration Hours Upper Bound 2026"]) / 24,
            "color": RESTORED_2026_COLOR,
            "marker": "s",
            "format": ".2f",
        },
    ]
    y = np.arange(len(rows))[::-1]
    for position, row in zip(y, rows, strict=True):
        midpoint = np.sqrt(row["lower"] * row["upper"])
        axis.errorbar(
            midpoint,
            position,
            xerr=interval_error(row["lower"], row["upper"], midpoint),
            fmt=row["marker"],
            markersize=9.0,
            markerfacecolor=row["color"],
            markeredgecolor="white",
            markeredgewidth=1.0,
            ecolor=row["color"],
            elinewidth=2.2,
            capsize=5,
            capthick=1.5,
            zorder=4,
        )
        axis.annotate(
            f"{midpoint:{row['format']}} days",
            xy=(midpoint, position),
            xytext=(11, 0),
            textcoords="offset points",
            ha="left",
            va="center",
            fontsize=9.0,
            fontweight="bold",
            color=row["color"],
        )

    axis.text(
        0,
        1.03,
        "Event-to-restoration time",
        transform=axis.transAxes,
        ha="left",
        va="bottom",
        fontsize=11.2,
        fontweight="bold",
        color=TEXT_COLOR,
    )
    axis.text(
        1,
        1.03,
        "same physical bridge",
        transform=axis.transAxes,
        ha="right",
        va="bottom",
        fontsize=9.0,
        color="#66727A",
    )
    axis.set_xscale("log")
    axis.set_xlim(10, 1650)
    axis.set_ylim(-0.65, 2.65)
    axis.set_yticks(y)
    axis.set_yticklabels([row["label"] for row in rows], fontsize=9.2)
    axis.set_xlabel("Days since earthquake origin (log scale)", fontsize=10)
    axis.xaxis.set_major_locator(LogLocator(base=10, subs=(1.0, 2.0, 5.0)))
    axis.xaxis.set_major_formatter(FuncFormatter(log_number))
    axis.xaxis.set_minor_formatter(NullFormatter())
    axis.grid(axis="x", which="major", color=GRID_COLOR, linewidth=0.6, linestyle=(0, (3, 3)))
    axis.tick_params(axis="x", labelsize=8.6, colors="#4B5962")
    axis.tick_params(axis="y", length=0, pad=7, colors=TEXT_COLOR)
    for side in ("top", "right", "left"):
        axis.spines[side].set_visible(False)
    axis.spines["bottom"].set_color("#69757D")


def plot_ratio_sensitivity(axis: plt.Axes, data: pd.DataFrame) -> None:
    ordered = data.set_index("Endpoint Role").loc[
        ["primary matched endpoint", "2016 early-access sensitivity"]
    ]
    labels = [
        "Full reopening\n(primary matched endpoint)",
        "2016 early access\n(sensitivity endpoint)",
    ]
    colors = [PRIMARY_COLOR, SENSITIVITY_COLOR]
    markers = ["o", "^"]
    y = np.arange(len(ordered))[::-1]

    axis.axvspan(0.01, 1.0, color="#E6F2EC", alpha=0.75, zorder=0)
    axis.axvline(1.0, color=REFERENCE_COLOR, linewidth=1.2, linestyle=(0, (4, 3)), zorder=2)
    axis.text(
        0.025,
        0.09,
        "faster in 2026",
        transform=axis.get_xaxis_transform(),
        fontsize=8.3,
        color="#267154",
        ha="left",
        va="bottom",
    )
    axis.text(
        1.0,
        0.96,
        "no change",
        transform=axis.get_xaxis_transform(),
        fontsize=8.1,
        color=REFERENCE_COLOR,
        ha="right",
        va="top",
    )

    for position, (_, row), color, marker in zip(
        y, ordered.iterrows(), colors, markers, strict=True
    ):
        lower = float(row["Restoration Ratio Lower Bound (2026/2016)"])
        upper = float(row["Restoration Ratio Upper Bound (2026/2016)"])
        midpoint = np.sqrt(lower * upper)
        axis.errorbar(
            midpoint,
            position,
            xerr=interval_error(lower, upper, midpoint),
            fmt=marker,
            markersize=9.2,
            markerfacecolor=color,
            markeredgecolor="white",
            markeredgewidth=1.0,
            ecolor=color,
            elinewidth=2.4,
            capsize=5,
            capthick=1.5,
            zorder=4,
        )
        axis.annotate(
            f"{lower:.5f}–{upper:.5f}",
            xy=(midpoint, position),
            xytext=(11, 0),
            textcoords="offset points",
            ha="left",
            va="center",
            fontsize=8.8,
            fontweight="bold",
            color=color,
        )

    first = ordered.iloc[0]
    mmi_difference = float(first["Mean MMI 2026"] - first["Mean MMI 2016"])
    pga_ratio = float(first["PGA Ratio (2026/2016)"])
    axis.text(
        0,
        1.03,
        "Endpoint sensitivity",
        transform=axis.transAxes,
        ha="left",
        va="bottom",
        fontsize=11.2,
        fontweight="bold",
        color=TEXT_COLOR,
    )
    axis.text(
        1,
        1.03,
        f"2026 stronger: MMI +{mmi_difference:.2f}; PGA ×{pga_ratio:.2f}",
        transform=axis.transAxes,
        ha="right",
        va="bottom",
        fontsize=9.0,
        color="#66727A",
    )
    axis.set_xscale("log")
    axis.set_xlim(0.015, 1.25)
    axis.set_ylim(-0.65, 1.65)
    axis.set_yticks(y)
    axis.set_yticklabels(labels, fontsize=9.2)
    axis.set_xlabel("2026 / 2016 restoration-time ratio (log scale)", fontsize=10)
    axis.xaxis.set_major_locator(LogLocator(base=10, subs=(1.0, 2.0, 5.0)))
    axis.xaxis.set_major_formatter(FuncFormatter(log_number))
    axis.xaxis.set_minor_formatter(NullFormatter())
    axis.grid(axis="x", which="major", color=GRID_COLOR, linewidth=0.6, linestyle=(0, (3, 3)))
    axis.tick_params(axis="x", labelsize=8.6, colors="#4B5962")
    axis.tick_params(axis="y", length=0, pad=7, colors=TEXT_COLOR)
    for side in ("top", "right", "left"):
        axis.spines[side].set_visible(False)
    axis.spines["bottom"].set_color("#69757D")


def main() -> None:
    data = pd.read_parquet(SOURCE)
    if len(data) != 2 or data["Endpoint Definition"].nunique() != 2:
        raise RuntimeError("The Yokoe endpoint layer must contain two definitions.")
    if not data["Faster in 2026"].all():
        raise RuntimeError("The endpoint direction is not robustly faster in 2026.")
    if not data["Hazard Direction"].eq("2026 stronger under both MMI and PGA").all():
        raise RuntimeError("The Yokoe hazard direction does not match the framework.")

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
        figsize=(15.2, 5.7),
        gridspec_kw={"width_ratios": (1.0, 1.16), "wspace": 0.36},
    )
    plot_restoration_time(axes[0], data)
    plot_ratio_sensitivity(axes[1], data)

    for label, axis in zip("ab", axes, strict=True):
        axis.text(
            -0.115,
            1.06,
            label,
            transform=axis.transAxes,
            fontsize=13,
            fontweight="bold",
            color="#1F2933",
            va="top",
            ha="left",
            clip_on=False,
        )

    fig.subplots_adjust(left=0.145, right=0.975, top=0.88, bottom=0.18)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
