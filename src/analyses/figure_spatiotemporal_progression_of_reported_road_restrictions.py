#!/usr/bin/env python3
"""Spatiotemporal Progression of Reported Road Restrictions.

Plan: Show the geography and reported-state composition of road restrictions
inside Kumamoto Prefecture at four observation-coverage-based times.
Framework: Section 5 bounded descriptive spatial progression; Section 6.2
representative snapshots selected from the available observation sequence;
Section 7 descriptive geography only, without segment-restoration inference.
"""

from __future__ import annotations

import math
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/ke02-matplotlib")

import geopandas as gpd
import matplotlib.patheffects as path_effects
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.lines import Line2D
from pyproj import Transformer
from shapely.geometry import LineString


ROOT = Path(__file__).resolve().parents[2]
RESTRICTIONS = ROOT / "data/processed/kumamoto_2026_road_restriction_snapshots_preprocessed.parquet"
ADMINISTRATIVE = ROOT / "data/processed/kumamoto_administrative_areas_cartographic_preprocessed.parquet"
OUT = ROOT / "docs/process-records/assets/supplementary/Figure_spatiotemporal_progression_of_reported_road_restrictions.png"

PROJECTED_CRS = 6670
GEOGRAPHIC_CRS = 6668
STATE_ORDER = [
    "active_full_closure",
    "active_emergency_access_only",
    "restriction_lifted",
    "unknown_status",
]
STATE_LABELS = {
    "active_full_closure": "Full closure",
    "active_emergency_access_only": "Emergency access only",
    "restriction_lifted": "Restriction lifted",
    "unknown_status": "Status unavailable",
}
STATE_COLORS = {
    "active_full_closure": "#C0364E",
    "active_emergency_access_only": "#E69F00",
    "restriction_lifted": "#0072B2",
    "unknown_status": "#707981",
}
PLACE_LABELS = {
    "熊本市": "Kumamoto City",
    "宇城市": "Uki",
    "八代市": "Yatsushiro",
    "益城町": "Mashiki",
    "山都町": "Yamato",
}


def graticule_values(lower: float, upper: float, step: float) -> list[float]:
    start = math.ceil((lower - 1e-9) / step) * step
    stop = math.floor((upper + 1e-9) / step) * step
    count = int(round((stop - start) / step)) + 1
    return [round(start + index * step, 8) for index in range(max(0, count))]


def add_graticule(
    ax: plt.Axes,
    geographic_bounds: tuple[float, float, float, float],
    step: float = 0.25,
) -> None:
    """Draw the KE01-family labelled longitude-latitude graticule."""
    lon_min, lat_min, lon_max, lat_max = geographic_bounds
    longitudes = graticule_values(lon_min, lon_max, step)
    latitudes = graticule_values(lat_min, lat_max, step)
    samples = 160

    lines = [
        LineString(
            zip(
                np.full(samples, longitude),
                np.linspace(lat_min - step, lat_max + step, samples),
                strict=True,
            )
        )
        for longitude in longitudes
    ]
    lines.extend(
        LineString(
            zip(
                np.linspace(lon_min - step, lon_max + step, samples),
                np.full(samples, latitude),
                strict=True,
            )
        )
        for latitude in latitudes
    )
    gpd.GeoSeries(lines, crs=GEOGRAPHIC_CRS).to_crs(PROJECTED_CRS).plot(
        ax=ax,
        color="#7D8992",
        linewidth=0.42,
        linestyle=(0, (2.5, 3.5)),
        alpha=0.48,
        zorder=3,
    )

    transformer = Transformer.from_crs(GEOGRAPHIC_CRS, PROJECTED_CRS, always_xy=True)
    centre_latitude = (lat_min + lat_max) / 2
    centre_longitude = (lon_min + lon_max) / 2
    label_style = {"fontsize": 6.8, "color": "#46515A", "clip_on": False}
    for longitude in longitudes:
        x_position, _ = transformer.transform(longitude, centre_latitude)
        ax.text(
            x_position,
            -0.012,
            f"{longitude:.2f}°E",
            transform=ax.get_xaxis_transform(),
            ha="center",
            va="top",
            **label_style,
        )
    for latitude in latitudes:
        _, y_position = transformer.transform(centre_longitude, latitude)
        ax.text(
            -0.014,
            y_position,
            f"{latitude:.2f}°N",
            transform=ax.get_yaxis_transform(),
            ha="right",
            va="center",
            **label_style,
        )

    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_color("#303A40")
        spine.set_linewidth(0.85)
        spine.set_zorder(20)


