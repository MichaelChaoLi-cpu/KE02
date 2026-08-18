#!/usr/bin/env python3
"""Apply the assistant's first-pass blind labels to the Mashiki validation sample."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
LABEL_PATH = ROOT / "data/exp/reconstruction-validation/mashiki/labels_round1.csv"

# Each tuple contains label/confidence for pairs 1, 2, and 3.  These judgements
# were made from the A-F blind panels before opening blind_mapping.csv.
LABELS: dict[str, tuple[str, str, str, str, str, str]] = {
    "RV001": ("left_only_building", "high", "left_only_building", "high", "changed_both_present", "medium"),
    "RV002": ("neither_present", "high", "right_only_building", "high", "right_only_building", "high"),
    "RV003": ("left_only_building", "high", "left_only_building", "high", "changed_both_present", "high"),
    "RV004": ("stable_both_present", "medium", "stable_both_present", "medium", "right_only_building", "high"),
    "RV005": ("stable_both_present", "high", "changed_both_present", "medium", "changed_both_present", "high"),
    "RV006": ("stable_both_present", "high", "changed_both_present", "high", "changed_both_present", "high"),
    "RV007": ("stable_both_present", "high", "stable_both_present", "high", "stable_both_present", "high"),
    "RV008": ("neither_present", "high", "neither_present", "medium", "left_only_building", "medium"),
    "RV009": ("stable_both_present", "high", "changed_both_present", "high", "left_only_building", "high"),
    "RV010": ("uninterpretable", "low", "changed_both_present", "low", "changed_both_present", "medium"),
    "RV011": ("stable_both_present", "low", "stable_both_present", "low", "changed_both_present", "low"),
    "RV012": ("stable_both_present", "medium", "changed_both_present", "high", "right_only_building", "high"),
    "RV013": ("stable_both_present", "low", "changed_both_present", "medium", "stable_both_present", "medium"),
    "RV014": ("stable_both_present", "high", "changed_both_present", "medium", "changed_both_present", "high"),
    "RV015": ("neither_present", "medium", "right_only_building", "high", "left_only_building", "medium"),
    "RV016": ("neither_present", "medium", "right_only_building", "low", "uninterpretable", "low"),
    "RV017": ("stable_both_present", "high", "stable_both_present", "high", "stable_both_present", "high"),
    "RV018": ("changed_both_present", "high", "changed_both_present", "high", "changed_both_present", "high"),
    "RV019": ("left_only_building", "high", "right_only_building", "high", "changed_both_present", "medium"),
    "RV020": ("left_only_building", "high", "left_only_building", "high", "left_only_building", "high"),
    "RV021": ("neither_present", "high", "right_only_building", "high", "stable_both_present", "high"),
    "RV022": ("stable_both_present", "low", "changed_both_present", "low", "right_only_building", "high"),
    "RV023": ("neither_present", "high", "neither_present", "high", "left_only_building", "high"),
    "RV024": ("changed_both_present", "medium", "changed_both_present", "low", "right_only_building", "high"),
    "RV025": ("stable_both_present", "high", "changed_both_present", "high", "changed_both_present", "high"),
    "RV026": ("neither_present", "medium", "left_only_building", "low", "left_only_building", "medium"),
    "RV027": ("neither_present", "high", "neither_present", "high", "neither_present", "high"),
    "RV028": ("neither_present", "high", "neither_present", "high", "neither_present", "high"),
    "RV029": ("neither_present", "high", "neither_present", "high", "left_only_building", "low"),
    "RV030": ("stable_both_present", "medium", "left_only_building", "high", "right_only_building", "high"),
    "RV031": ("neither_present", "high", "neither_present", "high", "right_only_building", "low"),
    "RV032": ("left_only_building", "high", "left_only_building", "high", "neither_present", "medium"),
    "RV033": ("neither_present", "high", "neither_present", "high", "neither_present", "high"),
    "RV034": ("stable_both_present", "high", "stable_both_present", "high", "stable_both_present", "high"),
    "RV035": ("neither_present", "high", "right_only_building", "low", "uninterpretable", "low"),
    "RV036": ("stable_both_present", "low", "stable_both_present", "low", "stable_both_present", "medium"),
    "RV037": ("neither_present", "high", "neither_present", "high", "neither_present", "high"),
    "RV038": ("changed_both_present", "high", "changed_both_present", "high", "stable_both_present", "high"),
    "RV039": ("uninterpretable", "low", "uninterpretable", "low", "neither_present", "medium"),
    "RV040": ("stable_both_present", "high", "changed_both_present", "high", "changed_both_present", "medium"),
    "RV041": ("right_only_building", "high", "right_only_building", "high", "changed_both_present", "medium"),
    "RV042": ("stable_both_present", "high", "stable_both_present", "high", "changed_both_present", "high"),
    "RV043": ("stable_both_present", "medium", "changed_both_present", "high", "changed_both_present", "high"),
    "RV044": ("neither_present", "medium", "right_only_building", "medium", "right_only_building", "high"),
    "RV045": ("right_only_building", "medium", "right_only_building", "high", "changed_both_present", "high"),
    "RV046": ("neither_present", "medium", "right_only_building", "low", "changed_both_present", "medium"),
    "RV047": ("stable_both_present", "medium", "changed_both_present", "medium", "changed_both_present", "medium"),
    "RV048": ("stable_both_present", "high", "changed_both_present", "high", "changed_both_present", "high"),
    "RV049": ("stable_both_present", "medium", "changed_both_present", "medium", "changed_both_present", "high"),
    "RV050": ("stable_both_present", "medium", "right_only_building", "high", "changed_both_present", "high"),
    "RV051": ("left_only_building", "medium", "changed_both_present", "low", "changed_both_present", "medium"),
    "RV052": ("right_only_building", "low", "left_only_building", "low", "neither_present", "medium"),
    "RV053": ("changed_both_present", "medium", "changed_both_present", "high", "changed_both_present", "high"),
    "RV054": ("stable_both_present", "low", "changed_both_present", "medium", "changed_both_present", "medium"),
    "RV055": ("stable_both_present", "high", "changed_both_present", "medium", "left_only_building", "medium"),
    "RV056": ("left_only_building", "high", "left_only_building", "high", "changed_both_present", "medium"),
    "RV057": ("stable_both_present", "high", "changed_both_present", "high", "stable_both_present", "medium"),
    "RV058": ("neither_present", "high", "neither_present", "high", "neither_present", "high"),
    "RV059": ("stable_both_present", "high", "changed_both_present", "high", "changed_both_present", "high"),
    "RV060": ("neither_present", "high", "right_only_building", "high", "stable_both_present", "high"),
    "RV061": ("stable_both_present", "low", "changed_both_present", "medium", "stable_both_present", "high"),
    "RV062": ("stable_both_present", "medium", "changed_both_present", "high", "changed_both_present", "high"),
    "RV063": ("changed_both_present", "medium", "left_only_building", "medium", "right_only_building", "high"),
    "RV064": ("changed_both_present", "medium", "changed_both_present", "high", "changed_both_present", "high"),
    "RV065": ("stable_both_present", "medium", "changed_both_present", "medium", "right_only_building", "medium"),
    "RV066": ("neither_present", "high", "right_only_building", "low", "neither_present", "medium"),
    "RV067": ("stable_both_present", "medium", "changed_both_present", "high", "stable_both_present", "high"),
    "RV068": ("stable_both_present", "medium", "changed_both_present", "high", "changed_both_present", "high"),
    "RV069": ("left_only_building", "medium", "right_only_building", "medium", "changed_both_present", "low"),
    "RV070": ("stable_both_present", "medium", "changed_both_present", "high", "changed_both_present", "high"),
    "RV071": ("stable_both_present", "high", "changed_both_present", "high", "changed_both_present", "high"),
    "RV072": ("stable_both_present", "high", "changed_both_present", "high", "changed_both_present", "high"),
    "RV073": ("stable_both_present", "medium", "changed_both_present", "high", "changed_both_present", "high"),
    "RV074": ("stable_both_present", "medium", "left_only_building", "high", "left_only_building", "high"),
    "RV075": ("stable_both_present", "high", "changed_both_present", "high", "changed_both_present", "high"),
    "RV076": ("changed_both_present", "medium", "changed_both_present", "medium", "right_only_building", "high"),
    "RV077": ("neither_present", "high", "neither_present", "medium", "left_only_building", "medium"),
    "RV078": ("stable_both_present", "high", "changed_both_present", "high", "changed_both_present", "high"),
    "RV079": ("stable_both_present", "medium", "changed_both_present", "high", "changed_both_present", "high"),
    "RV080": ("stable_both_present", "medium", "changed_both_present", "high", "changed_both_present", "medium"),
    "RV081": ("stable_both_present", "low", "changed_both_present", "medium", "changed_both_present", "high"),
    "RV082": ("left_only_building", "medium", "changed_both_present", "medium", "changed_both_present", "high"),
    "RV083": ("stable_both_present", "high", "changed_both_present", "medium", "changed_both_present", "high"),
    "RV084": ("stable_both_present", "high", "changed_both_present", "high", "changed_both_present", "high"),
    "RV085": ("stable_both_present", "high", "changed_both_present", "high", "changed_both_present", "high"),
    "RV086": ("stable_both_present", "medium", "changed_both_present", "high", "changed_both_present", "high"),
    "RV087": ("neither_present", "high", "right_only_building", "low", "left_only_building", "low"),
    "RV088": ("stable_both_present", "high", "changed_both_present", "high", "changed_both_present", "high"),
    "RV089": ("stable_both_present", "medium", "changed_both_present", "medium", "uninterpretable", "low"),
    "RV090": ("left_only_building", "high", "left_only_building", "high", "stable_both_present", "high"),
    "RV091": ("left_only_building", "high", "left_only_building", "high", "right_only_building", "high"),
    "RV092": ("stable_both_present", "high", "changed_both_present", "high", "changed_both_present", "high"),
    "RV093": ("right_only_building", "high", "left_only_building", "high", "changed_both_present", "medium"),
    "RV094": ("left_only_building", "high", "left_only_building", "high", "changed_both_present", "medium"),
    "RV095": ("right_only_building", "high", "left_only_building", "high", "changed_both_present", "high"),
    "RV096": ("right_only_building", "high", "left_only_building", "high", "changed_both_present", "high"),
    "RV097": ("right_only_building", "high", "left_only_building", "high", "stable_both_present", "high"),
    "RV098": ("neither_present", "high", "neither_present", "high", "left_only_building", "high"),
    "RV099": ("stable_both_present", "medium", "changed_both_present", "high", "changed_both_present", "high"),
    "RV100": ("neither_present", "high", "neither_present", "high", "neither_present", "high"),
}


def main() -> None:
    frame = pd.read_csv(LABEL_PATH, dtype=str).fillna("")
    expected = set(frame["Validation ID"])
    if expected != set(LABELS):
        raise RuntimeError("label dictionary does not match validation IDs")
    for validation_id, values in LABELS.items():
        row = frame["Validation ID"].eq(validation_id)
        for pair_number in range(1, 4):
            frame.loc[row, f"Round 1 Pair {pair_number} Label"] = values[(pair_number - 1) * 2]
            frame.loc[row, f"Round 1 Pair {pair_number} Confidence"] = values[(pair_number - 1) * 2 + 1]
    allowed_labels = {
        "left_only_building",
        "right_only_building",
        "changed_both_present",
        "stable_both_present",
        "neither_present",
        "uninterpretable",
    }
    allowed_confidence = {"high", "medium", "low"}
    for pair_number in range(1, 4):
        if not set(frame[f"Round 1 Pair {pair_number} Label"]).issubset(allowed_labels):
            raise RuntimeError(f"invalid pair {pair_number} label")
        if not set(frame[f"Round 1 Pair {pair_number} Confidence"]).issubset(allowed_confidence):
            raise RuntimeError(f"invalid pair {pair_number} confidence")
    frame.to_csv(LABEL_PATH, index=False)
    print(frame.filter(like="Label").stack().value_counts().to_string())
    print(frame.filter(like="Confidence").stack().value_counts().to_string())


if __name__ == "__main__":
    main()
