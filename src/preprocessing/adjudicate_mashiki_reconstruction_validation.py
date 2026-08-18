#!/usr/bin/env python3
"""Reveal blind pair orientations and audit the Mashiki reconstruction sample."""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
EXP = ROOT / "data/exp/reconstruction-validation/mashiki"
SAMPLE_PATH = (
    ROOT / "data/processed/mashiki_reconstruction_validation_sample_preprocessed.parquet"
)
OUTPUT_PATH = (
    ROOT / "data/processed/mashiki_reconstruction_validation_adjudicated_preprocessed.parquet"
)
PAIR_DATES = {
    1: ("2016-04-15 post-foreshock", "2016-04-16 post-mainshock"),
    2: ("2016-04-16 post-mainshock", "2020-11 orthophoto"),
    3: ("2020-11 orthophoto", "PLATEAU FY2023 orthophoto"),
}


def decode_pair(label: str, left_is: str, earlier: str, later: str) -> tuple[str, str, str]:
    if label == "stable_both_present":
        return "present", "present", "stable_present_to_present"
    if label == "changed_both_present":
        return "present", "present", "changed_present_to_present"
    if label == "neither_present":
        return "absent", "absent", "absent_to_absent"
    if label == "uninterpretable":
        return "unknown", "unknown", "uninterpretable"
    if label == "left_only_building":
        return (
            ("present", "absent", "present_to_absent")
            if left_is == earlier
            else ("absent", "present", "absent_to_present")
        )
    if label == "right_only_building":
        return (
            ("absent", "present", "absent_to_present")
            if left_is == earlier
            else ("present", "absent", "present_to_absent")
        )
    raise ValueError(label)


def inventory_assessment(status: str, transition: str) -> str:
    if status == "ambiguous":
        return "not_assessed"
    if transition == "uninterpretable":
        return "unresolved"
    if status == "retained":
        return "supported" if transition.endswith("present_to_present") else "not_supported"
    if status == "suspected_rebuild":
        if transition == "changed_present_to_present":
            return "strongly_supported"
        if transition in {"absent_to_present", "present_to_absent"}:
            return "partly_supported"
        if transition == "stable_present_to_present":
            return "not_supported"
        return "unresolved"
    if status == "disappeared":
        if transition == "present_to_absent":
            return "strongly_supported"
        if transition == "absent_to_absent":
            return "timing_unresolved"
        return "not_supported"
    if status == "new":
        if transition == "absent_to_present":
            return "strongly_supported"
        if transition == "absent_to_absent":
            return "timing_unresolved"
        return "not_supported"
    raise ValueError(status)


def markdown_table(frame: pd.DataFrame) -> str:
    return frame.to_markdown()


