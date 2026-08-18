#!/usr/bin/env python3
"""Apply the assistant's targeted second-pass blind review labels."""

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
LABEL_PATH = ROOT / "data/exp/reconstruction-validation/mashiki/round2/labels_round2.csv"

LABELS: dict[str, tuple[str, str]] = {
    "R2001": ("left_only_building", "high"),
    "R2002": ("left_only_building", "low"),
    "R2003": ("stable_both_present", "high"),
    "R2004": ("changed_both_present", "medium"),
    "R2005": ("left_only_building", "medium"),
    "R2006": ("left_only_building", "high"),
    "R2007": ("right_only_building", "high"),
    "R2008": ("left_only_building", "medium"),
    "R2009": ("uninterpretable", "low"),
    "R2010": ("changed_both_present", "high"),
    "R2011": ("left_only_building", "high"),
    "R2012": ("neither_present", "high"),
    "R2013": ("neither_present", "high"),
    "R2014": ("changed_both_present", "high"),
    "R2015": ("left_only_building", "high"),
    "R2016": ("changed_both_present", "medium"),
    "R2017": ("right_only_building", "medium"),
    "R2018": ("stable_both_present", "medium"),
    "R2019": ("left_only_building", "medium"),
    "R2020": ("changed_both_present", "high"),
    "R2021": ("left_only_building", "high"),
    "R2022": ("changed_both_present", "medium"),
    "R2023": ("right_only_building", "high"),
    "R2024": ("right_only_building", "medium"),
    "R2025": ("left_only_building", "medium"),
    "R2026": ("neither_present", "medium"),
    "R2027": ("changed_both_present", "high"),
    "R2028": ("stable_both_present", "high"),
    "R2029": ("right_only_building", "high"),
    "R2030": ("changed_both_present", "medium"),
    "R2031": ("stable_both_present", "high"),
    "R2032": ("changed_both_present", "medium"),
    "R2033": ("neither_present", "high"),
    "R2034": ("changed_both_present", "high"),
    "R2035": ("uninterpretable", "low"),
    "R2036": ("left_only_building", "high"),
    "R2037": ("changed_both_present", "medium"),
    "R2038": ("changed_both_present", "high"),
    "R2039": ("changed_both_present", "low"),
    "R2040": ("stable_both_present", "medium"),
    "R2041": ("right_only_building", "high"),
    "R2042": ("neither_present", "medium"),
    "R2043": ("right_only_building", "high"),
    "R2044": ("stable_both_present", "low"),
    "R2045": ("changed_both_present", "medium"),
    "R2046": ("stable_both_present", "high"),
    "R2047": ("right_only_building", "medium"),
    "R2048": ("changed_both_present", "low"),
    "R2049": ("changed_both_present", "high"),
    "R2050": ("stable_both_present", "low"),
    "R2051": ("stable_both_present", "low"),
    "R2052": ("left_only_building", "medium"),
    "R2053": ("neither_present", "high"),
}


def main() -> None:
    frame = pd.read_csv(LABEL_PATH, dtype=str).fillna("")
    if set(frame["Review ID"]) != set(LABELS):
        raise RuntimeError("round-2 dictionary does not match review IDs")
    for review_id, (label, confidence) in LABELS.items():
        row = frame["Review ID"].eq(review_id)
        frame.loc[row, "Round 2 Label"] = label
        frame.loc[row, "Round 2 Confidence"] = confidence
    frame.to_csv(LABEL_PATH, index=False)
    print(frame["Round 2 Label"].value_counts().to_string())
    print(frame["Round 2 Confidence"].value_counts().to_string())


if __name__ == "__main__":
    main()
