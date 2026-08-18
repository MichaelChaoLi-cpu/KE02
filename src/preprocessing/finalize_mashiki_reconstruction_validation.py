#!/usr/bin/env python3
"""Reconcile two blind review rounds and produce conservative final validation flags."""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import pandas as pd

from adjudicate_mashiki_reconstruction_validation import (
    PAIR_DATES,
    decode_pair,
    inventory_assessment,
    markdown_table,
)


ROOT = Path(__file__).resolve().parents[2]
EXP = ROOT / "data/exp/reconstruction-validation/mashiki"
INPUT = ROOT / "data/processed/mashiki_reconstruction_validation_adjudicated_preprocessed.parquet"
OUTPUT = ROOT / "data/processed/mashiki_reconstruction_validation_final_preprocessed.parquet"
CONFIDENCE_RANK = {"low": 1, "medium": 2, "high": 3}


def main() -> None:
    frame = gpd.read_parquet(INPUT)
    mapping = pd.read_csv(EXP / "round2/blind_mapping_round2.csv", dtype=str)
    labels = pd.read_csv(EXP / "round2/labels_round2.csv", dtype=str)
    round2 = mapping.merge(labels, on="Review ID", validate="one_to_one")
    if round2[["Round 2 Label", "Round 2 Confidence"]].isna().any().any():
        raise RuntimeError("round-2 labels are incomplete")

    round2_records: list[dict[str, object]] = []
    for _, row in round2.iterrows():
        pair_number = int(row["Pair Number"])
        earlier, later = PAIR_DATES[pair_number]
        _, _, transition = decode_pair(
            row["Round 2 Label"], row["Round 2 X Is"], earlier, later
        )
        round2_records.append(
            {
                "Validation ID": row["Validation ID"],
                "Pair Number": pair_number,
                "Round 2 Ordered Transition": transition,
                "Round 2 Confidence": row["Round 2 Confidence"],
                "Review ID": row["Review ID"],
            }
        )
    round2_long = pd.DataFrame(round2_records)

    final_rows: list[dict[str, object]] = []
    for _, row in frame.iterrows():
        record: dict[str, object] = {"Validation ID": row["Validation ID"]}
        reviewed = round2_long.loc[round2_long["Validation ID"].eq(row["Validation ID"])]
        for pair_number in range(1, 4):
            r1_transition = row[f"Pair {pair_number} Ordered Transition"]
            r1_confidence = row[f"Round 1 Pair {pair_number} Confidence"]
            r2 = reviewed.loc[reviewed["Pair Number"].eq(pair_number)]
            if r2.empty:
                final_transition = r1_transition
                final_confidence = r1_confidence
                resolution = "round1_not_targeted"
            else:
                r2_transition = r2.iloc[0]["Round 2 Ordered Transition"]
                r2_confidence = r2.iloc[0]["Round 2 Confidence"]
                if r1_transition == r2_transition:
                    final_transition = r1_transition
                    final_confidence = max(
                        (r1_confidence, r2_confidence), key=CONFIDENCE_RANK.get
                    )
                    resolution = "blind_rounds_agree"
                elif CONFIDENCE_RANK[r1_confidence] > CONFIDENCE_RANK[r2_confidence]:
                    final_transition = r1_transition
                    final_confidence = r1_confidence
                    resolution = "round1_higher_confidence"
                elif CONFIDENCE_RANK[r2_confidence] > CONFIDENCE_RANK[r1_confidence]:
                    final_transition = r2_transition
                    final_confidence = r2_confidence
                    resolution = "round2_higher_confidence"
                else:
                    final_transition = "unresolved_round_disagreement"
                    final_confidence = r1_confidence
                    resolution = "excluded_equal_confidence_disagreement"
            record[f"Final Pair {pair_number} Ordered Transition"] = final_transition
            record[f"Final Pair {pair_number} Confidence"] = final_confidence
            record[f"Final Pair {pair_number} Resolution"] = resolution
        final_rows.append(record)
    final = frame.merge(pd.DataFrame(final_rows), on="Validation ID", validate="one_to_one")

    state_lookup = {
        "stable_present_to_present": ("present", "present"),
        "changed_present_to_present": ("present", "present"),
        "present_to_absent": ("present", "absent"),
        "absent_to_present": ("absent", "present"),
        "absent_to_absent": ("absent", "absent"),
        "uninterpretable": ("unknown", "unknown"),
        "unresolved_round_disagreement": ("unknown", "unknown"),
    }
    for pair_number in range(1, 4):
        states = final[f"Final Pair {pair_number} Ordered Transition"].map(state_lookup)
        final[f"Final Pair {pair_number} Earlier State"] = states.str[0]
        final[f"Final Pair {pair_number} Later State"] = states.str[1]
    final["Final 2016-04-16 Cross-Pair Consistent"] = (
        final["Final Pair 1 Later State"].eq(final["Final Pair 2 Earlier State"])
        | final["Final Pair 1 Later State"].eq("unknown")
        | final["Final Pair 2 Earlier State"].eq("unknown")
    )
    final["Final 2020-11 Cross-Pair Consistent"] = (
        final["Final Pair 2 Later State"].eq(final["Final Pair 3 Earlier State"])
        | final["Final Pair 2 Later State"].eq("unknown")
        | final["Final Pair 3 Earlier State"].eq("unknown")
    )
    final["Final Inventory Status Visual Assessment"] = [
        inventory_assessment(status, transition)
        if transition != "unresolved_round_disagreement"
        else "unresolved"
        for status, transition in zip(
            final["Source Match Status"],
            final["Final Pair 3 Ordered Transition"],
            strict=True,
        )
    ]
    final["Final Inventory Validation Eligible"] = (
        final["Final Pair 2 Confidence"].isin(["high", "medium"])
        & final["Final Pair 3 Confidence"].isin(["high", "medium"])
        & ~final["Final Pair 2 Ordered Transition"].isin(
            ["uninterpretable", "unresolved_round_disagreement"]
        )
        & ~final["Final Pair 3 Ordered Transition"].isin(
            ["uninterpretable", "unresolved_round_disagreement"]
        )
        & final["Final 2020-11 Cross-Pair Consistent"]
    )
    final["Final Longitudinal Validation Eligible"] = (
        final[[f"Final Pair {p} Confidence" for p in range(1, 4)]]
        .isin(["high", "medium"])
        .all(axis=1)
        & ~final[[f"Final Pair {p} Ordered Transition" for p in range(1, 4)]]
        .isin(["uninterpretable", "unresolved_round_disagreement"])
        .any(axis=1)
        & final["Final 2016-04-16 Cross-Pair Consistent"]
        & final["Final 2020-11 Cross-Pair Consistent"]
    )
    final.to_parquet(OUTPUT, index=False)

    targeted = []
    for _, row in round2_long.iterrows():
        source = frame.loc[frame["Validation ID"].eq(row["Validation ID"])].iloc[0]
        targeted.append(
            source[f"Pair {int(row['Pair Number'])} Ordered Transition"]
            == row["Round 2 Ordered Transition"]
        )
    exact_agreement = int(sum(targeted))
    resolution_counts = pd.concat(
        [final[f"Final Pair {p} Resolution"] for p in range(1, 4)]
    ).value_counts()
    assessment = pd.crosstab(
        final["Source Match Status"],
        final["Final Inventory Status Visual Assessment"],
        margins=True,
    )
    eligible = pd.crosstab(
        final["Source Match Status"], final["Final Inventory Validation Eligible"], margins=True
    )
    report = f"""# Mashiki reconstruction validation: final two-round audit

## Review closure

- Round 1: 300/300 pair labels complete.
- Targeted round 2: {len(round2_long)}/53 pair labels complete.
- Exact ordered-transition agreement among targeted pairs: {exact_agreement}/{len(round2_long)} ({exact_agreement / len(round2_long) * 100:.1f}%).
- Equal-confidence disagreements excluded rather than forced: {int(resolution_counts.get('excluded_equal_confidence_disagreement', 0))} pair labels.
- Final 2016-04-16 cross-pair consistency: {int(final['Final 2016-04-16 Cross-Pair Consistent'].sum())}/100.
- Final 2020-11 cross-pair consistency: {int(final['Final 2020-11 Cross-Pair Consistent'].sum())}/100.
- Inventory-validation eligible records: {int(final['Final Inventory Validation Eligible'].sum())}/100.
- Fully longitudinal eligible records: {int(final['Final Longitudinal Validation Eligible'].sum())}/100.

The workflow is closed at the preset criteria: both rounds are complete, unresolved equal-confidence disagreements are explicit exclusions, and no source-status information was used to choose between disagreeing visual labels.

## Resolution counts across all 300 pairs

{markdown_table(resolution_counts.rename('count').to_frame())}

## Final inventory-status assessment

{markdown_table(assessment)}

## Eligibility by source status

{markdown_table(eligible)}

## Scientific boundary

This is an image-based calibration set. It supports presence/change screening and uncertainty measurement, but it does not convert the PLATEAU candidate classes into an official reconstruction register. The exact acquisition date of the FY2023 orthophoto also remains unresolved, so the final pair is described by release rather than an asserted flight year.
"""
    (EXP / "audit_final.md").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