def select_representative_times(times: pd.DatetimeIndex) -> pd.DatetimeIndex:
    if len(times) < 4:
        raise ValueError("At least four available snapshot times are required")
    indices = np.rint(np.array([0.0, 0.25, 0.50, 1.0]) * (len(times) - 1)).astype(int)
    if len(set(indices)) != 4:
        raise ValueError("Coverage-based selection did not produce four unique times")
    return times[indices]


def prepare_data() -> tuple[
    gpd.GeoDataFrame,
    gpd.GeoDataFrame,
    gpd.GeoDataFrame,
    pd.DatetimeIndex,
    tuple[float, float, float, float],
]:
    restrictions = gpd.read_parquet(RESTRICTIONS)
    administrative = gpd.read_parquet(ADMINISTRATIVE)
    required = {
        "Snapshot Time",
        "Geometry",
        "Restriction Type",
        "Municipality",
        "Road Type",
        "Observation State",
        "Restriction Feature ID",
    }
    missing = sorted(required - set(restrictions.columns))
    if missing:
        raise ValueError(f"Missing required restriction columns: {missing}")
    if restrictions.crs is None or administrative.crs is None:
        raise ValueError("A required map layer has no CRS")
    if restrictions.geometry.isna().any() or restrictions.geometry.is_empty.any():
        raise ValueError("Restriction geometry contains missing or empty values")
    if len(administrative) != 49:
        raise ValueError("Expected 49 official municipality or ward polygons")

    administrative = administrative.to_crs(PROJECTED_CRS)
    prefecture = administrative.dissolve()
    restrictions = restrictions.to_crs(PROJECTED_CRS)
    restrictions = gpd.clip(restrictions, prefecture).reset_index(drop=True)
    if restrictions.empty:
        raise ValueError("No restriction geometry intersects Kumamoto Prefecture")

    times = pd.DatetimeIndex(
        restrictions["Snapshot Time"].drop_duplicates().sort_values().tolist()
    )
    if len(times) != 24:
        raise ValueError(f"Expected 24 available snapshots after clipping, found {len(times)}")
    selected = select_representative_times(times)
    geographic_bounds = tuple(prefecture.to_crs(GEOGRAPHIC_CRS).total_bounds)
    return restrictions, administrative, prefecture, selected, geographic_bounds


