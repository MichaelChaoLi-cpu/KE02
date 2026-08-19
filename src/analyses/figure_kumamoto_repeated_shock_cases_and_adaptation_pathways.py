#!/usr/bin/env python3
"""Kumamoto Repeated-Shock Cases and Adaptation Pathways.

Plan: Locate the two core cases and show the common sequence from documented
2016 failure through completed adaptation to the 2026 stress test and observed
performance.
Framework: AnaSOP Sections 5.1-5.4, 6.1, and Analytical Workflow step 1.
The figure establishes traceable location and temporal order; it does not
present the two cases as a natural experiment or a pooled comparison.
"""
from __future__ import annotations

import math
import textwrap
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter, MultipleLocator
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data/processed"
OUT = (
    ROOT
    / "data/results/figures"
    / "Figure_kumamoto_repeated_shock_cases_and_adaptation_pathways.png"
)

ADMIN = PROCESSED / "kumamoto_administrative_areas_cartographic_preprocessed.parquet"
EVIDENCE = PROCESSED / "repeated_shock_two_case_evidence_preprocessed.parquet"
CASE_GEOMETRIES = PROCESSED / "repeated_shock_case_geometries_preprocessed.parquet"

GEOGRAPHIC_CRS = "EPSG:4326"
CAPACITY_COLOR = "#D97706"
STRUCTURAL_COLOR = "#2563A8"
FAILURE_COLOR = "#B33A3A"
SHOCK_COLOR = "#424B54"
PERFORMANCE_COLOR = "#25875A"
LAND_COLOR = "#F2F4F5"
BOUNDARY_COLOR = "#AAB2B8"
TEXT_COLOR = "#263238"


def wrapped(text: str, width: int = 18) -> str:
    return "\n".join(textwrap.wrap(text, width=width, break_long_words=False))


def degree_formatter(suffix: str) -> FuncFormatter:
    return FuncFormatter(lambda value, _: f"{value:.2f}°{suffix}")


def load_geometries() -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame, gpd.GeoDataFrame]:
    admin = gpd.read_parquet(ADMIN).set_geometry("Geometry").to_crs(GEOGRAPHIC_CRS)
    cases = (
        gpd.read_parquet(CASE_GEOMETRIES)
        .set_geometry("Geometry")
        .to_crs(GEOGRAPHIC_CRS)
    )
    if (
        len(cases) != 2
        or set(cases["Case ID"]) != {"MASHIKI-CENTRAL", "YOKOE-BRIDGE"}
        or not cases["Geometry Gate"].all()
    ):
        raise RuntimeError("The final two-case geometry contract is invalid.")
    mashiki = cases.loc[cases["Case ID"].eq("MASHIKI-CENTRAL")].copy()
    yokoe = cases.loc[cases["Case ID"].eq("YOKOE-BRIDGE")].copy()
    return admin, mashiki, yokoe


