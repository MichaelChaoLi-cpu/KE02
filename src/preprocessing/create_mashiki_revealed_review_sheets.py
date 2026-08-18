#!/usr/bin/env python3
"""Create date-revealed review sheets without altering the blind source chips."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
CALIBRATION_ROOT = ROOT / "data/exp/building-label-calibration/mashiki"
SAMPLE_PATH = ROOT / "data/processed/mashiki_calibration_sample_preprocessed.parquet"
LABELS_PATH = CALIBRATION_ROOT / "labels.csv"
CHIPS_ROOT = CALIBRATION_ROOT / "chips_blind_round1"
OUTPUT_ROOT = CALIBRATION_ROOT / "contact_sheets_revealed_round2"

NO = "no_visible_change"
HEADER_HEIGHT = 54
ROWS_PER_SHEET = 5


def counterpart_2016(left: str) -> str:
    if left == "2016-04-16 post-mainshock":
        return "2016-04-15 post-foreshock"
    return "2016-04-16 post-mainshock"


def counterpart_2026(left: str) -> str:
    if left == "2026 post-event":
        return "PLATEAU FY2023 pre-2026 baseline"
    return "2026 post-event"


def add_revealed_header(row: pd.Series) -> Image.Image:
    chip = Image.open(CHIPS_ROOT / f"{row['Calibration ID']}.png").convert("RGB")
    canvas = Image.new("RGB", (chip.width, chip.height + HEADER_HEIGHT), "white")
    canvas.paste(chip, (0, HEADER_HEIGHT))
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default()
    pair_1_right = counterpart_2016(row["Pair 1 Left Is"])
    pair_2_right = counterpart_2026(row["Pair 2 Left Is"])
    line_1 = (
        f"{row['Calibration ID']} | A={row['Pair 1 Left Is']} | B={pair_1_right} | "
        f"R1={row['Round 1 Pair 1 Label']} ({row['Round 1 Pair 1 Confidence']})"
    )
    line_2 = (
        f"C={row['Pair 2 Left Is']} | D={pair_2_right} | "
        f"R1={row['Round 1 Pair 2 Label']} ({row['Round 1 Pair 2 Confidence']})"
    )
    draw.text((8, 7), line_1, fill="black", font=font)
    draw.text((8, 29), line_2, fill="black", font=font)
    draw.line((0, HEADER_HEIGHT - 1, chip.width, HEADER_HEIGHT - 1), fill="black", width=1)
    return canvas


def main() -> None:
    labels = pd.read_csv(LABELS_PATH, dtype=str, keep_default_na=False)
    sample = pd.read_parquet(SAMPLE_PATH)
    merged = labels.merge(
        sample[["Calibration ID", "Pair 1 Left Is", "Pair 2 Left Is"]],
        on="Calibration ID",
        validate="one_to_one",
    )
    selected = merged.loc[
        (merged["Round 1 Pair 1 Label"] != NO)
        | (merged["Round 1 Pair 2 Label"] != NO)
    ].copy()
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    selected.to_csv(OUTPUT_ROOT / "review_selection.csv", index=False)

    rendered = [add_revealed_header(row) for _, row in selected.iterrows()]
    for sheet_number, start in enumerate(range(0, len(rendered), ROWS_PER_SHEET), start=1):
        rows = rendered[start : start + ROWS_PER_SHEET]
        sheet = Image.new(
            "RGB",
            (max(row.width for row in rows), sum(row.height for row in rows)),
            "white",
        )
        y_offset = 0
        for row in rows:
            sheet.paste(row, (0, y_offset))
            y_offset += row.height
        sheet.save(OUTPUT_ROOT / f"review_sheet_{sheet_number:02d}.png", optimize=True)


if __name__ == "__main__":
    main()
