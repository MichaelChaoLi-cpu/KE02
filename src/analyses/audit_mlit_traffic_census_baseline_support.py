#!/usr/bin/env python3
"""Audit official MLIT traffic-census support for intervention corridors."""
from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data/raw/official_resilience/mlit_traffic_census"
OUT = ROOT / "data/exp/feasibility-check/intervention-geometry"

FILES = {
    2015: RAW / "mlit_traffic_census_2015_kumamoto_locations.csv",
    2021: RAW / "mlit_traffic_census_2021_kumamoto_locations.csv",
}

CORRIDORS = {
    "INT-KT-FOUR-LANING": {
        "name": "Kumamoto-Takamori / Mashiki Central",
        "route": "熊本高森線",
        "segment_ids": (43400280200, 43400280210, 43400280220),
        "expected_length_km": 3.5,
        "expected_lanes": 2,
        "match_type": "exact basic-section match to the 3.5 km planning corridor",
    },
    "BM-EAST-AIRPORT": {
        "name": "East Town-Airport mature four-lane benchmark",
        "route": "熊本益城大津線",
        "segment_ids": (
            43400360030,
            43400360040,
            43400360050,
            43400360060,
            43400360070,
            43400360080,
            43400360090,
        ),
        "expected_length_km": 9.1,
        "expected_lanes": 4,
        "match_type": "route-name and municipality match; 9.3 km census span approximates official 9.1 km corridor",
    },
}

