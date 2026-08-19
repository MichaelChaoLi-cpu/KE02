#!/usr/bin/env python3
"""Case Selection and Inference Boundaries.

Plan: Summarize how four complete official candidate universes yield two
physical core cases and classify prespecified claim checks as robust, bounded,
or unsupported.
Framework: AnaSOP Sections 5.2-5.5, Sections 6.4-6.5, and Analytical Workflow
steps 5-6. Denominator rows are audit units, not a statistical sample.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
CANDIDATES = (
    ROOT
    / "data/processed"
    / "repeated_shock_candidate_ledger_preprocessed.parquet"
)
CLAIMS = (
    ROOT
    / "data/processed"
    / "repeated_shock_claim_sensitivity_preprocessed.parquet"
)
OUT = (
    ROOT
    / "data/results/figures"
    / "Figure_case_selection_and_inference_boundaries.png"
)

DENOMINATOR_COLOR = "#D9DFE3"
MASHIKI_COLOR = "#D97706"
YOKOE_COLOR = "#2563A8"
CONTEXT_COLOR = "#B7A37B"
ROBUST_COLOR = "#27825B"
BOUNDED_COLOR = "#D58A16"
UNSUPPORTED_COLOR = "#B33A3A"
TEXT_COLOR = "#263238"
GRID_COLOR = "#D8DEE2"


UNIVERSE_ORDER = [
    "post-2016 local road projects",
    "2016 officially restored bridges",
    "2026 bridge-damage records",
    "additional official reconstructions",
]
UNIVERSE_LABELS = {
    "post-2016 local road projects": "Post-2016 local\nroad projects",
    "2016 officially restored bridges": "2016 officially\nrestored bridges",
    "2026 bridge-damage records": "2026 bridge-damage\nrecords",
    "additional official reconstructions": "Additional official\nreconstructions",
}
CLAIM_ORDER = ["C1", "C2", "C3", "C4"]
CLAIM_LABELS = {
    "C1": "Mashiki service evidence",
    "C2": "Yokoe restoration",
    "C3": "Case-selection validity",
    "C4": "Source precedence",
}


def summarize_denominators(candidates: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for universe in UNIVERSE_ORDER:
        subset = candidates.loc[candidates["Candidate Universe"].eq(universe)]
        if subset.empty:
            raise RuntimeError(f"Missing candidate universe: {universe}")
        included = subset["Core Status"].str.startswith("include")
        hazard_admissible = subset["Hazard Gate"].isin(["pass", "metric dependent"])
        if universe == "post-2016 local road projects":
            role_label = f"{int(included.sum())} stages → 1 corridor"
            role_color = MASHIKI_COLOR
        elif universe in {
            "2016 officially restored bridges",
            "2026 bridge-damage records",
        }:
            role_label = f"{int(included.sum())} Yokoe record"
            role_color = YOKOE_COLOR
        else:
            context_count = int(
                subset["Core Status"].eq("contextual mechanism case only").sum()
            )
            role_label = f"{context_count} context only; 0 core"
            role_color = CONTEXT_COLOR

        rows.append(
            {
                "Candidate Universe": universe,
                "Screened": int(len(subset)),
                "Identity": int(subset["Identity Gate"].sum()),
                "Geometry": int(subset["Geometry Gate"].sum()),
                "Hazard": int(hazard_admissible.sum()),
                "Outcome": int(subset["Outcome Gate"].sum()),
                "Core Records": int(included.sum()),
                "Role Label": role_label,
                "Role Color": role_color,
            }
        )
    summary = pd.DataFrame(rows)
    core_rows = candidates["Core Status"].str.startswith("include")
    if not candidates.loc[core_rows, "Identity Gate"].all():
        raise RuntimeError("An included record fails the identity gate.")
    if not candidates.loc[core_rows, "Geometry Gate"].all():
        raise RuntimeError("An included record fails the geometry gate.")
    if not candidates.loc[core_rows, "Outcome Gate"].all():
        raise RuntimeError("An included record fails the outcome gate.")
    if not candidates.loc[core_rows, "Hazard Gate"].isin(
        ["pass", "metric dependent"]
    ).all():
        raise RuntimeError("An included record lacks admissible hazard evidence.")
    return summary


def plot_denominators(axis: plt.Axes, candidates: pd.DataFrame) -> None:
    summary = summarize_denominators(candidates)
    y = np.arange(len(summary))[::-1]
    columns = ["Screened", "Identity", "Geometry", "Hazard", "Outcome", "Core Records"]
    labels = ["Screened", "Identity", "Geometry", "Hazard", "Outcome", "Core\nrecords"]
    colors = [DENOMINATOR_COLOR, "#6B7780", "#3976A8", "#D58A16", "#27825B", "#243746"]
    x = np.arange(len(columns))

    for row_position, (_, row) in zip(y, summary.iterrows(), strict=True):
        for column_position, (column, color) in enumerate(
            zip(columns, colors, strict=True)
        ):
            count = int(row[column])
            axis.scatter(
                column_position,
                row_position,
                s=520,
                marker="s",
                color="#F1F3F4",
                edgecolor="white",
                linewidth=1.0,
                zorder=1,
            )
            if count > 0:
                axis.scatter(
                    column_position,
                    row_position,
                    s=245,
                    color=color,
                    edgecolor="white",
                    linewidth=1.0,
                    zorder=2,
                )
            axis.text(
                column_position,
                row_position,
                str(count),
                ha="center",
                va="center",
                fontsize=8.4,
                fontweight="bold",
                color="white" if count > 0 and column != "Screened" else "#4F5B63",
                zorder=3,
            )
        axis.text(
            len(columns) - 0.30,
            row_position,
            str(row["Role Label"]),
            ha="left",
            va="center",
            fontsize=8.2,
            fontweight="bold",
            color=row["Role Color"],
            zorder=4,
        )

    axis.text(
        0,
        1.03,
        "Gate-specific candidate audit",
        transform=axis.transAxes,
        ha="left",
        va="bottom",
        fontsize=11.2,
        fontweight="bold",
        color=TEXT_COLOR,
    )
    axis.set_xlim(-0.55, 7.15)
    axis.set_ylim(-0.58, len(summary) - 0.42)
    axis.set_xticks(x)
    axis.set_xticklabels(labels, fontsize=8.2)
    axis.set_yticks(y)
    axis.set_yticklabels(
        [UNIVERSE_LABELS[value] for value in summary["Candidate Universe"]],
        fontsize=9.0,
    )
    axis.set_xlabel("Gate-specific passing records", fontsize=9.3, labelpad=7)
    axis.grid(False)
    axis.tick_params(axis="x", labelsize=8.2, colors="#4B5962", length=0, pad=7)
    axis.tick_params(axis="y", length=0, pad=7, colors=TEXT_COLOR)
    for side in ("top", "right", "left"):
        axis.spines[side].set_visible(False)
    axis.spines["bottom"].set_visible(False)


def broad_classification(value: str) -> str:
    normalized = value.strip().lower()
    if "unsupported" in normalized:
        return "Unsupported extension"
    if "measurement dependent" in normalized or "non-comparable" in normalized:
        return "Measurement / outcome boundary"
    if "robust" in normalized:
        return "Robust evidence"
    raise RuntimeError(f"Unmapped claim classification: {value}")


def plot_claim_boundaries(axis: plt.Axes, claims: pd.DataFrame) -> None:
    claims = claims.copy()
    claims["Boundary Class"] = claims["Classification"].map(broad_classification)
    if claims["Inference Ceiling"].isna().any():
        raise RuntimeError("Every claim scenario must have an inference ceiling.")

    classes = [
        "Robust evidence",
        "Measurement / outcome boundary",
        "Unsupported extension",
    ]
    colors = [ROBUST_COLOR, BOUNDED_COLOR, UNSUPPORTED_COLOR]
    background = ["#E9F3EE", "#FBF1DD", "#F8E8E8"]
    y = np.arange(len(CLAIM_ORDER))[::-1]
    x = np.arange(len(classes))

    for position, shade in zip(x, background, strict=True):
        axis.axvspan(position - 0.46, position + 0.46, color=shade, zorder=0)
    for separator in np.arange(len(CLAIM_ORDER) - 1) + 0.5:
        axis.axhline(separator, color="white", linewidth=1.4, zorder=1)

    counts = (
        claims.groupby(["Claim ID", "Boundary Class"])
        .size()
        .rename("Scenario Count")
        .reset_index()
    )
    for row_position, claim_id in zip(y, CLAIM_ORDER, strict=True):
        for column_position, (classification, color) in enumerate(
            zip(classes, colors, strict=True)
        ):
            match = counts.loc[
                counts["Claim ID"].eq(claim_id)
                & counts["Boundary Class"].eq(classification),
                "Scenario Count",
            ]
            if match.empty:
                continue
            count = int(match.iloc[0])
            axis.scatter(
                column_position,
                row_position,
                s=230,
                color=color,
                edgecolor="white",
                linewidth=1.2,
                zorder=3,
            )
            axis.text(
                column_position,
                row_position,
                str(count),
                ha="center",
                va="center",
                fontsize=9.2,
                fontweight="bold",
                color="white",
                zorder=4,
            )

    axis.text(
        0,
        1.03,
        "Claim classifications",
        transform=axis.transAxes,
        ha="left",
        va="bottom",
        fontsize=11.2,
        fontweight="bold",
        color=TEXT_COLOR,
    )
    axis.set_xlim(-0.52, 2.52)
    axis.set_ylim(-0.58, 3.58)
    axis.set_xticks(x)
    axis.set_xticklabels(
        ["Robust\nevidence", "Measurement / outcome\nboundary", "Unsupported\nextension"],
        fontsize=8.8,
    )
    axis.set_yticks(y)
    axis.set_yticklabels([CLAIM_LABELS[value] for value in CLAIM_ORDER], fontsize=9.0)
    axis.tick_params(axis="both", length=0, pad=7, colors=TEXT_COLOR)
    for side in ("top", "right", "left", "bottom"):
        axis.spines[side].set_visible(False)


def main() -> None:
    candidates = pd.read_parquet(CANDIDATES)
    claims = pd.read_parquet(CLAIMS)
    if len(candidates) != 65 or candidates["Candidate Universe"].nunique() != 4:
        raise RuntimeError("Unexpected candidate-ledger denominator structure.")
    if len(claims) != 12 or set(claims["Claim ID"]) != set(CLAIM_ORDER):
        raise RuntimeError("Unexpected claim-sensitivity structure.")

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
        figsize=(15.8, 6.2),
        gridspec_kw={"width_ratios": (1.12, 0.88), "wspace": 0.36},
    )
    plot_denominators(axes[0], candidates)
    plot_claim_boundaries(axes[1], claims)

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

    fig.subplots_adjust(left=0.15, right=0.98, top=0.88, bottom=0.14)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
