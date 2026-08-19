#!/usr/bin/env python3
"""Audit the remediated candidate gate and final geometry contracts.

This is a feasibility audit, not a final result. It verifies that every core
ledger row passes the Boolean gates at its declared Gate Unit and has either a
passing or explicitly metric-dependent hazard gate.
"""
from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
LEDGER = ROOT / "data/processed/repeated_shock_candidate_ledger_preprocessed.parquet"
GEOMETRIES = ROOT / "data/processed/repeated_shock_case_geometries_preprocessed.parquet"
OUT = ROOT / "data/exp/feasibility-check/gate-remediation"
UNIVERSE_ORDER = [
    "post-2016 local road projects",
    "2016 officially restored bridges",
    "2026 bridge-damage records",
    "additional official reconstructions",
]


def main() -> None:
    ledger = pd.read_parquet(LEDGER)
    geometries = gpd.read_parquet(GEOMETRIES)
    included = ledger["Core Status"].str.startswith("include")
    hazard_admissible = ledger["Hazard Gate"].isin(["pass", "metric dependent"])
    ledger["Boolean Gates Pass"] = (
        ledger["Identity Gate"] & ledger["Geometry Gate"] & ledger["Outcome Gate"]
    )
    ledger["Hazard Gate Admissible"] = hazard_admissible
    ledger["Core Contract Pass"] = (
        ~included | (ledger["Boolean Gates Pass"] & ledger["Hazard Gate Admissible"])
    )

    if len(ledger) != 65 or set(ledger["Candidate Universe"]) != set(UNIVERSE_ORDER):
        raise RuntimeError("Unexpected candidate denominator contract.")
    if not ledger.loc[included, "Core Contract Pass"].all():
        raise RuntimeError("An included row fails the remediated core gate contract.")
    if (
        len(geometries) != 2
        or set(geometries["Case ID"]) != {"MASHIKI-CENTRAL", "YOKOE-BRIDGE"}
        or not geometries["Geometry Gate"].all()
        or geometries.geometry.is_empty.any()
        or not geometries.geometry.is_valid.all()
    ):
        raise RuntimeError("The final two-case geometry contract failed.")

    summary_rows: list[dict[str, object]] = []
    for universe in UNIVERSE_ORDER:
        subset = ledger.loc[ledger["Candidate Universe"].eq(universe)]
        summary_rows.append(
            {
                "Candidate Universe": universe,
                "Records Screened": int(len(subset)),
                "Identity Gate Pass": int(subset["Identity Gate"].sum()),
                "Geometry Gate Pass": int(subset["Geometry Gate"].sum()),
                "Hazard Gate Admissible": int(subset["Hazard Gate Admissible"].sum()),
                "Outcome Gate Pass": int(subset["Outcome Gate"].sum()),
                "Included Records": int(subset["Core Status"].str.startswith("include").sum()),
            }
        )
    summary = pd.DataFrame(summary_rows)
    core = ledger.loc[
        included,
        [
            "Candidate ID",
            "Candidate Universe",
            "Gate Unit",
            "Identity Gate",
            "Geometry Gate",
            "Geometry Gate Basis",
            "Hazard Gate",
            "Outcome Gate",
            "Core Status",
            "Core Contract Pass",
        ],
    ].copy()

    OUT.mkdir(parents=True, exist_ok=True)
    summary.to_csv(OUT / "candidate_gate_summary.csv", index=False)
    core.to_csv(OUT / "included_record_gate_audit.csv", index=False)
    geometry_preview = geometries.drop(columns="Geometry").copy()
    geometry_preview.to_csv(OUT / "case_geometry_contract.csv", index=False)
    (OUT / "README.md").write_text(
        "# Final Candidate Gate Contract Audit\n\n"
        "- Candidate ledger: 65 rows across four official denominators.\n"
        "- Included ledger rows: 5 audit rows collapsing to two physical cases.\n"
        "- All included rows pass Identity, Geometry, and Outcome gates at Gate Unit.\n"
        "- Mashiki Hazard Gate remains metric dependent and is admissible only with its stated boundary.\n"
        "- Both final case geometries are non-empty, valid, and Geometry Gate=True.\n"
        "- The audit supports selection-contract consistency; it does not establish causality.\n",
        encoding="utf-8",
    )
    print(f"Saved gate audit -> {OUT.relative_to(ROOT)}")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