def municipality_label_points(administrative: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    municipalities = administrative.dissolve(by="Municipality Name", as_index=False)
    municipalities = municipalities.loc[
        municipalities["Municipality Name"].isin(PLACE_LABELS)
    ].copy()
    municipalities["Geometry"] = municipalities.geometry.representative_point()
    return municipalities


def add_place_labels(ax: plt.Axes, labels: gpd.GeoDataFrame) -> None:
    for _, row in labels.iterrows():
        text = ax.text(
            row["Geometry"].x,
            row["Geometry"].y,
            PLACE_LABELS[row["Municipality Name"]],
            ha="center",
            va="center",
            fontsize=6.6,
            color="#2F3C45",
            zorder=7,
        )
        text.set_path_effects(
            [path_effects.withStroke(linewidth=2.2, foreground="white", alpha=0.9)]
        )


def add_scale_bar(ax: plt.Axes, length_km: int = 25) -> None:
    x_min, x_max = ax.get_xlim()
    y_min, y_max = ax.get_ylim()
    length = length_km * 1_000
    x_start = x_min + 0.07 * (x_max - x_min)
    y = y_min + 0.06 * (y_max - y_min)
    tick_height = 700
    ax.plot([x_start, x_start + length], [y, y], color="#263238", linewidth=2.0, zorder=15)
    ax.plot([x_start, x_start], [y - tick_height, y + tick_height], color="#263238", linewidth=1.0, zorder=15)
    ax.plot([x_start + length, x_start + length], [y - tick_height, y + tick_height], color="#263238", linewidth=1.0, zorder=15)
    ax.text(
        x_start + length / 2,
        y + 0.012 * (y_max - y_min),
        f"{length_km} km",
        ha="center",
        va="bottom",
        fontsize=7.2,
        color="#263238",
        zorder=15,
    )


def main() -> None:
    restrictions, administrative, prefecture, selected_times, geographic_bounds = prepare_data()
    labels = municipality_label_points(administrative)

    bounds = tuple(prefecture.total_bounds)
    x_margin = 0.018 * (bounds[2] - bounds[0])
    y_margin = 0.018 * (bounds[3] - bounds[1])
    x_limits = (bounds[0] - x_margin, bounds[2] + x_margin)
    y_limits = (bounds[1] - y_margin, bounds[3] + y_margin)

    sns.set_theme(style="white", context="paper", font_scale=1.0)
    fig, axes = plt.subplots(2, 2, figsize=(11.7, 11.0), sharex=True, sharey=True)

    for panel_label, snapshot_time, ax in zip("abcd", selected_times, axes.flat):
        administrative.plot(ax=ax, color="#F0F2F3", edgecolor="none", zorder=0)
        administrative.boundary.plot(
            ax=ax,
            color="#A2ADB5",
            linewidth=0.32,
            alpha=0.95,
            zorder=2,
        )
        prefecture.boundary.plot(ax=ax, color="#46545E", linewidth=0.65, zorder=4)
        add_graticule(ax, geographic_bounds)
        add_place_labels(ax, labels)

        snapshot = restrictions.loc[
            restrictions["Snapshot Time"].eq(snapshot_time)
        ].copy()
        for state in STATE_ORDER:
            state_rows = snapshot.loc[snapshot["Observation State"].eq(state)]
            if state_rows.empty:
                continue
            lines = state_rows.loc[
                state_rows.geometry.geom_type.isin(["LineString", "MultiLineString"])
            ]
            points = state_rows.loc[state_rows.geometry.geom_type.eq("Point")]
            if not lines.empty:
                lines.plot(
                    ax=ax,
                    color=STATE_COLORS[state],
                    linewidth=2.15 if state.startswith("active_") else 1.8,
                    linestyle="-" if state != "unknown_status" else (0, (2, 2)),
                    zorder=9 if state.startswith("active_") else 8,
                )
            if not points.empty:
                points.plot(
                    ax=ax,
                    color=STATE_COLORS[state],
                    markersize=25,
                    marker="o",
                    edgecolor="white",
                    linewidth=0.5,
                    zorder=10,
                )

        counts = snapshot["Observation State"].value_counts().reindex(STATE_ORDER, fill_value=0)
        ax.text(
            0.025,
            0.975,
            pd.Timestamp(snapshot_time).strftime("%b %d, %H:%M JST"),
            transform=ax.transAxes,
            ha="left",
            va="top",
            fontsize=9.3,
            fontweight="bold",
            color="#172033",
            bbox={"facecolor": "white", "edgecolor": "#D0D5DD", "alpha": 0.92, "pad": 2.5},
            zorder=20,
        )
        ax.text(
            0.025,
            0.910,
            (
                f"closure {int(counts['active_full_closure'])}  |  "
                f"emergency {int(counts['active_emergency_access_only'])}  |  "
                f"lifted {int(counts['restriction_lifted'])}  |  "
                f"unknown {int(counts['unknown_status'])}"
            ),
            transform=ax.transAxes,
            ha="left",
            va="top",
            fontsize=7.3,
            color="#344054",
            bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.88, "pad": 2.0},
            zorder=20,
        )
        ax.text(
            -0.085,
            1.025,
            panel_label,
            transform=ax.transAxes,
            fontsize=12,
            fontweight="bold",
            color="#172033",
            va="top",
        )
        ax.set_xlim(*x_limits)
        ax.set_ylim(*y_limits)
        ax.set_aspect("equal")

    axes[0, 0].annotate(
        "N",
        xy=(0.94, 0.91),
        xytext=(0.94, 0.79),
        xycoords="axes fraction",
        textcoords="axes fraction",
        ha="center",
        va="bottom",
        fontsize=8.2,
        fontweight="bold",
        arrowprops={"arrowstyle": "-|>", "color": "#222222", "linewidth": 1.0},
        zorder=20,
    )
    add_scale_bar(axes[1, 1])

    state_handles = [
        Line2D(
            [0],
            [0],
            color=STATE_COLORS[state],
            linewidth=2.8,
            linestyle="-" if state != "unknown_status" else (0, (2, 2)),
            label=STATE_LABELS[state],
        )
        for state in STATE_ORDER
    ]
    fig.legend(
        handles=state_handles,
        loc="lower center",
        bbox_to_anchor=(0.5, 0.014),
        ncol=4,
        frameon=False,
        columnspacing=1.8,
        handlelength=2.8,
    )
    fig.subplots_adjust(
        left=0.075,
        right=0.99,
        top=0.992,
        bottom=0.09,
        wspace=0.12,
        hspace=0.12,
    )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)

    selected_labels = ", ".join(pd.Timestamp(time).isoformat() for time in selected_times)
    print(f"Selected snapshots: {selected_labels}")
    print(f"Mapped Kumamoto-clipped records: {len(restrictions):,}")
    print(f"Saved: {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
