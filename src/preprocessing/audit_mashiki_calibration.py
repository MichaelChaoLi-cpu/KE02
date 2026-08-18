#!/usr/bin/env python3
"""Audit labeling consistency and score usefulness for the Mashiki pilot."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score


ROOT = Path(__file__).resolve().parents[2]
LABELED_PATH = ROOT / "data/processed/mashiki_calibration_labeled_preprocessed.parquet"
CANDIDATE_PATH = ROOT / "data/processed/mashiki_building_candidates_preprocessed.parquet"
OUTPUT_ROOT = ROOT / "data/exp/building-label-calibration/mashiki/audit"

CLEAR = "clear_visible_change"
NO = "no_visible_change"
POSSIBLE = "possible_visible_change"
UNINTERPRETABLE = "target_absent_or_uninterpretable"


def safe_ratio(numerator: float, denominator: float) -> float:
    return float(numerator / denominator) if denominator else float("nan")


def score_diagnostics(
    labeled: pd.DataFrame,
    candidates: pd.DataFrame,
    year: str,
) -> dict[str, float | int | str]:
    label_column = f"Adjudicated {year} Label"
    score_column = f"{year} Change Score"
    strong = labeled[label_column].isin([CLEAR, NO])
    frame = labeled.loc[strong, [label_column, score_column]].copy()
    outcome = (frame[label_column] == CLEAR).astype(int)
    threshold = float(candidates[score_column].quantile(0.85))
    predicted = frame[score_column] >= threshold
    true_positive = int((predicted & outcome.eq(1)).sum())
    false_positive = int((predicted & outcome.eq(0)).sum())
    false_negative = int((~predicted & outcome.eq(1)).sum())
    true_negative = int((~predicted & outcome.eq(0)).sum())
    return {
        "comparison": year,
        "strong_label_n": int(len(frame)),
        "clear_n": int(outcome.sum()),
        "no_change_n": int(outcome.eq(0).sum()),
        "candidate_score_q85_threshold": threshold,
        "roc_auc_enriched_panel": float(roc_auc_score(outcome, frame[score_column])),
        "average_precision_enriched_panel": float(
            average_precision_score(outcome, frame[score_column])
        ),
        "threshold_true_positive": true_positive,
        "threshold_false_positive": false_positive,
        "threshold_false_negative": false_negative,
        "threshold_true_negative": true_negative,
        "threshold_precision_enriched_panel": safe_ratio(
            true_positive, true_positive + false_positive
        ),
        "threshold_recall_enriched_panel": safe_ratio(
            true_positive, true_positive + false_negative
        ),
        "threshold_specificity_enriched_panel": safe_ratio(
            true_negative, true_negative + false_positive
        ),
        "scope_warning": (
            "calibration panel is deliberately enriched and spatially balanced; "
            "metrics are not population estimates"
        ),
    }


def format_number(value: float, digits: int = 3) -> str:
    if np.isnan(value):
        return "NA"
    return f"{value:.{digits}f}"


def main() -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    labeled = pd.read_parquet(LABELED_PATH)
    candidates = pd.read_parquet(CANDIDATE_PATH)

    label_counts = []
    for year in ["2016", "2026"]:
        counts = labeled[f"Adjudicated {year} Label"].value_counts()
        for label in [CLEAR, POSSIBLE, NO, UNINTERPRETABLE]:
            label_counts.append(
                {"comparison": year, "label": label, "count": int(counts.get(label, 0))}
            )
    label_counts_frame = pd.DataFrame(label_counts)
    label_counts_frame.to_csv(OUTPUT_ROOT / "label_counts.csv", index=False)

    stratum_frames = []
    for year in ["2016", "2026"]:
        table = pd.crosstab(
            labeled["Sampling Stratum"], labeled[f"Adjudicated {year} Label"]
        ).reset_index()
        table.insert(0, "comparison", year)
        stratum_frames.append(table)
    stratum_counts = pd.concat(stratum_frames, ignore_index=True).fillna(0)
    stratum_counts.to_csv(OUTPUT_ROOT / "stratum_label_counts.csv", index=False)

    score_summary_frames = []
    for year in ["2016", "2026"]:
        frame = (
            labeled.groupby(f"Adjudicated {year} Label")[f"{year} Change Score"]
            .agg(["count", "mean", "median", "min", "max"])
            .reset_index()
            .rename(columns={f"Adjudicated {year} Label": "label"})
        )
        frame.insert(0, "comparison", year)
        score_summary_frames.append(frame)
    pd.concat(score_summary_frames, ignore_index=True).to_csv(
        OUTPUT_ROOT / "score_by_label.csv", index=False
    )

    diagnostics = pd.DataFrame(
        [
            score_diagnostics(labeled, candidates, "2016"),
            score_diagnostics(labeled, candidates, "2026"),
        ]
    )
    diagnostics.to_csv(OUTPUT_ROOT / "score_diagnostics.csv", index=False)

    consistency = []
    for pair, comparison in [(1, "2016"), (2, "2026")]:
        first = labeled[f"Round 1 Pair {pair} Label"]
        second = labeled[f"Round 2 Pair {pair} Label"]
        consistency.append(
            {
                "comparison": comparison,
                "label_agreement_count": int((first == second).sum()),
                "label_changed_count": int((first != second).sum()),
                "label_agreement_rate": float((first == second).mean()),
                "reviewer_independence": "same AI reviewer; two-pass consistency only",
            }
        )
    consistency_frame = pd.DataFrame(consistency)
    consistency_frame.to_csv(OUTPUT_ROOT / "review_consistency.csv", index=False)

    d2016 = diagnostics.loc[diagnostics["comparison"] == "2016"].iloc[0]
    d2026 = diagnostics.loc[diagnostics["comparison"] == "2026"].iloc[0]
    agreement_2016 = consistency_frame.loc[
        consistency_frame["comparison"] == "2016", "label_agreement_rate"
    ].iloc[0]
    agreement_2026 = consistency_frame.loc[
        consistency_frame["comparison"] == "2026", "label_agreement_rate"
    ].iloc[0]
    report = f"""# Mashiki building-label calibration feasibility audit