def plot_map(
    axis: plt.Axes,
    admin: gpd.GeoDataFrame,
    mashiki: gpd.GeoDataFrame,
    yokoe: gpd.GeoDataFrame,
) -> None:
    admin.plot(
        ax=axis,
        facecolor=LAND_COLOR,
        edgecolor=BOUNDARY_COLOR,
        linewidth=0.42,
        zorder=1,
    )

    admin.loc[admin["Municipality Label"].eq("益城町")].plot(
        ax=axis,
        facecolor="#FDE8C4",
        edgecolor=CAPACITY_COLOR,
        linewidth=0.8,
        zorder=2,
    )
    admin.loc[admin["Municipality Label"].eq("八代市")].plot(
        ax=axis,
        facecolor="#DCEAF7",
        edgecolor=STRUCTURAL_COLOR,
        linewidth=0.8,
        zorder=2,
    )
    mashiki.plot(
        ax=axis,
        facecolor=CAPACITY_COLOR,
        edgecolor="#8A4B03",
        linewidth=1.2,
        alpha=0.92,
        zorder=5,
    )
    yokoe.plot(
        ax=axis,
        color=STRUCTURAL_COLOR,
        linewidth=3.0,
        zorder=6,
    )

    mashiki_centroid = mashiki.to_crs(6670).geometry.union_all().centroid
    mashiki_point = gpd.GeoSeries([mashiki_centroid], crs=6670).to_crs(4326).iloc[0]
    yokoe_centroid = yokoe.to_crs(6670).geometry.union_all().centroid
    yokoe_point = gpd.GeoSeries([yokoe_centroid], crs=6670).to_crs(4326).iloc[0]

    axis.scatter(
        [mashiki_point.x],
        [mashiki_point.y],
        s=54,
        marker="o",
        color=CAPACITY_COLOR,
        edgecolor="white",
        linewidth=0.9,
        zorder=7,
    )
    axis.scatter(
        [yokoe_point.x],
        [yokoe_point.y],
        s=57,
        marker="D",
        color=STRUCTURAL_COLOR,
        edgecolor="white",
        linewidth=0.9,
        zorder=7,
    )
    axis.annotate(
        "Mashiki Central Line",
        xy=(mashiki_point.x, mashiki_point.y),
        xytext=(18, 18),
        textcoords="offset points",
        fontsize=8.4,
        fontweight="semibold",
        color="#754006",
        arrowprops={"arrowstyle": "-", "color": CAPACITY_COLOR, "lw": 0.9},
        bbox={"boxstyle": "round,pad=0.22", "fc": "white", "ec": "none", "alpha": 0.9},
        zorder=8,
    )
    axis.annotate(
        "Yokoe Bridge",
        xy=(yokoe_point.x, yokoe_point.y),
        xytext=(-75, -25),
        textcoords="offset points",
        fontsize=8.4,
        fontweight="semibold",
        color="#194D78",
        arrowprops={"arrowstyle": "-", "color": STRUCTURAL_COLOR, "lw": 0.9},
        bbox={"boxstyle": "round,pad=0.22", "fc": "white", "ec": "none", "alpha": 0.9},
        zorder=8,
    )

    west, south, east, north = admin.total_bounds
    longitude_padding = 0.035 * (east - west)
    latitude_padding = 0.035 * (north - south)
    axis.set_xlim(west - longitude_padding, east + longitude_padding)
    axis.set_ylim(south - latitude_padding, north + latitude_padding)
    axis.set_aspect("equal")
    axis.xaxis.set_major_locator(MultipleLocator(0.25))
    axis.yaxis.set_major_locator(MultipleLocator(0.25))
    axis.xaxis.set_major_formatter(degree_formatter("E"))
    axis.yaxis.set_major_formatter(degree_formatter("N"))
    axis.grid(
        True,
        color="#7E8991",
        linewidth=0.45,
        linestyle=(0, (2.5, 3.5)),
        alpha=0.48,
        zorder=0,
    )
    axis.tick_params(axis="both", labelsize=7.2, colors="#44515A", length=0)
    for spine in axis.spines.values():
        spine.set_visible(True)
        spine.set_color("#59636A")
        spine.set_linewidth(0.8)

    legend = [
        Line2D(
            [0],
            [0],
            marker="o",
            color="none",
            markerfacecolor=CAPACITY_COLOR,
            markeredgecolor="white",
            markersize=7.5,
            label="Corridor capacity expansion",
        ),
        Line2D(
            [0],
            [0],
            marker="D",
            color="none",
            markerfacecolor=STRUCTURAL_COLOR,
            markeredgecolor="white",
            markersize=7.0,
            label="Structural reconstruction",
        ),
    ]
    axis.legend(
        handles=legend,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.105),
        ncol=2,
        frameon=False,
        fontsize=7.7,
        handletextpad=0.45,
        columnspacing=1.15,
        borderaxespad=0,
    )