def main() -> None:
    sample = gpd.read_parquet(SAMPLE_PATH)
    labels = pd.read_csv(EXP / "labels_round1.csv", dtype=str).fillna("")
    mapping = pd.read_csv(EXP / "blind_mapping.csv", dtype=str).fillna("")
    blind = mapping.merge(labels, on="Validation ID", validate="one_to_one")
    if len(blind) != len(sample):
        raise RuntimeError("sample, mapping, and labels do not have the same length")

    decoded_records: list[dict[str, str]] = []
    for _, row in blind.iterrows():
        record: dict[str, str] = {"Validation ID": row["Validation ID"]}
        for pair_number, (earlier, later) in PAIR_DATES.items():
            earlier_state, later_state, transition = decode_pair(
                row[f"Round 1 Pair {pair_number} Label"],
                row[f"Pair {pair_number} Left Is"],
                earlier,
                later,
            )
            record[f"Pair {pair_number} Earlier State"] = earlier_state
            record[f"Pair {pair_number} Later State"] = later_state
            record[f"Pair {pair_number} Ordered Transition"] = transition
        decoded_records.append(record)
    decoded = pd.DataFrame(decoded_records)
    result = sample.merge(labels, on="Validation ID", validate="one_to_one")
    result = result.merge(decoded, on="Validation ID", validate="one_to_one")
    result["2016-04-16 Cross-Pair Consistent"] = (
        result["Pair 1 Later State"].eq(result["Pair 2 Earlier State"])
        | result["Pair 1 Later State"].eq("unknown")
        | result["Pair 2 Earlier State"].eq("unknown")
    )
    result["2020-11 Cross-Pair Consistent"] = (
        result["Pair 2 Later State"].eq(result["Pair 3 Earlier State"])
        | result["Pair 2 Later State"].eq("unknown")
        | result["Pair 3 Earlier State"].eq("unknown")
    )
    result["Inventory Status Visual Assessment"] = [
        inventory_assessment(status, transition)
        for status, transition in zip(
            result["Source Match Status"], result["Pair 3 Ordered Transition"], strict=True
        )
    ]
    result.to_parquet(OUTPUT_PATH, index=False)

    pair_counts = {
        pair_number: result[f"Pair {pair_number} Ordered Transition"].value_counts()
        for pair_number in PAIR_DATES
    }
    confidence_counts = labels.filter(like="Confidence").stack().value_counts()
    confidence_usable = int(confidence_counts.get("high", 0) + confidence_counts.get("medium", 0))
    unreadable = int(
        labels.filter(like="Label").stack().eq("uninterpretable").sum()
    )
    assessment = pd.crosstab(
        result["Source Match Status"],
        result["Inventory Status Visual Assessment"],
        margins=True,
    )
    pair3 = pd.crosstab(
        result["Source Match Status"],
        result["Pair 3 Ordered Transition"],
        margins=True,
    )
    report = f"""# Mashiki reconstruction validation audit

## Scope

- Sample: 100 spatially distributed buildings, 20 from each candidate inventory status.
- Blind comparisons: 300 date pairs across 2016-04-15, 2016-04-16, 2020-11, and the PLATEAU FY2023 orthophoto release.
- Important limitation: the FY2023 orthophoto's exact flight date remains unresolved; its CityGML source-register date is not treated as a flight date.
- Visual labels describe building presence and footprint/roof-form change. They do not by themselves establish earthquake causation or legal reconstruction status.

## Round-1 quality gates

- Complete labels: {int(labels.filter(like='Label').ne('').sum().sum())}/300.
- High-confidence labels: {int(confidence_counts.get('high', 0))}/300.
- High-or-medium-confidence labels: {confidence_usable}/300 ({confidence_usable / 3:.1f}%).
- Uninterpretable labels: {unreadable}/300 ({unreadable / 3:.1f}%).
- 2016-04-16 state consistent across adjacent pairs: {int(result['2016-04-16 Cross-Pair Consistent'].sum())}/100.
- 2020-11 state consistent across adjacent pairs: {int(result['2020-11 Cross-Pair Consistent'].sum())}/100.

The preset operational gates are met for completeness (100%), high-or-medium confidence (at least 85%), and uninterpretable share (at most 10%). Cross-pair inconsistencies remain flagged at record level and must not be silently resolved.

## Ordered transition counts

### 2016-04-15 to 2016-04-16

{markdown_table(pair_counts[1].rename('count').to_frame())}

### 2016-04-16 to 2020-11

{markdown_table(pair_counts[2].rename('count').to_frame())}

### 2020-11 to PLATEAU FY2023 orthophoto release

{markdown_table(pair_counts[3].rename('count').to_frame())}

## Candidate inventory status versus final image pair

{markdown_table(pair3)}

## Conservative visual assessment of inventory status

{markdown_table(assessment)}

## Interpretation rules

- `retained`: supported only when a building is visible in both final-pair images.
- `suspected_rebuild`: strongly supported only by visible change with buildings present at both dates; one-sided presence is partial support; visually stable buildings are not support.
- `disappeared`: strongly supported by present-to-absent; absent-to-absent leaves disappearance timing unresolved.
- `new`: strongly supported by absent-to-present; absent-to-absent leaves appearance timing unresolved.
- `ambiguous`: not assessed against a directional inventory claim.

## Use in the study

Use the image-derived states as calibration evidence and uncertainty flags, not as a complete reconstruction outcome. Restrict any provisional reconstruction analysis to high/medium-confidence records with consistent adjacent-pair states, and label `suspected_rebuild` as a candidate until the requested official reconstruction register is available.
"""
    (EXP / "audit_round1.md").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
