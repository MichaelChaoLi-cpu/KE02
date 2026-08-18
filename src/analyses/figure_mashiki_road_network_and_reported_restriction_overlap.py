#!/usr/bin/env python3
"""Mashiki Road Network and Reported Restriction Overlap.

Plan: Assess the spatial coverage and limits of linking reported restriction
geometry to the official Mashiki road network.
Framework: Section 6.2 O_it(d) over d in {0, 10, 25, 50} metres and Section 7
spatial-linkage readiness only; overlap is not passability or restoration.
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
import shapely
from matplotlib.lines import Line2D
from pyproj import Transformer
from shapely.geometry import LineString


ROOT = Path(__file__).resolve().parents[2]
ROADS = ROOT / "data/processed/mashiki_official_road_network_preprocessed.parquet"
RESTRICTIONS = ROOT / "data/processed/kumamoto_2026_road_restriction_snapshots_preprocessed.parquet"
ADMINISTRATIVE = ROOT / "data/processed/kumamoto_administrative_areas_cartographic_preprocessed.parquet"
OUT = ROOT / "data/results/figures/Figure_mashiki_road_network_and_reported_restriction_overlap.png"

PROJECTED_CRS = 6670
GEOGRAPHIC_CRS = 6668
TOLERANCES = np.array([0.0, 10.0, 25.0, 50.0])

MAP_CLASSES = [
    "Beyond 50 m",
    "Additional within 50 m",
    "Additional within 25 m",
    "Exact intersection",
]
MAP_COLORS = {
    "Beyond 50 m": "#D5DCE1",
    "Additional within 50 m": "#4C9F9B",
    "Additional within 25 m": "#E69F00",
    "Exact intersection": "#6A3D9A",
}


def graticule_values(lower: float, upper: float, step: float) -> list[float]:
    start = math.ceil((lower - 1e-9) / step) * step
    stop = math.floor((upper + 1e-9) / step) * step
    count = int(round((stop - start) / step)) + 1
    return [round(start + index * step, 8) for index in range(max(0, count))]


def add_graticule(
    ax: plt.Axes,
    geographic_bounds: tuple[float, float, float, float],
    step: float = 0.025,
) -> None:
    lon_min, lat_min, lon_max, lat_max = geographic_bounds
    longitudes = graticule_values(lon_min, lon_max, step)
    latitudes = graticule_values(lat_min, lat_max, step)
    samples = 120
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
            -0.015,
            f"{longitude:.3f}°E",
            transform=ax.get_xaxis_transform(),
            ha="center",
            va="top",
            **label_style,
        )
    for latitude in latitudes:
        _, y_position = transformer.transform(centre_longitude, latitude)
        ax.text(
            -0.018,
            y_position,
            f"{latitude:.3f}°N",
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


def add_scale_bar(ax: plt.Axes, length_km: int = 2) -> None:
    x_min, x_max = ax.get_xlim()
    y_min, y_max = ax.get_ylim()
    length = length_km * 1_000
    x_start = x_min + 0.065 * (x_max - x_min)
    y = y_min + 0.055 * (y_max - y_min)
    tick_height = 90
    ax.plot([x_start, x_start + length], [y, y], color="#263238", linewidth=2.0, zorder=15)
    for x in (x_start, x_start + length):
        ax.plot([x, x], [y - tick_height, y + tick_height], color="#263238", linewidth=1.0, zorder=15)
    ax.text(
        x_start + length / 2,
        y + 0.012 * (y_max - y_min),
        f"{length_km} km",
        ha="center",
        va="bottom",
        fontsize=7.0,
        color="#263238",
        zorder=15,
    )


def prepare_data() -> tuple[
    gpd.GeoDataFrame,
    gpd.GeoDataFrame,
    gpd.GeoDataFrame,
    pd.DataFrame,
    pd.Timestamp,
    tuple[float, float, float, float],
]:
    roads = gpd.read_parquet(ROADS)
    restrictions = gpd.read_parquet(RESTRICTIONS)
    administrative = gpd.read_parquet(ADMINISTRATIVE)
    required_road = {
        "Road Segment ID",
        "Route Class",
        "Route Name",
        "Official Geometry Length (m)",
        "Geometry",
    }
    required_restriction = {"Restriction Feature ID", "Snapshot Time", "Geometry"}
    if missing := sorted(required_road - set(roads.columns)):
        raise ValueError(f"Missing required road columns: {missing}")
    if missing := sorted(required_restriction - set(restrictions.columns)):
        raise ValueError(f"Missing required restriction columns: {missing}")
    if roads.crs is None or restrictions.crs is None or administrative.crs is None:
        raise ValueError("A required geometry layer has no CRS")
    if len(roads) != 433 or not roads["Road Segment ID"].is_unique:
        raise ValueError("Expected 433 uniquely identified Mashiki road segments")

    roads = roads.to_crs(PROJECTED_CRS)
    restrictions = restrictions.to_crs(PROJECTED_CRS)
    mashiki = administrative.loc[
        administrative["Municipality Name"].eq("益城町")
    ].to_crs(PROJECTED_CRS).dissolve()
    if len(mashiki) != 1 or not roads.intersects(mashiki.geometry.iloc[0]).all():
        raise ValueError("Official road network does not fit the Mashiki boundary")

    road_length = roads["Official Geometry Length (m)"].astype(float)
    total_length = float(road_length.sum())
    rows: list[dict[str, object]] = []
    distance_by_time: dict[pd.Timestamp, np.ndarray] = {}
    for snapshot_time in sorted(restrictions["Snapshot Time"].unique()):
        snapshot = restrictions.loc[restrictions["Snapshot Time"].eq(snapshot_time)]
        restriction_union = shapely.union_all(snapshot.geometry.array)
        distances = roads.geometry.distance(restriction_union).to_numpy(float)
        time = pd.Timestamp(snapshot_time)
        distance_by_time[time] = distances
        for tolerance in TOLERANCES:
            within = distances <= tolerance + 1e-9
            rows.append(
                {
                    "Snapshot Time": time,
                    "Tolerance (m)": tolerance,
                    "Matched Segment Count": int(within.sum()),
                    "Matched Segment Share (%)": 100 * float(within.mean()),
                    "Matched Length Share (%)": 100 * float(road_length[within].sum()) / total_length,
                }
            )
    sensitivity = pd.DataFrame(rows)

    latest_time = max(distance_by_time)
    latest_distances = distance_by_time[latest_time]
    roads = roads.copy()
    roads["Minimum Distance (m)"] = latest_distances
    roads["Map Class"] = np.select(
        [
            latest_distances <= 1e-9,
            latest_distances <= 25.0,
            latest_distances <= 50.0,
        ],
        [
            "Exact intersection",
            "Additional within 25 m",
            "Additional within 50 m",
        ],
        default="Beyond 50 m",
    )
    latest_restrictions = restrictions.loc[
        restrictions["Snapshot Time"].eq(latest_time)
    ]
    latest_restrictions = gpd.clip(latest_restrictions, mashiki).reset_index(drop=True)
    geographic_bounds = tuple(mashiki.to_crs(GEOGRAPHIC_CRS).total_bounds)
    return roads, latest_restrictions, mashiki, sensitivity, latest_time, geographic_bounds


def main() -> None:
    roads, latest_restrictions, mashiki, sensitivity, latest_time, geographic_bounds = prepare_data()
    latest_summary = sensitivity.loc[sensitivity["Snapshot Time"].eq(latest_time)]

    sns.set_theme(style="white", context="paper", font_scale=1.0)
    fig, (map_ax, sensitivity_ax) = plt.subplots(
        1,
        2,
        figsize=(13.2, 6.25),
        gridspec_kw={"width_ratios": [1.03, 1.0]},
    )

    mashiki.plot(ax=map_ax, color="#F1F3F4", edgecolor="none", zorder=0)
    for map_class in MAP_CLASSES:
        subset = roads.loc[roads["Map Class"].eq(map_class)]
        if subset.empty:
            continue
        subset.plot(
            ax=map_ax,
            color=MAP_COLORS[map_class],
            linewidth=0.75 if map_class == "Beyond 50 m" else 2.0,
            zorder=4 if map_class == "Beyond 50 m" else 6,
        )
    if not latest_restrictions.empty:
        latest_restrictions.plot(
            ax=map_ax,
            color="#20262B",
            linewidth=1.15,
            linestyle=(0, (3, 2)),
            zorder=9,
        )
    mashiki.boundary.plot(ax=map_ax, color="#46545E", linewidth=0.75, zorder=10)

    bounds = tuple(mashiki.total_bounds)
    x_margin = 0.03 * (bounds[2] - bounds[0])
    y_margin = 0.03 * (bounds[3] - bounds[1])
    map_ax.set_xlim(bounds[0] - x_margin, bounds[2] + x_margin)
    map_ax.set_ylim(bounds[1] - y_margin, bounds[3] + y_margin)
    map_ax.set_aspect("equal")
    add_graticule(map_ax, geographic_bounds)
    add_scale_bar(map_ax)
    map_ax.annotate(
        "N",
        xy=(0.94, 0.91),
        xytext=(0.94, 0.78),
        xycoords="axes fraction",
        textcoords="axes fraction",
        ha="center",
        va="bottom",
        fontsize=8.2,
        fontweight="bold",
        arrowprops={"arrowstyle": "-|>", "color": "#222222", "linewidth": 1.0},
        zorder=20,
    )
    place = mashiki.geometry.representative_point().iloc[0]
    label = map_ax.text(
        place.x,
        place.y,
        "Mashiki",
        ha="center",
        va="center",
        fontsize=8.3,
        fontweight="bold",
        color="#2F3C45",
        zorder=12,
    )
    label.set_path_effects(
        [path_effects.withStroke(linewidth=2.8, foreground="white", alpha=0.92)]
    )

    counts = latest_summary.set_index("Tolerance (m)")["Matched Segment Count"]
    map_ax.text(
        0.025,
        0.975,
        pd.Timestamp(latest_time).strftime("%b %d, %H:%M JST"),
        transform=map_ax.transAxes,
        ha="left",
        va="top",
        fontsize=9.2,
        fontweight="bold",
        color="#172033",
        bbox={"facecolor": "white", "edgecolor": "#D0D5DD", "alpha": 0.92, "pad": 2.5},
        zorder=20,
    )
    map_ax.text(
        0.025,
        0.915,
        (
            f"exact {int(counts.loc[0.0])}/433  |  "
            f"within 25 m {int(counts.loc[25.0])}/433  |  "
            f"within 50 m {int(counts.loc[50.0])}/433"
        ),
        transform=map_ax.transAxes,
        ha="left",
        va="top",
        fontsize=7.3,
        color="#344054",
        bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.88, "pad": 2.0},
        zorder=20,
    )

    grouped = sensitivity.groupby("Tolerance (m)")
    for column, color, marker, label_text in [
        ("Matched Segment Share (%)", "#6A3D9A", "o", "Matched road-segment share"),
        (
            "Matched Length Share (%)",
            "#00876C",
            "s",
            "Length share of matched segments",
        ),
    ]:
        median = grouped[column].median().reindex(TOLERANCES).to_numpy(float)
        low = grouped[column].min().reindex(TOLERANCES).to_numpy(float)
        high = grouped[column].max().reindex(TOLERANCES).to_numpy(float)
        sensitivity_ax.errorbar(
            TOLERANCES,
            median,
            yerr=np.vstack([median - low, high - median]),
            color=color,
            linewidth=2.0,
            marker=marker,
            markersize=6,
            capsize=3,
            label=label_text,
            zorder=5,
        )

    latest_counts = latest_summary.set_index("Tolerance (m)")["Matched Segment Count"]
    segment_median = grouped["Matched Segment Share (%)"].median().reindex(TOLERANCES)
    for tolerance in TOLERANCES:
        sensitivity_ax.annotate(
            f"{int(latest_counts.loc[tolerance])}",
            xy=(tolerance, segment_median.loc[tolerance]),
            xytext=(0, 9),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=7.4,
            color="#5A2E83",
        )
    sensitivity_ax.set_xlabel("Spatial tolerance (m)")
    sensitivity_ax.set_ylabel("Share of official Mashiki network (%)")
    sensitivity_ax.set_xticks(TOLERANCES, ["0\nintersect", "10", "25", "50"])
    sensitivity_ax.set_xlim(-3, 53)
    sensitivity_ax.set_ylim(0, 15)
    sensitivity_ax.grid(axis="y", color="#D0D5DD", linewidth=0.7)
    sensitivity_ax.grid(axis="x", visible=False)
    sensitivity_ax.legend(frameon=False, loc="upper left")
    sensitivity_ax.text(
        0.03,
        0.88,
        "Median and range across 23 available snapshots\nNumbers label matched road segments",
        transform=sensitivity_ax.transAxes,
        ha="left",
        va="top",
        fontsize=8.0,
        color="#475467",
    )
    sns.despine(ax=sensitivity_ax)

    map_handles = [
        Line2D([0], [0], color=MAP_COLORS[map_class], linewidth=2.5, label=map_class)
        for map_class in MAP_CLASSES
    ]
    map_handles.append(
        Line2D(
            [0],
            [0],
            color="#20262B",
            linewidth=1.4,
            linestyle=(0, (3, 2)),
            label="Reported restriction geometry",
        )
    )
    map_ax.legend(
        handles=map_handles,
        frameon=False,
        ncol=2,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.095),
        fontsize=7.4,
        columnspacing=1.3,
        handlelength=2.6,
    )

    for label_text, ax in zip("ab", (map_ax, sensitivity_ax)):
        ax.text(
            -0.09,
            1.025,
            label_text,
            transform=ax.transAxes,
            fontsize=12,
            fontweight="bold",
            color="#172033",
            va="top",
        )
    fig.subplots_adjust(left=0.075, right=0.985, top=0.98, bottom=0.18, wspace=0.19)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Latest snapshot: {latest_time.isoformat()}")
    print(
        "Matched segment counts: "
        + ", ".join(
            f"{int(tolerance)}m={int(latest_counts.loc[tolerance])}"
            for tolerance in TOLERANCES
        )
    )
    print(f"Saved: {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
