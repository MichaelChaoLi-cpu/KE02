#!/usr/bin/env python3
"""Prepare a re-randomized blind review of uncertain or inconsistent pair labels."""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
EXP = ROOT / "data/exp/reconstruction-validation/mashiki"
ADJUDICATED = (
    ROOT / "data/processed/mashiki_reconstruction_validation_adjudicated_preprocessed.parquet"
)
SEED = 20260819
PANEL_PIXELS = 224
ROWS_PER_SHEET = 5


def main() -> None:
    frame = gpd.read_parquet(ADJUDICATED)
    tasks: set[tuple[str, int]] = set()
    reasons: dict[tuple[str, int], set[str]] = {}

    def add(validation_id: str, pair_number: int, reason: str) -> None:
        key = (validation_id, pair_number)
        tasks.add(key)
        reasons.setdefault(key, set()).add(reason)

    for _, row in frame.iterrows():
        validation_id = row["Validation ID"]
        for pair_number in range(1, 4):
            if row[f"Round 1 Pair {pair_number} Confidence"] == "low":
                add(validation_id, pair_number, "round1_low_confidence")
        if not row["2016-04-16 Cross-Pair Consistent"]:
            add(validation_id, 1, "2016_cross_pair_inconsistency")
            add(validation_id, 2, "2016_cross_pair_inconsistency")
        if not row["2020-11 Cross-Pair Consistent"]:
            add(validation_id, 2, "2020_cross_pair_inconsistency")
            add(validation_id, 3, "2020_cross_pair_inconsistency")

    output = EXP / "round2"
    chips = output / "chips_blind"
    sheets = output / "contact_sheets_blind"
    chips.mkdir(parents=True, exist_ok=True)
    sheets.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)
    existing_mapping_path = output / "blind_mapping_round2.csv"
    design_path = output / "review_design_round2.csv"
    design_source = design_path if design_path.is_file() else existing_mapping_path
    fixed_design: dict[tuple[str, int], tuple[str, bool]] = {}
    if design_source.is_file():
        design = pd.read_csv(design_source)
        design_keys = {
            (str(row["Validation ID"]), int(row["Pair Number"]))
            for _, row in design.iterrows()
        }
        if design_keys != tasks:
            raise RuntimeError("persisted round-2 design does not match selected tasks")
        design = design.sort_values("Review ID")
        task_order = [
            (str(row["Validation ID"]), int(row["Pair Number"]))
            for _, row in design.iterrows()
        ]
        for _, row in design.iterrows():
            raw_flip = row["Round 2 Flipped"]
            flipped = (
                raw_flip
                if isinstance(raw_flip, (bool, np.bool_))
                else str(raw_flip).strip().lower() == "true"
            )
            fixed_design[(str(row["Validation ID"]), int(row["Pair Number"]))] = (
                str(row["Review ID"]),
                bool(flipped),
            )
    else:
        task_order = sorted(tasks)
        rng.shuffle(task_order)
    mapping_rows: list[dict[str, object]] = []
    chip_paths: list[Path] = []
    row_lookup = frame.set_index("Validation ID")

    for number, (validation_id, pair_number) in enumerate(task_order, start=1):
        key = (validation_id, pair_number)
        if key in fixed_design:
            review_id, flipped = fixed_design[key]
        else:
            review_id, flipped = f"R2{number:03d}", bool(rng.integers(0, 2))
        source = Image.open(EXP / "chips_blind_round1" / f"{validation_id}.png").convert("RGB")
        x0 = (pair_number - 1) * PANEL_PIXELS * 2
        left = source.crop((x0, 0, x0 + PANEL_PIXELS, PANEL_PIXELS))
        right = source.crop(
            (x0 + PANEL_PIXELS, 0, x0 + PANEL_PIXELS * 2, PANEL_PIXELS)
        )
        if flipped:
            left, right = right, left
        composite = Image.new("RGB", (PANEL_PIXELS * 2, PANEL_PIXELS), "white")
        composite.paste(left, (0, 0))
        composite.paste(right, (PANEL_PIXELS, 0))
        draw = ImageDraw.Draw(composite)
        for offset, label in ((0, "X"), (PANEL_PIXELS, "Y")):
            draw.rectangle((offset, 0, offset + 30, 24), fill=(0, 0, 0))
            draw.text(
                (offset + 8, 4), label, fill=(255, 255, 255), font=ImageFont.load_default()
            )
        path = chips / f"{review_id}.png"
        composite.save(path, optimize=True)
        chip_paths.append(path)
        original_left = row_lookup.loc[validation_id, f"Pair {pair_number} Left Is"]
        mapping_rows.append(
            {
                "Review ID": review_id,
                "Validation ID": validation_id,
                "Pair Number": pair_number,
                "Round 2 X Is": (
                    original_left if not flipped else "original_right"
                ),
                "Original Left Is": original_left,
                "Round 2 Flipped": flipped,
                "Review Reasons": ";".join(sorted(reasons[(validation_id, pair_number)])),
            }
        )

    # Replace the temporary marker with the actual right-hand date without exposing
    # it in images or the label template.
    pair_dates = {
        1: ("2016-04-15 post-foreshock", "2016-04-16 post-mainshock"),
        2: ("2016-04-16 post-mainshock", "2020-11 orthophoto"),
        3: ("2020-11 orthophoto", "PLATEAU FY2023 orthophoto"),
    }
    for mapping in mapping_rows:
        if mapping["Round 2 X Is"] == "original_right":
            earlier, later = pair_dates[int(mapping["Pair Number"])]
            mapping["Round 2 X Is"] = (
                later if mapping["Original Left Is"] == earlier else earlier
            )
    mapping_frame = pd.DataFrame(mapping_rows)
    mapping_frame.to_csv(output / "blind_mapping_round2.csv", index=False)
    mapping_frame.to_csv(design_path, index=False)
    blank_labels = pd.DataFrame(
        {
            "Review ID": [row["Review ID"] for row in mapping_rows],
            "Round 2 Label": "",
            "Round 2 Confidence": "",
        }
    )
    labels_path = output / "labels_round2.csv"
    if labels_path.is_file():
        existing_labels = pd.read_csv(labels_path, dtype=str).fillna("")
        if set(existing_labels["Review ID"]) != set(blank_labels["Review ID"]):
            raise RuntimeError("existing round-2 labels do not match the review design")
        if not existing_labels[["Round 2 Label", "Round 2 Confidence"]].ne("").all().all():
            blank_labels.to_csv(labels_path, index=False)
    else:
        blank_labels.to_csv(labels_path, index=False)

    row_height = PANEL_PIXELS + 26
    for offset in range(0, len(chip_paths), ROWS_PER_SHEET):
        selected = chip_paths[offset : offset + ROWS_PER_SHEET]
        sheet = Image.new("RGB", (PANEL_PIXELS * 2, row_height * len(selected)), (245, 245, 245))
        draw = ImageDraw.Draw(sheet)
        for row_number, path in enumerate(selected):
            y = row_number * row_height
            draw.text((5, y + 6), path.stem, fill=(0, 0, 0), font=ImageFont.load_default())
            with Image.open(path) as chip:
                sheet.paste(chip, (0, y + 26))
        sheet.save(sheets / f"sheet_{offset // ROWS_PER_SHEET + 1:02d}.png", optimize=True)
    print(f"prepared {len(mapping_rows)} second-round blind tasks")


if __name__ == "__main__":
    main()