COLUMN_MAP = {
    2015: {
        "route": "路線／路線名",
        "unit": "交通量調査単位区間番号／調査単位区間番号",
    },
    2021: {
        "route": "路線名",
        "unit": "交通量／調査単位区間番号",
    },
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_year(year: int) -> pd.DataFrame:
    path = FILES[year]
    if not path.exists():
        raise FileNotFoundError(path)
    source = pd.read_csv(path, encoding="cp932", low_memory=False)
    names = COLUMN_MAP[year]
    selected = source.rename(
        columns={
            "交通調査基本区間番号": "Basic Section ID",
            "市区町村コード": "Municipality Code",
            names["route"]: "Route Name",
            names["unit"]: "Survey Unit ID",
            "区間延長（ｋｍ）": "Section Length (km)",
            "車線数": "Lanes",
            "昼間１２時間自動車類交通量（上下合計）／合計（台）": "Daytime 12h Traffic (vehicles)",
            "混雑度": "Congestion Degree",
        }
    )
    columns = [
        "Basic Section ID",
        "Municipality Code",
        "Route Name",
        "Survey Unit ID",
        "Section Length (km)",
        "Lanes",
        "Daytime 12h Traffic (vehicles)",
        "Congestion Degree",
    ]
    selected = selected[columns].copy()
    selected["Basic Section ID"] = pd.to_numeric(
        selected["Basic Section ID"], errors="coerce"
    ).astype("Int64")
    selected["Survey Unit ID"] = pd.to_numeric(
        selected["Survey Unit ID"], errors="coerce"
    ).astype("Int64")
    selected["Census Year"] = year
    selected["Source File"] = path.name
    selected["Source SHA256"] = sha256(path)
    return selected


def extract_segments() -> pd.DataFrame:
    rows = []
    for year in sorted(FILES):
        source = load_year(year)
        for corridor_id, spec in CORRIDORS.items():
            subset = source.loc[
                source["Basic Section ID"].isin(spec["segment_ids"])
            ].copy()
            expected = set(spec["segment_ids"])
            found = set(subset["Basic Section ID"].dropna().astype(int))
            if found != expected:
                raise ValueError(
                    f"{year} {corridor_id} basic-section mismatch: "
                    f"missing={sorted(expected - found)}, extra={sorted(found - expected)}"
                )
            if set(subset["Municipality Code"].astype(int)) != {43443}:
                raise ValueError(f"{year} {corridor_id} municipality mismatch")
            if set(subset["Route Name"]) != {spec["route"]}:
                raise ValueError(f"{year} {corridor_id} route mismatch")
            if set(subset["Lanes"].dropna().astype(int)) != {
                spec["expected_lanes"]
            }:
                raise ValueError(f"{year} {corridor_id} lane mismatch")
            subset.insert(0, "Corridor ID", corridor_id)
            subset.insert(1, "Corridor", spec["name"])
            subset["Match Type"] = spec["match_type"]
            rows.append(subset)
    return pd.concat(rows, ignore_index=True).sort_values(
        ["Corridor ID", "Census Year", "Basic Section ID"]
    )


def build_units(segments: pd.DataFrame) -> pd.DataFrame:
    unit_keys = ["Corridor ID", "Corridor", "Census Year", "Survey Unit ID"]
    records = []
    for keys, group in segments.groupby(unit_keys, dropna=False, sort=True):
        traffic = group["Daytime 12h Traffic (vehicles)"].dropna().unique()
        congestion = group["Congestion Degree"].dropna().unique()
        lanes = group["Lanes"].dropna().unique()
        if len(traffic) > 1 or len(congestion) > 1 or len(lanes) > 1:
            raise ValueError(f"Survey-unit metrics vary within unit {keys}")
        records.append(
            {
                **dict(zip(unit_keys, keys, strict=True)),
                "Basic Sections": ";".join(
                    str(v) for v in sorted(group["Basic Section ID"].astype(int))
                ),
                "Covered Length (km)": group["Section Length (km)"].sum(),
                "Lanes": lanes[0] if len(lanes) else pd.NA,
                "Daytime 12h Traffic (vehicles)": traffic[0]
                if len(traffic)
                else pd.NA,
                "Congestion Degree": congestion[0] if len(congestion) else pd.NA,
            }
        )
    return pd.DataFrame(records)


def build_coverage(segments: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for corridor_id, spec in CORRIDORS.items():
        for year in sorted(FILES):
            subset = segments.loc[
                segments["Corridor ID"].eq(corridor_id)
                & segments["Census Year"].eq(year)
            ]
            observed = subset["Section Length (km)"].sum()
            exact = abs(observed - spec["expected_length_km"]) < 0.01
            status = "pass" if corridor_id == "INT-KT-FOUR-LANING" and exact else "partial"
            rows.append(
                {
                    "Corridor ID": corridor_id,
                    "Corridor": spec["name"],
                    "Census Year": year,
                    "Expected Official Length (km)": spec["expected_length_km"],
                    "Selected Census Length (km)": observed,
                    "Basic Sections Found": len(subset),
                    "Lane Configuration": ";".join(
                        str(int(v)) for v in sorted(subset["Lanes"].dropna().unique())
                    ),
                    "Coverage Status": status,
                    "Interpretation": spec["match_type"],
                }
            )
    rows.extend(
        [
            {
                "Corridor ID": "INT-EW3",
                "Corridor": "Mashiki East-West Line section 3",
                "Census Year": "2015/2021",
                "Expected Official Length (km)": 0.244,
                "Selected Census Length (km)": 0.0,
                "Basic Sections Found": 0,
                "Lane Configuration": "",
                "Coverage Status": "fail",
                "Interpretation": "new local street is not directly represented by a named census corridor",
            },
            {
                "Corridor ID": "BM-SORYO-KIYAMA",
                "Corridor": "Soryo-Kiyama established two-lane benchmark",
                "Census Year": "2015/2021",
                "Expected Official Length (km)": 3.8,
                "Selected Census Length (km)": 0.0,
                "Basic Sections Found": 0,
                "Lane Configuration": "",
                "Coverage Status": "fail",
                "Interpretation": "local/urban corridor cannot be defensibly linked to a named census route",
            },
        ]
    )
    return pd.DataFrame(rows)


def build_gates() -> pd.DataFrame:
    return pd.DataFrame(
        [
            ("C1", "Official reproducible source", "pass", "MLIT 2015 and 2021 prefecture CSVs are locally hash-bound"),
            ("C2", "Exact treated-corridor linkage", "pass", "Three basic sections reproduce the 3.5 km Mashiki Central planning corridor in both years"),
            ("C3", "Pre-treatment structural state", "pass", "The linked corridor has two lanes in both 2015 and 2021, before four-lane completion in 2026"),
            ("C4", "Repeated longitudinal baseline", "partial", "Two census waves only; 2021 is during construction and is not a clean untreated year"),
            ("C5", "Common baseline support across units", "fail", "East-West section 3 and the local Soryo-Kiyama benchmark lack direct census matches"),
            ("C6", "Same outcome before and after event", "fail", "Census traffic and congestion are structural context, not pre-event private-probe passage observations"),
            ("C7", "Causal estimator supported", "fail", "No untreated counterfactual or common longitudinal outcome panel is identified"),
        ],
        columns=["Gate ID", "Gate", "Status", "Evidence"],
    )


def render_markdown(
    segments: pd.DataFrame,
    units: pd.DataFrame,
    coverage: pd.DataFrame,
    gates: pd.DataFrame,
) -> str:
    kt = units.loc[units["Corridor ID"].eq("INT-KT-FOUR-LANING")]
    east = units.loc[units["Corridor ID"].eq("BM-EAST-AIRPORT")]
    hashes = segments[["Census Year", "Source File", "Source SHA256"]].drop_duplicates()
    return f"""# MLIT traffic-census baseline support audit

## Result

The official road-traffic census establishes a reproducible structural baseline for the Mashiki Central treatment corridor. In both 2015 and 2021, basic sections 43400280200, 43400280210, and 43400280220 reproduce exactly 3.5 km of Kumamoto-Takamori Road in Mashiki; every section is recorded as two lanes. This is consistent with a two-to-four-lane intervention completed before the 2026 earthquake.

The census does **not** create a pre-event version of the 2026 private-probe passage outcome. It measures traffic demand, congestion, and road structure in two distant census years. The 2021 wave occurred during the intervention period and may also reflect pandemic-era traffic conditions. These data therefore support context and treatment validation, not a before-after causal estimate.

## Treated-corridor survey units

{kt.to_markdown(index=False, floatfmt=".2f")}

## Mature four-lane measurement benchmark

{east.to_markdown(index=False, floatfmt=".2f")}

East Town-Airport is a useful scale and measurement benchmark because the selected census span is consistently four lanes and carries high traffic. Its 9.3 km census span only approximates the official 9.1 km urban-planning corridor, and it differs from the treatment in route role, exposure, and selection. It is not a causal control.

## Coverage by candidate unit

{coverage.to_markdown(index=False, floatfmt=".3f")}

## Gates

{gates.to_markdown(index=False)}

## Source binding

{hashes.to_markdown(index=False)}

## Permissible interpretation

- The Mashiki Central corridor had measurable traffic demand and congestion while still configured as two lanes in 2015 and 2021.
- The 2026 four-laning is structurally verified as a two-to-four-lane change, not merely inferred from the project title.
- Traffic-census levels must not be compared directly with post-earthquake probe-passage presence as though they were the same outcome.
- No common baseline exists for both exact post-2016 intervention units, so the project still cannot identify a common causal resilience effect.

## Rebuild

```bash
UV_CACHE_DIR=/private/tmp/ke02-uv-cache uv run python src/analyses/audit_mlit_traffic_census_baseline_support.py
```
"""


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    segments = extract_segments()
    units = build_units(segments)
    coverage = build_coverage(segments)
    gates = build_gates()
    segments.to_csv(OUT / "mlit_traffic_census_baseline_segments.csv", index=False)
    units.to_csv(OUT / "mlit_traffic_census_baseline_units.csv", index=False)
    coverage.to_csv(OUT / "mlit_traffic_census_baseline_coverage.csv", index=False)
    gates.to_csv(OUT / "mlit_traffic_census_baseline_gate.csv", index=False)
    (OUT / "TRAFFIC_CENSUS_BASELINE_AUDIT.md").write_text(
        render_markdown(segments, units, coverage, gates), encoding="utf-8"
    )
    print(OUT / "TRAFFIC_CENSUS_BASELINE_AUDIT.md")


if __name__ == "__main__":
    main()
