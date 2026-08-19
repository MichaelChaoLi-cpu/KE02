#!/usr/bin/env python3
"""Intervention linkage and eligibility audit record.

Plan: Preserve how 20 documented interventions move from official evidence
through candidate route matching to geometry and treatment eligibility as a
documented process record rather than a Results figure.
Framework: Section 6.4 F_s and r_s and Section 7 intervention-evidence audit;
candidate name matching is not a treatment indicator or causal exposure.
"""

from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/ke02-matplotlib")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


ROOT = Path(__file__).resolve().parents[2]
INTERVENTIONS = ROOT / "data/processed/mashiki_resilience_interventions_preprocessed.parquet"
OUT = ROOT / "docs/process-records/assets/intervention-linkage-and-eligibility.png"

STAGE_LABELS = [
    "Documented intervention",
    "Completed before 2026 event",
    "At least one candidate route match",
    "Geometry usable for exposure",
    "Treatment assignment usable",
]
STAGE_COLORS = ["#314E68", "#3E6B82", "#3C8D87", "#D4DADD", "#D4DADD"]

GROUP_ORDER = [
    ("road widening", "high"),
    ("evacuation road", "medium"),
    ("evacuation road", "low-partial"),
]
GROUP_LABELS = {
    ("road widening", "high"): "Road widening · high quality",
    ("evacuation road", "medium"): "Evacuation road · medium quality",
    ("evacuation road", "low-partial"): "Evacuation road · low-partial quality",
}


def prepare_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    interventions = pd.read_parquet(INTERVENTIONS)
    required = {
        "Intervention ID",
        "Asset Type",
        "Completed Before 2026 Event",
        "Route Match Count",
        "Geometry Use Eligible",
        "Treatment Use Eligible",
        "Quality Flag",
    }
    if missing := sorted(required - set(interventions.columns)):
        raise ValueError(f"Missing required intervention columns: {missing}")
    if len(interventions) != 20 or not interventions["Intervention ID"].is_unique:
        raise ValueError("Expected 20 uniquely identified interventions")

    route_matched = interventions["Route Match Count"].fillna(0).gt(0)
    stage_masks = [
        pd.Series(True, index=interventions.index),
        interventions["Completed Before 2026 Event"].fillna(False).astype(bool),
        route_matched,
        interventions["Geometry Use Eligible"].fillna(False).astype(bool),
        interventions["Treatment Use Eligible"].fillna(False).astype(bool),
    ]
    total = len(interventions)
    funnel = pd.DataFrame(
        {
            "Stage": STAGE_LABELS,
            "Count": [int(mask.sum()) for mask in stage_masks],
        }
    )
    funnel["Share (%)"] = 100 * funnel["Count"] / total

    working = interventions.assign(**{"Candidate Route Match": route_matched})
    grouped_rows: list[dict[str, object]] = []
    observed_groups = set(
        zip(working["Asset Type"], working["Quality Flag"], strict=True)
    )
    if observed_groups != set(GROUP_ORDER):
        raise ValueError(f"Unexpected Asset Type × Quality Flag groups: {observed_groups}")
    for asset_type, quality_flag in GROUP_ORDER:
        subset = working.loc[
            working["Asset Type"].eq(asset_type)
            & working["Quality Flag"].eq(quality_flag)
        ]
        grouped_rows.append(
            {
                "Group": GROUP_LABELS[(asset_type, quality_flag)],
                "Documented": len(subset),
                "Candidate route match": int(subset["Candidate Route Match"].sum()),
            }
        )
    grouped = pd.DataFrame(grouped_rows)

    expected_counts = [20, 20, 12, 0, 0]
    if funnel["Count"].tolist() != expected_counts:
        raise ValueError(
            f"Eligibility funnel changed: {funnel['Count'].tolist()} != {expected_counts}"
        )
    return funnel, grouped


def main() -> None:
    funnel, grouped = prepare_data()

    sns.set_theme(style="whitegrid", context="paper", font_scale=1.03)
    fig, (funnel_ax, group_ax) = plt.subplots(
        1,
        2,
        figsize=(12.6, 5.45),
        gridspec_kw={"width_ratios": [1.04, 0.96], "wspace": 0.42},
    )

    y = np.arange(len(funnel))
    bars = funnel_ax.barh(
        y,
        funnel["Count"],
        height=0.58,
        color=STAGE_COLORS,
        edgecolor="none",
    )
    funnel_ax.set_yticks(y, funnel["Stage"])
    funnel_ax.invert_yaxis()
    funnel_ax.set_xlabel("Interventions passing stage (count)")
    funnel_ax.set_xlim(0, 22.5)
    funnel_ax.set_xticks([0, 5, 10, 15, 20])
    funnel_ax.grid(axis="x", color="#DCE1E4", linewidth=0.7)
    funnel_ax.grid(axis="y", visible=False)
    for bar, count, share in zip(
        bars,
        funnel["Count"],
        funnel["Share (%)"],
        strict=True,
    ):
        x = count + 0.45 if count > 0 else 0.45
        funnel_ax.text(
            x,
            bar.get_y() + bar.get_height() / 2,
            f"{count}  ({share:.0f}%)",
            ha="left",
            va="center",
            fontsize=9.3,
            fontweight="bold" if count == 0 else "normal",
            color="#8F2D2D" if count == 0 else "#26343B",
        )

    group_y = np.arange(len(grouped))
    offset = 0.19
    height = 0.32
    documented = group_ax.barh(
        group_y - offset,
        grouped["Documented"],
        height=height,
        color="#C7CED3",
        edgecolor="none",
        label="Documented",
    )
    matched = group_ax.barh(
        group_y + offset,
        grouped["Candidate route match"],
        height=height,
        color="#3C8D87",
        edgecolor="none",
        label="Candidate route match",
    )
    group_ax.set_yticks(group_y, grouped["Group"])
    group_ax.invert_yaxis()
    group_ax.set_xlabel("Interventions (count)")
    group_ax.set_xlim(0, 13.2)
    group_ax.set_xticks(np.arange(0, 13, 3))
    group_ax.grid(axis="x", color="#DCE1E4", linewidth=0.7)
    group_ax.grid(axis="y", visible=False)
    for bar_set in (documented, matched):
        for bar in bar_set:
            group_ax.text(
                bar.get_width() + 0.25,
                bar.get_y() + bar.get_height() / 2,
                f"{int(bar.get_width())}",
                ha="left",
                va="center",
                fontsize=9.0,
                color="#26343B",
            )
    group_ax.legend(
        frameon=False,
        ncol=2,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.16),
        columnspacing=1.5,
        handlelength=1.8,
    )

    for label, ax in zip("ab", (funnel_ax, group_ax), strict=True):
        ax.text(
            -0.13,
            1.04,
            label,
            transform=ax.transAxes,
            fontsize=12,
            fontweight="bold",
            va="top",
        )
        sns.despine(ax=ax, left=True, bottom=False)

    fig.subplots_adjust(left=0.235, right=0.975, top=0.96, bottom=0.20)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
