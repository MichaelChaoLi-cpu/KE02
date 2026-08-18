#!/usr/bin/env python3
"""Apply the documented blind first-pass labels to the Mashiki calibration CSV.

The four-class vocabulary is deliberately observational: it records whether a
change is visible in the orthophotos, not whether an earthquake caused it.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
LABELS_PATH = ROOT / "data/exp/building-label-calibration/mashiki/labels.csv"

NO = "no_visible_change"
POSSIBLE = "possible_visible_change"
CLEAR = "clear_visible_change"
UNINTERPRETABLE = "target_absent_or_uninterpretable"

# calibration_id: (pair_1_label, pair_1_confidence,
#                  pair_2_label, pair_2_confidence, exclusion_reason)
ROUND_1 = {
    "M001": (POSSIBLE, "medium", POSSIBLE, "low", ""),
    "M002": (NO, "high", NO, "high", ""),
    "M003": (NO, "high", CLEAR, "high", ""),
    "M004": (NO, "high", NO, "high", ""),
    "M005": (NO, "high", NO, "high", ""),
    "M006": (CLEAR, "high", NO, "high", ""),
    "M007": (NO, "high", NO, "high", ""),
    "M008": (NO, "high", NO, "high", ""),
    "M009": (NO, "high", NO, "high", ""),
    "M010": (POSSIBLE, "low", NO, "high", ""),
    "M011": (NO, "high", NO, "high", ""),
    "M012": (UNINTERPRETABLE, "high", NO, "high", "pair_1_target_not_visible"),
    "M013": (NO, "high", CLEAR, "high", ""),
    "M014": (POSSIBLE, "low", POSSIBLE, "low", ""),
    "M015": (NO, "high", NO, "high", ""),
    "M016": (CLEAR, "high", NO, "high", ""),
    "M017": (CLEAR, "high", NO, "high", ""),
    "M018": (NO, "high", NO, "high", ""),
    "M019": (NO, "high", NO, "high", ""),
    "M020": (NO, "high", NO, "high", ""),
    "M021": (NO, "high", NO, "high", ""),
    "M022": (POSSIBLE, "low", NO, "high", ""),
    "M023": (NO, "high", NO, "high", ""),
    "M024": (POSSIBLE, "medium", NO, "high", ""),
    "M025": (POSSIBLE, "low", NO, "high", ""),
    "M026": (NO, "high", NO, "high", ""),
    "M027": (NO, "high", NO, "high", ""),
    "M028": (NO, "high", NO, "high", ""),
    "M029": (NO, "high", POSSIBLE, "low", ""),
    "M030": (NO, "high", NO, "high", ""),
    "M031": (NO, "high", NO, "high", ""),
    "M032": (NO, "high", NO, "high", ""),
    "M033": (UNINTERPRETABLE, "high", NO, "high", "pair_1_target_not_visible"),
    "M034": (UNINTERPRETABLE, "high", NO, "high", "pair_1_target_not_visible"),
    "M035": (NO, "high", NO, "high", ""),
    "M036": (CLEAR, "high", NO, "high", ""),
    "M037": (NO, "high", NO, "high", ""),
    "M038": (POSSIBLE, "low", NO, "high", ""),
    "M039": (CLEAR, "high", NO, "high", ""),
    "M040": (NO, "high", POSSIBLE, "low", ""),
    "M041": (POSSIBLE, "medium", NO, "high", ""),
    "M042": (NO, "high", NO, "high", ""),
    "M043": (CLEAR, "high", NO, "high", ""),
    "M044": (NO, "high", NO, "high", ""),
    "M045": (POSSIBLE, "low", NO, "high", ""),
    "M046": (NO, "high", NO, "high", ""),
    "M047": (POSSIBLE, "medium", NO, "high", ""),
    "M048": (UNINTERPRETABLE, "high", POSSIBLE, "low", "pair_1_target_not_visible"),
    "M049": (CLEAR, "high", NO, "high", ""),
    "M050": (POSSIBLE, "low", NO, "high", ""),
    "M051": (POSSIBLE, "low", NO, "high", ""),
    "M052": (NO, "high", POSSIBLE, "low", ""),
    "M053": (NO, "high", NO, "high", ""),
    "M054": (NO, "high", NO, "high", ""),
    "M055": (POSSIBLE, "low", NO, "high", ""),
    "M056": (NO, "high", NO, "high", ""),
    "M057": (NO, "high", POSSIBLE, "low", ""),
    "M058": (CLEAR, "medium", POSSIBLE, "low", ""),
    "M059": (NO, "high", UNINTERPRETABLE, "high", "pair_2_target_obscured"),
    "M060": (POSSIBLE, "low", POSSIBLE, "medium", ""),
    "M061": (NO, "high", NO, "high", ""),
    "M062": (UNINTERPRETABLE, "high", POSSIBLE, "low", "pair_1_target_not_visible"),
    "M063": (NO, "high", NO, "high", ""),
    "M064": (UNINTERPRETABLE, "high", UNINTERPRETABLE, "high", "footprint_not_a_roof_surface"),
    "M065": (NO, "high", NO, "high", ""),
    "M066": (NO, "high", NO, "high", ""),
    "M067": (NO, "high", NO, "high", ""),
    "M068": (UNINTERPRETABLE, "high", NO, "high", "pair_1_target_not_visible"),
    "M069": (UNINTERPRETABLE, "high", NO, "high", "pair_1_target_not_visible"),
    "M070": (NO, "high", NO, "high", ""),
    "M071": (POSSIBLE, "medium", NO, "high", ""),
    "M072": (UNINTERPRETABLE, "high", POSSIBLE, "medium", "pair_1_target_not_visible"),
    "M073": (NO, "high", NO, "high", ""),
    "M074": (NO, "high", NO, "high", ""),
    "M075": (NO, "high", NO, "high", ""),
    "M076": (POSSIBLE, "low", NO, "high", ""),
    "M077": (POSSIBLE, "low", NO, "high", ""),
    "M078": (POSSIBLE, "medium", NO, "high", ""),
    "M079": (NO, "high", NO, "high", ""),
    "M080": (NO, "high", NO, "high", ""),
    "M081": (POSSIBLE, "medium", POSSIBLE, "medium", ""),
    "M082": (CLEAR, "high", CLEAR, "high", ""),
    "M083": (NO, "high", NO, "high", ""),
    "M084": (UNINTERPRETABLE, "high", POSSIBLE, "low", "pair_1_target_not_visible"),
    "M085": (NO, "high", POSSIBLE, "low", ""),
    "M086": (NO, "high", NO, "high", ""),
    "M087": (NO, "high", NO, "high", ""),
    "M088": (NO, "high", NO, "high", ""),
    "M089": (POSSIBLE, "low", POSSIBLE, "medium", ""),
    "M090": (POSSIBLE, "low", NO, "high", ""),
    "M091": (NO, "high", NO, "high", ""),
    "M092": (NO, "high", NO, "high", ""),
    "M093": (POSSIBLE, "low", CLEAR, "medium", ""),
    "M094": (UNINTERPRETABLE, "high", UNINTERPRETABLE, "high", "target_obscured_or_too_small"),
    "M095": (NO, "high", NO, "high", ""),
    "M096": (NO, "high", NO, "high", ""),
    "M097": (NO, "high", NO, "high", ""),
    "M098": (NO, "high", NO, "high", ""),
    "M099": (NO, "high", NO, "high", ""),
    "M100": (POSSIBLE, "low", NO, "high", ""),
}


def main() -> None:
    labels = pd.read_csv(LABELS_PATH, dtype=str, keep_default_na=False)
    expected = set(labels["Calibration ID"])
    if set(ROUND_1) != expected:
        missing = sorted(expected - set(ROUND_1))
        extra = sorted(set(ROUND_1) - expected)
        raise RuntimeError(f"label key mismatch; missing={missing}, extra={extra}")

    columns = [
        "Round 1 Pair 1 Label",
        "Round 1 Pair 1 Confidence",
        "Round 1 Pair 2 Label",
        "Round 1 Pair 2 Confidence",
        "Round 1 Exclusion Reason",
    ]
    for row_index, calibration_id in labels["Calibration ID"].items():
        labels.loc[row_index, columns] = ROUND_1[calibration_id]
    labels.to_csv(LABELS_PATH, index=False)


if __name__ == "__main__":
    main()