Date: 2026-08-18  
Status: exploratory calibration; not independent validation or damage ground truth

## Decision

- **2016 imagery:** conditional pass for manually/AI-screened *candidate mainshock damage proxies* at building level. It does not recover damage caused by the 14 April foreshock because the baseline is already post-foreshock.
- **2026 imagery:** fail for event-attributed building-damage labels. The available baseline is PLATEAU FY2023, so every visible change through the 2026 post-event image is confounded by ordinary construction, demolition, and roof replacement.
- **Automated pixel-change score:** fail as a stand-alone classifier for either comparison. It is useful only for candidate enrichment and must not be treated as a damage label.

## Calibration outcomes

| Comparison | Clear visible change | Possible | No visible change | Uninterpretable |
|---|---:|---:|---:|---:|
| 2016 | 10 | 11 | 68 | 11 |
| 2026 | 6 | 0 | 91 | 3 |

All six clear 2026 cases are long-interval building or roof changes; **zero are eligible for earthquake attribution with the current baseline**. The ten clear 2016 cases include blue roof coverings, roof-surface loss, and buildings disappearing between the post-foreshock and post-mainshock acquisitions. They are candidates, not confirmed structural-damage observations.

## Score audit

| Comparison | ROC AUC | Average precision | q85 precision | q85 recall | q85 specificity |
|---|---:|---:|---:|---:|---:|
| 2016 | {format_number(float(d2016['roc_auc_enriched_panel']))} | {format_number(float(d2016['average_precision_enriched_panel']))} | {format_number(float(d2016['threshold_precision_enriched_panel']))} | {format_number(float(d2016['threshold_recall_enriched_panel']))} | {format_number(float(d2016['threshold_specificity_enriched_panel']))} |
| 2026 | {format_number(float(d2026['roc_auc_enriched_panel']))} | {format_number(float(d2026['average_precision_enriched_panel']))} | {format_number(float(d2026['threshold_precision_enriched_panel']))} | {format_number(float(d2026['threshold_recall_enriched_panel']))} | {format_number(float(d2026['threshold_specificity_enriched_panel']))} |

These metrics use only clear/no-change cases and an intentionally enriched 100-building panel. They quantify screening behavior inside this panel, not population accuracy. The 2016 score AUC of {format_number(float(d2016['roc_auc_enriched_panel']))} is too weak for automatic labeling, and clear cases occurring in the stable-low stratum demonstrate false negatives.

## Review stability and limitations

- Blind-to-revealed label agreement was {format_number(float(agreement_2016), 2)} for 2016 and {format_number(float(agreement_2026), 2)} for 2026. Date revelation changed {int(100 * (1 - agreement_2016))} and {int(100 * (1 - agreement_2026))} labels, respectively.
- Both passes were conducted by the same AI system. They are not independent annotators, do not establish inter-rater reliability, and do not replace an official damage inventory or trained human validation sample.
- The PLATEAU geometry sometimes represents a roof edge/surface unsuitable as a footprint; target absence, parallax, shadow, trees, flight-strip seams, radiometry, and roof reflectance remain material error sources.
- The calibration sample deliberately over-represents high-score and stable-low cases and cannot estimate Mashiki-wide prevalence without a probability sample and sampling weights.

## Research implication

Do not scale the current score into a 2016-versus-2026 building-damage outcome. The defensible next route is to use the 2016 candidates to test linkage against an official building-damage inventory, while treating 2026 orthophotos as contextual evidence or a long-interval urban-change outcome. A genuine 2026 building-damage comparison requires a near-event pre-earthquake orthophoto or authoritative post-disaster damage labels.
"""
    (OUTPUT_ROOT / "feasibility_audit.md").write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