def plot_pathway_timeline(
    axis: plt.Axes,
    case_label: str,
    pathway_label: str,
    pathway_color: str,
    descriptions: list[str],
    dates: list[str],
    show_stage_labels: bool,
) -> None:
    x = np.arange(4, dtype=float)
    colors = [FAILURE_COLOR, pathway_color, SHOCK_COLOR, PERFORMANCE_COLOR]

    axis.annotate(
        "",
        xy=(3.13, 0.50),
        xytext=(-0.10, 0.50),
        arrowprops={"arrowstyle": "-|>", "lw": 1.6, "color": "#98A1A8"},
        zorder=1,
    )
    for position, color in zip(x, colors, strict=True):
        axis.scatter(
            position,
            0.50,
            s=82,
            color=color,
            edgecolor="white",
            linewidth=1.0,
            zorder=3,
        )

    for position, description, date in zip(x, descriptions, dates, strict=True):
        axis.text(
            position,
            0.72,
            wrapped(description, 18),
            ha="center",
            va="bottom",
            fontsize=8.1,
            color=TEXT_COLOR,
            linespacing=1.15,
        )
        axis.text(
            position,
            0.30,
            date,
            ha="center",
            va="top",
            fontsize=7.5,
            color="#5A646B",
            linespacing=1.15,
        )

    axis.text(
        0.0,
        0.98,
        case_label,
        transform=axis.transAxes,
        ha="left",
        va="top",
        fontsize=10.2,
        fontweight="bold",
        color=TEXT_COLOR,
    )
    axis.text(
        1.0,
        0.98,
        pathway_label,
        transform=axis.transAxes,
        ha="right",
        va="top",
        fontsize=8.2,
        fontweight="semibold",
        color=pathway_color,
    )

    axis.set_xlim(-0.28, 3.28)
    axis.set_ylim(0.05, 1.04)
    axis.set_yticks([])
    if show_stage_labels:
        axis.set_xticks(x)
        axis.set_xticklabels(
            ["2016 failure", "Adaptation", "2026 shock", "Observed performance"],
            fontsize=7.7,
            color="#3E4A52",
        )
        axis.tick_params(axis="x", length=0, pad=8)
    else:
        axis.set_xticks([])
        axis.tick_params(axis="x", labelbottom=False)
    for side in ("left", "right", "top", "bottom"):
        axis.spines[side].set_visible(False)


def main() -> None:
    evidence = pd.read_parquet(EVIDENCE)
    if set(evidence["Case ID"]) != {"MASHIKI-CENTRAL", "YOKOE-BRIDGE"}:
        raise RuntimeError("The two-case evidence layer does not contain the declared core.")
    if not evidence["Core Case"].all():
        raise RuntimeError("A declared case is not marked as a core case.")

    admin, mashiki, yokoe = load_geometries()

    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "axes.facecolor": "white",
            "figure.facecolor": "white",
            "savefig.facecolor": "white",
        }
    )
    fig = plt.figure(figsize=(14.8, 7.1))
    grid = fig.add_gridspec(
        2,
        2,
        width_ratios=(1.02, 1.58),
        height_ratios=(1, 1),
        wspace=0.18,
        hspace=0.20,
    )
    map_axis = fig.add_subplot(grid[:, 0])
    mashiki_axis = fig.add_subplot(grid[0, 1])
    yokoe_axis = fig.add_subplot(grid[1, 1], sharex=mashiki_axis)

    plot_map(map_axis, admin, mashiki, yokoe)
    plot_pathway_timeline(
        mashiki_axis,
        case_label="Mashiki Central Line",
        pathway_label="Capacity pathway",
        pathway_color=CAPACITY_COLOR,
        descriptions=[
            "Official corridor restrictions",
            "Four-laning fully opened",
            "Second earthquake",
            "Near-full passage first observed",
        ],
        dates=["Apr 2016", "20 Mar 2026", "28 Jul 2026", "30 Jul 2026\n≤43.55 h"],
        show_stage_labels=False,
    )
    plot_pathway_timeline(
        yokoe_axis,
        case_label="Yokoe Bridge",
        pathway_label="Structural pathway",
        pathway_color=STRUCTURAL_COLOR,
        descriptions=[
            "Same bridge closed",
            "Rebuilt bridge reopened",
            "Second shock; bridge closed",
            "General traffic reopened",
        ],
        dates=["16 Apr 2016", "2 Feb 2019", "28–29 Jul 2026", "17 Aug 2026\n19.61 days"],
        show_stage_labels=True,
    )
    mashiki_axis.tick_params(axis="x", which="both", bottom=False, labelbottom=False)

    for label, axis in zip("abc", (map_axis, mashiki_axis, yokoe_axis), strict=True):
        axis.text(
            -0.075,
            1.035,
            label,
            transform=axis.transAxes,
            fontsize=12,
            fontweight="bold",
            color="#1F2933",
            va="top",
            ha="left",
            clip_on=False,
        )

    fig.subplots_adjust(left=0.055, right=0.985, top=0.965, bottom=0.12)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
