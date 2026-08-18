#!/usr/bin/env python3
"""Apply date-revealed review and create the adjudicated calibration dataset.

Round 2 was performed by the same AI reviewer as Round 1. It is a consistency
and temporal-interpretation pass, not an independent inter-rater assessment.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
CALIBRATION_ROOT = ROOT / "data/exp/building-label-calibration/mashiki"
LABELS_PATH = CALIBRATION_ROOT / "labels.csv"
SAMPLE_PATH = ROOT / "data/processed/mashiki_calibration_sample_preprocessed.parquet"
OUTPUT_PATH = ROOT / "data/processed/mashiki_calibration_labeled_preprocessed.parquet"

NO = "no_visible_change"
POSSIBLE = "possible_visible_change"
CLEAR = "clear_visible_change"
UNINTERPRETABLE = "target_absent_or_uninterpretable"

# Only records whose revealed-date review changed the blind first-pass result
# are overridden. Values are pair-1 label/confidence and pair-2 label/confidence.
ROUND_2_OVERRIDES = {
    "M001": (CLEAR, "high", NO, "high"),
    "M006": (POSSIBLE, "low", NO, "high"),
    "M014": (CLEAR, "medium", NO, "high"),
    "M022": (NO, "medium", NO, "high"),
    "M025": (CLEAR, "medium", NO, "high"),
    "M029": (NO, "high", NO, "medium"),
    "M039": (POSSIBLE, "low", NO, "high"),
    "M040": (NO, "high", NO, "medium"),
    "M041": (NO, "medium", NO, "high"),
    "M045": (NO, "medium", NO, "high"),
    "M047": (CLEAR, "medium", NO, "high"),
    "M048": (UNINTERPRETABLE, "high", NO, "medium"),
    "M050": (NO, "medium", NO, "high"),
    "M051": (NO, "medium", NO, "high"),
    "M052": (NO, "high", NO, "low"),
    "M055": (NO, "medium", NO, "high"),
    "M057": (NO, "high", NO, "low"),
    "M058": (POSSIBLE, "medium", NO, "high"),
    "M060": (POSSIBLE, "low", NO, "medium"),
    "M062": (UNINTERPRETABLE, "high", NO, "medium"),
    "M071": (POSSIBLE, "low", NO, "high"),
    "M072": (UNINTERPRETABLE, "high", NO, "low"),
    "M076": (NO, "medium", NO, "high"),
    "M077": (NO, "medium", NO, "high"),
    "M078": (POSSIBLE, "low", NO, "high"),
    "M081": (POSSIBLE, "medium", CLEAR, "medium"),
    "M084": (UNINTERPRETABLE, "medium", NO, "medium"),
    "M085": (NO, "high", NO, "low"),
    "M089": (NO, "low", CLEAR, "high"),
    "M090": (NO, "low", NO, "high"),
    "M093": (NO, "medium", CLEAR, "medium"),
}

VISIBLE_2016_SUBTYPE = {
    "M001": "blue roof covering appears after the mainshock",
    "M014": "substantial roof-surface appearance change after the mainshock",
    "M016": "blue roof covering appears after the mainshock",
    "M017": "blue roof covering appears after the mainshock",
    "M025": "bright roof covering or exposed roof surface appears after the mainshock",
    "M036": "building visible after the foreshock is absent after the mainshock",
    "M043": "already disturbed building shows further visible loss after the mainshock",
    "M047": "rooftop array or roof surface disappears after the mainshock",
    "M049": "blue roof covering appears after the mainshock",
    "M082": "building visible after the foreshock is absent after the mainshock",
}

VISIBLE_2026_SUBTYPE = {
    "M003": "clear building-stock change",
    "M013": "clear building-stock change",
    "M081": "clear rooftop-surface or rooftop-array change",
    "M082": "clear building loss or redevelopment",
    "M089": "clear building reconstruction or replacement",
    "M093": "clear building or rooftop change",
}


def combine_notes(parts: list[str]) -> str:
    return " ".join(part for part in parts if part)


def main() -> None:
    labels = pd.read_csv(LABELS_PATH, dtype=str, keep_default_na=False)
    sample = pd.read_parquet(SAMPLE_PATH)

    labels["Round 2 Pair 1 Label"] = labels["Round 1 Pair 1 Label"]
    labels["Round 2 Pair 1 Confidence"] = labels["Round 1 Pair 1 Confidence"]
    labels["Round 2 Pair 2 Label"] = labels["Round 1 Pair 2 Label"]
    labels["Round 2 Pair 2 Confidence"] = labels["Round 1 Pair 2 Confidence"]
    labels["Round 2 Exclusion Reason"] = labels["Round 1 Exclusion Reason"]

    for calibration_id, values in ROUND_2_OVERRIDES.items():
        row = labels["Calibration ID"] == calibration_id
        if row.sum() != 1:
            raise RuntimeError(f"expected exactly one row for {calibration_id}")
        labels.loc[row, [
            "Round 2 Pair 1 Label",
            "Round 2 Pair 1 Confidence",
            "Round 2 Pair 2 Label",
            "Round 2 Pair 2 Confidence",
        ]] = values

    labels["Adjudicated 2016 Label"] = labels["Round 2 Pair 1 Label"]
    labels["Adjudicated 2016 Confidence"] = labels["Round 2 Pair 1 Confidence"]
    labels["Adjudicated 2026 Label"] = labels["Round 2 Pair 2 Label"]
    labels["Adjudicated 2026 Confidence"] = labels["Round 2 Pair 2 Confidence"]

    notes: list[str] = []
    for _, row in labels.iterrows():
        calibration_id = row["Calibration ID"]
        label_2016 = row["Adjudicated 2016 Label"]
        label_2026 = row["Adjudicated 2026 Label"]
        parts: list[str] = []
        if calibration_id in VISIBLE_2016_SUBTYPE:
            parts.append(
                f"2016: {VISIBLE_2016_SUBTYPE[calibration_id]}; this is a candidate "
                "mainshock damage proxy, not validated damage ground truth."
            )
        elif label_2016 == POSSIBLE:
            parts.append(
                "2016: possible roof-surface difference remains after review; imagery, "
                "radiometry, or parallax cannot be excluded."
            )
        elif label_2016 == UNINTERPRETABLE:
            parts.append("2016: target is absent, obscured, or not a usable roof footprint.")

        if calibration_id in VISIBLE_2026_SUBTYPE:
            parts.append(
                f"2026: {VISIBLE_2026_SUBTYPE[calibration_id]}; the FY2023-to-2026 "
                "interval is too long for earthquake attribution."
            )
        elif label_2026 == POSSIBLE:
            parts.append(
                "2026: possible long-interval appearance change is not event-attributable."
            )
        elif label_2026 == UNINTERPRETABLE:
            parts.append("2026: target is obscured or not a usable roof footprint.")
        notes.append(combine_notes(parts))
    labels["Adjudication Note"] = notes
    labels.to_csv(LABELS_PATH, index=False)

    labeled = sample.merge(labels, on=["Calibration ID", "Sampling Stratum"], validate="one_to_one")
    labeled["2016 Mainshock Proxy Status"] = labeled["Adjudicated 2016 Label"].map(
        {
            CLEAR: "candidate_proxy_only",
            POSSIBLE: "uncertain",
            NO: "no_visible_change",
            UNINTERPRETABLE: "not_usable",
        }
    )
    labeled["2016 Causal Window"] = (
        "mainshock_increment_only; baseline_is_already_post_foreshock"
    )
    labeled["2026 Event Attribution Eligible"] = False
    labeled["2026 Attribution Limitation"] = (
        "FY2023 baseline to 2026 post-event interval confounds ordinary construction, "
        "demolition, roof replacement, and earthquake effects"
    )
    labeled["Review Independence"] = (
        "same_AI_reviewer_two_pass;_not_independent_inter_rater_validation"
    )
    labeled.to_parquet(OUTPUT_PATH, index=False)


if __name__ == "__main__":
    main()
